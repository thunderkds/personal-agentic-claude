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
Stage 4: Code review (+ security review for Medium/High risk tasks) → HTML reports
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
| `.claude/settings.json` | Hook wiring *(deployed as a per-project copy — projects append their own permissions)* |
| `templates/` | Blank templates for PRD, PROJECT_SPEC, KANBAN, TASK_GUIDE, HTML report, etc. |
| `CLAUDE.md` | Supervisor instructions (greenfield) |
| `CLAUDE_LEGACY.md` | Supervisor instructions (brownfield / existing codebase) |
| `tasks/` | *(per project)* Task guides generated at Stage 2 |
| `memory/MEMORY.md` | *(per project)* Hot-tier memory index — ≤200 lines, injected into every sub-agent spawn prompt |
| `memory/decisions.md` | *(per project)* Architectural + infrastructure decisions |
| `memory/glossary.md` | *(per project)* Canonical biz-domain terms and core domain models |
| `memory/learnings.md` | *(per project)* Specs clarifications, patterns, gotchas |

Shared resources (`agents`, `skills`, `hooks`, `templates`, `packs`) are **symlinked** from `~/.supervisor` so all projects update automatically. `.claude/settings.json` is **copied** (projects add their own permissions to it). Project-specific files are created fresh and never overwritten.

---

## Packs (optional domain extensions)

The core framework ships four agents (backend, frontend, common-infrastructure, qa) for every project. **Packs** add domain-specific agents and skills on top — selected at install time, never replacing core resources.

| Pack | Domain | Adds |
|------|--------|------|
| `mobile` | Flutter, React Native, Swift, Kotlin | `mobile-developer` agent + `ui-accessibility` + `platform-compatibility` skills |
| `data` | Pipelines, notebooks, ETL, dbt | `data-engineer` agent + `notebook-review` + `pipeline-safety` skills |
| `devops` | Terraform, K8s, CI/CD, Docker | `devops-engineer` agent + `infra-safety` + `deployment-checklist` skills |
| `ai-agent` | LLM apps, RAG, MCP servers | `ai-engineer` agent + `prompt-review` + `eval-design` skills |
| `api` | REST/gRPC, OpenAPI, auth flows | `api-designer` agent + `contract-review` + `auth-checklist` skills |

**Install packs interactively** — `setup.sh` prompts for pack selection when run from a TTY.

**Install a specific pack** into an existing project:
```sh
sh ~/.supervisor/setup.sh --pack=mobile
sh ~/.supervisor/setup.sh --pack=mobile --pack=api   # multiple packs
```

Pack agents and skills are symlinked into the project's `.claude/agents/` and `.claude/skills/` alongside the core resources. Each pack ships a `PACK.md` describing when to use it and what it adds.

---

## Quick Start

Run from inside the target project root:

```sh
curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh
```

That's it — the script clones the framework to `~/.supervisor` (first run only), symlinks the shared resources into the project, and scaffolds `tasks/` + the two-tier `memory/` files.

Installing from a fork? Export your username first and swap it into the URL:

```sh
export GITHUB_USERNAME=your-username
curl -fsSL https://raw.githubusercontent.com/$GITHUB_USERNAME/personal-agentic-claude/main/setup.sh | sh
```

> Piped installs are non-interactive: they default to **greenfield** (`CLAUDE.md`) and never overwrite existing files. For a brownfield project, run it interactively instead: `sh ~/.supervisor/setup.sh` and choose option 2.

After installing, restart Claude Code in the project so the deployed hooks in `.claude/settings.json` are picked up.

---

## Update

```sh
sh ~/.supervisor/update.sh   # pulls latest; symlinked projects update instantly
```

If `MANIFEST` changed, re-run `sh ~/.supervisor/setup.sh` from each project root to deploy new resources.

---

## HTML Reports (Stage 4)

After each Stage 4 review skill completes, the Supervisor invokes the `html-report` skill to produce a self-contained `.html` report saved locally under `reports/`.

```
Skill({ skill: "html-report", args: "skill=code-review task=T001 branch=main" })
```

Each report contains:
- **Scorecard header** — skill name, branch, date, overall health badge (Healthy / Needs Attention / Critical)
- **Dimension gauges** — Risk %, Code Quality %, Adaptation Effort % as progress bars (0–100)
- **Findings table** — severity badge (High/Med/Low/Info), file, line range, description
- **Summary prose** — the skill's narrative, unchanged
- **Metadata footer** — model, task ID, timestamp

Reports are generated for all three Stage 4 skills: `code-review`, `security-review`, and `blast-radius`.

**Filename convention:** `reports/<skill>_<branch>_<YYYYMMDDTHHMMSS>.html`
Example: `reports/code-review_main_20260618T143022.html`

Reports are **local-only** (`.gitignore`d) — open directly in any browser, no server needed.

| Template | Skill definition |
|----------|-----------------|
| `templates/report_template.html` | `.claude/skills/html-report/SKILL.md` |

---

## Thinking Reports (Stage 0.5–2)

After a brainstorming, grilling, or planning session locks a direction, the Supervisor invokes the `thinking-report` skill to capture *how* the decision was reached — not just what was decided.

```
Skill({ skill: "thinking-report", args: "session=brainstorming task=T001 branch=main" })
```

Each report contains:
- **Decision box** — the problem statement, chosen option, and rationale (the "why")
- **Trade-Off Matrix** — options × criteria table (✅ / ⚠️ / ❌), chosen column highlighted green
- **Assumptions & Open Questions** — resolved items, tracked assumptions, and deferred decisions tagged by status

Triggered automatically after:
- Stage 0.5b brainstorming direction is approved
- Stage 2 planning task breakdown is confirmed

**Filename convention:** `reports/thinking-report_<branch>_<YYYYMMDDTHHMMSS>.html`

| Template | Skill definition |
|----------|-----------------|
| `templates/report_template.html` | `.claude/skills/html-report/SKILL.md` |
| `templates/thinking_report_template.html` | `.claude/skills/thinking-report/SKILL.md` |

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
- `curl`
- POSIX `sh`

---

## Options

| Variable | Default | Purpose |
|----------|---------|---------|
| `SUPERVISOR_PATH` | `~/.supervisor` | Override the central clone location |
| `GITHUB_USERNAME` | `thunderkds` | Install from a fork instead of the canonical repo |

**Greenfield vs Brownfield** — chosen interactively during `setup.sh`. Brownfield uses `CLAUDE_LEGACY.md` which adds legacy-codebase guidance (risk hotspots, strangler-fig patterns).

**`--copy` mode** — copies instead of symlinking. Files do not auto-update; merge upstream changes manually from `~/.supervisor/<path>`.

**Git submodule alternative** — add as `.supervisor` submodule for pinned versioning; symlink resources manually; update with `git submodule update --remote`.
