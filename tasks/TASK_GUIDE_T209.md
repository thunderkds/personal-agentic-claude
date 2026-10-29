# TASK_GUIDE — T209: Auto verify refuses a verdict line that lists choices (`**Verdict:** PASS | FAIL | …`) and the doctrine names every accepted shape
**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `.claude/hooks/stop_auto_verify.py` (`VERDICT`, `parse()` — T208's version), the T208 block in `tests/test_auto_verify.py`, and `docs/claude-md/tracks.md` `### Auto verify (Stop hook)`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29: "go" — to the Supervisor's offer to plan the open weaknesses as fix tasks.

**Observed defect** (T208's auto verify, 2026-10-29, step 8): the `/verify` skill's blank report-template line, pasted as is, `**Verdict:** PASS | FAIL | BLOCKED | SKIP`, parses as `pass`. A session that copies the template without choosing would be recorded as a pass. The pre-T208 regex had the same flaw. Also, `docs/claude-md/tracks.md` still names only the `**Verdict:** PASS|FAIL` shape, while T208 accepts four.

**Restated intent**:
> A verdict line counts only when it names exactly one verdict word. A line that lists choices (two or more of PASS, FAIL, BLOCKED, SKIP, or a `|` between words right after the label) is not a verdict; with no other verdict line the run is `blocked`. The doctrine names every shape the parser accepts and says the parser fails closed.

**Out of scope**: the merge gate (T210); `call_claude`, budgets, the run record, the close-out.

**Requirement Refs**: no PRD — traces to the T208 verify log `.claude/verify-runs/T208-8ec94d5fbeeb.log` (step 8).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, 2026-10-29; user "go")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (auto verify, verdict, run record)
- [x] Every Acceptance Criterion traces to the observed defect
- [x] Requirement Refs — N/A, traced to the log above

---

## Dependencies & Reachability

**Depends on**: T208 (merged)
**Entry point**: `python3 .claude/hooks/stop_auto_verify.py --start <ID>` → `run()` → `parse()`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `parse()` returns `blocked` for a result whose only verdict line is `**Verdict:** PASS \| FAIL \| BLOCKED \| SKIP`, `**Verdict:** PASS \| FAIL`, `**Verdict: PASS / FAIL**` or `**Verdict:** PASS or FAIL` | defect |
| 2 | A report that carries the blank template line AND a real `**Verdict:** PASS` line parses as `pass` (the template line is ignored, not counted as a second verdict) | defect, no regression |
| 3 | Every T208 shape still parses (`**Verdict:** PASS`, `**Verdict: PASS**`, `**Verdict: PASS. …**`, `**Verdict**: PASS`) and every T208 fail-closed case still blocks | regression |
| 4 | `docs/claude-md/tracks.md` `### Auto verify (Stop hook)` names the accepted shapes in one sentence and says a line listing choices is not a verdict | doctrine |
| 5 | Mutation: remove the new choice check → the AC 1 test turns RED | guarantee |
| 6 | `tests/test_auto_verify.py`, `.claude/hooks/tests` and `tests` pass in full | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a stub `claude` on PATH printing a report whose only verdict line is the blank template | `--start` logs `verdict: blocked (no single verdict line)` | real hook, throwaway project |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_auto_verify.py -q && python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T209.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T209.md`.

---

## UI / Design Acceptance Criteria

N/A — hook-only change. All three UI Evidence rows ☐ N/A (justification: no UI component).

---

## Approach

**Pattern reference**: T208's `VERDICT` regex and its test block.
**Vital slice**: one extra check in `parse()` (or the pattern) + the AC 1–3 tests + the one doctrine sentence.
**Cut list**: changing the `/verify` skill text; new verdict states.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` | ignore a verdict line that lists choices |
| `tests/test_auto_verify.py` | AC 1–3, 5 tests |
| `docs/claude-md/tracks.md` | one sentence in `### Auto verify (Stop hook)` |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | T210, guarded by `merge_gate_guard.py` |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first (AC 1 fails on `main`), then the change, the AC 5 mutation by hand, Success Criterion 1 with a stub `claude`, then the full suites run plainly (no `timeout` prefix).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T209.md` (Hard-Stop Gate 5)
- [ ] Supervisor Stage 4 review (code-review + security-review, Risk Medium)
- [ ] Auto verify run started by the Supervisor (T203)
