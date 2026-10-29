# TASK_GUIDE — T211: Merge gate sees `git -C`/`-c` forms and resolves merges with any option, so the committed-row rule cannot be skipped
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: High
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
6. Read `.claude/hooks/pre_bash_block_unsafe_merge.py` end to end — above all `BLOCKED_PATTERNS`, `strip_quoted_spans`/`strip_heredoc_bodies`, `_command_segments`, `_git_actions`, `MERGE_FLAGS`, `_merge_source`, `branch_target`, `committed_verify_row`, `pushed_task_ids`, `main` — then `tasks/TASK_GUIDE_T210.md` and `.claude/hooks/tests/test_merge_gate_t210.py`
7. Read the T209/T210 entry in `memory/decisions.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29: "yes" — to the Supervisor's offer to plan T211 (registered from the T210 auto verify findings and Stage 4 P2).

**Observed gaps** (measured by the T210 auto verify run and Stage 4, 2026-10-29):
- **G5** `BLOCKED_PATTERNS` need `git` directly followed by the verb. `git -C <dir> merge|push|pull|rebase`, `git -c k=v merge`, `git --git-dir=… push`, `git --no-pager merge` match nothing, so they run with no check at all.
- **G6** `_merge_source` returns None for any option outside `MERGE_FLAGS` (`-X ours`, `-s`/`--strategy recursive`, `--allow-unrelated-histories`, `-S`) and for an octopus merge (two or more branches). `branch_target` is then None, and D4 falls back to the working-tree read — the hole that let T207/T208 merge without a committed pass row.
- **G7** `git -c alias.<x>=push <x>` defines and runs an alias in one command; the verb never appears.

**Restated intent**:
> Any `git` command that can merge, push, pull or rebase is gated, whatever global options come between `git` and the verb. A merge resolves to the branches it names whatever its options are, and each named task's verify row must be committed on its branch. When the gate cannot tell what a `git` command does, it treats it as gated (fail closed).

**Supervisor design decisions**:
- **D1 (G5)** one shared pattern for the verb after optional global options: `-C <path>`, `-c <k=v>`, `--git-dir[= ]<p>`, `--work-tree[= ]<p>`, `--namespace[= ]<n>`, `--no-pager`, `-P`, `--bare`, `--no-replace-objects`, `--literal-pathspecs`, `--exec-path[=<p>]`. `BLOCKED_PATTERNS` and `_git_actions` both use it, so classification and narrowing cannot drift. `-C <dir>` changes the directory `_git_actions` resolves in (same as `cd <dir> &&`).
- **D2 (G6)** `_merge_source` skips any `-`-option, and also skips the argument of options that take one (`-m`, `-F`, `-s`, `--strategy`, `-X`, `--strategy-option`, `--into-name`; `--opt=value` is one token). Every remaining name is a branch. One branch → today's D4 path. Two or more (octopus) → each must resolve to exactly one task and each task's row must be committed on its branch; any doubt → block with a message naming the branch.
- **D3 (G7)** `-c alias.<anything>=…` anywhere in a `git` invocation → the command is gated as a merge (whole-board check). A configured alias (in `.gitconfig`) stays out of reach of a static check: document it as a known limit in the gate's docstring, do not try to read git config.
- **D4** fail closed: a `git` command with a global option this pattern does not know, followed by any word, is gated only if that word is `push|merge|rebase|pull` — unknown options are skipped the same way as known ones (`-x`, `--x`, `--x=y`).

**Out of scope**: shell aliases and functions (`alias gp='git push'`), scripts that call git, `hub`/`gh pr merge` (no local merge).

**Requirement Refs**: no PRD — traces to the T210 verify log `.claude/verify-runs/T210-7ea033bef3f5.log` (steps 9, 10) and the T209/T210 decision entry.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, 2026-10-29; user "yes")
- [ ] **User sign-off: add `T211` to `merge_gate_guard.AUTHORISED_TASKS`** — PENDING
- [x] Every Acceptance Criterion traces to G5–G7 / D1–D4
- [x] Requirement Refs — N/A, traced to the log and decision above

> The agent must NOT start until the user sign-off box is checked.

---

## Dependencies & Reachability

**Depends on**: T210 (merged)
**Entry point**: `.claude/hooks/pre_bash_block_unsafe_merge.py` (PreToolUse on `Bash`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | With an unverified task on the board, each is blocked: `git -C ../wt-x merge feat/x`, `git -C /abs push origin feat/x`, `git -c core.x=y merge feat/x`, `git --git-dir=.git push`, `git --no-pager pull`, `git -C x rebase main`; and `git -C x merge-base A B`, `git -C x log` are allowed | G5, D1 |
| 2 | `git -C <worktree> push origin feat/t900-x` narrows to T900 exactly like `cd <worktree> && git push origin feat/t900-x` (T197 behaviour) | D1 |
| 3 | `git merge -X ours feat/t900-x`, `git merge -s recursive feat/t900-x`, `git merge --strategy=ours feat/t900-x`, `git merge --allow-unrelated-histories feat/t900-x` resolve to T900; with T900's row only in the worktree → blocked with the T210 D4 message; committed → allowed | G6, D2 |
| 4 | Octopus `git merge feat/t900-x feat/t901-y`: both committed → allowed; either uncommitted → blocked naming that branch; a branch naming no task → blocked | D2 |
| 5 | `git -c alias.p=push p`, `git -c alias.m='merge' m feat/x` → gated as a merge (blocked with an unverified board) | G7, D3 |
| 6 | Mentions stay mentions: `grep "git -C x push"`, a heredoc body, `echo git -c alias.p=push p` are allowed (T099 rules unchanged) | regression |
| 7 | `merge_gate_guard.AUTHORISED_TASKS` += `T211`; every existing gate test and the oracle files pass unchanged | sign-off, regression |
| 8 | Mutations, each turns a new test RED: **M1** drop the global-option prefix from the blocked pattern; **M2** restore `_merge_source`'s "unknown option → None"; **M3** let an octopus merge resolve to its first branch only; **M4** drop the alias rule | guarantees asserted |
| 9 | `.claude/hooks/tests` and `tests` pass in full, run plainly | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a throwaway clone with an In Progress row | real PreToolUse JSON events: `git -C . merge feat/x` and `git -c alias.p=push p` blocked; `git -C . log` allowed | feed events to the real hook |
| 2 | a throwaway clone, row only in the worktree | `git merge -X ours feat/t900-x` blocked with the D4 message; after commit, allowed | real hook |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q && python3 -m pytest tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T211.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T211.md`.

---

## UI / Design Acceptance Criteria

N/A — hook-only change. All three UI Evidence rows ☐ N/A (justification: no UI component).

---

## Approach

**Pattern reference**: T210's `_git_actions` / `branch_target` / `committed_verify_row` and its test file; T099 wrapper-aware quoting.
**Vital slice**: D1 (shared global-option prefix in the blocked pattern and `_git_actions`) and D2 (option-agnostic `_merge_source`) with tests.
**Cut list**: reading git config for aliases; shell aliases; `gh pr merge`.

---

## Edge Case Checklist

- [ ] `git -C "dir with space" push` — a quoted path (the pattern must not break T099 quoting)
- [ ] `git -Cdir push` (attached form) — treat as gated
- [ ] `git merge -m "message with feat/x in it" feat/y` — the message is not a branch

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | D1–D4 |
| `.claude/hooks/tests/merge_gate_guard.py` | `AUTHORISED_TASKS` += `T211` (after sign-off) |
| `.claude/hooks/tests/test_merge_gate_guard.py` | the allowlist pin |
| `.claude/hooks/tests/test_merge_gate_t211.py` | new: AC 1–6, 8 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/stop_auto_verify.py`, `lib/*` | out of scope |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first for AC 1–5 on `main`; then D1, D2, D3; M1–M4 by hand; both Success Criteria through the real hook in a throwaway clone (never by running a gated command in a real Bash call); then the full suites run plainly. Commit everything; leave nothing uncommitted.

---

## Completion Checklist

- [ ] User sign-off recorded (Fidelity Gate)
- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T211.md` (Hard-Stop Gate 5)
- [ ] Supervisor Stage 4 review (code-review + security-review, Risk High)
- [ ] Auto verify run started by the Supervisor (T203); its row committed on the branch before the merge (T210)
