# TASK_GUIDE — T109: CI runs every install/update shell suite, and the one it would have caught is fixed
**Date**: 2026-09-12
**Complexity Level**: C2 (Hard-Stop Gate 2 floor: this is *test coverage* work — the change itself is small)
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`
**Branch**: worktree off the integration branch `feat/easy-kit-one-command` (cut from `main`); merges back into it, never into `main` (`memory/decisions.md`, 2026-09-12)

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` — this task is follow-up (1) of it

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-12: "check the install and the update shell script can work as expected". A Supervisor
probe that day found nine installer defects; the root reason none were caught is that **CI never runs
the installer's own test suites**. `.github/workflows/ci.yml` runs `scripts/smoke-install.sh` and
`tests/test_harness_projection.sh` only. Measured on `main` `8115bc9`, 2026-09-12:

| Suite | Result | In CI? |
|---|---|---|
| `tests/test_setup.sh` | 18 passed, 0 failed | no |
| `tests/test_update.sh` | 31 passed, 0 failed | no |
| `tests/test_install_update_smoke.sh` | **8 passed, 1 failed** | no |
| `tests/test_t098_harness_presence.sh` | 20 passed, 0 failed | no |
| `tests/test_pack_choice_parsing.sh` | 15 passed, 0 failed | no |

The failing case is a **test** defect, not an installer defect:
`FAIL: AC1: MANIFEST path 'skills          codex=.codex/skills' missing from target after setup.sh`.
The smoke suite reads MANIFEST lines raw; T097 added the optional `<harness>=<dest>` column, so the test
now looks for a path literally named `skills          codex=.codex/skills`. It has been red since T097
and nobody saw, because nothing runs it.

**Restated intent**:
> Every shell test suite for the installer runs in CI as its own named step, all of them are green, and
> a new suite added later cannot silently stay out of CI.

**Out of scope** (what this task explicitly does NOT do):
- Any change to `setup.sh`, `update.sh` or `lib/harness-fetch.sh` behaviour (T110–T116 do that).
- Adding new installer test cases beyond the smoke fix — later tasks add their own.
- Extending the shellcheck lint list in `ci.yml:19`. That list is mirrored by `tests/test_shellcheck_clean.sh` (T105); changing it is a separate decision.
- Fixing the pre-existing `tests/test_readme_slim.py` failure (README 83 > 75 lines) — owned by T115.

**Requirement Refs**: none in `PRD.md` — defect against existing CI; authority is ADR-0002 Follow-up (1).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, from the 2026-09-12 probe + user-approved breakdown)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary ("Manifest", "destination map")
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No `PRD.md` refs claimed, so none to verify

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `.github/workflows/ci.yml` — job `Framework integrity + install smoke test`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `tests/test_install_update_smoke.sh` passes 9/9: its MANIFEST reading uses field 1 only (the same rule as `harness_manifest_path` in `lib/harness-fetch.sh`), so a destination column never becomes part of the path | the one red suite |
| 2 | `ci.yml` runs `tests/test_setup.sh`, `tests/test_update.sh`, `tests/test_install_update_smoke.sh`, `tests/test_t098_harness_presence.sh`, `tests/test_pack_choice_parsing.sh` — **one named step each**, so a red suite is identified by step name | "every suite runs in CI as its own named step" |
| 3 | Each new step invokes its suite directly, with no pipe after it — the step's exit status is the suite's exit status | `cmd \| tail` masks failure (`memory/learnings.md`) |
| 4 | A new Python test fails if any `tests/*.sh` is **neither** run by `ci.yml` **nor** listed in an explicit exclusion list inside that test, where every exclusion carries a one-line reason | "a new suite cannot silently stay out of CI" |
| 5 | The same test also fails if `ci.yml` references a `tests/*.sh` path that does not exist (the other drift direction) | anti-drift both directions (`memory/learnings.md`, T106) |
| 6 | Mutation control M1: reverting only the AC1 fix makes `bash tests/test_install_update_smoke.sh` exit non-zero — observed, landing confirmed by `git diff` first | a fix never observed failing is not evidence |
| 7 | Mutation control M2: deleting one new step from `ci.yml` makes the AC4 test fail naming that suite | the drift guard must be observed failing |
| 8 | **(Round 2)** CI runs the drift guard: one named `ci.yml` step runs `python3 tests/test_ci_wires_shell_suites.py`; the file has a `__main__` block that runs every `test_*` function and exits non-zero on any failure, and stays pytest-collectable | /verify FAIL 2026-09-12: an unwired failing suite left the replayed job green — "cannot silently stay out of CI" |
| 9 | **(Round 2)** A suite counts as wired only via a `run:` line that directly invokes it (`run: bash tests/<name>.sh` or `run: sh tests/<name>.sh`). Mentions in another command (the shellcheck argument list), a comment, or a step name do not count | /verify probes A and B: shellcheck-only and comment-only mentions passed the guard |
| 10 | **(Round 2)** The guard asserts that `ci.yml` has a run: step invoking `python3 tests/test_ci_wires_shell_suites.py` (self-check) | deleting the guard's own step must not silently disable it |
| 11 | **(Round 2)** The review file's DELTA states only what is guaranteed; round 1's "now gates every future push" is corrected | claim/evidence divergence found at /verify |
| 12 | **(Round 2)** Mutation controls, each observed failing with landing confirmed by `git diff`: M3 shellcheck-only mention → guard fails naming the suite; M4 comment-only mention → guard fails; M5 guard step deleted → self-check fails; M6 `python3 tests/test_ci_wires_shell_suites.py` with an unwired failing suite present → exit non-zero. M1/M2 re-run and still fail | a guard never observed failing is not evidence |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | clean worktree | `bash tests/test_install_update_smoke.sh` → `9 passed, 0 failed`, exit 0 | automated test |
| 2 | clean worktree | each of the 5 suites in AC2 exits 0 when run exactly as its `ci.yml` step runs it | automated (step commands) |
| 3 | `ci.yml` with one suite step removed | AC4 test fails and names the missing suite | mutation control M2 |
| 4 | a fake `tests/test_zz_new.sh` created, not wired, not excluded | AC4 test fails naming it; file removed after | mutation control |
| 5 | smoke fix reverted | smoke suite exits non-zero | mutation control M1 |
| 6 | full Python suite | no new failures beyond the pre-existing `test_readme_slim.py` | automated |

### Verification Command (exact, runnable)

```bash
bash tests/test_setup.sh
bash tests/test_update.sh
bash tests/test_install_update_smoke.sh
bash tests/test_t098_harness_presence.sh
bash tests/test_pack_choice_parsing.sh
python3 -m pytest tests/test_ci_wires_shell_suites.py -q
python3 tests/test_ci_wires_shell_suites.py; echo "guard as CI runs it: rc=$?"   # round 2
python3 -m pytest .claude/hooks/tests/ tests/ -q   # expect only test_readme_slim.py red (pre-existing, T115)
```

> Run each line separately and read its exit status. Do **not** chain them with `| tail`.

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T109.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T109.md`.

---

## Approach

**Pattern reference**: `tests/test_pack_docs_flags.py` — a Python test that reads a shell/CI artifact at
test time and asserts agreement with the repo, rather than hardcoding a copied list. Imitate reading
the real `ci.yml` and globbing the real `tests/` directory. Do **not** copy a list of suite names into
the test — `memory/learnings.md` records that a test mirroring another file's list by copying it "is a
comment, not a mechanism" (T105).

**Vital slice**: the smoke-suite field-1 fix plus five `ci.yml` steps. The drift test is what keeps the
fix from decaying, so it is in the slice, not a nice-to-have.
**Cut list**:
- Parallel CI jobs / matrix — the suites run in seconds; one job is enough.
- Running the suites under `dash` as well as `bash` — not requested; the scripts are shellchecked as POSIX already.
- Caching shellcheck — unrelated.

The drift test (AC4) covers **every** `tests/*.sh`, not only the five in AC2. Measured 2026-09-12, three
more suites exist and are also absent from `ci.yml`, so AC4 forces a decision on each:
`tests/test_harness_fetch.sh`, `tests/test_readme_current.sh`, `tests/test_shellcheck_clean.sh`. For each,
**either** wire it as its own step (run it first — if it is red, STOP and report rather than fix unrelated
code) **or** put it in the exclusion list with a reason a reviewer can check (e.g. `test_shellcheck_clean.sh`
if it needs a binary the lint step already provides — **verify, don't assume**). AC2's five are mandatory
wires; these three are the agent's call, justified in the review file.

---

## Edge Case Checklist

- [ ] A suite that needs `git` identity (`user.email`) fails in CI's fresh runner — set `GIT_AUTHOR_*`/`GIT_COMMITTER_*` in the step `env`, or confirm the suite sets its own
- [ ] A suite that depends on a TTY (none should — confirm) would hang or skip in CI
- [ ] `grep` in this dev environment wraps ugrep; the drift test must not shell out to `grep` (`memory/learnings.md`, T107)
- [ ] The glob for suites must include `tests/*.sh` only — not `scripts/*.sh`, which are not test suites
- [ ] `tests/test_harness_projection.sh` is already wired (`ci.yml:28`) — the drift test must count it as wired, not flag it

---

## Documentation to Update

> Batch rule (user, 2026-09-12: "make sure the document also be updated"): every task updates the
> user-facing docs its change makes wrong, **in the same task**, and quotes the new text in the review
> file. Historical records (`docs/adr/`, `docs/ddr/`, `tasks/`, `memory/`, `BRAINSTORMING_LOG*.md`, the
> task and decision tables in `PROJECT_SPEC.md`) are never rewritten.

**None — this task changes CI and tests only; no user-facing behaviour or instruction changes.** The
review file's documentation row is marked N/A with this reason.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `tests/test_install_update_smoke.sh` | Read MANIFEST field 1 only (AC1) |
| `.github/workflows/ci.yml` | Five new named steps (AC2, AC3) |
| `tests/test_ci_wires_shell_suites.py` | New — drift guard both directions (AC4, AC5) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/harness-fetch.sh` | Behaviour changes belong to T110–T116; this task only makes the existing suites run |
| `ci.yml:19` shellcheck file list + `tests/test_shellcheck_clean.sh` | Mirrored pair (T105); out of scope |
| `README.md`, `tests/test_readme_slim.py` | Pre-existing red, owned by T115 |
| `MANIFEST` | The smoke test must adapt to MANIFEST's documented format, not the reverse |

---

## Test Plan

- Fix AC1, run the smoke suite: 9/9.
- Add the five steps; run every step command locally exactly as written.
- Write `tests/test_ci_wires_shell_suites.py`; run M1, M2 and the fake-suite control, restoring after each (re-read the diff after every restore — `memory/learnings.md`: reverting a mutation with `git checkout` also reverts uncommitted fixes; commit the fix first).
- Full Python suite: only the pre-existing README failure remains.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor — sub-agents have no Skill tool)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T109.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `/verify` — user-invoked; the Supervisor cannot run this gate
- [ ] `memory/MEMORY.md` — flag learnings to the Supervisor (Supervisor-only writes)
- [ ] Supervisor notified: task ready for Stage 4 review
