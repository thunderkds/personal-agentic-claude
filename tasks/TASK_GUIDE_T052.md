# TASK_GUIDE — T052: Stuck-Loop Escalation checkpoint in diagnose + Attempts Log
**Date**: 2026-08-04
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Complexity is **C1** — 2 files, known pattern (skill-instruction edit, same shape as prior
   `general-agent-template.md`/`diagnose`/`bugfix` amendments), no new component

---

## Requirement (Pillar 1 — Adapt the requirement)

User (2026-08-04, via `/brainstorming` then `/grill-with-docs`, approved): in bugfix/diagnosis
sessions, the agent currently tries hypothesis after hypothesis with no stopping point — "this way,
that way, another way" — a long flow with no options ever surfaced to the user, and no warning
occurs. Need a checkpoint that stops the agent after repeated failed attempts and forces it to
present explicit options, with the record captured in the plan (TASK_GUIDE) for evaluation.

**Restated intent**: Add a **Stuck-Loop Escalation checkpoint** to the `diagnose` skill: after 2
consecutive disproven hypotheses (Phase 4 instrumentation contradicts the prediction), STOP before
testing hypothesis 3 — present 3 explicit options (try next hypothesis / widen scope-reconsider the
mental model / abandon and escalate to the Supervisor) and do not proceed until one is chosen. Add
a new `### Attempts Log` section to `bugfix`'s TASK_GUIDE-generation template (Step 3) so the
tested hypotheses, their predicted vs. actual results, and the chosen escalation option are
captured in the plan, not just a chat aside.

**Out of scope**:
- No new hook, no trace-based failure detection (brainstorming explicitly rejected this — path 2,
  too heuristic/false-positive-prone against real trace data).
- No change to `pre_agent_step_limit.py` or any other existing hook.
- The checkpoint threshold (2) is a Supervisor-chosen default the user deferred on — do not
  "improve" or auto-tune it; it's a literal number in the skill text, changeable later by a human.
- Do not touch `Phase 1` (feedback loop), `Phase 2` (reproduce), `Phase 5` (fix), or `Phase 6`
  (cleanup) of `diagnose` — only Phase 3/4's hypothesis-testing loop gets the checkpoint.

**Requirement Refs**: No `PRD.md` (framework self-maintenance). Traceability: user's confirmed
request across the brainstorming/grilling dialogue + `memory/decisions.md`'s "Stuck-Loop
Escalation checkpoint in diagnose" entry.

### Requirement Fidelity Gate
- [x] Restated intent confirmed to match the user's request (brainstorming + grilling dialogue)
- [x] Domain terms align — "hypothesis", "Phase 3/4", "Attempts Log" all reuse existing
      `diagnose`/`bugfix` skill vocabulary, no new terms invented
- [ ] Every Acceptance Criterion below traces to a line in the Requirement — agent verifies before starting

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `Standalone — N/A: this changes skill instruction text read by the Supervisor/agent
at diagnose-invocation time, not called from application code.`

---

## Acceptance Criteria

| # | Criterion | Traces to |
|---|---|---|
| 1 | `.claude/skills/diagnose/SKILL.md` Phase 3 or Phase 4 gains explicit text: after 2 consecutive disproven hypotheses, STOP and present 3 named options before testing hypothesis 3 | "STOP after 2 consecutive failed hypotheses" |
| 2 | The 3 options are named explicitly in the skill text: (a) try next hypothesis, (b) widen scope / reconsider mental model, (c) abandon and escalate to Supervisor | "present 3 explicit options" |
| 3 | `.claude/skills/bugfix/SKILL.md`'s Step 3 TASK_GUIDE template gains a new `### Attempts Log` section, placed after `### Diagnosis Gates`, with a table for hypothesis/predicted/actual/verdict and a checkpoint record (options presented, option chosen, user go-ahead) | "captured in the plan... for evaluation" |
| 4 | Neither `diagnose` nor `bugfix`'s SKILL.md exceeds ~150 lines after the edit (existing project convention — `slim-skills` threshold) — if the addition would push over, keep it tight rather than verbose | Simplicity First |
| 5 | No other phases of `diagnose` (1, 2, 5, 6) are touched; no hook files touched | out-of-scope guard |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|---|---|---|
| 1 | `.claude/skills/diagnose/SKILL.md` | Contains the checkpoint text with "2" as the threshold and all 3 named options | grep for key phrases |
| 2 | `.claude/skills/bugfix/SKILL.md` | Contains `### Attempts Log` positioned after `### Diagnosis Gates` in the template block | grep + manual read |
| 3 | Both files | Line count still reasonable (~150 line convention) | `wc -l` |
| 4 | `diagnose` Phases 1/2/5/6 | Byte-identical to pre-task version | `git diff` scoped to those sections |

### Verification Command

```bash
grep -n "consecutive\|2 disproven\|widen scope\|abandon and escalate" .claude/skills/diagnose/SKILL.md
grep -n "Attempts Log" .claude/skills/bugfix/SKILL.md
wc -l .claude/skills/diagnose/SKILL.md .claude/skills/bugfix/SKILL.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes |
|-------|--------|-------|
| **New test(s) cover Acceptance Criteria** | ☐ pass / ☐ fail | docs/skill-instruction task — verification script above is the accepted oracle, no unit-test framework applies |
| Verification command run | ☐ pass / ☐ fail | paste real output |
| Negative cases hold | ☐ pass / ☐ fail | confirm Phases 1/2/5/6 of `diagnose` are untouched (git diff scoped check) |
| verify | ☐ pass / ☐ fail / ☐ N/A | Supervisor reads both skill files end-to-end, confirms the checkpoint reads naturally in Phase 3/4's flow and the Attempts Log table is usable |
| Review scope bounded to blast radius | ☐ pass / ☐ fail | `.claude/skills/diagnose/SKILL.md`, `.claude/skills/bugfix/SKILL.md` only |
| Full smoke suite still green | ☐ pass / ☐ fail | `pytest .claude/hooks/tests/` — no hook code touched, expect unchanged |
| UI rows | ☑ N/A | no UI |

---

## Approach

**Pattern reference**: `.claude/agents/general-agent-template.md`'s `## Staleness Guard` footer
(T051) — same shape of "add a short, explicit new subsection to an existing skill/template file
without restructuring the rest." Also `.claude/skills/diagnose/SKILL.md` Phase 3's own existing
line — "Show the ranked list to the user (cheap checkpoint...)" — establishes the precedent that
`diagnose` already has one lightweight checkpoint; this task adds a second, mandatory one.

**Suggested diagnose addition** (agent may adjust wording, must keep the hard "2" threshold and all
3 named options), appended to the end of Phase 4 or as a new subsection between Phase 4 and Phase 5:

```markdown
### Stuck-Loop Checkpoint (mandatory)
After Phase 4 instrumentation disproves a hypothesis (the predicted signal did not appear), track
it. If **2 consecutive hypotheses are disproven**, STOP before testing hypothesis 3 — do not
silently continue. Present exactly these 3 options and wait for a choice before proceeding:
1. Try the next ranked hypothesis (or generate new ones if the list is exhausted).
2. Widen the diagnostic scope — reconsider the mental model itself, not just the next guess.
3. Abandon this diagnosis approach and escalate to the Supervisor.
Record the two disproven hypotheses and the chosen option in the TASK_GUIDE's Attempts Log
(bugfix-flavored guides) or report them directly to the Supervisor (standalone diagnose calls with
no bugfix-shaped guide).
```

**Suggested Attempts Log addition** to `bugfix`'s Step 3 template, inserted after the existing
`### Diagnosis Gates` block and before `### Fix Gates`:

```markdown
### Attempts Log (filled live during diagnosis — required if >1 hypothesis tested)
| # | Hypothesis | Predicted signal | Actual result | Verdict |
|---|---|---|---|---|

**Stuck checkpoint** (if 2 consecutive hypotheses disproven):
- [ ] 3 options presented (next hypothesis / widen scope / abandon+escalate)
- [ ] Chosen option: ___
- [ ] User's explicit go-ahead: ___
```

---

## Edge Case Checklist

- [ ] Standalone `diagnose` invocations (not via `bugfix`, e.g. a Stage-3 sub-agent hitting a bug
      mid-task with no bugfix-shaped TASK_GUIDE) still need the checkpoint to fire — the skill text
      must say to report the attempts log to the Supervisor directly in that case, not silently
      skip the checkpoint because no TASK_GUIDE field exists to write it into
- [ ] The counter is **consecutive** disproven hypotheses, not total — if hypothesis 1 fails,
      hypothesis 2 confirms partially then gets refined and re-tested and passes, the counter
      should not have fired; state this precisely so it isn't misread as "2 total failures ever"
- [ ] Don't let this checkpoint block the *first* hypothesis test — only fires after 2 have already
      been disproven, never pre-emptively before any testing has happened

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/diagnose/SKILL.md` | Add Stuck-Loop Checkpoint subsection (Phase 3/4 area) |
| `.claude/skills/bugfix/SKILL.md` | Add `### Attempts Log` to the Step 3 TASK_GUIDE template |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_agent_step_limit.py` | Brainstorming explicitly rejected a hook-based approach (path 2) — out of scope |
| `CLAUDE.md`, `docs/claude-md/*.md` | This is skill-internal behavior, not a Hard-Stop Gate — no CLAUDE.md change needed |
| `templates/TASK_GUIDE_template.md` | The Attempts Log is bugfix-flavored only, lives in `bugfix`'s own template block, not the generic standard-task template |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not mandated (Low risk)
- [ ] Tests written AND pass — verification script output pasted into Evidence
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (new decision: Stuck-Loop Escalation checkpoint shipped)
- [ ] Supervisor notified: ready for Stage 4 review
