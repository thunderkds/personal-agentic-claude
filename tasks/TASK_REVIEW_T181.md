# TASK_REVIEW — T181: README and site describe the two tracks, the Debate step and `[auto]`

> Sibling of `tasks/TASK_GUIDE_T181.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (docs change: verbatim prior content, captured 2026-10-27 before any change; `README.md` is 75 lines):

`README.md` lines 1-9:

```markdown
# Easy Kit

**v2.1.0** — a general-purpose multi-agent supervisor framework for Claude Code, Codex, and Cursor.
Install once, deploy into any project: agent definitions, skills, hooks, and templates that drive a
5-stage agentic pipeline
(clarify → brainstorm → plan → parallel execution in worktrees → review → verify/ship), enforced by
pipeline hooks rather than prompt reminders — e.g. `pre_agent_step_limit.py` blocks runaway tool-call
loops (default 90 calls), and `post_agent_move_to_review.py` is a deliberately inert reminder-only
hook since T044 (it does not move any KANBAN row or reset any counter — see its docstring).
```

`site/index.html` lines 356-364 (end of `#what-you-get` and the start of the next section; there is no `#tracks` and no `href="#tracks"` in the file):

```html
    <rect x="10" y="506" width="300" height="50" rx="8"/>
    <text class="node-title" x="160" y="527" text-anchor="middle">Stage 5 · Integrate</text>
    <text class="node-out" x="160" y="545" text-anchor="middle">verify, merge, release plan</text>
  </g>
</svg>
</section>

<section id="install">
<h2>Install</h2>
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
