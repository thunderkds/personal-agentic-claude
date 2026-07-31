# TASK_GUIDE — T044: Hook lifecycle & evidence integrity — make the merge gate mean something
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
7. Read in full: `.claude/hooks/post_agent_move_to_review.py`, `.claude/hooks/pre_bash_block_unsafe_merge.py`,
   `.claude/hooks/lib/task_context.py` (landed by T043 — the helper this task reuses)

---

## Requirement (Pillar 1 — Adapt the requirement)

T043 fixed *which* task a tool call is attributed to. This task fixes *when* a task is considered
finished and *what counts as proof* it was verified. Three defects, all observed during the
2026-07-23 session, all in the same subsystem:

| # | Defect | Observed |
|---|---|---|
| A | `post_agent_move_to_review.py:28` extracts the Task ID with `re.findall(r"\bT(\d{3})\b", prompt)` over the **entire** `Agent` spawn prompt — which by Stage-3 rule always carries a verbatim `memory/MEMORY.md` paste full of prose task IDs. It can move an unrelated in-progress task to Ready for Review and delete its step counter. | Reported by the T043 agent after auditing every hook; it was on T043's must-not-touch list. |
| B | The same hook is a `PostToolUse` matcher on `Agent`, and with async/background sub-agents that event fires when the spawn is **issued**, not when it completes. The board says Ready for Review before any work exists. | Watched happen live on T039: the row flipped while the agent was still writing its first test. |
| C | `pre_bash_block_unsafe_merge.py:trace_shows_verification` accepts any non-error trace record whose `summary` merely **contains** `pytest\|npm test\|jest\|go test\|cargo test\|verify`. | Verified on T043: the only two qualifying records were Supervisor *inspection* commands that happened to contain those words. No test had run under that tag, yet the gate would have passed the merge. |

**Restated intent**:
> A task is marked review-ready because its work finished, not because a spawn started. A merge is
> allowed because a test actually ran, not because a string that looks like a test command appeared
> somewhere in a trace record.

Defect C is the important one. The gate exists specifically to close the "agent claims it ran tests"
gap — and it is currently satisfied by a claim-shaped string. It is the same vacuous-evidence family
as T039's AC5 checksum (see `memory/learnings.md`): a check that has never been observed rejecting
anything is not a check.

**Interaction with T043 — read before designing.** A `Bash` command is now never attributed, so a
real test run produces **no** trace record under any task unless `CLAUDE_ACTIVE_TASK=Txxx` is
exported in the environment where the tests run. Tightening C without addressing this makes the gate
fail closed on every honest task. Both halves must land together.

**Out of scope**:
- Re-litigating T043's attribution precedence — reuse `resolve_task_id` as-is
- `pre_agent_validate_guide.py` (the reference implementation) and `post_write_register_task.py`
- The `### `-truncation defect in `find_kanban_section` — that is T045
- Changing the step limit value or the Stage 4/5 pipeline definition in `CLAUDE.md`

**Requirement Refs**: no `PRD.md`. Traceability:
- **`memory/learnings.md`** — "The merge gate's own evidence is a substring match" (2026-07-23),
  "post_agent_move_to_review.py fires at spawn, not completion"
- **`memory/decisions.md`** — T043 entry (the helper), and the original deterministic-guardrails entry
  that introduced this gate
- **User directive 2026-07-23** — bundle these three into one task

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Defect A verified by the T043 agent's hook audit and by the Supervisor reading line 28
- [x] Defect B observed live by the Supervisor during the T039 spawn
- [x] Defect C reproduced by the Supervisor against the live `memory/event-trace/T043.jsonl`
- [ ] **Agent to confirm**: every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: **T043** (Done, merged 2026-07-23 at `95a7424`) — provides `lib/task_context.py:resolve_task_id`.

**Entry point**: `trace_shows_verification`
> The gate function in `pre_bash_block_unsafe_merge.py` this task hardens. Grep-able and unique.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `post_agent_move_to_review.py` resolves its Task ID via `lib/task_context.py:resolve_task_id` — no local free-text `T\d{3}` scan remains | Defect A |
| 2 | **Negative**: an `Agent` spawn prompt containing a MEMORY.md-style paste that mentions several unrelated task IDs in prose moves **only** the task the prompt is structurally about — no other In-Progress row changes and no other step counter is deleted | Defect A |
| 3 | The Ready-for-Review move happens on genuine sub-agent **completion**, not at spawn issuance. If the harness gives no reliable completion signal for background agents, the hook must **not** move the row at all and must say so in its docstring — a silently wrong board is worse than a manual one | Defect B |
| 4 | `trace_shows_verification` no longer accepts a bare substring match. A record qualifies only if the command **invokes** a test runner (matched at a command boundary — start of the command or after a `\|`, `&&`, `;`, `\|\|` separator), not if the token merely appears inside a longer string | Defect C |
| 5 | **Negative — this is the core proof**: a trace record whose summary is `ls memory/event-trace/ \| grep -c "pytest"` or `python3 -c "...pat=re.compile(r'pytest\|verify')..."` is **rejected**. Both are real records from `T043.jsonl` that the current gate accepts | Defect C |
| 6 | **Positive**: `python3 -m pytest .claude/hooks/tests/ -q`, `bash scripts/smoke-install.sh`, and `npm test` are each still accepted | no false-negative regression |
| 7 | `CLAUDE_ACTIVE_TASK` is exported wherever a task's tests are expected to run, so an honest task produces a qualifying record. Document the mechanism in the guide's Approach and in `craft-spawn-prompt`'s output if that is where it belongs | T043 interaction |
| 8 | **Negative**: with a missing or empty trace file the gate still fails **closed** (existing contract — do not weaken it) | existing behavior preserved |
| 9 | **Negative**: all three hooks preserve fail-open on malformed stdin — exit 0, no traceback | these fire on every tool call |
| 10 | **Negative**: `pre_agent_validate_guide.py` and its tests remain untouched | it is the reference |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Spawn prompt structurally about T099 but whose pasted memory text mentions T001, T028, T040 | only T099 moves; T001/T028/T040 rows and counters untouched | automated test |
| 2 | The two real `T043.jsonl` inspection records (fixture-copied into the test) | gate returns False | automated test (AC5) |
| 3 | A record whose summary is a genuine `python3 -m pytest …` invocation | gate returns True | automated test (AC6) |
| 4 | Trace file absent / empty / malformed JSONL | gate returns False; no traceback | automated test (AC8) |
| 5 | Malformed stdin to each of the three hooks | exit 0, silent | automated test (AC9) |

### Verification Command (exact, runnable)

```bash
CLAUDE_ACTIVE_TASK=T044 python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_merge_gate_evidence.py` (29 tests — AC4/AC5/AC6/AC8/AC9) + `.claude/hooks/tests/test_move_to_review.py` (11 tests — AC1/AC2/AC3/AC9). `python3 -m pytest .claude/hooks/tests/test_merge_gate_evidence.py .claude/hooks/tests/test_move_to_review.py -q` → `40 passed`. **+2 added at Stage 4 review by the Supervisor** (`test_runner_named_in_the_description_of_a_truncated_record_is_rejected`, `test_truncated_record_still_reads_its_own_command`) — the implementer was not the sole author of its own oracle |
| Verification command run | ☑ pass | **Independently re-run by the Supervisor**, not trusted from the implementer's claim. `CLAUDE_ACTIVE_TASK=T044 python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh` → `107 passed in 0.98s` + `smoke-install.sh: PASS` at `1565cd1`; `109 passed in 0.95s` + `smoke-install.sh: PASS` at `832231d` (post-review-fix) |
| Negative cases hold | ☑ pass | **RED before fix**: merge gate `9 failed, 18 passed` (incl. both real-record tests); move-to-review `7 failed, 4 passed` — the reproduction: one spawn emptied `### In Progress` entirely (T001+T028+T099 all moved) and deleted 3 counters, leaving `['step_count_T040.txt']`. **Mutation controls, each observed RED then reverted**: (1) substring match reinstated → `9 failed, 18 passed`; (2) free-text `\bT(\d{3})\b` scan reinstated → `3 failed, 8 passed`; (3) `isinstance(event, dict)` fail-open guard removed → `1 failed, 26 passed` (`AttributeError: 'list' object has no attribute 'get'`). Post-revert `107 passed`. **AC8** missing/empty/malformed/non-string-summary trace → all fail closed. **AC10** `git diff --name-only main` on `pre_agent_validate_guide.py`, `lib/task_context.py`, `post_write_register_task.py`, `CLAUDE.md` → empty. **Supervisor independently reproduced** mutation (1): substring match reinstated → `9 failed, 18 passed`, matching the implementer's claim exactly, then reverted → `107 passed`. **Stage-4 P1 fix mutated too**: bound fragment reverted to `summary[match.end():]` → `1 failed, 108 passed` (only the new description-leak test), reverted → `109 passed` |
| verify | ☑ pass | pass — full verification command run post-revert from the committed worktree state; 107 unit tests + install/update smoke suite both green |
| Review scope bounded to the change's blast radius | ☑ pass | 3 files modified + 2 new test files. No adjacent-code "improvements"; `find_kanban_section`'s `###` truncation left for T045. **Stage 4 code-review** (Supervisor, 2026-07-30): scope = 3 changed source files + 2 test files; Phase 0.5 entry point `trace_shows_verification` found at `pre_bash_block_unsafe_merge.py:148` ✅ reachable. Result: **0 P0, 1 P1 (found + fixed at `832231d`), 0 P2, 2 P3 accepted** |
| Full smoke suite still green (no regression) | ☑ pass | `bash scripts/smoke-install.sh` → all 15 `[ok]` assertions, `smoke-install.sh: PASS` |
| **UI: Visual regression** | ☐ N/A | Python hooks, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Python hooks, no UI component |
| **UI: Responsiveness** | ☐ N/A | Python hooks, no UI component |

---

## Approach

**A — reuse, don't reinvent.** One-line change in spirit: `from task_context import resolve_task_id`,
same `sys.path` insert idiom T043 established, same fail-open import guard.

**B — establish what the harness actually signals before designing.** Do not assume a completion
event exists. Determine empirically whether `PostToolUse`/`Agent` can distinguish spawn from
completion for a **background** agent. If it cannot, the correct outcome is to **stop moving the row
automatically** and document why — Karpathy Ask-vs-Guess. A board that is confidently wrong is worse
than one the Supervisor updates by hand, and the Supervisor already does update it every task.

**C — match at a command boundary, not anywhere in the string.** The distinction is between a token
*invoked* and a token *mentioned*. Anchor to the start of the command or to a shell separator. Do not
attempt full shell parsing — Simplicity First; a boundary anchor rejects both real false-positive
records from `T043.jsonl` while still accepting every genuine invocation in AC6.

Be honest about the residual limit and write it in the docstring: this still trusts that the recorded
command *ran*, which the trace's `is_error: false` supports but does not prove. The goal is to close
the gap between "a string looked like a test" and "a test command was invoked" — not to achieve
certainty this design cannot deliver.

**Write the tests first** (`tdd`), following `.claude/hooks/tests/` conventions. Use **real records
copied from `memory/event-trace/T043.jsonl`** as fixtures for AC5 — synthetic strings would be a
weaker oracle than the actual data that fooled the gate.

### Outcome as built (filled by the implementer)

**AC3 — no reliable background-completion signal exists.** The harness does expose `SubagentStop`
and `TaskCompleted`, which fire on genuine completion, but their payloads carry only `session_id` /
`transcript_path` / `agent_id` / `agent_type` — no `tool_input`, no spawn prompt, no task
identifier. `SubagentStop` matchers filter on *agent type*, and one type (`common-infrastructure`)
serves many tasks, so the event can say *that* something finished, never *which task*.
`resolve_task_id` has nothing structural to work from. Per the sanctioned outcome,
`post_agent_move_to_review.py` no longer writes to `PROJECT_KANBAN.md` at all; it resolves the task
structurally and prints a stderr reminder. The docstring states this and what re-enabling would
require.

**Consequence to know:** the step-limit counter is no longer reset when a task reaches a gate (that
reset lived inside the buggy spawn-time move, and it deleted *unrelated* tasks' counters). Reset by
hand when a rework cycle needs a fresh budget: `rm .claude/hooks/.state/step_count_Txxx.txt`. This
fired during T044's own implementation. An automatic reset on a *correct* trigger is a follow-up
task, not in this scope.

**AC7 — the mechanism, documented in `.claude/skills/craft-spawn-prompt/SKILL.md`** as spawn-prompt
element 6: every assembled prompt now instructs the sub-agent to run tests as
`CLAUDE_ACTIVE_TASK=Txxx <command>` (or `export` once), because a `Bash` `command` is never
attributed structurally and the merge gate fails closed on a missing record. The block reason in
`pre_bash_block_unsafe_merge.py` also names the export, so an operator hitting the closed gate is
told how to satisfy it.

**Defect C had a layer the guide didn't anticipate:** a trace record's `summary` is the
JSON-serialized `tool_input`, truncated to 300 chars — so the command arrives JSON-escaped and
usually as *invalid* JSON. `extract_command` peels that layer (strict parse, then a single-pass
unescape of the truncated fragment) before shell quoting means anything. Only then: strip quoted
spans (a token inside quotes is data), split on shell separators, peel env assignments and benign
wrappers, match **anchored** at the command head, and consider `Bash` records only. Quote-stripping
is what kills the second real fixture specifically — its runner alternation is a single-quoted regex
literal, and without it the bare `jest` chunk still matches an anchored pattern after splitting on
`|`.

**Mutation-test every negative control** (the T043 standard, now the project norm): after the fix,
break each guard in turn, confirm the relevant test goes RED, revert, and paste that red output into
Evidence. A negative control that has never been observed failing is not evidence.

---

## Edge Case Checklist

- [ ] These hooks fire on **every tool call**; a crash or spurious block breaks all work. Fail open.
- [ ] AC3 may legitimately conclude "no reliable signal exists" — that is a valid, documented outcome,
      not a failure to deliver. Report it to the Supervisor rather than inventing a heuristic.
- [ ] Tightening C without doing AC7 makes the gate fail closed on every honest task. Land both.
- [ ] `git merge` runs from the **main** repo, so the trace file the gate reads is the main repo's —
      not the worktree's. `memory/event-trace/` is gitignored, so a worktree's records never merge.
- [ ] Do not weaken the fail-closed-on-missing-trace contract while tightening the match (AC8).
- [ ] Do not "improve" adjacent hook code (Surgical Changes).

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/post_agent_move_to_review.py` | Use `resolve_task_id`; resolve or disable the spawn-vs-completion move |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Command-boundary matching in `trace_shows_verification` |
| `.claude/hooks/tests/test_merge_gate_evidence.py` | **New** — AC4/AC5/AC6/AC8 with real `T043.jsonl` fixtures |
| `.claude/hooks/tests/test_move_to_review.py` | **New or extended** — AC1/AC2/AC3 |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | Only if AC7's mechanism belongs there — confirm with the Supervisor first |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_agent_validate_guide.py` | Reference implementation; AC10 |
| `.claude/hooks/lib/task_context.py` | Landed by T043; reuse as-is |
| `.claude/hooks/post_write_register_task.py` | Unrelated hook |
| `PROJECT_KANBAN.md` section regex | That is T045 |
| `CLAUDE.md` | Pipeline semantics are not changing |

---

## Test Plan

1. **Red**: write the tests against the current hooks. AC2 and AC5 must fail — that failure *is* the
   reproduction of the reported defects, and its output belongs in Evidence.
2. **Green**: implement; AC1–AC10 pass.
3. **Mutation controls**, each observed RED then reverted, output pasted: reinstate the substring
   match; reinstate the free-text task scan; remove a fail-open guard.
4. **Regression**: full `.claude/hooks/tests/` suite, then `bash scripts/smoke-install.sh`.
5. Paste real command output into every Evidence row — never a claim of output.

---

## Stage 4 Review Findings (Supervisor, 2026-07-30)

**P0**: none. **P2**: none surviving the confidence gate.

**P1 — fixed at `832231d`.** `extract_command`'s truncated-JSON fallback returned
`summary[match.end():]` — everything after `"command": "` — without stopping at the command value's
closing quote, so every sibling field leaked into the string that `invokes_test_runner` then parsed.
A Bash `tool_input` always carries an agent-authored `description`, and once the record exceeds
`post_tool_trace.py`'s 300-char cut the summary stops being valid JSON and this fallback is the only
path. A separator inside that prose (`"inspect the trace records; pytest was already run earlier"`)
promoted the next word to a command head and the gate returned True — defect C reinstated through a
side door, one layer *below* the boundary-matching logic that was written to close it. Fixed by
bounding the fallback to the command value's own body (`COMMAND_VALUE_BODY_PATTERN`, stops at the
first unescaped quote). Two regression tests: the leak case, and a guard that a genuine invocation
which is itself truncated is still accepted (so the fix cannot over-correct into a false negative).

**P3 — accepted, not fixed:**
1. `post_agent_move_to_review.py` is now deliberately inert, so its filename no longer describes it.
   Renaming requires a `settings.json` hook-config change — out of this task's scope. The docstring
   states the situation prominently.
2. `pre_bash_block_unsafe_merge.py` has one blank line before `def main()`; the file uses two
   elsewhere. Cosmetic.

**Follow-ups to schedule (not in this task's scope):**
- Automatic step-counter reset on a *correct* trigger — the reset died with the buggy spawn-time
  move. Manual workaround: `rm .claude/hooks/.state/step_count_Txxx.txt`.
- Renaming `post_agent_move_to_review.py` + its `settings.json` entry.

---

## Stage 4 Security Review (Supervisor, manual — 2026-07-31)

**Verdict: PASS — 0 actionable findings. P0/P1/P2: none. 2 informational (P3).**

Risk=Medium makes this gate mandatory. The built-in `security-review` was **not** used: it diffs the
current branch against main, and this repo is checked out on `main`, so it would have seen an empty
diff and reported a false clean. (This is a *different* failure from the pre-2026-07-23 one — the
`origin/HEAD` fix landed and the built-in does run now; it is simply the wrong instrument when the
branch under review is not the checked-out one.) Reviewed the real diff instead:
`main...feat/hook-lifecycle-evidence`, 3 source files.

- **Authority reduced, not expanded.** `post_agent_move_to_review.py` no longer writes
  `PROJECT_KANBAN.md` and no longer calls `os.remove()` on a path built from untrusted spawn-prompt
  text. The diff strictly *removes* filesystem write authority from a hook firing on every `Agent`
  call.
- **No new execution surface.** No `subprocess`, `eval`, `os.system`, or shell interpolation. All new
  code is regex parsing over a 300-char-bounded `summary`.
- **ReDoS: clear.** `COMMAND_VALUE_BODY_PATTERN` `(?:[^"\\]|\\.)*` has disjoint branch-leading char
  classes → linear. `ENV_ASSIGNMENT_PREFIX` / `BENIGN_COMMAND_PREFIX` nest `+` over `\S*\s+` and
  distinct literal wrappers — also disjoint. `strip_command_prefixes`'s loop provably terminates
  (each pass strictly shortens or returns).

**P3 — informational, accepted:**
1. `QUOTED_SPAN_PATTERN` doesn't track quoting context, so an apostrophe inside a double-quoted
   string (`echo "don't"; pytest`) opens a spurious single-quote span that swallows a following real
   invocation. Fails **closed** — consistent with the gate's contract, same family as the two limits
   the docstring already states.
2. The gate proves *invocation*, not *passing* (`pytest --version` qualifies). Explicitly documented
   as a residual limit; this is an honesty guardrail, not an adversarial boundary.

**Reports** (Stage 4 item 6, both saved 2026-07-31):
- `reports/code-review_feat-hook-lifecycle-evidence_20260731T093433.html` — Risk 10%, Quality 90%, Effort 15%
- `reports/security-review_feat-hook-lifecycle-evidence_20260731T093433.html` — Risk 4%, Quality 100%, Effort 5%

**Stage 4 is complete for T044.** No findings remain open.

---

## Completion Checklist

- [x] Implementation done
- [x] Self-review run (note: a sub-agent has no `Skill` tool — perform code-review/security-review manually and label them as manual)
- [x] Security review — **mandatory, Risk=Medium**. Done manually 2026-07-31 (built-in is the wrong instrument for a branch that is not checked out — see the Security Review section above). PASS, 0 actionable findings
- [x] Tests written AND pass — output pasted into Evidence (Hard-Stop Gate 5)
- [x] Every negative control observed RED, with pasted output
- [x] Report to the Supervisor for `memory/`: whether a reliable background-agent completion signal exists (do not write memory yourself) — **no**, `SubagentStop`/`TaskCompleted` carry no task identity
- [x] Supervisor notified: task ready for Stage 4 review
