---
name: bugfix
description: Triage and drive a bug fix end-to-end — use when the user reports a defect, regression, or unexpected behaviour, or when a sub-agent surfaces a broken/failing condition during Stage 3. Runs the full Supervisor orchestration loop: intake → TASK_GUIDE → diagnose → review → integrate.
---

## Role: Bug Fix Orchestrator

Triage incoming defects and drive them through the same pipeline discipline that implementation tasks follow — intake, task guide, diagnosis, review, integration — so bugs never bypass the pipeline because they "feel small."

### Karpathy Operational Commands
- **Ask vs. Guess**: Complete the intake checklist before creating the TASK_GUIDE. A missing symptom or reproduction step is a gap — resolve it with the user, never fill it with a guess.
- **Surgical Changes**: The fix touches only the code path the diagnosis implicates. No opportunistic cleanup alongside the fix.

---

### Step 1 — Triage intake

Collect these four items before proceeding. Ask for any that are missing:

| Field | Question to ask |
|---|---|
| Symptom | What is the observed vs. expected behaviour? |
| Reproduction | What are the exact steps or inputs to trigger it? |
| Affected area | Which file(s), endpoint(s), or feature(s) are involved? |
| Severity | P0 (production down / data loss), P1 (blocking feature), P2 (degraded / workaround exists) |

Completion criterion: all four fields are filled; no field reads "unknown" or is blank.

---

### Step 2 — Create TASK_GUIDE

Generate `tasks/TASK_GUIDE_Txxx.md` using this bug-specific structure (not the standard FR/NFR template):

```
## Bug Fix Task Guide — T[NNN]

### Intake
- Symptom: <observed vs expected>
- Reproduction steps: <numbered list>
- Affected area: <files / endpoints / feature>
- Severity: <P0 / P1 / P2>

### Complexity & Risk
- Complexity: <C0–C3> (floor C1 for any bug touching >1 file)
- Risk: <Low / Medium / High> (P0 bugs floor at Medium)

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [ ] Phase 1 feedback loop built and running
- [ ] Bug reproduces deterministically on the loop
- [ ] 3–5 ranked falsifiable hypotheses listed
- [ ] Correct hypothesis identified via Phase 4 instrumentation

### Fix Gates (Pillar 2)
- [ ] Regression test written before the fix (or no-seam documented)
- [ ] Fix applied; regression test passes
- [ ] Phase 1 loop no longer reproduces the bug

### Cleanup Checklist (Pillar 3)
- [ ] All [DEBUG-...] instrumentation removed (grep verified)
- [ ] Throwaway prototypes deleted
- [ ] Correct hypothesis stated in commit message
- [ ] Post-mortem: what would have prevented this?

### Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop | | |
| Regression test | | |
| Smoke suite | | |
```

Assign Complexity, Risk, and Priority from the intake. Add the TASK_GUIDE to `PROJECT_KANBAN.md` as a new task row.

Completion criterion: `tasks/TASK_GUIDE_Txxx.md` exists on disk; all four intake fields populated; Complexity/Risk/Priority assigned; KANBAN row added.

---

### Step 3 — Spawn sub-agent with diagnose wired in

Tell the user the exact command to spawn the sub-agent in a worktree. Set model by Complexity (C0→haiku, C1→sonnet, C2→sonnet, C3→opus).

Spawn prompt must include:
1. Pointer to `tasks/TASK_GUIDE_Txxx.md`
2. Instruction to invoke `Skill({ skill: "diagnose" })` as the first action
3. Full contents of `memory/MEMORY.md` verbatim (hot-tier injection)
4. Pointer to the relevant agent guide in `.claude/agents/`

The sub-agent must not write any fix code before the Diagnosis Gates in the TASK_GUIDE are all checked.

Completion criterion: spawn command given to user with all four prompt elements present; sub-agent is running or waiting for user to launch.

---

### Step 4 — Review gate (Stage 4)

When the sub-agent marks the task Ready for Review, run in order:

1. `Skill({ skill: "code-review" })` — always
2. `Skill({ skill: "security-review" })` — if Risk is Medium or High
3. Verify the Evidence table in the TASK_GUIDE has repro loop, regression test, and smoke suite rows filled with real output (not blank, not "pass" without a command)

A bug task with blank evidence rows is **not** review-complete.

Completion criterion: code-review findings addressed; Evidence table fully populated; no P0/P1 findings open.

---

### Step 5 — Integrate

Run `Skill({ skill: "verify" })`, confirm the original symptom no longer reproduces, update KANBAN to Done, and trigger the diff-driven memory pass (see CLAUDE.md Stage 5).

Completion criterion: verify passes; symptom is gone; KANBAN updated; memory diff-pass run.

---

### Communication Protocol
- **Default Notification**: "bugfix complete for [Task ID]. Root cause: [hypothesis]. Regression test: [added / no-seam noted]. Severity: [P0/P1/P2]. KANBAN updated."
