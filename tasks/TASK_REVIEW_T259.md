# TASK_REVIEW — T259: `code-review`: stale-reference sweep for every fact the diff changes

> Sibling of `tasks/TASK_GUIDE_T259.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_stale_reference_sweep.py` (7 tests, AC1-AC4 plus a negative case). RED against the prior text, 2026-11-05: `FAILED test_ac1_sweep_names_each_changed_fact_kind`, `..._names_each_place_to_grep`, `..._sits_in_phase_0_5`, `test_ac2_hit_outside_files_to_change_is_p2_with_file_line`, `test_ac3_template_checklist_has_stale_reference_line` — `5 failed, 2 passed` (the 2 passes are the AC4 size pin and the negative-case reader test, which must pass on prior text). GREEN after the change: `7 passed in 0.03s`. Pins narrowed: `.claude/hooks/tests/test_guide_sections.py::test_ac3_reasoning_prose_sections_are_byte_identical_to_the_baseline` (Edge Case Checklist may gain lines; baseline lines must stay, in order). |
| Verification command run | ☑ pass | `python3 -m pytest -q tests/ .claude/hooks/tests/`: first full run `2 failed, 3407 passed` (template 206 lines over the 205 cap in `test_vital_slice.py`; the byte-identical Edge Case Checklist pin) — fixed by rewrapping one blockquote in the template and narrowing the pin. Second full run `1 failed, 3408 passed, 25 subtests passed in 378.89s` — the one failure, `tests/test_auto_verify.py::test_ac5_a_minimal_fail_record_blocks_even_if_the_line_is_edited_to_pass`, is a timing flake of a detached run while 3 suites ran at once; alone: `python3 -m pytest -q tests/test_auto_verify.py` -> `254 passed in 94.96s`. |
| Negative cases hold | ☑ pass | `test_neg_readers_reject_prior_content` (readers raise on text with no sweep and no checklist line). Mutation: `[edge case 2]` -> `[edge case TWO]` in the template makes the narrowed `test_ac3_reasoning_prose_sections_are_byte_identical_to_the_baseline` fail (`1 failed`); reverted. `skills/code-review/SKILL.md` is 8161 bytes (cap 8192). |
| verify | ☐ pass / ☐ fail / ☐ N/A | [filled from the headless auto verify run (`stop_auto_verify.py --start T259`)] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor `code-review` 2026-11-05 on `main...feat/t259-stale-reference-sweep` (5 files): `skills/code-review/SKILL.md` (Phase 0.5 sweep paragraph + ~500 bytes of prose trims), `templates/TASK_GUIDE_template.md` (checklist line; Dependencies blockquote rewrapped 5→4 lines, same words, to stay at the 205-line cap), `.claude/hooks/tests/test_guide_sections.py` (Edge Case Checklist pin narrowed to an in-order subsequence), new `tests/test_stale_reference_sweep.py`. lane_check: `lane: C1, 4 files, 123 lines, FITS; unpredicted: .claude/hooks/tests/test_guide_sections.py, tests/test_stale_reference_sweep.py`. Startup reads: all 3 Permanent-Rule reads present. P0 0, P1 0, P2 2, P3 0. P2 (75): the size trims in `skills/code-review/SKILL.md` go beyond the AC and drop one sentence ("Suppress advisory findings from a single low-confidence reviewer"; the confidence gate still covers it). P2 (100): `skills/code-review/SKILL.md` is 8161 of 8192 bytes, 31 bytes of headroom: the next edit hits the Codex cap; register a split of the skill body into `references/` before the next change. Supervisor re-run: `349 passed in 107.29s` (T259 tests, test_guide_sections, test_vital_slice, test_auto_verify — the suite's one failure was this timing test, green alone). |
| Full smoke suite still green (no regression) | ☑ pass | Agent full run: `1 failed, 3408 passed` — the failure `tests/test_auto_verify.py::test_ac5_a_minimal_fail_record_blocks_even_if_the_line_is_edited_to_pass` was a timing flake with 3 suites running at once; Supervisor re-run of `tests/test_auto_verify.py` with the T259 pin tests: `349 passed in 107.29s`. |
| **Companion score (easy-verifier)** | ☐ N/A | Not run: C1 / Risk Low, skill-text and template change. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI component: skill text, template and tests only. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | No UI component: skill text, template and tests only. |
| **UI: Responsiveness at target viewports** | ☐ N/A | No UI component: skill text, template and tests only. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: non-executable change (skill-instruction text and a template line); verbatim prior content, captured 2026-11-05 before any implementation commit.

`skills/code-review/SKILL.md` (8175 bytes) ends Phase 0.5 with the Startup-reads check and has no stale-reference sweep:

```
**Startup-reads check (T129).** Compare the implementing agent's final-report line `Startup reads: <paths>` against the spawn prompt's `**Startup reads**` block. A Permanent-Rule read (`PROJECT_SPEC.md`, the TASK_GUIDE, the `agents/` role guide) missing from the line is a **P1 process finding**; a missing line counts as all missing.

---

#### Phase 1 — Run Always-On Reviewers
```

`templates/TASK_GUIDE_template.md` Edge Case Checklist (no line for stale references):

```
## Edge Case Checklist

[Populated from brainstorming skill output. List silent failures and boundary conditions to guard against.]

- [ ] [edge case 1]
- [ ] [edge case 2]
```

**AFTER**: verbatim new content.

`skills/code-review/SKILL.md`, Phase 0.5, after the reachability completion criterion:

```
**Stale-reference sweep (T259).** For each fact the diff changes (a flag, count, path, channel or skill name, version, or a "green" claim), grep the repo for the old wording: README, `site/`, `docs/claude-md/`, docstrings and comments, `agents/`, `PROJECT_KANBAN.md` notes, test comments. Each hit outside the guide's `Files to Change` is a **P2 finding** with its `file:line`.
```

`templates/TASK_GUIDE_template.md` Edge Case Checklist:

```
- [ ] Stale references: for each fact this task changes (flag, count, path, name, version, "green" claim), grep the repo for the old wording (README, `site/`, `docs/claude-md/`, comments, docstrings, `agents/`, board notes)
```

**DELTA**: A reviewer, and a guide author, now has a written step to grep the repo for the old wording of every fact a diff changes, and each stray hit is a P2 finding with its file:line.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
