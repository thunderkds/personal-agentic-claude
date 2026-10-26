# TASK_REVIEW — T177: Kit-arms round 2 — a scripted user answers at each stop

> Sibling of `tasks/TASK_GUIDE_T177.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `experiments/kit-arms/tests/test_kit_arms.py` (T177 section, 16 test functions): SC1 `test_sc1_stop_without_change_sends_reply1_resuming_turn1_session`, `test_sc1_trailing_question_triggers_a_reply_even_after_a_change`, `test_needs_reply_is_the_s1_trigger`; SC2 `test_sc2_finished_change_gets_no_reply`; SC3 `test_sc3_never_finishing_run_gets_exactly_two_replies_from_the_file`, `test_missing_session_id_ends_the_run_after_turn1`; SC4 `test_sc4_followup_argv_mounts_copy_run_home_and_read_only_credentials_only`, `test_make_home_is_fresh_and_holds_only_the_credentials_mountpoint`, `test_sc4_real_followup_through_the_docker_stub_and_the_3x_cap`, `test_followup_cap_stops_before_any_run`; SC5 `test_sc5_grade2_passes_only_biggest_total_first` (4 cases); SC6 `test_sc6_followup_dry_run_36_cells_zero_spend`; AC 2 `test_replies_json_holds_the_s2_replies_verbatim`. RED at `73015d3` (16 failed, 58 passed); GREEN at `f66550d`: `74 passed in 343.67s (0:05:43)` (agent, 2026-10-26). |
| Verification command run | ☑ pass | Run 2026-10-26T14:56:45Z at `f66550d` (agent), tail: `task6 full    run 2: fail      $0.00  0s  (spent $0.00)` / `Report: /tmp/kit-arms-r2-dry/report.md  (36 runs, spend $0.00, rule complete: True)` / `0` (RULE.md diff vs `e3affd5`: 0 lines). Dry run: 36 rows, turns_used 1/2/3 = 12/12/12, replies used 12 per arm, spend $0.00. |
| Negative cases hold | ☑ pass | Finished change without trailing `?` gets no reply; missing `session_id` ends the run after turn 1 and counts the turn's budget; never-finishing run stops at 3 turns even when replies.json holds 3 replies; spent 22.5 + 3 x $1.00 > $25 stops before any run with no docker call; grade2 fails `guessed-B`, untouched fixture, and asked-without-change. Main checkout `git status --porcelain` identical before and after the verification command; `docker ps -a --filter name=tally-run -q` = 0. Round 1 frozen paths: `git diff 504eab0 -- RULE.md fixture tasks oracles arms Dockerfile results` = 0 lines (grade2.py is new, outside that diff only as an addition). |
| verify | ☐ pass / ☐ fail / ☐ N/A | (user-only; Supervisor) |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | (Stage 4 reviewer) Affected set: `experiments/kit-arms/run_arms.py`, `replies.json`, `oracles/task4/grade2.py`, `RULE-2.md`, `tests/test_kit_arms.py`. No kit file touched. |
| Full smoke suite still green (no regression) | ☑ pass | All 58 round-1 kit-arms tests still pass inside the 74 (round-1 `claude_argv`/`docker_argv` output unchanged when `home` is not given). Kit suites not run: no kit file changed. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: Python runner and data files only. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI: Python runner and data files only. |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI: Python runner and data files only. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure at the start of T177, before any file in the worktree changed (HEAD `c92bf96`, git status clean; no implementation commit exists yet):

```
2026-10-26T10:09:25Z
$ python3 experiments/kit-arms/run_arms.py --help | grep -c -- --followup
0
$ ls experiments/kit-arms/replies.json experiments/kit-arms/RULE-2.md 2>&1
ls: cannot access 'experiments/kit-arms/replies.json': No such file or directory
ls: cannot access 'experiments/kit-arms/RULE-2.md': No such file or directory
HEAD c92bf96
```

**AFTER**: same commands at `f66550d` (agent):

```
2026-10-26T15:02:05Z
$ python3 experiments/kit-arms/run_arms.py --help | grep -c -- --followup
2
$ ls experiments/kit-arms/replies.json experiments/kit-arms/RULE-2.md 2>&1
experiments/kit-arms/RULE-2.md
experiments/kit-arms/replies.json
HEAD f66550d
```

**DELTA**: `run_arms.py --followup` now runs each cell as up to 3 turns, answering a stop with the fixed replies from `replies.json` via `--resume` in a per-run HOME, and grades the final state under `RULE-2.md`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
