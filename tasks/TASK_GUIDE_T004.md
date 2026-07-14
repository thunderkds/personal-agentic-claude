# TASK_GUIDE — T004: .gitignore + Repo Hygiene
**Date**: 2026-06-10
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any content:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Create `.gitignore` appropriate for a shell-script deployment repo. Ensure no project-specific files can be accidentally committed to this repo.

**Restated intent**:
> The repo stays clean — only general framework files are ever committed. A `git status` in this repo never shows project-specific noise.

**Out of scope**:
- Language-specific ignores (no Node, Python, etc. — this is a shell repo)

**Requirement Refs**:
- FR-014: `.gitignore` appropriate for a shell-script deployment repo
- NFR-002: No project-specific files ever committed to the supervisor repo

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed
- [x] All Acceptance Criteria trace to requirements

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `.gitignore` ignores `tasks/`, `memory/`, `PRD.md`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md` | NFR-002 |
| 2 | `.gitignore` ignores common OS/editor noise: `.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/`, `*.swp` | FR-014 |
| 3 | `git status` in this repo shows clean after adding the `.gitignore` (no untracked noise files) | FR-014 |
| 4 | `setup.sh`, `update.sh`, `MANIFEST`, `README.md`, `CLAUDE.md`, `CLAUDE_LEGACY.md`, `.claude/`, `templates/` are NOT ignored | FR-014 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Create `tasks/test.md` and `PRD.md` in repo root | `git status` does not show them | Manual test |
| 2 | `setup.sh` exists | `git status` shows it as tracked | Manual check |

### Verification Command

```bash
touch tasks/test.md PRD.md .DS_Store
git status
# Expect: none of the above appear in untracked files
rm tasks/test.md PRD.md .DS_Store
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

Simple `.gitignore` with three sections:
1. Project-specific files (must never be in this repo)
2. OS/editor noise
3. Shell script artifacts (e.g. test temp dirs)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.gitignore` | Create new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| All other files | T004 is hygiene-only |

---

## Completion Checklist

- [ ] Implementation done
- [ ] `git status` clean after adding `.gitignore`
- [ ] Supervisor notified: T004 ready for Stage 4 review
