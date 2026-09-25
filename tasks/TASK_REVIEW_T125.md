# TASK_REVIEW — T125: Focused handoff — a spawned agent gets the memory lines its task touches, not the whole index

> Sibling of `tasks/TASK_GUIDE_T125.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured 2026-09-25T05:51:32Z at `598cc02`, before any T125 implementation commit):

1. `skills/craft-spawn-prompt/SKILL.md` element 4, verbatim as it exists at `598cc02` (line 33):

   > \| 4 \| Memory reference \| The **path** `memory/MEMORY.md`, with an instruction to read it in full. Do **not** paste its contents \| same \|

2. Baseline row, `docs/token-focus-finding-2026-09-25.md` § 3 (14 spawns, medians):

   > \| **Read before the first Edit/Write** \| **16.8k tokens over 8 calls** \| — most-read file before
   > the first edit: `memory/MEMORY.md` (6 of 14; 41k chars ≈ 12k tokens).

3. The slice command does not exist, and the spawn hook says nothing about a missing slice:

```
$ date -u; git rev-parse --short HEAD
2026-09-25T05:51:32Z
598cc02
$ python3 scripts/memory_slice.py tasks/TASK_GUIDE_T125.md; echo exit=$?
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t125/scripts/memory_slice.py': [Errno 2] No such file or directory
exit=2
$ printf %s '{"tool_name":"Agent","tool_input":{"prompt":"Task ID: T125\nRead tasks/TASK_GUIDE_T125.md"}}' | python3 .claude/hooks/pre_agent_validate_guide.py; echo exit=$?
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Advisory warning (not blocking):\n  \u2022 T125 declares 'Depends on: T124', which is currently 'Ready for Review' (not Done). Confirm this is intentional (e.g. parallel stub work) before proceeding.\n  \u2022 T125's Demonstration BEFORE field is blank. Capture it BEFORE your first implementation commit \u2014 a BEFORE taken after the change is not a BEFORE, and there is no N/A path."}}
exit=0
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
