# PRD — [Project Name]
**Last updated**: [YYYY-MM-DD]
**Status**: Draft / In Review / Approved
**Owner**: [name or team]

> **Scope of this document**: *What* to build and *why* — product intent, user stories, requirements, success metrics.
> Technical decisions, architecture, agent config, and task state live in `PROJECT_SPEC.md`.
> If Out of Scope here conflicts with Critical Constraints there, resolve the conflict before Stage 2.

---

## Overview

[One paragraph: the problem being solved, who it affects, and the intended outcome. Written from the user's perspective, not the engineer's.]

---

## Personas

| ID | Name | Role | Pain Point |
|----|------|------|-----------|
| P1 | [name] | [role] | [what frustrates them today] |
| P2 | [name] | [role] | [what frustrates them today] |

---

## User Stories

| ID | Story | Persona |
|----|-------|---------|
| US-001 | As a [P1], I want [goal] so that [value]. | P1 |
| US-002 | As a [P2], I want [goal] so that [value]. | P2 |

---

## Functional Requirements

Each FR must trace to at least one User Story.

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-001 | [specific, testable requirement — avoid "should"; use "must"] | US-001 |
| FR-002 | [requirement] | US-001, US-002 |
| FR-003 | [requirement] | US-002 |

---

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-001 | [e.g. p95 response time < 200 ms under 1k concurrent users] | Performance |
| NFR-002 | [e.g. all PII fields encrypted at rest using AES-256] | Security |
| NFR-003 | [e.g. system must handle 10× traffic spike without config change] | Scalability |

---

## Success Metrics / KPIs

| Metric | Baseline | Target | How measured |
|--------|----------|--------|--------------|
| [metric name] | [current value] | [goal value] | [tool / query] |

---

## Out of Scope

The following are explicitly excluded from this project:

- [feature or concern that will NOT be addressed]
- [dependency or integration that is deferred]

---

## Open Questions / Assumptions

Provenance per the Ambiguity Resolution Protocol (`CLAUDE.md` Phase 0 Step 1.5):
**STATED** = user said it · **INFERRED** = supervisor guessed from a vague answer · **DEFAULT** =
filled an empty answer. INFERRED/DEFAULT items must be confirmed before they can drive a task.

| # | Question / Assumption | Source | Owner | Revisit / Due |
|---|----------------------|--------|-------|---------------|
| 1 | [unresolved decision or stated assumption] | STATED / INFERRED / DEFAULT | [name] | [trigger or YYYY-MM-DD] |
| 2 | [question] | — | [name] | [YYYY-MM-DD] |
