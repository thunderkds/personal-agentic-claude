# TASK_REVIEW — T156: Push + outbox: milestone comments and Ready for Review reach the board, offline writes arrive later exactly once

> Sibling of `tasks/TASK_GUIDE_T156.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-19T07:43:08Z in `wt-t156`, before any implementation commit):

```
$ date -u: 2026-10-19T07:43:08Z
$ python3 scripts/board_sync.py push status ENG-1 ready-for-review
usage: board_sync.py [-h] {pull}
board_sync.py: error: argument command: invalid choice: 'push' (choose from pull)
exit=2
$ python3 scripts/board_sync.py status
usage: board_sync.py [-h] {pull}
board_sync.py: error: argument command: invalid choice: 'status' (choose from pull)
exit=2
```

**AFTER** (fake board, `git_auto_status: true`, 2026-10-19T07:45:53Z):

```
date -u: 2026-10-19T07:45:53Z
$ board_sync.py push comment ENG-1 green ok
[board] pushed comment for ENG-1
exit=0
$ board_sync.py push status ENG-1 ready-for-review
[board] pushed status for ENG-1
exit=0
$ board_sync.py push status ENG-1 done
[board] git_auto_status is on: the git integration moves done; only todo and ready-for-review are pushed
exit=2
$ board_sync.py push comment ENG-1 chatter x
[board] milestone must be one of: started, red, green, review, verify, merged, blocked, question
exit=2
$ board_sync.py status
0 unsynced
exit=0
```

**DELTA**: An agent can push a Ready for Review status and milestone comments to the board, and they queue in `.board/outbox.jsonl` and replay exactly once when the board is unreachable.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T156.jsonl`, never the
implementing agent alone]
