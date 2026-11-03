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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

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
