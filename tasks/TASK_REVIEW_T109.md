# TASK_REVIEW — T109: CI runs every install/update shell suite, and the one it would have caught is fixed

> Sibling of `tasks/TASK_GUIDE_T109.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_ci_wires_shell_suites.py` (AC4/AC5/AC8/AC9/AC10, round 2 adds `test_ci_runs_the_drift_guard_itself` + `__main__` block + `run:`-line-only wiring) + fixed `tests/test_install_update_smoke.sh` (AC1) + one new `ci.yml` step (AC8). Round 2: `python3 -m pytest tests/test_ci_wires_shell_suites.py -v`: `test_every_real_suite_is_wired_or_excluded PASSED`, `test_every_ci_referenced_suite_exists PASSED`, `test_ci_runs_the_drift_guard_itself PASSED`, `test_excluded_suites_still_exist_and_are_really_excluded PASSED` — 4 passed. `python3 tests/test_ci_wires_shell_suites.py; echo rc=$?` → `4 passed, 0 failed`, `rc=0` (runs as CI will, no pytest). |
| Verification command run | ☑ pass | Every guide line run separately, own exit status read (no `\| tail`): `rc=0 test_setup.sh :: 18 passed, 0 failed`; `rc=0 test_update.sh :: 31 passed, 0 failed`; `rc=0 test_install_update_smoke.sh :: 9 passed, 0 failed`; `rc=0 test_t098_harness_presence.sh :: 20 passed, 0 failed`; `rc=0 test_pack_choice_parsing.sh :: 15 passed, 0 failed`; `rc=0 test_ci_wires_shell_suites.py :: 3 passed`; `python3 -m pytest .claude/hooks/tests/ tests/ -q :: 1 failed, 847 passed` (the failure is `tests/test_readme_slim.py::test_readme_is_at_most_75_lines`, README 83>75, pre-existing per T115, guide's expected exception). |
| Negative cases hold | ☑ pass | **M1** (AC6): reverted the smoke-suite fix in the working tree only (`git revert --no-commit c4b8eaa`), confirmed via `git diff --stat` the mutation landed, then ran the suite: `FAIL: AC1: MANIFEST path 'skills          codex=.codex/skills' missing from target after setup.sh` — `8 passed, 1 failed`, `rc=1`. Restored via `git checkout HEAD -- tests/test_install_update_smoke.sh` (re-confirmed 9/9, rc=0). **M2** (AC7): deleted the `Pack choice parsing test suite` step from `ci.yml` (confirmed via `git diff --stat` → `1 file changed, 2 deletions(-)`), ran the drift test: `test_every_real_suite_is_wired_or_excluded FAILED` — `AssertionError: tests/*.sh suite(s) neither run by ci.yml nor listed in EXCLUDED_SUITES with a reason: test_pack_choice_parsing.sh`, naming exactly the removed suite. Restored via `git checkout HEAD -- .github/workflows/ci.yml` (re-confirmed 3 passed). **Fake-suite control** (Success Criterion #4): created untracked `tests/test_zz_new.sh` (not wired, not excluded), drift test failed naming it (`AssertionError: ... test_zz_new.sh`), then deleted the file (confirmed via `git status --short` showing it gone, no residue). **Round 2 re-run**: M1 re-run after round-2 fix — same result, rc=1 (8/1) reverted, rc=0 (9/0) restored. M2 re-run — same result, drift test still fails naming `test_pack_choice_parsing.sh` (now 4-test suite: `1 failed, 3 passed`). **M3** (AC9/AC12): deleted the `Per-harness projection tests (T097)` step (kept in shellcheck line) — mutation confirmed via `git diff --stat` (`1 file changed, 3 deletions(-)`) — drift test now correctly **fails**, naming `test_harness_projection.sh` (`1 failed, 3 passed`); restored, diff clean. **M4** (AC9/AC12): added always-failing `tests/test_zz_comment_only.sh` plus `# TODO later: tests/test_zz_comment_only.sh` comment — mutation confirmed via `git diff --stat` (`1 file changed, 2 insertions(+)`) and `git status --short` (new file) — drift test **fails**, naming `test_zz_comment_only.sh`; both removed, `git status --short` clean. **M5** (AC10/AC12): deleted the new guard step from `ci.yml` — mutation confirmed via `git diff --stat` (`1 file changed, 3 deletions(-)`) — `test_ci_runs_the_drift_guard_itself` **fails** with the expected assertion message; restored, diff clean. **M6** (AC12): ran `python3 tests/test_ci_wires_shell_suites.py` (own exit status, no pipe) with untracked always-failing `tests/test_zz_unwired.sh` present → `1 failed, 3 passed`, `rc=1` (confirmed non-zero); file removed, `git status --short` clean. |
| verify | ☑ pass | **Round 2: pass** (user-run /verify, Supervisor-executed, 2026-09-12, @ `54babca`). Same method as round 1: every ci.yml run: step replayed in a fresh ubuntu:24.04 container from a git bundle, no git identity. R1 as-is → all 13 steps ok incl. `CI wires every shell suite (drift guard)` (4 passed), JOB RESULT: success. R2 unwired always-failing tests/test_zz_unwired.sh → fails only at the drift-guard step: `FAIL: test_every_real_suite_is_wired_or_excluded: … test_zz_unwired.sh`, JOB RESULT: failure (round 1: success). R3 projection run step deleted, still on shellcheck line → guard step FAILED naming `test_harness_projection.sh`. R4 failing suite mentioned only in a YAML comment → guard step FAILED naming `test_zz_comment_only.sh`. R5 guard step itself deleted → JOB RESULT: success (inherent: the self-check runs inside that step). R6 README-current step rewritten as `run: |` block → guard (run directly on that tree) fails naming `test_readme_current.sh` — a harmless YAML reformat breaks CI, loudly. Not a real Actions run (triggers are push-to-main/PR; gh unauthenticated; act absent). || **Round 1: fail** (user-run /verify, Supervisor-executed, 2026-09-12). Surface = CI workflow; replayed every ci.yml run: step in a fresh ubuntu:24.04 container on a bundle clone of 813902a (no git identity; apt instead of sudo apt-get). R1 as-is → JOB RESULT: success (all 12 steps ok). R3 appended exit 1 to tests/test_readme_current.sh → `STEP [README-current test suite] -> FAILED rc=1`, job failure. **R2 added an unwired always-failing tests/test_zz_unwired.sh → JOB RESULT: success** — no ci.yml step runs the drift guard. Probes on the guard: deleting the test_harness_projection.sh run step (still named on the shellcheck line) → 3 passed; comment-only mention → 3 passed; no mention (control) → failed as intended. Round 2 spawned with AC8–AC12. Not a real Actions run: triggers are push-to-main/PR, gh unauthenticated, act absent. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Touched only: `tests/test_install_update_smoke.sh` (AC1's own field-1 fix), `.github/workflows/ci.yml` (7 new named steps, no other line touched — `ci.yml:19` shellcheck list and its file untouched), `tests/test_ci_wires_shell_suites.py` (new). No edit to `setup.sh`, `update.sh`, `lib/harness-fetch.sh`, `MANIFEST`, `README.md`, `tests/test_readme_slim.py`, or `tests/test_shellcheck_clean.sh`. |
| Full smoke suite still green (no regression) | ☑ pass | `tests/test_install_update_smoke.sh`: `9 passed, 0 failed`, rc=0 (was 8/1 before the fix). All other suites (`test_setup.sh` 18/0, `test_update.sh` 31/0, `test_t098_harness_presence.sh` 20/0, `test_pack_choice_parsing.sh` 15/0, `test_harness_fetch.sh` 9/0, `test_readme_current.sh` all pass) unchanged, 0 failed. Round 2: full Python suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `1 failed, 848 passed` (only pre-existing `test_readme_slim.py::test_readme_is_at_most_75_lines`, README 83>75, T115, unrelated). |
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

**DELTA (corrected, round 2)**: CI now runs all seven installer shell suites as their own named steps
and fails the exact suite that regresses. That guarantee holds **only for suites already wired as a
`run:` step** — round 1's "now gates every future push" overclaimed: a suite added later without a
corresponding `ci.yml` step, or removed from `ci.yml`, was not itself caught at CI time. Round 2 closes
that gap: `ci.yml` now also runs `tests/test_ci_wires_shell_suites.py` as its own named step, and that
guard fails the build if any `tests/*.sh` file is neither wired nor explicitly excluded (or vice versa),
using only a literal `run: bash|sh tests/<name>.sh` line as "wired" — a mention in the shellcheck
argument list, a comment, or a step name no longer counts. So the actual guarantee is: any new or
deleted suite, or any suite silently un-wired, is caught by the drift-guard step failing the build; a
regression *inside* an already-wired suite is caught by that suite's own step failing.

**WITNESS**: Common-Infrastructure-Agent, 2026-09-12T10:26–~10:40Z UTC, run in worktree `wt-t109` on `fix/t109-ci-suites`.

**AFTER (round 2)** (Common-Infrastructure-Agent, 2026-09-12, worktree `wt-t109` @ `af9e620`, post round-2 implementation):

```
python3 -m pytest tests/test_ci_wires_shell_suites.py -v
  test_every_real_suite_is_wired_or_excluded PASSED
  test_every_ci_referenced_suite_exists PASSED
  test_ci_runs_the_drift_guard_itself PASSED
  test_excluded_suites_still_exist_and_are_really_excluded PASSED
  4 passed in 0.07s

python3 tests/test_ci_wires_shell_suites.py; echo rc=$?
  PASS x4
  ----- summary: 4 passed, 0 failed -----
  rc=0

ci.yml now has: "- name: CI wires every shell suite (drift guard)\n  run: python3 tests/test_ci_wires_shell_suites.py"
Probe A repeated post-fix (delete Per-harness projection step) -> guard now FAILS naming test_harness_projection.sh (M3)
Probe B repeated post-fix (comment-only mention + unwired suite) -> guard now FAILS naming the suite (M4)
```

**DELTA (round 2)**: see corrected DELTA above. **WITNESS (round 2)**: Common-Infrastructure-Agent, 2026-09-12, worktree `wt-t109` on `fix/t109-ci-suites`.

**WITNESS (independent, Supervisor — Stage 4 P2-2)**: the implementing agent is not the sole witness. On 2026-09-12 the
Supervisor replayed every `ci.yml` `run:` step in fresh `ubuntu:24.04` containers from git bundles, twice: round 1 @ `813902a`
(as-is success; broken wired suite → fails at its step; **unwired failing suite → job success = FAIL**) and round 2 @ `54babca`
(as-is success incl. drift guard 4/4; unwired failing suite, shellcheck-only mention and comment-only mention → each fails at the
drift-guard step naming the exact suite; guard step deleted → success; `run: |` block → guard fails naming the still-running
suite). Full step output: the verify row in the Evidence table.


---

## Round 2 (opened 2026-09-12 after /verify FAIL)

**Findings driving round 2** (Supervisor, from the /verify run — details in the verify row above):
1. The drift guard never runs in CI → an unwired failing suite leaves the job green.
2. The guard treats any `tests/X.sh` text in `ci.yml` as wired (shellcheck argument list, comments).
3. DELTA overclaimed ("now gates every future push").

**Also recorded**: the round-1 agent's session ended with exit 129 (window closed) after its 3 commits; worktree was clean, nothing lost.
During /verify the shared `active_task` state file still named T109, so Supervisor verification commands are mixed into T109's trace.

**BEFORE (round 2)** (Common-Infrastructure-Agent, 2026-09-12T11:24:34Z, worktree `wt-t109` @ `13ba936`, before any round-2 implementation commit):

```
=== Probe A: delete "Per-harness projection tests (T097)" step, run guard ===
git diff --stat .github/workflows/ci.yml  ::  1 file changed, 3 deletions(-)   (mutation confirmed landed)
python3 -m pytest tests/test_ci_wires_shell_suites.py -v
  test_every_real_suite_is_wired_or_excluded PASSED
  test_every_ci_referenced_suite_exists PASSED
  test_excluded_suites_still_exist_and_are_really_excluded PASSED
  3 passed in 0.01s   <-- guard did NOT catch the deletion; test_harness_projection.sh is still
                          matched via the shellcheck argument list at ci.yml:19
(ci.yml restored via cp from backup; git diff --stat shows no diff after restore)

=== Probe B: add always-failing tests/test_zz_comment_only.sh + a comment-only mention ===
Added tests/test_zz_comment_only.sh (exit 1) and appended to ci.yml:
  # TODO later: tests/test_zz_comment_only.sh
git diff --stat .github/workflows/ci.yml  ::  1 file changed, 2 insertions(+)   (mutation confirmed landed)
python3 -m pytest tests/test_ci_wires_shell_suites.py -v
  test_every_real_suite_is_wired_or_excluded PASSED
  test_every_ci_referenced_suite_exists PASSED
  test_excluded_suites_still_exist_and_are_really_excluded PASSED
  3 passed in 0.01s   <-- guard did NOT catch the unwired failing suite; the comment-only mention
                          was enough to count it as "wired"
(tests/test_zz_comment_only.sh removed, ci.yml restored via git checkout --; git status --short clean)

=== Proof no ci.yml step runs the guard ===
grep -n "test_ci_wires_shell_suites" .github/workflows/ci.yml
NOT FOUND: no step in ci.yml runs the guard
```
