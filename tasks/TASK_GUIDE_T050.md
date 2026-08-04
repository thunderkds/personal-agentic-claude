# TASK_GUIDE — T050: Scope token-audit generator to its window's start date
**Date**: 2026-08-04
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Complexity is **C1** — single-file script fix, no schema/migration, no UI

---

## Requirement (Pillar 1 — Adapt the requirement)

User request (2026-08-04): "close the window with what we have and start a new one" — referring to
the DDR-0001 Token Audit Log window (`reports/token-audit_2026-07-21.md`), which just closed via
its 14-calendar-day condition.

**Restated intent**: The Supervisor closed the 2026-07-21 window manually (docs-only edit, already
done). While verifying the close, the Supervisor found `scripts/token_audit.py` has `WINDOW_DATE`
and `DEFAULT_REPORT_PATH` hardcoded to `2026-07-21`, and `build_entries()` derives from **every**
record in `memory/event-trace/*.jsonl` with no lower-bound timestamp filter. Re-running the script
as-is for a "new window" would either (a) keep overwriting the same 2026-07-21 file with the same
95 historical entries, or (b) if pointed at a new file, dump the entire trace history — including
the just-closed window's data — into the new window too. Neither is a real "start fresh."

Fix: parameterize the window start date and report path (env var or CLI arg, agent's choice — no
prior art elsewhere in this repo to imitate for this exact shape), and filter `build_entries()` to
only emit records whose derived `date` is `>= window_start_date`. Then regenerate a fresh, correctly
scoped `reports/token-audit_2026-08-04.md` (should currently contain 1 entry: today's `cold-start`
that we're in right now, plus this session's own eventual stage/spawn events).

**Out of scope**:
- Do not touch `reports/token-audit_2026-07-21.md` further — it's already closed and annotated.
- Do not change the entry format, event classification (`STAGE_MAP`), or cache-hit heuristic.
- Do not add real token-count estimation — the DDR-0001 "never synthesize" constraint stands.

**Requirement Refs**: DDR-0001 (`docs/ddr/0001-measure-first-token-refactor.md`) + Amendment 1 —
the window-rotation convention this fixes ("start a new file... rather than appending further").

### Requirement Fidelity Gate
- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with DDR-0001 / `memory/decisions.md` T040 entry
- [ ] Every Acceptance Criterion below traces to a line in the Requirement — agent verifies before starting

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `scripts/token-audit.sh` (the wrapper the Supervisor/user actually invokes; calls `scripts/token_audit.py`)

---

## Acceptance Criteria

| # | Criterion | Traces to |
|---|---|---|
| 1 | Running the script with no arguments still regenerates `reports/token-audit_2026-07-21.md` unchanged (default behavior preserved — don't break the closed window's file) | backward compatibility |
| 2 | Running the script pointed at window start `2026-08-04` produces `reports/token-audit_2026-08-04.md` containing **only** records with derived `date >= 2026-08-04` | "start a new one" |
| 3 | `2026-07-21` window's `2026-08-04` `cold-start` entry (today's session) — the one entry currently past the new window's start — appears in the **new** file, not (only) the old one, when regenerated with the new window's parameters | correct boundary handling at the exact start date |
| 4 | No entry-format, event-classification, or cache-heuristic change — diff limited to date-filtering + parameterization | out-of-scope guard |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|---|---|---|
| 1 | `python3 scripts/token_audit.py` (no args) | Same output as current `reports/token-audit_2026-07-21.md` (byte-identical minus the Supervisor's closure banner, which lives above the generator's own header and must survive) | automated diff |
| 2 | `python3 scripts/token_audit.py --window-start 2026-08-04 --report-path reports/token-audit_2026-08-04.md` (or equivalent flags the agent designs) | New file with only `>= 2026-08-04` entries | automated: grep dates in new file |
| 3 | A trace record dated before 2026-08-04 | Does NOT appear in the new window's file | negative test |

### Verification Command

```bash
python3 scripts/token_audit.py
git diff --stat reports/token-audit_2026-07-21.md   # expect: no change beyond what's already committed
python3 scripts/token_audit.py --window-start 2026-08-04 --report-path reports/token-audit_2026-08-04.md
grep -c "^2026-" reports/token-audit_2026-08-04.md
grep "2026-07" reports/token-audit_2026-08-04.md    # expect: no output (negative case)
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes |
|-------|--------|-------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | if `scripts/` has no existing test suite, a small standalone script asserting the two scenarios above is acceptable — state where it lives |
| Verification command run | ☐ pass / ☐ fail | paste real output |
| Negative cases hold | ☐ pass / ☐ fail | pre-window-start record correctly excluded |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to blast radius | ☐ pass / ☐ fail | `scripts/token_audit.py`, `scripts/token-audit.sh` only |
| Full smoke suite still green | ☐ pass / ☐ fail | `pytest .claude/hooks/tests/` — this task touches no hook code |
| UI rows | ☑ N/A | no UI |

---

## Approach

**Pattern reference**: `None — no comparable prior art in this repo for CLI-flag parameterization of a generator script.` The script already has a clear `DEFAULT_REPORT_PATH`/`WINDOW_DATE` module-level constant pair to parameterize from — keep the same structure, just make both overridable (CLI args with sane defaults, or env vars — agent's call, note the choice and why).

Minimal fix: add a `window_start` parameter to `build_entries()` (or filter its return value) comparing each entry's derived `date` string against the window-start string (both `YYYY-MM-DD`, so a plain string comparison is correct and avoids a datetime dependency beyond what's already imported).

---

## Edge Case Checklist

- [ ] Date string comparison must use the already-normalized `YYYY-MM-DD` format (not raw ISO timestamps) — confirm `_date_from_timestamp`'s output format matches the window-start argument's format exactly, or the `>=` string comparison silently misbehaves
- [ ] A record whose date can't be parsed (`_date_from_timestamp` returns `"?"`) must not crash the filter and must not be silently included — decide and document the behavior (agent's call, state the reasoning)
- [ ] Running the script twice with identical arguments must stay idempotent (existing guarantee) — don't regress this

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/token_audit.py` | Parameterize window start date + report path; add date filter to `build_entries()` |
| `scripts/token-audit.sh` | Pass through any new flags/env vars if the wrapper needs updating |
| `reports/token-audit_2026-08-04.md` | New — generated output for the new window (via the fixed script, not hand-written) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `reports/token-audit_2026-07-21.md` | Already closed and annotated by the Supervisor |
| `.claude/hooks/post_tool_trace.py` | Trace-writing side is correct and out of scope |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not mandated (Low risk) — optional if agent notices something concrete
- [ ] Tests written AND pass — pasted into Evidence
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (new decision: window-scoping fix)
- [ ] Supervisor notified: ready for Stage 4 review
