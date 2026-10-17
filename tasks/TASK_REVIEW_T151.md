# TASK_REVIEW — T151: The docs and site describe what T144, T145, T148 and T149 changed

> Sibling of `tasks/TASK_GUIDE_T151.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (non-executable change: verbatim prior text, captured 2026-10-17 before any implementation commit):

- `docs/claude-md/pipeline-stages.md:159`: "...verbatim: the `memory/MEMORY.md` index lines that name the guide's files, its `Depends on` tasks or its ID (T125). Then the fallback: ..."
- `docs/claude-md/pipeline-stages.md:171-175` (Stage 4 code-review): "Bound the review to the change's **blast radius** ... `code-review` also runs the Entry-Point Reachability Check (Phase 0.5) against the task's declared `Entry point:` field." (no lane_check mention)
- `docs/claude-md/pipeline-stages.md:231-235` (ship): "... `ship` **plans and de-risks** the release — it never auto-deploys; the operator executes the plan." (no approval / smoke-test mention)
- `site/index.html:531`: "<span class="tag tag-advise">advises</span> — appends every tool call to <code>memory/event-trace/&lt;task&gt;.jsonl</code>"
- `site/index.html:548`: "<strong>Memory slice</strong> — the spawn prompt pastes only the <code>memory/MEMORY.md</code> lines about the task's own files, capped at 30 lines / 4,000 characters"
- `site/index.html:655`: "...the <strong>memory slice</strong> — the index lines naming the task's files, dependencies or ID — and the agent reads the whole file only if its work reaches what the slice misses"
- `site/index.html:371-373`: "the kit's hooks are reconciled into it on install <em>and</em> on update, while your own permissions and your own hook entries are kept exactly as they are."
- `site/index.html:516-518`: "...including into one your project already has — and never touch your own permissions or hook entries. No manual merge step."

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
