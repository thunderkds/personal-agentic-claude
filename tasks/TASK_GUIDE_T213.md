# TASK_GUIDE — T213: Sidebar scroll-spy highlights the item above the clicked one
**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md`

## Bug Fix Task Guide — T213

### Mental Model (confirmed by user)
- Observed: user, 2026-10-29: "when I click the nav item, but the highlight is the nav item that above the item click". `/verify T212` saw the same: after `#skills` scrolled into view, the active link stayed "Agent roles".
- Expected (testable): (a) for every sidebar link, a click makes THAT link the only `.active` link; (b) when scrolling by hand, the active link is the section at the top of the view, just below the 64px sticky header; (c) for the last sections, which the page cannot scroll to the top, the clicked link stays active until the user scrolls by hand (user choice, 2026-10-29: "Clicked item stays lit").
- Likely divergence point: `site/index.html:2316-2319`. The `IntersectionObserver` uses `rootMargin: "0px 0px -60% 0px"`, so its top edge is the viewport top, under the sticky header. After an anchor jump, `scroll-margin-top: calc(var(--header-h) + var(--s-4))` (80px, `site/theme.css:224`) puts the target 80px down. The previous section ends `--s-8` (40px) above it, so its tail still intersects the band under the header. `paint()` picks the first intersecting section in document order, which is the previous one.
- Recent context: scroll-spy code unchanged since T089 (`b1baabf`). T204/T207 restyles kept it. T212 (glow on `.sidebar a.active`, branch `feat/t212-neon-glow`, not yet on `main`) makes it more visible but did not touch the script.

### Intake
- Trigger: open `site/index.html`, click any sidebar link (e.g. "Skills"); the link above it ("Agent roles") gets `.active`.
- Severity: P2 (navigation aid wrong; content still reachable).
- Affected area: `site/index.html` scroll-spy script (lines 2296-2321). Possibly `site/theme.css` only if an offset token is needed.

### Complexity & Risk
- Complexity: C1
- Risk: Low

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [x] Phase 1 feedback loop built and running (headless Chrome, see Approach)
- [x] Bug reproduces deterministically on the loop (list every sidebar link whose click leaves a different link active)
- [x] 3–5 ranked falsifiable hypotheses listed (consistent with confirmed mental model)
- [x] Correct hypothesis identified via Phase 4 instrumentation

### Attempts Log (filled live during diagnosis — required if >1 hypothesis tested)
| # | Hypothesis | Predicted signal | Actual result | Verdict |
|---|---|---|---|---|
| 1 | Previous section's tail is inside the observer band [0, 40% vh] after an anchor jump (band top is the viewport top, under the header) | After `#skills` click: `agent-roles` rect bottom between 0 and 360 and `paint()` picks it first | `agent-roles` top=-446 bottom=40, `skills` top=80; active = agent-roles | Confirmed |
| 2 | Counterfactual: a band starting at the 80px anchor offset excludes the previous section | A second IntersectionObserver with `-80px 0px -60% 0px` reports only the target | today `["agent-roles","skills"]`; `-80px` -> `["skills"]` (also install/tracks, hooks/skills) | Confirmed |
| 3 | Harness artifact: smooth scroll not settled when read | Result changes with longer wait / rects not final | `scroll-behavior: auto`, 400ms wait, rects static; same result every run | Disproven |
| 4 | Stale `visible` map (observer only reports transitions) | A section flagged visible that is not in the band | The wrongly active section really intersects the band; no stale entry needed | Disproven |

**Stuck checkpoint** (if 2 consecutive hypotheses disproven):
- [ ] 3 options presented (next hypothesis / widen scope / abandon+escalate)
- [ ] Chosen option: ___
- [ ] User's explicit go-ahead: ___

### Fix Gates (Pillar 2)
- [x] Regression test written before the fix (or no-seam documented)
- [x] Fix applied; regression test passes
- [x] Phase 1 loop no longer reproduces the bug
- [x] Fix matches the "correct behaviour" definition from the mental model (a), (b) and (c)

### Cleanup Checklist (Pillar 3)
- [x] All [DEBUG-...] instrumentation removed (grep verified)
- [x] Throwaway prototypes deleted
- [x] Correct hypothesis stated in commit message
- [x] Post-mortem: what would have prevented this?

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T213.md`.

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T213.md`.

---

## Dependencies & Reachability

**Depends on**: none. Branch from `main`.
**Entry point**: `site/index.html` (static, served by `vercel.json` → `outputDirectory: site`).

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Headless Chrome check: at 1440×900, for EVERY `#site-nav a[href^="#"]`, after a click (with `scroll-behavior: auto`) exactly one link is `.active` and it is the clicked one | Expected (a), (c) |
| 2 | Same check: after `window.scrollTo` so a section's top sits just below the header (for every section that can reach that position), the active link is that section's | Expected (b) |
| 3 | After a click on one of the last, short sections, then a manual scroll up by ≥ one section, the active link follows the scroll again | Expected (c) |
| 4 | The check FAILS on today's `main` code (paste the failing link list in BEFORE) and passes after the fix | Regression |
| 5 | No-JS and no-`IntersectionObserver` behavior unchanged (script still returns early); `tests/test_site_content.py` and `node --test tests/settings_tool/*.mjs` stay green | Scope lock |

## Approach

- Phase 1 loop: Chrome is at `/usr/bin/google-chrome` (also `/snap/bin/chromium`). Playwright is not installed. `/verify T212` drove Chrome over raw CDP with Node's built-in `WebSocket`; that works. Read `memory/learnings.md` "Driving the site's scroll-spy in headless Chrome" (set `scroll-behavior: auto` before clicking; headless window floors ~500px).
- Regression test: put the headless check under `tests/` (e.g. `tests/site_scrollspy/test_scrollspy.mjs` run by `node --test`), and make it SKIP with a clear message when no Chrome binary is found, so CI without Chrome stays green. Add a static assertion in `tests/test_site_content.py` only if it pins real intent (e.g. the observer's top margin accounts for the header), not a magic string.
- Fix direction (confirm by diagnosis first): move the observer's top edge below the header (derive from `--header-h`/`scroll-margin-top`, not a hard-coded guess where avoidable), and on a sidebar click set the clicked link active and hold it until the next user scroll (wheel/touch/key), so (c) holds.
- Surgical: touch only the scroll-spy block (and `theme.css` only if a token is needed). No glow/colour edits (T212 owns those).

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | scroll-spy block only |
| `tests/site_scrollspy/*` (new) or `tests/test_site_content.py` | regression check |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/theme.css` colour/glow tokens | T212 |
| settings-tool script | unrelated |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

## Verification Command

```bash
node --test tests/site_scrollspy/ && python3 -m pytest tests/test_site_content.py -q && node --test tests/settings_tool/*.mjs
```

## Completion Checklist

- [ ] Diagnosis Gates checked before any fix code
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T213.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows filled (Hard-Stop Gate 6): click check per link, manual-scroll check, 375px drawer click
- [ ] Supervisor notified: task ready for Stage 4 review
