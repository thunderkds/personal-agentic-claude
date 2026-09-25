# TASK_GUIDE — T129: Spawn prompts name the mandatory startup reads, and the agent confirms them
**Date**: 2026-09-25
**Complexity Level**: C1
**Risk Level**: Low — instruction text in one skill, one non-blocking hook warning
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `tasks/TASK_REVIEW_T125.md` § "AC9" and `skills/craft-spawn-prompt/SKILL.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25: approved T129 on the integration branch (*"yes, do it in this branch"*), after the
Supervisor's description: spawn prompts name the mandatory startup reads explicitly, and the agent
confirms them in its final report (Supervisor's recommendation, included as the default).

**Observed defect** (`tasks/TASK_REVIEW_T125.md` § AC9): the headless T126 agent read its TASK_GUIDE but
**not** `PROJECT_SPEC.md` or `agents/common-infrastructure.md` — a Permanent Rule (`CLAUDE.md`: *"Every
sub-agent must read `PROJECT_SPEC.md`, its TASK_GUIDE_Txxx.md, and the corresponding file in agents/
before starting work"*). The guide lists them under Mandatory Startup; the spawn prompt only pointed at
the guide. Skipped reads also flatter T125's pre-edit numbers for a reason unrelated to the slice.

**Restated intent:**
> Every spawn prompt states the startup reads by path, as the first instruction after the task pointer,
> and asks the agent to list what it read in its final report; a spawn prompt without that block gets a
> non-blocking warning at spawn time — the same pattern as T125's memory-slice warning.

**Out of scope:**
- Enforcing reads (a hook cannot see which files an agent later opens) — the report line is the check.
- Changing *which* files are mandatory, or the Permanent Rule text.
- Rewriting existing TASK_GUIDEs or the template's Mandatory Startup list.
- T128's meter work.

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's approval, the Permanent Rule, and the T125 AC9 finding.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-09-25)
- [x] Domain terms align: *startup reads*, *spawn prompt*, *memory slice*, *Permanent Rule*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: T125 — element 4 (memory slice) and the hook's warning pattern this task mirrors

**Entry point**: `skills/craft-spawn-prompt/SKILL.md` (new element) → `.claude/hooks/pre_agent_validate_guide.py` (warning)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `craft-spawn-prompt` gains one element, placed directly after the guide pointer: a block starting with the literal line `**Startup reads** (before anything else, in this order):` listing `PROJECT_SPEC.md`, `tasks/TASK_GUIDE_Txxx.md`, `agents/<role>.md` (from the guide's `**Agent guide**`), plus any extra read the guide's Mandatory Startup names for this task's Complexity (e.g. a C2 finding doc) | Permanent Rule |
| 2 | The same element tells the agent to end its final report with `Startup reads: <paths read>` — one line | user default |
| 3 | The skill's pre-flight (step 4) flags a prompt that names a `TASK_GUIDE_Txxx.md` but has no `**Startup reads**` line | pre-flight |
| 4 | `pre_agent_validate_guide.py` adds a **non-blocking** warning for the same condition, beside T125's memory-slice warning (same shape; never `decision`, never exit 2) | can't silently go missing |
| 5 | The Supervisor's Stage 4 checklist gains one line: compare the agent's `Startup reads:` line against the block; a missing Permanent-Rule read is a P1 process finding. Put it in `skills/code-review/SKILL.md` Phase 0.5 area or `docs/claude-md/pipeline-stages.md` Stage 4 — wherever the review already checks spawn/guide conformance; say which and why | the check |
| 6 | No `CLAUDE.md` change (it is at 200 lines and byte-pinned); no role-guide change (T100 test) | Surgical |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Hook stdin: prompt naming `TASK_GUIDE_T129.md`, with slice, **without** `**Startup reads**` | exit 0, warning names the missing block, no `decision` | pytest via subprocess (T125 SC5 pattern) |
| 2 | Same with the block present | no startup-reads warning | pytest |
| 3 | Prompt naming no guide | no startup-reads warning | pytest |
| 4 | `craft-spawn-prompt/SKILL.md` | element present with the literal first line, the report-line instruction, and the pre-flight flag | structural pytest |
| 5 | Stage 4 checklist file | contains the compare-the-report line | structural pytest |

**Mutation controls:** **M1** — make the hook block → SC1 RED. **M2** — drop the report-line instruction → SC4 RED. **M3** — match `Startup reads` case-insensitively anywhere (so a prose mention passes) → add a fixture where only prose mentions it; SC1 must go RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_pre_agent_validate_guide.py tests/test_spawn_startup_reads.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T129.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T129.md`. BEFORE: the skill's element table verbatim. AFTER: a live
> spawn (headless, as T125's verify did) showing the warning without the block, silence with it, and the
> agent's `Startup reads:` line.

---

## Approach

**Pattern reference**: `check_memory_slice_warning` in `.claude/hooks/pre_agent_validate_guide.py` (T125) and its tests in `.claude/hooks/tests/test_pre_agent_validate_guide.py` — mirror them; element 4's row in `skills/craft-spawn-prompt/SKILL.md`.

**Vital slice**: AC1, AC2, AC4.

**Cut list**: verifying reads from transcripts (the meter could, later); per-role read lists beyond the guide's own.

---

## Edge Case Checklist

- [ ] Element numbering in the skill table shifts — update every in-file reference to element numbers (element 4 is cited by T125's hook message and docs: keep "element 4" meaning the memory slice, or update those citations together)
- [ ] Bugfix-flavoured guides get the same block
- [ ] The hook runs both warnings independently; one missing does not hide the other

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/craft-spawn-prompt/SKILL.md` | New element + pre-flight flag |
| `.claude/hooks/pre_agent_validate_guide.py` | Non-blocking warning |
| `.claude/hooks/tests/test_pre_agent_validate_guide.py` | SC1–3 |
| `tests/test_spawn_startup_reads.py` | **New.** SC4–5 |
| `skills/code-review/SKILL.md` or `docs/claude-md/pipeline-stages.md` | AC5 line |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | 200-line cap, byte-pinned (AC6) |
| `agents/*.md` | No rule bodies in role guides (T100) |
| `scripts/token_meter.py` | T128's scope |
| `memory/*` | Supervisor-only writes |

---

## Test Plan

1. `tdd`: SC1–5 first. 2. Implement. 3. M1–M3 RED/GREEN pasted. 4. User-run `/verify` with a live headless spawn.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Risk Low)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T129.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M3 pasted
- [ ] `/verify` — user-run
- [ ] UI Evidence rows: ☐ N/A — no UI component
- [ ] Supervisor notified: task ready for Stage 4 review
