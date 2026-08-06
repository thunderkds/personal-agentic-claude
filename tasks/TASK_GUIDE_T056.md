# TASK_GUIDE — T056: Session-scoped step counters + TTL expiry
**Date**: 2026-08-06
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Read `.claude/hooks/lib/task_context.py` **in full**, including the module docstring — it documents the precedence chain and four recorded defects that live *below* the logic under review
7. C2 task: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

On 2026-08-06 the step-limit guard hard-blocked an entire Supervisor session. Two Stage 3 agents
(T053, T055) were spawned in parallel. T055's agent legitimately consumed its 40-call budget. Because
the counter is keyed on task ID alone and the active-task pointer is a single shared file, **every
other session that resolved to `T055` inherited the exhausted budget** — including the Supervisor's.
The Supervisor's `Bash` and `Read` calls were both killed, while the hook's own block message
instructed the Supervisor to reset the counter — an action that itself requires a tool call.

Recovery required the user to intervene by hand. The escape hatch that eventually worked was
incidental: the `Write` tool was never gated, so overwriting the counter with `0` released the block.

**Restated intent**:
> A runaway or budget-exhausted task must never be able to block a session other than its own, and a
> step counter must not require manual cleanup to stop being a landmine.

**Root causes** (all three are real; this task fixes 1 and 2):
1. **Counters are never reset.** `post_agent_move_to_review.py` is deliberately inert as a writer
   (T044 — no completion event carries task identity), so `step_count_<task>.txt` grows monotonically
   forever. There is no automatic path back to zero for any task, ever.
2. **Counters are keyed by task alone**, so they are shared by every session that resolves to that
   task ID — including the Supervisor's.
3. A worktree-isolated agent structurally cannot write the main-checkout `active_task` path (its
   sandbox redirects the write), so it inherits whatever ID another agent left there. **Out of scope
   here** — see "Out of scope" below.

**Out of scope** (what this task explicitly does NOT do):
- Any change to `.claude/hooks/lib/task_context.py` or the `active_task` state file / attribution
  precedence chain. Root cause 3 is real but has four recorded defects living below its logic; it
  gets its own task. This task must make the guard safe *without* depending on attribution being
  fixed first.
- Changing `post_agent_move_to_review.py` back into a writer — T044 documented why it cannot be one.
- Any change to `pre_bash_block_unsafe_merge.py` or the merge gate.
- Raising or lowering `CLAUDE_STEP_LIMIT` itself (40 stays the default).

**Requirement Refs**: no `PRD.md` FR covers hook guardrails; traceability is to the 2026-08-06
incident recorded in `memory/learnings.md` ("A guard can lock out the only role able to release it")
and to the T047 known-limitation note in `task_context.py`'s docstring.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the incident (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked.

---

## Dependencies & Reachability

**Depends on**: None — independent of T054. Should land before any further parallel Stage 3 spawn.

**Entry point**: `.claude/hooks/pre_agent_step_limit.py` — `main()`, the `counter_path` construction

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The counter file name incorporates the event's `session_id` in addition to the task ID | root cause 2 |
| 2 | Two events with the same task ID but different `session_id` values maintain **independent** counts — one exceeding the limit does not block the other | the incident: Supervisor killed by an agent's budget |
| 3 | A counter whose file mtime is older than a TTL (default 6h, env-overridable) is treated as `0` rather than carried forward | root cause 1 |
| 4 | The TTL env var is parsed defensively — a malformed value falls back to the default and never raises at import | recorded: "A 'never raises' contract does not cover module import" |
| 5 | An event carrying **no** `session_id` still counts and still blocks (degrades to the current task-only behavior, never to "no guard") | a guard must not be disabled by a missing field |
| 6 | The block message names the exact counter file to reset, including the session component | the old message named a path that was correct but insufficient |
| 7 | Fail-open is preserved end to end: malformed stdin, unreadable counter, or unwritable state dir never raise and never block | `.claude/agents/general-agent-template.md` |
| 8 | Existing step-limit tests still pass unmodified — the guard still blocks a genuine runaway within a single session | no regression on the guard's actual purpose |
| 9 | A counter belonging to a task that has already reached Done/Ready for Review on `PROJECT_KANBAN.md` never blocks a later session — the TTL (AC3) is sufficient on its own, but confirm this case explicitly | 2026-08-06 second incident: a *completed* task's counter kept claiming victims |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | 41 events, same task, same `session_id` | 41st is blocked | automated test |
| 2 | 41 events for session A, then 1 event for session B, same task | session B's event is **allowed** — the incident, inverted | automated test |
| 3 | A counter file with mtime 7h old, then one new event | count restarts at 1, not 41 | automated test |
| 4 | `CLAUDE_STEP_COUNT_TTL_S="not-a-number"` | default TTL used, no exception at import | automated test |
| 5 | Event with no `session_id` key at all | still counted, still blocks past the limit | automated test |
| 6 | Malformed stdin / unwritable state dir | exit 0, no `decision` key emitted | automated test |
| 7 | Full existing suite | Still green | `python3 -m pytest .claude/hooks/tests -q` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_step_limit_session_scope.py` (new, AC1-AC9) + 2 pre-existing assertions in `.claude/hooks/tests/test_task_context.py` updated to the new session-scoped filename (`step_count_nosession_T099.txt`) |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `169 passed in 5.97s` |
| Negative cases hold | ☑ pass | SC4 (`test_sc4_malformed_ttl_env_falls_back_to_default_no_import_raise`): `CLAUDE_STEP_COUNT_TTL_S=not-a-number` → returncode 0, no traceback. SC5 (`test_sc5_missing_session_id_still_counts_and_blocks`): no `session_id` key → still counted, still blocked at call 41, file `step_count_nosession_T914.txt`. SC6 (`test_sc6_malformed_stdin_fails_open`, `test_sc6_unwritable_state_dir_fails_open`): malformed stdin → returncode 0, empty stdout; unreadable counter content → degrades to count 0, no raise. |
| verify | pass | `python3 -m pytest .claude/hooks/tests -q` → `169 passed in 5.97s`, no regressions. Mutation check on both load-bearing assertions (session key, TTL comparison) went RED then GREEN on restore (see Test Plan section / commit history). |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff touches only `.claude/hooks/pre_agent_step_limit.py` (the guide's declared entry point) and `.claude/hooks/tests/` (new test file + 2 filename-literal updates in an existing test). No change to `task_context.py`, `post_agent_move_to_review.py`, or `pre_bash_block_unsafe_merge.py`, per the guide's "Files Must NOT Touch". |
| Full smoke suite still green (no regression) | ☑ pass | Same run: `169 passed in 5.97s`, includes the 10 new tests in `test_step_limit_session_scope.py` and all pre-existing hook tests, 0 failures. |
| **UI: Visual regression** | ☐ N/A | Pure hook task — no UI component |
| **UI: Design-system compliance** | ☐ N/A | Pure hook task — no UI component |
| **UI: Responsiveness** | ☐ N/A | Pure hook task — no UI component |

---

## Demonstration

**BEFORE** (executable — captured 2026-08-06, before the first implementation commit): drove
`pre_agent_step_limit.py` with 41 events for task `T900` under `session_id: "A"`, then a single event
for `T900` under `session_id: "B"`. Real output, 41st call for session A:

```
{"decision": "block", "reason": "[hook:pre_agent_step_limit] T900 has exceeded 40 tool calls without
reaching Ready for Review. Killing the run to prevent an infinite loop / token waste. Supervisor:
stop, inspect memory/event-trace/T900.jsonl, and either escalate to the user or manually reset
.claude/hooks/.state/step_count_T900.txt after confirming the task isn't actually stuck."}
```

Session B's single event (its very first call for the task):

```
{"decision": "block", "reason": "[hook:pre_agent_step_limit] T900 has exceeded 40 tool calls without
reaching Ready for Review. ... .claude/hooks/.state/step_count_T900.txt ..."}
```

Session B is blocked despite having spent one call — the incident, reproduced on demand.

**BEFORE** (verbatim prior content): `counter_path = os.path.join(STATE_DIR,
f"step_count_{task_id}.txt")` — the session is absent from the key, and nothing anywhere in the file
consults the counter's age.

**AFTER** (captured post-fix, same script, same 41+1 drive against `T900`):

Session A's 41st call:

```
{"decision": "block", "reason": "[hook:pre_agent_step_limit] T900 has exceeded 40 tool calls without
reaching Ready for Review. ... .claude/hooks/.state/step_count_A_T900.txt after confirming the task
isn't actually stuck."}
```

Session B's single event: `(no output)` — the hook exits 0 with no `decision` key, i.e. allowed.

Session A's next call (confirming it is not silently reset by B's activity): still blocked, same
message, `step_count_A_T900.txt`.

A counter file aged 7h (mtime rewound via `os.utime`) restarts its count at 1 rather than carrying
the prior 41 forward — verified by `test_sc3_expired_counter_restarts_at_one` in
`.claude/hooks/tests/test_step_limit_session_scope.py`, which asserts the post-expiry call is
unblocked and the counter file's fresh content is `"1"`.

**DELTA**: one task's exhausted budget can no longer halt an unrelated session, and a stale counter
stops being a landmine that waits for the next session to resolve to that task ID.

**WITNESS**: [filled at Stage 4/5 — derive from `memory/event-trace/T056.jsonl`, not typed. Must not
be the implementing agent alone.]

---

## Approach

**Pattern reference**: `_resolve_max_age_s()` in `.claude/hooks/lib/task_context.py` — the defensive
env-var parse with a default fallback, written for exactly the import-time-raise defect AC4 guards
against. Copy that shape; do not invent a new one.

Key the counter on `f"step_count_{session}_{task_id}.txt"`, where `session` is a **sanitized** slice
of the event's `session_id` (it reaches a file name — treat it as untrusted, allow `[A-Za-z0-9]` only,
truncate, and fall back to a literal like `nosession` when absent or empty). The T047 docstring's
warning about externally-supplied values reaching file names applies directly here.

TTL: compare the counter file's mtime against the window and treat an expired file as count `0`.
Do not delete it — a write is enough, and deletion adds a failure mode on a read-only state dir.

Deliberately **not** solved here: the shared `active_task` file still means two concurrent agents can
mis-*attribute* each other's calls. After this task they can no longer *block* each other, which is
the harm that actually stopped a session.

---

## Edge Case Checklist

- [ ] `session_id` present but empty string, or a non-string type — must not produce a path like `step_count__T056.txt` colliding across sessions
- [ ] `session_id` containing `/` or `..` — it reaches a file name; sanitize before use
- [ ] A counter file that exists but is unreadable (permissions) — fail open, count as 0, never raise
- [ ] Clock skew making mtime appear in the future — treat as fresh, not as expired-and-reset (mirrors `task_context.py`'s `age_s < 0` handling)
- [ ] The state dir does not exist yet on first run — `makedirs(exist_ok=True)` already handles it; confirm it still does when the path is unwritable
- [ ] Old `step_count_<task>.txt` files from before this change linger in `.state/` — they must simply be ignored, not misread as a session-keyed file
- [ ] The block message must not leak a full absolute path containing anything sensitive; keep it repo-relative as it is today
- [ ] **The escape hatch must not depend on a file being absent.** Observed 2026-08-06: once blocked, `Bash` and `Read` are both killed, and `Write` only worked because the counter file did not yet exist — `Write` on an *existing* file requires a prior `Read`, which the same hook blocks. The first lockout was escapable by luck; the second was not, and needed the user. Whatever this task leaves in place, a blocked session must retain at least one reliable way to clear its own counter

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_agent_step_limit.py` | Session-keyed counter path, TTL expiry, defensive env parse, updated block message |
| `.claude/hooks/tests/` | New tests for SC1–SC6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/task_context.py` | Attribution/state-file race is a separate task; 4 recorded defects live below its logic |
| `.claude/hooks/post_agent_move_to_review.py` | T044 documented why it cannot be a writer |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Merge gate is out of scope |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Test Plan

Drive `main()` as a real subprocess with crafted JSON events, as
`test_demonstration_before_warning.py` does — the observable contract is stdout plus the counter
files, and a subprocess run is the only way to exercise the real import-time env parsing that AC4
covers.

Mutation-check the two load-bearing assertions: (a) drop the session component from the counter key
and confirm SC2 goes RED; (b) disable the TTL comparison and confirm SC3 goes RED. Restore and
confirm GREEN. An assertion never observed failing is not evidence — this repo has four recorded
vacuous-assertion incidents (T036/T042/T039, and T053's own near-miss). **Commit before mutating**:
reverting a mutation with `git checkout` also reverts your fix.

---

## Completion Checklist

- [x] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run — deferred to Stage 4 (Supervisor/reviewer)
- [ ] Security review: `Skill({ skill: "security-review" })` run — Medium risk, mandatory — deferred to Stage 4
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — deferred to Stage 5
- [x] Demonstration block filled, including a BEFORE captured before the first implementation commit
- [x] Supervisor notified: task ready for Stage 4 review
