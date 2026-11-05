# TASK_GUIDE — T259: `code-review`: stale-reference sweep for every fact the diff changes
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
6. Read `reports/self-review/self-review-20261105T082737.md` (the pattern and its cited lines) and `memory/learning-records/LR-0005-stale-text-after-change.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Drafted by `/self-review` (2026-11-05) from pattern `stale-claim-after-behaviour-change`, approved by the user 2026-11-05. Seen on T069, T073, T087, T095, T098, T101, T105; cited lines: `tasks/TASK_REVIEW_T069.md:131`, `tasks/TASK_REVIEW_T073.md:52`, `tasks/TASK_REVIEW_T101.md:322`, `tasks/TASK_REVIEW_T105.md:96` (full list in the report).

**Restated intent**:
> A change in this kit often leaves a comment, docstring, doc sentence, site line or board note that states the old fact; it is found only at Stage 4/5, or not at all. Change the kit so the defect is caught when the work is done, not by a later reviewer.

**Out of scope**:
- Fixing the past tasks' tests or text. Any hook. Any other self-review pattern.

**Requirement Refs**: self-review report `reports/self-review/self-review-20261105T082737.md`, pattern `stale-claim-after-behaviour-change`; PRD `docs/prd/PRD_self-review.md` FR-008.

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
| 1 | `skills/code-review/SKILL.md` has a stale-reference sweep step: for each fact the diff changes (flag, count, path, channel/skill name, version, a 'green' claim), grep the repo for the old wording (README, `site/`, `docs/claude-md/`, docstrings and comments, `agents/`, `PROJECT_KANBAN.md` notes, test comments). | self-review `stale-claim-after-behaviour-change` |
| 2 | Each hit outside the guide's Files to Change is a P2 finding with the file:line. | self-review `stale-claim-after-behaviour-change` |
| 3 | `templates/TASK_GUIDE_template.md` Edge Case Checklist has a line for stale references. | self-review `stale-claim-after-behaviour-change` |
| 4 | Pins on `skills/code-review/SKILL.md` and the template still pass; the skill stays under the Codex 8 KB cap. | self-review `stale-claim-after-behaviour-change` |
| 5 | A new test asserts AC 1-3 by text. | self-review `stale-claim-after-behaviour-change` |

---

## Evaluation & Acceptance

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q .claude/hooks/tests/ tests/
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T259.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T259.md`.

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
| `skills/code-review/SKILL.md` | Phase 0.5 gains a stale-reference sweep |
| `templates/TASK_GUIDE_template.md` | Edge Case Checklist line for stale references |
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
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T259.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
