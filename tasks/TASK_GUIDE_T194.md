# TASK_GUIDE — T194: The site says the kit can call both servers and requires neither, and the test stops banning the true sentence
**Date**: 2026-10-28
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt
3. Read this file completely, then `docs/prd/PRD_companion-scoring.md` (FR-012)
4. Read `agents/frontend.md`
5. Read `tasks/TASK_GUIDE_T168.md` (the `#mcps` section as built), `TASK_GUIDE_T135.md` and `TASK_GUIDE_T165.md` (the honesty constraint's history, and the mutation controls that enforce it)
6. Read `tests/test_site_content.py` lines 759–855 — the T135/T165/T168 tests, `HONESTY_PHRASES` at line 820, and `test_mcps_section_says_separate_and_never_claims_kit_integration`
7. Read the **shipped** `skills/score/SKILL.md` and `skills/ui-test/SKILL.md` (T191, T192). The copy describes what shipped, never what was planned

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28: *"if you use verifier mcp, and ui to check, the code must pass them. if not, just
work on the normal flow, that all"*.

**Restated intent**:
> Until now the site truthfully said the kit uses neither companion server. After T190–T193 that is
> no longer true: the kit can call both, and binds their result when it does. The `#mcps` copy says
> exactly that — can call, never requires — and the test that guards the section stops banning the
> honest wording while still catching an overclaim.

**Out of scope**:
- The `#verifier` element id, the nav order, the section position, or the existing highlight lists.
  T165 and T168 fixed all of those and old links depend on `id="verifier"`.
- Adding a link to either server's site beyond the two already present.
- Any claim that the kit ships, bundles, installs or requires either server. It does none of those.
- Deleting any existing test. The T135/T165/T168 tests are **updated**, never removed.

**Requirement Refs**:
- FR-012: the `#mcps` copy and its honesty test change together

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor)
- [x] Domain terms align with the glossary — **Companion score** and **evaluate gate** are defined in `PROJECT_SPEC.md` by T193; use them as written there
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `docs/prd/PRD_companion-scoring.md` and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: T193 — the glossary defines the two terms this copy uses, and the doctrine is the source for what the kit now claims.

**Entry point**: `id="mcps"`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The `#mcps` section lead no longer says the two servers are "not part of this kit" in a way that denies any use, and instead states both facts: the kit can call them through two optional Stage 4 skills, and it requires neither | FR-012 |
| 2 | Each entry keeps the word `separate` and the word `companion` in the section lead — `test_mcps_section_says_separate_and_never_claims_kit_integration` reads both, and both are still true: the servers are separate repositories the operator runs | FR-012 |
| 3 | `HONESTY_PHRASES` is re-based: it still fails on a claim that the kit **ships with**, **bundles**, **installs** or **requires** either server, and it no longer fails on the true sentence "requires neither" / "never required" | FR-012 |
| 4 | **Negative case (mutation M1):** inserting `the kit ships with easy-verifier-mcp` into `#mcps` turns the honesty test RED | FR-012 |
| 5 | **Negative case (mutation M2):** inserting `easy-ui-mcp is required` into `#mcps` turns the honesty test RED | FR-012 |
| 6 | **Negative case (mutation M3):** deleting the sentence that says the kit requires neither turns a test RED — the honest claim is asserted, not merely permitted | FR-012 |
| 7 | **Negative case (mutation M4):** removing either repo link turns the existing T168 link tests RED (unchanged behaviour, re-verified) | FR-012 |
| 8 | The verifier entry keeps `id="verifier"` and both its links; the easy-ui entry keeps its repo link, each `target="_blank" rel="noopener noreferrer"` | FR-012 |
| 9 | Each entry gains at most one new highlight line naming what the kit does with that server (the Companion score row for the verifier, the three UI design rows for easy-ui). The existing highlight counts the T168 tests assert (4–5 per entry) still hold | FR-012 |
| 10 | Every T135, T165 and T168 test still exists and passes — updated where the copy moved, deleted nowhere | FR-012 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The page as shipped | `#mcps` states both facts (can call, requires neither); no overclaim | automated test |
| 2 | Each of mutations M1–M4 applied in turn, the suite run, the page restored | RED each time, with the mutation named in the Evidence row | automated test, one run per mutation |
| 3 | The page served and read at 1280 px and 375 px | the section renders with no horizontal overflow and no clipped text | easy-ui session (`ui-test`) |

> The mutation set is the Supervisor's oracle. It is specified here, before the agent starts, so the
> agent cannot choose mutations its own copy happens to survive.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q && sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T192.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T192.md`.

---

## UI / Design Acceptance Criteria

> This task changes a rendered page, so Hard-Stop Gate 6 applies and all three rows must be filled.
> `ui-test` (T192) is the preferred method here — it is the first real use of the skill this feature
> ships. If the easy-ui container is not running, a headless-Chrome screenshot pass is acceptable;
> manual inspection is not, because this is a C1 task.

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#mcps` section, both entries | `ui-test` session + screenshot, compared against the page before the change | Only the lead paragraph and one highlight per entry differ; layout, card structure and link styling unchanged |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | computed style via the session, against a neighbouring Reference section | Same token values as `#memory-system`; no new hex literal introduced |
| Typography matches spec | computed style of the new lead and highlight | Same font-family, size and weight as the existing lead and `<li>` elements |
| Spacing / layout matches spec | computed margin and padding of the changed nodes | Unchanged from the sibling cards |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (320–480px) | `ui-test` at 375 px | No horizontal overflow; the longer lead wraps without clipping |
| Tablet (768px) | `ui-test` at 768 px | Cards stack or sit side by side as the existing Reference sections do |
| Desktop (1024px+) | `ui-test` at 1280 px | Identical to today apart from the changed text |

---

## Approach

**Pattern reference**: `site/index.html`'s `#mcps` section as T168 built it, and the neighbouring
`#memory-system` section for the Reference-group card idiom. Change text inside the existing
structure; add no new element type, no new class, no new colour.

**The test is the harder half.** `HONESTY_PHRASES = ("the kit uses", "ships with", "built in",
"required")` bans substrings. Two of those four are now wrong: the kit *does* use these servers
optionally, and the honest sentence contains `required`. Re-base the list so it catches the
**overclaim** rather than the **word** — for example by asserting a required-sounding claim in
context (`is required`, `requires easy-`, `ships with`, `bundled`) and by separately asserting that
the true disclaimer is present (AC 6). A blocklist that bans the honest sentence is the failure this
AC exists to prevent, and it already happened once: the list was written when the honest sentence was
the opposite one.

**Vital slice**: the lead paragraph, one highlight per entry, and the re-based test.

**Cut list**: no new section, no diagram, no screenshots embedded in the page, no change to the nav.

---

## Edge Case Checklist

- [ ] `test_mcps_section_says_separate_and_never_claims_kit_integration` reads the lead for both `separate` and `companion` — keep both words or that test goes red for the wrong reason
- [ ] The T168 tests assert 4–5 highlights per entry; adding two would break them
- [ ] `id="verifier"` is kept for old inbound links (T168 AC 2)
- [ ] A re-based blocklist that is now too loose — AC 4 and AC 5 are what prove it is still tight
- [ ] The nav order assertions (`#mcps` right after `#memory-system`, `#options` after `#mcps`) are position tests; do not move the section
- [ ] The site's version labels are parsed from the RUNBOOK's Release Log at test time (T104) — unrelated, do not touch
- [ ] The copy must not promise a score for every task; the row is optional and extended-track only

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | `#mcps` lead paragraph; one new highlight per entry |
| `tests/test_site_content.py` | `HONESTY_PHRASES` re-based; the honesty test updated; a new assertion for AC 6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/index.html` outside `#mcps` | Scope lock. Other sections have their own tests and tasks |
| The nav, the section order, `id="verifier"` | T165/T168 assert all three |
| `AGENTS.md`, `docs/claude-md/**`, `PROJECT_SPEC.md` | T193 |
| `skills/**`, `.claude/hooks/**` | T190–T192 |
| `RUNBOOK.md` version labels | T104's test parses them at test time |

---

## Test Plan

1. Update `tests/test_site_content.py` and run it alone, then the full suite.
2. Run each of M1–M4 in turn: apply the mutation, run the suite, record the RED, restore the page.
   Paste one line per mutation into the Evidence row, as T168 did.
3. `ui-test` session at 375 px, 768 px and 1280 px for the three UI rows; paste the verdict and the
   report path.
4. `sh scripts/validate.sh`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: ☐ N/A — Low risk, static copy and a test
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T192.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] **All three UI Evidence rows filled with pasted evidence** (Hard-Stop Gate 6 — this task has a UI component; ☐ N/A is not available)
- [ ] `memory/MEMORY.md` updated
- [ ] Supervisor notified: task ready for Stage 4 review
