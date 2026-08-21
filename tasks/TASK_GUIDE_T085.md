# TASK_GUIDE — T085: Slim README to ~50 lines and correct two false hook rows
**Date**: 2026-08-21
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` (**this task is harness-scope, not site-scope**)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. C1 → apply the C1 row of the Complexity matrix

---

## Requirement (Pillar 1)

> "due to the README is too much information at current, we need to simplify it"

and the user's chosen depth, from the Stage 2 scoping questions: **"Quickstart only, ~50 lines"** —
pitch, install, prerequisites, link to the site.

**Restated intent**:
> Cut `README.md` from 477 lines to roughly 50 — a landing surface, with the reference material now
> living on the site — and, in the same pass, fix the two hook facts the README states wrongly, so the
> correction happens at the source rather than being erased by deletion.

**This task absorbs T081.** T081's row on `PROJECT_KANBAN.md` is marked SUPERSEDED and must not be
worked separately.

**Out of scope**:
- `site/**` and `vercel.json` — T083/T084 own those.
- Changing any hook's *behavior*. This task corrects documentation to match code, never the reverse.
- Rewriting `CLAUDE.md` or `CLAUDE_LEGACY.md`.
- Deleting content that exists nowhere else — see the AC3 constraint.

**Requirement Refs**: N/A — direct user request, 2026-08-21.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-08-21; user chose the ~50-line option explicitly)
- [x] Domain terms align with `PROJECT_SPEC.md`
- [x] Every AC traces to the Requirement
- [x] Requirement Refs recorded N/A with reason

---

## Dependencies & Reachability

**Depends on**: T083 — do not remove reference content from `README.md` until `site/index.html`
exists and carries it. Removing first would leave the material in neither place.

**Entry point**: `README.md` — the repo's GitHub landing document.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `README.md` is ≤ 60 lines (target ~50) | "simplify it", user's chosen depth |
| 2 | It retains: a one-paragraph statement of what the kit is; the `curl … \| sh` install command verbatim and working; the git-repo prerequisite; the `git`/`curl`/POSIX-`sh` prerequisites; the restart-Claude-Code step; a link to the deployed site | Quickstart-only scope |
| 3 | **No content is deleted that exists in neither `site/index.html` nor another repo doc.** For each removed section, the agent states in its report where that content now lives, or that it was intentionally dropped and why. A section that exists nowhere afterwards is a silent loss, not a simplification | "simplify", not "discard" |
| 4 | The `post_agent_move_to_review.py` row is corrected: the file performs **0 write operations**, does not move any KANBAN row, and does not reset any step counter — it prints a reminder and is deliberately inert (since T044). Its own docstring is the authority | T081 (1) |
| 5 | The `pre_agent_step_limit.py` default is corrected from **40** to **90**, matching `STEP_LIMIT = int(os.environ.get("CLAUDE_STEP_LIMIT", "90"))` | T081 (2) |
| 6 | The `Advisory vs. blocking` sentence near the old `README.md:422` is checked and corrected if it repeats either false claim; if it does not, say so explicitly rather than leaving it unmentioned | T081 scope note |
| 7 | If the hook table itself is removed by the slimming, AC4–AC6 are satisfied by verifying the **site** carries the corrected facts (T083's AC5) and stating that in the report — the corrections must land somewhere, and "deleted" is not "corrected" | T081 + drift constraint |
| 8 | `tests/test_readme_slim.py` asserts AC1, asserts the install command string is present and unbroken, and asserts the README contains **neither** the false step-limit default `40` in a step-limit context **nor** any claim that the move-to-review hook moves a task | Gate 5 |
| 9 | Full suite passes, 0 regressions | repo convention |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | `README.md` as committed | line count ≤ 60 | automated test |
| 2 | `README.md` as committed | contains the exact install URL and the `\| sh` suffix | automated test |
| 3 | `README.md` as committed | contains no sentence asserting the move-to-review hook moves/resets anything | automated test |
| 4 | **Mutation control M1** — re-insert the sentence "Moves task In Progress → Ready for Review; also resets that task's step-limit counter" | the AC8 false-claim test goes **RED**; revert after observing | Supervisor re-runs manually |
| 5 | **Mutation control M2** — append 20 filler lines to `README.md` | the line-count test goes **RED**; revert after observing | Supervisor re-runs manually |

> M1 is the load-bearing control: without it, "the README does not contain the false claim" is
> trivially satisfied by any README that happens not to mention hooks at all — the vacuous-assertion
> family this repo has hit 9 times.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_readme_slim.py -q && python3 -m pytest .claude/hooks/tests/ tests/ -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T085.md`.

---

## UI / Design Acceptance Criteria

**N/A — pure documentation task.** No UI component; all three Gate 6 rows are ☐ N/A for this reason.

---

## Approach

**Pattern reference**: the current `## Quick Start` section of `README.md` (lines ~205–228) — it is
already the right register and the install command in it is correct. Build the slim README around it.

**Vital slice**: pitch + install + prerequisites + site link. That is the whole deliverable.

**Cut list** (moved to the site by T083, or deliberately dropped):
- Pack matrix and the five pack detail sections → site (or dropped from v1 of the page; if T083 did not carry them, say so under AC3 rather than assuming).
- Update flow, Options table, folder layout, HTML/Thinking reports, codebase map, memory system, custom-skills contract → site.
- The fork-install and brownfield-install variants → these are genuinely useful and exist nowhere else; keep one line pointing at the site rather than deleting.

Work in this order: (1) verify both false facts against the hook sources yourself — do not take this
guide's word for them; (2) write `tests/test_readme_slim.py` red; (3) rewrite the README; (4) green.

---

## Edge Case Checklist

- [ ] AC8's `40` assertion must not false-positive on an unrelated `40` elsewhere in the README — scope it to the step-limit context
- [ ] The install one-liner contains a pipe and a long URL; a line-wrap or a smart-quote substitution silently breaks copy-paste. Assert the exact string
- [ ] `README.md` is listed in `MANIFEST` and hash-locked in `.claude/harness-lock.json` — a change here reaches every installed project through `update.sh`. Check whether the lock needs regenerating and report the answer either way
- [ ] The site link must point at the real deployed URL; if T084's deploy has not run yet, use the repo-relative `site/index.html` path and flag that the URL needs filling at Stage 5 — **do not invent a `.vercel.app` hostname**
- [ ] Anchors: other docs may link to `README.md#section` headings being deleted. Grep for such links before removing headings

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `README.md` | Rewrite to ~50 lines; correct both hook facts |
| `tests/test_readme_slim.py` | New — AC8 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/**` | Documentation is being corrected to match code; changing code to match docs inverts the fix |
| `site/**`, `vercel.json` | T083/T084 own those |
| `PROJECT_KANBAN*.md`, `memory/**` | Supervisor-only |
| `CLAUDE.md`, `CLAUDE_LEGACY.md` | Out of scope |

---

## Test Plan

`tests/test_readme_slim.py`: line-count assertion; exact-install-string assertion; false-claim absence
assertions for both hook facts (scoped, per the edge cases). Full suite for regressions. Then M1 and M2.

Manual: read the slimmed README top to bottom as a stranger and confirm AC2's six elements are all
present and the install command copy-pastes intact.

---

## Completion Checklist

- [ ] Both false facts independently verified against hook source **before** editing — paste the source lines
- [ ] Implementation done
- [ ] M1 and M2 each observed RED with the failing assertion pasted, then reverted
- [ ] AC3 report written: for every removed section, where it now lives
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: **N/A** — Low risk, documentation only
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T085.md` (Gate 5)
- [ ] UI/Design rows: ☐ N/A ×3 (Gate 6)
- [ ] Supervisor notified: ready for Stage 4 review
