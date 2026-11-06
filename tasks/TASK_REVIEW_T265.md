# TASK_REVIEW — T265: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T265.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_proc.py` (17 tests, new in `c097b620`): AC 3 `test_posix_kill_tree_kills_parent_and_grandchild` (real `sh -c 'sleep 60 & echo $!; wait'`, held PIDs only, both gone within 5 s, child leads its own session); AC 4 `test_windows_start_detached_uses_creationflags_not_new_session`, `test_windows_kill_tree_runs_taskkill_as_an_argument_list` (forced `win32`, fake `Popen`/`run`); AC 5 `test_posix_kill_tree_on_exited_process_does_not_raise`, `test_posix_kill_tree_twice_is_a_no_op`, `test_windows_kill_tree_on_exited_process_runs_nothing`; AC 6 `test_kill_tree_rejects_a_non_int_pid_before_running_anything` ×5 (`"4242"`, `"4242 & calc"`, `42.0`, `None`, `True`), `test_posix_kill_tree_rejects_a_non_int_pid`; AC 2 `test_stop_auto_verify_uses_the_helper_only`; plus `test_start_detached_refuses_shell`, `test_start_detached_refuses_a_command_string`, `test_windows_kill_tree_falls_back_to_kill_when_taskkill_is_missing`. 2026-11-06T12:07:56Z `python3 -m pytest .claude/hooks/tests/test_proc.py -q` → `17 passed in 0.04s` |
| Verification command run | ☑ pass | 2026-11-06T12:07:56Z on `c097b620`: `python3 -m pytest .claude/hooks/tests/test_proc.py -q && python3 -m pytest .claude/hooks/tests -q -k "auto_verify or proc"` → `17 passed in 0.04s` then `21 passed, 1517 deselected in 1.79s`. AC 7: `python3 -m pytest tests/test_auto_verify.py -q` (the existing stop_auto_verify suite, unchanged) → `254 passed in 94.95s` (2026-11-06T11:59:27Z; same count as BEFORE). `grep -n "killpg\|start_new_session\|SIGKILL" .claude/hooks/stop_auto_verify.py` → no lines (exit 1) |
| Negative cases hold | ☑ pass | Red first (2026-11-06T11:58:01Z, before `lib/proc.py` existed): `ERROR .claude/hooks/tests/test_proc.py` / `1 error in 0.12s`; then with the helper but the hook unchanged: `FAILED .claude/hooks/tests/test_proc.py::test_stop_auto_verify_uses_the_helper_only` / `1 failed, 16 passed`. Mutation control (Success 4, 2026-11-06T11:59:15Z; `proc.py` untracked then, so `diff -u` against a saved copy instead of `git diff --stat`): `-        os.killpg(pid, signal.SIGKILL)  # the group ... +        proc.kill()  # MUTATION: parent only` → `E           AssertionError: grandchild 294406 survived kill_tree` / `1 failed, 16 deselected in 5.04s`; restored (`diff` empty) → `17 passed`. Leftover `sleep` killed by the test's own `killpg` cleanup (`kill -0 290580` → `no such process`) |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `1538 passed, 25 subtests passed in 50.44s` (2026-11-06T12:01:03Z); `python3 -m pytest tests -q -p no:cacheprovider` → `1899 passed in 166.32s` (2026-11-06T12:04:47Z, after repointing the pin in `tests/test_hooks_from_plugin.py::test_no_data_path_comes_from_file`, which allowed `__file__` only on a `subprocess.Popen` line; it now also allows a `start_detached(` line — the same "spawn this hook" code location). Shell suites (`tests/*.sh`) not run: no shell file changed |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: a Python hook helper and its tests |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI: a Python hook helper and its tests |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI: a Python hook helper and its tests |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-11-06T11:54:31Z on `0aafdf84` (worktree `wt-t265`, before any implementation commit):

```
$ python3 -m pytest .claude/hooks/tests/ -q -k auto_verify
.                                                                        [100%]
1 passed, 1520 deselected in 1.31s

$ grep -n "killpg\|start_new_session\|SIGKILL" .claude/hooks/stop_auto_verify.py
206:                         close_fds=True, start_new_session=True)  # setsid: survives this hook
373:                                start_new_session=True)
380:            os.killpg(proc.pid, signal.SIGKILL)

$ ls .claude/hooks/lib/proc.py
ls: cannot access '.claude/hooks/lib/proc.py': No such file or directory
```

The `stop_auto_verify` tests proper live in `tests/test_auto_verify.py` (2026-11-06T11:54:40Z):

```
$ python3 -m pytest tests/test_auto_verify.py -q
254 passed in 95.41s (0:01:35)
```

On Windows the three lines above cannot work: `os.killpg` and `signal.SIGKILL` do not exist there, and
`start_new_session` is ignored, so auto verify cannot detach its run or kill it on timeout.

**AFTER**: captured 2026-11-06T12:07:56Z on `c097b620`:

```
$ python3 -m pytest .claude/hooks/tests/test_proc.py -q && python3 -m pytest .claude/hooks/tests -q -k "auto_verify or proc"
17 passed in 0.04s
21 passed, 1517 deselected in 1.79s

$ grep -n "killpg\|start_new_session\|SIGKILL" .claude/hooks/stop_auto_verify.py
(no lines; exit 1)

$ grep -n "start_detached\|kill_tree" .claude/hooks/stop_auto_verify.py
99:from proc import kill_tree, start_detached  # noqa: E402
203:        start_detached([sys.executable, os.path.abspath(__file__), "--run", task.task_id,
374:        proc = start_detached(argv, cwd=checkout, env=env, stdin=subprocess.DEVNULL,
381:        kill_tree(proc)

$ python3 -m pytest tests/test_auto_verify.py -q
254 passed in 94.95s (0:01:34)
```

**DELTA**: auto verify now has one helper (`.claude/hooks/lib/proc.py`) that detaches its run and kills it with its children on timeout on Windows (`CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS`, `taskkill /T /F`) as well as on POSIX, where behaviour is unchanged; the Windows branch is proven with fakes only, until T263's CI.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
