# TASK_GUIDE — T252: Stop check skips a marked auto task this session did not work on
**Date**: 2026-11-04
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide

---

## Requirement (Pillar 1 — Adapt the requirement)

From T250's auto verify (`.claude/verify-runs/T250-dc9e9da502e0.log`, Findings item 1): "The G3 narrowing covers only tasks found by file time. In step 7, the session did no work on T250, but the Stop hook still blocked on T250. T250's review file already says `Mode: auto`, so it counts as an auto task, and `check_task` asks about ownership only when no such marker exists. So a parallel `[auto]` session's report, if it is missing a line, still blocks this session's stop."

Code: `.claude/hooks/stop_auto_mode_check.py` `check_task` — `marked = task.marked`; the `owned(task)` question runs only inside `if not marked and windows:`.

T250's decision (`memory/decisions.md` 2026-11-04 T250) is that the Stop check judges only this session's work. The user approved T252 on 2026-11-04 ("let start").

Also folded in (user 2026-11-04, from T251 verify): `docs/claude-md/tracks.md` `### Known limits`, T251 bullet — the `Bash(*.claude/projects/*)` rule matches command text, so it also refuses a Bash command that only names that folder, for example a `grep` over a repo file that contains the string. Say so.

**Restated intent**:
> The Stop check blocks a session only for auto-mode tasks this session (or its sub-agents) worked on. A task whose report is marked auto mode, but which this session did not work on, is not checked and gets one stderr note. When ownership cannot be told, the task is checked as before (fail closed). The Known-limits text says the Bash transcript rule also refuses commands that only name the folder.

**Out of scope**:
- `pre_bash_block_unsafe_merge.py` and `session_work.py` logic (reuse `worked_on` as is).
- `stop_auto_verify.py` (auto close-out) — it uses `marker`, a separate path.
- Any change to the deny rules themselves.

**Requirement Refs**: no `PRD.md` IDs (`PROJECT_SPEC.md` `## Readiness`: `README.md` stand-in). Traces to T250 verify Findings item 1 and T251 verify finding (Bash rule over-blocks).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user 2026-11-04: "let start" (on the Supervisor's T252 summary)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered (none in `PRD.md`)

---

## Dependencies & Reachability

**Depends on**: T250 — `session_owner` / `session_work.worked_on` (merged `04418364`)

**Entry point**: `check_task` in `.claude/hooks/stop_auto_mode_check.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A task with `task.marked` True (review file `## Auto decisions` starting `Mode: auto`, or a `Mode: auto` Decision record, or the `[auto]` tag) whose report fails a check, and `owned(task) is False` → `check_task` returns `[]` and writes one stderr line naming the task and saying this session did not work on it | Restated intent: not checked, one note |
| 2 | The same task with `owned(task) is True` → the same reasons as today (block) | only this session's work |
| 3 | `owned` is None, or `owned(task)` returns None (no transcript, unreadable, error) → the same reasons as today (fail closed) | fail closed |
| 4 | The existing file-time path (T250 G3, `not marked` + window) is unchanged; all of `.claude/hooks/tests/test_stop_auto_mode_check.py` and `.claude/hooks/tests/test_t250_session_ownership.py` stay green | regression |
| 5 | End to end through `main()`: a Stop event (JSON on stdin, `transcript_path` to a synthetic transcript with no work on the task) with a marked, failing task prints no `"decision": "block"`; the same event with a transcript holding a `Write` to that task's review file prints the block | Restated intent |
| 6 | `docs/claude-md/tracks.md`: the Stop-check text (near line 306, "Since T250 …") says the ownership rule also applies to a task already marked auto mode; the T251 Known-limits bullet says the Bash rule also refuses a command that only names the folder (e.g. a `grep` over a repo file holding `.claude/projects/`) | Restated intent: docs |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Marked failing task, session did not work on it | stop allowed, one stderr note | automated test (AC 1, AC 5) |
| 2 | Marked failing task, session worked on it | block, same reasons | automated test (AC 2, AC 5) |
| 3 | Transcript missing | block, same reasons | automated test (AC 3) |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_stop_auto_mode_check.py .claude/hooks/tests/test_t250_session_ownership.py -q
python3 -m pytest .claude/hooks/tests/ tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T252.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T252.md`.

---

## Approach

**Pattern reference**: the T250 G3 branch in `check_task` (the `owned(task) is False` → `warn(...)`, `marked = False` lines) and its tests in `.claude/hooks/tests/test_t250_session_ownership.py`.

**Vital slice**: one ownership question for every marked-or-window task, before the reasons are built.
**Cut list**: no change to how `owned` decides; no new config.

Decisions:
- **D1 — where the question goes.** Recommended: after `marked` is computed (both paths), ask `owned(task)` once when `owned is not None`; `False` → warn + `return []`. Keep the existing file-time warning text for that path; a new text for the marked path, e.g. `"<ID>: its report is marked auto mode, but this session did not work on it — not checked"`.
- **D2 — a task this session ran in `[auto]`, then the user `/resume`d into a new session id.** Accepted gap: the new session did not work on it, so it is not checked there; the session that ran it was already checked at its own stop. Write it into `docs/claude-md/tracks.md` next to the AC 6 text, one sentence.

Write the tests for AC 1, 2, 3, 5 first and see AC 1 and the AC 5 no-work case fail; then the change; then docs.

---

## Edge Case Checklist

- [ ] A task already paused (`last_pause`) — ownership is asked before; a not-owned task returns `[]` without stamping its report
- [ ] `owned` raises → `session_owner` already returns None → checked (fail closed)
- [ ] Minimal-track task with a `Mode: auto` Decision record and no work by this session → not checked
- [ ] A verified extended task (`VERIFY_PASSED`) still returns `[]` first, unchanged

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_mode_check.py` | ownership check for marked tasks |
| `.claude/hooks/tests/test_t250_session_ownership.py` or new `.claude/hooks/tests/test_t252_marked_ownership.py` | AC 1–3, 5 tests |
| `docs/claude-md/tracks.md` | AC 6 text, D2 sentence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py`, `.claude/hooks/lib/session_work.py` | out of scope |
| `.claude/settings.json` | out of scope |

---

## Test Plan

Unit tests on `check_task` with a fake `owned`; one end-to-end test through the hook's `main()` with stdin JSON and a synthetic transcript (pattern: the T250 Stop tests); full suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T252.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — via the auto verify run
- [ ] Supervisor notified: task ready for Stage 4 review
