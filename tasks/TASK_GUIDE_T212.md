# TASK_GUIDE — T212: Landing page takes the neon Graphite Mint accent (#3CF5A8) with glow, per the updated design canvas
**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC_SITE.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `site/theme.css` (T204 tokens) and `tests/test_site_content.py` section `# ---- AC 4: no glow, no gradient ----`. This guide's token table below is the single source for every new value; `tasks/T204_graphite_mint_spec.md` stays the source for everything else, except its "No glow" lines, which this task supersedes

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29, verbatim: "hey, checking the design and update following https://claude.ai/artifact/5jKFUHLaGJTPK4KgazQ2o1#page-dcb81aee8d83".
Supervisor compared the canvas board "B · Graphite Mint — Easy Kit" (`project/Graphite-Mint.dc.html`) with `site/`: the only design change since T204 is the accent. The board uses neon mint `#3CF5A8` with glow (prop `glow` default `true`), and stat numbers in the accent. Plain links stay `#7EDDB0` / hover `#B2EDCF`.
User decision, 2026-10-29 (AskUserQuestion): "Yes, neon + glow" — accent `#3CF5A8`, glow as in the board, mint stat numbers; replace the T204 no-glow test with one that matches the new rule.

**Restated intent**:
> `site/` keeps the T204 layout, copy, anchors and section order. Only the accent changes: the neon mint `#3CF5A8` replaces `#7EDDB0` on accent elements, and a soft glow, defined once as tokens in `site/theme.css`, sits on the eyebrow, the active sidebar item, the stat numbers, the install code box, the primary buttons, the active family-nav dot, the highlighted card and the bar fill. Plain links keep the soft mint. Gradients and blur stay banned.

**Out of scope**: Easy Memory and Easy Verifier sites (other repos); layout, copy or section changes; a glow on/off switch for the viewer; animation; any change to settings-tool logic.

**Requirement Refs**: canvas board `Graphite-Mint.dc.html` (`renderVals()`: `accentSoft = accent+'14'`, `accentLine = accent+'59'`, `neonText`, `neonGlow`, `dotGlow`, `glowShadow`), T204 spec (all other values).

### Requirement Fidelity Gate

- [x] Restated intent confirmed (user answer, 2026-10-29)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every AC traces to the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T204, T207 (both Done, on `main`). Branch from `main`.
**Entry point**: `site/index.html` + `site/theme.css`, static (`vercel.json` → `outputDirectory: site`).

---

## Token table (from the board's `renderVals()`, accent `#3CF5A8` = rgb 60, 245, 168)

| Token | Value | Board name |
|---|---|---|
| `--accent` | `#3CF5A8` | accent |
| `--accent-hover` | `#8AF9CB` | (new: lighter neon for primary-button hover) |
| `--accent-soft` | `rgba(60, 245, 168, 0.08)` | accentSoft (`14` hex) |
| `--accent-line` | `rgba(60, 245, 168, 0.35)` | accentLine (`59` hex) |
| `--link` | `#7EDDB0` | helmet `a` color |
| `--link-hover` | `#B2EDCF` | helmet `a:hover` color |
| `--glow-text` | `0 0 12px rgba(60, 245, 168, 0.35)` | neonText |
| `--glow-button` | `0 0 0 1px rgba(60, 245, 168, 0.25), 0 0 18px rgba(60, 245, 168, 0.25)` | neonGlow |
| `--glow-dot` | `0 0 8px #3CF5A8` (write it as `0 0 8px var(--accent)`) | dotGlow |
| `--glow-box` | `0 0 0 1px rgba(60, 245, 168, 0.20), 0 0 24px rgba(60, 245, 168, 0.12)` | glowShadow |

`--on-accent` stays `#0E100F`. The favicon's stroke (`%237EDDB0` in `site/index.html`) becomes `%233CF5A8`.

## Where the glow goes (board → site)

| Element | Board style | Site rule |
|---|---|---|
| Hero eyebrow | accent + neonText | `.eyebrow { text-shadow: var(--glow-text) }` |
| Active sidebar item | accentSoft bg, accent, neonText, `inset 0 0 0 1px accentLine` | `.sidebar a.active` |
| Quick reference stat numbers | accent + neonText (was `--text-strong`) | stat number rule; suffix (`/11`) stays `--text-dim` |
| Install `.codebox` | glowShadow | `.codebox { box-shadow: var(--glow-box) }` (main install box only if `.codebox` is reused for plain code; then use a modifier) |
| `.btn-primary` / Copy | accent bg + neonGlow | `.btn-primary { box-shadow: var(--glow-button) }` |
| Family nav active dot | accent + dotGlow | `.family-nav a[aria-current="page"] .dot` |
| Highlighted card / outcome flow node | accentLine border + neonGlow | `.card.is-highlight`, `.flow-node.is-outcome` |
| `.bar > span` fill | accent + dotGlow | `.bar > span` |
| Plain `a` | `#7EDDB0` / `#B2EDCF` | `a { color: var(--link) } a:hover { color: var(--link-hover) }` |

Step numbers and the `$` prompt use `--accent` with no glow (board has none there).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `site/theme.css` `:root` holds every token in the Token table with exactly those values; `--accent` is `#3CF5A8`; `#7EDDB0` appears only as `--link` (test) | Token table |
| 2 | Every `text-shadow` and `box-shadow` value in `site/` CSS (comments stripped) is `none`, a `var(--glow-*)` token, or `inset 0 0 0 1px var(--accent-line)`; raw shadow values appear only inside the `--glow-*` token definitions. `linear-gradient`, `radial-gradient`, `conic-gradient`, `backdrop-filter`, `filter: blur`, `drop-shadow(` stay banned (replaces `test_site_css_has_no_gradient_glow_or_blur`, test renamed, not deleted silently: old intent "no gradient, no blur" kept) | User decision |
| 3 | Each element in "Where the glow goes" carries its glow token (test per selector, parsed from CSS) and stat numbers use `color: var(--accent)` | Board → site table |
| 4 | Plain links use `--link` / `--link-hover`; `.btn-primary` text stays `--on-accent` on hover; hex still only in `theme.css` (existing AC 2 test of T204 stays green) | Board helmet |
| 5 | `prefers-contrast: more` media query sets every `--glow-*` token to `none` (glow is decoration; no info is lost) | Accessibility |
| 6 | Every other existing test passes unchanged: section ids/order, nav, drift, settings-tool, fonts, external-asset, container. Tests that pinned `#7EDDB0` as the accent are updated to the new token, none deleted | Scope lock |
| 7 | Mutations RED then green: **M1** set `--accent: #7EDDB0` (AC 1 fails); **M2** add `text-shadow: 0 0 4px red` to a rule outside `:root` (AC 2 fails); **M3** remove the glow from `.btn-primary` (AC 3 fails); **M4** add `background: linear-gradient(red, blue)` (AC 2 fails) | AC 1–3 asserted |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | the page served over HTTP at 1440 px | neon mint accent with soft glow on the listed elements, matching the board; links soft mint | `/verify` screenshot beside the board |
| 2 | 1440, 1024, 768, 375 px | layout unchanged from T204/T207, `scrollWidth == clientWidth` | `/verify` |
| 3 | text contrast | `--accent` on `--bg` and `--on-accent` on `--accent` ≥ 4.5:1 (compute and paste the ratios) | agent report |

### Verification Command

```bash
python3 -m pytest tests/test_site_content.py -q && node --test tests/settings_tool/*.mjs
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T212.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| Full page | headless Chrome screenshots 1440 and 375 px | header, hero, strip, step grid, cards as before; accent neon with glow on the listed elements |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Tokens | AC 1–3 tests | glow only via `--glow-*`, hex only in `theme.css` |
| Accent use | visual check | glow only on the "Where the glow goes" elements |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 1920 / 1440 / 1024 / 768 / 375 | screenshot + `scrollWidth == clientWidth` | unchanged from T207 |

---

## Approach

**Pattern reference**: `site/theme.css` token block and component rules (T204). Change token values, add the `--link*` and `--glow-*` tokens, add the shadow declarations. No markup change except the favicon stroke.
**Vital slice**: tokens, the eight glow placements, the replaced no-glow test, AC 3 tests, mutations.
**Cut list**: viewer glow toggle (board's `glow` prop is a design lever, not a page feature); the other two family sites; animation.

---

## Edge Case Checklist

- [ ] `.codebox` reused for non-install code: glow only on the install box (modifier class if needed)
- [ ] Settings tool primary button (`#settings-tool .st-primary` in `site/index.html`) — same glow as `.btn-primary`, via token
- [ ] `:focus-visible` outline stays `--accent` and stays visible next to a glow
- [ ] No-JS render unchanged

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/theme.css` | token values, new tokens, shadow declarations, `prefers-contrast` block, header comment ("No glow" line updated) |
| `site/index.html` | favicon stroke; settings-tool primary glow if it lives there |
| `tests/test_site_content.py` | replace AC 4 no-glow test; new AC 1–5 tests; update tests pinning `#7EDDB0` |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `tasks/T204_graphite_mint_spec.md` | historical spec copy |
| settings-tool logic, `vercel.json`, `.vercelignore` | behavior unchanged |
| `memory/*`, `PROJECT_KANBAN*.md`, `tasks/TASK_REVIEW_T212.md` | Supervisor owns them |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T212.md` (Hard-Stop Gate 5)
- [ ] UI / Design Evidence rows filled (Hard-Stop Gate 6)
- [ ] Auto verify run (`stop_auto_verify.py --start T212`)
- [ ] Supervisor notified: task ready for Stage 4 review
