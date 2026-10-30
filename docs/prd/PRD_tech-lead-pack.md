# PRD — Tech-Lead Pack (top-level project documents)
**Last updated**: 2026-10-30
**Status**: In Review (Stage 0.5a done — grilling decisions D1–D7; brainstorming next)
**Owner**: quannhm1604@gmail.com

> **Scope of this document**: *What* to build and *why*. Architecture and task state go to the
> spec/board files at Stage 2.
> Source: chat 2026-10-30 + Stage 0.5 `grill-with-docs mode=requirement`. Each FR cites the decision it came from.

---

## Overview

A project's top-level documents — the ones a tech lead, project manager or BA would ask for first —
are mostly absent from kit projects today. The kit covers some of them (`PRD.md`, `PROJECT_SPEC.md`,
`templates/ADR_template.md`, `memory/glossary.md`, `to-issues` for epics/stories, `security-review` /
`blast-radius`), but nothing owns C4, sequence, ER, journey or algorithm diagrams, a roadmap /
timeline, or a technical risk register, and nothing decides which of these a given project needs.

User request (2026-10-30, verbatim): "should we create another child in the family that contain the
thinking of technical lead, project manager, or anyone in the top level which can identify the top
documents of project" — with a pasted list from a colleague: C4 diagram, ADR, high-level
architecture, algorithm diagram, sequence diagram, ER diagram, business flow (journey diagram) for
the core features, terms dictionary, timeline/roadmap, epics and user stories ("fairly detailed, do
later"), BA diagrams and spec documents, technical risks, security — "and many more".

## Grilling decisions

| ID | Question | Decision (user) |
|----|----------|-----------------|
| D1 | New family member (MCP, e.g. easy-*) or kit content? | **Kit content.** The tech-lead thinking is judgment, which lives in agents/skills, not an MCP server. Detecting which documents exist is a separate, later easy-verifier extension. (Supervisor recommendation, user moved on to "agent vs pack" without objection.) |
| D2 | Agent or pack? | **Agent, shipped in a pack.** A `tech-lead` agent (role + judgment) plus per-document skills, packaged as `packs/tech-lead` — optional, the base team (Common-Infrastructure, Backend, Frontend, QA) is unchanged. User: "techlead should be agents, not the packs, right?" → confirmed the pack is the box the agent ships in. |
| D3 | Project-manager work (roadmap, timeline)? | **Same agent at first.** One `tech-lead` agent; split out a PM agent later only if needed. |
| D4 | Which documents are in v1? | **C4 + high-level architecture; sequence + journey diagrams for core features; ER diagram; risk register + roadmap.** Existing kit documents (ADR, PRD, PROJECT_SPEC, glossary, to-issues epics/stories, security-review) are linked, not rebuilt. Algorithm diagrams are deferred. |
| D5 | How does the agent pick the documents a project needs? | **Document map, user approves.** The agent first writes one index listing each document type as needed / not needed with a one-line reason, linking existing kit documents. It writes documents only after the user approves the map. |
| D6 | When does the Supervisor spawn it? | **Stage 2 + on demand + refresh.** New project: Stage 2, after `PROJECT_SPEC.md`. Existing repo: on demand, drafting from the code. After a merge that changes architecture or the data model, the Supervisor re-runs it to update the affected documents. |
| D7 | Where and in what format? | **`docs/architecture/`, Markdown with Mermaid diagrams.** No rendering tool. |

## Personas

| ID | Name | Pain point |
|----|------|-----------|
| P1 | Tech lead / reviewer joining a kit project | No one-page view of the architecture, flows, data model or risks |
| P2 | Kit user starting a project | Does not know which top documents this project needs, or how to keep them current |
| P3 | Supervisor | Plans with `PRD.md`/`PROJECT_SPEC.md` only; no diagrams or risk register to check work against |

## Functional requirements

- **FR-001** (D2) `packs/tech-lead/` follows the existing pack layout: `PACK.md`, `agents/tech-lead.md`, `skills/<name>/SKILL.md`; it ships in the dormant Pack catalog (ADR-0002) and is activated by copying its files into `agents/`/`skills/` after user approval (by hand until `select-packs`, T117, exists). `setup.sh` has no `--pack` option.
- **FR-002** (D2, D3) The `tech-lead` agent owns the top documents only. The Supervisor keeps `PRD.md`, `PROJECT_SPEC.md` and `PROJECT_KANBAN.md`; the agent reads them and never edits them.
- **FR-003** (D4) The pack can produce: a C4 context + container diagram with a short high-level architecture overview; one sequence diagram and one journey (business-flow) diagram per core feature; an ER diagram; a technical risk register (risk, area incl. security, likelihood, impact, owner, status, mitigation); a roadmap/timeline of milestones.
- **FR-004** (D4) For document types the kit already has (ADR, PRD, PROJECT_SPEC, glossary, epics/stories, security review), the agent links to the existing file and never writes a second copy.
- **FR-005** (D5) The agent's first output is a document map `docs/architecture/README.md`: every FR-003/FR-004 document type, marked needed / not needed with a one-line reason, plus links. It writes no other document until the user approves the map. The user can edit the map; the approved map is what later refreshes check against.
- **FR-006** (D5) In `[auto]` mode the agent writes the map only, and the final report lists it for approval; no document is written without approval. (Supervisor default — same pattern as settings-setup FR-006.)
- **FR-007** (D6) Triggers: (a) Stage 2 of a new project, after `PROJECT_SPEC.md` is locked; (b) on demand for an existing repo, drafting from the code (cited file paths), with anything inferred marked as inferred; (c) refresh after a merge that changes the architecture or data model — the agent updates only the documents the map says the change affects.
- **FR-008** (D7) Documents live in `docs/architecture/` as Markdown; diagrams are Mermaid code blocks (`C4Context`/`C4Container`, `sequenceDiagram`, `journey`, `erDiagram`, `gantt` or `timeline`).
- **FR-009** (D2) `AGENTS.md` and `docs/claude-md/pipeline-stages.md` gain only a pointer: when the pack is installed, the Supervisor spawns `tech-lead` at the FR-007 triggers.

## Non-functional requirements

- **NFR-001** No new runtime dependency: diagrams are text in the repo (format per D7), no rendering tool required.
- **NFR-002** Simplicity: the base team and `AGENTS.md` pipeline are unchanged except a pointer where the pack hooks in.

## Out of scope

- A new MCP / family member (D1).
- easy-verifier detection of these document roles (D1) — separate task in `easy-verifier-mcp`.
- A separate project-manager agent (D3).
- Algorithm diagrams (D4) — deferred.
- Rewriting ADRs, glossary, PRD/SPEC or epics/stories (FR-004).

## Open questions

None open for the user. Brainstorming decides: how the refresh trigger (FR-007c) detects "changes the architecture or data model"; whether each document type is its own skill or one skill with sections; how the agent marks inferred content when drafting from code.
