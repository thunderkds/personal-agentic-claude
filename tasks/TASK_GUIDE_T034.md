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

- [ ] Restated intent confirmed to match ADR-0001 and the Stage 4 Evidence Gate rule
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to ADR-0001
- [ ] Requirement Ref (ADR-0001) is fully covered by the Acceptance Criteria below

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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | N/A | Pure backend/tooling task — no UI component |
| **UI: Design-system compliance** | N/A | Pure backend/tooling task — no UI component |
| **UI: Responsiveness** | N/A | Pure backend/tooling task — no UI component |

---

## Approach

Write `tests/test_install_update_smoke.sh` as a single end-to-end shell script that: creates a scratch temp dir, `git init`s it, runs `setup.sh` against it (pointing `GITHUB_USERNAME`/repo URL at this actual repo, or a local `file://` fixture if network flakiness in CI is a concern — decide based on what T031's tests already established), asserts file state, runs `update.sh` cleanly, edits a file, re-runs `update.sh` with piped stdin answers to hit both the overwrite and skip branches, and finally asserts the non-git-directory rejection in a separate throwaway non-git dir.

---

## Edge Case Checklist

- [ ] Test must clean up all scratch directories on both pass and fail (trap-based, matching T031's own cleanup discipline)
- [ ] If network fetch is used (real GitHub URL) rather than a local fixture, the suite must tolerate/report network unavailability distinctly from an actual regression
- [ ] Confirm the "skip" branch in the conflict prompt genuinely leaves the file byte-identical to the user's edit (not just "didn't crash")

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

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A — Low risk
- [ ] Lint passes (`shellcheck tests/test_install_update_smoke.sh`)
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in a real scratch repo
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
