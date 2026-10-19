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
| Negative cases hold | pass | at /verify: my own, unassigned and me-unset review rows still block; a forged title cannot pass as mine or as a teammate; the real harness push was blocked with my review open |
| verify | pass | /verify 2026-10-19 on an isolated copy (T161 + T164) with a stub Linear board, me=HungN. Merge gate fed a push event: only Bob's ENG-181 In Review -> allowed, stderr `teammates' Ready for Review tasks, not checked here: ENG-181`; + my ENG-182 -> block `missing Stage 5 verify evidence: ENG-182 (no evidence row)` (ENG-181 only noted); unassigned ENG-183 -> block; Bob's title forged `x | @HungN` -> rendered escaped, still Bob's, allowed; `me` unset -> every row checked, ENG-181 blocks with both safe-side notes; me=`hungn` (case) -> ENG-182 still blocks. Real harness (`claude -p` in the copy, local bare remote): push with only Bob's review open succeeded (remote main ad93fcc); push with my ENG-182 in review blocked, remote unchanged — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | code-review + security-review on feat/online-board...feat/t161-review-filter (4 files) plus callers (gate main(), my_blocking_tasks users); reports `reports/code-review_feat-t161-review-filter_20261019T222011.html`, `reports/security-review_feat-t161-review-filter_20261019T222011.html` |
| Full smoke suite still green (no regression) | ☑ pass (implementer; reviewer to confirm) | `python3 -m pytest -q tests .claude/hooks/tests` (worktree root, exit read directly) → exit=0, `1375 passed, 25 subtests passed in 29.10s` (1364 before + 11 new) |
| **UI: Visual regression (diff or verdict pasted)** | N/A | backend task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | backend task, no UI |
| **UI: Responsiveness at target viewports** | N/A | backend task, no UI |

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

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T161 via the active-task state file (`memory/event-trace/T161.jsonl`).
