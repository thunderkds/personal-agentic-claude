# tests/windows/smoke-install.ps1 - T268 smoke of setup.ps1 (AC 14).
#
# Runs in the Windows CI job (.github/workflows/windows.yml) under Windows PowerShell 5.1 and
# PowerShell 7, and in Linux PowerShell through Docker (tests/test_setup_ps1_pwsh.py).
# Set SUPERVISOR_REPO to the kit checkout. The script makes a temp git repo whose path holds a
# space and a non-ASCII letter, then runs setup.ps1 -Yes four times:
#   1. fresh install: every MANIFEST path, no excluded path, canon links, lock hashes, hooks in the
#      Windows form (no python3 anywhere in .claude/settings.json);
#   2. a second run: no backup, the same lock;
#   3. after an edit to AGENTS.md: exactly one AGENTS.md.bak-* holding the edit, the kit's copy back;
#   4. once more: no new backup, the same lock, no duplicate exclude line.
# On Windows the canon links must be junctions; elsewhere a junction or a copy recorded in the lock.
# Prints SMOKE PASS, or throws with the first failure.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$kit = $env:SUPERVISOR_REPO
if (-not $kit) { throw 'Set SUPERVISOR_REPO to the kit checkout (a path or a git URL).' }
$setup = [IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot, '..', '..', 'setup.ps1'))
. ([IO.Path]::Combine([IO.Path]::GetDirectoryName($setup), 'lib', 'harness.ps1'))
$exe = (Get-Process -Id $PID).Path
$onWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT

function Assert-Smoke([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "SMOKE FAIL: $Message" }
}

function Get-SmokeBackups([string]$Repo) {
    $found = New-Object 'System.Collections.Generic.List[string]'
    $entries = Get-HarnessTreeEntries $Repo
    foreach ($key in $entries.Keys) {
        if ($key.StartsWith('.git/', [StringComparison]::Ordinal)) { continue }
        if ([IO.Path]::GetFileName($key).Contains('.bak-')) { $found.Add($key) }
    }
    $list = $found.ToArray()
    [Array]::Sort($list, [StringComparer]::Ordinal)
    return , $list
}

function Get-SmokeFilesBlock([string]$Repo) {
    $text = [IO.File]::ReadAllText((Join-HarnessPath $Repo '.claude/harness-lock.json'))
    return $text.Substring($text.IndexOf('"files"'))
}

function Invoke-SmokeSetup([string]$Repo) {
    $arguments = @('-NoProfile', '-NonInteractive')
    if ($onWindows) { $arguments += @('-ExecutionPolicy', 'Bypass') }
    $arguments += @('-File', $setup, '-Yes')
    $saved = [Environment]::CurrentDirectory
    Push-Location -LiteralPath $Repo
    [Environment]::CurrentDirectory = $Repo
    try {
        $result = Invoke-HarnessNative $exe $arguments
    } finally {
        [Environment]::CurrentDirectory = $saved
        Pop-Location
    }
    foreach ($line in $result.Output) { Write-Host "  | $line" }
    Assert-Smoke ($result.ExitCode -eq 0) "setup.ps1 exited $($result.ExitCode)"
    return $result
}

$repo = [IO.Path]::Combine([IO.Path]::GetTempPath(), 'easykit smoke ' + [char]0x00e9 + ' ' + [guid]::NewGuid().ToString('N').Substring(0, 8))
[void][IO.Directory]::CreateDirectory($repo)
try {
    $init = Invoke-HarnessNative 'git' @('init', '--quiet', $repo)
    Assert-Smoke ($init.ExitCode -eq 0) "git init failed: $($init.Output -join ' ')"
    $manifest = Join-HarnessPath $repo 'MANIFEST'

    Write-Host '== run 1: fresh install'
    [void](Invoke-SmokeSetup $repo)
    $kitManifest = Join-HarnessPath $kit 'MANIFEST'
    if (-not (Test-HarnessFile $kitManifest)) { $kitManifest = [IO.Path]::Combine([IO.Path]::GetDirectoryName($setup), 'MANIFEST') }
    foreach ($line in [IO.File]::ReadAllLines($kitManifest)) {
        $rel = Get-HarnessManifestPath $line
        if ($rel) { Assert-Smoke (Test-HarnessPresent (Join-HarnessPath $repo $rel)) "MANIFEST path '$rel' is missing" }
    }
    foreach ($excluded in (Get-HarnessManifestExclusions $kitManifest)) {
        Assert-Smoke (-not (Test-HarnessPresent (Join-HarnessPath $repo $excluded))) "excluded path '$excluded' was installed"
    }
    Assert-Smoke (-not (Test-HarnessPresent $manifest)) 'MANIFEST itself was copied in'

    $lockText = [IO.File]::ReadAllText((Join-HarnessPath $repo '.claude/harness-lock.json'))
    $lock = $lockText | ConvertFrom-Json
    foreach ($canon in @('skills', 'agents')) {
        $link = Join-HarnessPath $repo ".claude/$canon"
        if ($onWindows) {
            Assert-Smoke (Test-HarnessLink $link) ".claude/$canon is not a junction on Windows"
        } else {
            Assert-Smoke ((Test-HarnessLink $link) -or $lockText.Contains("`".claude/$canon`"")) ".claude/$canon is neither a link nor a recorded copy"
        }
        $first = @((New-Object IO.DirectoryInfo (Join-HarnessPath $repo $canon)).GetFileSystemInfos())[0].Name
        Assert-Smoke (Test-HarnessPresent (Join-HarnessPath $link $first)) ".claude/$canon does not show ./$canon/$first"
    }

    $count = 0
    foreach ($entry in $lock.files.PSObject.Properties) {
        $count += 1
        $actual = Get-HarnessFileHash (Join-HarnessPath $repo $entry.Name)
        Assert-Smoke ($actual -eq $entry.Value) "lock hash of '$($entry.Name)' does not match the file"
    }
    Assert-Smoke ($count -gt 100) "the lock lists only $count files"
    Assert-Smoke ($lock.claude_md_source -eq 'CLAUDE.md') 'claude_md_source is not CLAUDE.md'

    $settingsText = [IO.File]::ReadAllText((Join-HarnessPath $repo '.claude/settings.json'))
    Assert-Smoke (-not $settingsText.Contains('python3')) '.claude/settings.json still calls python3'
    $settings = $settingsText | ConvertFrom-Json
    $execForm = 0
    foreach ($event in $settings.hooks.PSObject.Properties) {
        foreach ($group in @($event.Value)) {
            foreach ($hook in @($group.hooks)) {
                if ($hook.PSObject.Properties.Name -contains 'args') {
                    $execForm += 1
                    Assert-Smoke (@('py', 'python') -contains $hook.command) "hook command '$($hook.command)' is not py or python"
                }
            }
        }
    }
    Assert-Smoke ($execForm -gt 5) "only $execForm hooks are in the Windows exec form"
    $filesBlock = Get-SmokeFilesBlock $repo
    Assert-Smoke ((Get-SmokeBackups $repo).Length -eq 0) 'a fresh install made a backup'

    Write-Host '== run 2: second run is idempotent'
    [void](Invoke-SmokeSetup $repo)
    Assert-Smoke ((Get-SmokeBackups $repo).Length -eq 0) 'the second run made a backup'
    Assert-Smoke ((Get-SmokeFilesBlock $repo) -ceq $filesBlock) 'the second run changed the lock hashes'

    Write-Host '== run 3: an edited kit file is backed up'
    $agents = Join-HarnessPath $repo 'AGENTS.md'
    [IO.File]::AppendAllText($agents, "`nsmoke edit`n")
    $run3 = Invoke-SmokeSetup $repo
    $backups = Get-SmokeBackups $repo
    Assert-Smoke ($backups.Length -eq 1 -and $backups[0].StartsWith('AGENTS.md.bak-')) "expected one AGENTS.md backup, got: $($backups -join ', ')"
    Assert-Smoke ([IO.File]::ReadAllText((Join-HarnessPath $repo $backups[0])).EndsWith("smoke edit`n")) 'the backup does not hold the edit'
    Assert-Smoke (($run3.Output -join "`n").Contains('[warn]')) 'no [warn] line named the backup'
    Assert-Smoke ((Get-SmokeFilesBlock $repo) -ceq $filesBlock) 'AGENTS.md was not restored to the kit copy'

    Write-Host '== run 4: no new backup'
    [void](Invoke-SmokeSetup $repo)
    $again = Get-SmokeBackups $repo
    Assert-Smoke (($again -join '|') -ceq ($backups -join '|')) "the fourth run changed the backups: $($again -join ', ')"
    Assert-Smoke ((Get-SmokeFilesBlock $repo) -ceq $filesBlock) 'the fourth run changed the lock hashes'
    $exclude = [IO.File]::ReadAllLines((Join-HarnessPath $repo '.git/info/exclude'))
    foreach ($canon in @('skills', 'agents')) {
        $hits = @($exclude | Where-Object { $_ -ceq "/.claude/$canon" }).Length
        Assert-Smoke ($hits -eq 1) "/.claude/$canon is in .git/info/exclude $hits times"
    }
    Write-Host 'SMOKE PASS'
} finally {
    Remove-HarnessPath $repo
}
