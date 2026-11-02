# TASK_REVIEW — T234: Skills and agents work under the easy-kit prefix

> Sibling of `tasks/TASK_GUIDE_T234.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_plugin_names.py` (24 tests after round 3, each skill command run in both layouts), `tests/test_auto_verify.py::test_t234_start_from_a_plugin_cache_runs_in_the_project_not_the_cache`. Supervisor rerun at `c08fc9fc`: `pytest tests` 1594 passed. |
| Verification command run | ☑ pass | Supervisor rerun at `c08fc9fc`: `tests/test_plugin_names.py` within 1594 passed; `smoke-install.sh: PASS`. |
| Negative cases hold | ☑ pass | Round 2: child env mutation RED then green. Round 3: `abspath` back in `pull_moment.py` gave `ModuleNotFoundError: No module named 'board'` in the install layout, then 24 passed (implementer). |
| verify | ☑ fail | auto-run by hook, session b9428bc1-c15b-4944-8523-42ce1ff67616, commit 8ddd5925393f67f9176896e86fd6b70adb3d8c2b, log .claude/verify-runs/T234-8ddd5925393f.log — fail |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review inline on `main...HEAD`: P0 0, P1 1 fixed in round 2 (`--run` used the plugin folder as root), P2 0 open, P3 0. security-review on the branch diff: no finding at or above confidence 8. Merge gate file unchanged. `test_agents_md_primary.py` and `T070_BASELINE_REF` edits follow the T226/T228 pattern: merge without squashing, because the baseline names `fb3ff0f`. `scripts/test-claude-md-refs.sh` AC5/AC6 fail the same way on `main`. Open items moved to T235 D7. lane: `C2, 29 files, 571 lines, EXCEEDS`, label kept: most are one-line path changes. Startup-reads line complete. Round 3 (`8aa7cd1f..c08fc9fc`): auto verify found the `setup.sh` regression that this review missed; realpath and quoting fix read by the Supervisor, P0 0, P1 0.  |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor rerun at `c08fc9fc` on an idle machine: `pytest tests` 1594 passed; `.claude/hooks/tests` 1389 passed, 25 subtests passed; `smoke-install.sh: PASS`. Implementer saw `test_ac4_blocked_row_never_says_pass[pass-and-fail]` fail once under load (T237). |
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

**BEFORE** (captured 2026-11-02T08:22:02Z, unchanged code at commit `17691294`, before any T234 commit; Claude Code 2.1.316, model haiku, cost $0.011, 8 turns):

Command (`$SP` = a scratchpad folder; the temp project holds only `PROJECT_KANBAN.md` after `git init`, no kit files):

```
cd <temp project> && claude -p "/easy-kit:wake" --plugin-dir /home/hungnguyenhuu/workspace/pets/wt-t234 \
  --model haiku --max-budget-usd 0.5 --allowedTools Bash Read Skill Agent --output-format stream-json --verbose
```

Every script call the skill names fails from the temp project (tool results, verbatim):

```
python3: can't open file '<temp project>/scripts/pull_moment.py': [Errno 2] No such file or directory
python3: can't open file '<temp project>/skills/wake/scripts/memory_sections.py': [Errno 2] No such file or directory
python3: can't open file '<temp project>/skills/wake/scripts/dirty_worktrees.py': [Errno 2] No such file or directory
```

The model then said "The working directory is a scratchpad, not the project. The skill's scripts live under `/home/hungnguyenhuu/workspace/pets/wt-t234`, so I'll run the steps from there" and `cd`-ed into the plugin folder. So the briefing printed only because the model improvised and read the kit's own repo; it ran against the plugin folder, not the user's project.

**AFTER** (captured 2026-11-02T08:42:29Z on branch `feat/t234-plugin-names` at `fb3ff0f`; same command, same kind of temp project, `--plugin-dir` the worktree, haiku, cost $0.0067, 7 turns). Every script the skill names ran from the plugin folder and exited 0, with no "can't open file":

```
python3 /home/hungnguyenhuu/workspace/pets/wt-t234/scripts/pull_moment.py wake            -> exit=0
python3 /home/hungnguyenhuu/workspace/pets/wt-t234/skills/wake/scripts/memory_sections.py -> No MEMORY.md found.
python3 /home/hungnguyenhuu/workspace/pets/wt-t234/skills/wake/scripts/dirty_worktrees.py -> exit=0
```

Spawn and a craft-spawn-prompt script, plugin run (2026-11-02T08:43:04Z, $0.028):

```
Skill easy-kit:craft-spawn-prompt          -> Launching skill
python3 .../skills/craft-spawn-prompt/scripts/memory_slice.py tasks/TASK_GUIDE_T900.md
                                           -> <!-- memory-slice:T900 --> ... <!-- /memory-slice -->
Agent subagent_type=easy-kit:qa-expert     -> Async agent launched successfully ... reply "QA_OK"
```

Same two skills after a `setup.sh` install (`SUPERVISOR_REPO=file://<worktree>`, 2026-11-02T08:43:38Z and 08:44:07Z): `/wake` scripts exit 0 (`.claude/skills/wake/scripts/...`); `craft-spawn-prompt` ran `.claude/skills/craft-spawn-prompt/scripts/memory_slice.py` and returned a slice block; `Agent subagent_type=qa-expert` replied `QA_OK`.

Round 2 (D5a): `stop_auto_verify.py --start` now passes the project it resolved to the detached `--run` as `CLAUDE_PROJECT_DIR`. Test `tests/test_auto_verify.py::test_t234_start_from_a_plugin_cache_runs_in_the_project_not_the_cache` (fake plugin cache, variable unset, cwd in a temp kit project, fake `claude`). RED before the fix: `AssertionError: (None, [.../anchors/cache-noremote, ...cache-noremote/verify-runs/T951-<sha>.json])` (the run record was keyed to the cache). Green after: `1 passed`. Mutation (drop `"CLAUDE_PROJECT_DIR": ROOT` from the child env): `1 failed` with the same assertion; restored: `1 passed`. Paths in the two `pre_agent_validate_guide.py` messages and in `pull_moment.py`'s unsynced message are now `shlex.quote`d (tests `test_hook_messages_quote_a_plugin_path_with_a_space`, `test_pull_moment_unsynced_message_quotes_a_plugin_path_with_a_space`; RED before: `2 failed`, green after: `21 passed` in `tests/test_plugin_names.py`).

Round 3 (auto verify fail: in a `setup.sh` install `${CLAUDE_SKILL_DIR}` is `<project>/.claude/skills/<name>`, a symlinked path, and `abspath(__file__)` dropped `../..` without following it).
- **Scripts checked** for `abspath(__file__)` used to find code, every script a `${CLAUDE_SKILL_DIR}` command reaches. Changed to `realpath`: `scripts/pull_moment.py`, `scripts/board_sync.py`, `scripts/lane_check.py`, `scripts/token_meter.py`, `skills/settings-setup/scripts/apply_profile.py`, and `.claude/hooks/lib/board/moments.py` (consistency). Already safe: `skills/delivery-report/render.py` (`realpath`), `skills/craft-spawn-prompt/scripts/memory_slice.py` (`realpath`), `skills/wake/scripts/dirty_worktrees.py` (`realpath`), `skills/companion-setup/scripts/check_companions.py` (`Path.resolve`). No location lookup: `skills/wake/scripts/memory_sections.py`, `skills/dotfiles/scripts/dotfiles.py`. Not reachable from a skill command, left alone: `scripts/token_audit.py`, `ci_verify_done_tasks.py`, `memory_usage_report.py`, `gen_sandbox_profile.py`, `verify_trace.py`, `measure_agent_guide_tokens.py`.
- **Quoting:** every `${CLAUDE_SKILL_DIR}` command in the skills is now `python3 "${CLAUDE_SKILL_DIR}/..."`; the rule in `skills/write-better-skill/SKILL.md` says so. `wake` 8183, `code-review` 8163, `resolve-question` 8184 bytes (limit 8192).
- **Test:** `tests/test_plugin_names.py::test_every_skill_dir_command_runs[install|plugin]` builds each layout in folders named `my project` / `my plugin`, expands each command to the `.claude/skills/<name>` (install) or `<plugin>/skills/<name>` path, runs it with harmless arguments, and fails on a crash, a non-zero exit or `UNKNOWN` from `lane_check.py`. Exempt from the skill's own arguments (a harmless argument replaces them): `token_meter.py`, `apply_profile.py`, `dotfiles.py` run `--help` (the real run reads transcripts or writes settings or home folders). RED before the fix: `install: skills/code-review/SKILL.md: lane_check.py ... UNKNOWN ([Errno 2] No such file or directory: '.../my project/.claude/scripts/../skills/craft-spawn-prompt/scripts/mem...` Green after: `24 passed`. Mutation (`abspath` back in `scripts/pull_moment.py`): `install: skills/craft-spawn-prompt/SKILL.md: pull_moment.py ['wake'] ... ModuleNotFoundError: No module named 'board'`; restored: `24 passed`.
- **Real `setup.sh` install** (`SUPERVISOR_REPO=file://<worktree>`, folder `my proj`, 2026-11-02T09:16:10Z), `wake`'s three commands as the skill writes them, with `CLAUDE_SKILL_DIR=<proj>/.claude/skills/wake`:

```
python3 "${CLAUDE_SKILL_DIR}/../../scripts/pull_moment.py" wake   -> (no output)  pull_moment rc=0
python3 "${CLAUDE_SKILL_DIR}/scripts/memory_sections.py"          -> <!-- Format: ... -->  memory_sections rc=0
python3 "${CLAUDE_SKILL_DIR}/scripts/dirty_worktrees.py"          -> (no output)  dirty_worktrees rc=0
```

D1 (before any skill edit, 2026-11-02T08:23Z): `${CLAUDE_SKILL_DIR}` expands in both modes. Plugin: `SKILLDIR=<plugin>/skills/dirprobe`, then `python3 ${CLAUDE_SKILL_DIR}/../../scripts/root_marker.py` printed `ROOT_SCRIPT_OK`. `setup.sh` install: `SKILLDIR=<project>/.claude/skills/dirprobe`, same script printed `ROOT_SCRIPT_OK`. Both ran in a project holding only `PROJECT_KANBAN.md` (plugin) or the installed kit (install).

**DELTA**: A plugin user can run `/easy-kit:wake` and spawn `easy-kit:qa-expert` in their own project, and every script a skill calls is found, with the same skill files unchanged in a `setup.sh` install.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
