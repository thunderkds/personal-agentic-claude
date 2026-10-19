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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_board_push.py` (+ updated `tests/test_board_sync_pull.py`). `python3 -m pytest .claude/hooks/tests tests -q` → `1228 passed, 25 subtests passed in 45.43s` (Supervisor re-run on 86dc365 with the 163ea78 memory index) |
| Verification command run | ☑ pass | `board_sync.py push comment ENG-101 started …` → `pushed comment`; offline → `queued comment for ENG-101 (1 unsynced)`; `status` → `2 unsynced` — pass |
| Negative cases hold | ☑ pass | git_auto_status refuses in-progress (exit 2); bad milestone / `../x` / empty text exit 2; key typed into text stored as `[redacted]`, 0 occurrences in `.board/`; `.board/` gitignored; offline flush keeps all (exit 1); 401 keeps all (exit 1, `check LINEAR_API_KEY`) — pass |
| verify | ☑ pass | /verify by user 2026-10-19: first run FAIL (401 dropped queued writes) → fixed 86dc365 → Supervisor re-ran the same probes against the real Linear endpoint: queue kept, exit 1, auth message, key never stored. Verdict PASS — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review + security-review on `git diff feat/online-board...HEAD` of wt-t156; P1 poison entry fixed 40a5f35, P2 marker + gitignore fixed 40a5f35, verify P1 (401 drop) fixed 86dc365; 0 HIGH/MED security. Reports: `reports/code-review_feat-t156-board-push_20261019T151000.html`, `reports/security-review_feat-t156-board-push_20261019T151000.html`. lane EXCEEDS (lines 726 > 500), C2 kept |
| Full smoke suite still green (no regression) | ☑ pass | 1176 → 1228 passed, 0 failed — pass |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | CLI-only task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | CLI-only task, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | CLI-only task, no UI |

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

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19T08:01–08:03Z, Bash calls attributed to T156 via the active-task state file.
