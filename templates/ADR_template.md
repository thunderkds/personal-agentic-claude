# [NNNN]. [Short decision title]

> **What this is**: An Architecture Decision Record — a permanent, dated note capturing *one* significant decision and the trade-off behind it.
> **When to write one**: Only when **all three** hold — (1) the decision is **hard to reverse**, (2) it is **surprising without context** (a future reader would ask "why on earth did they do that?"), and (3) it is the **result of a genuine trade-off** (real alternatives were on the table). If **any** is missing, do **not** write an ADR — record the decision in `PROJECT_SPEC.md` Memory/Insights instead.
> **Where it lives**: `docs/adr/NNNN-title.md` — `NNNN` is a 4-digit zero-padded sequence number (`0001`, `0002`, …), `title` is the kebab-case decision title (e.g. `docs/adr/0007-use-event-sourcing-for-orders.md`).
> **Source**: Offered by the `grill-with-docs` skill during Stage 2; the Supervisor approves before it is committed.

---

**Status**: Proposed | Accepted | Superseded | Deprecated
**Date**: [YYYY-MM-DD]
**Deciders**: [names / roles who signed off]
**Related**: [Task IDs Txxx] · [FR/NFR IDs] · [other ADRs, e.g. supersedes 0003 / superseded by 0012]

---

## Context

[The forces at play: the problem, the constraints, and *why a decision is needed now*. State what makes this hard to reverse and what would surprise a future reader. Keep it factual — no solution yet.]

---

## Decision

[The decision, stated in active voice: "We will …". Be specific and unambiguous — a future engineer should be able to act on this without guessing.]

---

## Alternatives Considered

[At least one seriously-considered alternative is **required** — an ADR without a real trade-off does not belong here (see the three-part gate above). Add rows as needed.]

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| [Chosen option] | [pros] | [cons] | **Selected** |
| [Alternative A] | [pros] | [cons] | [reason rejected] |
| [Alternative B] | [pros] | [cons] | [reason rejected] |

---

## Consequences

### Positive
- [Benefit gained by this decision]

### Negative (accepted trade-offs)
- [Cost or limitation we knowingly accept]

### Follow-up
- [ ] [Action, migration, or future revisit triggered by this decision — link Task IDs where they exist]
