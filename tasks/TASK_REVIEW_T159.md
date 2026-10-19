# TASK_REVIEW — T159: Planning creates the board issue with the full guide as its description

> Sibling of `tasks/TASK_GUIDE_T159.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_board_create.py` (33 tests, AC1-AC4); `python3 -m pytest tests/test_board_create.py -q` -> `33 passed in 0.09s` |
| Verification command run | pass | `python3 -m pytest -q tests .claude/hooks/tests` exit=0, tail: `1346 passed, 25 subtests passed in 29.96s` |
| Negative cases hold | pass | missing fields refused (exit 2), offline/auth/rejected create exit 1 with no file and no outbox, local mode non-zero, unsafe board ID writes nothing |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | pass | see Verification row; one obsolete assertion in `tests/test_board_sync_pull.py` updated (stubs now checked on `BoardAdapter`) |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-19T10:39:47Z in `/home/hungnguyenhuu/workspace/pets/wt-t159`, before any implementation commit:

```
$ python3 scripts/board_sync.py create --guide draft.md
usage: board_sync.py [-h] {pull,flush,status,decide,init,push} ...
board_sync.py: error: argument command: invalid choice: 'create' (choose from pull, flush, status, decide, init, push)
exit=2
```

**AFTER**: 2026-10-19T10:43:02Z, same command against a scratch project with the fake board:

```
$ python3 scripts/board_sync.py create --guide draft.md
[board] created ENG-1: tasks/TASK_GUIDE_ENG-1.md written
exit=0
```

**DELTA**: Stage 2 in board mode can create the board issue from a draft guide and get the board-assigned ID plus the guide cache in one command.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T159.jsonl`, never the
implementing agent alone]
