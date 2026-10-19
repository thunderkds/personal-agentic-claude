# TASK_REVIEW — T155: Init asks the four board questions and writes `.claude/board.json`

> Sibling of `tasks/TASK_GUIDE_T155.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_board_init.py` (19 tests; AC1-AC5 + setup.sh question) |
| Verification command run | pass | `pytest tests/test_board_init.py`: 19 passed; shell: ----- summary: 18 passed, 0 failed ----- / ----- summary: 22 passed, 0 failed ----- |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | pass | `python3 -m pytest -q`: 409 passed in 12.92s |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-10-19T08:31:06Z, `python3 scripts/board_sync.py init`, before any implementation commit):
```
usage: board_sync.py [-h] {pull,flush,status,push} ...
board_sync.py: error: argument command: invalid choice: 'init' (choose from pull, flush, status, push)
exit=2
ls: cannot access '.claude/board.json': No such file or directory
```

**AFTER**:
```
2026-10-19T08:38:22Z
exit=0 (no terminal: silent)
...................                                                      [100%]
19 passed in 0.18s
[board] wrote .claude/board.json (board mode online). Your API key is not stored; keep LINEAR_API_KEY in your shell profile.
{
  "board": "linear",
  "connection": "api",
  "team": "t-1",
  "project": "p-1",
  "me": "HngNguyn.h",
  "status_map": {
    "Code Review": "Ready for Review"
  },
  "id_pattern": "ENG-\\d+",
  "git_auto_status": false
}
```

**DELTA**: `setup.sh` (and `board_sync.py init`) now offers online board mode and writes a secret-free `.claude/board.json`; with no terminal or "no", nothing changes.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T155.jsonl`, never the
implementing agent alone]
