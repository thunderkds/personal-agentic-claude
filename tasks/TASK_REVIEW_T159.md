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
| verify | pass | /verify 2026-10-19 on an isolated copy of feat/t159-board-create against a stateful stub Linear (shim rewrites api.linear.app): `create --guide draft.md` -> `[board] created ENG-5: tasks/TASK_GUIDE_ENG-5.md written`, rc=0; Linear got issueCreate {teamId t1, projectId p1, assigneeId u1 (viewer), priority 2, labelIds [L1 reused case-insensitively, L12 created for risk:medium]}; forged `☑ pass` Evidence row vacated in the cache; `pull` renders `ENG-5 ... C2, Risk: Medium, P1`; `update --guide ENG-5` (and `eng-5`) round-trips an edit; offline -> rc=1 `cannot reach Linear ... a create cannot be queued; nothing was written`, tasks/ unchanged, no .board/; bad key rc=1, key not echoed; no key rc=2; missing Risk/Priority rc=2; board ID `../../x` -> rc=1, no file; read-back 503 -> guide from the draft, warned; local mode rc=2 with 0 requests — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | code-review + security-review on feat/online-board...feat/t159-board-create (7 files) plus callers (render.guide_files, write_atomically, main error handling); reports `reports/code-review_feat-t159-board-create_20261019T174452.html`, `reports/security-review_feat-t159-board-create_20261019T174452.html` |
| Full smoke suite still green (no regression) | pass | see Verification row; one obsolete assertion in `tests/test_board_sync_pull.py` updated (stubs now checked on `BoardAdapter`) |
| **UI: Visual regression (diff or verdict pasted)** | N/A | backend CLI task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | backend CLI task, no UI |
| **UI: Responsiveness at target viewports** | N/A | backend CLI task, no UI |

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

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T159 via the active-task state file (`memory/event-trace/T159.jsonl`).
