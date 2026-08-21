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
| verify | ☑ pass | User-run `/verify` 2026-08-21 — **pass**. The README's two corrected claims are *behavioural*, so the hooks themselves were the surface and both were **run against real payloads**, not read back. (1) `post_agent_move_to_review.py` driven with an Agent payload, `PROJECT_KANBAN.md` md5'd either side: `76c5cc7a…` before and after, zero counters created — it printed its reminder and wrote nothing, so the README's "does not move any KANBAN row or reset any counter" is true of the running hook. (2) `pre_agent_step_limit.py` driven in a loop under an isolated session id with `CLAUDE_STEP_LIMIT` deliberately unset: **90 calls allowed, first block on call #91**, and the block payload also showed the self-clearing reset. The corrected figure is exact, with no off-by-one. Every README promise resolves on T087's page (Repository layout 1/1, pack 3/17, Memory System 2/2, Options 1/1, brownfield 0/3, GITHUB_USERNAME 0/4). Install command md5-identical to canonical after a 477→55 line rewrite; its URL returns HTTP 200. Counter file created during the probe was removed; tree clean. |
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


---

## Stage 5 `/verify` findings (2026-08-21, user-run)

1. **⚠️ The site link is inert for the audience it is aimed at, and this makes deploying a release
   blocker rather than a follow-up.** All three pointers are `[site](site/index.html)`. **GitHub does
   not render HTML files** — a visitor who clicks that gets syntax-highlighted *source*. So the whole
   "full reference lives on the site" strategy delivers nothing to a GitHub reader until the operator
   deploys T084 and pastes the real URL in. The implementing agent flagged that the URL needs filling;
   what it did not say is that until then the link is worse than absent, because it looks live.
2. The README documents the step limit as 90 while `CLAUDE_STEP_LIMIT` stays overridable. Verification
   ran with it unset deliberately — a stale env var in the shell would have measured someone else's
   number and reported it as the default.
3. Probe that held: 90 allowed / 91 blocked exactly. Off-by-one was the easy error here and is absent.
4. Probe that held: the install one-liner is byte-identical to canonical after the rewrite, and its URL
   returns HTTP 200 — the primary call to action is not pointing at a 404.
5. Two sentences were restored beyond the cut list (pointers to `docs/claude-md/untrusted-content-boundary.md`
   and to the role guides' Complexity matrix) because deleting them broke pre-existing invariant tests
   from T082 and T066. That is the repo's own "pointer, not copy" pattern asserting itself, and it is
   why the file is 55 lines rather than the ~50 target. Correct call by the implementer.

## Stage 4 note — a genuine vacuous assertion, and the guide premise the implementer corrected

`test_readme_does_not_claim_step_limit_default_is_40` was measured **passing against a README that
read `default 40 calls`** — the mutation was confirmed landed by grep before concluding. Two
independent causes: `.` does not match a newline, so the context window stopped at the line break; and
even normalised to one line, a `.{0,40}` window after `step_limit` ends inside `(defa`, six characters
short of the number. Replaced with a positive assertion against the hook source, mirroring T083's
`test_step_limit_matches_source`, which additionally closes an AC7 gap the negative form could never
cover: **deleting** the fact now fails too, since "deleted" is not "corrected".

Separately, the implementer checked this guide's premise instead of obeying it and found the
Supervisor's harness-lock edge case was factually wrong: `README.md` is **not** in `MANIFEST`, and
`.claude/harness-lock.json` does not exist in this repo at all (it is generated in the *target*
project at install time). Second time this session an implementer corrected a Supervisor guide premise.
