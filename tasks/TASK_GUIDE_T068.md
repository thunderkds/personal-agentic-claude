# TASK_GUIDE — T068: An unfilled `verify` Evidence row already satisfies the merge gate
**Date**: 2026-08-09
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Found by the T064 implementer during Stage 3 and confirmed **pre-existing** by the Supervisor against
baseline `2612a05`, so it is not a T064 regression.

`pre_bash_block_unsafe_merge.py` decides whether a task in *Ready for Review* has Stage 5 verify
evidence using:

```python
VERIFY_ROW_PATTERN = re.compile(r"verify\s*\|[^|\n]+\|[^|\n]*pass", re.IGNORECASE)
```

The intent is the T026 two-bug fix and it is **correct**: the Check cell must be the literal word
`verify`, and the word "pass" must appear in the **Notes** column, not merely the Result column.

The defect is that T026 also wrote the word "pass" into the template's own placeholder **as
guidance**:

```
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail"
here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes
column for the word "pass", not just the Result column] |
```

That placeholder matches its own gate. A task that has filled in **nothing at all** already clears
the row check; only `trace_shows_verification` still stands between it and a merge.

This is the **fourth distinct way this gate has failed to gate** — after the T044 bare-substring
match, the `extract_command` truncated-JSON leak, and the false-PASS-from-the-wrong-branch pattern —
and the third whose root cause is *guidance text being indistinguishable from filled-in evidence*.
T064 makes it more visible, not worse: every new task now starts from a `TASK_REVIEW_Txxx.md`
carrying that placeholder.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Make the merge gate tell the difference between a `verify` row a reviewer has filled in and one
> still carrying the template's placeholder — without weakening the Notes-column requirement T026
> established, and without rejecting any row a reviewer has legitimately filled.

**Out of scope**:
- Changing `trace_shows_verification` or any other blocker in the gate. Only the row check.
- Any other Evidence row. `verify` is the one the gate reads.
- Back-filling or editing historical guides and review files.
- Relaxing the requirement that "pass" appear in the **Notes** column. That is the T026 property and
  it stays.

**Requirement Refs**: none — harness-internal tooling, no `PRD.md` FR/NFR.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed — defect reproduced by the Supervisor at baseline `2612a05`
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A, stated rather than left blank

---

## Dependencies & Reachability

**Depends on**: `None` — T064 merged; the resolver the gate now reads through is in place.

**Entry point**: `VERIFY_ROW_PATTERN` — the literal, grep-able identifier in
`.claude/hooks/pre_bash_block_unsafe_merge.py`.

---

## Acceptance Criteria

> **The corpus below is the oracle.** A survey of every real `verify` row in `tasks/*.md`,
> `templates/*.md` and `.claude/skills/bugfix/SKILL.md` was run at Stage 2. Any rule you write must
> classify all of it correctly — this is what stops a plausible fix from silently rejecting honest
> work.
>
> | Result-cell text | Real? | Must classify as |
> |---|---|---|
> | `☐ pass / ☐ fail / ☐ N/A` | template placeholder, 3 occurrences | **unfilled** |
> | `☐ pass / ☐ fail` | 2 historical guides | **unfilled** |
> | `☑ pass` | ~25 historical guides | filled |
> | `pass` | 4 historical guides | filled |
> | `✅ pass` | 1 historical guide | filled |
> | `☑ pass / ☐ N/A` | 1 historical guide (T050) | **filled** — and it still contains `☐` |
>
> That last row is the trap: the obvious fix — "reject any Result cell containing `☐`" — rejects a
> legitimately filled row. Do not ship it.

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The gate's row check returns **False** for the current `templates/TASK_REVIEW_template.md` placeholder row, exactly as it ships | Restated intent |
| 2 | The gate's row check returns **False** for `☐ pass / ☐ fail` | Restated intent |
| 3 | The gate's row check returns **True** for every one of the four filled shapes in the table above, including `☑ pass / ☐ N/A` | "without rejecting any row a reviewer has legitimately filled" |
| 4 | The Notes-column requirement is preserved: a row with "pass" in the Result cell but **not** in Notes still returns False. This is the T026 defect and it must stay caught | Out of scope — do not weaken |
| 5 | The Check cell must still be exactly `verify` — a row for some other check whose notes mention "pass" is not accepted | Out of scope — do not weaken |
| 6 | Every historical `TASK_GUIDE_*.md` / `TASK_REVIEW_*.md` that the *old* pattern accepted is still accepted by the new one, verified by running both over the real corpus and diffing the verdicts. Any intentional difference must be **only** the unfilled placeholders | "without rejecting any row a reviewer has legitimately filled" |
| 7 | **Negative, mutation-verified**: reverting the pattern to the old one turns AC1's test RED | vacuous-assertion family |
| 8 | The fix is in the **matcher**, not in the template's wording. The placeholder text stays byte-identical | see Approach |
| 9 | `pre_bash_block_unsafe_merge.py` still fails closed on a missing/unreadable Evidence section and on a missing resolver (T064's AC7 property is not regressed) | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> Fill **Success Criteria** and **Verification Command** at Stage 2. The reviewer fills Evidence in
> `tasks/TASK_REVIEW_T068.md` at Stage 4/5 — this task uses the split layout T064 introduced.

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A task in Ready for Review whose review file is the untouched template | gate **blocks** | automated test |
| 2 | Same, but the reviewer filled Result `☑ pass` and put "pass" in Notes | row check passes | automated test |
| 3 | T050's real `☑ pass / ☐ N/A` row | row check passes (AC3 trap) | automated test |
| 4 | Result `pass`, Notes `[what was observed]` | row check **fails** (T026 property, AC4) | automated test |
| 5 | Old vs new pattern over the whole real corpus | verdicts differ **only** on placeholder rows | automated test |

### Verification Command (exact, runnable)

```bash
pytest .claude/hooks/tests/ -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T068.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T068.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/pre_bash_block_unsafe_merge.py` — `VERIFY_ROW_PATTERN` and
`has_filled_verify_row()` as they stand today. Change the pattern and its docstring; keep the
function's shape, its fail-closed contract and its call site untouched.

**Recommended rule, derived from the corpus: reject the Result cell only when it contains an
unchecked _pass_ — the literal `☐ pass`.** Checked against every row in the AC table it is exactly
right: it rejects `☐ pass / ☐ fail / ☐ N/A` and `☐ pass / ☐ fail`, and accepts `☑ pass`, `pass`,
`✅ pass`, and the awkward `☑ pass / ☐ N/A` (which contains `☐ N/A` but never `☐ pass`). It is a
strictly narrower change than "no `☐` anywhere", which AC3 forbids.

You are not obliged to use it. If you find a rule that classifies the corpus correctly and is simpler
or harder to fool, take it and say why in your report. What you must not do is widen the rule until
the corpus passes — the corpus is the oracle, not a hint.

**Fix the matcher, not the template (AC8).** Rewording the placeholder so it no longer contains
"pass" is the tempting one-line fix and it is wrong twice over: a test pins that string, and the
recorded rule is to fix the prose *around* a pinned string rather than loosen the test — but more
importantly, the wording is genuinely useful guidance for reviewers, and the gate should not depend
on evidence text avoiding a particular word. A matcher that only works because nobody wrote "pass" in
a comment is the same class of defect as the T044 substring match.

**AC6 is the safety net.** Run both patterns over every real guide and review file and diff the
verdicts before you trust anything. A fix here that rejects honest historical work would block merges
repo-wide, and the failure would look like the gate working.

---

## Edge Case Checklist

- [ ] A row using a different checked glyph (`☑`, `✅`, `[x]`) — enumerate what the corpus actually contains rather than guessing at Unicode variants
- [ ] Case: `☐ PASS` / `☐ Pass` — the pattern is `re.IGNORECASE`, so the guard must be too
- [ ] Whitespace: `☐  pass` (double space), `☐pass` (none) — decide and pin the behaviour rather than leaving it to chance
- [ ] A Notes cell that legitimately contains the string `☐ pass` while quoting this very defect — T068's own review file will do exactly that. **This is the recorded "a defect can reproduce itself during its own write-up" pattern, now on its 3rd occurrence; re-run the real gate over your own review file before committing**
- [ ] The `☐ N/A`-only case: a genuinely N/A verify row has no "pass" anywhere and is already rejected — confirm that stays true and is deliberate
- [ ] Multiple `verify` rows in one Evidence table (bugfix flavor has extra rows) — confirm which one wins and that it is deterministic

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | `VERIFY_ROW_PATTERN` + `has_filled_verify_row()` docstring |
| `.claude/hooks/tests/test_guide_sections.py` **or** a new `test_verify_row_fill_detection.py` | AC1–AC7; pick whichever the existing layout makes natural and say which |
| `tasks/TASK_REVIEW_T068.md` | new — created from `templates/TASK_REVIEW_template.md` |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `templates/TASK_REVIEW_template.md`, `templates/TASK_GUIDE_template.md` | AC8 — the fix is in the matcher, and the placeholder wording is pinned by a test |
| `tasks/TASK_GUIDE_*.md`, other `tasks/TASK_REVIEW_*.md` | historical Evidence is the AC6 corpus; editing it destroys the oracle |
| `.claude/hooks/lib/guide_sections.py` | T064's resolver is correct and out of scope |
| `memory/*` | Supervisor-only writes — flag learnings to the Supervisor instead |
| `PROJECT_KANBAN.md` | Supervisor closes the row; it is also test-covered |

---

## Test Plan

Write the AC1 test first and watch it **fail against the current code** — that is the defect
reproduction, and per the Karpathy Task Transformation Table this task is "write a test that
reproduces the bug, then make it pass".

Then AC3 (the `☑ pass / ☐ N/A` trap) and AC4 (the T026 property) before touching the pattern, so the
constraints exist before the fix does.

AC6 is a single test that walks the real `tasks/` corpus, applies the old and new patterns, and
asserts the verdict sets differ only by the placeholder rows. Read the files; **never write to
anything under `tasks/`** — T059 was exactly that defect and in a worktree it destroyed data.

Mutation-verify AC7 by restoring the old pattern and confirming RED, and confirm the mutation
actually took effect before trusting the verdict — a Supervisor control on T063 sat after
`sys.exit(main())` and never ran, and one on T064 failed to apply at all and was caught only by its
own assert. Attack AC1 from a second direction too: the recorded T067 finding is that an assertion
can be non-vacuous against one mutation and vacuous against another.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — required (Medium risk); check `git branch --show-current` first, the built-in diffs the checked-out branch
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T068.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] UI Evidence rows marked ☐ N/A with justification — pure-backend task
- [ ] Learnings flagged to the Supervisor (do not write `memory/` yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
