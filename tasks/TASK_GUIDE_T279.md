# TASK_GUIDE — T279: The Home and Docs links in the top nav are 44px wide on phones
**Date**: 2026-11-07
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt
3. Read this file completely
4. Read `agents/frontend.md`
5. Read `skills/ux-evaluate/SKILL.md` (check B-d) and run its `scripts/tap_probe.py`
6. Read `site/theme.css` lines 285–306 (the phone block) and `tests/test_site_content.py` lines 1984–1994 (`test_touch_targets_reach_44px_below_720px`)
7. Read `memory/learning-records/LR-0004-pin-tests-hit-later-tasks.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Found in T278 Stage 4 (`ux-evaluate`, check B-d, 2026-11-07): at 375px the tap probe reports `2 under 44px: Home 38x44; Docs 31x44`. Both are the `.page-nav` links in the top header of `site/docs.html` and `site/index.html`. User, 2026-11-07: *"yes, let update, merge and push [auto]"* answering the Supervisor's offer to register a task for these links. Auto mode: the Supervisor merges and pushes nothing.

**Restated intent**:
> Every tap target in the site header is at least 44 by 44 px at 375px. The height is already 44px (`theme.css` line 302); the width is not. The two links get a minimum width of 44px on phones.

**Out of scope** (what this task explicitly does NOT do):
- Any change to desktop or tablet layout (above 719px)
- The family-nav, the brand, the menu button, the sidebar (already 44px, or not in the probe's list)
- Any new color, font or spacing token

**Requirement Refs**: None — follow-up to T278 `ux-evaluate` finding B-d.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor))
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (auto (Supervisor))
- [x] Every Acceptance Criterion below traces to a line in the Requirement (auto (Supervisor))
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above (none claimed)

---

## Dependencies & Reachability

**Depends on**: T278 — merged (`07d70c4e`); it found the defect. No code dependency.

**Entry point**: `.page-nav a` in `site/theme.css`, inside `@media (max-width: 719px)`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | In the `@media (max-width: 719px)` block of `site/theme.css`, a rule for `.page-nav a` sets `min-width: 44px` and centres the label (`justify-content: center`) | "at least 44 by 44 px" |
| 2 | `python3 skills/ux-evaluate/scripts/tap_probe.py <abs path of site/docs.html> <dir>` and the same for `site/index.html`, shot at 375px, print a banner that does not list `Home` or `Docs`, for both pages. (The probe scans the whole page and also lists body links, journey cards and Settings-tool controls; those are out of scope. Reworded 2026-11-07 [auto], Supervisor: the first wording, `0 under 44px`, came from a scratch copy that hid every other section.) | Requirement |
| 3 | No rule outside the `@media (max-width: 719px)` block changes; the page at 1280px is pixel-for-pixel the same header (screenshot compared by eye, no layout shift) | Out of scope |
| 4 | At 375px the header does not scroll sideways, and the brand, `Home`, `Docs` and `Menu` all show on one row or wrap cleanly with no clipping | B-h |
| 5 | The existing site tests pass with no edit to a baseline or pin, except the one test this task extends (see Files) | LR-0004 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `site/theme.css` after the change | the phone block has a `.page-nav a` rule with `min-width: 44px` | automated test (new, `tests/test_t279_nav_tap_targets.py`) |
| 2 | Tap probe at 375px on both pages | the banner no longer lists `Home` or `Docs`, and no red box shows on them | tap_probe run, output pasted |
| 3 | Mutation: delete the `min-width: 44px` declaration | the new test fails | mutation control, run by the reviewer |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_t279_nav_tap_targets.py tests/test_site_content.py tests/test_site_story.py tests/test_site_visual_first.py tests/test_docs_t151.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T279.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T279.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| Site header, `docs.html` and `index.html` at 375px and 1280px | LLM-vision screenshot (`ux-evaluate`) | 1280px header unchanged; 375px header keeps one row of brand, Home, Docs, Menu |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | CSS audit | No new color |
| Typography matches spec | computed style | `Home` and `Docs` keep the same font and size |
| Spacing / layout matches spec | computed style | Only `min-width` and `justify-content` added, inside the phone block |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375px) | Playwright or headless Chrome screenshot, tap probe | `Home` and `Docs` are 44px wide and not in the banner; no sideways scroll |
| Tablet (768px) | screenshot | Header unchanged (the rule sits in the 719px block) |
| Desktop (1280px) | screenshot | Header unchanged |

### 4. UX Acceptance Criteria

| User story | User goal | Flow / state | Pass condition (observable) |
|------------|-----------|--------------|-----------------------------|
| Request: "update" (T278 B-d finding) | Tap Home or Docs with a thumb without missing | Open either page at 375px | The tap probe banner does not list `Home` or `Docs`, and no red box shows on them |

---

## Approach

**Pattern reference**: `site/theme.css` line 301 — `.family-nav a { min-height: 44px; }` in the same phone block. Extend line 302's existing `.page-nav a` rule (do not add a second rule for the same selector).

**Vital slice**: add `min-width: 44px; justify-content: center;` to the existing `.page-nav a` rule at line 302, and extend `test_touch_targets_reach_44px_below_720px` or add the new test file for the width.
**Cut list**: Padding on the links (a min-width is enough); a change to the family-nav; a pin change.

Why the old test missed it: `test_touch_targets_reach_44px_below_720px` checks only `min-height: 44px`, never width.

---

## Edge Case Checklist

- [ ] `index.html` and `docs.html` share the header markup and `theme.css`; probe both
- [ ] The brand-wrap uses `min-width: 0` and may shrink: confirm `Menu` is not pushed off screen at 375px
- [ ] `aria-current="page"` underline on `Docs` still shows after centring
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep `tests/` and `docs/claude-md/` for "44px" claims that now need width too; fix only inside `Files to Change`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/theme.css` | `.page-nav a` rule at line 302: add `min-width: 44px; justify-content: center;` |
| `tests/test_t279_nav_tap_targets.py` | New: AC 1 as a test, with the mutation control |
| Pre-existing pin tests | `tests/test_site_content.py::test_touch_targets_reach_44px_below_720px` (checks min-height only; stays green); CSS-pin tests in `tests/test_site_content.py` (no gradient, no uppercase, shadow tokens: unaffected); `tests/test_site_visual_first.py` (sentence hashes of page text: unaffected, no text change). Handling: none expected; escalate if one fails |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/docs.html`, `site/index.html` | Markup is not the defect |
| `skills/**`, `memory/**` | Out of scope |

---

## Test Plan

1. Write `tests/test_t279_nav_tap_targets.py` first (red: no `min-width` on `.page-nav a`).
2. Edit the one rule in `site/theme.css` (green).
3. Run the Verification Command.
4. Run `tap_probe.py` on both pages and shoot them at 375px; run `ux-evaluate` for the screenshots at 375px and 1280px.
5. Mutation: remove `min-width: 44px`; the test must fail. Restore it.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T279.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] UI Evidence rows (visual, design-system, responsiveness) filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
