# TASK_GUIDE — T047: CLAUDE_ACTIVE_TASK never reaches the trace hook, so the merge gate fails closed on honest tasks
**Date**: 2026-07-31
**Complexity Level**: C1
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
5. Note the **Complexity Level** above (C1) and apply the matching process from the Complexity matrix
   in `.claude/agents/general-agent-template.md`
6. Read in full: `.claude/hooks/lib/task_context.py`, `.claude/hooks/post_tool_trace.py`,
   `.claude/hooks/pre_bash_block_unsafe_merge.py` (the `trace_shows_verification` half), and
   `.claude/settings.json` (the hook wiring)

---

## Requirement (Pillar 1 — Adapt the requirement)

T044 tightened the merge gate so a trace record counts as verification evidence only when a test
runner was actually *invoked*. It shipped alongside AC7, whose job was to make sure an honest task
still produces such a record: `craft-spawn-prompt` now instructs every agent to

> run every test and verification command with `CLAUDE_ACTIVE_TASK=Txxx` set — e.g.
> `CLAUDE_ACTIVE_TASK=Txxx python3 -m pytest -q`, or `export CLAUDE_ACTIVE_TASK=Txxx` once at the
> start of your shell.

**Neither form works.** Observed on 2026-07-31, running T044's own verification command from `main`
immediately after the merge:

```
$ export CLAUDE_ACTIVE_TASK=T044 && python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
109 passed in 1.18s
smoke-install.sh: PASS
```

The record landed in `_untagged.jsonl`, not `T044.jsonl` (whose mtime stayed at the previous day's
09:36 while `_untagged.jsonl` was written at 10:03):

```
2026-07-31T03:03:10.807899+00:00 | {"command": "export CLAUDE_ACTIVE_TASK=T044 && python3 -m pytest ..."}
```

And the gate agrees:

```
trace_shows_verification('T044') = False
```

**Root cause.** `task_context.py:resolve_task_id` reads `CLAUDE_ACTIVE_TASK` from `os.environ` — the
*hook process's* environment. Hooks are spawned by the Claude Code harness as siblings of the tool
call, so they inherit the harness's environment, not the environment the Bash tool creates for the
command it runs. An `export` or an inline `VAR=val cmd` inside a Bash tool call is scoped to that
command's own subshell and is invisible to the hook by construction. The precedence rule is sound;
the channel it reads from is one the agent cannot write to.

**Restated intent**:
> A task that genuinely runs its tests must end up with a trace record filed under that task, through
> a channel the agent can actually write to from inside a tool call. The merge gate should block
> dishonest evidence, not honest work.

**Why P0.** The gate now fails closed on every honest task, so it will block the next real local
merge. T044 merged only because it went through the GitHub UI, which never invokes the local
`PreToolUse` hook — the gate has still not been exercised end-to-end on a real merge.

**Why Medium risk.** It touches the guardrail subsystem itself. A wrong fix here either re-opens the
"agent claims it ran tests" hole T044 closed, or hard-blocks all merges. It is also a **hub** area:
`task_context.py` feeds both `post_tool_trace.py` and `pre_agent_step_limit.py`.

**Out of scope**:
- Re-litigating T044's boundary-matching logic in `invokes_test_runner` — that half is correct and
  reviewed. This task fixes *attribution reaching the hook*, not *what counts as a test*.
- Re-introducing a scan of the Bash `command` string. T043 removed that deliberately: command text
  can quote arbitrary file content. Whatever channel is chosen must be **structural**, not free text.
- Changing `trace_shows_verification`'s evidence rule, the step-limit value, or the Stage 4/5
  pipeline definition in `CLAUDE.md`.
- T040 (deriving the Token Audit Log from event-trace) — but note it inherits this defect; see
  Dependencies.

**Requirement Refs**: no `PRD.md`. Traceability:
- **Observed defect, 2026-07-31** — Supervisor, Stage 5 verify of T044 from `main` (evidence above)
- **`tasks/TASK_GUIDE_T044.md`** — AC7, and the Edge Case Checklist line "Tightening C without doing
  AC7 makes the gate fail closed on every honest task. Land both."
- **`memory/learnings.md`** — "A guard is only as strong as the layer that feeds it"

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Defect reproduced by the Supervisor from `main` at `de120da`, with the trace file mtimes and
      the `trace_shows_verification` return value recorded above
- [x] Root cause confirmed by reading `resolve_task_id`'s `os.environ` read against the harness's
      hook-spawning model — not inferred from the symptom alone
- [ ] **Agent to confirm**: every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: **T044** (Done, merged 2026-07-31 at `de120da`) — provides the tightened gate and the
AC7 instruction this task repairs.

> Note for planning, not a blocker: **T040** depends on trace attribution being correct for `Bash`
> calls. It should not start until this task lands, or it will build a token-audit window on records
> that are silently all `_untagged`.

**Entry point**: `resolve_task_id`
> The attribution function in `.claude/hooks/lib/task_context.py` whose precedence list this task
> extends or re-channels. Grep-able and unique.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A test command issued the way an agent actually issues one — as a Bash tool call, from a tool-call-scoped shell — results in a trace record filed under that task, not in `_untagged.jsonl` | Root cause |
| 2 | `trace_shows_verification('<that task>')` returns True after such a run | Restated intent |
| 3 | The chosen channel is **structural** — it must not be derived from scanning the Bash `command` string or any other free text | Out of scope / T043 |
| 4 | **Negative**: a task that ran no test still gets no qualifying record — the gate must still fail closed. Prove it with a task ID that has no trace file and one whose only records are inspection commands | T044's whole purpose |
| 5 | **Negative**: the two real `T043.jsonl` inspection records that fooled the pre-T044 gate are still rejected — this task must not regress T044's fix | Out of scope guard |
| 6 | `resolve_task_id`'s existing precedence (validated env → guide path in a path field → `Agent` spawn prompt → unattributed) still behaves identically for every case T043's tests cover | T043 preserved |
| 7 | Whatever the new channel is, it is **documented where the agent will actually read it** — `craft-spawn-prompt`'s Element 6 text must be corrected, since it currently prescribes a mechanism that does nothing | "Already covered" must mean reaches-the-context |
| 8 | **Negative**: all hooks preserve fail-open on malformed stdin and on a missing/corrupt channel — exit 0, no traceback | These fire on every tool call |
| 9 | **Negative**: `pre_agent_validate_guide.py` and `invokes_test_runner`'s matching logic remain untouched | Reference impl / T044 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A test runner invoked through the real hook path for task Txxx | a record appears in `memory/event-trace/Txxx.jsonl` | automated test + one real end-to-end run |
| 2 | That same state | `trace_shows_verification('Txxx')` is True | automated test |
| 3 | A task with no trace file, and a task whose records are only inspection commands | gate returns False in both cases | automated test (AC4) |
| 4 | The two real `T043.jsonl` inspection records | still rejected | automated test (AC5) |
| 5 | Malformed stdin / missing channel file | exit 0, silent, no traceback | automated test (AC8) |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
```

> Deliberately written **without** a `CLAUDE_ACTIVE_TASK=` prefix — prefixing it is the thing that
> does not work, and this guide must not repeat T044's mistake of documenting an inert mechanism.
>
> **T047 landed** (with a Stage 4 fix: the state-file path must be an **absolute path to the main
> checkout**, not a bare relative path or `$CLAUDE_PROJECT_DIR` — that var is real inside a hook's own
> spawned process but empty inside a `Bash` tool call's own shell, confirmed empirically; a relative
> path resolves against your cwd, which for a worktree agent is the worktree, not the checkout the
> live hook reads). The correct invocation, when a trace record filed under this task is required
> (i.e. running the command above as evidence toward the merge gate), is to write the active-task
> state file first, using the real absolute path of the main checkout, then run the command exactly
> as shown above — unprefixed:
>
> ```bash
> MAIN_CHECKOUT="/absolute/path/to/main/checkout"   # substitute the real path; do not use a variable
> mkdir -p "$MAIN_CHECKOUT/.claude/hooks/.state" && printf '%s\n%s\n' "T047" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$MAIN_CHECKOUT/.claude/hooks/.state/active_task"
> python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
> ```
>
> See `.claude/hooks/lib/task_context.py` (precedence slot 2, `_resolve_root`) and
> `craft-spawn-prompt`'s Element 6 for why. `CLAUDE_ACTIVE_TASK=Txxx` still works, but only when set
> in the process that launches the whole session — never inside a `Bash` tool call.

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ✅ pass | `.claude/hooks/tests/test_task_context.py` — 16 new tests added for T047 (8 unit-level `StateFileOverride` cases, 2 real-subprocess end-to-end cases, 1 `_load_merge_gate_module`/gate-integration case, plus the Stage-4 P1 regression guard `test_state_file_resolves_off_claude_project_dir_not_the_executing_copy`). `python3 -m pytest .claude/hooks/tests/ -q` → `120 passed in ~1.1s` (was 109 pre-T047). |
| Verification command run | ✅ pass | `python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh` → `120 passed in 1.07s` then `smoke-install.sh: PASS`, run from inside the T047 worktree with the corrected (absolute-path) state-file instruction. |
| Negative cases hold | ✅ pass | AC4/AC5/AC8/AC9 covered by pre-existing suite (unchanged, still green) plus new negative controls `test_missing_state_file_falls_through_to_next_slot`, `test_malformed_state_file_content_is_ignored_not_trusted`, `test_stale_state_file_is_rejected`, `test_state_file_corrupt_timestamp_degrades_to_absent`. **Mutation-tested, each observed RED then reverted**: (1) disabling the staleness check → `test_stale_state_file_is_rejected` FAILED (`assert 'T047' is None`); (2) removing task-id format validation → `test_malformed_state_file_content_is_ignored_not_trusted` FAILED; (3) reordering precedence so the state file beat env → `test_env_var_still_wins_over_state_file` FAILED; (4) **Stage-4 P1 fix** — reverting `_resolve_root()` to always fall back to `__file__` arithmetic (the original defect) → `test_state_file_resolves_off_claude_project_dir_not_the_executing_copy` FAILED (`stdout='None'`, expected `'T047'`). All four reverted; suite back to 120 passed each time. |
| verify | ✅ pass | Real end-to-end run **within the worktree's own root** (agent write path and hook read path shared a single directory tree in this manual check — see caveat below): wrote `.claude/hooks/.state/active_task` with a plain shell redirect (no `CLAUDE_ACTIVE_TASK` anywhere), piped a real `Bash` event with no env prefix into the real `post_tool_trace.py`, got `memory/event-trace/T900.jsonl` (not `_untagged.jsonl`), and the real `pre_bash_block_unsafe_merge.py:trace_shows_verification("T900")` returned `True`. **This validated the state-file mechanism only within one shared root — it did not, by itself, cross the worktree→main-checkout boundary the live hook actually crosses; that boundary is what the Stage-4 P1 fix (`_resolve_root` reading `$CLAUDE_PROJECT_DIR`) addresses, and it is covered separately by the new regression test above** (`test_state_file_resolves_off_claude_project_dir_not_the_executing_copy`, run as a real subprocess against a genuinely different `__file__`-directory and `$CLAUDE_PROJECT_DIR`, not a shared-root shape). |
| Review scope bounded to the change's blast radius | ✅ pass | Diff touches only `.claude/hooks/lib/task_context.py`, `.claude/hooks/tests/test_task_context.py`, `.claude/skills/craft-spawn-prompt/SKILL.md`, `tasks/TASK_GUIDE_T047.md`. `git diff --stat -- .claude/hooks/pre_bash_block_unsafe_merge.py .claude/hooks/pre_agent_validate_guide.py` is empty (AC9 held). |
| Full smoke suite still green (no regression) | ✅ pass | `bash scripts/smoke-install.sh` → `smoke-install.sh: PASS`, all artifact checks `[ok]`. |
| **UI: Visual regression** | ☐ N/A | Python hooks, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Python hooks, no UI component |
| **UI: Responsiveness** | ☐ N/A | Python hooks, no UI component |

---

## Approach

**Pattern reference**: `.claude/hooks/lib/task_context.py` — the precedence-list shape, the
normalize-and-validate-before-trusting rule for any externally-supplied value, and the never-raises
contract. Whatever channel is added should slot into that precedence list in the same style, not
bypass it.

**Establish the channel empirically before designing — this is the whole task.** T044's AC7 failed
because a plausible mechanism was documented without ever being observed working end-to-end. Do not
repeat that. Before choosing, write a throwaway probe that proves which channels a hook process can
actually observe from inside a Bash tool call, and record what you find.

Candidate directions, **none pre-selected** — this is an implementation decision for you to make and
justify, not one the Supervisor has made:

1. **A state file the Supervisor/agent writes** — e.g. `.claude/hooks/.state/active_task`, added to
   `resolve_task_id`'s precedence above or below the env var. Structural, writable from a tool call,
   survives across processes. Consider: staleness (who clears it, and what happens when a task ends),
   and concurrent worktrees sharing one repo.
2. **`settings.json` env configuration**, if the harness supports injecting env into hook processes.
   Verify this rather than assuming — and note it may be static, which would not vary per task.
3. **Deriving the task from something already structural in the payload or the cwd** — e.g. a
   worktree path that encodes the task. Note the Supervisor often runs from `main`, not a worktree,
   so check this covers the real cases before relying on it.

Weigh them on: does it work from a tool call (non-negotiable), does it stay structural (AC3), can it
go stale and silently mis-attribute (the T043 defect class), and how much machinery it adds
(Simplicity First — a one-line file read beats a config mechanism).

If the honest conclusion is that **no channel can carry per-task identity to the hook**, that is a
valid, documented outcome — say so and report it rather than inventing a heuristic, exactly as T044's
AC3 correctly did for the completion signal. In that case the follow-on question is whether the
gate's evidence should come from somewhere other than the trace at all; raise it, do not decide it
alone.

**Write the tests first** (`tdd`). Note the trap that let this defect ship: T044's tests all pass
because they exercise `resolve_task_id` with a **patched environment**, which never crosses the real
harness→hook process boundary where the failure lives. A unit test that patches the channel proves
the precedence logic, not that the channel works. **At least one acceptance check must be a real
end-to-end run** — issue a test command the way an agent does, then inspect the actual trace file.

**Mutation-test every negative control** (project norm since T043): break each guard in turn, confirm
the relevant test goes RED, revert, and paste that red output into Evidence.

---

## Edge Case Checklist

- [ ] These hooks fire on **every tool call**; a crash or spurious block breaks all work. Fail open.
- [ ] Do not re-open T044's hole. AC5 is the specific regression guard — run it.
- [ ] A stale channel value is worse than none: it files records under the *wrong* task, which is the
      exact defect class T043 existed to remove. Design for clearing it, and test the stale case.
- [ ] Multiple worktrees share one repo root. Check whether the chosen channel collides across
      concurrent tasks.
- [ ] `memory/event-trace/` is gitignored, so a worktree's records never merge to main, and
      `git merge` runs from the main repo and reads the **main repo's** trace file.
- [ ] A unit test that patches the channel cannot prove the channel works — see Approach.
- [ ] Do not "improve" adjacent hook code (Surgical Changes).

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/task_context.py` | Add the chosen channel to `resolve_task_id`'s precedence |
| `.claude/hooks/tests/test_task_context.py` | Extend — new channel, precedence, stale case |
| `.claude/hooks/tests/test_merge_gate_evidence.py` | Extend — AC2/AC4/AC5 end-to-end |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | Correct Element 6, which currently prescribes an inert mechanism (AC7) |
| `.claude/settings.json` | Only if the chosen direction needs hook wiring — confirm with the Supervisor first |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_agent_validate_guide.py` | Reference implementation; AC9 |
| `invokes_test_runner` / `extract_command` in `pre_bash_block_unsafe_merge.py` | T044's reviewed matching logic; AC9 |
| `CLAUDE.md` | Pipeline semantics are not changing |
| `PROJECT_KANBAN.md` section regex | That is T045 |

---

## Test Plan

1. **Probe**: prove empirically which channels the hook process can observe from a Bash tool call.
   Record the result — it is the finding this task turns on.
2. **Red**: write tests against current behavior. AC1 and AC2 must fail; that failure is the
   reproduction, and its output belongs in Evidence.
3. **Green**: implement; AC1–AC9 pass.
4. **End-to-end**: run a real test command as a Bash tool call, then inspect the real trace file and
   `trace_shows_verification`. A passing unit suite is not sufficient evidence for this task.
5. **Mutation controls**, each observed RED then reverted, output pasted.
6. **Regression**: full `.claude/hooks/tests/` suite, then `bash scripts/smoke-install.sh`.
7. Paste real command output into every Evidence row — never a claim of output.

---

## Completion Checklist

- [ ] Probe result recorded (which channels a hook can actually observe)
- [ ] Implementation done
- [ ] Self-review run (note: a sub-agent has no `Skill` tool — perform code-review/security-review
      manually and label them as manual)
- [ ] Security review — **mandatory, Risk=Medium**. Note for the Supervisor: the built-in diffs the
      **checked-out** branch, so run it from the branch under review or do it manually against the
      real `main...<branch>` diff and label it
- [ ] Tests written AND pass — output pasted into Evidence (Hard-Stop Gate 5)
- [ ] At least one **real end-to-end** run, not only unit tests
- [ ] Every negative control observed RED, with pasted output
- [ ] Report to the Supervisor for `memory/`: what the probe found about hook-observable channels
      (do not write memory yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
