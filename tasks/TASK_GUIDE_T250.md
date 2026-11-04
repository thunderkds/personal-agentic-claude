# TASK_GUIDE — T250: Gates tell this session's work from a parallel session's, and a blocked verify falls back to the user's `/verify`
**Date**: 2026-11-04
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: the task changes the merge gate (`.claude/hooks/pre_bash_block_unsafe_merge.py`) and the
> auto-mode Stop check. A wrong answer in either is silent and repo-wide: the gate stops gating, or it
> blocks every merge. Gate 2 floor applies (the work touches gates). Every change must fail closed.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `docs/claude-md/tracks.md` `### Auto verify (Stop hook)` and `### Auto-mode check (Stop hook)`, and the docstrings of `has_filled_verify_row` and `trace_shows_verification` in `.claude/hooks/pre_bash_block_unsafe_merge.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

Found 2026-11-04 while merging T229, T245 and T248 (board row T250). Three gaps, all seen live:

1. **G1 — blocked verify deadlock (minimal track).** T246 (docs only) got an auto verify run whose verifier answered SKIP, so the hook wrote `☐ blocked`. `stop_auto_verify.py --start T246` now prints `its result is already filled for commit …` (the blocked line counts as filled for the same code, `filled_for`). `docs/claude-md/tracks.md` says a blocked run "falls back to `/verify (yours)`". The user ran `/verify T246` in session `f5ea81bb-c349-4953-9f6b-0307a641966a` and it passed, but `has_filled_verify_row` (T188 D5) counts only hook-written `auto-run by hook` lines for a minimal-track task. So the documented fallback can never open the gate.
2. **G2 — another session's In Progress task blocks every merge.** T249 (another session's experiment, `../wt-t249`) was In Progress, so the gate refused this session's merges of unrelated branches (`fix/t229-auto-scope`, also `git merge-tree`). No active-task state file names T249, so `active_task.d` cannot tell who owns it.
3. **G3 — the auto-mode Stop check charges a parallel session's task to this one.** `stop_auto_mode_check.py` `check_task` (around line 334) marks a task auto when any of its files has an mtime inside this session's `[auto]` window. T249's own session wrote its files between 04:47 and 08:31 (UTC 2026-11-04), inside this session's window, so every stop here was blocked with "T249: tasks/TASK_REVIEW_T249.md has no `## Auto decisions` section".

User decision 2026-11-04 (AskUserQuestion, G1): *"Gate reads your /verify (Recommended)"* — the gate accepts a hand-written pass line only when the session transcript shows the user typed `/verify <ID>`.

**Restated intent**:
> The merge gate and the auto-mode Stop check judge only work this session did. A task worked on by another session neither blocks this session's merge nor its stop. When an auto verify run is blocked, the user's own `/verify <ID>` — proven from the transcript, not from the line's text — opens the gate for a minimal-track task.

**Out of scope**:
- Changing what the headless verifier answers (SKIP stays `blocked`).
- Changing how the extended-track Evidence row is read (`verify_row_passes` for `TASK_REVIEW_*.md`), except where G1's fallback needs the same rule there.
- Board mode `online` assignee logic (T157, T161) — keep it working as is.
- Merging anything, or editing T246 / T249 records.

**Requirement Refs**: no `PRD.md` IDs (`PROJECT_SPEC.md` `## Readiness`: `README.md` stand-in). Traces to G1–G3 and the user decision above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed against the user's "do T250" and the G1 choice (Supervisor, 2026-11-04)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — **auto verify run**, **Decision record**, **merge gate**
- [x] Every Acceptance Criterion below traces to G1, G2 or G3
- [x] No `PRD.md` IDs exist; G1–G3 are covered by AC 1–9

---

## Dependencies & Reachability

**Depends on**: `None` (T229 is merged at `c7761770`; this task builds on its `auto_windows`)

**Entry point**: `has_filled_verify_row` (merge gate, G1/G2 in `pre_bash_block_unsafe_merge.py`) and `check_task` (Stop check, G3 in `stop_auto_mode_check.py`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Minimal track: a Decision record line `- verify: ☑ pass — /verify by the user, session <sid>, commit <sha>` passes `has_filled_verify_row` **only** when the transcript of session `<sid>` holds a human user entry whose command is `/verify` with args naming the task ID (`<command-name>/verify</command-name>` + `<command-args>T246</command-args>`), dated before the line was committed, and `<sha>` is the same code as the checkout head (`vr.same_code`, the report file excepted) | G1 |
| 2 | Negative: the same line with no matching `/verify` in that transcript, a `/verify` for another task ID, a `/verify` from a non-human entry (task notification, `isMeta`, tool result), a missing or unreadable transcript, or a commit with other code → not a pass (fail closed) | G1 |
| 3 | `stop_auto_verify.py` never overwrites or removes the user line, and `--start` still starts nothing for it; `docs/claude-md/tracks.md` `### Auto verify (Stop hook)` states the exact line shape the user's fallback uses | G1 |
| 4 | Ownership: one helper (in `.claude/hooks/lib/`) answers "did this session work on task X" from the session transcript: a non-read tool call (`Edit`, `Write`, `NotebookEdit`, or a `Bash` command whose working directory or file arguments are the task's worktree or its `tasks/*_T<id>*` files, or an `Agent` spawn naming the task) by this session. Read-only calls (`Read`, `Grep`, `Glob`, a `Bash` `grep`/`cat`/`git log`) do not count | G2, G3 |
| 5 | Merge gate: an In Progress task blocks this merge only when this session worked on it (AC 4), or the merge brings in its branch, or ownership cannot be decided (no transcript, unreadable) — fail closed. T249's case (another session's task, unrelated branch) no longer blocks | G2 |
| 6 | Merge gate: the T157/T161 online-mode assignee scoping still holds unchanged (existing tests stay green) | G2 regression |
| 7 | Stop check: a task is auto-mode work only when its files changed inside an `[auto]` window **and** this session worked on it (AC 4), or its report has the `Mode: auto` line. T249's case no longer blocks this session's stop; a task this session edited in the window still does | G3 |
| 8 | Every new path fails closed: an exception or unreadable input keeps today's behaviour (block / check), never a silent pass. A test proves it for each of AC 1, 5, 7 | all |
| 9 | Full suite green against a `main` run; `memory/MEMORY.md` untouched by tests | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture transcript with a human `/verify T900` entry + a user pass line for T900 | `has_filled_verify_row("T900")` True | automated test |
| 2 | Same line, transcript has `/verify T901` only / no transcript / a `task-notification` entry | False | automated test |
| 3 | Board: T900 In Progress, fixture transcript of this session shows only `Grep` on T900 files; command merges `fix/t901-x` | gate does not list T900 | automated test |
| 4 | Same, transcript has an `Edit` of `tasks/TASK_GUIDE_T900.md` | gate blocks: `Tasks still In Progress: T900` | automated test |
| 5 | Stop check: T900 files' mtime inside an `[auto]` window, this session never wrote them | T900 not checked | automated test |
| 6 | Same, this session `Write`s T900's review file in the window | T900 checked as today | automated test |
| 7 | Real run: on this repo, with T249 In Progress (or a copy of that board state) and T246's user line, the gate's decision for `git merge --no-ff <unrelated branch>` | no `T249` blocker; T246 accepted only with session f5ea81bb's transcript | app run |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_t250_session_ownership.py -q
python3 -m pytest .claude/hooks/tests/ tests/ -q
# ci: skip for the line below — needs this machine's session transcripts
echo '{"tool_name":"Bash","tool_input":{"command":"git merge --no-ff fix/t229-auto-scope"},"transcript_path":"'"$HOME"'/.claude-personal/projects/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/f5ea81bb-c349-4953-9f6b-0307a641966a.jsonl","session_id":"f5ea81bb-c349-4953-9f6b-0307a641966a","cwd":"'"$PWD"'"}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py; echo "exit=$?"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T250.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T250.md`.

---

## Approach

**Pattern reference**: `auto_windows()` and `request_text()` in `.claude/hooks/stop_auto_mode_check.py` (T229) — the transcript reader to reuse for both the `/verify` entry (AC 1) and ownership (AC 4); `auto_row_confirmed` in the merge gate for the "same code" check.

**Vital slice**: one transcript-ownership helper in `.claude/hooks/lib/`, used by the gate (G2) and the Stop check (G3); one extra accepted line shape in `minimal_line_passes` backed by the transcript (G1).
**Cut list**:
- Extended-track user `/verify` fallback in `TASK_REVIEW_*.md` — not seen live; add only if a test of AC 1's helper makes it free.
- A session-id field in `memory/event-trace/*.jsonl` — would be cleaner ownership, but it changes every trace writer.
- Detecting a parallel session that is still running (process or lock checks).

---

## Edge Case Checklist

- [ ] The transcript of the session named in the user line is not the current session's (the user ran `/verify` in a different session) — read that session's file by id from the same projects folder; missing → fail closed
- [ ] `/verify` typed with extra words (`/verify T246 please`) still names T246; `/verify T2460` does not
- [ ] The user line exists but an auto `☑ pass` line for the head also exists — either passes; no double counting problems
- [ ] A task with no worktree and no files yet (just a board row) and no transcript activity — not this session's work, does not block (but log it)
- [ ] Bash commands that write through `cd <worktree> && …` count as work; `git -C <worktree> log` does not
- [ ] Sub-agent transcripts (`subagents/`) of this session count as this session's work
- [ ] Huge transcripts: read line by line, no whole-file load

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/session_work.py` | new — transcript ownership helper (AC 4) and `/verify` entry finder (AC 1) |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | G1 line shape in `minimal_line_passes`; G2 In Progress scoping (AC 1, 2, 5, 8) |
| `.claude/hooks/stop_auto_mode_check.py` | G3: `check_task` also requires session work (AC 7, 8) |
| `docs/claude-md/tracks.md` | the user fallback line shape; ownership rule (AC 3) |
| `.claude/hooks/tests/test_t250_session_ownership.py` | new — AC 1–8 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `AGENTS.md` | no doctrine change; 196/200 lines |
| `tasks/MINIMAL_LOG.md` T246 record, `tasks/*T249*` | other tasks' records |
| `memory/MEMORY.md` | hot tier is at its char ratchet (41,942 / 42,000) |
| `.claude/hooks/stop_auto_verify.py` verdict parsing | out of scope |

---

## Test Plan

Test-first (`tdd`): `.claude/hooks/tests/test_t250_session_ownership.py` with fixture transcripts (JSONL lines shaped like real Claude Code entries: `type`, `timestamp`, `message.content`, `origin.kind`, tool_use blocks). Red first, then the helper, then wire each hook. Run the full suite and compare with `main`. Real run: the Verification Command's last line against this repo.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk High)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T250.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — via the headless auto verify run
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
