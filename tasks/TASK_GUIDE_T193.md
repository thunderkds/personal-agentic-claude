# TASK_GUIDE — T193: Doctrine and glossary say what the companion gate does, in four lines of AGENTS.md headroom
**Date**: 2026-10-28
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt
3. Read this file completely, then `PRD_companion-scoring.md` (FR-003, FR-013, FR-015)
4. Read `agents/common-infrastructure.md`
5. Read the **shipped** `skills/score/SKILL.md` and `skills/ui-test/SKILL.md` (T191, T192). This task documents what they actually do, not what the PRD planned — if the two differ, the shipped skill wins and you say so in your report
6. Read `docs/claude-md/pipeline-stages.md` lines 185–225 (Stage 4) and 226+ (Stage 5)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28: *"the scoring is a optional, so if users do not use this one, we should run the
normal flow, not required the mcp must run, or depend on that 100%"*.

**Restated intent**:
> The doctrine states the two new optional Stage 4 skills, the floor, and the rule that a tool which
> ran is binding while a tool nobody ran changes nothing. The glossary keeps two similar-sounding
> terms apart so the next reader cannot confuse the kit's row with the verifier's asking round.

**Out of scope**:
- Changing the pipeline's stage order, any Hard-Stop Gate's wording, or the `verify` row.
- Making either skill mandatory anywhere in the doctrine.
- Any new rule. Stage 5 already reads *"Do not merge while any evidence row reads fail or is blank"*
  (`docs/claude-md/pipeline-stages.md`, Stage 5 step 1). This task documents that T190 finally
  **enforces** that existing sentence for these rows; it does not invent a gate.

**Requirement Refs**:
- FR-003: the floor is declared in the doctrine and the skill, never in a TASK_GUIDE
- FR-013: two glossary terms, kept apart
- FR-015: binding only when used

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — this task *writes* the two terms
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD_companion-scoring.md` and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: T191 — `skills/score/SKILL.md` must be shipped, because this task documents its real behaviour. (T192 is also read; `Depends on` carries one ID, and T192 is listed under Blocked by on the board.)

**Entry point**: `Companion score`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `AGENTS.md` stays **at or under 200 lines** (`tests/test_claude_md_slim.py:17`). It is at 196 today, so this task has **four lines of headroom** and must spend at most that | FR-003 |
| 2 | `AGENTS.md`'s Stage 4 bullet names `score` and `ui-test` as **optional** Stage 4 skills and points at `docs/claude-md/pipeline-stages.md` for the detail — one line, in the established pointer style | FR-003, FR-015 |
| 3 | `docs/claude-md/pipeline-stages.md`'s Stage 4 gains the two skills as numbered steps marked optional, each stating what it needs to be available and that an unavailable tool is skipped, not waited for | FR-015 |
| 4 | The floor appears in `docs/claude-md/pipeline-stages.md` exactly as `overall ≥ 80`, together with the rule that a failing `change_risk` rule fails the row whatever `overall` says | FR-003 |
| 5 | The doctrine states the binding rule in one sentence: a tool that ran is binding and its `fail` stops the merge; a tool nobody ran means no row, no stop and no dependency | FR-015 |
| 6 | The doctrine states that a `TASK_GUIDE` may never name its own floor | FR-003 |
| 7 | `PROJECT_SPEC.md`'s Glossary gains **Companion score** — the kit's Evidence row, its floor, and the fact that it is optional | FR-013 |
| 8 | `PROJECT_SPEC.md`'s Glossary gains **evaluate gate** — easy-verifier's own round where the engine asks the caller to rate what its rules cannot decide — and its definition says explicitly that it is **not** the kit's Evidence Gate and not the merge gate | FR-013 |
| 9 | **Negative case:** no file says either skill is required, or that a task cannot reach Done without it. A test greps the doctrine for a required-sounding claim about these two skills and fails on one | FR-015 |
| 10 | `sh scripts/validate.sh` reports PASS (it checks that every path named inside `AGENTS.md` exists), and the full suite stays green — in particular `tests/test_claude_md_slim.py`, `tests/test_docs_match_installer.py` and `tests/test_response_standard.py` | FR-003 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `wc -l AGENTS.md` after the edit | ≤ 200 | automated test |
| 2 | A grep for `overall ≥ 80` across the repo | hits in `docs/claude-md/pipeline-stages.md` and `skills/score/SKILL.md`, and in **no** `tasks/TASK_GUIDE_*.md` as a task-set floor | automated test |
| 3 | A grep for `evaluate gate` in `PROJECT_SPEC.md` | one glossary row, whose definition contains a denial that it is the kit's gate | automated test |
| 4 | The doctrine read by someone who has not followed this feature | they can tell, without opening a skill, that both tools are optional | manual (Supervisor sign-off) |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/ -q && sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T191.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T191.md`.

---

## Approach

**Pattern reference**: `AGENTS.md`'s existing Stage 4 bullet — it names the skills and conditions in
one line and defers to `docs/claude-md/pipeline-stages.md`. Imitate that exactly. The 200-line cap is
why that pattern exists, and the four remaining lines are the whole budget for this feature's
doctrine.

**Vital slice**: one `AGENTS.md` line, two numbered Stage 4 steps, two glossary rows.

**Cut list**: no new `docs/claude-md/` file; no DDR (this records a user decision, not a trade-off
the DDR gate's two-of-three test clears); no change to the Hard-Stop Gate list, because Gate 5 and
Gate 6 already cover tests and UI evidence and neither needs amending for an optional tool.

---

## Edge Case Checklist

- [ ] The 200-line cap is lines, not bytes — a long single line passes the cap and still bloats the file
- [ ] `scripts/validate.sh` checks that paths named inside `AGENTS.md` exist; a pointer to a file that is not there fails the build
- [ ] `tests/test_response_standard.py` asserts things about `AGENTS.md`'s own wording — read it before editing that file
- [ ] `CLAUDE.md` is asserted byte-for-byte as `b"@AGENTS.md\n"`; never edit it
- [ ] The word "required" is the honest word for "not required", and `tests/test_site_content.py:820` bans it **inside `#mcps` only** — that constraint belongs to T194 and does not apply to the doctrine
- [ ] The glossary is alphabetical in places — match the surrounding order rather than appending blindly

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `AGENTS.md` | One line in the Stage 4 bullet. At most four lines total |
| `docs/claude-md/pipeline-stages.md` | Two optional Stage 4 steps, the floor, the binding rule |
| `PROJECT_SPEC.md` | Two glossary rows |
| `tests/test_companion_doctrine.py` | New — AC 1, 2, 4, 6, 9 and Success Criteria 2–3 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | Asserted byte-for-byte as `b"@AGENTS.md\n"` (`tests/test_agents_md_primary.py:130`) |
| `.claude/hooks/**` | T190 |
| `skills/score/SKILL.md`, `skills/ui-test/SKILL.md` | T191, T192. This task documents them; it does not edit them |
| `site/**`, `tests/test_site_content.py` | T194 |
| The Hard-Stop Gate list in `AGENTS.md` | No gate is amended by this feature |

---

## Test Plan

1. `tests/test_companion_doctrine.py` — the line cap, the pointer line, the single spelling of the
   floor, the "never in a TASK_GUIDE" rule, the two glossary rows with `evaluate gate`'s denial, and
   AC 9's grep for a required-sounding claim.
2. Full suite plus `sh scripts/validate.sh`.
3. Supervisor reads the changed doctrine cold and signs off Success Criterion 4.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: ☐ N/A — Low risk, documentation only
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T191.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] UI Evidence rows marked ☐ N/A with a justification (documentation only, no UI component)
- [ ] `memory/MEMORY.md` updated
- [ ] Supervisor notified: task ready for Stage 4 review
