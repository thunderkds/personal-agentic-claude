# TASK_GUIDE — T201: Settings tool profiles — High security and Legacy on the Build tab, each with a "for whom" line, held equal to `profiles.json`
**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md` (registered there by `post_write_register_task.py`, as T199 was)

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC_SITE.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `PRD_settings-profiles.md` (D1, D3, D5, FR-001..FR-004, FR-008) and `tasks/TASK_GUIDE_T185.md` (Build tab design, `settings-tool-core` / node:vm test setup)
7. Read `skills/settings-setup/profiles.json` from T200 — the one source of profile values

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29, verbatim: "for the settings support section from the page, currently, we support for the generate, and checking the json settings file, but we should provide more options for users to pick". Grilling D1: "More profiles".

**Restated intent**:
> The Build tab's "Start from" bar offers named profiles: High security, Legacy, Solo engineer, Team project, Empty. Each shows a one-line "for whom" description. Their values equal `skills/settings-setup/profiles.json`, and a test fails if they drift. The section lead no longer says the kit installs no settings; it says what is true.

**Out of scope**: a question wizard; new catalog keys; Check-tab rules (T187); `profiles.json` itself (T200).

**Requirement Refs**: `PRD_settings-profiles.md` FR-001, FR-002, FR-003, FR-004 (page half), FR-008, NFR-001, NFR-002.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-29)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every AC traces to the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T200 (`profiles.json`). Branch from T200's branch, or from `main` after T200 merges.
**Entry point**: `#settings-tool` → `#st-presets`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | The catalog `presets` array holds `high-security`, `legacy`, `solo-engineer`, `team-project`, `empty`, in that order; `safe-baseline` is gone (replaced by `high-security`) | FR-001 |
| 2 | Each preset has a `for` string; the Build tab shows the active or hovered/focused profile's `for` line next to the bar (keyboard focus shows it too) | FR-001 |
| 3 | Drift test (pytest): the page's preset id set equals `profiles.json`'s id set, and for each id `generate()` of the page preset (with `$suggest` expanded) equals the profile `values` | FR-004 |
| 4 | Picking High security, target Project, gives JSON with exactly the 7 deny, 4 ask rules and `"disableBypassPermissionsMode": "disable"` under `permissions` | FR-002 |
| 5 | Legacy's output note says the kit's hooks are added by the installer, not by this file | FR-003 |
| 6 | The lead sentence "The kit installs no settings of its own." is replaced by text that is true after T200 (e.g. the installer adds only its hooks and 2 deny rules; at Stage 1 the Supervisor offers these profiles and uses High security if you skip) | FR-008 |
| 7 | NFR-001: no page preset emits `bypassPermissions`, `allow`, or `defaultMode` (test) | NFR-001 |
| 8 | Mutations RED then green: **M1** change one rule in the page `high-security`; **M2** add a preset id to the page only; **M3** restore the old lead sentence | AC 3, 6 asserted |
| 9 | Existing `tests/settings_tool/*.mjs` and `tests/test_site_content.py` pass; tests that named `safe-baseline` are updated, none deleted | regression |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | the page | 5 profiles, `for` line visible | pytest + node tests |
| 2 | 375 px and 1280 px | the preset bar and `for` line wrap, no horizontal scroll | `/verify` screenshots |

### Verification Command

```bash
node --test tests/settings_tool/*.mjs && python3 -m pytest tests/test_site_content.py -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T201.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| Build tab preset bar + `for` line | screenshot 1280 px | same `.st-btn` buttons; `for` line in muted small text like `.st-why` |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Colors | reuse existing tokens/classes | no new color |
| Typography | `for` line computed style equals `.st-why` | identical |
| Spacing | no new spacing values | reuse `.st-presetbar` gaps |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 375 px | screenshot + `scrollWidth == clientWidth` | buttons wrap, no sideways scroll |
| 1280 px | screenshot | one or two rows of buttons |

---

## Approach

**Pattern reference**: existing `presets` + `applyPreset()` (`site/index.html:801,878`) and the Replace / Keep mine confirm (T185).

**Vital slice**: two new presets + drift test + lead sentence.
**Cut list**: a profile comparison table; a "recommended" badge; URL-hash sharing.

Writing: page text follows AGENTS.md Writing Principles (ASD-STE100).

---

## Edge Case Checklist

- [ ] A user with edits picks a profile → existing confirm still shows
- [ ] `for` text uses `textContent`, never `innerHTML`
- [ ] Check tab's I1 tip still points to Build and still works (it reads `permissions.deny.suggest`, unchanged)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | catalog `presets`, `for` line render, lead sentence |
| `tests/settings_tool/test_generate.mjs` | preset tests |
| `tests/test_site_content.py` | drift test, lead test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/settings-setup/*` | T200 owns the source |
| Check-tab rules in `settings-tool-core` | T187 |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T201.md` (Hard-Stop Gate 5)
- [ ] UI / Design Evidence rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review
