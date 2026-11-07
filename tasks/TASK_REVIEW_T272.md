# TASK_REVIEW — T[NNN]: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_setup_ps1_preflight_pwsh.py` (7 tests: AC 1, 2, 3, 5 and the mutation control). Docker pwsh tests RAN (image present), not skipped. |
| Verification command run | ☑ pass | 2026-11-07T04:32Z: guide command (+ the new file) -> `76 passed in 127.96s`; `python3 -m pytest .claude/hooks/tests tests -q` -> `3845 passed, 25 subtests passed in 372.49s` (base 3838 + 7 new). |
| Negative cases hold | ☑ pass | Red first: `6 failed, 1 passed in 16.03s` before the code. Mutation: `test_sc4_mutation_control_without_the_preflight_scenario_1_goes_red` removes the fenced preflight from a copy of setup.ps1 and asserts the project tree CHANGES (passes, so the unmutated scenario-1 check would go red). |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `3845 passed, 25 subtests passed` (see above). |
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

**BEFORE**: captured 2026-11-07T04:31:43Z, before any implementation commit (only the new test file existed, uncommitted). Docker pwsh 7.4.2 (the T268 harness). Kit = clone of this checkout minus `lib/windows_hooks.py`; project = a git repo that owns `.claude/hooks/own.py`, `CLAUDE.md`, `.claude/settings.json`, `scripts/verify_trace.py`. Command: `Set-Location /work/proj; & /work/kit/setup.ps1 -Yes`. Output (trimmed, order kept):
```
exit code: 2
[info]  Using repo: /work/kit-nohooks
  - Existing paths that differ from the kit are moved aside first:
      .claude/hooks -> hooks.bak-20261107
      scripts/verify_trace.py -> verify_trace.py.bak-20261107
      CLAUDE.md -> CLAUDE.md.bak-20261107
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[info]  Wrote ./.claude/harness-lock.json (147 file hashes).
[info]  Setup complete. Easy Kit copied into /work/proj
[warn]  Backed up your existing './CLAUDE.md' to './CLAUDE.md.bak-20261107' before installing the kit's copy ...
[error] The fetched Easy Kit has no lib/windows_hooks.py, so the hooks keep their POSIX form and do not run on Windows.
[error] Setup finished, but Easy Kit hooks were NOT wired (see the message above).
moved-aside: ['.claude/hooks.bak-20261107', '.claude/hooks.bak-20261107/own.py', 'CLAUDE.md.bak-20261107', 'scripts/verify_trace.py.bak-20261107']
changed/added paths: .claude/agents/*, .claude/harness-lock.json, .claude/hooks.bak-20261107, ... (project half installed)
```
New tests on that tree: `python3 -m pytest tests/test_setup_ps1_preflight_pwsh.py -q` at 2026-11-07T04:31:18Z -> `6 failed, 1 passed in 16.03s` (the 1 pass is `test_a_full_kit_still_installs`; scenario 3 with `update.ps1 -Yes` got exit 2, i.e. the update also ran before the error).

**AFTER**: same command, same kit, 2026-11-07T04:41:03Z, with the preflight in `setup.ps1`:
```
exit code: 1
[info]  Using repo: /work/kit-nohooks
[info]  Fetching (shallow clone): /work/kit-nohooks
[error] The fetched Easy Kit has no lib/windows_hooks.py, so it has no Windows support yet. Nothing was changed. Wait for a kit release that supports Windows, or point SUPERVISOR_REPO at a kit that has it.
LEFTOVER 0
changed/added paths: []
moved-aside: []
```
New tests: `python3 -m pytest tests/test_setup_ps1_preflight_pwsh.py -q` -> `7 passed in 15.28s`.

**DELTA**: A Windows user who runs `setup.ps1` against a kit without Windows support now gets one clear error right after the fetch and an untouched project, instead of a half-installed one.

**WITNESS**: common-infrastructure agent ran both captures (2026-11-07T04:31:43Z, 04:41:03Z); the Supervisor's trace `memory/event-trace/T272.jsonl` is the independent record. Not yet independently witnessed.
