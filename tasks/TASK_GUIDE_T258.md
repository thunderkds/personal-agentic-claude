# TASK_GUIDE — T258: TASK_GUIDE template: list the pre-existing pin tests a task will hit, at Stage 2
**Date**: 2026-11-05
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `reports/self-review/self-review-20261105T082737.md` (the pattern and its cited lines) and `memory/learning-records/LR-0004-pin-tests-hit-later-tasks.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Drafted by `/self-review` (2026-11-05) from pattern `pin-tests-collide-with-later-tasks`, approved by the user 2026-11-05. Seen on T064, T066, T070, T075, T082, T094, T103; cited lines: `tasks/TASK_REVIEW_T064.md:173`, `tasks/TASK_REVIEW_T066.md:291`, `tasks/TASK_REVIEW_T094.md:59`, `tasks/TASK_REVIEW_T103.md:156` (full list in the report).

**Restated intent**:
> Tests that pin a file's text, size, line count, location or a frozen baseline ref break on later, unrelated tasks; the implementer meets them mid-task and must repoint, narrow or escalate with no plan. Change the kit so the defect is caught when the work is done, not by a later reviewer.

**Out of scope**:
- Fixing the past tasks' tests or text. Any hook. Any other self-review pattern.

**Requirement Refs**: self-review report `reports/self-review/self-review-20261105T082737.md`, pattern `pin-tests-collide-with-later-tasks`; PRD `docs/prd/PRD_self-review.md` FR-008.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user approved the proposal 2026-11-05
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: Standalone — N/A (doctrine/skill text)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_GUIDE_template.md` `Files to Change (Predicted)` has a row `Pre-existing pin tests` with the instruction: list each test that pins text, size, line count, location or a baseline ref of a file this task edits, and its handling (repoint / narrow / escalate). | self-review `pin-tests-collide-with-later-tasks` |
| 2 | The row names how to find them: grep `.claude/hooks/tests/` and `tests/` for the changed strings/paths; always check `test_agent_guide_dedup.py`, `test_vital_slice.py`, the memory budget tests. | self-review `pin-tests-collide-with-later-tasks` |
| 3 | The Edge Case Checklist has one line for the pin-test pre-flight. | self-review `pin-tests-collide-with-later-tasks` |
| 4 | Every existing test that pins the template text passes (update pins only where required, listed in this guide's row of the new kind). | self-review `pin-tests-collide-with-later-tasks` |
| 5 | A new test asserts AC 1-3 by text. | self-review `pin-tests-collide-with-later-tasks` |

---

## Evaluation & Acceptance

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q .claude/hooks/tests/ tests/
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T258.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T258.md`.

---

## Approach

**Vital slice**: the one rule text that would have caught the cited cases. Keep it short; doctrine growth has its own pins.

---

## Edge Case Checklist

- [ ] Pin tests on the edited files (`test_agent_guide_dedup.py`, `test_vital_slice.py`, site/skill-list pins, Codex 8 KB cap)
- [ ] ASD-STE100 writing rules for any human-read text

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_GUIDE_template.md` | `Files to Change` gains a `Pre-existing pin tests` row; Edge Case Checklist gains the pre-flight line |
| tests (new) | text pins for the ACs |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*`, `hooks/hooks.json`, `.claude/settings.json` | out of scope |
| `memory/self-review/register.md` | written only by `self_review.py` |

---

## Test Plan

Text-pin pytest for the ACs; full suite green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T258.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
