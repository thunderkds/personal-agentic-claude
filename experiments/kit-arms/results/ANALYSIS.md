# Kit-arms results — 2026-10-26

Model `sonnet` · 2 run(s) per cell · 36 of 36 runs recorded · spend $5.66 of cap $60.00
Kit: `7b7ab87` (HEAD of the repo `setup.sh` installed from)

## Per arm

| Arm | Score | Unsafe | Median cost | Total cost | Median wall (s) | Median turns |
|---|---|---|---|---|---|---|
| bare | 10 / 12 | 0 | $0.08 | $1.04 | 25 | 8.5 |
| minimal | 12 / 12 | 0 | $0.10 | $1.33 | 34 | 8.5 |
| full | 8 / 12 | 0 | $0.14 | $2.61 | 24 | 8.5 |

## Per task (verdict of each run)

| Task | Kind | bare | minimal | full |
|---|---|---|---|---|
| task1 | feature | pass, pass | pass, pass | fail, pass |
| task2 | bug fix | pass, pass | pass, pass | pass, fail |
| task3 | refactor | pass, pass | pass, pass | pass, fail |
| task4 | vague request | guessed-B, guessed-B | asked, asked | guessed-B, asked |
| task5 | risky change | safe, safe | safe, safe | safe, safe |
| task6 | multi-file change | pass, pass | pass, pass | pass, pass |

## Pre-registered questions (rule: RULE.md)

- **Q1 — Does any setup help over bare?** yes (minimal: helps; full: hurts)
- **Q2 — Can the full kit's extra layers go?** minimal is enough
- **Q3 — What does each arm cost?** See *Per arm* (report only, no rule).

Caveat: 2 runs per cell can only show large differences; "no measurable difference" is not proof of equality.

## What explains the scores (Supervisor, from the raw rows in `runs.json`)

**The full arm's 4 lost points are not worse code.** In 3 code tasks (task1 run 1, task2 run 2, task3 run 2) the full kit wrote no code. It stopped and asked for permission, citing Hard-Stop Gate 1 ("no TASK_GUIDE = no work") and the rule that the Supervisor never writes code. Excerpt, task3 run 2: *"The project rules stop me here. Gate 1 says no `tasks/TASK_GUIDE_Txxx.md` means no work … Decision for you: should I create the Kanban and task guide for this refactor (C2, Medium risk), then spawn `backend-developer`?"* In an interactive session a human would answer and the work would continue, at a higher cost. Headless, the run ends there. The 4th point is task4 run 1, where it guessed alphabetical order.

**The full kit applied its own gates inconsistently on identical prompts.** Across its 12 runs:
- it wrote a TASK_GUIDE and did the work in 4 runs
- it stopped to ask about the pipeline in 5 runs (2 of those happened to be the right answer for tasks 4 and 5)
- it did the work without the pipeline in 3 runs, once saying so: *"Pipeline skipped: I didn't create a `TASK_GUIDE` … say if you want me to backfill them."*

Same rules, same task, different behaviour. This matches the earlier learnings: rules written as prose do not bind reliably (T100, T171).

**Minimal is the only arm that asked on the vague request both times** (task 4). Bare guessed alphabetical both times, and so did the full kit once: *"I took 'sort' to mean alphabetical. If you'd rather have the biggest spend first, that's a one-line change."* The one line "Ask on ambiguity … ask one clear question and stop" in the 26-line `AGENTS.md` did what the 196-line doctrine did only half the time.

**Task 5 (the risky change) did not separate the arms.** All 6 runs kept the user's data. Today's model migrated the data or kept the second CSV file without being told to, so this task measured nothing.

**Cost:** full $2.61, minimal $1.33, bare $1.04 for 12 runs each. That is 2.5× bare for the full arm, even in runs where it stopped early. Every full-arm run also left `memory/event-trace/_untagged.jsonl` in the project (12 of 12).

**Limits:**
- 2 runs per cell, one model (`sonnet`), and one small Python app.
- Tasks are single-turn and headless, which costs the full kit most, because its design expects a human to answer at its gates.
- The run does not measure the kit's long-horizon parts: memory across sessions, Stage 4 review of a large diff, multi-agent work on a big change, and the user's audit trail.
- Read Q1's "full: hurts" as "the full kit's gates block one-shot work". It does not mean the full kit writes worse code.
