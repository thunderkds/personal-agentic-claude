# TASK_GUIDE — T081: Two provably false rows in the README hook table
**Date**: 2026-08-18
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. C0 task, single file — `memory/codebase-map.md` not required

---

## Requirement (Pillar 1 — Adapt the requirement)

Salvaged from T074, which was closed 2026-08-18 as unnecessary. T074 bundled a `SessionStart`
hook-wiring validator (closed — all 8 project and 22 machine-level hook commands resolve, and the
hooks were observed firing throughout the 2026-08-18 session) with two stale README rows. The
validator half is dead; **this half is repo-local, verified against source, and still true.**

Both rows were re-verified by the Supervisor on 2026-08-18 directly against the hook files, not
inherited from T074's row:

| `README.md` claims | Source says |
|---|---|
| L415: `post_agent_move_to_review.py` — "Moves task `In Progress → Ready for Review` after agent finishes; also resets that task's step-limit counter" | The file contains **0 write operations**. Its own docstring, line 6: *"It only prints a reminder. It is deliberately inert as a writer"* — deliberate since T044. |
| L416: `pre_agent_step_limit.py` — "blocks further calls past `CLAUDE_STEP_LIMIT` (default 40)" | `STEP_LIMIT = int(os.environ.get("CLAUDE_STEP_LIMIT", "90"))` — default **90** (T057), keyed `<session>_<task>` with a 6h TTL (T056), and self-clearing, so it interrupts rather than halts. |

**Restated intent**:
> Make the two README hook-table rows state what the hooks actually do.

**Why this is worth a task at all**: the first row is not merely stale, it is *actively misleading*.
The vanished counter reset is the recorded root cause of the step-limit lockouts in
`memory/learnings.md` ("Guards that lock out the role meant to release them", 4 incidents). Anyone
debugging one and consulting the README is told a reset happens that has not happened since T044.

**Out of scope**:
- The `SessionStart` validator, `scripts/hook-doctor.sh`, or any hook-wiring check — closed with T074
- Any change to the hooks themselves. The **code is correct**; the documentation is wrong. Do not
  "fix" `post_agent_move_to_review.py` to match the README — its inertness is deliberate and its
  docstring spends 25 lines explaining why.
- Auditing the rest of the hook table beyond the check in AC3

**Requirement Refs**: `None — salvaged from a closed task, verified independently.`

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-08-18)
- [x] Both claims verified against source, not against T074's row
- [x] Every AC traces to the Requirement
- [x] Requirement Refs: `None` recorded with a reason

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `README.md` → `## Pipeline Enforcement Hooks`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `README.md`'s `post_agent_move_to_review.py` row states that the hook **only prints a reminder** and is deliberately inert as a writer, and no longer claims it moves the Kanban row or resets the step counter | row 1 of the table above |
| 2 | `README.md`'s `pre_agent_step_limit.py` row states the default as **90**, not 40 | row 2 |
| 3 | The `Advisory vs. blocking` sentence at `README.md:422` is checked; if it repeats either corrected claim it is corrected too, otherwise its correctness is recorded in the review file | "the two rows plus L422 if it repeats either claim" |
| 4 | No file outside `README.md` is modified | negative condition — the code is correct, only the docs are wrong |
| 5 | The corrected rows name the reason the behaviour is what it is (inert since T044; default raised to 90 by T057), so a future reader does not "restore" the old wording as a fix | the actively-misleading problem |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|---|---|---|
| 1 | `grep -c "default 40" README.md` | `0` | command output pasted |
| 2 | `grep "resets that task's step-limit counter" README.md` | no match | command output pasted |
| 3 | The default stated in README vs. the default in the source | identical (`90`) | both greps pasted side by side |
| 4 | Full hook suite | `649 passed` — unchanged; this task touches no code | automated test |
| 5 | **Mutation control** — temporarily restore the wording `default 40` in README, then re-run SC1 | SC1 returns `1`, i.e. the check can actually detect the stale text. Revert after observing. | observed, output pasted |

> SC5 is mandatory and is the whole verification here: SC1/SC2 are `grep` checks for *absence*, and
> an absence check whose pattern is wrong passes trivially against any file. This repo has recorded
> that failure eight times. Prove the pattern matches the real stale text before trusting that its
> disappearance means anything.

### Verification Command

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  grep -c "default 40" README.md ; \
  grep -c "resets that task's step-limit counter" README.md ; \
  grep -n 'CLAUDE_STEP_LIMIT", "' .claude/hooks/pre_agent_step_limit.py ; \
  python3 -m pytest .claude/hooks/tests/ -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T081.md`.

---

## UI / Design Acceptance Criteria

Documentation-only, no UI component. All three UI Evidence rows ☐ N/A — no rendered surface, no
design tokens, no viewports.

---

## Approach

**Pattern reference**: `README.md`'s existing hook-table rows — match their register exactly: one
line, the hook name, its event, and what it does, with any non-obvious behaviour stated in the same
sentence rather than a footnote.

**Vital slice**: the `post_agent_move_to_review.py` row. It is the one that actively misleads during
an incident; the step-limit number is merely wrong.

**Cut list**:
- Auditing the remaining hook-table rows. Two were verified false; the rest are unexamined, and
  widening this into a full table audit turns a C0 into a C2. If the reviewer notices another
  suspect row, record it for a follow-up rather than fixing it here.

---

## Edge Case Checklist

- [ ] The step-limit row also mentions blocking behaviour — the hook is **self-clearing** (T057), so it interrupts rather than halts. Do not describe it as a hard block.
- [ ] `README.md:422` names `pre_agent_step_limit.py` among hooks that "can actually block a tool call" — decide whether that remains accurate given self-clearing, and say so explicitly either way (AC3)
- [ ] `CLAUDE_LEGACY.md` mirrors README content per the recorded sync policy — check whether it carries either stale claim, and if so report it rather than editing (out of scope, but a silent divergence is worth flagging)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `README.md` | AC1, AC2, AC3, AC5 — two hook-table rows and possibly L422 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/post_agent_move_to_review.py` | The code is correct. Its inertness is deliberate and documented; "fixing" it to match the README would reintroduce the defect that caused the recorded step-limit lockouts. |
| `.claude/hooks/pre_agent_step_limit.py` | The default of 90 is correct (T057) |
| `CLAUDE_LEGACY.md` | Flag divergence, do not edit — see Edge Case Checklist |

---

## Test Plan

1. Run SC5's mutation control **first**, against the current README, to prove SC1's grep pattern
   actually matches the stale text that is there right now.
2. Correct the two rows; evaluate L422.
3. Run the verification command; paste SC1–SC4 output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: ☐ N/A — Low risk, documentation-only, no code path changed
- [ ] Tests: no new test; covered by the existing suite plus SC1–SC3 greps. Record that reasoning in the Evidence table rather than leaving the Hard-Stop-Gate-5 row blank.
- [ ] Mutation control SC5 observed and pasted
- [ ] Supervisor notified: ready for Stage 4 review
