# lib/harness-update.ps1 - the Update action, and the Reinstall file step, of the PowerShell installer
# (T271, ADR-0003 decision 5).
#
# Dot-sourced by setup.ps1 after lib/harness.ps1, whose functions it uses. It defines functions only
# and does no work when it is loaded. Each function names the function in lib/harness-update.sh it
# ports; that file stays the source of truth for behaviour. Claude Code only: no Codex or Cursor
# re-projection (reproject_harnesses), no board mode.
#
# One rule differs from the shell, on purpose (T271 AC 5): when nobody can be asked about an edited
# file (no terminal, or -Yes), the user's file is kept, as the shell keeps it, and the kit's new copy
# is also written beside it as <file>.kit-new, so the user can merge by hand.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Set by setup.ps1: a terminal answers the questions; -Yes was given.
$script:HarnessInteractive = $false
$script:HarnessYes = $false
# ask | overwrite_all | keep_all (UPDATE_MODE). Only the menu in setup.ps1, at a terminal, sets it.
$script:HarnessUpdateMode = 'ask'
# What this run did to each file, for the update log (record_outcome): Kind, Path, Detail.
$script:HarnessOutcomes = New-Object 'System.Collections.Generic.List[object]'
$script:HarnessUnresolved = 0
$script:HarnessBackupFailed = 0
$script:HarnessDeletionAborted = $false
$script:HarnessLastInstalled = $false
# The step the run is on; setup.ps1 names it when the step fails (T271 AC 12).
$script:HarnessStep = ''
# T173: the first line of a CLAUDE.md installed before CLAUDE.md became the `@AGENTS.md` import.
$script:HarnessPreT173Heading = '# Claude Project Supervisor Guidelines'

# ports record_outcome
function Add-HarnessOutcome([string]$Kind, [string]$Path, [string]$Detail = '') {
    $script:HarnessOutcomes.Add([pscustomobject]@{ Kind = $Kind; Path = $Path; Detail = $Detail })
}

# Read one answer at the terminal; $null at the end of input.
function Read-HarnessAnswer([string]$Prompt) {
    try {
        return Read-Host -Prompt $Prompt
    } catch {
        return $null
    }
}

function New-HarnessMap {
    return , (New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal))
}

function New-HarnessSet {
    return , (New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal))
}

# ports extract_lock_pairs: the "files" block of the lock as path -> hash (the first entry wins,
# as lookup_lock_hash reads it). Every path is checked before the first write: a path that could
# leave the project stops the run with nothing changed.
function Read-HarnessLockFiles([string]$Lock) {
    $map = New-HarnessMap
    $text = [IO.File]::ReadAllText($Lock)
    $cut = $text.IndexOf('"files"')
    if ($cut -lt 0) { return , $map }
    foreach ($line in ($text.Substring($cut) -split "`r?`n")) {
        $match = [regex]::Match($line, '^\s*"([^"]+)"\s*:\s*"([0-9a-f]+)"\s*,?\s*$')
        if (-not $match.Success) { continue }
        $key = $match.Groups[1].Value
        if (-not (Test-HarnessSafeRel $key)) {
            Write-HarnessError "The lock entry '$key' in ./.claude/harness-lock.json is not a plain relative path inside the project. Nothing was changed. Remove that line from the lock, then re-run."
            throw $script:HarnessStop
        }
        if (-not $map.ContainsKey($key)) { $map[$key] = $match.Groups[2].Value }
    }
    return , $map
}

# The "canon_copies" field of the lock (written by setup.ps1 only): the canon paths that are copies.
function Read-HarnessLockCanonCopies([string]$Lock) {
    $found = New-Object 'System.Collections.Generic.List[string]'
    $text = [IO.File]::ReadAllText($Lock)
    $cut = $text.IndexOf('"files"')
    if ($cut -ge 0) { $text = $text.Substring(0, $cut) }
    $match = [regex]::Match($text, '"canon_copies"\s*:\s*\[([^\]]*)\]')
    if ($match.Success) {
        foreach ($item in [regex]::Matches($match.Groups[1].Value, '"([^"]*)"')) {
            $value = $item.Groups[1].Value
            if (@('.claude/skills', '.claude/agents') -ccontains $value) { $found.Add($value) }
        }
    }
    return , $found.ToArray()
}

# The MANIFEST paths (field 1), checked as Get-HarnessManifestPath checks them.
function Get-HarnessManifestRoots([string]$Manifest) {
    $roots = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in [IO.File]::ReadAllLines($Manifest)) {
        $rel = Get-HarnessManifestPath $line
        if ($rel) { $roots.Add($rel) }
    }
    return , $roots.ToArray()
}

# ports manifest_root_of: the MANIFEST path that covers <Rel>; '' when none does.
function Get-HarnessRootOf([string[]]$Roots, [string]$Rel) {
    foreach ($root in $Roots) {
        if (Test-HarnessUnder $Rel @($root)) { return $root }
    }
    return ''
}

# ports detect_symlinks: a MANIFEST path that is a link in the project is an old symlink-model
# install. Refuse before any write; never convert it.
function Assert-HarnessNoManifestLinks([string]$Target, [string]$Manifest) {
    $found = $false
    foreach ($rel in (Get-HarnessManifestRoots $Manifest)) {
        if (Test-HarnessLink (Join-HarnessPath $Target $rel)) {
            Write-HarnessError "MANIFEST path './$rel' is a link (old symlink-model install)."
            $found = $true
        }
    }
    if ($found) {
        Write-HarnessError 'This project was installed with the old symlink model. Easy Kit will not convert it.'
        Write-HarnessError 'To migrate: remove the linked path(s) above, then re-run setup.ps1 and choose Update - it restores them as real files.'
        throw $script:HarnessStop
    }
}

# Before any write: no folder above a kit file or a lock entry may be a link (a junction or a
# symbolic link), or a copy or a removal would act through it, outside the kit folder. Stops the run.
function Assert-HarnessNoLinkedParents([string]$Target, [string[]]$Rels) {
    $checked = New-HarnessSet
    foreach ($rel in $Rels) {
        $parts = $rel.Split([char]'/')
        $prefix = ''
        for ($i = 0; $i -lt $parts.Length - 1; $i++) {
            if ($prefix) { $prefix = "$prefix/$($parts[$i])" } else { $prefix = $parts[$i] }
            if (-not $checked.Add($prefix)) { continue }
            if (Test-HarnessLink (Join-HarnessPath $Target $prefix)) {
                Write-HarnessError "'./$prefix' is a link inside an Easy Kit folder; Easy Kit will not write or delete through it. Nothing was changed. Move the link away (or replace it with a real folder), then re-run."
                throw $script:HarnessStop
            }
        }
    }
}

# The lock entries under a current MANIFEST path: the only ones Update may write or remove.
function Get-HarnessKeysUnderRoots([string]$Manifest, $LockFiles) {
    $roots = Get-HarnessManifestRoots $Manifest
    $found = New-Object 'System.Collections.Generic.List[string]'
    foreach ($key in $LockFiles.Keys) {
        if (Get-HarnessRootOf $roots $key) { $found.Add($key) }
    }
    return , $found.ToArray()
}

# ports build_fresh_file_list: every kit file under the MANIFEST paths, as a repo-relative '/'
# path. A directory is expanded to its files in byte order; a link is skipped (`find -type f`);
# a `!` exclusion is left out. Every path is checked before the first write.
function Get-HarnessFreshFiles([string]$Tmp, [string]$Manifest) {
    $exclusions = Get-HarnessManifestExclusions $Manifest
    $list = New-Object 'System.Collections.Generic.List[string]'
    $seen = New-HarnessSet
    foreach ($rel in (Get-HarnessManifestRoots $Manifest)) {
        $src = Join-HarnessPath $Tmp $rel
        if (Test-HarnessDirectory $src) {
            $entries = Get-HarnessTreeEntries $src
            $keys = New-Object 'string[]' $entries.Count
            $entries.Keys.CopyTo($keys, 0)
            [Array]::Sort($keys, [StringComparer]::Ordinal)
            foreach ($key in $keys) {
                if ($entries[$key] -ne 'file') { continue }
                $full = "$rel/$key"
                if (Test-HarnessExcluded $exclusions $full) { continue }
                Assert-HarnessSafeRel $full 'Kit file'
                if ($seen.Add($full)) { $list.Add($full) }
            }
        } elseif (Test-HarnessFile $src) {
            if ($seen.Add($rel)) { $list.Add($rel) }
        } else {
            Write-HarnessWarn "MANIFEST entry '$rel' not found in the fetched kit - skipping."
        }
    }
    return , $list.ToArray()
}

# The SHA-256 of a plain file; '' for anything else (absent, a directory, a link).
function Get-HarnessCurrentHash([string]$Path) {
    if (Test-HarnessFile $Path) { return Get-HarnessFileHash $Path }
    return ''
}

# ports install_file: put the kit's copy at <Dst>, creating its parent folders. A read-only or
# locked <Dst> makes this throw; the run then stops and setup.ps1 names the step.
function Install-HarnessUpdateFile([string]$Src, [string]$Dst) {
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Dst))
    [IO.File]::Copy($Src, $Dst, $true)
}

# ports `diff -u` in prompt_conflict: git's diff of two files, shown at the terminal.
function Show-HarnessDiff([string]$Current, [string]$Fresh) {
    $result = Invoke-HarnessNative 'git' @('diff', '--no-index', '--no-color', '--', $Current, $Fresh)
    foreach ($line in $result.Output) { Write-Host $line }
}

# ports prompt_conflict: 'o' overwrite (your file is backed up first), 's' keep, or 'new' when
# nobody can be asked (no terminal, -Yes, end of input): keep, and write the kit's copy beside it.
function Read-HarnessConflict([string]$Current, [string]$Fresh) {
    if (-not $script:HarnessInteractive) { return 'new' }
    if ($script:HarnessUpdateMode -eq 'overwrite_all') { return 'o' }
    if ($script:HarnessUpdateMode -eq 'keep_all') { return 's' }
    Show-HarnessDiff $Current $Fresh
    while ($true) {
        $answer = Read-HarnessAnswer '  Resolve: [o]verwrite / [s]kip / [v]iew diff again'
        if ($null -eq $answer) { return 'new' }
        $answer = $answer.Trim()
        if (@('o', 'overwrite') -contains $answer) { return 'o' }
        if (@('s', 'skip') -contains $answer) { return 's' }
        if (@('v', 'view') -contains $answer) {
            Show-HarnessDiff $Current $Fresh
            continue
        }
        Write-Host '  Please enter o, s, or v.'
    }
}

# ports process_one_file: compare one kit file with the project's copy and the lock, act, and
# record the hash for the new lock in <Decisions> (none: the entry is dropped).
#   absent                         -> added
#   unedited since install, or already equal to the kit's copy -> refreshed (copied only if it differs)
#   edited, and the kit did not change it                      -> kept (T271 AC 2; the shell asks)
#   edited (or <Force>: the source of CLAUDE.md is unknown)    -> Read-HarnessConflict
function Update-HarnessFile([string]$Src, [string]$Dst, [string]$Rel, $LockFiles, $Decisions, $Processed, [bool]$Force = $false) {
    $script:HarnessStep = "updating './$Rel'"
    $script:HarnessLastInstalled = $false
    [void]$Processed.Add($Rel)
    $fresh = Get-HarnessFileHash $Src
    $recorded = ''
    if ($LockFiles.ContainsKey($Rel)) { $recorded = $LockFiles[$Rel] }

    if (-not (Test-HarnessPresent $Dst)) {
        Install-HarnessUpdateFile $Src $Dst
        $script:HarnessLastInstalled = $true
        $Decisions[$Rel] = $fresh
        Add-HarnessOutcome 'added' $Rel
        Write-HarnessInfo "new file installed: $Rel"
        return
    }
    $current = Get-HarnessCurrentHash $Dst
    if (-not $Force -and $current -and (($recorded -and $current -eq $recorded) -or $current -eq $fresh)) {
        if ($current -ne $fresh) { Install-HarnessUpdateFile $Src $Dst }
        $script:HarnessLastInstalled = $true
        $Decisions[$Rel] = $fresh
        Add-HarnessOutcome 'refreshed' $Rel
        return
    }
    if (-not $Force -and $recorded -and $recorded -eq $fresh) {
        $Decisions[$Rel] = $recorded
        Add-HarnessOutcome 'kept' $Rel
        Write-HarnessInfo "kept: $Rel (you edited it; the kit did not change it)"
        return
    }

    if ($recorded) {
        Write-HarnessWarn "conflict: '$Rel' has local changes since install"
    } else {
        Write-HarnessWarn "conflict: '$Rel' is not recorded in the lock and differs from upstream"
    }
    $decision = Read-HarnessConflict $Dst $Src
    if ($decision -eq 'o') {
        $to = Get-HarnessBackupName $Dst
        $shown = $Rel + $to.Substring($Dst.Length)
        try {
            Backup-HarnessPath $Src $Dst $Rel
        } catch {
            if ("$_" -ne $script:HarnessStop) { Write-HarnessError "Could not back up './$Rel': $($_.Exception.Message)" }
            $script:HarnessBackupFailed += 1
            if ($recorded) { $Decisions[$Rel] = $recorded }
            Add-HarnessOutcome 'backup_failed' $Rel "could not move it to $shown"
            return
        }
        Install-HarnessUpdateFile $Src $Dst
        $script:HarnessLastInstalled = $true
        $Decisions[$Rel] = $fresh
        if (Test-HarnessPresent $to) {
            Add-HarnessOutcome 'overwrote' $Rel $shown
        } else {
            Add-HarnessOutcome 'refreshed' $Rel
        }
        Write-HarnessInfo "overwrote: $Rel"
        return
    }
    if ($recorded) { $Decisions[$Rel] = $recorded }
    Add-HarnessOutcome 'kept' $Rel
    if ($decision -eq 's') {
        Write-HarnessInfo "skipped: $Rel (kept your local version)"
        return
    }
    # Nobody to ask: keep the user's file and put the kit's copy beside it. An older <file>.kit-new
    # that differs is moved to a backup first, never overwritten.
    $script:HarnessUnresolved += 1
    $kitNew = "$Dst.kit-new"
    if ((Get-HarnessCurrentHash $kitNew) -ne $fresh) {
        Backup-HarnessPath $Src $kitNew "$Rel.kit-new"
        Install-HarnessUpdateFile $Src $kitNew
    }
    Write-HarnessWarn "kept your './$Rel' as it is; the kit's new copy is in './$Rel.kit-new' - compare and merge by hand, then delete it."
}

# The first line of a file, without its line ending; '' when there is none.
function Get-HarnessFirstLine([string]$Path) {
    if (-not (Test-HarnessFile $Path)) { return '' }
    $reader = [IO.File]::OpenText($Path)
    try {
        $line = $reader.ReadLine()
    } finally {
        $reader.Dispose()
    }
    if ($null -eq $line) { return '' }
    return $line
}

# ports resolve_claude_md_source: 'CLAUDE.md', 'CLAUDE_LEGACY.md', or 'conflict' when neither or
# both candidates match the first line of the project's CLAUDE.md. Never a guess.
function Resolve-HarnessClaudeSource([string]$Lock, [string]$Tmp, [string]$Dst) {
    $recorded = Read-HarnessLockField $Lock 'claude_md_source'
    if ($recorded) {
        if (@('CLAUDE.md', 'CLAUDE_LEGACY.md') -ccontains $recorded) { return $recorded }
        Write-HarnessWarn "recorded claude_md_source '$recorded' is not an allowed value (CLAUDE.md or CLAUDE_LEGACY.md) - falling back to heading inference."
    }
    if (-not (Test-HarnessPresent $Dst)) { return 'CLAUDE.md' }
    $first = Get-HarnessFirstLine $Dst
    $match = ''
    foreach ($candidate in @('CLAUDE.md', 'CLAUDE_LEGACY.md')) {
        $path = Join-HarnessPath $Tmp $candidate
        if (-not (Test-HarnessFile $path)) { continue }
        $candidateFirst = Get-HarnessFirstLine $path
        if ($candidate -eq 'CLAUDE.md' -and $first -ceq $script:HarnessPreT173Heading) { $candidateFirst = $first }
        if ($first -ceq $candidateFirst) {
            if ($match) { return 'conflict' }
            $match = $candidate
        }
    }
    if ($match) { return $match }
    return 'conflict'
}

# ports process_claude_md: CLAUDE.md goes through Update-HarnessFile like every kit file. Returns
# the claude_md_source for the new lock: '' while it is still unresolved.
function Update-HarnessClaude([string]$Tmp, [string]$Target, [string]$Lock, $LockFiles, $Decisions, $Processed) {
    $dst = Join-HarnessPath $Target 'CLAUDE.md'
    $source = Resolve-HarnessClaudeSource $Lock $Tmp $dst
    if ($source -eq 'conflict') {
        Write-HarnessWarn "conflict: 'CLAUDE.md' install source could not be determined from its first line - treating as customized."
        Update-HarnessFile (Join-HarnessPath $Tmp 'CLAUDE.md') $dst 'CLAUDE.md' $LockFiles $Decisions $Processed $true
        if ($script:HarnessLastInstalled) { return 'CLAUDE.md' }
        return ''
    }
    $src = Join-HarnessPath $Tmp $source
    if (-not (Test-HarnessFile $src)) {
        Write-HarnessError "CLAUDE.md source '$source' not found in the fetched Easy Kit - leaving your CLAUDE.md untouched."
        return $source
    }
    Update-HarnessFile $src $dst 'CLAUDE.md' $LockFiles $Decisions $Processed
    return $source
}

# ports deletion_is_safe: removals run only when the fetched kit looks whole (a non-empty file
# list, and every MANIFEST path present).
function Test-HarnessDeletionSafe([string]$Tmp, [string[]]$Roots, [string[]]$Fresh) {
    if ($Fresh.Length -eq 0) { return $false }
    foreach ($root in $Roots) {
        if (-not (Test-HarnessPresent (Join-HarnessPath $Tmp $root))) { return $false }
    }
    return $true
}

function Get-HarnessParentRel([string]$Rel) {
    $i = $Rel.LastIndexOf('/')
    if ($i -lt 0) { return '' }
    return $Rel.Substring(0, $i)
}

# ports prune_empty_dirs: remove the now-empty folders above <Rel>, up to (not including) <Root>.
function Remove-HarnessEmptyParents([string]$Target, [string]$Rel, [string]$Root) {
    $dir = Get-HarnessParentRel $Rel
    while ($dir -and $dir -cne $Root) {
        $full = Join-HarnessPath $Target $dir
        if (-not (Test-HarnessDirectory $full)) { break }
        if (@((New-Object IO.DirectoryInfo $full).GetFileSystemInfos()).Length -gt 0) { break }
        [IO.Directory]::Delete($full, $false)
        $dir = Get-HarnessParentRel $dir
    }
}

# The unit a removal is reported as: the top folder under the MANIFEST path (a skill), or the
# file itself when it sits directly in it.
function Get-HarnessRemovalUnit([string]$Rel, [string]$Root) {
    if ($Rel -ceq $Root) { return $Rel }
    $rest = $Rel.Substring($Root.Length + 1)
    $i = $rest.IndexOf('/')
    if ($i -ge 0) { return "$Root/" + $rest.Substring(0, $i) }
    return $Rel
}

# ports carry_over_unprocessed: every lock entry this run did not process. Outside the MANIFEST:
# kept in the lock, untouched. Under it: an unedited file is removed (its empty folders pruned)
# and dropped; an edited one is kept, named, and kept in the lock; a gone one is dropped. Only
# paths the lock records are ever removed, and only as plain files (never a link, never a folder
# with content).
function Update-HarnessUnshipped([string]$Tmp, [string]$Target, [string]$Manifest, [string[]]$Fresh, $LockFiles, $Decisions, $Processed) {
    $roots = Get-HarnessManifestRoots $Manifest
    $canDelete = Test-HarnessDeletionSafe $Tmp $roots $Fresh
    if (-not $canDelete) {
        $script:HarnessDeletionAborted = $true
        Write-HarnessError 'The fetched upstream looks incomplete (empty file list or a MANIFEST path missing) - nothing was removed. Re-run once the upstream is whole.'
    }
    $units = New-HarnessSet
    # A case-only rename by the kit: on NTFS both names are one file, just refreshed. Never remove
    # it; drop the old key (review P2-1).
    $processedAnyCase = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($rel in $Processed) { [void]$processedAnyCase.Add($rel) }
    foreach ($key in @($LockFiles.Keys)) {
        if ($Processed.Contains($key)) { continue }
        if ($processedAnyCase.Contains($key)) {
            Write-HarnessInfo "kept '$key': the kit now ships it under another letter case (a case-only rename)."
            continue
        }
        $hash = $LockFiles[$key]
        $root = Get-HarnessRootOf $roots $key
        if (-not $root -or -not $canDelete) {
            $Decisions[$key] = $hash
            continue
        }
        $path = Join-HarnessPath $Target $key
        if (-not (Test-HarnessPresent $path)) { continue }
        $script:HarnessStep = "removing './$key'"
        if ((Get-HarnessCurrentHash $path) -eq $hash) {
            Remove-HarnessPath $path
            Remove-HarnessEmptyParents $Target $key $root
            $unit = Get-HarnessRemovalUnit $key $root
            if ($units.Add($unit)) {
                Add-HarnessOutcome 'removed' $unit
                Write-HarnessInfo "removed '$unit' - upstream no longer ships it and you never edited it."
            }
        } else {
            $Decisions[$key] = $hash
            Add-HarnessOutcome 'kept_unshipped' $key
            Write-HarnessWarn "upstream no longer ships '$key' - you edited it, so it is kept (delete it yourself if you no longer want it)."
        }
    }
}

# ports plan_removals: the same classification, read-only. Remove holds units, Keep holds files.
function Get-HarnessRemovalPlan([string]$Tmp, [string]$Target, [string]$Manifest, [string[]]$Fresh, $LockFiles) {
    $roots = Get-HarnessManifestRoots $Manifest
    $freshSet = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($rel in $Fresh) { [void]$freshSet.Add($rel) }
    $remove = New-Object 'System.Collections.Generic.List[string]'
    $keep = New-Object 'System.Collections.Generic.List[string]'
    foreach ($key in @($LockFiles.Keys)) {
        if ($key -ceq 'CLAUDE.md' -or $freshSet.Contains($key)) { continue }
        $root = Get-HarnessRootOf $roots $key
        if (-not $root) { continue }
        $path = Join-HarnessPath $Target $key
        if (-not (Test-HarnessPresent $path)) { continue }
        if ((Get-HarnessCurrentHash $path) -eq $LockFiles[$key]) {
            $unit = Get-HarnessRemovalUnit $key $root
            if (-not $remove.Contains($unit)) { $remove.Add($unit) }
        } else {
            $keep.Add($key)
        }
    }
    return [pscustomobject]@{
        Safe = (Test-HarnessDeletionSafe $Tmp $roots $Fresh)
        Remove = $remove.ToArray()
        Keep = $keep.ToArray()
    }
}

# ports plan_list
function Write-HarnessPlanList([string[]]$Items, [string]$Empty) {
    if ($Items.Length -eq 0) {
        Write-Host "      $Empty"
        return
    }
    foreach ($item in $Items) { Write-Host "      $item" }
}

# ports plan_print_removals
function Write-HarnessRemovalPlan($Plan) {
    if ($Plan.Safe) {
        Write-Host '  - Upstream no longer ships these and you never edited them; they will be removed:'
        Write-HarnessPlanList $Plan.Remove '(none)'
    } else {
        Write-Host '  - Removals skipped: the fetched upstream looks incomplete, so nothing will be removed.'
    }
    Write-Host '  - Upstream no longer ships these, but you edited them; they will be kept:'
    Write-HarnessPlanList $Plan.Keep '(none)'
}

# ports plan_update_asks: would Update stop at this file? Not when it is unedited since install,
# already equal to the kit's copy, or unchanged by the kit (kept). <Force>: the source of
# CLAUDE.md is unknown.
function Test-HarnessUpdateAsks([string]$Src, [string]$Dst, [string]$Rel, $LockFiles, [bool]$Force = $false) {
    if ($Force) { return $true }
    $current = Get-HarnessCurrentHash $Dst
    if (-not $current) { return $true }
    $fresh = Get-HarnessFileHash $Src
    if ($LockFiles.ContainsKey($Rel) -and ($current -eq $LockFiles[$Rel] -or $fresh -eq $LockFiles[$Rel])) { return $false }
    return $current -ne $fresh
}

# ports plan_update: the screen names the files the run then acts on (same rules, read-only).
# Returns the number of edited files the run will stop at.
function Write-HarnessUpdatePlan([string]$Tmp, [string]$Target, [string]$Lock, [string]$Manifest, [string[]]$Fresh, $LockFiles) {
    $asks = New-Object 'System.Collections.Generic.List[string]'
    $new = 0
    foreach ($rel in $Fresh) {
        $dst = Join-HarnessPath $Target $rel
        if (-not (Test-HarnessPresent $dst)) {
            $new += 1
        } elseif (Test-HarnessUpdateAsks (Join-HarnessPath $Tmp $rel) $dst $rel $LockFiles) {
            $asks.Add($rel)
        }
    }
    $claudeDst = Join-HarnessPath $Target 'CLAUDE.md'
    $source = Resolve-HarnessClaudeSource $Lock $Tmp $claudeDst
    if (-not (Test-HarnessPresent $claudeDst)) {
        $new += 1
    } elseif ($source -eq 'conflict') {
        $asks.Add('CLAUDE.md')
    } elseif ((Test-HarnessFile (Join-HarnessPath $Tmp $source)) -and
            (Test-HarnessUpdateAsks (Join-HarnessPath $Tmp $source) $claudeDst 'CLAUDE.md' $LockFiles)) {
        $asks.Add('CLAUDE.md')
    }
    $removals = Get-HarnessRemovalPlan $Tmp $Target $Manifest $Fresh $LockFiles

    Write-Host ''
    Write-Host "Plan: Update Easy Kit in $Target (keeps your edits)"
    Write-Host '  - Kit files you never edited are refreshed from upstream.'
    Write-Host "  - Files to add or restore: $new"
    if ($script:HarnessInteractive) {
        Write-Host '  - You edited these; next you choose: ask about each one, overwrite all, or keep all.'
        Write-Host "    Overwriting moves your version to <file>.$(Get-HarnessBackupSuffix) first:"
    } else {
        Write-Host "  - You edited these; they are kept as they are, and the kit's new copy is written beside each as <file>.kit-new:"
    }
    Write-HarnessPlanList $asks.ToArray() '(none)'
    Write-HarnessRemovalPlan $removals
    if ($script:HarnessInteractive) {
        Write-Host '  - Backed up: only a file you choose to overwrite. Keeping it leaves your edit in place.'
    } else {
        Write-Host '  - Backed up: nothing. Update keeps your edits in place instead.'
    }
    Write-Host '  - Links: a junction at .claude/skills or .claude/agents is left as it is; a copy there is refreshed from ./skills or ./agents unless you changed it.'
    Write-Host '  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept), then turned into the Windows form.'
    return $asks.Count
}

# ports reinstall_needs_backup: move this path aside before the kit's copy goes in? Yes for
# anything that is not a plain file, and for a file that differs from both the kit and the lock.
function Test-HarnessReinstallBackup([string]$Src, [string]$Dst, [string]$Rel, $LockFiles) {
    if (-not (Test-HarnessPresent $Dst)) { return $false }
    if (-not (Test-HarnessFile $Dst)) { return $true }
    $current = Get-HarnessFileHash $Dst
    if ($current -eq (Get-HarnessFileHash $Src)) { return $false }
    if ($LockFiles.ContainsKey($Rel) -and $current -eq $LockFiles[$Rel]) { return $false }
    return $true
}

# ports plan_reinstall. Returns the exact list of paths the run moves aside, and no others.
function Write-HarnessReinstallPlan([string]$Tmp, [string]$Target, [string]$Manifest, [string[]]$Fresh, $LockFiles, [string]$ClaudeSrc, $Python) {
    $backups = New-Object 'System.Collections.Generic.List[string]'
    foreach ($rel in $Fresh) {
        if (Test-HarnessReinstallBackup (Join-HarnessPath $Tmp $rel) (Join-HarnessPath $Target $rel) $rel $LockFiles) { $backups.Add($rel) }
    }
    if (Test-HarnessReinstallBackup (Join-HarnessPath $Tmp $ClaudeSrc) (Join-HarnessPath $Target 'CLAUDE.md') 'CLAUDE.md' $LockFiles) {
        $backups.Add('CLAUDE.md')
    }
    $removals = Get-HarnessRemovalPlan $Tmp $Target $Manifest $Fresh $LockFiles
    $type = 'New project (CLAUDE.md)'
    if ($ClaudeSrc -eq 'CLAUDE_LEGACY.md') { $type = 'Existing / legacy project (CLAUDE_LEGACY.md)' }
    $launcher = (@($Python.Name) + @($Python.Prefix)) -join ' '

    Write-Host ''
    Write-Host "Plan: Reinstall Easy Kit in $Target (backs up your edits)"
    Write-Host '  - Every kit file is replaced with a fresh copy, and the lock is rewritten.'
    Write-Host '  - CLI: Claude Code'
    Write-Host "  - Project type: $type"
    Write-Host "  - Your edited files are moved to <file>.$(Get-HarnessBackupSuffix) first:"
    Write-HarnessPlanList $backups.ToArray() '(none: no file the kit ships now has been edited)'
    Write-HarnessRemovalPlan $removals
    Write-Host '  - Your own files that the kit does not ship are left alone.'
    Write-Host '  - Links: .claude/skills and .claude/agents point at ./skills and ./agents (a junction, or a copy when a junction cannot be made).'
    Write-Host "  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept); they run through '$launcher'."
    return , $backups.ToArray()
}

# ports run_reinstall (the file part): move aside exactly the planned paths, copy every kit file in,
# apply the removal rule of Update, and return the entries for the new lock: the kit's files plus
# what the removal rule keeps, never a disk scan (a user's own file is not recorded as the kit's).
function Invoke-HarnessReinstallFiles([string]$Tmp, [string]$Target, [string]$Manifest, [string[]]$Fresh, $LockFiles, [string[]]$Backups, [string]$ClaudeSrc) {
    $decisions = New-HarnessMap
    $processed = New-HarnessSet
    $backupSet = New-HarnessSet
    foreach ($rel in $Backups) { [void]$backupSet.Add($rel) }
    foreach ($rel in (@($Fresh) + @('CLAUDE.md'))) {
        [void]$processed.Add($rel)
        $src = Join-HarnessPath $Tmp $rel
        if ($rel -ceq 'CLAUDE.md') { $src = Join-HarnessPath $Tmp $ClaudeSrc }
        if (-not (Test-HarnessFile $src)) { continue }
        $dst = Join-HarnessPath $Target $rel
        $script:HarnessStep = "installing './$rel'"
        if ($backupSet.Contains($rel)) { Backup-HarnessPath $src $dst $rel }
        Install-HarnessUpdateFile $src $dst
        $decisions[$rel] = Get-HarnessFileHash $src
    }
    Update-HarnessUnshipped $Tmp $Target $Manifest $Fresh $LockFiles $decisions $processed
    return , $decisions
}

# Reinstall: remove each canon copy the lock records and the user did not change (no drift), so
# Install-HarnessCanonLinks makes it again with no backup. A changed copy stays, and is backed up.
function Clear-HarnessCanonCopies([string]$Target, [string[]]$Copies, $Drift) {
    foreach ($rel in $Copies) {
        $path = Join-HarnessPath $Target $rel
        if (-not (Test-HarnessDirectory $path)) { continue }
        if ($Drift.ContainsKey($rel) -and @($Drift[$rel]).Length -gt 0) { continue }
        Remove-HarnessPath $path
    }
}

# ADR-0003 decision 5, before the files change: for each canon copy the lock records, the files in
# it that differ both from the lock and from ./<canon> (the user changed the copy). An empty list
# means the copy is still what Easy Kit put there.
function Get-HarnessCanonDrift([string]$Target, [string[]]$Copies, $LockFiles) {
    $drift = @{}
    foreach ($rel in $Copies) {
        $canon = $rel.Substring('.claude/'.Length)
        $copyDir = Join-HarnessPath $Target $rel
        $canonDir = Join-HarnessPath $Target $canon
        $changed = New-Object 'System.Collections.Generic.List[string]'
        if (Test-HarnessDirectory $copyDir) {
            $entries = Get-HarnessTreeEntries $copyDir
            foreach ($key in $entries.Keys) {
                if ($entries[$key] -eq 'dir') { continue }
                if ($entries[$key] -eq 'link') {
                    $changed.Add("$rel/$key")
                    continue
                }
                $hash = Get-HarnessFileHash (Join-HarnessPath $copyDir $key)
                $lockKey = "$canon/$key"
                if ($LockFiles.ContainsKey($lockKey) -and $LockFiles[$lockKey] -eq $hash) { continue }
                if ((Get-HarnessCurrentHash (Join-HarnessPath $canonDir $key)) -eq $hash) { continue }
                $changed.Add("$rel/$key")
            }
        }
        $drift[$rel] = $changed.ToArray()
    }
    return $drift
}

# Does the link at <Link> point at <Expected>? (A junction's target is an absolute path, so it goes
# stale when the project folder moves.)
function Test-HarnessLinkTarget([string]$Link, [string]$Expected) {
    try {
        $target = @((Get-Item -LiteralPath $Link -Force).Target)[0]
    } catch {
        return $false
    }
    if (-not $target) { return $false }
    if (-not [IO.Path]::IsPathRooted($target)) { $target = [IO.Path]::Combine([IO.Path]::GetDirectoryName($Link), $target) }
    $a = [IO.Path]::GetFullPath($target).TrimEnd([char[]]@('\', '/'))
    $b = [IO.Path]::GetFullPath($Expected).TrimEnd([char[]]@('\', '/'))
    return [string]::Equals($a, $b, [StringComparison]::OrdinalIgnoreCase)
}

# ADR-0003 decision 5, on Update (the part of reproject_harnesses Claude Code needs): a junction
# onto ./<canon> is left as it is - it already shows the updated files - and made again when it
# points elsewhere. A copy the lock records is refreshed from ./<canon>, unless <Drift> names files
# the user changed in it: then it is kept and they are named. A missing one is made as at install.
# Returns the canon paths that are copies now (the new lock's canon_copies).
function Update-HarnessCanonLinks([string]$Target, [string[]]$Copies, $Drift) {
    $now = New-Object 'System.Collections.Generic.List[string]'
    [void][IO.Directory]::CreateDirectory((Join-HarnessPath $Target '.claude'))
    foreach ($canon in @('skills', 'agents')) {
        $rel = ".claude/$canon"
        $link = Join-HarnessPath $Target $rel
        $canonDir = Join-HarnessPath $Target $canon
        $script:HarnessStep = "refreshing './$rel'"
        if (Test-HarnessLink $link) {
            if (Test-HarnessLinkTarget $link $canonDir) { continue }
            Write-HarnessWarn "'./$rel' does not point at './$canon' (was the project folder moved?) - re-making it."
            Remove-HarnessPath $link
            if (New-HarnessCanonLink $Target $canon) { $now.Add($rel) }
            continue
        }
        if (-not (Test-HarnessPresent $link)) {
            if (New-HarnessCanonLink $Target $canon) { $now.Add($rel) }
            continue
        }
        if (($Copies -ccontains $rel) -and (Test-HarnessDirectory $link)) {
            $now.Add($rel)
            $changed = @()
            if ($Drift.ContainsKey($rel)) { $changed = @($Drift[$rel]) }
            if ($changed.Length -gt 0) {
                Write-HarnessWarn "Kept './$rel' as it is: it is a copy of './$canon', and you changed these files in it: $($changed -join ', '). Copy your changes into './$canon', delete './$rel', then re-run update.ps1."
                continue
            }
            if (Test-HarnessSameContent $canonDir $link) { continue }
            # Stage the new copy, rename the old one aside, swap; the old copy is removed only after
            # the swap, and put back if the swap fails (review P3-2).
            $id = [guid]::NewGuid().ToString('N').Substring(0, 8)
            $stage = "$link.easykit-$id"
            $aside = "$link.easykit-old-$id"
            try {
                Copy-HarnessPath $canonDir $stage
                Move-HarnessItem $link $aside
            } catch {
                Remove-HarnessPath $stage
                throw
            }
            try {
                Move-HarnessItem $stage $link
            } catch {
                Move-HarnessItem $aside $link
                Remove-HarnessPath $stage
                throw
            }
            try {
                Remove-HarnessPath $aside
            } catch {
                Write-HarnessWarn "Could not remove the old copy '$aside' ($($_.Exception.Message)); delete it by hand."
            }
            Write-HarnessInfo "Refreshed './$rel' (a copy of './$canon')."
            continue
        }
        Write-HarnessWarn "'./$rel' is neither a junction nor a copy Easy Kit recorded - left as it is. Run setup.ps1 and choose Reinstall to link it again."
    }
    return , $now.ToArray()
}

# ports update_decided_by
function Get-HarnessDecidedBy([int]$Asks) {
    if ($Asks -eq 0) { return 'no edited files' }
    if (-not $script:HarnessInteractive) {
        if ($script:HarnessYes) { return '-Yes (kept edits)' }
        return 'no terminal (kept edits)'
    }
    if ($script:HarnessUpdateMode -eq 'overwrite_all') { return 'auto-approve (overwrite all)' }
    if ($script:HarnessUpdateMode -eq 'keep_all') { return 'auto-approve (keep all)' }
    return 'asked per file'
}

# ports render_update_log_entry: paths, outcomes and counts only, never contents. The em dash and
# the arrow are built from their code points: this file stays ASCII for Windows PowerShell 5.1.
function Get-HarnessUpdateLogEntry([int]$Asks, [string]$KitCommit) {
    $dash = [string][char]0x2014
    $arrow = [string][char]0x2192
    $old = $script:HarnessPrevCommit
    if ($old -cnotmatch '^[0-9a-f]+$') { $old = 'unknown' }
    $new = $KitCommit
    if (-not $new) { $new = 'unknown' }
    $lines = New-Object 'System.Collections.Generic.List[string]'
    $lines.Add("## $(Get-Date -Format 'yyyy-MM-dd HH:mm') $dash Update $old $arrow $new")
    $lines.Add("Decided by: $(Get-HarnessDecidedBy $Asks)")
    $refreshed = 0
    $added = 0
    foreach ($outcome in $script:HarnessOutcomes) {
        $path = $outcome.Path
        switch -CaseSensitive ($outcome.Kind) {
            'overwrote' { $lines.Add("- $path $dash overwrote (your edits; backup $($outcome.Detail))") }
            'kept' { $lines.Add("- $path $dash kept your version") }
            'backup_failed' { $lines.Add("- $path $dash kept (backup failed: $($outcome.Detail))") }
            'removed' { $lines.Add("- $path $dash removed (upstream no longer ships it)") }
            'kept_unshipped' { $lines.Add("- $path $dash kept (you edited it; upstream no longer ships it)") }
            'refreshed' { $refreshed += 1 }
            'added' { $added += 1 }
        }
    }
    $lines.Add("- $refreshed kit files you never edited $dash refreshed")
    $lines.Add("- $added files added")
    return ($lines -join "`n") + "`n"
}

# ports write_update_log: prepend the entry to ./.claude/update-log.md (UTF-8, LF, the older
# entries kept byte for byte). A failure warns and never changes the outcome of the update; a link
# or a folder at that path is refused, so nothing is written through it.
function Write-HarnessUpdateLog([string]$Target, [string]$Entry) {
    $log = Join-HarnessPath $Target '.claude/update-log.md'
    if ((Test-HarnessPresent $log) -and -not (Test-HarnessFile $log)) {
        Write-HarnessWarn './.claude/update-log.md is not a plain file - this run was not added to the update log.'
        return
    }
    try {
        $entryBytes = $script:HarnessUtf8.GetBytes($Entry)
        $stream = New-Object IO.MemoryStream
        try {
            $stream.Write($entryBytes, 0, $entryBytes.Length)
            if (Test-HarnessFile $log) {
                $older = [IO.File]::ReadAllBytes($log)
                $stream.WriteByte(10)
                $stream.Write($older, 0, $older.Length)
            }
            $bytes = $stream.ToArray()
        } finally {
            $stream.Dispose()
        }
        Write-HarnessBytesAtomic $log $bytes
        Write-HarnessInfo 'Recorded this run in ./.claude/update-log.md.'
    } catch {
        Write-HarnessWarn "Could not write ./.claude/update-log.md - this run was not added to the update log. ($($_.Exception.Message))"
    }
}

# ports run_update (up to the settings step, which setup.ps1 runs next): every kit file, CLAUDE.md,
# what the kit stopped shipping, then the canon links. Returns the new lock's parts; setup.ps1
# writes the lock after the settings step, so any failure before it keeps the old lock.
function Invoke-HarnessUpdateFiles([string]$Tmp, [string]$Target, [string]$Lock, [string]$Manifest, [string[]]$Fresh, $LockFiles) {
    $decisions = New-HarnessMap
    $processed = New-HarnessSet
    $copies = Read-HarnessLockCanonCopies $Lock
    $drift = Get-HarnessCanonDrift $Target $copies $LockFiles
    foreach ($rel in $Fresh) {
        Update-HarnessFile (Join-HarnessPath $Tmp $rel) (Join-HarnessPath $Target $rel) $rel $LockFiles $decisions $processed
    }
    $claudeSource = Update-HarnessClaude $Tmp $Target $Lock $LockFiles $decisions $processed
    Update-HarnessUnshipped $Tmp $Target $Manifest $Fresh $LockFiles $decisions $processed
    $now = Update-HarnessCanonLinks $Target $copies $drift
    return [pscustomobject]@{ Entries = $decisions; ClaudeSource = $claudeSource; CanonCopies = $now }
}
