# TASK_GUIDE — T079: Description triggering + the instruction-pattern library
**Date**: 2026-08-18
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
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C2 task, multi-file: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

> User request (2026-08-18, verbatim): *"following this documents as knowledge to enhance the skills,
> https://agentskills.io/home. Create branch, tasks, and update the README also."*

T078 absorbs the spec's **hard constraints**. This task absorbs the two bodies of *craft* guidance
that `write-better-skill` demonstrably lacks, both from agentskills.io's skill-creation guides:

1. **Description triggering.** `write-better-skill` currently spends three bullets on descriptions
   ("front-load the leading word", "one trigger per branch", "cut identity already in the body") —
   all about *pruning*. It says nothing about the two rules that decide whether a skill fires at
   all: **imperative phrasing** ("Use this skill when…", not "This skill does…") and **user intent
   over implementation**. Nor does it carry the "err on the side of pushy" rule — explicitly listing
   contexts where the skill applies *including when the user does not name the domain*. And there is
   no method for testing a description, only taste.

2. **Instruction patterns.** The spec's best-practices guide names six reusable structures —
   gotchas sections, output templates, checklists, validation loops, plan-validate-execute, and
   bundled scripts — plus three calibration rules (match specificity to fragility; provide defaults
   not menus; procedures over declarations) and one sourcing rule (start from real expertise, not
   the model's general training knowledge). `write-better-skill` has none of them.

The **gotchas** pattern is the highest-value gap for this repo specifically. `memory/learnings.md`
already holds exactly the material a gotchas section is made of — the vacuous-assertion family (7
instances), the worktree/`isolation` trap, `$CLAUDE_PROJECT_DIR` being empty in an agent's Bash
call — and none of it flows back into the skills where an agent would read it *before* hitting the
situation.

**Restated intent**:
> Give `write-better-skill` the description-triggering discipline and the instruction-pattern
> library from the Agent Skills creation guides, delivered behind context pointers so `SKILL.md`
> stays legible, and make `teach` consult them when it drafts.

**Out of scope**:
- Frontmatter constraints and the conformance test — **T078**, merged first
- README / CLAUDE.md / MEMORY.md registration — **T080**
- Rewriting the 30 existing skills' descriptions against the new rules. This task ships the rule and
  the method; applying them retroactively is a separate, much larger task the Supervisor will size
  after seeing this land. Record it as a follow-up, do not start it.
- Building the trigger-eval harness (the `eval_queries.json` + bash runner from the spec's
  optimizing-descriptions guide). See Cut list — the method is documented, the harness is not built.

**Requirement Refs**: `None — direct user request.` Same reason as T078.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-08-18)
- [x] Domain terms align with `PROJECT_SPEC.md` — "context pointer", "progressive disclosure",
      "leading word" are existing terms and must be reused, not re-coined
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] Requirement Refs: `None` recorded with a reason

---

## Dependencies & Reachability

**Depends on**: T078 — this task adds a `references/` directory to `write-better-skill`, and T078's
conformance test defines how bundled directories are discovered and validated. Starting before T078
merges risks writing files the test then rejects.

**Entry point**: `.claude/skills/write-better-skill/references/`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/skills/write-better-skill/references/descriptions.md` exists and states the four description rules: imperative phrasing ("Use this skill when…"); user intent over implementation mechanics; err on the side of pushy, naming contexts where the user does *not* say the domain word; stay under 1024 chars | "the two rules that decide whether a skill fires at all" |
| 2 | `references/descriptions.md` documents the trigger-eval method: ~20 labelled queries at roughly 8–10 should-trigger / 8–10 should-not-trigger; **near-miss negatives** (sharing keywords but needing something else) rather than obviously-irrelevant ones; 3 runs per query with a 0.5 trigger-rate threshold; a fixed ~60/40 train/validation split with proportional label mix; and the rule that the best iteration is chosen by **validation** pass rate, which may not be the last one produced | "there is no method for testing a description, only taste" |
| 3 | `references/descriptions.md` states the anti-overfitting rule explicitly: do not paste keywords from a failed query into the description — generalize to the category that query represents | same |
| 4 | `.claude/skills/write-better-skill/references/instruction-patterns.md` exists and documents all six patterns — gotchas, output templates, checklists, validation loops, plan-validate-execute, bundled scripts — each with a one-line "use when" and a short concrete example | "names six reusable structures … `write-better-skill` has none of them" |
| 5 | The gotchas entry states that gotchas belong **in `SKILL.md`**, not behind a pointer, because the agent may not recognize the trigger for a non-obvious issue — and that a correction the user has to make is the direct signal to add one | "the agent would read it *before* hitting the situation" |
| 6 | The gotchas entry names `memory/learnings.md` as this repo's existing store of gotcha material and instructs the author to mine it when writing a skill in a subsystem that file already covers | "none of it flows back into the skills" |
| 7 | `references/instruction-patterns.md` documents the three calibration rules: match specificity to fragility (free where several approaches are valid, prescriptive where operations are fragile or order matters); provide a default with a brief escape hatch rather than a menu; teach a reusable procedure rather than a specific answer | "three calibration rules" |
| 8 | A new `## Sourcing` section in `write-better-skill/SKILL.md` states the start-from-real-expertise rule: a skill drafted from the model's general training knowledge produces generic filler ("handle errors appropriately"); source material must be project-specific — execution traces, user corrections, git history, review comments, real failure cases — and names the two extraction routes (extract from a completed hands-on task; synthesize from existing project artifacts) | "one sourcing rule" |
| 9 | `write-better-skill/SKILL.md` reaches both new reference files through **context pointers that name the trigger condition** (per T078 AC6), e.g. "read `references/descriptions.md` when writing or revising a model-invoked `description`" — not a bare "see references/" | "delivered behind context pointers" |
| 10 | `.claude/skills/teach/SKILL.md` consults both new reference files at the matching points of its drafting workflow: `references/descriptions.md` when it drafts the `description`, `references/instruction-patterns.md` when it drafts the body | "make `teach` consult them when it drafts" |
| 11 | `write-better-skill/SKILL.md` is still ≤500 lines after the edit, and both new reference files are one level deep from the skill root | T078's budgets |
| 12 | The existing `## Failure Modes` and `## Pruning` sections are not duplicated into the new reference files — each meaning keeps a single source of truth | negative condition; `write-better-skill`'s own Pruning rule |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The repo after this task's edits | T078's `test_skill_spec_conformance.py` still passes over all skills | automated test |
| 2 | The full existing hook suite | Still passes | automated test |
| 3 | A new test `.claude/hooks/tests/test_skill_reference_pointers.py` asserting that every relative Markdown link inside any `.claude/skills/*/SKILL.md` resolves to a file that **exists**, and is at most one directory level below the skill root | automated test |
| 4 | **Mutation control A** — temporarily rename `references/descriptions.md` to `references/desc.md` without updating the pointer | SC3's test goes **RED** on the unresolved link. Revert after observing. | automated test, observed RED |
| 5 | **Mutation control B** — temporarily add a pointer to `references/deep/nested/x.md` (with the file created) | SC3's test goes **RED** on the depth rule, proving the depth assertion is not vacuous while the existence assertion passes. Revert after observing. | automated test, observed RED |
| 6 | **Mutation control C** — temporarily delete every relative link from all `SKILL.md` files in a scratch copy | SC3's test must go **RED** on an "asserted over zero links" guard, not pass silently. If it passes, the test is free-passing and the guard must be added. | automated test, observed RED |
| 7 | AC12 check: `grep` the two new reference files for distinctive phrases owned by `SKILL.md`'s Failure Modes and Pruning sections | Zero hits — no meaning duplicated | manual grep, output pasted |

> **SC4–SC6 are mandatory.** SC6 in particular targets the exact failure recorded in
> `memory/learnings.md`: *"a negative-grep test is free-passing if its file list is wrong — assert
> every file exists and that content-excluded lines are still present."* A link test that finds no
> links is the same defect wearing a different hat.

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  python3 -m pytest .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T079.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T079.md`.

---

## UI / Design Acceptance Criteria

Pure-documentation + test task, no UI component. All three UI Evidence rows are **☐ N/A** —
justification: this task adds two Markdown reference files and one pytest module; no rendered
surface, no design tokens, no viewports.

---

## Approach

**Pattern reference**: `.claude/skills/write-better-skill/SKILL.md` itself — match its register
exactly. It is terse, defines a term in bold on first use, and states rules as imperatives with a
one-line rationale. The new reference files must read as the same document continued, not as pasted
web documentation. Specifically: **do not** copy agentskills.io's PDF/CSV examples. Re-cut every
example against this repo — a gotchas example should use this repo's real gotchas, a validation-loop
example should use `python3 -m pytest .claude/hooks/tests/ -q`.

**Vital slice**: `references/instruction-patterns.md`'s gotchas entry plus AC6's instruction to mine
`memory/learnings.md`. That single link — from the repo's accumulated hard-won failures into the
skills an agent actually reads — carries most of this task's value. Everything else is good
reference; that one is the mechanism.

**Cut list**:
- The trigger-eval bash harness and `eval_queries.json` from the spec's guide — documented as a
  method, not built. Building it means running `claude -p` 60 times per skill against 30 skills;
  that is its own task with its own cost profile, and the method is useful to a human running it by
  hand today. Recorded here so the omission is not mistaken for an oversight.
- Retroactive description rewrites across the 30 skills — see Out of scope.
- The spec's `evaluating-skills` guide (test cases / grading / output quality). Adjacent and
  genuinely useful, but it is a third body of guidance; folding it in here makes this task C3.
  **Follow-up candidate — the Supervisor will size it separately.**

Read `https://agentskills.io/skill-creation/best-practices` and
`https://agentskills.io/skill-creation/optimizing-descriptions` before drafting. Both are the source
of record for this task; do not work from a summary.

---

## Edge Case Checklist

- [ ] AC12 conflict: `write-better-skill`'s existing "Writing the description" subsection overlaps the new `references/descriptions.md`. Decide one home — recommended: leave the three pruning bullets inline (they are about context cost, which every author needs) and put triggering/eval behind the pointer (only some authors reach it). Whichever is chosen, the other must not restate it.
- [ ] `teach`'s workflow may already have a description step; AC10 must slot the pointer into it, not append a parallel step
- [ ] SC3's link test must not flag external `https://` links, anchor-only links (`#section`), or links inside fenced code blocks
- [ ] `write-better-skill` is at 140 lines today; AC8's Sourcing section plus two pointers must not push any *other* skill over budget — verify AC11 by running the test, not by eye
- [ ] The pack symlink case (CLAUDE.md: packs symlink skills into `.claude/skills/`) — SC3's link resolution must handle a symlinked skill root without reporting false unresolved links

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/write-better-skill/references/descriptions.md` | New — AC1–AC3 |
| `.claude/skills/write-better-skill/references/instruction-patterns.md` | New — AC4–AC7 |
| `.claude/skills/write-better-skill/SKILL.md` | Add `## Sourcing` (AC8); add two context pointers (AC9); de-duplicate the existing description subsection per the Edge Case Checklist |
| `.claude/skills/teach/SKILL.md` | Consult both reference files at the matching workflow points (AC10) |
| `.claude/hooks/tests/test_skill_reference_pointers.py` | New — SC3 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/tests/test_skill_spec_conformance.py` | T078 owns it; this task must pass it, not amend it |
| Any other `.claude/skills/*/SKILL.md` | Retroactive application is out of scope |
| `README.md`, `CLAUDE.md`, `memory/MEMORY.md` | T080 owns registration |
| `.claude/skills/craft-agent/SKILL.md` | It consults `write-better-skill` for the Fidelity Gate only; the new material is skill-drafting, not agent-drafting. Widening its reach is speculation. |

---

## Test Plan

1. Write `test_skill_reference_pointers.py` first. It should pass trivially today (no relative links
   exist yet) — **that is the free-pass condition**, so implement SC6's zero-links guard immediately
   and confirm it goes RED before any reference file is written.
2. Write both reference files; confirm the link test now finds and resolves them.
3. Run mutation controls SC4–SC6, observing each transition and reverting each.
4. Edit `SKILL.md` and `teach/SKILL.md`.
5. Run the full suite including T078's conformance test (SC1, SC2, AC11).
6. Run AC12's grep (SC7) and paste the output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — required)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T079.md` (Hard-Stop Gate 5)
- [ ] Mutation controls SC4–SC6 each observed and their output pasted
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (Supervisor only)
- [ ] Supervisor notified: task ready for Stage 4 review
