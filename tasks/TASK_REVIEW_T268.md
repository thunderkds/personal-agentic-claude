# TASK_REVIEW — T268: Native Windows support, step 7 - setup.ps1, the PowerShell installer (install and reinstall)

> Sibling of `tasks/TASK_GUIDE_T268.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Implementer-filled (common-infrastructure, 2026-11-06). New: `tests/test_setup_ps1_static.py` (AC 1, 5, SC 6: 14 tests), `tests/test_setup_ps1_pwsh.py` (SC 1-5, AC 2, 4, 6, 9, 10, 11, 12, 13: 9 tests, Linux pwsh 7.4.2 in Docker), `tests/windows/smoke-install.ps1` (AC 14, run by the Windows CI job and by the Docker test); extended: `tests/test_windows_ci_workflow.py` (smoke steps under `shell: powershell` and `shell: pwsh` + 2 mutations). `python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py -q` → `23 passed in 38.98s` (2026-11-06T14:57Z). AC 10 parity: the Docker test reads the setup.ps1 lock with `extract_lock_pairs` / `lookup_lock_field` (setup.sh define-only) and compares its `files` block, the four memory files and CLAUDE.md with a lock written by `setup.sh` on a twin repo from the same kit: equal. Docker: the implementer pulled `mcr.microsoft.com/powershell` once by hand (digest `sha256:810c4f1e0c9d...d5b0`, pinned in the test); the image has no git/Python, so the test mounts host `/usr` read-only and runs host git/python through the host loader. **Windows-only behaviour is NOT verified**: on Linux `New-Item -ItemType Junction` made no link, so the junction path never ran (only the copy fallback did); `core.symlinks=false`, CRLF checkout, PowerShell 5.1 and Windows paths are covered only by the CI smoke, which has not run yet |
| Verification command run | ☑ pass | After the review fixes (2026-11-06T15:24-15:29Z): `python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py tests/test_windows_ci_workflow.py -q` → `43 passed in 37.07s`; `python3 -m pytest .claude/hooks/tests tests -q` → `3812 passed, 25 subtests passed in 227.44s (0:03:47)`. Before them: `python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py -q && python3 -m pytest .claude/hooks/tests tests -q` → `23 passed in 38.98s`, then `3809 passed, 25 subtests passed in 254.47s (0:04:14)` (2026-11-06T15:02:40Z-15:06:55Z, head `f1f695bb`). The first full run (head `dfbecdc4`) had `1 failed, 3808 passed`: the pin test `tests/test_repo_name.py::test_no_live_file_names_the_old_repo` flagged the fork-fallback URL in `lib/harness.ps1:75`; allowed with a reason in `f1f695bb`, as setup.sh's line is |
| Negative cases hold | ☑ pass | Review fixes, red first (tests on disk, `lib/harness.ps1` unchanged): `3 failed, 23 passed in 36.60s`. The failures were `test_an_exclusion_outside_the_project_stops_before_any_write` and `test_held_excluded_content_survives_a_failed_move[restore]`/`[hold]`: own files deleted. Green after the fix. Red first (2026-11-06T14:47:24Z, before any implementation commit): `21 failed, 1 passed in 5.25s` (see BEFORE). SC 6 mutation control, in the static test: injecting `& python3 -c ...`, `git status && git log`, `$a ?? 'b'`, `& sh -c`, `/dev/null`, a non-ASCII char, `Get-Content \| Set-Content`, and dropping StrictMode or `$ErrorActionPreference = 'Stop'` each make `problems()` non-empty: 9 passed. Behaviour mutation, by hand: `lib/harness.ps1 \| 2 +-` (Backup-HarnessPath's first line replaced by `return`) → `FAILED ...test_the_windows_ci_smoke_passes_in_linux_pwsh`, `FAILED ...test_edited_file_is_backed_up_and_a_rerun_is_idempotent`, `2 failed, 6 deselected`; reverted with `git checkout`. Workflow mutations (`shell: powershell` → `pwsh`, smoke run removed) are caught by `test_windows_ci_workflow.py` (17 passed) |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | After the review fixes: `3812 passed, 25 subtests passed in 227.44s` (+3 review tests). Before them: `python3 -m pytest .claude/hooks/tests tests -q` → `3809 passed, 25 subtests passed in 254.47s` (base: `3784 passed`; +25 = 23 new + 2 workflow mutations). `git diff --stat windows -- setup.sh update.sh 'lib/*.sh' lib/merge-settings.py lib/windows_hooks.py .claude/hooks` → empty (AC 15). Shell suites (`tests/*.sh`) not run by this agent |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: a command-line installer |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI: a command-line installer |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI: a command-line installer |


## Review fixes

Stage 4 found P1, P2 and P3; all three are fixed in the commit `fix(T268): review P1-P3`. The implementing agent wrote the tests first and showed them red.
- **P1** (`Install-HarnessExcluding`): one `try` now covers both the hold loop and the replace. Each move back has its own `try/catch`. The work folder is deleted only when everything was put back. If a move back fails, the folder is kept, two `[error]` lines name `<work>/held`, and the run stops (`HarnessStop`). Test: `test_held_excluded_content_survives_a_failed_move[restore|hold]` forces the failure with an overridden `Move-HarnessItem`.
- **P2**: `Assert-HarnessSafeRel` now checks every MANIFEST path and every `!` exclusion. It rejects an empty path, a leading `/`, a `\`, a `:` and a `..` segment. The plan screen reads both kinds of line before the first write, so a bad line stops the run with nothing written. Test: `test_an_exclusion_outside_the_project_stops_before_any_write`.
- **P3**: the second run now keeps the same hook entry count and the user's `Stop` hook. The check is in `test_edited_file_is_backed_up_and_a_rerun_is_idempotent` and in `tests/windows/smoke-install.ps1` run 2. It passed before the fix: this adds coverage, not a code change.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by the implementing agent in the worktree on branch `feat/t268-setup-ps1` at
`e781f503`, before any implementation commit):

```
2026-11-06T14:43:08Z
$ ls setup.ps1 lib/harness.ps1
ls: cannot access 'setup.ps1': No such file or directory
ls: cannot access 'lib/harness.ps1': No such file or directory
exit=2
$ grep -nE "^\s+- (uses|name):" .github/workflows/windows.yml
31:      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
36:      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
40:      - name: Install pytest and PyYAML
43:      - name: Python tests
$ python3 -m pytest .claude/hooks/tests tests -q
3784 passed, 25 subtests passed in 196.58s (0:03:16)
2026-11-06T14:46:25Z
```

The new tests, written first, red against the base (no `setup.ps1` yet):

```
2026-11-06T14:47:24Z
$ python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py -q
FAILED tests/test_setup_ps1_static.py::test_installer_source_is_51_safe_and_posix_free[setup.ps1]
FAILED tests/test_setup_ps1_static.py::test_installer_source_is_51_safe_and_posix_free[lib/harness.ps1]
FAILED tests/test_setup_ps1_static.py::test_smoke_script_is_51_safe - Asserti...
FAILED tests/test_setup_ps1_static.py::test_setup_ps1_dot_sources_the_library_and_calls_both_helpers
FAILED tests/test_setup_ps1_static.py::test_mutation_control_a_missing_header_is_caught[...] (x2)
FAILED tests/test_setup_ps1_static.py::test_mutation_control_a_banned_token_is_caught[...] (x7)
FAILED tests/test_setup_ps1_pwsh.py::test_the_windows_ci_smoke_passes_in_linux_pwsh
FAILED tests/test_setup_ps1_pwsh.py::test_install_matches_the_manifest_and_setup_sh
FAILED tests/test_setup_ps1_pwsh.py::test_edited_file_is_backed_up_and_a_rerun_is_idempotent
FAILED tests/test_setup_ps1_pwsh.py::test_python_is_found_when_py_and_python3_are_absent
FAILED tests/test_setup_ps1_pwsh.py::test_no_usable_python_stops_with_nothing_written[bin-nopy]
FAILED tests/test_setup_ps1_pwsh.py::test_no_usable_python_stops_with_nothing_written[bin-stub]
FAILED tests/test_setup_ps1_pwsh.py::test_outside_a_git_repo_stops_with_nothing_written
FAILED tests/test_setup_ps1_pwsh.py::test_existing_install_without_consent_cancels
21 failed, 1 passed in 5.25s
```

**AFTER** (same commands, implementing agent, worktree, heads `dfbecdc4` then `f1f695bb`):

```
2026-11-06T14:57:17Z
$ ls setup.ps1 lib/harness.ps1
lib/harness.ps1
setup.ps1
$ grep -nE "^\s+- (uses|name):" .github/workflows/windows.yml
31:      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
36:      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
40:      - name: Install pytest and PyYAML
43:      - name: Python tests
48:      - name: setup.ps1 smoke (Windows PowerShell 5.1)
54:      - name: setup.ps1 smoke (PowerShell 7)
$ python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py -q
23 passed in 38.98s
2026-11-06T15:02:40Z
$ python3 -m pytest .claude/hooks/tests tests -q
3809 passed, 25 subtests passed in 254.47s (0:04:14)
2026-11-06T15:06:55Z
```

Linux pwsh 7.4.2 (Docker) run of `tests/windows/smoke-install.ps1`, excerpt of run 3 (an edited AGENTS.md):

```
  | Plan: Reinstall Easy Kit into /tmp/easykit smoke é 6fec028b
  |   - Existing paths that differ from the kit are moved aside first:
  |       AGENTS.md -> AGENTS.md.bak-97d86c2
  | [warn]  Backed up your existing './AGENTS.md' to './AGENTS.md.bak-97d86c2' before installing the kit's copy - compare and merge by hand, then delete the backup.
  | [warn]  Could not create a junction at './.claude/skills' (the junction was not created).
  | [warn]  Copied './skills' to './.claude/skills' instead. Re-run setup.ps1 after './skills' changes, or Claude Code reads an old copy.
  | [info]  Easy Kit hooks in ./.claude/settings.json run through 'py' (Windows form).
  | [info]  Wrote ./.claude/harness-lock.json (147 file hashes).
SMOKE PASS
```

Not yet observed: the Windows CI smoke (junction, PowerShell 5.1, `core.symlinks=false`, CRLF) has not run.

**DELTA**: A Windows user with Git, Python and PowerShell can install or reinstall Easy Kit for Claude Code with `setup.ps1`, without Bash or WSL (Windows behaviour pending the first CI run).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
