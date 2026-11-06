# TASK_REVIEW — T266: Native Windows support, step 5 - hooks fire on the PowerShell tool and the installer can write the Windows hook form

> Sibling of `tasks/TASK_GUIDE_T266.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. The three shell-inspecting hooks are matched on `Bash|PowerShell` and accept the PowerShell tool name, because on Windows without Git Bash there is no Bash tool and a Bash-only matcher never fires — FACT: `.claude/hooks/pre_bash_block_unsafe_merge.py:1322` "if event.get("tool_name") != "Bash":" (the gate ignores every other tool); the docs (code.claude.com/docs/en/hooks.md) say "Match `Bash|PowerShell` in hooks that inspect shell commands"
2. The Windows hook form is written per OS by the installer, as exec form (`py -3`, no shell), instead of one `sh -c` command for every OS — DEBATED: per-OS exec form (Advocate 1: inline `command -v py || command -v python3 || command -v python` chain; Advocate 2: probe loop with a loud failure; Advocate 3: `sh -c` exec chain; all three named per-OS installer settings as the fallback if hooks run under PowerShell, and the docs fact check showed they do when Git Bash is not installed) ⚠ decided for you — please review
3. The plugin's `hooks.json` command strings are not converted for Windows (matchers are widened) — RULE: `AGENTS.md § Karpathy Engineering Principles` (Simplicity First: vital slice and cut list)
Checks: pending (T266 in progress)
Memory: pending (written before the run ends)
Not done: merge (yours); auto verify: not started


## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_windows_hooks.py` (32 tests, new in this task): AC1 `MatcherTest` (settings.json, hooks/hooks.json, plugin/hooks/hooks.json; exact-name regex); AC2/3 `SensitivePathPowerShellTest`, `MemoryHookPowerShellTest` (subprocess, PowerShell vs Bash verdicts, Read/Glob silent, no-command); AC4/10 `HookPathsTest`, `WiresInRepoHookTest`; AC5/6 `ConverterTest`; AC7 `RoundTripTest` + `test_idempotent`; AC8 `CliTest`; SC5 `MutationControlTest`. RED first at `3facd258`: `18 failed, 14 passed in 0.62s`. GREEN at `f726d641`: `32 passed in 0.60s`. Pins repointed: `.claude/hooks/tests/test_pre_tool_sensitive_path.py:277`, `tests/test_subagent_sandbox_profile.py` (settings diff allow-list, matcher lines only) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_windows_hooks.py -q && bash tests/test_settings_merge.sh && python3 -m pytest .claude/hooks/tests tests -q` at 2026-11-06T12:48:40Z: `32 passed in 0.60s` / `--- 49 passed, 0 failed ---` / `3452 passed, 25 subtests passed in 236.96s (0:03:56)` |
| Negative cases hold | ☑ pass | Mutation (SC5), `diff -u` of `lib/windows_hooks.py`: `-    return converted` / `+    return hook` (identity conversion) -> `5 failed, 27 passed in 0.61s` (`test_repo_settings_to_py`, `test_repo_settings_to_python`, `test_plugin_root_converts`, `test_cli_writes_exec_form`, plus the in-file control's anchor check); restored -> `32 passed`. The same mutation also runs inside the suite (`MutationControlTest`). AC10: exec-form `args` path `${CLAUDE_PROJECT_DIR}/scripts/mine.py` is not a kit group and `merge_event_groups` keeps it (`test_negative_exec_form_outside_hooks_is_user_entry`); unknown launcher `python3` -> exit 2, no file written |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | BEFORE at `dcf83f54`: shell merge `49 passed, 0 failed`, pytest `3420 passed, 25 subtests passed`. AFTER at `f726d641`: `49 passed, 0 failed`, `3452 passed, 25 subtests passed` (3420 + 32 new, 0 failed). An intermediate run (`fe7b5e34`) had 3 failures, all fixed in `f726d641`: T233 D3 sync test and T243 byte-copy test (root `hooks/hooks.json` is the source of the plugin copy and was not yet widened) and the T147 settings-diff pin |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component: hooks, JSON settings and a Python converter |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on branch `feat/t266-windows-hooks` at `dcf83f54`, before any implementation commit.
The script prints the matcher lists (`python3 -c` over both JSON files), then feeds `{"tool_name":"<T>","tool_input":{"command":"cat .env"}}` to `.claude/hooks/pre_tool_sensitive_path.py` on a temp fixture project (shipped `.claude/sensitive-paths.txt`, `PROJECT_KANBAN.md`):

```
captured 2026-11-06T12:37:36Z  HEAD dcf83f54
.claude/settings.json ['Write', 'Agent', 'Bash', '.*', 'Agent', 'Bash', 'Edit|Write|Bash', '.*', None, None, None]
plugin/hooks/hooks.json ['Write', 'Agent', 'Bash', '.*', 'Agent', 'Bash', 'Edit|Write|Bash', '.*', None, None, None]
tool_name=PowerShell exit=0 output=<empty>
tool_name=Bash exit=0 output={"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "[hook:sensitive-path] This Bash call touches a sensitive path: .env (pattern `.env`). Listed in .claude/sensitive-paths.txt and no active task predicts it."}}
```

Suites at `dcf83f54` (2026-11-06T12:37:40Z):

```
$ bash tests/test_settings_merge.sh
--- 49 passed, 0 failed ---
$ python3 -m pytest .claude/hooks/tests tests -q
3420 passed, 25 subtests passed in 201.47s (0:03:21)
```

The PowerShell `cat .env` call gets no decision (silent allow), and no matcher names `PowerShell`, so on Windows without Git Bash none of the three shell-inspecting hooks fires at all.

**AFTER**: same script at `3facd258` working tree with the implementation applied (committed as `fe7b5e34`):

```
captured 2026-11-06T12:44:04Z  HEAD 3facd258
.claude/settings.json ['Write', 'Agent', 'Bash|PowerShell', '.*', 'Agent', 'Bash|PowerShell', 'Edit|Write|Bash|PowerShell', '.*', None, None, None]
plugin/hooks/hooks.json ['Write', 'Agent', 'Bash|PowerShell', '.*', 'Agent', 'Bash|PowerShell', 'Edit|Write|Bash|PowerShell', '.*', None, None, None]
tool_name=PowerShell exit=0 output={"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "[hook:sensitive-path] This PowerShell call touches a sensitive path: .env (pattern `.env`). Listed in .claude/sensitive-paths.txt and no active task predicts it."}}
tool_name=Bash exit=0 output={"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "[hook:sensitive-path] This Bash call touches a sensitive path: .env (pattern `.env`). Listed in .claude/sensitive-paths.txt and no active task predicts it."}}
$ python3 lib/windows_hooks.py .claude/settings.json win.json --launcher py   -> exit=0
{"description": "Block git push/merge if pipeline gates are not satisfied", "matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": "py", "args": ["-3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/pre_bash_block_unsafe_merge.py"]}]}
$ python3 lib/windows_hooks.py .claude/settings.json x.json --launcher python3
windows_hooks.py: error: argument --launcher: invalid choice: 'python3' (choose from py, python)
exit=2   (x.json not created)
```

Suites at `f726d641`: `--- 49 passed, 0 failed ---`; `3452 passed, 25 subtests passed`.

**DELTA**: On Windows without Git Bash, a PowerShell command that reads `.env` now asks the user first instead of passing silently, and the Windows installer (T268) can write every kit hook as `py -3` exec form with one call to `to_windows_settings`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
