# TASK_REVIEW — T160: `wake` triages my new board tasks: propose priority, ask, then ready-or-investigate

> Sibling of `tasks/TASK_GUIDE_T160.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: captured by backend-developer in worktree `wt-t160` at HEAD `12048b9`, before any T160 implementation commit. `triage` does not exist, and the spawn hook lets a one-line guide through (advisories only, no `"decision": "block"`). The hook ran from a scratch copy of `.claude/hooks` with an `ENG-\d+` id_pattern and a one-line `tasks/TASK_GUIDE_ENG-171.md`.

```text
$ date -u; git rev-parse --short HEAD
2026-10-19T14:44:36Z
12048b9
$ python3 scripts/board_sync.py triage; echo exit=$?
usage: board_sync.py [-h]
                     {pull,flush,status,decide,init,create,update,push} ...
board_sync.py: error: argument command: invalid choice: 'triage' (choose from pull, flush, status, decide, init, create, update, push)
exit=2
$ cat tasks/TASK_GUIDE_ENG-171.md   # scratch project, board mode online, one-line guide
# ENG-171: Add dark mode
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Task ID: ENG-171
Guide: tasks/TASK_GUIDE_ENG-171.md"}}' | python3 .claude/hooks/pre_agent_validate_guide.py; echo exit=$?
[hook:pre_agent] memory-slice missing: Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none of the memory lines its task touches. Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste its output verbatim (craft-spawn-prompt element 4).
[hook:pre_agent] startup-reads missing: Spawn prompt names a TASK_GUIDE but has no `**Startup reads**` block, so the agent is not told to read PROJECT_SPEC.md, its guide and its role guide first (craft-spawn-prompt element 8).
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Advisory warning (not blocking):\n  \u2022 ENG-171's Demonstration BEFORE field is blank. Capture it BEFORE your first implementation commit \u2014 a BEFORE taken after the change is not a BEFORE, and there is no N/A path.\n  \u2022 Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none of the memory lines its task touches. Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste its output verbatim (craft-spawn-prompt element 4).\n  \u2022 Spawn prompt names a TASK_GUIDE but has no `**Startup reads**` block, so the agent is not told to read PROJECT_SPEC.md, its guide and its role guide first (craft-spawn-prompt element 8)."}}
exit=0
```

Non-executable part, verbatim prior content of `skills/wake/SKILL.md` Step 0 (8,119 bytes, no `references/` directory under `skills/wake/`):

> Run `python3 scripts/pull_moment.py wake` first (FR-009; no-op in `local` mode). Show any line it prints (`board unreachable — using cache (N unsynced)` or `⚠ N unsynced board writes — …`) atop the briefing and continue.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T160.jsonl`, never the
implementing agent alone]
