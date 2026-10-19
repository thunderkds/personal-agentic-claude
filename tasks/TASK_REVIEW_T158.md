# TASK_REVIEW — T158: Decision Log: decisions go to one shared board document and reach every developer

> Sibling of `tasks/TASK_GUIDE_T158.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_board_decisions.py` (35 tests, AC1-AC6); `tests/test_memory_slice.py` unchanged |
| Verification command run | pass | `python3 -m pytest tests/test_board_decisions.py tests/test_memory_slice.py -q` (2026-10-19): `65 passed in 1.06s` |
| Negative cases hold | ☑ pass | Real CLI vs stub Linear: forged text (newlines, `### Forged heading`, `**Files**: setup.sh`, fake end marker) → one escaped line, 1 heading in section; key in text → `[redacted]`, outbox 0 `lin_api`; Documents query rejected → `Decision Log not read (...); memory/decisions.md left as is`, KANBAN still pulled, file hash unchanged; dead proxy → queued `1 unsynced`, flush delivers; write landed + reply lost → replay, entry present exactly once; wrong key → exit 1, kept queued; `decide ../etc` → `not a task ID`, exit 2 — pass |
| verify | ☑ pass | /verify by user 2026-10-19. alice `decide` → document created; hung `pull` → local decisions.md prefix byte-identical, board section appended; `wake` → `3 new decisions from teammates since your last session`, second wake silent, own entries never counted; spawn memory slice shows only ENG-170 entries. Round 1 defect: double escaping (`\\\#`) → fixed 2c92707; re-run: `Retry \(3x\) ...` single-escaped in cache and slice, two pulls same hash `252c0bf0` — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review + security-review on `git diff feat/online-board...HEAD` of wt-t158 (+ callers); P1 fixed 0446f7c (Decision Log failure broke the task pull); P1 process (Startup reads skimmed, re-read); P2 untrusted label → T164; lane EXCEEDS 792>500 (warn) — pass |
| Full smoke suite still green (no regression) | pass | `python3 -m pytest -q`: `425 passed in 17.29s` (subset, tests/ only; superseded by the next row) (one pre-existing test, `test_unbuilt_operations_raise_not_implemented`, edited: it listed T158's two operations as unbuilt) |
| Decision Log read failure does not fail the pull (review P1) | pass | `test_unreadable_decision_log_does_not_fail_the_pull`. Red before the fix: `[board] pull failed: Linear rejected the query (GraphQL error). The board cache was left unchanged.` / `1 failed, 35 deselected`. Green after: `1 passed, 35 deselected` |
| Full suite, both folders | pass | `python3 -m pytest -q tests .claude/hooks/tests`: `1291 passed, 25 subtests passed in 39.24s` |
| Single escaping layer end to end (verify defect) | pass | `test_pull_does_not_escape_twice`. Red before: the cache line held `\\\#\\\#\\\# x \\\| y` (triple backslash) instead of the document line's `\#\#\# x \| y`; `1 failed, 36 deselected`. Green after: `37 passed` in `tests/test_board_decisions.py`. Fix: `parse_decision_lines` unescapes, `format_decision` escapes once, `memory_slice.py` formats through `format_decision` |
| Full suite, both folders (after verify fix) | pass | `python3 -m pytest -q tests .claude/hooks/tests`: `1292 passed, 25 subtests passed in 49.65s` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | CLI/hooks-only task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | CLI/hooks-only task, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | CLI/hooks-only task, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-19T08:31:44Z, before any implementation commit; board mode `fake`, `me` alice, fresh temp project):

```
$ python3 -c "import sys; sys.path.insert(0,'scripts'); import board_sync; sys.exit(board_sync.main(['decide','ENG-170','Retry 3 times'], root='<tmpproject>'))"
usage: -c [-h] {pull,flush,status,push} ...
-c: error: argument command: invalid choice: 'decide' (choose from pull, flush, status, push)
exit=2
$ python3 -m pytest tests/test_board_decisions.py tests/test_memory_slice.py -q
ERROR: file or directory not found: tests/test_board_decisions.py
no tests ran in 0.00s
```

**AFTER** (2026-10-19T08:34:56Z, same command, same project; the fake board is rebuilt from its file on every CLI run, so the persisted entry is shown by the tests):
```
[board] decision recorded for ENG-170
exit=0
$ python3 -m pytest tests/test_board_decisions.py tests/test_memory_slice.py -q
65 passed in 1.06s
```
`test_decide_appends_exact_format` asserts the stored line `- <date>  Retry 3 times  (from ENG-170, by alice)`.

**DELTA**: A developer can record a decision against a task on the shared board (queued offline), and teammates' decisions appear in `memory/decisions.md`, in `wake`'s count and in the spawned task's memory slice.

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T158 via the active-task state file.
