# TASK_GUIDE — T166: The Skills section shows a stage flow with skill chips
**Date**: 2026-10-20
**Complexity Level**: C1 — one section's markup + CSS, plus drift tests
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
6. Read `site/index.html` (the `#skills` section, its CSS at `.skill-groups`/`.skill-group`, the `#quick-reference` card and the pipeline SVG in `#what-you-get` for style) and `tests/test_site_content.py` (skill, nav and T165 tests)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-20, after viewing T165's page locally: *"for skills sections, you can draw the flow through stage to show up more visualize"* — then chose **"Stage flow + chips"** from a mock: stage boxes joined by arrows, each holding its skills as small chips; a band underneath for the cross-cutting skills; left-to-right on wide screens, stacked on phones; built in HTML/CSS so skill names stay real text.

**Restated intent:**
> Replace the `#skills` section's plain per-stage lists with a visual flow: one box per stage
> (0.5 → 1 → 1.5 → 2 → 3 → 4 → 5) joined by arrows in stage order, each box holding that stage's
> skills as chips. The 13 cross-cutting skills sit in one full-width "Any stage" band below the flow.
> On a wide screen the boxes run left to right and wrap onto further rows as needed; at phone width
> they stack top to bottom with downward arrows. Same skills, same grouping as today — only the
> presentation changes.

**Grouping is unchanged (source of truth = the current page):** 0.5 brainstorming, ideate · 1 git-guardrails-claude-code, map-codebase · 1.5 craft-agent · 2 grill-with-docs, to-issues · 3 tdd, bugfix, diagnose, craft-spawn-prompt, migration-safety · 4 blast-radius, code-review, html-report · 5 ship, delivery-report · cross-cutting: the other 13.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user picked "Stage flow + chips" from the mock, 2026-10-20)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md` glossary (*Skill*, pipeline stage)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: T165 (same branch `feat/t165-site-scan-first`; builds on its page)

**Entry point**: `site/index.html` `#skills`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `#skills` holds an ordered flow (e.g. `<ol class="skill-flow">`) with exactly one step per pipeline stage 0.5–5, in the same order as `_pipeline_stage_numbers()` minus Phase 0 — derived in the test, not hardcoded | flow through stages |
| 2 | Each step shows its stage number + short name and its skills as chips (`<li>` or `<span class="chip">`, plain text, no SVG `<text>`) | chips |
| 3 | Arrows between consecutive steps are visual only (CSS pseudo-elements or `aria-hidden="true"` elements), so a screen reader reads a plain ordered list; the flow has an accessible name | accessible |
| 4 | A separate "Any stage" band below the flow holds the cross-cutting skills | cross-cutting band |
| 5 | Every skill directory under `skills/` appears **exactly once** in `#skills` (flow + band), and every chip names a real skill dir — both directions, derived from `skills/` | drift constraint |
| 6 | The grouping matches the Requirement's list (test may assert stage → skill set from that list; this is the one place the grouping is pinned) | grouping unchanged |
| 7 | All existing `tests/test_site_content.py`, `tests/test_docs_t151.py`, `tests/test_docs_match_installer.py` assertions stay green, including T165's AC1/AC2 caps | no regression |
| 8 | New tests for AC1–AC6, observed RED before the page change | Gate 5 |

**Mutation controls:** **M1** — swap the order of steps 3 and 4 → AC1 RED. **M2** — duplicate `tdd` into step 4 → AC5 RED. **M3** — rename a chip to a non-existent skill → AC5 RED. **M4** — drop the cross-cutting band → AC4/AC5 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T166.md`. BEFORE: the verbatim current `#skills` section markup.

---

## UI / Design Acceptance Criteria

- Reuse existing tokens only (`--surface`, `--surface2`, `--border`, `--cyan`, `--purple`, `--muted`, …); stage headings may keep the current purple label style; arrows in `--cyan` to echo the pipeline SVG. No new colors, fonts, images, scripts or external assets.
- Wide (≥ ~900px content): boxes flow left to right and wrap onto rows; arrows point right. ≤ the page's existing mobile breakpoint: one column, arrows point down.
- 375px: no horizontal page scroll; long chips (`git-guardrails-claude-code`) wrap or shrink inside their box.
- No new JavaScript.

---

## Approach

**Pattern reference**: `.quick-ref` card and `.skill-group` box styling; `svg.pipeline` arrow colour.

**Vital slice**: AC1, AC2, AC4, AC5. **Cut list**: per-skill tooltips or descriptions; links from chips to docs; animation; reusing the SVG diagram.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | `#skills` markup + CSS (replace `.skill-groups` rules if unused) |
| `tests/test_site_content.py` | AC1–AC6 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | Deploy config unchanged |
| `.claude/hooks/**`, `skills/**`, `agents/**` | No harness change in scope |
| `README.md`, `memory/**`, `PROJECT_KANBAN*.md` | Out of scope / Supervisor-only |

---

## Completion Checklist

- [ ] New AC1–AC6 tests observed RED first, then GREEN
- [ ] M1–M4 results pasted in the review's "Negative cases hold" row
- [ ] All three UI Evidence rows filled (screenshots at 1280px and 375px)
- [ ] `/verify` — user-run
