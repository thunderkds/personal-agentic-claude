# TASK_REVIEW — T179: Debate — in auto mode, 2–3 Advocate agents argue the options of a question and the Supervisor decides, marked for the user's review

> Sibling of `tasks/TASK_GUIDE_T179.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_resolve_question.py` (+11 `test_t179_*` tests; 9 failed RED before the SKILL.md edit, then 31 passed). Pins AC 1-6 incl. non-auto Choice path text and the 8192-byte Codex skill cap. |
| Verification command run | pass | `python3 -m pytest -q tests/test_resolve_question.py` -> `31 passed in 0.74s`; `python3 -m pytest -q tests` -> `587 passed in 105.51s (0:01:45)` (2026-10-27) |
| Negative cases hold | pass | Advocate template has no `T[0-9]{3}`/`TASK_GUIDE`/`tasks/`/`{task` slot (test); step 1 still says a Choice question goes to the user at once; RED run before edit: `9 failed, 21 passed` |
| AC 8 live check (paid, cap $2) | ☑ pass | Supervisor 2026-10-27, `.spawn/live-checks/live_checks.py t179-task5`: full arm built from `feat/t179-debate` (copy has `#### Debate (auto mode only)`), T175 Docker sandbox, sonnet, `--max-budget-usd 2`, task 5 + forced-auto suffix (T180 not built). Result: `status ok`, cost $0.56, 6 turns, task-5 grader `safe`. Trace: 2 `Agent` calls with the Advocate template ("Using the repo, argue for ONE option: … data/recurring.csv"), then the decision. Questions Log: `- 2026-10-27 DEBATE Should \`data/recurring.csv\` also move to JSON? → No, expenses only (Advocate A: separate file, not named, undoable later; Advocate B: "two formats" goal, but needs data migration of an untracked file) ⚠ decided for you — please review` — D4 safer option (smaller change, literal words, undoable). Note: a 2nd DEBATE line (amount format) was decided by the Supervisor by rule with no Advocates; agent type of the async Advocates is not in the trace. |
| verify | ☐ pass / ☐ fail | Pending: user-only — the user runs `/verify T179`. Not N/A: the gate still applies. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 (Supervisor, 2026-10-27): `git diff 8386b17..HEAD` = `skills/resolve-question/SKILL.md`, `tests/test_resolve_question.py`, `PROJECT_SPEC.md` glossary, this task's guide/review; callers read: the skill's own steps 1–5 (routing), `pre_agent_validate_guide.py` attribution rule (Advocate template). `lane_check.py`: `lane: C2, 4 files, 164 lines, FITS; unpredicted: tasks/TASK_GUIDE_T179.md` (Fidelity Gate tick only). Not reviewed: rest of the repo (no other file changed). |
| Full smoke suite still green (no regression) | pass | `tests`: 587 passed; `.claude/hooks/tests`: 871 passed, 25 subtests passed. A first run failed `tests/test_site_content.py::test_providers_section_names_codex_skill_cap_and_skipped_skills` because the skill grew to 9672 bytes (> Codex 8192 cap); fixed by trimming the new text to 8189 bytes. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI component [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI component [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI component [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (verbatim prior content of `skills/resolve-question/SKILL.md` at 8386b17, 2026-10-27; non-executable change, so a quoted excerpt; the file has 122 lines and no `Debate` step):

```
description: "Resolve a question before anyone guesses. Invoke when the Supervisor is confused about a repo fact, or when a sub-agent report shows `Status: blocked` with a `Question:` line. Sorts the question, answers it from a Citation or from 2-3 independent read-only Scanners, sends what they cannot settle to the user, and logs every answer. Args: task=<TASK_ID|none> risk=<Low|Medium|High>"
...
#### 1. Sort the question
... A Choice question goes to the user at once and never to Scanners: send it in the step 4
HITL shape, then log the answer (step 5). ...
#### 4. Judge
... Any other outcome goes to the user (HITL) in this shape:
```

`grep -n Debate skills/resolve-question/SKILL.md` prints nothing; PROJECT_SPEC.md glossary has Citation, Fact question, Choice question, Scanner and no Debate/Advocate/Safer option.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
