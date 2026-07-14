# TASK_GUIDE — T016: Wire `ui-test` into pipeline (qa.md + CLAUDE.md)
**Date**: 2026-07-01
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: qa-expert
**Agent guide**: `.claude/agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/qa.md`
5. Complexity Level is C1 — light rigor per the Complexity matrix
6. Small, known files — skip `memory/codebase-map.md`

**Depends on**: T015 (`.claude/skills/ui-test/SKILL.md`) must exist and be reviewed before this task starts — it references the skill concretely rather than describing it abstractly.

---

## Requirement (Pillar 1 — Adapt the requirement)

Continuation of T015: with the `ui-test` skill built, wire it into the actual pipeline so `qa-expert` invokes it at Stage 5 and its output is recognized as valid Gate 6 evidence at Stage 4.

**Restated intent**:
> Update `.claude/agents/qa.md` to add: qa-expert invokes `Skill({ skill: "ui-test" })` during Stage 5 `verify` for any task whose TASK_GUIDE has a non-deleted "UI / Design Acceptance Criteria" section. Update `CLAUDE.md`'s skills table (add `ui-test` row) and add one clarifying sentence to Hard-Stop Gate 6 noting that MCP-produced evidence from `ui-test` satisfies the three UI Evidence rows when available, without changing the gate's requirement that the rows be filled with real evidence either way.

**Out of scope**:
- Rewriting Gate 6 itself, or removing the manual-evidence fallback path
- Any change to Stage 1–3 skills
- Building the skill's internals (done in T015)

**Requirement Refs**: None (internal tooling task) — traces to `BRAINSTORMING_LOG.md` → Surgical Scope → "Files that should be touched".

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, via approved brainstorming session)
- [x] Domain terms align with `BRAINSTORMING_LOG.md`
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No `PRD.md` Requirement Refs apply — Supervisor waives this row

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/agents/qa.md`'s "Available skills" table gains a `ui-test` row, invoked at Stage 5 `verify`, conditioned on the task having a UI/Design AC section | Restated intent |
| 2 | `CLAUDE.md`'s custom-skills table gains a `ui-test` row referencing `.claude/skills/ui-test/SKILL.md`, under Stage 5 | Restated intent |
| 3 | `CLAUDE.md` Hard-Stop Gate 6 text gains one sentence clarifying MCP evidence satisfies the three rows when available, without weakening the gate's evidence requirement when it's not | Gate 6 reuse requirement |
| 4 | No change to Stage 1–3 skill definitions or agent files outside `qa.md` | Surgical Scope |
| 5 | The conditional invocation logic (only call `ui-test` when a UI/Design AC section exists) is explicit, not implied | Non-blocking requirement |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A TASK_GUIDE with a UI/Design AC section reaches Stage 5 | `qa.md` documents that `ui-test` is invoked | Read-through of updated `qa.md` |
| 2 | A pure-backend TASK_GUIDE (UI/Design AC section deleted) reaches Stage 5 | `qa.md` documents that `ui-test` is NOT invoked | Read-through of updated `qa.md` |
| 3 | `CLAUDE.md` diff reviewed | Only the skills table + Gate 6 sentence changed; no other pipeline stage altered | `git diff CLAUDE.md` |

### Verification Command (exact, runnable)

```bash
git diff --stat .claude/agents/qa.md CLAUDE.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | Documentation task — "test" = diff review against Acceptance Criteria table |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | Confirm no accidental edits outside the two named files |
| `verify` skill — works in running app | ☐ N/A | No running app for a docs-only change |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | Blast radius = qa.md + CLAUDE.md only |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | ☐ N/A | Docs-only task |
| **UI: Design-system compliance** | ☐ N/A | Docs-only task |
| **UI: Responsiveness** | ☐ N/A | Docs-only task |

---

## Approach

Minimal, additive diffs only. In `qa.md`, add one row to the existing "Available skills" table (matching its existing format: `| Skill | Invoke | When |`). In `CLAUDE.md`, add one row to the custom-skills table (matching its existing `| Skill | Definition | When to use |` format) and append one sentence to the Hard-Stop Gate 6 paragraph — do not restructure the gate.

---

## Edge Case Checklist

- [ ] Don't let the Gate 6 sentence imply MCP evidence is *required* — it's one valid evidence source among others (manual/other tools remain acceptable)
- [ ] Don't add `ui-test` to Stage 3/4 — only Stage 5 per the locked decision
- [ ] Confirm the conditional (has UI/Design AC section vs. deleted) is unambiguous in qa.md's wording

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/agents/qa.md` | Add `ui-test` row to Available skills table |
| `CLAUDE.md` | Add `ui-test` row to skills table; append one sentence to Hard-Stop Gate 6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/ui-test/SKILL.md` | Built in T015; this task only references it |
| `.claude/agents/frontend.md`, `.claude/agents/backend.md`, `.claude/agents/common-infrastructure.md` | Out of scope per Surgical Scope |
| `templates/TASK_GUIDE_template.md` | Optional per brainstorming log, deferred — not required for this task's acceptance criteria |

---

## Test Plan

`git diff` review against the Acceptance Criteria table above; confirm both edits are additive and match existing table formats.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Lint passes (Markdown only)
- [ ] Tests written AND pass — output pasted into Evidence table (diff review counts as the test for a docs-only task)
- [ ] `Skill({ skill: "verify" })` run — N/A, docs-only
- [ ] `memory/MEMORY.md` updated (ui-test skill now wired into Stage 5 + Gate 6)
- [ ] Supervisor notified: task ready for Stage 4 review
