# TASK_GUIDE — T257: `tdd` + review template: prove each new test or mutation control can go red
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
6. Read `reports/self-review/self-review-20261105T082737.md` (the pattern and its cited lines) and `memory/learning-records/LR-0003-tests-that-cannot-fail.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Drafted by `/self-review` (2026-11-05) from pattern `vacuous-assertion-or-noop-mutation-control`, approved by the user 2026-11-05. Seen on T075, T082, T083, T085, T088, T101, T105, T109; cited lines: `tasks/TASK_REVIEW_T082.md:92`, `tasks/TASK_REVIEW_T083.md:117`, `tasks/TASK_REVIEW_T101.md:183`, `tasks/TASK_REVIEW_T105.md:91`, `tasks/TASK_REVIEW_T109.md:113` (full list in the report).

**Restated intent**:
> Tests, guards and mutation controls that can never fail keep shipping in this kit and are caught only by a later reviewer: an `x <= x` assertion, a `sed` mutation that changed no bytes, a `not in` check on a string the old file never held, a 'mirror' test that hardcodes its list, a guard no CI step runs. Change the kit so the defect is caught when the work is done, not by a later reviewer.

**Out of scope**:
- Fixing the past tasks' tests or text. Any hook. Any other self-review pattern.

**Requirement Refs**: self-review report `reports/self-review/self-review-20261105T082737.md`, pattern `vacuous-assertion-or-noop-mutation-control`; PRD `docs/prd/PRD_self-review.md` FR-008.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user approved the proposal 2026-11-05; signed auto (Supervisor) for the [auto] run 2026-11-05
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
| 1 | `skills/tdd/SKILL.md` has a required step: before a test counts as covering an AC, run it against the prior content (`git show <base>:<file>` or the pre-change checkout) and paste the RED output. | self-review `vacuous-assertion-or-noop-mutation-control` |
| 2 | `skills/tdd/SKILL.md` requires each mutation control to show a non-empty `git diff --stat` (or equivalent byte diff) before its verdict. | self-review `vacuous-assertion-or-noop-mutation-control` |
| 3 | `skills/tdd/SKILL.md` lists the vacuous forms seen: `x <= x`; `not in` on a string the old content never held; a hand-kept list claiming to mirror a file; a guard no CI step runs. | self-review `vacuous-assertion-or-noop-mutation-control` |
| 4 | `templates/TASK_REVIEW_template.md` row `Negative cases hold` asks for the red run or the mutation diff. | self-review `vacuous-assertion-or-noop-mutation-control` |
| 5 | A test pins AC 1-4 by text; `skills/tdd/SKILL.md` stays under the Codex 8 KB cap. | self-review `vacuous-assertion-or-noop-mutation-control` |

---

## Evaluation & Acceptance

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q .claude/hooks/tests/ tests/
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T257.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T257.md`.

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
| `skills/tdd/SKILL.md` | add the red-against-prior-content step and the vacuous-form checklist |
| `templates/TASK_REVIEW_template.md` | `Negative cases hold` row asks for the red run / mutation diff |
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
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T257.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
