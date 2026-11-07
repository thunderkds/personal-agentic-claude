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

**BEFORE** (captured 2026-11-07T06:28:48Z, Linux, before any implementation commit; this task changes test code only):

Verbatim `conftest.py` markers section (the only marker is `posix_only`; no `needs_symlinks`, no `needs_bash`):

```python
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "posix_only(reason): skip on native Windows (sys.platform == 'win32'); the reason is required",
    )


def pytest_collection_modifyitems(config, items):
    for item in items:
        for mark in item.iter_markers(name="posix_only"):
            reason = (mark.args[0] if mark.args else mark.kwargs.get("reason", "")) or ""
            if not str(reason).strip():
                raise pytest.UsageError(f"{item.nodeid}: posix_only needs a non-empty reason")
            if sys.platform == "win32":
                item.add_marker(pytest.mark.skip(reason=f"POSIX-only: {reason}"))
            break
```

Tests to mark `needs_symlinks` (found by running the suite with `os.symlink` and `Path.symlink_to` patched to raise `OSError(1314)` through a `sitecustomize` on `PYTHONPATH`; 29 + 2 failed):

- test_dotfiles.py::test_dangling_source_base_link_is_refused
- test_dotfiles.py::test_each_source_part_is_optional
- test_dotfiles.py::test_second_apply_writes_nothing
- test_dotfiles.py::test_links_are_made_for_skills_and_instructions
- test_dotfiles.py::test_conflicts_are_reported_and_left_unchanged
- test_dotfiles.py::test_dangling_link_is_a_conflict
- test_dotfiles.py::test_correct_link_is_no_change
- test_dotfiles.py::test_skills_path_that_is_not_a_plain_folder_is_a_conflict[link]
- test_dotfiles.py::test_symlinked_settings_is_reported_and_not_replaced
- test_dotfiles.py::test_codex_target_never_gets_settings
- test_dotfiles.py::test_missing_target_folder_codes
- test_dotfiles.py::test_target_equal_to_source_is_refused_and_the_next_goes_on[--claude-dir-plan]
- test_dotfiles.py::test_target_equal_to_source_is_refused_and_the_next_goes_on[--claude-dir-apply]
- test_dotfiles.py::test_target_equal_to_source_is_refused_and_the_next_goes_on[--claude-dir-status]
- test_dotfiles.py::test_target_equal_to_source_is_refused_and_the_next_goes_on[--codex-dir-plan]
- test_dotfiles.py::test_target_equal_to_source_is_refused_and_the_next_goes_on[--codex-dir-apply]
- test_dotfiles.py::test_target_equal_to_source_is_refused_and_the_next_goes_on[--codex-dir-status]
- test_dotfiles.py::test_status_exit_codes
- test_dotfiles.py::test_link_left_broken_by_the_source_is_a_conflict[--claude-dir-AGENTS.md]
- test_dotfiles.py::test_link_left_broken_by_the_source_is_a_conflict[--claude-dir-skills/one]
- test_dotfiles.py::test_link_left_broken_by_the_source_is_a_conflict[--claude-dir-skills/two]
- test_dotfiles.py::test_link_left_broken_by_the_source_is_a_conflict[--codex-dir-AGENTS.md]
- test_dotfiles.py::test_link_left_broken_by_the_source_is_a_conflict[--codex-dir-skills/one]
- test_dotfiles.py::test_link_left_broken_by_the_source_is_a_conflict[--codex-dir-skills/two]
- test_dotfiles.py::test_broken_link_is_reported_once_when_the_source_part_exists
- test_dotfiles.py::test_broken_link_outside_the_source_is_left_alone
- test_dotfiles.py::test_relative_broken_link_into_the_source_is_found
- test_dotfiles.py::test_broken_link_found_through_a_linked_source_path
- test_dotfiles.py::test_only_settings_json_is_opened_in_a_target
- test_plugin_names.py::test_every_skill_dir_path_exists_in_the_setup_install_layout
- test_plugin_names.py::test_every_skill_dir_command_runs[install]

Tests to mark `needs_bash`: all 7 in `tests/test_ci_verify_done_tasks.py::CiVerifyDoneTasksTest`.
Tests to mark `posix_only` (illegal file name): `tests/test_dotfiles.py::test_t230_a_skill_folder_name_with_unprintable_text_is_refused[x3]`, `tests/test_self_review.py::test_fx9_odd_review_file_name_is_ignored`.
Tests to edit: `tests/test_dirty_worktrees.py::test_sc5_missing_worktree_dir` (`rm -rf`), `tests/test_companion_setup.py::_run` (fake tool `.cmd`), path-separator normalization in `test_board_create.py::test_cache_is_named_by_the_board_id_and_has_no_forged_review_section`, `test_board_id_pattern.py::test_dirty_worktrees_maps_lowercase_board_branch` and `::test_dirty_worktrees_without_config_maps_t_ids_only`, `test_dirty_worktrees.py::test_sc1_dirty_in_progress_worktree_reported` and `::test_subfolder_run_finds_board`, `test_self_review.py::test_ac10_default_report_path`, `test_plugin_init.py` (`test_ac1_init_creates_every_d2_file_and_the_project_counts_as_a_kit_project`, `test_ac2_a_file_inside_a_copied_tree_is_kept_and_named`).

Command: `python3 -m pytest tests/test_companion_setup.py tests/test_dirty_worktrees.py -q`
```
...................................                                      [100%]
35 passed in 0.78s
```
(On Linux these pass; the failures are Windows-only and cannot be shown here. Marker tests do not exist yet: `tests/test_windows_markers.py` is absent.)

**AFTER** (2026-11-07T06:49Z, Linux): `python3 -m pytest tests/test_windows_markers.py -q` -> `21 passed in 6.22s`; `python3 -m pytest .claude/hooks/tests tests -q` -> `1 failed, 3870 passed, 25 subtests passed in 366.35s` (the one failure is the parity ledger pin, red before this task too; the Supervisor updates `docs/windows-parity.md`). With symlinks denied and a failing `bash`, the nested run of the marked tests gives `0 failed, 38 skipped`. The Windows run is the user's: `py -3 -m pytest tests .claude\hooks\tests -q --timeout=60`.

**DELTA**: A Windows run without Developer Mode or a working `bash` now skips the tests that need them, with a written reason, so a red test points at a kit bug.

**WITNESS**: Linux runs by common-infrastructure agent 2026-11-07; the Supervisor confirms from `memory/event-trace/T274.jsonl`. The Windows re-run is the user's.
