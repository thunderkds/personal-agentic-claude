# TASK_REVIEW — T222: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T222.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_stop_auto_mode_check.py` (`test_t222_ac2…`, `ac3…` x9, `ac4…` x2, `ac5…`); `tests/test_auto_mode.py::test_d8_advocate_spawn_description_starts_with_advocate` updated for the new tracks.md sentence. 2026-10-31T04:28Z |
| Verification command run | ☑ pass | `python3 -m pytest -q .claude/hooks/tests/test_stop_auto_mode_check.py tests/test_auto_mode.py tests/test_resolve_question.py` (2026-10-31T04:28:23Z) -> `216 passed in 5.18s`. After Stage 4 P1 fix (reason text names the prefix; tracks.md:284 and the `test_auto_mode.py` pin moved; new assert on the reason in the AC 3 test) (2026-10-31T04:35:21Z): `216 passed in 5.28s` |
| Negative cases hold | ☑ pass | AC 3 (7 params + check-5 + Medium `has 1`) and AC 5 pass. AC 8 mutation control (2026-10-31T04:28:09Z): hook helper replaced by `field(summary, "description").startswith("Advocate")` -> `9 failed, 60 passed` (all AC 3/5 tests); hook restored, `69 passed` |
| verify | ☑ pass | auto-run by hook, session b05c66f7-fbfa-4752-8bab-a0d41fad08bc, commit ae8ae7f3b3f13b99bb8d5d5735ca19b7fe3d600d, log .claude/verify-runs/T222-ae8ae7f3b3f1.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review 2026-10-31 on `main...HEAD` (6 files) + readers (`post_tool_trace.py` `summarize()`, `field()`); lane_check `C1, 5 files, 135 lines, FITS`; 0 P0, 1 P1 (block-reason text still named the old rule — fixed in cad92b26), process note: agent did not read `agents/common-infrastructure.md` separately (loaded as its system prompt; accepted). security-review 2026-10-31 on `main...HEAD`: No findings — new check is a strict subset of the old one (counts fewer, never more); escaped `\"prompt\"` inside another value cannot match the fallback regex; truncation fails closed — pass |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `5 failed, 2567 passed, 25 subtests passed in 144.20s`; re-run after the P1 fix: `5 failed, 2567 passed, 25 subtests passed in 141.94s`. The 5 failures are `test_memory_channel_and_budget.py` x4 and `test_token_audit_format.py::test_memory_md_hot_tier_stays_within_char_budget` (memory/MEMORY.md char budget); they fail the same on clean main in the main checkout (`5 failed, 13 passed`), not touched by T222 (the branch predates main's fix cfd8cc94) Supervisor re-ran 2026-10-31 on cad92b26: `5 failed, 2567 passed` — the 5 are the MEMORY.md budget tests, caused by the Supervisor's T221 memory pass and fixed on main at cfd8cc94 (main: `2559 passed`); the branch predates the fix and the merge gate blocks merging main in while T222 is In Progress. |
| **Companion score (easy-verifier)** | ☑ N/A | not run for T222 |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component (hook + docs) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-31T04:27:31Z at HEAD `52925352` (only the new tests added to
`.claude/hooks/tests/test_stop_auto_mode_check.py`; `.claude/hooks/stop_auto_mode_check.py` unchanged,
still `.startswith("Advocate")`). Command: `python3 -m pytest -q .claude/hooks/tests/test_stop_auto_mode_check.py -k t222`

```
FAILED ...::test_t222_ac2_the_hook_prefix_constant_equals_the_templates_first_line
FAILED ...::test_t222_ac3_a_call_off_the_pattern_does_not_count[Advocates summary-None]
FAILED ...::test_t222_ac3_a_call_off_the_pattern_does_not_count[Advocate 1 keep x-None]
FAILED ...::test_t222_ac3_a_call_off_the_pattern_does_not_count[Advocate 1: x-Argue for keeping it. Using the repo, answer alone: x]
FAILED ...::test_t222_ac3_a_call_off_the_pattern_does_not_count[Advocate 1: x-Using the repo, answer: x]
FAILED ...::test_t222_ac3_a_call_off_the_pattern_does_not_count[Advocate 1: x- Using the repo, answer alone: x]
FAILED ...::test_t222_ac3_a_call_off_the_pattern_does_not_count[Advocate 1: x-]
FAILED ...::test_t222_ac3_check5_at_high_risk_blocks_when_one_of_three_lacks_the_prefix
FAILED ...::test_t222_ac3_medium_with_one_good_and_a_summary_agent_blocks_with_has_1
FAILED ...::test_t222_ac5_a_summary_cut_inside_the_prefix_is_not_counted
10 failed, 3 passed, 56 deselected in 0.91s
```

(The 3 that pass already: `advocate 1: x` lower case, and the two AC 4 tests. The old hook let an `[auto]` run stop with `{}` in the failed cases, e.g. AC 5: `AssertionError: {}`.)

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
