# PROJECT_SPEC.md
**Last updated**: [YYYY-MM-DD]
**Version**: 1.0

> **Scope of this document**: *How* to build it safely — architecture, agent config, constraints, risk areas, task state, and accumulated learnings.
> Product intent (personas, user stories, FR/NFR, success metrics) lives in `PRD.md`.
> If Critical Constraints here conflict with Out of Scope in `PRD.md`, resolve before Stage 2.

---

## Project Identity

- **Name**: [project name]
- **Repo**: [repo URL or local path]
- **Primary tech**: [language / framework]
- **Type**: [web app / API / CLI / mobile / etc.]
- **Deployment target**: [prod URL or environment]
- **Key stakeholders**: [names / teams]

---

## Architecture Summary

[2–3 sentences describing the high-level architecture. Expand in docs/ if needed.]

---

## Critical Constraints

[Copy the most important do-not-touch rules here for agent reference. Examples:]
- Never modify `[file/module]` without Supervisor approval
- Auth layer is owned by [team] — no changes without sign-off
- DB schema changes require Liquibase migrations only

---

## Known Risk Areas

| Area | Risk Level | Reason | Files |
|------|-----------|--------|-------|
| [feature/module] | High / Med / Low | [why it's fragile] | [file paths] |

---

## Assumptions & Deferred Decisions

Choices the supervisor made for the user (vague answer) or the user deferred (`"you decide"`), per
the Ambiguity Resolution Protocol. Each is **reversible** until confirmed — revisit before it
hardens into architecture.

| # | Assumption / Deferred decision | Source | Rationale | Revisit by |
|---|--------------------------------|--------|-----------|-----------|
| 1 | [what was assumed] | INFERRED / DEFAULT | [one-line why] | [trigger or date] |

---

## Architecture Decision Records

Index of `docs/adr/NNNN-title.md` — recorded only for hard-to-reverse, surprising trade-offs.

| ADR | Title | Status | Related Tasks |
|-----|-------|--------|---------------|
| [0001](docs/adr/0001-title.md) | [decision] | Accepted | [Txxx] |

---

## Sub-Agent Team

| Agent | Role | CLI Spawn Command |
|---|---|---|
| Common-Infrastructure-Agent | Env setup, worktrees, migrations | `Agent({ subagent_type: "common-infrastructure", prompt: "..." })` |
| Backend-Implementer | Server-side implementation | `Agent({ subagent_type: "backend-developer", prompt: "..." })` |
| Frontend-Implementer | UI implementation | `Agent({ subagent_type: "frontend-developer", prompt: "..." })` |
| QA-Automation-Agent | Tests and smoke validation | `Agent({ subagent_type: "qa-expert", prompt: "..." })` |

---

## Tasks

| ID | Title | Status | Assigned Agent | Complexity | Risk | Priority |
|----|-------|--------|---------------|-----------|------|----------|
| T001 | [title] | Todo / In Progress / Review / Done | [agent] | C0–C3 | Low / Med / High | P0–P2 |

---

## Memory / Insights

Running log of key decisions, patterns, and lessons learned across tasks.

| Date | Insight | Source Task |
|------|---------|------------|
| [YYYY-MM-DD] | [decision or pattern] | T[NNN] |
