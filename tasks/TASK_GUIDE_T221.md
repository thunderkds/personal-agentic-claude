# TASK_GUIDE — T221: Debate Advocates frame the problem (What? Why? How?) and each proposes its own option
**Date**: 2026-10-31
**Complexity Level**: C2
**Risk Level**: Medium (auto-mode doctrine; `.claude/hooks/stop_auto_mode_check.py` and `tests/test_resolve_question.py` key on the Advocate wording)
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` (glossary rows Debate, Advocate, Safer option, Auto mode, Final report)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Read `skills/resolve-question/SKILL.md` `#### Debate (auto mode only)` and `docs/claude-md/tracks.md` `### Debate size by Risk`
6. Read `.claude/hooks/stop_auto_mode_check.py` (what it counts: `Agent` calls whose `description` starts `Advocate`; `Advocate <n>:` names on `DEBATED` lines)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-31: "for the debate agents needed to find the answer, the debate agent should make question What? Why? How? to identify the problem, and contribute the idea to make final decision seperately"

User choice, 2026-10-31 (forced choice, option "Frame, then own idea"): each Advocate works alone. It first answers **What** is the problem / **Why** does it matter (root cause) / **How** could it be solved, from the repo with Citations. Then it proposes its **own** option — the Supervisor assigns none. The Supervisor compares the separate proposals and decides by the existing rules (necessary > safer option). Advocates proposing the same option is logged as agreement.

**Restated intent**:
> Today the Supervisor picks the options and gives each Advocate one to argue, so no agent ever checks what the problem really is. After this task, every Advocate gets only the question, frames the problem itself (What / Why / How, cited), and proposes its own option, without seeing the other Advocates' output. The Supervisor collects the proposals and decides by the unchanged Decide rules. Counts by Risk (Low none, Medium 2, High 3), the cap of 3 Debates, the log line shapes and the Stop hook's checks stay as they are.

**Out of scope**:
- Debate sizes by Risk, the 3-Debate cap, the Decide rules 1–3, the `DEBATE` / `DEBATED` log line shapes
- Any change to `.claude/hooks/stop_auto_mode_check.py` (its checks must keep passing unchanged)
- Scanners (Fact questions) — unchanged
- A second Debate round

**Requirement Refs**: user request 2026-10-31 + forced choice above

### Requirement Fidelity Gate

- [x] Restated intent confirmed — the user picked "Frame, then own idea" 2026-10-31
- [x] Domain terms align — Debate, Advocate, Safer option (`PROJECT_SPEC.md` glossary)
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered

---

## Dependencies & Reachability

**Depends on**: none (T179 / T180 Debate is on main)
**Entry point**: `skills/resolve-question/SKILL.md` `#### Debate (auto mode only)`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The Advocate prompt template's only slot is `{question}`; `{option}` and `{other_options}` are gone. It still carries no task ID or guide path | "contribute the idea … separately"; none assigned |
| 2 | The template asks the Advocate, in this order, to return `WHAT:` (the problem, cited), `WHY:` (why it matters / root cause), `HOW:` (ways to solve it, 1–3), then `PROPOSAL:` (its own one option), `FOR:`, `CITATIONS:` (`<path>:<line> "<quoted text>"`), `RISK:`, `CONFIDENCE: low\|medium\|high` | "make question What? Why? How? to identify the problem" |
| 3 | The Debate step says each Advocate works alone: it gets the question only, never another Advocate's output or a Supervisor-chosen option. All Advocates of one Debate are spawned in one message (parallel) | "separately" |
| 4 | At Risk High the third Advocate's prompt adds one line telling it to favour the smallest safe thing; the text "smallest safe thing" stays in the Debate step | keep existing sizes |
| 5 | Spawn `description` is `Advocate <n>: <short question>` (still starts `Advocate`, so the Stop hook count is unchanged). The `DEBATED` / `DEBATE` log lines name each Advocate's **proposal** (`Advocate 1: <its proposal>`) | hook unchanged |
| 6 | Decide: open every cited line first; compare the WHAT/WHY framings — framings that disagree on the problem are noted in the log; the same proposal from all Advocates is logged as agreement; then rules 1–3 unchanged | "to make final decision" |
| 7 | `PROJECT_SPEC.md` glossary rows Debate and Advocate, `docs/claude-md/tracks.md` `### Debate size by Risk` (and the line-239 example), `templates/MINIMAL_LOG_template.md` / `templates/TASK_REVIEW_template.md` example lines, and `site/index.html` line ~495 say "propose" / "its proposal" instead of "argue one option" where they describe what an Advocate does. Nothing else in them changes | One Term, One Meaning |
| 8 | `tests/test_resolve_question.py`: the T179 AC 2 tests are updated to the new slot set and fields (with a comment that T221 supersedes them), and new tests assert AC 1–6. A mutation control: a template that still has `{option}` fails | Gate 5 |
| 9 | Negative: `.claude/hooks/` unchanged; `tests/test_auto_mode.py`, `.claude/hooks/tests/`, `tests/test_site_content.py`, `tests/test_site_visual_first.py` still pass | out of scope |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | The new SKILL.md | AC 1–6 text present | `tests/test_resolve_question.py` |
| 2 | Mutant template with `{option}` slot | test fails | mutation control |
| 3 | A sample `DEBATED` line `Advocate 1: <proposal>; Advocate 2: <proposal>` at Risk Medium | Stop hook check passes as before | existing `tests/test_auto_mode.py` |
| 4 | Whole repo | suite green except the known MEMORY.md budget failures that also fail on main | `python3 -m pytest -q` |

### Verification Command

```bash
python3 -m pytest -q tests/test_resolve_question.py tests/test_auto_mode.py tests/test_site_content.py tests/test_site_visual_first.py .claude/hooks/tests/
```

---

## Approach

**Pattern reference**: the current `#### Debate (auto mode only)` step and its fenced template; keep its terse style and line count close (≤ +12 lines).

**Vital slice**: the new template (AC 1–2) and the "works alone" sentence (AC 3).
**Cut list**: a second Debate round; a framing-merge step by the Supervisor; any hook change; per-Advocate "lenses" beyond the existing High third-Advocate line.

---

## Edge Case Checklist

- [ ] All Advocates propose the same option → logged as agreement, still `DEBATED` with each Advocate named.
- [ ] Advocates frame different problems → note it in the log line; Decide still runs on the proposals.
- [ ] An Advocate returns no PROPOSAL or hits its step limit → it counts as a call but its proposal is "none"; use rule 2 and log it (matches today's step-limit rule).
- [ ] A proposal that deletes or overwrites data → existing "pause and ask" rule still applies.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/resolve-question/SKILL.md` | Debate step + Advocate template |
| `docs/claude-md/tracks.md` | wording in `### Debate size by Risk` and the `DEBATED` example |
| `PROJECT_SPEC.md` | glossary rows Debate, Advocate (wording only) |
| `templates/MINIMAL_LOG_template.md`, `templates/TASK_REVIEW_template.md` | example line wording |
| `site/index.html` | one sentence (~line 495) |
| `tests/test_resolve_question.py` | updated + new tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/**` | out of scope; must pass unchanged |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |

---

## Test Plan

Red first: write the new tests, run them against the current SKILL.md, paste the failure. Then change the docs, run the Verification Command, then the full suite; paste outputs.

---

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T221.md`. No UI component: the three UI rows are N/A (one site sentence, text only).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T221.md`.

---

## Questions Log

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T221.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] Supervisor notified: task ready for Stage 4 review (code-review + security-review, Risk Medium)
