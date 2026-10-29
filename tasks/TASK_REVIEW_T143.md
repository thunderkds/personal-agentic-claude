# TASK_REVIEW — T143: CI re-runs the Verification Command of every task a PR moves to Done

> Sibling of `tasks/TASK_GUIDE_T143.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_ci_verify_done_tasks.py` (23 tests, each over a real two-commit git fixture; SC1-SC6 plus fail-closed, closed-row, stale-base and bad-ref cases). Run 2026-10-29 10:12 UTC: `23 passed in 1.28s`. F1 fix (top-level `permissions: contents: read`): wiring test RED without the block (`1 failed, 22 passed`: `Regex didn't match: '(?m)^permissions:\n  contents: read$'`), then `23 passed in 1.32s`; `python3 tests/test_ci_wires_shell_suites.py` -> `summary: 5 passed, 0 failed` |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_ci_verify_done_tasks.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q` -> `23 passed in 1.28s` then `2129 passed, 25 subtests passed in 121.14s (0:02:01)` |
| Negative cases hold | ☑ pass | failing block, skip with no reason, skip with `<reason>`, no section, no guide file, no fence, empty block, placeholder block, unknown base ref (exit 2): all exit non-zero and run nothing wrongly. A `[~]` Closed row, a bold cross-reference and a task already Done at base are not selected |
| verify | ☑ pass | /verify (user) 2026-10-29: pass. Clone of the branch; a PR commit moving T143 to Done, run with the workflow step's exact command (`--base 026bc61 --head <pr sha>`) → `T143: PASS`, exit 0. Probes: one PR moving T139/T143/T163/T186/T191 → `T139: FAIL (no Verification Command block ...)`, `T163: FAIL (`# ci: skip` needs a reason after the dash)`, `T186: SKIP (needs a live auto-mode session)`, `T191: FAIL (exit 4)` (test file absent), exit 1; a prose `- [x] **T162**` mid-line not selected; `--base deadbeef` → exit 2 (message ends in an empty git stderr); `--base HEAD --head HEAD` → `no tasks moved to Done`, exit 0; ci.yml parses with `permissions: {contents: read}`. Not run: a real GitHub Actions run (gh not authenticated). |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: code-review over `main...HEAD` (scripts/ci_verify_done_tasks.py, its test, ci.yml, the template line) plus callers `.claude/hooks/lib/guide_sections.py` (consumed, unchanged). lane_check: `C2, 5 files, 411 lines, FITS`. Findings: F1 P2 security — no `permissions:` block while checkout persists the token → fixed f5295c7 (`permissions: contents: read`, RED/GREEN in tests row). P2 noted, not fixed (cut list): older guides whose Verification Command diffs against `main` or a worktree (e.g. T196) fail if a PR moves them to Done. P3 accepted: a lone `[ -f x ]` block reads as placeholder and fails closed. security-review (Risk Medium): guide commands run only on `pull_request`, SHAs pass via `env:` and are quoted (no event-data injection), no secrets, read-only token; `persist-credentials` left default (P3). Full suite after fix: `2129 passed, 25 subtests passed`. |
| Full smoke suite still green (no regression) | ☑ pass | `2129 passed` (baseline before change: `2106 passed`, +23 new); `sh scripts/validate.sh` -> `validate.sh: PASS` |
| **Companion score (easy-verifier)** | ☑ N/A | easy-verifier not run: the `score` skill (T191) is not merged yet and the tool is not installed on this machine |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI: no rendered page changes (backend/CLI/skill text only) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI: no rendered page changes (backend/CLI/skill text only) |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI: no rendered page changes (backend/CLI/skill text only) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-29 10:05:39 UTC, before any implementation commit, on branch feat/t143-ci-verify at 09caa8f):

```
$ python3 -m pytest tests/test_ci_verify_done_tasks.py -q
ERROR: file or directory not found: tests/test_ci_verify_done_tasks.py

no tests ran in 0.00s
$ ls scripts/ci_verify_done_tasks.py
ls: cannot access 'scripts/ci_verify_done_tasks.py': No such file or directory
$ grep -c ci_verify .github/workflows/ci.yml
0
```

Baseline of the full suite: `python3 -m pytest tests/ .claude/hooks/tests/ -q` gave `2106 passed, 25 subtests passed in 90.59s`.

**AFTER** (2026-10-29 10:12 UTC):

```
$ python3 -m pytest tests/test_ci_verify_done_tasks.py -q
.......................                                                  [100%]
23 passed in 1.28s
$ python3 scripts/ci_verify_done_tasks.py --base HEAD --head HEAD
no tasks moved to Done
$ python3 scripts/ci_verify_done_tasks.py --base 483bee0~3 --head 483bee0   # real repo; T196 went to Done in that range
tasks moved to Done: T196
T196: running Verification Command:
python3 -m pytest -q .claude/hooks/tests/test_task_context.py ...
...
T196: FAIL (exit 1)
```

(T196's own block compares a diff against `main`, so it fails in this replay: that is the machine re-check working on an old guide, not a defect.)

**Mutation control (SC7)**: made the "no block" branch print `PASS (mutant)` and return True -> `3 failed, 20 passed` (`test_missing_guide_file_fails_closed`, `test_missing_verification_command_fails_closed`, `test_section_without_a_fenced_block_fails_closed`); restored -> `23 passed`.

**DELTA**: A PR that moves a task to Done now fails CI unless that task's `### Verification Command` block runs clean (or is skipped by name with a reason).

**WITNESS**: Implementing agent (common-infrastructure) 2026-10-29 10:05-10:12 UTC; the Supervisor re-runs SC7 and confirms from `memory/event-trace/T143.jsonl` at Stage 4.
