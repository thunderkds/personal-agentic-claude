# TASK_GUIDE — T272: `setup.ps1` checks the fetched kit before it changes the project
**Date**: 2026-11-07
**Complexity Level**: C1
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
6. Read `tasks/TASK_GUIDE_T268.md` (the installer) and `tasks/TASK_REVIEW_T268.md`
7. Read `setup.ps1` (the whole `Invoke-Setup` flow, lines 225-330) and `lib/harness.ps1` `Install-HarnessSettings` (lines 564-604)

---

## Requirement (Pillar 1 — Adapt the requirement)

Evidence from the user's real Windows machine, 2026-11-07 (install into an existing project, "Existing / legacy project"):

```
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[error] The fetched Easy Kit has no lib/windows_hooks.py, so the hooks keep their POSIX form and do not run on Windows.
[info]  Wrote ./.claude/harness-lock.json (145 file hashes).
[info]  Setup complete. Easy Kit copied into D:\workspace\easy\easy-kit
[error] Setup finished, but Easy Kit hooks were NOT wired (see the message above).
```

Cause: `setup.ps1` clones the default branch of `easy-kit`. That branch has no `lib/windows_hooks.py` yet (the Windows work lives on branch `windows`). `Install-HarnessSettings` finds this only after the installer has moved the user's `.claude/hooks`, `.claude/skills`, `.claude/agents`, `CLAUDE.md`, `scripts/verify_trace.py` and `docs/claude-md` aside, copied the kit in, and merged POSIX-form hooks into `.claude/settings.json`. The project is left half installed.

**Restated intent**:
> When the fetched kit lacks a file the Windows installer needs, `setup.ps1` stops right after the fetch with a clear error and changes nothing in the project, on every action (install, reinstall, update). This matches the rule already written in `setup.ps1`: every question and every check comes before any project write.

**Decisions already made (do not reopen)**:
- User, 2026-11-07: "yes" to a small fix task for this preflight.
- Check these files in the fetched clone, right after the `MANIFEST` check in `setup.ps1`: `lib/windows_hooks.py` and `lib/merge-settings.py`. Both are read from the clone later by `Install-HarnessSettings`; neither is in the `MANIFEST`.
- Exit code 1, same style as the `MANIFEST not found` error. The message names the missing file and says the fetched kit is too old for Windows (it has no Windows support yet), so the user knows to wait for a kit release or point `SUPERVISOR_REPO` at a kit that has it.
- Keep the late check in `Install-HarnessSettings` as it is (defense in depth). Do not remove it.

**Out of scope (cut list)**: a `-Ref`/branch option for the fetch, any change to `setup.sh`, `update.sh`, `lib/*.sh`, `lib/*.py`, undoing an earlier half install, changing the "Setup complete" wording of other failure paths.

**Requirement Refs**: `docs/windows-support-plan.md` T-W7; `docs/adr/0003-native-windows-support.md` decision 3. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-07)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T268, T271 (merged into `windows`)

**Entry point**: `setup.ps1` (and `update.ps1`, which runs it)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | With a fetched kit that has no `lib/windows_hooks.py`, `setup.ps1 -Yes` (install into an existing project that has its own `.claude/hooks`, `CLAUDE.md`, `.claude/settings.json`) exits 1, prints an error naming `lib/windows_hooks.py`, and the project tree is byte-identical to before (no `.bak-*`, no lock, no moved paths, no settings change) | the log above |
| 2 | Same for a kit that has no `lib/merge-settings.py` | Decision: both files checked |
| 3 | The same stop happens for the Reinstall and the Update action (an installed project with a lock; project tree unchanged) | "on every action" |
| 4 | A full kit (both files present) installs exactly as before: all existing `tests/test_setup_ps1_pwsh.py` and `tests/test_update_ps1_pwsh.py` tests pass unchanged | Surgical Changes |
| 5 | The check runs before the action menu and before any prompt, so a non-interactive run never asks a question first | "after the fetch, before any write" |
| 6 | `setup.sh`, `update.sh`, `lib/*.sh`, `lib/*.py` are byte-identical to the base | Surgical Changes |
| 7 | Same hygiene as T268: 5.1-safe syntax, pure ASCII, no BOM, no CRLF; `tests/test_setup_ps1_static.py` passes | T268 AC 15 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Local fake kit without `lib/windows_hooks.py`; existing project with own hooks and `CLAUDE.md` | Exit 1, error names the file, project tree hash unchanged | Docker pwsh test (reuse the harness of `tests/test_setup_ps1_pwsh.py`) |
| 2 | Fake kit without `lib/merge-settings.py` | Same | Docker pwsh test |
| 3 | Installed project (lock present), fake kit without `lib/windows_hooks.py`, action reinstall and update | Exit 1, tree unchanged | Docker pwsh test |
| 4 | The preflight removed (mutation) | Success Criterion 1 test goes red | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py tests/test_update_ps1_pwsh.py tests/test_windows_ci_workflow.py -q && python3 -m pytest .claude/hooks/tests tests -q
```

The Docker tests skip when the pinned pwsh image is absent. On this machine the image is pulled; say in the Evidence whether they ran or skipped.

---

## Approach

**Pattern reference**: the `MANIFEST not found` check in `setup.ps1` and `Test-HarnessFile` in `lib/harness.ps1`.

**Vital slice**: one small loop over the two required files right after the `MANIFEST` check, one test file with the three scenarios, one mutation control. Write the tests first (red), then the code.

---

## Edge Case Checklist

- [ ] Error text names the missing file and says what to do, in plain words
- [ ] The temp clone is still cleaned up on this exit path (as for the `MANIFEST` error)
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `docs/windows-support-plan.md` for text that says where the Windows file check happens

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.ps1` | The preflight after the `MANIFEST` check |
| `tests/test_setup_ps1_pwsh.py` (or a new `tests/test_setup_ps1_preflight_pwsh.py`) | The Docker pwsh scenarios and the mutation control |
| `tests/test_setup_ps1_static.py` | Only if it pins `setup.ps1` text |
| Pre-existing pin tests | Grep `tests/` and `.claude/hooks/tests/` for `setup.ps1` text pins; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/*.sh`, `lib/*.py` | Fixed behaviour |
| `lib/harness.ps1` | The late check stays as it is |
| `.claude/hooks/*` | Not this task |
| `docs/windows-support-plan.md`, `memory/`, `PROJECT_KANBAN.md` | Supervisor |

---

## Test Plan

The three Docker pwsh scenarios, the mutation control, the static test, the workflow shape test, the full Python suites. Windows-only behaviour is not touched by this change.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] No unrelated files modified
- [ ] Evidence table below filled in

---

## Evidence (fill in before Ready for Review)

| Item | Result | Pasted evidence |
|------|--------|-----------------|
| New test(s) cover acceptance criteria | ☑ | `tests/test_setup_ps1_preflight_pwsh.py`: `7 passed in 15.28s` (Docker pwsh RAN, image present; not skipped). Before the code: `6 failed, 1 passed in 16.03s` |
| Test suite passes (verification command above) | ☑ | 2026-11-07T04:32Z: `76 passed in 127.96s` (the guide's four files + the new one); `python3 -m pytest .claude/hooks/tests tests -q` -> `3845 passed, 25 subtests passed in 372.49s` |
| Mutation control goes red | ☑ | `test_sc4_mutation_control_...`: setup.ps1 copy without the fenced preflight -> project tree changes (moved `.claude/hooks`, lock written), so scenario 1 would fail; the real run leaves `changed/added paths: []` |
| Pre-existing pin tests | ☑ | `grep -rln setup.ps1 tests .claude/hooks/tests`: `test_windows_ci_workflow.py`, `test_setup_ps1_pwsh.py`, `test_setup_ps1_static.py`, `test_update_ps1_pwsh.py`; none pins the MANIFEST check or the new text; all pass unchanged |
| UI: visual regression | ☐ N/A (no UI) | |
| UI: design-system compliance | ☐ N/A (no UI) | |
| UI: responsiveness | ☐ N/A (no UI) | |
