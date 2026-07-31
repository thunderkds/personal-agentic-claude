# TASK_GUIDE — T048: The hook test suite fails whenever the active-task channel is armed
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
6. Read in full: `.claude/hooks/lib/task_context.py` (precedence list + `ACTIVE_TASK_FILE`),
   `.claude/hooks/tests/test_task_context.py` (especially `StateFileOverride` and the nine tests
   named below), and `.claude/skills/craft-spawn-prompt/SKILL.md` Element 6

---

## Requirement (Pillar 1 — Adapt the requirement)

T047 (merged 2026-07-31) made trace attribution work by adding a state file,
`.claude/hooks/.state/active_task`, as precedence slot 2 in `resolve_task_id` — above the path-field
slot and the `Agent`-prompt slot. Its production behavior is correct and was verified end-to-end from
`main`: a real `Bash` tool call was attributed to `T047.jsonl` and
`trace_shows_verification('T047')` returned `True`.

**But the test suite is green only while the feature is unused.** Observed immediately after the
merge, from `main`:

```
# with no state file present
$ python3 -m pytest .claude/hooks/tests/ -q
121 passed in 1.13s

# arm the channel exactly as craft-spawn-prompt Element 6 now instructs
$ printf '%s\n%s\n' "T047" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .claude/hooks/.state/active_task

$ python3 -m pytest .claude/hooks/tests/ -q
9 failed, 112 passed in 1.18s

# remove it again
$ python3 -m pytest .claude/hooks/tests/ -q
121 passed in 1.16s
```

The nine failures, all pre-existing T043-era tests:

```
test_env_var_takes_precedence_over_a_guide_path
test_malformed_env_var_values_are_ignored
test_only_path_valued_fields_are_scanned
test_path_fields_are_scanned_in_declared_order
test_agent_prompt_structural_markers_are_recognized
test_agent_prompt_prose_mention_is_not_a_structural_marker
test_prompt_is_only_scanned_for_agent_calls
test_task_ids_are_normalized_to_three_digits_upper_case
test_resolve_never_raises_on_malformed_events
```

**Root cause.** T047 added a `StateFileOverride` context manager that repoints
`task_context.ACTIVE_TASK_FILE` at a throwaway path — but used it **only in its own new tests**. The
nine older tests were written before slot 2 existed and read the module's real `ACTIVE_TASK_FILE`.
They assert what the *lower* precedence slots resolve to, so once a real state file exists, slot 2
short-circuits and returns its task ID for every event, and every one of those assertions breaks.

This is a **test-isolation** defect, not a production-logic defect: slot 2 winning is the designed
behavior. The damage is to the workflow, not the runtime.

**Restated intent**:
> The hook test suite must produce the same result whether or not the active-task channel happens to
> be armed on the machine running it. A test's outcome must not depend on ambient repo state that
> normal operation is *supposed* to create.

**Why P0.** `python3 -m pytest .claude/hooks/tests/ -q` is the verification command in the TASK_GUIDE
template, the thing Hard-Stop Gate 5 requires pasted output from, and part of what the merge gate
looks for. Any agent that follows the current `craft-spawn-prompt` instruction — which T047 makes
mandatory — arms the channel and then cannot get a green suite. The two halves of T047 are in direct
conflict for every future task.

**Why Medium risk.** It touches `task_context.py`'s test surface, the module both `post_tool_trace.py`
and `pre_agent_step_limit.py` depend on. A careless "fix" that neutralizes slot 2 during tests could
mask a real slot-2 regression — the tests must still genuinely cover the state-file path.

**Out of scope**:
- Changing `resolve_task_id`'s precedence order. Slot 2 above the path-field slot is deliberate and
  reviewed; do not reorder it to make tests pass.
- Reverting or weakening the state-file channel — it works and is verified.
- The shared-`.state`-root concurrency limitation across worktrees (separate known gap, see
  `memory/decisions.md` T047 entry).
- `pre_bash_block_unsafe_merge.py` and `pre_agent_validate_guide.py`.

**Requirement Refs**: no `PRD.md`. Traceability:
- **Observed defect, 2026-07-31** — Supervisor, Stage 5 verify of T047 from `main` (transcript above)
- **`tasks/TASK_GUIDE_T047.md`** — the mechanism and the Element 6 instruction that arms it
- **`memory/learnings.md`** — "A guard is only as strong as the layer that feeds it"

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Defect reproduced by the Supervisor on `main` post-merge, with a clean causal control
      (absent → 121 pass, present → 9 fail, removed → 121 pass)
- [x] Root cause confirmed by reading `StateFileOverride`'s usage sites, not inferred from the
      failure names
- [ ] **Agent to confirm**: every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: **T047** (Done, merged 2026-07-31) — introduced slot 2 and `StateFileOverride`.

**Entry point**: `StateFileOverride`
> The isolation helper this task must apply suite-wide. Grep-able and unique.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `python3 -m pytest .claude/hooks/tests/ -q` passes with a valid `.claude/hooks/.state/active_task` present, naming any task ID | Root cause |
| 2 | The same command passes with **no** state file present | No regression |
| 3 | The same command passes with a **malformed** and with a **stale** state file present | Ambient-state independence |
| 4 | Isolation is applied by default to the whole suite, not hand-added per test — a test written tomorrow that forgets it must still be isolated | Restated intent |
| 5 | **Negative — the isolation must not blind the suite**: the tests that genuinely exercise slot 2 still read a real (throwaway) state file and still fail if slot 2 is broken. Prove by mutation: disable slot 2 in `resolve_task_id` and confirm the slot-2 tests go RED | "must still genuinely cover" |
| 6 | **Negative**: precedence order is unchanged — env var still beats the state file, state file still beats path fields, path fields still beat the `Agent` prompt | Out of scope guard |
| 7 | **Negative**: the nine listed tests still assert what they originally asserted; they are isolated, not rewritten to expect the state file's value | Do not paper over |
| 8 | No production behavior change in `resolve_task_id` — the diff to non-test code is empty, or justified in the report if not | Test-isolation defect |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Valid state file present naming `T047` | full suite passes | run the verification command with the file armed |
| 2 | No state file | full suite passes | run it with the file absent |
| 3 | Malformed / stale state file | full suite passes | run it in both states |
| 4 | Slot 2 deliberately broken | slot-2 tests go RED | mutation control (AC5) |
| 5 | Precedence probes for all four slots | unchanged resolution | automated test (AC6) |

### Verification Command (exact, runnable)

```bash
# must pass in BOTH states — running it only one way is what let this defect ship
printf '%s\n%s\n' "T047" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .claude/hooks/.state/active_task
python3 -m pytest .claude/hooks/tests/ -q && \
rm -f .claude/hooks/.state/active_task && \
python3 -m pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output — **both states**] |
| Negative cases hold | ☐ pass / ☐ fail | [AC5, AC6, AC7 — **each mutation observed RED**] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [must literally state "pass" or "fail" in this Notes column] |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | [`scripts/smoke-install.sh`] |
| **UI: Visual regression** | ☐ N/A | Python hooks, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Python hooks, no UI component |
| **UI: Responsiveness** | ☐ N/A | Python hooks, no UI component |

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_task_context.py:StateFileOverride` — the isolation
helper already exists and is correct. This task is about making it the **default** rather than
opt-in. Match its save/restore shape; do not invent a second mechanism.

The judgment call is *how* to apply it suite-wide, and it is yours to make:
- a `conftest.py` autouse fixture (idiomatic pytest, but note the suite is also runnable via its
  `if __name__ == "__main__"` block — check that path still works, it is used by `smoke-install.sh`
  conventions elsewhere in this repo);
- a module-level setup that repoints `ACTIVE_TASK_FILE` at a throwaway path for every test, with the
  slot-2 tests opting *in* to a real one;
- something else you can justify.

Weigh: does it cover a test written tomorrow that forgets to isolate (AC4); does it still let slot-2
tests genuinely fail when slot 2 breaks (AC5); does it work under both `pytest` and direct execution.

**The trap to avoid, stated plainly.** The lazy fix is to neutralize the state file globally and
never read a real one. That turns nine red tests green *and* silently removes the coverage T047 added
— the vacuous-assertion pattern this project has hit four times (T036/T042/T039/T047). AC5 exists
specifically to catch that; run it.

**Write the test first** (`tdd`): a test that arms the channel and asserts the suite is unaffected is
awkward to express from inside the suite, so the honest oracle here is the two-state verification
command above, run and pasted. At minimum, add a test that asserts `resolve_task_id` ignores ambient
state when isolation is active.

**Mutation-test every negative control** (project norm): break each guard, confirm RED, revert, paste.

---

## Edge Case Checklist

- [ ] The suite must pass in **both** states. Running it one way is exactly how this shipped.
- [ ] Do not rewrite the nine tests' expectations to match the state file (AC7) — isolate them.
- [ ] Do not reorder precedence to dodge the problem (out of scope).
- [ ] Keep the direct-execution path (`python3 test_task_context.py`) working, not just `pytest`.
- [ ] Slot-2 coverage must remain able to fail (AC5).
- [ ] These hooks fire on every tool call — no production regressions; the non-test diff should be
      empty or explicitly justified.
- [ ] Note: a state file may be armed on the machine running your tests, because the workflow now
      tells agents to arm it. Assume ambient state, do not assume a clean machine.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/tests/test_task_context.py` | Apply `StateFileOverride` (or equivalent) suite-wide |
| `.claude/hooks/tests/conftest.py` | **New**, only if the chosen approach is an autouse fixture |
| `.claude/hooks/tests/test_merge_gate_evidence.py` | Only if it shares the same ambient-state exposure — check |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/task_context.py` | Production logic is correct; AC8 |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Out of scope |
| `.claude/hooks/pre_agent_validate_guide.py` | Reference implementation |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | The instruction is right; the tests are wrong |

---

## Test Plan

1. **Red**: with the channel armed, run the suite and observe the nine failures. That output is the
   reproduction and belongs in Evidence.
2. **Green**: apply isolation; suite passes armed and unarmed.
3. **AC5 mutation**: break slot 2 in `resolve_task_id`, confirm the slot-2 tests go RED (proving
   isolation did not blind them), revert.
4. **AC6/AC7**: confirm precedence probes unchanged and the nine tests still assert their originals.
5. **Regression**: full suite both ways, then `bash scripts/smoke-install.sh`.
6. Paste real command output into every Evidence row — never a claim of output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review run (a sub-agent has no `Skill` tool — do code-review/security-review manually and
      label them as manual)
- [ ] Security review — **mandatory, Risk=Medium**. Note for the Supervisor: the built-in diffs the
      **checked-out** branch, so run it from the branch under review or do it manually against the
      real `main...<branch>` diff and label it
- [ ] Tests written AND pass — output pasted into Evidence, **from both states** (Hard-Stop Gate 5)
- [ ] Every negative control observed RED, with pasted output
- [ ] Report to the Supervisor for `memory/`: what you chose for suite-wide isolation and why
      (do not write memory yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
