# TASK_REVIEW — T233: Plugin package and MIT LICENSE at the repo root

> Sibling of `tasks/TASK_GUIDE_T233.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_plugin_package.py` (7 tests; red first: `7 failed in 0.14s` before the files existed; `7 passed in 0.79s` after) |
| Verification command run | ☑ pass | `claude plugin validate . --profile directory` -> `✔ Validation passed with warnings` (warnings: ICON_MISSING, README install line, symlinked .claude dirs; no LICENSE_MISSING); `python3 -m pytest tests -q` -> `1563 passed in 132.81s`; `python3 -m pytest .claude/hooks/tests -q` -> `1389 passed, 25 subtests passed in 38.01s`; `sh scripts/smoke-install.sh` -> `smoke-install.sh: PASS` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☑ pass | auto-run by hook, session 0f8ab46b-7503-4a0e-8290-d18cebc96f78, commit f58dd1498390dee78b3821ed2db48a370c1fe957, log .claude/verify-runs/T233-f58dd1498390.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Round 1: code-review P0-P3 0, but it missed the sensitive-list defect that auto verify found. Round 2 (`94e196a1..HEAD`): Supervisor read the `pre_tool_sensitive_path.py` diff: project list wins, an unreadable project list asks with no fallback, missing everywhere asks; no call that asked before now passes unless the plugin list clears it. P0 0, P1 0. Open: `lib/board/moments.py:51` carried to T234. Startup-reads line complete. |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor rerun after round 2: see Demonstration AFTER; `pytest tests` 1569 passed; `.claude/hooks/tests` 1389 passed; `smoke-install.sh: PASS`. |
| **Companion score (easy-verifier)** | ☐ N/A | Optional tool, not run for this task. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI in this task. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | No UI in this task. |
| **UI: Responsiveness at target viewports** | ☐ N/A | No UI in this task. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-02T07:37:17Z, `/home/hungnguyenhuu/workspace/pets/wt-t233`, unchanged code, no implementation commit):

```
$ claude plugin validate .
Validating components in: /home/hungnguyenhuu/workspace/pets/wt-t233

Validating skill: .../wt-t233/.claude/skills
⚠ Found 1 warning:
  ❯ directory: This directory is a symlink and nothing in it was read — component directories are read without following symlinks. ...

Validating agent: .../wt-t233/.claude/agents
⚠ Found 1 warning:
  ❯ directory: This directory is a symlink and nothing in it was read — ...

Plugin directory checks for /home/hungnguyenhuu/workspace/pets/wt-t233. ...

✘ Found 1 problem the plugin directory refuses a submission for:
  ❯ LICENSE: License missing (LICENSE_MISSING). This plugin has no LICENSE file and plugin.json has no `license`. The directory requires one of them.

$ ls LICENSE .claude-plugin hooks
ls: cannot access 'LICENSE': No such file or directory
ls: cannot access '.claude-plugin': No such file or directory
ls: cannot access 'hooks': No such file or directory
```

**AFTER** (2026-11-02, same worktree, files added):

```
$ ls LICENSE .claude-plugin hooks
LICENSE
.claude-plugin:
marketplace.json  plugin.json
hooks:
hooks.json

$ claude plugin validate . --profile directory
... ⚠ ICON_MISSING, README install-line advice (T236) ...
✔ Validation passed with warnings        (no LICENSE_MISSING)

$ (temp git project with PROJECT_KANBAN.md, T900 In Progress) claude -p "Run this exact bash command: <git push origin main>" --plugin-dir <worktree> --model haiku --max-budget-usd 0.5   [2026-11-02T07:38:16Z]
The push was blocked, and I haven't pushed anything.
A pre-push hook rejected the push because task T900 is still In Progress. ...
```

**AFTER, round 2** (auto verify found: a plugin kit project with no `.claude/sensitive-paths.txt` got `ask` on every Bash call; `pre_tool_sensitive_path.py` read the list from the project only).

Fix: `pattern_file_path(root)` in `.claude/hooks/pre_tool_sensitive_path.py` returns the project list when that path exists (even if unreadable, so the hook asks and never falls back), else the plugin's copy `<hooks folder>/../sensitive-paths.txt`, else the project path (so missing in both places still asks). In the `setup.sh` install both paths are the same file: no change.

Tests, `tests/test_hooks_from_plugin.py` (kit project holding only `PROJECT_KANBAN.md`, hooks in a fake plugin cache), RED before the fix:
```
FAILED tests/test_hooks_from_plugin.py::test_plugin_list_lets_a_harmless_bash_call_through
  ... "permissionDecision": "ask" ... "Sensitive-path list unreadable (.../kit-project/.claude/sensitive-paths.txt: FileNotFoundError)"
1 failed, 11 passed
```
Green after: `111 passed in 9.47s` (whole file). Mutations (each reverted, then `111 passed`):
```
M1 no fallback              -> FAILED test_plugin_list_lets_a_harmless_bash_call_through
M2 plugin copy beats project -> FAILED test_project_list_wins_over_the_plugin_list, test_unreadable_project_list_asks_and_does_not_fall_back
M3 unreadable project file falls back -> FAILED test_unreadable_project_list_asks_and_does_not_fall_back
M4 missing in both = empty list -> FAILED test_no_list_anywhere_still_asks
M5 plugin copy ignored (empty list) -> FAILED test_plugin_list_still_asks_for_a_sensitive_path, test_unreadable_plugin_list_still_asks
```
Also: `.claude/hooks/tests/test_pre_tool_sensitive_path.py::test_sc7_missing_pattern_file_asks` ran the repo's real hook against a project with no list, so it now found the repo's list. Its intent (missing everywhere asks) is kept: it runs a hook copy with no sibling list. The merge-gate test file is untouched.

Sweep result (kit-shipped file read from the project root, absent in a plugin-made kit project). Checked all of: `.claude/hooks/` post_agent_move_to_review, post_bash_memory_update, post_tool_trace, post_write_register_task, pre_agent_step_limit, pre_agent_validate_guide, pre_bash_block_unsafe_merge, pre_tool_sensitive_path, stop_auto_mode_check, stop_auto_verify, stop_review_reminder; `.claude/hooks/lib/` auto_closeout, auto_mode, guide_sections, project_root, shell_data, task_context, trace_chain, verify_record; `lib/board/` __init__, base, config, fake, linear, moments, outbox, render. Method: grep for open/read/path joins against `.claude`, templates, skills, agents, settings, MANIFEST, scripts, docs, json/txt/md names.
- FIXED: `pre_tool_sensitive_path.py` (`.claude/sensitive-paths.txt`). The only kit-shipped list, config or template read from the project.
- REPORTED, not fixed: `lib/board/moments.py:51` `pull_cache` runs `<project>/scripts/board_sync.py pull`. In a plugin project that script is absent, so an online-board project gets the warning `board unreachable — using cache (N unsynced)` and the gate uses the cached board. It blocks nothing extra. A fix needs `scripts/board_sync.py` to take the project root (it derives `ROOT` from its own location, so running the plugin's copy would write into the plugin cache), and `pull_cache` is called from the merge gate (`pre_bash_block_unsafe_merge.py:1180`). Left for a follow-up task.
- Project-owned (not kit-shipped), no change: `PROJECT_KANBAN.md`, `tasks/`, `memory/`, `PROJECT_SPEC.md` (`pre_agent_validate_guide.py:388`), `.claude/board.json` (`lib/board/config.py`, `moments.py`, `project_root.py`), `.claude/hooks/.state`, `.claude/verify-runs`.
- Mentions only (messages and docstrings, never read): `skills/craft-spawn-prompt/scripts/memory_slice.py`, `docs/claude-md/*`, `scripts/verify_trace.py`.

Live run 2 (2026-11-02T07:52:03Z, script `.../scratchpad/bin/live2.sh`, haiku, $0.50 cap each): project holds only `.git` and `PROJECT_KANBAN.md` (T900 In Progress), `origin` is a temp bare repo.
```
=== run 1: harmless call
The command printed `HARMLESS_OK`.
=== run 2: real push
The push did not go through. A pre-push hook blocked it:
  Pipeline gate failed — cannot push/merge:
    • Tasks still In Progress: T900
  Complete Stage 4 review and Stage 5 verify first.
=== remote refs after run 2:      (none: nothing was pushed)
```
Reruns: `claude plugin validate . --profile directory` -> `✔ Validation passed with warnings`; `python3 -m pytest tests/test_plugin_package.py -q` -> `7 passed in 0.78s`; `python3 -m pytest tests -q` -> `1569 passed in 142.69s`; `python3 -m pytest .claude/hooks/tests -q` -> `1389 passed, 25 subtests passed in 43.31s`; `sh scripts/smoke-install.sh` -> `smoke-install.sh: PASS`.

**DELTA**: A user can load the repo as the `easy-kit` plugin or add it as a marketplace, and its guard hooks fire from the plugin.

**WITNESS**: [reviewer fills from `memory/event-trace/T233.jsonl`]
