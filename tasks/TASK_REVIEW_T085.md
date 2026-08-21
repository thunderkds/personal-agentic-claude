# TASK_REVIEW — T085: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T085.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_readme_slim.py` — 4 tests covering AC1 (line count), AC2 (install command), AC4/AC6 (move-to-review false claim absence), AC5 (step-limit-40 false claim absence, scoped) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_readme_slim.py -q` → `4 passed in 0.01s` |
| Negative cases hold | ☑ pass | M1/M2 mutation controls both observed RED (see Demonstration/report), then reverted |
| verify | ☐ N/A | Stage 5 `verify` is user-run only per `memory/MEMORY.md` (project_verify_skill_is_user_only) — not run by the implementing agent |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: `README.md` (rewritten), `tests/test_readme_slim.py` (new). Skipped: `site/**`, `vercel.json`, `.claude/hooks/**` — out of scope per TASK_GUIDE Files Must NOT Touch |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `699 passed in 9.42s` (baseline 695 + 4 new T085 tests, 0 regressions after adding the two invariant-preserving sentences described in the report) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Pure documentation task, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Pure documentation task, no UI component |
| **UI: Responsiveness at target viewports** | ☑ N/A | Pure documentation task, no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: (captured 2026-08-21T09:37:16Z, before any implementation commit)

```
$ wc -l README.md
477 README.md
```

Two false hook-fact rows quoted verbatim from `README.md` as they read at this commit (lines 419–420):

```
419:| `post_agent_move_to_review.py` | PostToolUse / Agent | Moves task `In Progress → Ready for Review` after agent finishes; also resets that task's step-limit counter |
420:| `pre_agent_step_limit.py` | PreToolUse / all tools | Deterministic guardrail: counts tool calls per Task ID and **blocks** further calls past `CLAUDE_STEP_LIMIT` (default 40) — kills runaway loops instead of relying on the model to stop itself |
```

Regression baseline (2026-08-21T09:37:16Z):
```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
695 passed in 9.49s
```

**AFTER**:

```
$ wc -l README.md
55 README.md
```

Corrected hook facts, quoted verbatim from the new `README.md` (lines 6–8):

```
pipeline hooks rather than prompt reminders — e.g. `pre_agent_step_limit.py` blocks runaway tool-call
loops (default 90 calls), and `post_agent_move_to_review.py` is a deliberately inert reminder-only
hook since T044 (it does not move any KANBAN row or reset any counter — see its docstring).
```

Full-suite regression run post-change:
```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
699 passed in 9.42s
```
(baseline 695 + 4 new `tests/test_readme_slim.py` tests, 0 regressions)

**DELTA**: A newcomer reading `README.md` now gets a ~55-line landing page (pitch, correct hook
facts, install command, prerequisites, site link) instead of a 477-line reference dump — and no
longer reads two false claims about hook behavior (the move-to-review hook does not move/reset
anything; the step-limit default is 90, not 40) that previously matched neither `post_agent_move_to_review.py`'s
docstring nor `pre_agent_step_limit.py`'s `STEP_LIMIT` source line.

**WITNESS**: common-infrastructure agent (T085 implementer), 2026-08-21T09:37Z–09:52Z, per
`.claude/hooks/.state/active_task` trace attribution; Supervisor to co-sign at Stage 4 review per
the Demonstration field's requirement that WITNESS is never the implementing agent alone.
