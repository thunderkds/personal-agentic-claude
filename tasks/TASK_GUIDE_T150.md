# TASK_GUIDE — T150: Spawns run as background agents, and `wake` flags work a dead agent left behind
**Date**: 2026-10-17
**Complexity Level**: C1
**Risk Level**: Low
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
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

The user, 2026-10-17, after T144/T145/T148/T149 were spawned as background `Agent()` calls with no
stated reason and T148 was left half-done when the session ended (`BRAINSTORMING_LOG_spawn-mode.md`):
asked "what is good for the subagent, new sandbox pane, cli or background jobs", then chose
background agents — they do not need to watch sub-agents work; the final report and commits are
enough — and said "yes, create this task guide" for the two-part change:
(1) write the spawn-mode rule into Stage 3; (2) make `wake` flag uncommitted work left in an
In Progress task's worktree.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> The spawn mode stops being an accident: Stage 3 says every spawn is a background `Agent()` call
> unless the user asks to watch or the task runs on a non-Claude CLI. Because a background agent
> dies with the Supervisor session, `wake` reports any In Progress task whose worktree has
> uncommitted changes, so half-finished work like T148's is seen at the next session start.

**Out of scope** (what this task explicitly does NOT do):
- Changing the CLI-pane launcher, its markers, or the T147 sandbox profile (`templates/subagent-sandbox.settings.json`, `scripts/gen_sandbox_profile.py`)
- Relaunching or finishing T148 — the Supervisor does that separately
- Auto-committing, stashing or cleaning any worktree — `wake` stays read-only
- Reporting worktrees of tasks that are not In Progress (the ~50 old `wt-t0xx`/`wt-t1xx` trees)

**Requirement Refs**: none in `PRD.md` — harness process change from the user's 2026-10-17 decision (`BRAINSTORMING_LOG_spawn-mode.md`, Recommended Path).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, from the user's 2026-10-17 "they('re enough)" / "yes let me see" / "yes, create this task guide")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (Stage 3, worktree, spawn, In Progress)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No PRD refs — N/A

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `dirty_worktrees.py` (called from `skills/wake/SKILL.md` Step 1)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `docs/claude-md/pipeline-stages.md` Stage 3 has a **Spawn mode** bullet: background `Agent()` by default; a CLI pane only when the user asks to watch or the task runs on a non-Claude CLI; the T147 sandboxed profile not used until a nested-userns check passes | Part (1) |
| 2 | `skills/craft-spawn-prompt/SKILL.md` output names the spawn mode, consistent with AC1 | Part (1) — the skill is what the Supervisor follows at spawn time |
| 3 | `skills/wake/scripts/dirty_worktrees.py` prints one line per In Progress task whose worktree has uncommitted changes: task ID, worktree path, modified count, untracked count | Part (2) |
| 4 | It prints nothing (exit 0) when every In Progress worktree is clean, and ignores worktrees of tasks not In Progress | Part (2), Out of scope |
| 5 | It never fails `wake`: no git, no board, or a missing worktree → no output, exit 0 | `wake` "never halt" rule |
| 6 | `skills/wake/SKILL.md` runs the script as a fifth source and shows its lines under In-Flight Work, inside the 50-line cap | Part (2) |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Temp repo: board with T901 In Progress, worktree on branch `feat/t901-x` with 1 modified + 2 untracked files | one line naming `T901`, the worktree path, `1 modified`, `2 untracked` | automated test |
| 2 | Same, worktree clean | no output, exit 0 | automated test |
| 3 | Dirty worktree for T902 which is in **Done** | no line for T902 | automated test |
| 4 | Worktree branch names two tasks (`feat/t903-t904-x`), both In Progress | one line per task ID, or one line naming both — either, documented | automated test |
| 5 | No `PROJECT_KANBAN.md`; not a git repo | no output, exit 0 | automated test |
| 6 | Stage 3 rule + craft-spawn-prompt line + wake source row present | literal strings present | automated docs test (pattern: `tests/test_spawn_startup_reads.py`) |
| 7 | Run on this repo today | flags `T148` / `wt-t148` (uncommitted `post_tool_trace.py`, untracked `trace_chain.py`, `verify_trace.py`) — unless T148 was finished first | manual, Supervisor at Stage 5 |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_dirty_worktrees.py -q && python3 skills/wake/scripts/dirty_worktrees.py
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T150.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T150.md`.

---

## Approach

**Pattern reference**: `skills/craft-spawn-prompt/scripts/memory_slice.py` + `tests/test_memory_slice.py` — a stdlib-only script beside its skill, called by the skill's prose, tested with pytest; `tests/test_spawn_startup_reads.py` for the docs-string tests.

**Vital slice**: the script + its tests; the two doc edits are a few lines each.
**Cut list**:
- Matching worktrees by the board's `Branch:` field — match the task ID in the worktree's branch name instead (`t(\d{3})`, case-insensitive), which every repo branch already carries
- Showing *which* files are dirty — counts only; the Supervisor runs `git status` itself

Find In Progress task IDs from the `### In Progress` section of `PROJECT_KANBAN.md` (**bold** `**Txxx**` at the start of each row only — a bold cross-reference inside a row is not that row's ID; see T093). Get worktrees from `git worktree list --porcelain`, skipping the main worktree. Count with `git -C <path> status --porcelain`: `??` = untracked, anything else = modified.

---

## Edge Case Checklist

- [ ] A row's text mentions another task in bold (`**T093**`) — only the row's leading ID counts (T093 lesson)
- [ ] Worktree path in `git worktree list` no longer exists on disk (`prunable`) — skip, don't crash
- [ ] Detached-HEAD worktree (no branch) — skip
- [ ] One worktree carries two tasks (`feat/t146-t147-…`)
- [ ] The main worktree is itself on a task branch (`feat/t144-t145-t148-t149`) — never report the main worktree
- [ ] Script must be stdlib-only and Python 3 — it ships to downstream projects via `MANIFEST` (`skills`)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `docs/claude-md/pipeline-stages.md` | Stage 3: add the **Spawn mode** bullet after the `craft-spawn-prompt` bullet |
| `skills/craft-spawn-prompt/SKILL.md` | output list: name the spawn mode per the Stage 3 rule |
| `skills/wake/SKILL.md` | Step 1 table: fifth source row; Section 2: where its lines go; edge-case row |
| `skills/wake/scripts/dirty_worktrees.py` | new — the check |
| `tests/test_dirty_worktrees.py` | new — SC1–SC6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `templates/subagent-sandbox.settings.json`, `scripts/gen_sandbox_profile.py` | T147 scope |
| `PROJECT_KANBAN.md`, `memory/**` | Supervisor-only |
| `.claude/settings.json`, `.claude/hooks/**` | not needed; hooks are out of scope |
| `CLAUDE.md` | the rule lives in `pipeline-stages.md`; `CLAUDE.md` only points there |

---

## Test Plan

`tests/test_dirty_worktrees.py` builds a throwaway git repo in `tmp_path` with a fake `PROJECT_KANBAN.md` and real `git worktree add` worktrees, runs the script via `subprocess` with `cwd` set to it, and asserts on stdout/exit code (SC1–SC5). Docs tests read the three markdown files and assert the rule strings (SC6). Run the full suite after: `python3 -m pytest tests/ .claude/hooks/tests/ -q`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T150.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — script run on this repo
- [ ] Supervisor notified: task ready for Stage 4 review
