# TASK_GUIDE — T058: diagnose Phase 4 — turn "instrument" from a preference into an evidence loop
**Date**: 2026-08-06
**Complexity Level**: C1
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
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. C1 single-file task — `memory/codebase-map.md` read is not required

---

## Requirement (Pillar 1 — Adapt the requirement)

Original user request, verbatim across the session:

> "with the bug fix, I think we missing the skill for debugging the issues"

> "for the debug, I just care about how can the agent depend on the data to proceduce, we will focus on the logs, insert logs, trace them, and analyze to focus on the bugs"

> "agent should logs for debug purpose the event trace is served for another purpose"

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> A sub-agent running `diagnose` must locate a bug from evidence it collects by instrumenting the
> program — inserting its own debug log statements, running the Phase 1 feedback loop, reading the
> actual emitted values, and narrowing the suspect range against them — rather than from reasoning
> alone. `diagnose` Phase 4 currently states a *preference* between instrument types but gives no
> procedure for where to place the first probe, how to narrow after reading its output, or when to
> stop. This task replaces that preference with a concrete, followable loop.

**Out of scope** (what this task explicitly does NOT do):
- Any Complexity-gating of `diagnose` phases (the C0–C3 ladder explored earlier this session). Dropped by user redirect, not deferred. `diagnose` line 8's `"Skip phases only when explicitly justified"` clause stays exactly as-is.
- Any change to `memory/event-trace/*.jsonl` or the hooks that write it. User ruled this out explicitly: the event-trace records *tool calls*, serves the merge gate and the token-audit generator, and cannot answer "what was this variable at that point." Debug logs are the agent's own, added and removed inside the task.
- Any new skill, and any split of `diagnose` into hard-bug/easy-bug variants. Rejected during brainstorming: the project has exactly one scaling control (the C0–C3 matrix in `general-agent-template.md`) and a second skill would compete with it.
- Any change to `.claude/skills/bugfix/SKILL.md`. Its Step 4 already wires `diagnose` in as mandatory first action; nothing about that wiring changes.
- Adding `diagnose` to the trigger-threshold table in `general-agent-template.md`. That was part of the dropped gating direction.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):
- None — this is framework-internal skill authoring, not a PRD-tracked product requirement. Traceability runs to the verbatim user requests quoted above instead.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — confirmed by the user on 2026-08-06 ("agent should logs for debug purpose the event trace is served for another purpose" locked the last open question)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — `grill-with-docs` run this session; the one term needing sharpening was *debug log* vs *event trace*, resolved by the user and recorded under Out of scope
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist — N/A, see above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `### Phase 4 — Instrument`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/skills/diagnose/SKILL.md` retains a section whose heading is exactly `### Phase 4 — Instrument`, and its body is a numbered/bulleted procedure of at least 5 discrete steps, not a single preference sentence | "how can the agent depend on the data to proceduce" |
| 2 | The Phase 4 body instructs placing the first probes at **boundaries** (function entry/exit, module or process edges) before narrowing inward | "insert logs, trace them" |
| 3 | The Phase 4 body instructs logging **actual values** and comparing each against a stated expected value | "analyze to focus on the bugs" |
| 4 | The Phase 4 body states an explicit narrowing rule: the boundary showing correct-input/incorrect-output localises the defect, then halve the remaining range and repeat | "focus on the bugs" |
| 5 | The Phase 4 body states an explicit stop condition (a single function/expression isolated, or the loop's failing value explained) | "focus on the bugs" |
| 6 | The `[DEBUG-xxxx]` unique-prefix tagging requirement survives the rewrite, and Phase 6's `grep`-the-prefix cleanup checkbox still refers to it | Surgical Changes — existing cleanup contract must not break |
| 7 | Phase 4 explicitly states that debug logs are the agent's own temporary instrumentation and must NOT be written to `memory/event-trace/` | "the event trace is served for another purpose" |
| 8 | The existing Stuck-Loop Checkpoint's dependency on Phase 4 still holds: the rewritten Phase 4 still produces a per-hypothesis confirmed/disproven outcome that the checkpoint can count | Existing T052 contract must not silently break |
| 9 | `diagnose/SKILL.md` line 8's `"Skip phases only when explicitly justified"` sentence is byte-identical to its pre-change form (negative criterion — proves the dropped gating direction was not smuggled in) | Out of scope |
| 10 | Every other `### Phase N` heading in the file is byte-identical to its pre-change form (negative criterion — scope lock) | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The shipped `.claude/skills/diagnose/SKILL.md` | A `### Phase 4 — Instrument` section parses out with ≥5 procedure steps | automated test |
| 2 | The shipped Phase 4 body | Contains a boundary-first instruction, an expected-vs-actual instruction, a halving/narrowing rule, and a stop condition | automated test |
| 3 | The shipped Phase 4 body | Contains `[DEBUG-` and an explicit prohibition naming `event-trace` | automated test |
| 4 | The shipped file, line 8 | Byte-identical to the pre-change sentence (negative case — a violation must FAIL the suite) | automated test |
| 5 | The shipped file's `### Phase` heading list | Exactly the pre-change set, unchanged in text and order (negative case) | automated test |
| 6 | A Phase 4 body rewritten as prose with no enumerated steps (mutation) | Test for SC1 goes RED | mutation check, observed then reverted |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_diagnose_phase4_procedure.py -q && \
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [SC4/SC5 must be observed RED under mutation, then reverted] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | Pure skill-instruction text change, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Pure skill-instruction text change, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | Pure skill-instruction text change, no UI component |

---

## Demonstration

> Non-executable change (skill-instruction text), so BEFORE is the verbatim prior content.

**BEFORE**: `.claude/skills/diagnose/SKILL.md` lines 27–28, captured 2026-08-06 before any implementation commit exists:

```
### Phase 4 — Instrument
Each probe maps to a specific prediction. Change one variable at a time. Prefer debugger/REPL > targeted boundary logs > never "log everything and grep". Tag logs `[DEBUG-xxxx]`. For perf: measure a baseline first (profiler/timing/query plan), then bisect.
```

That is the entire section: one heading and one line. It ranks instrument types by preference and never says where to place a probe, how to narrow after reading one, or when to stop.

**AFTER**: [verbatim excerpt of the rewritten `### Phase 4 — Instrument` section]

**DELTA**: [one sentence — what a sub-agent running `diagnose` can now follow that it could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T058.jsonl`, never the implementing agent alone]

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_bugfix_evidence_parity.py` — structural assertions over a SKILL.md's markdown (section extraction by heading, then content assertions on the extracted block), including negative cases that must be observed RED. Imitate its section-extraction helper rather than writing new regex from scratch.

Rewrite `### Phase 4 — Instrument` as an ordered procedure. The shape agreed with the user:

1. Place the first probes at **boundaries** — function entry/exit, module edges, process edges — not adjacent to where the bug is suspected. A probe next to the suspicion only confirms the suspicion.
2. Log **actual values**, and state the expected value alongside each. A log line with no expectation attached cannot disprove anything.
3. Run the Phase 1 feedback loop, read the emitted values, and find the boundary where **input is correct and output is not**. The defect is between that boundary and the previous good one.
4. Halve the remaining range with the next probe and repeat.
5. Stop when a single function or expression is isolated, or when the loop's failing value is fully explained.

Constraints that must survive the rewrite:
- One variable at a time (existing Surgical Changes override at line 13).
- Every probe tagged `[DEBUG-xxxx]` with a unique prefix so Phase 6 cleanup is one `grep`.
- Each probe still maps to a specific prediction, so the Stuck-Loop Checkpoint can count confirmed/disproven per hypothesis.
- The perf sub-case (baseline first via profiler/timing/query plan, then bisect) is retained.
- Debug logs are temporary and agent-owned; they must not be routed to `memory/event-trace/`.

The section will grow from 2 lines to roughly 12–15. `diagnose` is currently 59 lines, well under the 150-line slim-skills threshold, so the growth needs no offsetting trim.

---

## Edge Case Checklist

- [ ] The rewrite makes Phase 4 longer than every other phase and unbalances the skill — keep it tight; procedure steps, not prose paragraphs
- [ ] "Boundary-first" is misread as "log every boundary in the program" — the skill already forbids "log everything and grep"; that prohibition must survive explicitly
- [ ] A bug with no reachable seam for a log statement (compiled dependency, third-party binary) — the procedure must not dead-end; fall back to the Phase 1 ladder's differential/bisection loops
- [ ] Non-deterministic bugs where a probe's own timing changes the outcome (heisenbug) — Phase 1 already covers raising reproduction rate; Phase 4 must not contradict it
- [ ] The `[DEBUG-` literal appears in the test as a substring assertion and would pass on a mere mention in prose — assert it inside the extracted Phase 4 block, not file-wide
- [ ] Section-extraction regex truncating early on a nested heading — this repo has 6 recorded defects in that exact family (`find_kanban_section`, `extract`, register-hook metadata); anchor the terminator with `^###` under `re.MULTILINE`
- [ ] Writing this guide or the new Phase 4 text with a heredoc containing a guarded command trips the merge gate's `BLOCKED_PATTERNS` prose scan — use the Write tool for file content

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/diagnose/SKILL.md` | Rewrite the `### Phase 4 — Instrument` section only (currently lines 27–28) into a ≥5-step procedure. No other line changes. |
| `.claude/hooks/tests/test_diagnose_phase4_procedure.py` | New. Structural tests for AC1–AC10, modelled on `test_bugfix_evidence_parity.py`. |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/bugfix/SKILL.md` | Step 4's `diagnose` wiring is already correct and unconditional; out of scope |
| `.claude/agents/general-agent-template.md` | The trigger-table row was part of the dropped Complexity-gating direction |
| `.claude/hooks/post_tool_trace.py` and anything under `memory/event-trace/` | User ruled the event-trace out explicitly; it serves the merge gate and token-audit generator |
| `.claude/skills/diagnose/SKILL.md` line 8 and all `### Phase` headings other than Phase 4 | Scope lock, asserted by AC9/AC10 |

---

## Test Plan

New file `.claude/hooks/tests/test_diagnose_phase4_procedure.py`, following `test_bugfix_evidence_parity.py`:

1. A section-extraction helper reading the real shipped `.claude/skills/diagnose/SKILL.md`, terminating on `^###` under `re.MULTILINE` (see Edge Case Checklist — this repo has a recorded defect family here).
2. AC1 — extracted Phase 4 block contains ≥5 enumerated steps.
3. AC2–AC5 — one test each for the boundary-first, expected-vs-actual, narrowing, and stop-condition instructions.
4. AC6/AC7 — `[DEBUG-` present inside the extracted block; an explicit `event-trace` prohibition present inside the extracted block.
5. AC9 — line 8's sentence asserted byte-identical.
6. AC10 — the full ordered list of `### Phase` headings asserted against the known pre-change list.
7. Mutation controls, each observed RED then reverted, per SC6 and the Negative-cases Evidence row: (a) collapse the Phase 4 body to a single prose sentence → AC1 test RED; (b) alter line 8 → AC9 test RED; (c) rename a non-Phase-4 heading → AC10 test RED.

Then the full hook suite (`188 passed` at HEAD, `dbef7ca`) must remain green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — required)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working
- [ ] `docs/legacy/` updated (N/A — not legacy mode)
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
