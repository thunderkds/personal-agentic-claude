# Agentic Claude — Project Supervisor System

A Claude Code configuration that turns Claude into an autonomous project supervisor, orchestrating a team of specialized sub-agents through a structured delivery pipeline.

Two playbooks are provided for different project contexts:

| Playbook | File | Use when |
|---|---|---|
| **Greenfield** | `CLAUDE.md` | Starting a new project from scratch |
| **Legacy / Brownfield** | `CLAUDE_LEGACY.md` | Working in an existing, production codebase |

---

## Quickstart

1. Copy this repo's `.claude/` folder, `tasks/`, `templates/`, and `memory/` into your project root.
2. Decide which playbook applies and delete (or ignore) the other — Claude reads both by default, which creates ambiguity.
3. Say **"Start new project supervision"** to begin.

---

## How it works

Claude acts as a **Project Supervisor** that runs a 5-stage agentic pipeline:

```
Phase 0: Context gathering (Q&A with you)
  ↓
Stage 0.5: Brainstorming — three implementation paths, adversarial review
  ↓
Stage 1: Environment & provider setup
  ↓
Stage 1.5: Sub-agent team design
  ↓
Stage 2: Planning (/plan) — PROJECT_SPEC.md + task guides generated
  ↓
Stage 3: Parallel execution — each task runs in an isolated git worktree
  ↓
Stage 4: Code review + security review
  ↓
Stage 5: Integration & end-to-end verification
```

The Supervisor never implements directly. It spawns focused sub-agents, each constrained to their worktree and their assigned task guide.

---

## Folder structure

```
.claude/
  agents/          # Sub-agent definitions (auto-discovered by Claude Code)
    backend.md             → subagent_type: "backend-developer"
    frontend.md            → subagent_type: "frontend-developer"
    qa.md                  → subagent_type: "qa-expert"
    common-infrastructure.md → subagent_type: "common-infrastructure"
    general-agent-template.md  # Shared base rules (not spawned directly)
  skills/          # Custom skills (auto-discovered by Claude Code)
    brainstorming/
      SKILL.md             → Skill({ skill: "brainstorming" })
  settings.local.json

tasks/             # TASK_GUIDE_T001.md … generated at Stage 2, one per task
templates/         # Blank templates for PROJECT_SPEC, KANBAN, TASK_GUIDE, BRAINSTORMING_LOG
memory/
  MEMORY.md        # Session-persistent insights index

CLAUDE.md          # Greenfield playbook (active supervisor instructions)
CLAUDE_LEGACY.md   # Brownfield playbook
```

---

## Greenfield (`CLAUDE.md`)

Designed for new projects. The Supervisor starts with open-ended context gathering, runs brainstorming before any planning is locked, and builds the full pipeline from scratch.

**Key behaviors:**
- Strict stage ordering — no stage can be skipped or reordered
- All sub-agents spawned with real `subagent_type` values (backed by `.claude/agents/`)
- `BRAINSTORMING_LOG.md` generated from `templates/BRAINSTORMING_LOG_template.md` before planning begins
- `PROJECT_SPEC.md` and `PROJECT_KANBAN.md` are the twin sources of truth
- Code review mandatory at Stage 4; security review mandatory for Medium/High risk tasks
- `verify` skill mandatory before any merge

---

## Legacy / Brownfield (`CLAUDE_LEGACY.md`)

Designed for production codebases where the risk of regressions is high. Adds an investigation phase before any implementation starts.

**Key differences from greenfield:**
- **Investigation-first**: the Supervisor runs structured discovery sessions to build a `docs/legacy/` knowledge base (architecture map, risk hotspots, dependency graph) before writing any code
- **Modes**: `feature-addition`, `bug-fix`, or `legacy-improvement` — each with its own risk posture
- **Risk-gated brainstorming**: brainstorming is mandatory for Medium/High risk tasks, optional for Low
- **Surgical-change enforcement**: sub-agents are explicitly told which files must not be touched
- Maintains its own folder at `docs/legacy/` for investigation outputs

---

## Skills vs Agents

Two distinct mechanisms — do not confuse them:

| | Skills | Agents |
|---|---|---|
| Defined in | `.claude/skills/<name>/SKILL.md` (custom) or built-in | `.claude/agents/<name>.md` |
| Invoked via | `Skill({ skill: "name" })` | `Agent({ subagent_type: "name", prompt: "..." })` |
| Runs | Inline in the current conversation | Isolated sub-process with its own context window |
| Use for | Cross-cutting analysis (brainstorm, review, verify) | Focused implementation in a worktree |

**Custom skill in this repo:** `brainstorming`
**Built-in skills used:** `code-review`, `security-review`, `verify`, `run`, `update-config`, `fewer-permission-prompts`

---

## Karpathy Engineering Principles

All agents enforce these four principles:

| Principle | Rule |
|---|---|
| **Think Before Coding** | State all assumptions explicitly. Stop at any point of confusion. |
| **Simplicity First** | Reject any abstraction not explicitly requested. If 200 lines can be 50, rewrite. |
| **Surgical Changes** | Touch only code required by the task. Do not "improve" adjacent code. |
| **Goal-Driven Execution** | Convert every instruction into a verifiable success criterion before starting. |
