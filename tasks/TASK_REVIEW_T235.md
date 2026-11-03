# TASK_REVIEW — T235: /easy-kit:init sets up a project, and plugin hooks stand down beside in-repo hooks

> Sibling of `tasks/TASK_GUIDE_T235.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_plugin_init.py` (39 tests: AC1-AC5, D6a, D6b, D7, D7a, D7c, D8, edge cases). Supervisor rerun at `e1a77b22`: `39 passed in 2.45s`. |
| Verification command run | ☑ pass | Supervisor at `e1a77b22`: `python3 -m pytest tests/test_plugin_init.py -q && sh scripts/smoke-install.sh` -> `39 passed in 2.45s`, `smoke-install.sh: PASS`. Implementer live headless runs (haiku, about $0.02 total): `/easy-kit:init` created 59 paths; a push with an In Progress T900 was blocked; both modes gave one block, from the in-repo hook. |
| Negative cases hold | ☑ pass | Red first at `97dee307`: `2 failed, 1 passed, 33 errors`. Against the old `project_root.py`: `10 failed, 26 passed` (AC4 stand-down and both D6a tests). Gate kept when the wired file is missing, the settings are not JSON, or the hooks are init's unwired copies; a worker call with arguments never stands down; a broken `project_root.py` still blocks (D6b). |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review inline on `main...HEAD` (5 files) plus callers of `exit_outside_kit_project` (all 11 hooks, unchanged): P0 0, P1 0, P2 2 left (stand-down reads `.claude/settings.json` only, not `settings.local.json`: a project wiring hooks there gets two blocks, not zero; `MEMORY` scaffold text in `scripts/plugin_init.py` is copied from `setup.sh` with no test that they match), P3 1 (run from a repo subfolder, init writes into that subfolder; consistent with `CLAUDE_PROJECT_DIR`, no action). lane_check: `EXCEEDS (lines 799 > 500); unpredicted: scripts/plugin_init.py` — 468 of the lines are tests. Startup reads: all three Permanent-Rule reads present. security-review scoped by the Supervisor: `git` called with an argument list, no shell; JSON parsed with `json.load` and type-checked; copies never overwrite (`os.path.lexists`); the stand-down lets a project turn off a plugin gate only by wiring its own copy of that gate, the same trust as an in-repo install. No finding. |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor at `e1a77b22`: `pytest tests` 1657 passed; `.claude/hooks/tests` 1389 passed, 25 subtests passed (the 5 budget failures the implementer saw came from the Supervisor's `memory/MEMORY.md` line, fixed on main in `f786631d` and cherry-picked); `smoke-install.sh: PASS`. |
| **Companion score (easy-verifier)** | ☐ N/A | Optional tool, not run for this task. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI: a command, a script and a hook library. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | No UI: a command, a script and a hook library. |
| **UI: Responsiveness at target viewports** | ☐ N/A | No UI: a command, a script and a hook library. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on `feat/t235-plugin-init` at `e9a02e11`, before the first implementation commit.
`both_modes.sh` builds a temp project whose `.claude/settings.json` wires the in-repo kit hooks
(a copy of the kit's), plus a plugin-shaped copy of the kit (`.claude-plugin/plugin.json` + `.claude/hooks`),
and feeds one `git push origin main` payload to each copy of `pre_bash_block_unsafe_merge.py`.

```
2026-11-03T02:38:08Z
$ ls commands/init.md
ls: cannot access 'commands/init.md': No such file or directory
$ python3 -m pytest tests/test_plugin_init.py -q

no tests ran in 0.00s
$ sh both_modes.sh <worktree>   # in-repo hooks wired + plugin copy, one push payload
[proj hook] exit=0 stdout={"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Task
[plugin hook] exit=0 stdout={"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Task
```

No `/easy-kit:init` command exists, and with both modes present the same push gets two blocks.

**AFTER** (Supervisor, at `e1a77b22`; `both_modes.sh` was a scratch script, so the both-modes check is its committed test):

```
2026-11-03T02:59:39Z
$ ls commands/init.md
commands/init.md
$ python3 -m pytest tests/test_plugin_init.py -q -k "ac4_both_modes or ac1_init_creates or ac2_a_second"
3 passed, 36 deselected in 0.32s
```

**DELTA**: A plugin user runs `/easy-kit:init` once to get the project files, add-only, and a project with both the plugin and in-repo hooks now gets one block per push, not two.

**WITNESS**: common-infrastructure agent ran it 2026-11-03 (trace `memory/event-trace/T235.jsonl`); the Supervisor reran the tests and suites at `e1a77b22`; independent witness pending: the auto verify run.
