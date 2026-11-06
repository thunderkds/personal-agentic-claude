# TASK_REVIEW — T268: Native Windows support, step 7 - setup.ps1, the PowerShell installer (install and reinstall)

> Sibling of `tasks/TASK_GUIDE_T268.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [paste the red run against the prior content, or the mutation diff (`git diff --stat`, non-empty) before each verdict] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
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

**BEFORE** (captured by the implementing agent in the worktree on branch `feat/t268-setup-ps1` at
`e781f503`, before any implementation commit):

```
2026-11-06T14:43:08Z
$ ls setup.ps1 lib/harness.ps1
ls: cannot access 'setup.ps1': No such file or directory
ls: cannot access 'lib/harness.ps1': No such file or directory
exit=2
$ grep -nE "^\s+- (uses|name):" .github/workflows/windows.yml
31:      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
36:      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
40:      - name: Install pytest and PyYAML
43:      - name: Python tests
$ python3 -m pytest .claude/hooks/tests tests -q
3784 passed, 25 subtests passed in 196.58s (0:03:16)
2026-11-06T14:46:25Z
```

The new tests, written first, red against the base (no `setup.ps1` yet):

```
2026-11-06T14:47:24Z
$ python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py -q
FAILED tests/test_setup_ps1_static.py::test_installer_source_is_51_safe_and_posix_free[setup.ps1]
FAILED tests/test_setup_ps1_static.py::test_installer_source_is_51_safe_and_posix_free[lib/harness.ps1]
FAILED tests/test_setup_ps1_static.py::test_smoke_script_is_51_safe - Asserti...
FAILED tests/test_setup_ps1_static.py::test_setup_ps1_dot_sources_the_library_and_calls_both_helpers
FAILED tests/test_setup_ps1_static.py::test_mutation_control_a_missing_header_is_caught[...] (x2)
FAILED tests/test_setup_ps1_static.py::test_mutation_control_a_banned_token_is_caught[...] (x7)
FAILED tests/test_setup_ps1_pwsh.py::test_the_windows_ci_smoke_passes_in_linux_pwsh
FAILED tests/test_setup_ps1_pwsh.py::test_install_matches_the_manifest_and_setup_sh
FAILED tests/test_setup_ps1_pwsh.py::test_edited_file_is_backed_up_and_a_rerun_is_idempotent
FAILED tests/test_setup_ps1_pwsh.py::test_python_is_found_when_py_and_python3_are_absent
FAILED tests/test_setup_ps1_pwsh.py::test_no_usable_python_stops_with_nothing_written[bin-nopy]
FAILED tests/test_setup_ps1_pwsh.py::test_no_usable_python_stops_with_nothing_written[bin-stub]
FAILED tests/test_setup_ps1_pwsh.py::test_outside_a_git_repo_stops_with_nothing_written
FAILED tests/test_setup_ps1_pwsh.py::test_existing_install_without_consent_cancels
21 failed, 1 passed in 5.25s
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
