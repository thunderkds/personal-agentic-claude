# TASK_REVIEW — T242: Smaller plugin source: a `plugin/` folder of symlinks

> Sibling of `tasks/TASK_GUIDE_T242.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. Picked T242, not T243: T243 needs the listing icon, which the directory keeps from the first submission and never changes — RULE: `skills/resolve-question/SKILL.md` § Decide, rule 2 ("it can be undone" ranks first); the icon choice stays the user's
2. Extended track, C2 / Risk Medium: new component and a packaging change across many paths — RULE: `docs/claude-md/tracks.md` § Track rule (row 1: "Complexity C2 or above: 3+ files, a design choice, or a new component")
3. Layout: a `plugin/` folder of per-path symlinks, `"source": "./plugin"`, root `.claude-plugin/plugin.json` kept a real file — DEBATED: A (Advocate 1: A, per-path links, root plugin.json linked or removed; Advocate 2: A, per-path links, plugin.json moved into `plugin/`); both Advocates also left the 16 MB marketplace clone out of scope; the root file stays because it is the smaller change ⚠ decided for you — please review

Paused: trace mismatch — the 2 Advocate calls for decision 3 ran (descriptions `Advocate 1: how to shrink plugin install?` / `Advocate 2: …`, prompts starting `Using the repo, answer alone:`), but `memory/event-trace/T241.jsonl` holds them, because this session's task file still named T241 when they ran. The Supervisor did not move trace records and did not debate the question twice (`skills/resolve-question/SKILL.md` § Debate: "A question is never debated twice"). Please review decision 3 yourself.
Checks: tests `python3 -m pytest tests -q` — `1709 passed`; `python3 -m pytest .claude/hooks/tests -q` — `1389 passed, 25 subtests passed`; `sh scripts/smoke-install.sh` — PASS; reviews code-review — P0 0, P1 0, P2 0, P3 1; security-review — no findings; real run: git-marketplace install of the branch — `✔ Successfully installed plugin: easy-kit@easy-kit`, cache 1.3M (was 12M), 0 symlinks (auto-checked, not /verify)
Memory: `memory/decisions.md` — T242 entry (plugin/ symlink layout, 12M → 1.3M, D1 http-backend recipe)
Not done: merge (yours); push (yours); auto verify: ☑ pass (session f9f44b46-d62b-4f2a-bac1-489b5cf42481, commit 87a03426beee7a2f6c37792cb5b8fe87305b3a6a, log .claude/verify-runs/T242-87a03426beee.log)
Paused: auto-mode check failed — 1 `DEBATED` line(s) need ≥2 Advocate `Agent` calls (description `Advocate <n>:` and a prompt starting `Using the repo, answer alone:`); the trace has 0 [report cf56b025f4bf]

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
Closed: row moved to Done 2026-11-03 — auto verify pass (session f9f44b46-d62b-4f2a-bac1-489b5cf42481, commit 87a03426beee7a2f6c37792cb5b8fe87305b3a6a); Gates 5 and 6 checked

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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Written by this task (common-infrastructure, 2026-11-03): `tests/test_plugin_source.py` (32 cases). AC 3/D3: every `${CLAUDE_PLUGIN_ROOT}/...` path in `hooks/hooks.json`, `commands/`, `skills/` resolves under `plugin/` (13 params); every `plugin_init.TREES`/`FILES` path resolves (9 params); every hook `.py` has a link; every link is relative, resolves, and lands inside the repo; `plugin/` holds only links; `.claude/hooks/tests` is not reachable from `plugin/` (walk with `followlinks=True`); `plugin/.claude-plugin/plugin.json` links to the real root file; MANIFEST does not ship `plugin/`; `claude plugin validate plugin/` passes (skip with no `claude`). AC 4: `::test_marketplace_source_is_the_plugin_folder`. RED on `main` (`git archive main` at `927385ab` + the new test, 2026-11-03T12:05:13Z): `28 failed, 4 passed in 0.80s`. GREEN on the branch: `41 passed in 1.58s` (with `tests/test_plugin_package.py`). AC 1/AC 2 are proven by the real runs under `## D1` |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_plugin_package.py tests/test_plugin_source.py -q && sh scripts/smoke-install.sh` (2026-11-03T12:08Z) → `41 passed in 1.83s`, `smoke-install.sh: PASS` |
| Negative cases hold | ☑ pass | AC 2 from the 1.3 MB cache (hook-level, T236 driver): `pre_agent_validate_guide.py` → `{"decision": "block", "reason": "[hook:pre_agent] Cannot spawn agent \u2014 missing TASK_GUIDE for: T901. ..."}`; `pre_bash_block_unsafe_merge.py` → `{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed \u2014 cannot push/merge:\n  \u2022 Tasks still In Progress: T900 ..."}`. The guard test is red on `main` (28 failed) |
| verify | ☑ pass | auto-run by hook, session f9f44b46-d62b-4f2a-bac1-489b5cf42481, commit 87a03426beee7a2f6c37792cb5b8fe87305b3a6a, log .claude/verify-runs/T242-87a03426beee.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review over `c67b5159...HEAD` plus the readers of the linked paths (`hooks/hooks.json`, `scripts/plugin_init.py` TREES/FILES, `KIT_DIR`/`HOOKS_DIR` joins in `.claude/hooks`). Lane: `lane: C2, 25 files, 150 lines, EXCEEDS (files 25 > 14)` — 23 of the 25 are one-line symlinks. Findings: P0 0, P1 0, P2 0, P3 1 (lane count inflated by symlinks). security-review: all 23 links relative and inside the repo; the change narrows what ships; no findings ≥ 8 — pass. Startup reads complete. |
| Full smoke suite still green (no regression) | ☑ pass | AC 5, started 2026-11-03T12:05:38Z after the last code commit: `python3 -m pytest tests -q` → `1709 passed in 157.59s (0:02:37)`; `python3 -m pytest .claude/hooks/tests -q` → `1389 passed, 25 subtests passed in 38.26s`; `sh scripts/smoke-install.sh` → `smoke-install.sh: PASS` |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI: packaging (symlinks, one JSON value) and a test; no `site/` or README change |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI: no CSS, HTML or page text changed |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI: no page changed |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-03T12:03:46Z by common-infrastructure, before any implementation commit;
branch at `c67b5159` = `main`). Recipe: a bare clone of the worktree, served over smart HTTP on
`127.0.0.1:18742` (`git http-backend` in a stdlib `wsgiref` wrapper, `<scratch>/t242/drv/smart_http.py`),
because the CLI refuses `file://` (`✘ Invalid marketplace source format. Try: owner/repo, https://..., or ./path`)
and the dumb HTTP protocol (`fatal: dumb http transport does not support shallow capabilities`). Isolated
`CLAUDE_CONFIG_DIR=<D>/cfg`, `HOME=<D>/home`, `GIT_TERMINAL_PROMPT=0`. Driver `<scratch>/t242/drv/install.sh`.

```
2026-11-03T12:03:46Z
c67b5159 plan(T242): guide, review file, board In Progress (auto; layout DEBATED)
$ claude plugin marketplace add http://127.0.0.1:18742/repo.git
Adding marketplace…Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): http://127.0.0.1:18742/repo.git
Clone complete, validating marketplace…
Cleaning up old marketplace cache…
✔ Successfully added marketplace: easy-kit (declared in user settings)
exit 0
$ claude plugin install easy-kit@easy-kit
Installing plugin "easy-kit@easy-kit"...✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)
exit 0
cache: <cfg>/plugins/cache/easy-kit/easy-kit/2.2.0
$ du -sh <cache>
12M	<D>/cfg/plugins/cache/easy-kit/easy-kit/2.2.0
$ find <cache> -type l | wc -l
2
$ find <cache> -type l | head -5
<cache>/.claude/agents
<cache>/.claude/skills
$ du -sh <marketplace clone>
16M	<D>/cfg/plugins/marketplaces/easy-kit
$ test -e <cache>/.claude/hooks/tests
present
$ ls <cache>
.claude .claude-plugin .cursor .github .gitignore .in_use .vercelignore AGENTS.md BRAINSTORMING_LOG.md CLAUDE.md CLAUDE_LEGACY.md LICENSE MANIFEST PROJECT_KANBAN.md PROJECT_KANBAN_SITE.md PROJECT_SPEC.md PROJECT_SPEC_SITE.md README.md RUNBOOK.md agents commands docs experiments hooks lib memory packs reports scripts setup.sh site skills tasks templates tests update.sh vercel.json
```

The whole repo is copied (12 MB, matching T236's 12 MB), with `tasks/`, `tests/`, `site/` and `.claude/hooks/tests`.

**AFTER** (2026-11-03T12:04:32Z, same driver, branch at `d94110ad`, port 18743):

```
2026-11-03T12:04:32Z
d94110ad feat(T242): plugin/ folder of per-path symlinks; marketplace source ./plugin
$ claude plugin marketplace add http://127.0.0.1:18743/repo.git
Adding marketplace…Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): http://127.0.0.1:18743/repo.git
Clone complete, validating marketplace…
Cleaning up old marketplace cache…
✔ Successfully added marketplace: easy-kit (declared in user settings)
exit 0
$ claude plugin install easy-kit@easy-kit
Installing plugin "easy-kit@easy-kit"...✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)
exit 0
cache: <cfg>/plugins/cache/easy-kit/easy-kit/2.2.0
$ du -sh <cache>
1.3M	<D>/cfg/plugins/cache/easy-kit/easy-kit/2.2.0
$ find <cache> -type l | wc -l
0
$ find <cache> -type l | head -5
$ du -sh <marketplace clone>
16M	<D>/cfg/plugins/marketplaces/easy-kit
$ test -e <cache>/.claude/hooks/tests
absent
$ ls <cache>
.claude .claude-plugin .in_use AGENTS.md LICENSE agents commands docs hooks scripts skills templates 
```

**DELTA**: a git install of the plugin now copies 1.3 MB of real files (129, the exact set the plugin runs from) instead of the 12 MB repo, with no symlink and no `.claude/hooks/tests`; the 16 MB marketplace clone is unchanged (out of scope).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

---

## D1 — the plugin folder, installed from a copied git marketplace (common-infrastructure, 2026-11-03)

Result: **pass**. The AFTER block above is the D1 run. Extra checks on the same cache:

```
$ find <cache> -type f | wc -l
129
$ (every git-tracked file under the D2 paths, compared with cmp against <cache>/<same path>)
checked 129 committed files, 0 differ or missing
$ ls -A <cache>/.claude/hooks
lib post_agent_move_to_review.py post_bash_memory_update.py post_tool_trace.py post_write_register_task.py pre_agent_step_limit.py pre_agent_validate_guide.py pre_bash_block_unsafe_merge.py pre_tool_sensitive_path.py stop_auto_mode_check.py stop_auto_verify.py stop_review_reminder.py
$ du -sh <cache>/*
40K agents · 24K AGENTS.md · 4.0K commands · 100K docs · 4.0K hooks · 4.0K LICENSE · 196K scripts · 392K skills · 112K templates · 372K .claude · 4.0K .claude-plugin
$ cmp <cache>/.claude-plugin/plugin.json .claude-plugin/plugin.json && echo plugin.json identical
plugin.json identical
```

| Where | T236 (`main`) | T242 (branch) |
|---|---|---|
| `plugins/cache/easy-kit/easy-kit/2.2.0` | 12 MB, 2 symlinks (`.claude/agents`, `.claude/skills`), `.claude/hooks/tests` present | **1.3 MB**, 0 symlinks, `.claude/hooks/tests` absent |
| `plugins/marketplaces/easy-kit` (clone) | 16 MB | 16 MB (out of scope) |

`claude plugin validate plugin/` (Claude Code 2.1.317): `✔ Validation passed with warnings`, exit 0. The 4 warnings
say the validator does not read inside a linked `skills/`, `agents/`, `commands/`, `hooks/`. The root
`claude plugin validate .` test in `tests/test_plugin_package.py` still validates the real folders.

### Runtime path list (D2), confirmed from the code

Every `${CLAUDE_PLUGIN_ROOT}/...` path: the 11 hook scripts in `hooks/hooks.json`; `scripts/plugin_init.py` and
`skills/settings-setup/scripts/apply_profile.py` (`commands/init.md`, `skills/settings-setup/SKILL.md`). File-relative
reads: `pre_tool_sensitive_path.py:93` (`.claude/sensitive-paths.txt`); `pre_agent_validate_guide.py:319,512`
(`skills/craft-spawn-prompt/scripts/memory_slice.py`, `scripts/board_sync.py`); `lib/board/moments.py:29`
(`scripts/board_sync.py`); `lib/auto_closeout.py:47` (`pre_bash_block_unsafe_merge.py`); `apply_profile.py:34`
(`skills/settings-setup/profiles.json`); `plugin_init.TREES`/`FILES` (`templates`, `docs/claude-md`, `agents`,
`.claude/hooks/lib`, `AGENTS.md`, `.claude/hooks/stop_auto_verify.py`, `scripts/board_sync.py`,
`scripts/pull_moment.py`, `skills/craft-spawn-prompt/scripts/memory_slice.py`). All fall under the D2 list.
**No path was added.** No tracked symlink sits inside the linked trees (`find ... -type l` printed nothing).

### AC 2 — hook-level run from the 1.3 MB cache — pass

```
2026-11-03T12:05:32Z
$ git init -q
exit 0
$ python3 <cache>/scripts/plugin_init.py
easy-kit init in <scratch>/t242/proj-hooks
+ created CLAUDE.md
+ created PROJECT_KANBAN.md
+ created AGENTS.md
+ created .claude/hooks/stop_auto_verify.py
+ created scripts/board_sync.py
+ created scripts/pull_moment.py
+ created skills/craft-spawn-prompt/scripts/memory_slice.py
+ created templates/ADR_template.md
+ created templates/BRAINSTORMING_LOG_template.md
+ created templates/DDR_template.md
+ created templates/LEARNING-RECORD-FORMAT.md
+ created templates/MINIMAL_LOG_template.md
+ created templates/PACK_template.md
+ created templates/PRD_template.md
+ created templates/PROJECT_KANBAN_template.md
+ created templates/PROJECT_SPEC_template.md
+ created templates/RUNBOOK_template.md
+ created templates/SKILL_template.md
+ created templates/TASK_GUIDE_template.md
+ created templates/TASK_REVIEW_template.md
+ created templates/delivery_report_template.html
+ created templates/general-agent-template.md
+ created templates/report_template.html
+ created templates/subagent-sandbox.settings.json
+ created templates/thinking_report_template.html
+ created docs/claude-md/code-naming-conventions.md
+ created docs/claude-md/folder-structure.md
+ created docs/claude-md/memory-write-protocol.md
+ created docs/claude-md/pipeline-stages.md
+ created docs/claude-md/stage0-define.md
+ created docs/claude-md/token-economy.md
+ created docs/claude-md/tracks.md
+ created docs/claude-md/untrusted-content-boundary.md
+ created agents/backend.md
+ created agents/common-infrastructure.md
+ created agents/frontend.md
+ created agents/qa.md
+ created .claude/hooks/lib/auto_closeout.py
+ created .claude/hooks/lib/auto_mode.py
+ created .claude/hooks/lib/guide_sections.py
+ created .claude/hooks/lib/project_root.py
+ created .claude/hooks/lib/shell_data.py
+ created .claude/hooks/lib/task_context.py
+ created .claude/hooks/lib/trace_chain.py
+ created .claude/hooks/lib/verify_record.py
+ created .claude/hooks/lib/board/__init__.py
+ created .claude/hooks/lib/board/base.py
+ created .claude/hooks/lib/board/config.py
+ created .claude/hooks/lib/board/fake.py
+ created .claude/hooks/lib/board/linear.py
+ created .claude/hooks/lib/board/moments.py
+ created .claude/hooks/lib/board/outbox.py
+ created .claude/hooks/lib/board/render.py
+ created tasks/
+ created memory/MEMORY.md
+ created memory/decisions.md
+ created memory/glossary.md
+ created memory/learnings.md
+ created memory/learning-records/.gitkeep
59 path(s) created.
note: templates/, docs/claude-md/, agents/ and the copied scripts go stale after a plugin update. Run /easy-kit:init again to add new files; it never replaces a file that is there.
note: the gates are plugin hooks. Each teammate must install the easy-kit plugin (`claude plugin install easy-kit@easy-kit`); a teammate without it has no gates.
exit 0
--- board In Progress section after init:
['## Board', '### Todo', '### In Progress', '- [~] **T900** — open task | backend-developer | C1 | Risk: Low | P1', '### Ready for Review', '### Done', '## Blocked', '## Stage Tracker']
--- pre_agent_validate_guide.py <- {"subagent_type": "easy-kit:backend-developer", "prompt": "Task ID: T901\nGuide: tasks/TASK_GUIDE_T901.md"}
$ python3 <cache>/.claude/hooks/pre_agent_validate_guide.py
{"decision": "block", "reason": "[hook:pre_agent] Cannot spawn agent \u2014 missing TASK_GUIDE for: T901. Run Stage 2 planning first to generate the guide(s) in tasks/."}
exit 0
--- pre_bash_block_unsafe_merge.py <- {"command": "git push origin main"}
$ python3 <cache>/.claude/hooks/pre_bash_block_unsafe_merge.py
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed \u2014 cannot push/merge:\n  \u2022 Tasks still In Progress: T900\nComplete Stage 4 review and Stage 5 verify first.\n  Note: if a task above is missing its trace record rather than its evidence row, attribute your Bash calls. A sub-agent whose spawn prompt carries `Task ID: Txxx` or a `tasks/TASK_GUIDE_Txxx.md` path is attributed from its own transcript and writes nothing. Otherwise write this session's state file first: `mkdir -p <main-checkout>/.claude/hooks/.state/active_task.d && printf '%s\\n%s\\n' \"Txxx\" \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" > <main-checkout>/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID` \u2014 using the literal absolute path of the main checkout (not $CLAUDE_PROJECT_DIR, which is empty inside a Bash tool call, and not a relative path, which resolves into your worktree). Valid for CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S seconds (default 6h). CLAUDE_ACTIVE_TASK=Txxx <command> does NOT work from inside a session: a hook is a sibling process of the tool call and never inherits its subshell (T047). The env var only takes effect when set before the session starts."}
exit 0
```

### Notes

- **Install recipe.** The CLI refuses `file://` (`✘ Invalid marketplace source format. Try: owner/repo, https://..., or ./path`).
  A dumb-HTTP server fails (`fatal: dumb http transport does not support shallow capabilities`). So the bare clone
  was served by `git http-backend` behind a stdlib `wsgiref` wrapper on `127.0.0.1`
  (`<scratch>/t242/drv/smart_http.py`, `<scratch>/t242/drv/install.sh`). Nothing touched GitHub or the real config.
- **`--plugin-dir ./plugin`** (links kept, not copied): `project_root.py` computes `_FILE_ROOT` with `abspath`, so
  imported through the link it is `<repo>/plugin`, equal to `$CLAUDE_PLUGIN_ROOT`. Probe from a scratch project with
  `CLAUDE_PLUGIN_ROOT=<worktree>/plugin`: `_FILE_ROOT <worktree>/plugin`, `project_root() <scratch>/t242/proj-hooks`,
  `script_project_root() <scratch>/t242/proj-hooks`. `plugin_init.py` uses `realpath`, so it copies from the repo
  root: the same bytes.
- **Edge cases.** `setup.sh`/MANIFEST: `plugin/` is not in MANIFEST (guard test). Tree-walking tests
  (`test_plugin_names.py`, site sweeps): the full suite passes, 1709, so no double count fails a test.
- **Windows `core.symlinks=false`**: a clone there checks each link out as a small text file holding the target
  path, so `plugin/` would hold text files, not folders. This affects the Windows git checkout used as the
  marketplace source. Not tested; noted only, as the guide asks.
- **`main` moved** during the run (`c67b5159` → `927385ab`); the branch is not rebased. The red run used `main` at `927385ab`.
