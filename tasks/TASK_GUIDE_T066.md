# TASK_GUIDE — T066: De-duplicate the startup read set, in the direction the channel allows
**Date**: 2026-08-09
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Apply the Complexity matrix in `.claude/agents/general-agent-template.md`
6. **C2 task**: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Registered as "de-duplicate the startup read set": `CLAUDE.md` (3,819 tok),
`general-agent-template.md` (1,811 tok) and the per-role agent guides (730–1,670 tok) overlap, and
all ship downstream. The row ranks it last deliberately and states the constraint Stage 2 must
resolve: **T039 already harvested most of this once**, and the recorded learning *"already covered
must mean reaches-the-context"* says some overlap is deliberate redundancy across *different* context
windows — collapsing it would be the exact error T041 was written to fix.

**Stage 2 measured which is which. The answer inverts the obvious direction of the fix.**

Two facts settle it:

1. **`CLAUDE.md` never reaches a sub-agent at all.** It is not in the agent startup read list
   (`general-agent-template.md` step 1–6 names `PROJECT_SPEC.md`, `memory/MEMORY.md`, the TASK_GUIDE,
   the role guide, and optionally `memory/codebase-map.md`). Its 3,819 tokens are Supervisor-context
   only, and per DDR-0004 that context is ~97% cache read. **So `CLAUDE.md` ↔ agent-guide overlap is
   cross-context redundancy and must NOT be collapsed** — that is precisely T041's fix, which inlined
   a compact Karpathy table into `general-agent-template.md` *because* `CLAUDE.md` never arrives.

2. **The role guide is guaranteed in context; the template is not.** The harness auto-loads
   `.claude/agents/<name>.md` as the agent's system prompt, so a role guide is *always* present.
   `general-agent-template.md` is present only if the agent chooses to read it — the event trace
   shows 7 `Read` records across 3 task buckets, and per T063 those counts are a **floor, not a
   rate** (the active-task pointer arms after the startup reads, so most land in `_untagged`).

Measured duplication between the template and the four role guides, for the sections that appear in
both:

| Section | template | c-infra | backend | frontend | qa |
|---|---|---|---|---|---|
| Mandatory Startup Sequence | 1,019 | 242 | 453 | 453 | 433 |
| Communication Protocol | 338 | **0** | 338 | 338 | 399 |
| Available Skills | 973 | 481 | 1,137 | 1,038 | 1,034 |
| Complexity | 1,689 | **0** | 1,435 | 1,340 | 1,333 |

10,454 chars (~2,613 tok) of the role guides restate sections the template also carries. Per spawn
the pair costs 2,541 tok (c-infra) to 3,482 tok (backend).

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Remove the duplication that lands inside a *single* agent context, and do it by consolidating into
> the channel that is guaranteed to arrive — the role guide — rather than into the template, which an
> agent may never open. Leave every cross-context redundancy exactly as it is.

**Out of scope**:
- **Touching `CLAUDE.md`, or collapsing any `CLAUDE.md` ↔ agent-guide overlap.** Fact 1 above.
  AC9 pins `CLAUDE.md` byte-identical.
- **Removing the compact Karpathy table or the Search-Before-You-Build ladder from the agent side.**
  That is T041's fix and the direct instantiation of "already covered must reach the context".
- `PROJECT_SPEC.md` staleness — the row states this explicitly: it does not ship, so it is
  instance-only cleanup.
- Any change to what the *Supervisor* reads.

**Requirement Refs**: none — harness-internal, no `PRD.md` FR/NFR.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed against the row's own stated constraint
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A, stated rather than left blank

---

## Dependencies & Reachability

**Depends on**: `None` — T065 merged; the memory channel is settled, so what reaches an agent is now
documented accurately.

**Entry point**: `Mandatory Startup Sequence` — the literal, grep-able heading present in all five
agent files.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | **Nothing is removed from a role guide unless it is present in all four role guides afterwards.** The consolidation direction is *into* the guaranteed channel. Assert per shared section, per role guide | Fact 2 |
| 2 | `Communication Protocol` and the Complexity guidance now exist in `common-infrastructure.md`, which currently has **neither** (0 chars in both). Removing them from the template without this step would silently strip them from every c-infra spawn | Fact 2 |
| 3 | `general-agent-template.md` no longer restates any section that all four role guides carry; what remains is only content that is genuinely universal **and** not present in every role guide | Restated intent |
| 4 | The agent startup sequence no longer instructs the agent to read the file that is already its system prompt. Step 4 ("Read the relevant guide in `.claude/agents/` for your role") is a re-read of the auto-loaded role guide — remove or reword it | Restated intent |
| 5 | **Negative, file-wide**: `CLAUDE.md` is byte-identical to `HEAD` | Out of scope |
| 6 | **Negative**: the compact Karpathy Engineering Principles table and the `Search Before You Build` ladder are still reachable from every role's context after the change — assert their presence in whichever file each role actually loads | Out of scope — T041's fix |
| 7 | Total tokens loaded per spawn (role guide + template, as each role actually loads them) is **lower** than at `HEAD` for all four roles. Report the before/after per role; do not claim a figure you did not measure | Restated intent |
| 8 | **Negative, mutation-verified**: deleting a shared section from one role guide without it existing elsewhere in that role's context turns AC1 RED | vacuous-assertion family |
| 9 | No role guide loses a role-specific section (`Environment Health Checklist`, `The independence rule`, `Scope boundaries`, the decision-gated Appendices). Enumerate them and assert each survives | Surgical Changes |
| 10 | `MANIFEST` unchanged — `.claude/agents` is a directory entry already copied with `cp -r` | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Each of the 4 role guides after the change | carries every shared section it needs, none missing (AC1/AC2) | automated test |
| 2 | `general-agent-template.md` after the change | no section duplicated in all 4 role guides (AC3) | automated test |
| 3 | `CLAUDE.md` | byte-identical to `HEAD` (AC5) | automated test |
| 4 | Karpathy table + Search-Before-You-Build | reachable from every role's context (AC6) | automated test |
| 5 | Per-role token totals | strictly lower than `HEAD` (AC7) | automated test, numbers reported |
| 6 | One shared section deleted from a role guide | AC1 test RED (AC8) | mutation control |

### Verification Command (exact, runnable)

```bash
pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T066.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T066.md`.

---

## Approach

**Pattern reference**: `.claude/agents/general-agent-template.md` and the four role guides as they
stand. Match their existing heading style and tone exactly; this is a content move, not a rewrite.

**Consolidate toward the guaranteed channel, not the tidy one.** The instinct is to make the template
the single source and thin the role guides — it reads better and it is what "de-duplicate" usually
means. It is wrong here: the template arrives only if the agent opens it, while the role guide is the
system prompt and always arrives. Moving content *out* of a guaranteed channel *into* an optional one
is the "already covered must mean reaches-the-context" error with extra steps.

**AC2 is the trap.** `common-infrastructure.md` currently has **no** Communication Protocol and **no**
Complexity section — it relies entirely on the template for both. So the very first deletion from the
template silently strips them from every common-infrastructure spawn, which is the agent type this
project uses most. Fold them in *before* removing anything.

**Do not treat the trace counts as a rate.** 7 reads across 3 buckets is a floor: T063 established
that the active-task pointer arms after the startup reads, so most agent reads land in `_untagged`.
The design above does not depend on the exact rate — it only depends on *guaranteed* vs *not
guaranteed*, which is a structural fact about the harness, not a measurement. Do not go looking for a
more precise number to justify a bolder cut.

**AC7 must be measured, not asserted.** Report before/after per role. If a role's total does not go
down, say so rather than reframing the criterion — a null result here is a legitimate outcome and far
more useful than a claimed saving.

---

## Edge Case Checklist

- [ ] A "shared" section whose *content* differs materially between role guides — do not merge on heading name alone; diff the bodies and keep role-specific wording
- [ ] `common-infrastructure.md` is the smallest guide (730 tok) and gains the most; confirm it does not end up larger than the pair it replaces (that would be a net loss for the most-used role)
- [ ] `CLAUDE_LEGACY.md` has an additions-only sync policy — check whether it mirrors any moved section, and do not delete from it
- [ ] The template's `Staleness Guard` footer references sync with `CLAUDE.md`; if the template shrinks, that note must still be true
- [ ] A role guide's Appendix is decision-gated and must not be promoted into the always-loaded body
- [ ] `craft-agent` generates new role guides from this shape — if the role guide becomes the single source, that skill's template must reflect it or the next generated agent starts non-compliant

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/agents/common-infrastructure.md` | gains Communication Protocol + Complexity (AC2) |
| `.claude/agents/general-agent-template.md` | loses sections all four role guides carry (AC3); startup step 4 reworded (AC4) |
| `.claude/agents/backend.md`, `frontend.md`, `qa.md` | only if a shared section is missing; otherwise untouched |
| `.claude/skills/craft-agent/SKILL.md` | reflect the new single-source shape if the generated template changes |
| `.claude/hooks/tests/` (new) | AC1–AC10 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | AC5 — cross-context redundancy, byte-identical |
| `CLAUDE_LEGACY.md` | additions-only sync policy |
| `PROJECT_SPEC.md` | explicitly out of scope per the row |
| `MANIFEST` | AC10 — directory entry already deploys |
| `memory/*` | Supervisor-only writes |
| `PROJECT_KANBAN.md` | Supervisor closes the row; also test-covered |

---

## Test Plan

Write AC1 and AC2 **first** — they are the guards that make every later deletion safe, and AC2 in
particular protects the most-used agent type from a silent strip.

Then AC5/AC6 (the negatives protecting T041's fix), then the deletions.

Measure AC7 from the real files, per role, and paste the table.

Mutation-verify AC8 by deleting a shared section from one role guide and confirming RED; confirm the
mutation actually took effect before trusting the verdict — a control that never executes proves
nothing, which has happened twice on this project. Attack AC6 from more than one direction (delete
the table; and delete only its *heading*) — an assertion can be non-vacuous against one mutation and
vacuous against another.

Never write to any file under `tasks/` other than creating `tasks/TASK_REVIEW_T066.md`.

---

## Completion Checklist

> **`Skill()` is not available to a sub-agent** (toolset is Read/Write/Edit/Bash/Glob/Grep). Do the
> equivalent work manually and label it as manual; the **Supervisor** runs `code-review`,
> `security-review` and `verify` at Stage 4. Do not claim a skill run you did not perform.

- [ ] Implementation done
- [ ] Self-review performed manually and labelled
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T066.md` (Hard-Stop Gate 5)
- [ ] AC7 before/after token table pasted, measured not asserted
- [ ] UI Evidence rows marked ☐ N/A with justification — pure-backend task
- [ ] Learnings flagged to the Supervisor (do not write `memory/` yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
