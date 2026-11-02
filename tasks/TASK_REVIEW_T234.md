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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_plugin_names.py` (19 tests; AC1 `test_no_repo_relative_script_call_left_in_skills_or_agents` + two layout tests, AC4 `test_register_hook_keeps_the_whole_agent_name`, `test_spawn_hook_decides_the_same_for_both_forms`, `test_trace_hook_records_either_agent_type`, D3/D5 tests): `python3 -m pytest tests/test_plugin_names.py -q` -> `19 passed in 1.09s` |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_plugin_names.py -q` -> `19 passed`; `sh scripts/smoke-install.sh` -> `smoke-install.sh: PASS` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests -q` -> `1588 passed in 149.09s`; `python3 -m pytest .claude/hooks/tests -q` -> `1389 passed, 25 subtests passed in 70.70s` |
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

D1 (before any skill edit, 2026-11-02T08:23Z): `${CLAUDE_SKILL_DIR}` expands in both modes. Plugin: `SKILLDIR=<plugin>/skills/dirprobe`, then `python3 ${CLAUDE_SKILL_DIR}/../../scripts/root_marker.py` printed `ROOT_SCRIPT_OK`. `setup.sh` install: `SKILLDIR=<project>/.claude/skills/dirprobe`, same script printed `ROOT_SCRIPT_OK`. Both ran in a project holding only `PROJECT_KANBAN.md` (plugin) or the installed kit (install).

**DELTA**: A plugin user can run `/easy-kit:wake` and spawn `easy-kit:qa-expert` in their own project, and every script a skill calls is found, with the same skill files unchanged in a `setup.sh` install.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
