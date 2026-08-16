# TASK_GUIDE — T071: Vital Slice — extend Simplicity First in the guaranteed channel
**Date**: 2026-08-16
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` — in particular the **`Vital Slice`** and **`Cut List`** glossary rows added for this task
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide (`.claude/agents/common-infrastructure.md`)
6. Read `docs/ddr/0005-vital-slice-extends-simplicity-first.md` **in full** — it is the specification for this task, and its "Decision" section is normative. This guide implements it; where they appear to differ, STOP and ask the Supervisor.
7. C2 task: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Original user request (verbatim, across the Stage 0.5 session):

> "focus on parento principal (80/20 rules) for the effectively improve. The same idea with the
> karpathy in this repos" … "this repos is the kit, so we will apply it to enhance this kit to make
> another repos that use this kit" … "the important things for me to looks forward when apply parento
> principal is the quote that '80% of the software's outcomes, value, or performance overhead stem
> from a vital 20% of its codebase' so it means that, when delivery a feature, we just need 20% of
> the code to get 80% of quality." … "i think cut will be better, but should make sure the feature
> work correctly, or i think it will be the optional steps for making the effectively code, cause
> karpathy covered it from start."

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> A repo that installs this kit should, at feature-delivery time, build the **Vital Slice** — the
> subset of a requested feature's implementation surface carrying most of its value — and record what
> it deliberately did not build as a **Cut List**. The rule reaches the implementing agent through the
> guaranteed channel (the role guide), extends Simplicity First rather than becoming a fifth
> principle, and is bounded so that "cut" can never mean "cut an Acceptance Criterion".

**Out of scope** (what this task explicitly does NOT do):
- No hook, no gate, no merge-gate check, no CI enforcement — advisory only, following T046's `Pattern reference` precedent (DDR-0005 §5).
- **No backfill.** The ~35 existing `tasks/TASK_GUIDE_T0*.md` files stay byte-identical (T064's fallback-not-migration precedent).
- No fifth Karpathy principle, and no new skill. Both were evaluated and rejected in DDR-0005's Alternatives table.
- No change to any Acceptance Criterion, pipeline stage, or Hard-Stop Gate.
- Does not resolve the unrelated open item that `memory/MEMORY.md` is near its 50,000-char ratchet.

**Requirement Refs**: `PRD.md` does not exist in this repo (verified 2026-08-16); the authoritative
source is **DDR-0005** plus the `BRAINSTORMING_LOG.md` session dated 2026-08-16. The Requirement
Fidelity Gate row for `PRD.md` is therefore N/A and is marked so below rather than left unchecked.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user selected Path C and gave four explicit rulings (all four role guides / per-role wording / `Vital Slice` with the number confined to `CLAUDE.md` / +8 lines per guide)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — `grill-with-docs` run 2026-08-16; `Vital Slice` and `Cut List` written to the glossary during that session
- [x] Every Acceptance Criterion below traces to a line in the Requirement or to DDR-0005
- [x] N/A — no `PRD.md` in this repo; DDR-0005 is the requirement source of record

---

## Dependencies & Reachability

**Depends on**: `None` — DDR-0005 is committed alongside this guide, not a separate task.

**Entry point**: `## Simplicity First (your defining constraint)` — the literal, grep-able heading
that must exist in all four role guides after this task. It exists today only in `backend.md` and
`frontend.md`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | All four role guides (`backend.md`, `frontend.md`, `common-infrastructure.md`, `qa.md`) contain the heading `## Simplicity First (your defining constraint)` | User ruling: all four; DDR-0005 §1 |
| 2 | Each of the four sections states the Vital Slice rule in **role-specific** wording — no two guides share a sentence of ≥12 consecutive words in the added text | User ruling: "written per-role"; DDR-0005 §1 |
| 3 | Each of the four sections states the **AC-immunity** rule: the cut narrows implementation surface only — never an Acceptance Criterion, never a pipeline stage, never a Hard-Stop Gate | User constraint "must work correctly"; DDR-0005 §4 |
| 4 | **Negative, file-wide**: no role guide and not `templates/TASK_GUIDE_template.md` contains `80/20`, `80%`, `20%`, or `Pareto` | User ruling: number only in `CLAUDE.md`; DDR-0005 §3 |
| 5 | `CLAUDE.md` contains exactly one mention of the 80/20 heuristic, in the Simplicity First row, explicitly labelled a heuristic and not a target | DDR-0005 §3 |
| 6 | **Byte-identity, positive**: the `KARPATHY_TABLE` constant in `.claude/hooks/tests/test_agent_guide_dedup.py` is unmodified, and its Simplicity First row still matches all four role guides verbatim. **Amended 2026-08-16** — this AC constrains the `KARPATHY_TABLE` constant and every assertion body; it does **not** forbid repointing the two baseline refs named in AC14, which is an explicit user ruling | DDR-0005 §2; amended by AC14 |
| 7 | **Byte-identity, positive**: `scripts/test-agent-template.sh` is unmodified and still passes; all four `grep -qF` operational-command strings are found | DDR-0005 §2 |
| 8 | **Byte-identity, positive**: the two `If 200 lines can be 50` occurrences that `test_memory_channel_and_budget.py` requires still exist and are untouched | DDR-0005 §2 |
| 9 | `templates/TASK_GUIDE_template.md`'s `## Approach` section gains a `Vital slice` field and a `Cut list` field, in the shape of the existing `Pattern reference` field | DDR-0005 §5 |
| 10 | `CLAUDE_LEGACY.md`'s Simplicity First row receives the matching additive edit, in the **same commit** as the `CLAUDE.md` edit | Recorded sync policy; DDR-0005 §3 |
| 11 | **Line cap**: `backend.md` ≤ 145, `frontend.md` ≤ 142, `common-infrastructure.md` ≤ 137, `qa.md` ≤ 129, `CLAUDE.md` ≤ 200, `templates/TASK_GUIDE_template.md` ≤ 197. If the content will not fit, **tighten the prose — do not raise a cap** | User ruling: +8/guide; DDR-0005 §6 |
| 12 | **Negative, no-enforcement**: no file under `.claude/hooks/` is modified, and no test asserts that the `Vital slice` or `Cut list` field is non-empty | Out of scope; DDR-0005 §5 |
| 13 | **Negative, no-backfill**: every pre-existing `tasks/TASK_GUIDE_T0*.md` is byte-identical to its state at HEAD | Out of scope; T064 precedent |
| 14 | **Added 2026-08-16.** In `.claude/hooks/tests/test_agent_guide_dedup.py`, exactly two module-level constants change: `T070_BASELINE_REF` (`9f3f2e9` → T071's `CLAUDE.md` edit commit) and `BASELINE_REF` (`8fc4dd2` → the same T071 commit). **Repointed, not deleted** — no assertion body, no parametrize list and no `KARPATHY_TABLE` byte is touched, and after the change both tests still fail if the file they guard is mutated | User ruling 2026-08-16; T070 precedent |
| 15 | **Added 2026-08-16, mutation-verified.** After repointing, `test_ac5_ac10_out_of_scope_files_are_byte_identical_to_the_baseline` and `test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline` must each be shown **RED** by mutating the file they guard (append a line to `CLAUDE.md`; append ~400 chars to `common-infrastructure.md`). A repointed pin that no longer discriminates is a vacuous assertion, and this repo has 7 recorded instances | Guards against the repoint silently disarming the pin |

> **AC11 baselines, captured 2026-08-16** (`wc -l`): backend 137, frontend 134, common-infrastructure
> 129, qa 121, `CLAUDE.md` 198, `templates/TASK_GUIDE_template.md` 193. The caps above are baseline
> +8 / +2 / +4 as ruled. These are **as-of-this-task** numbers used as a budget, deliberately **not**
> committed as a standing invariant — the recorded T065 lesson is that a scope guard pinned as an
> invariant blocks what it guarded. AC11's test may pin them; it must be written to read the baseline
> from a pinned commit ref, or be deleted after review. State which at Stage 4.

> ### Stage 3 amendment, 2026-08-16 — why AC14/AC15 exist
>
> The first spawn **halted before implementation** and was right to. Two live invariants made the
> original AC table unsatisfiable, and the Supervisor verified both independently rather than taking
> the report at face value:
>
> 1. `test_ac5_ac10_…byte_identical` pins `CLAUDE.md` byte-for-byte to `9f3f2e9`, so **any** edit is
>    RED — while AC5 mandates an edit and AC6 forbade touching the test. No implementation satisfies
>    both; only a test change does. **This is a Stage 2 defect, not an implementation problem.**
> 2. `test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline` leaves **222 chars** of headroom
>    on `common-infrastructure.md` (backend 1,884 · frontend 1,865 · qa 1,907), and
>    `test_t069_ac9_report_per_role_pair_size` leaves **362 chars** on every role. The ruled +8-line
>    budget is ~600 chars, so **it was unreachable for all four roles**. The Stage 2 sweep checked for
>    pinned *strings* and never checked for *size invariants* — the recorded "an AC written against a
>    file's older shape" pattern, repeating.
>
> The user ruled **repoint both baselines** (option A). This is not weakening a guard: T070 hit the
> identical `CLAUDE.md` pin and repointed it to its own edit commit, and that precedent is documented
> in the test file's own comments. The substantive argument for repointing `BASELINE_REF` in
> particular: AC7 asserts these files stay *strictly smaller forever*, which was only a meaningful
> question during T066's review. As a standing assertion it forbids ever adding a legitimate sentence
> to a role guide — the **5th occurrence** of T065's "scope guard committed as an invariant". The
> sibling test directly below it, `test_t069_ac9`, carries a comment explicitly refusing that shape
> for exactly this reason. AC15 exists because a repointed pin is the easiest possible place to
> accidentally create a vacuous assertion.

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The four role guides after the edit | All four contain the section heading and a role-specific Vital Slice + AC-immunity statement | automated test |
| 2 | `grep -rn '80/20\|80%\|20%\|Pareto'` over the four role guides and the TASK_GUIDE template | **Zero hits** | automated test (negative) |
| 3 | `grep -c` for the 80/20 heuristic in `CLAUDE.md` | Exactly 1 | automated test |
| 4 | The existing suite, unmodified | Still passes — including `test_agent_guide_dedup.py`, `test_memory_channel_and_budget.py` and `scripts/test-agent-template.sh` | automated test |
| 5 | **Mutation control**: delete the AC-immunity sentence from one role guide | The AC3 test goes **RED** | mutation control, must be observed |
| 6 | **Mutation control**: insert the literal `20%` into `qa.md` | The AC4 negative goes **RED** | mutation control, must be observed |
| 7 | **Mutation control**: pad `backend.md` past its cap with **blank** lines | The AC11 test goes **RED** | mutation control — T067's P3 was exactly this: `rstrip` made blank-line padding invisible while non-blank padding was caught. **Pad both ways.** |
| 8 | Copy the same paragraph into two role guides | The AC2 per-role test goes **RED** | mutation control |

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  python -m pytest .claude/hooks/tests/ -q > /tmp/t071.log 2>&1; echo "pytest exit=$?"; \
  bash scripts/test-agent-template.sh; echo "shell exit=$?"; tail -5 /tmp/t071.log
```

> Do **not** pipe pytest into `tail` behind `&&` — `tail` always exits 0 and `&&` gates on the last
> command of the pipeline, which is how this repo once committed a red suite.

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T071.md` (copy `templates/TASK_REVIEW_template.md`).
> All three UI/Design rows are **☐ N/A — pure documentation task, no UI component** (Hard-Stop Gate 6).

---

## Demonstration

> See `tasks/TASK_REVIEW_T071.md`.

---

## Approach

**Pattern reference**: `.claude/agents/backend.md` (the existing `## Simplicity First (your defining
constraint)` section, line 48) — imitate its length, its imperative second-person voice, and the way
it grounds an abstract principle in that role's concrete artifacts. For the template fields, imitate
`templates/TASK_GUIDE_template.md`'s `Pattern reference` field (line 145): one bold field name, an
`or None` escape hatch, and a blockquoted example line.

**Reasoning.** The whole design turns on one measured fact: `CLAUDE.md` is not in the sub-agent read
set, while the role guide **is** (the harness auto-loads it as the system prompt). T069 had already
moved the Karpathy table into the role guides for exactly this reason — and in doing so byte-pinned
those table rows in two places. So the rule goes into the *prose section beside* the pinned table,
never into the table. This is the recorded rule *"when a test pins prose, fix the prose around it,
not the test"* applied by **placement**, which is why AC6/AC7/AC8 are positive byte-identity
assertions rather than test edits.

`common-infrastructure.md` and `qa.md` have no such section and will have one created. This is the
T066 shape — the smallest leaf is missing the shared section entirely — and it is why the user ruled
all four rather than the two that already had it.

Suggested per-role angle (guidance, not dictation — AC2 requires genuinely different wording):
- **backend** — speculative generality in service and data-access layers: config flags nobody set, interfaces with one implementation, pagination on an endpoint returning three rows.
- **frontend** — component surface: variants, themes and props built ahead of a second caller.
- **common-infrastructure** — the sharpest case: shared services are where generality accumulates because "someone might need it", and this role writes them first, before any consumer exists to prove the need.
- **qa** — the inverse duty: QA owns the oracle that the cut still works, and is the role that must reject an inverted Cut List. Uncovered error handling is not a Vital Slice, it is a hole.

---

## Edge Case Checklist

- [ ] A cut list that names error handling, validation or boundary conditions — **inverted ranking**; that is where correctness lives and it is exactly the code that looks like the disposable 80%. Note `templates/TASK_GUIDE_template.md`'s AC row 3 is already templated as `[negative / boundary condition]`.
- [ ] A task with a single AC and no meaningful surface — the fields must be legitimately `None` without tripping anything.
- [ ] A bugfix-flavored guide — a Vital Slice on a bug fix is close to nonsense; a fix is at a root cause or it is not (T067). Do not add these fields to the bugfix flavor.
- [ ] `CLAUDE_LEGACY.md` drift — the sync policy has been missed before; AC10 requires the same commit.
- [ ] The word `20%` leaking into an operative file — AC4 is file-wide and negative for this reason.
- [ ] AC11's caps becoming a standing invariant that blocks future edits (T065's recorded failure).
- [ ] A test asserting the advisory fields are filled — that would silently convert this into the gate DDR-0005 explicitly refused.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/agents/backend.md` | +≤8 lines in the existing `## Simplicity First` section |
| `.claude/agents/frontend.md` | +≤8 lines in the existing `## Simplicity First` section |
| `.claude/agents/common-infrastructure.md` | **create** the section, +≤8 lines |
| `.claude/agents/qa.md` | **create** the section, +≤8 lines |
| `CLAUDE.md` | +≤2 lines — the sole 80/20 mention, additive; the pinned row text unchanged |
| `CLAUDE_LEGACY.md` | matching additive edit, same commit |
| `templates/TASK_GUIDE_template.md` | +≤4 lines — `Vital slice` + `Cut list` in `## Approach` |
| `.claude/hooks/tests/test_vital_slice.py` | **new** — AC1–AC13 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/tests/test_agent_guide_dedup.py` | **Amended** — AC14 permits changing exactly two module-level baseline refs in it. Everything else (assertion bodies, parametrize lists, `KARPATHY_TABLE`) stays untouched |
| `scripts/test-agent-template.sh` | AC7 — same reason |
| `.claude/hooks/tests/test_memory_channel_and_budget.py` | AC8 — it requires the "If 200 lines can be 50" lines to survive |
| Any file under `.claude/hooks/` (non-test) | AC12 — advisory by design, no enforcement |
| `tasks/TASK_GUIDE_T0*.md` (pre-existing) | AC13 — historical record, no backfill |
| The Karpathy compact table row in any role guide | The whole design depends on it staying byte-identical |
| `PROJECT_SPEC.md` glossary rows for Vital Slice / Cut List | Already written during grilling; do not re-word |

---

## Test Plan

New `test_vital_slice.py` covering AC1–AC13. Then, non-negotiably, **run every mutation control in
the Success Criteria table above and observe RED before reverting** — this repo has **7 recorded
vacuous-assertion incidents**, and the two most relevant are live here: a negative-grep test is
free-passing if its file list is wrong (so assert every target file **exists** before asserting
absence), and a line-cap assertion using `rstrip("\n")` is blind to blank-line padding (so pad both
blank and non-blank).

Do not write a helper that re-implements the logic under test; call the real thing. A helper reaching
for a module's constants rather than its functions is the tell.

Full suite must be green: `python -m pytest .claude/hooks/tests/ -q` (405 passed at HEAD) **plus**
`bash scripts/test-agent-template.sh`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T071.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] All mutation controls observed RED, then reverted — **commit the fix before mutating**, or `git checkout` will silently revert it along with the mutation
- [ ] Lint / `sh -n` clean
- [ ] Supervisor notified: task ready for Stage 4 review

> **Stage 4/5 gates are the Supervisor's to run, not yours.** A sub-agent has no `Skill` tool, so
> `code-review`, `security-review` and `verify` cannot be invoked from here — do not record a result
> for them. Report completion and stop.
