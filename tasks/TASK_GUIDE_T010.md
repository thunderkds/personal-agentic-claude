# TASK_GUIDE — T010: Registration — CLAUDE.md + MEMORY.md + README + setup.sh
**Date**: 2026-06-19
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Read `setup.sh` to understand the existing idempotent directory-creation pattern before editing
6. Apply C0 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**Depends on**: T009 (`.claude/skills/learn/SKILL.md` must exist before it can be registered)

---

## Requirement (Pillar 1 — Adapt the requirement)

Register the `learn` skill and the `memory/learning-records/` infrastructure across all four discovery surfaces:

1. **`CLAUDE.md`** — add `learn` row to the custom skill table (same format as existing rows); add trigger description so the Supervisor knows when to auto-fire it.
2. **`memory/MEMORY.md`** — add a `### Learning Records` section header with an empty index (ready for first runtime LR entry).
3. **`README.md`** — add `learn` to the custom skills table and document the `memory/learning-records/` folder in the project structure section.
4. **`setup.sh`** — ensure `memory/learning-records/` is created (with `.gitkeep`) on fresh installs; the folder must exist before the `learn` skill can write any LR files.

**Restated intent**: After T010 merges, any user cloning the repo for the first time will have the LR folder created by `setup.sh`, will see `learn` listed in `CLAUDE.md` and `README.md`, and the Supervisor will have a `### Learning Records` index section in `MEMORY.md` ready to populate.

**Out of scope**:
- Writing the actual SKILL.md (T009)
- Writing any LR files (runtime, done by the skill)
- Changing anything in `.claude/agents/` (no new agents)

**Requirement Refs**:
- Brainstorming decision 2026-06-19: trigger = both Supervisor-auto + user `/learn`
- Brainstorming decision 2026-06-19: `memory/learning-records/` as fourth cold-tier storage
- User answer 2026-06-19: setup.sh must auto-create `memory/learning-records/` on fresh installs

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with existing CLAUDE.md skill table format
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] T009 is complete — `.claude/skills/learn/SKILL.md` exists

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `CLAUDE.md` custom skill table contains a `learn` row with: definition path `.claude/skills/learn/SKILL.md`, and trigger: "Use during or after any significant exchange where the Supervisor detects a non-obvious insight, correction, domain discovery, or pattern confirmation. Also user-invokable as `/learn`." | CLAUDE.md registration |
| 2 | `memory/MEMORY.md` contains a `### Learning Records` section with an empty index comment (ready for first LR entry) | MEMORY.md index requirement |
| 3 | `README.md` custom skills table contains a `learn` row | README registration |
| 4 | `README.md` project structure section documents `memory/learning-records/` with a one-line description | README project structure |
| 5 | `setup.sh` creates `memory/learning-records/` and writes a `.gitkeep` inside it (idempotent — no error if already exists) | setup.sh fresh-install requirement |
| 6 | Running `bash setup.sh` on a clean clone produces `memory/learning-records/.gitkeep` | setup.sh verification |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `grep "learn" CLAUDE.md` | Row present in custom skill table | grep |
| 2 | `grep "Learning Records" memory/MEMORY.md` | Section header present | grep |
| 3 | `grep "learn" README.md` | Row present in skills table | grep |
| 4 | `grep "learning-records" setup.sh` | mkdir/gitkeep logic present | grep |

### Verification Command

```bash
grep -n "learn" CLAUDE.md && \
grep -n "Learning Records" memory/MEMORY.md && \
grep -n "learn" README.md && \
grep -n "learning-records" setup.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold (setup.sh idempotent on existing folder) | ☐ pass / ☐ fail | |
| `verify` skill — n/a (file edits only) | ☐ pass / ☐ fail | N/A |
| Review scope bounded to CLAUDE.md, MEMORY.md, README.md, setup.sh only | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |

---

## Approach

### CLAUDE.md — custom skill table

Add one row to the existing table in the "Custom project skill" section, matching the format of adjacent rows exactly:

```markdown
| `learn` | `.claude/skills/learn/SKILL.md` | Use during or after any significant exchange where the Supervisor detects a non-obvious insight, user correction, domain discovery, or pattern confirmation. Also user-invokable as `/learn`. Auto-fires after a significant exchange; writes `memory/learning-records/LR-NNNN-slug.md` files. |
```

Also add the trigger rule to the Supervisor's memory write protocol section:
> The `learn` skill is the Supervisor's inline "Reflect & Encode" reflex. Fire it after any exchange that meets the materiality gate (see SKILL.md). Do not fire it on every message.

### memory/MEMORY.md — new section

Insert after the last `### Decisions` or `### Patterns` section:

```markdown
### Learning Records
<!-- One-liner per active LR: - [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — summary -->
<!-- Superseded LRs: ~~old text~~ → see LR-NNNN -->
```

### README.md

Add `learn` to the custom skills table. In the project structure section, add:
```
memory/learning-records/   ← sequential LR-NNNN-slug.md files (written by the learn skill at runtime)
```

### setup.sh

Find the section that creates `memory/` sub-files (e.g. where `decisions.md`, `glossary.md`, `learnings.md` are initialized). Add:

```bash
mkdir -p "$TARGET/memory/learning-records"
touch "$TARGET/memory/learning-records/.gitkeep"
```

Use the same idempotent pattern already used for other directories in setup.sh. Do not change the function signatures or flow.

---

## Edge Case Checklist

- [ ] `setup.sh` runs on a repo where `memory/learning-records/` already exists — must not fail or double-create `.gitkeep`
- [ ] CLAUDE.md table row uses exact pipe/column format as adjacent rows — misalignment breaks markdown table rendering
- [ ] `memory/MEMORY.md` already has a `### Learning Records` header from a previous partial run — must not duplicate it
- [ ] README.md skill table column order must match existing rows exactly

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | Add `learn` row to custom skill table; add trigger rule to Memory Write Protocol |
| `memory/MEMORY.md` | Add `### Learning Records` section with empty index comment |
| `README.md` | Add `learn` to custom skills table; add `memory/learning-records/` to project structure |
| `setup.sh` | Add `mkdir -p` + `.gitkeep` for `memory/learning-records/` |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/learn/SKILL.md` | Written by T009, not T010 |
| `memory/learnings.md` | Existing cold tier — not modified by registration |
| `memory/decisions.md` | Existing cold tier — not modified by registration |
| Any `.claude/agents/` files | No new agents in this task |

---

## Test Plan

- `grep "learn" CLAUDE.md` — row present
- `grep "Learning Records" memory/MEMORY.md` — section header present
- `grep "learning-records" setup.sh` — mkdir logic present
- Simulate: run `bash setup.sh` in a temp dir — `memory/learning-records/.gitkeep` created; run again — no error

---

## Completion Checklist

- [ ] `CLAUDE.md` updated with `learn` row and trigger rule
- [ ] `memory/MEMORY.md` updated with `### Learning Records` section
- [ ] `README.md` updated with `learn` row and `memory/learning-records/` in project structure
- [ ] `setup.sh` updated with idempotent `mkdir + .gitkeep` for `memory/learning-records/`
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T010 ready for Stage 4 review
