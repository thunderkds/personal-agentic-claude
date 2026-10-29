# TASK_GUIDE — T208: Auto verify reads a PASS written as `**Verdict: PASS …**` — a real pass is no longer recorded as blocked
**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P0
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
6. Read `.claude/hooks/stop_auto_verify.py` (`VERDICT`, `parse()`), `tests/test_auto_verify.py` (the `_verdict_output` / `VERDICT_OUTPUT` fixtures) and `docs/claude-md/tracks.md` `### Auto verify (Stop hook)`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29: "is yours, I remember updated in the last task. if the verify do not run by automated, let fix the tasks"

**Observed defect** (Supervisor, 2026-10-29): `python3 .claude/hooks/stop_auto_verify.py --start T207` ran a real headless `/verify` that ended in a PASS report. The hook logged `verdict: blocked (no single verdict line)` and wrote `☐ blocked` into T207's `verify` row. The session's line was `**Verdict: PASS. All six flow visuals render …**` (bold around the whole sentence). `VERDICT = re.compile(r"^\s*\*\*Verdict:\*\*\s*([A-Z]+)\b", re.M)` at `.claude/hooks/stop_auto_verify.py:90` accepts only `**Verdict:** PASS`. Earlier runs (T197, T203) happened to use that shape. The raw output is saved at `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t208/t207_verify_output.json`.

**Restated intent**:
> The auto verify run reads the verdict whether the `/verify` report bolds only the label (`**Verdict:** PASS`) or the label and the word together (`**Verdict: PASS**`, `**Verdict: PASS. …**`, `**Verdict**: PASS`). It still fails closed: no verdict line, two different verdicts, or a verdict word that is not PASS or FAIL stays `blocked`. A mention of a verdict inside prose never counts.

**Out of scope**:
- `call_claude`, budgets, the run record, the close-out (T189), the merge gate
- Changing what `/verify` writes (it is a built-in skill)

**Requirement Refs**: no PRD — traces to the user message and the T207 run log `.claude/verify-runs/T207-64833b3ecc41.log`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, 2026-10-29; user: "let fix the tasks")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (auto verify, run record, verdict)
- [x] Every Acceptance Criterion traces to the observed defect or the fail-closed rule
- [x] Requirement Refs — N/A, traced to the log above

---

## Dependencies & Reachability

**Depends on**: T203 (merged)
**Entry point**: `python3 .claude/hooks/stop_auto_verify.py --start <ID>` → `run()` → `parse()`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `parse()` returns `pass` for a result whose verdict line is any of: `**Verdict:** PASS`, `**Verdict: PASS**`, `**Verdict: PASS. All six …**`, `**Verdict**: PASS`; and `fail` for the same four shapes with FAIL | defect |
| 2 | The saved T207 output (copied into `tests/fixtures/auto_verify/verify_pass_bold_sentence.json`) parses as `pass` | defect |
| 3 | Still `blocked`: no verdict line; one PASS and one FAIL line; `**Verdict:** BLOCKED`; `**Verdict:** SKIP`; a line where `Verdict: PASS` appears mid-sentence (not at line start); a non-success run | fail closed |
| 4 | Mutation: restore the old regex → the AC 2 test turns RED; make the pattern drop the line-start anchor → an AC 3 test turns RED | guarantees asserted |
| 5 | `tests/test_auto_verify.py` and `.claude/hooks/tests` pass in full | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a stub `claude` on PATH that prints the T207 output, in a throwaway project with a Ready-for-Review task | `--start` logs `verdict: pass` and the `verify` row reads `☑ pass … auto-run by hook` | run the real hook |
| 2 | after merge, `--start T207` on a new T207 commit | `verdict: pass` | Supervisor, live |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_auto_verify.py -q && python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T208.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T208.md`.

---

## UI / Design Acceptance Criteria

N/A — hook-only change. All three UI Evidence rows ☐ N/A (justification: no UI component).

---

## Approach

**Pattern reference**: the existing `VERDICT` regex and `_verdict_output()` test helper.

**Vital slice**: one regex change in `stop_auto_verify.py` plus the AC 1–3 parse tests and the fixture.
**Cut list**:
- Parsing verdict words other than PASS/FAIL into new states
- Telling `/verify` how to format its report

---

## Edge Case Checklist

- [ ] `**Verdict:**PASS` (no space) — accept
- [ ] Lower-case `pass` — stays blocked (the skill's template is upper case; do not widen)
- [ ] The verdict line inside a fenced code block of the report — document whether it counts (today's regex counts it)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` | `VERDICT` pattern (and its comment) |
| `tests/test_auto_verify.py` | AC 1–4 tests |
| `tests/fixtures/auto_verify/verify_pass_bold_sentence.json` | new fixture from the T207 output |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | merge gate, guarded by `merge_gate_guard.py` |
| `.claude/hooks/lib/auto_closeout.py`, `lib/verify_record.py` | out of scope |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: add the AC 1–3 cases and the fixture, see AC 1/2 fail on `main`. Change the pattern. Run the AC 4 mutations by hand and paste each RED and green. Drive Success Criterion 1 with a stub `claude`. Then the full suites, run plainly (no `timeout` prefix).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T208.md` (Hard-Stop Gate 5)
- [ ] Supervisor Stage 4 review (code-review + security-review, Risk Medium)
- [ ] Auto verify run started by the Supervisor (T203)
- [ ] Supervisor notified: task ready for Stage 4 review
