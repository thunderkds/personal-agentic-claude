# TASK_GUIDE — T274: The test suite is honest on Windows: skip what a machine cannot do, normalize paths
**Date**: 2026-11-07
**Complexity Level**: C2
**Risk Level**: Low
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
7. Read `conftest.py` (the `posix_only` marker) and `tests/test_windows_ci_workflow.py` (the shape test of the marker)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-07: continue the Windows migration to a beta release. Evidence: a real Windows 11 run (Python 3.15, no Developer Mode) of `py -3 -m pytest tests .claude\hooks\tests -q` gave `63 failed, 1111 passed, 184 skipped` before a Ctrl-C (a test hangs; location not yet known). The installer, update and the T272 preflight passed on that machine.

**Restated intent**:
> On a Windows machine, a red test must mean a kit bug. Today 53 of 63 failures are test problems: the test needs a thing the machine may lack (a symlink right, bash, a legal file name, `rm`), or it compares a path with the wrong separator, or a fake tool has no `.cmd` suffix. Fix the tests, never the product code, so a Windows run shows only real defects.

**Decisions already made (do not reopen)**:
- Fix the tests, not the product. The product prints paths the way the OS does; the tests normalize.
- A new marker `needs_symlinks(reason)` in `conftest.py`: it skips a test when this machine cannot create a symlink (probe once per session in a temp dir; cache the answer). GitHub's Windows runner can, so these tests still run in CI. It skips with the written reason, like `posix_only`; an empty reason is a collection error.
- A new marker `needs_bash(reason)`: skips when `bash -c "exit 0"` does not run (the WSL launcher stub in System32 exists but fails; probe by running it, not by `shutil.which`). Same cache and reason rule.
- Illegal file names (newline, tab, `|`, ESC in a name): `posix_only` with the reason.
- Do not touch `tests/test_plugin_source.py`, `tests/test_auto_verify.py::test_ac5_*` (T276) or the spawn-hook regex in `tests/test_plugin_names.py::test_spawn_hook_names_the_scripts...` (T275).

**Out of scope (cut list)**: any product code, `.github/workflows/`, `tests/test_windows_ci_workflow.py` (T277 edits it; put the marker's shape test in a new file), the hang (the user sends the `--timeout` run), the 114 `posix_only` auto-verify tests.

**Requirement Refs**: `docs/windows-parity.md` (Skip inventory, Next steps 2); user log of 2026-11-07.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-07)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T272, T273 (merged into `windows`)

**Entry point**: Standalone — N/A (test suite only)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `conftest.py` has `needs_symlinks(reason)` and `needs_bash(reason)`. Each skips with the reason when its probe fails, never skips when it passes, and raises a collection error on an empty reason. The probe runs once per session | markers |
| 2 | A new `tests/test_windows_markers.py` proves AC 1 on Linux by monkeypatching the probe (`os.symlink` raising `OSError(1314)`; `subprocess.run` for bash returning non-zero), including the empty-reason error | markers |
| 3 | Every test that calls `symlink_to` / `os.symlink` or runs `dotfiles.py` apply (it links) carries `needs_symlinks`: the ~30 in `tests/test_dotfiles.py` and the 2 in `tests/test_plugin_names.py` (`test_every_skill_dir_path_exists_in_the_setup_install_layout`, `test_every_skill_dir_command_runs[install]`). List each decorated test in the Evidence | 32 failures |
| 4 | The 7 `tests/test_ci_verify_done_tasks.py` tests carry `needs_bash` (the script runs `bash -c`) | 7 failures |
| 5 | The 4 illegal-file-name tests (`test_dotfiles.py::test_t230_a_skill_folder_name_with_unprintable_text_is_refused` x3, `test_self_review.py::test_fx9_odd_review_file_name_is_ignored`) carry `posix_only("<reason naming the characters>")` | 4 failures |
| 6 | `tests/test_dirty_worktrees.py::test_sc5_missing_worktree_dir` uses `shutil.rmtree`, not `rm -rf` | 1 failure |
| 7 | `tests/test_companion_setup.py` `_run` writes each fake tool as `<tool>.cmd` (`@exit /b 0`) when `os.name == "nt"` and the extensionless `sh` file otherwise, and sets `PATHEXT` in `env` on Windows | 1 failure |
| 8 | The path-separator failures compare normalized paths: `test_board_create.py::test_cache_is_named_by_the_board_id...`, `test_board_id_pattern.py` (2), `test_dirty_worktrees.py` (`test_sc1...`, `test_subfolder_run_finds_board`), `test_self_review.py::test_ac10_default_report_path`, `test_plugin_init.py` (`test_ac1...`, `test_ac2...`: compare stdout after `.replace("\\", "/")`). Use `os.path.normpath` or `Path.as_posix()`; do not weaken what is asserted | 8 failures |
| 9 | On Linux the suite has the same pass count as before plus the new marker tests; nothing is newly skipped on Linux | Surgical Changes |
| 10 | No file under `.claude/hooks/*.py`, `lib/`, `scripts/`, `skills/` changed | cut list |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Probe patched to fail | Marked tests skip with the reason | `tests/test_windows_markers.py` |
| 2 | Probe passes (Linux) | Marked tests run | full suite |
| 3 | Empty reason | Collection error | `tests/test_windows_markers.py` |
| 4 | The decorator removed from one dotfiles test, probe patched to fail (mutation) | The marker test goes red | mutation control |
| 5 | The Windows run (user) | The 53 test-side failures are gone | user re-runs `py -3 -m pytest tests .claude\hooks\tests -q --timeout=60` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests tests -q
```

This machine is Linux. Windows-only behavior cannot be proven here; say so in the Evidence and name what the user must re-run on Windows.

---

## Approach

**Vital slice**: the two markers and AC 3, 4 (39 of 53 failures), then AC 5-8. Tests first for the markers (red), then code.
**Pattern reference**: `conftest.py` `posix_only`.

---

## Edge Case Checklist

- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `docs/windows-support-plan.md`, `docs/windows-parity.md` for text the change makes false
- [ ] A test with both `posix_only` and `needs_symlinks` keeps both reasons
- [ ] The marker works on a class and as `pytestmark`
- [ ] The probe leaves no temp file behind

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `conftest.py` | The two markers and probes |
| `tests/test_windows_markers.py` | New: marker tests |
| `tests/test_dotfiles.py`, `tests/test_plugin_names.py`, `tests/test_ci_verify_done_tasks.py`, `tests/test_self_review.py`, `tests/test_dirty_worktrees.py`, `tests/test_companion_setup.py`, `tests/test_board_create.py`, `tests/test_board_id_pattern.py`, `tests/test_plugin_init.py` | Markers and normalization only |
| Pre-existing pin tests | Grep for pins on `conftest.py` text or marker names; handle each |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py`, `lib/*`, `scripts/*`, `skills/*`, `.github/workflows/*` | Product code and CI |
| `tests/test_windows_ci_workflow.py`, `tests/test_plugin_source.py`, `tests/test_auto_verify.py` | T276, T277 |
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
| New test(s) cover acceptance criteria | ☐ | |
| Test suite passes (verification command above) | ☐ | |
| Mutation control goes red | ☐ | |
| Pre-existing pin tests | ☐ | |
| UI: visual regression | ☐ N/A (no UI) | |
| UI: design-system compliance | ☐ N/A (no UI) | |
| UI: responsiveness | ☐ N/A (no UI) | |
