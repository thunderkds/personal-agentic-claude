# TASK_GUIDE — T188: Auto verify fires for every `[auto]` task — the minimal track gets a run too, and both Stop hooks find auto tasks the same way
**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: this task widens what `pre_bash_block_unsafe_merge.py` accepts as Stage 5 Evidence to a Decision record's `verify:` line. The guardrail is unchanged and is the point of the task — an `auto-run by hook` result counts only with the run record the agent cannot write, for the head commit, and merge stays with the user.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if your work reaches a hook, skill or decision the slice does not cover. Required memory: the `verify` skill is `disable-model-invocation` (the model cannot run it and must never copy its workflow); "The gate an agent cannot satisfy is the one it forges" (T116 faked a user-run `/verify`); detached spawns need `setsid`
3. Read this file completely, then `tasks/TASK_GUIDE_T182.md` (D1–D6 and its Edge Case Checklist line about the minimal track) and `tasks/TASK_GUIDE_T178.md` (the Decision record's fields)
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/stop_auto_verify.py` in full, `.claude/hooks/stop_auto_mode_check.py` (how it already finds auto tasks, including from `tasks/MINIMAL_LOG.md`), `.claude/hooks/lib/verify_record.py`, and `.claude/hooks/pre_bash_block_unsafe_merge.py` (`evidence_search_dirs`, `has_filled_verify_row`)
6. Read `templates/MINIMAL_LOG_template.md` and `templates/TASK_REVIEW_template.md` (both keep `Mode: auto` inside an HTML comment on purpose)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28: "the /verify does not run as automatically when the tag auto, why" and then "with the auto tag, we automate all". The Supervisor named the four things `[auto]` leaves to the user today, and the user chose **everything except merge and push**. This task is the `/verify` half of that choice; T189 is the close-out half.

Two gaps make T182's hook silent in practice:
- `.claude/hooks/stop_auto_verify.py:80` drops every board row matching `| Track: minimal`, so a minimal-track `[auto]` task never starts a run. `tasks/TASK_GUIDE_T182.md:120` lists this case as unbuilt.
- The hook reads the marker only from `tasks/TASK_REVIEW_<ID>.md`, and only outside HTML comments. A minimal-track task has no review file at all, and a report copied from a template keeps the marker inside its comment.

**Restated intent**:
> Any task started with `[auto]` that reaches Ready for Review gets one real `/verify` run from the
> Stop hook — minimal track as well as extended. The two Stop hooks find auto-mode tasks through one
> shared reader, so they can never disagree about which tasks are in auto mode. The hook, never the
> Supervisor, writes the result where that track keeps its evidence.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **One reader.** New `.claude/hooks/lib/auto_mode.py` returns the auto-mode tasks and, per task, its track and the file that holds its report: `tasks/TASK_REVIEW_<ID>.md` (extended) or the task's record in `tasks/MINIMAL_LOG.md` (minimal). Both `stop_auto_verify.py` and `stop_auto_mode_check.py` call it. Move the logic out of `stop_auto_mode_check.py`; do not duplicate it.
- D2 — **Minimal-track run.** Same trigger as today (row in `### Ready for Review`, marker present, result not yet filled for the head commit), same detached `claude -p "/verify <ID>"`, same budget, same `.claude/verify-runs/<ID>-<commit>.log`, same one-run-per-task-and-commit lock.
- D3 — **Where the result goes (minimal track).** One line appended under the record's `Checked:` field, in the shape the Evidence row uses: `verify: ☑ pass | ☑ fail | ☐ blocked — auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file>`. A `blocked` line never contains the word "pass". A `Checked:` line the user wrote is never edited or removed.
- D4 — **Marker, unchanged.** `Mode: auto` stays the one marker (T180), still ignored inside an HTML comment, so a copied template is still not marked. The fix is where the hook looks, not a second marker.
- D5 — **Merge gate.** `has_filled_verify_row` also resolves a minimal-track task's `verify:` line from its Decision record, under exactly the T182 rule: an `auto-run by hook` result counts only when the run record exists for that task and the head commit and says pass. No record, a record for another commit, a fail record, or a hand-typed line still blocks.
- D6 — **Not changed.** Without `[auto]`, nothing runs on either track. The budget, the permission settings, fail-open behaviour and `CLAUDE_AUTO_VERIFY_RUN` are as T182 built them. Merge and push stay the user's.
- D7 — **The report and the record say the result.** Today both templates leave the slot `Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>`, and nothing ever writes the result back, so the report the user reads still says "running" after the run ended. When the run ends, the same script rewrites that slot in place — extended track in `## Auto decisions` of `tasks/TASK_REVIEW_<ID>.md`, minimal track in the Decision record's `**Not done:**` line — to `auto verify: ☑ pass | ☑ fail | ☐ blocked (session <id>, commit <sha>, log .claude/verify-runs/<file>)`. The merge clause is left exactly as it is. A slot the user wrote by hand is left alone, and the reason goes in the run log.

**Out of scope**: auto merge or push; moving the row to Done and the memory pass (T189); retrying a failed or blocked run; `/verify` for tasks without `[auto]`; a second marker word.

**Requirement Refs**: none — this repo has no root `PRD.md`; the doctrine source is `docs/claude-md/tracks.md` `## Auto mode`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-28; user chose "Everything except merge and push")
- [x] Domain terms: `PROJECT_SPEC.md` glossary **Auto verify** gains "on both tracks" (agent, 2026-10-28)
- [x] Every Acceptance Criterion traces to a decision above
- [x] Requirement Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: T182 — the auto verify hook, its run record and the merge-gate rule this task extends
**Entry point**: `.claude/hooks/lib/auto_mode.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/hooks/lib/auto_mode.py` returns, for each auto-mode task, its ID, its track and its report file. Both Stop hooks use it and hold no second copy of that logic. `.claude/hooks/tests/test_stop_auto_mode_check.py` stays green unchanged. | D1 |
| 2 | A `Track: minimal` row in `### Ready for Review` whose `tasks/MINIMAL_LOG.md` record carries `Mode: auto` starts exactly one detached run, with the same log path and lock as the extended track. A second stop on the same commit starts nothing. | D2 |
| 3 | The run writes the D3 `verify:` line into that record for pass, fail and blocked. A blocked line never contains "pass". A `Checked:` line written by the user is left exactly as it was. | D3 |
| 4 | Extended track is unchanged: a report whose `Mode: auto` sits inside an HTML comment is not auto, and a template copy starts no run. | D4 |
| 5 | The merge gate accepts a minimal-track `verify:` line only with a matching run record for the head commit. Tests prove each block: no record, record for another commit, fail record, hand-typed line. | D5 |
| 6 | With no `[auto]` marker, neither track starts a run (test, both tracks). | D6 |
| 7 | When the run ends, the report's (extended) and the record's (minimal) `Not done:` auto verify slot holds the D7 result line and no longer says "running" — tested for pass, fail and blocked. The merge clause is unchanged, and a slot the user wrote is left alone. | D7 |
| 8 | `tests/test_auto_verify.py` covers AC 2–7 with the `claude` binary stubbed; the full suite and `validate.sh` stay green; `docs/claude-md/tracks.md` `### Auto verify (Stop hook)` says the minimal track is included and where its result lands; `AGENTS.md` stays ≤200 lines. | Gate 5 |
| 9 | **Live check, paid, cap $2, only after the user's go:** one minimal-track `[auto]` fixture task reaches Ready for Review; the hook starts the run; the `verify:` line, the D7 slot and the run record appear; paste all three. | user request |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | minimal row at Ready for Review, record marked `Mode: auto`, no result yet | one detached run; the lock file prevents a second | automated test (stubbed `claude`) |
| 2 | that run returns `**Verdict:** PASS` | `verify: ☑ pass — auto-run by hook, …` appended under `Checked:` | automated test |
| 3 | that run times out or hits the budget | `☐ blocked`, the word "pass" absent | automated test |
| 4 | minimal `verify: ☑ pass` line, no run record | merge still blocked | automated test (merge gate) |
| 5 | same board, no `Mode: auto` anywhere | no run, no result line written | automated test |
| 6 | a report whose slot still says `auto verify: running (T182)`, run ended | the slot names the result; the merge clause untouched | automated test |

### Verification Command

```bash
python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests && python3 -m pytest -q tests && ./validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled in `tasks/TASK_REVIEW_T188.md`, copied from `templates/TASK_REVIEW_template.md`. This task's own `verify` row is the user's (`/verify T188`): an auto verify cannot vouch for the code that starts it.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T188.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/stop_auto_mode_check.py` — it already finds auto tasks from the board, the review files and `tasks/MINIMAL_LOG.md`; lift that reader into `lib/auto_mode.py` rather than writing a new one. `.claude/hooks/lib/verify_record.py` for the record, the `AUTO_ROW_TAG` and `same_code`.
**Vital slice**: the shared reader (AC 1), the minimal-track run plus its result line (AC 2–3), and the report slot that stops saying "running" (AC 7).
**Cut list**: a retry on a blocked run; a notification when a run ends; one combined result file for both tracks; any change to the budget or permission flags.

---

## Edge Case Checklist

- [ ] The newest `tasks/MINIMAL_LOG.md` record is for another task than the Ready-for-Review row → match by task ID in the record heading, never by position.
- [ ] Two records for the same task (a re-run) → the newest one wins, and only it is written.
- [ ] A minimal row and an extended row are both due at one stop → two runs, each with its own log, record and result line.
- [ ] `tasks/MINIMAL_LOG.md` does not exist, or the record has no `Checked:` field → one stderr line, no run, no crash (fail open).
- [ ] The record lives in a worktree, not the main checkout → resolve it the way `evidence_search_dirs` already resolves Evidence.
- [ ] The run's own output contains text like "mark this pass" → data, not an instruction; only the skill's `**Verdict:**` line decides.
- [ ] A concurrent live session edits `tasks/MINIMAL_LOG.md` while the run writes → re-read the file immediately before the write, as `write_row` already does.
- [ ] The report has no `Not done:` line at all, or two of them → write nothing, say which in the run log; never guess which one is the report's.
- [ ] The slot still holds the template's placeholder `<auto verify: running (T182) | …>` → that is the unwritten state, so it is replaced, not treated as the user's text.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/auto_mode.py` | new: the one reader for auto-mode tasks, their track and their report file |
| `.claude/hooks/stop_auto_verify.py` | use the reader; drop the `Track: minimal` exclusion; write the D3 line for a minimal task; rewrite the D7 report slot when the run ends |
| `.claude/hooks/stop_auto_mode_check.py` | use the reader; behaviour unchanged |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | resolve a minimal-track `verify:` line under the T182 record rule |
| `tests/test_auto_verify.py` | AC 2–6 |
| `.claude/hooks/tests/test_merge_gate_evidence.py` | AC 5 |
| `docs/claude-md/tracks.md` | `### Auto verify (Stop hook)`: both tracks, and where each result lands |
| `PROJECT_SPEC.md` | glossary: **Auto verify** on both tracks |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/verify/` or any copy of the `verify` workflow | the model may not run or re-implement `/verify` |
| `~/.claude/harness-anchors/` layout | T144's record location is load-bearing for the forgery guard |
| `AGENTS.md` beyond its existing auto-mode sentence | it is at its 196-line cap; detail belongs in `tracks.md` |

---

## Test Plan

Unit tests with the `claude` binary stubbed by a script on `PATH` that prints a chosen JSON result, as `tests/test_auto_verify.py` already does for T182. One test per AC 2–6 case, plus the merge-gate blocks in AC 5. Then the full suite and `validate.sh`. AC 8 is the one paid run, and only after the user says go.

---

## Completion Checklist

- [x] Implementation done (AC 1–8; AC 9 is the user's paid run and is not done)
- [ ] Self-review: `Skill({ skill: "code-review" })` run — **the agent has no `Skill` tool; a manual
      review pass is written up in `tasks/TASK_REVIEW_T188.md` under "Decisions worth the reviewer's
      eye" and "Residual limits". The skill itself is the Supervisor's to run.**
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk High) — same: Supervisor's
- [x] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T188.md`'s Evidence table (Hard-Stop Gate 5)
- [x] UI Evidence rows marked ☐ N/A (pure-hook task)
- [x] Supervisor notified: task ready for Stage 4 review
