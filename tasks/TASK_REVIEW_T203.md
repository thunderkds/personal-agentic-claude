# TASK_REVIEW — T203: Auto verify for every task, started by the Supervisor

> Sibling of `tasks/TASK_GUIDE_T203.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_auto_verify.py` — 32 new `test_t203_*` functions (39 cases): AC 1 `test_t203_ac1_*` (unmarked extended row, unmarked minimal line, no review file = one stderr line); AC 2 `test_t203_ac2_*` (`--start` returns at once with the log path, twice = one run + `already started`, Stop hook and `--start` share one lock both orders, not at Ready for Review, user-filled row, new commit = new run, no `claude` = blocked, no review file = one line); AC 3 `test_t203_ac3_*` (off/OFF/` off ` hook, off `--start`, off minimal, off still runs a marked task both entries); AC 4 `test_t203_ac4_*` (user row/line never run over, child guard both entries, unmarked pass does not move to Done, marked pass still closes out); AC 5 `test_t203_ac5_*` (unmarked: hook row + record allows; hand-typed, other commit, fail record, `auto-checked` block); AC 6 `test_t203_ac6_*` (5 doctrine tests); AC 7 `test_t203_ac7_*` (merge-settings adds the Stop entry, keeps user Stop entry, `permissions.allow`, `model`; MANIFEST ships the hook files). Mutation check: against the pre-T203 hook (`git show HEAD:.claude/hooks/stop_auto_verify.py`), `-k t203` → `20 failed, 13 passed, 139 deselected in 195.61s` (the 13 are negatives and AC 7, true before too). `python3 -m pytest -q tests/test_auto_verify.py -p no:cacheprovider -k t203` → `39 passed, 139 deselected in 32.33s`. **Stage 4 fixes (test-first; all 11 failed before the fix: `11 failed, 178 deselected in 3.71s`, then `11 passed, 178 deselected in 2.60s`):** P1 `test_t203_p1_a_worktree_copy_wins_over_main_placeholder_and_the_run_is_in_the_worktree` (main placeholder + worktree copy → checkout is the worktree, stub `claude` cwd is the worktree, main copy byte-identical), `test_t203_p1_with_two_worktree_copies_the_branch_naming_the_task_wins`, `test_t203_p1_branch_names_the_task_word_bounded` (6 cases), `test_t203_p1_a_minimal_record_in_a_worktree_wins_over_main_without_it`; P2 `test_t203_p2_the_hook_in_a_linked_worktree_starts_nothing` (Stop hook and `--start`). Read-only dry run of the fixed `resolve()` on main's board: `T189 marker=True checkout=/home/hungnguyenhuu/workspace/pets/wt-t189`, `T191 marker=False checkout=/home/hungnguyenhuu/workspace/pets/wt-t191`, `T143 marker=False checkout=/home/hungnguyenhuu/workspace/pets/wt-t143` **Security-review Medium fix (test-first; 11 failed before: `11 failed, 189 deselected in 1.24s`):** `test_t203_sec_row_branch_reads_the_newest_started_segment` (5 cases, both row shapes), `test_t203_sec_a_decoy_naming_the_task_and_sorting_first_loses_to_the_row_branch` (decoy `fix/t951-x` listed first; the run's cwd is the real worktree; the decoy's row stays empty), `test_t203_sec_two_worktrees_naming_the_task_and_no_branch_in_the_row_start_nothing` (Stop hook and `--start`: one `ambiguous … nothing started` line, no `claude` call), `test_t203_sec_a_row_branch_with_no_live_worktree_uses_no_worktree_copy`, `test_t203_sec_no_branch_in_the_row_and_exactly_one_worktree_naming_the_task_is_used`, `test_t203_sec_no_branch_in_the_row_and_no_worktree_naming_the_task_is_ambiguous`; after: `22 passed, 178 deselected in 5.13s` (`-k "t203_sec or t203_p"`). Fixture rows updated to name `feat/t951`: `test_t203_p1_a_minimal_record_in_a_worktree_wins_over_main_without_it`, `test_ac2_a_record_in_a_worktree_is_resolved_like_evidence`, `_ran_minimal(worktree=True)`. Read-only dry run on main's board: `T204 branch=feat/t204-graphite-mint ambiguous=False checkout=/home/hungnguyenhuu/workspace/pets/wt-t204` — pass |
| Verification command run | ☑ pass | after the security-review fix (2026-10-29T11:24:38Z): `python3 -m pytest -q tests .claude/hooks/tests -p no:cacheprovider` → `2219 passed, 25 subtests passed in 149.39s (0:02:29)`. After the Stage 4 P1/P2 fixes (2026-10-29T11:12:45Z): `python3 -m pytest -q tests .claude/hooks/tests -p no:cacheprovider` → `2208 passed, 25 subtests passed in 148.55s (0:02:28)`. Before them, at `0eeb35f` (2026-10-29T11:04:06Z) → `2197 passed, 25 subtests passed in 148.74s (0:02:28)` (baseline before T203 at `ae719eb`: `2158 passed, 25 subtests passed in 115.07s`). `sh scripts/validate.sh` → `validate.sh: PASS` (the guide's `./validate.sh` lives at `scripts/validate.sh`) — pass |
| Negative cases hold | ☑ pass | Off switch: unmarked task untouched by hook and `--start` (`CLAUDE_AUTO_VERIFY=off`, also `OFF`, ` off `). Not at Ready for Review / user-filled row / already started / already filled / inside the child run (`CLAUDE_AUTO_VERIFY_RUN=1`) → nothing started, one line. Merge gate for an unmarked task: hand-typed `auto-run by hook` row with no record, record for another commit, fail record edited to pass, `auto-checked, not /verify` → all `block`. D6: an unmarked pass leaves the board byte-identical and writes no `Closed:`/`Paused:` line. The 7 T182/T188 tests that pinned "no marker, no run" now run under `CLAUDE_AUTO_VERIFY=off` and pass — pass |
| verify | ☑ pass | auto-run by hook, session f6681c9c-0f1d-455b-8bef-e688dbf411ef, commit d027b736968b8b0b45568a4a1be60d03be3375b5, log .claude/verify-runs/T203-d027b736968b.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Implementer self-check only (Stage 4 `code-review` + `security-review` still due): changed set = `.claude/hooks/stop_auto_verify.py` (trigger, `--start`, off switch, D6 close-out guard), doctrine (`AGENTS.md`, `docs/claude-md/tracks.md`, `docs/claude-md/pipeline-stages.md`, `PROJECT_SPEC.md`), tests. Stage 4 P1 adds `lib/auto_mode.py` `find_for_task` / `names_task` / `branch_of` (shared by `stop_auto_mode_check.py` through `resolve()`; its tests stay green); P2 adds `linked_worktree()` to the hook. Unchanged and re-run: `pre_bash_block_unsafe_merge.py` (trust rule, no edit), `lib/verify_record.py`, `lib/auto_closeout.py`, `lib/merge-settings.py`, `setup.sh` — pass |
| Full smoke suite still green (no regression) | ☑ pass | same run as above: `2219 passed, 25 subtests passed in 149.39s (0:02:29)`; one pin repointed, not weakened: `.claude/hooks/tests/test_agent_guide_dedup.py` `T070_BASELINE_REF` `65fe3a8` → `2616322` (T203's AGENTS.md edit commit, D4) — pass |
| **Companion score (easy-verifier)** | ☑ N/A | neither companion tool was run by the implementer; the Stage 4 reviewer may score it |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI: a Python hook, doctrine Markdown and tests; no page or component changed |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI: a Python hook, doctrine Markdown and tests; no page or component changed |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI: a Python hook, doctrine Markdown and tests; no page or component changed |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on branch `feat/t203-auto-verify-all` at `ae719eb` (T189's code, no T203 change),
by the scratch script `demo.sh <kit-checkout>`: it copies the kit's `.claude/hooks` into a throwaway git
project whose board has one **unmarked** task (`T951`, no `Mode: auto`) at Ready for Review with an
empty `verify` row, puts a stub `claude` first on `PATH` (it only logs its argv; no real run, no money),
then fires the Stop hook and tries `--start T951`:

```
2026-10-29T10:46:54Z
$ grep -c "Mode: auto" tasks/TASK_REVIEW_T951.md
0
$ echo {"hook_event_name":"Stop"} | python3 .claude/hooks/stop_auto_verify.py
exit 0
$ python3 .claude/hooks/stop_auto_verify.py --start T951 </dev/null
exit 0
$ ls .claude/verify-runs
ls: cannot access '.claude/verify-runs': No such file or directory
$ cat claude_calls.txt
cat: /tmp/t203-demo.pLHCdA/claude_calls.txt: No such file or directory
$ grep "^| verify" tasks/TASK_REVIEW_T951.md
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed] |
```

An unmarked task at Ready for Review gets no run: the Stop hook is silent, `--start` is not an entry
(it falls through to the Stop hook and does nothing), `claude` is never called, and the `verify` row
stays empty — the merge waits on the user's `/verify`.

**AFTER**: the same scratch script, same fixture (unmarked `T951`, stub `claude`), run against the
changed tree at `2616322` (the later `0eeb35f` changes only the wording of the no-`verify`-row
reason, which this fixture does not reach):

```
2026-10-29T10:59:03Z
$ grep -c "Mode: auto" tasks/TASK_REVIEW_T951.md
0
$ echo {"hook_event_name":"Stop"} | python3 .claude/hooks/stop_auto_verify.py
[hook:stop_auto_verify] T951: auto verify started for commit e7c79d3a0073 — log .claude/verify-runs/T951-e7c79d3a0073.log
exit 0
$ python3 .claude/hooks/stop_auto_verify.py --start T951 </dev/null
T951: its result is already filled for commit e7c79d3a0073 — nothing started
exit 1
$ ls .claude/verify-runs
T951-e7c79d3a0073.log
$ cat claude_calls.txt
stub claude called: -p /verify T951 --max-budget-usd 2 --output-format json
$ grep "^| verify" tasks/TASK_REVIEW_T951.md
| verify | ☑ pass | auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit e7c79d3a0073facdcf577e90d04d6be47da26196, log .claude/verify-runs/T951-e7c79d3a0073.log — pass |
```

And with the Supervisor's `--start` as the first entry, plus the off switch (`demo_start.sh`, same
fixture):

```
2026-10-29T10:59:18Z
$ grep -c "Mode: auto" tasks/TASK_REVIEW_T951.md
0
$ CLAUDE_AUTO_VERIFY=off python3 .claude/hooks/stop_auto_verify.py --start T951 </dev/null
T951: CLAUDE_AUTO_VERIFY=off and the task has no `Mode: auto` line — nothing started; /verify stays yours
exit 1
$ python3 .claude/hooks/stop_auto_verify.py --start T951 </dev/null
T951: auto verify started for commit c66d6c90c75d — log .claude/verify-runs/T951-c66d6c90c75d.log
exit 0
$ python3 .claude/hooks/stop_auto_verify.py --start T951 </dev/null
T951: its result is already filled for commit c66d6c90c75d — nothing started
exit 1
$ echo {"hook_event_name":"Stop"} | python3 .claude/hooks/stop_auto_verify.py
exit 0
$ ls .claude/verify-runs
T951-c66d6c90c75d.log
$ cat claude_calls.txt
stub claude called: -p /verify T951 --max-budget-usd 2 --output-format json
$ grep "^| verify" tasks/TASK_REVIEW_T951.md
| verify | ☑ pass | auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit c66d6c90c75d9128593254a8158b6a69bdb7c2ea, log .claude/verify-runs/T951-c66d6c90c75d.log — pass |
```

(The stub answers at once, so the second `--start` finds the row already filled; the "already started"
answer for a run still going is pinned by `test_t203_ac2_start_twice_on_one_commit_runs_once`.)

**DELTA**: A task with no `[auto]` tag now gets its real headless `/verify` run as soon as it reaches
Ready for Review — started by the Supervisor with `--start <ID>`, or by the Stop hook as a backstop —
so the merge gate no longer waits on the user to type `/verify`; `CLAUDE_AUTO_VERIFY=off` brings back
the old rule.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T203.jsonl`, never the
implementing agent alone]
