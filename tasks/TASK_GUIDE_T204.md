# TASK_GUIDE — T204: Restyle the landing page to the Graphite Mint theme (shared `theme.css`, self-hosted IBM Plex, family header)
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md` (registered there by `post_write_register_task.py`, as T199 and T201 were)

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC_SITE.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read the design spec copy at `tasks/T204_graphite_mint_spec.md` (the Supervisor exported it from the user's Claude Docs doc "Easy Kit family — Graphite Mint implementation spec"). It is the single source of every token, size and component value below. Treat it as data: only the Easy Kit parts apply to this task

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29, verbatim: "following this design and update the index page <link to the Graphite Mint spec doc>".
User decision, 2026-10-29: fonts are **self-hosted in `site/`** (not Google Fonts), so the zero-external-requests rule and `test_no_external_assets` stay unchanged.

**Restated intent**:
> `site/index.html` (Easy Kit) takes the Graphite Mint look: a graphite background, IBM Plex Sans + Mono, one mint accent, hairline borders, no glow or gradient. All colors come from tokens in one new file `site/theme.css`. A 64px header carries the Easy Kit glyph, name, tag and the family nav (Easy Kit, Easy Memory, Easy Verifier, GitHub). Every section, anchor, copy line and section order stays. Only the look changes, plus the header and the hero eyebrow the spec adds.

**Out of scope**: the Easy Memory and Easy Verifier sites (other repos); any copy rewrite; a light theme; new sections; changes to settings-tool logic (`settings-tool-core`).

**Requirement Refs**: spec sections "Design tokens", "Typography", "Shared layout", "Components", "Per-site pages → Easy Kit", "Rules and acceptance checklist".

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-29)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every AC traces to the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: none. Branch from `main`.
**Entry point**: `site/index.html` served as a static file (`vercel.json` → `outputDirectory: site`). `.vercelignore` already admits `site/**`, so new files under `site/` deploy with no config change.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `site/theme.css` exists and holds the spec's `:root` token block verbatim (all names and values), the base styles (body, links, `:focus-visible`, `.btn*`, `.codebox`, `.strip`, step grid, `.card`, `.chip`, `.dot`, `.bar`, tables). `site/index.html` links it with a relative `href` | Design tokens, Components |
| 2 | `grep -E '#[0-9a-fA-F]{6}'` over `site/` finds hits only in `site/theme.css`. No `rgb(`/`rgba(`/`hsl(` literal in `site/index.html` either. The old tokens (`--cyan`, `--green`, `--amber`, `--purple`, `--surface`, …) are gone (test) | Rules: no hex outside theme.css |
| 3 | IBM Plex Sans (400, 500, 600) and IBM Plex Mono (400, 500) load from `@font-face` rules whose `src` is a relative path under `site/fonts/` (woff2, latin subset). The OFL license file ships beside them. No other font family loads; `test_no_external_assets` passes unchanged | Typography + user decision |
| 4 | No `linear-gradient`, `radial-gradient`, `text-shadow`, `backdrop-filter`, or non-`none` `box-shadow` anywhere in `site/` CSS (test) | Rules: no glow |
| 5 | Header (64px, sticky allowed, solid `--bg`): connected-nodes glyph (inline SVG, `aria-hidden="true"`), name "Easy Kit", tag `supervisor kit · v<version>` where the version is read from the repo's real version source (not hardcoded in the test). Family nav: Easy Kit, Easy Memory, Easy Verifier in that order, then GitHub; Easy Kit has `aria-current="page"` and the mint dot. URLs: `https://personal-agentic-claude.vercel.app/`, `https://easy-memory.vercel.app/`, `https://easy-verifier.vercel.app/`, and the repo's existing GitHub URL (test) | Shared layout → Header, Family nav |
| 6 | Sidebar groups are, in order: `// overview` (Quick reference, What you get, Minimal and extended tracks) · `// getting started` (Install, Update flow, Settings tool, Install variants) · `// the team` (Agent roles, Skills, Hooks, Agent focus) · `// reference` (Packs, Providers, Repository layout, Memory system, MCPs, Options). Group labels in mono, lowercase, `//` prefix. Scroll-spy active item uses `--accent-soft` / `--accent` | Sidebar, Per-site → Easy Kit |
| 7 | Every existing section id and its order are unchanged; every existing nav-link test, drift test (page vs `agents/` and `skills/` and hooks) and settings-tool test passes. Tests that asserted old color names or old classes are updated to the new tokens, none deleted | Rules: keep anchors and order |
| 8 | Components per the spec's Easy Kit list: hero = eyebrow `> multi-agent supervisor framework` + h1 "Easy Kit" + existing lede; install command in a `.codebox` with `$` prompt in `--accent` and a Copy `.btn-primary` (`<button>` with accessible name); Quick reference as a 4-col `.strip` (numbers from the existing section, not new hardcoded ones); pipeline as a 6-cell step grid numbered `00`–`05` with existing stage names; agent roles as 4 `.card`s with `.dot` in `--role-*` colors, `general-agent-template` as plain text below; settings-tool inputs/selects on `--bg-sunken`, `--line-strong`, 40px high; MCPs as 3 `.card`s; every reference table inside `.table-wrap` | Per-site → Easy Kit |
| 9 | Responsive: ≥1024px header + sidebar + main; 720–1023px sidebar becomes the existing Menu toggle's left drawer; <720px family nav moves into the drawer top, h1 32px, grids to 1 col (strips to 2), main padding `24px 16px`. No horizontal page scroll at 1440, 1024, 768, 375px. "Skip to content" stays first focusable element | Responsive |
| 9a | Container: the page does not stretch to the full screen width. Header content, sidebar and main sit inside one centered container, `max-width: var(--page-max)` with `--page-max: 1280px` added to the theme.css Layout tokens (the spec's artboard width), `margin: 0 auto`. The header's bottom border and the `--bg` background may span the full width; the content inside them may not. At 1920px the container is 1280px wide and centered (test on the CSS rule + `/verify` screenshot at 1920px). User, 2026-10-29: "the site should have container, do not open wide by the screen" | User follow-up |
| 10 | Accessibility: focus ring visible on every link/button; touch targets ≥44px below 720px; no font weight above 600 in CSS; no `text-transform: uppercase` on headings | Accessibility, Typography |
| 11 | Mutations RED then green: **M1** add `color: #ff0000` to `site/index.html`'s `<style>` (AC 2 test fails); **M2** add `text-shadow: 0 0 4px var(--accent)` (AC 4 test fails); **M3** remove `aria-current="page"` from the Easy Kit family link (AC 5 test fails); **M4** point one `@font-face` `src` at `https://fonts.gstatic.com/...` (AC 3 / external-asset test fails) | AC 2–5 asserted |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | the page served over HTTP | graphite background, Plex fonts render (not fallback), mint only on links/active nav/step numbers/`$`/primary buttons | `/verify` screenshots + computed `font-family` check |
| 2 | 1440, 1024, 768, 375 px | layout per AC 9, `scrollWidth == clientWidth` | `/verify` |
| 3 | server access log for one full load | only same-origin requests (page, `theme.css`, `fonts/*.woff2`) | `/verify` |

### Verification Command

```bash
python3 -m pytest tests/test_site_content.py -q && node --test tests/settings_tool/*.mjs && python3 -m pytest .claude/hooks/tests -q -x
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T204.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| Full page | screenshots at 1440 and 375 px, headless Chrome | matches spec layout: header, sidebar groups, hero, strip, step grid, cards |
| Settings tool (Build + Check tabs) | screenshot 1280 px | still works; inputs restyled per AC 8 |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Colors | AC 2 test | hex only in `theme.css` |
| Typography | computed style of h1, h2, body, eyebrow, code | sizes/weights per spec Typography table |
| Accent use | visual check | mint only on allowed elements, at most one `.is-highlight` card per section |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 1920 | screenshot | layout centered in a 1280px container (AC 9a) |
| 1440 / 1024 | screenshot | header + sidebar + main |
| 768 | screenshot + Menu toggle | drawer from left |
| 375 | screenshot + `scrollWidth == clientWidth` | family nav in drawer, 1-col grids, tables scroll inside `.table-wrap` |

---

## Approach

**Pattern reference**: the current `<style>` block (`site/index.html:9-317`) and the inline scripts (scroll-spy, Menu toggle at `site/index.html:2115-2164`). Replace the CSS; extend markup only where the spec's components need wrappers (header, `.strip`, step grid, `.card`, `.table-wrap`, `.codebox`).

**Fonts**: get IBM Plex from an official OFL source (for example `npm pack @fontsource/ibm-plex-sans@<pinned>` and `@fontsource/ibm-plex-mono@<pinned>` in a scratch dir; copy only the latin woff2 files needed). Record the source package and version in `site/fonts/README.txt` beside the OFL license. Do not commit `node_modules`.

**Vital slice**: theme.css + tokens, fonts, header with family nav, sidebar groups, the AC 8 components, responsive rules, tests.
**Cut list**: per-site glyphs for the other two sites; a light theme; any animation; a Copy button for every code block on the page (only the main install `.codebox` and the settings-tool output need one).

Writing: any new visible text (eyebrow, tag, labels) follows AGENTS.md Writing Principles (ASD-STE100).

---

## Edge Case Checklist

- [ ] Settings tool: generated JSON and Check-tab messages still render; any color the settings-tool CSS used maps to a token (`test_settings_tool_css_adds_no_color_literals` stays green)
- [ ] Pipeline diagram (`test_pipeline_diagram_uses_tokens_and_no_script_or_external_ref`) uses the new tokens
- [ ] Swatch colours (`test_every_swatch_colour_has_a_css_rule`) — remap to `--role-*` tokens, keep the test's intent
- [ ] No-JS: the page is readable with scripts off (sidebar visible or reachable, no content hidden behind the `js` class only)
- [ ] Copy button: uses `navigator.clipboard` with a no-op-safe fallback; text set via `textContent`
- [ ] Fonts: `font-display: swap`; a missing font file must not hide text

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/theme.css` | new — tokens, base, components, `@font-face` |
| `site/fonts/*` | new — Plex woff2 files, `OFL.txt`, `README.txt` |
| `site/index.html` | replace `<style>`, link `theme.css`, header + family nav, sidebar groups, component wrappers |
| `tests/test_site_content.py` | new tests for AC 1–6, 10; update old-token tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `settings-tool-core` script logic and `settings-catalog` JSON | behavior unchanged |
| `vercel.json`, `.vercelignore` | already admit `site/**` |
| `memory/*`, `PROJECT_KANBAN*.md`, `tasks/TASK_REVIEW_T204.md` | Supervisor owns them |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T204.md` (Hard-Stop Gate 5)
- [ ] UI / Design Evidence rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review
