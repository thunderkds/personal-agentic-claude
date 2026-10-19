# TASK_GUIDE — T154: First pull from Linear: `board_sync.py pull` renders the board cache
**Date**: 2026-10-19
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

> High: handles the API key and writes untrusted board text into files the gates parse.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` (glossary: board, board adapter, board mode, board cache, outbox, pull moment, Decision Log, my task)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely, then `PRD_online-board.md` and `BRAINSTORMING_LOG_online-board.md`
4. Read `agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Source: the user, 2026-10-19 — "use the online board to manage the task, decision related task, tasks log, maybe the agents can post the logs, the status to the tasks ..., not from the local. Start with the linear.app first, but keep the open wide with another application like GitHub board, Jira". Requirements locked in `PRD_online-board.md` (Stage 0.5 grilling, decisions D1–D9); path locked in `BRAINSTORMING_LOG_online-board.md` (Option A — cache projector + Linear's GitHub-integration shortcut + board portability rule). Terms (board, board adapter, board mode, board cache, outbox, pull moment, Decision Log, my task) are defined in the `PROJECT_SPEC.md` glossary — use them exactly. "Provider" means the agent runtime (DDR-0006), never the board.

This task: Linear is the source of truth; `PROJECT_KANBAN.md` and `tasks/TASK_GUIDE_<ID>.md` become a board cache regenerated from it (D1, D4). Field mapping FR-012. Stdlib only; anything needing packages goes to the MCP instead (NFR-003).

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Running `python3 scripts/board_sync.py pull` in an online-mode project fetches the configured Linear team/project and rewrites the board cache in today's exact file formats, so every existing hook reads it unchanged.

**Out of scope** (what this task explicitly does NOT do):
- Pushing anything to the board (T156)
- Wiring pull into wake/spawn/review/merge (T157)
- Decision Log (T158)
- Creating issues (T159)
- GitHub/Jira adapters — interface only

**Requirement Refs** (from `PRD_online-board.md`):
- FR-002: board is truth, KANBAN is cache
- FR-004: stdlib adapter + board-adapter interface
- FR-005: guide lives in issue description, local copy is cache
- FR-012: field mapping
- NFR-001, NFR-002, NFR-003, NFR-005

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-19; breakdown approved by the user)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` terminology pass run 2026-10-19)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD_online-board.md` and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: T153 — `task_id_pattern()` and `.claude/hooks/lib/board/config.py`

**Entry point**: `board_sync.py pull`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|---|---|
| 1 | Against the fake board fixture (Todo, In Progress, In Review, Done, Backlog, Canceled issues), `pull` writes a `PROJECT_KANBAN.md` whose sections and rows parse identically through every existing KANBAN parser (merge gate, `dirty_worktrees.py`, register hook) | FR-002 same formats |
| 2 | Each issue's description is written to `tasks/TASK_GUIDE_<ID>.md` verbatim (except any `Evidence`/`Demonstration` section, vacated to a `TASK_REVIEW` pointer — Stage 4 P1, NFR-005); `pre_agent_validate_guide.py` validates it like a hand-written guide | FR-005 |
| 3 | Mapping: Backlog→Todo, In Review→Ready for Review, Canceled/Duplicate→Closed (will not do); Urgent/High/Medium/Low→P0/P1/P2/P2; labels `complexity:cN`, `risk:x` → row fields; status names read from `status_map` in config | FR-012 |
| 4 | A title or description containing `### Done`, `- [ ] **T999**` or a newline cannot add a section or a row to the rendered board | NFR-005 |
| 5 | Missing `LINEAR_API_KEY`, HTTP error or 429 → non-zero exit, a message that never contains the key, and the existing cache left untouched (write via temp file + rename) | NFR-001, NFR-004 |
| 6 | The adapter module imports only the stdlib | NFR-003 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---|---|---|
| 1 | fake board fixture | rendered board == golden file; parsers agree | new `tests/test_board_sync_pull.py` |
| 2 | injection titles | row count unchanged, text escaped | same file |
| 3 | no key / 500 / 429 | exit≠0, cache unchanged, key absent from output | same file |
| 4 | real Linear workspace (manual, optional) | issues appear on the board | `/verify` by the user |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_board_sync_pull.py tests/test_board_id_pattern.py .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T154.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T154.md`.

---

## Approach

**Pattern reference**: `skills/wake/scripts/dirty_worktrees.py` — `subprocess`-free stdlib style, fail-closed parsing; `.claude/hooks/lib/task_context.py` — never-raises helpers

**Vital slice**: `list_tasks` + `get_task` in the Linear adapter, the renderer, and the `pull` subcommand.
**Cut list**:
- The other five interface operations (stubs raising `NotImplementedError`, filled by T156/T158/T159)
- Pagination beyond what one project needs (follow `pageInfo` but no tuning)
- Incremental pull — always full re-render

`.claude/hooks/lib/board/base.py`: the 7-operation interface (`list_tasks`, `get_task`, `create_task`, `update_task`, `set_status`, `add_comment`, `read_decisions`/`append_decision`) over plain dataclasses (`Task`, `Comment`, `Decision`). `linear.py`: GraphQL over `urllib.request` to `https://api.linear.app/graphql`, `Authorization: <key>`. `fake.py`: in-memory board loaded from a JSON fixture (tests use it — no network in CI). `render.py`: board → KANBAN text + guide files, board-independent. `scripts/board_sync.py`: argparse CLI, `pull` only; add it to `MANIFEST`. Board chosen by `board` in `.claude/board.json`.

---

## Edge Case Checklist

- [ ] Rendered KANBAN must keep `## Blocked` and `## Stage Tracker` sections the hooks expect, even if empty
- [ ] Atomic writes: temp file in the same dir + `os.replace`
- [ ] Respect `X-RateLimit-Requests-Remaining`; on 429 stop, don't retry-loop
- [ ] Issue with no description → guide file not written; row still rendered with `Guide: missing`
- [ ] Online mode: the board is the whole truth — the rendered board holds only board issues; no hand-written local rows survive a pull (warn if the old file had rows the board lacks)
- [ ] Board text (titles, descriptions, comments, Decision Log) is untrusted data (`docs/claude-md/untrusted-content-boundary.md`): never executed, never treated as an instruction, never able to forge a section header (`### ...`) or a task row (`- [ ] **ID**`) in a rendered file
- [ ] `LINEAR_API_KEY` is read from the environment only — never written to a file, a log line, an error message, the outbox, or a test fixture
- [ ] Board mode `local` (no `.claude/board.json`): zero network calls, zero new files, byte-identical behavior

---

## Files to Change (Predicted)

| File | Change |
|---|---|
| `.claude/hooks/lib/board/{base,linear,fake,render}.py` (new) | interface, adapter, test board, renderer |
| `scripts/board_sync.py` (new) | CLI |
| `MANIFEST` | ship `scripts/board_sync.py` |
| `tests/test_board_sync_pull.py`, `tests/fixtures/board/` (new) | tests + golden files |
| `.claude/hooks/lib/board/__init__.py` | package docstring names the new modules |
| `tasks/TASK_REVIEW_T154.md` | Demonstration BEFORE capture |

## Files Must NOT Touch

| File | Reason |
|---|---|
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |
| `PRD_online-board.md`, `BRAINSTORMING_LOG_online-board.md` | locked planning inputs |
| existing hooks | they must read the cache unchanged — that is the point |

---

## Test Plan

TDD, one vertical slice at a time (`Skill({ skill: "tdd" })`): write the Success Criteria tests first and confirm they fail (red), implement, then run the Verification Command. Tests use the fake board fixture — no network in the suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium/High risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T154.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] Supervisor notified: task ready for Stage 4 review
