# TASK_GUIDE — T008: Infrastructure — `memory/learning-records/` folder + LR format template
**Date**: 2026-06-19
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Apply C0 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Create the storage infrastructure for the Learning Record (LR) system:
1. A `memory/learning-records/` folder tracked by git (via `.gitkeep`).
2. A canonical format spec at `templates/LEARNING-RECORD-FORMAT.md` — the single source of truth for how an LR file is structured (slots, required/optional fields, status values, naming convention).

**Restated intent**: Before the `learn` skill (T009) can write any LR files, the folder must exist and the LR file format must be defined in the project's `templates/` directory so both the skill and future agents have an unambiguous reference.

**Out of scope**:
- Writing any actual LR files (that's done by the `learn` skill at runtime)
- Modifying `CLAUDE.md` or `MEMORY.md` (that's T010)
- Implementing the `learn` skill itself (that's T009)

**Requirement Refs**:
- Brainstorming decision 2026-06-19: `memory/learning-records/` as fourth cold-tier storage
- Brainstorming decision 2026-06-19: sequential `LR-NNNN-slug.md` naming with status/evidence/implications fields

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `BRAINSTORMING_LOG.md` and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `memory/learning-records/.gitkeep` exists and the folder is tracked by git | Folder creation requirement |
| 2 | `templates/LEARNING-RECORD-FORMAT.md` exists with all required slots documented | Format spec requirement |
| 3 | The format spec defines: `name/slug`, `date`, `type` (project\|user), `insight`, `status` (active\|superseded by LR-NNNN), `evidence`, `implications` | LR field requirements from brainstorming |
| 4 | The format spec includes the naming convention: `LR-NNNN-kebab-slug.md` | Naming convention requirement |
| 5 | The format spec includes a filled example LR and a minimal blank template | Usability requirement |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `ls memory/learning-records/` | `.gitkeep` present, folder tracked | manual / `git status` |
| 2 | `cat templates/LEARNING-RECORD-FORMAT.md` | All 7 fields documented, example present | manual review |
| 3 | A new LR file written following the format | Passes a mental "does this slot exist?" check against the spec | manual |

### Verification Command

```bash
ls memory/learning-records/.gitkeep && grep -c "LR-" templates/LEARNING-RECORD-FORMAT.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | N/A — file system artifact |
| Review scope bounded to `memory/` + `templates/` only | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |

---

## Approach

1. Create `memory/learning-records/` with a `.gitkeep` file.
2. Write `templates/LEARNING-RECORD-FORMAT.md` using this canonical structure:

**Required frontmatter fields:**
```
---
name: LR-NNNN-kebab-slug        # e.g. LR-0001-supervisor-fires-learn-on-corrections
date: YYYY-MM-DD
type: project | user             # project = domain/pattern/gotcha; user = preference/knowledge/style
status: active | superseded by LR-NNNN
---
```

**Required body sections:**
- `## Insight` — 1–3 sentences: the non-obvious thing learned
- `## Evidence` — how it was observed (user correction, pattern seen twice, explicit statement)
- `## Implications` — what this unlocks or restricts in future sessions

**Optional sections:**
- `## Supersedes` — link to the older LR(s) this replaces (if status = superseded)

Include one complete filled example (`LR-0001-example-slug.md`) and one blank template stub in the file.

---

## Edge Case Checklist

- [ ] `memory/learning-records/` already exists on re-run — script/agent must not error; `.gitkeep` is idempotent
- [ ] `templates/LEARNING-RECORD-FORMAT.md` already exists from a previous attempt — overwrite only if content changed
- [ ] Naming convention must be unambiguous: `LR-0001` (zero-padded 4 digits) not `LR-1` — document this explicitly in the format spec

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `memory/learning-records/.gitkeep` | Create (new folder) |
| `templates/LEARNING-RECORD-FORMAT.md` | Create (new format spec) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/MEMORY.md` | Registration step belongs to T010 |
| `CLAUDE.md` | Registration step belongs to T010 |
| `memory/learnings.md` | Existing cold tier — T008 adds a new tier, doesn't modify the old one |
| `setup.sh` | setup.sh update belongs to T010 |

---

## Test Plan

- `git status` shows `memory/learning-records/.gitkeep` as a new tracked file
- `cat templates/LEARNING-RECORD-FORMAT.md` shows all required fields, naming convention, example, and blank template
- Manual: mentally "fill out" an LR using only the spec — confirm no ambiguity in any field

---

## Completion Checklist

- [ ] `memory/learning-records/.gitkeep` created
- [ ] `templates/LEARNING-RECORD-FORMAT.md` created with all 7 fields, naming convention, example, and blank template
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T008 ready for Stage 4 review
