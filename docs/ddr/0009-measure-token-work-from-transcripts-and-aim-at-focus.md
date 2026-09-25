# 0009. Measure token work from session transcripts, and aim it at agent focus

> **What this is**: A Design Decision Record — a permanent, dated note capturing *one* design decision and the trade-off behind it.
> **Gate**: 2-of-3 — (2) surprising without context ✅ (a planned, user-approved hook was parked), (3) genuine trade-off ✅. Not (1) hard to reverse.

---

**Status**: Accepted
**Date**: 2026-09-25
**Deciders**: User (project owner) · Supervisor
**Related**: T124–T127 · `docs/token-focus-finding-2026-09-25.md` · DDR-0001/0002 (the failed manual instrument) · DDR-0004 (spawn-prompt size) · DDR-0008 (deferred by this record)

---

## Context

T124 was planned on 2026-09-24 as a Bash-output compression hook (headroom's idea), a review persona
(ponytail) and a terse-output rule (caveman). The user then named evaluation as the hard part: the
work is about cost, so it must be measurable. DDR-0001 tried to measure spend by hand-pasted `/cost`
and failed twice; DDR-0002 retired it and said any future attempt needs a structural, automatic source.

Claude Code's session transcripts are that source: every API call records its `usage`, including the
cache-write / cache-read split. Replaying them (finding doc) showed:

- the compression hook would have saved **~1%** of spend, and removed a line the agent then needed in
  11% of the outputs it touched;
- **92%** of spend is Supervisor sessions, whose median call re-reads ~105k tokens;
- a spawned agent reads a median **16.8k tokens before its first edit** — `memory/MEMORY.md` most
  often — and that reading is **17%** of spawn spend.

The user's stated vision: work moves agent-to-agent by prompt, and each agent must stay focused on its
request without being overwhelmed by content.

## Decision

1. **Every token/context change is measured from transcripts** by one tested meter (T124), with an
   offline counterfactual *before* building and a before/after comparison *after* shipping. Per-spawn
   token metrics (pre-edit reading, context at first edit) are the primary signal — dollar totals over
   a handful of sessions are too noisy.
2. **Aim at focus, where the load is measured:** the spawned agent's pre-edit reading (T125) and the
   Supervisor's session length (T126). The output rule and review persona (T127) carry over from the
   user's 2026-09-24 decisions as quality work, with no savings claimed.
3. **Park the compression hook** (DDR-0008 deferred). Revive only if the meter shows a threshold that
   clears 5% of spend with low recall risk.
4. **Quality guard on every focus change:** Stage 4 P0/P1 findings and `/verify` results must not
   worsen over the evaluation window; otherwise revert.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|---|---|---|---|
| Build T124 as planned | Already specified; user-approved | ~1% saving; 11% recall risk; secrets on disk (DDR-0008) | Below DDR-0001's own 5% rollback trigger |
| Measure only, change nothing | Zero risk | Leaves the measured 17% pre-edit load and 92% Supervisor share untouched | Doesn't serve the stated vision |
| **Meter + focus changes (selected)** | Targets the measured load; every change has a gate | Focused spawns may miss a memory decision the task didn't obviously touch | Quality guard + revert covers it |

## Consequences

### Positive
- Cost and focus claims become reproducible numbers, regenerated from data nobody has to paste.
- Spawned agents start closer to their task.

### Negative (accepted trade-offs)
- The meter reads transcripts that contain everything the session saw, secrets included; it must print
  aggregates only and never content.
- Transcript format is Claude Code's, not a public contract; the meter must fail loudly on a shape
  change rather than report zeros.
- 14 historical spawns is a thin baseline; the evaluation window is counted in spawns, not days.

### Follow-up
- [ ] T124 reproduces the finding doc's numbers from the same transcripts
- [ ] T125/T126 evaluated against the baseline over ≥ 5 spawns / ≥ 5 Supervisor sessions; outcome recorded here

### Evaluation log (T125 window, pre-edit reading; baseline median 16.8k over 14 spawns)

| Date | Spawn | Startup reads | Pre-edit | Note |
|---|---|---|---|---|
| 2026-09-25 | T126 | skipped PROJECT_SPEC + role guide | 13.3k (via bash) | measured by hand, then by T128's meter |
| 2026-09-25 | T128 | all (explicit block) | 19.8k (via tool) | slice matched only broad dir keys (18 lines) |
| 2026-09-25 | T129 | all (explicit block) | 20.0k (via tool) | |

**Interim reading (3 of ≥5):** the slice removes the `MEMORY.md` read (~12k) as designed, but pre-edit
totals are dominated by mandatory reads (`PROJECT_SPEC.md` ≈ 5.4k tokens, role guide ≈ 2k) and task
files; with all startup reads done the median is above baseline. The −50% target looks unreachable
through the memory slice alone; the next measured lever is `PROJECT_SPEC.md` itself. Decide after ≥5.
