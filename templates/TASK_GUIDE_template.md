# TASK_GUIDE — T[NNN]: [Short Title]
**Date**: [YYYY-MM-DD]
**Complexity Level**: C0 / C1 / C2 / C3
**Risk Level**: Low / Medium / High
**Priority**: P0 / P1 / P2
**Assigned agent**: [agent name]
**Agent guide**: `.claude/agents/[agent-file].md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/[agent-file].md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`

If docs/legacy/ exists (legacy mode): also read `docs/legacy/risk-hotspots.md` and `docs/legacy/architecture.md`.

---

## Requirement (Pillar 1 — Adapt the requirement)

[Original user request — verbatim or closely paraphrased. Do not interpret yet.]

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> [one or two sentences — what success means for the user]

**Out of scope** (what this task explicitly does NOT do):
- [non-goal 1]

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):
- FR-NNN: [short description]

**Related ADRs** (decisions in `docs/adr/` that constrain this task, if any):
- [ADR-NNNN: title — or "none"]

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | [testable condition 1] | [which part of the requirement] |
| 2 | [testable condition 2] | [which part of the requirement] |
| 3 | [negative / boundary condition] | [which part of the requirement] |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> Fill **Success Criteria** and **Verification Command** at Stage 2 (before spawning the agent).
> The reviewer fills **Evidence** at Stage 4/5. A task is **not done** until every row has evidence.
> Rule: the implementing agent must NOT be the sole author of its own acceptance test — the
> Supervisor writes or signs off on the oracle first, so code and test can't be wrong together.

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | [concrete input] | [concrete expected output] | automated test / manual / app run |
| 2 | [negative / invalid input] | [expected failure or guard] | automated test |

### Verification Command (exact, runnable)

```bash
# the single command (or short sequence) that proves this task works
[e.g. pytest tests/test_T001.py -q   |   npm test -- T001   |   curl ... | grep ...]
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | [what was observed] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |

---

## Approach

[Recommended approach from brainstorming skill output, or Supervisor's decision for Low-risk tasks. Include the reasoning.]

---

## Edge Case Checklist

[Populated from brainstorming skill output. List silent failures and boundary conditions to guard against.]

- [ ] [edge case 1]
- [ ] [edge case 2]

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| [path/to/file] | [what and why] |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| [path/to/file] | [why it's off-limits] |

---

## Test Plan

[How to verify this works — unit tests, integration tests, manual steps, or all three.]

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Migration safety: `Skill({ skill: "migration-safety" })` gate passed (if task touches DB schema/migrations)
- [ ] Lint passes
- [ ] Tests pass
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `docs/legacy/` updated (if new insights, legacy mode only)
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
