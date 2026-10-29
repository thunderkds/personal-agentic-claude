# TASK_GUIDE — T196: Trace attribution per session and per sub-agent, not one file per checkout
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: changes which task every tool call is attributed to, and so what `trace_shows_verification` (the merge gate's one deterministic check) accepts. Touches the merge gate file for one message only (D6).

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `.claude/hooks/lib/task_context.py` in full (its docstring is the design history: T043, T047) and `.claude/hooks/tests/merge_gate_guard.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

Board row T196 (registered 2026-10-28, measured): `.claude/hooks/.state/active_task` is one file per checkout. At 05:34:10Z the T190 agent wrote it; at 05:40:25Z another live session overwrote it with `T188`. `memory/event-trace/T188.jsonl` then held 280 records, 89 of them T190's work in `wt-t190-gate`; `T190.jsonl` held 3 of T188's. So `pre_bash_block_unsafe_merge.py:trace_shows_verification(tid)` can be satisfied by another task's verification run without anyone lying. It happened again on 2026-10-29: the T202 agent deleted the shared file at the end of its run while the T200/T201 session was live. The row says: "Do NOT fix by telling agents to coordinate — the whole point of the channel is that it is structural."

**Facts measured by the Supervisor on 2026-10-29 (Claude Code 2.1.312, headless probe with a `PostToolUse` hook that dumped its stdin):**
- F1 — Every hook payload carries `session_id` and `transcript_path`. A tool call made **by a sub-agent** also carries `agent_id` (e.g. `a54df34ef9d22bed6`) and `agent_type`; a main-session call has neither. A sub-agent shares its parent's `session_id`.
- F2 — Inside a `Bash` tool call, `$CLAUDE_CODE_SESSION_ID` equals the hook's `session_id`, in the main session and in a sub-agent alike. No agent-ID variable exists in a sub-agent's environment.
- F3 — A sub-agent's transcript is `<dirname(transcript_path)>/<session_id>/subagents/agent-<agent_id>.jsonl`; its first line is `{"type": "user", "message": {"role": "user", "content": "<the spawn prompt, verbatim>"}, ...}`. A sibling `agent-<agent_id>.meta.json` holds `agentType`, `toolUseId`. This layout is internal to Claude Code and undocumented.
- F4 — A `Bash` call that exits non-zero did not reach the `PostToolUse` hook in the probe (only the successful call was captured). Do not depend on failed calls being traced.

**Restated intent**:
> Make attribution answer "which task is this tool call for?" per caller, not per checkout. A sub-agent's
> calls belong to the task its spawn prompt structurally names (`TASK_GUIDE_Txxx.md` or `Task ID:`), read
> by the hook from that sub-agent's own transcript — the agent writes nothing. A main-session (Supervisor)
> call belongs to the task in a state file keyed by its own session ID. The shared per-checkout file stops
> being read, so one session or agent can no longer attribute another's calls, and deleting or
> overwriting a file can no longer move another caller's evidence.

**Supervisor design decisions** (stated, not asked; the user confirms them with the restated intent before spawn):
- D1 — **New precedence** in `resolve_task_id` (first match wins):
  1. `CLAUDE_ACTIVE_TASK` env var — unchanged.
  2. **Spawn binding** (new): the event has `agent_id` → read the first line of the F3 transcript, take the spawn prompt, extract a Task ID with the existing structural patterns (`_guide_path_pattern`, `_task_id_declaration_pattern`), first match. Cache the result in `.claude/hooks/.state/agent_task/<session_id>/<agent_id>` (hook-written) so later calls do not re-read the transcript.
  3. **Per-session state file** (replaces the shared file): `.claude/hooks/.state/active_task.d/<session_id>`, same two-line format and the same `CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S` age rule. `<session_id>` comes from the event, never from the file.
  4. Path fields — unchanged. 5. `Agent` prompt — unchanged. 6. `None`.
- D2 — **The shared `.claude/hooks/.state/active_task` is no longer read.** Reading it is the forgeable path. A file left there is ignored.
- D3 — **Path safety:** `session_id` and `agent_id` are used in a file name only when they match `\A[A-Za-z0-9_-]{1,128}\Z`; otherwise that slot is skipped. The transcript path is derived only from the event's `transcript_path`, never from free text, and is read only, never written.
- D4 — **Degrade, never guess:** a missing/unreadable transcript, a first line that is not a user message, or a spawn prompt with no structural ID → slot 2 yields nothing and resolution falls through to slot 3 (keyed by the same session) — documented residual: two sub-agents of one session spawned *without* a structural ID still share slot 3. `resolve_task_id` keeps its never-raises contract.
- D5 — **Writer instructions** change to the per-session path: `printf '%s\n%s\n' "Txxx" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > <main-checkout>/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID` (after `mkdir -p`). Sub-agents need no write at all when their spawn prompt carries the Task ID: `craft-spawn-prompt` element 6 becomes "the spawn binding attributes you; write the per-session file only if told your prompt carries no Task ID". Update every live instruction: `skills/craft-spawn-prompt/SKILL.md` element 6, `skills/resolve-question/SKILL.md:58`, `docs/claude-md/tracks.md:75`, the module docstring of `task_context.py`.
- D6 — **Merge gate message only:** `pre_bash_block_unsafe_merge.py`'s `ATTRIBUTION_REMEDY` text names the shared file and becomes wrong advice. Change that string (and nothing else in the gate) to the D5 path. This needs `T196` in `.claude/hooks/tests/merge_gate_guard.py:AUTHORISED_TASKS` with the rule it owns ("T196 — the attribution remedy text names the per-session state file; no gate logic change"), and the user's sign-off before spawn. Every commit that touches the gate names T196 in its subject.

**Out of scope**: changing `trace_shows_verification` or any other gate logic; per-agent state files written by agents (F2: they cannot know their `agent_id`); scanning `Bash` command text (still never scanned); migrating or rewriting existing `memory/event-trace/*.jsonl`; failed-call tracing (F4).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent + D1–D6 confirmed by the user (including adding T196 to `AUTHORISED_TASKS`)
- [x] Terms: **spawn binding**, **per-session state file** (new, defined in D1); trace, attribution as in `task_context.py`
- [x] Every AC traces to the Requirement
- [x] Refs covered

---

## Dependencies & Reachability

**Depends on**: None.

**Entry point**: `.claude/hooks/lib/task_context.py:resolve_task_id` — called by `post_tool_trace.py` (which trace file a record lands in), `pre_agent_step_limit.py`, `pre_tool_sensitive_path.py`, `post_agent_move_to_review.py`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | An event with `agent_id` whose F3 transcript's first line is a spawn prompt containing `Task ID: T190` (or `tasks/TASK_GUIDE_T190.md`) resolves to `T190`, even when the per-session file for the same `session_id` says `T188`. | D1.2 |
| 2 | The spawn binding is cached at `.state/agent_task/<session_id>/<agent_id>` on first resolution; a second event reads the cache, not the transcript (test: delete the transcript after the first call, the second still resolves). | D1.2 |
| 3 | Two `session_id`s with per-session files `T188` and `T190` each resolve to their own task; neither file's content, deletion or overwrite changes the other session's result. | D1.3, D2 |
| 4 | A file at the old shared path `.state/active_task` is ignored (event with no other signal → `None`). | D2 |
| 5 | `session_id`/`agent_id` values that fail `\A[A-Za-z0-9_-]{1,128}\Z` (e.g. `../x`, empty, 200 chars) never reach a path; resolution skips that slot and never raises. | D3 |
| 6 | Missing transcript, empty file, first line not a user message, non-JSON first line, and a spawn prompt with no structural ID each fall through to the per-session file; none raises. A spawn prompt that only *mentions* `T188` in prose (no guide path, no `Task ID:` line) does not bind. | D4 |
| 7 | **Incident replay:** fixture of the 2026-10-28 shape — session A's sub-agent (spawn prompt `Task ID: T190`) and session B's main session (per-session file `T188`) interleave `Bash` calls through `post_tool_trace.py` → every A call lands in `T190.jsonl`, every B call in `T188.jsonl`, 0 crossings; and `trace_shows_verification("T188")` is not satisfied by A's calls. | Requirement |
| 8 | Every live instruction names the per-session path (D5): `grep -rn "hooks/.state/active_task\b" skills docs/claude-md agents templates AGENTS.md .claude/hooks --include=*.md --include=*.py` finds no instruction to write the shared file (historical task guides/reviews are not edited). | D5 |
| 9 | Gate diff is `ATTRIBUTION_REMEDY`'s text only; `merge_gate_guard.AUTHORISED_TASKS` gains `T196` with its rule comment; `test_merge_gate_guard.py`'s expected tuple is updated in the same commit; the gate-untouched suites pass. | D6 |
| 10 | **Live check** (real Claude Code, not a stub): from a headless session in a throwaway copy, spawn one sub-agent with `Task ID: T9xx` that runs one `echo`; the main session writes its per-session file with a different ID and runs one `echo` → the kit's real `post_tool_trace.py` puts each record in its own task's trace. Paste the two trace lines. | all |
| 11 | `python3 -m pytest -q .claude/hooks/tests/ tests/` → 0 failed. | — |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | AC 1–6 fixtures | as stated | `test_task_context.py` |
| 2 | incident replay | 0 crossings; T188 verification not satisfied by T190 calls | new test through `post_tool_trace.py` + gate function |
| 3 | live headless run | sub-agent record in its task's trace, main record in the other | Supervisor-reviewed capture |
| 4 | old shared file present | ignored | test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q .claude/hooks/tests/test_task_context.py .claude/hooks/tests/test_post_tool_trace_spawn.py .claude/hooks/tests/test_merge_gate_guard.py && python3 -m pytest -q .claude/hooks/tests/ tests/ 2>&1 | tail -1 && git diff main -- .claude/hooks/pre_bash_block_unsafe_merge.py | grep -E '^[-+][^-+]' | grep -v ATTRIBUTION_REMEDY -c
```

The last number counts changed gate lines outside the remedy string (expect only the string's own continuation lines; the reviewer reads them).

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T196.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T196.md`. BEFORE = the incident replay (AC 7) run against the unchanged `task_context.py`, showing the crossings.

---

## Approach

**Pattern reference**: `.claude/hooks/lib/task_context.py` — extend it in place; keep its never-raises contract, its explicit lists and its docstring style (record why, cite the task). Structural ID extraction already exists: reuse `_guide_path_pattern` / `_task_id_declaration_pattern`, do not write a third pattern.
**Vital slice**: D1.2 spawn binding + D1.3 per-session file + D2 (AC 1, 3, 4, 7).
**Cut list**: per-agent files written by agents (impossible, F2); a cleanup job for old per-session files (age rule already degrades them); attributing failed calls (F4).

---

## Edge Case Checklist

- [ ] `transcript_path` absent or relative in the event → slot 2 skipped.
- [ ] Transcript first line can be large (a long spawn prompt): read only the first line, cap the read (e.g. 1 MB).
- [ ] Cache directory write fails (read-only FS) → still resolve from the transcript this call; never raise.
- [ ] A nested sub-agent (spawned by a sub-agent): same F3 layout under the same `session_id`? Check in the live run; if not, it falls through (D4) — record what you saw.
- [ ] Hooks run with `$CLAUDE_PROJECT_DIR` = main checkout; `_resolve_root()` is unchanged.
- [ ] `pre_agent_step_limit.py` counts per task: a sub-agent now always counts against its spawn task — check its tests.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/task_context.py` | D1–D4, docstring |
| `.claude/hooks/tests/test_task_context.py` | AC 1–6 |
| `.claude/hooks/tests/test_post_tool_trace_spawn.py` (or a new test file) | AC 7 |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | `ATTRIBUTION_REMEDY` text only (D6) |
| `.claude/hooks/tests/merge_gate_guard.py`, `test_merge_gate_guard.py` | add `T196` (D6) |
| `skills/craft-spawn-prompt/SKILL.md`, `skills/resolve-question/SKILL.md`, `docs/claude-md/tracks.md` | D5 instruction text |
| any test that asserts the old instruction text (`tests/test_tracks.py`, `tests/test_resolve_question.py`, …) | follow the text |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| any gate logic in `pre_bash_block_unsafe_merge.py` | D6: message only |
| `memory/event-trace/*.jsonl` | evidence history |
| historical `tasks/TASK_GUIDE_T0xx–T1xx.md`, `TASK_REVIEW_*.md` | records of their time |
| `AGENTS.md`, role guides | line/size budgets (T202); not needed |

---

## Test Plan

Unit tests for every precedence slot and degrade path (AC 1–6), one incident-replay test through the real trace hook and gate function (AC 7), the guard tests (AC 9), one live headless run (AC 10).

---

## Completion Checklist

- [ ] User confirmed restated intent + D1–D6 (Supervisor)
- [ ] BEFORE captured before the first implementation commit (agent)
- [ ] Implementation + tests (agent)
- [ ] Live check AC 10 (agent; ≤ $0.50, cap the run with `--max-budget-usd`)
- [ ] Stage 4 `code-review` + `security-review` (Supervisor)
- [ ] `verify` (user)

---

## Questions Log
