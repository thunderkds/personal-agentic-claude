# TASK_GUIDE — T061: capture per-spawn cost telemetry the harness already receives
**Date**: 2026-08-07
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
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
6. Read `memory/codebase-map.md` (C2, multi-file)

Also read `.claude/hooks/post_tool_trace.py` and `.claude/hooks/lib/task_context.py` in full before editing either.

**STOP-check before anything else**: run `ls tasks/TASK_GUIDE_T061.md`. If it is not there, you are in a
worktree forked from the wrong commit — stop and report to the Supervisor rather than proceeding.

---

## Requirement (Pillar 1 — Adapt the requirement)

`.claude/hooks/post_tool_trace.py:53` reads `tool_response` out of the PostToolUse event and then uses
exactly one field from it — `is_error` on line 60. The record it writes contains `summarize(tool_input)`:
the prompt going *in*. Everything the spawn reports coming *back* is discarded.

For `tool_name == "Agent"` that discarded payload was measured empirically on 2026-08-07 with a
temporary probe (registered on `PostToolUse`/`Agent`, three spawns, then reverted):

```
tool_response keys: status  agentId  agentType  resolvedModel  content  prompt
                    totalTokens  totalToolUseCount  totalDurationMs  usage  toolStats

usage:      input_tokens, output_tokens, cache_creation_input_tokens,
            cache_read_input_tokens, cache_creation{ephemeral_5m,ephemeral_1h},
            service_tier, iterations[]
toolStats:  readCount searchCount bashCount editFileCount linesAdded linesRemoved otherToolCount
```

42 Agent spawns are already recorded in `memory/event-trace/`. Every one of them threw this away.

**Restated intent**:
> Every Agent spawn should leave behind a durable, machine-readable record of what it actually cost —
> tokens split by cache disposition, tool-call mix, lines changed, resolved model, duration — captured
> from data the harness already hands the hook, with no human in the loop and no new instrument.

**Out of scope**:
- Any analysis, report, dashboard, or optimization decision built on the captured data. This task captures; it concludes nothing.
- Any change to what `post_tool_trace.py` records for non-`Agent` tools. Their record shape stays byte-identical.
- Any `/cost` capture, manual logging, or session-level cost accounting. That is what DDR-0002 retired, and this task must not resurrect it.
- Re-opening DDR-0001's ≥20%/<5% $/task criteria. Superseded; not a target here.
- Reading `subagent_tokens` from rendered result text. The structured `tool_response` is the source.

**Requirement Refs**: none — internal, traced to the 2026-08-07 ideation session recorded in `BRAINSTORMING_LOG.md`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `post_tool_trace.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | For `tool_name == "Agent"`, the trace record gains a `spawn` object carrying `total_tokens`, `tool_use_count`, `duration_ms`, `resolved_model`, `agent_type`, `status` | "what it actually cost" |
| 2 | The `spawn` object carries a `usage` sub-object with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` | "tokens split by cache disposition" |
| 3 | The `spawn` object carries a `tool_stats` sub-object with `read_count`, `search_count`, `bash_count`, `edit_file_count`, `lines_added`, `lines_removed` | "tool-call mix, lines changed" |
| 4 | For every `tool_name` other than `Agent`, the emitted record is **byte-identical** to what the pre-change hook produced for the same event | scope lock |
| 5 | Negative: the record never contains the spawn's `prompt` or `content` fields from `tool_response` | those are already covered by `summary`; duplicating them doubles trace size for no gain |
| 6 | A missing, `None`, non-dict, or partially-populated `tool_response` produces a record with `spawn` **absent**, never a crash and never a partial object with `None` values | fail-open contract |
| 7 | A `tool_response` where `usage` or `toolStats` is missing still emits `spawn` with the fields that *are* present, omitting the rest | real payloads vary by harness version |
| 8 | `is_error` continues to be derived exactly as before | scope lock |
| 9 | Existing task attribution is unchanged — the record still lands in `memory/event-trace/<task>.jsonl` via `resolve_task_id` | scope lock |
| 10 | Negative: `MAX_SUMMARY_LEN` truncation of `summary` is unaffected by the new field | scope lock |
| 11 | Full hook suite green, all 220 pre-existing tests unmodified | no regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A realistic captured Agent event (fixture below) | record contains `spawn` with all three groups populated | automated test |
| 2 | A `Bash` event | record byte-identical to pre-change output | automated test, golden comparison |
| 3 | Agent event with `tool_response` absent / `None` / a string / `{}` | no `spawn` key, no exception, exit 0 | automated test, 4 cases |
| 4 | Agent event with `usage` present but `toolStats` missing | `spawn.usage` present, `spawn.tool_stats` absent | automated test |
| 5 | Full hook suite | 220 + new tests pass | automated test |

**Fixture**: use the real probe capture, not an invented one. A verbatim `tool_response` recorded on
2026-08-07 is reproduced in the Approach section below — copy it into the test as the fixture so the
test is pinned to a payload the harness genuinely produced.

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_post_tool_trace_spawn.py` — 26 tests, AC1–AC11 (25 by the implementer, 1 added by the Supervisor at Stage 4 to pin the P2 cache-TTL fix). `python3 -m pytest .claude/hooks/tests/test_post_tool_trace_spawn.py -q` → `25 passed in 0.65s`. **Not end-to-end**: the Agent payload is a fixture pinned to the guide's 2026-08-07 probe capture (key set + arm-B numbers); a test cannot spawn a sub-agent to produce a real `tool_response`. The hook itself *is* driven for real — subprocess, event JSON on stdin, foreign cwd, isolated sandbox root. |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `246 passed` (220 pre-existing, unmodified, + 26 new), re-run after the Stage 4 P2 fix. Baseline before any edit in this worktree: `220 passed in 7.19s`. |
| Negative cases hold | ☑ pass | **Supervisor added 3 further controls at Stage 4, all RED then restored GREEN**: AC5 forced `prompt`/`content` into `spawn`; the P2 `usage.update` disabled; the fixture reverted to its invented `ephemeral_5m` key. Implementer's own: AC4 golden: checked twice — pinned pre-change record lines (timestamp elided, key order included) **and** a differential run of the actual pre-change source recovered via `git show 82883a2:.claude/hooks/post_tool_trace.py`; both identical. AC6: five fail-open cases (key absent / `None` / string / `{}` / dict with no cost fields) all yield `set(record) == {timestamp, tool_name, summary, is_error}`, exit 0. All mutation-verified — 5 cycles, each RED then restored GREEN (`cp` from a backup, never `git checkout`): M1 emit `prompt`+`content` → 5 failed incl. `test_record_never_carries_the_spawn_prompt_or_content`; M2 always-emit `spawn` with `None`s → 13 failed; M3 drop the `Agent`-only guard → 7 failed incl. **both** golden tests; M4 pass camelCase through → 11 failed; M5 require both sub-objects → 6 failed. Restore verified byte-identical by `diff`. |
| verify | ☑ pass | Full suite 246 passed; hook exercised as a real subprocess in every test; `extract_spawn` never raises by construction (`isinstance` guard + `try/except` → `None`), matching the fail-open contract of `lib/task_context.py`. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Two files: `.claude/hooks/post_tool_trace.py` (+72/−0, one new pure function plus a 4-line `if tool_name == "Agent"` block) and the new test file. No file in "Files Must NOT Touch" was read or written. `pre_bash_block_unsafe_merge.py` reads these records by key and is unaffected: no existing key changed, one optional key added on `Agent` only. |
| Full smoke suite still green (no regression) | ☑ pass | `246 passed`; the 220 pre-existing tests are byte-unmodified (`git status --short` shows no change under `tests/` other than the new file). |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | hook change, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | hook change, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | hook change, no UI component |

---

## Demonstration

**BEFORE**: verbatim `.claude/hooks/post_tool_trace.py` lines 53–67 as of `82883a2`:

```python
    tool_response = event.get("tool_response", {})

    task_id = resolve_task_id(event) or "_untagged"

    os.makedirs(TRACE_DIR, exist_ok=True)
    trace_path = os.path.join(TRACE_DIR, f"{task_id}.jsonl")

    is_error = bool(tool_response.get("is_error")) if isinstance(tool_response, dict) else False

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "summary": summarize(tool_input),
        "is_error": is_error,
    }
```

Supporting capture, same commit — all 42 Agent records in `memory/event-trace/` carry only
`['timestamp', 'tool_name', 'summary', 'is_error']`, where `summary` is the spawn *prompt*.

Live capture, taken before the first implementation commit, against the real trace directory the
hook writes to. Note: `memory/event-trace/` does not exist inside this worktree (it is gitignored,
so a fresh worktree has none); the directory scanned is the main checkout's, which is where the live
hook actually writes — the same records the guide's "42 Agent spawns" line refers to, now 45.

```
$ ls memory/event-trace          # inside the worktree
ls: cannot access 'memory/event-trace': No such file or directory

captured_at_utc: 2026-08-07T06:32:22.958346+00:00
trace_dir: /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/memory/event-trace
agent_records: 45
records_with_spawn: 0
keys: ['is_error', 'summary', 'timestamp', 'tool_name'] count: 45
```

Every Agent record in existence has exactly those four keys and none has a `spawn` key.

**AFTER**: post-change record for an Agent spawn, emitted by the real hook over a subprocess with the
guide's probe payload on stdin (fixture, not a live spawn — see the note in the Evidence table):

```json
{"timestamp": "2026-08-07T06:35:21.754835+00:00", "tool_name": "Agent", "summary": "{\"subagent_type\": \"common-infrastructure\", \"prompt\": \"Task ID: T061\\nSee tasks/TASK_GUIDE_T061.md\"}", "is_error": false, "spawn": {"total_tokens": 16981, "tool_use_count": 1, "duration_ms": 6875, "resolved_model": "claude-sonnet-5", "agent_type": "common-infrastructure", "status": "completed", "usage": {"input_tokens": 2, "output_tokens": 3, "cache_creation_input_tokens": 404, "cache_read_input_tokens": 16572}, "tool_stats": {"read_count": 0, "search_count": 0, "bash_count": 1, "edit_file_count": 0, "lines_added": 0, "lines_removed": 0}}}
```

**DELTA**: an Agent trace record gains a `spawn` object carrying the six top-level cost fields, a
four-field `usage` split by cache disposition and a six-field `tool_stats`, all snake_cased, while
every non-`Agent` record stays byte-identical to what the pre-change hook emitted.

**WITNESS**: derived by the Supervisor from `memory/event-trace/T061.jsonl` (43 records,
`2026-08-07T06:27:02Z` to `2026-08-07T06:44:23Z`), first attributed test run at `06:32:12Z` — not
from the implementing agent's report.

**The agent's one acknowledged gap was closed by the Supervisor, not accepted.** It reported,
correctly, that its Agent-path test is a fixture because it cannot spawn a sub-agent to produce a
real `tool_response`. The Supervisor still had the two verbatim payloads captured by the 2026-08-07
probe and drove the new hook with them directly. Both reproduce their hand-measured numbers through
the new code path:

```
tokens=15669  cache_rd=15259  cr_5m=405  cr_1h=0  bash=1  model=claude-sonnet-5
tokens=16981  cache_rd=16572  cr_5m=404  cr_1h=0  bash=1  model=claude-sonnet-5
```

AC4 was additionally re-verified by an independent differential: the pre-change hook recovered via
`git show 82883a2:.claude/hooks/post_tool_trace.py`, run over identical `Bash`/`Write`/`Read` events
in a parallel sandbox, output compared with timestamps elided — **byte-identical**. AC5 was
mutation-controlled by the Supervisor (forcing `prompt`/`content` into `spawn` → RED, restore →
GREEN), as were the Stage 4 P2 fix and the fixture-drift correction.
---

## Approach

**Pattern reference**: `.claude/hooks/post_tool_trace.py` itself — its existing fail-open shape
(`try/except` around `json.load`, `sys.exit(0)` on any failure, `isinstance` guard before
`.get`) is exactly the contract the new extraction must honour. Imitate it rather than introducing
new error handling. Also read `.claude/hooks/lib/task_context.py` for the "never raises" contract
this hook family depends on.

Add a single extraction step for `tool_name == "Agent"`, guarded so that any shape other than the
expected one yields no `spawn` key at all. Suggested record shape:

```json
{"timestamp": "...", "tool_name": "Agent", "summary": "...", "is_error": false,
 "spawn": {"total_tokens": 16981, "tool_use_count": 1, "duration_ms": 6875,
           "resolved_model": "claude-sonnet-5", "agent_type": "common-infrastructure",
           "status": "completed",
           "usage": {"input_tokens": 2, "output_tokens": 3,
                     "cache_creation_input_tokens": 404, "cache_read_input_tokens": 16572},
           "tool_stats": {"read_count": 0, "search_count": 0, "bash_count": 1,
                          "edit_file_count": 0, "lines_added": 0, "lines_removed": 0}}}
```

Field names are snake_cased on the way in to match this repo's Python conventions; the harness sends
camelCase (`totalTokens`, `toolStats`, `resolvedModel`). Do not pass the harness's names through
unchanged — every other field in this record is snake_case.

### Why this is not what DDR-0002 retired

DDR-0002 retired the token-audit instrument on 2026-08-05 with the conclusion *retire, don't
re-instrument*. What it retired was **manual `/cost` logging** — an instrument that failed twice, in
both measurement windows, because it depended on a human pasting a number and that never once
happened. This task depends on no human action: the harness hands the hook the payload, and the hook
already runs on every Agent spawn today. It therefore cannot fail in the way that killed both prior
instruments. `reports/token-audit_*.md` stays retired and untouched; nothing here writes to it.

Recorded so the distinction is not re-litigated later: if a future reader thinks this reverses
DDR-0002, the answer is that DDR-0002 governed a manual channel, and this is an automatic one.

### Measurements that motivated this task (2026-08-07, temporary probe, since reverted)

Three spawns, same trivial work (`echo`), varying only the unique prompt size:

| arm | unique prompt | total | cache_read | cache_creation | output | tools |
|---|---|---|---|---|---|---|
| probe | 29 tok | 15,708 | 15,282 | 417 | 7 | 1 |
| A | 29 tok | 15,669 | 15,259 | 405 | 3 | 1 |
| B | 1,144 tok | 16,981 | 16,572 | 404 | 3 | 1 |

Two hypotheses were tested and one was **rejected** — recorded here because the rejection is the
reason this task is scoped to capture-only:

- **H1 — the payload carries structured cost fields.** **CONFIRMED.** Field list above.
- **H2 — unique per-task content is paid at `cache_creation` rates while stable injected content is
  served as `cache_read`.** **REJECTED.** Arm B added 1,115 tokens of novel prompt text and moved
  `cache_creation` by −1. The unique content landed in `cache_read` like everything else, because the
  spawn prompt is already inside the Supervisor's cached context by the time the agent starts.

The consequence is that **token-volume optimization is worth roughly a tenth of its nominal figure**,
since nearly everything injected is billed as a cache read. The larger lever is spawn *count* — every
spawn costs ~15.7k tokens before doing any work (arm A: 15,669 for a single `echo`), against 48,401
for T059's real three-line fix and 81,220 for T060.

**That conclusion rests on n=3 hand-run spawns and must not be treated as established.** It is
precisely why this task ships capture rather than any optimization: the next decision should be made
against dozens of real spawns, not three synthetic ones. Do not implement any optimization here, and
do not encode any of these numbers as thresholds in code.

---

## Edge Case Checklist

- [x] `tool_response` arriving as a JSON string rather than a dict — `isinstance` guard returns `None`; covered by `test_unusable_tool_response_yields_no_spawn_key[truncated payload-False]`. The same guard is applied one layer down to `usage`/`toolStats` (`test_non_dict_usage_and_tool_stats_are_skipped_not_crashed`), because this hook family's last four defects sat *below* the logic under review
- [x] `usage.iterations` never copied — it is absent from `SPAWN_USAGE_FIELDS`, asserted by `test_record_never_carries_the_spawn_prompt_or_content` and size-bounded by `test_record_line_stays_small` (5,000 iterations + 500 KB `content` → line < 1000 chars)
- [x] A spawn that errored still records its cost — `status` is copied when present, never required; `test_failed_spawn_still_records_its_cost` (status absent, `is_error` true) and `test_error_flag_still_derived_from_tool_response`
- [x] `usage.cache_creation.{ephemeral_5m,ephemeral_1h}` — **explicitly dropped**, not flattened: their sum is already `cache_creation_input_tokens`, which AC2 names, so keeping them adds a third nesting level for a value already present. Recorded in the code comment; asserted absent
- [x] `toolStats` all zeros is kept — omission would make "used no tools" indistinguishable from "harness didn't report"; `test_tool_stats_of_all_zeros_is_still_recorded`
- [x] Record size — fixed set of scalars, no unbounded field copied; see `test_record_line_stays_small`
- [x] Write mode untouched — still `open(trace_path, "a")` + a single `json.dumps` line; the diff does not touch the write

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/post_tool_trace.py` | extract Agent cost fields from `tool_response` into a `spawn` object, fail-open |
| `.claude/hooks/tests/test_post_tool_trace_spawn.py` | new test file — AC1–AC11 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/task_context.py` | attribution is correct and reviewed; T043/T047/T048 chain is closed |
| `.claude/hooks/token_audit.py`, `scripts/token-audit.sh` | the retired DDR-0002 instrument; this task is not connected to it |
| `reports/token-audit_*.md` | retired historical record; never write to it (T059) |
| `.claude/settings.json` | the hook is already registered on `PostToolUse`/`.*`; no new registration needed |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | the merge gate reads these records; changing what it reads is out of scope |

---

## Test Plan

New file `test_post_tool_trace_spawn.py`, matching the existing hook-test style (subprocess-driving
the hook with a JSON event on stdin, reading the resulting JSONL).

The load-bearing test is **AC4, the golden comparison**: capture the pre-change record for a `Bash`
event, then assert the post-change hook emits it byte-identically. Without this, a regression in the
common path would be invisible — `Agent` is a small fraction of traced calls.

Every new assertion must be mutation-verified: break what it guards, observe RED, restore, observe
GREEN, paste both. Note specifically that AC5 and AC6 are **negative** criteria — an assertion that
a key is *absent* passes trivially against a hook that never adds it, so mutate by making the hook
emit the forbidden key and confirm RED.

The implementing agent must not be the sole oracle; the Supervisor writes or signs off on the AC4
golden test and the AC6 fail-open cases.

---

## Completion Checklist

- [x] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run — **not run by the implementing agent**: the `Skill` tool is not available in a sub-agent context. A manual read-through of the full diff was done instead (findings: none beyond what the Evidence table records). Stage 4 must run the real skill.
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk) — **not run**, same reason. Manual note for the reviewer: the change adds no I/O, no new file path, no network, no `subprocess`, no user-controlled value reaching a filename; it copies six scalars out of a payload the hook already holds in memory. `task_id` (the only value reaching a path) is untouched.
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `Skill({ skill: "verify" })` run — equivalent verification performed and recorded in the Evidence `verify` row; the skill itself is not invocable here.
- [ ] `memory/MEMORY.md` updated (flag to Supervisor; sub-agents do not write memory)
- [x] Supervisor notified: task ready for Stage 4 review
