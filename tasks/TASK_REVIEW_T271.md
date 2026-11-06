# TASK_REVIEW — T271: Native Windows support, step 8 - update.ps1 and the Update action of setup.ps1

> Sibling of `tasks/TASK_GUIDE_T271.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Implementer-filled (common-infrastructure, 2026-11-06). New: `tests/test_update_ps1_pwsh.py` (15 tests, Linux pwsh 7.4.2 in Docker, T268's harness reused by import: same pinned image digest, same two mounts, `--network none`, no privileged flag, no pull): SC 1 `test_sc1_...`, SC 2 `test_sc2_...` (X2 kept, `X2.kit-new`, line names it, exit 2; X3 edited but unchanged by the kit is kept with no `.kit-new`), SC 3 `test_sc3_...`, SC 4 `test_sc4_...` (exec form, same entry count, user Stop hook kept, converter ran), AC 7 `test_ac7_...` (canon copy refreshed, `canon_copies` kept, user's own skill visible), AC 9 `test_ac9_...` (log entry shape), SC 5 `test_sc5_...` (second Update: tree identical except `.claude/update-log.md`, which gets a new entry by design of AC 9), SC 6 `test_sc6_...` (read-only AGENTS.md: exit 1, lock bytes and file unchanged, `[error]` names the file and the lock), SC 7 `test_sc7_mutation_control_...`, AC 8 `test_ac8_lock_and_log_match_update_sh` (setup.sh + update.sh on a twin, no terminal: `files` block, `kit_commit`, `claude_md_source` and the sorted log lines equal), AC 10 `test_ac10_...`, AC 12 `test_an_unsafe_lock_entry_stops_before_any_write`, `test_a_link_inside_a_kit_folder_stops_before_any_write`, AC 1 `test_update_ps1_refuses_where_nothing_is_installed`, AC 13 `test_the_windows_ci_update_smoke_passes_in_linux_pwsh` (runs `tests/windows/smoke-update.ps1`). Extended: `tests/test_setup_ps1_static.py` (update.ps1, lib/harness-update.ps1, smoke-update.ps1 under the 5.1/ASCII/banned-token checks; new ban `Remove-Item ... -Recurse` + its mutation; AC 1 alias check), `tests/test_windows_ci_workflow.py` (update smoke under both shells + 2 mutations). **Windows-only behaviour is NOT verified**: junction refresh and stale-junction re-make, `core.symlinks=false`, CRLF and PowerShell 5.1 run only in the CI steps, which have not run. The interactive menus and the per-file prompt (`[o]/[s]/[v]`, `choose_update_mode`) have no automated test (no TTY in Docker) |
| Verification command run | ☑ pass | Head `ae6855c2`, 2026-11-06T15:49:49Z-15:55:26Z: `python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py tests/test_update_ps1_pwsh.py tests/test_windows_ci_workflow.py -q` → `65 passed in 70.87s (0:01:10)`; then `python3 -m pytest .claude/hooks/tests tests -q` → `3834 passed, 25 subtests passed in 265.27s (0:04:25)` |
| Negative cases hold | ☑ pass | Red first (tests on disk, no update.ps1 / lib/harness-update.ps1 yet, before any implementation commit): `python3 -m pytest tests/test_setup_ps1_static.py tests/test_update_ps1_pwsh.py tests/test_windows_ci_workflow.py -q` → `20 failed, 32 passed in 9.81s` (every new update test, the 4 new static checks, the workflow shape test and its 2 new mutations; `test_sc4_...` passed red because a failed run leaves the settings as installed, so `assert "Windows form" in r.stdout` was added to it). SC 7 mutation control, automated (`test_sc7_mutation_control_a_neutered_replace_is_caught`): the line `    [IO.File]::Copy($Src, $Dst, $true)` in `Install-HarnessUpdateFile` is replaced in a copy of the installer → `sc1_problems()` is non-empty (passes). Link guard red check: `setup.ps1 \| 194 +++---` (the `Assert-HarnessNoLinkedParents` call removed from a copy) → `1 failed`: `[error] Stopped while updating './skills/blast-radius/SKILL.md': Exception calling "CreateDirectory"...` (the run had already written earlier files); restored, green. Two findings fixed during the green phase: a file the user edited but the kit did not change got a useless `.kit-new` (shell asks about it; now kept, AC 2), and Reinstall moved an untouched canon copy to `.claude/skills.bak-*` (now re-made with no backup unless the user changed the copy) |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `3834 passed, 25 subtests passed` (T268 after its fixes: `3812 passed`; +22 = 15 update tests + 5 static + 2 workflow mutations). AC 14: `git diff --stat 863913c2 -- setup.sh update.sh 'lib/*.sh' lib/merge-settings.py lib/windows_hooks.py .claude/hooks` → empty. `LC_ALL=C grep -nP '[^\x00-\x7F]'` on the five new or changed .ps1 files → no match (exit 1). Shell suites (`tests/*.sh`) not run by this agent. `code-review` and `security-review` skills were not run by this agent (no Skill tool in its session): Supervisor |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: a command-line installer |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI: a command-line installer |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI: a command-line installer |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by the implementing agent in the worktree on branch `feat/t271-update-ps1` at
`f430d180`, before any implementation commit):

```
2026-11-06T15:34:28Z
$ ls update.ps1 lib/harness-update.ps1
ls: cannot access 'update.ps1': No such file or directory
ls: cannot access 'lib/harness-update.ps1': No such file or directory
exit=2
$ grep -nE "Write-Host .  [0-9]\)|updateNote =" setup.ps1
34:    $updateNote = 'Update (keeps your edits) is not in setup.ps1 yet: it comes with update.ps1 in a later Easy Kit version.'
49:        Write-Host '  1) Reinstall (backs up your edits)'
50:        Write-Host '  2) Cancel'
63:    Write-Host '  1) Install'
64:    Write-Host '  2) Cancel'
84:    Write-Host '  1) New project'
85:    Write-Host '  2) Existing / legacy project'
$ grep -nE "^\s+- (uses|name):" .github/workflows/windows.yml
31:      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
36:      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
40:      - name: Install pytest and PyYAML
43:      - name: Python tests
48:      - name: setup.ps1 smoke (Windows PowerShell 5.1)
54:      - name: setup.ps1 smoke (PowerShell 7)
$ python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py tests/test_windows_ci_workflow.py -q
...........................................                              [100%]
43 passed in 36.37s
2026-11-06T15:35:04Z
```

So today an existing install offers only Reinstall or Cancel (lines 49-50), and there is no Update
in PowerShell.

**AFTER** (same commands, implementing agent, worktree, head `ae6855c2`):

```
2026-11-06T15:52:59Z
$ ls update.ps1 lib/harness-update.ps1
lib/harness-update.ps1
update.ps1
$ grep -nE "Write-Host .  [0-9]\)|updateNote =" setup.ps1
52:        Write-Host '  1) Update (keeps your edits)'
53:        Write-Host '  2) Reinstall (backs up your edits)'
54:        Write-Host '  3) Cancel'
68:    Write-Host '  1) Install'
69:    Write-Host '  2) Cancel'
89:    Write-Host '  1) New project'
90:    Write-Host '  2) Existing / legacy project'
160:    Write-Host '  1) Ask me about each one'
161:    Write-Host '  2) Overwrite all of them (each backed up first)'
162:    Write-Host '  3) Keep all of them'
163:    Write-Host '  4) Cancel'
$ grep -nE "^\s+- (uses|name):" .github/workflows/windows.yml
31:      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
36:      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
40:      - name: Install pytest and PyYAML
43:      - name: Python tests
48:      - name: setup.ps1 smoke (Windows PowerShell 5.1)
54:      - name: setup.ps1 smoke (PowerShell 7)
63:      - name: update.ps1 smoke (Windows PowerShell 5.1)
69:      - name: update.ps1 smoke (PowerShell 7)
2026-11-06T15:49:49Z
$ python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py tests/test_update_ps1_pwsh.py tests/test_windows_ci_workflow.py -q
65 passed in 70.87s (0:01:10)
```

Linux pwsh 7.4.2 (Docker) run of `tests/windows/smoke-update.ps1`, excerpt of the second Update (before the exit-code fix, same output):

```
  | Plan: Update Easy Kit in /tmp/easykit update é 2eb5173e (keeps your edits)
  |   - Files to add or restore: 0
  |   - You edited these; they are kept as they are, and the kit's new copy is written beside each as <file>.kit-new:
  |       docs/claude-md/code-naming-conventions.md
  |   - Upstream no longer ships these, but you edited them; they will be kept:
  |       templates/BRAINSTORMING_LOG_template.md
  | [warn]  kept your './docs/claude-md/code-naming-conventions.md' as it is; the kit's new copy is in './docs/claude-md/code-naming-conventions.md.kit-new' - compare and merge by hand, then delete it.
  | [info]  Easy Kit hooks in ./.claude/settings.json run through 'py' (Windows form).
  | [info]  Wrote ./.claude/harness-lock.json (147 file hashes).
  | [error] 1 edited file(s) were kept as they are, with the kit's new copy beside each as <file>.kit-new (no terminal, or -Yes). Merge them by hand, or re-run setup.ps1 in a terminal and choose Update to resolve them.
SMOKE PASS
```

Not yet observed: the Windows CI steps `update.ps1 smoke (Windows PowerShell 5.1)` and `(PowerShell 7)` have not run (junction, `core.symlinks=false`, CRLF, 5.1).

**DELTA**: A Windows user who installed Easy Kit with `setup.ps1` can now update it with `update.ps1` (or Update in the `setup.ps1` menu): files they never edited are refreshed, their edits are kept (with the kit's copy beside them when nobody can be asked), files the kit stopped shipping are removed only if unedited, and the hooks stay in the Windows form (Windows behaviour pending the first CI run).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
