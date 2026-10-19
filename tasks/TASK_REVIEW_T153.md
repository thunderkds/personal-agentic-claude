# TASK_REVIEW — T153: Task IDs come from board config, so hooks accept `T142` and `ENG-170` side by side

> Sibling of `tasks/TASK_GUIDE_T153.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_board_id_pattern.py` (30 tests: merge gate, register-on-write, spawn validator incl. path-unsafe IDs, resolve_task_id, memory_slice, token_meter, dirty_worktrees, bad-config fallback). `python3 -m pytest .claude/hooks/tests tests -q` → `1136 passed, 25 subtests passed in 43.86s` (Supervisor re-run 2026-10-19, after 5377ff0) |
| Verification command run | ☑ pass | Demonstration AFTER below: merge gate lists `T142, ENG-170`; spawn validator blocks missing `ENG-171` guide — pass |
| Negative cases hold | ☑ pass | No config → only `T\d+` (tests `*_without_config_*`); invalid JSON → one warning + `T\d+` fallback (seen live: `[board] ignoring …board.json: not valid JSON`); path-unsafe IDs dropped — pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review + security-review on `git diff feat/online-board...HEAD` of wt-t153 + direct callers; 0 P0/P1, P2 fixed (5377ff0), 0 HIGH/MED security. Reports: `reports/code-review_feat-t153-board-id-pattern_20261019T141600.html`, `reports/security-review_feat-t153-board-id-pattern_20261019T141600.html`. lane_check: `EXCEEDS (lines 787 > 500)` — vague guide Files table, C2 kept |
| Full smoke suite still green (no regression) | ☑ pass | 1106 baseline → 1136 passed, 0 failed — pass |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Backend/hook-only task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Backend/hook-only task, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | Backend/hook-only task, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by the implementing agent at base commit `b06653c`, before any T153 commit.
Script: copies `.claude/hooks` into a temp project, writes `.claude/board.json` =
`{"id_pattern": "ENG-\\d+"}` and a board with `T142` and `ENG-170` In Progress, then pipes a
`git push` event into the merge gate and an `Agent` event naming a missing
`tasks/TASK_GUIDE_ENG-171.md` into the spawn validator.

```
== date: 2026-10-19T05:10:15Z
== .claude/board.json: {"id_pattern": "ENG-\d+"}
== merge gate on 'git push':
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • Tasks still In Progress: T142\nComplete Stage 4 review and Stage 5 verify first.\n  Note: if a task above is missing its trace record ... (remedy text elided)"}

== spawn validator, prompt names missing tasks/TASK_GUIDE_ENG-171.md:
(exit 0; empty output = spawn allowed)
```

The merge gate does not see `ENG-170` (In Progress, but not listed), and the spawn validator lets
an agent start on `ENG-171`, a task with no guide (Hard-Stop Gate 1 not enforced for board IDs).
Baseline suite at the same commit: `1106 passed, 25 subtests passed in 19.77s`.

**AFTER**: same scenario, run by the Supervisor on 5377ff0:

```
== date: 2026-10-19T07:15:14Z
== .claude/board.json: {"id_pattern": "ENG-\d+"}
== merge gate on 'git push':
block
  • Tasks still In Progress: T142, ENG-170
== spawn validator, prompt names missing tasks/TASK_GUIDE_ENG-171.md:
block
[hook:pre_agent] Cannot spawn agent — missing TASK_GUIDE for: ENG-171. Run Stage 2 planning first to generate the guide(s) in tasks/.
```

**DELTA**: With `.claude/board.json` setting `id_pattern`, every gate now recognises board IDs like `ENG-170` next to `T142`, so Hard-Stop Gate 1 and the merge gate hold for board tasks.

**WITNESS**: Supervisor (main session), 2026-10-19T07:15Z, Bash calls attributed to T153 via the active-task state file.
