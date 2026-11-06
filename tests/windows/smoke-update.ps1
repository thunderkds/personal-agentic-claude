# tests/windows/smoke-update.ps1 - T271 smoke of update.ps1 (AC 13).
#
# Runs in the Windows CI job (.github/workflows/windows.yml) under Windows PowerShell 5.1 and
# PowerShell 7, and in Linux PowerShell through Docker (tests/test_update_ps1_pwsh.py).
# Set SUPERVISOR_REPO to the kit checkout (kit A). The script:
#   1. installs kit A with setup.ps1 -Yes into a temp git repo whose path holds a space and a
#      non-ASCII letter, then edits two kit files, adds a file of its own under skills/ and a Stop
#      hook of its own;
#   2. makes kit B, a clone of kit A with a second local commit: AGENTS.md (X1) and one edited file
#      (X2) changed, skills/zz-smoke-new/SKILL.md (Y) added, two templates files (Z1, and Z2 which
#      the user edited) deleted;
#   3. runs update.ps1 -Yes against kit B: X1 replaced, Y added (and seen through .claude/skills),
#      Z1 removed, Z2 and X2 kept, X2.kit-new written, hooks still in the Windows form, lock updated;
#   4. runs update.ps1 -Yes again: nothing changes.
# Prints SMOKE PASS, or throws with the first failure.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$kitA = $env:SUPERVISOR_REPO
if (-not $kitA) { throw 'Set SUPERVISOR_REPO to the kit checkout (a path or a git URL).' }
$root = [IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot, '..', '..'))
$setup = [IO.Path]::Combine($root, 'setup.ps1')
$update = [IO.Path]::Combine($root, 'update.ps1')
. ([IO.Path]::Combine($root, 'lib', 'harness.ps1'))
$exe = (Get-Process -Id $PID).Path
$onWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT

function Assert-Smoke([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "SMOKE FAIL: $Message" }
}

function Invoke-SmokeGit([string[]]$Arguments) {
    $result = Invoke-HarnessNative 'git' (@('-c', 'user.name=smoke', '-c', 'user.email=smoke@example.invalid') + $Arguments)
    Assert-Smoke ($result.ExitCode -eq 0) "git $($Arguments -join ' ') failed: $($result.Output -join ' ')"
    return $result
}

function Invoke-SmokeScript([string]$Script, [string]$Repo, [string]$Kit) {
    $arguments = @('-NoProfile', '-NonInteractive')
    if ($onWindows) { $arguments += @('-ExecutionPolicy', 'Bypass') }
    $arguments += @('-File', $Script, '-Yes')
    $savedDir = [Environment]::CurrentDirectory
    $savedKit = $env:SUPERVISOR_REPO
    Push-Location -LiteralPath $Repo
    [Environment]::CurrentDirectory = $Repo
    $env:SUPERVISOR_REPO = $Kit
    try {
        $result = Invoke-HarnessNative $exe $arguments
    } finally {
        $env:SUPERVISOR_REPO = $savedKit
        [Environment]::CurrentDirectory = $savedDir
        Pop-Location
    }
    foreach ($line in $result.Output) { Write-Host "  | $line" }
    return $result
}

# Every entry of the project, without .git and the update log: path -> hash, 'dir' or 'link'.
function Get-SmokeTree([string]$Repo) {
    $entries = Get-HarnessTreeEntries $Repo
    $lines = New-Object 'System.Collections.Generic.List[string]'
    foreach ($key in $entries.Keys) {
        if ($key -ceq '.git' -or $key.StartsWith('.git/', [StringComparison]::Ordinal)) { continue }
        if ($key -ceq '.claude/update-log.md') { continue }
        $value = $entries[$key]
        if ($value -eq 'file') { $value = Get-HarnessFileHash (Join-HarnessPath $Repo $key) }
        $lines.Add("$key=$value")
    }
    $list = $lines.ToArray()
    [Array]::Sort($list, [StringComparer]::Ordinal)
    return ($list -join "`n")
}

function Get-SmokeHookCount($Settings) {
    $count = 0
    foreach ($event in $Settings.hooks.PSObject.Properties) { $count += @($event.Value).Length }
    return $count
}

$temp = [IO.Path]::GetTempPath()
$id = [guid]::NewGuid().ToString('N').Substring(0, 8)
$repo = [IO.Path]::Combine($temp, 'easykit update ' + [char]0x00e9 + ' ' + $id)
$kitB = [IO.Path]::Combine($temp, 'easykit-kit-b-' + $id)
try {
    [void](Invoke-SmokeGit @('init', '--quiet', $repo))
    [void](Invoke-SmokeGit @('clone', '--quiet', $kitA, $kitB))
    $docs = @((New-Object IO.DirectoryInfo (Join-HarnessPath $kitB 'docs/claude-md')).GetFiles() | ForEach-Object { $_.Name })
    $templates = @((New-Object IO.DirectoryInfo (Join-HarnessPath $kitB 'templates')).GetFiles() | ForEach-Object { $_.Name })
    [Array]::Sort($docs, [StringComparer]::Ordinal)
    [Array]::Sort($templates, [StringComparer]::Ordinal)
    $x1 = 'AGENTS.md'
    $x2 = 'docs/claude-md/' + $docs[0]
    $y = 'skills/zz-smoke-new/SKILL.md'
    $z1 = 'templates/' + $templates[0]
    $z2 = 'templates/' + $templates[1]
    $own = 'skills/zz-smoke-own/SKILL.md'

    Write-Host '== install kit A'
    $run = Invoke-SmokeScript $setup $repo $kitA
    Assert-Smoke ($run.ExitCode -eq 0) "setup.ps1 exited $($run.ExitCode)"
    foreach ($rel in @($x2, $z2)) { [IO.File]::AppendAllText((Join-HarnessPath $repo $rel), "`nsmoke user edit`n") }
    [void][IO.Directory]::CreateDirectory((Join-HarnessPath $repo 'skills/zz-smoke-own'))
    [IO.File]::WriteAllText((Join-HarnessPath $repo $own), "mine`n")
    $settingsPath = Join-HarnessPath $repo '.claude/settings.json'
    $settings = [IO.File]::ReadAllText($settingsPath) | ConvertFrom-Json
    $userHook = '{"hooks": [{"type": "command", "command": "echo user-own-hook"}]}' | ConvertFrom-Json
    if ($settings.hooks.PSObject.Properties.Name -contains 'Stop') {
        $settings.hooks.Stop = @($settings.hooks.Stop) + @($userHook)
    } else {
        $settings.hooks | Add-Member -MemberType NoteProperty -Name 'Stop' -Value @($userHook)
    }
    [IO.File]::WriteAllText($settingsPath, ($settings | ConvertTo-Json -Depth 20))
    $hookCount = Get-SmokeHookCount $settings
    $oldLock = [IO.File]::ReadAllText((Join-HarnessPath $repo '.claude/harness-lock.json')) | ConvertFrom-Json

    Write-Host '== make kit B'
    foreach ($rel in @($x1, $x2)) { [IO.File]::AppendAllText((Join-HarnessPath $kitB $rel), "`nsmoke kit B change`n") }
    [void][IO.Directory]::CreateDirectory((Join-HarnessPath $kitB 'skills/zz-smoke-new'))
    [IO.File]::WriteAllText((Join-HarnessPath $kitB $y), "---`nname: zz-smoke-new`ndescription: added by kit B`n---`n")
    foreach ($rel in @($z1, $z2)) { Remove-HarnessPath (Join-HarnessPath $kitB $rel) }
    [void](Invoke-SmokeGit @('-C', $kitB, 'add', '-A'))
    [void](Invoke-SmokeGit @('-C', $kitB, 'commit', '--quiet', '-m', 'kit B'))
    $headB = ((Invoke-SmokeGit @('-C', $kitB, 'rev-parse', 'HEAD')).Output[0]).Trim()

    Write-Host '== update to kit B'
    $run = Invoke-SmokeScript $update $repo $kitB
    $text = $run.Output -join "`n"
    Assert-Smoke ($run.ExitCode -eq 2) "update.ps1 exited $($run.ExitCode), expected 2 (one edited file left to merge)"
    Assert-Smoke (-not $text.Contains('re-making')) 'update.ps1 re-made a canon link that was correct'
    $hashB = @{}
    foreach ($rel in @($x1, $x2, $y)) { $hashB[$rel] = Get-HarnessFileHash (Join-HarnessPath $kitB $rel) }
    Assert-Smoke ((Get-HarnessFileHash (Join-HarnessPath $repo $x1)) -eq $hashB[$x1]) "$x1 was not replaced with kit B's copy"
    Assert-Smoke ((Get-HarnessFileHash (Join-HarnessPath $repo $y)) -eq $hashB[$y]) "$y was not added"
    Assert-Smoke (Test-HarnessFile (Join-HarnessPath $repo ".claude/$y")) ".claude/skills does not show $y"
    Assert-Smoke (-not (Test-HarnessPresent (Join-HarnessPath $repo $z1))) "$z1 was not removed"
    Assert-Smoke ([IO.File]::ReadAllText((Join-HarnessPath $repo $z2)).EndsWith("smoke user edit`n")) "the edited $z2 was not kept"
    Assert-Smoke ([IO.File]::ReadAllText((Join-HarnessPath $repo $x2)).EndsWith("smoke user edit`n")) "the edited $x2 was overwritten"
    Assert-Smoke ((Get-HarnessFileHash (Join-HarnessPath $repo "$x2.kit-new")) -eq $hashB[$x2]) "$x2.kit-new does not hold kit B's copy"
    Assert-Smoke ($text.Contains("$x2.kit-new")) "no line named $x2.kit-new"
    Assert-Smoke ($text.Contains($z2)) "no line named the kept $z2"
    Assert-Smoke (Test-HarnessFile (Join-HarnessPath $repo $own)) 'the user file under skills/ was removed'

    $lockText = [IO.File]::ReadAllText((Join-HarnessPath $repo '.claude/harness-lock.json'))
    $lock = $lockText | ConvertFrom-Json
    $names = @($lock.files.PSObject.Properties.Name)
    Assert-Smoke ($headB.StartsWith($lock.kit_commit)) "the lock records kit_commit '$($lock.kit_commit)', not kit B ($headB)"
    Assert-Smoke ($lock.files.$x1 -eq $hashB[$x1]) "the lock does not hold the new hash of $x1"
    Assert-Smoke ($names -ccontains $y) "the lock does not list $y"
    Assert-Smoke (-not ($names -ccontains $z1)) "the lock still lists $z1"
    Assert-Smoke ($lock.files.$x2 -eq $oldLock.files.$x2) "the lock changed the hash of the kept $x2"
    foreach ($canon in @('skills', 'agents')) {
        $link = Join-HarnessPath $repo ".claude/$canon"
        if ($onWindows) {
            Assert-Smoke (Test-HarnessLink $link) ".claude/$canon is not a junction on Windows after Update"
        } else {
            Assert-Smoke ((Test-HarnessLink $link) -or $lockText.Contains("`".claude/$canon`"")) ".claude/$canon is neither a link nor a recorded copy after Update"
        }
    }

    $settingsText = [IO.File]::ReadAllText($settingsPath)
    Assert-Smoke (-not $settingsText.Contains('python3')) '.claude/settings.json calls python3 after Update'
    $after = $settingsText | ConvertFrom-Json
    Assert-Smoke ((Get-SmokeHookCount $after) -eq $hookCount) "Update changed the hook entry count: $hookCount -> $(Get-SmokeHookCount $after)"
    $userKept = @(@($after.hooks.Stop) | Where-Object { @($_.hooks)[0].command -eq 'echo user-own-hook' }).Length
    Assert-Smoke ($userKept -eq 1) 'Update dropped the user Stop hook'
    $execForm = 0
    foreach ($event in $after.hooks.PSObject.Properties) {
        foreach ($group in @($event.Value)) {
            foreach ($hook in @($group.hooks)) {
                if ($hook.PSObject.Properties.Name -contains 'args') {
                    $execForm += 1
                    Assert-Smoke (@('py', 'python') -contains $hook.command) "hook command '$($hook.command)' is not py or python"
                }
            }
        }
    }
    Assert-Smoke ($execForm -gt 5) "only $execForm hooks are in the Windows exec form after Update"
    Assert-Smoke ([IO.File]::ReadAllText((Join-HarnessPath $repo '.claude/update-log.md')).StartsWith('## ')) 'no update log entry'

    Write-Host '== update again: nothing changes'
    $tree = Get-SmokeTree $repo
    $run = Invoke-SmokeScript $update $repo $kitB
    Assert-Smoke ($run.ExitCode -eq 2) "the second update.ps1 exited $($run.ExitCode), expected 2"
    Assert-Smoke (-not (($run.Output -join "`n").Contains('re-making'))) 'the second update re-made a canon link'
    Assert-Smoke ((Get-SmokeTree $repo) -ceq $tree) 'the second Update changed the project'
    Write-Host 'SMOKE PASS'
} finally {
    foreach ($dir in @($repo, $kitB)) {
        if (Test-HarnessPresent $dir) { Remove-HarnessPath $dir }
    }
}
exit 0
