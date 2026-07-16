# [NNNN]. [Short decision title]

> **What this is**: A Design Decision Record — a permanent, dated note capturing *one* design decision and the trade-off behind it. This is the **default** standalone decision artifact for day-to-day design work.
> **When to write one**: When **2-of-3 (at least two of three)** hold — (1) the decision is **hard to reverse**, (2) it is **surprising without context** (a future reader would ask "why on earth did they do that?"), and (3) it is the **result of a genuine trade-off** (real alternatives were on the table). If fewer than 2-of-3 hold, do **not** write a DDR — record the decision in `memory/decisions.md` instead. If all 3-of-3 hold, it is ADR-eligible — flag it and ask the user before escalating to a full ADR (see `templates/ADR_template.md`); never silently upgrade.
> **Where it lives**: `docs/ddr/NNNN-title.md` — `NNNN` is a 4-digit zero-padded sequence number (`0001`, `0002`, …), `title` is the kebab-case decision title (e.g. `docs/ddr/0007-use-event-sourcing-for-orders.md`). DDR numbering is independent of ADR numbering — always disambiguate with the `DDR-`/`ADR-` prefix, never a bare number.
> **Source**: Offered by the `grill-with-docs` skill during Stage 2; the Supervisor approves before it is committed.

---

**Status**: Proposed | Accepted | Superseded | Deprecated
**Date**: [YYYY-MM-DD]
**Deciders**: [names / roles who signed off]
**Related**: [Task IDs Txxx] · [FR/NFR IDs] · [other DDRs, e.g. supersedes DDR-0003 / superseded by DDR-0012]

---

## Context

[The forces at play: the problem, the constraints, and *why a decision is needed now*. State which of the 2-of-3 gate criteria apply. Keep it factual — no solution yet.]

---

## Decision

[The decision, stated in active voice: "We will …". Be specific and unambiguous — a future engineer should be able to act on this without guessing.]

---

## Alternatives Considered

[At least one seriously-considered alternative is **required** — a DDR without a real trade-off does not belong here (see the gate above). Add rows as needed.]

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
