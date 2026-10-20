# TASK_REVIEW — T169: Writing Principles (ASD-STE100) for text a human reads only

> Sibling of `tasks/TASK_GUIDE_T169.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: Captured 2026-10-20T05:00:52Z, before any implementation commit. Docs change, so BEFORE is the prior state.

Command: `grep -n "Writing Principles" CLAUDE.md agents/*.md AGENTS.md .cursor/rules/agent-base.mdc` -> no output, exit 1.

Prior `CLAUDE.md` Response Standard bullet (line 35, verbatim):
> - Write for a reader who hasn't followed the project, above all when asking them to decide: plain words; a task ID or internal term gets a few words saying what it is; technical depth only when asked.

Prior `CLAUDE.md` section order: `## Karpathy Engineering Principles` (line 109) is followed directly by `## Code Naming Conventions` (line 127). `AGENTS.md` and `.cursor/rules/agent-base.mdc` list only the 4 Karpathy names.

AC 9 token_meter BEFORE (`python3 scripts/token_meter.py --current --json`, main checkout, this implementer session, not a baseline of a Supervisor session): calls 44, spend_usd 3.853, context_now 127710, calls_over_150k 0. The AFTER row is left for the Supervisor.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
