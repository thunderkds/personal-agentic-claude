# TASK_REVIEW — T131: The Agent focus section says "we apply A to save B"

> Sibling of `tasks/TASK_GUIDE_T131.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (verbatim T130 `#agent-focus` table, `site/index.html` at 3d76f9b, captured 2026-09-25 before any implementation commit):

```html
<div class="table-wrap">
<table>
<thead><tr><th>Mechanism</th><th>What it does</th></tr></thead>
<tbody>
<tr><td>Memory slice</td><td>The spawn prompt pastes only the <code>memory/MEMORY.md</code> index lines that name the task's files, dependencies or ID, capped at 30 lines / 4,000 characters (lines with the fewest matches are dropped first and the header says how many)</td></tr>
<tr><td>Startup reads</td><td>The spawn prompt lists what the agent must read first — <code>PROJECT_SPEC.md</code>, its TASK_GUIDE and its role guide — and the agent ends its report with a <code>Startup reads:</code> line naming what it read</td></tr>
<tr><td>Response Standard</td><td>Replies lead with the answer and stay short, but code, exact error text, file paths, commands and security warnings are quoted verbatim. The audit trail — board rows, guides and their Evidence, decisions, commit messages — stays fully detailed, and a report points to evidence by <code>path:line</code> instead of pasting logs</td></tr>
<tr><td>Stage 4 review</td><td><code>code-review</code> runs an over-engineering reviewer on any diff that adds a function, class, module, dependency or config option, and compares the agent's <code>Startup reads:</code> line with its spawn prompt — a missing required read is a P1 process finding</td></tr>
<tr><td>Measuring</td><td>A claim that a change saves or costs tokens is measured from session transcripts before it is kept (DDR-0009), never estimated by eye. No savings figure is published here</td></tr>
</tbody>
</table>
</div>
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
