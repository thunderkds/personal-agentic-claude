# TASK_GUIDE — T153: Task IDs come from board config, so hooks accept `T142` and `ENG-170` side by side
**Date**: 2026-10-19
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk raised Medium → High: touches hub gate files (merge gate, spawn validator) — a regex slip silently disables a gate.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` (glossary: board, board adapter, board mode, board cache, outbox, pull moment, Decision Log, my task)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely, then `PRD_online-board.md` and `BRAINSTORMING_LOG_online-board.md`
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Source: the user, 2026-10-19 — "use the online board to manage the task, decision related task, tasks log, maybe the agents can post the logs, the status to the tasks ..., not from the local. Start with the linear.app first, but keep the open wide with another application like GitHub board, Jira". Requirements locked in `PRD_online-board.md` (Stage 0.5 grilling, decisions D1–D9); path locked in `BRAINSTORMING_LOG_online-board.md` (Option A — cache projector + Linear's GitHub-integration shortcut + board portability rule). Terms (board, board adapter, board mode, board cache, outbox, pull moment, Decision Log, my task) are defined in the `PROJECT_SPEC.md` glossary — use them exactly. "Provider" means the agent runtime (DDR-0006), never the board.

This task: Every hook and script that recognises a task ID hard-codes `T\d+`. In board mode `online` new tasks use the board's IDs (Linear `ENG-170`; later GitHub `#170`, Jira `PROJ-170`) — FR-006, board portability rule.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> The task-ID pattern is read from `.claude/board.json` (`id_pattern`); with no config file every site behaves exactly as today. A board holding both `T142` and `ENG-170` is parsed correctly by every gate.

**Out of scope** (what this task explicitly does NOT do):
- Any network call, adapter or sync code (T154)
- Writing `.claude/board.json` (T155 — tests write fixtures)
- The "my task" merge filter (T157)
- Renaming existing `Txxx` tasks

**Requirement Refs** (from `PRD_online-board.md`):
- FR-001: opt-in, local mode unchanged
- FR-006: Linear IDs; hooks accept both patterns

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-19; breakdown approved by the user)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` terminology pass run 2026-10-19)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD_online-board.md` and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `task_id_pattern`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|---|---|
| 1 | With no `.claude/board.json`, every existing test in `.claude/hooks/tests/` and `tests/` passes unchanged | FR-001 local mode unchanged |
| 2 | With `{"id_pattern": "ENG-\\d+"}`, a board with `T142` and `ENG-170` In Progress: the merge gate lists both; `TASK_GUIDE_ENG-170.md` is registered on Write; the spawn validator, `task_context.resolve_task_id`, `memory_slice.py` and `token_meter.py` resolve `ENG-170` | FR-006 both patterns |
| 3 | `dirty_worktrees.py` maps branch `eng-170-dark-mode` (lower-case, as Linear names branches) to `ENG-170`, and `feat/t142-x` to `T142` | FR-006 branches |
| 4 | Malformed JSON or an invalid regex in `id_pattern` → one stderr warning and fallback to `T\d+`; no gate becomes more permissive than today | safety of gates |
| 5 | `normalize_task_id` still zero-pads `T` IDs (`T7`→`T007`) and upper-cases board IDs (`eng-170`→`ENG-170`) | ID canonical form |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---|---|---|
| 1 | no config, current repo | full suites green | `pytest .claude/hooks/tests tests -q` |
| 2 | config `ENG-\d+`, fixture board with T142 + ENG-170 In Progress | merge gate blocks naming both | new `tests/test_board_id_pattern.py` |
| 3 | config `id_pattern: "("` | warning + `T\d+` behavior | new test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T153.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T153.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/lib/task_context.py` — compiled module-level patterns, never-raises contract; `post_agent_move_to_review.py:51` — `sys.path.insert(0, .../lib)` import style

**Vital slice**: One `task_id_pattern()` helper in `.claude/hooks/lib/board/config.py`, used by every site.
**Cut list**:
- Per-board ID validation beyond a regex
- Config caching across hook processes

Grep every `T\\d`, `T(\\d`, `t(\\d` and `"T" +` site (≈20 sites in 9 files today: `post_write_register_task.py`, `pre_agent_validate_guide.py`, `pre_bash_block_unsafe_merge.py`, `lib/task_context.py`, `skills/wake/scripts/dirty_worktrees.py`, `skills/craft-spawn-prompt/scripts/memory_slice.py`, `scripts/token_meter.py`, plus the docstring in `post_agent_move_to_review.py`). Add `.claude/hooks/lib/board/__init__.py` + `config.py` exposing `load_config()` (missing file → `None`) and `task_id_pattern()` (returns the alternation of `T\d+` and the configured pattern — old `Txxx` tasks keep working in online mode, FR-006). Replace each hard-coded pattern with the helper, keeping each site's anchors/boundaries. Write the mixed-board fixture test first (red).

---

## Edge Case Checklist

- [ ] Branch names are lower-case (`eng-170-…`): match case-insensitively, emit upper-case
- [ ] Guide file names: `TASK_GUIDE_ENG-170.md` contains a hyphen — check every filename regex
- [ ] `\bT\d+\b` boundaries must not match inside `ENG-170` or `ST100`
- [ ] A `#170` (GitHub) pattern contains `#` — keep it out of markdown-header parsing; test one `#\d+` config too
- [ ] Board mode `local` (no `.claude/board.json`): zero network calls, zero new files, byte-identical behavior

---

## Files to Change (Predicted)

| File | Change |
|---|---|
| `.claude/hooks/lib/board/config.py` (new) | config loader + `task_id_pattern()` |
| the ≈9 files above | use the helper |
| `tests/test_board_id_pattern.py` (new) | mixed-board tests |

## Files Must NOT Touch

| File | Reason |
|---|---|
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |
| `PRD_online-board.md`, `BRAINSTORMING_LOG_online-board.md` | locked planning inputs |
| `setup.sh`, `lib/*.sh` | init is T155 |

---

## Test Plan

TDD, one vertical slice at a time (`Skill({ skill: "tdd" })`): write the Success Criteria tests first and confirm they fail (red), implement, then run the Verification Command. Tests use the fake board fixture — no network in the suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium/High risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T153.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] Supervisor notified: task ready for Stage 4 review
