# PROJECT_KANBAN.md
**Last updated**: [YYYY-MM-DD]

> Compact task board. Full context lives in `PROJECT_SPEC.md`. Update this file whenever a task status changes.

---

## Board

> Task line format: **Txxx** — [title] | [agent] | C[0–3] | Risk: Low/Med/High | P[0–2]

### Todo
- [ ] **T001** — [short title] | [agent] | C2 | Risk: Low/Med/High | P1

### In Progress
- [ ] **T002** — [short title] | [agent] | C2 | Risk: Low/Med/High | P1 | Started: [date]

### Ready for Review
- [ ] **T003** — [short title] | [agent] | C2 | PR/branch: [branch name]

### Done
- [x] **T000** — [short title] | C1 | Completed: [date]

---

## Blocked

| Task | Reason | Waiting on |
|------|--------|-----------|
| T[NNN] | [blocker description] | [person / dependency] |

---

## Stage Tracker

| Stage | Status |
|-------|--------|
| 0.5 Brainstorming | ✅ Done / 🔄 In Progress / ⬜ Not Started |
| 1 Environment Setup | ✅ Done / 🔄 In Progress / ⬜ Not Started |
| 1.5 Sub-Agent Architecture | ✅ Done / 🔄 In Progress / ⬜ Not Started |
| 2 Planning (/plan) | ✅ Done / 🔄 In Progress / ⬜ Not Started |
| 3 Execution | ✅ Done / 🔄 In Progress / ⬜ Not Started |
| 4 Review | ✅ Done / 🔄 In Progress / ⬜ Not Started |
| 5 Integration & Verify | ✅ Done / 🔄 In Progress / ⬜ Not Started |
