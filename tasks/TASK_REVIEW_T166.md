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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py` — 6 new `test_skills_*` tests (AC1–AC6). RED first: `6 failed, 47 passed` (no `skill-flow`); GREEN after page change: `65 passed` (site+t151+installer) |
| Verification command run | ☑ pass | `65 passed in 0.09s`; `.claude/hooks/tests tests`: `1389 passed, 25 subtests passed`; `validate.sh: PASS` (2026-10-20) |
| Negative cases hold | ☑ pass | M1 (swap steps 3/4): 1 failed (AC1 order). M2 (tdd also in stage 4): 2 failed (AC5 dupes, AC6). M3 (`ideate`→`ideat`): 3 failed (AC5, AC6, existing every-skill test). M4 (band removed): 3 failed (AC4, AC5, existing every-skill test). Page restored after each. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | T165 lead/cell caps and test_docs_t151 inside the 65 passed; 1389 passed full |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Headless Chrome screenshots of `#skills` (other sections hidden by a throwaway injected style): 1280px `/tmp/t166/wide.png` — 2-column flow, arrows between pairs, Stage 5 full width, band below; 375px iframe `/tmp/t166/mobile.png` — one column, down arrows, band last. Visual verdict by agent only, no pixel diff. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | Only `--surface`, `--surface2`, `--border`, `--purple`, `--cyan` used; no new colours, fonts, images or scripts (script count unchanged: 2) |
| **UI: Responsiveness at target viewports** | ☑ pass | 1280px direct; 375px via iframe in a 500px window (headless Chrome will not go below ~485px, so not real device emulation). No horizontal overflow seen; `git-guardrails-claude-code` fits inside its box. |

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

**AFTER** (2026-10-20, `site/index.html`, markup; CSS in the `<style>` block `.skill-flow` / `.flow-step` / `.chip` / `.skill-band`):

```html
<ol class="skill-flow" aria-label="Skills grouped by pipeline stage, in stage order">
  <li class="flow-step" data-stage="0.5">
    <h3>Stage 0.5 — Requirement Grilling / Brainstorming</h3>
    <p class="chips"><span class="chip">brainstorming</span><span class="chip">ideate</span></p>
  </li>
  … stages 1, 1.5, 2, 3, 4, 5 the same shape …
</ol>
<div class="skill-band">
  <h3>Any stage</h3>
  <p class="chips"> … the 13 cross-cutting chips … </p>
</div>
```

**DELTA**: a reader sees the skills laid out as the pipeline's stage sequence, with arrows and chips, instead of eight plain lists. Known limit: in the 2-column wide layout the arrow is shown only between the two boxes of a row, not from the end of one row to the start of the next (reading order is still stage order, and each box is labelled).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
