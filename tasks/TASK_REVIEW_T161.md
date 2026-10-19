# TASK_REVIEW — T161: Online mode: a teammate's Ready for Review task no longer blocks my push

> Sibling of `tasks/TASK_GUIDE_T161.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass (implementer; reviewer to confirm) | `tests/test_merge_gate_review_filter.py` — 11 tests: AC1 (`test_mine_blocks_teammate_is_named_in_a_note`, `test_only_teammate_review_row_lets_push_through`), AC2 (same + case-insensitive `me`), AC3 (`me` missing, not a board render, two assignee fields), AC4 (`test_unassigned_review_row_is_checked`), AC5 (`test_local_mode_checks_every_row_exactly_as_today`), fail-closed (`test_filter_exception_checks_every_row`), forged `\| @alice` title. Red before the change: `6 failed, 5 passed in 1.10s`; after: `24 passed in 3.08s` (with T157's file) |
| Verification command run | ☑ pass (implementer; reviewer to confirm) | The guide's command names `tests/test_merge_gate_my_tasks.py`, which does not exist (the file is `.claude/hooks/tests/test_merge_gate_my_tasks.py`): as written it prints `no tests ran in 0.00s`, exit 4. Corrected path, `python3 -m pytest -q tests/test_merge_gate_review_filter.py .claude/hooks/tests/test_merge_gate_my_tasks.py .claude/hooks/tests` → exit=0, `876 passed, 25 subtests passed in 18.47s` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass (implementer; reviewer to confirm) | `python3 -m pytest -q tests .claude/hooks/tests` (worktree root, exit read directly) → exit=0, `1375 passed, 25 subtests passed in 29.10s` (1364 before + 11 new) |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on `feat/t161-review-filter` at `65c0bc4` (no implementation commit yet).
Harness: a temp copy of `.claude/hooks` + `scripts/board_sync.py`, `.claude/board.json` online
(`board: fake`, `me: alice`), fake board with one task `ENG-181` in `In Review` assigned to `bob`
and no evidence; the gate fed `{"tool_name": "Bash", "tool_input": {"command": "git push"}}`.

```
$ date -u +%Y-%m-%dT%H:%M:%SZ && git rev-parse --short HEAD && python3 <scratchpad>/demo_t161.py /home/hungnguyenhuu/workspace/pets/wt-t161
2026-10-19T15:15:10Z
65c0bc4
exit: 0
stdout: {"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • Tasks in Ready for Review missing Stage 5 verify evidence: ENG-181 (no evidence row)\nComplete Stage 4 review and Stage 5 verify first.\n  Note: if a task above is missing its trace record rather than its evidence row, attribute your Bash calls by writing the active-task state file first: ... (attribution remedy elided)"}
stderr: (empty)
```

Today the teammate's (`bob`'s) unverified Ready for Review row blocks `alice`'s push.

**AFTER**: same harness, after the implementation (uncommitted working tree on top of `9394477`):

```
$ date -u +%Y-%m-%dT%H:%M:%SZ && python3 <scratchpad>/demo_t161.py /home/hungnguyenhuu/workspace/pets/wt-t161
2026-10-19T15:18:10Z
exit: 0
stdout: (empty — push allowed)
stderr: [hook:pre_bash] teammates' Ready for Review tasks, not checked here: ENG-181
```

**DELTA**: In board mode `online`, a developer can push while a teammate's Ready for Review task lacks verify evidence (the teammate's task is named in a note); their own and unassigned Ready for Review tasks still block, and local mode is unchanged.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
