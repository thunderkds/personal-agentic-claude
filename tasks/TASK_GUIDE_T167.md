# TASK_GUIDE — T167: Site tables never scroll sideways — fit on desktop, stacked cards on phones
**Date**: 2026-10-20
**Complexity Level**: C1 — CSS + per-cell label attributes on the page's existing tables, plus tests
**Risk Level**: Low — static HTML/CSS, no script, no deploy config
**Priority**: P1
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md` (site scope, drift constraint)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `site/index.html` (table CSS at `.table-wrap` / `table` / `th, td` / the sticky first-column rule, the `@media (max-width: 767px)` block, and every `<table>`) and `tests/test_site_content.py`, `tests/test_docs_t151.py` (reads the page line by line)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-20, after viewing the page locally: *"the tables got the scroll horizontal, it does not look good, check and remove it"*.

**Supervisor diagnosis (measured 2026-10-20, headless Chrome, branch `feat/t165-site-scan-first`):**
- `site/index.html:124` `table { … min-width: 40rem; }` forces every table to ≥ 640px, so at 375px **all 8 tables** scroll inside their `.table-wrap` (`overflow-x: auto`, line 123).
- At 1280px the `#hooks` table is 716px inside a 639px wrap (long unbreakable `<code>` script names), so it scrolls on desktop too — identical on `main`, i.e. pre-existing; it already breaks T083's own desktop criterion ("tables fully visible without horizontal scroll").
- The sideways scroll on phones was a deliberate T083 choice (with a sticky first column, lines 127–129). The user is now overriding it.

**Restated intent:**
> No table on the page scrolls sideways, at any width. On wide screens every table fits its column:
> drop the forced minimum width and let long code tokens wrap. On phones (the page's existing
> ≤ 767px breakpoint) each table row becomes a stacked card: one cell per line, each cell preceded
> by its column header as a small label, so no column meaning is lost. Content and tables are
> unchanged otherwise.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user: "check and remove it"; Supervisor chose fit-on-desktop + stacked-cards-on-phone as the standard no-scroll pattern that keeps column meaning)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: T166 (same branch `feat/t165-site-scan-first`)

**Entry point**: `site/index.html` — every `<table>`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | The page CSS sets no `min-width` on `table`, and `.table-wrap` no longer uses `overflow-x: auto`/`scroll`; the sticky-first-column rule (only useful while scrolling) is removed | remove scroll |
| 2 | Long code tokens inside table cells can wrap (e.g. `td code { overflow-wrap: anywhere; }` or equivalent) | fit on desktop |
| 3 | Every `<td>` carries a `data-label` equal to its column's `<th>` text (test derives the header text per table and compares — drift-proof, both directions: no missing, no mismatched) | stacked-card labels |
| 4 | Inside `@media (max-width: 767px)`: `thead` visually hidden (still in the accessibility tree, e.g. clip pattern — not `display: none`), rows and cells `display: block`, and `td::before { content: attr(data-label) }` shows the label | stacked cards |
| 5 | Runtime (UI evidence, not a pytest): at 1280px and 375px, for every `.table-wrap`, `scrollWidth <= clientWidth`, and the page `scrollWidth` equals the viewport | no scroll anywhere |
| 6 | All existing tests stay green, including T165's visible-`td` ≤ 25-word cap and `tests/test_docs_t151.py` | no regression |
| 7 | New tests for AC1–AC4, observed RED before the change | Gate 5 |

**Mutation controls:** **M1** — restore `min-width: 40rem` → AC1 RED. **M2** — delete one `data-label` → AC3 RED. **M3** — change one `data-label` to a wrong header → AC3 RED. **M4** — remove the `td::before` rule → AC4 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T167.md`. BEFORE is pre-filled there by the Supervisor.

---

## UI / Design Acceptance Criteria

- Existing tokens only; the stacked-card label uses the current `th` look (`--muted`, uppercase, small).
- Each stacked row reads as one card (border/spacing between rows); the `<details>` fold-outs inside cells still open.
- Screenshots at 1280px and 375px of `#hooks` and one other table; a runtime overflow measurement for AC5 (DevTools device emulation — headless Chrome won't size a window below ~485px; page uses smooth scrolling, so scroll with `behavior: 'instant'` before measuring).

---

## Approach

**Pattern reference**: the existing `@media (max-width: 767px)` block; `th` styling for the label.

**Vital slice**: AC1, AC3, AC4, AC5. **Cut list**: per-table custom layouts; JS; changing any table's content or columns.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | Table CSS; `data-label` on every `<td>` |
| `tests/test_site_content.py` | AC1–AC4 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | Deploy config unchanged |
| `.claude/hooks/**`, `skills/**`, `agents/**` | No harness change in scope |
| `README.md`, `memory/**`, `PROJECT_KANBAN*.md` | Out of scope / Supervisor-only |

---

## Completion Checklist

- [ ] New AC1–AC4 tests observed RED first, then GREEN
- [ ] M1–M4 results pasted in the review's "Negative cases hold" row
- [ ] AC5 runtime measurement pasted; all three UI Evidence rows filled
- [ ] `/verify` — user-run
