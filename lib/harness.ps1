# lib/harness.ps1 - the PowerShell installer library (T268, ADR-0003 decisions 3 and 5).
#
# Dot-sourced by setup.ps1 (before lib/harness-update.ps1, T271). It defines functions only and does no
# work when it is loaded. Each function names the shell function in setup.sh or
# lib/harness-fetch.sh it ports; setup.sh stays the source of truth for behaviour.
#
# Rules kept everywhere, so Windows PowerShell 5.1 and PowerShell 7 both run it:
#   - files are read and written through [IO.File] / [IO.Directory] with absolute paths, so bytes
#     are copied as they are (no re-encoding, no line-ending rewrite) and no wildcard is expanded;
#   - a native command gets its arguments as an array (Invoke-HarnessNative), never a built string;
#   - a link (junction or symbolic link) is removed or moved as the link itself, never followed.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# The kit version this run replaces (kit_commit in the old lock). Names every backup (T137).
$script:HarnessPrevCommit = ''
# Temp directories to remove when the run ends, also on error or Ctrl+C (setup.ps1's finally).
$script:HarnessTempDirs = New-Object 'System.Collections.Generic.List[string]'
# Thrown after an [error] line was already printed; the caller exits 1 without a second message.
$script:HarnessStop = 'HARNESS-STOP'
$script:HarnessUtf8 = New-Object System.Text.UTF8Encoding $false

# ports log_info / log_warn / log_error
function Write-HarnessInfo([string]$Message) { Write-Host "[info]  $Message" }
function Write-HarnessWarn([string]$Message) { [Console]::Error.WriteLine("[warn]  $Message") }
function Write-HarnessError([string]$Message) { [Console]::Error.WriteLine("[error] $Message") }

# Run a native program; returns ExitCode and Output (stdout and stderr lines, as text). The local
# 'Continue' keeps a stderr line from becoming a terminating error under 5.1.
function Invoke-HarnessNative {
    param([string]$Exe, [string[]]$Arguments = @())
    $ErrorActionPreference = 'Continue'
    $lines = @(& $Exe @Arguments 2>&1 | ForEach-Object { "$_" })
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $lines }
}

function Test-HarnessCommand([string]$Name) {
    return [bool](Get-Command -Name $Name -CommandType Application -ErrorAction SilentlyContinue)
}

# ADR-0003 decision 3: `py -3`, else `python`. Each is run with a version probe, so the Microsoft
# Store stub (a `python` that only prints a hint) is rejected. Returns $null when none works.
function Find-HarnessPython {
    $probe = 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'
    $candidates = @(
        [pscustomobject]@{ Name = 'py'; Prefix = @('-3') },
        [pscustomobject]@{ Name = 'python'; Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        if (-not (Test-HarnessCommand $candidate.Name)) { continue }
        $result = Invoke-HarnessNative $candidate.Name (@($candidate.Prefix) + @('-c', $probe))
        if ($result.ExitCode -eq 0) { return $candidate }
    }
    return $null
}

# Run a kit Python helper with the launcher Find-HarnessPython chose.
function Invoke-HarnessPython($Python, [string[]]$Arguments) {
    return Invoke-HarnessNative $Python.Name (@($Python.Prefix) + $Arguments)
}

# ports kit_repo_url (setup.sh)
function Get-HarnessKitUrl {
    $user = 'thunderkds'
    if ($env:GITHUB_USERNAME) { $user = $env:GITHUB_USERNAME }
    $url = "https://github.com/$user/easy-kit.git"
    if ($user -ne 'thunderkds') {
        $saved = $env:GIT_TERMINAL_PROMPT
        $env:GIT_TERMINAL_PROMPT = '0'
        try {
            $probe = Invoke-HarnessNative 'git' @('ls-remote', $url, 'HEAD')
        } finally {
            $env:GIT_TERMINAL_PROMPT = $saved
        }
        if ($probe.ExitCode -ne 0) { $url = "https://github.com/$user/personal-agentic-claude.git" }
    }
    return $url
}

# <base> joined with a repo-relative path written with '/'.
function Join-HarnessPath([string]$Base, [string]$Rel) {
    if (-not $Rel) { return $Base }
    return [IO.Path]::Combine($Base, $Rel.Replace([char]'/', [IO.Path]::DirectorySeparatorChar))
}

# The attributes of a path, without following a link; $null when nothing is there (a broken link
# is still there).
function Get-HarnessAttributes([string]$Path) {
    try {
        $info = New-Object IO.FileInfo $Path
        if ([int]$info.Attributes -eq -1) { return $null }
        return $info.Attributes
    } catch {
        return $null
    }
}

function Test-HarnessPresent([string]$Path) { return $null -ne (Get-HarnessAttributes $Path) }

function Test-HarnessFlag($Attributes, [IO.FileAttributes]$Flag) {
    return ($null -ne $Attributes) -and (($Attributes -band $Flag) -eq $Flag)
}

function Test-HarnessLink([string]$Path) {
    return Test-HarnessFlag (Get-HarnessAttributes $Path) ([IO.FileAttributes]::ReparsePoint)
}

function Test-HarnessDirectory([string]$Path) {
    $attributes = Get-HarnessAttributes $Path
    return (Test-HarnessFlag $attributes ([IO.FileAttributes]::Directory)) -and
        -not (Test-HarnessFlag $attributes ([IO.FileAttributes]::ReparsePoint))
}

function Test-HarnessFile([string]$Path) {
    $attributes = Get-HarnessAttributes $Path
    return ($null -ne $attributes) -and
        -not (Test-HarnessFlag $attributes ([IO.FileAttributes]::Directory)) -and
        -not (Test-HarnessFlag $attributes ([IO.FileAttributes]::ReparsePoint))
}

# ports compute_file_hash (setup.sh): lower-case hex SHA-256 of the content.
function Get-HarnessFileHash([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        $bytes = $sha.ComputeHash($stream)
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

# Every entry under <root>, keyed by its '/'-separated relative path: 'dir', 'file' or 'link'.
# A link is listed and never followed (so a junction is never walked into).
function Get-HarnessTreeEntries([string]$Root) {
    $map = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push('')
    while ($pending.Count -gt 0) {
        $rel = $pending.Pop()
        $dir = Join-HarnessPath $Root $rel
        foreach ($item in (New-Object IO.DirectoryInfo $dir).GetFileSystemInfos()) {
            $childRel = $item.Name
            if ($rel) { $childRel = "$rel/$($item.Name)" }
            if (Test-HarnessFlag $item.Attributes ([IO.FileAttributes]::ReparsePoint)) {
                $map[$childRel] = 'link'
            } elseif (Test-HarnessFlag $item.Attributes ([IO.FileAttributes]::Directory)) {
                $map[$childRel] = 'dir'
                $pending.Push($childRel)
            } else {
                $map[$childRel] = 'file'
            }
        }
    }
    return , $map
}

function Test-HarnessUnder([string]$Rel, [string[]]$Prefixes) {
    foreach ($prefix in $Prefixes) {
        if ($Rel -ceq $prefix -or $Rel.StartsWith("$prefix/", [StringComparison]::Ordinal)) { return $true }
    }
    return $false
}

# Same content, as `cmp -s` (files) or `diff -rq` (directories) decides it. <Ignore> holds paths
# relative to both roots that are left out of the comparison (MANIFEST exclusions, T113). A link
# on the destination side is never the same.
function Test-HarnessSameContent([string]$Src, [string]$Dst, [string[]]$Ignore = @()) {
    $srcAttr = Get-HarnessAttributes $Src
    $dstAttr = Get-HarnessAttributes $Dst
    if ($null -eq $srcAttr -or $null -eq $dstAttr) { return $false }
    if (Test-HarnessLink $Dst) { return $false }
    $srcIsDir = Test-HarnessFlag $srcAttr ([IO.FileAttributes]::Directory)
    $dstIsDir = Test-HarnessFlag $dstAttr ([IO.FileAttributes]::Directory)
    if (-not $srcIsDir -and -not $dstIsDir) {
        if ((New-Object IO.FileInfo $Src).Length -ne (New-Object IO.FileInfo $Dst).Length) { return $false }
        return (Get-HarnessFileHash $Src) -eq (Get-HarnessFileHash $Dst)
    }
    if (-not ($srcIsDir -and $dstIsDir)) { return $false }
    $srcMap = Get-HarnessTreeEntries $Src
    $dstMap = Get-HarnessTreeEntries $Dst
    foreach ($key in @($srcMap.Keys)) { if (Test-HarnessUnder $key $Ignore) { [void]$srcMap.Remove($key) } }
    foreach ($key in @($dstMap.Keys)) { if (Test-HarnessUnder $key $Ignore) { [void]$dstMap.Remove($key) } }
    if ($srcMap.Count -ne $dstMap.Count) { return $false }
    foreach ($key in $srcMap.Keys) {
        if (-not $dstMap.ContainsKey($key) -or $srcMap[$key] -ne $dstMap[$key]) { return $false }
        if ($dstMap[$key] -eq 'link') { return $false }
    }
    foreach ($key in $srcMap.Keys) {
        if ($srcMap[$key] -eq 'file') {
            $a = Join-HarnessPath $Src $key
            $b = Join-HarnessPath $Dst $key
            if ((Get-HarnessFileHash $a) -ne (Get-HarnessFileHash $b)) { return $false }
        }
    }
    return $true
}

# Remove a path. A link is removed as the link (its target is untouched); a read-only file is
# made writable first.
function Remove-HarnessPath([string]$Path) {
    $attributes = Get-HarnessAttributes $Path
    if ($null -eq $attributes) { return }
    if (Test-HarnessFlag $attributes ([IO.FileAttributes]::ReparsePoint)) {
        if (Test-HarnessFlag $attributes ([IO.FileAttributes]::Directory)) {
            try { [IO.Directory]::Delete($Path, $false) } catch { [IO.File]::Delete($Path) }
        } else {
            [IO.File]::Delete($Path)
        }
        return
    }
    if (Test-HarnessFlag $attributes ([IO.FileAttributes]::Directory)) {
        foreach ($item in (New-Object IO.DirectoryInfo $Path).GetFileSystemInfos()) {
            Remove-HarnessPath $item.FullName
        }
        [IO.Directory]::Delete($Path, $false)
        return
    }
    if (Test-HarnessFlag $attributes ([IO.FileAttributes]::ReadOnly)) {
        [IO.File]::SetAttributes($Path, ($attributes -band (-bnot [IO.FileAttributes]::ReadOnly)))
    }
    [IO.File]::Delete($Path)
}

# Move a file, directory or link (as the link itself) to a new name in the same folder.
function Move-HarnessItem([string]$From, [string]$To) {
    if (Test-HarnessFlag (Get-HarnessAttributes $From) ([IO.FileAttributes]::Directory)) {
        [IO.Directory]::Move($From, $To)
    } else {
        [IO.File]::Move($From, $To)
    }
}

# A real copy of a file or a directory tree, byte for byte (`cp -r`). <Dst> must not exist.
# A link inside the source is skipped with a warning: the kit ships none in a MANIFEST path.
function Copy-HarnessPath([string]$Src, [string]$Dst) {
    if (Test-HarnessDirectory $Src) {
        [void][IO.Directory]::CreateDirectory($Dst)
        foreach ($item in (New-Object IO.DirectoryInfo $Src).GetFileSystemInfos()) {
            $target = [IO.Path]::Combine($Dst, $item.Name)
            if (Test-HarnessFlag $item.Attributes ([IO.FileAttributes]::ReparsePoint)) {
                Write-HarnessWarn "Skipped the link '$($item.FullName)': a link is not copied."
                continue
            }
            Copy-HarnessPath $item.FullName $target
        }
        return
    }
    [IO.File]::Copy($Src, $Dst, $false)
}

# ports harness_backup_suffix: bak-<old kit commit>, or bak-<yyyyMMdd>. The lock is the project's
# file, so anything but a lower-case hex commit ID is ignored rather than let into a path.
function Get-HarnessBackupSuffix {
    if ($script:HarnessPrevCommit -cmatch '^[0-9a-f]+$') { return "bak-$($script:HarnessPrevCommit)" }
    return 'bak-' + (Get-Date -Format 'yyyyMMdd')
}

# ports harness_backup_name: the first free <dst>.<suffix>, <dst>.<suffix>.1, ... (a taken name,
# a broken link included, is never reused).
function Get-HarnessBackupName([string]$Dst) {
    $base = "$Dst." + (Get-HarnessBackupSuffix)
    $to = $base
    $n = 0
    while (Test-HarnessPresent $to) {
        $n += 1
        $to = "$base.$n"
    }
    return $to
}

# ports harness_backup_path: move a pre-existing <dst> that differs from <src> (or is a link, or a
# type mismatch) aside to Get-HarnessBackupName, and name it in a [warn] line. Identical content:
# nothing. A failed move prints an [error] and stops the run before <dst> is replaced.
# <Display> is the repo-relative path shown to the user.
function Backup-HarnessPath([string]$Src, [string]$Dst, [string]$Display) {
    if (-not (Test-HarnessPresent $Dst)) { return }
    if (-not (Test-HarnessLink $Dst) -and (Test-HarnessSameContent $Src $Dst)) { return }
    $to = Get-HarnessBackupName $Dst
    $shown = './' + $Display + $to.Substring($Dst.Length)
    try {
        Move-HarnessItem $Dst $to
    } catch {
        Write-HarnessError "Could not back up './$Display' to '$shown' - './$Display' was not replaced; paths before it in this run, if any, were already installed. Fix the permissions, then re-run. ($($_.Exception.Message))"
        throw $script:HarnessStop
    }
    Write-HarnessWarn "Backed up your existing './$Display' to '$shown' before installing the kit's copy - compare and merge by hand, then delete the backup."
    if ($Display -ceq '.claude/hooks') {
        Write-HarnessWarn "Your own hooks now live in '$shown'; any entries in .claude/settings.json that point at them must be updated to that path."
    }
}

# Would Backup-HarnessPath move <dst> aside? (install_would_back_up, setup.sh) The paths in
# <Ignore> are left out on both sides, because the install never touches them (T113).
function Test-HarnessWouldBackUp([string]$Src, [string]$Dst, [string[]]$Ignore = @()) {
    if (-not (Test-HarnessPresent $Dst)) { return $false }
    if (Test-HarnessLink $Dst) { return $true }
    return -not (Test-HarnessSameContent $Src $Dst $Ignore)
}

# ports harness_manifest_path: field 1 of a MANIFEST line; '' for a comment, a blank line or a
# `!` exclusion. Trailing `<cli>=<dest>` pairs are ignored (Claude Code only). A path that could
# leave the project (rooted, a drive, a `..` segment, a backslash) stops the run: every path is
# read, and the plan is printed, before the first write.
function Get-HarnessManifestPath([string]$Line) {
    $text = $Line.Replace("`r", '').Trim()
    if (-not $text -or $text.StartsWith('#') -or $text.StartsWith('!')) { return '' }
    $rel = ($text -split '\s+')[0]
    Assert-HarnessSafeRel $rel 'MANIFEST path'
    return $rel
}

# Stop the run (an [error], then HarnessStop) when a MANIFEST path or `!` exclusion could leave
# the project: empty, rooted, a drive, a backslash or a `..` segment.
function Assert-HarnessSafeRel([string]$Rel, [string]$Kind) {
    if (-not (Test-HarnessSafeRel $Rel)) {
        Write-HarnessError "$Kind '$Rel' must be a relative path inside the project (no leading '/', no drive, no '..'). The fetched Easy Kit may be corrupt."
        throw $script:HarnessStop
    }
}

# A repo-relative path that stays inside the project: not empty, not rooted, no drive, no
# backslash, no `..` segment.
function Test-HarnessSafeRel([string]$Rel) {
    return -not (-not $Rel -or $Rel.StartsWith('/') -or $Rel.Contains('\') -or $Rel.Contains(':') -or
        (@($Rel.Split([char]'/')) -contains '..'))
}

# ports harness_manifest_exclusions: the `!<path>` lines, without the `!`.
function Get-HarnessManifestExclusions([string]$Manifest) {
    $found = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in [IO.File]::ReadAllLines($Manifest)) {
        $text = $line.Replace("`r", '').Trim()
        if (-not $text) { continue }
        $field = ($text -split '\s+')[0]
        if ($field.Length -gt 1 -and $field[0] -eq [char]'!') {
            Assert-HarnessSafeRel $field.Substring(1) 'MANIFEST exclusion'
            $found.Add($field.Substring(1))
        }
    }
    return , $found.ToArray()
}

# ports harness_is_excluded: <rel> equals an exclusion or sits under one, on whole path segments.
function Test-HarnessExcluded([string[]]$Exclusions, [string]$Rel) {
    return Test-HarnessUnder $Rel $Exclusions
}

# ports _harness_exclusions_under: exclusions strictly under <rel>, made relative to it.
function Get-HarnessExclusionsUnder([string[]]$Exclusions, [string]$Rel) {
    $found = New-Object 'System.Collections.Generic.List[string]'
    foreach ($exclusion in $Exclusions) {
        if ($exclusion.StartsWith("$Rel/", [StringComparison]::Ordinal)) {
            $found.Add($exclusion.Substring($Rel.Length + 1))
        }
    }
    return , $found.ToArray()
}

# ports harness_make_temp_dir: a new temp path (not created: `git clone` creates it), registered
# for removal when the run ends.
function New-HarnessTempPath {
    $name = 'harness-fetch.' + [guid]::NewGuid().ToString('N').Substring(0, 12)
    $path = [IO.Path]::Combine([IO.Path]::GetTempPath(), $name)
    $script:HarnessTempDirs.Add($path)
    return $path
}

# ports harness_cleanup: remove every registered temp dir. Safe to call more than once.
function Clear-HarnessTemp {
    foreach ($dir in $script:HarnessTempDirs) {
        try { Remove-HarnessPath $dir } catch { Write-HarnessWarn "Could not remove the temp folder '$dir': $($_.Exception.Message)" }
    }
    $script:HarnessTempDirs.Clear()
}

# ports harness_fetch: git clone --depth 1 <url> <dest>.
function Invoke-HarnessFetch([string]$Url, [string]$Dest) {
    Write-HarnessInfo "Fetching (shallow clone): $Url"
    $result = Invoke-HarnessNative 'git' @('clone', '--depth', '1', '--quiet', '--', $Url, $Dest)
    if ($result.ExitCode -ne 0) {
        foreach ($line in $result.Output) { [Console]::Error.WriteLine($line) }
        Write-HarnessError "Failed to clone '$Url'. Check the URL, network connectivity, and git credentials."
        throw $script:HarnessStop
    }
}

# ports _harness_install_excluding: install <src> over <dst> when the MANIFEST excludes a path under
# <rel>. The kit's copy is staged without it, and the project's own excluded path is held aside and
# put back, so it is neither installed, backed up nor compared. The work folder sits next to <dst>,
# so every move stays on one volume. Whatever happens, held content is put back; if a move back
# fails, the work folder is kept (never deleted), named in an [error], and the run stops.
function Install-HarnessExcluding([string]$Src, [string]$Dst, [string]$Rel, [string[]]$Subs) {
    $work = "$Dst.easykit-" + [guid]::NewGuid().ToString('N').Substring(0, 8)
    $stage = Join-HarnessPath $work 'stage'
    $held = Join-HarnessPath $work 'held'
    [void][IO.Directory]::CreateDirectory($work)
    $restored = $true
    try {
        try {
            Copy-HarnessPath $Src $stage
            $canHold = Test-HarnessDirectory $Dst
            foreach ($sub in $Subs) {
                Remove-HarnessPath (Join-HarnessPath $stage $sub)
                $own = Join-HarnessPath $Dst $sub
                if ($canHold -and (Test-HarnessPresent $own)) {
                    $keep = Join-HarnessPath $held $sub
                    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($keep))
                    Move-HarnessItem $own $keep
                }
            }
            Backup-HarnessPath $stage $Dst $Rel
            Remove-HarnessPath $Dst
            Copy-HarnessPath $stage $Dst
        } finally {
            foreach ($sub in $Subs) {
                $keep = Join-HarnessPath $held $sub
                if (-not (Test-HarnessPresent $keep)) { continue }
                try {
                    $own = Join-HarnessPath $Dst $sub
                    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($own))
                    Move-HarnessItem $keep $own
                } catch {
                    $restored = $false
                    Write-HarnessError "Could not put your own './$Rel/$sub' back ($($_.Exception.Message)). It is safe in '$keep': move it back by hand."
                }
            }
        }
    } finally {
        if ($restored) {
            Remove-HarnessPath $work
        } else {
            Write-HarnessError "Kept '$held' (your own files, not deleted). Move them back to './$Rel', then delete '$work' and re-run."
        }
    }
    if (-not $restored) { throw $script:HarnessStop }
}

# ports harness_copy_manifest: copy each MANIFEST path from <tmp> into <target> as real files. A
# differing existing path is backed up first; an excluded path is never copied, backed up or
# recorded; an entry missing from the kit is warned and skipped.
function Copy-HarnessManifest([string]$Tmp, [string]$Target, [string]$Manifest) {
    $exclusions = Get-HarnessManifestExclusions $Manifest
    foreach ($line in [IO.File]::ReadAllLines($Manifest)) {
        $rel = Get-HarnessManifestPath $line
        if (-not $rel) { continue }
        $src = Join-HarnessPath $Tmp $rel
        $dst = Join-HarnessPath $Target $rel
        if (-not (Test-HarnessPresent $src)) {
            Write-HarnessWarn "MANIFEST entry '$rel' not found in the fetched kit - skipping."
            continue
        }
        if (Test-HarnessExcluded $exclusions $rel) { continue }
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
        $subs = Get-HarnessExclusionsUnder $exclusions $rel
        if ($subs.Length -gt 0) {
            Install-HarnessExcluding $src $dst $rel $subs
            continue
        }
        Backup-HarnessPath $src $dst $rel
        Remove-HarnessPath $dst
        Copy-HarnessPath $src $dst
    }
}

# ports install_claude: CLAUDE.md from CLAUDE.md or CLAUDE_LEGACY.md, backed up before a replace.
function Install-HarnessClaude([string]$Tmp, [string]$Target, [string]$ClaudeSrc) {
    $src = Join-HarnessPath $Tmp $ClaudeSrc
    $dst = Join-HarnessPath $Target 'CLAUDE.md'
    if (-not (Test-HarnessFile $src)) {
        Write-HarnessError "Source '$ClaudeSrc' not found in the fetched Easy Kit. Aborting."
        throw $script:HarnessStop
    }
    Backup-HarnessPath $src $dst 'CLAUDE.md'
    Remove-HarnessPath $dst
    Copy-HarnessPath $src $dst
}

# ports harness_install_canon_symlinks for Windows (ADR-0003 decision 5): .claude/skills and
# .claude/agents become directory junctions onto <target>\skills and <target>\agents. When a
# junction cannot be made, the canon is copied there instead, and both facts are printed.
# An old link is replaced; a real directory or a file there (a symlink checked out with
# core.symlinks=false) is backed up unless it already holds the canon's exact content.
# Returns the repo-relative paths that are copies (the lock's canon_copies).
function Install-HarnessCanonLinks([string]$Target) {
    $copies = New-Object 'System.Collections.Generic.List[string]'
    [void][IO.Directory]::CreateDirectory((Join-HarnessPath $Target '.claude'))
    foreach ($canon in @('skills', 'agents')) {
        $rel = ".claude/$canon"
        $link = Join-HarnessPath $Target $rel
        $canonDir = Join-HarnessPath $Target $canon
        if (Test-HarnessLink $link) {
            Remove-HarnessPath $link
        } elseif (Test-HarnessPresent $link) {
            Backup-HarnessPath $canonDir $link $rel
            Remove-HarnessPath $link
        }
        if (New-HarnessCanonLink $Target $canon) { $copies.Add($rel) }
    }
    return , $copies.ToArray()
}

# Make ./.claude/<canon> a junction onto ./<canon>; when a junction cannot be made, copy ./<canon>
# there instead and print both facts. Nothing may be at ./.claude/<canon>. $true when it is a copy.
function New-HarnessCanonLink([string]$Target, [string]$Canon) {
    $rel = ".claude/$Canon"
    $link = Join-HarnessPath $Target $rel
    $canonDir = Join-HarnessPath $Target $Canon
    $reason = 'the junction was not created'
    try {
        [void](New-Item -ItemType Junction -Path $link -Value $canonDir -ErrorAction Stop)
    } catch {
        $reason = $_.Exception.Message
    }
    if (Test-HarnessLink $link) { return $false }
    Remove-HarnessPath $link
    Copy-HarnessPath $canonDir $link
    Write-HarnessWarn "Could not create a junction at './$rel' ($reason)."
    Write-HarnessWarn "Copied './$Canon' to './$rel' instead. Re-run setup.ps1 after './$Canon' changes, or Claude Code reads an old copy."
    return $true
}

# ports ensure_gitignore_entry: add <entry> under a `# <reason>` comment unless the file already
# has that exact line. Idempotent: a second run adds nothing.
function Add-HarnessIgnoreEntry([string]$File, [string]$Entry, [string]$Reason) {
    $text = ''
    if (Test-HarnessFile $File) { $text = [IO.File]::ReadAllText($File) }
    foreach ($line in ($text -split "`r?`n")) {
        if ($line -ceq $Entry) { return }
    }
    $add = ''
    if ($text.Length -gt 0 -and -not $text.EndsWith("`n")) { $add = "`n" }
    $add += "`n# $Reason`n$Entry`n"
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($File))
    [IO.File]::AppendAllText($File, $add, $script:HarnessUtf8)
    Write-HarnessInfo "Added '$Entry' to $([IO.Path]::GetFileName($File)) ($Reason)."
}

# Keep git from storing the duplicated canon under .claude (a junction reads as a directory).
function Add-HarnessCanonExcludes([string]$Target) {
    $result = Invoke-HarnessNative 'git' @('-C', $Target, 'rev-parse', '--git-path', 'info/exclude')
    if ($result.ExitCode -ne 0 -or $result.Output.Length -eq 0) {
        Write-HarnessWarn "Could not find .git/info/exclude; git may list the files under .claude/skills and .claude/agents."
        return
    }
    $file = $result.Output[0].Trim()
    if (-not [IO.Path]::IsPathRooted($file)) { $file = Join-HarnessPath $Target $file }
    foreach ($canon in @('skills', 'agents')) {
        Add-HarnessIgnoreEntry $file "/.claude/$canon" "Easy Kit: .claude/$canon is a junction or a copy of ./$canon (setup.ps1)"
    }
}

# ports settings_merge_refused: say what to add by hand; the project's file is left as it was.
function Write-HarnessSettingsRefused([string]$Reason, [string]$Src) {
    Write-HarnessError "Could not merge Easy Kit hooks into ./.claude/settings.json: $Reason"
    Write-HarnessError "Nothing was written. Add the `"hooks`" entries below to ./.claude/settings.json by hand (keep your own entries), then re-run:"
    [Console]::Error.WriteLine([IO.File]::ReadAllText($Src))
}

# ports install_settings and merge_settings, then converts the kit hooks to the Windows exec form
# with lib/windows_hooks.py (T266). Both helpers run from the temp clone. Returns $false when the
# hooks were not wired (the caller finishes the rest and exits 2).
function Install-HarnessSettings([string]$Tmp, [string]$Target, $Python) {
    $src = Join-HarnessPath $Tmp '.claude/settings.json'
    $dst = Join-HarnessPath $Target '.claude/settings.json'
    if (-not (Test-HarnessFile $src)) {
        Write-HarnessWarn ".claude/settings.json not found in the fetched Easy Kit - hooks will not be wired."
        return $true
    }
    [void][IO.Directory]::CreateDirectory((Join-HarnessPath $Target '.claude'))
    if (Test-HarnessPresent $dst) {
        $merge = Join-HarnessPath $Tmp 'lib/merge-settings.py'
        if (-not (Test-HarnessFile $merge)) {
            Write-HarnessSettingsRefused 'the fetched Easy Kit has no lib/merge-settings.py' $src
            return $false
        }
        $result = Invoke-HarnessPython $Python @($merge, $src, $dst, $Target)
        foreach ($line in $result.Output) { [Console]::Error.WriteLine($line) }
        if ($result.ExitCode -ne 0) {
            Write-HarnessSettingsRefused 'the merge refused this file (reason above)' $src
            return $false
        }
        Write-HarnessInfo "Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept)."
    } else {
        Copy-HarnessPath $src $dst
        Write-HarnessInfo 'Installed .claude/settings.json (copy). Restart Claude Code to activate hooks.'
    }
    $convert = Join-HarnessPath $Tmp 'lib/windows_hooks.py'
    if (-not (Test-HarnessFile $convert)) {
        Write-HarnessError 'The fetched Easy Kit has no lib/windows_hooks.py, so the hooks keep their POSIX form and do not run on Windows.'
        return $false
    }
    $result = Invoke-HarnessPython $Python @($convert, $dst, $dst, '--launcher', $Python.Name)
    if ($result.ExitCode -ne 0) {
        foreach ($line in $result.Output) { [Console]::Error.WriteLine($line) }
        Write-HarnessError 'Could not convert the Easy Kit hooks in ./.claude/settings.json to the Windows form (reason above).'
        return $false
    }
    Write-HarnessInfo "Easy Kit hooks in ./.claude/settings.json run through '$($Python.Name)' (Windows form)."
    return $true
}

# Write <text> as UTF-8 without a BOM, with LF line endings, only when <path> is absent.
function Write-HarnessNewFile([string]$Path, [string]$Text) {
    if (Test-HarnessPresent $Path) { return }
    [IO.File]::WriteAllText($Path, $Text.Replace("`r`n", "`n"), $script:HarnessUtf8)
}

# ports scaffold_project: tasks/, memory/ and the four memory files, only when absent. The text is
# the same bytes setup.sh writes; {D} is an em dash and {LE} a less-than-or-equal sign, kept out of
# this file because Windows PowerShell 5.1 reads a script without a BOM as ANSI.
function New-HarnessScaffold([string]$Target) {
    $dash = [string][char]0x2014
    $le = [string][char]0x2264
    foreach ($dir in @('tasks', 'memory', 'memory/learning-records')) {
        [void][IO.Directory]::CreateDirectory((Join-HarnessPath $Target $dir))
    }
    $memory = @'
# MEMORY.md {D} Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 42,000 characters {D} a ratchet: `/compact-memory` may lower
> it, never raise it to fit growth. One-line summaries + links to cold files.
> Each spawn prompt carries a slice of these lines (craft-spawn-prompt's memory_slice.py) and this
> path to read in full only when the slice falls short; the whole file is not pasted.
> Updated by the Supervisor {D} prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

---

## Memory Architecture

- [decisions.md](decisions.md) {D} code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) {D} canonical biz domain terms and core domain models
- [learnings.md](learnings.md) {D} specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) {D} one-line summary.
     Target {LE}150 chars/entry. Advisory: reported by the size test, never enforced.
     The enforced gate is the 42,000-character whole-file budget above. -->

'@
    $decisions = @'
# decisions.md {D} Cold Tier: Architectural & Infrastructure Decisions

> **Rules**: Supervisor-only writes. Each entry: `### YYYY-MM-DD {D} Title`, then **Decision**, **Why**, and **Files** (cite paths {D} the diff-driven pass greps this file by changed file path).

## Architecture

## Infrastructure

'@
    $glossary = @'
# glossary.md {D} Cold Tier: Domain Terms & Domain Models

> **Rules**: Supervisor-only writes. One canonical definition per term {D} update in place, never duplicate. Domain Models section is populated at Stage 1 step 7 (Core Domain Models scan) and confirmed by the user.

## Domain Terms

## Domain Models

'@
    $learnings = @'
# learnings.md {D} Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

## Patterns

## Gotchas

'@
    $files = [ordered]@{
        'memory/MEMORY.md' = $memory
        'memory/decisions.md' = $decisions
        'memory/glossary.md' = $glossary
        'memory/learnings.md' = $learnings
    }
    foreach ($rel in $files.Keys) {
        $text = $files[$rel].Replace('{D}', $dash).Replace('{LE}', $le)
        Write-HarnessNewFile (Join-HarnessPath $Target $rel) $text
    }
    Write-HarnessNewFile (Join-HarnessPath $Target 'memory/learning-records/.gitkeep') ''
}

# ports lookup_lock_field: a top-level lock field, read before the "files" block; '' if absent.
function Read-HarnessLockField([string]$Lock, [string]$Field) {
    $text = [IO.File]::ReadAllText($Lock)
    $cut = $text.IndexOf('"files"')
    if ($cut -ge 0) { $text = $text.Substring(0, $cut) }
    $match = [regex]::Match($text, '"' + [regex]::Escape($Field) + '": "([^"]*)"')
    if ($match.Success) { return $match.Groups[1].Value }
    return ''
}

function ConvertTo-HarnessJsonString([string]$Text) {
    return $Text.Replace('\', '\\').Replace('"', '\"')
}

# ports write_harness_lock: one SHA-256 per installed file (MANIFEST directories expanded to their
# files, excluded paths left out, CLAUDE.md added), repo-relative '/' paths in byte order, in the
# same layout setup.sh writes, plus "canon_copies" when the canon links fell back to copies.
function Write-HarnessLock([string]$Target, [string]$Manifest, [string]$ClaudeSrc, [string]$KitCommit, [string[]]$CanonCopies) {
    $exclusions = Get-HarnessManifestExclusions $Manifest
    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
    foreach ($line in [IO.File]::ReadAllLines($Manifest)) {
        $rel = Get-HarnessManifestPath $line
        if (-not $rel) { continue }
        $path = Join-HarnessPath $Target $rel
        if (Test-HarnessDirectory $path) {
            $entries = Get-HarnessTreeEntries $path
            foreach ($key in $entries.Keys) {
                $full = "$rel/$key"
                if ($entries[$key] -eq 'file' -and -not (Test-HarnessExcluded $exclusions $full)) { [void]$set.Add($full) }
            }
        } elseif (Test-HarnessFile $path) {
            [void]$set.Add($rel)
        }
    }
    if (Test-HarnessFile (Join-HarnessPath $Target 'CLAUDE.md')) { [void]$set.Add('CLAUDE.md') }
    $entries = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
    foreach ($rel in $set) { $entries[$rel] = Get-HarnessFileHash (Join-HarnessPath $Target $rel) }
    Write-HarnessLockEntries $Target $ClaudeSrc $KitCommit $CanonCopies $entries
}

# ports write_new_lock (lib/harness-update.sh) and the layout of write_harness_lock: the given
# path -> hash entries in byte order. "claude_md_source" is left out when '' (still unresolved).
# Written through a temp file and a rename, so a failure keeps the old lock whole.
function Write-HarnessLockEntries([string]$Target, [string]$ClaudeSrc, [string]$KitCommit, [string[]]$CanonCopies, $Entries) {
    $files = New-Object 'string[]' $Entries.Count
    $Entries.Keys.CopyTo($files, 0)
    [Array]::Sort($files, [StringComparer]::Ordinal)

    $out = New-Object System.Text.StringBuilder
    [void]$out.Append("{`n")
    if ($ClaudeSrc) { [void]$out.Append('  "claude_md_source": "' + (ConvertTo-HarnessJsonString $ClaudeSrc) + "`",`n") }
    if ($KitCommit) { [void]$out.Append('  "kit_commit": "' + $KitCommit + "`",`n") }
    if ($CanonCopies.Length -gt 0) {
        $quoted = @($CanonCopies | ForEach-Object { '"' + (ConvertTo-HarnessJsonString $_) + '"' })
        [void]$out.Append('  "canon_copies": [' + ($quoted -join ', ') + "],`n")
    }
    [void]$out.Append("  `"files`": {`n")
    $lines = New-Object 'System.Collections.Generic.List[string]'
    foreach ($rel in $files) {
        $lines.Add('    "' + (ConvertTo-HarnessJsonString $rel) + '": "' + $Entries[$rel] + '"')
    }
    [void]$out.Append(($lines -join ",`n"))
    [void]$out.Append("`n  }`n}`n")
    $lock = Join-HarnessPath $Target '.claude/harness-lock.json'
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($lock))
    Write-HarnessBytesAtomic $lock ($script:HarnessUtf8.GetBytes($out.ToString()))
    Write-HarnessInfo "Wrote ./.claude/harness-lock.json ($($files.Length) file hashes)."
}

# Write <Bytes> to <Path> through a temp file in the same folder, then a rename: a failure leaves
# the old file whole. The temp file is removed if anything fails.
function Write-HarnessBytesAtomic([string]$Path, [byte[]]$Bytes) {
    $tmp = "$Path.easykit-" + [guid]::NewGuid().ToString('N').Substring(0, 8)
    try {
        [IO.File]::WriteAllBytes($tmp, $Bytes)
        if (Test-HarnessPresent $Path) {
            [IO.File]::Replace($tmp, $Path, [NullString]::Value)
        } else {
            [IO.File]::Move($tmp, $Path)
        }
    } finally {
        if (Test-HarnessPresent $tmp) { Remove-HarnessPath $tmp }
    }
}
