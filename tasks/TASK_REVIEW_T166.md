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
| verify | ☑ pass / ☐ fail / ☐ N/A | /verify 2026-10-20 (user-invoked), pass — page served at http://127.0.0.1:8080/ from the branch and driven in headless Chrome over DevTools: accessibility tree gives a `list` named "Skills grouped by pipeline stage, in stage order" with 7 list items read 0.5→5, and no arrow glyph in readable text (arrows are `content: "→" / ""`); live resize on one page load: 1024 and 768px → 2 columns, arrows → ↓ ← ↓ → ↓; 767 and 600px → 1 column, all ↓; page scrollWidth equals viewport at every width; 200% root font size at 1280px → no page overflow, no chip outside its box. Noted: at 200% text the heading word "TRANSFORMATION" (Stage 2) reaches about 9px past its box's right edge; at 768px `git-guardrails-claude-code` wraps at a hyphen inside its chip. |
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

**DELTA**: a reader sees the skills laid out as the pipeline's stage sequence, with arrows and chips, instead of eight plain lists. (Round 1 known limit — missing arrows between rows — is fixed in round 2, below.)

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Stage 4 — code-review round 1 (Supervisor, 2026-10-20) — returned for rework

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P1 | `site/index.html` `.skill-flow` (wide layout) | At ≥768px the steps sit in a 2-column grid with arrows only inside each row (0.5→1, 1.5→2, 3→4). There is no arrow 1→1.5, 2→3 or 4→5, so the wide view reads as a grid, not a flow — AC3 ("arrows between consecutive steps") and the user's "draw the flow through stage" are not met. Supervisor screenshot at 1280px (DevTools emulation). The 375px view (one column, ↓ between every step) is correct. | 100 | Rework: snake layout (below) |
| P3 | `.skill-flow` arrows | Arrows are small (body-text glyph) and low-contrast next to the boxes | 75 | Make them clearly visible in `--cyan`, like the pipeline SVG |

**Rework spec (snake / boustrophedon), wide layout only:** row 1 `0.5 → 1`; then `↓` under Stage 1 (right column); row 2 `2 ← 1.5` (Stage 1.5 placed in the **right** column, Stage 2 in the left, arrow pointing left); then `↓` under Stage 2 (left column); row 3 `3 → 4`; then `↓` under Stage 4 (right column) into Stage 5 (full width, or right column). Every consecutive pair 0.5→1→1.5→2→3→4→5 gets exactly one visible arrow. DOM/reading order stays 0.5…5 (use grid placement, not reordering). Keep the current phone layout. Add a test that pins this as far as markup allows (e.g. every step except the last carries the arrow hook class/attribute the CSS uses, and the CSS has rules for right, left and down arrows) and include a 1280px screenshot check in the UI evidence.

## Round 2 BEFORE (2026-10-20, as committed in 154c867)

CSS (wide, then the max-width:767px override):

```css
  .skill-flow { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem 2.2rem; }
  .flow-step { position: relative; min-width: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: .9rem 1.1rem; }
  .flow-step:not(:last-child)::after {
  .flow-step:nth-child(2n)::after { content: none; }
  .flow-step:last-child { grid-column: 1 / -1; }
  .flow-step h3, .skill-band h3 { margin: 0 0 .6rem; font-size: .8rem; color: var(--purple); text-transform: uppercase; letter-spacing: .05em; }
  .chips { margin: 0; display: flex; flex-wrap: wrap; gap: .4rem; }
  .chip { max-width: 100%; overflow-wrap: anywhere; background: var(--surface2); border: 1px solid var(--border); border-radius: 999px; padding: .15rem .65rem; font-size: .82rem; }
  .skill-band { margin-top: 1.2rem; background: var(--surface); border: 1px dashed var(--border); border-radius: 8px; padding: .9rem 1.1rem; }
    .skill-flow { grid-template-columns: minmax(0, 1fr); gap: 2.2rem; }
    .flow-step:nth-child(2n)::after { content: "\2192" / ""; }
    .flow-step:not(:last-child)::after { right: auto; left: 50%; top: auto; bottom: -1.8rem; transform: translateX(-50%) rotate(90deg); }
<ol class="skill-flow" aria-label="Skills grouped by pipeline stage, in stage order">
  <li class="flow-step" data-stage="0.5">
  <li class="flow-step" data-stage="1">
  <li class="flow-step" data-stage="1.5">
  <li class="flow-step" data-stage="2">
  <li class="flow-step" data-stage="3">
  <li class="flow-step" data-stage="4">
  <li class="flow-step" data-stage="5">
```

Markup: the `<ol class="skill-flow">` shown under AFTER above (steps carry only `class="flow-step" data-stage="…"`; no direction hook). Wide layout: 2-column grid, arrow only on odd steps (0.5→1, 1.5→2, 3→4); none between rows.

## Round 2 — AFTER / DELTA / evidence (Frontend-Implementer, 2026-10-20)

**RED first**: `tests/test_site_content.py::test_skills_flow_snakes_with_an_arrow_between_every_consecutive_pair` failed (`1 failed, 53 passed`) before the page change; GREEN after.

**AFTER**: each step except the last carries `data-next="right|down|left"` (0.5 right, 1 down, 1.5 left, 2 down, 3 right, 4 down; 5 none). CSS: `.flow-step[data-next="right|left|down"]::after` draw → ← ↓ in `--cyan` at 1.9rem, bold, in a 2.6rem gutter (gap 2.6rem); wide grid placement by `grid-area` (0.5 1/1, 1 1/2, 1.5 2/2, 2 2/1, 3 3/1, 4 3/2, 5 4/2), DOM order unchanged. Under `max-width:767px` the placement resets to auto and every arrow is ↓ centred below its box.

**DELTA**: at 1280px every consecutive pair 0.5→1→1.5→2→3→4→5 has one visible arrow (snake); arrows are larger and cyan. Phone layout unchanged (↓ between every step).

**Verification** (2026-10-20):
- `python3 -m pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q` → `66 passed`
- `python3 -m pytest .claude/hooks/tests tests -q | tail -1` → `1390 passed, 25 subtests passed`
- `sh scripts/validate.sh` → `validate.sh: PASS`

**UI evidence**: 1280px headless-Chrome screenshot (`/tmp/t166shots/wc.png`, viewed): →, ↓, ←, ↓, →, ↓ all visible between the seven boxes; chips wrap inside boxes. 375px: page rendered in a 375px-wide iframe (headless Chrome cannot go below ~485px window) (`/tmp/t166shots/mc.png`, viewed): one column, ↓ between every step, no horizontal overflow of the flow, `git-guardrails-claude-code` fits. Not checked: real device emulation, tablet widths 768–900px, a pixel-diff regression tool, M1–M4 not re-run this round (markup order/chips unchanged; no new tests touch them).

## Stage 4 — code-review round 2 (Supervisor, 2026-10-20) — accepted

P0 0 · P1 0 open · P2 0 · P3 0. Round-1 P1 (no arrows between rows) **fixed** in `7f2b731`: Supervisor DevTools-emulated screenshots at 1280px (→ ↓ ← ↓ → ↓, all six pairs connected), 800px (same snake, chips wrap inside boxes) and 375px (one column, ↓ between every step) — the 768–900px gap the implementer left unchecked is covered by the 800px shot. Round-1 P3 (arrow size/contrast) fixed: arrows larger, `--cyan`.

Supervisor re-run: `1390 passed, 25 subtests passed`; mutations re-run on the round-2 page (implementer did not repeat them): **M2** `tdd` duplicated into Stage 4 → `2 failed, 52 passed`; **M1** steps 3 and 4 swapped → `2 failed, 52 passed`; page restored, `git status` clean.

**Process finding (recorded, not blocking):** the round-2 report's `Startup reads:` line lists `PROJECT_SPEC.md`, `PROJECT_SPEC_SITE.md` and `agents/frontend.md`, but the same report says these were only line-counted this session. Round 1 (same task, same day) read them in full and the round-2 work was confined to the review file's rework spec, so the gap did not reach the change. The line should say what was actually read.

Security-review: not required (Low risk); the diff adds no script, form, link or external asset.
