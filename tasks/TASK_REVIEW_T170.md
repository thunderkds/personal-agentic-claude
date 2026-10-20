# TASK_REVIEW — T170: `resolve-question` skill

> Sibling of `tasks/TASK_GUIDE_T170.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: captured by common-infrastructure before the first implementation commit (branch head
`e1a6bb8`). Docs/skill-text task, so BEFORE is the guide's named command plus the verbatim prior
content of each file that changes.

```
2026-10-20T11:15:45Z
$ ls skills/resolve-question; grep -n "Question (if blocked)" agents/*.md
ls: cannot access 'skills/resolve-question': No such file or directory
grep exit=1
```

Prior report format, `agents/backend.md:118-122` (`frontend.md:117-121` same shape;
`common-infrastructure.md:112-116` adds `environment-ready` to Status; `qa.md:121-126` adds a
`Verdict:` line):

```
Agent: backend-developer
Task: T[NNN] — [short title]
Status: [in-progress | ready-for-review | blocked]
Changed files: [list]
Blockers / notes: [any]
```

Prior `CLAUDE.md:65` tail: `Cross-cutting (any stage, not tied to a single one): `compact-memory` (cold memory files), `compact-advisor` (live conversation health — see Self-monitoring rule above).`

Prior `skills/thinking-report/SKILL.md:3` args: `Args: session=<brainstorming|grilling|planning> task=<TASK_ID> branch=<branch-name>"`;
prior save line `:121`: `SAVE → reports/thinking-report_<branch-arg>_<YYYYMMDDTHHMMSS>.html`

Prior `site/index.html:582` (Any stage chips, no `resolve-question`):
`<span class="chip">strategy</span><span class="chip">teach</span><span class="chip">thinking-report</span><span class="chip">wake</span>`

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
