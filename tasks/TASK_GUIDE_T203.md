# TASK_GUIDE — T203: Auto verify for every task — the Supervisor starts the real headless `/verify` for any task at Ready for Review, not only `[auto]` tasks
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: paid headless Claude sessions start for every task at Ready for Review, not only for opted-in `[auto]` tasks, and the doctrine line "only the user runs `/verify`" goes away. The guardrails stay the point: the run is a separate session, only the run script writes the result and its run record (T182 D5), the merge gate's trust rule is unchanged, and merge/push stay with the user.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if your work reaches a hook, skill or decision the slice does not cover. Required memory: T182 auto verify (gate trusts the row only with the run record); "The gate an agent cannot satisfy is the one it forges" (T116); the `verify` skill is `disable-model-invocation` — the Supervisor starts the headless run, it never runs or copies the skill in its own session; detached spawns need `setsid`
3. Read this file completely, then `tasks/TASK_GUIDE_T182.md` (the run, the row, the record), `tasks/TASK_GUIDE_T188.md` (both tracks, the shared reader) and `tasks/TASK_GUIDE_T189.md` (the Done move this task must keep working)
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/stop_auto_verify.py`, `.claude/hooks/lib/auto_mode.py`, `.claude/hooks/lib/verify_record.py`, `.claude/hooks/stop_auto_mode_check.py`, and in `.claude/hooks/pre_bash_block_unsafe_merge.py` the `verify` row reader and its block messages
6. Read `docs/claude-md/tracks.md` (`## Auto mode`, `### Auto verify (Stop hook)`, row 18, `### Never in auto mode`, the minimal-track "Merge is never automatic" paragraph), `docs/claude-md/pipeline-stages.md` Stage 5 item 1, and `AGENTS.md` `## Tracks`
7. Read `setup.sh` `install_settings` / `merge_settings` and `lib/merge-settings.py` (AC 7)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29: "checking if in auto mode, the /verify does not run by auto and need my approval on that", then "I want supervisor to run it as automated", then: "supervisor, but for now when I update all the repos with the latest, it require me /verify is real, and also the current repos require still". The Supervisor restated: the Supervisor runs a real `/verify` for every task at Ready for Review, not only `[auto]` tasks, so the merge gate stops waiting on the user; the run stays a separate headless session whose own script writes the result; merge stays the user's. User: "just yes, and I will test later".

**Restated intent**:
> Every task that reaches Ready for Review gets one real `/verify` run per head commit, on either
> track, with or without `[auto]`. The Supervisor starts it (and the Stop hook starts it as a
> backstop), in a separate headless session, exactly as T182's run does today. The run script —
> never the Supervisor — writes the result and the run record, so the merge gate's trust rule is
> unchanged. The Supervisor waits for the verdict and reports it. Merge and push stay the user's.
> A repo that takes the kit's Update gets the same behaviour.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **No marker needed.** `stop_auto_verify.py` starts a run for every Ready for Review task whose result is unfilled for its head commit; the `Mode: auto` condition is removed from the trigger. Every other condition (head commit, exclusive log lock, user-filled result never overwritten, `CLAUDE_AUTO_VERIFY_RUN=1` child guard) stays. `stop_auto_mode_check.py` and the `[auto]` marker keep their other meanings (no-question runs, final report).
- D2 — **The Supervisor starts it.** A new entry `python3 .claude/hooks/stop_auto_verify.py --start <ID>` runs the same due-check and the same detached `start()` for one task, prints the log path (or why nothing started: not at Ready for Review, already filled for this commit, already running), and returns at once. The doctrine tells the Supervisor to call it right after it moves a task to Ready for Review, then wait for the run (Monitor on the log / result) and put the verdict in its reply or final report. The Stop hook stays as the backstop. Both paths share one lock, so a task and commit never run twice.
- D3 — **Off switch.** `CLAUDE_AUTO_VERIFY=off` (env) restores today's rule: only `[auto]` tasks run, everything else is `/verify (yours)`. Default is on. Documented next to `CLAUDE_AUTO_VERIFY_BUDGET_USD`.
- D4 — **Doctrine.** `AGENTS.md` `## Tracks` (the auto-mode sentence "never merges, pushes, moves a task to Done or runs `/verify`"), `docs/claude-md/tracks.md` (`### Auto verify (Stop hook)`, row 18, the minimal-track "the user runs `/verify`" sentence, `### Never in auto mode`), `docs/claude-md/pipeline-stages.md` Stage 5 item 1, and the block message in `pre_bash_block_unsafe_merge.py` that tells the user to run `/verify` all say: the Supervisor starts the headless auto verify run; the user may still run `/verify` themselves; a `blocked` run falls back to `/verify (yours)`. The Supervisor still never writes the `verify` row or runs the skill in its own session. `AGENTS.md` stays ≤200 lines.
- D5 — **Gate unchanged.** The merge gate already accepts an `auto-run by hook` row only with the D5 run record, with no marker check — keep it so. A row the agent typed, and `auto-checked, not /verify`, still block. Merge, push and `ship` stay the user's in every mode.
- D6 — **T189 still works.** If T189 has merged, its Done move after a pass keeps its current scope (auto-mode tasks only, unless T189's own doctrine says otherwise) — do not widen the Done move in this task.
- D7 — **Update reaches other repos.** Prove that the kit's Update merges the `stop_auto_verify.py` Stop entry into an existing project `settings.json` that lacks it (and ships the hook file via `MANIFEST`'s `.claude/hooks`). If it does not, fix `lib/merge-settings.py` / `setup.sh` so it does.

**Out of scope**: auto merge or push; widening T189's Done move; retries on the same commit; a settings UI for the off switch; running `/verify` in the T175 sandbox.

**Requirement Refs**: none — no root `PRD.md`; doctrine source is `docs/claude-md/tracks.md` `## Auto mode`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (user, 2026-10-29: "just yes, and I will test later")
- [ ] Domain terms: update the **Auto verify** glossary entry in `PROJECT_SPEC.md` (agent): every task, started by the Supervisor, Stop hook as backstop, `CLAUDE_AUTO_VERIFY=off`
- [x] Every AC traces to the Requirement
- [x] Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: T189 — it changes `.claude/hooks/stop_auto_verify.py` and `docs/claude-md/tracks.md` and is at Ready for Review; branch T203 from `main` only after T189 merges (or T189 is closed).
**Entry point**: `python3 .claude/hooks/stop_auto_verify.py --start <ID>` (Supervisor) and the existing `Stop` entry in `.claude/settings.json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The Stop hook starts one detached run for a Ready for Review task **without** `Mode: auto`, on the extended track (row in `TASK_REVIEW_<ID>.md`) and the minimal track (Decision record `Checked:` line). | D1 |
| 2 | `stop_auto_verify.py --start <ID>` starts the same detached run for one task and returns at once with the log path; it starts nothing, with a one-line reason, when the task is not at Ready for Review, its result is filled for the head commit, or a run for that commit already started. Hook and `--start` share the lock: the same task and commit never run twice. | D2 |
| 3 | `CLAUDE_AUTO_VERIFY=off` → only marked tasks run (hook and `--start`); unmarked tasks are untouched. | D3 |
| 4 | A user-filled result is never overwritten, and the child session's own Stop hooks still do nothing (`CLAUDE_AUTO_VERIFY_RUN=1`). Existing T182/T188 (and T189 if merged) tests still pass unchanged. | D1, D6 |
| 5 | The merge gate: an `auto-run by hook` row with a matching run record for an **unmarked** task passes; the same row without a record, with a record for another commit, with a fail record, and `auto-checked, not /verify` block. Tests prove each case. | D5 |
| 6 | Doctrine D4 text updated in every listed file; `AGENTS.md` ≤200 lines; `tests/test_docs_*` style checks (if any cover these lines) updated; no live doc still says only the user can run `/verify` except as the off-switch / blocked fallback. | D4 |
| 7 | A test runs the Update merge (`lib/merge-settings.py`) on a project `settings.json` with no `stop_auto_verify.py` entry and asserts the Stop entry is added and the user's own entries are kept. | D7 |
| 8 | Tests (`tests/test_auto_verify.py` and the merge-gate tests) pin AC 1–5 with `claude` stubbed. Full suite green: `python3 -m pytest -q tests .claude/hooks/tests`. | Gate 5 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | unmarked task at Ready for Review, row empty | one detached run, result written by the run script | test (stubbed `claude`) |
| 2 | `--start T…` twice on the same commit | one run, second call says already started | test |
| 3 | `CLAUDE_AUTO_VERIFY=off`, unmarked task | no run | test |
| 4 | row `auto-run by hook … pass`, no record | merge blocked | test (gate) |
| 5 | Update on a settings.json without the entry | entry added, user entries kept | test |

### Verification Command

```bash
python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests && python3 -m pytest -q tests
```

### Evidence

> **Moved.** Filled in `tasks/TASK_REVIEW_T203.md`. This task's own `verify` row is the user's (`/verify T203`): the auto verify cannot vouch for the change to itself. The user said they will test it later.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T203.md`.

---

## Approach

**Pattern reference**: `stop_auto_verify.py` `stop_hook()` / `due()` / `start()` (reuse — `--start` is a thin entry over the same functions); `lib/auto_mode.py` `resolve()` (it already reads unmarked tasks: `task.marker` is just false); `.claude/hooks/tests` stubs for `claude`.
**Vital slice**: drop the marker condition (AC 1), the `--start` entry (AC 2), doctrine (AC 6).
**Cut list**: a notification when the run ends (the Supervisor waits and reports); a per-project budget setting beyond the existing env vars; widening T189's Done move.

---

## Edge Case Checklist

- [ ] A Ready for Review task with no `TASK_REVIEW_<ID>.md` (old tasks on the board) → one stderr line, no run (today's `due()` behaviour for a missing row).
- [ ] Old Ready for Review rows that predate the `verify` row shape → no run, no crash.
- [ ] Several tasks at Ready for Review at once → one run each, own log and record; note the cost line in tracks.md (≤ `CLAUDE_AUTO_VERIFY_BUDGET_USD` each).
- [ ] The Supervisor commits again while a run is going → the old run is for the old commit; the next `--start` / Stop starts one for the new head.
- [ ] `claude` not on `PATH` → `blocked`, falls back to `/verify (yours)`, no crash.
- [ ] Board mode `online` → same as T182 (local files; board row moves as today).

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` | drop marker condition; `--start <ID>`; `CLAUDE_AUTO_VERIFY=off`; docstring |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | block message wording only (trust rule unchanged) |
| `AGENTS.md`, `docs/claude-md/tracks.md`, `docs/claude-md/pipeline-stages.md` | D4 doctrine |
| `templates/TASK_REVIEW_template.md` | `Not done:` slot wording if it names `[auto]`-only verify |
| `PROJECT_SPEC.md` | glossary |
| `lib/merge-settings.py` / `setup.sh` | only if AC 7 shows the Stop entry is not merged |
| `tests/test_auto_verify.py`, `.claude/hooks/tests/`, an installer test | new tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| any `verify` skill file | Claude Code built-in; called, never copied |
| `lib/verify_record.py` record format | the gate's trust anchor; reuse, do not change |
| `experiments/kit-arms/` | frozen experiment |

---

## Completion Checklist

- [ ] T189 merged (or closed) → branch from `main`
- [ ] Build + tests (agent)
- [ ] Stage 4: code-review, security-review (High risk)
- [ ] `verify` (user-only: `/verify T203` — user tests later)
- [ ] Merge only when the user asks

---

## Questions Log
