---
name: LR-0002-pipeline-compliance-not-enforced-in-practice
date: 2026-06-22
type: user
status: active
---

## Insight
The user explicitly flagged that pipeline compliance (Stage 2 → TASK_GUIDE → sub-agent) is not being pushed as high priority in practice — it gets bypassed when tasks feel small or familiar. This is a systemic behavior pattern, not a one-off slip. The three root causes the user identified: (1) perceived task smallness, (2) no TASK_GUIDE acting as a gate, (3) Supervisor role drift into implementation.

## Evidence
User statement on 2026-06-22: "the flow is not push as high priority, this is the issue when I use in a practice." Followed by a detailed self-analysis of three bypass root causes.

## Implications
- The pipeline is non-negotiable regardless of perceived task size. "It feels small" is never a valid reason to skip TASK_GUIDE creation or sub-agent spawn.
- The Supervisor must treat the absence of a TASK_GUIDE as a hard blocker — no implementation without it.
- When the user raises a pipeline violation, treat it as a systemic signal, not a one-time correction. Audit whether the same bypass pattern could recur elsewhere.
- Supervisor role = orchestrate + guide. Implementation = sub-agent only. This boundary must be enforced even when spawning an agent feels like more overhead than just doing the work.
