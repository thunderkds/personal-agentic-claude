# Easy Kit

**v2.0.0** — a general-purpose multi-agent supervisor framework for Claude Code, Codex, and Cursor.
Install once, deploy into any project: agent definitions, skills, hooks, and templates that drive a
5-stage agentic pipeline
(clarify → brainstorm → plan → parallel execution in worktrees → review → verify/ship), enforced by
pipeline hooks rather than prompt reminders — e.g. `pre_agent_step_limit.py` blocks runaway tool-call
loops (default 90 calls), and `post_agent_move_to_review.py` is a deliberately inert reminder-only
hook since T044 (it does not move any KANBAN row or reset any counter — see its docstring).

Each role guide (not this README) carries its own Complexity matrix (C0–C3) — see
`agents/general-agent-template.md`. Externally authored text (PR comments, fetched pages,
pasted content) is quarantined per `docs/claude-md/untrusted-content-boundary.md`.

`CLAUDE.md` is the primary source of truth; Codex and Cursor get a thin adapter each (`AGENTS.md`,
`.cursor/rules/agent-base.mdc`) carrying the kit's non-negotiables — see `docs/MULTI_AGENT.md`.

**Full reference** — architecture, the pipeline stages, packs, memory system, hooks table, custom
skills, and update flow — lives on the project site:
[personal-agentic-claude.vercel.app](https://personal-agentic-claude.vercel.app/)

---

## Quick Start

**Prerequisite:** the target directory must already be a git repository (`git init` first if it
isn't — your project's own git history is the undo mechanism, since nothing is symlinked from a
shared location).

Run from inside the target project root:

```sh
curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh
```

This fetches the framework into a temporary clone, copies every `MANIFEST`-listed path plus
`CLAUDE.md`/`CLAUDE_LEGACY.md` into your project as real files, and scaffolds `tasks/` +
`memory/`. No persistent central clone is required. After installing, restart Claude Code in the
project so the deployed hooks in `.claude/settings.json` are picked up.

The command takes no options. It asks from numbered lists: what to do (**Install**, or **Update** /
**Reinstall** where Easy Kit is already installed), **which CLIs** to set up (`1) Claude Code  2) Codex`;
those found on your `PATH` are pre-selected), and whether this is a **new or an existing / legacy
project**. It shows a plan and asks `Proceed? [Y/n]` before it changes anything.

Codex caps a skill body at 8 KB. A skill whose body currently exceeds that cap is **skipped**
entirely on a Codex install — never truncated — with a named, loud warning. Skills currently
affected:

- `bugfix`
- `craft-spawn-prompt`
- `diagnose`
- `write-better-skill`

To update, run the same line again and choose **Update** — it keeps the CLIs your project already has,
so a Codex-only install stays Codex-only. To add a CLI later, choose **Reinstall** and pick it. Fork
installs, packs and the full Update flow: see the [site](https://personal-agentic-claude.vercel.app/).

---

## Prerequisites

- `git`
- `curl`
- POSIX `sh`

---

## Learn more

Repository layout, agent guides, packs (`mobile`/`data`/`devops`/`ai-agent`/`api`), the custom
skills catalog, the pipeline enforcement hooks table, and the two-tier memory system are all
documented on the [site](https://personal-agentic-claude.vercel.app/).
