# 0004. Uphold Hard-Stop Gate 1; pursue cheaper spawns rather than fewer spawns

**Status**: Accepted
**Date**: 2026-08-07
**Deciders**: hungnh1110@gmail.com (ruling), Supervisor (measurement + options)
**Related**: T062 (closed by this decision) · T061 (the telemetry that produced the measurement) · T063/T064/T065/T066 (the path this decision selects) · LR-0001, LR-0002 · supersedes nothing

---

## Context

T061 shipped per-spawn cost telemetry, and a probe run on 2026-08-07 produced the first hard numbers
about what the harness spends on sub-agent isolation:

| observation | value |
|---|---|
| cost of a spawn that does nothing (`echo`, 1 tool call) | **15,669 tokens** |
| T059 — a real three-line test fix | 48,401 tokens |
| T060 — a real C2 task | 81,220 tokens |
| T067 — a real C2 task, first production telemetry record | 83,802 tokens, 97.6% cache read |

Two findings followed. First, **every spawn pays a floor of ~15.7k tokens before doing any work** —
fixed, and paid once per spawn regardless of how lean the context is. Second, and against the
Supervisor's initial hypothesis, **trimming injected context is worth roughly a tenth of its nominal
token count**: an experiment varying only the unique prompt size (arm A 29 unique tokens, arm B 1,144)
moved `cache_creation` by **−1**, because the spawn prompt is already inside the Supervisor's cached
context before the agent starts. Nearly everything injected is billed as a cache read.

Taken together those point at spawn *count*, not spawn *content*, as the dominant lever. Eliminating a
spawn saves the whole floor; trimming artifacts nibbles at ~10% of the variable part.

The obstacle is a Permanent Rule. `CLAUDE.md` Hard-Stop Gate 1 ends: *"The Supervisor must never write
implementation code directly."* Eliminating spawns for small tasks means the Supervisor implements
them, which the Gate forbids by name.

**Gate criteria**: 2-of-3 hold. Not hard to reverse (this decision can be revisited whenever). It **is**
surprising without context — a future reader finding the 15.7k measurement would reasonably ask why the
largest measured lever was left on the table. It **is** a genuine trade-off, with three real
alternatives on the table and a measurable cost to the option chosen.

---

## Decision

**Hard-Stop Gate 1 stands unchanged. T062 is closed without implementation.** The harness will pursue
*cheaper* spawns (T064, T065, T066) rather than *fewer* spawns, accepting the ~15.7k floor as the
standing price of sub-agent isolation.

---

## Alternatives Considered

**A — Carve a C0/C1 exemption into Gate 1.** Keep the whole pipeline (TASK_GUIDE, Stage 4 review,
evidence) but let the Supervisor do the editing for small tasks. Largest saving: eliminates the floor
entirely for a whole task class rather than reducing it by a percentage. **Rejected.** Two costs. The
Gate exists because of recorded failure — LR-0001 and LR-0002 both document the Supervisor drifting
into implementation because a task "felt small", and perceived smallness is the precise trigger an
exemption would legitimise by name. More concretely, it collapses implementer and reviewer into one
role: over the 2026-08-07 session, acting as an independent reviewer caught a fixture whose provenance
claim was false, a line-cap assertion that was vacuous against blank-line padding, and three Evidence
tables that had gone stale. That separation is doing real work.

**B — Keep the Gate, make spawns cheaper.** **Chosen.** Attack the floor from the content side:
leaner injected context, fewer and smaller startup reads, a tighter guide format. Already registered
as T064/T065/T066; requires no rule change and no loss of review independence.

**C — Reject the direction outright and record the floor as the price of isolation.** Close T062 and
attempt nothing further on spawn cost. **Rejected** as needlessly absolute — B is available at low risk
and some saving is better than none, even if the ceiling is low.

**D — Defer until more telemetry accumulates.** **Rejected** for the Gate question specifically: more
cost data would refine the size of the prize but cannot answer whether a Permanent Rule should bend,
which is a judgment about review independence rather than about tokens. Deferral is still correct for
*sequencing* T064/T066, which do benefit from real records.

---

## Consequences

**Accepted, stated not hidden**: the largest measured lever is deliberately not pulled. The ~15.7k
floor remains on every spawn, and the chosen path has a **low ceiling** — since ~97% of injected
context arrives as cache reads, trimming it recovers roughly a tenth of its nominal token count. Nobody
should expect T064/T065/T066 to recover the floor; they will not.

**Preserved**: review independence, and the pipeline discipline the Gate protects. The implementer is
never its own sole oracle.

**Follow-on**: T062 is closed by this DDR rather than deleted, so the measurement and the reasoning stay
discoverable. T063 (prove injected memory is used at all) becomes the next executable task and gates
T065 — if agents never draw on injected memory, the correct change there is deletion rather than
compression.

**Revisit if**: telemetry over many real spawns shows the floor is materially larger than 15.7k, or
shows small tasks are far more numerous than assumed; or if a mechanism appears that preserves
implementer/reviewer separation without a second full spawn. Either would change the trade-off, not
just its magnitude.

**Weak counter-evidence on the record**: during the 2026-08-07 session the step-limit hook killed the
T053 and T055 agents mid-task and the Supervisor completed both itself, including all eight of T053's
tests. Both passed Stage 4 and merged clean. That is n=2, unplanned, and the Supervisor was also the
reviewer — noted so a future reader knows it was weighed, not overlooked.
