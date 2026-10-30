# PACK.md — Tech Lead
**Pack**: `tech-lead`
**Domain**: Top project documents — C4 and architecture overview, sequence and journey diagrams, ER diagram, risk register, roadmap
**Core framework version tested**: 1.18+

---

## When to use this pack

Select when a project needs the documents a tech lead, project manager or new reviewer asks for first, and the project does not have them. The core agents write code and the Supervisor keeps `PRD.md`, `PROJECT_SPEC.md` and `PROJECT_KANBAN.md`. This pack adds one role that owns the architecture-level documents, and decides with the user which of them the project needs.

**Select this pack when your project involves:**
- More than one deployable part, or more than one external system (a C4 diagram helps)
- Core features that cross several parts of the system (sequence and journey diagrams help)
- A database or structured data with relations (an ER diagram helps)
- A reviewer, new team member or stakeholder who needs a one-page view
- An existing repo with no architecture documents

**Do NOT select if:** the project is a single script or a small one-part tool. `PROJECT_SPEC.md` already covers it.

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `tech-lead` | Agent | Writes a document map the user approves, then drafts and refreshes only the approved documents |
| `architecture-docs` | Skill | The map template, plus one section per document type: when needed, required content, Mermaid skeleton, watched paths |

**Boundary from core agents:**
- The Supervisor keeps `PRD.md`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, ADRs and the glossary. `tech-lead` reads them and never edits them.
- `tech-lead` owns everything under `docs/architecture/`.
- Implementers own code. `tech-lead` writes no code.
- For documents the kit already has (ADR, PRD, PROJECT_SPEC, glossary, epics and stories, security review), `tech-lead` links to the file. It writes no second copy.

---

## Agents installed

### `tech-lead`
**File**: `packs/tech-lead/agents/tech-lead.md`
Writes `docs/architecture/README.md` (the document map) first. It writes no other document until the user approves the map. Every document it drafts ends with a `Sources` list, and marks statements that no file backs with `(inferred)`.

---

## Skills installed

### `architecture-docs`
**File**: `packs/tech-lead/skills/architecture-docs/SKILL.md`
The map template (document, needed or not, reason, file, watched paths) and one section for each document type: C4 + overview, sequence, journey, ER, risk register, roadmap.

---

## User guide

### 1. Activate the pack

Every project ships this pack inactive in `packs/`. No CLI loads it until it is activated. Activation copies two paths into the kit folders, after you approve (ADR-0002). Ask your Supervisor to do it, or run, from the project root:

```sh
cp packs/tech-lead/agents/tech-lead.md agents/tech-lead.md
cp -r packs/tech-lead/skills/architecture-docs skills/architecture-docs
```

Do not overwrite an existing `agents/tech-lead.md` or `skills/architecture-docs`: stop and rename instead. The `select-packs` skill (task T117) will do this copy for you.

### 2. When the Supervisor spawns `tech-lead`

| Trigger | When | Result |
|---|---|---|
| Stage 2 | New project, after `PROJECT_SPEC.md` is locked | The map from `PRD.md` and `PROJECT_SPEC.md`; documents after you approve |
| On demand | Existing repo; you ask for it | The map from the code, with cited files and `(inferred)` marks; documents after you approve |
| Refresh | After a merge whose changed files match a watched path in the approved map | Only the matched documents change; no match means no change |

When `docs/claude-md/pipeline-stages.md` names `tech-lead`, the Supervisor spawns it at Stage 2 and at refresh on its own. Otherwise, ask for it by hand.

### 3. What lands in `docs/architecture/`

| File | Content |
|---|---|
| `README.md` | The document map: each document marked needed or not needed with a reason, links to existing kit documents, watched paths |
| `c4-overview.md` | Overview, C4 context and container diagrams |
| `sequence-<feature>.md` | One sequence diagram per core feature |
| `journey-<feature>.md` | One journey diagram per core feature |
| `er-diagram.md` | Entities and relations (only if the project stores data) |
| `risk-register.md` | Risks with area, likelihood, impact, owner, status, mitigation |
| `roadmap.md` | Milestones as a Mermaid `gantt` or `timeline` |

All diagrams are Mermaid code blocks in Markdown. You need no rendering tool. Algorithm diagrams are not part of this pack yet.

### 4. The approval step

1. The agent writes `README.md` only.
2. You read the map, change any "needed" or "not needed" mark, and edit the watched paths.
3. You tell the Supervisor the map is approved. The Supervisor fills the map's `Approved by:` line (your name and the date) and commits it, so every later refresh sees the approval. The agent then drafts the needed documents.
4. In `[auto]` mode the agent stops after step 1 and the final report lists the map for your approval.

### 5. Example spawn

```
Agent({ subagent_type: "tech-lead", prompt: "T0xx: on demand — write the document map for this repo from the code. Map only; wait for approval." })
```

After approval:

```
Agent({ subagent_type: "tech-lead", prompt: "T0xx: the map in docs/architecture/README.md is approved. Draft the documents it marks needed." })
```

### 6. Rules the agent follows

- Map first. No other document before you approve it.
- It never edits `PRD.md`, `PROJECT_SPEC.md` or `PROJECT_KANBAN.md`.
- It never overwrites a file in `docs/architecture/` that the map does not list.
- Every document ends with `Sources`. Unbacked statements carry `(inferred)`.
- A refresh changes only the documents whose watched paths matched, and only the affected section.
