# TASK_GUIDE — T210: Merge gate closes four gaps — `git pull` is gated, `timeout`-wrapped test runs count, `git merge-base` is read-only, and the verify row must be committed on the branch
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
6. Read `.claude/hooks/pre_bash_block_unsafe_merge.py` end to end (`BLOCKED_PATTERNS`, `BENIGN_COMMAND_PREFIX`, `strip_command_prefixes`, `invokes_test_runner`, `trace_shows_verification`, `evidence_search_dirs`, `has_filled_verify_row`, `pushed_task_ids`, `main`), `.claude/hooks/tests/merge_gate_guard.py`, and the gate's test files under `.claude/hooks/tests/`
7. Read `memory/learnings.md` `### Merge-gate blind spots seen on 2026-10-29` and the T207/T208 entries in `memory/decisions.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29: "go" — to the Supervisor's offer to plan the merge-gate blind spots as fix tasks. The gate-file change needs the user's sign-off (`merge_gate_guard.AUTHORISED_TASKS`); see the Fidelity Gate.

**Observed gaps** (Supervisor, 2026-10-29, all measured):
- **G1** `BLOCKED_PATTERNS` covers `git push`, `git merge`, `git rebase` only. `git pull` (fetch + merge) is ungated. The T189 AC 11 run 3 headless auto Supervisor ran `git pull`.
- **G2** `BENIGN_COMMAND_PREFIX` peels `sudo|env|time|nohup|npx|uv run|…` but not `timeout <N>`, so `timeout 900 python3 -m pytest …` is not a test run; T189's agent ran only such commands and its trace read "no verified tool call".
- **G3** `\bgit\s+merge\b` also matches `git merge-base`, a read-only query; a `git merge-base --is-ancestor` check was blocked as a merge while tasks were open.
- **G4** `has_filled_verify_row` reads review files from `evidence_search_dirs` (the worktrees' working trees). The auto verify run writes the `verify` row into the worktree AFTER the branch's last commit, so T207 and T208 were merged with a pass the merged commit did not contain (each needed a second merge to carry the row).

**Restated intent**:
> The gate blocks every command that can merge (including `git pull`), never blocks a read-only `git merge-base`, counts a test run wrapped in `timeout <N>`, and accepts a `verify` row only when that row is committed on the branch being merged or pushed. Where it is unsure, it blocks (fail closed).

**Supervisor design decisions**:
- **D1 (G1)** `git pull` is treated as a merge: whole-board check, same message. `git pull --ff-only` and `git pull --rebase` are also gated (both change the branch).
- **D2 (G2)** add `timeout(?:\s+-[-\w=]+)*\s+\d+[smhd]?` to the benign prefixes. Nothing else is added.
- **D3 (G3)** `merge-base` (and only it) is exempted: `\bgit\s+merge\b(?!-)`. `git merge-file`, `git merge-tree` stay blocked (they are not read-only in every form, and nobody asked).
- **D4 (G4)** for a merge or push of a task branch, the `verify` row counts only if `git show <branch>:tasks/TASK_REVIEW_<ID>.md` (or the guide, guide first) holds it. A row present only in the working tree gives a new message: `verify row for <ID> is not committed on <branch> — commit it, then merge`. When the branch cannot be resolved, keep today's behaviour (whole-board check reading working trees) — never weaker than today.

**Out of scope**: the auto verify parser (T209); the push-scope rules of T197; the board reader.

**Requirement Refs**: no PRD — traces to `memory/learnings.md` (2026-10-29 entries) and the T189/T207/T208 logs.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, 2026-10-29; user "go")
- [ ] **User sign-off: add `T210` to `merge_gate_guard.AUTHORISED_TASKS`** (the gate file may not change without it) — PENDING
- [x] Every Acceptance Criterion traces to G1–G4 / D1–D4
- [x] Requirement Refs — N/A, traced to the learnings above

> The agent must NOT start until the user sign-off box is checked.

---

## Dependencies & Reachability

**Depends on**: T197 (push scope, merged), T208 (merged)
**Entry point**: `.claude/hooks/pre_bash_block_unsafe_merge.py` (PreToolUse on `Bash`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | With an unverified task on the board, `git pull`, `git pull --ff-only`, `git pull --rebase origin main`, and `cd x && git pull` are blocked with the merge message; with a clean board they are allowed | G1, D1 |
| 2 | `git merge-base --is-ancestor A B`, `git merge-base A B` are allowed with an unverified task on the board; `git merge feat/x` is still blocked | G3, D3 |
| 3 | A trace record `timeout 900 python3 -m pytest -q`, `timeout -k 5 60s pytest`, `(timeout 300 python3 -m pytest …)` counts as a test run; `timeout 900 echo pytest` does not | G2, D2 |
| 4 | Merge of a task branch whose `verify ☑ pass` row is only in the worktree's working tree → blocked with the D4 message; after committing the row → allowed. Same for a narrowed push (T197) | G4, D4 |
| 5 | Branch not resolvable → today's behaviour (asserted by an existing-behaviour test) | D4 fail-safe |
| 6 | `merge_gate_guard.AUTHORISED_TASKS` gains `T210`; `test_merge_gate_guard.py` passes | sign-off |
| 7 | Mutations, each turns a new test RED: **M1** drop `pull` from the patterns; **M2** drop the `(?!-)`; **M3** drop the `timeout` prefix; **M4** read the verify row from the working tree again | guarantees asserted |
| 8 | `.claude/hooks/tests`, `tests` pass in full; the gate's oracle data files (`t190_`, `t197_pre_change_gate_output.txt`) are regenerated only if a message text changed, with the reason in the commit | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a throwaway clone with an In Progress row | a real PreToolUse JSON event for `git pull` is blocked; for `git merge-base --is-ancestor HEAD main` is allowed | feed events to the real hook |
| 2 | a throwaway clone where the verify row is uncommitted in a worktree | merge blocked with the D4 message; after commit, allowed | real hook |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q && python3 -m pytest tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T210.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T210.md`.

---

## UI / Design Acceptance Criteria

N/A — hook-only change. All three UI Evidence rows ☐ N/A (justification: no UI component).

---

## Approach

**Pattern reference**: T197 (`pushed_task_ids`, narrowed push) for resolving the branch; T099 tests for command-classification cases.
**Vital slice**: G1 + G3 (two regex changes) and G4 (committed-row read) with tests; G2 is one prefix.
**Cut list**: gating other git subcommands; changing the push-scope rules; reformatting messages.

---

## Edge Case Checklist

- [ ] `git pull` inside `bash -c "…"` is blocked (T099 wrapper rule); `grep "git pull"` is a mention
- [ ] A detached HEAD or a branch name with `/` resolves for D4
- [ ] Guide-first, review-second order kept for D4 (`guide_sections`)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | G1–G4 |
| `.claude/hooks/tests/merge_gate_guard.py` | `AUTHORISED_TASKS` += `T210` (after sign-off) |
| `.claude/hooks/tests/test_*` (gate tests) | AC 1–5, 7 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` | T209 |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first for AC 1–4 on `main`, then each change, the M1–M4 mutations by hand, both Success Criteria through the real hook, then the full suites run plainly.

---

## Completion Checklist

- [ ] User sign-off recorded (Fidelity Gate)
- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T210.md` (Hard-Stop Gate 5)
- [ ] Supervisor Stage 4 review (code-review + security-review, Risk High)
- [ ] Auto verify run started by the Supervisor (T203)
