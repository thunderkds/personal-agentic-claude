# PROJECT_KANBAN.md
**Last updated**: 2026-07-21

> Compact task board. Full context lives in `PROJECT_SPEC.md`. Update this file whenever a task status changes.

---

## Board

### Todo
- [ ] **T039** — Dedup the `## Skills vs Agents` section in CLAUDE.md | Common-Infrastructure-Agent | C2 | Risk: Medium | P1
- [ ] **T040** — Derive the Token Audit Log from event-trace instead of manual entry; restart the DDR-0001 window | Common-Infrastructure-Agent | C1 | Risk: Medium | P1
- [ ] **T041** — Make engineering principles reachable by sub-agents + add the Search-Before-You-Build ladder | Common-Infrastructure-Agent | C2 | Risk: Medium | P1
- [ ] **T030** — Post-baseline analysis — pick the token refactor from real data (blocked: T028 window must close — 7 sessions/14 days, DDR-0001) | Supervisor + user (HITL) | C1 | Risk: Low | P1

### In Progress

### Ready for Review

### Done
- [x] **T042** — Fix post_write_register_task.py Complexity/Risk/Priority extraction — regexes never matched the template's own `**X Level**:` format, so every auto-registered row silently defaulted to C1/Low/P1; defaults now `?`; 4th regex defect in this hook family. Stage 4: 0 P0/P1, 1 P2 fixed, 3 P3 accepted. security-review unrunnable (built-in hardcodes `origin/HEAD`, remote is `github`) — done manually, no findings | C1 | Completed: 2026-07-21
- [x] **T038** — Fix setup.sh piped `curl \| sh` install — primary documented install command was completely broken since T031 (2 days, undetected until a real user hit it); verified against the real live pushed repo | C2 | Completed: 2026-07-19
- [x] **T037** — Fix CI shellcheck SC1091 — missing `-x` flag meant shellcheck refused to follow the already-correctly-annotated lib/harness-fetch.sh source, failing CI on an info-level finding | C0 | Completed: 2026-07-19
- [x] **T036** — Fix scripts/smoke-install.sh for direct-repo model — CI was broken (red) since T031-T033 landed, never caught until this review; 1 P1 code-review fix (vacuous assertion) | C1 | Completed: 2026-07-19
- [x] **T029** — Prune 4 oversized SKILL.md files: learn 182→128, map-codebase 165→130 pruned; bugfix + code-review skipped at safe floor. Recovered from a stale branch after the original prune was lost to a failed /compact | C1 | Completed: 2026-07-19
- [x] **T034** — QA — independent smoke suite for install/update (9/9 pass, incl. negative-control sabotage self-check on update.sh's conflict detection) | C1 | Completed: 2026-07-19
- [x] **T035** — README.md — install/update sections rewritten for direct-repo model (2 stale-doc gaps found beyond original scope: pack ~/.supervisor no-longer-auto-created, obsolete git-submodule note removed) | C0 | Completed: 2026-07-19
- [x] **T026** — Fix TASK_GUIDE_template.md example verify Evidence row (2 compounding gate bugs found + fixed) | C0 | Completed: 2026-07-19
- [x] **T024** — Fix post_write_register_task.py agent-field regex | C0 | Completed: 2026-07-19
- [x] **T012** — Registration — CLAUDE.md + MEMORY.md + README | C0 | Completed: 2026-07-19 (audit-confirmed: skills deploy via MANIFEST's blanket `.claude/skills` line, documented in CLAUDE.md/README.md/MEMORY.md — no separate registration work remained)
- [x] **T011** — Core `wake` SKILL.md — live 4-section cold-start briefing | C2 | Completed: 2026-07-19 (audit-confirmed: `.claude/skills/wake/SKILL.md` exists, mandatory-invoked every session per CLAUDE.md)
- [x] **T010** — Registration — CLAUDE.md + MEMORY.md + README + setup.sh | C0 | Completed: 2026-07-19 (audit-confirmed, same basis as T012)
- [x] **T009** — Core `learn` SKILL.md — detection, LR writing, supersession, skill promotion | C2 | Completed: 2026-07-19 (audit-confirmed: `.claude/skills/learn/SKILL.md` exists, actively used — LR-0001/LR-0002 on disk)
- [x] **T008** — Infrastructure — `memory/learning-records/` folder + LR format template | C0 | Completed: 2026-07-19 (audit-confirmed: folder exists with LR-0001, LR-0002)
- [x] **T007** — QA — Unit Tests + Sample Traces + Smoke Suite | C2 | Completed: 2026-07-19 (closed per user confirmation — original Typer-CLI-project scope, superseded when repo pivoted to the Supervisor framework; no code ever existed to test)
- [x] **T006** — Mermaid Export (Stretch Goal) | C1 | Completed: 2026-07-19 (closed per user confirmation — same superseded original scope as T005/T007)
- [x] **T005** — CLI Wiring — Typer Entrypoint | C1 | Completed: 2026-07-19 (closed per user confirmation — no Typer/Python CLI code ever existed in this repo; original scope superseded by the Supervisor framework direction)
- [x] **T028** — Token Audit Log — scaffold + entry convention + format test (DDR-0001) | C1 | Completed: 2026-07-19
- [x] **T033** — New update.sh — hash-lock compare, per-file conflict prompt, symlink-refusal, git-repo check (ADR-0001) | C2 | Completed: 2026-07-17
- [x] **T032** — Rewrite setup.sh — direct-copy install, git-repo prerequisite check, write .claude/harness-lock.json (ADR-0001) | C2 | Completed: 2026-07-17
- [x] **T031** — lib/harness-fetch.sh — shared temp-clone-copy-discard + MANIFEST parsing (ADR-0001) | C2 | Completed: 2026-07-17
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
