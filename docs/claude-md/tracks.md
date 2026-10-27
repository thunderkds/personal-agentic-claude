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
| The change deletes, moves, renames or converts user data or its storage format (for example CSV to JSON, or "get rid of the old file"), even when the request does not say *migrate*. This row needs no rating first: the data change alone decides | extended |
| The work clearly spans more than one session, or more than one agent | extended |
| A UI component: the Gate 6 design Evidence rows do not fit a Decision record | extended |

Otherwise the task goes on the **minimal** track: C0 or C1, Risk Low, no Gate-2 word, no change to user data,
one session, one agent, no UI.

---

## Announcement

Before any work, the Supervisor says the track in one line, with the reasons that decided it:

```
Track: minimal — C0, Risk Low, one file, no Gate-2 word
Track: extended — C2 (a new command across 3 files), Risk Medium
```

Then it starts the work at once. The announcement is a statement, not a question: it does not wait for a
reply. The Supervisor must never ask which track, never recommend a lower one. On the extended track it goes
on with the pipeline at once, from the first stage not yet done.

---

## Switching track

- The user can reply `full` (extended track) or `minimal` at any time, and the Supervisor switches. The
  Supervisor does not prompt for it: never ask which track, never recommend a lower one; the user's `minimal`
  is their own choice.
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
Stage 4 skills. In auto mode, the Debate's read-only `Explore` Advocates are the one exception
(`## Auto mode`).

1. **Register.** Take the next task ID and set the active-task state (`.claude/hooks/.state/active_task`, at the literal absolute path of the main checkout), so the trace hook attributes every call to the task.
2. **Branch.** Work on a new branch for the task, never on `main`.
3. **Test first.** Write a new test that fails for the right reason, and run it to see it fail. Gate 5 holds on this track too: a new test, and its passing output in the record's `Checked:` field.
4. **Change.** Make the smallest change that passes the test. Touch only the code the task needs.
5. **Run it for real.** Run the full test suite. Then run the program the way a user would, and note the command and what it printed.
6. **Record.** Append the Decision record to `tasks/MINIMAL_LOG.md`, newest first, with every field of the template: the `## <ID> — <title> · <track>` heading, `Asked:`, `Decisions:`, `Checked:`, `Files:`, `Not done:`. If the file does not exist, create it from `templates/MINIMAL_LOG_template.md`. The same block is the Supervisor's final chat message.
7. **Board.** Add one board row under Ready for Review in `PROJECT_KANBAN.md`, marked `| Track: minimal | Record: tasks/MINIMAL_LOG.md` at its end. Commit on the task branch without asking: the commit is part of this step.

**The only stop.** When the request itself is unclear (it has more than one reasonable reading), ask one
clear question and stop. Asking is cheaper than undoing a wrong guess. In auto mode, a Debate settles it
instead (`## Auto mode`). A question about a fact in the code is not a stop: read the code and go on.
Asking whether to commit is not a stop either: step 7 commits.

**Backups.** A backup must sit inside the project or in a path the user named, never in `/tmp`: a temp
directory can be gone by the time the user needs it.

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
| 6. UI evidence | A UI component puts the task on the extended track (rule row 6). |

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

---

## Auto mode

The user turns auto mode on with the literal tag `[auto]` anywhere in the request, for example
`move the data from CSV to JSON [auto]`. Only the bracketed tag counts, exactly as written: a bare word
*auto* (for example "add auto-save") or `[Auto]` is not the tag, and the task runs in normal mode. Without
the tag, both tracks behave as the sections above say.

In auto mode the Supervisor picks the track by the same rule and runs it to the end without asking the user
anything. Each decision it would have asked about is made by a rule, a Citation or a Debate
(`skills/resolve-question/SKILL.md`), and goes in the **final report**. The track line says so:

```
Track: extended · auto — <reasons>. I won't stop for questions; every decision goes in the final report.
Track: minimal · auto — <reasons>. I won't stop for questions; every decision goes in the final report.
```

**Marker.** The task records auto mode in one line that a hook can read: `Mode: auto`, exactly as written,
alone on its line, outside any HTML comment. On the extended track it is the first line under
`## Auto decisions` in `tasks/TASK_REVIEW_<ID>.md`. On the minimal track it is the line right under the
Decision record's heading. T182's hook keys on this line. Both templates hold the line inside an HTML
comment, so a copied template is not marked.

### Debate size by Risk

The task's **Risk** label sets how every decision that would have been a question to the user is made:

| Risk | Who decides | Advocates |
|---|---|---|
| Low | The Supervisor decides alone and logs `RULE`, `FACT` or `SAFER OPTION` with the reason | none: no Debate |
| Medium | A Debate (`resolve-question`): the Advocates argue, the Supervisor decides by its rules | exactly 2, required |
| High | A Debate (`resolve-question`): the Advocates argue, the Supervisor decides by its rules | exactly 3, required; the third argues the smallest safe thing |

At Risk High, at least one decision is always debated by 3 Advocates: pick the decision with the biggest
effect on the user's data or scope (for example, convert `recurring.csv` too, or leave it). Cited `RULE:`
lines do not replace it; they stay valid for safety actions.

Each Advocate `Agent` call's `description` starts with `Advocate` (for example
`Advocate 1: keep recurring.csv`), so the auto-mode check below can count them.

Every decision, at every Risk level, has its log line in the final report. This supersedes T179's count
("2, or 3 for 3+ options or High risk") in auto mode. Outside auto mode, `resolve-question` is unchanged.

### Minimal track in auto mode

The one stop of the minimal track (an unclear request) is decided by `### Debate size by Risk`. A
minimal-track task is Risk Low by the track rule, so the Supervisor decides and logs the reason: no
Advocates are required. When the user set the minimal track for a Medium or High risk task, the table's
Advocates are required, and they are the one exception to the track's no-sub-agent rule; the Supervisor
starts them (`resolve-question`) and never argues both sides itself. The Decision record carries the
final report: the `Mode: auto` line, each decision with how it was made, and the flag
(`templates/MINIMAL_LOG_template.md`). A minimal-track task has no guide, so it counts its Debates per
session.

### Every user stop and its auto rule

These are all the places where a track waits for the user today: `AGENTS.md`,
`docs/claude-md/pipeline-stages.md` and the skills the stages run. In auto mode each one follows its rule.
`⚠` in the last column means the report line ends with `⚠ decided for you — please review`. "Debate" in
this table follows `### Debate size by Risk`: on a Risk Low task the Supervisor decides alone, and the line
is logged `RULE`, `FACT` or `SAFER OPTION`, not `DEBATED`. At Risk Medium or High, every decision flagged
`⚠` is a Debate, whatever the last column says.

| # | Stop today (where) | Auto rule | Logged as |
|---|---|---|---|
| 1 | Phase 0 questions and the `PRD.md` confirmation, new project only (`docs/claude-md/phase0-project-initiation.md`) | Answer each question from the request and the repo, with Citations. A question they cannot answer is a Choice question: Debate. | `FACT` / `DEBATED` ⚠ |
| 2 | Stage 0.5a `grill-with-docs`: "Resolve all flagged items with the user" | Answer from the docs and code with Citations. What they cannot answer is a Choice question: Debate. | `FACT` / `DEBATED` ⚠ |
| 3 | `grill-with-docs`: an ADR-eligible decision ("ask the user whether to escalate") | Write the DDR; do not escalate to an ADR (the smaller change). | `SAFER OPTION` ⚠ |
| 4 | Stage 0.5b `brainstorming`: the user approves one direction | Take the recommended direction and list the alternatives in the report. | `RULE` ⚠ (taste) |
| 5 | Stage 1 item 1: one-time setup (`fewer-permission-prompts`, `update-config`) | Skip both: they change the user's permission settings and hooks. Name them under `Not done:`. | `RULE` |
| 6 | Stage 1 item 2 and `AGENTS.md` `## Multi-CLI Configuration`: the user lists the CLIs and their models | Read the `## CLI Model Table` in `PROJECT_SPEC.md`. No row or an empty cell: row 14. | `FACT` |
| 7 | Stage 1 item 3: a missing agent guide ("ask the user to save it") | The Supervisor writes it from `templates/` on the task branch. | `RULE` |
| 8 | Stage 1 item 4: "run `git status` … and paste the output" | The Supervisor runs it itself. | `RULE` |
| 9 | Stage 1 item 6: the user must save or confirm `PROJECT_SPEC.md` | The Supervisor checks the file, or writes it from `templates/PROJECT_SPEC_template.md`. | `RULE` |
| 10 | Stage 1 item 8: "Are they correct?" (the domain models) | Record the models the scan found, with their paths. | `FACT` ⚠ (taste) |
| 11 | Stage 1.5: "Approve or request any modifications?" (the sub-agent team) | The base team; `craft-agent` only for a role the base team does not cover. | `RULE` |
| 12 | Stage 2: the user approves the task breakdown and confirms `tasks/` | The Supervisor's own breakdown, labelled by the Complexity matrices. It lists `tasks/` itself. | `RULE` |
| 13 | Stage 2/3: the Requirement Fidelity Gate ("Restated intent confirmed") | Signed `auto (Supervisor)`, not by the user. | `RULE` |
| 14 | Stage 3 `craft-spawn-prompt` returns STOP-and-ask: no CLI named, no `## CLI Model Table` row, or an empty cell | Spawn on the CLI that runs this session, with the model this session runs as. Never invent another CLI's model name. | `SAFER OPTION` ⚠ |
| 15 | Stage 3: a sub-agent reports `Status: blocked` with a `Question:`, or asks to approve its `tdd` plan | `resolve-question`: a Fact question by Citation or Scanners, a Choice question by Debate. The Supervisor approves a `tdd` plan that matches the guide. | `FACT` / `DEBATED` ⚠ / `RULE` |
| 16 | Stage 4 pull moment 3 (board mode `online`): "review against the new version?" | Review against the new version. | `RULE` |
| 17 | Stage 4 item 7: a finding whose fix needs a choice | Debate. | `DEBATED` ⚠ |
| 18 | Stage 5 item 1: `/verify` (only the user can run it) | The Supervisor's own real-run check, written under `Checks:` as `auto-checked, not /verify`. The `verify` Evidence row stays unchecked: T182's hook fills it from a real `/verify` run, or the user does. | `Checks:` |
| 19 | Stage 5 items 3–6: memory update, merge, Done, `ship` | Never in auto mode. The task ends at Ready for Review on its branch. | `Not done:` |
| 20 | `AGENTS.md` self-monitoring: "want me to compact before continuing?" | Do not ask. Near the session's context or usage limit, stop at a clean point (see Edge cases). | `Paused:` |
| 21 | Minimal track: an unclear request (its one stop) | By `### Debate size by Risk`. At Risk Low (the minimal track's own level) the Supervisor decides the reading and logs why. | `RULE` / `SAFER OPTION` ⚠ |

The skills these rows name keep their own stop text. In auto mode this table wins over it.

### Final report

The final report is the `## Auto decisions` section of `tasks/TASK_REVIEW_<ID>.md` (extended track), or
the Decision record itself (minimal track). It is written to its file before the run ends. If
`tasks/TASK_REVIEW_<ID>.md` does not exist yet, create it from `templates/TASK_REVIEW_template.md`. The
chat message is a copy, not the report. On the extended track, Stage 4 `code-review` still runs before
the run ends, plus `security-review` at Risk Medium or High, because it is not a user stop. Copy the report's shape from `templates/TASK_REVIEW_template.md` or
`templates/MINIMAL_LOG_template.md`:

- `Mode: auto`, then one numbered line per decision: what was decided, then how — `RULE: …`,
  `FACT: <Citation>`, `DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>)` or
  `SAFER OPTION: …`. Every Debate, safer-option and taste decision ends with
  `⚠ decided for you — please review`.
- Write `DEBATED` only when ≥2 Advocate `Agent` calls ran for that question, naming each Advocate's
  option. A decision with no Advocates is labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`: the
  Supervisor's own weighing of options is not a Debate.
- A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A safety action a rule
  requires (for example the backup before a delete) is `RULE` without the flag.
- At Risk Medium or High, every `⚠` line is `DEBATED` with exactly 2 or 3 Advocates named.
- At Risk Medium or High, a `RULE:` counts only when it names a written rule: a repo path with a line or a
  section — `path:line`, `path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`. `FACT:` needs a
  Citation (`path:line "quoted text"`) under the same rule. A `RULE:` or `FACT:` without one counts as a
  choice, so it is `DEBATED` with 2 or 3 Advocates. Good: `2. backed up the CSV before the delete — RULE:
  `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv untouched — RULE: Surgical Changes`
  (it names no written rule, so it is a choice). Low risk is unchanged.
- `Paused:` — a stop that stayed (below), and why. Only when one paused the task.
- `Checks:` — the tests, the reviews, and the real run, labelled `auto-checked, not /verify`.
- `Not done: merge (yours)`, plus the `/verify` state: `auto verify: running (T182)`, its result, or
  `/verify (yours)` when T182 is not built or its run was blocked.

The Supervisor's final chat message repeats the block. It is not the `delivery-report` HTML page, and it is
not Evidence: the merge gate does not read it. A Debate also leaves its `DEBATE` line under the guide's
`## Questions Log` (`resolve-question`); the report collects those lines.

### Auto-mode check (Stop hook)

`.claude/hooks/stop_auto_mode_check.py` runs when the Supervisor is about to stop. It finds auto-mode tasks
from the board's In Progress and Ready for Review rows, and also from their files: every
`tasks/TASK_REVIEW_*.md` with `## Auto decisions` or a `Mode: auto` line, and the newest `tasks/MINIMAL_LOG.md`
record with `Mode: auto`. A project with no `PROJECT_KANBAN.md` is still checked. It skips a finished task: one
whose row is in Done, or whose review file has `☑ pass` in its `verify` row's Result cell. It blocks the stop
with a short reason when:

1. the report has no `## Auto decisions` section whose first line is `Mode: auto` (extended), the Decision
   record does not start with `Mode: auto` (minimal), or there is no report file at all;
2. at Risk Medium or High, a choice is not `DEBATED` with exactly 2 or 3 Advocates named. A choice is a `⚠`
   line, a `SAFER OPTION`, or an uncited `RULE:` or `FACT:`: an uncited `RULE:` or `FACT:` counts as a choice.
   The reason gives the decision number and its label, for example decision 1 (`RULE`);
3. the event trace holds fewer Advocate `Agent` calls (description starting `Advocate`) than 2 or 3 per
   `DEBATED` line;
4. on the extended track, the trace has no `code-review` Skill call, or no `security-review` Skill call at
   Risk Medium or High;
5. at Risk High, no `DEBATED` line names 3 Advocates, or the trace holds fewer than 3 Advocate `Agent`
   calls: `Risk High, but no decision was DEBATED with 3 Advocates`.

A board row counts as auto mode when its report carries `## Auto decisions` or a `Mode: auto` line, when its
Decision record's request carries `[auto]`, or when this session's request carries `[auto]` and the task's
files changed after it. Risk comes from the guide's `**Risk Level**`, else the review file, else the board
row, else Low; a Decision record is Risk Low unless it says otherwise. The trace is `memory/event-trace/<ID>.jsonl` plus the last 6 hours of
`memory/event-trace/_untagged.jsonl` (`CLAUDE_AUTO_CHECK_WINDOW_S`): Advocate prompts carry no task ID, so
their calls land in `_untagged.jsonl` unless the active-task state file is set.

It never loops: on the second fire (`stop_hook_active`) it allows the stop and appends
`Paused: auto-mode check failed — <reasons>` to the report. Unreadable files fail open, with one line on
stderr. It does not read or write Evidence: the merge gate is unchanged.

### Auto verify (Stop hook)

`.claude/hooks/stop_auto_verify.py` runs the real `/verify` for an auto-mode task, so the Supervisor never
runs it. It fires when the Supervisor stops. It acts on a task only when all of these hold:

1. The task's row is in `### Ready for Review` on `PROJECT_KANBAN.md`.
2. Its `tasks/TASK_REVIEW_<ID>.md` has the `Mode: auto` line.
3. Its `verify` row is empty, or holds an earlier auto run for other code.

The hook then starts one new headless session in the task's checkout (the main checkout or its worktree):
`claude -p "/verify <ID>" --max-budget-usd 2 --output-format json`. The session uses your normal permission
settings, never `--dangerously-skip-permissions`. The hook returns at once: the run is detached in its own
session (`setsid`). `CLAUDE_AUTO_VERIFY_BUDGET_USD` changes the budget, and `CLAUDE_AUTO_VERIFY_TIMEOUT_S`
the time limit (default 1800). The run writes its output to `.claude/verify-runs/<ID>-<commit>.log`
(gitignored). One task and commit run once: to run again on the same commit, delete that log. A commit that
changes only the task's review file counts as the same code.

When the run ends, the hook, never the Supervisor, writes two things:

- A run record, in the directory that `.claude/settings.json` denies agents write access to (the trace
  anchors' directory, `~/.claude/harness-anchors/`).
- The `verify` row: `☑ pass`, `☑ fail` or `☐ blocked`, with the Notes
  `auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file> — <pass|fail|blocked>`.

Only the `**Verdict:** PASS` or `FAIL` line of the skill's result sets the row. Each of these is `blocked`: a
SKIP or BLOCKED verdict, no verdict line, a budget stop, a timeout, or no `claude` on the PATH. A blocked
row never contains the word "pass". The hook never overwrites a row you filled. The merge gate accepts an
`auto-run by hook` row only when its run record exists for that task and the head commit, and says pass.
The merge stays yours. Without `[auto]`, nothing changes: `/verify` stays yours.

### Stops that stay

Even in auto mode, the Supervisor pauses the task, with one message that says why, for:

- a safety-hook block;
- an action that deletes or overwrites data with no backup;
- the 4th Debate in a task (the `resolve-question` cap);
- a paid action outside the task's own work;
- a login or secret the Supervisor does not have;
- the same sub-agent hitting the step limit twice.

The pause also goes in the final report, on its `Paused:` line.

### Never in auto mode

- merge or push;
- the Supervisor running `/verify` or writing its `verify` Evidence row (only T182's hook writes it). The
  merge gate cannot tell who wrote the row, so this rule is doctrine: the Supervisor's own check goes under
  `Checks:`, never in the `verify` row. The one exception the gate can check is an `auto-run by hook` row:
  it needs the hook's run record (`### Auto verify (Stop hook)`);
- moving a task to Done;
- moving a task down a track.

### Edge cases

- `[auto]` with "ask me before X" in the same request: the explicit ask wins for X. Everything else is
  auto.
- A minimal-track task that moves up mid-task stays in auto mode on the extended
  track, and the report says when it moved.
- A sub-agent reports `Status: blocked` with a Choice question: a Debate settles it, not the user.
- The session nears its usage limit: stop at a clean point, write the final report so far, and say what is left.
- Two `[auto]` tasks in one session: each task has its own report and its own Debate count.
