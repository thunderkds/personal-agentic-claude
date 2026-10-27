# TASK_GUIDE — T180: Auto mode — with the user's `[auto]` parameter, either track runs to Ready for Review without stopping and ends with a final report of every decision
**Date**: 2026-10-26
**Complexity Level**: C3
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: removes the user's stops from the extended track, the track used for risky work. The stops that stay (merge, `/verify`, safety hooks, the Debate cap) are the guardrails of the task.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if needed
3. Read this file completely, then `tasks/TASK_GUIDE_T178.md` and `tasks/TASK_GUIDE_T179.md`
4. Read `agents/common-infrastructure.md`
5. Read `memory/codebase-map.md` (C3) and `docs/claude-md/pipeline-stages.md` — list every place where the extended track waits for the user today
6. Read `skills/delivery-report/SKILL.md` and `templates/TASK_REVIEW_template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-26: "I want to automate 2 of tracks also, with track 2 I will give the param to automate, and note the decision for the final report." Supervisor's reply, accepted ("yes, write the 3 task guides"): the run ends at Ready for Review on its branch; merge and `/verify` stay with the user (Claude Code lets only the user run `/verify`); the Supervisor runs its own real-run check, labelled "auto-checked, not /verify"; safety hooks still block; Debates are capped at 3 per task. User, 2026-10-27: "I want to make the /verify command is automate also" — chose "Hook runs real /verify": that is T182 (a hook, not the Supervisor, runs the built-in `/verify` in a fresh session). This task leaves the `verify` row unfilled for it.

**Restated intent**:
> When the user's request carries the auto parameter, the Supervisor runs the chosen track to the end
> without asking anything: every decision it would have asked about is made by a rule, a Citation or a
> Debate (T179), and written to a **final report** in the task's review file. The user then reads the report,
> checks the decisions marked for review, reads the `/verify` result (run by T182's hook, or runs `/verify`
> itself when T182 is not built or its run was blocked), and decides on the merge.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **The parameter.** The literal tag `[auto]` anywhere in the request, e.g. `move the data from CSV to JSON [auto]`. A bracketed tag, so a request about an "auto-save" feature never turns auto mode on. The Supervisor confirms in the track line: `Track: extended · auto — <reasons>. I won't stop for questions; every decision goes in the final report.` Without `[auto]`, both tracks behave as in T178. The task records that it runs in auto mode in a form a hook can read (e.g. a `Mode: auto` line in its review file or Decision record) — T182's hook keys on it.
- D2 — **Auto mode on the minimal track.** The one remaining stop (an unclear request) becomes a Debate (T179); the Decision record (T178) gets the same flags as D4 below.
- D3 — **Auto mode on the extended track.** Every user stop the agent listed in startup step 5 gets an auto rule, for example:
  - Stage 0.5 brainstorming → the Supervisor takes its recommended path and logs the alternatives.
  - grill-with-docs → answered from the docs and code with Citations; what they cannot answer is a Choice question → Debate.
  - Requirement Fidelity Gate → signed `auto (Supervisor)`, not by the user.
  - A Stage 4 finding whose fix needs a choice → Debate.
  - Stage 5 → the Supervisor's real-run check, written in the review file as `auto-checked, not /verify`; the `verify` Evidence row stays unchecked: T182's hook fills it from a real `/verify` run, or the user does.
- D4 — **Final report.** A `## Auto decisions` section in `tasks/TASK_REVIEW_Txxx.md` (extended) or inside the Decision record (minimal). One numbered line per decision: what was decided; how (`RULE: …`, `FACT: <Citation>`, `DEBATED: <who argued what>`, `SAFER OPTION`); and `⚠ decided for you — please review` on every Debate, safer-option and taste decision. Then `Checks:` (tests, reviews, real run) and `Not done: merge (yours)` plus the `/verify` state: `auto verify: running (T182)`, its result, or `/verify (yours)` when T182 is not built or its run was blocked. The same block is the Supervisor's final chat message.
- D5 — **Stops that stay in auto mode:** a safety-hook block; an action that deletes or overwrites data with no backup; the 4th Debate in a task (T179 D6); a paid action outside the task's own work; a login or secret the Supervisor does not have; the same sub-agent hitting the step limit twice. Each pauses the task with one message that says why, and that pause also goes in the final report.
- D6 — **Never in auto mode:** merge, push, the Supervisor running `/verify` or writing its row (only T182's hook writes it), moving a task to Done, or changing the track down.

**Out of scope**: the tracks and the Decision record (T178); the Debate step (T179); running `/verify` automatically (T182); a CI or scheduled trigger for auto mode.

**Requirement Refs**: none in `PRD.md`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-26; user: "yes, write the 3 task guides")
- [ ] Domain terms: add **Auto mode** and **Final report** to the `PROJECT_SPEC.md` glossary (agent). "Final report" is not the `delivery-report` HTML page.
- [x] Every AC traces to the Requirement
- [x] Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: T178 — the tracks, the track line and the Decision record; T179 — the Debate step in `resolve-question`
**Entry point**: `[auto]`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `docs/claude-md/tracks.md` has an `## Auto mode` section: the D1 tag and track-line example, D2, the D3 rule for **every** user stop the agent listed (the list is in the section, one row per stop), the D5 stops that stay and the D6 never-list. `AGENTS.md` gets ≤4 lines with a pointer and stays ≤32,768 bytes. **Line cap (T178 Stage 4):** the real cap is 196 lines (`.claude/hooks/tests/test_vital_slice.py`, "do not raise the cap"), and T178 left AGENTS.md at exactly 196. Either fit the pointer into the existing `## Tracks` paragraph (no new line), or tighten other lines without dropping a rule, or stop and ask the user to approve a higher cap. | D1–D3, D5, D6 |
| 2 | `templates/TASK_REVIEW_template.md` has an optional `## Auto decisions` section in the D4 shape; T178's `templates/MINIMAL_LOG_template.md` gains the same lines. | D4 |
| 3 | `skills/resolve-question/SKILL.md` and the stages in `docs/claude-md/pipeline-stages.md` that stop for the user each name their auto-mode rule or point to the `## Auto mode` table. **Size limit (T179 Stage 4):** the skill is 8189 of the 8192 bytes Codex accepts (`tests/test_resolve_question.py::test_t179_ac6_skill_stays_under_the_codex_skill_body_cap`; over it, `tests/test_site_content.py` fails and Codex skips the skill). Make room by tightening existing text, without dropping a rule, before adding the pointer. While there, fix the two T179 P2s: (a) step 1's `Done when:` still says every Choice question part goes to the user — add the auto-mode exception and put the routing line before `Done when:`; (b) say how the Debate cap is counted (the `DEBATE` lines under the guide's `## Questions Log`) and what "per task" means for `task=none` (per session). | D3 |
| 4 | The merge gate (`pre_bash_block_unsafe_merge.py`) still blocks a merge whose `verify` row says only `auto-checked, not /verify`: a test proves it. (T182 adds the one auto case the gate accepts: a hook-written row with its record.) | D3, D6 |
| 5 | Tests (`tests/test_auto_mode.py`) pin AC 1–4: the literal `[auto]`, that a bare "auto" word is not the tag, the stop list, the never-list, the D4 flag text. The full suite stays green. | Gate 5 |
| 6 | Live check, **after the user's go, paid, cap $6**: 2 headless runs of the updated kit in the T175 Docker sandbox, single turn, no scripted replies: (a) fixture task 5 `[auto]` → `Track: extended · auto`, no stop, ends Ready for Review on a branch, data safe by the task-5 oracle, `## Auto decisions` present with the `recurring.csv` decision flagged; (b) fixture task 4 `[auto]` → minimal track, the vague sort settled by a Debate and flagged in the Decision record. | user request |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | request with `[auto]` | track line says `· auto` | test (text) + run |
| 2 | request "add auto-save" without the tag | normal mode | test |
| 3 | `verify` row = `auto-checked, not /verify` | merge still blocked | test (hook) |
| 4 | task 5 `[auto]` (paid) | 1 turn, no stop, safe, flagged decision | run |
| 5 | task 4 `[auto]` (paid) | Debate, flagged record | run |

### Verification Command

```bash
python3 -m pytest -q tests/test_auto_mode.py tests/test_tracks.py tests/test_resolve_question.py tests/test_agents_md_primary.py && python3 -m pytest -q tests
```

### Evidence

> **Moved.** Filled in `tasks/TASK_REVIEW_T180.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T180.md`.

---

## Approach

**Pattern reference**: T174's Update auto modes (`lib/harness-update.sh`: `UPDATE_MODE`, `update_decided_by`, `render_update_log_entry`) — the same idea in the installer: a mode chosen once, every decision recorded with who decided it; `experiments/kit-arms/run_arms.py` for the live check.
**Vital slice**: the `## Auto mode` table covering every stop (AC 1), the final report shape (AC 2), the merge gate still holding (AC 4).
**Cut list**: auto mode without the tag (e.g. a project-wide setting); auto merge; a separate HTML page for the final report.

---

## Edge Case Checklist

- [ ] `[auto]` given for a request that also says "ask me before X" → the explicit "ask me" wins for X; everything else is auto.
- [ ] Auto mode on a minimal-track task that moves up mid-task → it stays in auto mode on the extended track, and the report says when it moved.
- [ ] A sub-agent reports `Status: blocked` with a Choice question → Debate (T179), not the user.
- [ ] The session is near its usage limit → stop at a clean point, write the final report so far, and say what is left.
- [ ] Two `[auto]` tasks in one session → each has its own report and its own Debate count.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `docs/claude-md/tracks.md` | `## Auto mode` |
| `AGENTS.md` | ≤4-line pointer |
| `docs/claude-md/pipeline-stages.md` | auto rules at each user stop |
| `templates/TASK_REVIEW_template.md`, `templates/MINIMAL_LOG_template.md` | `## Auto decisions` |
| `skills/resolve-question/SKILL.md` | where auto mode comes from (pointer only; the Debate itself is T179) |
| `PROJECT_SPEC.md` | glossary |
| `tests/test_auto_mode.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | the merge gate must not get weaker; test it, do not change it (if it must change, stop and report) |
| `experiments/kit-arms/` | frozen experiment (used read-only for AC 6) |

---

## Completion Checklist

- [ ] Build + tests (agent)
- [ ] Stage 4: code-review, security-review (High risk)
- [ ] User go → AC 6 paid live check (Supervisor)
- [ ] `verify` (user-only)
- [ ] Merge only when the user asks

---

## Questions Log
