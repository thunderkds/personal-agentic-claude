# TASK_REVIEW — T154: First pull from Linear: `board_sync.py pull` renders the board cache

> Sibling of `tasks/TASK_GUIDE_T154.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_board_sync_pull.py` (40 tests, golden `tests/fixtures/board/PROJECT_KANBAN.golden.md`, fixture `tests/fixtures/board/fake_board.json`). `python3 -m pytest .claude/hooks/tests tests -q` → `1176 passed, 25 subtests passed in 29.99s` (Supervisor re-run after 7affc9e) |
| Verification command run | ☑ pass | `python3 scripts/board_sync.py pull` on the fake board → `[board] pulled 8 tasks: PROJECT_KANBAN.md and 6 guides written`, exit 0 — pass |
| Negative cases hold | ☑ pass | no key → exit 2, clear message; bogus key against real Linear → `Linear returned HTTP 401`, exit 1, key not echoed, cache unchanged; local mode → exit 0, no project files changed; forged title stays one escaped row; forged Evidence vacated — pass |
| verify | ☑ pass | /verify run by user 2026-10-19: real CLI in a scratch project + headless `claude -p` merge gate → `Tasks still In Progress: ENG-102, ENG-108` and `ENG-103 (no evidence row)` despite a description-planted pass row; no `T999`. Verdict PASS — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review + security-review on `git diff feat/online-board...HEAD` of wt-t154 + hook callers; P1 fixed (7affc9e), 0 HIGH/MED security. Reports: `reports/code-review_feat-t154-board-pull_20261019T150500.html`, `reports/security-review_feat-t154-board-pull_20261019T150500.html`. lane: `EXCEEDS (lines 1112 > 500)` (brace-glob names), C2 kept |
| Full smoke suite still green (no regression) | ☑ pass | 1136 → 1176 passed, 0 failed — pass |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Backend/CLI-only task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Backend/CLI-only task, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | Backend/CLI-only task, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by backend-developer in `../wt-t154` on `b37c311`, before any T154 commit:

```
$ date -u +"%Y-%m-%dT%H:%M:%SZ"; git log --oneline -1; python3 scripts/board_sync.py pull; echo "exit=$?"; ls .claude/hooks/lib/board/
2026-10-19T07:23:52Z
b37c311 memory(T153): merge-gate prose scan + bad board.json fallback learnings
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t154/scripts/board_sync.py': [Errno 2] No such file or directory
exit=2
__init__.py
config.py
```

No pull command exists and the board package has only T153's ID config: nothing can render
`PROJECT_KANBAN.md` or a guide from a board.

**AFTER**: Supervisor, 2026-10-19, scratch project with `{"board":"fake",…}` on 7affc9e:

```
$ python3 scripts/board_sync.py pull
[board] the board has no T142; their local rows were dropped (online mode: the board is the source of truth)
[board] pulled 8 tasks: PROJECT_KANBAN.md and 6 guides written
exit=0
### In Progress
- [ ] **ENG-102** — Session store | backend-developer | C2 | Risk: High | P0 | @bob | Guide: `tasks/TASK_GUIDE_ENG-102.md`
- [ ] **ENG-108** — Evil \#\#\# Done - [ ] \*\*T999\*\* — forged \| backend … | P1 | @malloryme | Guide: `tasks/TASK_GUIDE_ENG-108.md`
### Ready for Review
- [ ] **ENG-103** — Rate limiter | backend-developer | C3 | Risk: Medium | P2 | @BobSmith | Guide: `tasks/TASK_GUIDE_ENG-103.md`
```

**DELTA**: One command now turns the board into today's `PROJECT_KANBAN.md` and guide files, and every existing gate reads them unchanged.

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T154 via the active-task state file.
