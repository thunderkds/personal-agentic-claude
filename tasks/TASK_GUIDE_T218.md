# TASK_GUIDE — T218: `packs/tech-lead` — a `tech-lead` agent and an `architecture-docs` skill for a project's top documents
**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`
6. C2: read `memory/codebase-map.md` for layout
7. Read `docs/prd/PRD_tech-lead-pack.md` (decisions D1–D7, FR-001..FR-009) and `docs/brainstorming/BRAINSTORMING_LOG_tech-lead-pack.md` (Option B, mechanisms, edge cases)

---

## Requirement (Pillar 1 — Adapt the requirement)

User (2026-10-30): "should we create another child in the family that contain the thinking of technical lead, project manager, or anyone in the top level which can identify the top documents of project" — colleague's list: C4 diagram, ADR, high-level architecture, algorithm diagram, sequence diagram, ER diagram, business flow (journey diagram) for core features, terms dictionary, timeline/roadmap, epics and user stories, BA diagrams/specs, technical risks, security. Then: "techlead should be agents, not the packs, right?" → agent shipped in a pack. Then: "compose all the tasks related, run with [auto], remember to add the docs, guide for that."

**Restated intent**:
> Ship an optional `packs/tech-lead` pack: a `tech-lead` agent that first writes a document map the user approves, then writes and refreshes the project's top documents (C4 + overview, per-core-feature sequence and journey diagrams, ER diagram, risk register, roadmap) as Markdown + Mermaid in `docs/architecture/`, linking — never copying — the kit's existing ADR/PRD/PROJECT_SPEC/glossary/epics/security-review output. The pack includes its own user guide (how to activate, when to spawn, what it writes).

**Out of scope** (what this task explicitly does NOT do):
- Editing `docs/claude-md/pipeline-stages.md` or `AGENTS.md` (the Stage 2 / Stage 5 pointers are T219 — hub file, separate review)
- The stale `setup.sh --pack` lines in the other packs, `templates/PACK_template.md` and `docs/claude-md/folder-structure.md` (T220)
- Activating the pack in this repo (copying into `agents/` / `skills/`) — dormant catalog per ADR-0002; `select-packs` is T117
- Algorithm diagrams; a separate project-manager agent; any MCP; easy-verifier document detection

**Requirement Refs** (from `docs/prd/PRD_tech-lead-pack.md`):
- FR-001: pack layout, dormant catalog, activation by approved copy
- FR-002: agent owns top documents only; never edits PRD.md / PROJECT_SPEC.md / PROJECT_KANBAN.md
- FR-003: the v1 document set
- FR-004: link existing kit documents, never copy them
- FR-005: document map first, user approval before any other document
- FR-006: `[auto]` → map only
- FR-007: three triggers (Stage 2, on demand from code with Sources/(inferred), refresh by watched paths) — described in the agent/skill; the pipeline pointer itself is T219
- FR-008: `docs/architecture/`, Markdown + Mermaid
- NFR-001: no new runtime dependency

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — signed `auto (Supervisor)` 2026-10-30
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — terms come from the PRD grilling (D1–D7): Pack catalog, Activated pack (ADR-0002), document map, watched paths
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `docs/prd/PRD_tech-lead-pack.md` and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `packs/tech-lead/PACK.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `packs/tech-lead/PACK.md`, `packs/tech-lead/agents/tech-lead.md`, `packs/tech-lead/skills/architecture-docs/SKILL.md` exist. The agent frontmatter has `name: tech-lead`, a `description:` starting "Use when", `tools:` without `Agent`; the skill frontmatter has `name: architecture-docs` and a `description:` | FR-001 |
| 2 | The skill has one `###` section per v1 document type — C4 + high-level overview, sequence diagram, journey diagram, ER diagram, risk register, roadmap — and each section states: when it is needed, required content, a Mermaid skeleton (`C4Context`/`C4Container` with a `flowchart` fallback note, `sequenceDiagram`, `journey`, `erDiagram`, a risk table, `gantt` or `timeline`), and default watched paths | FR-003, FR-007, FR-008 |
| 3 | The skill holds a document-map template for `docs/architecture/README.md` with columns: document, needed / not needed, reason, file, watched paths; plus link rows for ADR (`docs/adr/`), `PRD.md`, `PROJECT_SPEC.md`, `memory/glossary.md`, epics/stories (`to-issues` / `PROJECT_KANBAN.md`), security review | FR-004, FR-005 |
| 4 | The agent file states, as rules: map first and no other document before user approval; `[auto]` → map only, listed for approval in the final report; never edit `PRD.md`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`; never overwrite a file under `docs/architecture/` the map does not list; every drafted document ends with a `Sources` list and marks unbacked statements `(inferred)`; refresh updates only the documents whose watched paths the diff matched | FR-002, FR-005, FR-006, FR-007 |
| 5 | `PACK.md` follows the existing PACK.md layout (When to use / Do NOT select / What this pack adds / Boundary from core agents / Agents installed / Skills installed) and adds a **user guide**: activation by copying the two files into `agents/` and `skills/` after approval (ADR-0002; `select-packs` T117 will automate it), the three triggers, what lands in `docs/architecture/`, and an example spawn. It contains no `setup.sh --pack` line | FR-001, FR-007, user "add the docs, guide" |
| 6 | `README.md`'s pack list names `tech-lead`. `site/index.html` `#packs` table has a `tech-lead` row (Domain: top project documents — C4, sequence, journey, ER, risks, roadmap; Agent `tech-lead`; Skills `architecture-docs`) built exactly like the existing rows, and the hero count reads 6 optional domain packs | user "add the docs"; `tests/test_site_content.py::test_every_pack_appears_on_page` (T087) fails without it |
| 7 | `tests/test_tech_lead_pack.sh` checks AC 1–5 and the README line, and passes; it includes at least one mutation control (a mutant copy with a rule removed makes a check fail), as `tests/test_pack_catalog.sh` does. `tests/test_pack_catalog.sh` and `python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q` pass (update only the `5optional domain packs` text entry in `test_site_visual_first.py` to the new count, with its id regenerated the way that file does) | Gate 5, NFR-001 |
| 8 | Negative: nothing under `agents/`, `skills/`, `.claude/` changes; no new dependency file | Out of scope, NFR-001 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The pack folder | Files, frontmatter and sections of AC 1–6 present | `bash tests/test_tech_lead_pack.sh` |
| 2 | A mutant copy of the agent file without the "never edit PROJECT_SPEC.md" rule | The test's check fails on the mutant | mutation control in the same test |
| 3 | The kit with the new pack folder | Catalog test and site tests green | `bash tests/test_pack_catalog.sh`; pytest site tests |
| 4 | Real run: the skill's map step followed by hand on this repo, output to a scratch dir | A plausible map with needed/not-needed reasons and linked kit docs | Supervisor at Stage 5 (`Checks:`), not committed |

### Verification Command (exact, runnable)

```bash
bash tests/test_tech_lead_pack.sh && bash tests/test_pack_catalog.sh && python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q
```

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#packs` table | headless-browser screenshot at 1280 px | 6 rows; the new row looks like the other five (same `<code>` chips, `data-label` cells) |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Markup and classes | diff of the new `<tr>` against the `api` row | same elements, attributes and `data-label` values; no new CSS, no inline style |
| Typography / colors | computed style of the new row's `<code>` vs the `api` row's | identical |
| Spacing / layout | computed style | identical row height rules; no new class |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375px) | screenshot + `document.documentElement.scrollWidth == clientWidth` | row renders as the stacked `data-label` card like the others; no horizontal scroll |
| Tablet (768px) | screenshot | table readable, no overflow |
| Desktop (1280px) | screenshot | 6-row table |

---

## Approach

**Pattern reference**: `packs/api/PACK.md`, `packs/api/agents/api-designer.md`, `packs/api/skills/contract-review/SKILL.md` — layout, frontmatter, tone; `tests/test_pack_catalog.sh` — shell test style, `pass`/`fail`/`verdict` helpers, mutation controls.

**Vital slice**: the agent's rules (AC 4) and the skill's map template + per-document sections (AC 2–3) — that is what the Supervisor and the agent actually run.
**Cut list**: algorithm diagrams (D4 deferred); per-document skills (Option A rejected); automatic activation (T117); pipeline pointers (T219); stale `--pack` lines elsewhere (T220).

Brainstorming Option B (selected in auto mode, `RULE ⚠`): one agent + one `architecture-docs` skill with a section per document type; shared rules (Mermaid conventions, Sources + `(inferred)`, never overwrite unlisted files) written once in the skill. Keep the skill around 200 lines. The agent file holds role, boundaries, triggers and hard rules; the skill holds the how.

---

## Edge Case Checklist

- [ ] Project with no stored data → map marks ER "not needed" with a reason; no empty ER file written.
- [ ] Existing repo with no `PROJECT_SPEC.md` (on-demand mode) → agent drafts from code, every claim cited or `(inferred)`; it does not create `PROJECT_SPEC.md`.
- [ ] `docs/architecture/` already exists with user-written files → never overwrite an unlisted file; the map links it.
- [ ] Refresh with no watched path matched → no change.
- [ ] Refresh where the user edited a document by hand → update only the affected section.
- [ ] `[auto]` mode → map only (FR-006).
- [ ] Mermaid C4 is experimental → `flowchart` fallback noted.
- [ ] `tests/test_pack_catalog.sh` stays green.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `packs/tech-lead/PACK.md` | new — pack doc + user guide |
| `packs/tech-lead/agents/tech-lead.md` | new — agent |
| `packs/tech-lead/skills/architecture-docs/SKILL.md` | new — skill |
| `tests/test_tech_lead_pack.sh` | new — test |
| `README.md` | add `tech-lead` to the pack list (line ~73) |
| `site/index.html` | `#packs` table row + hero count 5 → 6 |
| `tests/test_site_visual_first.py` | only the `5optional domain packs` entry |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `docs/claude-md/pipeline-stages.md`, `AGENTS.md` | T219 (hub file) |
| `site/index.html` outside `#packs` and the hero count | surgical |
| `packs/{mobile,data,devops,ai-agent,api}/PACK.md`, `templates/PACK_template.md`, `docs/claude-md/folder-structure.md` | T220 |
| `agents/`, `skills/`, `.claude/`, `setup.sh`, `MANIFEST` | dormant catalog; no activation here |
| `PROJECT_KANBAN.md`, `PROJECT_SPEC.md`, `memory/` | Supervisor-only |

---

## Test Plan

`bash tests/test_tech_lead_pack.sh` (new, with a mutation control) and `bash tests/test_pack_catalog.sh` (regression). Paste both outputs into the report.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into the report
- [ ] Supervisor notified: task ready for Stage 4 review
