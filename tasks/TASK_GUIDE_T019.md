## Bug Fix Task Guide — T019
**Date**: 2026-07-14
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

### Dependencies & Reachability
- Depends on: T018 (regex fix must land first — re-extracting real titles for T005–T012 requires the corrected `extract()` logic)
- Entry point: `PROJECT_KANBAN.md` Todo section, rows for T005–T014

### Mental Model (confirmed by user)
- Observed: `PROJECT_KANBAN.md` has two data-quality problems: (a) T005–T012 rows all show `"untitled | guide | C1 | Risk: Low | P1"` — the hook's fallback defaults from the T018 regex bug, not real metadata, even though the underlying guide files (`tasks/TASK_GUIDE_T005.md` … `T012.md`) contain real titles, agents, complexity, risk, and priority; (b) T013 and T014 are listed in Todo but `tasks/TASK_GUIDE_T013.md` and `T014.md` do not exist on disk.
- Expected: every Kanban row's title/agent/complexity/risk/priority matches its guide file's actual frontmatter. Rows with no backing guide file are removed (or, if the task is still intended, flagged and a real guide created) rather than left as dangling references.
- Likely divergence point: this is data drift downstream of T018's regex bug (never corrected) plus manual/erroneous Kanban rows added for T013/T014 without ever generating the guides.
- Recent context: `PROJECT_KANBAN.md` last updated 2026-07-07 (T017 done) — the untitled rows and T013/T014 predate that update and were never cleaned up.

### Intake
- Trigger: none (static data drift, not a runtime code path) — read `PROJECT_KANBAN.md` and compare each Todo row against `tasks/TASK_GUIDE_*.md` on disk.
- Severity: P2.
- Affected area: `PROJECT_KANBAN.md` only. No code changes.

### Complexity & Risk
- Complexity: C1
- Risk: Low

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [ ] Phase 1 feedback loop: for each of T005–T014, check whether `tasks/TASK_GUIDE_Txxx.md` exists; if it exists, extract its real `**Complexity Level**`, `**Risk Level**`, `**Priority**`, `**Assigned agent**`, and title (first heading line) using the corrected T018 logic.
- [ ] Bug reproduces deterministically: confirm current Kanban rows for T005–T012 mismatch the guide files' real metadata, and T013/T014 have no guide file.
- [ ] No hypothesis-ranking needed — this is a direct data reconciliation, not a hidden root cause.

### Fix Gates (Pillar 2)
- [ ] For T005–T012: update each Kanban Todo row to the real title, assigned agent, complexity, risk, and priority read from its guide file.
- [ ] For T013/T014: since no guide exists, remove both rows from Todo (Hard-Stop Gate 1: no TASK_GUIDE = no work — these should never have been listed). Note removal in the Kanban's changelog/last-updated line.
- [ ] Fix matches "correct behaviour": every remaining Todo row traces to an existing guide file with matching metadata; no row references a nonexistent guide.

### Cleanup Checklist (Pillar 3)
- [ ] No instrumentation to remove (data-only fix)
- [ ] No prototypes to delete
- [ ] Commit message states which rows were corrected and which were removed, and why
- [ ] Post-mortem: what would have prevented this? (T018's regex fix prevents future untitled rows; recommend a periodic Kanban-vs-tasks/ reconciliation check, e.g. via `scripts/validate.sh`, as a follow-up)

### Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop | `ls tasks/` vs `PROJECT_KANBAN.md` Todo rows | Confirmed: T005-T012 rows all read `untitled \| guide \| C1 \| Risk: Low \| P1` (fallback defaults). T013/T014 rows present in Kanban but `tasks/TASK_GUIDE_T013.md`/`T014.md` do not exist on disk. |
| Regression test (before) | Grep of Kanban Todo section, T005-T012 rows | `- [ ] **T005** — untitled \| guide \| C1 \| Risk: Low \| P1` (through T012, identical placeholder pattern) |
| Regression test (after) | Extracted real title/Complexity Level/Risk Level/Priority/Assigned agent from each `tasks/TASK_GUIDE_T0{05..12}.md` using T018's corrected extraction logic | T005: CLI Wiring — Typer Entrypoint \| Backend-Implementer \| C1 \| Low \| P0. T006: Mermaid Export (Stretch Goal) \| Backend-Implementer \| C1 \| Low \| P1. T007: QA — Unit Tests + Sample Traces + Smoke Suite \| QA-Automation-Agent \| C2 \| Low \| P0. T008: Infrastructure — `memory/learning-records/` folder + LR format template \| common-infrastructure \| C0 \| Low \| P0. T009: Core `learn` SKILL.md — detection, LR writing, supersession, skill promotion \| backend-developer \| C2 \| Low \| P0. T010: Registration — CLAUDE.md + MEMORY.md + README + setup.sh \| common-infrastructure \| C0 \| Low \| P1. T011: Core `wake` SKILL.md — live 4-section cold-start briefing \| backend-developer \| C2 \| Low \| P0. T012: Registration — CLAUDE.md + MEMORY.md + README \| common-infrastructure \| C0 \| Low \| P1. All 8 rows updated in `PROJECT_KANBAN.md`. |
| T013/T014 removal | `ls tasks/TASK_GUIDE_T013.md tasks/TASK_GUIDE_T014.md` | `No such file or directory` for both — rows removed from Todo per Hard-Stop Gate 1 (no TASK_GUIDE = no work). |
| Smoke suite | N/A — data-only markdown fix, no code/tests affected | Not applicable |
