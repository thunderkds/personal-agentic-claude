# TASK_REVIEW — T236: Real plugin install proven, then published on the README and site

> Sibling of `tasks/TASK_GUIDE_T236.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Written by this task (frontend-developer, 2026-11-03). AC 3: `tests/test_site_content.py::test_install_shows_the_plugin_and_setup_sh_paths_each_in_its_own_copy_box`, `::test_install_puts_the_plugin_path_first_and_the_version_floor_beside_the_one_step_form`, `tests/test_plugin_package.py::test_readme_quick_start_shows_the_plugin_and_setup_sh_paths`. AC 4: `tests/test_site_content.py::test_install_states_the_plugin_limits` (4 cases). D2: `tests/test_site_story.py::test_hero_mentions_the_plugin_and_links_to_the_docs_install_section`. RED before the docs edit: `8 failed, 199 passed in 17.18s` (all 8 were the new tests). GREEN after: `249 passed in 2.16s`. AC 1 and AC 2 are proven by the runs pasted under `## D1`, not by unit tests |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_site_content.py tests/test_site_story.py tests/test_plugin_package.py tests/test_site_visual_first.py tests/test_readme_slim.py tests/test_companion_setup.py -q` → `249 passed in 2.16s` (2026-11-03, after the last docs edit) |
| Negative cases hold | ☑ pass | AC 2: an `Agent` spawn with no guide and a push with T900 In Progress were both refused by hooks in a real session; the bare remote has no refs after. Anonymous: SSH with no key fails (`SSH clone failed, retrying with HTTPS`), HTTPS with no credential helper succeeds. Caps hold: `index.html` 300/300 words, `#install` 142/150 first-load words, README 75/75 lines |
| verify | ☑ pass | auto-run by hook, session 05ee1e6c-9a80-4d2a-ad03-a4c2037a9fad, commit 5c8beddb7fd58f78ba08cac211456af28789217d, log .claude/verify-runs/T236-5c8beddb7fd5.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review over `main...HEAD` (6 files): `lane: C2, 6 files, 137 lines, FITS; unpredicted: tests/test_plugin_package.py`. Findings: P0 0, P1 0, P2 0, P3 1 (the `docs.html` "Plugin details" list omits `templates/`, `docs/claude-md/`, `agents/` that init also adds; incomplete, not false). security-review on the same diff: static HTML/README text and tests only; no findings ≥ 8 — pass. Startup reads complete. |
| Full smoke suite still green (no regression) | ☑ pass | AC 6, started 2026-11-03T10:55:36Z after the last edit: `python3 -m pytest tests -q` → `1673 passed in 204.50s (0:03:24)`; `node --test tests/settings_tool/*.mjs` → `ℹ tests 59 ℹ pass 59 ℹ fail 0`; `node --test tests/site_scrollspy/*.mjs` → `ℹ tests 8 ℹ pass 8 ℹ fail 0`. An earlier full run, before the final edits, failed 3 cap tests (README 106 > 75 lines ×2, `#install` 228 > 150 words); all three were fixed |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional; docs-only change |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | frontend-developer viewed before/after (headless Chrome, `file://`, 2026-11-03T10:53–10:58Z): `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/00571797-1b9e-4f83-80d5-93fdec2d9ab5/scratchpad/t236/shots/png/before_docs_install_1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/00571797-1b9e-4f83-80d5-93fdec2d9ab5/scratchpad/t236/shots/png/after_docs_install_1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/00571797-1b9e-4f83-80d5-93fdec2d9ab5/scratchpad/t236/shots/png/after_docs_install_375.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/00571797-1b9e-4f83-80d5-93fdec2d9ab5/scratchpad/t236/shots/png/before_index_hero_1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/00571797-1b9e-4f83-80d5-93fdec2d9ab5/scratchpad/t236/shots/png/after_index_hero_1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/00571797-1b9e-4f83-80d5-93fdec2d9ab5/scratchpad/t236/shots/png/after_index_hero_375.png`. Verdict: `#install` shows the plugin path first (h3, 3 Copy boxes, version floor, init line, 3 limits, a closed `Plugin details` fold), then the `setup.sh` part unchanged; the hero gains one line `Or install the plugin`; header, sidebar, strip and journey unchanged. Copy check (headless click on each `#install` button, clipboard stubbed): `["Copied","Copied","Copied","Copied"]`; the copied text equals the 4 commands, with no `$ ` |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | No CSS changed (`site/theme.css` not in the diff); no `style=` attribute and no hex added (grep of `git diff site/` → none). Existing classes only: `codebox`, `prompt`, `btn btn-primary`, `lead`, plain `details`. Existing tests pass in the full run: `tests/test_site_visual_first.py::test_no_hex_colour_outside_the_token_block_and_no_third_party_asset`, `tests/test_site_story.py::test_no_hex_colour_and_no_third_party_asset_on_either_page` |
| **UI: Responsiveness at target viewports** | ☑ pass | `chrome-headless-shell` (Playwright 1248; full Chrome clamps to 485 px, so it was not used for 375), `--window-size=W,900`, injected script, 2026-11-03T10:58:48Z: `index 1440 scrollWidth=1425 clientWidth=1425`, `docs 1440 1425=1425 codeboxes=5 overflowing=[]`, `index 768 753=753`, `docs 768 753=753 codeboxes=5 overflowing=[]`, `index 375 360=360`, `docs 375 360=360 codeboxes=5 overflowing=[]`. Long commands wrap inside their box at 375 (`after_docs_install_375.png`) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-03T10:39Z by frontend-developer, before any implementation commit; docs
unchanged at `6c5e18e9`). The plugin path is absent from every install surface: each offers only `setup.sh`.

`README.md:25-35` (Quick Start, verbatim):

```
## Quick Start

**Prerequisite:** the target directory must already be a git repository (`git init` first if it
isn't — your project's own git history is the undo mechanism, since nothing is symlinked from a
shared location).

Run from inside the target project root:

```sh
curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh
```
```

`site/docs.html:466-473` (`#install`, verbatim):

```
<section id="install">
<h2>Install</h2>
<p class="lead">
  Prerequisites: an existing <strong>git repo</strong>, and <code>git</code>, <code>curl</code>,
  and a POSIX <code>sh</code> on your PATH.
</p>
<div class="codebox"><code><span class="prompt">$ </span>curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh</code><button type="button" class="btn btn-primary" aria-label="Copy install command">Copy</button></div>
```

`site/index.html:63-67` (`#hero`, verbatim):

```
<section id="hero" class="hero">
  <p class="eyebrow">&gt; multi-agent supervisor framework</p>
  <h1>Easy Kit</h1>
  <p class="lead">You ask for a change. Easy Kit plans it, builds it, checks it, and leaves the merge to you.</p>
  <div class="codebox"><code><span class="prompt">$ </span>curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh</code>...
```

**AFTER** (frontend-developer, 2026-11-03; full text in the diff `main...feat/t236-plugin-publish`):

`site/docs.html` `#install` now opens with the plugin path:

```
<h3>Claude Code plugin</h3>
<p class="lead">Run in a terminal:</p>
<div class="codebox">...$ claude plugin marketplace add thunderkds/easy-kit ...Copy</div>
<div class="codebox">...$ claude plugin install easy-kit@easy-kit ...Copy</div>
<p class="lead">Or, on Claude Code 2.1.292 or later, in one step:</p>
<div class="codebox">...$ claude plugin install easy-kit --marketplace thunderkds/easy-kit ...Copy</div>
<p class="lead">Then, in Claude Code, run <code>/easy-kit:init</code> once in your git repo.</p>
<ul class="lead"> Claude Code only. / Each teammate installs the plugin. / A plugin cannot set permissions. </ul>
<details><summary>Plugin details</summary> init adds ... / easy-kit:<name> prefix </details>
<h3><code>setup.sh</code>: copy the kit into your repo</h3>
(the old setup.sh content follows, unchanged)
```

`README.md` Quick Start: one line naming both paths, a `**Claude Code plugin.**` paragraph with the same commands
and limits, then `**`setup.sh`.**` with the old text. `site/index.html` `#hero`: one new line under the
`setup.sh` box, `Or <a href="docs.html#install">install the plugin</a>`.

**DELTA**: A reader of the README or the site can now install Easy Kit as a Claude Code plugin from GitHub with
commands that were run anonymously, and sees its limits before choosing it.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

---

## D1 — install run (frontend-developer, 2026-11-03)

Isolation for every run below: `HOME` and `CLAUDE_CONFIG_DIR` = fresh scratch dirs; `GIT_CONFIG_NOSYSTEM=1`,
`GIT_CONFIG_GLOBAL=/dev/null` (no credential helper); `GIT_TERMINAL_PROMPT=0`; `SSH_AUTH_SOCK` unset and
`GIT_SSH_COMMAND` with `IdentityFile=/dev/null`, `BatchMode=yes` (no SSH key reachable). The user's real config
(`~/.claude-personal`) was never touched.

Note: a first attempt with only `GIT_TERMINAL_PROMPT=0` and no credential helper still succeeded **over SSH**,
using the user's SSH agent key (`SSH_AUTH_SOCK` was set). That run is NOT anonymous and is discarded. The
anonymous runs below force the SSH attempt to fail, so Claude Code falls back to HTTPS.

### AC 1 — two-step form (anonymous) — pass

```
2026-11-03T10:36:45Z
credential.helper: []  GIT_TERMINAL_PROMPT=0  SSH_AUTH_SOCK=[]  HOME=<scratch>/t236/home
$ claude plugin marketplace add thunderkds/easy-kit
Adding marketplace…Cloning via SSH: git@github.com:thunderkds/easy-kit.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): git@github.com:thunderkds/easy-kit.git
SSH clone failed, retrying with HTTPS: https://github.com/thunderkds/easy-kit.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): https://github.com/thunderkds/easy-kit.git
Clone complete, validating marketplace…
Cleaning up old marketplace cache…
✔ Successfully added marketplace: easy-kit (declared in user settings)
exit 0
$ claude plugin install easy-kit@easy-kit
Installing plugin "easy-kit@easy-kit"...✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)
exit 0
$ claude plugin list
Installed plugins:

  ❯ easy-kit@easy-kit
    Version: 2.2.0
    Scope: user
    Status: ✔ enabled

exit 0
```

### AC 1 — one-step form, Claude Code 2.1.317 (anonymous, fresh config) — pass

```
2026-11-03T10:37:07Z
$ claude plugin install easy-kit --marketplace thunderkds/easy-kit
Adding marketplace…
Cloning via SSH: git@github.com:thunderkds/easy-kit.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): git@github.com:thunderkds/easy-kit.git
SSH clone failed, retrying with HTTPS: https://github.com/thunderkds/easy-kit.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): https://github.com/thunderkds/easy-kit.git
Clone complete, validating marketplace…
✔ Successfully added marketplace: easy-kit (declared in user settings)
Installing plugin "easy-kit@easy-kit"...✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)
exit 0
```

The `/plugin install easy-kit --marketplace thunderkds/easy-kit` in-session form was NOT run (needs an
interactive session).

### AC 2 — pass: a real session with `--plugin-dir`, by the user's choice (option (b), 2026-11-03)

The first try, in the isolated config, could not log in:

```
$ timeout 60 claude -p "Reply with the single word OK." --model haiku --max-budget-usd 0.05
Not logged in · Please run /login
```

**Decision, by the user's choice:** both sessions below use the user's **real Claude login** (the real
`CLAUDE_CONFIG_DIR`). They load the plugin with `--plugin-dir <isolated cache>`, which points at the copy that
the anonymous AC 1 install fetched from GitHub. No `claude plugin install` and no `marketplace add` ran against
the real config. Further flags: `--setting-sources project,local`, so the user's own settings and hooks are not
loaded and only the plugin's hooks act. `--strict-mcp-config` loads no user MCP servers.
`--no-session-persistence` keeps the session from saving a transcript. Model `haiku`. Budget $0.40 + $0.60
(at most $1). Actual cost $0.0054 + $0.0049. Scratch repo: a fresh `git init` with one commit. Its `origin` is
a throwaway local bare repo, `<scratch>/remote-ac2.git`, never GitHub. Driver:
`<scratch>/t236/drv/ac2.py`. The raw stream-json logs are `<scratch>/t236/s1-init.jsonl` and `s2-gates.jsonl`.

Session 1 at 2026-11-03T10:42:42Z: `claude -p "/easy-kit:init" --model haiku --max-budget-usd 0.40 --plugin-dir <cache> --setting-sources project,local --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --allowedTools Bash(python3:*)`

```
init: plugins [{'name': 'easy-kit', 'path': '<scratch>/t236/cfg/plugins/cache/easy-kit/easy-kit/2.2.0', 'source': 'easy-kit@inline', 'version': '2.2.0'}, ...builtins] | easy-kit slash cmds ['easy-kit:init', 'init'] | agents ['easy-kit:backend-developer', 'easy-kit:common-infrastructure', 'easy-kit:frontend-developer', 'easy-kit:qa-expert']
TOOL_USE {"command": "python3 \"<cache>/scripts/plugin_init.py\"; echo \"EXIT=$?\"", ...}
RESULT This Bash command contains multiple operations. The following part requires approval: echo "EXIT=$?"
TOOL_USE {"command": "python3 \"<cache>/scripts/plugin_init.py\"", ...}
RESULT easy-kit init in <scratch>/t236/proj-ac2
+ created CLAUDE.md
+ created PROJECT_KANBAN.md
+ created AGENTS.md
... 
TEXT Step 1 created 59 paths and kept none. Next, the settings dry runs.
(legacy and high-security --dry-run: "dry run: nothing written" for each)
TEXT ... Write these changes to `.claude/settings.json`? Both profiles only add rules.
RESULT-FINAL cost 0.00538603 success
```

(The model's first Bash call added `echo`. `--allowedTools` did not cover it, so the session's permission check
refused it. The model then ran the script alone. Nothing was written to settings, because no one approved.)

Between the sessions the driver added `- [~] **T900** — open task | backend-developer | C1 | Risk: Low | P1` under
`### In Progress` and committed. `tasks/` holds no `TASK_GUIDE_T901.md`.

Session 2 at 2026-11-03T10:43:36Z: the prompt asks for one `Agent` call (`easy-kit:backend-developer`, `Task ID: T901`) and
one `git push origin main`. `--allowedTools Agent Bash(git push:*)`, so only a hook could refuse either call.

```
TOOL_USE Agent {"description": "T901", "subagent_type": "easy-kit:backend-developer", "prompt": "Task ID: T901\nGuide: tasks/TASK_GUIDE_T901.md\nReply DONE."}
TOOL_USE Bash {"command": "git push origin main", "description": "Push main branch to origin"}
RESULT is_error=True PreToolUse:Agent hook error: [hook:pre_agent] Cannot spawn agent — missing TASK_GUIDE for: T901. Run Stage 2 planning first to generate the guide(s) in tasks/.
RESULT is_error=True PreToolUse:Bash hook error: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
Complete Stage 4 review and Stage 5 verify first.
  ...
RESULT-FINAL cost 0.004869460000000001 success
remote refs after: ''
```

Both gates blocked, from the plugin installed from GitHub, in a real Claude Code 2.1.317 session. The bare remote
has no refs, so the push did not happen.

Earlier hook-level check: the same cache, the hooks fed JSON directly, with no session. It is kept as a supporting run:

```
2026-11-03T10:38:10Z
$ python3 <cache>/scripts/plugin_init.py
easy-kit init in <scratch>/t236/proj-hooks
+ created CLAUDE.md
+ created PROJECT_KANBAN.md
+ created AGENTS.md
... (59 lines: templates/, docs/claude-md/, agents/, .claude/hooks/lib/, tasks/, memory/)
59 path(s) created.
note: the gates are plugin hooks. Each teammate must install the easy-kit plugin (`claude plugin install easy-kit@easy-kit`); a teammate without it has no gates.
exit 0
--- pre_agent_validate_guide.py <- {"subagent_type": "easy-kit:backend-developer", "prompt": "Task ID: T901\nGuide: tasks/TASK_GUIDE_T901.md"}
{"decision": "block", "reason": "[hook:pre_agent] Cannot spawn agent \u2014 missing TASK_GUIDE for: T901. Run Stage 2 planning first to generate the guide(s) in tasks/."}
exit 0
--- pre_bash_block_unsafe_merge.py <- {"command": "git push origin main"}
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed \u2014 cannot push/merge:\n  \u2022 Tasks still In Progress: T900\n..."}
exit 0
```

### D5 — what a git-sourced install copies

Measured with `du -sh` after the anonymous two-step install (`main` at `1d9669df`):

| Where | Size | Notes |
|---|---|---|
| `plugins/cache/easy-kit/easy-kit/2.2.0` (the installed plugin) | 12 MB | `tasks/` 4.7 MB, `tests/` 1.6 MB, `experiments/` 1.2 MB, `.claude/` 1.2 MB, `docs/` 784 KB, `memory/` 620 KB, `skills/` 392 KB, `site/` 324 KB, `scripts/` 196 KB, `packs/` 128 KB, `templates/` 112 KB, `lib/` 80 KB, `PROJECT_KANBAN.md` 72 KB, `agents/` 40 KB |
| `plugins/marketplaces/easy-kit` (the marketplace clone) | 16 MB | includes `.git/` 3.8 MB |
| Total on disk | about 28 MB | |

No `.claude/hooks/.state/` in the cache: a git source copies only committed files (T233's local-path install
copied it). The parts the plugin runs from (`agents/`, `skills/`, `.claude/`, `hooks/`, `commands/`,
`scripts/`, `lib/`, `templates/`, `docs/claude-md/`) are about 2 to 2.5 MB of the 12 MB. A smaller plugin
source (a `plugins/easy-kit/` subfolder, or a `git-subdir` source) could cut the cache by roughly 80%, but it
needs a build or a mirror step, and the 16 MB marketplace clone would stay unless the marketplace moves too.
Recommendation: worth a follow-up task, low priority (P2): size only, no correctness issue.

---

## D2 — what was cut, and why

- `index.html` was at 296 of 300 words. The hero gained `Or install the plugin` (4 words, now exactly 300).
  Nothing was cut from the page. The plugin commands, the version floor and the limits stay on
  `docs.html#install` only.
- `docs.html#install` has a cap of 150 words on first load (`tests/test_site_visual_first.py`). The first
  draft showed 228 words. Cuts: an intro paragraph naming both paths (the two `<h3>` headings name them).
  Two notes moved into a `<details>Plugin details</details>` fold: what `/easy-kit:init` adds,
  and the `easy-kit:` name prefix. Now 142 words. The four D3 limits stay visible.
- `README.md` has a cap of 75 lines (`tests/test_readme_slim.py`, `tests/test_companion_setup.py`) and was at 75.
  To make room for the plugin path, two parts of the old text were reshaped, with no fact dropped. The
  `## Prerequisites` section (`git`, `curl`, POSIX `sh`) merged into the `setup.sh` prerequisite line. The
  4-item Codex skill list became one inline line. Now 75 lines.
- Removed from the drafts: "Pick one path: with both installs active, each gate runs twice." T233's verify
  saw this, but T235 then made each plugin hook stand down beside its wired in-repo twin
  (`tests/test_plugin_init.py::test_ac4_every_plugin_hook_stands_down_silently_beside_its_in_repo_twin`).
  The sentence is false today, so it is not published.
- Cut list (guide): no third install path, no version badge. The `/plugin install` in-session form is not
  documented, because it was not run. The quick-reference row at the top of `docs.html` still shows only `setup.sh`.

## D4 — claims audit (every new sentence and what proves it)

| # | Where | Sentence | Proof |
|---|---|---|---|
| 1 | docs, README | `claude plugin marketplace add thunderkds/easy-kit` then `claude plugin install easy-kit@easy-kit` ("Run in a terminal") | AC 1, two-step run, anonymous, 2026-11-03T10:36:45Z: `✔ Successfully added marketplace`, `✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)` |
| 2 | docs, README | "Or, on Claude Code 2.1.292 or later, in one step: `claude plugin install easy-kit --marketplace thunderkds/easy-kit`" | The command: AC 1, one-step run on 2.1.317, anonymous, 2026-11-03T10:37:07Z, exit 0. The floor `2.1.292`: the official docs (code.claude.com/docs/en/plugins, cited in the Supervisor note of 2026-11-03). **Not run on 2.1.292 itself**: only 2.1.317 is installed |
| 3 | docs, README | "Then, in Claude Code, run `/easy-kit:init` once in your git repo." | AC 2 session 1: `/easy-kit:init` loaded from the GitHub copy (`easy-kit:init` in the session's slash commands) and created 59 paths. "once": `commands/init.md` description ("Set up this project … once"). "git repo": `commands/init.md` Step 1, exit 2 outside a git repository |
| 4 | docs, README | "Claude Code only. For Codex, use `setup.sh`." | The package is a Claude Code plugin (`.claude-plugin/plugin.json`, `claude plugin validate .`). Only Claude Code was run (AC 1, AC 2). `setup.sh` offers Codex: `tests/test_site_content.py::test_install_section_names_every_cli_and_options_table_has_no_flags` reads `VALID_HARNESSES` |
| 5 | docs, README | "Each teammate installs the plugin. Without it, a teammate has no gates." | `plugin_init.py` output in AC 2: `note: the gates are plugin hooks. Each teammate must install the easy-kit plugin … a teammate without it has no gates.` init wires no hook: `tests/test_plugin_init.py::test_ac4_the_hook_copies_init_makes_are_not_wired_so_the_plugin_gate_runs`. T233 verify step 7: with no plugin, the push went through |
| 6 | docs, README | "A plugin cannot set permissions. `/easy-kit:init` shows the kit's settings rules, and writes them only after you approve." | AC 2 session 1: both `--dry-run`s printed `dry run: nothing written`, then the session asked `Write these changes to .claude/settings.json?` and wrote nothing. `commands/init.md` Step 2 ("The plugin cannot set permissions"). `tests/test_plugin_init.py::test_ac3_the_command_shows_a_dry_run_and_writes_only_after_approval` |
| 7 | docs (fold) | "`/easy-kit:init` adds `CLAUDE.md`, `AGENTS.md`, the task board, `tasks/` and `memory/`." | AC 2 session 1 output: `+ created CLAUDE.md`, `+ created PROJECT_KANBAN.md`, `+ created AGENTS.md`, `+ created tasks/`, `+ created memory/MEMORY.md` … |
| 8 | docs (fold) | "It never changes a file that is already there." | `tests/test_plugin_init.py::test_ac2_a_second_run_changes_no_byte`, `::test_ac2_a_pre_existing_claude_md_is_unchanged_and_named`, `::test_ac2_a_file_inside_a_copied_tree_is_kept_and_named` |
| 9 | docs (fold) | "Skills and agents are named `easy-kit:<name>`, for example `/easy-kit:wake` and `easy-kit:backend-developer`." | AC 2 session init event: 36 `easy-kit:` slash commands, including `easy-kit:wake`; agents `easy-kit:backend-developer`, `easy-kit:common-infrastructure`, `easy-kit:frontend-developer`, `easy-kit:qa-expert` |
| 10 | README | "There are two ways to install: the Claude Code plugin, or `setup.sh`, which copies the kit into your repo and can also set up Codex." | Plugin: AC 1. `setup.sh` copies: the README text kept right below ("copies every `MANIFEST`-listed path … into your project as real files"). Codex: row 4 |
| 11 | README | "More: [site](https://personal-agentic-claude.vercel.app/docs.html#install)." | `vercel.json` `outputDirectory: site`, so `site/docs.html` is served as `/docs.html`. `#install` exists. **The live URL was not fetched** (no network check in this task) |
| 12 | docs | `<h3><code>setup.sh</code>: copy the kit into your repo</h3>` | Same as row 10 |
| 13 | index | "Or install the plugin" (link to `docs.html#install`) | AC 1. Target exists: `tests/test_site_story.py::test_hero_mentions_the_plugin_and_links_to_the_docs_install_section` |
| — | README | `**`setup.sh`.** Prerequisites: `git`, `curl`, POSIX `sh`, and a git repository …` and the inline Codex skill list | Not new: merged from the old `## Prerequisites` list and the old prerequisite sentence and skill list, word for word except the list format |

No sentence is unproven. Two carry a stated limit: row 2 (the floor comes from the docs, not from a 2.1.292 run)
and row 11 (the live URL was not fetched).
