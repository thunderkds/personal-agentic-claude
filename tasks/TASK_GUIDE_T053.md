# TASK_GUIDE — T053: Demonstration block in both guide flavors + spawn-time blank-BEFORE warning
**Date**: 2026-08-05
**Complexity Level**: C2
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
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Read `docs/ddr/0003-demonstration-block-and-delivery-report.md` — this task implements decisions 1, 2 and 5 of that DDR
7. C2 task: read `memory/codebase-map.md` for directory layout and blast-radius hotspots

---

## Requirement (Pillar 1 — Adapt the requirement)

Original user request, verbatim:

> "start with the output validation after implementation or fixbugs, we should have number or the
> checklist to validation the list"

and, when told the checklist looked generic:

> "I means is it good to show off the whole implementation or the bugs fix"

and, on choosing the direction:

> "c is good, but remember apply for the implementation and bugfix"

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Every task — implementation *and* bugfix — must carry a **Demonstration** block that anchors what it
> delivered to an observable before/after pair, so a reader can see the outcome rather than a row of
> ticked conformance checkboxes.

**Out of scope** (what this task explicitly does NOT do):
- The `delivery-report` skill and `templates/delivery_report_template.html` — that is T054
- Bugfix Evidence-table parity (the missing `verify` row) — that is T055
- Any change to `pre_bash_block_unsafe_merge.py`; merge blocking is deliberately deferred per DDR-0003
- Any change to `templates/report_template.html` or `.claude/skills/html-report/SKILL.md`

**Requirement Refs**: no `PRD.md` FR covers Supervisor process artifacts; traceability is to
DDR-0003 decisions 1, 2 and 5, and to the user's literal words above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary — `Demonstration` and `BEFORE capture` were added there 2026-08-05
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked.

---

## Dependencies & Reachability

**Depends on**: None — can start immediately

**Entry point**: `## Demonstration` — the literal H2 heading added to `templates/TASK_GUIDE_template.md` and to the bugfix guide skeleton in `.claude/skills/bugfix/SKILL.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_GUIDE_template.md` contains a `## Demonstration` section with exactly the four fields BEFORE / AFTER / DELTA / WITNESS | "apply for the implementation" |
| 2 | The bugfix guide skeleton emitted by `.claude/skills/bugfix/SKILL.md` Step 3 contains the same four fields, in the same order, with the same field names | "and bugfix" |
| 3 | The bugfix flavor's BEFORE field explicitly names its Phase 1 repro loop as the source, and does not create a second competing copy of it | DDR-0003 edge case: one source of truth |
| 4 | Neither flavor offers an `N/A` option on BEFORE; the block states the executable rule (pasted timestamped capture) and the non-executable rule (verbatim prior-content excerpt) | DDR-0003 decision 2 |
| 5 | `.claude/skills/craft-spawn-prompt/SKILL.md` instructs the spawned agent to capture BEFORE prior to any implementation commit | DDR-0003 decision 5 |
| 6 | `pre_agent_validate_guide.py` emits a **non-blocking** warning when a referenced guide's Demonstration BEFORE field is empty, in the same style as its existing `Depends on` warning | DDR-0003 decision 5 |
| 7 | The hook's fail-open behavior is preserved — a malformed or missing guide never blocks a spawn | `.claude/agents/general-agent-template.md`; 6 recorded defects in this hook family |
| 8 | Adding the new H2 does not change any existing hook's parse of a TASK_GUIDE (title, agent, Complexity, Risk, Priority, Depends on all still extract correctly) | recorded gotcha: "A defect can reproduce itself during its own write-up" |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A guide whose Demonstration BEFORE field is blank, referenced in an `Agent()` spawn prompt | Hook prints a blank-BEFORE warning to stderr; spawn proceeds | automated test |
| 2 | A guide whose BEFORE field is filled | No blank-BEFORE warning printed; spawn proceeds | automated test |
| 3 | A guide file that does not exist / is unreadable | Hook exits without raising and without blocking (fail-open) | automated test |
| 4 | The current `tasks/TASK_GUIDE_T052.md` (pre-dates this change, has no Demonstration section) | Hook warns but does not error; all existing field extraction still returns correct values | automated test |
| 5 | Full existing hook suite | Still green — no regression from the new warning path | `python3 -m pytest .claude/hooks/tests -q` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_demonstration_before_warning.py` — 8 tests covering SC1–SC4, the prose false-positive edge case, non-blocking behaviour, malformed-input fail-open, and AC8 field-extraction stability |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `159 passed in 1.38s` (baseline before this task was `146 passed`; +8 T053, +5 T055) |
| Negative cases hold | ☑ pass | SC3 fail-open: `check_demonstration_warnings(["999"])` → `[]` for a nonexistent guide. SC4 legacy guide with no Demonstration section → warns, does not raise. Malformed stdin → exit 0, no `decision` key |
| verify | ☑ pass | Mutation-tested, not asserted: flipping `before_field_is_blank`'s missing-section branch `True`→`False` produced `1 failed, 158 passed` (RED at test_demonstration_before_warning.py:97), restore → `159 passed` — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | 4 files: the two guide flavors, `craft-spawn-prompt/SKILL.md`, `pre_agent_validate_guide.py`, plus the new test file. `pre_bash_block_unsafe_merge.py` and the report templates untouched, per Files Must NOT Touch |
| Full smoke suite still green (no regression) | ☑ pass | `159 passed`, zero pre-existing tests modified |
| **UI: Visual regression** | ☐ N/A | Pure process/hook task — no UI component |
| **UI: Design-system compliance** | ☐ N/A | Pure process/hook task — no UI component |
| **UI: Responsiveness** | ☐ N/A | Pure process/hook task — no UI component |

---

## Demonstration

> This task introduces the Demonstration block, so it fills one for itself. Non-executable change to
> two markdown files plus an executable change to one hook — both rules apply.

**BEFORE** (verbatim prior content — non-executable half): `templates/TASK_GUIDE_template.md` ends its
Evaluation section at the Evidence table, with no Demonstration section anywhere in the file. The
bugfix skeleton in `.claude/skills/bugfix/SKILL.md` likewise ends at its 3-row Evidence table.
Confirm with: `grep -c '^## Demonstration' templates/TASK_GUIDE_template.md .claude/skills/bugfix/SKILL.md` → expect `0` for both.

**BEFORE** (executable half — the hook): a spawn referencing a guide with no Demonstration block emits
only the existing `Depends on` warning, never a blank-BEFORE one. Capture the stderr of the hook run
against `tasks/TASK_GUIDE_T052.md` before any change.

**BEFORE captured by the Stage 3 agent, pre-implementation** (2026-08-06, before its first commit):
```
$ grep -c '^## Demonstration' templates/TASK_GUIDE_template.md .claude/skills/bugfix/SKILL.md
templates/TASK_GUIDE_template.md:0
.claude/skills/bugfix/SKILL.md:0
$ python3 -m pytest .claude/hooks/tests -q
146 passed in 1.38s
```
Hook baseline: an `Agent` event referencing `TASK_GUIDE_T052.md` produced no output at all — no
blank-BEFORE warning existed to emit.

**AFTER**: same `grep` returns `1` for both files; the hook run against a blank-BEFORE guide prints the
new warning and still exits 0.
```
$ grep -c '^## Demonstration' templates/TASK_GUIDE_template.md .claude/skills/bugfix/SKILL.md
templates/TASK_GUIDE_template.md:1
.claude/skills/bugfix/SKILL.md:1
$ python3 -m pytest .claude/hooks/tests -q
159 passed in 1.38s
```

**DELTA**: every task guide generated from this point forward — implementation or bugfix — carries a
before/after anchor, and an agent is warned at spawn time if it is about to start work without one.

**WITNESS**: Not the implementing agent alone — the Stage 3 agent captured BEFORE and wrote the three
markdown changes, but was killed by the step-limit hook before implementing AC6/AC7. The Supervisor
independently implemented the hook warning and all 8 tests, and re-ran every verification from the
main checkout on branch `docs/stage2-demonstration-block-t053-t055`, including the RED-then-GREEN
mutation cycle. Trace: `memory/event-trace/T053.jsonl`.

---

## Approach

**Pattern reference**: `.claude/hooks/pre_agent_validate_guide.py:76-83` — the existing `Depends on`
extraction and non-blocking warning. The blank-BEFORE check is the same shape in the same file:
field-anchored `re.search`, warn to stderr, never block, never raise.

Add the `## Demonstration` H2 to both guide flavors with identical field names and ordering, so T054's
renderer can read either with one parser. Place it after the Evidence table in the implementation
template (it describes the delivered outcome, which is what Evidence substantiates) and in the
equivalent position in the bugfix skeleton.

For the bugfix flavor, BEFORE must *point at* the Phase 1 repro loop rather than restating it —
DDR-0003 records the two-copies-that-disagree risk explicitly.

Verified 2026-08-05, before this guide was written: every regex in `post_write_register_task.py` and
`pre_agent_validate_guide.py` is field-anchored (`**Depends on**:`, `Complexity Level:`,
`^# TASK_GUIDE`), so none depends on section ordering. AC8 re-confirms this rather than assuming it.

---

## Edge Case Checklist

- [ ] Agent back-fills BEFORE after implementing — capture must precede the first implementation commit
- [ ] Bugfix BEFORE duplicates the Phase 1 repro loop instead of referencing it — two copies can disagree
- [ ] A pre-existing guide (T001–T052) has no Demonstration section — hook must warn, never error
- [ ] The new H2 text appears inside a Kanban row and truncates `find_kanban_section` via its `(?=###|\Z)` — do not put `###` in any row text for this task
- [ ] `extract()` in `post_write_register_task.py` searches the whole guide with `re.MULTILINE` — confirm no word in the new section (e.g. "Risk", "Priority") shadows a header field extraction
- [ ] The blank-BEFORE regex matches the heading but not a filled field containing the literal word "BEFORE" in prose
- [ ] Hook raises on a guide with unusual encoding — fail-open must hold (recorded: "A 'never raises' contract does not cover module import")

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_GUIDE_template.md` | Add `## Demonstration` section, 4 fields, no N/A path |
| `.claude/skills/bugfix/SKILL.md` | Add the same section to the Step 3 guide skeleton; BEFORE references the Phase 1 repro loop |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | Add the BEFORE-capture-before-implementation instruction to the assembled prompt |
| `.claude/hooks/pre_agent_validate_guide.py` | Add non-blocking blank-BEFORE warning |
| `.claude/hooks/tests/` | New tests for SC1–SC4 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Merge blocking deliberately deferred (DDR-0003) |
| `templates/report_template.html` | Stage 4 reports render from it; slots load-bearing in HTML + CSS |
| `.claude/skills/html-report/SKILL.md` | Separate artifact, separate trigger |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Test Plan

Unit tests against `pre_agent_validate_guide.py` covering SC1–SC4, plus a regression assertion that
the existing `Depends on` warning still fires unchanged. Mutation-check the blank-BEFORE regex: blank
the field in a fixture guide, confirm the test goes RED, restore, confirm GREEN — the recorded
vacuous-assertion pattern (T036/T042/T039) means an assertion never observed failing does not count.
Commit before mutating (recorded: "Reverting a mutation with `git checkout` also reverts your fix").

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — Medium risk, mandatory
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Demonstration block filled, including a BEFORE captured before the first implementation commit
- [ ] Supervisor notified: task ready for Stage 4 review
