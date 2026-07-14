# TASK_GUIDE — T003: README.md
**Date**: 2026-06-10
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any content:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read the completed `setup.sh` and `update.sh` (T001, T002) before writing docs — README must reflect actual behavior

---

## Requirement (Pillar 1 — Adapt the requirement)

Write the `README.md` for this repo — the primary onboarding document for any developer wanting to use the supervisor framework across projects.

**Restated intent**:
> A developer landing on this repo can understand what it is, install it in a new project in one command, and know how to update, customize, and extend it — without needing to read any other file.

**Out of scope**:
- Internal implementation details (script internals go in code comments, not README)
- Per-project task guides or PRD documentation

**Requirement Refs**:
- FR-012: `curl | bash` one-liner install command
- FR-013: Document install, update, add skills globally, override skills per project, git-submodule alternative

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] All Acceptance Criteria trace to requirements
- [x] All Requirement Refs covered

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | README contains a `curl \| bash` one-liner (with placeholder URL noted as "fill in when repo is public") | FR-012 |
| 2 | README has an Installation section covering: prerequisites, one-liner, greenfield vs brownfield choice | FR-013 |
| 3 | README has an Update section: how to run `update.sh`, what it reports | FR-013 |
| 4 | README has an "Add a skill globally" section: edit the skill in `~/.supervisor/.claude/skills/`, commit, update | FR-013 |
| 5 | README has an "Override per project" section: documents the `--copy` flag and manual file replacement pattern | FR-013 |
| 6 | README has an optional "Git Submodule Alternative" section | FR-013 |
| 7 | README documents `SUPERVISOR_PATH` env var | FR-001 |
| 8 | README is scannable — uses headers, code blocks, and a quick-start section at the top | Usability |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | A developer unfamiliar with the project reads README | They can install, update, and override without asking questions | Manual review |
| 2 | README's install command is copy-pasteable | Command works when repo is public | Manual check |

### Verification Command

```bash
# Render and review locally
cat README.md | head -80
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill | ☐ pass / ☐ fail | |
| Review scope bounded | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

Structure:
1. **Title + one-line description**
2. **What this repo is** (2–3 sentences — general supervisor framework, not project-specific)
3. **Quick Start** (one-liner install)
4. **Installation** (step-by-step, greenfield vs brownfield, prerequisites)
5. **Update** (`update.sh` usage)
6. **Add a Skill Globally** (edit central clone, commit, pull)
7. **Override per Project** (`--copy` flag, then edit the local copy)
8. **Environment Variables** (`SUPERVISOR_PATH`)
9. **Git Submodule Alternative** (optional section)
10. **What Gets Deployed** (table matching MANIFEST)

Note: one-liner URL is a placeholder — mark clearly: `# Replace with your repo's raw URL`.

---

## Edge Case Checklist

- [ ] One-liner command must work with both `curl` and `wget` (provide both variants)
- [ ] Note that `--copy` files won't auto-update — user must re-run `setup.sh --copy` or manually merge

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `README.md` | Replace existing content |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh` | Already implemented in T001/T002 |
| `MANIFEST` | Data file |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: all 8 Acceptance Criteria checked
- [ ] Supervisor notified: T003 ready for Stage 4 review
