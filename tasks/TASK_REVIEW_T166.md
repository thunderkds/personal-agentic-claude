# TASK_REVIEW — T166: The Skills section shows a stage flow with skill chips

> Sibling of `tasks/TASK_GUIDE_T166.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (Supervisor, 2026-10-20, `site/index.html` on `feat/t165-site-scan-first` @ `b5b6199`) — verbatim `#skills` section:

```html
<section id="skills">
<h2>Skills (30)</h2>
<p class="lead">
  One inline instruction set loaded per invocation, grouped by which pipeline stage it belongs to.
</p>

<div class="skill-groups">
  <div class="skill-group">
    <h3>Stage 0.5 — Requirement Grilling / Brainstorming</h3>
    <ul><li>brainstorming</li><li>ideate</li></ul>
  </div>
  <div class="skill-group">
    <h3>Stage 1 — Environment &amp; Provider Setup</h3>
    <ul><li>git-guardrails-claude-code</li><li>map-codebase</li></ul>
  </div>
  <div class="skill-group">
    <h3>Stage 1.5 — Sub-Agent Architecture</h3>
    <ul><li>craft-agent</li></ul>
  </div>
  <div class="skill-group">
    <h3>Stage 2 — Intent Transformation</h3>
    <ul><li>grill-with-docs</li><li>to-issues</li></ul>
  </div>
  <div class="skill-group">
    <h3>Stage 3 — Parallel Execution via Isolation</h3>
    <ul><li>tdd</li><li>bugfix</li><li>diagnose</li><li>craft-spawn-prompt</li><li>migration-safety</li></ul>
  </div>
  <div class="skill-group">
    <h3>Stage 4 — Review</h3>
    <ul><li>blast-radius</li><li>code-review</li><li>html-report</li></ul>
  </div>
  <div class="skill-group">
    <h3>Stage 5 — Integration &amp; Verification</h3>
    <ul><li>ship</li><li>delivery-report</li></ul>
  </div>
  <div class="skill-group">
    <h3>Cross-cutting</h3>
    <ul>
      <li>compact-advisor</li><li>compact-memory</li><li>compound</li><li>compound-refresh</li>
      <li>learn</li><li>optimize</li><li>resolve-pr-feedback</li><li>slim-skills</li>
      <li>strategy</li><li>teach</li><li>thinking-report</li><li>wake</li><li>write-better-skill</li>
    </ul>
  </div>
</div>
</section>
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
