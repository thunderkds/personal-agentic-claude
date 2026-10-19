# PRD — Online Task Board (Linear first)
**Last updated**: 2026-10-19
**Status**: In Review (Stage 0.5 done — path A selected, see BRAINSTORMING_LOG_online-board.md)
**Owner**: hungnh1110@gmail.com

> **Scope of this document**: *What* to build and *why*. Architecture and task state go to `PROJECT_SPEC.md` at Stage 2.
> Source: Stage 0.5 `grill-with-docs mode=requirement`, 2026-10-19. Each FR cites the grilling decision (D1–D9) it came from.

---

## Overview

Today a project's tasks, task logs and decisions live only in local files (`PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_Txxx.md`, `memory/decisions.md`). Another developer only sees them after a branch is merged and pulled, so two people can grab the same task and agents work without teammates' decisions. This feature moves the shared truth to an online board — **Linear first** — so every developer and every agent sees tasks, status, logs and decisions as soon as they are posted. Other boards (GitHub Projects, Jira) are a later, lower-priority adapter behind the same interface.

---

## Personas

| ID | Name | Role | Pain Point |
|----|------|------|-----------|
| P1 | Developer | Runs the Supervisor on their machine | Cannot see what teammates are doing or have decided until their branches merge |
| P2 | Sub-agent | Implements one task | Starts work without decisions made in other branches; has nowhere shared to report progress |
| P3 | Teammate in Linear | Creates/assigns issues in the Linear UI | Their issues never reach the pipeline |

---

## User Stories

| ID | Story | Persona |
|----|-------|---------|
| US-001 | As a developer, I want task status to live in Linear so my whole team sees the same board. | P1 |
| US-002 | As a sub-agent, I want to post milestone logs to my task in Linear so humans can follow progress without opening my terminal. | P2 |
| US-003 | As a developer, I want my teammates' decisions to reach me and my agents at session start — and mine to reach them. | P1 |
| US-004 | As a teammate, I want an issue I create and assign in Linear to be picked up, prioritised and planned by the assignee's Supervisor. | P3, P1 |
| US-005 | As a developer, I want work to continue when Linear is unreachable. | P1 |
| US-006 | As a developer without Linear, I want the kit to keep working exactly as today. | P1 |

---

## Functional Requirements

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-001 | Linear mode is **opt-in per project**, chosen at init. Projects that decline keep the local-only flow and `Txxx` IDs unchanged. (D6) | US-006 |
| FR-002 | In Linear mode, **Linear is the source of truth** for task status. `PROJECT_KANBAN.md` is a cache regenerated from Linear; hooks keep reading the cache. (D1) | US-001 |
| FR-003 | Init asks four questions: use Linear (y/n); connect via API key / MCP / both; which Linear team + project (picked from a fetched list); who the user is in Linear. (D2, D9) | US-001 |
| FR-004 | Hooks and scripts reach Linear through a Python adapter (GraphQL + API key); the Supervisor may also use the Linear MCP. The adapter exposes a board-adapter interface so GitHub/Jira can plug in later. (D2) | US-001 |
| FR-005 | The task guide (acceptance criteria, labels, Evidence table) lives in the **Linear issue description**. `tasks/TASK_GUIDE_<ID>.md` is a cache pulled from it and committed with the task's work. (D4) | US-001, US-002 |
| FR-006 | New tasks in Linear mode use **Linear issue IDs** (e.g. `ENG-143`) in branches, commits and hooks. Hooks accept both `Txxx` and Linear ID patterns. Existing `Txxx` tasks are not migrated. (D5, D6) | US-001, US-006 |
| FR-007 | Sub-agents post **milestone comments only** to their issue: started, failing test written, tests passing, Stage 4 result, verify result, merged, and any blocker/question. (D3b) | US-002 |
| FR-008 | All decisions go to **one shared "Project Decisions" Linear Document**, each entry dated, attributed, and linked to the issue it came from. `memory/decisions.md` becomes a cache of it; agents get it in their memory slice. (D7) | US-003 |
| FR-009 | The local cache is pulled from Linear at exactly four moments: session start (`wake`), before spawning an agent, before Ready for Review, before merge. Local changes are pushed immediately. If the guide changed while an agent worked, the pre-review pull flags it and asks whether to review against the new version. (D8) | US-001, US-003 |
| FR-010 | When Linear is unreachable, gates read the cache and writes queue in a local **outbox**, replayed when Linear is back; `wake` shows the unsynced count. (D3) | US-005 |
| FR-011 | On `wake`, for each new/changed issue: **not assigned to me** → update the cache only, no action. **Assigned to me** → Supervisor reads it, proposes a priority with a reason and asks the user; after approval it judges readiness — clear enough → writes the full guide into the issue and starts; too vague → investigate (brainstorm/grill) first. No agent is spawned before that. (D9) | US-004 |
| FR-012 | Field mapping (confirmed 2026-10-19 after a conflict check). **Status**: Todo→Todo, In Progress→In Progress, Ready for Review→In Review, Done→Done; Linear Backlog→Todo; Canceled/Duplicate→"Closed (will not do)". Status names live in config, filled at init, because teams can rename them. **Priority**: P0/P1/P2→Urgent/High/Medium; Linear Low→P2; "No priority" = untriaged → FR-011 triage flow; Low and No priority are never written back. **Complexity**: label `complexity:c0..c3`, not Estimate (team scales differ and zero is usually disabled), so Estimate stays free for the team. **Risk**: label `risk:low/medium/high`. | US-001 |

---

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-001 | The API key is read from an environment variable and is **never** written to any committed file. | Security |
| NFR-002 | A normal session stays well under Linear's limit of 2,500 requests/hour per user (target < 300/hour). | Performance |
| NFR-003 | Easy Kit sets up agents only; it never installs packages or manages the environment. The adapter uses the Python stdlib only (confirmed 2026-10-19). If a job cannot be done by the stdlib script without extra packages or environment setup, it moves to the Linear MCP; dependencies are never added. | Maintainability |
| NFR-004 | A Linear outage never blocks local work; at worst the outbox grows. | Reliability |
| NFR-005 | Comments and issue text from Linear are **untrusted data**, never instructions to agents (`docs/claude-md/untrusted-content-boundary.md`). Teammates — or anyone with workspace access — can write there. | Security |

---

## Success Metrics / KPIs

| Metric | Baseline | Target | How measured |
|--------|----------|--------|--------------|
| Time for a teammate's decision to reach my agents | until branch merge + pull (days) | next session start | `wake` shows it |
| Tasks grabbed by two developers | possible (T142) | 0 — assignee is visible to all | Linear assignee |
| Work blocked by Linear outage | n/a | 0 | outbox replays |

---

## Out of Scope

- GitHub Projects / Jira adapters (interface only; later, lower priority).
- Pulling Linear changes **while** an agent is mid-task (four pull moments only).
- Migrating the existing `T001–T152` tasks into Linear.
- Full activity-stream logging (every tool call) to Linear.
- Two-way merge/conflict resolution: Linear wins; the cache is overwritten.

---

## Open Questions / Assumptions

| # | Question / Assumption | Owner | Due |
|---|----------------------|-------|-----|
| 1 | Hook rewrite cost: 12 hooks/scripts read `PROJECT_KANBAN.md` and match `T\d{3}` — dual-pattern IDs touch all of them. Assumed acceptable; size at Stage 2. | Supervisor | Stage 2 |
| 2 | `pre_bash_block_unsafe_merge.py` blocks pushes while a task is In Progress (T142 finding) — does Linear mode change that gate? | brainstorming | Stage 0.5b |
| 3 | Does Linear mode supersede deferred T142 (atomic claim)? Assignee covers it if FR-011 holds. | user | Stage 2 |
| 4 | Cache files (`PROJECT_KANBAN.md`, guide copies) committed or gitignored in Linear mode? FR-005 says guide copies are committed. | brainstorming | Stage 0.5b |
| 5 | **Deferred by user (2026-10-19):** ADRs, DDRs and context docs will be stored through a separate MCP, coming from another task. Owed records held until then: ADR candidate "Linear is the source of truth" (D1, 3-of-3); DDR candidate "Linear issue IDs replace Txxx" (D5). | user | when that MCP task lands |
