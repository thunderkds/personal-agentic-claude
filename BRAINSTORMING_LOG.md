# BRAINSTORMING_LOG.md
**Generated**: 2026-07-16
**Task / Context**: Introduce DDR (Design Decision Record) as the primary, low-ceremony decision-record artifact for day-to-day/feature-level design decisions; keep ADR (Architecture Decision Record) as an optional, rare escalation reserved for genuinely hard-to-reverse architectural changes.
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (moderate ambiguity, resolved via user Q&A)

---

## The Problem Space

Three overlapping decision-capture mechanisms already exist in this repo, verified by reading each:

1. **`memory/decisions.md`** — an append-only rolling log (149 lines and growing). Every task this session (T017, T018–T020, T021–T023, T025) wrote an entry here. It has no per-decision addressability — you can't link to "the T025 decision" as a standalone artifact, only grep for a heading inside a long file.
2. **ADR** (`templates/ADR_template.md`, `docs/adr/NNNN-title.md`) — gated by a strict 3-of-3 test (hard to reverse **AND** surprising without context **AND** a genuine trade-off). Offered by `grill-with-docs` at Stage 2. Verified via `ls docs/adr` → **the folder doesn't exist**; despite ~15+ decisions logged this repo's life, zero have ever cleared the ADR bar. The gate is calibrated for architecture-level stakes this project rarely produces (a doc/skill-authoring framework, not a service with a database/deployment topology to reverse).
3. **`docs/solutions/`** (via `compound` skill) — a *different* axis entirely: reactive problem→solution capture post-fix, not a decision record.

The user's diagnosis, confirmed through this session's Q&A: ADR's bar is calibrated for architecture that "is hard to cover" and "not required by the time" to change — correctly rare. But that leaves a real gap: decisions like this session's T017 (Depends-on/Entry-point field design), T025 (craft-agent whole-team-mode / draft-only / base-team-optional), or T021–T023 (spawn-hook hardening approach) are genuine **design** decisions — real alternatives were weighed, a specific shape was chosen — but none of them are architecture-level enough to ever clear ADR's 3-of-3 gate. They currently only get a paragraph buried in the ever-growing `decisions.md` stream, with no standalone, linkable, supersede-able record.

**DDR fills that gap**: a mid-tier artifact, structurally identical to ADR (one file per decision, `Context`/`Decision`/`Alternatives`/`Consequences`, supersession-linkable) but gated at 2-of-3 instead of 3-of-3, making it the *default* write-up for real design decisions, while ADR stays the rare escalation for the (currently zero, possibly always zero) cases that hit all three criteria.

---

## Questions for the User

None outstanding — storage shape, write-gate, decisions.md relationship, and skill-wiring order were all resolved via `AskUserQuestion` before this log was written.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | The Simple Path | New `docs/ddr/NNNN-title.md` artifact, `templates/DDR_template.md` cloned from ADR's shape with a 2-of-3 gate; `grill-with-docs` checks DDR first, ADR as escalation; `decisions.md` keeps a one-liner pointer | Low-Medium | ~90 lines template + ~15 lines skill wiring | Low | ✅ Yes |
| B | The Scalable Path | Same as A, plus a new `ddr-index` skill that maintains `docs/ddr/INDEX.md` (auto-generated table of contents, supersession graph) | Medium | ~90 + ~60 lines | Low-Medium | |
| C | The Minimalist Path | Don't add a new file type — just add a `### Design Decisions` subsection inside `memory/decisions.md` with per-decision headings addressable by anchor link | Low | ~10 lines (doc convention only) | Low | |

### Option A — The Simple Path
**Approach**: `templates/DDR_template.md` — near-identical structure to `templates/ADR_template.md` (Status/Date/Deciders/Related, Context, Decision, Alternatives Considered, Consequences), but the header note states the 2-of-3 gate instead of 3-of-3, and files live in `docs/ddr/NNNN-title.md` (independent numbering sequence from ADR's `docs/adr/`). `grill-with-docs` Stage 2 evaluates the DDR gate first; if a decision also clears all 3 ADR criteria, it flags "this is ADR-eligible — escalate?" per the user's chosen wiring. `memory/decisions.md` keeps its existing one-liner-per-decision habit unchanged, just adding a `→ see docs/ddr/NNNN` link when a DDR was written (mirrors the existing `MEMORY.md → decisions.md` link pattern already in use).
**Pros**: Structurally proven (literally copies ADR's already-designed shape); zero disruption to the existing diff-driven memory-update habit; immediately usable — every decision this session (T017, T021–T023, T025) would have qualified and can be retro-filed as an example.
**Cons**: Two near-identical templates (ADR and DDR) sitting side by side — someone unfamiliar with the distinction has to read the header note on both to know which one applies.
**Why it might fail**: If the 2-of-3 gate isn't meaningfully different from "just write one for anything," DDR becomes the new decisions.md-equivalent flood, defeating its own purpose of being more selective than the rolling log. Mitigated by keeping the gate an explicit 2-of-3 check rather than "any decision with alternatives" (the rejected alternative gate from Q&A).

### Option B — The Scalable Path
**Approach**: All of Option A, plus a maintained `docs/ddr/INDEX.md` auto-generated by a new `ddr-index` skill that lists every DDR with status/date/one-liner and renders the supersession chain.
**Pros**: Solves discoverability at scale — useful once dozens of DDRs exist.
**Cons**: No such scale problem exists yet (zero DDRs, zero ADRs currently). Adding an index-maintenance skill before there's anything to index is exactly the kind of premature abstraction Simplicity First rejects.
**Why it might fail**: Violates the 50% Rule outright — this is solving a discoverability problem for a future state 20+ DDRs from now, not the problem in front of us.

### Option C — The Minimalist Path
**Approach**: No new folder/template — add a `### Design Decisions` heading convention inside the existing `memory/decisions.md`, using markdown anchors for linkability.
**Pros**: Zero new files, minimal code volume.
**Cons**: Directly contradicts the user's own resolved answer ("one file per decision... mirrors ADR's addressable, linkable, supersede-able shape") — a heading inside a single growing file is not truly addressable/supersede-able the way a standalone file with a stable path is; `git log --follow docs/ddr/0003-....md` gives per-decision history that a heading inside a monolithic file cannot.
**Why it might fail**: Rejected by the user's explicit answer in Q&A, not just theoretically weaker — surfaced here for completeness per the divergent-thinking requirement, not as a live contender.

---

## 50% Rule Check

Option A is already the minimal viable shape: it reuses ADR's proven template structure wholesale (no new document design work) and reuses the existing `grill-with-docs`/`decisions.md` wiring points rather than inventing new pipeline stages. The only further cut considered — skipping the `decisions.md` one-liner pointer — was rejected: without it, the diff-driven memory-update pass (which greps `decisions.md` for changed-file references) would have no way to discover that a DDR exists for a given file, silently breaking the existing memory-sync habit.

---

## Recommended Path

**Option A — The Simple Path**

Directly matches every constraint resolved in Q&A (one-file-per-decision shape, 2-of-3 gate, one-liner pointer in `decisions.md`, DDR-default/ADR-escalation wiring in `grill-with-docs`), reuses a proven template structure instead of designing a new one, and doesn't build discoverability tooling (Option B) for a scale problem that doesn't exist yet.

---

## Surgical Scope

Files that **should** be touched:
- `templates/DDR_template.md` — new, cloned from `templates/ADR_template.md`'s shape with the 2-of-3 gate header
- `.claude/skills/grill-with-docs/SKILL.md` — Stage 2 section: evaluate DDR gate first, ADR as escalation when all 3 criteria also hold
- `CLAUDE.md` — folder-structure requirements list (add `templates/DDR_template.md`); update the ADR-related sentence in Step 1.5 Ambiguity Resolution Protocol to mention DDR as the default
- `PROJECT_SPEC.md` — glossary: add DDR term, distinguish from ADR and from `memory/decisions.md`
- `memory/decisions.md` — no structural change; future entries gain an optional `→ see docs/ddr/NNNN` pointer when applicable

Files that **must not** be touched:
- `templates/ADR_template.md` — stays as-is; ADR's 3-of-3 gate is explicitly not being loosened, only supplemented
- `.claude/skills/compound/SKILL.md`, `docs/solutions/` — different axis (reactive problem→solution), out of scope
- `memory/MEMORY.md` hot-tier structure — unchanged; DDR entries follow the same one-liner-with-link pattern already used for `decisions.md`/`glossary.md`/`learnings.md`

---

## Edge Case Checklist for TASK_GUIDE

- [ ] A decision meets DDR's 2-of-3 gate AND all 3 ADR criteria simultaneously — `grill-with-docs` must flag it as ADR-eligible and ask before defaulting to DDR-only, not silently downgrade an architecture-level decision
- [ ] Numbering collision — `docs/ddr/` and `docs/adr/` use independent sequences (both starting at `0001`); a Related-decisions cross-reference between a DDR and an ADR must disambiguate (`DDR-0003` vs `ADR-0003`, not bare `0003`)
- [ ] Retro-filing existing decisions.md history — this task drafts the mechanism only; retroactively splitting the 149-line `decisions.md` into individual DDR files is explicitly out of scope unless the user asks for it separately
- [ ] A DDR is later superseded — the template's `Related` field must support `supersedes DDR-000X` / `superseded by DDR-000Y`, mirroring ADR's existing supersession field, so status tracking doesn't silently rot
- [ ] `grill-with-docs` currently runs in two modes (`requirement`, `terminology`) — the DDR/ADR gate check belongs in terminology mode's "Where decisions land" section, not requirement mode; must not blur the two modes' distinct responsibilities

---

## Next Actions

1. Run `grill-with-docs` (terminology mode) to sharpen DDR's canonical definition against the glossary — distinguish DDR from ADR and from a plain `decisions.md` entry in `PROJECT_SPEC.md`'s glossary, same as done for `craft-agent`/T025.
2. Proceed to Stage 2 (`/plan`): generate a `TASK_GUIDE_Txxx.md` for this work (Hard-Stop Gate 1 — no template/skill edits without a guide).
3. Draft `templates/DDR_template.md` cloned from `templates/ADR_template.md`'s shape, with the 2-of-3 gate header per the Edge Case Checklist above.
4. Update `.claude/skills/grill-with-docs/SKILL.md` and `CLAUDE.md` per Surgical Scope.

---

## User Selection

> **Approved direction**: Option A — The Simple Path
> Approved by user on 2026-07-16.
