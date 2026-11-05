# TASK_REVIEW — T255: `self_review.py` — watermark gate, citation check and proposal register

> Sibling of `tasks/TASK_GUIDE_T255.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_self_review.py` — 46 passed (AC 1-14, SC 1-4; fake miner = JSON file, call counter in `test_ac2_no_loop_miner_called_once`) |
| Verification command run | ☑ pass | `46 passed in 6.03s`; real-repo `pre`: `ready 40 109` (149 review files on `main`) |
| Negative cases hold | ☑ pass | FX tests cover fabricated/short/negative-line quotes, odd file names, non-ancestor watermark, malformed JSON/register (exit 2, nothing written), off-main checkout, fix-task review under a new slug |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 code-review of `main...feat/t256-self-review-skill` only (15 files + direct callers: `skills/learn/SKILL.md`, skill-list pins). 3 reviewers (maintainability sonnet, correctness opus, adversarial opus). lane_check: EXCEEDS on both guides (15 files, 1334 lines, mostly tests) — warn-only, label C2/C1 kept. 7 P1 + 5 P2 fixed in fix round 1 (`093545e9`, FX-1..12 / SX-1..6); left as suggestions: beyond-cap patterns lost, Kanban archive not read for `fixed`, no pre/post lock, `--report` accepts any path |
| Full smoke suite still green (no regression) | ☑ pass | after fix round 1: `python3 -m pytest -q .claude/hooks/tests/ tests/` -> `3383 passed, 25 subtests passed in 191.64s` (07:35:08Z, `093545e9`); self-review tests re-run by Supervisor: `82 passed in 8.95s` |
| **Companion score (easy-verifier)** | ☑ N/A | easy-verifier not run (Risk Low; optional) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | pure-backend script/skill text, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | pure-backend script/skill text, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | pure-backend script/skill text, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-11-05T04:25:15Z, worktree `wt-t255`, before any implementation commit; the guide's Verification Command):

```
$ python3 -m pytest -q tests/test_self_review.py
ERROR: file or directory not found: tests/test_self_review.py
no tests ran in 0.00s
$ python3 skills/self-review/scripts/self_review.py pre --repo .
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t255/skills/self-review/scripts/self_review.py': [Errno 2] No such file or directory
```

**AFTER** (2026-11-05T04:30:11Z, commit `feat(T255)`, same two commands):

```
$ python3 -m pytest -q tests/test_self_review.py
..............................................                           [100%]
46 passed in 6.03s
$ python3 skills/self-review/scripts/self_review.py pre --repo . | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'], len(d['files']), d['deferred'])"
ready 40 109
```

**Fix round 1 — BEFORE** (2026-11-05T07:29:57Z, worktree `wt-t256`, branch `feat/t256-self-review-skill` at `96102a2e`; the new and changed tests are written, no fix is applied yet):

```
$ python3 -m pytest -q tests/test_self_review.py tests/test_self_review_skill.py
FAILED tests/test_self_review.py::test_ac1_watermark_at_head_is_nothing_new
FAILED tests/test_self_review.py::test_ac1_no_review_changed_since_watermark
FAILED tests/test_self_review.py::test_sc3_fx12_new_review_commit_repeating_open_pattern_is_not_proposed
FAILED tests/test_self_review.py::test_ac3_range_after_watermark_only - Asser...
FAILED tests/test_self_review.py::test_ac6_known_pattern_dropped[row0-kw0] - ...
FAILED tests/test_self_review.py::test_ac6_known_pattern_dropped[row1-kw1] - ...
FAILED tests/test_self_review.py::test_ac6_known_pattern_dropped[row2-kw2] - ...
FAILED tests/test_self_review.py::test_ac6_known_pattern_dropped[row3-kw3] - ...
FAILED tests/test_self_review.py::test_ac6_known_pattern_dropped[row4-kw4] - ...
FAILED tests/test_self_review.py::test_ac6_low_overlap_is_a_new_pattern - Ass...
FAILED tests/test_self_review.py::test_ac7_regressed_only_with_post_fix_evidence
FAILED tests/test_self_review.py::test_ac7_old_evidence_does_not_count - Asse...
FAILED tests/test_self_review.py::test_ac8_fix_task_review_is_not_evidence - ...
FAILED tests/test_self_review.py::test_ac10_report_failure_leaves_register_untouched
FAILED tests/test_self_review.py::test_ac11_kanban_done_marks_fixed - Asserti...
FAILED tests/test_self_review.py::test_ac11_post_also_marks_fixed - Assertion...
FAILED tests/test_self_review.py::test_ac12_decide - AssertionError: assert 2...
FAILED tests/test_self_review.py::test_ac12_unknown_fingerprint_exit_2_register_unchanged
FAILED tests/test_self_review.py::test_fx8_watermark_not_ancestor_of_head_exits_2[side-branch]
FAILED tests/test_self_review.py::test_fx8_watermark_not_ancestor_of_head_exits_2[unknown]
FAILED tests/test_self_review.py::test_fx1_register_records_title_and_proposal_file
FAILED tests/test_self_review.py::test_fx1_matches_names_a_known_row_across_runs[open]
FAILED tests/test_self_review.py::test_fx1_matches_names_a_known_row_across_runs[rejected]
FAILED tests/test_self_review.py::test_fx1_title_overlap_without_matches_is_held[open]
FAILED tests/test_self_review.py::test_fx1_title_overlap_without_matches_is_held[rejected]
FAILED tests/test_self_review.py::test_fx2_fix_task_review_never_counts_under_a_new_slug[True]
FAILED tests/test_self_review.py::test_fx2_fix_task_review_never_counts_under_a_new_slug[False]
FAILED tests/test_self_review.py::test_fx3_matches_a_fixed_row_is_regressed
FAILED tests/test_self_review.py::test_fx4_off_main_checkout_lists_and_reads_main_content
FAILED tests/test_self_review.py::test_fx4_uncommitted_edit_is_not_evidence
FAILED tests/test_self_review.py::test_fx5_weak_quotes_and_bad_lines_dropped[e]
FAILED tests/test_self_review.py::test_fx5_weak_quotes_and_bad_lines_dropped[#]
FAILED tests/test_self_review.py::test_fx5_weak_quotes_and_bad_lines_dropped[negative-line]
FAILED tests/test_self_review.py::test_fx5_weak_quotes_and_bad_lines_dropped[fabricated-tail]
FAILED tests/test_self_review.py::test_fx5_weak_quotes_and_bad_lines_dropped[over-200]
FAILED tests/test_self_review.py::test_fx5_report_prints_the_file_line_not_the_quote
FAILED tests/test_self_review.py::test_fx6_linked_worktree_uses_the_main_checkout
FAILED tests/test_self_review.py::test_fx6_missing_register_with_reports_exits_2
FAILED tests/test_self_review.py::test_fx7_first_parent_walk_never_mines_a_file_twice
FAILED tests/test_self_review.py::test_fx9_odd_review_file_name_is_ignored - ...
FAILED tests/test_self_review.py::test_fx10_free_text_capped_and_guardrail_files_flagged
FAILED tests/test_self_review.py::test_fx11_decide_changes_only_open_rows[rejected]
FAILED tests/test_self_review.py::test_fx11_decide_changes_only_open_rows[fixed]
FAILED tests/test_self_review_skill.py::test_ac1_frontmatter_user_only_description_and_codex_cap
FAILED tests/test_self_review_skill.py::test_ac3_sx2_exactly_one_read_only_sonnet_miner_reply_saved_to_the_scratchpad
FAILED tests/test_self_review_skill.py::test_ac4_miner_prompt_is_the_spike_prompt_adapted
FAILED tests/test_self_review_skill.py::test_sx3_known_rows_carry_state_title_file_and_miner_sets_matches
FAILED tests/test_self_review_skill.py::test_sx4_report_and_miner_output_are_untrusted_and_guardrail_flag_shown
FAILED tests/test_self_review_skill.py::test_sx5_miner_failure_keeps_watermark_and_names_the_skip_command
FAILED tests/test_self_review_skill.py::test_sx6_register_and_report_live_in_the_main_checkout_and_are_not_committed
50 failed, 32 passed in 8.75s
```

Many of the reds above come from the new 7-column register header in the fixtures alone. To show that each FX test fails on its defect, not on the header, the FX/SC3 tests were also run on the unchanged script from a scratch copy whose fixture keeps the old 5-column header (2026-11-05T07:30:36Z; same tests, only `TABLE_HEAD` and `write_reg` changed back):

```
$ python3 -m pytest -q tests/test_self_review_oldhdr.py -k "fx or sc3" --tb=no -rf
FAILED tests/test_self_review_oldhdr.py::test_sc3_fx12_new_review_commit_repeating_open_pattern_is_not_proposed
FAILED tests/test_self_review_oldhdr.py::test_fx8_watermark_not_ancestor_of_head_exits_2[side-branch]
FAILED tests/test_self_review_oldhdr.py::test_fx8_watermark_not_ancestor_of_head_exits_2[unknown]
FAILED tests/test_self_review_oldhdr.py::test_fx1_register_records_title_and_proposal_file
FAILED tests/test_self_review_oldhdr.py::test_fx1_matches_names_a_known_row_across_runs[open]
FAILED tests/test_self_review_oldhdr.py::test_fx1_matches_names_a_known_row_across_runs[rejected]
FAILED tests/test_self_review_oldhdr.py::test_fx1_title_overlap_without_matches_is_held[open]
FAILED tests/test_self_review_oldhdr.py::test_fx1_title_overlap_without_matches_is_held[rejected]
FAILED tests/test_self_review_oldhdr.py::test_fx2_fix_task_review_never_counts_under_a_new_slug[True]
FAILED tests/test_self_review_oldhdr.py::test_fx2_fix_task_review_never_counts_under_a_new_slug[False]
FAILED tests/test_self_review_oldhdr.py::test_fx3_matches_a_fixed_row_is_regressed
FAILED tests/test_self_review_oldhdr.py::test_fx4_off_main_checkout_lists_and_reads_main_content
FAILED tests/test_self_review_oldhdr.py::test_fx4_uncommitted_edit_is_not_evidence
FAILED tests/test_self_review_oldhdr.py::test_fx5_weak_quotes_and_bad_lines_dropped[e]
FAILED tests/test_self_review_oldhdr.py::test_fx5_weak_quotes_and_bad_lines_dropped[#]
FAILED tests/test_self_review_oldhdr.py::test_fx5_weak_quotes_and_bad_lines_dropped[negative-line]
FAILED tests/test_self_review_oldhdr.py::test_fx5_weak_quotes_and_bad_lines_dropped[fabricated-tail]
FAILED tests/test_self_review_oldhdr.py::test_fx5_weak_quotes_and_bad_lines_dropped[over-200]
FAILED tests/test_self_review_oldhdr.py::test_fx5_report_prints_the_file_line_not_the_quote
FAILED tests/test_self_review_oldhdr.py::test_fx6_linked_worktree_uses_the_main_checkout
FAILED tests/test_self_review_oldhdr.py::test_fx6_missing_register_with_reports_exits_2
FAILED tests/test_self_review_oldhdr.py::test_fx7_first_parent_walk_never_mines_a_file_twice
FAILED tests/test_self_review_oldhdr.py::test_fx9_odd_review_file_name_is_ignored
FAILED tests/test_self_review_oldhdr.py::test_fx10_free_text_capped_and_guardrail_files_flagged
FAILED tests/test_self_review_oldhdr.py::test_fx11_decide_changes_only_open_rows[rejected]
FAILED tests/test_self_review_oldhdr.py::test_fx11_decide_changes_only_open_rows[fixed]
26 failed, 44 deselected in 2.96s
```

**Fix round 1 — AFTER** (FX-1..FX-11 in `self_review.py`, SX-1..SX-6 in `SKILL.md` and `references/miner-prompt.md`; worktree `wt-t256`, before the fix commit):

```
$ python3 -m pytest -q .claude/hooks/tests/ tests/        # 2026-11-05T07:35:08Z
3383 passed, 25 subtests passed in 191.64s (0:03:11)
$ python3 -m pytest -q tests/test_self_review.py tests/test_self_review_skill.py        # 2026-11-05T07:38:37Z
82 passed in 8.46s
$ python3 skills/self-review/scripts/self_review.py pre --repo . | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'], len(d['files']), d['deferred'])"
ready 40 109
```

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
