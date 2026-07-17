# PROJECT_KANBAN.md
**Last updated**: 2026-07-17

> Compact task board. Full context lives in `PROJECT_SPEC.md`. Update this file whenever a task status changes.

---

## Board

### Todo
- [ ] **T035** — README.md — update install/update instructions for direct-repo model (ADR-0001, depends on T033) | backend-developer | C0 | Risk: Low | P1
- [ ] **T034** — QA — smoke tests: fresh install, untouched-update, conflict-prompt, non-git-dir rejection (ADR-0001, depends on T032/T033) | qa-expert | C1 | Risk: Low | P0
- [ ] **T033** — New update.sh — hash-lock compare, per-file conflict prompt, symlink-refusal, git-repo check (ADR-0001, depends on T031/T032) | backend-developer | C2 | Risk: Medium | P0
- [ ] **T032** — Rewrite setup.sh — direct-copy install, git-repo prerequisite check, write .claude/harness-lock.json (ADR-0001, depends on T031) | backend-developer | C2 | Risk: Medium | P0
- [ ] **T031** — lib/harness-fetch.sh — shared temp-clone-copy-discard + MANIFEST parsing (ADR-0001) | backend-developer | C2 | Risk: Medium | P0
- [ ] **T030** — Post-baseline analysis — pick the token refactor from real data (blocked: T028 window must close — 7 sessions/14 days, DDR-0001) | Supervisor + user (HITL) | C1 | Risk: Low | P1
- [ ] **T029** — Prune the 4 oversized SKILL.md files via /slim-skills (HITL, approval-gated) | Supervisor + user (HITL) | C1 | Risk: Low | P1
- [ ] **T028** — Token Audit Log — scaffold + entry convention + format test (DDR-0001) | backend-developer | C1 | Risk: Low | P0
- [ ] **T026** — Fix TASK_GUIDE_template.md example `verify` Evidence row to match pre_bash_block_unsafe_merge.py's gate regex | backend-developer | C0 | Risk: Low | P1
- [ ] **T024** — Fix post_write_register_task.py agent-field regex (matches "Agent guide" before "Assigned agent") | backend-developer | C0 | Risk: Low | P2
- [ ] **T012** — Registration — CLAUDE.md + MEMORY.md + README | common-infrastructure | C0 | Risk: Low | P1
- [ ] **T011** — Core `wake` SKILL.md — live 4-section cold-start briefing | backend-developer | C2 | Risk: Low | P0
- [ ] **T010** — Registration — CLAUDE.md + MEMORY.md + README + setup.sh | common-infrastructure | C0 | Risk: Low | P1
- [ ] **T009** — Core `learn` SKILL.md — detection, LR writing, supersession, skill promotion | backend-developer | C2 | Risk: Low | P0
- [ ] **T008** — Infrastructure — `memory/learning-records/` folder + LR format template | common-infrastructure | C0 | Risk: Low | P0
- [ ] **T007** — QA — Unit Tests + Sample Traces + Smoke Suite | QA-Automation-Agent | C2 | Risk: Low | P0
- [ ] **T006** — Mermaid Export (Stretch Goal) | Backend-Implementer | C1 | Risk: Low | P1
- [ ] **T005** — CLI Wiring — Typer Entrypoint | Backend-Implementer | C1 | Risk: Low | P0
- [ ] **T003** — README.md | backend-developer | C0 | Risk: Low | P1
- [ ] **T004** — .gitignore + repo hygiene | backend-developer | C0 | Risk: Low | P2

### In Progress

### Ready for Review

### Done
- [x] **T027** — DDR (Design Decision Record) — default decision artifact, ADR as rare escalation | C1 | Completed: 2026-07-16
- [x] **T025** — craft-agent skill (optional, supplemental agent-drafting) + Stage 1.5 wiring | C2 | Completed: 2026-07-16
- [x] **T001** — setup.sh + MANIFEST | C1 | Completed: 2026-06-10
- [x] **T002** — update.sh | C1 | Completed: 2026-06-10
- [x] **T003** — README.md | C0 | Completed: 2026-06-10
- [x] **T004** — .gitignore + repo hygiene | C0 | Completed: 2026-06-10
- [x] **T015** — ui-test skill (easy-ui-mcp orchestration) | C1 | Completed: 2026-07-01
- [x] **T016** — Wire ui-test into pipeline (qa.md + CLAUDE.md) | C1 | Completed: 2026-07-01
- [x] **T021** — Clean dangling T013/T014 prose references in cold memory | C0 | Completed: 2026-07-14
- [x] **T022** — Harden pre_agent_validate_guide.py task-ID extraction | C2 | Completed: 2026-07-14
- [x] **T023** — craft-spawn-prompt skill + wire Stage 3 / bugfix to it | C2 | Completed: 2026-07-14
- [x] **T017** — Task dependency declaration & entry-point reachability check | C1 | Completed: 2026-07-07
- [x] **T018** — Fix title-extraction regex in post_write_register_task.py | C1 | Completed: 2026-07-14
- [x] **T019** — Reconcile PROJECT_KANBAN.md rows (T005-T012 metadata, remove T013/T014) | C1 | Completed: 2026-07-14
- [x] **T020** — Update .gitignore for live-instance tracked files | C1 | Completed: 2026-07-14

---

## Blocked

| Task | Reason | Waiting on |
|------|--------|-----------|

---

## Stage Tracker

| Stage | Status |
|-------|--------|
| 0.5 Brainstorming | ✅ Done |
| 1 Environment Setup | ✅ Done |
| 1.5 Sub-Agent Architecture | ✅ Done |
| 2 Planning (/plan) | ✅ Done |
| 3 Execution | ✅ Done |
| 4 Review | ✅ Done |
| 5 Integration & Verify | ✅ Done |
