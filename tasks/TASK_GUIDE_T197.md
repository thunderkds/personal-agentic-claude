# TASK_GUIDE — T197: The push gate checks the task being pushed, not every task on the board
**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: this task **loosens** a fail-closed security gate. A wrong edit lets an unverified task's
> branch leave the machine, or lets a push that should be global slip through as "scoped". `security-review`
> is mandatory at Stage 4. Every doubt must still resolve to today's behaviour: check the whole board.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` for directory layout and blast-radius hotspots
7. Read `.claude/hooks/pre_bash_block_unsafe_merge.py` **in full** before editing one line of it, and `.claude/hooks/tests/test_merge_gate_evidence.py`, `test_merge_gate_t095.py` and `test_merge_gate_companion_rows.py` for how it is tested
8. Read the `T044` comment at the top of that file. A broken check in this exact file went unnoticed for three sessions

> **Live-session warning.** T188, T189 and T196 each touch `pre_bash_block_unsafe_merge.py`, mostly the
> `ready_review` loop that this task also edits. Before you edit that file, run `git log --oneline -3`
> and `git status --short`, and check whether their change has landed. If it has not, report it and ask
> the Supervisor rather than merging by hand. T190 (the companion-row check, in the same loop) lands first.

---

## Requirement (Pillar 1 — Adapt the requirement)

Found on 2026-10-28 while pushing T190. The push was refused with
`Tasks in Ready for Review missing Stage 5 verify evidence: T195 (no evidence row)`. T195 is another
session's task and has nothing to do with the T190 branch being pushed. User: *"it does not related, so
we do not need to wait it, just focus on your tasks and push"*, then *"create the task to update this
gate, cause I saw the unconditional here"*.

Measured cause: `main()` builds `ready_review` and `in_progress` with `tasks_in_section(...)` over the
**whole board**. Nothing in that code reads which branch the command pushes. In `local` board mode, one
task parked in Ready for Review, or In Progress, by any other live session stops every other session's push.

**Restated intent**:
> A `git push` of a task's branch is judged by that task's own state. Another session's open task does
> not block it. When the hook cannot tell which task a command touches, it checks the whole board,
> exactly as it does today.

**Out of scope** (what this task explicitly does NOT do):
- Merges. A `git merge` still checks the whole board: a merge puts every pending task into the target branch. Only `git push` of a branch that names exactly one task is scoped.
- Pushes of `main`, a `release/*` branch, an integration branch, `--all`, `--mirror` or a tag. They stay global.
- The `verify` row rules, `has_filled_verify_row`, `trace_shows_verification` and the T190 companion-row rules. They are unchanged. This task only decides **which tasks** they run on.
- The `online` board mode filters (`my_blocking_tasks`, `my_review_tasks`). They stay as they are. When they apply, scoping is applied on top of their result, never instead of it.
- T196 (per-worktree attribution of the event trace). A scoped push still needs its own task's trace.

**Requirement Refs**: none. This task has no PRD. It traces to the two quoted user messages above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, from the two quoted messages above)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary. Terms used: **Ready for Review**, **Evidence row**, **verify row**, **board mode**
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: none exist; the Acceptance Criteria trace to the quoted user messages

---

## Dependencies & Reachability

**Depends on**: `None`. T190 is the same loop; see the live-session warning for landing order.

**Entry point**: `pushed_task_ids`

---

## Acceptance Criteria

Design decisions are made here by the Supervisor. The agent does not reopen them. If one proves wrong, STOP and ask.

**D1. How the hook finds the pushed task.** From the branch the command pushes, never from the board. Resolution order:
1. An explicit source ref in the command (`git push origin feat/t190-x`, or `src:dst` → `src`).
2. `HEAD`, or no refspec: the current branch of the directory the command runs in. That is `git -C <dir>` if given, else a leading `cd <dir> &&` if given, else the event's `cwd`. Read it with `git rev-parse --abbrev-ref HEAD`, 5-second timeout.
3. The branch name must contain **exactly one** task ID (the board's `id_pattern`, case-insensitive: `t190` -> `T190`). Zero IDs, or two or more (for example `plan/t190-t194-...`), mean "unresolved".

**D2. Unresolved means global.** Every failure of D1 (no branch, detached HEAD, git absent, timeout, unparsable command, `main`, `release/*`, `--all`, `--mirror`, a tag, a task ID that is not on the board) keeps today's check over the whole board. Fail closed, as the rest of this file does.

**D3. A scoped push checks only the pushed task**, in both sections: if it is In Progress it blocks; if it is Ready for Review it needs the verify evidence and the T190 companion-row rules. Other tasks in either section are ignored. A scoped push of a task that is Todo, Done or absent from the board is allowed by the board check, since the branch is not a pending review.

**D4. `git merge` and every non-push trigger are not scoped** (see Out of scope).

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Fixture board: T900 and T901 both Ready for Review. T900 has a filled verify row and trace; T901 has no Evidence row. `git push origin feat/t900-x` -> no block | Restated intent, first sentence |
| 2 | Same fixture, `git push origin feat/t901-x` -> blocked, and the reason names `T901` and not `T900` | Restated intent |
| 3 | Same fixture, `git push origin main` -> blocked, naming `T901`. This is today's output, byte for byte | Restated intent, second sentence |
| 4 | **Negative case:** a branch naming two IDs (`plan/t900-t901-x`) -> whole-board check, blocked on `T901` | D1.3, D2 |
| 5 | **Negative case:** a scoped push of T900 with T900 itself In Progress -> blocked | D3 |
| 6 | **Negative case:** a scoped push of T900 whose own companion row reads `☑ fail` -> blocked (T190 rule still binds the pushed task) | D3 |
| 7 | **Negative case:** `git push` with no refspec, `cwd` on branch `feat/t900-x` -> scoped to T900. With `cwd` not a git repo, or a detached HEAD -> whole board | D1.2, D2 |
| 8 | **Negative case:** `git merge feat/t900-x` with T901 unverified -> blocked, naming `T901` | D4 |
| 9 | **Negative case:** `git push --all`, `git push --mirror`, `git push origin v1.0` (tag) -> whole board | D2 |
| 10 | **Negative case:** a branch name that merely contains a task-like string inside a longer word (`feat/fix-t9000-typo` against board IDs T900/T9000, `feat/cat900`) resolves only on a whole-ID match, never a substring | D1.3 |
| 11 | **Negative case:** a command that mentions the branch only in prose or a heredoc (`cat <<EOF ... git push origin feat/t900-x ... EOF`) does not scope anything. The scoping reads the real `git push` invocation, the same way the existing gate already ignores heredoc text | D2 |
| 12 | With the board having **no** Ready for Review and no In Progress task, the output is byte-identical to the pre-change hook (oracle captured before the edit, as in T190 AC 4) | Restated intent |
| 13 | Every pre-existing hook test still passes, and `sh scripts/validate.sh` reports PASS | Restated intent |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The AC-3 and AC-12 oracle is **specified** by the Supervisor and **captured** by the implementing agent before the implementation edit exists. Write the fixture and its capture entry point first, run it against the unchanged hook, commit the output, and only then edit the hook. Do not stash to get the old output.

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | AC 1 fixture, hook run on stdin with `git push origin feat/t900-x` | exit 0, empty stdout | automated test |
| 2 | AC 2 fixture | `{"decision": "block"}`, reason names `T901` only | automated test |
| 3 | AC 3 and AC 12 fixtures against the pre-change oracle | stdout and stderr equal the committed oracle | automated test |
| 4 | Each negative case in AC 4-11 | the stated outcome | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_merge_gate_push_scope.py -q \
  && python3 -m pytest .claude/hooks/tests/ -q \
  && sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T197.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T197.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/pre_bash_block_unsafe_merge.py`, `strip_command_prefixes` (line 144), `evidence_search_dirs` and `worktree_tasks_dirs` (276-325). Imitate three things: structural parsing of the command (never a substring search; see the T044 comment), a 5-second timeout on every `git` subprocess, and "every failure degrades to today's behaviour". `.claude/hooks/lib/task_context.py` already resolves a task from a worktree; read it before writing new resolution code.

**Vital slice**: a function `pushed_task_ids(command, cwd)` that returns one task ID or `None`, plus the two-line change in `main()` that narrows `in_progress` and `ready_review` to it when it returns one. `None` leaves `main()` exactly as it is.
**Cut list**:
- Range branch names (`t190-t194`) are not expanded. Two IDs means global. Expanding is a later task if it hurts.
- No change for `online` mode filters.
- No scoping of `git merge`, `git pull`, `gh pr merge`.
- No new setting or env var to turn scoping off. The only switch is the branch name.

The agent follows `tdd`: RED test file first (oracle committed before the hook edit), then GREEN.

---

## Edge Case Checklist

- [ ] The session's `cwd` is the main checkout on `main`, while the command is `cd ../wt-x && git push origin HEAD`. A scoped result must come from the `cd` target, never from the session `cwd`. Resolving `HEAD` against the wrong directory is the worst failure here: it scopes to the wrong task, or silently to none.
- [ ] `git push origin HEAD:refs/heads/main` from a `feat/t900-x` branch pushes **to main**. The destination matters: a push whose destination is `main`, `release/*` or an integration branch stays global even when the source is a task branch.
- [ ] `git push -u origin feat/t900-x` and `git push --force-with-lease origin feat/t900-x`: flags before and after the remote.
- [ ] A command chain: `git commit ... && git push origin feat/t900-x`. The gate sees the whole string. Resolve each `git push` invocation; if there is more than one, any unresolved invocation makes the result global.
- [ ] Branch name contains an ID but the board has no such task (`feat/t999-x`): global (D2).
- [ ] Mixed case `Feat/T900-X`.
- [ ] A task whose branch name carries the **wrong** ID. The scoping trusts the branch name. Record in the TASK_REVIEW that this is a stated trust boundary: a branch that lies about its task is checked against that other task, and the push still needs *that* task's evidence.
- [ ] `git` missing or the 5-second timeout fires: global.
- [ ] The `online` mode path still runs `pull_cache` and its filters before scoping.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | add `pushed_task_ids`; narrow `in_progress` and `ready_review` in `main()` when it resolves |
| `.claude/hooks/tests/test_merge_gate_push_scope.py` | new: AC 1-11 |
| `.claude/hooks/tests/data/t197_pre_change_gate_output.txt` | new: the AC 3 / AC 12 oracle, captured before the hook edit |
| `docs/claude-md/` page that documents the gate, if one exists | one paragraph: a branch push is judged by its own task; merges and unresolved pushes by the whole board |

Existing tests may pin the old whole-board behaviour. If one fails because it asserts that an unrelated task blocks a task-branch push, widen that single assertion and record it, as T190 did (`9d99aa8`). Do not repoint `BASE_REF`.

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/verify_record.py` | the T182 verify record; a separate gate |
| `.claude/hooks/post_tool_trace.py`, `.claude/hooks/.state/` | trace attribution is T196 |
| `PROJECT_KANBAN.md`, `memory/` | the Supervisor owns them |
| `.claude/settings.json` | no new hook is registered; the existing one is edited |

---

## Test Plan

1. RED: write `test_merge_gate_push_scope.py` and the oracle capture entry point. Run the capture against the unchanged hook and commit the output. Run the new tests and show them fail.
2. GREEN: implement `pushed_task_ids` and the `main()` narrowing. Show the new tests pass.
3. Run the full hook suite and `scripts/validate.sh`.
4. Drive the real hook on stdin against a constructed repo, as `/verify T190` did, for AC 1, 2, 3, 8 and one chain command. Paste the output.
5. Before Done: the user runs `/verify T197`, and the Supervisor runs `code-review` and `security-review`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk High)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T197.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
