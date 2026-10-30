# TASK_GUIDE — T219: Pipeline pointers for the tech-lead pack — Stage 2 spawn and Stage 5 refresh by watched paths
**Date**: 2026-10-30
**Complexity Level**: C1
**Risk Level**: Medium (hub file: `docs/claude-md/pipeline-stages.md` — Stage 2 rule raises Risk one level)
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Read `docs/prd/PRD_tech-lead-pack.md` (FR-007, FR-009) and `docs/brainstorming/BRAINSTORMING_LOG_tech-lead-pack.md` § Recommended Path (refresh trigger)
6. Read `packs/tech-lead/agents/tech-lead.md` and `packs/tech-lead/skills/architecture-docs/SKILL.md` (from T218) so the wording matches

---

## Requirement (Pillar 1 — Adapt the requirement)

PRD FR-009: "`AGENTS.md` and `docs/claude-md/pipeline-stages.md` gain only a pointer: when the pack is installed, the Supervisor spawns `tech-lead` at the FR-007 triggers." FR-007 (a) Stage 2 after `PROJECT_SPEC.md` is locked; (c) refresh after a merge whose diff matches a watched path in the approved map. Trigger (b), on demand, needs no doctrine.

**Restated intent**:
> The Supervisor learns, from the pipeline doctrine, the two moments to spawn `tech-lead` — but only in a project where the pack is activated (`agents/tech-lead.md` exists). In every other project the pipeline reads and behaves exactly as before.

**Out of scope**:
- Any hook or script that detects watched paths automatically; the Supervisor does the match during the Stage 5 item 4 pass it already runs
- Changes to `packs/tech-lead/` (T218)

**Requirement Refs**: FR-007 (a, c), FR-009

### Requirement Fidelity Gate

- [x] Restated intent confirmed — signed `auto (Supervisor)` 2026-10-30
- [x] Domain terms align — "Activated pack" (ADR-0002), "document map", "watched paths" (PRD D5, brainstorming log)
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] All Requirement Refs exist in `docs/prd/PRD_tech-lead-pack.md` and are covered

---

## Dependencies & Reachability

**Depends on**: T218 — `packs/tech-lead/agents/tech-lead.md` and its map / watched-paths wording must exist
**Entry point**: `## Stage 2: Intent Transformation` and `## Stage 5: Integration & Verification` in `docs/claude-md/pipeline-stages.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Stage 2 gains one numbered item or sub-bullet: if `agents/tech-lead.md` exists (tech-lead pack activated), after `PROJECT_SPEC.md` is locked the Supervisor spawns `tech-lead` to write the document map `docs/architecture/README.md` for user approval (auto mode: map only, listed in the final report) | FR-007a, FR-009 |
| 2 | Stage 5 item 4 gains one sub-bullet: if `agents/tech-lead.md` and `docs/architecture/README.md` both exist, the Supervisor matches the item-4 `git diff HEAD~1 --name-only` list against the map's watched paths; on a match it spawns `tech-lead` in refresh mode for the matched documents only; no match → nothing | FR-007c, FR-009 |
| 3 | Both additions are conditional on the file check, name the pack (`packs/tech-lead/PACK.md`), and add no other text; no existing line of `pipeline-stages.md` is reworded | FR-009 "only a pointer"; surgical |
| 3b | `AGENTS.md` gains exactly ONE line in `## 5-Stage Agentic Pipeline` (after the Stage 5 bullet): if `agents/tech-lead.md` exists, spawn `tech-lead` at Stage 2 (document map) and at the Stage 5 item 4 refresh — detail in `pipeline-stages.md`. `tests/test_tracks.py` and `tests/test_claude_md_slim.py` AGENTS.md caps (≤200 lines, ≤32,768 bytes) still pass | FR-009; Debate 2026-10-30 (see TASK_REVIEW_T219 Auto decisions) |
| 4 | A test (new `tests/test_tech_lead_pipeline_pointer.sh`, or an added case in an existing doctrine test if one covers `pipeline-stages.md`) asserts AC 1–2 text and the conditional, with a mutation control (the pointer without its `agents/tech-lead.md` condition fails the check) | Gate 5 |
| 5 | Negative: `.claude/`, `skills/`, `agents/` unchanged; AGENTS.md changes by one line only | Out of scope |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | `pipeline-stages.md` after the change | Stage 2 and Stage 5 pointers present and conditional | the new test |
| 2 | Mutant: pointer without the condition | check fails | mutation control |
| 3 | Full repo | existing tests that read `pipeline-stages.md` still pass | `grep -rl pipeline-stages tests/` → run those |

### Verification Command

```bash
bash tests/test_tech_lead_pipeline_pointer.sh
```

---

## Approach

**Pattern reference**: the existing conditional wording style in `docs/claude-md/pipeline-stages.md` (e.g. "Auto mode: …" sentences inside numbered items); `tests/test_pack_catalog.sh` for shell test + mutation control style.

**Vital slice**: the two conditional sentences.
**Cut list**: automatic watched-path matching in a hook; any AGENTS.md text beyond one line.

Keep each addition to 1–3 lines. Write the Stage 5 sub-bullet under item 4, after the `git diff HEAD~1 --name-only` bullet, so it reuses that list.

---

## Edge Case Checklist

- [ ] Pack not activated → both pointers are no-ops by their wording.
- [ ] Map exists but pack not activated (`agents/tech-lead.md` missing) → no spawn.
- [ ] Map without a watched-paths column (user edited it) → Supervisor treats it as no match and notes it; say so in the sub-bullet only if it fits in one clause.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `docs/claude-md/pipeline-stages.md` | two conditional pointers |
| `AGENTS.md` | one conditional line (AC 3b) |
| `tests/test_tech_lead_pipeline_pointer.sh` | new test (also asserts the AGENTS.md line) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `packs/tech-lead/**` | T218 |
| `PROJECT_KANBAN.md`, `PROJECT_SPEC.md`, `memory/` | Supervisor-only |

---

## Test Plan

Run the new test and every existing test that reads `pipeline-stages.md`; paste outputs.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted
- [ ] Supervisor notified: task ready for Stage 4 review (code-review + security-review, Risk Medium)
