# TASK_GUIDE — T034: QA — smoke tests for the new install/update model
**Date**: 2026-07-17
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: qa-expert
**Agent guide**: `.claude/agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/qa.md`
5. C1 — apply brainstorm/decompose/verify depth from the Complexity matrix in `.claude/agents/general-agent-template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

T032/T033 each ship their own per-task automated tests (Hard-Stop Gate 5 requires this), but per this repo's own convention (the implementing agent must not be the sole author of its own acceptance test — Supervisor/QA writes or signs off on the oracle), this task is the independent QA pass: an end-to-end smoke suite exercising `setup.sh` and `update.sh` together as a user actually would, written/reviewed separately from the implementers of T032/T033.

**Restated intent**:
> Write (or, if T031/T032/T033's own tests already cover a scenario adequately, explicitly sign off on reusing them rather than duplicating) an end-to-end smoke suite that proves: fresh install works, a no-op update is silent, a real local edit triggers the conflict prompt correctly, and a non-git target is rejected — run against the actual `setup.sh`/`update.sh`, not mocks.

**Out of scope**:
- Does not re-review `lib/harness-fetch.sh`'s internals in isolation — that's covered by T031's own unit tests; this task's smoke suite exercises the public `setup.sh`/`update.sh` surface.
- Does not test packs or migration — both out of scope per ADR-0001.

**Requirement Refs**: ADR-0001 (Consequences — "closes a gap the old symlink model never had to solve"), CLAUDE.md Stage 4 Evidence Gate ("implementing agent must not be the sole author of its own acceptance test")

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match ADR-0001 and the Stage 4 Evidence Gate rule
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to ADR-0001
- [x] Requirement Ref (ADR-0001) is fully covered by the Acceptance Criteria below

> An agent must NOT start implementing until this gate is checked. If anything here is unclear, STOP and ask the Supervisor.

---

## Dependencies & Reachability

**Depends on**: `T032 — setup.sh must be rewritten`, `T033 — update.sh must be rewritten`

**Entry point**: `bash setup.sh` and `bash update.sh`, exercised end-to-end from a real scratch directory (not unit-level mocks)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Smoke suite runs `setup.sh` in a fresh scratch git repo and asserts every `MANIFEST` path + `CLAUDE.md` land as real files (not symlinks) | ADR-0001 |
| 2 | Smoke suite runs `update.sh` immediately after (no local edits) and asserts zero prompts, all files silently refreshed | ADR-0001 |
| 3 | Smoke suite edits one installed file, runs `update.sh`, and asserts the conflict path is reached (diff shown, choice honored for both "overwrite" and "skip" sub-cases) | ADR-0001 |
| 4 | Smoke suite runs both `setup.sh` and `update.sh` against a non-git target directory and asserts both reject before writing anything | ADR-0001 |
| 5 | Smoke suite is independent of T031/T032/T033's own unit tests — written by QA, not copy-pasted from the implementer's test files | Stage 4 Evidence Gate — independent oracle rule |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Full scratch-repo run of setup → update → edit → update | All four assertions in Acceptance Criteria above pass in one suite run | automated test |
| 2 | Suite run twice in a row | Idempotent — no leftover temp dirs, no stale state between runs | automated test |

### Verification Command (exact, runnable)

```bash
bash tests/test_install_update_smoke.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_install_update_smoke.sh` (new, written independently by QA — not copy-pasted from `tests/test_harness_fetch.sh`/`tests/test_setup.sh`/`tests/test_update.sh`). Maps 1:1 to AC1-AC4: AC1 (real-file/no-symlink check), AC2 (silent no-op update), AC3a/AC3b (conflict prompt overwrite + skip sub-cases), AC4 (non-git rejection, both scripts, no writes). Run output: `bash tests/test_install_update_smoke.sh` → `PASS: setup.sh exits 0 on a fresh git repo` / `PASS: AC1: fresh install lands every MANIFEST path + CLAUDE.md as real files (no symlinks)` / `PASS: AC2: no-op update.sh run is silent (exit 0, no conflict prompts)` / `PASS: AC3a: conflict prompt reached, 'o' (overwrite) restores upstream content` / `PASS: AC3b: conflict prompt reached, 's' (skip) leaves the file byte-identical to the user's edit` / `PASS: AC4: setup.sh rejects a non-git target directory (exit 1)` / `PASS: AC4: setup.sh wrote nothing into the non-git target before rejecting it` / `PASS: AC4: update.sh rejects a non-git target directory (exit 1)` / `PASS: AC4: update.sh wrote nothing into the non-git target before rejecting it` / `9 passed, 0 failed` / exit=0 |
| Verification command run | ☑ pass | `bash tests/test_install_update_smoke.sh` — exit 0, `9 passed, 0 failed` (run twice in a row, both green, see Success Criterion #2 below) |
| Negative cases hold | ☑ pass | (a) AC4 non-git-dir rejection asserted with 0 entries written before exit, for both scripts. (b) Regression-detection self-check: sabotaged `update.sh`'s conflict-warning line (`sed` no-op'd the `log_warn "conflict: ..."` call), re-ran the suite — it correctly went red: `FAIL: AC3a: update.sh did not report a conflict for a locally-edited file` / `FAIL: AC3b: update.sh did not report a conflict for a locally-edited file` / `7 passed, 2 failed` / exit=1. Reverted `update.sh` immediately after (confirmed via `git diff --stat update.sh` → no changes); this proves the suite is not a rubber stamp. |
| verify | ☑ pass | Ran the actual `setup.sh`/`update.sh` (not mocks) end-to-end against real scratch git repos via the suite above — this is the verify for a CLI tool: fresh install → real files land, no-op update → silent, edited file → real conflict prompt with real diff output and real stdin-driven choices, non-git dir → real rejection before any write. Also independently re-ran the existing per-task unit suites in the same worktree state to confirm no cross-task regression: `test_harness_fetch.sh` → `9 passed, 0 failed`; `test_setup.sh` → `15 passed, 0 failed`; `test_update.sh` → `22 passed, 0 failed` — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Only `tests/test_install_update_smoke.sh` added (new file). Read `setup.sh`, `update.sh`, `lib/harness-fetch.sh`, `MANIFEST` to understand behavior for oracle design — none of them modified (confirmed via `git status --short` / `git diff --stat` showing only the new test file, no residual diff on the implementation files after the negative-control experiment above) |
| Full smoke suite still green (no regression) | ☑ pass | `test_harness_fetch.sh`: 9/9 pass; `test_setup.sh`: 15/15 pass; `test_update.sh`: 22/22 pass; new `test_install_update_smoke.sh`: 9/9 pass. Total 55/55 across the four suites, 0 failures |
| **UI: Visual regression** | N/A | Pure backend/tooling task — no UI component |
| **UI: Design-system compliance** | N/A | Pure backend/tooling task — no UI component |
| **UI: Responsiveness** | N/A | Pure backend/tooling task — no UI component |

---

## Approach

Write `tests/test_install_update_smoke.sh` as a single end-to-end shell script that: creates a scratch temp dir, `git init`s it, runs `setup.sh` against it (pointing `GITHUB_USERNAME`/repo URL at this actual repo, or a local `file://` fixture if network flakiness in CI is a concern — decide based on what T031's tests already established), asserts file state, runs `update.sh` cleanly, edits a file, re-runs `update.sh` with piped stdin answers to hit both the overwrite and skip branches, and finally asserts the non-git-directory rejection in a separate throwaway non-git dir.

---

## Edge Case Checklist

- [x] Test must clean up all scratch directories on both pass and fail (trap-based, matching T031's own cleanup discipline) — `trap cleanup EXIT INT TERM HUP`; verified no leftover `/tmp/t034-smoke.*` dirs after two consecutive runs, and no leftovers even mid-debugging (caught and fixed a subshell-scoping bug during self-test — see Files to Change note)
- [x] If network fetch is used (real GitHub URL) rather than a local fixture, the suite must tolerate/report network unavailability distinctly from an actual regression — resolved by design: `SUPERVISOR_REPO` is pointed at this worktree's own local path, so `git clone --depth 1` never touches the network at all; no network-flakiness handling needed
- [x] Confirm the "skip" branch in the conflict prompt genuinely leaves the file byte-identical to the user's edit (not just "didn't crash") — AC3b captures the edited content into `$EXPECTED_SKIP_CONTENT` before running update.sh, then string-compares against the post-run file content

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `tests/test_install_update_smoke.sh` | New file — end-to-end smoke suite |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/harness-fetch.sh` | Implementation files from T031/T032/T033 — QA verifies, does not modify |

---

## Test Plan

The smoke suite itself is the test plan for this task — see Verification Command above. No separate unit-test layer needed; this is explicitly the end-to-end/integration layer sitting above T031-T033's own unit tests.

---

## Completion Checklist

- [x] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run — deferred to Supervisor/Stage 4 (QA role does not review its own oracle per independence rule)
- [x] Security review: N/A — Low risk
- [ ] Lint passes (`shellcheck tests/test_install_update_smoke.sh`) — shellcheck not available in this environment (same gotcha noted for T031); substituted `sh -n tests/test_install_update_smoke.sh` (syntax OK) plus real execution under both `bash` and `dash` (both pass, 9/9), matching this repo's documented no-shellcheck fallback
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `Skill({ skill: "verify" })` run — feature confirmed working in a real scratch repo (see Evidence row above)
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned) — Supervisor-only write; flagged below for the Supervisor to add
- [x] Supervisor notified: task ready for Stage 4 review
