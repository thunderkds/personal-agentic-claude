# TASK_GUIDE — T046: Pattern reference field in TASK_GUIDE_template.md
**Date**: 2026-07-24
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. C1 single-file-plus-test task — skip `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

From a scan of `https://code.claude.com/docs/en/prompt-library` (2026-07-24). The library's
"Follow an existing pattern" entry teaches:

> *"Point at code you already like. Without a reference, Claude defaults to general best practices.
> With one, it matches the conventions your codebase actually uses."*

A grep of `templates/`, `.claude/agents/`, and `CLAUDE.md` for `reference implementation` /
`existing pattern` / `look at how` returns **zero hits**. The Karpathy **Surgical Changes**
principle already says "Match existing styles perfectly" — but that is a principle with no
operational hook. A spawned agent is told to match a style it has not been pointed at.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Every TASK_GUIDE gains one advisory field naming an existing file the implementing agent should
> imitate, so "match the existing style" arrives as a concrete, grep-able file pointer instead of a
> general instruction the agent has to infer.

**Out of scope** (what this task explicitly does NOT do):
- The UI render→compare→fix self-check loop (prompt-library gap #2) — deferred; this repo has run
  zero UI tasks, so it would be speculative abstraction (Simplicity First)
- A Supervisor→agent steering/correction protocol (prompt-library gap #3) — deferred, no observed need
- Any change to `.claude/agents/*.md` — the guide is already in every agent's mandatory read list,
  so a field inside it reaches the agent without a second edit
- Any hook enforcement, Hard-Stop Gate, or merge-gate check — this field is **advisory**, matching
  the existing `Entry point` / `Depends on` precedent
- Backfilling the field into the 40+ existing `tasks/TASK_GUIDE_T0*.md` files

**Requirement Refs**: this repo has no `PRD.md`. Traceability:
- **Prompt library** (`https://code.claude.com/docs/en/prompt-library`) — `follow-an-existing-pattern`
  entry, `src: best-practices`
- **`CLAUDE.md` → Karpathy Engineering Principles → Surgical Changes** — "Match existing styles
  perfectly"; this task supplies the missing operational hook
- **`memory/learnings.md`** — *"'Already covered' must mean reaches-the-context"*: the principle
  lives in `CLAUDE.md`, which is **not** in the sub-agent read list, so it currently reaches no
  sub-agent. `TASK_GUIDE_Txxx.md` **is** in that list (Mandatory Startup step 3)
- **Precedent in-repo**: `tasks/TASK_GUIDE_T043.md:143` opens its Approach with *"Reuse the pattern
  that already works"* and names `pre_agent_validate_guide.py:extract_structural_task_ids` — the
  behavior this task makes routine instead of incidental

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor — user approved scoping to
      gap #1 only, explicitly rejecting gaps #2 and #3)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "advisory field" follows the established
      `Entry point` / `Depends on` convention; no new domain terms introduced
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs resolve (no `PRD.md` in this repo — traceability listed above)

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `**Pattern reference**:` — the literal string added to the template and asserted by
the test. Grep-able in `templates/TASK_GUIDE_template.md`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_GUIDE_template.md` contains a `**Pattern reference**:` field carrying a placeholder and a concrete in-repo example | "concrete, grep-able file pointer" |
| 2 | The field sits inside the `## Approach` section — not merely somewhere in the file | field must be read at the point of implementation guidance |
| 3 | The field defines an explicit opt-out value for genuinely novel work, so it is never ambiguously blank | advisory, mirrors `Entry point`'s `Standalone — N/A` escape hatch |
| 4 | (negative) The test FAILS if the field is deleted, or if it is present but outside the `## Approach` section | guards AC1 + AC2 against a vacuous assertion |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Template with the field inside `## Approach` | all tests pass | automated test |
| 2 | Field string deleted from the template | test fails (RED observed) | automated test + manual mutation |
| 3 | Field present but relocated outside `## Approach` (e.g. into `## Test Plan`) | test fails (RED observed) | automated test + manual mutation |
| 4 | Opt-out wording removed | test fails (RED observed) | automated test + manual mutation |

> Per `memory/learnings.md` — *"An assertion never observed failing is not evidence"* (3 prior
> occurrences: T036/T042/T039). Each of Success Criteria 2–4 must be **actually mutated and observed
> RED**, then reverted. Pasting only a green run is not acceptable evidence for this task.

### Verification Command (exact, runnable)

```bash
CLAUDE_ACTIVE_TASK=T046 python3 -m pytest .claude/hooks/tests/test_task_guide_template_pattern_reference.py -q
```

> `CLAUDE_ACTIVE_TASK` must be exported — per `memory/MEMORY.md`, a `Bash` command is never
> attributed after T043, so without it the merge gate finds no trace record.

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [paste the RED output for each of Success Criteria 2, 3, 4] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "generated a guide from the template, field present and populated — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | [`python3 -m pytest .claude/hooks/tests/ -q`] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure-infra task, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure-infra task, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure-infra task, no UI component |

---

## Approach

**Pattern reference**: `templates/TASK_GUIDE_template.md` lines 50–63 (`## Dependencies &
Reachability`) — the `Depends on:` / `Entry point:` fields. Copy their exact shape: a bolded
label, a bracketed placeholder, a `>` example line, and an explicit escape-hatch value. Test style:
`.claude/hooks/tests/test_task_guide_template_verify_row.py` — structural assertion against the real
template file plus negative fixtures that prove the assertion can fail.

Add **one field** to the `## Approach` section of `templates/TASK_GUIDE_template.md`:

```
**Pattern reference**: [path/to/existing/file.ext — what to imitate about it] or `None — no comparable prior art in this repo` (with a one-line reason)
> Example: `Pattern reference: .claude/hooks/pre_agent_validate_guide.py — structural ID extraction, fail-open error handling`
> Point at code that already works and should be imitated. Without one, the agent falls back to
> generic best practice instead of this repo's conventions (Karpathy: Surgical Changes).
```

Then write `.claude/hooks/tests/test_task_guide_template_pattern_reference.py` asserting AC1–AC4.
The section-scoping assertion (AC2) must slice the template between `## Approach` and the next `##`
heading and search **only that slice** — a bare `in template` check would pass even if the field
drifted to the bottom of the file, which is exactly the vacuous-assertion trap this repo has hit
three times.

**Why `## Approach` and not `## Dependencies & Reachability`**: the field is implementation
guidance, not a dependency or a reachability claim. Filing it under a section named for something
else is the kind of misnaming that later makes the field invisible to whoever reads it.

---

## Edge Case Checklist

- [ ] The `## Approach` slice regex must anchor on `^## ` with `re.MULTILINE` — per
      `memory/learnings.md`, an unanchored `(?=##)` lookahead truncates at the first inline `##`
      anywhere in a row (the T045 defect). This guide's own text quotes `##`; do not let it self-trip
- [ ] The test must read the real `templates/TASK_GUIDE_template.md`, never an inline copy of it —
      a test asserting against its own fixture proves nothing about the shipped template
- [ ] Adding a row to `PROJECT_KANBAN.md` must not quote a `###` heading marker (T045 defect,
      still open) — keep the T046 row free of `###`
- [ ] The field must not be worded as a requirement (`must name a file`) — genuinely novel work
      exists, and a mandatory field with no honest answer gets filled with noise
- [ ] Do not add the field to the Completion Checklist or any gate — advisory only, per Out of scope

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_GUIDE_template.md` | add `**Pattern reference**:` field + example + rationale inside `## Approach` |
| `.claude/hooks/tests/test_task_guide_template_pattern_reference.py` | new — asserts AC1–AC4 with negative fixtures |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | out of scope; the field reaches agents via the guide, not the Supervisor doc |
| `.claude/agents/*.md` | out of scope per Requirement; guide is already in the mandatory read list |
| `.claude/hooks/*.py` (non-test) | advisory field, no hook enforcement — Out of scope |
| `tasks/TASK_GUIDE_T0*.md` (existing) | no backfill — Out of scope |
| `templates/TASK_GUIDE_template.md` §`Evidence`, §`UI / Design`, §`Completion Checklist` | untouched — this task adds one field to `## Approach` only (Surgical Changes) |

---

## Test Plan

1. Write `test_task_guide_template_pattern_reference.py` **first** (red), covering AC1–AC4.
2. Confirm RED before the template edit — the field does not exist yet, so AC1 must fail.
3. Add the field to `templates/TASK_GUIDE_template.md` `## Approach`. Confirm GREEN.
4. Mutate and observe RED for each of Success Criteria 2, 3, 4 — delete the field; move it out of
   `## Approach`; strip the opt-out wording. Revert after each. Paste all three RED outputs.
5. Regression: `CLAUDE_ACTIVE_TASK=T046 python3 -m pytest .claude/hooks/tests/ -q` — full suite green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — hub file)
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] All three negative controls observed RED and pasted (Success Criteria 2, 3, 4)
- [ ] `Skill({ skill: "verify" })` run — a guide generated from the edited template carries the field
- [ ] Supervisor notified: task ready for Stage 4 review
