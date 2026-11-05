---
name: LR-0004-pin-tests-hit-later-tasks
date: 2026-11-05
type: project
status: active
source: agent
---

## Insight

Tests that pin a file's text, size, line count, location or a frozen baseline ref break on later, unrelated tasks; the implementer meets them mid-task and must repoint, narrow or escalate with no plan.

## Evidence

Found by `/self-review` (first real run, 2026-11-05), pattern `pin-tests-collide-with-later-tasks` on T064, T066, T070, T075, T082, T094, T103; every quote checked by `self_review.py post`. Report: `reports/self-review/self-review-20261105T082737.md`. Citations include `tasks/TASK_REVIEW_T064.md:173`, `tasks/TASK_REVIEW_T066.md:291`, `tasks/TASK_REVIEW_T094.md:59`, `tasks/TASK_REVIEW_T103.md:156`. Approved by the user 2026-11-05; kit task T258.

## Implications

- At Stage 2, grep `.claude/hooks/tests/` and `tests/` for the strings, sizes and paths a task changes, and write the hits and their planned handling in the guide.
- Expect `test_agent_guide_dedup.py`, `test_vital_slice.py` and the memory budget tests to bite on doctrine edits.
