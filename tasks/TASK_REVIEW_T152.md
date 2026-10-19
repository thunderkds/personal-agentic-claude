# TASK_REVIEW — T152: `dirty_worktrees.py` finds the board from the repo root

> Sibling of `tasks/TASK_GUIDE_T152.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_dirty_worktrees.py::test_subfolder_run_finds_board (new, AC1; red before fix, green after); `13 passed in 0.56s` |
| Verification command run | pass | `python3 -m pytest tests/test_dirty_worktrees.py -q` -> `13 passed in 0.56s` (Supervisor re-run 2026-10-19) |
| Negative cases hold | pass | AC3: `test_sc5_not_a_git_repo` and `test_sc5_no_board` green; Supervisor by-hand: repo path with a space, run from a subfolder -> `T901 ... 0 modified, 1 untracked`, exit 0 |
| verify | ☑ pass | User-invoked `/verify` 2026-10-19 at the real surface (the script run by hand in the T152 worktree, commits `46ba2ad..e2cce6a`), one untracked file in `wt-t152`: repo root → `T152 /home/hungnguyenhuu/workspace/pets/wt-t152 0 modified, 1 untracked`; `docs/` → same line; `skills/wake/scripts/` → same line; pre-fix script from `docs/` → empty (the bug); outside any repo → empty, exit 0; after cleanup → empty. Note: a first probe used a `.tmp` file, which `.gitignore` hides — not a script defect — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 code-review 2026-10-19, `e219642...HEAD`: dirty_worktrees.py, test_dirty_worktrees.py; caller skills/wake/SKILL.md read (unchanged). lane_check: `lane: C0, 2 files, 15 lines, FITS`. Findings: P0 0 / P1 0 / P2 0 / P3 0. Startup reads line complete |
| Full smoke suite still green (no regression) | pass | `python3 -m pytest tests/ .claude/hooks/tests/ -q` -> 1100 passed, 25 subtests passed in 39.79s |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI — a CLI script |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI — a CLI script |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI — a CLI script |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-19T02:32:33Z, before any implementation commit, on branch `fix/t152-board-root`
with the script unchanged. Command: `python3 -m pytest tests/test_dirty_worktrees.py -q -k test_subfolder_run_finds_board`

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-19T02:32:33Z
$ python3 -m pytest tests/test_dirty_worktrees.py -q -k test_subfolder_run_finds_board
F                                                                        [100%]
=================================== FAILURES ===================================
________________________ test_subfolder_run_finds_board ________________________
...
>       assert run(docs).strip() == f"T901 {wt} 1 modified, 2 untracked"
E       AssertionError: assert '' == 'T901 /tmp/py..., 2 untracked'
E
E         - T901 /tmp/pytest-of-hungnguyenhuu/pytest-0/test_subfolder_run_finds_board0/wt901 1 modified, 2 untracked
tests/test_dirty_worktrees.py:108: AssertionError
=========================== short test summary info ============================
FAILED tests/test_dirty_worktrees.py::test_subfolder_run_finds_board - Assert...
1 failed, 12 deselected in 0.15s
```

Run from `docs/`, the script prints nothing: the bare `PROJECT_KANBAN.md` path resolves against cwd and misses the board.

**AFTER**:
```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-10-19T02:34:21Z
$ python3 -m pytest tests/test_dirty_worktrees.py -q -k test_subfolder_run_finds_board
1 passed, 12 deselected in 0.08s
```

**DELTA**: Running `dirty_worktrees.py` by hand from any subfolder now reports dirty In Progress worktrees instead of printing nothing.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
