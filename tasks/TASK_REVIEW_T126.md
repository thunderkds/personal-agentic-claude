# TASK_REVIEW — T126: The Supervisor can see its own context size — compact-advisor decides on a measurement, not a feeling

> Sibling of `tasks/TASK_GUIDE_T126.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_token_meter.py (test_current_*), tests/test_compact_advisor_measures.py (SC6) — 40 passed |
| Verification command run | pass | `pytest tests/test_token_meter.py tests/test_compact_advisor_measures.py -q` → `40 passed in 1.83s`; `pytest .claude/hooks/tests tests -q` → `922 passed in 20.87s` |
| Negative cases hold | pass | Mutation controls (RED then GREEN, same run): M1 oldest-file → `test_current_picks_newest…` FAILED; M2 include subagents/ → same test FAILED; M3 restore "no tool exposes your own context size" → `test_sc6_no_longer_claims…` FAILED; restored → `40 passed`. Also: missing slug dir exit 2 naming path; SENTINEL absent from text+JSON output |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | pass | 922 passed (above) |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-09-25T08:38:06Z, before any implementation commit; `python3 scripts/token_meter.py --current`):

```
usage: token_meter.py [-h] [--projects-dir PROJECTS_DIR] [--session SESSION]
                      [--task TASK] [--bash-lines BASH_LINES]
                      [--price-in PRICE_IN] [--price-out PRICE_OUT] [--json]
token_meter.py: error: unrecognized arguments: --current
exit=2
```

`skills/compact-advisor/SKILL.md` prior text, verbatim:

> - **Ask vs. Guess**: This is a judgment call based on observed session behavior, not a measurable
>   token count — no tool exposes your own context size. Never claim a precise number; report what you
>   actually observed.
>
> **a. Live conversation context** (`/compact` territory — user-invoked only):
> - Have you had to ask the user to re-state or re-confirm something from earlier this session?

**AFTER** (2026-09-25, this worktree's live session; `python3 scripts/token_meter.py --current`):

```
token_meter --session 4b9912b3-d928-46f5-8277-5ddacaf63f23.jsonl
context now: 55,864 | peak: 55,864 | calls over 150k: 0 of 7 | top: user_text 2%, attachment:environment 0%, attachment:model 0%
```
Skill step 2a now opens with "**Measure first**: run `python3 scripts/token_meter.py --current --json`…". The `/compact-advisor` live run is the user's `/verify`.

**DELTA**: `/compact-advisor` can quote the live session's measured context size and top content kind instead of guessing.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
