# TASK_REVIEW — T168: An "MCPs" section lists the companion MCP servers

> Sibling of `tasks/TASK_GUIDE_T168.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (Supervisor, 2026-10-20, `site/index.html` @ `d7874e7`) — verbatim sidebar Reference group:

```html
    <p class="nav-group-title">Reference</p>
    <ul>
      <li><a href="#packs">Packs</a></li>
      <li><a href="#providers">Providers</a></li>
      <li><a href="#repository-layout">Repository layout</a></li>
      <li><a href="#memory-system">Memory system</a></li>
      <li><a href="#verifier">easy-verifier-mcp</a></li>
      <li><a href="#options">Options</a></li>
    </ul>
```

Verbatim `#verifier` section:

```html
<section id="verifier">
<h2>easy-verifier-mcp</h2>
<p class="lead">
  A separate companion tool, not part of this kit: a no-LLM evidence engine you can run alongside Stage 4 review.
</p>
<ul>
  <li>No LLM and no model API key — ratings are deterministic rules over cited metrics</li>
  <li>Seven independently callable dimensions, from architecture to blast-radius</li>
  <li>Auditable coverage — a "found 4/6" always shows the sources it did not find</li>
  <li>Read-only and local — never runs the target repo's code, no outbound network</li>
  <li>Kit-aware mode treats this kit's specs, task guides and memory as ground truth</li>
</ul>
<p><a href="https://github.com/thunderkds/easy-verifier-mcp" target="_blank" rel="noopener noreferrer">easy-verifier-mcp on GitHub</a> &middot; <a href="https://easy-verifier.vercel.app/" target="_blank" rel="noopener noreferrer">Easy Verifier site</a></p>
</section>
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
