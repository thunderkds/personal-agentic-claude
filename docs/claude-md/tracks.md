# Tracks — minimal and extended

> Extracted from `AGENTS.md` (`## Tracks`), which keeps the short rule and points here. Evidence: the
> kit-arms experiment (T175–T177). On 6 small tasks, a 26-line `AGENTS.md` scored 12/12 with 3 stops; the
> full kit scored 12/12 only after 7 stops (5 about its own process) at 2.3× the cost.

Every implementation request goes on one of two tracks:

- **Minimal track** — small, low-risk work. The Supervisor writes the code itself and runs straight
  through: test first, change, real run. No process stop. It ends with a **Decision record**.
- **Extended track** — big, risky or multi-session work. This is the full 5-stage pipeline
  (`docs/claude-md/pipeline-stages.md`), unchanged.

The rule below picks the track, never how small a task feels.

---

## Track rule

Assign Complexity and Risk as today (the Complexity matrices in `agents/<role>.md`). Then check each row.
If **any** row is true, the task goes on the extended track.

| Condition | Track |
|---|---|
| Complexity C2 or above: 3+ files, a design choice, or a new component | extended |
| Risk Medium or High. A request that touches a risky file counts here even when it looks small: a migration, auth or secrets, a delete of user data | extended |
| The request has a Gate-2 word (*refactor*, *restructure*, *migrate to pattern*, *clean architecture*, *QA suite*, *test coverage*) or the word *migrate* | extended |
| The work clearly spans more than one session, or more than one agent | extended |
| A UI component: the Gate 6 design Evidence rows do not fit a Decision record | extended |

Otherwise the task goes on the **minimal** track: C0 or C1, Risk Low, no Gate-2 word, one session, one
agent, no UI.

---

## Announcement

Before any work, the Supervisor says the track in one line, with the reasons that decided it:

```
Track: minimal — C0, Risk Low, one file, no Gate-2 word
Track: extended — C2 (a new command across 3 files), Risk Medium
```

Then it starts the work at once. The announcement is a statement, not a question: it does not wait for a
reply.

---

## Switching track

- The user can reply `full` (extended track) or `minimal` at any time, and the Supervisor switches.
- The Supervisor may move a task **up** (minimal → extended) mid-task when it finds a row of the rule that
  is true. It says so in one line: `Track: extended — moved up: <reason>`. It never moves a task **down** on
  its own.
- A task grows when it needs more than one file beyond its first estimate, a design choice, or a second
  session. Move it up, then write the task guide from what was learned. The extended track continues from
  Stage 2 with that guide.
- The user says `minimal` for a task that the rule puts on the extended track (for example High risk): the
  Supervisor complies. It states the risk in one line, and the record's `Decisions:` says "track set by the
  user".

---

## Minimal-track flow

The Supervisor runs these steps itself, in one context, straight through. No task guide, no sub-agent, no
Stage 4 skills.

1. **Register.** Take the next task ID and set the active-task state (`.claude/hooks/.state/active_task`, at the literal absolute path of the main checkout), so the trace hook attributes every call to the task.
2. **Branch.** Work on a new branch for the task, never on `main`.
3. **Test first.** Write a new test that fails for the right reason, and run it to see it fail. Gate 5 holds on this track too: a new test, and its passing output in the record's `Checked:` field.
4. **Change.** Make the smallest change that passes the test. Touch only the code the task needs.
5. **Run it for real.** Run the full test suite. Then run the program the way a user would, and note the command and what it printed.
6. **Record.** Append the Decision record to `tasks/MINIMAL_LOG.md`, newest first. If the file does not exist, create it from `templates/MINIMAL_LOG_template.md`. The same block is the Supervisor's final chat message.
7. **Board.** Add one board row under Ready for Review in `PROJECT_KANBAN.md`, marked `| Track: minimal | Record: tasks/MINIMAL_LOG.md` at its end. Commit on the task branch.

**The only stop.** When the request itself is unclear (it has more than one reasonable reading), ask one
clear question and stop. Asking is cheaper than undoing a wrong guess. A question about a fact in the code
is not a stop: read the code and go on.

**Merge is never automatic.** The row stays in Ready for Review, so the merge gate blocks every push and
merge while it is there. The branch merges only when the user asks. Stage 5 verify is still mandatory before
any merge: the user runs `/verify`, then the Supervisor moves the row to Done and merges. The record's
`Not done:` field always names the merge.

---

## Hard-Stop Gates on the minimal track

| Gate | On the minimal track |
|---|---|
| 1. No TASK_GUIDE = no work | Does not apply: it is scoped to the extended track. |
| 2. Complexity floor | A Gate-2 word puts the task on the extended track (rule row 3). |
| 3. KANBAN current | Applies: step 7 adds the row; the merge moves it to Done. |
| 4. One project per KANBAN | Applies unchanged. |
| 5. No tests = not done | Applies, through the record's `Checked:` field (step 3 and step 5). |
| 6. UI evidence | A UI component puts the task on the extended track (rule row 5). |

---

## Hooks for a task with no guide

`tests/test_tracks.py` pins each of these (AC 6 of T178):

- `pre_bash_block_unsafe_merge.py` — blocks every push and merge while the row is In Progress or Ready for
  Review. A Decision record is not Evidence, so the row reads `(no evidence row)`. The `Track: minimal`
  marker exempts nothing.
- `pre_agent_step_limit.py` — counts the task's calls by the active-task state from step 1, with the same
  limit as any task. A call with no task stays uncounted.
- `post_write_register_task.py` — fires only on a `TASK_GUIDE_*.md` write, so a write to
  `tasks/MINIMAL_LOG.md` leaves the board alone. Step 7 adds the row by hand.
- `stop_review_reminder.py` — lists a `Track: minimal` row as waiting for the user's merge decision, not
  for Stage 4 review.

---

## Board mode `online`

In board mode `online` the record still goes to `tasks/MINIMAL_LOG.md`. The board row goes through
`scripts/board_sync.py` as today. If the board's render drops the `Track: minimal` marker, the stop reminder
lists the row for Stage 4. That is a wrong reminder, not a weaker gate.
