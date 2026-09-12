# TASK_REVIEW — T109: CI runs every install/update shell suite, and the one it would have caught is fixed

> Sibling of `tasks/TASK_GUIDE_T109.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_ci_wires_shell_suites.py` (new, AC4/AC5) + fixed `tests/test_install_update_smoke.sh` (AC1). `python3 -m pytest tests/test_ci_wires_shell_suites.py -v`: `test_every_real_suite_is_wired_or_excluded PASSED`, `test_every_ci_referenced_suite_exists PASSED`, `test_excluded_suites_still_exist_and_are_really_excluded PASSED` — 3 passed. |
| Verification command run | ☑ pass | Every guide line run separately, own exit status read (no `\| tail`): `rc=0 test_setup.sh :: 18 passed, 0 failed`; `rc=0 test_update.sh :: 31 passed, 0 failed`; `rc=0 test_install_update_smoke.sh :: 9 passed, 0 failed`; `rc=0 test_t098_harness_presence.sh :: 20 passed, 0 failed`; `rc=0 test_pack_choice_parsing.sh :: 15 passed, 0 failed`; `rc=0 test_ci_wires_shell_suites.py :: 3 passed`; `python3 -m pytest .claude/hooks/tests/ tests/ -q :: 1 failed, 847 passed` (the failure is `tests/test_readme_slim.py::test_readme_is_at_most_75_lines`, README 83>75, pre-existing per T115, guide's expected exception). |
| Negative cases hold | ☑ pass | **M1** (AC6): reverted the smoke-suite fix in the working tree only (`git revert --no-commit c4b8eaa`), confirmed via `git diff --stat` the mutation landed, then ran the suite: `FAIL: AC1: MANIFEST path 'skills          codex=.codex/skills' missing from target after setup.sh` — `8 passed, 1 failed`, `rc=1`. Restored via `git checkout HEAD -- tests/test_install_update_smoke.sh` (re-confirmed 9/9, rc=0). **M2** (AC7): deleted the `Pack choice parsing test suite` step from `ci.yml` (confirmed via `git diff --stat` → `1 file changed, 2 deletions(-)`), ran the drift test: `test_every_real_suite_is_wired_or_excluded FAILED` — `AssertionError: tests/*.sh suite(s) neither run by ci.yml nor listed in EXCLUDED_SUITES with a reason: test_pack_choice_parsing.sh`, naming exactly the removed suite. Restored via `git checkout HEAD -- .github/workflows/ci.yml` (re-confirmed 3 passed). **Fake-suite control** (Success Criterion #4): created untracked `tests/test_zz_new.sh` (not wired, not excluded), drift test failed naming it (`AssertionError: ... test_zz_new.sh`), then deleted the file (confirmed via `git status --short` showing it gone, no residue). |
| verify | ☐ pass / ☐ fail / ☐ N/A | User-run per `memory/MEMORY.md` (`project_verify_skill_is_user_only.md`) — not run by this agent. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Touched only: `tests/test_install_update_smoke.sh` (AC1's own field-1 fix), `.github/workflows/ci.yml` (7 new named steps, no other line touched — `ci.yml:19` shellcheck list and its file untouched), `tests/test_ci_wires_shell_suites.py` (new). No edit to `setup.sh`, `update.sh`, `lib/harness-fetch.sh`, `MANIFEST`, `README.md`, `tests/test_readme_slim.py`, or `tests/test_shellcheck_clean.sh`. |
| Full smoke suite still green (no regression) | ☑ pass | `tests/test_install_update_smoke.sh`: `9 passed, 0 failed`, rc=0 (was 8/1 before the fix). All other 4 mandatory suites unchanged at 0 failed. Full Python suite: 847 passed, 1 pre-existing failure (T115, unrelated). |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ N/A | CI and tests only; no user-facing behaviour or instruction changed |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | CI config + test files only; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit):

```
rc=0 tests/test_setup.sh                 :: ----- summary: 18 passed, 0 failed -----
rc=0 tests/test_update.sh                :: ----- summary: 31 passed, 0 failed -----
rc=1 tests/test_install_update_smoke.sh  :: 8 passed, 1 failed
rc=0 tests/test_pack_choice_parsing.sh   :: ----- summary: 15 passed, 0 failed -----
rc=0 tests/test_t098_harness_presence.sh :: 20 passed, 0 failed
(none of these in ci.yml)

FAIL: AC1: MANIFEST path 'skills          codex=.codex/skills' missing from target after setup.sh
```

**BEFORE re-run** (Common-Infrastructure-Agent, 2026-09-12T10:26:01Z, worktree `wt-t109`, branch `fix/t109-ci-suites` @ `ad8d71c`, before any implementation commit):

```
rc=0 tests/test_setup.sh                 :: ----- summary: 18 passed, 0 failed -----
rc=0 tests/test_update.sh                :: ----- summary: 31 passed, 0 failed -----
rc=1 tests/test_install_update_smoke.sh  :: 8 passed, 1 failed
rc=0 tests/test_t098_harness_presence.sh :: 20 passed, 0 failed
rc=0 tests/test_pack_choice_parsing.sh   :: ----- summary: 15 passed, 0 failed -----

FAIL: AC1: MANIFEST path 'skills          codex=.codex/skills' missing from target after setup.sh
```

**AFTER** (Common-Infrastructure-Agent, 2026-09-12, worktree `wt-t109` @ `37a2435`, post-implementation):

```
rc=0 tests/test_setup.sh                       :: ----- summary: 18 passed, 0 failed -----
rc=0 tests/test_update.sh                      :: ----- summary: 31 passed, 0 failed -----
rc=0 tests/test_install_update_smoke.sh        :: 9 passed, 0 failed
rc=0 tests/test_t098_harness_presence.sh       :: 20 passed, 0 failed
rc=0 tests/test_pack_choice_parsing.sh         :: ----- summary: 15 passed, 0 failed -----
rc=0 tests/test_harness_fetch.sh               :: ----- summary: 9 passed, 0 failed -----
rc=0 tests/test_readme_current.sh              :: test_readme_current: ALL PASS
rc=0 python3 -m pytest tests/test_ci_wires_shell_suites.py -q  :: 3 passed
(all 7 wired as their own named ci.yml step; test_shellcheck_clean.sh excluded with a checkable reason)
```

**DELTA**: CI now runs all seven installer shell suites as their own named steps and fails the exact suite that regresses, instead of silently passing on a broken installer test forever (the one that was already red — `test_install_update_smoke.sh`'s AC1 — is fixed and now gates every future push).

**WITNESS**: Common-Infrastructure-Agent, 2026-09-12T10:26–~10:40Z UTC, run in worktree `wt-t109` on `fix/t109-ci-suites`.
