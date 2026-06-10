# Supervisor Agent Deployment System

Deploy a structured multi-agent supervisor framework into any project with a single command.

---

## What this repo is

This repo is a general-purpose supervisor framework for Claude Code. It provides a set of agent
definitions, skills, and templates that turn Claude into an autonomous project supervisor —
orchestrating a team of specialized sub-agents through a structured delivery pipeline. The framework
is project-agnostic: you install it once and deploy it into as many projects as you like. General
resources (agents, skills, templates) are shared from a central clone and symlinked into each
project; project-specific files (task guides, memory, PRD) are always created fresh per project and
are never shared.

---

## Quick Start

```sh
# curl variant (replace YOUR_GITHUB_USERNAME/per-agentic-claude with your fork URL when the repo is public)
curl -fsSL https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/per-agentic-claude/main/setup.sh | sh

# wget variant
wget -qO- https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/per-agentic-claude/main/setup.sh | sh
```

> **Placeholder notice:** the URL above is a placeholder. Replace `YOUR_GITHUB_USERNAME/per-agentic-claude`
> with the actual raw URL of your fork before using.

Run from inside the target project's root directory.

---

## Prerequisites

- **git** — required for cloning and updating the central clone
- **bash** or **sh** (POSIX-compatible) — both scripts are POSIX-compatible; no bash 4+ features required

---

## Installation

### 1. Clone via `setup.sh`

Run `setup.sh` from inside the root of the project you want to deploy into:

```sh
sh setup.sh          # default: symlink mode
sh setup.sh --copy   # copy mode (see Override per Project below)
```

The script:
1. Clones this repo to `~/.supervisor` (the central clone) if it does not already exist.
2. Prompts you to choose **greenfield** or **brownfield** mode.
3. Reads the `MANIFEST` and symlinks (or copies) each listed resource into the current directory.
4. Creates `CLAUDE.md` (greenfield) or `CLAUDE_LEGACY.md` as `CLAUDE.md` (brownfield).
5. Scaffolds project-specific folders and files.

### 2. Greenfield vs brownfield

| Mode | When to use | `CLAUDE.md` source |
|------|-------------|-------------------|
| **Greenfield** | Starting a new project from scratch | `CLAUDE.md` |
| **Brownfield** | Working in an existing or production codebase | `CLAUDE_LEGACY.md` |

Choose at the interactive prompt. The choice only affects which supervisor playbook is active.

### 3. What gets deployed

The following table matches the `MANIFEST`:

| Resource | Type | Description |
|----------|------|-------------|
| `.claude/agents/` | Shared (symlinked) | Sub-agent definitions auto-discovered by Claude Code |
| `.claude/skills/` | Shared (symlinked) | Custom skill definitions auto-discovered by Claude Code |
| `templates/` | Shared (symlinked) | Blank templates for PRD, PROJECT_SPEC, KANBAN, TASK_GUIDE, etc. |
| `CLAUDE.md` | Shared (symlinked) | Active supervisor instructions (greenfield or brownfield) |
| `tasks/` | Project-specific (created fresh) | Task guides generated at Stage 2, one per task |
| `memory/MEMORY.md` | Project-specific (created fresh) | Session-persistent insights index |

Shared resources are symlinked by default so all projects receive updates automatically when you
run `update.sh`. Project-specific files are never symlinked and are never overwritten on re-runs.

---

## Update

Pull the latest framework changes into all projects that use it:

```sh
sh update.sh
```

`update.sh` must be run from the project directory or anywhere — it operates on the central clone
(`~/.supervisor`), not the project. What it does:

1. Runs `git pull --ff-only` on the central clone.
2. Reports the commit range that was pulled (`old-sha → new-sha`) with one-line summaries.
3. Warns if the `MANIFEST` changed, indicating new resources are available — re-run `setup.sh` to
   deploy them.
4. If already up to date, reports `HEAD` and exits cleanly.

Because projects use symlinks into the central clone, the updated files are immediately active in
every symlinked project — no per-project action needed (unless `MANIFEST` changed).

---

## Add a Skill Globally

To add a new skill that is available in all projects:

1. Create the skill folder inside the central clone:
   ```sh
   mkdir -p ~/.supervisor/.claude/skills/my-skill
   # Create ~/.supervisor/.claude/skills/my-skill/SKILL.md following templates/SKILL_template.md
   ```
2. Add the skill path to `~/.supervisor/MANIFEST` if you want it auto-deployed to new projects.
3. Commit and push from the central clone:
   ```sh
   git -C ~/.supervisor add .claude/skills/my-skill MANIFEST
   git -C ~/.supervisor commit -m "feat(skills): add my-skill"
   git -C ~/.supervisor push
   ```
4. On any machine where you want the change, run:
   ```sh
   sh update.sh
   ```

All projects using symlinks will see the new skill immediately after the pull.

---

## Override per Project

To customize a resource for a single project without affecting others, use the `--copy` flag:

```sh
sh setup.sh --copy
```

This copies each `MANIFEST` resource into the project instead of symlinking it. You can then edit
the local copy freely.

**Important:** copied files do not auto-update. When you run `update.sh`, the central clone updates
but the local copies in `--copy` projects are not touched. To pull upstream changes into a copied
resource you must either:
- Re-run `sh setup.sh --copy` for files that have not been locally edited (idempotent for
  unchanged files).
- Manually merge changes from `~/.supervisor/<path>` into the project's local copy.

> If a file is already a symlink from a previous install and you re-run with `--copy`, the script
> warns and skips that file. Remove the symlink manually first to switch modes.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPERVISOR_PATH` | `~/.supervisor` | Path to the central clone. Set this to use a non-default location. |

Example:

```sh
SUPERVISOR_PATH=/opt/supervisor sh setup.sh
SUPERVISOR_PATH=/opt/supervisor sh update.sh
```

Both `setup.sh` and `update.sh` respect this variable.

---

## Git Submodule Alternative (Optional)

Instead of a central clone managed by `setup.sh`, you can add this repo as a git submodule inside
your project:

```sh
git submodule add https://github.com/YOUR_GITHUB_USERNAME/per-agentic-claude .supervisor
```

Then symlink or copy resources manually from `.supervisor/` into the project root. Run
`git submodule update --remote` to pull updates. This approach ties the framework version to the
project's commit history, which is useful when you need reproducible, pinned deployments. The
`setup.sh` / `update.sh` workflow is simpler for most use cases; submodules are the better fit when
strict version pinning matters.
