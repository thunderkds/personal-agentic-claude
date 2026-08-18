# TASK_GUIDE — T080: Register the Agent Skills conformance contract in README + CLAUDE.md
**Date**: 2026-08-18
**Complexity Level**: C1
**Risk Level**: Low
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
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1 task — `memory/codebase-map.md` is optional; read it only if the README edit turns out to span more sections than predicted below

---

## Requirement (Pillar 1 — Adapt the requirement)

> User request (2026-08-18, verbatim): *"following this documents as knowledge to enhance the skills,
> https://agentskills.io/home. Create branch, tasks, and update the README also."*

T078 and T079 add the rules and the tests. This task makes them **discoverable**: today the README's
`## Custom Skills` section opens with one sentence — *"All skills live in
`.claude/skills/<name>/SKILL.md` and are auto-discovered by Claude Code"* — and never says that this
is an implementation of an open standard, never states a single constraint a new skill must satisfy,
and never points at `write-better-skill` as the place those constraints live. A contributor reading
the README has no way to learn what makes a skill valid here.

**Restated intent**:
> State in the README that this repo's skills implement the Agent Skills open format, summarize the
> contract a new skill must meet, point at `write-better-skill` and the conformance test as the
> authorities, and register the new material in `CLAUDE.md` and `memory/MEMORY.md` so the Supervisor
> and every future session see it.

**Out of scope**:
- Reproducing the specification in the README. The README states the contract and links out; the
  authority is `write-better-skill` (in-repo) and agentskills.io (upstream). Duplicating the spec
  into a third place is exactly the `Duplication` failure mode `write-better-skill` itself names.
- Any change to skill content or tests — T078 and T079 own those.
- Documenting the trigger-eval method in the README. It is authoring craft, not the contract; it
  lives behind T079's context pointer where an author reaches it.

**Requirement Refs**: `None — direct user request.`

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-08-18)
- [x] Domain terms align with `PROJECT_SPEC.md`
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] Requirement Refs: `None` recorded with a reason

---

## Dependencies & Reachability

**Depends on**: T079 — the README must describe what actually shipped. Writing it before T078/T079
merge risks documenting a contract that changed during implementation.

**Entry point**: `README.md` → `## Custom Skills`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `README.md`'s `## Custom Skills` section states that skills in this repo implement the **Agent Skills** open format, and links to `https://agentskills.io` | "never says that this is an implementation of an open standard" |
| 2 | The section gains a short **skill contract** summary listing what a new skill must satisfy: `SKILL.md` required; `name` lowercase alphanumeric + hyphens, matching the parent directory; `description` ≤1024 chars; `SKILL.md` ≤500 lines; optional `scripts/`, `references/`, `assets/` | "never states a single constraint a new skill must satisfy" |
| 3 | The contract summary is a **pointer, not a copy** — ≤12 lines, naming `write-better-skill` as the in-repo authority for the full rules and the reasoning behind them | "the authority is `write-better-skill`" |
| 4 | The section names `.claude/hooks/tests/test_skill_spec_conformance.py` as the automated check, with the exact command to run it | "point at … the conformance test as the authorities" |
| 5 | The `write-better-skill` row in the README's **Maintenance & Meta** table is updated to mention the two new reference files and what each covers | discoverability |
| 6 | `CLAUDE.md`'s `## Skills vs Agents` **Stage index** line is unchanged in structure but the meta/cross-cutting entries reflect any new skill names — if T078/T079 added **no** new skill, state that explicitly in the review notes rather than editing the line for its own sake | "register the new material in `CLAUDE.md`" |
| 7 | `memory/MEMORY.md` gains **one** index entry (Supervisor writes it, not the agent) recording the Agent Skills conformance decision and linking to `decisions.md` | "register … in `memory/MEMORY.md`" |
| 8 | `memory/MEMORY.md` stays within its `HOT_TIER_CHAR_BUDGET` after AC7's entry | T075's budget ratchet |
| 9 | The README's existing structure is preserved — no section renamed, reordered, or removed, and no skill table row deleted | negative condition |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The repo after this task's edits | Full hook suite passes, including T078's conformance test and T079's pointer test | automated test |
| 2 | `memory/MEMORY.md` after AC7 | `assert_hot_tier_within_budget` passes (AC8) | automated test |
| 3 | `grep -c '^## ' README.md` before vs after | Identical count — AC9's structure-preservation check | automated diff, output pasted |
| 4 | `git diff --stat main -- README.md` | Additions only within `## Custom Skills`; no deletions outside it | manual diff review, output pasted |
| 5 | **Mutation control** — temporarily delete one `## ` heading from README.md | SC3's count check goes **RED**. Revert after observing. | observed RED |

> SC5 is mandatory. SC3 is a count comparison, and a count comparison between two runs of the same
> unchanged command is the classic vacuous assertion this repo has hit 7 times. Observe it fail.

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  python3 -m pytest .claude/hooks/tests/ -q && \
  grep -c '^## ' README.md
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T080.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T080.md`.

---

## UI / Design Acceptance Criteria

Documentation-only task, no UI component. All three UI Evidence rows are **☐ N/A** — justification:
this task edits Markdown documentation; there is no rendered application surface, no design token,
and no viewport involved.

---

## Approach

**Pattern reference**: `README.md`'s existing `## Memory System` and `## Pipeline Enforcement Hooks`
sections — both state a contract compactly and point at the authoritative file rather than
reproducing it. Match that shape exactly.

**Vital slice**: AC1–AC4, the contract paragraph inside `## Custom Skills`. That is the part a
contributor actually reads before adding skill #31.

**Cut list**:
- A dedicated top-level `## Agent Skills Conformance` README section — folded into the existing
  `## Custom Skills` section instead. A new top-level heading for four paragraphs inflates
  prominence past real rank.
- Badges / shields linking to agentskills.io — decorative, no behavioural change.

---

## Edge Case Checklist

- [ ] AC6 may legitimately require **no edit** to `CLAUDE.md` if T078/T079 added reference files but no new skill. A no-op is the correct outcome there — record it as "no change required, and why", never invent an edit to fill the row
- [ ] AC7 is a **Supervisor-only** write (Memory Write Protocol). The agent must not edit `memory/MEMORY.md` itself — it reports the proposed one-liner to the Supervisor and stops
- [ ] The README states `SKILL.md` line/char numbers that T078 also states in `write-better-skill` — this is the one place duplication is accepted (a summary must contain the numbers to be useful). Keep the numbers identical to T078's, and if they ever diverge, `write-better-skill` wins
- [ ] `slim-skills` currently tells authors to prune a `SKILL.md` past **150 lines** while the spec's budget is **500** — these are different thresholds serving different goals (repo taste vs. spec ceiling). Do not silently reconcile them; if the README's contract paragraph makes the tension visible, flag it to the Supervisor as a follow-up rather than editing `slim-skills`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `README.md` | AC1–AC5 — contract paragraph in `## Custom Skills`, updated `write-better-skill` table row |
| `CLAUDE.md` | AC6 — only if T078/T079 introduced a new skill name; otherwise no change, documented |
| `memory/MEMORY.md` | AC7 — **Supervisor writes this, not the agent** |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/**` | T078 and T079 own all skill content |
| `.claude/hooks/tests/**` | This task adds no test; it is verified by the tests those tasks already shipped |
| `.claude/skills/slim-skills/SKILL.md` | See Edge Case Checklist — the 150 vs 500 line tension is flagged, not resolved here |
| `memory/decisions.md` | Supervisor-only, per the Memory Write Protocol |

---

## Test Plan

1. Record `grep -c '^## ' README.md` and `git diff --stat main -- README.md` as the pre-state.
2. Run mutation control SC5 against the pre-state check; observe RED; revert.
3. Make the README edits (AC1–AC5, AC9).
4. Evaluate AC6; edit `CLAUDE.md` or record the documented no-op.
5. Report AC7's proposed MEMORY.md one-liner to the Supervisor; do not write it.
6. Run the full verification command; paste SC1–SC4 output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: ☐ N/A — Low risk, documentation-only, no code path or data flow changed
- [ ] Lint passes
- [ ] Tests pass — output pasted into `tasks/TASK_REVIEW_T080.md` (Hard-Stop Gate 5). **Note**: this task writes no new test; it is covered by T078's and T079's suites, which is acceptable only because those tests directly assert over the artifacts this task edits. Record that reasoning in the Evidence table rather than leaving the row blank.
- [ ] Mutation control SC5 observed and its output pasted
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (Supervisor only)
- [ ] Supervisor notified: task ready for Stage 4 review
