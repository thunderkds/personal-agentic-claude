# TASK_GUIDE — T152: `dirty_worktrees.py` finds the board from the repo root, not the current folder
**Date**: 2026-10-19
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` — skip, this task is C0 and touches one known file plus its test

---

## Requirement (Pillar 1 — Adapt the requirement)

Registered 2026-10-17 from T150's `/verify`: `skills/wake/scripts/dirty_worktrees.py` reads
`PROJECT_KANBAN.md` relative to cwd, so from `docs/` it finds no board and prints nothing while a
worktree is dirty. `wake` always runs it from the repo root, so only a by-hand run is affected.
Fix: resolve the board from `git rev-parse --show-toplevel`.
The user, 2026-10-19: "yes, do it and push to the current branch also".

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Running `dirty_worktrees.py` from any subfolder of the repo gives the same output as running it
> from the repo root, because the board path is resolved from the git top-level directory.

**Out of scope** (what this task explicitly does NOT do):
- Any change to the output format, the In Progress parsing, the worktree filtering, or `skills/wake/SKILL.md`
- Choosing a different board when run inside a linked worktree (it reads that worktree's own board — see Edge Cases)

**Requirement Refs**: none in `PRD.md` — follow-up bug from T150's `/verify`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-19)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (follow-up bug, no PRD ID)

---

## Dependencies & Reachability

**Depends on**: T150 — `skills/wake/scripts/dirty_worktrees.py` and `tests/test_dirty_worktrees.py` must exist (Done, merged)

**Entry point**: `dirty_worktrees.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Run from a subfolder of the main worktree with a dirty In Progress worktree, the script prints the same line as from the root | "from `docs/` it finds no board and prints nothing" |
| 2 | Every existing T150 test still passes unchanged (root run, no board, not a git repo, missing worktree dir) | "Fix" must not regress T150 |
| 3 | Outside a git repo the script still prints nothing and exits 0 | fail-open contract of the script |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | temp repo, In Progress T901, dirty worktree on `feat/t901-x`, cwd = `repo/docs` | `T901 <wt> 1 modified, 2 untracked` | new pytest `test_subfolder_run_finds_board` |
| 2 | the T150 fixtures | all existing tests green | `pytest tests/test_dirty_worktrees.py` |
| 3 | cwd not in a git repo | empty stdout, exit 0 | existing `test_sc5_not_a_git_repo` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_dirty_worktrees.py -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T152.md`.

---

## Approach

**Pattern reference**: `skills/wake/scripts/dirty_worktrees.py` itself — `subprocess.run([...], capture_output=True, text=True, check=True)` and the outer `try/except` fail-open.

**Vital slice**: `None — the whole surface is the slice` (one path lookup).
**Cut list**: `None — nothing was cut`

In `main()`, replace the bare `BOARD` path with `os.path.join(<git rev-parse --show-toplevel>, BOARD)`,
using the same `subprocess.run` style as `worktrees()`. Outside a git repo the call raises, which the
existing outer `except` already turns into silent exit 0. Write the failing test first (red), then the fix.

---

## Edge Case Checklist

- [ ] Not a git repo → `rev-parse` fails → still empty output, exit 0
- [ ] Run inside a linked worktree → `--show-toplevel` is that worktree's root, so it reads that worktree's board copy. Accepted: `wake` runs from the main root; do not add logic for this
- [ ] Top-level path with spaces → use the stripped stdout as-is in `os.path.join`, no shell

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/wake/scripts/dirty_worktrees.py` | resolve board from git top-level |
| `tests/test_dirty_worktrees.py` | add the subfolder test (SC1) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/wake/SKILL.md` | behavior from root is unchanged; no doc change needed |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |

---

## Test Plan

TDD: add `test_subfolder_run_finds_board` (makes `repo/docs`, runs from there, expects the T901
line) — confirm it fails on the current code — then apply the fix and run the full file.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T152.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] Supervisor notified: task ready for Stage 4 review
