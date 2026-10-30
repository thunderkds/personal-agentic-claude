# BRAINSTORMING_LOG_tech-lead-pack.md
**Generated**: 2026-10-30
**Task / Context**: `docs/prd/PRD_tech-lead-pack.md` (grilling D1–D7, gate PASS) — a `tech-lead` agent that owns a project's top documents.
**Skill**: `Skill({ skill: "brainstorming" })`
**Scope tier**: Standard. Requirements are locked (D1–D7); what is open is the shape of the pack and three mechanisms the PRD hands to brainstorming.

---

## The Problem Space

The PRD fixes *what*: a `tech-lead` agent, shipped as `packs/tech-lead`, writes a document map
(`docs/architecture/README.md`) that the user approves, then C4 + overview, per-core-feature sequence
and journey diagrams, an ER diagram, a risk register and a roadmap, all Markdown + Mermaid. It links
the kit's existing ADR / PRD / PROJECT_SPEC / glossary / to-issues / security-review output instead of
copying it. Triggers: Stage 2, on demand, refresh after a merge.

Open, for this log:
1. Pack shape — one skill or one skill per document type.
2. Refresh trigger (FR-007c) — how "this merge changes the architecture or data model" is detected.
3. Inferred content (FR-007b) — how a document drafted from code marks what it guessed.

**Verified facts that change the plan (claim gate):**
- **Packs cannot be activated today.** ADR-0002 (`docs/adr/0002-one-confirmed-menu-driven-installer.md:81-95`)
  made `packs/` a dormant catalog: copied into the project, linked to no CLI. Activation is a
  `select-packs` skill that copies a pack's `agents/*.md` and `skills/*/` into `agents/` / `skills/`.
  That skill is **T117, still Todo** (`PROJECT_KANBAN.md:51`). ADR-0002 also states that a verbatim
  copy of kit-shipped pack files after explicit approval is configuration, not implementation — so
  the Supervisor may do it by hand.
- The `sh ~/.supervisor/setup.sh --pack=<name>` line in each existing `PACK.md` is stale: `setup.sh`
  has no `--pack` option. PRD FR-001 copied that line and is corrected below.
- `tests/test_pack_catalog.sh` (T116) checks that `packs/` ships as a catalog; a new pack folder must
  keep it green.
- Stage 5 item 4 (`docs/claude-md/pipeline-stages.md:244`) is already a diff-driven pass over
  `git diff HEAD~1 --name-only` — the natural place for the refresh check.
- `memory/glossary.md` and `templates/ADR_template.md` exist (FR-004 link targets).

## Questions for the User

1. Activation: since T117 is not built, is a documented manual copy (Supervisor copies the pack's
   files into `agents/`/`skills/` after you approve) acceptable for v1? **Recommended: yes**; T117
   stays its own task and later automates the same copy.

## Alternative Paths

### Option A — Agent + one skill per document type
**Approach**: `agents/tech-lead.md` + skills `doc-map`, `c4-overview`, `flow-diagrams` (sequence +
journey), `er-diagram`, `risk-register`, `roadmap` — 6 skills.
**Pros**: each skill is small and testable alone; the Supervisor could run one skill without the agent.
**Cons**: 7 files of doctrine for one role; the agent must still know the whole set to write the map;
duplicated rules (Mermaid conventions, citing sources, inferred markers) across 6 skills.
**Why it might fail**: skill sprawl is exactly what the user's "make the kit simple" direction
(2026-10-30 plugin/distribution discussion) pushes against; the 6 skills drift apart.

### Option B — Agent + one `architecture-docs` skill (sections per document)
**Approach**: `agents/tech-lead.md` (role, boundaries, triggers, map-first rule) + one skill
`architecture-docs` with one section per document type (when needed, what it must contain, a Mermaid
skeleton, its watched paths) and the shared rules once. The map template sits in the skill.
**Pros**: 2 doctrine files; shared rules written once; the map, the document rules and the refresh
watch-list live in one place, so they cannot drift.
**Cons**: one longer skill (~200 lines); running "just the ER diagram" means invoking the whole skill
with an argument.
**Why it might fail**: the skill grows each time a document type is added (algorithm diagrams later)
— mitigated by the section-per-type layout, split only when one section outgrows the rest.

### Option C — Core agent, no pack
**Approach**: put `tech-lead.md` straight into `agents/` (always active), skill into `skills/`.
**Pros**: works today with no activation step; no T117 dependency.
**Cons**: contradicts D2 (optional, base team unchanged); every project, including a small CLI, gets
the role and its Stage 2 trigger.
**Why it might fail**: reverses a user decision made in this session to dodge a missing installer step.

## 50% Rule Check

Option B is already the 50% version of A (2 files instead of 7). A further halving — the agent file
alone, with the document rules inline — saves one file but puts ~200 lines of document rules into
every spawn of the agent's system prompt, even for a one-document refresh. Not worth it: the skill
loads only when used.

## Recommended Path

**Option B — Agent + one `architecture-docs` skill, activated by a documented manual copy until T117.**

Mechanisms:
- **Refresh trigger (FR-007c):** the approved map lists, per document, its **watched paths** (globs,
  e.g. ER → `**/migrations/**`, `**/schema*`; C4 → new top-level service folders, `docker-compose*`,
  deploy manifests). Stage 5 item 4 gains one sub-step: if `docs/architecture/README.md` exists and
  `git diff HEAD~1 --name-only` matches a watched path, the Supervisor spawns `tech-lead` in refresh
  mode for those documents only. Deterministic, no judgment in the trigger; the user edits the globs
  in the map.
- **Inferred content (FR-007b):** each document ends with a `Sources` list of cited file paths; any
  statement not backed by a cited file carries `(inferred)` inline. The map's "needed" reasons follow
  the same rule.
- **Activation:** `PACK.md` documents the manual copy (two `cp` commands) and states that `select-packs`
  (T117) will automate it. The stale `--pack=` line is not copied into the new PACK.md. (Fixing it in
  the other five PACK.md files is out of scope — note it as a follow-up.)

## Surgical Scope

**Touch:**
- `packs/tech-lead/PACK.md`, `packs/tech-lead/agents/tech-lead.md`, `packs/tech-lead/skills/architecture-docs/SKILL.md` (new)
- `docs/claude-md/pipeline-stages.md` — Stage 2 pointer + Stage 5 item 4 refresh sub-step (FR-009)
- `AGENTS.md` — one pointer line only if the stage index needs it (FR-009; prefer pipeline-stages.md only)
- a new test (e.g. `tests/test_tech_lead_pack.sh`) — pack layout, agent frontmatter, skill sections, map template fields
- `docs/prd/PRD_tech-lead-pack.md` — FR-001 correction

**Must not touch:**
- `agents/` / `skills/` root canon (activation is a later, approved copy — not part of building the pack)
- `setup.sh`, `MANIFEST`, the other five packs, `PRD.md`, `PROJECT_SPEC.md` content (FR-002)
- `tests/test_pack_catalog.sh` logic (it must simply stay green)

## Edge Case Checklist for TASK_GUIDE

- [ ] Project with no stored data → map marks ER "not needed" with a reason; no empty ER file written.
- [ ] Existing repo with no `PROJECT_SPEC.md` (on-demand mode) → agent drafts from code, every claim cited or `(inferred)`; it does not create `PROJECT_SPEC.md`.
- [ ] `docs/architecture/` already exists with user-written files → agent never overwrites an unlisted file; the map links it.
- [ ] Refresh with no watched path matched → no spawn, no change.
- [ ] Refresh where the user edited a document by hand → agent updates only the affected section, keeps the rest.
- [ ] `[auto]` mode → map only, listed in the final report (FR-006).
- [ ] Mermaid C4 support is experimental in Mermaid → skill notes a `flowchart` fallback if a renderer rejects `C4Context`.
- [ ] Agent tries to edit `PRD.md`/`PROJECT_SPEC.md`/`PROJECT_KANBAN.md` → forbidden by its scope section (FR-002); test greps the agent file for that rule.
- [ ] `tests/test_pack_catalog.sh` stays green with the new pack folder.

## Next Actions

1. User picks a path (below) and answers the activation question.
2. Correct PRD FR-001 (activation per ADR-0002, not `setup.sh --pack`).
3. Stage 2: register the task on `PROJECT_KANBAN.md`, write `tasks/TASK_GUIDE_T218.md` (C2, Risk Low, P1, Common-Infrastructure-Agent — doctrine/Markdown + a shell test).
4. Note follow-up: stale `--pack=` line in the five existing `PACK.md` files.

## User Selection

**Selected path**: _pending_
**Date**: 2026-10-30
**Rationale**: _pending_
