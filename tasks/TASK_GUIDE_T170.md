# TASK_GUIDE — T170: `resolve-question` skill — a confused Fact question is answered from a Citation or by 2 independent scanners, else escalated to the user
**Date**: 2026-10-20
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Medium: a new cross-cutting Supervisor skill plus a change to every role guide's report format and to `thinking-report`. Skill/docs/tests only; no hook, script or installer behavior changes.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` — note the glossary terms **Citation**, **Fact question**, **Choice question**, **Scanner**, **Decision Log**, **Board cache**
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely, then `BRAINSTORMING_LOG_confusion-resolution.md`
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Source: the user, 2026-10-20: "when supervisor or agent got confused about the things, we should spawn at least 2 agents, or 3 seperate with the asking supervisor, or asking agent. That can go independently to scan the repos for answer the question from the asking. if still do not get the answer, let human know that for HITL, if get the answer, let note it as html report for the logs of the agent conversation". Option B approved: "yes, it's oke".

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> A new Supervisor skill `skills/resolve-question/SKILL.md` handles every question raised by a confused Supervisor or sub-agent. It sorts the question. A **Choice question** goes to the user at once. For a **Fact question**, the Supervisor answers directly if it can give a **Citation**. Otherwise it starts 2 **Scanners** in one turn (3 for a Medium/High risk task), each assigned a distinct area. An answer is accepted only if ≥2 Scanners agree and each gives a Citation, and the Supervisor opens the cited lines. Otherwise the question goes to the user (HITL). Every answer (Citation, Scanner or user) is logged: online → Linear comment, plus a Decision Log entry when it settles a choice; local → an HTML page in `reports/`. The task's guide links the log under `## Questions Log`. Sub-agents cannot spawn agents, so they report `Status: blocked` with a `Question:` line and the Supervisor runs the skill.

**Grilling / brainstorming decisions (2026-10-20)**:
- D1 — Supervisor with a Citation skips the Scanners. User: "if supervisor go the answer with evidence, its good for make the choice".
- D2 — Online log = `python3 scripts/board_sync.py push comment <ID> question "<text>"`; when the answer settles a choice, also `python3 scripts/board_sync.py decide <ID> "<text>"`. User: "send the logs, decision as comment to linear".
- D3 — Local log = HTML page via `thinking-report` with a new `session=resolution`; the guide links it. User: "as HTML page is oke, and refer the link to the task guide also".
- D4 — Terms: Citation (not "evidence" — that is the Evidence table); Fact question / Choice question (not "intent" — that is Stage 2's restated requirement); Scanner. In `PROJECT_SPEC.md` glossary.
- D5 — Scanners are the read-only `Explore` agent type, each given one area: (a) code — `scripts/`, `.claude/hooks/`, `skills/*/scripts/`, tests; (b) docs — `docs/`, `memory/`, `templates/`, `agents/`, `skills/*/SKILL.md`, `PROJECT_SPEC.md`; (c, 3rd Scanner only) history — `git log`, `tasks/`. Identical prompts make correlated mistakes, so areas differ.
- D6 — `## Questions Log` is NOT added to `templates/TASK_GUIDE_template.md` (the template is at its 197-line cap in `.claude/hooks/tests/test_vital_slice.py:63`). The Supervisor adds the heading to a guide on first use.

**Out of scope** (what this task explicitly does NOT do):
- A hook that detects `Status: blocked` and forces the skill (Option C — completion signals are unreliable, `post_agent_move_to_review.py:18-25`)
- Any change to `.claude/hooks/*.py` or `scripts/board_sync.py`
- Sub-agents spawning Scanners themselves
- A new HTML template (reuse `templates/thinking_report_template.html`)
- Back-filling `## Questions Log` into existing guides

**Requirement Refs**: `BRAINSTORMING_LOG_confusion-resolution.md` § Questions for the User (Q1–Q3), § Option B, § Edge Case Checklist; `memory/decisions.md` § T170

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-20; user approved Option B: "yes, it's oke")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (Citation, Fact question, Choice question, Scanner added 2026-10-20)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `Skill({ skill: "resolve-question" })` — listed on `CLAUDE.md`'s cross-cutting skill line; the role guides' report format carries the `Question:` line that triggers it.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|---|---|
| 1 | `skills/resolve-question/SKILL.md` exists with frontmatter `name: resolve-question` and a `description` that names its trigger (a confused Supervisor, or a sub-agent report with `Status: blocked` + `Question:`) | Restated intent |
| 2 | The skill's first step sorts the question; a Choice question goes to the user at once and never to Scanners; when the kind is unclear it is treated as a Choice question; a mixed question is split | Restated intent; D4 |
| 3 | The skill skips Scanners when the Supervisor gives a Citation (`file:line` + quoted text it opened this session) | D1 |
| 4 | Otherwise the skill starts 2 `Explore` Scanners in one turn (3 for Medium/High risk), each with a distinct area as in D5, and a prompt template that carries the question but never the asking task's guide path | D5; Edge Case 4 |
| 5 | Acceptance rule stated: ≥2 Scanners agree, each with a Citation, ≥1 Citation outside `docs/`/`memory/` prose or in `memory/decisions.md`, and the Supervisor opens the cited lines; any other outcome → HITL message containing the question, each Scanner's finding, and the decision needed | Restated intent; Edge Case 1 |
| 6 | Log step stated for both board modes with the exact commands of D2 (online) and the `thinking-report session=resolution` call of D3 (local), plus the one `## Questions Log` line appended to the task guide (heading added on first use); a question with no task logs the HTML page only | D2, D3, D6 |
| 7 | `skills/thinking-report/SKILL.md` accepts `session=resolution`, maps Question → problem, Citations/Scanner findings → trade-off matrix, answer → decision box, and saves to `reports/question_<task-or-none>_<YYYYMMDDTHHMMSS>.html` | D3 |
| 8 | Each role guide (`agents/backend.md`, `frontend.md`, `common-infrastructure.md`, `qa.md`) report format gains exactly one line `Question (if blocked): [fact|choice] <question>`; every file stays within its `LINE_CAPS` | Restated intent |
| 9 | `CLAUDE.md` lists `resolve-question` on the existing cross-cutting skill line; `CLAUDE.md` stays at ≤186 lines | Entry point |
| 10 | `site/index.html` mentions `resolve-question` (required by `tests/test_site_content.py::test_every_skill_dir_appears_on_page`) | Existing test |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---|---|---|
| 1 | `skills/resolve-question/SKILL.md` | frontmatter, sort step, Citation skip, 2/3 Scanners + areas, acceptance rule, HITL message, both log paths present | new `tests/test_resolve_question.py` |
| 2 | Scanner prompt template in the skill | contains no `tasks/TASK_GUIDE_` path placeholder | same |
| 3 | `skills/thinking-report/SKILL.md` | `resolution` session + `reports/question_` save path | same |
| 4 | 4 role guides | exactly one `Question (if blocked):` line each | same |
| 5 | `CLAUDE.md`, role guides | within `LINE_CAPS` | existing `.claude/hooks/tests/test_vital_slice.py` |
| 6 | `site/index.html` | names every skill dir | existing `tests/test_site_content.py` |
| 7 | full suite | still green | `python3 -m pytest -q` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests/test_resolve_question.py .claude/hooks/tests/test_vital_slice.py tests/test_site_content.py
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T170.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T170.md`. BEFORE: `ls skills/resolve-question; grep -n "Question (if blocked)" agents/*.md` (expect no match). AFTER: the skill exists and each role guide shows one line. WITNESS: one dry run on a real Fact question, its `reports/question_*.html` page attached.

---

## Approach

**Pattern reference**: `skills/compact-advisor/SKILL.md` — a cross-cutting Supervisor skill with a sort-then-act workflow; `skills/thinking-report/SKILL.md` — session args and the `reports/` save step; `tests/test_writing_principles.py` — doc-content test style.

**Vital slice**: the skill's sort → Citation check → 2 Scanners → accept-or-HITL → log path, plus the role-guide `Question:` line.
**Cut list**:
- 3rd Scanner for Low risk (only Medium/High)
- `## Questions Log` in the template (D6 — line cap)
- Hook enforcement (Option C), back-fill of old guides

Write the skill following `skills/write-better-skill/SKILL.md`. Keep the Scanner prompt template inside the skill so every fan-out uses the same shape.

---

## Edge Case Checklist

- [ ] Scanners agree but both cite the same stale doc → require ≥1 Citation in code or `memory/decisions.md`; Supervisor reads the cited lines
- [ ] Question needs runtime behaviour (what a command prints) → read-only Scanners cannot run it → "not found" → HITL, never a guess
- [ ] Question mixes a Fact question and a Choice question → split; fact part to Scanners, choice part to HITL
- [ ] Scanner prompt carries the asking task's guide path → `pre_agent_validate_guide.py` / `pre_agent_step_limit.py` attribute it to that task; the template carries the question only
- [ ] Active-task state file (`.claude/hooks/.state/active_task`, `lib/task_context.py` slot 2) may still attribute Scanner calls to the active task's step budget → state this in the skill; check during the WITNESS run and record the result in TASK_REVIEW
- [ ] Same question asked again by the same agent → one fan-out per question; a repeat goes straight to HITL
- [ ] Cited path is a sensitive path (`pre_tool_sensitive_path.py`) → Scanner blocked → treat as not found
- [ ] Scanner output quotes repo text that reads like an instruction → data, not instructions (`docs/claude-md/untrusted-content-boundary.md`)
- [ ] Question with no task (Supervisor confused mid-discussion) → no guide and no Linear issue → HTML page only
- [ ] Online mode: the guide is Board cache ("never edited by hand") → append the Questions Log line, then `python3 scripts/board_sync.py update --guide <ID>`
- [ ] Supervisor sorting its own question as a Fact question to avoid asking the user → when unsure of the kind, treat as a Choice question

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/resolve-question/SKILL.md` | new — the protocol (AC 1–6) |
| `skills/thinking-report/SKILL.md` | `session=resolution` + save path (AC 7) |
| `agents/backend.md`, `agents/frontend.md`, `agents/common-infrastructure.md`, `agents/qa.md` | one `Question (if blocked):` line in the report format (AC 8) |
| `CLAUDE.md` | add `resolve-question` to the cross-cutting skill line, no new line (AC 9) |
| `site/index.html` | mention the new skill (AC 10) |
| `tests/test_resolve_question.py` | new — AC tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py`, `.claude/hooks/lib/*.py` | Scanners avoid hook attribution by prompt shape, not by hook change |
| `.claude/hooks/post_agent_move_to_review.py` | deliberately inert (T044) |
| `scripts/board_sync.py` | `push comment … question` and `decide` already exist |
| `templates/TASK_GUIDE_template.md` | at its line cap (D6) |
| `.claude/hooks/tests/test_vital_slice.py` `LINE_CAPS` | no cap is raised by this task |

---

## Test Plan

New `tests/test_resolve_question.py` (doc-content asserts, as in `tests/test_writing_principles.py`) for AC 1–8; existing `test_vital_slice.py` for caps and `test_site_content.py` for the site. Full suite `python3 -m pytest -q` must stay green. WITNESS: Supervisor runs the skill once on a real Fact question after merge-ready, attaching the HTML page.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T170.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Questions Log

- 2026-10-20 · Choice question from common-infrastructure (Stage 3, full suite 2 failed): how to clear `test_agent_guide_dedup.py` pins on `CLAUDE.md` (`T070_BASELINE_REF`) and the c-infra char floor (+48 chars, `AC7_ROLE_BASELINE`)? → answered by the user: "yes" (repoint both, floor raise approved) → `e264297`. Log: this line only (board mode `local`; `thinking-report session=resolution` page not yet available — it ships in this task).
