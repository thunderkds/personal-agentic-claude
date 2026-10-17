# TASK_REVIEW — T144: Stage 4 warns when a task's diff outgrows its declared Complexity

> Sibling of `tasks/TASK_GUIDE_T144.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_lane_check.py: `9 passed in 0.44s` (FITS, files budget, unpredicted, Gate 2, missing guide, no Complexity, bookkeeping exclusion, binary, rename) |
| Verification command run | pass (new tests; fix round 1: `python3 -m pytest tests/test_lane_check.py -q` -> `10 passed in 0.61s`, adds three-dot base-advance test) | `tests/test_lane_check.py` 9 passed; full suite `5 failed, 1045 passed` - the 5 failures are memory-budget tests that fail identically on the base branch (`5 failed, 1036 passed` before my change) |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `feat/t144-t145-t148-t149...feat/t144-lane-check`: scripts/lane_check.py, tests/test_lane_check.py, skills/code-review/SKILL.md, PROJECT_SPEC.md, MANIFEST; caller memory_slice.table_paths |
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

**BEFORE**:

```
$ date -u; python3 scripts/lane_check.py tasks/TASK_GUIDE_T144.md main..HEAD; python3 -m pytest tests/test_lane_check.py -q
Sat Oct 17 05:09:13 AM UTC 2026
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t144/scripts/lane_check.py': [Errno 2] No such file or directory


no tests ran in 0.00s
```

**AFTER**: `python3 -m pytest tests/test_lane_check.py -q` -> `9 passed`. Calibration run (SC7, merge-base diff of each merged branch, T135 has no merge commit, skipped; T133's PR bundled T132/T133 so it is over-counted):

```
T128 lane: C1, 2 files, 181 lines, FITS
T129 lane: C1, 5 files, 115 lines, FITS
T130 lane: C1, 2 files, 109 lines, FITS
T131 lane: C1, 3 files, 52 lines, FITS; unpredicted: tasks/TASK_GUIDE_T131.md
T132 lane: C1, 3 files, 51 lines, FITS
T133 lane: C1, 10 files, 460 lines, EXCEEDS (files 10 > 6; lines 460 > 250); unpredicted: .clau
T136 lane: C2, 8 files, 203 lines, FITS; unpredicted: skills/bugfix/SKILL.md, tasks/TASK_GUIDE_
T137 lane: C2, 11 files, 394 lines, FITS; unpredicted: tests/test_one_command_menu.sh, tests/te
T138 lane: C1, 2 files, 117 lines, FITS
```

Budgets chosen (table at top of scripts/lane_check.py): C0 (2 files, 30 lines), C1 (6, 250), C2 (14, 500), C3 none. Initial guesses C1 (4,150) / C2 (10,500) exceeded 4 of 9; raised C1 and C2 files so 1 of 9 exceeds (the bundled T133 PR). C0 has no sample in T128-T138; kept as a guess.

**DELTA**: The Stage 4 reviewer gets one line saying whether the diff fits the declared Complexity and predicted files.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Stage 4 — code-review (Supervisor, 2026-10-17)

Scope: `feat/t144-t145-t148-t149...feat/t144-lane-check` (5 files) plus its one caller dependency, `memory_slice.table_paths`. lane_check on itself: `lane: C1, 5 files, 245 lines, FITS; unpredicted: MANIFEST` (justified: installed projects need the script the new code-review step runs). Startup reads line present and complete for the three Permanent-Rule reads.
- **P2 (100) — fixed in round 1, `c971f20`**: the SKILL told reviewers to run `<base>..HEAD`; `git diff A..B` = `git diff A B`, so once the integration branch advances, other tasks' changes are counted (reversed). Seen live: a two-dot diff of T148 against the integration branch listed PROJECT_KANBAN.md, MEMORY.md and TASK_REVIEW_T146.md. Now `<base>...HEAD`, and `test_three_dot_ignores_base_advancing` covers it → `10 passed`.
- P0/P1: none. Over-engineering: none. The single budget table, warn-only exit 0, and reuse of `table_paths` all match the guide.
- Open (not a finding): the C0 budget is uncalibrated, because there was no C0 sample in T128–T138.
