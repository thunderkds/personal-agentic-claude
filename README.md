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

## Task Classification

Every task carries three **independent** labels. They answer different questions and never collapse into one number — a one-line change can be trivial *effort* yet high *risk*.

| Axis | Question it answers | What it controls |
|---|---|---|
| **Complexity** (C0–C3) | How much effort/process does this need? | Whether to brainstorm, decompose, spawn a sub-agent, which model, how deep to verify |
| **Risk** (Low/Med/High) | How dangerous is it if it goes wrong? | Safety gates: `security-review`, approvals, must-not-touch enforcement |
| **Priority** (P0/P1/P2) | When should we do it? | Ordering on the Kanban only — never *how* an agent works |

### Complexity levels

This is the axis an agent uses to **pick how much process to apply** to its assigned task.

| Level | Name | Signals — how to classify | What the agent does | Model |
|---|---|---|---|---|
| **C0** | Trivial | 1 file, ~≤10 LOC, no design decision (typo, copy text, config flag flip) | Work inline — no worktree, no brainstorm. `code-review` optional. | haiku |
| **C1** | Simple | 1–2 files, a known pattern, no new abstraction | No brainstorm. `code-review` always. `verify` if the change is user-facing. | sonnet |
| **C2** | Moderate | 3+ files, *or* a real design choice, *or* a new component | `brainstorming` when more than one approach is viable. Full `code-review` + `verify`. | sonnet / opus |
| **C3** | Complex | Cross-cutting, architectural, carries unknowns, or touches shared/core code | `brainstorming` **mandatory**. Decompose into subtasks. Multi-agent execution + adversarial `verify`. | opus |

> **Above C3 = "Epic".** Not an executable level — if a task reads bigger than C3, the Supervisor must **split it into smaller tasks during Stage 2 (Planning)** before any agent picks it up.

### How the axes compose

> **Example:** a one-line change to the auth token check → **C0 (trivial effort)** but **High risk**. The agent skips brainstorming and the worktree, but `security-review` is still mandatory because of the Risk axis. Merging the two axes would lose this — which is why they stay separate.

### Who assigns the level

The **Supervisor sets a baseline** Complexity (and Risk + Priority) in each `TASK_GUIDE` during Stage 2. On pickup, an agent that discovers hidden complexity **escalates the level and pauses to notify the Supervisor** rather than silently powering through — so the plan stays honest.

---

## Karpathy Engineering Principles

All agents enforce these four principles:

| Principle | Rule |
|---|---|
| **Think Before Coding** | State all assumptions explicitly. Stop at any point of confusion. |
| **Simplicity First** | Reject any abstraction not explicitly requested. If 200 lines can be 50, rewrite. |
| **Surgical Changes** | Touch only code required by the task. Do not "improve" adjacent code. |
| **Goal-Driven Execution** | Convert every instruction into a verifiable success criterion before starting. |
