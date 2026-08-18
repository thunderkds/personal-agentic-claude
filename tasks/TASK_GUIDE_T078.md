# TASK_GUIDE — T078: Agent Skills spec conformance — write it down, then enforce it
**Date**: 2026-08-18
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: QA-Automation-Agent
**Agent guide**: `.claude/agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/qa.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C2 task, multi-file: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

> User request (2026-08-18, verbatim): *"following this documents as knowledge to enhance the skills,
> https://agentskills.io/home. Create branch, tasks, and update the README also."*

The Agent Skills format (agentskills.io) is the open standard this repo's 30 skills already
implement de facto. The Supervisor audited all 30 on 2026-08-18: **every one currently passes** the
spec's hard constraints (`name` matches parent directory, `description` ≤ 1024 chars, `SKILL.md`
≤ 500 lines). That compliance is **accidental, not enforced** — `write-better-skill`, the repo's
authoritative craft reference, does not state a single one of the spec's normative constraints, and
nothing tests them. The 31st skill can violate any of them silently.

**Restated intent**:
> Record the Agent Skills specification's normative constraints in `write-better-skill` so future
> skill authors are bound by them, and add an automated conformance test so the binding is checked
> rather than trusted.

**Out of scope** (this task explicitly does NOT do):
- Description-triggering methodology and the instruction-pattern library — **T079**
- README / CLAUDE.md / MEMORY.md registration of the new contract — **T080**
- Rewriting or restructuring any of the 30 existing skills. They all pass today; this task adds the
  gate, it does not remodel what the gate now watches.
- The `allowed-tools` frontmatter field. Marked Experimental by the spec, unused in this repo, and
  the spec itself says support varies by implementation — recording it as a rule would be
  speculation (Karpathy: Simplicity First).

**Requirement Refs**: `None — direct user request, not traced to a PRD FR/NFR.` This repo's PRD
predates the Agent Skills standard; the Supervisor accepted the request as the requirement source.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-08-18)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "skill", "progressive disclosure",
      "context pointer" are already glossary terms; "conformance" is new and defined in AC1
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: `None` recorded with a reason above

---

## Dependencies & Reachability

**Depends on**: `None` — branched off `main`, independent of T074/T075.

> Note: T075 (P0) has the test suite RED on `feat/t074-hook-wiring-preflight`. That branch is not an
> ancestor of this one, so this task's suite runs green off `main`. Pushing is still gated
> repo-wide until T075 lands.

**Entry point**: `.claude/hooks/tests/test_skill_spec_conformance.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A new `## Agent Skills Spec Conformance` section exists in `.claude/skills/write-better-skill/SKILL.md` stating every normative `name` rule verbatim from the spec: 1–64 chars; unicode lowercase alphanumeric (`a-z`, `0-9`) and hyphens only; must not start or end with `-`; must not contain `--`; must match the parent directory name | "record the spec's normative constraints" |
| 2 | The same section states `description` is required, non-empty, and max 1024 characters | same |
| 3 | The same section records the optional fields `license`, `compatibility` (max 500 chars), and `metadata` (string→string map), each with one line on when it applies — and states that `allowed-tools` is deliberately out of scope as Experimental | same |
| 4 | The same section records the progressive-disclosure budgets as **spec numbers, not prose**: `SKILL.md` ≤ 500 lines and ≤ 5,000 tokens; metadata ≈100 tokens loaded at startup for every skill; resources loaded on demand | same |
| 5 | The same section records the bundled-directory convention (`scripts/`, `references/`, `assets/`) and the rule that file references use relative paths from the skill root and stay **one level deep** | same |
| 6 | The existing "Information Hierarchy" section's vague claim that "the pointer's *wording* decides how reliably the agent reaches the material" is made concrete: a context pointer must name the **trigger condition** for loading the file (spec example: "Read `references/api-errors.md` if the API returns a non-200 status code"), never a bare "see references/ for details" | "future skill authors are bound by them" |
| 7 | `.claude/hooks/tests/test_skill_spec_conformance.py` exists and asserts, for **every** directory under `.claude/skills/`, that: `SKILL.md` exists; frontmatter parses; `name` satisfies all five rules in AC1; `description` is present, non-empty and ≤1024 chars; `SKILL.md` is ≤500 lines; `compatibility` if present is ≤500 chars | "add an automated conformance test" |
| 8 | The test discovers skill directories from the filesystem — it must NOT contain a hardcoded list of skill names, so a 31st skill is covered the moment it is added | "the 31st skill can violate any of them silently" |
| 9 | The test asserts the discovered skill count is > 0 and that a known skill (`write-better-skill`) is among those discovered, so an empty or mis-rooted glob cannot free-pass | negative/boundary condition |
| 10 | The Registration checklist in `write-better-skill` gains one line pointing at the conformance test as the check for the frontmatter rules, replacing the reader's need to re-derive them | "the binding is checked rather than trusted" |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The repo as-is, 30 skills, unmodified | `test_skill_spec_conformance.py` passes — all 30 conform | automated test |
| 2 | The full existing hook suite | Still passes; no regression from the new test file | automated test |
| 3 | **Mutation control A** — temporarily create `.claude/skills/Bad--Name/SKILL.md` with `name: Bad--Name` | The conformance test goes **RED**, naming uppercase, consecutive-hyphen AND directory-match violations. Revert after observing. | automated test, observed RED |
| 4 | **Mutation control B** — temporarily pad any existing `SKILL.md` past 500 lines | The conformance test goes **RED** on the line budget. Revert after observing. | automated test, observed RED |
| 5 | **Mutation control C** — temporarily point the test's discovery root at an empty temp directory | The test goes **RED** via AC9's non-empty/known-skill guard, not silently green over zero skills. Revert after observing. | automated test, observed RED |
| 6 | **Mutation control D** — delete AC9's guard assertions, then repeat control C | If the test now passes over zero skills, AC9's guard was the only thing standing between this suite and a vacuous pass. Confirm it goes GREEN (proving the guard is load-bearing), then restore. | automated test, observed GREEN then restored |
| 7 | `write-better-skill/SKILL.md` after the edit | Still ≤500 lines and its own `description` still ≤1024 chars — the skill that states the budget must live inside it | the new conformance test itself |

> **SC3–SC6 are mandatory.** `memory/learnings.md` records the vacuous-assertion family at **7
> instances**; the newest was a control that never executed and one that attacked a metric from only
> one direction. SC3/SC4 attack the conformance test from two independent directions (name rules,
> size budget); SC5/SC6 attack the *discovery* layer, which is exactly the "a negative-grep test is
> free-passing if its file list is wrong" failure already recorded in this repo. Do not skip SC6
> because SC5 passed — SC5 alone does not prove the guard caused the RED.

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  python3 -m pytest .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T078.md`, copied from
> `templates/TASK_REVIEW_template.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T078.md`.

---

## UI / Design Acceptance Criteria

Pure-documentation + test task, no UI component. All three UI Evidence rows are **☐ N/A** —
justification: this task changes one Markdown reference file and adds one pytest module; there is no
rendered surface to regress, no design token to comply with, and no viewport to lay out.

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_guide_sections.py` — imitate its structural parsing
of Markdown/frontmatter and its per-file parametrized assertion style. For the frontmatter parse
itself, imitate whatever that file already does rather than adding a YAML dependency; the repo's
hooks are stdlib-only.

**Vital slice**: the conformance test over the five hard constraints (name, description, line
budget). That is the part carrying the value — it converts accidental compliance into checked
compliance.

**Cut list**:
- `skills-ref validate` (the spec's own reference validator) — not vendored. It is a Go/JS tool from
  an external repo; adding a toolchain dependency to gate 30 Markdown files fails Simplicity First.
  The test reimplements the five constraints in ~40 lines of stdlib Python.
- Token counting for the 5,000-token budget — the line budget is the checkable proxy; a real
  tokenizer is a dependency for a soft recommendation. Recorded in the skill as guidance, not tested.
- `allowed-tools` validation — see Out of scope.

Read the spec sections at `https://agentskills.io/specification` (frontmatter table, `name` field,
`description` field, progressive disclosure, file references) before editing. Do **not** paraphrase
the constraints from memory — the whole point of the task is that the numbers are exact.

---

## Edge Case Checklist

- [ ] A skill directory containing no `SKILL.md` at all (e.g. a stray folder) — must FAIL loudly, not be skipped
- [ ] `__pycache__/` and other non-skill directories under `.claude/skills/` — `delivery-report/__pycache__` exists today at one level *below* a skill; confirm discovery globs skill dirs only and does not treat a nested cache dir as a skill
- [ ] A multi-line YAML `description` (folded `>` or `|` block) — length must be measured on the joined value, not the first line
- [ ] A `description` containing a `:` or `#` — must not break a naive parser
- [ ] Symlinked skill directories (packs symlink into `.claude/skills/` per CLAUDE.md) — decide and document whether symlinks are followed; a broken symlink must not crash the test
- [ ] Frontmatter absent entirely, or a file whose first line is not `---`
- [ ] Line count measured consistently (trailing newline / no trailing newline must not shift a 500-line file across the boundary)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/write-better-skill/SKILL.md` | Add `## Agent Skills Spec Conformance` section (AC1–AC5); sharpen the context-pointer rule in `## Information Hierarchy` (AC6); add one Registration checklist line (AC10) |
| `.claude/hooks/tests/test_skill_spec_conformance.py` | New — the conformance test (AC7–AC9) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| Any `.claude/skills/*/SKILL.md` other than `write-better-skill` | All 30 pass today. Editing one to "improve" it is an orthogonal change (Karpathy: Surgical Changes). If the test finds a real violation, STOP and report to the Supervisor — do not fix it inline. |
| `.claude/hooks/tests/test_memory_channel_and_budget.py` | T075 owns it and is in flight; touching it would collide |
| `README.md`, `CLAUDE.md`, `memory/MEMORY.md` | T080 owns registration |
| `.claude/skills/teach/SKILL.md` | T079 owns it |

---

## Test Plan

1. Write `test_skill_spec_conformance.py` first (RED — it does not exist, so the constraints are
   unstated and unchecked). Confirm it passes over the current 30 skills.
2. Run mutation controls SC3–SC6 in order, observing each RED/GREEN transition and reverting each
   before the next. Record the actual output of each.
3. Edit `write-better-skill/SKILL.md` for AC1–AC6 and AC10.
4. Re-run the full suite; confirm `write-better-skill` still satisfies its own budgets (SC7).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — required)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T078.md` (Hard-Stop Gate 5)
- [ ] Mutation controls SC3–SC6 each observed and their output pasted
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (Supervisor only)
- [ ] Supervisor notified: task ready for Stage 4 review
