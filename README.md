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
| `.claude/skills/` | Custom skills (brainstorming, grill-with-docs, tdd, ship, compact-memory, …) |
| `.claude/hooks/` | Pipeline enforcement hooks (auto-kanban, gate checks, merge blocks, memory updates) |
| `.claude/settings.json` | Hook wiring |
| `templates/` | Blank templates for PRD, PROJECT_SPEC, KANBAN, TASK_GUIDE, etc. |
| `CLAUDE.md` | Supervisor instructions (greenfield) |
| `CLAUDE_LEGACY.md` | Supervisor instructions (brownfield / existing codebase) |
| `tasks/` | *(per project)* Task guides generated at Stage 2 |
| `memory/MEMORY.md` | *(per project)* Hot-tier memory index — ≤200 lines, injected into every sub-agent spawn prompt |
| `memory/decisions.md` | *(per project)* Architectural + infrastructure decisions |
| `memory/glossary.md` | *(per project)* Canonical biz-domain terms and core domain models |
| `memory/learnings.md` | *(per project)* Specs clarifications, patterns, gotchas |

Shared resources are **symlinked** from `~/.supervisor` so all projects update automatically. Project-specific files are created fresh and never overwritten.

---

## Quick Start

Set your GitHub username and run from inside the target project root:

```sh
GITHUB_USERNAME=your-username && curl -fsSL https://raw.githubusercontent.com/$GITHUB_USERNAME/personal-agentic-claude/main/setup.sh | sh
```

---

## Update

```sh
sh update.sh   # pulls latest into ~/.supervisor; symlinked projects update instantly
```

If `MANIFEST` changed, re-run `setup.sh` to deploy new resources.

---

## Pipeline Enforcement Hooks

Six hooks enforce the pipeline automatically — no prompt reminders needed.

| Hook | Event | What it does |
|------|-------|--------------|
| `post_write_register_task.py` | PostToolUse / Write | Writes a `TASK_GUIDE_Txxx.md` → auto-inserts task in `PROJECT_KANBAN.md` under Todo |
| `pre_agent_validate_guide.py` | PreToolUse / Agent | **Blocks** agent spawn if matching `TASK_GUIDE` is missing |
| `post_agent_move_to_review.py` | PostToolUse / Agent | Moves task `In Progress → Ready for Review` after agent finishes |
| `stop_review_reminder.py` | Stop | Prints Stage 4 review reminder for any `Ready for Review` tasks |
| `pre_bash_block_unsafe_merge.py` | PreToolUse / Bash | **Blocks** `git push/merge/rebase` if tasks are In Progress or verify evidence is missing |
| `post_bash_memory_update.py` | PostToolUse / Bash | After `git push/merge/pull` — prompts Supervisor to run the diff-driven memory-update pass |

---

## Memory System

The framework uses a **two-tier hot/cold memory** design to keep agents aligned across sessions.

```
memory/MEMORY.md          ← Hot tier (≤200 lines, always injected into spawn prompts)
memory/decisions.md       ← Cold tier: architectural + infrastructure decisions
memory/glossary.md        ← Cold tier: canonical biz-domain terms + core domain models
memory/learnings.md       ← Cold tier: specs clarifications, patterns, gotchas
```

**How it works:**
- **Supervisor-only writes.** Sub-agents never write to memory directly.
- **Spawn injection.** The Supervisor pastes the full `memory/MEMORY.md` verbatim into every sub-agent spawn prompt — no extra reads needed.
- **Auto-update.** The `post_bash_memory_update.py` hook fires after `git push/merge/pull` and prompts a diff-driven update pass: changed files → grep cold files → update matched entries → append new learnings.
- **Manual compaction.** Type `/compact-memory` any time to run a human-gated compaction: stale entries are flagged, reviewed, then pruned; the hot-tier index is re-synced.

**Cold file routing:**
| What happened | Write to |
|---|---|
| Architectural or infrastructure decision | `memory/decisions.md` |
| New canonical term or domain model confirmed | `memory/glossary.md` |
| Spec clarification, pattern, or gotcha discovered | `memory/learnings.md` |

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
