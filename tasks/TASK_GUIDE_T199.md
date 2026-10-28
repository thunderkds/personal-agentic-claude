# TASK_GUIDE — T199: The site's MCPs section lists easy-memory-mcp as a third optional companion, with honest claims
**Date**: 2026-10-28
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md` (same board as its dependency T194)

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `tasks/TASK_GUIDE_T194.md` — it rewrites the `#mcps` lead and the honesty test this task builds on
7. Read `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp/README.md` (read-only) — the only source for the facts on the card

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28, verbatim: "did you add it as easy-ui and easy-verifier mcps section in the index also" and "and add it to the index alos"; earlier: "the memory-mcp just an optional, so do not force in any solution yet, it looks like 'you have it, you reduce the token, if you don't have it, no problem, we go through normal flow'".

**Restated intent**:
> The site's `#mcps` section lists easy-verifier-mcp and easy-ui-mcp as separate companion tools. Add easy-memory-mcp as a third card of the same shape. The card says it is optional and separate, that the kit works the same without it, what it does, and what is and is not proven. It claims nothing the kit does not do: the kit does not ship, install or require it.

**Out of scope** (what this task explicitly does NOT do):
- No change to the kit's agents, skills or hooks.
- No claim of a token saving on real work. The only measured figure is about 28% on scripted tests (experiment 03), and the card says so.
- No change to the two existing cards beyond what the section's count wording needs.

**Requirement Refs**: none (the kit has no `PRD.md` for this scope; the source is the user request above).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-28)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist (none needed)

---

## Dependencies & Reachability

**Depends on**: T194 (soft). T194 rewrites the `#mcps` lead and re-bases `HONESTY_PHRASES`, and it is not merged yet (it sits on branch `plan/t190-t194-companion-scoring`, behind T193). **User decision, 2026-10-28 ("run the task 199"): build now on current `main`.** Keep every edit narrow so the later merge with T194 is a small manual resolution: do not rewrite the section lead, only change the count wording; add the card and tests after the easy-ui card and its tests, as separate blocks.

**Entry point**: `id="easy-memory-mcp"`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `#mcps` holds a third `<div class="agent-card" id="easy-memory-mcp">` after the easy-ui card, with an `<h3>` naming `easy-memory-mcp` and a `lead` paragraph that contains the words `separate`, `companion` and `optional` | third card, optional |
| 2 | The card has 4 to 5 one-line `<li>` highlights, drawn only from the easy-memory-mcp README: saves answers as local notes and shows a short index next session; MCP tools `memory_search`, `memory_read`, `memory_list`, `memory_forget`; per-repo switch and an on/off report; no network or model calls, notes in clear text readable only by the user; working prototype whose ~28% token cut was measured on scripted tests, not yet on real work | honest facts |
| 3 | One highlight says the kit works the same without it (for example "Without it installed, the kit runs as before") | "no problem without it" |
| 4 | The card links to `https://github.com/thunderkds/easy-memory-mcp` with `target="_blank" rel="noopener noreferrer"` (the repo is public: HTTP 200, 2026-10-28) | link |
| 5 | The section lead and any count wording say three, not two, once, consistently. On current `main` the existing honesty test bans the word `required` anywhere in `#mcps`, so write the card without it (use `optional`, `not needed`); do not edit `HONESTY_PHRASES` (T194 owns that) | consistency |
| 6 | **Negative (mutation M1):** inserting `the kit ships with easy-memory-mcp` into `#mcps` turns the honesty test RED | honesty |
| 7 | **Negative (mutation M2):** inserting `easy-memory-mcp is required` into `#mcps` turns the honesty test RED | honesty |
| 8 | **Negative (mutation M3):** deleting the optional/runs-as-before highlight turns a test RED | AC 3 asserted, not merely permitted |
| 9 | **Negative (mutation M4):** removing the repo link turns a test RED | AC 4 |
| 10 | Every existing `#mcps` test still exists and passes, updated where the card count moved, deleted nowhere | surgical |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `site/index.html` after the change | Three cards in `#mcps`; the third matches AC 1 to 4 | `python3 -m pytest tests/test_site_content.py -q` |
| 2 | The M1 to M4 mutations applied one at a time | Each turns a test RED, and reverting turns it green | run by the agent, output pasted |
| 3 | The page opened at 1280 px and 375 px | The card renders like the other two, with no horizontal overflow and the link visible | Supervisor `/verify` with a screenshot |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T199.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T199.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#mcps` section, third card | screenshot at 1280 px, LLM vision verdict | the card matches the two existing cards (same class, spacing, heading, list, link row) |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | the card reuses `agent-card`; no new CSS | no new color or class added |
| Typography matches spec | computed style of `h3`, `.lead`, `li` equals the easy-ui card's | identical |
| Spacing / layout matches spec | computed margin and padding equals the easy-ui card's | identical |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375 px) | screenshot | no horizontal scroll, text wraps |
| Desktop (1280 px) | screenshot | three cards read in order |

---

## Approach

**Pattern reference**: the `id="easy-ui-mcp"` card in `site/index.html` and `_ui_mcp_entry_body()` with its tests in `tests/test_site_content.py` — copy the card shape and add the matching test helpers.

**Vital slice**: the card, its link, the optional highlight, and the honesty and mutation tests.
**Cut list**:
- A sidebar or nav entry for the new card: only if the other two have one (check; follow them).
- A new CSS class: none, reuse `agent-card`.

---

## Edge Case Checklist

- [ ] The current `HONESTY_PHRASES` (`the kit uses`, `ships with`, `built in`, `required`) must stay green on the new card: avoid all four phrases
- [ ] The card never says "saves X% of your tokens"; it says what was measured and on what
- [ ] If T194 changed the card wording pattern, follow T194's merged form, not this guide's draft

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | third card in `#mcps`; count wording |
| `tests/test_site_content.py` | helpers and tests for the third card; mutation tests M1 to M4 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `agents/*`, `skills/*`, `.claude/hooks/*` | the card is copy only |
| `memory/*`, `PROJECT_KANBAN.md` | the Supervisor owns them |

---

## Test Plan

Red first: write the new tests, see them fail. Add the card. Run the Verification Command. Run M1 to M4 by hand and paste each RED and green. Then `python3 -m pytest tests -q -x`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T199.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] UI / Design Evidence rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Scope addendum (user, 2026-10-28: "yes, include in this one, and push the branch")

**Finding from `/verify T199`** (not caused by T199, same on `main`): between about 768 px and 899 px wide the page scrolls sideways, because the `#hooks` table (4 columns) is 851 px wide while the content column is 753 to 785 px. Measured with headless Chrome: client width 753 px, 785 px give `scrollWidth` 851; 885 px and above give none; 600 px and below none (the table reflows to cards under 768 px). Cause: `site/index.html` has `@media (min-width: 768px) { #hooks th:nth-child(-n+2), #hooks td:nth-child(-n+2) { width: 1%; white-space: nowrap; } }`, which forbids the EVENT and MATCHER columns from wrapping.

**Design rule to keep (T167):** tables never scroll sideways inside a wrapper. `test_tables_do_not_force_a_minimum_width_or_scroll_sideways` forbids `overflow-x: auto|scroll` on `.table-wrap` and a `min-width` on `table`. Do **not** add either. Fix by letting the first two columns wrap in the 768 to 899 px band, for example by moving the `nowrap` rule to `@media (min-width: 900px)`. Pick the smallest change that makes `scrollWidth` equal `clientWidth` at 768, 800 and 899 px.

| # | Criterion (testable) |
|---|----------------------|
| 11 | At viewport widths 768, 800 and 899 px, `document.documentElement.scrollWidth` equals `clientWidth` (no horizontal scroll). Measured in headless Chrome and pasted. |
| 12 | At 1000 px and 1280 px the `#hooks` table looks as before: the EVENT and MATCHER columns do not wrap (compare `white-space` computed style: `nowrap`). |
| 13 | A new test asserts that the `nowrap` rule for `#hooks` first two columns sits in a media query whose `min-width` is at least 900px. **Mutation M5:** changing that back to 768px turns the test RED. |
| 14 | The T167 test above, the T181 tests and every existing test still pass; none deleted. |

**Files to change (added):** `site/index.html` (one CSS rule), `tests/test_site_content.py` (one test). Nothing else.
