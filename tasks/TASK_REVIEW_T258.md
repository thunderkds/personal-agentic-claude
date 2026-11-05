# TASK_REVIEW — T258: TASK_GUIDE template: list the pre-existing pin tests a task will hit, at Stage 2

> Sibling of `tasks/TASK_GUIDE_T258.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. Track extended, run in parallel with T257/T258/T259 in 3 worktrees, one common-infrastructure agent each — RULE: `docs/claude-md/tracks.md` (extended when more than one agent; the user asked "start new one as parallel [auto]")
2. Spawn model claude · C1 → sonnet — FACT: PROJECT_SPEC.md `## CLI Model Table` "| claude | `claude` | haiku | sonnet |"
3. Requirement Fidelity Gate signed `auto (Supervisor)` — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` row 13
4. T258 and T259 both add one line to the Edge Case Checklist of `templates/TASK_GUIDE_template.md`; run them in parallel anyway and resolve the adjacent-line conflict at merge, keeping both lines — SAFER OPTION: parallel runs were asked for; the conflict is two added lines, no logic ⚠ decided for you — please review


## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t258_pin_test_preflight.py` (3 tests, AC 1-3 by text). RED first against the prior template: `3 failed in 0.07s` (AC1, AC2, AC3 each AssertionError); GREEN after the template edit. AC4: the line-cap pin is met by rewrapping 2 lines (cap stays 205); the Edge Case Checklist pin is narrowed (same hunk as T259); both listed in the guide's `Pre-existing pin tests` row. |
| Verification command run | ☑ pass | `python3 -m pytest -q tests/ .claude/hooks/tests/` -> `3405 passed, 25 subtests passed in 231.44s (0:03:51)` |
| Negative cases hold | ☑ pass | Mutating baseline line `- [ ] [edge case 1]` in the template turned the narrowed `test_ac3_reasoning_prose_sections_are_byte_identical_to_the_baseline` RED (`1 failed`); restored, green. The 3 new tests were RED against the prior template. |
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

**BEFORE**: (verbatim prior content of `templates/TASK_GUIDE_template.md`, captured 2026-11-05, before any T258 commit; the change is template text, not executable code)

```
## Edge Case Checklist

[Populated from brainstorming skill output. List silent failures and boundary conditions to guard against.]

- [ ] [edge case 1]
- [ ] [edge case 2]

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| [path/to/file] | [what and why] |
```

No `Pre-existing pin tests` row and no pin-test pre-flight line exist.

**AFTER**: (verbatim new content of `templates/TASK_GUIDE_template.md`)

```
- [ ] [edge case 2]
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
...
| [path/to/file] | [what and why] |
| Pre-existing pin tests | List each test that pins the text, size, line count, location or a baseline ref of a file this task edits, and its handling: repoint, narrow or escalate. Find them: grep `.claude/hooks/tests/` and `tests/` for the changed strings and paths; always check `test_agent_guide_dedup.py`, `test_vital_slice.py` and the memory budget tests. |
```

**DELTA**: A task author now lists, at Stage 2, the pre-existing pin tests the task will hit and how to handle each, instead of meeting them mid-task.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
