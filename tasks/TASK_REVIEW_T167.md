# TASK_REVIEW — T167: Site tables never scroll sideways — fit on desktop, stacked cards on phones

> Sibling of `tasks/TASK_GUIDE_T167.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (Supervisor, 2026-10-20T10:58:08+07:00, `site/index.html` @ `feat/t165-site-scan-first`, served at http://127.0.0.1:8080/, headless Chrome DevTools emulation; each entry is `[section, wrap clientWidth, table scrollWidth, overflow-x]` for every `.table-wrap` that scrolls):

```
1280px BRANCH overflowing wraps closed=[["hooks",639,716,"auto"]] open=[["hooks",639,716,"auto"]]
375px BRANCH overflowing wraps closed=[["update-flow",341,640,"auto"],["hooks",341,716,"auto"],["agent-focus",341,640,"auto"],["packs",341,640,"auto"],["providers",341,640,"auto"],["repository-layout",341,640,"auto"],["memory-system",341,640,"auto"],["options",341,640,"auto"]] open=[["update-flow",341,640,"auto"],["hooks",341,716,"auto"],["agent-focus",341,640,"auto"],["packs",341,640,"auto"],["providers",341,640,"auto"],["repository-layout",341,640,"auto"],["memory-system",341,640,"auto"],["options",341,640,"auto"]]
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
