# TASK_GUIDE — T277: `block-dangerous-git` gets a Python twin; `validate.sh` runs in the Windows job under Git Bash
**Date**: 2026-11-07
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`
6. Read `docs/windows-support-plan.md`, `docs/adr/0003-native-windows-support.md` and `docs/windows-parity.md` (the ledger: it says how each file is proven on Windows)
7. Read `skills/git-guardrails-claude-code/SKILL.md` and `skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh` (25 lines), `lib/windows_hooks.py`, `.github/workflows/windows.yml` and `tests/test_windows_ci_workflow.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-07: continue the Windows migration to a beta release. Evidence: a real Windows 11 run (Python 3.15, no Developer Mode) of `py -3 -m pytest tests .claude\hooks\tests -q` gave `63 failed, 1111 passed, 184 skipped` before a Ctrl-C (a test hangs; location not yet known). The installer, update and the T272 preflight passed on that machine.

**Restated intent**:
> The git-guardrails hook is a safety hook that blocks `git push`, `reset --hard` and similar. It exists only as a `.sh` file, so on Windows without bash it does nothing. Give it a Python twin with the same decisions, and let the skill install the right form. Also run the repo's own gate `scripts/validate.sh` in the Windows job under Git Bash (installed on `windows-latest`), as a separate job so its result is visible on its own.

**Decisions already made (do not reopen)**:
- The Python twin `skills/git-guardrails-claude-code/scripts/block-dangerous-git.py`: reads the hook JSON from stdin, blocks the same patterns as the `.sh`, exits 2 with the same BLOCKED text on stderr, exits 0 otherwise. Stdlib only. Parse the command with the same rules the `.sh` uses (read it end to end first); do not invent new patterns.
- The skill (`SKILL.md`) step 2/3 tells the installer which file to copy: the `.sh` on POSIX, the `.py` on Windows, and for the `.py` it registers the hook in the exec form (`command: "py"`, `args: ["-3", "<path>"]`, as `lib/windows_hooks.py` writes). Keep the text short.
- CI: a new job `Repo gate (Git Bash)` in `.github/workflows/windows.yml` on `windows-latest`, `shell: bash`, running `bash scripts/validate.sh`. It is a separate job with its own name so a red result is not mixed with `Python tests (Windows)`. Do not mark it `continue-on-error`.
- The `.sh` and `.py` must agree: a parity test feeds the same list of commands to both (the `.sh` part is `posix_only`) and compares exit codes.

**Out of scope (cut list)**: other `.sh` scripts (`test-agent-template.sh`, `test-claude-md-refs.sh`, `token-audit.sh`, `tests/*.sh`), changing the blocked pattern list, `settings.json` of this repo, `site/`.

**Requirement Refs**: `docs/windows-parity.md` rows `block-dangerous-git.sh` and `validate.sh`; `docs/adr/0003-native-windows-support.md`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-07)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T272, T273 (merged into `windows`)

**Entry point**: `skills/git-guardrails-claude-code/SKILL.md` (Stage 1 setup) and `.github/workflows/windows.yml`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `block-dangerous-git.py` exits 2 with a BLOCKED message for each pattern the `.sh` blocks, and exits 0 for safe commands (`git status`, `git log`, `git commit`, `git push` inside a quoted string of `echo`, if the `.sh` allows it). A table-driven test lists at least 20 commands | the twin |
| 2 | Parity: on POSIX the same command table gives the same exit code from the `.sh` (run through `bash`) and the `.py`. The `.sh` half is `posix_only` | parity |
| 3 | Bad input: empty stdin, invalid JSON, missing `tool_input` or `command`: exit 0 (never block on a hook error) and no traceback. Match what the `.sh` does; if the `.sh` blocks, match that and say so | robustness |
| 4 | `SKILL.md` names both files and the exec-form registration for Windows. A test checks the `.py` path appears in the skill text | skill |
| 5 | The registration JSON the skill shows for Windows passes `lib/windows_hooks.py`'s own shape (command `py`, args start with `-3`). Test it by calling the converter's exec-form check, not by string match alone | Windows form |
| 6 | `.github/workflows/windows.yml` has the job `Repo gate (Git Bash)` (`windows-latest`, `shell: bash`, `bash scripts/validate.sh`, no `continue-on-error`). `tests/test_windows_ci_workflow.py` is extended to prove it (the job exists, the step runs `validate.sh`, no `continue-on-error`) and still passes for the other jobs | CI |
| 7 | The `.github/workflows/windows.yml` change is checked for YAML validity (`yaml.safe_load` in the test; the test file already uses `pytest.importorskip("yaml")`) | CI |
| 8 | `scripts/validate.sh` and the `.sh` hook are byte-identical to the base | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | `git push origin main` on stdin | exit 2, BLOCKED on stderr | table test |
| 2 | `git status` | exit 0 | table test |
| 3 | Same table through `.sh` and `.py` | equal exit codes | parity test |
| 4 | A pattern removed from the `.py` (mutation) | the table test goes red | mutation control |
| 5 | The Windows run (GitHub, after the push) | job `Repo gate (Git Bash)` shows a result | the PR |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests tests -q
```

This machine is Linux. Windows-only behavior cannot be proven here; say so in the Evidence and name what the user must re-run on Windows.

---

## Approach

**Vital slice**: the `.py` + table test (AC 1-3), then the skill text (AC 4-5), then CI (AC 6-7). Tests first (red).
**Pattern reference**: the existing `.sh`; `lib/windows_hooks.py` for the exec form; `tests/test_windows_ci_workflow.py` for workflow shape tests.

---

## Edge Case Checklist

- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `docs/windows-support-plan.md`, `docs/windows-parity.md` for text the change makes false
- [ ] A command with `git push` inside quotes or a heredoc: copy the `.sh` behavior exactly, state which it is
- [ ] `git push --force-with-lease`, `git -C dir push`, `git  push` (two spaces): the `.sh` decides; match it
- [ ] CRLF in `.gitattributes` for the new `.py` (LF)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/git-guardrails-claude-code/scripts/block-dangerous-git.py` | New |
| `skills/git-guardrails-claude-code/SKILL.md` | Steps 2-3 |
| `tests/test_git_guardrails_py.py` | New: table, parity, input robustness, skill text |
| `.github/workflows/windows.yml`, `tests/test_windows_ci_workflow.py` | The new job and its shape test |
| Pre-existing pin tests | Grep for pins on the skill text, `MANIFEST` (does it list `skills/` as a whole?), the workflow job list, and the skill-body size cap (Codex 8 KB) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `scripts/validate.sh`, `skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh` | Fixed behavior |
| `.claude/settings.json`, `lib/windows_hooks.py` | Not this task |
| `docs/windows-parity.md`, `docs/windows-support-plan.md`, `memory/`, `PROJECT_KANBAN.md` | Supervisor |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (if your toolset has no Skill tool, say so; the Supervisor reviews)
- [ ] Lint passes
- [ ] No unrelated files modified
- [ ] Evidence table below filled in

---

## Evidence (fill in before Ready for Review)

| Item | Result | Pasted evidence |
|------|--------|-----------------|
| New test(s) cover acceptance criteria | ☑ pass | `tests/test_git_guardrails_py.py` (AC 1-5: 45-row table, `.sh` parity incl. stderr text, 14 bad-input cases, skill text, converter exec-form check) and `tests/test_windows_ci_workflow.py` (AC 6-7: `_gate_problems` plus 7 new mutation controls). Red first: `122 failed, 3 passed` before the `.py` existed; `8 failed, 18 passed` before the job existed. Green: `python3 -m pytest tests/test_git_guardrails_py.py tests/test_windows_ci_workflow.py -q` -> `151 passed in 3.08s` |
| Test suite passes (verification command above) | ☑ pass, with 2 failures outside this task's reach | `python3 -m pytest .claude/hooks/tests tests -q` -> `2 failed, 3980 passed, 25 subtests passed in 383.57s`. Both failures are in `tests/test_windows_parity_ledger.py`, which reads `docs/windows-parity.md` (Supervisor-owned, not edited here): (1) `test_every_repo_file_in_scope_has_a_row`: `no ledger row names: block-dangerous-git.py`; (2) `test_skip_inventory_matches_the_posix_only_marks_in_the_tests`: the table lacks `tests/test_git_guardrails_py.py` (3 lines) and, from before this task (T272 merge), `tests/test_setup_ps1_preflight_pwsh.py` (1 line). The Supervisor adds the ledger rows. Not proven here (Linux host): the Windows runs. The user must check on the PR that job `Repo gate (Git Bash)` shows a result (it may be red: `scripts/validate.sh` section 5 requires `.claude/skills` and `.claude/agents` to be symlinks, and a Windows checkout may not create them) and that `Python tests (Windows)` runs `tests/test_git_guardrails_py.py` (the 3 `.sh` parity tests skip there by `posix_only`; the table, bad-input and skill tests must pass). |
| Mutation control goes red | ☑ pass | Deleted the `"git branch -D",` line from the `.py` (`1 file changed, 1 deletion(-)`): `FAILED test_py_hook_decides_like_the_table[git branch -D old]`, `FAILED test_py_and_sh_agree_on_exit_code_and_message[git branch -D old]`, `2 failed, 123 passed`; restored: `125 passed`. Workflow: 7 new parametrized mutations (job renamed, `ubuntu-latest`, job-level and step-level `continue-on-error`, step replaced by `echo skipped`, `shell: pwsh`) all caught |
| Pre-existing pin tests | ☑ pass | Grepped tests for `git-guardrails`/`block-dangerous`: `tests/test_plugin_names.py` (skills use `${CLAUDE_SKILL_DIR}`, each path exists: step 2 now names both files under it, both exist), `tests/test_windows_gitattributes.py` (`.sh` LF; `*.py text eol=lf` already covers the new file, checked by my test with `git check-attr`), `.claude/hooks/tests/test_skill_spec_conformance.py` (`scripts/` is not a skill), the 8192-byte Codex cap (`SKILL.md` 2507 -> 3367 bytes; my test caps at 6000). `MANIFEST` lists `skills` as a whole, so the new file ships with no edit. All pass in the full run above. `scripts/validate.sh` and the `.sh` hook: `git diff --stat` on both is empty (AC 8) |
| UI: visual regression | ☐ N/A (no UI) | |
| UI: design-system compliance | ☐ N/A (no UI) | |
| UI: responsiveness | ☐ N/A (no UI) | |
