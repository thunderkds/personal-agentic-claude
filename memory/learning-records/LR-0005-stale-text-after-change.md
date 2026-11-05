---
name: LR-0005-stale-text-after-change
date: 2026-11-05
type: project
status: active
source: agent
---

## Insight

A change in this kit often leaves a comment, docstring, doc sentence, site line or board note that states the old fact; it is found only at Stage 4/5, or not at all.

## Evidence

Found by `/self-review` (first real run, 2026-11-05), pattern `stale-claim-after-behaviour-change` on T069, T073, T087, T095, T098, T101, T105; every quote checked by `self_review.py post`. Report: `reports/self-review/self-review-20261105T082737.md`. Citations include `tasks/TASK_REVIEW_T069.md:131`, `tasks/TASK_REVIEW_T073.md:52`, `tasks/TASK_REVIEW_T101.md:322`, `tasks/TASK_REVIEW_T105.md:96`. Approved by the user 2026-11-05; kit task T259.

## Implications

- For each fact a diff changes (flag, count, path, name, version, 'X is green'), grep the repo for the old wording before review ends.
- A hit outside the guide's Files to Change is a P2 finding.
