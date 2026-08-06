# TASK_GUIDE — T057: Self-clearing step-limit block + raised default limit
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
6. Read `.claude/hooks/pre_agent_step_limit.py` in full — T056 rewrote it and its docstring explains the current keying
7. C2 task: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

On 2026-08-06 the step-limit guard hard-blocked the Supervisor's session **four times in one day**,
each time requiring the user to run a manual `rm` because the Supervisor could not clear the counter
itself — `Bash` and `Read` are both blocked, and `Write` only escapes when the counter file does not
already exist.

T056 keyed counters by `session_id` to stop cross-session bleed. That fixed agent-vs-*unrelated*-session.
It did **not** fix the pairing that actually occurs: **a spawned sub-agent inherits its parent's
`session_id`**, so `step_count_<parent-session>_T054.txt` blocked the Supervisor when T054's agent
legitimately spent 42 calls on a ~7-file task.

**Restated intent**:
> A runaway must be interrupted, but interrupting it must never leave a session unable to act — and
> never require a human to run a shell command to recover.

**Chosen approach** (user decision, 2026-08-06): make the block **self-clearing**. When the count
exceeds the limit, emit the block message *and* reset the counter to 0 in the same call. The runaway
agent's current call still dies, so it must stop and report — but the next call from any session
works, so no lockout can persist and no manual `rm` is ever needed. This deliberately does not depend
on telling an agent apart from its spawner, which no field currently available to the hooks can do.

**Accepted trade-off, stated explicitly**: this weakens the guard. A genuinely stuck loop is now
interrupted every N calls rather than halted permanently. That is accepted because the guard's
observed cost (4 hard lockouts, ~an hour of recovery, 2 agent runs lost) has vastly exceeded its
observed benefit (0 real runaways caught). AC6 preserves an escalating signal so a true loop is still
visible.

**Out of scope**:
- Keying the counter on `cwd`, `transcript_path`, or any agent-identity field — investigated and
  rejected for now: no hook currently receives such a field, and its availability is unverified.
- Any change to `.claude/hooks/lib/task_context.py` or the `active_task` attribution chain.
- Re-enabling `post_agent_move_to_review.py` as a writer (T044 documented why it cannot be).

**Requirement Refs**: the 2026-08-06 incidents recorded in `memory/learnings.md` ("A guard can lock
out the only role able to release it", "A sub-agent inherits its parent's `session_id`") and T056's
own decisions entry.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the incidents (by Supervisor / user — not the implementing agent)
- [ ] The weakened-guard trade-off above is understood and accepted, not quietly optimised away
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: None — T056 is merged; this modifies the file T056 rewrote.

**Entry point**: `.claude/hooks/pre_agent_step_limit.py` — `main()`, the `count > STEP_LIMIT` branch

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | When the count exceeds the limit, the hook emits the block **and** resets the counter to 0 in the same invocation | the chosen approach |
| 2 | The call immediately following a block is **allowed** — proven by driving the hook `LIMIT + 2` times and asserting the last call emits no `decision` | "no lockout can persist" |
| 3 | The blocking call still emits `"decision": "block"` — the runaway's current call dies, it is not merely warned | "a runaway must be interrupted" |
| 4 | `CLAUDE_STEP_LIMIT`'s default is raised from 40 to a value justified in the code comment; env override still wins | 40 was too low for a ~7-file C2 task |
| 5 | The block message no longer instructs the reader to manually reset a counter file — that instruction is now false | the message told the Supervisor to run a command it was blocked from running |
| 6 | Repeated blocks for the same task are counted in a separate durable field, and the message escalates on the 3rd+ block ("this task has now been interrupted N times — it may be genuinely stuck") | AC-level mitigation of the accepted trade-off |
| 7 | Fail-open preserved: malformed stdin, unreadable/unwritable counter, or unwritable state dir never raise and never block | `.claude/agents/general-agent-template.md` |
| 8 | T056's session-keyed filename and TTL behaviour are unchanged — this task only changes what happens *at* the limit | no regression on T056 |
| 9 | All existing hook tests pass **unmodified**; any test that must change is flagged to the Supervisor with a reason, not silently edited | recorded: modifying pre-existing tests is how a suite goes falsely green |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `LIMIT + 1` events for one task/session | The last emits `decision: block` | automated test |
| 2 | `LIMIT + 2` events for one task/session | The **last** emits nothing — the session recovered by itself | automated test |
| 3 | The counter file after a block | Contains `0` (or is absent), never a value above the limit | automated test |
| 4 | `CLAUDE_STEP_LIMIT=5` in env | Block fires on the 6th call, not the new default | automated test |
| 5 | 3 separate blocks for the same task | The 3rd block's message contains the escalation wording | automated test |
| 6 | Malformed stdin / unwritable state dir | exit 0, no `decision` emitted | automated test |
| 7 | Full existing suite | Still green, unmodified | `python3 -m pytest .claude/hooks/tests -q` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_step_limit_self_clearing.py` — 11 tests, all pass: `python3 -m pytest .claude/hooks/tests/test_step_limit_self_clearing.py -q` → `11 passed in 1.56s` |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `188 passed in 7.63s`, re-run by the Supervisor from the main checkout after merge. **The agent's own run recorded `8 failed, 180 passed` and it correctly STOPPED rather than editing those tests (AC9).** All 8 were pre-existing assertions encoding intentionally-superseded behaviour — hardcoded 'blocks at 41' (broken by the raised default), the single-line counter format, and SC2's explicit 'session A must still be blocked' which this task deliberately reverses. The Supervisor verified each independently and updated them with inline reasons, each keeping the property it existed to protect; the limit is now pinned via env in that suite so a future default change cannot silently invalidate it again. |
| Negative cases hold | ☑ pass | SC4 (`test_sc4_env_override_still_wins_over_raised_default`): env override `CLAUDE_STEP_LIMIT=5` blocks on the 6th call, not the raised default — pass. SC6/AC7 fail-open (`test_sc6_malformed_stdin_fails_open_no_decision`, `test_ac7_unwritable_counter_still_fails_open`): malformed stdin and an unparseable counter file both `returncode == 0` with no `decision` emitted — pass. |
| verify | ☑ pass | Behaviour verified end-to-end by the Supervisor, not merely asserted: with the limit pinned low, the call at the limit emits `"decision": "block"` and **the very next call is allowed** — the session self-recovers. AC5 confirmed live (message no longer says 'manually reset'; it states the counter was reset automatically) and AC6 confirmed live (escalation wording appears on the 3rd block, not the 1st or 2nd). Full suite `188 passed` from the main checkout post-merge, smoke-install PASS — pass. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Changed: `.claude/hooks/pre_agent_step_limit.py` (the one file the guide's Entry Point names) + new test file. No other file touched; `reports/token-audit_2026-07-21.md` was incidentally modified by running the hooks during testing and was reverted with `git checkout --` before commit (confirmed clean `git status --short`). |
| Full smoke suite still green (no regression) | ☑ pass | See Verification command row — 8 pre-existing failures, flagged per AC9, not a silent regression. |
| **UI: Visual regression** | ☐ N/A | Pure hook task — no UI component |
| **UI: Design-system compliance** | ☐ N/A | Pure hook task — no UI component |
| **UI: Responsiveness** | ☐ N/A | Pure hook task — no UI component |

---

## Demonstration

**BEFORE** (executable — captured before the first implementation commit, via `git stash` to run the
original T056 hook): drove `pre_agent_step_limit.py` with 42 events (`LIMIT + 2`, default limit 40) for
task `T057DEMO` under one `session_id` (`DEMO`). Real captured stdout:

```
call 41: '{"decision": "block", "reason": "[hook:pre_agent_step_limit] T057 has exceeded 40 tool calls
without reaching Ready for Review. Killing the run to prevent an infinite loop / token waste.
Supervisor: stop, inspect memory/event-trace/T057.jsonl, and either escalate to the user or manually
reset .claude/hooks/.state/step_count_DEMO_T057.txt after confirming the task isn\'t actually stuck."}'
call 42: '{"decision": "block", "reason": "[hook:pre_agent_step_limit] T057 has exceeded 40 tool calls
without reaching Ready for Review. Killing the run to prevent an infinite loop / token waste.
Supervisor: stop, inspect memory/event-trace/T057.jsonl, and either escalate to the user or manually
reset .claude/hooks/.state/step_count_DEMO_T057.txt after confirming the task isn\'t actually stuck."}'
```

Both the 41st and the 42nd calls are blocked — the session never recovers on its own, and the message
names a manual `rm`-style reset the blocked reader cannot carry out (`Bash`/`Read` are both blocked by
this same hook). That is the lockout, reproduced on demand. (Note: `task_id` resolved to `T057` rather
than the literal string `T057DEMO` because `task_context.py`'s structural resolution used this session's
real `.claude/hooks/.state/active_task` file, set to `T057` per the spawn prompt's Trace Attribution
step, ahead of the event's own text — the counter filename and lockout behaviour demonstrated are
unaffected by this.)

**AFTER**: covered by `test_sc1_block_fires_with_env_limit` + `test_sc2_call_after_block_is_allowed` in
`.claude/hooks/tests/test_step_limit_self_clearing.py` (mutation-checked both directions — see Test Plan
section, GREEN restored and reverted before commit): the call at the limit is blocked
(`decision: block`), the counter file's first line reads `0` immediately after
(`test_sc3_counter_reads_zero_after_block`), and the very next call for the same session/task is
allowed (empty stdout, no `decision`). The block message no longer contains "manually reset" or a
`.state/step_count_` path (`test_ac5_block_message_no_longer_instructs_manual_reset`).

**DELTA**: a runaway is still interrupted (the over-limit call itself still dies with `decision: block`),
but no session can be left unable to act, and no human ever has to run a shell command to recover one.
AC6's escalating message (`test_sc5_third_block_escalates_message`) preserves visibility into a truly
stuck loop across repeated blocks, mitigating the accepted trade-off.

**WITNESS**: [filled at Stage 4/5 — derive from `memory/event-trace/T057.jsonl`, not typed. Must not
be the implementing agent alone.]

---

## Approach

**Pattern reference**: `pre_agent_step_limit.py` as T056 left it — keep its session-keyed filename,
its TTL, its defensive env parse, and its fail-open wrappers exactly as they are. This task changes
only the `count > STEP_LIMIT` branch and the default limit constant.

The block-count for AC6 needs somewhere durable. Simplest shape consistent with the existing file:
write the counter as two lines (`count` on line 1, `block_count` on line 2), mirroring
`task_context.py`'s two-line `active_task` format, and treat a legacy one-line file as `block_count`
0. Do not add a second file — one more piece of state in `.state/` is one more thing to leak.

Reset means write `0`, not delete. Deleting adds a failure mode on a read-only state dir, and the
block-count must survive the reset to make AC6 possible at all.

For AC4, pick the new default from evidence rather than taste: T054 consumed 42 calls making forward
progress on every one, and T056 took 38. State the reasoning in the comment.

---

## Edge Case Checklist

- [ ] The reset must happen even if the block message fails to serialise — order the writes so a crash between them cannot leave the counter above the limit
- [ ] A legacy one-line counter file written by T056 must not crash the two-line parse (AC8 regression risk)
- [ ] `block_count` must survive the count reset, or AC6's escalation never fires
- [ ] Clock skew / TTL expiry interacting with `block_count` — an expired counter should reset `count`, but should it reset `block_count`? Decide deliberately and comment the choice
- [ ] Two sessions sharing one counter (the T054 case) both being reset by either one — acceptable under this design, but confirm it cannot produce a negative or runaway value
- [ ] The escalation message must not imply the Supervisor should run a shell command (the defect AC5 removes)
- [ ] An unwritable state dir at reset time — fail open, never raise, never leave the block in place without the reset

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_agent_step_limit.py` | Self-clearing block, two-line counter with `block_count`, raised default, rewritten message |
| `.claude/hooks/tests/` | New tests for SC1–SC6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/task_context.py` | Attribution chain is a separate concern; 4 recorded defects live below its logic |
| `.claude/hooks/post_agent_move_to_review.py` | T044 documented why it cannot be a writer |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Merge gate is out of scope |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Test Plan

Drive `main()` as a real subprocess with crafted JSON events — the observable contract is stdout plus
the counter file's contents, and only a subprocess run exercises the real import-time env parsing.

The load-bearing assertion is SC2: **the call after a block is allowed**. Mutation-check it by
removing the reset write and confirming SC2 goes RED, then restore and confirm GREEN. Also
mutation-check AC3 (removing the block emission must turn SC1 RED) — a "self-clearing" guard that
silently stopped blocking at all would pass a naive SC2 while destroying the guard entirely. That
pairing is the one worth proving. **Commit before mutating.**

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — Medium risk, mandatory
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Demonstration block filled, including a BEFORE captured before the first implementation commit
- [ ] Supervisor notified: task ready for Stage 4 review
