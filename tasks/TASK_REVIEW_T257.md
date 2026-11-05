# TASK_REVIEW — T257: `tdd` + review template: prove each new test or mutation control can go red

> Sibling of `tasks/TASK_GUIDE_T257.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t257_tdd_red_proof.py` (AC1-AC5 + `test_pins_fail_on_prior_content`); `.claude/hooks/tests/test_guide_sections.py` pin repointed to the AC4 row text. Written first: against the prior content `4 failed, 2 passed` (AC1-AC4 RED; AC5 size pin and the prior-content control pass by design). After the edit `6 passed`. |
| Verification command run | ☑ pass | `python3 -m pytest -q tests/ .claude/hooks/tests/` -> `3408 passed, 25 subtests passed in 402.14s (0:06:42)`. An earlier run before the pin repoint showed `1 failed, 3407 passed` (`test_guide_sections.py::test_ac1_moved_evidence_rows_are_present_unchanged_and_in_order`, which froze the old row); fixed in the same commit. |
| Negative cases hold | ☑ pass | Red run against prior content: `4 failed, 2 passed` (see above). Mutation controls on the new text, each with a non-empty `git diff --stat` before the verdict, each `1 failed, 5 passed`, reverted to `6 passed`: `s/git show/git XXXX/` (1 insertion, 1 deletion); `s/non-empty/XXXX/` (2 ins, 2 del); `s/no CI step/XXXX/` (1/1); template `s/mutation diff (/XXXX (/` (1/1). The repointed `test_guide_sections.py` pin: with the prior template row `1 failed, 50 passed`; with the new row `57 passed`. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [filled from the headless auto verify run (`stop_auto_verify.py --start T257`)] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor `code-review` 2026-11-05 on `main...feat/t257-tdd-red-proof` (5 files): `skills/tdd/SKILL.md` step 5 + checklist line, `templates/TASK_REVIEW_template.md` Negative-cases row, `.claude/hooks/tests/test_guide_sections.py` (moved-row pin repointed to the new row text), new `tests/test_t257_tdd_red_proof.py`. lane_check: `lane: C1, 4 files, 101 lines, FITS; unpredicted: .claude/hooks/tests/test_guide_sections.py, tests/test_t257_tdd_red_proof.py`. Startup reads: all 3 Permanent-Rule reads present. P0 0, P1 0, P2 1, P3 1. P2 (75): `tests/test_t257_tdd_red_proof.py` RED control uses a hand-copied excerpt `PRIOR_TDD` instead of `git show <base>:skills/tdd/SKILL.md` — the 'hand-kept list that claims to mirror a file' form the new step itself names; suggestion: read the prior file with `git show e0093fed:...`. P3 (75): `test_guide_sections.py` now hard-codes the new row text in a second place (template + test). Supervisor re-run: `57 passed in 0.30s` (T257 tests + test_guide_sections). |
| Full smoke suite still green (no regression) | ☑ pass | `3408 passed, 25 subtests passed in 402.14s (0:06:42)` |
| **Companion score (easy-verifier)** | ☑ N/A | Companion tool not run: C1 skill/template text change. |
| **UI: Visual regression** | ☑ N/A | No UI component (skill text and template only). |
| **UI: Design-system compliance** | ☑ N/A | No UI component (skill text and template only). |
| **UI: Responsiveness** | ☑ N/A | No UI component (skill text and template only). |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: verbatim prior content (non-executable change: skill text and template), captured 2026-11-05 before the first implementation commit, from `skills/tdd/SKILL.md` (2813 bytes) and `templates/TASK_REVIEW_template.md:52`:

```
#### 2. Tracer Bullet
Write ONE test for the first behavior → it fails (RED) → write minimal code → it passes (GREEN). This proves the path works end-to-end.
...
### Checklist Per Cycle
[ ] Test describes behavior, not implementation
[ ] Test uses the public interface only
[ ] Test would survive an internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```
```
| Negative cases hold | ☐ pass / ☐ fail | |
```
The skill has no step to run a test against the prior content, no mutation-control rule and no list of vacuous forms; the template row has an empty Notes cell.

**AFTER**: `skills/tdd/SKILL.md` (3703 bytes) gains `#### 5. Prove each test can go RED`: a test counts only after it ran against the prior content (`git show <base>:<file>`) and failed, with the RED output pasted; a `mutation control` needs a non-empty `git diff --stat` before its verdict; four vacuous forms are listed (`x <= x`, `not in` on a string the old content never held, a hand-kept list that claims to mirror a file, a guard no CI step runs); the cycle checklist gains one line. `templates/TASK_REVIEW_template.md` row now reads:
```
| Negative cases hold | ☐ pass / ☐ fail | [paste the red run against the prior content, or the mutation diff (`git diff --stat`, non-empty) before each verdict] |
```

**DELTA**: A reviewer or implementer who follows `tdd` must show each new test failing against the prior content and each mutation changing bytes, so a test that can never fail is caught when the work is done.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
