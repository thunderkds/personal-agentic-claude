# Supervisor Agent Deployment System

A general-purpose multi-agent supervisor framework for Claude Code. Install once, deploy into any project.

---

## How it works

```
Phase 0: Clarify requirements → lock PRD
    ↓
Stage 0.5: Grill PRD → Brainstorm directions → lock direction
    ↓
Stage 1: Setup environment, verify folders, configure hooks
    ↓
Stage 1.5: Design sub-agent team
    ↓
Stage 2 (/plan): Generate PROJECT_SPEC + KANBAN + TASK_GUIDEs
    ↓
Stage 3: Parallel execution — each task in its own worktree (TDD)
    ↓
Stage 4: Code review (+ security review for Medium/High risk tasks)
    ↓
Stage 5: Verify end-to-end → merge → ship
```

**Three pillars every task must pass (Stage 3→5):**
1. **Requirement fidelity** — intent matches, terms align, ACs trace to FRs
2. **Right implementation** — built test-first, touches only predicted files
3. **Evaluation** — evidence table filled, smoke suite green, reviewer signs off

---

## Repository layout

| Path | What it contains |
|------|-----------------|
| `.claude/agents/` | Sub-agent definitions (common-infrastructure, backend, frontend, qa) |
| `.claude/skills/` | Custom skills (brainstorming, grill-with-docs, tdd, ship, …) |
| `.claude/hooks/` | Pipeline enforcement hooks (auto-kanban, gate checks, merge blocks) |
| `.claude/settings.json` | Hook wiring |
| `templates/` | Blank templates for PRD, PROJECT_SPEC, KANBAN, TASK_GUIDE, etc. |
| `CLAUDE.md` | Supervisor instructions (greenfield) |
| `CLAUDE_LEGACY.md` | Supervisor instructions (brownfield / existing codebase) |
| `tasks/` | *(per project)* Task guides generated at Stage 2 |
| `memory/MEMORY.md` | *(per project)* Session-persistent insights index |

Shared resources are **symlinked** from `~/.supervisor` so all projects update automatically. Project-specific files are created fresh and never overwritten.

---

## Quick Start

Replace `your-username` with your GitHub username, then run from inside the target project root:

```sh
GITHUB_USERNAME=your-username
curl -fsSL https://raw.githubusercontent.com/$GITHUB_USERNAME/personal-agentic-claude/main/setup.sh | sh
```

That's it. The script clones the framework to `~/.supervisor` and wires everything into the current directory.

---

## Update

```sh
sh update.sh   # pulls latest into ~/.supervisor; symlinked projects update instantly
```

If `MANIFEST` changed, re-run `setup.sh` to deploy new resources.

---

## Pipeline Enforcement Hooks

Five hooks enforce the pipeline automatically — no prompt reminders needed.

| Hook | Event | What it does |
|------|-------|--------------|
| `post_write_register_task.py` | PostToolUse / Write | Writes a `TASK_GUIDE_Txxx.md` → auto-inserts task in `PROJECT_KANBAN.md` under Todo |
| `pre_agent_validate_guide.py` | PreToolUse / Agent | **Blocks** agent spawn if matching `TASK_GUIDE` is missing |
| `post_agent_move_to_review.py` | PostToolUse / Agent | Moves task `In Progress → Ready for Review` after agent finishes |
| `stop_review_reminder.py` | Stop | Prints Stage 4 review reminder for any `Ready for Review` tasks |
| `pre_bash_block_unsafe_merge.py` | PreToolUse / Bash | **Blocks** `git push/merge/rebase` if tasks are In Progress or verify evidence is missing |

---

## Prerequisites

- `git`
- `bash` / POSIX `sh`

---

## Options

| Variable | Default | Purpose |
|----------|---------|---------|
| `SUPERVISOR_PATH` | `~/.supervisor` | Override the central clone location |

**Greenfield vs Brownfield** — chosen interactively during `setup.sh`. Brownfield uses `CLAUDE_LEGACY.md` which adds legacy-codebase guidance (risk hotspots, strangler-fig patterns).

**`--copy` mode** — copies instead of symlinking. Files do not auto-update; merge upstream changes manually from `~/.supervisor/<path>`.

**Git submodule alternative** — add as `.supervisor` submodule for pinned versioning; symlink resources manually; update with `git submodule update --remote`.
