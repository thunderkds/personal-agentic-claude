# TASK_REVIEW — T232: Hooks find the real project when they run from a plugin

> Sibling of `tasks/TASK_GUIDE_T232.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass / ☐ fail | `tests/test_hooks_from_plugin.py`, 105 tests, written first and seen RED on `main` (52 failed, 50 passed at that point). `python3 -m pytest tests -q`: 1556 passed in 116.93s (0:01:56) |
| Verification command run | ☑ pass / ☐ fail | `python3 -m pytest tests/test_hooks_from_plugin.py .claude/hooks/tests -q`: 1494 passed, 25 subtests passed in 30.68s. `python3 -m pytest .claude/hooks/tests -q`: 1389 passed, 25 subtests passed in 28.04s |
| Negative cases hold | ☑ pass / ☐ fail | M1 helper ignores `CLAUDE_PROJECT_DIR`: 30 failed, 105 passed on revert. M2 non-kit exit removed: 17 failed, 105 passed on revert. M3 `pre_agent_step_limit.py` state beside its code: 3 failed, 105 passed on revert. |
| verify | ☑ pass | auto-run by hook, session 2a20caf8-63b8-404c-89da-ec7bfe47e226, commit 321323c56e9aad0ed0efe5cb7f68f77c1fb10303, log .claude/verify-runs/T232-321323c56e9a.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review inline on `main...HEAD` plus direct callers. P0 0, P1 0, P2 1 (intermittent failure below), P3 1 (stale comment `pre_bash_block_unsafe_merge.py:319`). security-review run on the branch diff, not on `main` where the skill first scoped: no finding at or above confidence 8; sub-threshold plugin note on `lib/board/moments.py:51-53` carried to T234. Supervisor sign-off of the `AUTHORISED_TASKS` T232 entry: diff read, the gate only gets stricter, guide names the rule. lane: `C2, 23 files, 826 lines, EXCEEDS`: one line per hook plus tests, label kept. Startup-reads line complete. |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor runs: `pytest tests` 1 failed + 1555 passed once (test name not captured), then 1556 passed twice; `.claude/hooks/tests` with the new file 1494 passed. Implementer saw `test_t203_ac2_the_stop_hook_and_start_share_one_lock[start]` fail once; 3 reruns of `-k t203_ac2` passed. Intermittent, cause not found. |
| **Companion score (easy-verifier)** | ☐ N/A | Optional tool, not run for this task. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☑ N/A | no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☑ N/A | no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: `pre_bash_block_unsafe_merge.py` copied to a temp folder (a fake plugin cache), run on a `git push origin main` event with `CLAUDE_PROJECT_DIR` set to a temp kit project holding an In Progress task, on unchanged `main` code. Exit 0 with empty stdout: the gate passes the push silently.

```
timestamp: 2026-11-02T04:54:55.429352+00:00
git head : 53517c89
hook     : /tmp/t232-demo-4ewpaiiv/plugin-cache/easy-kit/hooks/pre_bash_block_unsafe_merge.py
project  : /tmp/t232-demo-4ewpaiiv/project (holds In Progress T900)
exit     : 0
stdout   : ''
stderr   : ''
```

**AFTER**: the same script, on the implementation commit. The gate blocks the push.

```
timestamp: 2026-11-02T05:11:17.345884+00:00
git head : dc19830c
hook     : /tmp/t232-demo-a33nq4nm/plugin-cache/easy-kit/hooks/pre_bash_block_unsafe_merge.py
project  : /tmp/t232-demo-a33nq4nm/project (holds In Progress T900)
exit     : 0
stdout   : '{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed \\u2014 cannot push/merge:\\n  \\u2022 Tasks still In Progress: T900\\nComplete Stage 4 review and Stage 5 verify first.\\n  Note: if a'
stderr   : ''
```

**DELTA**: A kit gate that runs from a plugin cache now judges the user's project, so a push with an open task is blocked, and in a repo with no kit files the same hook stays silent.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

---

## D4 audit

Each result is run inside a temp kit project with the hooks in a fake plugin cache, and pinned by a `test_d4_*` test in `tests/test_hooks_from_plugin.py`. "Broken import" means `raise ImportError` in the named `lib/` module.

| Hook | Bad stdin result | Broken import result | Change made or reason kept |
|------|------------------|----------------------|----------------------------|
| `pre_bash_block_unsafe_merge.py` | block (was exit 0, a silent pass). Also a non-object event, a non-object `tool_input`, a non-string `command` | block (`guide_sections`: as before; `project_root`: new) | **Changed**: `block_unreadable_input()`. This replaces a code comment that chose fail-open for payload shape; the hook docstring did not choose it |
| `pre_agent_validate_guide.py` | block (was exit 0, or exit 1 with a traceback on a non-object event; both pass). Also a non-object `tool_input`, a non-string `prompt` | `project_root`: block (new). `guide_sections`: the missing-guide block still works; the incomplete-guide block fails open | **Changed** for stdin and the helper. **Kept**: incomplete-guide fail-open, because the docstring says "A crash in that check fails open (allows)" |
| `pre_tool_sensitive_path.py` | ask (also a non-object `tool_input`) | ask (`shell_data`, `project_root`) | No change: it already asks |
| `pre_agent_step_limit.py` | exit 0, no decision | exit 0, no decision (`task_context`, `project_root`) | **Kept**: the docstring says "No session can be left permanently unable to act", and an unattributed call is "counted against nothing". This hook runs on every tool call, so a block here would stop the session from repairing `lib/` |
| `stop_auto_mode_check.py` | checks still run, one stderr line. A failing task gets its `Paused:` line and then a block; the next fire finds it paused and passes. No failing task: exit 0 with the stderr line (was exit 0, silent) | block on the first stop; a second fire, or unreadable stdin with it, passes with one stderr line; the headless verify run stays silent (was exit 1, a traceback, and the stop passed) | **Changed**. The pause comes first because `stop_hook_active` is unknown with bad stdin, and the docstring says "Never loops". If the pause cannot be written, the stop passes with stderr lines |

Gate changes under D4, complete list: the three rows marked **Changed**. Nothing else changes what a gate blocks.

Fail-open left in `stop_auto_mode_check.py`: `traced_test_run` passes when the gate's readers cannot load; its docstring says so. An unreadable file skips that task; the module docstring says so.

Limits to review:
- With `lib/project_root.py` itself broken, no hook can tell a kit project from another. The gates keep their fail-closed result, so outside a kit project a broken plugin blocks or asks. A test pins this for the merge gate. The advisory hooks exit 0.
- The broken-import block in `stop_auto_mode_check.py` fires in any session of a kit project, auto mode or not, because the hook cannot read which tasks are in auto mode.
- An exception inside a gate's `main()` on well-formed input still exits 1, and the harness lets the call run. D4 names bad stdin and broken imports only, so this is unchanged.

## Live run (Success Criteria)

Temp plugin at `--plugin-dir` holding copied hooks, `claude -p`, model haiku, budget $0.50, real `git push origin main` to a local bare remote. Cost $0.0076 in total. Run on 2026-11-02.

| # | Folder | Result |
|---|--------|--------|
| 1 | Kit project with In Progress T900 | Blocked: `PreToolUse:Bash hook error: [hook:pre_bash] Pipeline gate failed — cannot push/merge:` / `Tasks still In Progress: T900`. Remote refs: none |
| 2 | Folder with no kit files | No hook message. Push reached the remote (`refs/heads/main`). No file created in the folder, no `.state` in the plugin |

## Edge cases

- `CLAUDE_PROJECT_DIR` set to a missing path: `project_root()` falls back. From a plugin the hook is silent; in-repo it reads its own root. Tested.
- Linked worktree: state follows `CLAUDE_PROJECT_DIR`, as today, whatever the event's `cwd`. Tested.
- `stop_auto_verify.py` strips `CLAUDE_PROJECT_DIR` for the headless `claude` only. The detached `--run` keeps it and writes the result to the project. Tested with a stub `claude`.
- Board mode `online`: `.claude/board.json` with no `PROJECT_KANBAN.md` is a kit project. Tested. In that state the merge gate still exits 0 when the board file is missing after the pull, as it does today (D5).
