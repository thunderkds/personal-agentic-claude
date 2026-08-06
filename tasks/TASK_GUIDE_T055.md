# TASK_GUIDE — T055: bugfix Evidence-table parity with the gate-visible implementation shape
**Date**: 2026-08-05
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from `.claude/agents/general-agent-template.md`
6. Read `docs/ddr/0003-demonstration-block-and-delivery-report.md` — this task implements decision 6

---

## Requirement (Pillar 1 — Adapt the requirement)

This task fixes a defect found while investigating the user's request:

> "start with the output validation after implementation or fixbugs"

and, on scope:

> "remember apply for the implementation and bugfix"

The implementation-flavor Evidence table in `templates/TASK_GUIDE_template.md` has 9 rows, including a
row whose Check cell is literally `verify` and whose Notes column `pre_bash_block_unsafe_merge.py`
greps for the word "pass". The bugfix-flavor Evidence table in `.claude/skills/bugfix/SKILL.md:119-124`
has **3 rows** — Repro loop / Regression test / Smoke suite — with a free-text `Result` column, **no**
`☐ pass / ☐ fail` shape, and **no `verify` row at all**.

**Restated intent**:
> The merge gate is not failing on a bugfix task; it is structurally absent. Bring the bugfix Evidence
> table to the same gate-visible shape as the implementation flavor so Hard-Stop Gates 5 and 6 have
> something to bind to on a bugfix.

**Out of scope**:
- The Demonstration block (T053) and the `delivery-report` skill (T054)
- Any change to `pre_bash_block_unsafe_merge.py` itself — this task makes the *guide* match what the
  gate already looks for; it does not change the gate
- Retrofitting Evidence tables into already-closed bugfix guides

**Requirement Refs**: DDR-0003 decision 6 and defect 3.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist and are fully covered by the Acceptance Criteria above

---

## Dependencies & Reachability

**Depends on**: None — independent defect, independently valuable. May land before, after, or in
parallel with T053/T054.

**Entry point**: `.claude/skills/bugfix/SKILL.md` Step 3 guide skeleton, `### Evidence` table

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The bugfix Evidence table contains a row whose Check cell is exactly `verify` immediately before the `\|` delimiter | recorded: "verify Evidence-row gate regex" |
| 2 | That row's Notes column carries the same guidance as the implementation template — the reviewer must literally write "pass" or "fail" there, because the gate scans the Notes column, not the Result column | recorded: T026's two compounding bugs, undocumented until then |
| 3 | The table uses the `☐ pass / ☐ fail` cell shape, matching the implementation flavor | consistency across flavors |
| 4 | Rows added for: new tests cover acceptance criteria, negative cases, review scope bounded to blast radius, full smoke suite green | Hard-Stop Gate 5 |
| 5 | The three UI rows are present with explicit `☐ N/A` defaults and a note that a UI-affecting bugfix must fill them | Hard-Stop Gate 6 |
| 6 | The existing 3 bugfix-specific rows (Repro loop, Regression test, Smoke suite) are preserved, not replaced | the bugfix flavor's own diagnostic value |
| 7 | `pre_bash_block_unsafe_merge.py` is demonstrably able to find the `verify` row in a bugfix guide generated from the updated skeleton — shown by a test, not by inspection | recorded: "An assertion never observed failing is not evidence" |
| 8 | Step 5's review-gate wording is updated to reference the expanded row set | `.claude/skills/bugfix/SKILL.md:150` |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A bugfix guide generated from the updated skeleton, `verify` row Notes containing "pass" | `trace_shows_verification` / the gate's Evidence check resolves True | automated test |
| 2 | The same guide with the `verify` row Notes left blank | Gate resolves False — merge would be refused | automated test |
| 3 | The same guide with "pass" written in the **Result** column but not the Notes column | Gate resolves False — this is the exact T026 defect, and it must stay caught | automated test |
| 4 | An old bugfix guide with the original 3-row table | Gate resolves False (as it does today) — no silent retro-pass | automated test |
| 5 | Full existing suite | Still green | `python3 -m pytest .claude/hooks/tests -q` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_bugfix_evidence_parity.py` — 5 tests driving the real `pre_bash_block_unsafe_merge` gate end-to-end, not a re-implemented regex: SC1–SC4 plus AC7 against the literal SKILL.md skeleton text |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `159 passed in 1.38s`, re-run by the Supervisor from the main checkout after integration (the agent's own `151 passed` predates T053's 8 tests) |
| Negative cases hold | ☑ pass | SC2 blank `verify` Notes → blocked. SC3 (the T026 regression — "pass" in the Result column but not Notes) → blocked. SC4 old 3-row guide → still blocked, no silent retro-pass |
| verify | ☑ pass | Independently mutation-tested by the Supervisor rather than trusting the agent's report: renaming the `verify` Check cell to `verifyX` in the skeleton produced `1 failed, 158 passed` (RED at test_bugfix_evidence_parity.py:228), restore → `159 passed` — pass |
| Review scope bounded to the change's blast radius | ☑ pass | 2 files: `.claude/skills/bugfix/SKILL.md` (Evidence table + Step 5 wording) and the new test file. `pre_bash_block_unsafe_merge.py` untouched — this task makes the guide match the gate, not the reverse |
| Full smoke suite still green (no regression) | ☑ pass | `159 passed`, no pre-existing test modified |
| **UI: Visual regression** | ☐ N/A | Pure process/text task — no UI component |
| **UI: Design-system compliance** | ☐ N/A | Pure process/text task — no UI component |
| **UI: Responsiveness** | ☐ N/A | Pure process/text task — no UI component |

---

## Demonstration

**BEFORE** (verbatim prior content — non-executable): the Evidence table at
`.claude/skills/bugfix/SKILL.md:119-124` reads in full:

```
### Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop | | |
| Regression test | | |
| Smoke suite | | |
```

No `verify` row exists, so the merge gate's Evidence check cannot resolve True for any bugfix task.
Confirm with: `grep -c '| verify |' .claude/skills/bugfix/SKILL.md` → expect `0`.

**BEFORE** (executable half): run the gate's Evidence check against a bugfix guide generated from the
current skeleton and capture the `False` result before any change.

**BEFORE captured by the Stage 3 agent, pre-implementation** (2026-08-06):
```
$ grep -c '| verify |' .claude/skills/bugfix/SKILL.md
0
```
The gate's Evidence check therefore could not resolve True for any bugfix task — structurally absent,
not failing.

**AFTER**: same `grep` returns `1`; the gate's check resolves True for a properly-filled bugfix guide
(SC1) and still False for the three negative cases (SC2–SC4).
```
$ grep -c '| verify |' .claude/skills/bugfix/SKILL.md
1
$ python3 -m pytest .claude/hooks/tests -q
159 passed in 1.38s
```
The bugfix Evidence table went from 3 free-text rows to 12 gate-visible rows: the 9-row implementation
shape plus the 3 preserved bugfix-specific rows (Repro loop / Regression test / Smoke suite).

**DELTA**: a bugfix task is now subject to the same merge gate as an implementation task — the gate
stops being structurally absent on half of all work.

**WITNESS**: Not the implementing agent alone — the Stage 3 agent wrote the table and tests but was
killed by the step-limit hook before filling any evidence. The Supervisor independently re-ran the
suite and the RED-then-GREEN mutation cycle from the main checkout on branch
`docs/stage2-demonstration-block-t053-t055`. Trace: `memory/event-trace/T055.jsonl`.

---

## Approach

**Pattern reference**: `templates/TASK_GUIDE_template.md`, the 9-row Evidence table — copy its row set
and cell shape exactly, then append the three bugfix-specific rows that have no implementation
equivalent. Copying rather than inventing is deliberate: the gate's regex was written against that
exact shape, and this hook family has produced 6 recorded parsing defects from small divergences.

The critical subtlety, recorded from T026 and undocumented before it: the gate requires the word
"pass" in the **Notes** column, not the Result column, and requires the Check cell to be exactly
`verify` immediately before the `|`. AC2 and SC3 exist specifically to keep that distinction alive
rather than rediscovering it a seventh time.

Note that `templates/TASK_GUIDE_template.md`'s own example verify row historically did **not** match
the gate regex (the T026 follow-up). Confirm the current template row actually matches before copying
it — do not assume the template is correct.

---

## Edge Case Checklist

- [ ] Copying the template's example verify row verbatim reproduces the T026 defect if that example is still wrong — verify the template first
- [ ] The word "pass" appears in the Result column but not the Notes column (SC3) — must stay caught
- [ ] An old bugfix guide silently starts passing the gate after this change — must not happen (SC4)
- [ ] Table markdown alignment drifts and the gate's column split misreads cells
- [ ] `.claude/skills/bugfix/SKILL.md` is already 169 lines, past the ~150-line `slim-skills` baseline; this addition grows it further — a necessary increase, but note it for a future `slim-skills` pass
- [ ] The expanded table conflicts textually with T053's Demonstration insertion into the same file — sequence the merges or expect a conflict
- [ ] A UI-affecting bugfix defaults its three UI rows to `N/A` and skips Hard-Stop Gate 6 — the note in AC5 must make the obligation explicit

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/bugfix/SKILL.md` | Expand the Step 3 Evidence table to gate-visible parity; update Step 5 wording |
| `.claude/hooks/tests/` | New tests for SC1–SC4 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | This task makes the guide match the gate, not the reverse |
| `templates/TASK_GUIDE_template.md` | T053 owns it; this task only reads it as a pattern reference |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Test Plan

Automated tests for SC1–SC4 against the real gate function, using guides generated from the updated
skeleton. SC3 is the T026 regression and is the most important of the four — it is the case that
looks correct to a human reader and fails the gate. Mutation-check each assertion: break the `verify`
row, confirm RED, restore, confirm GREEN. Commit before mutating.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — Medium risk, mandatory
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Demonstration block filled, BEFORE captured before the first implementation commit
- [ ] Supervisor notified: task ready for Stage 4 review
