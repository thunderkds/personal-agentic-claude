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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
