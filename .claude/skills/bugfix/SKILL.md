---
name: bugfix
description: Triage and drive a bug fix end-to-end — use when the user reports a defect, regression, or unexpected behaviour, or when a sub-agent surfaces a broken/failing condition during Stage 3. Runs the full Supervisor orchestration loop: intake → orient → TASK_GUIDE → diagnose → review → integrate.
---

## Role: Bug Fix Orchestrator

Triage incoming defects and orient the investigation so the team shares one verified mental model before any code is touched — because a wrong overview produces a wrong fix with no way back.

### Karpathy Operational Commands
- **Ask vs. Guess**: Never fill an unknown field with a guess. If the symptom, expected behaviour, or context is ambiguous, ask. One question at a time — do not batch a wall of questions.
- **Think Before Coding**: The mental model statement in Step 2 must be confirmed by the user before the TASK_GUIDE is written. An unconfirmed model is a liability, not a starting point.
- **Surgical Changes**: The fix touches only the code path the diagnosis implicates. No opportunistic cleanup.

---

### Step 1 — Surface intake

Collect the minimum signal needed to begin investigation. Ask for any item that is missing or vague:

| Field | What to ask |
|---|---|
| Symptom | What is the observed behaviour? What did you expect instead? |
| Trigger | What are the exact steps or inputs that cause it? |
| Severity | P0 (down / data loss), P1 (blocking), P2 (degraded / workaround exists) |

Do not ask about affected files or root cause yet — that is the job of Step 2.

Completion criterion: symptom (observed vs expected) is concrete and unambiguous; trigger is specific enough to attempt reproduction; severity is set.

---

### Step 2 — Orient: build and confirm the mental model

**This step is a hard gate. Do not write the TASK_GUIDE until the user confirms the mental model.**

A wrong mental model at this point produces a wrong fix with no way back. Invest time here.

#### 2a — Investigate context

Before forming any theory, read the relevant code and history:

- Read the files or modules the symptom points to.
- Run `git log --oneline -10 -- <affected paths>` — check for recent changes that could have introduced the regression.
- Check `memory/decisions.md` and `memory/learnings.md` for prior decisions or known gotchas in this area.
- Ask the user: "When did this last work correctly?" and "Has anything changed recently in this area (deploy, config, dependency update)?"

#### 2b — Define "correct"

Ask the user explicitly: **"What does correct behaviour look like — what should happen instead?"**

Do not proceed until the expected behaviour is described precisely. A vague "it should work" is not sufficient — push for a concrete, testable definition.

#### 2c — State the mental model

Write a short mental model statement (3–5 sentences) covering:
1. What the affected code path is supposed to do
2. What it is doing instead
3. The most likely area where the divergence occurs (based on code reading, not guessing)
4. What "fixed" means in concrete, verifiable terms

Then ask the user: **"Does this match your understanding? Correct anything that's wrong before I continue."**

**Do not proceed to Step 3 until the user explicitly confirms or corrects the model.**

Completion criterion: mental model statement written and shown to user; user has confirmed it or corrections have been incorporated and re-confirmed; "correct behaviour" is testable.

---

### Step 3 — Create TASK_GUIDE

Generate `tasks/TASK_GUIDE_Txxx.md` using this bug-specific structure:

```
## Bug Fix Task Guide — T[NNN]

### Mental Model (confirmed by user)
- Observed: <what is happening>
- Expected: <what should happen — testable definition>
- Likely divergence point: <area identified in Step 2c>
- Recent context: <relevant git changes or decisions found in Step 2a>

### Intake
- Trigger: <exact steps / inputs>
- Severity: <P0 / P1 / P2>
- Affected area: <files / endpoints / feature — from Step 2 investigation>

### Complexity & Risk
- Complexity: <C0–C3> (floor C1 for any bug touching >1 file)
- Risk: <Low / Medium / High> (P0 floors at Medium)

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [ ] Phase 1 feedback loop built and running
- [ ] Bug reproduces deterministically on the loop
- [ ] 3–5 ranked falsifiable hypotheses listed (consistent with confirmed mental model)
- [ ] Correct hypothesis identified via Phase 4 instrumentation

### Fix Gates (Pillar 2)
- [ ] Regression test written before the fix (or no-seam documented)
- [ ] Fix applied; regression test passes
- [ ] Phase 1 loop no longer reproduces the bug
- [ ] Fix matches the "correct behaviour" definition from the mental model

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

Add the row to `PROJECT_KANBAN.md`.

Completion criterion: TASK_GUIDE exists on disk with the confirmed mental model in the header; Complexity/Risk/Priority assigned; KANBAN row added.

---

### Step 4 — Spawn sub-agent with diagnose wired in

Tell the user the exact command to spawn the sub-agent in a worktree. Set model by Complexity (C0→haiku, C1→sonnet, C2→sonnet, C3→opus).

Spawn prompt must include:
1. Pointer to `tasks/TASK_GUIDE_Txxx.md`
2. The confirmed mental model verbatim (so the sub-agent starts oriented, not blank)
3. Instruction to invoke `Skill({ skill: "diagnose" })` as the first action
4. Full contents of `memory/MEMORY.md` verbatim (hot-tier injection)
5. Pointer to the relevant agent guide in `.claude/agents/`

The sub-agent must not write any fix code before all Diagnosis Gates in the TASK_GUIDE are checked. If the sub-agent's diagnosis contradicts the confirmed mental model, it must stop and report back to the Supervisor before continuing.

Completion criterion: spawn command given with all five prompt elements; mental model is in the prompt, not just the TASK_GUIDE pointer.

---

### Step 5 — Review gate (Stage 4)

When the sub-agent marks the task Ready for Review:

1. `Skill({ skill: "code-review" })` — always
2. `Skill({ skill: "security-review" })` — if Risk is Medium or High
3. Confirm the fix matches the "correct behaviour" definition from the mental model — not just that tests pass
4. Verify the Evidence table has repro loop, regression test, and smoke suite rows filled with real output

A task with blank evidence rows or a fix that diverges from the confirmed mental model is **not** review-complete.

Completion criterion: code-review findings addressed; fix verified against mental model definition; Evidence table fully populated; no P0/P1 findings open.

---

### Step 6 — Integrate

Run `Skill({ skill: "verify" })`, confirm the original symptom no longer reproduces, update KANBAN to Done, trigger the diff-driven memory pass (see CLAUDE.md Stage 5).

If the post-mortem in the TASK_GUIDE identifies a systemic issue (missing test seam, tangled callers, wrong abstraction), flag it to the user as a follow-up task — do not silently discard it.

Completion criterion: verify passes; original symptom is gone; KANBAN updated; memory diff-pass run; systemic findings flagged if present.

---

### Communication Protocol
- **Default Notification**: "bugfix complete for [Task ID]. Root cause: [hypothesis]. Mental model confirmed by: [user, on date]. Regression test: [added / no-seam noted]. Severity: [P0/P1/P2]. KANBAN updated."
