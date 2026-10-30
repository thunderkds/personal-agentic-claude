# BRAINSTORMING_LOG_distribution.md
**Generated**: 2026-10-30
**Task / Context**: No task yet. Investigation of how Easy Kit is distributed: simple for "just run it" users, multi-provider, still transparent for devs who want to understand it.
**Skill**: `Skill({ skill: "brainstorming" })` — tier **Deep** (architectural choice; every user and every CLI is affected)

---

## The Problem Space

User, 2026-10-30, in order:
1. "we are using mcps as the kit family, but we do not install from initial … add for the options and run through the settings up?"
2. "when we add it, will make the settings up more complex, although my direction to make it simple as much"
3. "split this kit as small pieces also … support to run as plugin, just call and do not care more about the way to setting up"
4. "we can use another provider that diff with claude, so … the shell scripts will be better … fits with the devs who want to know the system, vice versa it hard to adapt from devs that just want the kit to run by simple … think about another ways also"

**Two audiences, one kit:**
- *Just run it*: one command, no reading, auto-update, no wrong steps.
- *Understand it*: plain files in the repo, readable and editable, works on any CLI.

**Measured today (main @ 5fd0bd00):**
- Installer: `setup.sh` 891 lines + `lib/harness-fetch.sh` 508 + `lib/harness-update.sh` 949 = 2,361 lines of POSIX sh.
- `VALID_HARNESSES="claude codex"` (setup.sh:95). Cursor gets one hand-written file, `.cursor/rules/agent-base.mdc`.
- Payload: 33 skills, 4 agents, 11 Python hooks (`.claude/hooks/*.py`), templates, `docs/claude-md`, packs.
- 11 distinct repo-relative script calls in skills/agents/doctrine (`python3 skills/wake/scripts/memory_sections.py`, `python3 scripts/pull_moment.py`, …).
- MCP family: easy-memory (Python + hooks, own `install --dry-run`), easy-verifier (Docker, `sudo chown`, `docker run`), easy-ui (Docker compose), easy-personal (Python 3.11 + uv + Node build), easy-context (uv or Docker). None is installed by the kit.

**Earlier decisions that bind this one** (not re-opened here):
- Canon at plain root (`skills/`, `agents/`); `.claude/skills|agents` are relative symlinks; other CLIs get copies (`BRAINSTORMING_LOG_harness-kit-portability.md`, Option B).
- Each project gets real copies, no central clone (`BRAINSTORMING_LOG_direct-install.md`, Option A).
- Per-CLI doctrine adapters are hand-written, not generated (`BRAINSTORMING_LOG_multi-provider.md`, Path A).

**Facts from vendor docs (research 2026-10-30; URLs in the session, "unconfirmed" kept as such):**

| CLI | Reads AGENTS.md | Native package | Package ships context | Skills | Agents | Blocking hooks | MCP | Package can set permissions |
|---|---|---|---|---|---|---|---|---|
| Claude Code | Y (only when no CLAUDE.md; else `@AGENTS.md`) | plugin + marketplace | N | Y | Y | Y | Y | N (only `agent`, `subagentStatusLine`) |
| Codex CLI | Y | plugin + marketplace (`/plugins`) | N | Y | unconfirmed in plugin (`.codex/agents/*.toml`) | Y, user must trust via `/hooks` | Y | unconfirmed |
| Cursor | Y | plugin (UI install; CLI unconfirmed) | Y (`rules/*.mdc`) | Y | Y | Y (CLI partial) | Y | unconfirmed |
| Gemini CLI | config needed | extension (`gemini extensions install`) | Y (`GEMINI.md`) | Y | Y (preview) | Y | Y | partial (deny only) |
| opencode | Y | JS/npm module | N | dirs only | dirs only | partial (throw) | via config | via config |

- **No package format on any CLI writes project files on install.** Board, `tasks/`, `memory/`, `PROJECT_SPEC.md` always need a command the user runs.
- **Portable today:** `AGENTS.md` (all five); Agent Skills `SKILL.md` format (all five); `.agents/skills/` is the shared skills dir for Codex, Cursor, Gemini, opencode (Claude Code does not document it; Cursor and opencode also read `.claude/skills`).
- **Not portable:** hooks (5 formats), sub-agent format, permissions. Agent Plugins spec 1.0 covers skills + MCP only.
- **Comparable kits:** GitHub Spec Kit (`uv tool install specify-cli` → `specify init --integration <agent>`); BMAD-METHOD (`npx bmad-method install`, v7 preview moves to `npx skills add …` + Claude and Codex plugin marketplaces); rulesync / ruler (one source → many CLIs' formats; hooks partial or none).

**Drift found in our own doctrine (separate bug, not this decision):** `AGENTS.md` says Codex reads skills "only from `.codex/skills/` … with an 8 KB skill-body cap". Current Codex docs list `.agents/skills`, `~/.agents/skills`, `/etc/codex/skills`, and the 8,000 figure is the budget for the skills *list*, not a per-body cap. Needs a live check against the installed Codex before any fix.

**Non-negotiables:**
- Hard-Stop Gates 1–6 stay enforced on Claude Code by hooks; a distribution change must not weaken a gate.
- Codex/Cursor stay supported; a Claude-only path may be added, never be the only path.
- Project state files stay plain files in the repo (they are the audit trail).

---

## Questions for the User

Asked one at a time; answers recorded here as they arrive.

1. For the first version, must the "just run it" path work on every CLI, or is Claude Code + Codex enough (the two the installer supports today)?
2. Which audience is primary when the two conflict: *just run it* or *understand it*?
3. Is a second install path acceptable if it doubles the install test surface, or must there stay exactly one?
4. Is a Node or Python runtime acceptable as an install requirement (`npx` / `uvx`), or must install need only `git` + `sh`?

User, 2026-10-30: "so what is your final solution" — the Supervisor answered Q1–Q4 with defaults, open to change by the user:
1. Claude Code first; Codex in the same package only if the spike shows one folder serves both; every other CLI uses `setup.sh`.
2. *Just run it* is primary; *understand it* keeps `setup.sh` unchanged.
3. Two paths accepted: `setup.sh` already exists, so the only new path is the plugin.
4. No new runtime: a plugin needs none; `setup.sh` keeps `git` + `sh`.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Polish the shell installer | Keep one path; fix drift, add CLIs, fewer questions | Low | ~200 lines changed | Low | |
| B | Native package per CLI | Claude plugin, Codex plugin, Gemini extension, Cursor plugin, built from the canon; setup.sh retired | High | ~1,500 new + 2,361 removed | High | |
| C | Thin repo + packaged tools (two layers) | Repo holds doctrine + state (every CLI); tools (skills, agents, hooks, MCPs) come as a native package where one exists, as copies where not; setup.sh stays as the "everything in repo" mode | Medium | ~600 new | Medium | ✅ Yes (pending Q1–Q4) |
| D | One CLI initializer (`uvx easy-kit init`) | Rewrite setup.sh as a Python CLI like Spec Kit; still copies plain files | Medium | ~1,200 Python replacing 2,361 sh | Medium | |
| E | Adopt a converter (rulesync) | Author the canon once in rulesync format; let it emit each CLI's files | Medium | ~300 config + migration | Medium–High | |
| F | Template repo | "Use this template" on GitHub for new projects | Low | ~0 | Low | only as an add-on |

### Option A — Polish the shell installer
**Approach**: Keep `setup.sh` as the only path. Add `gemini`/`opencode` to `VALID_HARNESSES` and project skills into `.agents/skills`. Cut the questions to one (which CLIs; detect the rest). Print one closing line pointing at the MCPs page.
**Pros**: Zero new concepts. Fully transparent. Works on every CLI, needs only `git` + `sh`. Keeps every earlier decision.
**Cons**: Does not give "just call it" simplicity: users still run a script and own the update. No auto-update. Every new CLI is more shell.
**Why it might fail**: The user's own words (point 4) say this path suits devs who want to know the system and is hard for those who just want it to run. A "polished" installer is still an installer.

### Option B — Native package per CLI
**Approach**: A build script turns the canon into one package per CLI (`.claude-plugin/`, root `plugin.json` for Codex/Cursor, `gemini-extension.json`). A `/easy-kit:init` skill writes project files. `setup.sh` is retired.
**Pros**: Simplest for the user on each CLI: one install command, vendor-managed updates. Splits naturally into small plugins (core, reports, each pack, each MCP).
**Cons**: Four package formats to build and test, each with different gaps (Codex hooks need manual trust; Cursor install is UI-only; opencode has no file package). Skill names get a prefix (`wake` → `easy-kit:wake`) in every reference and test. Doctrine still cannot ride in the package on Claude Code or Codex, so a repo file is needed anyway. Loses the transparent mode.
**Why it might fail**: The "every CLI" promise is carried by four vendor formats that change on their own schedule; a format change breaks one CLI silently. Retiring setup.sh drops the "understand it" audience completely. Hooks that fire in every project where the plugin is on can block work in non-kit repos.

### Option C — Thin repo + packaged tools (two layers)
**Approach**:
- **Layer 1, in the repo, every CLI:** `AGENTS.md` (+ `CLAUDE.md` with `@AGENTS.md`), project state files, `.claude/settings.json` permissions. Written once by an `init` step.
- **Layer 2, the tools:** skills, agents, hooks, MCPs. On a CLI with a package system: a native package (Claude Code plugin first, Codex plugin second). On any other CLI, or when the user wants to read and edit the kit: today's `setup.sh` copies the same tools into the repo ("in-repo mode").
- Split Layer 2 into small packages: `easy-kit` (core skills + agents + gate hooks), `easy-kit-reports`, one per pack, one per MCP (easy-memory first).
**Pros**: Each audience gets its own shape without a second doctrine. Packs and MCPs become opt-in packages, which settles question 1 of this session without making setup longer. Start with one CLI and grow. Keeps setup.sh, so no audience is lost.
**Cons**: Two ways to get the same tools means two install paths to test and document. Version skew is possible: `AGENTS.md` in the repo names a skill the installed package lacks. Prefix renaming still applies on the package path.
**Why it might fail**: "Two layers" is a new concept to explain; if the explanation is longer than today's install, the user's goal (simple) is missed. If in-repo mode and package mode drift, bugs show in one mode only. Untested: whether an agent spawn accepts `easy-kit:backend-developer`, and the kit's hooks check agent names.

### Option D — One CLI initializer (`uvx easy-kit init`)
**Approach**: Rewrite the 2,361 lines of shell as a Python CLI (hooks are already Python). `easy-kit init`, `easy-kit update`, `easy-kit add <pack|mcp>`. Same plain-file output as today.
**Pros**: Proven shape (Spec Kit). One path, every CLI, transparent output. Python is easier to test than POSIX sh; `add` makes "small pieces" one command each.
**Cons**: New runtime requirement (`uv`). A rewrite of a battle-tested installer. Still no vendor auto-update.
**Why it might fail**: A rewrite risks re-opening every edge case the shell installer already handles (backups, locks, legacy symlink refusal, T113 exclusions). It changes the language, not the user's experience: still "run an installer".

### Option E — Adopt a converter (rulesync)
**Approach**: Move the canon to rulesync's source format; its CLI generates each CLI's skills, agents, hooks, MCP and permissions.
**Pros**: Someone else maintains the per-CLI formats. Covers many CLIs.
**Cons**: Hooks support is partial per CLI (unconfirmed which); our gates are the kit's core. Adds a third-party dependency to the install. Conflicts with the hand-written-adapter decision.
**Why it might fail**: The gates are what make the kit the kit; a converter that drops or weakens a hook on one CLI makes that CLI silently unsafe.

### Option F — Template repo
**Approach**: Mark the repo (or a slim copy) as a GitHub template.
**Pros**: No install at all for a new project.
**Cons**: New projects only; no update path; no existing-repo install.
**Why it might fail**: Most users add the kit to an existing repo. Useful only as an extra button, never as the path.

---

## 50% Rule Check

For Option C: skip the build script and the multi-format work at first. Ship **one plugin folder** whose `skills/` and `agents/` are the existing canon, with only a `.claude-plugin/plugin.json` and `hooks/hooks.json` added. Codex reads the legacy `.claude-plugin/marketplace.json` and a root `plugin.json`, and Cursor loads Agent Plugins, so a second manifest file may give Codex/Cursor the same folder with no generator (unconfirmed; the spike tests it). setup.sh stays unchanged as in-repo mode. That is roughly 3 manifest files plus the 11 script-path rewrites, not ~600 lines.

---

## Recommended Path

**Option C — Thin repo + packaged tools**, staged, and only after Q1–Q4 are answered:
1. **Spike (throwaway, ~1 hour):** one plugin folder with one skill, one agent and one blocking hook, installed in Claude Code and Codex. Answers: prefixed agent name in a spawn; a blocking hook fires and does nothing in a non-kit repo; one folder serves both CLIs.
2. **easy-memory as the first real package** (smallest; proves MCP + hooks; settles the MCP question).
3. **Core kit package** for Claude Code; `setup.sh` unchanged as in-repo mode.

Why C over the rest: A keeps the "just run it" pain the user named; B drops the "understand it" audience and bets the kit on four vendor formats; D is a rewrite with the same user experience; E hands the gates to a third party. C is the only option that serves both audiences and can start with one small, reversible step.

Fallback if the spike fails (prefixed agent names break spawns or hooks): **Option A**, with the MCP closing line.

---

## Surgical Scope

Files that **should** be touched (later tasks, not this log):
- New plugin manifest(s) at repo root — package entry point
- `skills/*/SKILL.md`, `agents/*.md` — the 11 repo-relative script paths
- `.claude/hooks/*.py` — no-op outside a kit project
- `site/index.html` `#mcps`, README install section — document the two modes

Files that **must not** be touched:
- `setup.sh`, `lib/harness-*.sh` — in-repo mode stays as-is until a later decision
- `.claude/hooks/pre_bash_block_unsafe_merge.py` gate logic — distribution must not change a gate
- `MANIFEST` semantics — the in-repo installer depends on it

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Plugin hooks fire in every project where the plugin is enabled: each hook must exit 0 silently when the repo has no `PROJECT_KANBAN.md` / no kit marker
- [ ] Both modes installed at once (plugin + in-repo copies): a skill exists twice (`wake` and `easy-kit:wake`), hooks run twice
- [ ] `AGENTS.md` in the repo names a skill the installed package version lacks (version skew)
- [ ] Codex: plugin hooks need manual trust via `/hooks`; until trusted, gates are off with no warning
- [ ] `${CLAUDE_PLUGIN_ROOT}` changes on every update: no state written there; use `${CLAUDE_PLUGIN_DATA}`
- [ ] Teammate has `enabledPlugins` in project settings but never ran `claude plugin install`: gates silently absent
- [ ] Hooks that match on `subagent_type` see `easy-kit:backend-developer`, not `backend-developer`
