# TASK_GUIDE — T207: Visual-first landing page — diagrams lead each heavy section, long prose folds into Details
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `tasks/T204_graphite_mint_spec.md` (the design system: tokens, type scale, accent rules) and `site/theme.css` (the only place colors live)
7. Read `tests/test_site_content.py` end to end before moving any text: it pins phrases, anchors, the skill roster and the honesty rules

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29, verbatim: "investigate the page and update for the easy following, I mean should focus on the flow chart, or anything visualize, currently, too much text to read hard to follow. check and update. All as you recommend and automatic"

**Restated intent**:
> A reader should understand each section of `site/index.html` from a diagram and a short summary, without reading paragraphs. Every heavy section opens with a flow chart or visual summary drawn from the theme's tokens. The long explanation stays on the page, folded into a `<details>` block under the visual. The facts on the page do not change.

**Supervisor investigation (2026-10-29, `main` @ `c00d0fe`)**: ~4,000 visible words, 1 inline SVG (the pipeline, already folded into a `<details>`), 1 stage grid, 8 tables, 84 paragraphs. Visible words per section: `update-flow` 712, `hooks` 487, `tracks` 399, `mcps` 331, `install` 297, `agent-focus` 285, `providers` 259, `agent-roles` 240, `what-you-get` 222.

**Supervisor design decisions** (the user said "All as you recommend"; these are binding):
- **D1 — Visual first, text kept.** Each target section is: heading → a one- or two-sentence lead → the visual → a `<details class="more"><summary>Details</summary>…</details>` holding the prose, lists and tables that are there today. Text is moved, not deleted, except an exact duplicate of what the visual now says. Existing `<details>` blocks inside a section stay as they are.
- **D2 — The visuals** (one per section, built in HTML + CSS, inline SVG only where HTML cannot draw it):
  - `tracks`: a decision flow — *your request* → a diamond "any of: C2+ · Risk Medium/High · a Gate-2 word or *migrate* · changes user data · more than one session or agent · a UI component?" → **yes** → *Extended track: the 5-stage pipeline* / **no** → *Minimal track: 7 steps, one Decision record*. A second, horizontal flow for **Auto mode**: `[auto]` request → track runs → Stop check → auto verify (headless `/verify`) → close-out (Gates 5 and 6, complete report) → Done; a separate lane marked "yours": merge · push · ship.
  - `install`: a 4-step flow — run the one command → pick from numbered menus → read the plan → `Proceed? [Y/n]` — with a badge "never deletes: files it replaces are backed up first".
  - `update-flow`: a per-file decision map — *your copy is* untouched → overwritten · customized → asked / diff / backup · no longer shipped → removed if untouched, kept if edited · `.claude/settings.json` → merged.
  - `hooks`: a lifecycle strip — tool call → **PreToolUse** (the blocking hooks) → tool runs → **PostToolUse** (trace, memory, review moves) → **Stop** (auto-mode check, auto verify). Blocking hooks and advisory hooks are told apart by shape or label, never by color alone.
  - `agent-roles`: the Supervisor as a hub with the 4 spawnable roles around it, each in its existing `--role-*` color, with its one-line job.
  - `memory-system`: hot tier `memory/MEMORY.md` (index, character cap) → three cold files (`decisions.md`, `learnings.md`, `glossary.md`), with "Supervisor writes, agents read a slice".
  - `mcps`: the three companion servers as a row of cards (they may already be cards — keep them, fold the prose).
  - Other sections (`providers`, `agent-focus`, `packs`, `repository-layout`, `options`, `settings-tool`, `install-variants`, `skills`, `quick-reference`, `what-you-get`) only fold prose past the lead into `<details>` where they exceed the D3 budget; no new visual is required there.
- **D3 — Reading budget.** Words visible on first load (outside `<details>`, outside `<pre>`/`<code>`, outside SVG text) per target section ≤ 150, and for the whole page ≤ 60% of today's count. A new test measures it and is the ratchet.
- **D4 — Accessible.** An HTML flow is an `<ol>`/`<ul>` (screen readers get the order). An SVG has `role="img"`, `<title>` and `<desc>`. Every color pair meets WCAG AA contrast. No animation is required; any motion honours `prefers-reduced-motion`.
- **D5 — Responsive.** Each flow stacks vertically at ≤ 768 px. No horizontal page scroll at 375 px (`scrollWidth == clientWidth`).
- **D6 — Design system only.** Colors, radii and fonts come from `site/theme.css` tokens (the existing "hex only in `theme.css`" test holds). New CSS lives in `theme.css` or the page's existing `<style>`, following its naming. No new library, no CDN, no JavaScript for the diagrams.
- **D7 — Nothing else moves.** Section ids, sidebar nav, the settings tool's behaviour and every phrase `tests/test_site_content.py` pins stay as they are.

**Out of scope**:
- Changing any fact, number or claim on the page; new sections or pages
- The settings tool's logic (`settings-tool-core`, `settings-catalog`)
- `vercel.json`, deploy config, the family header from T204

**Requirement Refs**: no PRD — traces to the user's 2026-10-29 message above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-29; user: "All as you recommend and automatic")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (track, auto mode, auto verify, close-out, hot/cold tier are the page's existing words)
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D7
- [x] Requirement Refs — N/A, no PRD; traced to the user message

---

## Dependencies & Reachability

**Depends on**: T204 (Graphite Mint theme, merged)
**Entry point**: `site/index.html` (served as the landing page)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `tracks`, `install`, `update-flow`, `hooks`, `agent-roles`, `memory-system` each hold one visual element marked `data-visual="<section-id>"`, placed before that section's first `<details class="more">` | D1, D2 |
| 2 | The `tracks` visual names both outcomes (Extended, Minimal) and every trigger in D2; the auto-mode flow ends at Done and shows merge, push and ship in a lane marked as the user's | D2 |
| 3 | The `hooks` visual names PreToolUse, PostToolUse and Stop, and tells blocking from advisory by a text label or shape | D2, D4 |
| 4 | Visible words (outside `details`, `pre`, `code`, `svg`) ≤ 150 in each AC 1 section, and ≤ 60% of the page's count at `c00d0fe`; the baseline number is a constant in the test | D3 |
| 5 | No sentence is lost: every `<p>`/`<li>` text present at `c00d0fe` is still in the page, unless it is listed in the test as an exact duplicate of a visual label | D1 |
| 6 | Each SVG has `role="img"`, `<title>`, `<desc>`; each HTML flow is an `<ol>` or `<ul>` | D4 |
| 7 | No hex color outside `theme.css`; no new `<script src>` or `<link>` to a third party | D6 |
| 8 | All existing tests in `tests/test_site_content.py` pass unchanged (a test edited only to follow a moved element must say why in its commit) | D7 |
| 9 | Mutations, each turns a new test RED then green on revert: **M1** delete the `hooks` visual; **M2** move one 200-word paragraph out of its `<details>`; **M3** delete one sentence from a folded block; **M4** add `#ff0000` to the page's `<style>` | guarantees asserted |
| 10 | Full suites pass: `python3 -m pytest tests -q`, `node --test tests/settings_tool/*.mjs`, `python3 -m pytest .claude/hooks/tests -q` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | the page at 1440 px | each AC 1 section shows its visual above the fold of that section, prose folded | headless Chrome screenshot per section |
| 2 | the page at 375 px | flows stacked vertically, `scrollWidth == clientWidth` | headless Chrome |
| 3 | a `Details` block clicked | the moved prose, lists and tables appear unchanged | headless Chrome |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q && node --test tests/settings_tool/*.mjs
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T207.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T207.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| Each AC 1 section | screenshot at 1440 px, before and after | visual leads, prose folded |
| Settings tool | screenshot at 1280 px | unchanged |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Colors | AC 7 test | tokens only |
| Typography | computed style of a flow label and a node title | Plex Sans / Plex Mono from the theme scale |
| Accent use | visual check | mint only on the outcome nodes and the "Done" node; role colors only on role nodes |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 1440 / 1024 | screenshot | flows horizontal or branching as designed |
| 768 / 375 | screenshot + `scrollWidth == clientWidth` | flows stacked, no sideways scroll |

---

## Approach

**Pattern reference**: the existing `.flow-step` stage list in `#skills` and the `what-you-get` stage grid — reuse their markup style; the pipeline SVG at `#pipeline-diagram` for SVG accessibility attributes.

**Vital slice**: `tracks` + `hooks` + `install` + `update-flow` visuals (the four heaviest, 1,895 words today) with prose folded, plus the reading-budget test.
**Cut list**:
- Animated or interactive diagrams
- A diagram library or generated images
- Visuals for the sections D2 leaves at "fold only"

Writing: visual labels are short noun phrases or commands; text the user reads follows AGENTS.md Writing Principles (ASD-STE100).

---

## Edge Case Checklist

- [ ] `<details>` opened by an in-page link (`#update-flow` from the quick reference) — the target heading stays visible, not inside a closed block
- [ ] Find-in-page (Ctrl+F) still finds folded text in Chrome (it opens `<details>`)
- [ ] Print / no-CSS: flows read in order as lists
- [ ] Long code tokens in flow nodes wrap, no overflow at 375 px

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | visuals + `<details class="more">` folds |
| `site/theme.css` | flow / node / lane styles from existing tokens |
| `tests/test_site_visual_first.py` | new: AC 1–7, 9 |
| `tests/test_site_content.py` | only if a pinned element moved (AC 8) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `settings-tool-core` script and `settings-catalog` JSON in `site/index.html` | behaviour unchanged |
| `vercel.json`, `.vercelignore` | deploy unchanged |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: write `tests/test_site_visual_first.py` (AC 1–7) and see it fail on `c00d0fe`. Build the four vital-slice visuals, then the rest of D2. Run M1–M4 by hand and paste each RED and green. Take the screenshots listed above with headless Chrome (`google-chrome --headless=new`) and save them outside the repo. Then the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T207.md` (Hard-Stop Gate 5)
- [ ] All three UI Evidence rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review
