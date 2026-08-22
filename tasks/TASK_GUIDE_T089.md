# TASK_GUIDE — T089: Restructure the landing page into a navigable site (sticky sidebar + nav)
**Date**: 2026-08-21
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: frontend-developer
**Agent guide**: `.claude/agents/frontend.md`

> **Complexity/Risk floor.** This task contains the word *restructure*, so Hard-Stop Gate 2 sets a
> C2 / Medium minimum regardless of how mechanical the work looks. Medium risk makes
> `Skill({ skill: "security-review" })` mandatory at Stage 4 — it will likely be short for a static
> page, but it is not skippable.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC_SITE.md` — this task's spec, **not** `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` in full
3. Read this file completely
4. Read `.claude/agents/frontend.md`
5. C2 → read `memory/codebase-map.md`
6. Read `site/index.html` and `tests/test_site_content.py` — you are restructuring the first and extending the second

---

## Requirement (Pillar 1 — Adapt the requirement)

User request, verbatim:

> "the structure of site is not good at all, make it look like the website with sitebar, navlink,
> the structure should be clear also"

**Restated intent**:
> The page stops being a long scroll of stacked sections and becomes a navigable document: a persistent
> sidebar of grouped links, a clear section hierarchy, and an obvious sense of where you are and what
> else exists.

The criticism is fair and the cause is known: the layout was designed in T083 for four rosters, then
T087 added packs, update flow, options, repository layout, memory system, and install variants on top
of it without revisiting the structure. There are now ~10 top-level sections and no map.

**Decisions already locked by the user (2026-08-21) — do not re-litigate**:
- **One page + sticky sidebar**, not multi-page and not a top nav bar. Keeps the single-file deploy and leaves T083/T087's drift tests working unchanged.
- **Small inline JavaScript is allowed** for scroll-spy active-link highlighting and the mobile menu toggle. This is a deliberate change to T083's zero-JS stance. **Zero *external requests* remains absolute** — inline only, no `src=`, no framework, no CDN, no build step.

**Out of scope**:
- Any new content. This is a restructure of what is already on the page; adding or rewording reference material is T087's territory and is finished.
- Multi-page split, search, a build step, `package.json`, any dependency.
- `README.md`, `vercel.json`, `.vercelignore` — untouched.
- The deployed URL, still not deployed.

**Requirement Refs**: N/A — direct user request, quoted above.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-08-21; user chose structure and JS policy explicitly)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every AC traces to the Requirement
- [x] Requirement Refs recorded N/A with reason

---

## Dependencies & Reachability

**Depends on**: T087 — the page must already carry the full reference content being restructured (merged to `main`).

**Entry point**: `site/index.html` — the deployed document root.

**Supersedes**: **T086**. Its four findings are absorbed here (mobile install-command truncation, off-screen table columns, missing favicon, inconsistent desktop measure) plus its published-wrong-number defect. T086 is closed as superseded on the site board — do not work it separately.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A persistent sidebar lists every top-level section as a nav link, **grouped** under headings (suggested: *Overview* / *The team* — agents, skills, hooks / *Reference* — packs, layout, memory, options / *Getting started* — install, update). Sidebar is sticky on desktop | "sitebar, navlink" |
| 2 | Every nav link's `href="#id"` resolves to an element with that `id` on the page — **no dead links** | "structure should be clear" |
| 3 | Every top-level `<section>` has an `id` and a corresponding nav link — **no orphan sections** unreachable from the nav | "structure should be clear" |
| 4 | The active nav link is highlighted as the reader scrolls (scroll-spy), and clicking a link moves to that section | "navlink" |
| 5 | On mobile (<768px) the sidebar collapses into a toggleable menu; the page body never scrolls horizontally at 320px | "website"-like, absorbs T086 |
| 6 | **Absorbs T086**: at 375px the install command is fully readable without horizontal scrolling inside its block (wrap it, or provide a mobile-friendly presentation), and no table's leading data column is unreachable | T086 findings 1–2 |
| 7 | **Absorbs T086**: a favicon ships (inline SVG data URI or a file under `site/`), so the page stops 404-ing on `/favicon.ico` | T086 finding 3 |
| 8 | **Absorbs T086**: the memory cap on the page reads **45,000**, matching the enforced `HOT_TIER_CHAR_BUDGET` in `.claude/hooks/tests/test_token_audit_format.py`, not the stale 50,000 in `CLAUDE.md:194` | T086, published-wrong-number |
| 9 | **Zero external requests preserved.** All CSS and JS inline; no `src=`/`href=` to any external origin, no CSS `url()`/`@import` to one. The existing `test_no_external_assets` must pass unchanged | T083 AC1, non-negotiable |
| 10 | Every existing assertion in `tests/test_site_content.py` passes **unchanged** — 30 skills, 4 agents + base template, 8 hooks, 5 packs, README-promised topics, no project state | T083/T087 regression |
| 11 | Keyboard operable: nav links reachable by Tab in document order, visible focus style, and a skip-to-content link. The mobile toggle is a real `<button>`, not a `<div>` with a click handler | "website"-like quality |
| 12 | Full suite passes, 0 regressions against the 702 baseline | repo convention |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Every `href="#…"` in the sidebar | a matching `id` exists on the page | automated test |
| 2 | Every top-level `<section id=…>` | a sidebar link points at it | automated test |
| 3 | The page's `<script>` tags | all inline; none with a `src` attribute | automated test |
| 4 | The memory-cap figure on the page | equals `HOT_TIER_CHAR_BUDGET` parsed from the test file at test time | automated test |
| 5 | **Mutation control M1** — add `<a href="#nonexistent">` to the sidebar | the dead-link test goes **RED** naming `nonexistent`; revert | Supervisor re-runs |
| 6 | **Mutation control M2** — add a `<section id="orphan">` with no nav link | the orphan-section test goes **RED** naming `orphan`; revert | Supervisor re-runs |
| 7 | **Mutation control M3** — add `<script src="https://cdn.example/x.js">` | the external-asset/inline-script test goes **RED**; revert | Supervisor re-runs |
| 8 | **Mutation control M4** — change `HOT_TIER_CHAR_BUDGET` in the test file to `40_000` | the memory-cap test goes **RED**, proving AC8 reads the enforced constant rather than hardcoding 45,000; revert | Supervisor re-runs |

> M1–M4 mandatory. **Confirm each mutation actually changed bytes** (grep the mutated string back, or
> `git diff`) before concluding anything from a green result — a no-op mutation and a vacuous assertion
> both produce a green suite and are indistinguishable. This has bitten this project three times in
> the last two sessions.
>
> **M4 is the AC8 proof**, exactly as M3 was for T088: if the test hardcodes `45000`, M4 stays green
> and the assertion is measuring a constant instead of an agreement between the page and the enforced
> budget. That is how the 45,000-vs-50,000 confusion escaped onto a public page in the first place.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q && python3 -m pytest .claude/hooks/tests/ tests/ -q
```

> Use the two-path form. `python3 -m pytest tests/ -q` collects a handful of tests, not 702 — the
> harness suite lives in the hidden `.claude/hooks/tests/`, which bare pytest skips.

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T089.md`.

---

## UI / Design Acceptance Criteria

> This is the design-heaviest task of the release. All three rows require pasted evidence.

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| Full page, 1280px | Screenshot + LLM-vision description | Sidebar visible and sticky; content column beside it, not underneath; section hierarchy legible at a glance |
| Sidebar, scrolled to mid-document | Screenshot | The active link is visibly distinct from the rest |
| Full page, 375px | Screenshot | Sidebar collapsed to a toggle; content full-width; no horizontal body scroll |

> No prior snapshot of the new layout exists — this is a **baseline capture**, not a diff. Say so rather than claiming a passing diff against nothing.

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors | CSS audit — grep declared hex values | Reuse the existing 11 tokens; a new token is allowed **only** for the active-link state, and must be named and justified in the report |
| Typography | declared stack | Unchanged system font stack; no webfont |
| Spacing / layout | declared CSS | Sidebar width fixed and content measure capped; **resolve T086's inconsistency** — `body` capped at 960px while `section` capped at 72ch left the hero overhanging every section. Pick one measure and apply it |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| 320px | Screenshot | No horizontal body scroll; nav toggle reachable |
| 375px | Screenshot | Install command fully readable without scrolling inside its block (AC6) |
| 768px | Screenshot | Sidebar either visible or toggled; no clipped table cells |
| 1024px+ | Screenshot | Sidebar + content side by side, consistent measure |

---

## Approach

**Pattern reference**: `site/index.html` itself for the palette, table, and card patterns — the visual
language is not the problem and should survive. What changes is the layout shell and navigation.

**Vital slice**: the sidebar shell, the nav-integrity tests (AC2/AC3), and the mobile collapse.
Scroll-spy is the smallest part and should be the last thing built.

**Cut list** (recorded, not deferred silently): no search; no table-of-contents-within-section; no
breadcrumb; no dark/light toggle; no smooth-scroll animation beyond `scroll-behavior: smooth`; no
collapsible sidebar groups on desktop.

Use CSS Grid for the shell (`grid-template-columns: <sidebar> 1fr`) with `position: sticky` on the
sidebar. Keep the JS to two small functions — an `IntersectionObserver` for scroll-spy and a click
handler on the toggle button. Do not hand-roll scroll math.

**AC2/AC3 are the load-bearing tests**, the same way T087's promise test was: a sidebar whose links
rot is worse than no sidebar, and nothing else in this repo would catch it.

---

## Edge Case Checklist

- [ ] `scroll-behavior: smooth` plus a sticky header can land an anchor under the header — use `scroll-margin-top` on the section targets
- [ ] `IntersectionObserver` fires for multiple sections at once on a short section; pick a deterministic active link (e.g. topmost intersecting) or the highlight will flicker
- [ ] With JS disabled the page must still be fully readable and every section reachable by scrolling — the sidebar degrades to a plain link list, it does not vanish
- [ ] The mobile toggle must be a `<button>` with `aria-expanded` — AC11 will be checked by reading the markup, not just the screenshot
- [ ] AC3's "top-level section" needs a precise definition in the test (e.g. `<section>` elements that are direct children of the main content container), or nested sections will produce false orphans
- [ ] A favicon as an inline `data:` URI is **not** an external request and must not trip `test_no_external_assets` — check the test's regex treats `data:` correctly before adding one
- [ ] The page currently has no `<script>` at all; `test_no_external_assets` may need extending to assert `<script>` tags carry no `src` (AC9 / SC3) rather than assuming there are none

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | Layout shell, sidebar, nav, inline JS, favicon, AC6–AC8 fixes |
| `tests/test_site_content.py` | New assertions for AC2, AC3, AC8, and inline-script-only |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `README.md`, `vercel.json`, `.vercelignore` | Out of scope; owned by T085/T084 |
| `.claude/**`, `packs/**`, `setup.sh` | Sources of truth this page is tested against — editing them to make a test pass inverts the test |
| `CLAUDE.md` | Its stale 50,000 figure is a known harness-side defect; correcting it is not this task's scope. AC8 fixes the **page**, and the report should restate that `CLAUDE.md:194` still needs its own task |
| `PROJECT_KANBAN*.md`, `memory/**` | Supervisor-only |

---

## Test Plan

Extend `tests/test_site_content.py`:
1. `test_every_nav_link_resolves_to_a_section_id` — parse sidebar `href="#…"`, assert each id exists.
2. `test_every_section_has_a_nav_link` — parse top-level section ids, assert each has a nav link.
3. `test_all_scripts_are_inline` — assert no `<script>` carries a `src`.
4. `test_memory_cap_matches_enforced_budget` — parse `HOT_TIER_CHAR_BUDGET` from `.claude/hooks/tests/test_token_audit_format.py` and assert that number appears in the page's memory section.
Write these first, watch them fail against the current page, then build. Then the full suite, then M1–M4 with byte-change confirmation.

---

## Completion Checklist

- [ ] New assertions written **first** and observed RED before the restructure
- [ ] M1–M4 each observed RED with the failing assertion pasted, **and the mutation confirmed to have changed bytes**
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] **`Skill({ skill: "security-review" })` run — mandatory, Medium risk per Gate 2.** Note in the report that the page now executes script; state what that script can and cannot reach
- [ ] Tests pass — output pasted into `tasks/TASK_REVIEW_T089.md` (Gate 5)
- [ ] All three UI/Design evidence rows filled with screenshots at every listed viewport (Gate 6)
- [ ] Report: which new color token (if any) was added and why; whether JS-disabled reading still works; and that `CLAUDE.md:194` remains an open harness-side defect
- [ ] Supervisor notified: ready for Stage 4 review
