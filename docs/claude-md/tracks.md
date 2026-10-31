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

1. **Register.** Take the next task ID and set the active-task state for this session (`.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID`, at the literal absolute path of the main checkout), so the trace hook attributes every call to the task.
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

**Merge is never automatic.** The row stays in Ready for Review, so the merge gate blocks every merge, and
every push of the task's own branch, while it is there. The branch merges only when the user asks. Stage 5 verify is still mandatory before
any merge: the Supervisor starts the headless auto verify run and reports its verdict
(`### Auto verify (Stop hook)`). You may still run `/verify` yourself. You must run it when that run is
blocked or `CLAUDE_AUTO_VERIFY=off`. Then the Supervisor moves the row to Done and merges. The record's
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

- `pre_bash_block_unsafe_merge.py` — blocks every merge, and every push of the task's own branch, while the
  row is In Progress or Ready for Review. A Decision record is not Evidence, so the row reads
  `(no evidence row)`. The `Track: minimal` marker exempts nothing. Since T197 a push of a branch that names
  exactly one task in In Progress or Ready for Review is judged by that task alone: another session's open
  task does not block it. A merge, a push of a branch named after a Todo, Done or absent task, and every
  push the hook cannot tie to one task (`main`, `release/*`, `--all`, a tag, two IDs in the branch name, an
  unclear `cd`, a `&`, an option it does not know), check the whole board.
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
| Medium | A Debate (`resolve-question`): the Advocates propose, the Supervisor decides by its rules | exactly 2, required |
| High | A Debate (`resolve-question`): the Advocates propose, the Supervisor decides by its rules | exactly 3, required; the third favours the smallest safe thing |

At Risk High, at least one decision is always debated by 3 Advocates: pick the decision with the biggest
effect on the user's data or scope (for example, convert `recurring.csv` too, or leave it). Cited `RULE:`
lines do not replace it; they stay valid for safety actions.

Each Advocate `Agent` call's `description` starts with `Advocate` (for example
`Advocate 1: convert recurring.csv?`), so the auto-mode check below can count them.

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
| 18 | Stage 5 item 1: `/verify` (never in the Supervisor's own session) | The Supervisor starts the headless auto verify run (T182; every task since T203) with `python3 .claude/hooks/stop_auto_verify.py --start <ID>`, and writes its own real-run check under `Checks:` as `auto-checked, not /verify`. The `verify` Evidence row stays unchecked until that run fills it from a real `/verify`, or the user does: a blocked run falls back to `/verify (yours)`. | `Checks:` / `Not done:` |
| 19 | Stage 5 items 3–6: memory update, merge, Done, `ship` | Memory update: the Supervisor runs the diff-driven pass before it stops, and writes the `Memory:` line. Done: after an auto verify pass, the hook moves the row (`### Auto close-out`). Merge, push and `ship`: never in auto mode. The task waits in Ready for Review until the hook moves it. | `Memory:` / `Closed:` / `Not done:` |
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
  `FACT: <Citation>`, `DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>)` or
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
- `Memory:` — the diff-driven memory pass (`docs/claude-md/memory-write-protocol.md`), which the
  Supervisor runs before it stops. Name each entry it wrote, or write `Memory: nothing new`. The memory
  writes stay the Supervisor's; no hook writes memory.
- `Not done: merge (yours)`, plus the `/verify` state: `auto verify: running (T182)`, its result, or
  `/verify (yours)` when the hook is not installed, its run was blocked, or `CLAUDE_AUTO_VERIFY=off`.
- `Closed:` — written by the hook, never by the Supervisor, when it moves the row to Done
  (`### Auto close-out`). When a check stops the move, the hook writes `Paused: done not moved — <reason>`.

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
   calls: `Risk High, but no decision was DEBATED with 3 Advocates`;
6. the report has no `Memory:` line (T189): the memory pass is done before the stop, and recorded;
7. the task's own trace `memory/event-trace/<ID>.jsonl` holds no test run (Gate 5): register the task (minimal-track step 1), rerun its tests, then stop.

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

`.claude/hooks/stop_auto_verify.py` runs the real `/verify` in a separate headless session, so the
Supervisor never runs it in its own session. Since T203 it runs for **every task**, with or without
`[auto]`, on **both tracks** (T188). It acts on a task only when all of these hold:

1. The task's row is in `### Ready for Review` on `PROJECT_KANBAN.md`.
2. The task has a report file: `tasks/TASK_REVIEW_<ID>.md` with a `verify` Evidence row on the extended
   track, or the task's own record in `tasks/MINIMAL_LOG.md` with a `Checked:` field on the minimal track.
   A task without one gets one line on stderr and no run.
3. Its result is empty, or holds an earlier auto run for other code.

There are two ways in, and they share one lock:

- **The Supervisor starts it.** Right after it moves a task to Ready for Review, the Supervisor runs
  `python3 .claude/hooks/stop_auto_verify.py --start <ID>`. The command checks the three conditions above
  for that task, starts the run, prints the log path and returns at once (exit 0). When it starts nothing,
  it prints one line that says why and exits 1: the task is not at Ready for Review, its result is already
  filled for this commit, or a run for this commit already started. The Supervisor then waits for the run
  (it watches the log or the result) and puts the verdict in its reply or final report.
- **The Stop hook is the backstop.** It fires when the Supervisor stops and does the same for every task on
  the board.

Both read the main checkout's board only. Run from a linked worktree, they start nothing and say so in one
line. A task's report is read from its worktree first, so the run uses the task's own code and head commit,
never a placeholder copy on main. The worktree is the one whose branch the task's board row names
(`Started …: branch `<name>``). If the row names no branch, exactly one worktree whose branch names the task
may be used. With none or several, nothing starts and one line says the checkout is ambiguous. The order of
`git worktree list` never decides.

`CLAUDE_AUTO_VERIFY=off` turns this back to the T182 rule. Then only a task whose report has the
`Mode: auto` line runs, through the hook and through `--start`. Every other task's `/verify` stays yours.
The default is on. Each run costs at most `CLAUDE_AUTO_VERIFY_BUDGET_USD` (default 2), so several tasks at
Ready for Review at once cost up to that much each.

`.claude/hooks/lib/auto_mode.py` is the one reader of which tasks those are, which track each one is on, and
which file holds its report. The auto-mode check above reads the same module, so the two hooks can never
disagree about which tasks are in auto mode.

The hook then starts one new headless session in the task's checkout (the main checkout or its worktree):
`claude -p "/verify <ID>" --max-budget-usd 2 --output-format json`. The session uses your normal permission
settings, never `--dangerously-skip-permissions`. The hook returns at once: the run is detached in its own
session (`setsid`). `CLAUDE_AUTO_VERIFY_BUDGET_USD` changes the budget, and `CLAUDE_AUTO_VERIFY_TIMEOUT_S`
the time limit (default 1800). The run writes its output to `.claude/verify-runs/<ID>-<commit>.log`
(gitignored) — the same path and the same one-run-per-commit lock on both tracks. One task and commit run
once: to run again on the same commit, delete that log. A commit that changes only the file holding the
task's result counts as the same code.

When the run ends, the hook, never the Supervisor, writes three things:

- A run record, in the directory that `.claude/settings.json` denies agents write access to (the trace
  anchors' directory, `~/.claude/harness-anchors/`).
- The result, where that track keeps its evidence:
  - **extended track** — the `verify` Evidence row: `☑ pass`, `☑ fail` or `☐ blocked`, with the Notes
    `auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file> — <pass|fail|blocked>`.
  - **minimal track** — one line under the Decision record's `Checked:` field, in the same shape:
    `- verify: ☑ pass — auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file>`. A
    `Checked:` line you wrote is never edited or removed.
- The report's `Not done:` auto verify slot, so the report you read stops saying
  `auto verify: running (T182)` after the run ended. It becomes
  `auto verify: ☑ pass (session <id>, commit <sha>, log .claude/verify-runs/<file>)`, in
  `## Auto decisions` (extended) or the record's `**Not done:**` line (minimal). The merge clause is left
  exactly as it is. A slot you wrote by hand is left alone, and the reason goes in the run log.

Only a verdict line of the skill's result sets the result. The line starts with the bold label and names one
word, `PASS` or `FAIL`, in one of four shapes: `**Verdict:** PASS`, `**Verdict: PASS**`,
`**Verdict: PASS. <sentence>**` or `**Verdict**: PASS`. A line that lists choices (`**Verdict:** PASS | FAIL | BLOCKED | SKIP`,
`PASS / FAIL`, `PASS or fail`, `PASS - FAIL`; a second verdict word in any case, after `|`, `/`, `,`, a dash, `or` or `and`) is not a verdict and is ignored, so the blank report template never reads as a
pass. The parser fails closed: anything it does not recognise is `blocked`. Each of these is
`blocked`: a SKIP or BLOCKED verdict, no verdict line, a budget stop, a timeout, or no `claude` on the PATH.
A blocked result never contains the word "pass". The hook never overwrites a row or a line you filled. The
merge gate accepts an `auto-run by hook` row — or a minimal-track `verify:` line — only when its run record
exists for that task and the head commit, and says pass; a hand-typed line in a Decision record counts for
nothing. After a pass, the same run closes out a task whose report has the `Mode: auto` line (`### Auto close-out`).
A task without it stays in Ready for Review after its pass, and the Supervisor moves it to Done as before.
The merge stays yours. You may still run `/verify` yourself at any time; when the run is blocked, you must.

### Auto close-out

After an auto verify **pass**, the same detached run closes the task out (T189,
`.claude/hooks/lib/auto_closeout.py`). It moves the task's row from `### Ready for Review` to `### Done`.
It is not a merge: the branch stays unmerged, and the merge, the push and `ship` stay yours. A `fail` or
`blocked` result leaves the row where it is.

The run moves the row only when all three checks hold:

1. **The run record proves the pass.** The record for that task and the head commit exists and says pass,
   for the session that ran. The merge gate's own rule accepts the result. A hand-typed `auto-run by hook`
   result never moves a row.
2. **Hard-Stop Gates 5 and 6 hold.** The tests row is `☑ pass` with pasted output (minimal track: a
   `New test` line under `Checked:`), and the trace holds a real test run. Each of the three UI design
   rows is `☑ pass` with evidence, or N/A with a written reason. A task with no UI writes `☐ N/A` and a
   reason in all three. Auto mode never skips a Hard-Stop Gate.
3. **The report is complete.** It holds `Mode: auto`, at least one numbered decision line, `Checks:`
   (minimal: `**Checked:**`), `Memory:`, the `Not done:` auto verify slot with its result, and a
   `Not done:` line that still names the merge. A field that still holds a template `<...>` placeholder
   counts as missing. The report is the only account of a run that nobody watched, so it is a check,
   not a summary.

When all three hold, the run writes
`Closed: row moved to Done <date> — auto verify pass (session <id>, commit <sha>); Gates 5 and 6 checked`
into the report. It reads the report again, then moves the row: `- [ ]` becomes `- [x]`, the row goes to
the top of `### Done`, and it gains `Done <date>: auto verify pass (session <id>, commit <sha>)`. Nothing
else in the row changes. `**Last updated**` at the top of the board gets that date.

When a check fails, the row stays in Ready for Review. The run log says `done not moved: <reason>` or
`report incomplete: <field>`, and the report gains `Paused: done not moved — <reason>`, so the report
names what still waits for you. A failed Gate 5 or 6 check also adds `done not moved: <reason>` to the
end of the hook-written result.

Each line is added once. A line you wrote is never changed. The board in the main checkout is the
registry: the run reads it again just before the write and finds the row by its task ID. A row you
already moved is left alone. The run issues no git command that writes, and it writes no memory file.

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

These stay the user's, in every mode:

- merge;
- push;
- `ship`.

The memory pass and the move to Done are automatic: see `### Final report` (`Memory:`) and
`### Auto close-out`.

### The Supervisor never

- runs `/verify` or writes its `verify` Evidence row (only T182's hook writes it). The Supervisor starts
  the headless run with `--start <ID>`; it never runs the skill in its own session. The merge gate cannot
  tell who wrote the row, so this rule is doctrine: the Supervisor's own check goes under `Checks:`, never
  in the `verify` row. The one exception the gate can check is an `auto-run by hook` row: it needs the
  hook's run record (`### Auto verify (Stop hook)`);
- moves a task to Done (only the hook does, `### Auto close-out`);
- moves a task down a track.

### Edge cases

- `[auto]` with "ask me before X" in the same request: the explicit ask wins for X. Everything else is
  auto.
- A minimal-track task that moves up mid-task stays in auto mode on the extended
  track, and the report says when it moved.
- A sub-agent reports `Status: blocked` with a Choice question: a Debate settles it, not the user.
- The session nears its usage limit: stop at a clean point, write the final report so far, and say what is left.
- Two `[auto]` tasks in one session: each task has its own report and its own Debate count.
