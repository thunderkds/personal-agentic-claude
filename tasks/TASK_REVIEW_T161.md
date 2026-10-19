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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
