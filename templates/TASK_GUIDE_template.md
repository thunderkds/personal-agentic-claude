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
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

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

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

> Advisory, not a Hard-Stop Gate. `Depends on` is verified (non-blocking warning) at Agent-spawn
> time by `pre_agent_validate_guide.py`. `Entry point` is verified (non-blocking finding) at Stage 4
> `code-review` time. This is distinct from `PROJECT_KANBAN.md`'s `## Blocked` table, which stays a
> manual escape hatch for non-task blockers (external people/APIs/decisions) that can't be checked
> automatically — don't use `Depends on` for those.

**Depends on**: [Txxx — short description of the artifact this task needs from it] or `None`
> Example: `Depends on: T012 — /api/users endpoint must exist`

**Entry point**: [literal, grep-able identifier — route path, button label, function/consumer name] or `Standalone — N/A` (with a one-line reason)
> Example: `Entry point: POST /api/users` or `Entry point: <SaveButton>` or `Standalone — N/A: consumed by external webhook, not called from this repo`
> Do not use vague prose ("the dashboard") — the reachability check greps for this exact string.

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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## UI / Design Acceptance Criteria

> **Only fill for tasks with a UI component. Delete this entire section for pure-backend tasks.**
> Each row must name a verification method and produce pasted evidence before Done (Hard-Stop Gate 6).
> "Manual" is only acceptable for C0 tasks — C1+ must use an automated tool or LLM-vision screenshot.

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| [screen or component name] | [screenshot diff / LLM vision / Storybook snapshot] | [no diff / "matches spec"] |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | [CSS audit / LLM vision / token lint] | [token names or hex values] |
| Typography matches spec | [computed style / visual] | [font-family, size, weight] |
| Spacing / layout matches spec | [computed style / visual] | [margin, padding values] |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (320–480px) | [screenshot / Playwright / Detox / manual] | [expected layout description] |
| Tablet (768px) | [screenshot / Playwright / Detox / manual] | [expected layout description] |
| Desktop (1024px+) | [screenshot / Playwright / Detox / manual] | [expected layout description] |

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
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `docs/legacy/` updated (if new insights, legacy mode only)
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
