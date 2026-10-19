# BRAINSTORMING_LOG.md — Online Task Board (Linear first)
**Date**: 2026-10-19 · **Tier**: Deep · **Input**: `PRD_online-board.md` (FR-001..FR-012, decisions D1–D9)

---

## The Problem Space

Linear becomes the source of truth for tasks, guides, logs and decisions (D1, D4, D7). But the pipeline's gates are local Python hooks that read files: `PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_*.md` and `memory/decisions.md`. The problem is to get Linear's truth into those files at the four pull moments (D8), push local changes out at once (with an outbox when offline, D3), and leave a seam for GitHub/Jira later. All of this has to work without breaking projects that never opt in (D6).

Verified code facts (grep, 2026-10-19):
- Task-ID regexes `T\d+` appear at **11 sites in 6 files**: `post_write_register_task.py`, `pre_agent_validate_guide.py`, `pre_bash_block_unsafe_merge.py`, `dirty_worktrees.py`, `memory_slice.py`, `scripts/token_meter.py`.
- `pre_bash_block_unsafe_merge.py` blocks push/merge while **any** task is in the KANBAN "In Progress" section. In Linear mode the cache holds the **whole team's** In Progress tasks, so a teammate's work would block your push. The gate must filter to tasks assigned to me.
- `dirty_worktrees.py` matches branches by `t(\d{3,})`. Linear branch names (`eng-143-…`) won't match.
- No `STRATEGY.md`; no `docs/legacy/`.

---

## Questions for the User

1. Which path (below)? Asked in chat with a concrete example.

---

## Alternative Paths

### Option A — Cache projector (one sync script, hooks barely change)
A `lib/board/` adapter (board-adapter interface + `linear.py`, stdlib GraphQL) and one `board_sync.py` with `pull` / `push` / `flush-outbox`.
- `pull` renders Linear into the existing file formats: `PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_<ID>.md`, `memory/decisions.md`. Hooks read the same files as today.
- `push` is called by the Supervisor/agents to post status, milestone comments and decisions. On failure it appends to `.board/outbox.jsonl`.
- The 4 pull moments are wired into `wake`, `craft-spawn-prompt`/pre-spawn, `post_agent_move_to_review`, and the merge gate.
- **Pros**: hooks keep reading files, so offline works by construction. The board seam is one interface. The change surface is ID regexes plus the "mine" filter.
- **Cons**: rendering must reproduce file formats exactly, or hooks misparse them. The cache is stale between pull moments (accepted in D8).

### Option B — Board-native hooks (hooks ask Linear directly)
Each hook calls the adapter live (e.g. the merge gate queries "my In Progress issues"), and the cache is only an offline fallback.
- **Pros**: always fresh, and no rendering step.
- **Cons**: a network call inside every hook adds latency to every tool call it guards. Every one of the ~12 KANBAN consumers is rewritten, and each needs its own offline fallback. It contradicts D8 (four pull moments only).

### Option C — MCP-only Supervisor (no Python adapter)
The Supervisor uses the Linear MCP to read and write, and copies results into the local files by hand during `wake`, spawn and review.
- **Pros**: almost no code, and fastest to try.
- **Cons**: background sub-agents and hooks can't post (no MCP in hooks), which breaks FR-007 and the D2 "both" decision. Sync depends on the model remembering to do it, and LR-0002 shows pipeline steps get skipped. No outbox.

---

## 50% Rule Check

Linear's native **GitHub integration** already moves an issue to In Progress when a branch named `eng-143-…` is pushed or a PR opens, and to Done when the PR merges. With D5 (Linear IDs in branch names), Option A can **drop all status-push code** for those transitions and push only what GitHub can't express: Ready for Review, milestone comments and decisions. This roughly halves `push`. Cost: the user must enable the integration in Linear (one click per workspace). Risk: the Done move is automatic on merge, which bypasses Hard-Stop Gate 5 (Evidence before Done) unless the gate runs before merge. It already does: the merge gate blocks merge until evidence is in.

---

## Recommended Path

**Option A + the 50% cut.** One adapter + one sync script that renders Linear into today's file formats; status transitions on branch/PR left to Linear's GitHub integration. Vital slice first: `pull` (board + guides) → `push` (comments, decisions) → outbox → assigned-to-me triage in `wake`. Cut list: GitHub/Jira board adapters (interface only), two-way merge, mid-task pulls, migration of old tasks.

### Board portability rule (added after user asked "is changing to Jira/GitHub later easy?")
Only `lib/board/<board>.py` knows which board is used. `board_sync.py` and every hook depend on a fixed 7-operation interface: `list_tasks`, `get_task`, `create_task`, `update_task`, `set_status`, `add_comment`, `read/append_decisions`. Two things are config, never code, from day one:
1. **Task-ID pattern** (`ENG-143` / `#143` / `PROJ-143`): the 11 regex sites read it from config.
2. **`git_auto_status` capability flag**: if a board can't move status from branch/PR events, `board_sync` posts the status itself.
Known per-board quirks, each contained in its own file: Jira needs status transitions mapped and its guide text converted to ADF; GitHub status is a custom project field; the decisions home varies (Linear Document / pinned issue / Confluence).

---

## Surgical Scope

**Should touch**: new `lib/board/` (interface, `linear.py`, `outbox.py`), new `scripts/board_sync.py`; ID regexes at the 11 sites; "mine" filter in `pre_bash_block_unsafe_merge.py`; `dirty_worktrees.py` branch match; `skills/wake` (pull + triage section); `skills/craft-spawn-prompt` (pre-spawn pull); `post_agent_move_to_review.py` (pull + changed-guide flag); `setup.sh` init questions (FR-003); `.gitignore` for `.board/`.
**Must not touch**: the local-only path (opt-out projects behave byte-identically); `memory/MEMORY.md` hot-tier rules; TASK_GUIDE template sections (the rendered description must contain the same sections).

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Teammate's In Progress task must not block my push (merge gate filters by assignee).
- [ ] Outbox replay is idempotent: a comment that was half-posted before a timeout is not posted twice (dedupe key per entry).
- [ ] Rendered `PROJECT_KANBAN.md` round-trips through every existing KANBAN parser test.
- [ ] API key never reaches a committed file, a log line, or the outbox.
- [ ] Linear text is untrusted data: no rendered field can inject markdown that a hook parses as a section header or task row.
- [ ] Rate-limit headers (`X-RateLimit-Requests-Remaining`) are respected; on 429, writes go to the outbox.
- [ ] Mixed IDs: an old `T142` and a new `ENG-170` coexist on one rendered board.
- [ ] Guide changed while agent worked → pre-review pull flags it (FR-009), never silently overwrites the agent's Evidence rows.
- [ ] Opt-out project: zero network calls, zero new files.

---

## Next Actions

1. User picks a path (chat).
2. Re-confirm FR-012 mapping + NFR-003 (stdlib-only) at Stage 2.
3. Stage 2: `to-issues` → vertical slices; ID-regex change is structural, so C2/Medium floor.
4. Decide whether this supersedes deferred T142.

---

## User Selection

**2026-10-19 — Option A (cache projector) + GitHub-integration shortcut**, with the board portability rule (ID pattern + `git_auto_status` in config). Selected by the user in chat.
