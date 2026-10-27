# TASK_GUIDE — T186: Auto-mode check follow-up — a paused task stops re-blocking, new pause reasons are written, and the T180 limits are documented
**Date**: 2026-10-27
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: the change edits a `Stop` hook that can block every turn of a session. The merge gate (`pre_bash_block_unsafe_merge.py`) is not touched.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if needed
3. Read this file completely, then `tasks/TASK_GUIDE_T180.md` (D8, D9, D10 and the Questions Log) and the `Stage 4 round 2` and `verify` rows of `tasks/TASK_REVIEW_T180.md`
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/stop_auto_mode_check.py`, `.claude/hooks/tests/test_stop_auto_mode_check.py` and `docs/claude-md/tracks.md` `## Auto mode`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-27, after the D10 live check and `/verify T180` pass: "yes, accept it and continue" — accept the temporary `origin/HEAD` ref the auto-mode Supervisor added to start `security-review`, and record it with the other T180 limits in a follow-up task (the Supervisor's proposal). T180 Stage 4 round 2 found 3 P2s (`tasks/TASK_REVIEW_T180.md`).

**Restated intent**:
> The auto-mode Stop hook stops nagging about a task it already paused, and when it pauses a task again for a new
> reason, it writes that reason. `docs/claude-md/tracks.md` states the limits T180 left open, in plain words, so a
> user knows them before relying on `[auto]`.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **Paused means paused (T180 P2-a).** A task whose report holds a `Paused: auto-mode check failed` line is skipped by the first fire, unless the report file changed after the pause line was written (then it is checked again). The second fire writes a new `Paused:` line only when the reasons differ from the last one, so the newest reasons are always in the file and the same line is never repeated.
- D2 — **Accepted behavior, documented (user, 2026-10-27).** In `docs/claude-md/tracks.md` `## Auto mode`: in a repo with no git remote, the Supervisor may add a temporary `refs/remotes/origin/HEAD` so `security-review` can start; it removes the ref afterwards and logs both steps in the final report.
- D3 — **Known limits, documented, not fixed:** (a) without a remote and without D2, `security-review` cannot start and the hook pauses a Medium/High task; (b) Advocate and Skill calls in `_untagged.jsonl` from the last 6h count for every task, so two auto tasks in one session can share them (T180 P2-b; Advocate prompts carry no task ID by T179 D2); (c) a hand-typed `☑ pass` `verify` row ends the run unchecked, but the merge gate still blocks it at merge (T180 P2-c); (d) at High risk a decision can still hide behind a loosely related cited RULE, as long as one other decision is debated (D10 forces one Debate, not a Debate per choice).

**Out of scope**: fixing P2-b or P2-c in code; changing the merge gate; any paid live check.

**Requirement Refs**: none in `PRD.md`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (user, 2026-10-27: "yes, accept it and continue")
- [x] Every AC traces to the Requirement
- [x] Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: T180 (merged into the plan branch)
**Entry point**: the `Stop` entry for `stop_auto_mode_check.py` in `.claude/settings.json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A failing auto task whose report holds a `Paused:` line and has not changed since → the first fire does not block (test). The same report edited after the pause → blocks again (test). | D1 |
| 2 | Second fire with reasons different from the last `Paused:` line → a new line with the new reasons; same reasons → no new line (tests). | D1 |
| 3 | `docs/claude-md/tracks.md` `## Auto mode` states D2 and D3 (a)–(d) in plain words; a doc pin in `tests/test_auto_mode.py`. Line and byte caps the tests pin still hold; `AGENTS.md` unchanged. | D2, D3 |
| 4 | Full suites green: `python3 -m pytest -q tests`, `python3 -m pytest -q .claude/hooks/tests`, `sh scripts/validate.sh`. | Gate 5 |

---

## Evaluation & Acceptance

### Verification Command

```bash
python3 -m pytest -q .claude/hooks/tests/test_stop_auto_mode_check.py tests/test_auto_mode.py && python3 -m pytest -q tests .claude/hooks/tests
```

### Evidence

> **Moved.** Filled in `tasks/TASK_REVIEW_T186.md` (create it from `templates/TASK_REVIEW_template.md`).

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T186.md`. BEFORE: run the hook on a copy of `.spawn/live-checks/d9-high/tally` (hook replaced with the current one) with `{"stop_hook_active": false}` on stdin and paste the block it prints although the report already holds a `Paused:` line.

---

## Approach

**Pattern reference**: `record_pause` and `check_task` in `stop_auto_mode_check.py`; the `/verify T180` probes in `tasks/TASK_REVIEW_T180.md`.
**Vital slice**: AC 1–2. **Cut list**: fixing P2-b (task IDs in Advocate prompts) and P2-c (verify-row skip) in code.

---

## Edge Case Checklist

- [ ] Report file mtime unreadable → check the task as today (fail open toward checking, never toward a loop).
- [ ] Two `Paused:` lines already present (old reports) → compare against the last one.
- [ ] Minimal-track Decision record → the same rules inside its record block.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_mode_check.py` | D1 |
| `.claude/hooks/tests/test_stop_auto_mode_check.py` | AC 1–2 tests |
| `docs/claude-md/tracks.md` | D2, D3 text |
| `tests/test_auto_mode.py` | AC 3 doc pin |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | merge gate stays unchanged |
| `AGENTS.md` | at its line cap |
| `experiments/kit-arms/` | frozen experiment |

---

## Completion Checklist

- [ ] Build + tests (agent)
- [ ] Stage 4: code-review, security-review (Medium risk)
- [ ] `verify` (user-only: `/verify T186`)
- [ ] Merge only when the user asks

---

## Questions Log
