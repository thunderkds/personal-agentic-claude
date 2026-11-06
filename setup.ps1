# setup.ps1 - Easy Kit installer for native Windows (T268, ADR-0003). Claude Code only.
#
# Run it inside your project's git repository, from a checkout of the kit:
#   powershell -ExecutionPolicy Bypass -File C:\path\to\easy-kit\setup.ps1
#   pwsh -File C:\path\to\easy-kit\setup.ps1 -Yes        (no questions: install, or reinstall)
#
# It is a port of setup.sh, which stays the source of truth for behaviour: it fetches the kit into
# a temp clone, copies every MANIFEST path in as real files (a differing existing path is moved to
# <path>.bak-<id> first), links .claude/skills and .claude/agents onto ./skills and ./agents
# (a junction, else a copy), merges .claude/settings.json and turns the kit hooks into the Windows
# form, scaffolds memory/ and tasks/, and writes .claude/harness-lock.json.
#
# Needs: git, and Python 3.8 or newer as `py -3` or `python` (the hooks are Python).
# Env overrides: SUPERVISOR_REPO (the git URL or path to fetch), GITHUB_USERNAME (a fork).
# Not here yet: Update (update.ps1, a later version), Codex and Cursor, board mode, packs.
param([switch]$Yes)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. ([IO.Path]::Combine($PSScriptRoot, 'lib', 'harness.ps1'))

# Read one answer; $null when there is no answer (end of input).
function Read-SetupAnswer([string]$Prompt) {
    try {
        return Read-Host -Prompt $Prompt
    } catch {
        return $null
    }
}

# ports choose_action: install | reinstall | cancel. An existing install offers Reinstall or Cancel
# only (Update comes with update.ps1). Reinstall is never chosen without a terminal answer or -Yes.
function Select-SetupAction([bool]$Installed, [bool]$Interactive, [string]$Target) {
    $updateNote = 'Update (keeps your edits) is not in setup.ps1 yet: it comes with update.ps1 in a later Easy Kit version.'
    if (-not $Interactive) {
        if (-not $Installed) {
            if (-not $Yes) { Write-HarnessInfo 'No terminal - installing with the defaults: Claude Code, New project (CLAUDE.md).' }
            return 'install'
        }
        if ($Yes) { return 'reinstall' }
        Write-HarnessInfo "Easy Kit is already installed in $Target. $updateNote"
        Write-HarnessInfo 'No terminal - nothing was changed. To reinstall (your edited files are backed up first), re-run with -Yes.'
        return 'cancel'
    }
    Write-Host ''
    if ($Installed) {
        Write-Host "Easy Kit is already installed in $Target."
        Write-Host $updateNote
        Write-Host '  1) Reinstall (backs up your edits)'
        Write-Host '  2) Cancel'
        while ($true) {
            $answer = Read-SetupAnswer 'Choose [2]'
            if ($null -eq $answer) { return 'cancel' }
            switch ($answer.Trim()) {
                '1' { return 'reinstall' }
                '' { return 'cancel' }
                '2' { return 'cancel' }
            }
            Write-Host 'Please enter 1 or 2.'
        }
    }
    Write-Host "Easy Kit is not installed in $Target yet."
    Write-Host '  1) Install'
    Write-Host '  2) Cancel'
    while ($true) {
        $answer = Read-SetupAnswer 'Choose [1]'
        if ($null -eq $answer) { return 'cancel' }
        switch ($answer.Trim()) {
            '' { return 'install' }
            '1' { return 'install' }
            '2' { return 'cancel' }
        }
        Write-Host 'Please enter 1 or 2.'
    }
}

# ports prompt_mode: CLAUDE.md (new project) or CLAUDE_LEGACY.md (existing project).
function Select-SetupClaudeSource([bool]$Interactive, [string]$Default) {
    if (-not $Interactive) { return $Default }
    $number = '1'
    if ($Default -eq 'CLAUDE_LEGACY.md') { $number = '2' }
    Write-Host ''
    Write-Host 'Is this a new or an existing project?'
    Write-Host '  1) New project'
    Write-Host '  2) Existing / legacy project'
    while ($true) {
        $answer = Read-SetupAnswer "Choose [$number]"
        if ($null -eq $answer) { return $Default }
        switch ($answer.Trim()) {
            '' { return $Default }
            '1' { return 'CLAUDE.md' }
            '2' { return 'CLAUDE_LEGACY.md' }
        }
        Write-Host 'Please enter 1 or 2.'
    }
}

# ports plan_install: what will be copied, backed up, linked and merged.
function Write-SetupPlan([string]$Action, [string]$Tmp, [string]$Target, [string]$Manifest, [string]$ClaudeSrc, $Python) {
    $exclusions = Get-HarnessManifestExclusions $Manifest
    $paths = New-Object 'System.Collections.Generic.List[string]'
    $backups = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in [IO.File]::ReadAllLines($Manifest)) {
        $rel = Get-HarnessManifestPath $line
        if (-not $rel) { continue }
        $paths.Add($rel)
        $src = Join-HarnessPath $Tmp $rel
        $dst = Join-HarnessPath $Target $rel
        if (-not (Test-HarnessPresent $src) -or (Test-HarnessExcluded $exclusions $rel)) { continue }
        if (Test-HarnessWouldBackUp $src $dst (Get-HarnessExclusionsUnder $exclusions $rel)) {
            $backups.Add("$rel -> $([IO.Path]::GetFileName((Get-HarnessBackupName $dst)))")
        }
    }
    $claudeDst = Join-HarnessPath $Target 'CLAUDE.md'
    if (Test-HarnessWouldBackUp (Join-HarnessPath $Tmp $ClaudeSrc) $claudeDst) {
        $backups.Add("CLAUDE.md -> $([IO.Path]::GetFileName((Get-HarnessBackupName $claudeDst)))")
    }
    $type = 'New project (CLAUDE.md)'
    if ($ClaudeSrc -eq 'CLAUDE_LEGACY.md') { $type = 'Existing / legacy project (CLAUDE_LEGACY.md)' }
    $launcher = (@($Python.Name) + @($Python.Prefix)) -join ' '
    Write-Host ''
    Write-Host "Plan: $Action Easy Kit into $Target"
    Write-Host '  - CLI: Claude Code'
    Write-Host "  - Project type: $type"
    Write-Host "  - Copies in: $((@($paths) + @('CLAUDE.md')) -join ', ')"
    Write-Host '  - Existing paths that differ from the kit are moved aside first:'
    if ($backups.Count -eq 0) { Write-Host '      (none)' }
    foreach ($entry in $backups) { Write-Host "      $entry" }
    Write-Host '  - Links: .claude/skills and .claude/agents point at ./skills and ./agents (a junction, or a copy when a junction cannot be made).'
    Write-Host "  - Hooks: .claude/settings.json is created, or Easy Kit entries are merged into yours; they run through '$launcher'."
}

# ports confirm_plan: $true to act. -Yes, or no terminal, proceeds with the printed plan.
function Confirm-SetupPlan([bool]$Interactive) {
    if (-not $Interactive) {
        if ($Yes) { Write-HarnessInfo '-Yes given - proceeding with the plan above.' }
        else { Write-HarnessInfo 'No terminal - proceeding with the plan above.' }
        return $true
    }
    while ($true) {
        $answer = Read-SetupAnswer 'Proceed? [Y/n]'
        if ($null -eq $answer) { return $false }
        switch ($answer.Trim()) {
            { $_ -in @('', 'y', 'Y', 'yes', 'Yes') } { return $true }
            { $_ -in @('n', 'N', 'no', 'No') } { return $false }
        }
        Write-Host 'Please enter y or n.'
    }
}

# ports main (setup.sh). Returns the exit code: 0 done or cancelled, 1 stopped, 2 hooks not wired.
function Invoke-Setup {
    $target = (Get-Location).ProviderPath

    # Preconditions, before any file is written (check_git, check_target_is_git_repo).
    if (-not (Test-HarnessCommand 'git')) {
        Write-HarnessError 'Git is required but not installed. Install Git for Windows (https://git-scm.com), then re-run setup.ps1.'
        return 1
    }
    $inside = Invoke-HarnessNative 'git' @('-C', $target, 'rev-parse', '--is-inside-work-tree')
    if ($inside.ExitCode -ne 0 -or ($inside.Output -join '').Trim() -ne 'true') {
        Write-HarnessError "The current directory is not inside a git work tree. Run 'git init' first - setup.ps1 copies real files in, and git history is your only undo path."
        return 1
    }
    $python = Find-HarnessPython
    if ($null -eq $python) {
        Write-HarnessError "Python 3.8 or newer was not found as 'py -3' or 'python' (every Easy Kit hook is Python). Install it from https://www.python.org (tick 'Add python.exe to PATH'), then re-run setup.ps1."
        return 1
    }

    $interactive = (-not $Yes) -and (-not [Console]::IsInputRedirected)
    $url = $env:SUPERVISOR_REPO
    if (-not $url) { $url = Get-HarnessKitUrl }
    Write-HarnessInfo "Using repo: $url"

    # The fetch writes only to the temp clone; every question comes before any project write.
    $tmp = New-HarnessTempPath
    Invoke-HarnessFetch $url $tmp
    $kitCommit = ''
    $head = Invoke-HarnessNative 'git' @('-C', $tmp, 'rev-parse', '--short', 'HEAD')
    if ($head.ExitCode -eq 0 -and $head.Output.Length -gt 0) { $kitCommit = $head.Output[0].Trim() }
    $manifest = Join-HarnessPath $tmp 'MANIFEST'
    if (-not (Test-HarnessFile $manifest)) {
        Write-HarnessError 'MANIFEST not found in the fetched Easy Kit. The repo may be corrupt.'
        return 1
    }

    $lock = Join-HarnessPath $target '.claude/harness-lock.json'
    $installed = Test-HarnessFile $lock
    $claudeDefault = 'CLAUDE.md'
    if ($installed) {
        $script:HarnessPrevCommit = Read-HarnessLockField $lock 'kit_commit'
        if ((Read-HarnessLockField $lock 'claude_md_source') -eq 'CLAUDE_LEGACY.md') { $claudeDefault = 'CLAUDE_LEGACY.md' }
    }

    $action = Select-SetupAction $installed $interactive $target
    if ($action -eq 'cancel') {
        Write-HarnessInfo 'Cancelled - nothing was changed.'
        return 0
    }
    $claudeSrc = Select-SetupClaudeSource $interactive $claudeDefault
    $label = 'Install'
    if ($action -eq 'reinstall') { $label = 'Reinstall' }
    Write-SetupPlan $label $tmp $target $manifest $claudeSrc $python
    if (-not (Confirm-SetupPlan $interactive)) {
        Write-HarnessInfo 'Cancelled - nothing was changed.'
        return 0
    }

    # ports run_install
    Copy-HarnessManifest $tmp $target $manifest
    $copies = Install-HarnessCanonLinks $target
    Add-HarnessCanonExcludes $target
    Install-HarnessClaude $tmp $target $claudeSrc
    $wired = Install-HarnessSettings $tmp $target $python
    New-HarnessScaffold $target
    Write-HarnessLock $target $manifest $claudeSrc $kitCommit $copies

    Write-HarnessInfo "Setup complete. Easy Kit copied into $target"
    Write-HarnessInfo "CLAUDE source: $claudeSrc | lock: .claude/harness-lock.json"
    Write-HarnessInfo 'CLI: Claude Code'
    if ($copies.Length -eq 0) {
        Write-HarnessInfo "The junctions .claude/skills and .claude/agents point at '$target' by its full path: if you move this project folder, re-run setup.ps1."
    }
    Write-HarnessInfo 'Pack catalog: every pack is in packs/, inactive. Your Supervisor recommends packs for this project.'
    Write-HarnessInfo 'Companion MCP servers (optional): your Supervisor shows them at Stage 1. Skip is the default; the kit never installs one.'
    if (-not $wired) {
        Write-HarnessError 'Setup finished, but Easy Kit hooks were NOT wired (see the message above).'
        return 2
    }
    return 0
}

$code = 1
try {
    $code = Invoke-Setup
} catch {
    if ("$_" -ne $script:HarnessStop) { Write-HarnessError "Setup stopped: $($_.Exception.Message)" }
    $code = 1
} finally {
    Clear-HarnessTemp
}
exit $code
