---
name: LR-0003-tests-that-cannot-fail
date: 2026-11-05
type: project
status: active
source: agent
---

## Insight

Tests, guards and mutation controls that can never fail keep shipping in this kit and are caught only by a later reviewer: an `x <= x` assertion, a `sed` mutation that changed no bytes, a `not in` check on a string the old file never held, a 'mirror' test that hardcodes its list, a guard no CI step runs.

## Evidence

Found by `/self-review` (first real run, 2026-11-05), pattern `vacuous-assertion-or-noop-mutation-control` on T075, T082, T083, T085, T088, T101, T105, T109; every quote checked by `self_review.py post`. Report: `reports/self-review/self-review-20261105T082737.md`. Citations include `tasks/TASK_REVIEW_T082.md:92`, `tasks/TASK_REVIEW_T083.md:117`, `tasks/TASK_REVIEW_T101.md:183`, `tasks/TASK_REVIEW_T105.md:91`, `tasks/TASK_REVIEW_T109.md:113`. Approved by the user 2026-11-05; kit task T257.

## Implications

- Never count a test as covering an AC until it was run red against the prior content (`git show <base>:<file>`) with the output pasted.
- A mutation control counts only with a non-empty `git diff --stat` pasted before its verdict.
