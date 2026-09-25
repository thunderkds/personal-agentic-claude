# TASK_REVIEW — T132: The RUNBOOK says a push to `main` deploys the site

> Sibling of `tasks/TASK_GUIDE_T132.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☒ pass | `tests/test_vercel_config.py::test_runbook_says_push_to_main_deploys`. RED before docs: `1 failed, 7 passed`; GREEN after: `8 passed in 0.01s`. |
| Verification command run | ☒ pass | `tests/test_vercel_config.py` 8 passed; `.claude/hooks/tests tests` 978 passed; `validate.sh: PASS` |
| Negative cases hold | ☒ pass | M1 (restore "operator-run") → `1 failed, 7 passed`; M2 (drop "deploys production" sentence) → `1 failed, 7 passed`; restored → `8 passed` |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 (2026-09-25): `git diff tokenization-refactor...docs/t132-runbook-auto-deploy` — `RUNBOOK.md`, `PROJECT_SPEC_SITE.md`, `tests/test_vercel_config.py`, this file; repo grep for other operator-only deploy claims → only historical task files. **0 P0 / 1 P1 (fixed) / 0 P2 / 0 P3.** P1 — the Supervisor's own guide error, not the agent's: AC3 told the RUNBOOK to state that `.vercelignore` governs CLI uploads only and that the full repo reaches Vercel on every push. Vercel's docs do not say that: https://vercel.com/docs/builds/build-features says only the *built-in default* exclusions are CLI-only, and https://vercel.com/docs/deployments/vercel-ignore is silent on Git deployments. Reworded as not established, with an operator check (deployment URL + `/_src`, team-only Source view). 8 passed — pass |
| Full smoke suite still green (no regression) | ☒ pass | 978 passed; validate.sh PASS |
| **UI: Visual regression (diff or verdict pasted)** | ☒ N/A | no UI change |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☒ N/A | no UI change |
| **UI: Responsiveness at target viewports** | ☒ N/A | no UI change |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (verbatim, captured 2026-09-25 before any implementation commit):

`RUNBOOK.md:141-142`:
> **This deploy is operator-run.** No agent, hook, or CI workflow triggers any of the commands below.
> The operator runs them by hand from a terminal with the Vercel CLI installed and authenticated.

`PROJECT_SPEC_SITE.md:32`:
> - No automated deploy from CI. The operator runs the deploy.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
