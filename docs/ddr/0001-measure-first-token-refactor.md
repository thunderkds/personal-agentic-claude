# 0001. Measure token spend before refactoring for it

> **What this is**: A Design Decision Record — a permanent, dated note capturing *one* design decision and the trade-off behind it.
> **Gate**: 2-of-3 — (2) surprising without context ✅, (3) genuine trade-off ✅. Not (1) hard to reverse (additive-only), so not ADR-eligible.

---

**Status**: Accepted
**Date**: 2026-07-17
**Deciders**: hungnguyenhuu (user) · Supervisor
**Related**: BRAINSTORMING_LOG.md (2026-07-17 session) · task IDs assigned at Stage 2

---

## Context

The user wants to reduce billing spend across Supervisor sessions. Three candidate refactors surfaced in brainstorming: (A) trim/cache-stabilize `CLAUDE.md` (580 lines, injected every turn), (B) instrument actual per-stage/per-spawn token spend first, (C) run `slim-skills` on the four SKILL.md files over the repo's 150-line threshold (`learn` 182, `map-codebase` 165, `bugfix` 160, `code-review` 157).

No instrumentation exists; the user confirmed spend concentration is **unknown** (cold-start vs. spawn-heavy vs. report-output). The "obvious" fix (A) edits the file containing the Hard-Stop Gates on an unverified hypothesis. Costs are also confounded by prompt caching (cached reads ≈ 10% price, 1hr TTL; sub-agent spawns never inherit the parent session's cache) and per-model pricing (C0/haiku vs. C3/opus).

A future reader will ask: *"why is there a token-audit log, and why wasn't CLAUDE.md just trimmed?"* — that is this record.

## Decision

We will **measure before refactoring**: Option B (baseline token audit) with Option C (`slim-skills`) running in parallel as a free rider, and Option A explicitly **deferred** until baseline data justifies it.

Operational terms (canonical — see PROJECT_SPEC.md glossary):
- **Token Audit Log**: `reports/token-audit_<window>.md` — one-line entries at session cold-start, each stage transition, and each `Agent()` spawn; each entry tagged with a Task ID (or `overhead`), cache-hit vs. cache-miss, and model tier. `/cost` output logged at session end as ground truth.
- **Measurement Window**: closes at **7 logged sessions or 14 calendar days, whichever first**; a session = one conversation that ran `wake`. Same rule for baseline and validation windows.
- **Cost mapping**: $ per task ≈ session `/cost` split proportionally across that session's tagged entries.
- **Success criterion**: ≥20% reduction in $ per completed task at the same C-level, no Hard-Stop Gate regressions, over the validation window.
- **Rollback trigger**: <5% measured savings → revert/stop iterating.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| B + C parallel (measure first) | Zero wasted work; can conclude "don't refactor"; produces before/after evidence | Savings delayed 1–2 weeks; instrumentation discipline required | **Selected** |
| A now (trim CLAUDE.md) | Immediate, potentially largest savings if cold-start dominates | Edits Hard-Stop-Gate file on a guess; unprovable benefit without a baseline | Optimizing a hypothesis, not a measurement — violates Ask vs. Guess |
| C only (slim-skills alone) | Cheapest; tooling exists with checksum gate | Skills are invocation-triggered — likely a minor slice of spend | Doesn't address the suspected dominant costs; kept, but as a rider not the fix |

## Consequences

### Positive
- Refactor effort lands on the *measured* hotspot (could be A, spawn-prompt dedup, or report-output trimming)
- Evaluation is possible at all: baseline + validation windows use the same instrument
- The 4 oversized skills get slimmed regardless (repo's own >150-line rule satisfied)

### Negative (accepted trade-offs)
- No savings for the duration of the baseline window
- Audit-entry discipline is a per-session manual convention (deliberately no hook — Simplicity First); forgotten entries degrade the data
- With 7 sessions/side, only large wins (≈20%+) are reliably detectable — a marginal win is indistinguishable from noise, and is accepted as not worth a refactor

### Follow-up
- [x] Stage 2: generate TASK_GUIDEs for the audit convention (Option B) and the slim-skills run (Option C)
- [ ] After baseline window closes: follow-up brainstorm against real numbers to select the refactor
- [ ] After validation window: apply success criterion / rollback trigger; record outcome in this DDR's Status or a superseding DDR

---

## Amendment 1 — 2026-07-21: the manual instrument failed; window restarted

**Status**: Accepted · **Decider**: hungnguyenhuu (user) · **Task**: T040

The decision above is **unchanged** — measure before refactoring still stands. What failed is the
*instrument*, exactly where this record predicted it might.

Measured on 2026-07-21, day 4 of the 14-day window:

| Required | Actual |
|---|---|
| 7 logged sessions, or 14 days | 1 session logged |
| Entry at each cold-start / stage transition / spawn | last entry dated 2026-07-17 |
| `/cost` at session end as ground truth | never logged, not once |

T029, T034, T035, T036, T037 and T038 all merged on 2026-07-19 across multiple sessions and produced
zero entries. This is precisely the accepted trade-off recorded above — *"audit-entry discipline is a
per-session manual convention (deliberately no hook — Simplicity First); forgotten entries degrade
the data"* — and it degraded to nothing within 48 hours. The Simplicity First call to avoid tooling
was wrong here: the convention had no failure signal, so nobody noticed it had stopped.

**Amended terms:**
- The baseline window reopens at **2026-07-21** in `reports/token-audit_2026-07-21.md`.
  `reports/token-audit_2026-07-17.md` is closed **inconclusive at 1 of 7 sessions** and retained —
  the failure is itself the finding.
- Entries are **derived from `memory/event-trace/*.jsonl`** by `scripts/token-audit.sh` (T040)
  rather than typed by hand. The trace hook already captures every required event; no new always-on
  hook is added.
- **Known ceiling, accepted:** hooks cannot observe token counts and no hook can capture `/cost`.
  Only the event stream is automated; the `/cost` ground-truth line remains a manual paste at
  session end. Token counts must never be estimated or synthesised — a fabricated number is worse
  than a missing one.
- Window-close condition, cost mapping, success criterion (≥20%) and rollback trigger (<5%) are
  **unchanged**.

**Consequence for T030**: it stays blocked, but now on an instrument that records without anyone
remembering to. If the reopened window also comes up short, the honest conclusion is that
measure-first is not viable in this workflow — and that conclusion belongs in a superseding DDR,
not another amendment.
