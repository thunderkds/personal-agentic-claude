# TASK_REVIEW — T263: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T263.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_windows_ci_workflow.py` (13 tests: AC 1, 2, 5, 6 via `_problems`; AC 3 via the `posix_only` reason scan; AC 4 via `test_the_skip_is_win32_only`). Root `conftest.py` holds the shared `posix_only` marker. The Windows run is UNVERIFIED until the first push: no Windows runner was available to the agent. |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_windows_ci_workflow.py -q` -> `13 passed in 0.50s`. Full Linux: `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> BEFORE `3420 passed, 25 subtests passed`; AFTER `3433 passed, 25 subtests passed in 217.85s` (+13 = the new tests; no drop). `sh scripts/validate.sh` -> PASS. |
| Negative cases hold | ☑ pass | 8 workflow mutations (`ubuntu-latest`, floating `v4`, `main`, `contents: write`, python `"3"`, no `-I`, no `pull_request`, `secrets.`) each make `_problems` non-empty (`test_mutation_control_a_broken_workflow_is_caught`, 8 cases pass); a `posix_only` with no or blank reason raises `UsageError` on linux and win32. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Added: `.github/workflows/windows.yml`, `conftest.py`, new test. Edited: decorator lines only in 19 test files (plus one import-time guard, `needs_non_root` in `tests/test_dotfiles.py`). No hook, script, installer or `ci.yml` change. Own review only: `code-review` / `security-review` skills not run by this agent (Supervisor runs them at Stage 4). |
| Full smoke suite still green (no regression) | ☑ pass | Linux Python suite 3433 passed (see above). Shell suites not touched, not re-run. |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured Fri Nov 6 11:54:29 UTC 2026 (Linux), before any implementation commit, in `/home/hungnguyenhuu/workspace/pets/wt-t263` (branch `feat/t263-windows-ci`):

```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
3420 passed, 25 subtests passed in 213.61s (0:03:33)
$ ls .github/workflows
ci.yml        # no Windows workflow; no tests/conftest.py or repo-root conftest.py
```

**AFTER**: Fri Nov 6 12:01-12:05 UTC 2026 (Linux): `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `3433 passed, 25 subtests passed in 217.85s`. `.github/workflows/windows.yml` exists (job `python-tests` on `windows-latest`, Python 3.12, `python -I -m pytest tests/ .claude/hooks/tests/ -q`); 167 test functions (223 collected cases) carry `@pytest.mark.posix_only("<reason>")`. The Windows run itself is unverified until the first push.

**DELTA**: Every push and pull request now runs the kit's Python tests on a real Windows runner, with POSIX-only tests skipped and a written reason for each.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
