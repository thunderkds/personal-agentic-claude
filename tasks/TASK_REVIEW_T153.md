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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T153.jsonl`, never the
implementing agent alone]
