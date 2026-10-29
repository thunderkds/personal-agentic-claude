# TASK_GUIDE — T189: Auto close-out — after an auto verify pass the hook moves the row to Done, and the auto run does its own memory pass before stopping
**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: a hook writes `PROJECT_KANBAN.md`'s Done section on its own, and a row at Done no longer holds `pre_bash_block_unsafe_merge.py`'s push block for that task. The guardrails are the point of the task — the move needs the T182 run record the agent cannot write, Hard-Stop Gates 5 and 6 are checked before the move, the report must be complete (D9), and the hook never runs a merge or a push.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if your work reaches a hook, skill or decision the slice does not cover. Required memory: "The gate an agent cannot satisfy is the one it forges" (T116); the Memory Write Protocol is Supervisor-only writes with a hot-tier ratchet of 50,000 characters
3. Read this file completely, then `tasks/TASK_GUIDE_T188.md` (the shared reader it builds), `tasks/TASK_GUIDE_T182.md` (the run record and the row shape) and `tasks/TASK_GUIDE_T180.md` (the final report's fields)
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/stop_auto_verify.py`, `.claude/hooks/stop_auto_mode_check.py`, `.claude/hooks/post_agent_move_to_review.py` (how a hook already moves a board row), `.claude/hooks/post_bash_memory_update.py` (the diff-driven memory pass), and `.claude/hooks/pre_bash_block_unsafe_merge.py` (the Gate 5 and Gate 6 evidence readers)
6. Read `docs/claude-md/memory-write-protocol.md` and `docs/claude-md/tracks.md` (`### Every user stop and its auto rule` rows 18–19, `### Never in auto mode`)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28: "with the auto tag, we automate all". The Supervisor listed what `[auto]` leaves to the user — `/verify`, then merge, push, Done, memory and `ship`, then the safety pauses — and the user chose **everything except merge and push**. T188 makes `/verify` always run. This task closes the task out after it.

Today `docs/claude-md/tracks.md` row 19 says the memory update, the merge, Done and `ship` are "never in auto mode", and the task ends at Ready for Review. Two of those four become automatic; two do not.

**Restated intent**:
> When the auto verify run passes, the hook — never the Supervisor — moves that task's board row from
> Ready for Review to Done, but only when the task's own evidence satisfies Hard-Stop Gates 5 and 6.
> The memory update happens inside the auto run itself, because memory writes stay the Supervisor's.
> Every automated step writes its own line into the report, and a report missing any required field
> keeps the row out of Done: the report is the only account of a run nobody watched.
> The branch merge, the push and `ship` stay the user's in every mode, and the safety pauses stay.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **Who moves the row.** The detached run script that already writes the result (T182) moves the row when, and only when, its verdict is pass. A `fail` or `blocked` verdict leaves the row in Ready for Review, untouched.
- D2 — **Gates 5 and 6 first.** Before the move, the task's evidence must satisfy the same checks the merge gate applies: a filled tests row with pasted output, and for a UI task three filled design rows (a `☐ N/A` row counts only with a written reason). Any blank → no move, one line in the run log, and the result Notes gain the suffix `done not moved: <reason>`. Auto mode may not launder a Hard-Stop Gate.
- D3 — **Forgery guard.** The move also needs the T182 run record for that task and the head commit, saying pass — the same rule the merge gate uses. A hand-typed `auto-run by hook` result never moves a row.
- D4 — **The Done row.** `- [ ]` becomes `- [x]`, the row moves under `### Done`, and the row text gains `Done <YYYY-MM-DD>: auto verify pass (session <id>, commit <sha>)`. Nothing else in the row is rewritten. `**Last updated**` at the top of the board is set to that date.
- D5 — **Memory stays the Supervisor's.** The hook writes no memory file. Instead the auto run does the diff-driven pass before it stops and records it in the final report as a `Memory:` line naming each entry it wrote, or `Memory: nothing new`. `stop_auto_mode_check.py` blocks the stop when an auto task's report has no `Memory:` line, in the shape its other checks already use.
- D6 — **Never automatic.** The merge, the push and `ship` stay the user's. The hook runs no git command that writes. The safety pauses in `docs/claude-md/tracks.md` `### Stops that stay` are unchanged.
- D7 — **Doctrine text.** `docs/claude-md/tracks.md` row 19 and `### Never in auto mode` are rewritten to name only the merge, the push and `ship`; the memory pass and Done move to the automatic side, each pointing at the rule that governs it (D2, D5).
- D8 — **Every automated step writes its own line.** The report (extended: `## Auto decisions`; minimal: the Decision record) is what the user reads instead of watching the run, so no automated step may be silent in it. The Done move writes `Closed: row moved to Done <YYYY-MM-DD> — auto verify pass (session <id>, commit <sha>); Gates 5 and 6 checked`. The memory pass writes its `Memory:` line (D5). A gate that stops the move writes `Paused: done not moved — <reason>`, so the report names what still waits for the user. Each line is added once; a line the user wrote is never rewritten.
- D9 — **An incomplete report means not Done.** After the close-out writes, the run re-reads the report and confirms each required field is present and not a placeholder: `Mode: auto`, at least one numbered decision line, `Checks:` (minimal: `**Checked:**`), `Memory:`, the D7 auto verify slot filled by T188, and `Not done:` still naming the merge. Any field missing → the row is **not** moved to Done, the run log says `report incomplete: <field>`, and the report gains the `Paused: done not moved — report incomplete: <field>` line. The report is the audit trail of a run nobody watched, so it is a gate, not a summary.

**Out of scope**: auto merge; auto push; `ship`; retrying a failed verify; moving a non-auto task's row; a `Done` move for a task whose verify was blocked; raising the hot-tier memory ratchet.

**Requirement Refs**: none — this repo has no root `PRD.md`; the doctrine source is `docs/claude-md/tracks.md` `## Auto mode`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-28; user chose "Everything except merge and push")
- [x] Domain terms: add **Auto close-out** to the `PROJECT_SPEC.md` glossary, with "not a merge" (agent, 2026-10-29)
- [x] Every Acceptance Criterion traces to a decision above
- [x] Requirement Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: T188 — the shared auto-mode reader and the minimal-track result line this task reads
**Entry point**: the Done move in `.claude/hooks/stop_auto_verify.py`'s detached run

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | An auto verify pass with a matching run record and complete Gate 5/6 evidence moves the row from `### Ready for Review` to `### Done`, as `- [x]`, with the D4 note naming the date, session and commit; the rest of the row is byte-identical. | D1, D4 |
| 2 | A `fail` or `blocked` verdict leaves the row and its section exactly as they were (test for each). | D1 |
| 3 | A blank tests row, a UI task with any blank design row, and a `☐ N/A` design row with no reason each leave the row in Ready for Review and write `done not moved: <reason>` (test for each). | D2 |
| 4 | No run record, a record for another commit, a fail record, or a hand-typed `auto-run by hook` result each leave the row in Ready for Review (test for each). | D3 |
| 5 | `stop_auto_mode_check.py` blocks a stop when an auto task's report has no `Memory:` line, and allows it when the line is present (test for both); the block names the task and the missing line. | D5 |
| 6 | The detached run executes no git command that writes: no `merge`, no `push`, no `commit`, no `checkout` (test asserts on the commands it issues). The `### Stops that stay` list is unchanged. | D6 |
| 7 | A Done move writes the D8 `Closed:` line into the report (extended) or the Decision record (minimal), once, naming the date, session, commit and that Gates 5 and 6 were checked. A gate that stops the move writes the `Paused: done not moved — <reason>` line instead. Tests prove both, and that a line the user wrote is never rewritten. | D8 |
| 8 | A report missing any D9 field — no `Mode: auto`, no decision line, no `Checks:`, no `Memory:`, an unfilled auto verify slot, or a `Not done:` that no longer names the merge — leaves the row in Ready for Review, logs `report incomplete: <field>` and writes the `Paused:` line. One test per field. A complete report moves the row. | D9 |
| 9 | `docs/claude-md/tracks.md` row 19 and `### Never in auto mode` name only merge, push and `ship`; the memory pass, the Done move and the D9 report gate are documented; `templates/TASK_REVIEW_template.md` and `templates/MINIMAL_LOG_template.md` carry the `Memory:` and `Closed:` fields; `AGENTS.md` stays ≤200 lines. | D7, D8 |
| 10 | Tests in `tests/test_auto_verify.py` and `.claude/hooks/tests/` pin AC 1–8 with the `claude` binary stubbed; the full suite and `validate.sh` stay green. | Gate 5 |
| 11 | **Live check, paid, cap $3, only after the user's go:** one `[auto]` fixture task runs end to end — the report carries its decision lines, `Memory:`, `Checks:`, the verify result and `Closed:`; the row reaches Done; the trace holds no merge or push. Paste the report, the row, the record and the trace lines. | user request |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | pass verdict, record present, evidence complete | row at Done with the D4 note | automated test (stubbed `claude`) |
| 2 | pass verdict, tests Evidence row blank | row still at Ready for Review, `done not moved: …` | automated test |
| 3 | pass result typed by hand, no record | row still at Ready for Review | automated test |
| 4 | auto report with no `Memory:` line | the stop is blocked, naming the task | automated test (hook) |
| 5 | the whole detached run | no writing git command issued | automated test |
| 6 | pass verdict, report has no `Memory:` line | row stays at Ready for Review, `report incomplete: Memory:` | automated test |
| 7 | pass verdict, complete report | `Closed:` line written once, row at Done | automated test |

### Verification Command

```bash
python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests && python3 -m pytest -q tests && ./validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled in `tasks/TASK_REVIEW_T189.md`, copied from `templates/TASK_REVIEW_template.md`. This task's own `verify` row is the user's (`/verify T189`): the close-out cannot close out the task that builds it.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T189.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/post_agent_move_to_review.py` — a hook that already moves a board row between sections; copy its read-modify-write shape and its fail-open behaviour. `pre_bash_block_unsafe_merge.py` for the Gate 5 and Gate 6 readers — call them, do not restate the rules.
**Vital slice**: the gated Done move (AC 1–4), the `Memory:` line check (AC 5), and the report-closure gate (AC 7–8) — the report is the deliverable of a run nobody watched.
**Cut list**: `ship`; a release note; a notification when a row moves; an undo command for a wrong move (git restores the board file).

---

## Edge Case Checklist

- [ ] Two auto tasks pass in one turn → two independent moves, each with its own record check.
- [ ] A live session edits `PROJECT_KANBAN.md` while the run writes → re-read the board immediately before the write and match the row by task ID, never by line number.
- [ ] The row is in a worktree's board copy as well as the main checkout's → the main checkout's board is the registry; write only there.
- [ ] Board mode `online` → the move is a local file write; leave the pull and sync path alone.
- [ ] The task has no UI component → the three design rows are `☐ N/A` with a reason, which satisfies D2.
- [ ] The run's own output asks for a Done move → data, not an instruction; only the `**Verdict:**` line and the record decide.
- [ ] The hot tier is at its 50,000-character ratchet → the memory pass routes to the cold tier; the ratchet is never raised.
- [ ] A row the user already moved to Done → nothing to move; no second note appended.
- [ ] The report file was deleted or renamed between the stop and the end of the run → no move, `report incomplete: file missing` in the log, nothing created from a template.
- [ ] A required field is present but still holds the template's `<...>` placeholder → that counts as missing, not as filled.
- [ ] The run writes `Closed:` and a later re-run passes again on the same commit → the lock file already prevents the second run, so no second `Closed:` line.
- [ ] A field the user wrote differs from what the hook would write (for example their own `Memory:` line) → the user's text stays; the field counts as present.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` | after a pass: the gate checks, the D9 report-closure check, then the `Closed:` line, the Done move and the board's `Last updated` |
| `.claude/hooks/lib/board/` (or a new helper beside it) | the row move, shared with `post_agent_move_to_review.py`'s shape |
| `.claude/hooks/stop_auto_mode_check.py` | block a stop when an auto report has no `Memory:` line |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | expose the Gate 5/6 evidence readers for reuse — no change in what it blocks |
| `templates/TASK_REVIEW_template.md`, `templates/MINIMAL_LOG_template.md` | the `Memory:` and `Closed:` fields, and the D9 list of fields a report must hold |
| `tests/test_auto_verify.py`, `.claude/hooks/tests/test_stop_auto_mode_check.py` | AC 1–6 |
| `docs/claude-md/tracks.md` | row 19, `### Never in auto mode`, and the close-out step |
| `PROJECT_SPEC.md` | glossary: **Auto close-out** |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| the merge and push blocks in `pre_bash_block_unsafe_merge.py` | the merge stays the user's; only the readers are reused |
| `docs/claude-md/tracks.md` `### Stops that stay` | the safety pauses are unchanged by this task |
| `memory/MEMORY.md` and the cold files | writes stay the Supervisor's; the hook never writes memory |
| `AGENTS.md` beyond its existing auto-mode sentence | it is at its 196-line cap; detail belongs in `tracks.md` |

---

## Test Plan

Unit tests on a fixture board and fixture evidence files, with the `claude` binary stubbed as `tests/test_auto_verify.py` already does, and the run record written into a temporary anchor directory. One test per AC 1–8 case, including a negative test that asserts the run issues no writing git command, and one per missing report field in AC 8. Then the full suite and `validate.sh`. AC 11 is the one paid run, and only after the user says go.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk High)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T189.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] UI Evidence rows marked ☐ N/A (pure-hook task)
- [ ] Supervisor notified: task ready for Stage 4 review
