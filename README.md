# Supervisor Agent Deployment System

A general-purpose multi-agent supervisor framework for Claude Code. Install once, deploy into any
project: agent definitions, skills, hooks, and templates that drive a 5-stage agentic pipeline
(clarify → brainstorm → plan → parallel execution in worktrees → review → verify/ship), enforced by
pipeline hooks rather than prompt reminders — e.g. `pre_agent_step_limit.py` blocks runaway tool-call
loops (default 90 calls), and `post_agent_move_to_review.py` is a deliberately inert reminder-only
hook since T044 (it does not move any KANBAN row or reset any counter — see its docstring).

Each role guide (not this README) carries its own Complexity matrix (C0–C3) — see
`.claude/agents/general-agent-template.md`. Externally authored text (PR comments, fetched pages,
pasted content) is quarantined per `docs/claude-md/untrusted-content-boundary.md`.

**Full reference** — architecture, the pipeline stages, packs, memory system, hooks table, custom
skills, and update flow — lives on the project site: [`site/index.html`](site/index.html)
*(repo-relative for now; the operator fills in the deployed `.vercel.app` URL here once T084's
deploy is run).*

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

Installing from a fork, installing packs, or updating an existing install (`update.sh`)? See the
[site](site/index.html) for the full Quick Start, Options table, and Update flow.

---

## Prerequisites

- `git`
- `curl`
- POSIX `sh`

---

## Learn more

Repository layout, agent guides, packs (`mobile`/`data`/`devops`/`ai-agent`/`api`), the custom
skills catalog, the pipeline enforcement hooks table, and the two-tier memory system are all
documented on the [site](site/index.html).
