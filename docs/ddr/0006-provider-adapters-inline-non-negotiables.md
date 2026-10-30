# 0006. Provider adapters inline the non-negotiables; `CLAUDE.md` stays primary

**Status**: Accepted
**Date**: 2026-08-24
**Deciders**: User (product owner), Supervisor
**Related**: T090 · reverses part of T051 · applies the T069 split-by-mandate precedent · `docs/brainstorming/BRAINSTORMING_LOG_multi-provider.md`

---

## Context

The kit is marketed as provider-agnostic but its doctrine reaches only Claude Code with a guarantee.
The three delivery channels are mutually exclusive: `CLAUDE.md` is auto-injected by Claude Code and
not read by Codex or Cursor; `AGENTS.md` is auto-read by Codex and not by Claude Code; Cursor reads
`.cursor/rules/*.mdc`, which does not exist in this repo.

`AGENTS.md` exists today at 12 lines and **deliberately omits** the Karpathy Engineering Principles
and the Hard-Stop Gates — T051 (2026-08-04) excluded them specifically to stop `AGENTS.md` becoming a
second source of truth. The consequence is that a Codex-only user receives none of the kit's
non-negotiable rules through any guaranteed channel.

Measured evidence that a pointer does not close this gap (T069, 2026-08-10): all four role guides
carried an instruction to read `general-agent-template.md`, and the event trace recorded **9 `Read`
records across 66 task buckets**. The kit has hit this failure class three times (T041 → T066 → T069),
plus T085's link that "looks live and is not". T065 separately disproved that an instruction to read
a file is equivalent to the file arriving.

**Gate criteria**: (1) hard to reverse — **no**, these are documentation files. (2) surprising without
context — **yes**, it reverses an explicit, reasoned T051 decision. (3) genuine trade-off — **yes**,
static adapters versus a generator were both seriously on the table. **2 of 3 → DDR, not ADR.**

---

## Decision

We will keep `CLAUDE.md` + `docs/claude-md/` as the single **primary** source of truth, and add one
thin, hand-written **adapter** per provider (`AGENTS.md`, `.cursor/rules/agent-base.mdc`). Content is
split by mandate, not by file:

- **Inlined into every adapter** (because the mandate must reach the context): the four Karpathy
  principle names, the six Hard-Stop Gate titles, the untrusted-content boundary rule, and
  "no TASK_GUIDE = no work" — as one-liners, not full prose.
- **Left behind a pointer** (elaboration, read on demand): pipeline stage detail, Phase 0 protocol,
  folder structure, naming conventions, memory protocol — all in `docs/claude-md/`.
- **Stated explicitly in every adapter**: which gates that provider **cannot** enforce.

Adapters gain content but not authority: each keeps its "`CLAUDE.md` and `.claude/agents/` remain
canonical" line. Drift is caught by a conformance test asserting **byte-identical** shared spans with
`grep -qF`, shipped with a mutation control proving it goes RED.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| **Static adapters, non-negotiables inlined** | Smallest diff; no new machinery; each adapter auto-injected in full by its own provider; one C1 task | N copies of the non-negotiables; adding a 7th gate means editing N files | **Selected** |
| Generated adapters from a neutral core + CI regeneration check | One edit point; drift structurally impossible | Protection stops at this repo's CI — `setup.sh` copies adapters into downstream projects that have no generator and no CI, which is where the kit runs. Adds a CI entry point; T036 found `smoke-install.sh` silently red for 3 days across 5+ merged PRs. T051's own brainstorm already converged static-over-generated on the same inputs | Rejected — benefit does not reach the deployment target |
| `AGENTS.md` becomes canonical, `CLAUDE.md` points at it | Matches a pattern seen in other repos | Privileges Codex's channel and demotes Claude's — the identical reachability trap, mirrored. User explicitly required an additive change | Rejected at grill stage |
| Full doctrine duplicated into every adapter (~200 lines each) | Zero reachability risk | Three additional sources of truth; `CLAUDE_LEGACY.md` (629 lines, hand-synced) already demonstrates the outcome | Rejected before adversarial review |

---

## Consequences

### Positive
- A Codex-only or Cursor-only user receives the kit's non-negotiables through a **guaranteed** channel.
- The kit's provider-agnostic claim becomes structurally true rather than asserted.
- `CLAUDE.md` is untouched — Claude Code behaviour is unchanged (the user's explicit constraint).

### Negative (accepted trade-offs)
- The non-negotiables text exists in N places. Adding a Hard-Stop Gate becomes an N-file edit, and the
  conformance test will (correctly) fail until all N are updated.
- The adapters are documentation. They cannot make hooks or skills run on another provider, and they
  must say so — an adapter that reads as "run the full pipeline on Codex" would reproduce T085's defect.

### Follow-up
- [ ] T090 — implement the adapters, the limits sections, and the conformance test
- [ ] Neutralising `docs/claude-md/pipeline-stages.md` (27 of 38 provider-coupled refs) is **deliberately
      out of T090's scope** — it trips Hard-Stop Gate 2's C2 structural floor and needs its own task
- [ ] Revisit if a 4th provider is added: at N=4 the generator's cost/benefit inverts and this DDR
      should be reconsidered rather than assumed
