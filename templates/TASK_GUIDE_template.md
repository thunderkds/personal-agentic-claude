# TASK_GUIDE — T[NNN]: [Short Title]
**Date**: [YYYY-MM-DD]
**Risk Level**: Low / Medium / High
**Assigned agent**: [agent name]
**Agent guide**: `.claude/agents/[agent-file].md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/[agent-file].md`

If docs/legacy/ exists (legacy mode): also read `docs/legacy/risk-hotspots.md` and `docs/legacy/architecture.md`.

---

## Requirement

[Original user request — verbatim or closely paraphrased. Do not interpret yet.]

---

## Acceptance Criteria

- [ ] [testable condition 1]
- [ ] [testable condition 2]
- [ ] [testable condition 3]

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
- [ ] Tests pass
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `docs/legacy/` updated (if new insights, legacy mode only)
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
