# TASK_REVIEW — T182: Auto verify — for an `[auto]` task, a hook runs the real `/verify` in a fresh headless session

> Sibling of `tasks/TASK_GUIDE_T182.md`. Everything here is **filled by the reviewer at Stage
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
| AC 1 spike (paid, cap $1, user go 2026-10-27: "182 and 181") | ☑ pass | Supervisor 2026-10-27T14:34:46Z–14:35:39Z, cwd `../wt-t180-auto` (branch `feat/t180-auto-mode`, clean), command: `timeout 900 claude -p "/verify T180" --max-budget-usd 1 --model sonnet --output-format json` (user's normal settings, no `--dangerously-skip-permissions`). Result JSON: `subtype: success`, `is_error: false`, `total_cost_usd: 0.2565`, `num_turns: 7`, `duration_ms: 49612`, `session_id: bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4`, `permission_denials: []`. The built-in skill ran: the result is the skill's own report shape, `## Verification: T180 auto-mode Stop hook (D8–D10) …` / `**Verdict:** PASS` / `**Method:** … There is no verifier-* or run-* skill …` / 9 Steps (4 🔍 probes, temp projects via `mktemp`) / Findings. The worktree stayed clean (`git status --short` empty). Raw output kept in `.spawn/t182-spike/run1.json`. Notes for the build: the verdict is the line `**Verdict:** PASS|FAIL|BLOCKED|SKIP` in `result`; a run with no diff vs the base still ran (it measured the branch against `main`). D1 holds: no hand-written equivalent is needed. |
| AC 8 live check (paid, cap $4, user go 2026-10-27: "approve") | ☑ pass | Supervisor 2026-10-27T15:13Z–15:16Z. Fixture: a clone of `feat/t182-auto-verify` at `e77c155` in `.spawn/t182-live/repo`, branch `feat/t999-greet`; board cleared to one Ready for Review row, **T999** (a greet script + 2 tests, `tasks/TASK_REVIEW_T999.md` with `## Auto decisions` / `Mode: auto` and an unfilled `verify` row), committed as `794fdbf`. **Trigger:** `echo '{"hook_event_name":"Stop"}' | python3 .claude/hooks/stop_auto_verify.py` → `[hook:stop_auto_verify] T999: auto verify started for commit 794fdbfa225f — log .claude/verify-runs/T999-794fdbfa225f.log`, returned in 0.03 s; a second fire on the same commit started nothing (one `claude -p /verify T999 --max-budget-usd 2 --output-format json` process). **Run:** real headless `/verify`, `subtype: success`, `$0.35`, 4 turns, 35 s, `permission_denials: []`, `**Verdict:** PASS` (9 steps, 5 probes; it also flagged that the fixture commit removed the T182 board row — true, the fixture cleared the board). **Row written by the hook:** `| verify | ☑ pass | auto-run by hook, session 4056d1a7-2950-4065-9188-e43ab751c1a1, commit 794fdbfa225fb3803e5522aba0a19f1ba4931a0c, log .claude/verify-runs/T999-794fdbfa225f.log — pass |`. **Merge gate** (`git merge feat/t999-greet` on the clone's `pre_bash_block_unsafe_merge.py`): G1 before the task's test run is traced → `T999 (evidence row present but no verified tool call …)` (the row was accepted; the trace rule is unchanged); G2 after a real `pytest` run fed through `post_tool_trace.py` with T999 active → allowed. **Forgery and drift:** session id changed by hand → blocked `(no evidence row)`; commit changed to one with no record → blocked; Notes `auto-checked, not /verify` → blocked; a commit that changes only `tasks/TASK_REVIEW_T999.md` → still allowed (D2 tolerance); a new code commit → blocked, and the row is due again (`same_code False`, a new run would start; not run, to save cost). Spend: $0.35 (AC 1 + AC 8 together $0.61 of $5). The record itself was not read directly (the anchor folder is denied to the Supervisor's Bash too); the gate's acceptance is the evidence it exists and matches. |
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | common-infrastructure 2026-10-27. New: `tests/test_auto_verify.py` (50 tests; `claude` stubbed on a PATH of stub dir + `/usr/bin:/bin`, `_env` asserts no real `claude` is reachable) with fixture `tests/fixtures/auto_verify/verify_pass.json` (trimmed spike JSON). AC 2: `test_ac2_*` (returns at once, detached runner leads its own session, once per task+commit, blocked run not retried, new code commit reruns, review-file-only commit does not, not Ready for Review / user-filled / inside the headless run → no run, two tasks → two logs + records). AC 3: `test_ac3_*` (argv `-p "/verify T951" --max-budget-usd 2 --output-format json`, no resume/skip-permissions, cwd = worktree, budget override, log gitignored). AC 4: `test_ac4_*` (pass/fail shape; 9 blocked cases + timeout + no `claude`, Notes never contain "pass"; a user-filled row is kept). AC 5: `test_ac5_*` (accepted with record, also from a worktree and after a review-file-only commit; blocks: no record, record for another commit, row retargeted to head, fail record, record for another task, record the agent could write in the repo, 3 `auto-checked` rows; record path under the `permissions.deny` globs; relative record dir refused). AC 6: `test_ac6_*` (no marker / marker in a comment → no run; T180 check silent in the headless run; tracks.md step; AGENTS.md ≤200; glossary; settings wiring). RED commit `b9c02fc`: 45 failed, 5 passed; GREEN `42859ce`: 50 passed. |
| Verification command run | ☑ pass | common-infrastructure 2026-10-27T15:06:38Z on `42859ce`: `python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests` → `967 passed, 25 subtests passed in 43.53s`; `python3 -m pytest -q tests` → `832 passed in 37.38s`; `sh scripts/validate.sh` → `validate.sh: PASS`. |
| Negative cases hold | ☑ pass | common-infrastructure 2026-10-27: `python3 -m pytest -q tests/test_auto_verify.py -k "ac5 or ac6_no_auto or ac4_blocked or ac4_timeout or ac4_claude_not or ac4_fail"` → `29 passed, 21 deselected in 7.50s`. Mutation control (temporary edits, reverted, tree clean): M1 remove the D5 record check in the gate → 8 RED (`test_ac5_hand_typed_row_with_no_record_blocks`, `…record_for_another_commit_blocks`, `…row_retargeted_to_the_head_commit_without_its_record_blocks`, `…fail_record_blocks_even_if_the_row_is_edited_to_pass`, `…record_for_another_task_blocks`, `…a_record_the_agent_could_write_is_not_trusted`, plus the two gate-file pins); M2 accept any record verdict → `…fail_record_blocks…` RED; M3 skip the head-commit check → `…record_for_another_commit_blocks` RED. Existing merge-gate suites (`.claude/hooks/tests/test_merge_gate_*.py`, `test_verify_row_fill_detection.py`, `tests/test_merge_gate_review_filter.py`, `tests/test_auto_mode.py` AC 4) all green. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 (Supervisor, 2026-10-27): `git diff 0222ad6..HEAD` — `.claude/hooks/stop_auto_verify.py` (new, 258 lines), `.claude/hooks/lib/verify_record.py` (new, 128), `.claude/hooks/pre_bash_block_unsafe_merge.py` (+13: `has_filled_verify_row` only), `.claude/hooks/stop_auto_mode_check.py` (+4: `CLAUDE_AUTO_VERIFY_RUN` guard), `.claude/settings.json` (one `Stop` entry), `.gitignore`, `docs/claude-md/tracks.md`, `PROJECT_SPEC.md`, `site/index.html` (hook row), tests. Direct callers: `main()` of the gate (`has_filled_verify_row` at `:509`, still AND-ed with `trace_shows_verification` at `:510`). **code-review: 0 P0, 0 P1, 2 P2.** (P2-a, conf 100) the forgery residual is wider than the docstring says: any agent `Bash` call that imports `verify_record.write_record` (e.g. `python3 -c` with `.claude/hooks/lib` on `sys.path`) writes a valid record without naming the anchor directory, so the `Bash(*harness-anchors*)` deny never fires — same class as running the script with a fake `claude`, and as T148's anchors (raises the bar, not a proof); a `Bash(*stop_auto_verify*)` deny would not close it. (P2-b, conf 75) every new code commit on an `[auto]` task at Ready for Review starts a paid run (default `--max-budget-usd 2`, 1800 s) with no per-run consent — by design (D2/D3), but `tracks.md` should state the per-commit cost. Checked, no finding: the row's verdict comes only from one `**Verdict:**` line (two different verdicts → blocked); a user-filled row is never overwritten (`write_row`, `due`); the child session gets `CLAUDE_AUTO_VERIFY_RUN=1` so neither Stop hook re-fires in it; one run per task + commit via an `O_EXCL` log; the gate tightening (`auto-checked` rows rejected) affects no existing row (`grep -l '^| verify |.*auto-checked' tasks/*.md` → none). **Security pass (High): no finding ≥ 0.8.** `subprocess` calls use argv lists, no shell; task IDs reach argv and paths only through `[A-Za-z]+-?\d+` (`ROW_ID`) and `safe_name`; the record base must be absolute (`record_dir`); output JSON is parsed, never run. The anchor deny rule was observed live: the Supervisor's own Bash call naming the directory was denied (2026-10-27). The built-in `security-review` reviews the main checkout's branch, so the pass was done inline. |
| Full smoke suite still green (no regression) | ☑ pass | Same run as the verification command: 1749 unique tests (967 + 832, `tests/test_auto_verify.py` counted in both), 0 failed; baseline before T182 was 1699 passed. Three earlier tests changed on purpose: T180's two merge-gate file pins (`tests/test_auto_mode.py::test_ac4_merge_gate_file_is_unchanged`, `.claude/hooks/tests/test_stop_auto_mode_check.py::test_merge_gate_is_untouched`) now allow commits naming T182 only and still fail on any uncommitted gate change; `tests/test_subagent_sandbox_profile.py::test_sc5_*` names the two T182 `settings.json` lines. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI component: a hook, a lib module and docs. The only page change is one hook-table row in `site/index.html` that `tests/test_site_content.py` requires for every wired hook (66 passed). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI component; the site row reuses the existing `tag tag-advise` and `<details>` markup (`test_visible_table_cells_are_short` passes). |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI component; the row uses the table's existing `data-label` cells. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure at 2026-10-27T14:42:24Z on `7e73811` (before any T182
implementation commit), command `python3 /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/55ed681c-3b51-48e8-a01f-66698e543862/scratchpad/t182_demo.py /home/hungnguyenhuu/workspace/pets/wt-t182-auto-verify`
(a temp git project with the kit's hooks and `settings.json`; T951 is `Mode: auto`, Ready for Review, `verify`
row unfilled; `claude` on `PATH` is a stub that logs its argv and prints `**Verdict:** PASS`):

```
$ date -u  -> 2026-10-27T14:42:24Z
kit: /home/hungnguyenhuu/workspace/pets/wt-t182-auto-verify @ 7e73811
temp project head: 46e2d0f591c4; stub claude: /tmp/t182_demo_4pne2y_n/bin/claude

== 1. Stop hooks fire for the [auto] task T951 at Ready for Review ==
  stop_review_reminder.py: exit 0 in 0.02s
  stop_auto_mode_check.py: exit 0 in 0.03s
  stub claude calls: (none)
  verify row: | verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed] |
  .claude/verify-runs/: (absent)

== 2. hand-typed row, no D5 record, no test run in the trace ==
  git merge feat/t951: BLOCK — • Tasks in Ready for Review missing Stage 5 verify evidence: T951 (evidence row present but no verified tool call in memory/event-trace/T951.jsonl)

== 3. same hand-typed row, a test run in the trace ==
  git merge feat/t951: ALLOW
```

Today no Stop hook starts a `/verify` run (the stub is never called, the row stays unfilled). A hand-typed
`☑ pass | auto-run by hook, session forged-1, commit <sha>, … — pass` row is blocked only for the reason any
unverified row is (no test run in the trace); once the trace has a test run, the forged row is accepted.

**AFTER**: same command, captured by common-infrastructure at 2026-10-27T15:06:06Z on `42859ce` (GREEN):

```
$ date -u  -> 2026-10-27T15:06:06Z
kit: /home/hungnguyenhuu/workspace/pets/wt-t182-auto-verify @ 42859ce
temp project head: a5eddbb54ccb; stub claude: /tmp/t182_demo_2mnnup6r/bin/claude

== 1. Stop hooks fire for the [auto] task T951 at Ready for Review ==
  stop_review_reminder.py: exit 0 in 0.02s
  stop_auto_mode_check.py: exit 0 in 0.03s
  stop_auto_verify.py: exit 0 in 0.03s
  stub claude calls: -p /verify T951 --max-budget-usd 2 --output-format json
  verify row: | verify | ☑ pass | auto-run by hook, session stub-0001, commit a5eddbb54ccb8da6b6c754941ec8c42372715516, log .claude/verify-runs/T951-a5eddbb54ccb.log — pass |
  .claude/verify-runs/: ['T951-a5eddbb54ccb.log']

== 2. hand-typed row, no D5 record, no test run in the trace ==
  git merge feat/t951: BLOCK — • Tasks in Ready for Review missing Stage 5 verify evidence: T951 (no evidence row)

== 3. same hand-typed row, a test run in the trace ==
  git merge feat/t951: BLOCK — • Tasks in Ready for Review missing Stage 5 verify evidence: T951 (no evidence row)
```

The Stop hook now returns in 0.03 s and the detached run calls `claude` once with the D3 flags and writes the
D4 row and its log. The hand-typed `auto-run by hook … pass` row is blocked in both cases, also once the
trace has a test run (in case 2 and 3 a real record exists for that commit from step 1, but it names
session `stub-0001`, not the typed `forged-1`). The hook-written row itself is accepted:
`tests/test_auto_verify.py::test_ac5_hook_row_with_its_record_is_accepted`.

**DELTA**: For an `[auto]` task at Ready for Review, the user now gets a real `/verify` result in the `verify` row without typing `/verify`, and the merge gate refuses an `auto-run by hook` row that no hook run recorded.

**WITNESS**: BEFORE and AFTER run by common-infrastructure (2026-10-27T14:42:24Z and 15:06:06Z, Bash calls
attributed to T182 via the active-task state file). Needs a second witness: the Supervisor re-runs the same
command, and AC 8 (paid live check) is the Supervisor's after the user's go.
