---
name: LR-0001-refactor-task-size-evaluation
date: 2026-06-22
type: project
status: active
---

## Insight
"Refactor to clean architecture" (and similar structural refactors) are NOT small tasks. The Supervisor mis-evaluated this as a quick, low-complexity task and bypassed the pipeline as a result. Architectural refactors touch many files, carry high blast radius, and always warrant a TASK_GUIDE, Complexity ≥ C2, and Risk ≥ Medium — regardless of how the request is worded.

## Evidence
User correction on 2026-06-22: the Supervisor coded a clean-architecture refactor directly instead of going through Stage 2 → TASK_GUIDE → sub-agent spawn. When asked why, the Supervisor cited "the request felt small." The user clarified this was a wrong evaluation.

## Implications
- Never classify a refactor, restructure, or architectural pattern migration as C0/C1 by default — start at C2.
- When a request contains words like "refactor", "restructure", "migrate to pattern", "clean architecture" — treat as Medium Risk and require a TASK_GUIDE before any code.
- Task size evaluation must be based on predicted blast radius (files touched, callers affected), not on how casual the request sounds.
