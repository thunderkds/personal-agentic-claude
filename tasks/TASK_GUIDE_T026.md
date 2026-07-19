# TASK_GUIDE — T026: Fix TASK_GUIDE_template.md example `verify` Evidence row
**Date**: 2026-07-19
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. C0, single-file text fix — codebase-map not required

---

## Requirement (Pillar 1 — Adapt the requirement)

`.claude/hooks/pre_bash_block_unsafe_merge.py`'s Evidence-row gate regex is `verify\s*\|[^|\n]+\|[^|\n]*pass` — it requires the literal word `verify` immediately followed (after only whitespace) by a `|`. `templates/TASK_GUIDE_template.md`'s own example Evidence row reads `` | `verify` skill — works in running app | ☐ pass / ☐ fail / ☐ N/A | ... `` — the text "skill — works in running app" sits between "verify" and the pipe, so this regex never matches it. Every new task guide generated from this template inherits a row that cannot pass the merge gate until manually rewritten — discovered live blocking T025's merge twice (see `memory/learnings.md`, 2026-07-16 entry).

**Restated intent**:
> Edit the template's example Evidence row so the Check-column cell is exactly `` `verify` `` immediately before the `|`, matching the working convention already used successfully in this session's T028/T029 Evidence tables (`` | verify | ☑ pass | ... ``).

**Out of scope**:
- Does not touch `.claude/hooks/pre_bash_block_unsafe_merge.py` itself — the regex is correct; the template's example text is wrong.
- Does not touch any already-generated `tasks/TASK_GUIDE_T0*.md` files — this is a template-only fix; existing guides are unaffected.
- Does not touch the other Evidence rows (New tests, Verification command, Negative cases, UI rows) — only the `verify` row's Check-column wording.

**Requirement Refs**: N/A — internal framework fix, same precedent as T018/T024 (regex/template bugs, no `PRD.md` FR).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the observed live bug (Supervisor, confirmed via direct regex test against the gate)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (no new terms)
- [x] Every Acceptance Criterion below traces to the requirement
- [x] Requirement Refs: N/A precedent confirmed

---

## Dependencies & Reachability

**Depends on**: `None`
**Entry point**: `Standalone — N/A`: this is a template file consumed by the Supervisor at Stage 2 guide-generation time, not code reachable via a route/function/consumer.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The `verify` row's Check-column cell in `templates/TASK_GUIDE_template.md` reads exactly `` `verify` `` (or `verify`) immediately followed by `\|`, with no other text between the word and the pipe | "Check-column cell is exactly `verify` immediately before the `\|`" |
| 2 | The row's Result/Notes columns still document what to observe (moved out of the Check column, not deleted) | preserves the original guidance content |
| 3 | The edited row matches `pre_bash_block_unsafe_merge.py`'s gate regex when the Result cell contains "pass" | gate compatibility |
| 4 | No other Evidence row is modified | Out of scope — only the verify row |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The edited template's verify row, with Result cell filled "pass" | `re.search(r"verify\s*\|[^|\n]+\|[^|\n]*pass", row, re.IGNORECASE)` matches | automated test |
| 2 | The template's OLD row text (regression guard, kept as a negative fixture) | The old text still fails to match (proves the test actually distinguishes fixed from broken) | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_task_guide_template_verify_row.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_task_guide_template_verify_row.py` — 4 tests: fixed row matches gate, Result-column-only "pass" is NOT sufficient (2nd bug found beyond original scope), old broken row still fails (negative fixture), fixed text present in template file |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/test_task_guide_template_verify_row.py -q` → `4 passed in 0.02s` |
| Negative cases hold | ☑ pass | Old broken row confirmed still fails the gate; Result-column-only "pass" (no "pass" in Notes) also confirmed to fail, proving the fix required both changes |
| verify | ☑ pass | Extracted the REAL regex directly from `.claude/hooks/pre_bash_block_unsafe_merge.py` source (not a mirrored copy) and ran it against a realistically-filled row matching the fixed template's example — matched |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff isolated to `templates/TASK_GUIDE_template.md` (1 row) + new test file; no existing `tasks/TASK_GUIDE_T0*.md` touched (explicitly out of scope) |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ -q` → `24 passed in 0.03s` (20 pre-existing + 4 new) |
| **UI: Visual regression** | ☐ N/A | pure text/template task |
| **UI: Design-system compliance** | ☐ N/A | pure text/template task |
| **UI: Responsiveness** | ☐ N/A | pure text/template task |

---

## Approach

Change the row from:
```
| `verify` skill — works in running app | ☐ pass / ☐ fail | [what was observed] |
```
to:
```
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — e.g. "skill run, feature confirmed working in running app"] |
```
This moves the "skill — works in running app" guidance text into the Notes column (where it still documents intent) while making the Check-column cell match the gate's literal-`verify`-then-`|` requirement — same shape as the convention already proven working in this session's T028/T029 Evidence tables.

---

## Edge Case Checklist

- [ ] Confirm the fix doesn't accidentally break the *other* rows' Check-column text (e.g. "New test(s) cover..." row) — only the verify row changes
- [ ] The regex is case-insensitive (`re.IGNORECASE`) — `Verify` or `VERIFY` would also match; template can keep lowercase `verify` for consistency with the convention already in use
- [ ] Existing already-generated task guides (T001–T035) are NOT retroactively fixed by this change — flag as explicitly out of scope, not silently promised

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_GUIDE_template.md` | Fix the `verify` row's Check-column text |
| `.claude/hooks/tests/test_task_guide_template_verify_row.py` | new — regression test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | The gate regex is correct; only the template's example text is wrong |
| Any `tasks/TASK_GUIDE_T0*.md` | Out of scope — template-only fix, not retroactive |

---

## Test Plan

Pytest: (1) fixed row text matches the gate regex when Result="pass"; (2) old/broken row text does NOT match (negative fixture, proves the test is meaningful).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — confirm via a throwaway generated guide against the real gate script
- [ ] Supervisor notified: task ready for Stage 4 review
