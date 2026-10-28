# TASK_REVIEW — T190: The merge gate binds a failed companion row, and stays silent when there is none

> Sibling of `tasks/TASK_GUIDE_T190.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured at `2026-10-28T05:40:05Z`, worktree `/home/hungnguyenhuu/workspace/pets/wt-t190-gate`
at `858dd54` — the test file and the AC-4 oracle exist, no implementation commit does.

```
BEFORE capture: 2026-10-28T05:40:05Z
HEAD: 858dd54  (no implementation commit exists yet)

$ python3 -m pytest .claude/hooks/tests/test_merge_gate_companion_rows.py -q
FAILED ...::test_checked_fail_companion_row_blocks_and_names_the_task_and_the_row
FAILED ...::test_checked_fail_blocks_even_though_the_verify_row_is_filled
FAILED ...::test_checked_fail_in_any_ui_design_row_blocks[visual]
FAILED ...::test_checked_fail_in_any_ui_design_row_blocks[design-system]
FAILED ...::test_checked_fail_in_any_ui_design_row_blocks[responsive]
FAILED ...::test_a_failed_ui_row_blocks_whatever_produced_it
FAILED ...::test_an_unreadable_review_file_contributes_no_companion_block
FAILED ...::test_pass_row_citing_a_missing_report_does_not_block_but_warns_once
FAILED ...::test_pass_row_citing_no_path_does_not_block_but_warns_once
FAILED ...::test_a_report_path_that_is_a_directory_warns
FAILED ...::test_the_cited_path_is_checked_not_the_newest_in_the_directory
FAILED ...::test_the_gate_reads_the_result_cell_not_the_whole_row
FAILED ...::test_both_verdicts_in_one_result_cell_read_as_fail
FAILED ...::test_a_failed_row_in_the_task_guide_also_blocks
FAILED ...::test_a_failed_row_in_a_worktree_blocks
FAILED ...::test_the_block_depends_on_the_new_check
FAILED ...::test_the_advisory_depends_on_the_new_check
FAILED ...::test_the_template_carries_the_companion_score_row
FAILED ...::test_the_templates_unchecked_companion_row_does_not_block
19 failed, 23 passed in 0.25s

$ grep -c "Companion score" templates/TASK_REVIEW_template.md
0
$ grep -c "has_failed_companion_row" .claude/hooks/pre_bash_block_unsafe_merge.py
0
```

A `☑ fail` Companion score row on a Ready-for-Review task passes the gate: the push is allowed.

**AFTER**: captured at `2026-10-28T05:43:53Z` at `62bc352`.

```
AFTER capture: 2026-10-28T05:43:53Z
HEAD: 62bc352

$ python3 -m pytest .claude/hooks/tests/test_merge_gate_companion_rows.py -q
..........................................                               [100%]
42 passed in 0.06s

$ python3 -m pytest .claude/hooks/tests/ -q
=========================== short test summary info ============================
FAILED .claude/hooks/tests/test_guide_sections.py::test_ac1_moved_evidence_rows_are_byte_identical_to_the_baseline
FAILED .claude/hooks/tests/test_stop_auto_mode_check.py::test_merge_gate_is_untouched
2 failed, 957 passed, 25 subtests passed in 20.95s

$ sh scripts/validate.sh | tail -2
validate.sh: PASS

$ grep -c "Companion score" templates/TASK_REVIEW_template.md
1
$ grep -c "has_failed_companion_row" .claude/hooks/pre_bash_block_unsafe_merge.py
2
```

The two failures were PRE-EXISTING scope guards. The user authorised widening all three
(`9d99aa8`); final state at `c5f8768`, captured `2026-10-28T06:38:36Z`, the guide's exact
verification chain, exit 0:

```
$ python3 -m pytest .claude/hooks/tests/test_merge_gate_companion_rows.py -q \
    && python3 -m pytest .claude/hooks/tests/ -q \
    && sh scripts/validate.sh
42 passed in 0.09s
960 passed, 25 subtests passed in 30.65s
validate.sh: PASS

$ python3 -m pytest tests/ -q
846 passed in 44.28s
```

After the Stage 4 P1 fix (`4cdcc23`, FR-005 reads the path after a literal `report:` label) and the
P2 table update (`3e642ef`) — four more cases, same three suites:

```
$ python3 -m pytest .claude/hooks/tests/ -q
964 passed, 25 subtests passed in 20.49s

$ python3 -m pytest tests/ -q
846 passed in 38.36s

$ sh scripts/validate.sh
validate.sh: PASS
```

The end-to-end subprocess run was repeated against the label contract at `2026-10-28T06:47:26Z`:
cases 1–5 unchanged, plus a sixth — a `☑ pass` row with no `report:` label but an unrelated real
path (`skills/score/SKILL.md`) in the cell now still warns, where before the fix the advisory was
suppressed:

```
[hook:pre_bash] T900 Companion score row reads pass but its Notes cite no verifier report path
 — that row is unscored, not a pass (FR-005).
  [exit 0]
```

Baselines before the task: `917 passed, 25 subtests` (hooks) and `846 passed` (tests). The hook
suite gains 42 companion-row cases and one mutation proof for the relaxed T064 row check.

End-to-end run of the shipped hook as a real subprocess, real stdin, at
`2026-10-28T05:45:11Z` (`/tmp/claude-1000/.../scratchpad/t190_e2e.sh`, a constructed
repo with the hook tree copied in; `git push origin feat/t900` as the tool_input):

```
1) no companion row at all -> allowed (silent)
  [exit 0]

2) the Companion score row reads a checked fail -> blocked
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review with an Evidence row marked fail: T900 (Companion score) ...
  [exit 0]

3) the same row rewritten to N/A -> allowed again
  [exit 0]

4) a UI design row reads a checked fail -> blocked
{"decision": "block", "reason": "... Tasks in Ready for Review with an Evidence row marked fail: T900 (UI: Responsiveness) ...
  [exit 0]

5) a pass row citing a report that does not exist -> allowed, one advisory on stderr
[hook:pre_bash] T900 Companion score row reads pass but the verifier report it cites is not a
file on disk: /nonexistent/score.html — that row is unscored, not a pass (FR-005).
  [exit 0]
```

**DELTA**: A reviewer can now stop a merge by writing `☑ fail` in a task's Companion score row or
in any of its three UI design rows, and a machine that runs neither companion tool sees no change
at all — same decision, byte for byte.

**WITNESS**: Run by the `common-infrastructure` agent on 2026-10-28 (05:40:05Z BEFORE, 05:43:53Z
AFTER, 05:45:11Z end-to-end) in `/home/hungnguyenhuu/workspace/pets/wt-t190-gate`. Trace:
`memory/event-trace/T190.jsonl` carries the BEFORE-side runs; the runs after 05:40:25Z are
attributed to `T188.jsonl`, because another live session overwrote the shared
`.claude/hooks/.state/active_task` with its own task ID mid-run. A second witness is still owed:
the real `git push` refused by a real failed row is Stage 5 `/verify`, which is the user's to run.
