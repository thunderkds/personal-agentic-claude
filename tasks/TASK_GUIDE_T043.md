# TASK_GUIDE — T043: Fix trace/step-limit task attribution — stop inferring the Task ID from arbitrary tool text
**Date**: 2026-07-23
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (pasted into your spawn prompt — do not re-read if present)
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above (C2) and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. C2 task: read `memory/codebase-map.md` for structural orientation
7. Read in full: `.claude/hooks/post_tool_trace.py`, `.claude/hooks/pre_agent_step_limit.py`,
   `.claude/hooks/pre_agent_validate_guide.py` (this one already contains the *correct* pattern —
   `extract_structural_task_ids`, landed by an earlier hardening task)

---

## Requirement (Pillar 1 — Adapt the requirement)

Two always-on hooks decide "which task is this tool call about?" by taking the **first `T\d{3}`
substring found anywhere in the tool payload**:

- `post_tool_trace.py:find_task_id` searches `tool_input` **and `tool_response`** combined.
- `pre_agent_step_limit.py:find_task_id` searches `tool_input`.

Both are wrong in the same way, and both failures are already documented as real, recurring
incidents rather than theoretical risks:

| Hook | Observed failure |
|---|---|
| `post_tool_trace.py` | Verified 2026-07-21: a session's records were filed under T001, T012, T017, T028, T029, T030, T038 — all Done or untouched. *Reading* `PROJECT_KANBAN.md` or `memory/MEMORY.md` files the record under whichever Task ID appears earliest **in that file's text**, because the file body arrives in `tool_response`. |
| `pre_agent_step_limit.py` | `memory/learnings.md`: "blocks even Edit calls whose *text* mentions an old task ID; 25+ stale counter files never reset; fix is overdue, no longer occasional." The documented workaround is to bracket-glob the ID in prose — i.e. authors currently contort their writing to avoid tripping a hook. |

**Restated intent**:
> Attribution must come from **where the work is happening**, not from what the text happens to
> mention. A tool call is attributed to a task only when a structural signal says so — never
> because a Task ID appears somewhere in a file the agent happened to read.

**Why this blocks T040**: DDR-0001 maps spend as "session `/cost` split proportionally across that
session's tagged entries". With wrong tags the derived audit log is *confidently wrong*, which is
worse than the manual log that merely stopped. T040's guide already declares `Depends on: T043` and
instructs the agent to STOP if this task is not done.

**Out of scope** (this task explicitly does NOT do):
- Anything in T039 / T040 / T041's file lists (see *Files Must NOT Touch*)
- Writing the token-audit generator — that is T040
- Changing what the trace *records* (fields, format, JSONL shape) — only **which file** it lands in
- Changing the step limit value, or the block message wording beyond what attribution requires
- Rewriting `pre_agent_validate_guide.py`'s logic — it is the reference implementation to reuse,
  not a target to refactor

**Requirement Refs**: this repo has no `PRD.md`. Traceability:
- **DDR-0001** (`docs/ddr/0001-measure-first-token-refactor.md`) + **Amendment 1 (2026-07-21)** —
  the reopened window is derived from event-trace, so trace tags must be trustworthy
- **`tasks/TASK_GUIDE_T040.md` → Dependencies & Reachability** — names T043 as its precondition
- **`memory/learnings.md`** — step-limit false-positive entry

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Both defects verified by the Supervisor by reading the two hook sources on 2026-07-23 —
      `find_task_id` is a bare `re.search(r"\bT\d{3}\b", ...)` in both files
- [x] Trace mis-attribution independently verified 2026-07-21 against `memory/event-trace/`
- [x] Domain terms align — "Task ID", "structural reference", "hook" are already canonical
- [x] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `find_task_id`
> The function name present in both `post_tool_trace.py` and `pre_agent_step_limit.py` that this
> task replaces. Grep-able; after this task it should resolve to the shared helper's call sites.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A single shared helper module exists (e.g. `.claude/hooks/lib/task_context.py`) exposing one attribution function, and **both** hooks call it — neither defines its own `find_task_id` regex any more | "both are wrong in the same way" |
| 2 | Attribution **never** reads `tool_response`. Given a `Read` of a file whose body contains `T001`, the record is NOT filed under T001 | the verified trace defect |
| 3 | Attribution resolves in a documented precedence order, first match wins: (a) `CLAUDE_ACTIVE_TASK` env var if set and well-formed; (b) a `tasks/TASK_GUIDE_Txxx.md` path appearing in a **path-valued** field of `tool_input` (`file_path`, `notebook_path`, `path`); (c) for `Agent` calls only, a structural ref in `tool_input.prompt` — a `TASK_GUIDE_Txxx.md` path or an explicit `Task ID:` line; (d) otherwise unattributed | "structural signal, never prose" |
| 4 | Prose mentions never attribute: `Edit` whose `new_string` contains "…as in T028…", or a `Bash` command string containing `T017`, resolve to unattributed | step-limit false-positive |
| 5 | `post_tool_trace.py` writes unattributed records to `memory/event-trace/_untagged.jsonl` — still never dropped | existing behavior preserved |
| 6 | `pre_agent_step_limit.py` **exits 0 without counting** when unattributed (today it also exits 0 — confirm no call is counted against a task it does not belong to) | "attribution comes from where the work is happening" |
| 7 | The `Agent`-spawn path still attributes correctly: a spawn prompt referencing `tasks/TASK_GUIDE_T099.md` yields `T099` for both hooks | no regression on the case that works |
| 8 | **Negative**: the trace record schema (`timestamp`, `tool_name`, `summary`, `is_error`) is byte-compatible — an existing `.jsonl` line still parses under the new code | "only which file it lands in" |
| 9 | **Negative**: `pre_agent_validate_guide.py` behavior is unchanged — its own tests still pass untouched | it is the reference, not a target |
| 10 | Stale counter cleanup: the 25+ `.claude/hooks/.state/step_count_T*.txt` files for Done tasks are removed **once**, and the task documents that `post_agent_move_to_review.py` is what resets them going forward | `memory/learnings.md` "25+ stale counter files" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Hook event JSON: `Read` of `PROJECT_KANBAN.md`, response body containing `**T001**` | record appended to `_untagged.jsonl`, not `T001.jsonl` | automated test |
| 2 | Hook event JSON: `Edit` with `new_string` mentioning `T028` in prose | unattributed; no `step_count_T028.txt` increment | automated test (negative) |
| 3 | Hook event JSON: `Agent` with prompt referencing `tasks/TASK_GUIDE_T099.md` | attributed `T099` in both hooks | automated test |
| 4 | `CLAUDE_ACTIVE_TASK=T099` set, any tool call | attributed `T099` regardless of payload text | automated test |
| 5 | Malformed / empty stdin | both hooks exit 0 silently (existing contract) | automated test (negative) |
| 6 | An existing pre-change `.jsonl` line | `json.loads` succeeds, same keys | automated test (AC8) |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/ -q && \
  echo '{"tool_name":"Read","tool_input":{"file_path":"PROJECT_KANBAN.md"},"tool_response":{"content":"- [x] **T001** done"}}' \
  | python3 .claude/hooks/post_tool_trace.py && \
  tail -1 memory/event-trace/_untagged.jsonl
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_task_context.py` (29 tests — 18 hook-level via subprocess from a foreign cwd, 11 `resolve_task_id` unit). Run at commit `de7f571`, clean tree: `python3 -m pytest .claude/hooks/tests/ -q` → `............................................................ [100%]` / `60 passed in 0.60s` (31 pre-existing + 29 new). See the RED-before-GREEN and mutation runs below. |
| Verification command run | ☑ pass | Guide's exact command at `de7f571`: `60 passed in 0.60s`, then trace dir listing `_untagged.jsonl` (no `T001.jsonl` created), `tail -1` → `{"timestamp": "2026-07-23T04:22:29.791662+00:00", "tool_name": "Read", "summary": "{\"file_path\": \"PROJECT_KANBAN.md\"}", "is_error": false}` |
| Negative cases hold | ☑ pass | **RED first** (tests written against the unfixed hooks): 8 failed / 10 passed — `expected only _untagged.jsonl, got ['T001.jsonl']` (AC2), `AssertionError: ['step_count_T028.txt'] == []` (AC4 step counter), `got ['T028.jsonl']` (AC4 trace). **Then 6 mutations of the fixed source, each observed RED and reverted**: M1 reinstate whole-payload regex → `got ['T001.jsonl']`; M2 drop fail-open try/except → hook exits 1 with `JSONDecodeError`; M3 drop `is_error` key → `{'summary','timestamp','tool_name'} != {'is_error',...}` (AC8); M4 drop Agent-prompt branch → `['_untagged.jsonl'] != ['T099.jsonl']` (AC7); M5 make the lib import cwd-relative → same RED, proving the foreign-cwd subprocess test has teeth; M6 trust `CLAUDE_ACTIVE_TASK` blindly → real path traversal `memory/event-trace/../../etc/passwd.jsonl`. Post-restore `60 passed`. AC9: `git diff` shows `pre_agent_validate_guide.py` untouched; its 7 tests pass inside the 60. |
| verify | ☑ pass | pass — end-to-end in the real deployment shape, not just in-repo. `setup.sh` install into a fresh temp git repo ships `.claude/hooks/lib/task_context.py` via the MANIFEST `.claude/hooks` line; running the installed hook from `cwd=/` gave `T099.jsonl` for an Agent spawn prompt whose pasted MEMORY text also mentions T001, `_untagged.jsonl` for an Edit whose prose mentions T028, and the installed step-limit hook exited 0 with zero counter files for that same Edit. (Run manually — a sub-agent has no `Skill` tool.) |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed the 2 changed hooks + the new lib + every consumer of what they produce: `pre_bash_block_unsafe_merge.py` (reads `event-trace/<task>.jsonl`), `post_agent_move_to_review.py` (writes/deletes `step_count_<task>.txt`), `post_write_register_task.py`, `pre_agent_validate_guide.py`. Two consumer-side findings reported to the Supervisor, neither fixed here (both files are out of scope). |
| Full smoke suite still green (no regression) | ☑ pass | `bash scripts/smoke-install.sh` at `de7f571` → all 15 `[ok]` assertions, final line `smoke-install.sh: PASS` |
| **UI: Visual regression** | ☑ N/A | Python hooks, no UI component |
| **UI: Design-system compliance** | ☑ N/A | Python hooks, no UI component |
| **UI: Responsiveness** | ☑ N/A | Python hooks, no UI component |

---

## Approach

**Reuse the pattern that already works.** `pre_agent_validate_guide.py:extract_structural_task_ids`
was written precisely to stop bare-prose `Txxx` substrings from being treated as task references.
That idea is correct; it is simply not applied to the two hooks that need it most. Lift it into a
shared module and have all attribution flow through one function.

Suggested shape (adapt to what the code actually needs — do not over-build):

```
.claude/hooks/lib/task_context.py
    resolve_task_id(event) -> str | None
```

Precedence, first match wins, documented in the module docstring **and** mirrored in the
Acceptance Criteria above:

1. `CLAUDE_ACTIVE_TASK` env var — the explicit override; validate it matches `^T\d{3}$` and ignore
   it otherwise rather than trusting it blindly.
2. A `TASK_GUIDE_Txxx.md` path in a **path-valued** `tool_input` field. Path fields only — not a
   whole-payload regex, which is how the current bug happens.
3. `Agent` calls only: structural ref inside `tool_input.prompt` (guide path, or a `Task ID:` line).
4. `None` → caller decides (`_untagged` for the trace; no counting for the step limit).

**Deliberately rejected — do not implement:**
- *Infer the task from the git worktree path.* Worktrees here are named `agent-<hash>`
  (`git worktree list` confirms), carrying no Task ID. It would silently resolve to nothing while
  looking like it works.
- *Keep the whole-payload regex as a last-resort fallback.* That reintroduces exactly the defect —
  a wrong tag is worse than a missing one. This is the same principle T042 settled: a visibly
  missing value beats a plausible wrong one.
- *Add a new hook.* Nothing here needs one.

**Import path caveat:** hooks are invoked as standalone scripts via
`python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>.py`, so `.claude/hooks/` is not automatically an
importable package from an arbitrary cwd. Make the import work explicitly (e.g. `sys.path` insert
based on `__file__`, matching the existing `ROOT = os.path.dirname(...)` idiom already in both
files) and cover it with a test that runs the hook **as a subprocess from a different cwd** — not
just via direct import, which would hide the failure.

**Fail-open, always.** Both hooks currently `sys.exit(0)` on any parse problem. Preserve that: a
broken attribution helper must never block or crash a tool call. Wrap the resolve call so an
unexpected exception degrades to "unattributed", not to a traceback on every tool use in the repo.

**Write the tests first** (`tdd`). `.claude/hooks/tests/` already holds four pytest files
(`test_post_write_register_task.py`, `test_pre_agent_validate_guide.py`, …) — follow their existing
conventions exactly rather than inventing a new style.

**AC10 (stale counters)** is cleanup, not logic: delete the existing `step_count_T*.txt` files for
tasks already Done, and state in the completion report that ongoing resets are
`post_agent_move_to_review.py`'s job. Do not add new reset logic — that is a separate concern and
would be scope creep.

---

## Edge Case Checklist

- [x] `tool_input` field names vary by tool (`file_path`, `notebook_path`, `path`, `command`,
      `prompt`). Enumerate the path-valued ones explicitly; never fall back to scanning all values.
      → `task_context.PATH_FIELDS = ("file_path", "notebook_path", "path")`, scanned in that fixed
      order; `test_only_path_valued_fields_are_scanned` asserts both directions (each path field
      attributes; `command`/`content`/`new_string`/`old_string`/`description`/`pattern` never do).
- [x] A `Write` creating `tasks/TASK_GUIDE_T044.md` **should** attribute to T044 — that is a genuine
      structural signal via `file_path`, and it is how new guides get traced. Don't break it.
      → `test_write_of_a_new_task_guide_attributes_via_file_path` (the `content` in that fixture also
      mentions T001/T017, and is correctly ignored).
- [x] `Bash` commands that legitimately contain a guide path (e.g. `cat tasks/TASK_GUIDE_T012.md`)
      are ambiguous. Decided: **never scanned → unattributed.** Command text is free text that can
      quote arbitrary file content, and scanning it is the same class of guess being removed.
      Documented in the `task_context` module docstring; `test_bash_command_containing_a_guide_path_is_not_attributed`.
- [x] Case sensitivity: matched with `re.IGNORECASE` and normalized to upper case + 3 digits.
      `test_lowercase_guide_path_normalizes_to_the_same_bucket` (`tasks/task_guide_t044.md` → `T044.jsonl`)
      and `test_task_ids_are_normalized_to_three_digits_upper_case` (`t44` and `T044` are one bucket).
- [x] Concurrent worktree runs append to the same `.jsonl`. Unchanged — still a single
      `open(path, "a")` + one `write()`; no read-modify-write introduced.
- [x] This guide names `T001`, `T017`, `T028`, `T040`, `T042` in prose. Confirmed live during this
      task under the *pre-fix* hooks: reading `.claude/agents/general-agent-template.md` (which only
      *mentions* T001) appended to `memory/event-trace/T001.jsonl` — the defect reproducing itself
      while being fixed. No bracket-globbing was needed; the step limit was never hit.
- [x] Do not "improve" adjacent hook code while in these files (Surgical Changes). → diff is
      attribution only; `STATE_DIR`/`TRACE_DIR`/record shape/block message all left as-is.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/task_context.py` | **New** — shared `resolve_task_id(event)` with documented precedence |
| `.claude/hooks/post_tool_trace.py` | Drop local `find_task_id`; call the helper; stop reading `tool_response` for attribution |
| `.claude/hooks/pre_agent_step_limit.py` | Drop local `find_task_id`; call the helper |
| `.claude/hooks/tests/test_task_context.py` | **New** — attribution unit + subprocess tests |
| `.claude/hooks/.state/step_count_T*.txt` | Delete stale counters for Done tasks (AC10) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_agent_validate_guide.py` | Reference implementation; AC9 requires its behavior and tests stay untouched |
| `.claude/hooks/post_agent_move_to_review.py` | Counter reset is its job already; changing it is a separate concern |
| `.claude/settings.json` | Hook wiring is unchanged — same scripts, same matchers |
| `docs/ddr/0001-measure-first-token-refactor.md` | An agent must not edit a decision record; the Supervisor amends it |
| `scripts/token-audit.sh`, `reports/token-audit_*` | Owned by T040 |
| `CLAUDE.md` | Owned by T039 |
| `.claude/agents/general-agent-template.md` | Owned by T041 |
| `.claude/hooks/post_write_register_task.py` | Owned by T042 this cycle |

---

## Test Plan

1. **Red**: write `.claude/hooks/tests/test_task_context.py` against the *current* hooks. The
   `Read`-of-KANBAN case (SC1) and the prose-mention cases (SC2) must fail — that failure is the
   reproduction of the reported defect, and its output belongs in Evidence.
2. **Green**: add the shared helper, rewire both hooks; SC1–SC6 pass.
3. **Subprocess test**: invoke each hook as `python3 .claude/hooks/<name>.py` from a different cwd
   with event JSON on stdin, confirming the import path actually resolves in the real invocation
   shape — not only under direct import.
4. **Negative controls**, each with pasted output: prose-mention non-attribution; malformed stdin
   exits 0; an existing pre-change `.jsonl` line still parses.
5. **Regression**: `python3 -m pytest .claude/hooks/tests/ -q` — all pre-existing hook tests green,
   especially `test_pre_agent_validate_guide.py` (AC9). Then `bash scripts/smoke-install.sh`.
6. Paste real command output — not a claim of output — into every Evidence row
   (`memory/learnings.md`: "a checkmark is a claim, not a fact").

---

## Completion Checklist

- [x] Implementation done — commit `de7f571`
- [x] Self-review run **manually** (a sub-agent's tool set is Read/Write/Edit/Bash/Glob/Grep — no
      `Skill` tool, so `code-review` could not be invoked as a skill). Reviewed the full diff plus
      every consumer of the trace files and step counters. Findings are in the completion report.
- [x] Security review performed **manually** — the built-in was not invocable here for two reasons
      (no `Skill` tool in a sub-agent, and the known `origin/HEAD` hardcoding vs this repo's `github`
      remote). Attack surface reviewed: `CLAUDE_ACTIVE_TASK` is the one externally-supplied value
      that reaches a filename; it is validated with an anchored `T\d{3}\Z` match, and mutation M6
      demonstrated a real path traversal (`memory/event-trace/../../etc/passwd.jsonl`) the moment
      that validation is removed — so the check is load-bearing and covered by a test. All other IDs
      come from `T(\d+)` digit captures and are filename-safe. `sys.path.insert` adds only the
      repo's own `.claude/hooks/lib` (writable only by someone who could already edit the hook);
      stdlib imports complete before it. No new subprocess/eval/network, no secret logging;
      attribution now reads *less* of the payload than before (`tool_response` is no longer read).
      No findings.
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `verify` performed manually (no `Skill` tool) — see the `verify` Evidence row: a real
      `setup.sh` install into a fresh temp repo, hooks driven from `cwd=/` in the deployed shape
- [x] Report to the Supervisor for `memory/`: **yes — one other hook still infers a Task ID from
      free text.** `post_agent_move_to_review.py:28` does `re.findall(r"\bT(\d{3})\b", prompt)` over
      the whole Agent spawn prompt, which always contains a verbatim `memory/MEMORY.md` paste full of
      prose task IDs. Bounded (it only acts on rows currently in `### In Progress`) but real: it can
      move an unrelated in-progress task to Ready for Review and delete its step counter. Left
      untouched — it is on this task's *Files Must NOT Touch* list. Details + a second, unrelated
      finding are in the completion report. No memory file was written by this agent.
- [x] Supervisor notified: task ready for Stage 4 review
