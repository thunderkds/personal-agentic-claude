# setup.ps1 - Easy Kit installer for native Windows (T268, ADR-0003). Claude Code only.
#
# Run it inside your project's git repository, from a checkout of the kit:
#   powershell -ExecutionPolicy Bypass -File C:\path\to\easy-kit\setup.ps1
#   pwsh -File C:\path\to\easy-kit\setup.ps1 -Yes        (no questions: install, or reinstall)
#   pwsh -File C:\path\to\easy-kit\update.ps1 [-Yes]     (Update: keeps your edits; T271)
#
# It is a port of setup.sh, which stays the source of truth for behaviour: it fetches the kit into
# a temp clone, copies every MANIFEST path in as real files (a differing existing path is moved to
# <path>.bak-<id> first), links .claude/skills and .claude/agents onto ./skills and ./agents
# (a junction, else a copy), merges .claude/settings.json and turns the kit hooks into the Windows
# form, scaffolds memory/ and tasks/, and writes .claude/harness-lock.json. On an existing install
# it offers Update (lib/harness-update.ps1: refreshes the files you never edited, keeps yours,
# removes what the kit stopped shipping if you never edited it), Reinstall or Cancel.
#
# Needs: git, and Python 3.8 or newer as `py -3` or `python` (the hooks are Python).
# Env overrides: SUPERVISOR_REPO (the git URL or path to fetch), GITHUB_USERNAME (a fork).
# Not here: Codex and Cursor, board mode, packs.
param([switch]$Yes)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. ([IO.Path]::Combine($PSScriptRoot, 'lib', 'harness.ps1'))
. ([IO.Path]::Combine($PSScriptRoot, 'lib', 'harness-update.ps1'))

# Read one answer; $null when there is no answer (end of input).
function Read-SetupAnswer([string]$Prompt) {
    try {
        return Read-Host -Prompt $Prompt
    } catch {
        return $null
    }
}

# ports choose_action: install | update | reinstall | cancel. Enter cancels at an existing install.
# Without a terminal: -Yes reinstalls (as in T268), and with no -Yes nothing changes - update.ps1 is
# the command that updates without a terminal. Reinstall is never chosen without an answer or -Yes.
function Select-SetupAction([bool]$Installed, [bool]$Interactive, [string]$Target) {
    if (-not $Interactive) {
        if (-not $Installed) {
            if (-not $Yes) { Write-HarnessInfo 'No terminal - installing with the defaults: Claude Code, New project (CLAUDE.md).' }
            return 'install'
        }
        if ($Yes) { return 'reinstall' }
        Write-HarnessInfo "Easy Kit is already installed in $Target."
        Write-HarnessInfo 'No terminal - nothing was changed. To update (keeps your edits), run update.ps1. To reinstall (your edited files are backed up first), re-run setup.ps1 with -Yes.'
        return 'cancel'
    }
    Write-Host ''
    if ($Installed) {
        Write-Host "Easy Kit is already installed in $Target."
        Write-Host '  1) Update (keeps your edits)'
        Write-Host '  2) Reinstall (backs up your edits)'
        Write-Host '  3) Cancel'
        while ($true) {
            $answer = Read-SetupAnswer 'Choose [3]'
            if ($null -eq $answer) { return 'cancel' }
            switch ($answer.Trim()) {
                '1' { return 'update' }
                '2' { return 'reinstall' }
                '' { return 'cancel' }
                '3' { return 'cancel' }
            }
            Write-Host 'Please enter 1, 2 or 3.'
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

# ports choose_update_mode: how Update treats the edited files ($script:HarnessUpdateMode). Enter
# takes 1. $false to cancel (Cancel or end of input). Only reached at a terminal.
function Select-SetupUpdateMode {
    Write-Host 'How should Update treat your edited files?'
    Write-Host '  1) Ask me about each one'
    Write-Host '  2) Overwrite all of them (each backed up first)'
    Write-Host '  3) Keep all of them'
    Write-Host '  4) Cancel'
    while ($true) {
        $answer = Read-SetupAnswer 'Choice [1]'
        if ($null -eq $answer) { return $false }
        switch ($answer.Trim()) {
            '' { $script:HarnessUpdateMode = 'ask'; return $true }
            '1' { $script:HarnessUpdateMode = 'ask'; return $true }
            '2' { $script:HarnessUpdateMode = 'overwrite_all'; return $true }
            '3' { $script:HarnessUpdateMode = 'keep_all'; return $true }
            '4' { return $false }
        }
        Write-Host 'Please enter 1, 2, 3 or 4.'
    }
}

# ports the tail of run_update: the exit code and the lines that explain it.
function Complete-SetupUpdate([bool]$Wired) {
    Write-HarnessInfo 'Update complete. Re-recorded ./.claude/harness-lock.json'
    $code = 0
    if ($script:HarnessBackupFailed -gt 0) {
        Write-HarnessError "$($script:HarnessBackupFailed) file(s) could not be backed up, so they were kept as they are - see .claude/update-log.md."
        $code = 2
    }
    if ($script:HarnessUnresolved -gt 0) {
        Write-HarnessError "$($script:HarnessUnresolved) edited file(s) were kept as they are, with the kit's new copy beside each as <file>.kit-new (no terminal, or -Yes). Merge them by hand, or re-run setup.ps1 in a terminal and choose Update to resolve them."
        $code = 2
    }
    if ($code -ne 0) { return $code }
    if (-not $Wired) {
        Write-HarnessError 'Update finished, but Easy Kit hooks were NOT merged (see the message above).'
        return 2
    }
    if ($script:HarnessDeletionAborted) {
        Write-HarnessError 'Update finished, but removal of files upstream no longer ships was skipped (see the message above).'
        return 2
    }
    return 0
}

# ports main (setup.sh). Returns the exit code: 0 done or cancelled, 1 stopped, 2 hooks not wired
# (or, for Update, edited files left to merge).
function Invoke-Setup {
    $target = (Get-Location).ProviderPath
    # The seam update.ps1 sets (EASYKIT_ACTION of update.sh); not a user option.
    $seam = $env:EASYKIT_ACTION
    if ($seam -and $seam -cne 'update') {
        Write-HarnessError "Unknown EASYKIT_ACTION '$seam'."
        return 1
    }

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
    $lock = Join-HarnessPath $target '.claude/harness-lock.json'
    if ($seam -eq 'update' -and -not (Test-HarnessFile $lock)) {
        Write-HarnessError 'No .claude/harness-lock.json found in this repo. Easy Kit is not installed here - run setup.ps1 to install it.'
        return 1
    }
    $python = Find-HarnessPython
    if ($null -eq $python) {
        Write-HarnessError "Python 3.8 or newer was not found as 'py -3' or 'python' (every Easy Kit hook is Python). Install it from https://www.python.org (tick 'Add python.exe to PATH'), then re-run setup.ps1."
        return 1
    }

    $interactive = (-not $Yes) -and (-not [Console]::IsInputRedirected)
    $script:HarnessInteractive = $interactive
    $script:HarnessYes = [bool]$Yes
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
    # T272 preflight begin
    # Install-HarnessSettings reads these two helpers from the clone, and neither is in the MANIFEST.
    # Check them here, before any question and any project write, on every action.
    foreach ($needed in @('lib/windows_hooks.py', 'lib/merge-settings.py')) {
        if (-not (Test-HarnessFile (Join-HarnessPath $tmp $needed))) {
            Write-HarnessError "The fetched Easy Kit has no $needed, so it has no Windows support yet. Nothing was changed. Wait for a kit release that supports Windows, or point SUPERVISOR_REPO at a kit that has it."
            return 1
        }
    }
    # T272 preflight end

    $installed = Test-HarnessFile $lock
    $claudeDefault = 'CLAUDE.md'
    $lockFiles = $null
    $fresh = @()
    if ($installed) {
        $script:HarnessPrevCommit = Read-HarnessLockField $lock 'kit_commit'
        if ((Read-HarnessLockField $lock 'claude_md_source') -eq 'CLAUDE_LEGACY.md') { $claudeDefault = 'CLAUDE_LEGACY.md' }
        # Every path in the MANIFEST, the kit and the lock is checked here, before any write.
        Assert-HarnessNoManifestLinks $target $manifest
        $lockFiles = Read-HarnessLockFiles $lock
        $fresh = Get-HarnessFreshFiles $tmp $manifest
        Assert-HarnessNoLinkedParents $target (@($fresh) + @(Get-HarnessKeysUnderRoots $manifest $lockFiles))
    }

    if ($seam -eq 'update') {
        $action = 'update'
    } else {
        $action = Select-SetupAction $installed $interactive $target
    }
    if ($action -eq 'cancel') {
        Write-HarnessInfo 'Cancelled - nothing was changed.'
        return 0
    }
    $claudeSrc = $claudeDefault
    $backups = @()
    $asks = 0
    if ($action -eq 'update') {
        $asks = Write-HarnessUpdatePlan $tmp $target $lock $manifest $fresh $lockFiles
        if ($interactive -and $asks -gt 0) {
            $go = Select-SetupUpdateMode
        } else {
            $go = Confirm-SetupPlan $interactive
        }
    } else {
        $claudeSrc = Select-SetupClaudeSource $interactive $claudeDefault
        if ($action -eq 'reinstall') {
            $backups = Write-HarnessReinstallPlan $tmp $target $manifest $fresh $lockFiles $claudeSrc $python
        } else {
            Write-SetupPlan 'Install' $tmp $target $manifest $claudeSrc $python
        }
        $go = Confirm-SetupPlan $interactive
    }
    if (-not $go) {
        Write-HarnessInfo 'Cancelled - nothing was changed.'
        return 0
    }

    if ($action -eq 'update') {
        # ports run_update. The lock is written last, so a failure before it keeps the old one.
        $result = Invoke-HarnessUpdateFiles $tmp $target $lock $manifest $fresh $lockFiles
        $script:HarnessStep = 'merging ./.claude/settings.json'
        $wired = Install-HarnessSettings $tmp $target $python
        $script:HarnessStep = 'writing ./.claude/harness-lock.json'
        Write-HarnessLockEntries $target $result.ClaudeSource $kitCommit $result.CanonCopies $result.Entries
        $script:HarnessStep = ''
        Write-HarnessUpdateLog $target (Get-HarnessUpdateLogEntry $asks $kitCommit)
        Add-HarnessCanonExcludes $target
        return Complete-SetupUpdate $wired
    }
    if ($action -eq 'reinstall') {
        # ports run_reinstall: per-file backups, removals, and the lock from what was installed.
        $oldCopies = Read-HarnessLockCanonCopies $lock
        $drift = Get-HarnessCanonDrift $target $oldCopies $lockFiles
        $entries = Invoke-HarnessReinstallFiles $tmp $target $manifest $fresh $lockFiles $backups $claudeSrc
        $script:HarnessStep = 'linking .claude/skills and .claude/agents'
        Clear-HarnessCanonCopies $target $oldCopies $drift
        $copies = Install-HarnessCanonLinks $target
        Add-HarnessCanonExcludes $target
        $script:HarnessStep = 'merging ./.claude/settings.json'
        $wired = Install-HarnessSettings $tmp $target $python
        New-HarnessScaffold $target
        $script:HarnessStep = 'writing ./.claude/harness-lock.json'
        Write-HarnessLockEntries $target $claudeSrc $kitCommit $copies $entries
        $script:HarnessStep = ''
        if ($script:HarnessDeletionAborted) {
            Write-HarnessError 'Reinstall finished, but removal of files upstream no longer ships was skipped (see the message above).'
            $wired = $false
        }
    } else {
        # ports run_install
        Copy-HarnessManifest $tmp $target $manifest
        $copies = Install-HarnessCanonLinks $target
        Add-HarnessCanonExcludes $target
        Install-HarnessClaude $tmp $target $claudeSrc
        $wired = Install-HarnessSettings $tmp $target $python
        New-HarnessScaffold $target
        Write-HarnessLock $target $manifest $claudeSrc $kitCommit $copies
    }

    Write-HarnessInfo "Setup complete. Easy Kit copied into $target"
    Write-HarnessInfo "CLAUDE source: $claudeSrc | lock: .claude/harness-lock.json"
    Write-HarnessInfo 'CLI: Claude Code'
    if ($copies.Length -eq 0) {
        Write-HarnessInfo "The junctions .claude/skills and .claude/agents point at '$target' by its full path: if you move this project folder, re-run setup.ps1."
    }
    Write-HarnessInfo 'Pack catalog: every pack is in packs/, inactive. Your Supervisor recommends packs for this project.'
    Write-HarnessInfo 'Companion MCP servers (optional): your Supervisor shows them at Stage 1. Skip is the default; the kit never installs one.'
    if (-not $wired) {
        if (-not $script:HarnessDeletionAborted) { Write-HarnessError 'Setup finished, but Easy Kit hooks were NOT wired (see the message above).' }
        return 2
    }
    return 0
}

$code = 1
try {
    $code = Invoke-Setup
} catch {
    if ("$_" -ne $script:HarnessStop) {
        if ($script:HarnessStep) {
            Write-HarnessError "Stopped while $($script:HarnessStep): $($_.Exception.Message) The old ./.claude/harness-lock.json was kept, so re-running is safe; files before this one were already done, the rest of the run was not. Fix the cause (a read-only or locked file?), then re-run."
        } else {
            Write-HarnessError "Setup stopped: $($_.Exception.Message)"
        }
    } elseif ($script:HarnessStep) {
        Write-HarnessError "Stopped while $($script:HarnessStep). The old ./.claude/harness-lock.json was kept; fix the cause above, then re-run."
    }
    $code = 1
} finally {
    Clear-HarnessTemp
}
exit $code
