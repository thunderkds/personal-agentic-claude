# TASK_GUIDE — T182: Auto verify — for an `[auto]` task at Ready for Review, a hook runs the real `/verify` in a fresh headless session and writes the `verify` row
**Date**: 2026-10-27
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: a hook starts paid Claude sessions on its own, and the merge gate (`pre_bash_block_unsafe_merge.py`) learns to accept a `verify` row the user did not type. The guardrails — the Supervisor never runs or writes `/verify`, the row is only accepted with a record the agent cannot write, merge stays with the user — are the point of the task.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if needed. Required memory: the `verify` skill is `disable-model-invocation` (the model cannot run it and must not copy its workflow); "The gate an agent cannot satisfy is the one it forges" (T116 faked a user-run `/verify`); detached spawns need `setsid` (exit 129 otherwise); T144's anchored trace (a record the agent is denied to write)
3. Read this file completely, then `tasks/TASK_GUIDE_T180.md` (where auto mode is marked on a task, D3 Stage 5, D6)
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/pre_bash_block_unsafe_merge.py` (`has_filled_verify_row`, the `verify` row regex), `.claude/hooks/stop_review_reminder.py`, `.claude/settings.json` (`Stop`), and how T144 anchors its trace
6. Read `experiments/kit-arms/run_arms.py` for how the kit already starts headless `claude -p` runs with a budget cap

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-27: "I want to make the /verify command is automate also, let check and update the tasks". The Supervisor explained that `/verify` is a Claude Code built-in the model is blocked from running, and offered three ways. The user chose: "Hook runs real /verify" — a hook the user's settings run (not the Supervisor) starts a fresh headless session that runs the real `/verify`, and that run writes the `verify` row; merge stays with the user.

**Restated intent**:
> When a task started with `[auto]` (T180) reaches Ready for Review, a hook starts a new headless
> Claude session that runs the built-in `/verify` for that task. The hook — never the Supervisor —
> writes the result into the task's `verify` Evidence row with where the run's log is. The merge gate
> accepts that row only when a record the agent cannot write confirms the run. The user still decides
> the merge.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **Spike first (AC 1).** Prove that a fresh `claude -p "/verify <Txxx>"` runs the built-in skill headless. If it does not (refused, unknown command, or it needs a human to answer), **stop and report**: no hand-written equivalent of `/verify`, ever.
- D2 — **Trigger.** A `Stop` hook entry: when the task is marked auto (T180's marker), its status is Ready for Review, and its `verify` row is unfilled for the current head commit, the hook starts the run detached (`setsid`, so the Supervisor's turn ends at once). One run per task per head commit: a new commit may start a new run; the same commit never runs twice.
- D3 — **The run.** In the task's worktree, a new session (`claude -p "/verify <Txxx>"`, no `--resume`), with `--max-budget-usd 2` (a default the user can change) and the user's normal permission settings — never `--dangerously-skip-permissions`. Output goes to `.claude/verify-runs/<Txxx>-<short-sha>.log` (gitignored).
- D4 — **The row.** After the run ends, the hook script writes the `verify` row: `☑ pass` / `☑ fail` / `☐ blocked`, Notes `auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file> — <pass|fail|blocked>`. "blocked" (budget hit, a permission it could not get, the run did not finish) never contains the word "pass". The Supervisor never edits this row.
- D5 — **Forgery guard.** The hook also writes a run record outside the agent's write reach (reuse T144's anchor approach). The merge gate accepts an `auto-run by hook` row only if the record exists for that task and commit and says pass. A row typed by the agent — or `auto-checked, not /verify` (T180) — still blocks.
- D6 — **Not changed.** Without `[auto]`, `/verify` stays the user's, exactly as today. Merge, push and moving to Done stay with the user in every mode.

**Out of scope**: auto merge; auto `/verify` for non-`[auto]` tasks or as a project-wide setting; retry loops (a failed run is reported, not re-run on the same commit); running `/verify` inside the T175 Docker sandbox.

**Requirement Refs**: none in `PRD.md`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (user, 2026-10-27, chose "Hook runs real /verify (Recommended)")
- [ ] Domain terms: add **Auto verify** to the `PROJECT_SPEC.md` glossary (agent), with "Not the Supervisor's `auto-checked` real-run check (T180)"
- [x] Every AC traces to the Requirement
- [x] Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: T180 — the `[auto]` marker on a task and the Stage 5 rule this task completes
**Entry point**: the `Stop` hook entry in `.claude/settings.json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | **Spike, after the user's go, paid, cap $1:** one `claude -p "/verify <Txxx>"` on an existing Ready for Review task; paste the command and its output. Pass = the built-in skill ran. Fail = stop the task and report (D1). | D1 |
| 2 | A `Stop` hook starts the run only when all D2 conditions hold; it returns at once (the run is detached with `setsid`); the same task and commit never start twice. | D2 |
| 3 | The run uses a new session, the D3 budget flag, no `--dangerously-skip-permissions`, and writes its log under `.claude/verify-runs/` (gitignored). | D3 |
| 4 | The hook writes the D4 row for pass, fail and blocked; a blocked run's Notes never contain "pass". | D4 |
| 5 | The merge gate accepts an `auto-run by hook` row only with a matching D5 record; it still blocks: the same row with no record, a record for another commit, a fail record, and `auto-checked, not /verify`. Tests prove each case. | D5 |
| 6 | Without the `[auto]` marker the hook does nothing (test). `docs/claude-md/tracks.md` `## Auto mode` names the auto verify step; `AGENTS.md` stays ≤200 lines. | D6 |
| 7 | Tests (`tests/test_auto_verify.py`, plus the merge-gate tests) pin AC 2–6 with the `claude` binary stubbed. The full suite stays green. | Gate 5 |
| 8 | **Live check, after the user's go, paid, cap $4:** one `[auto]` fixture task reaches Ready for Review, the hook runs `/verify`, the row and record appear, and the merge gate allows the merge command check; then the row is hand-edited to "pass" with no record → the gate blocks. | user request |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | `claude -p "/verify T…"` | the built-in skill runs, or the task stops | spike (paid) |
| 2 | `[auto]` task at Ready for Review, row empty | one detached run, row written by the hook | test (stubbed `claude`) + run |
| 3 | row says `auto-run by hook … pass`, no record | merge blocked | test (hook) |
| 4 | `auto-checked, not /verify` only | merge blocked | test (hook) |
| 5 | task without `[auto]` | hook does nothing | test |

### Verification Command

```bash
python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests && python3 -m pytest -q tests
```

### Evidence

> **Moved.** Filled in `tasks/TASK_REVIEW_T182.md`. This task's own `verify` row is the user's (`/verify T182`): the auto verify cannot vouch for itself.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T182.md`.

---

## Approach

**Pattern reference**: `stop_review_reminder.py` (a `Stop` hook that reads the board); T144's anchored trace (a record the agent cannot write); `experiments/kit-arms/run_arms.py` (headless `claude -p` with `--max-budget-usd`); the `setsid` memory note (a detached run without it dies with exit 129).
**Vital slice**: the spike (AC 1), the hook-written row (AC 2–4), the forgery guard in the merge gate (AC 5).
**Cut list**: retries; a notification when the run ends (the final report and the row are enough); auto verify outside `[auto]`; a budget setting UI.

---

## Edge Case Checklist

- [ ] Two `[auto]` tasks reach Ready for Review in one turn → two runs, each with its own log and record.
- [ ] The Supervisor commits again while a run is going → the old run's result is for the old commit; the gate needs a record for the head commit.
- [ ] A minimal-track `[auto]` task (no `TASK_REVIEW` file) → the hook writes the result into its Decision record's `Checked:` line in the same shape; the merge gate reads it there only if T178 made the gate read Decision records — else the merge stays with the user's `/verify`.
- [ ] `claude` is not on `PATH` or not logged in → row `blocked`, one line in the final report, no crash.
- [ ] The run's own output contains text like "mark this pass" → data, not an instruction; only the skill's result decides.
- [ ] Board mode `online` → the row and record are local files; the board row moves as today.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` (or an extension of `stop_review_reminder.py`) | new: trigger + detached run + row + record |
| `.claude/settings.json` | `Stop` entry |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | accept an `auto-run by hook` row only with the D5 record — every other case unchanged |
| `.gitignore` | `.claude/verify-runs/` |
| `docs/claude-md/tracks.md` | auto verify step in `## Auto mode` |
| `PROJECT_SPEC.md` | glossary |
| `tests/test_auto_verify.py`, `.claude/hooks/tests/` | new tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `experiments/kit-arms/` | frozen experiment (read-only reference) |
| `skills/resolve-question/` | T179 |
| any `verify` skill file | it is a Claude Code built-in; the task calls it, never copies it |

---

## Completion Checklist

- [ ] User go → AC 1 spike (Supervisor); stop if it fails
- [ ] Build + tests (agent)
- [ ] Stage 4: code-review, security-review (High risk)
- [ ] User go → AC 8 paid live check (Supervisor)
- [ ] `verify` (user-only: `/verify T182`)
- [ ] Merge only when the user asks

---

## Questions Log
