# TASK_GUIDE — T045: Kanban section parsing breaks when a row quotes a markdown heading marker
**Date**: 2026-07-23
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (pasted into your spawn prompt — do not re-read if present)
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above (C1) and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Read in full: `.claude/hooks/pre_agent_validate_guide.py`, `.claude/hooks/pre_bash_block_unsafe_merge.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

Two hooks slice `PROJECT_KANBAN.md` into board sections with the same idiom:

```python
re.search(rf"### {re.escape(section)}\n(.*?)(?=###|\Z)", kanban, re.DOTALL)
```

The `(?=###|\Z)` lookahead is **not anchored to line start**, so it also matches a literal `###`
appearing *inside a row's text*. A Done row that quotes a markdown heading terminates the Done
section early, and every row below it becomes invisible to the parser.

**Observed 2026-07-23** (not hypothetical): the Supervisor wrote the phrase `` `### Hard-Stop Gates` ``
into T039's Done row while summarizing that task's review findings. Immediately:

| Task | `find_kanban_section` returned | Truth |
|---|---|---|
| T039 | `Done` | Done |
| T042 | `None` | Done |
| T038 | `None` | Done |
| T022 | `None` | Done |

Consequence: `pre_agent_validate_guide.py` emits `"declares 'Depends on: Txxx' but Txxx was not found
anywhere on PROJECT_KANBAN.md — unknown dependency, check for a typo"` for any task depending on a
Done task listed below the offending row. The advisory is non-blocking, so it degrades into noise
that trains the reader to ignore it — the worst failure mode for a warning.

`pre_bash_block_unsafe_merge.py:tasks_in_section` uses the same idiom and would truncate identically.
There it is **not** advisory: it decides whether a merge is blocked, so a truncated `In Progress`
section could let a merge through that should have been stopped.

The row was reworded as an immediate mitigation, so the board currently parses correctly. That
mitigation is a convention no one can be relied on to remember — a Kanban row is prose, and prose
will eventually contain a `#`. This task removes the trap.

**Restated intent**:
> Board-section parsing must depend only on real section headings, never on characters that happen to
> appear inside a row's text.

**Out of scope**:
- The hook-lifecycle and merge-gate-evidence defects — that is T044
- Task-ID attribution — landed in T043
- Changing the Kanban file format or the board's section names
- Rewriting either hook's surrounding logic (Surgical Changes)

**Requirement Refs**: no `PRD.md`. Traceability:
- **`memory/learnings.md`** — "Don't quote a `###` heading inside a PROJECT_KANBAN.md row" (2026-07-23),
  including the reproduction table above
- **User directive 2026-07-23** — split this from T044 as its own task

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Reproduced by the Supervisor against the live `PROJECT_KANBAN.md` on 2026-07-23 — T042/T038/T022 returned `None`
- [x] Confirmed fixed by rewording the row (mitigation only, not the fix)
- [x] Second site (`tasks_in_section`) confirmed to share the idiom
- [ ] **Agent to confirm**: every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `find_kanban_section`
> The section-slicing function in `pre_agent_validate_guide.py` this task fixes. Grep-able; the sibling
> site is `tasks_in_section` in `pre_bash_block_unsafe_merge.py`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Both `find_kanban_section` and `tasks_in_section` anchor the terminating lookahead to line start (`(?=^###\|\Z)` with `re.MULTILINE`, or an equivalent line-based scan) | the shared idiom |
| 2 | **Negative — the reproduction**: given a Kanban whose Done section contains a row with the literal text `` `### Hard-Stop Gates` `` followed by more rows, **every** task in that section still resolves to `Done` | the observed defect |
| 3 | A row containing `#`, `##`, or `####` inline likewise does not truncate | generalization |
| 4 | **Positive**: real section headings still terminate correctly — a task in `Todo` never resolves as `Done`, and section boundaries are unchanged on the current real board | no false-negative regression |
| 5 | `tasks_in_section` returns the complete In-Progress set for a board whose earlier sections contain inline `###` text | the merge-gate half |
| 6 | **Negative**: an empty section, a missing section, and an empty file each behave as before (no crash, existing return contract) | fail-open preserved |
| 7 | **Negative**: `pre_agent_validate_guide.py`'s existing tests pass unchanged — this is a fix inside it, not a behavior change to its advisory contract | non-regression |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture Kanban reproducing the real 2026-07-23 board (T039 row quoting `### Hard-Stop Gates`, T042/T038/T022 below it) | all four resolve `Done` | automated test (AC2) |
| 2 | Same fixture, `tasks_in_section("In Progress")` | complete set returned | automated test (AC5) |
| 3 | The current real `PROJECT_KANBAN.md` | every task resolves to its true section | automated test (AC4) |
| 4 | Empty / missing / malformed board | existing contract, no crash | automated test (AC6) |

### Verification Command (exact, runnable)

```bash
CLAUDE_ACTIVE_TASK=T045 python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [AC2 and AC3 **observed RED before the fix**, AC6, AC7] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [must literally state "pass" or "fail" in this Notes column] |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | [`scripts/smoke-install.sh`] |
| **UI: Visual regression** | ☐ N/A | Python hooks, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Python hooks, no UI component |
| **UI: Responsiveness** | ☐ N/A | Python hooks, no UI component |

---

## Approach

The minimal correct fix is anchoring: `(?=^###|\Z)` with `re.MULTILINE` added to the existing
`re.DOTALL`. Both flags are needed — `DOTALL` so `.` spans rows, `MULTILINE` so `^` means line start
rather than string start. Verify both are passed; adding `MULTILINE` while dropping `DOTALL` silently
breaks the capture instead.

Consider factoring the slice into one shared helper used by both hooks, in the spirit of T043's
`lib/task_context.py` — this is the **5th defect in this hook family** (T018, T022, T024, T042, this),
and duplicated parsing idioms are how the family keeps reproducing. Judgment call: if a shared helper
adds indirection without removing real duplication, say so and keep the two-line fix. Do not
over-build (Simplicity First).

**Write the test first** (`tdd`) using a fixture that reproduces the real board — the actual T039 row
text is in git history at `dd76c96` if you want the verbatim string. A fixture built from the real
failure is a stronger oracle than an invented one.

**Mutation-test the negative control** (project norm since T043): after the fix, revert the anchor to
`(?=###|\Z)`, confirm AC2 goes RED, restore, and paste that red output into Evidence. An assertion
never observed failing is not evidence — see `memory/learnings.md`.

---

## Edge Case Checklist

- [ ] `re.MULTILINE` and `re.DOTALL` must **both** be present; check the call sites, not just the pattern.
- [ ] The last section in the file has no following heading — `\Z` must still terminate it (AC6).
- [ ] Section names are matched via `re.escape` already; do not remove that.
- [ ] A row could legitimately start with `#` at line start inside a fenced code block. Out of scope —
      the board has no fenced blocks today; note it in the docstring rather than solving it.
- [ ] These hooks fire on tool calls; preserve fail-open on any parse failure.
- [ ] Do not "improve" adjacent hook code.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_agent_validate_guide.py` | Anchor the lookahead in `find_kanban_section` |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Same fix in `tasks_in_section` |
| `.claude/hooks/tests/test_kanban_section_parsing.py` | **New** — fixture reproducing the real 2026-07-23 board |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/task_context.py` | Landed by T043; unrelated concern |
| `.claude/hooks/post_agent_move_to_review.py` | Owned by T044 |
| `PROJECT_KANBAN.md` | The row was already reworded; the fix is in the parser, not the data |
| `CLAUDE.md` | No pipeline semantics change |

---

## Test Plan

1. **Red**: write the fixture test against the current hooks. AC2 and AC5 must fail — that is the
   reproduction; paste the output into Evidence.
2. **Green**: anchor both lookaheads; AC1–AC7 pass.
3. **Mutation control**: revert the anchor, confirm AC2 goes RED, restore. Paste the red output.
4. **Regression**: full `.claude/hooks/tests/` suite (T043's 60 tests must stay green), then
   `bash scripts/smoke-install.sh`.
5. Paste real command output into every Evidence row — never a claim of output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review run (a sub-agent has no `Skill` tool — perform code-review/security-review manually and label them as manual)
- [ ] Security review — **mandatory, Risk=Medium**
- [ ] Tests written AND pass — output pasted into Evidence (Hard-Stop Gate 5)
- [ ] Mutation control observed RED, with pasted output
- [ ] Report to the Supervisor for `memory/`: whether any other hook parses the Kanban with an unanchored idiom (do not write memory yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
