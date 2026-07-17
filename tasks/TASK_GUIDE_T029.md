# TASK_GUIDE — T029: Prune the 4 oversized SKILL.md files via slim-skills
**Date**: 2026-07-17
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Supervisor-orchestrated via `/slim-skills` (HITL — the skill's approval gate requires the user; no sub-agent spawn)
**Agent guide**: `.claude/skills/slim-skills/SKILL.md` (the process definition for this task)

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/skills/slim-skills/SKILL.md` — the 5-step process (scan → checksum → prune → approval gate → checksum verification) IS the implementation plan; do not improvise a different one
5. Read `docs/ddr/0001-measure-first-token-refactor.md` — this task is Option C, the parallel rider

---

## Requirement (Pillar 1 — Adapt the requirement)

Per DDR-0001: while the baseline Measurement Window runs (T028), the four SKILL.md files exceeding the repo's own 150-line threshold are pruned using the existing `slim-skills` pipeline — a safe parallel win because skill files are invocation-triggered and don't contaminate the always-on cost measurement.

**Restated intent**:
> Run `slim-skills` end-to-end on `learn` (182), `map-codebase` (165), `bugfix` (160), `code-review` (157): extract behavioral checksums, propose pruned versions (target ≤120 lines), get explicit user approval per file, write, and verify zero behavioral assertions lost.

**Out of scope**:
- Skills at or under 150 lines — even if trimmable, they're not candidates (Surgical Changes)
- Rewriting/redesigning any skill's behavior — prune = fewer tokens, identical behavior
- `CLAUDE.md`'s skill table descriptions — unchanged
- Any agent guide in `.claude/agents/`

**Requirement Refs**:
- No `PRD.md` FR applies — internal framework task (T023/T025/T027 precedent). Traces to DDR-0001 Follow-up item 1 and the pre-existing slim-skills decision (memory/decisions.md, 2026-06-24).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (BRAINSTORMING_LOG.md User Selection: Option C parallel rider, 2026-07-17)
- [x] Domain terms align with glossary (no new terms — slim-skills vocabulary already established)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A precedent confirmed

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: Standalone — N/A: modifies four already-registered skills in place; they remain reachable via their existing `Skill()` invocations and the CLAUDE.md skill table (unchanged).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | All 4 candidate files processed through all 5 slim-skills steps; each has an explicit user decision (approve/skip/edit) | "run slim-skills end-to-end" |
| 2 | Every approved file ≤120 lines, or the safe floor is noted with the blocking checksum items named | prune target |
| 3 | Post-write checksum verification passes for every approved file: every extracted behavioral assertion present verbatim-or-equivalent in the pruned version | "zero behavioral assertions lost" |
| 4 | Existing hook test suite still green (`pytest .claude/hooks/tests/ -q`) — no skill regression observable from the outside | identical behavior |
| 5 | Negative: if any checksum item is missing after write, the file is reverted and the loss reported — never silently shipped | slim-skills Step 5 contract |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `wc -l` on the 4 files after approval | each ≤120 (or safe-floor documented) | shell check |
| 2 | Checksum list vs. pruned file content | every item findable in pruned file | slim-skills Step 5 + reviewer spot-check |
| 3 | `pytest .claude/hooks/tests/ -q` | all pass | automated test |

### Verification Command (exact, runnable)

```bash
wc -l .claude/skills/learn/SKILL.md .claude/skills/map-codebase/SKILL.md .claude/skills/bugfix/SKILL.md .claude/skills/code-review/SKILL.md && pytest .claude/hooks/tests/ -q
```

> Hard-Stop Gate 5 note: this task writes no new product code — the "new test" requirement is satisfied by the checksum-verification protocol (slim-skills Step 5) whose per-file results must be pasted into the Evidence row below, plus the still-green existing suite. Supervisor signed off on this oracle at Stage 2 (this section).

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [paste per-file checksum verification results — the designated oracle for this task] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [any checksum miss → revert demonstrated or N/A] |
| verify | ☐ pass / ☐ fail | [invoke one pruned skill live; confirm behavior unchanged] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [4 SKILL.md files + their consumers] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | ☐ N/A | no UI component |
| **UI: Design-system compliance** | ☐ N/A | no UI component |
| **UI: Responsiveness** | ☐ N/A | no UI component |

---

## Approach

Follow `.claude/skills/slim-skills/SKILL.md` exactly — it already encodes the safe process (checksum-first, human approval, verify-or-revert). This task exists to *schedule and evidence* that run inside the pipeline, not to invent process. Risk stays Low despite touching the Stage 4 `code-review` skill because: (a) checksum extraction happens before any edit, (b) nothing is written without explicit per-file user approval, (c) Step 5 auto-reverts on any checksum miss.

---

## Edge Case Checklist

- [ ] `code-review` is itself a Stage 4 gate skill — a lost assertion there weakens every future review; double-check its checksum list is complete before approving its diff
- [ ] `bugfix` orchestrates other skills (`diagnose`, `craft-spawn-prompt`) — invocation references must survive verbatim
- [ ] `learn` contains the materiality gate and LR-numbering rules already recorded as patterns in MEMORY.md — those lines are checksum items, not prose
- [ ] If two candidates share duplicated text, prune each independently — no cross-file "shared section" abstraction (Simplicity First)
- [ ] User may skip any file — a skip is a valid outcome, record it, don't re-argue

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/learn/SKILL.md` | prune 182 → ≤120 (pending approval) |
| `.claude/skills/map-codebase/SKILL.md` | prune 165 → ≤120 (pending approval) |
| `.claude/skills/bugfix/SKILL.md` | prune 160 → ≤120 (pending approval) |
| `.claude/skills/code-review/SKILL.md` | prune 157 → ≤120 (pending approval) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | DDR-0001 defers all CLAUDE.md edits; skill-table descriptions unchanged |
| All other `.claude/skills/*/SKILL.md` | ≤150 lines — not candidates |
| `.claude/agents/*.md` | out of scope — agents, not skills |
| `reports/token-audit_*.md` | T028's artifact — parallel task, don't collide |

---

## Test Plan

(1) slim-skills Step 5 checksum verification per approved file — results pasted as evidence; (2) `pytest .claude/hooks/tests/ -q` green; (3) live invocation of one pruned skill (`verify` row) confirming behavior unchanged.

---

## Completion Checklist

- [ ] All 4 files have a user decision (approve/skip/edit)
- [ ] Checksum verification passed for every approved file (or revert executed + reported)
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Existing test suite green — output pasted into Evidence table
- [ ] `Skill({ skill: "verify" })` run — one pruned skill exercised live
- [ ] Supervisor notified: task ready for Stage 4 review
