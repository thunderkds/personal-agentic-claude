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
Phase 0: Context gathering (Q&A with you) → PRD.md generated
  ↓
Stage 0.5a: Requirement grilling — PRD.md validated before brainstorming
  ↓
Stage 0.5b: Brainstorming — three implementation paths, adversarial review
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

## The three pillars every task passes through

Whatever the task, the flow walks the same three pillars **in order** — each with a gate that must
be green before the next begins:

```
Pillar 1: Adapt the requirement   →   Pillar 2: Right implementation   →   Pillar 3: Evaluation
  capture intent faithfully            build it test-first, surgically      prove it works, with evidence
```

| Pillar | What it guarantees | Gate (proof it happened) | Stage |
|---|---|---|---|
| **1. Adapt the requirement** | We're building the *right thing* — intent captured in the project's language, criteria traced to the request, every FR/US ID in `PRD.md` covered | **Requirement Fidelity Gate** signed off by Supervisor/user (not the implementer) before any code; FR coverage confirmed at Stage 4 | Phase 0 → Stage 2, checked at Stage 3 start + Stage 4 |
| **2. Right implementation** | We're building it *the right way* — test-first, surgical, only the predicted files | `tdd` red→green→refactor + must-not-touch list | Stage 3 |
| **3. Evaluation** | It *actually works* — verified by an independent oracle, with recorded evidence | **Evidence Gate** — verification command run + output pasted, Requirement Refs covered, no regression | Stage 4 → Stage 5 |

The links between pillars are what keep the chain honest: every Acceptance Criterion **traces back
to a line in the Requirement** (1→3), and the implementing agent is never the sole author of its own
acceptance test (2 can't fake 3). The `TASK_GUIDE` is the single sheet where all three are recorded.

---

## How we evaluate agent work (correctness)

The hardest question in any agentic pipeline is *"how do we know the agent actually did it right?"*
This system answers it by making correctness **verifiable by construction**, not judged after the fact.

### The principle

Every task is phrased as a **verifiable goal**, never an imperative (the Karpathy *Task
Transformation Table*): "add validation" → *"write tests for invalid inputs, then make them
pass."* If a task can't be expressed as a pass/fail check, it isn't ready to spawn.

### The evaluation layers

| Layer | Oracle (what decides pass/fail) | Where |
|---|---|---|
| **1. Acceptance criteria** | Concrete `given → expect` rows + a single runnable verification command | `TASK_GUIDE` *Evaluation & Acceptance* section — filled **before** the agent starts |
| **2. Tests (TDD)** | Failing test written/approved by the Supervisor, then made green | `tdd` skill, Stage 3 |
| **3. Independent review** | A fresh context (not the implementer) reads the diff | `code-review` / `security-review`, Stage 4 |
| **4. End-to-end behavior** | The real app is run and observed | `verify` / `run` skill, Stage 5 |
| **5. No regression** | The full smoke suite stays green after merge | QA-agent owns the suite |

### The one rule that prevents self-deception

> **The implementing agent must not be the sole author of its own acceptance test.**
> If one agent writes both the code and the test, it can make both agree while both are wrong.
> The Supervisor writes or signs off on the oracle first, and review runs in a *separate* context
> from implementation.

### Evidence, not vibes

Each `TASK_GUIDE` carries an **Evaluation & Acceptance** block with three parts:

1. **Success Criteria** — observable `given → expect` rows (including negative cases)
2. **Verification Command** — the exact command that proves it works
3. **Evidence** — pass/fail + real output, filled in by the reviewer at Stage 4/5

A task is **not done** until every evidence row is filled. This turns "looks done" into a record
you can audit. See `templates/TASK_GUIDE_template.md` for the block.

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
    brainstorming/         → Skill({ skill: "brainstorming" })      # Stage 0.5
    grill-with-docs/       → Skill({ skill: "grill-with-docs" })    # Stage 2
    to-issues/             → Skill({ skill: "to-issues" })          # Stage 2
    tdd/                   → Skill({ skill: "tdd" })                # Stage 3
    diagnose/              → Skill({ skill: "diagnose" })           # Stage 3
    git-guardrails-claude-code/ → Skill({ skill: "git-guardrails-claude-code" })  # Stage 1 setup
    blast-radius/          → Skill({ skill: "blast-radius" })       # Stage 4
  settings.local.json

tasks/             # TASK_GUIDE_T001.md … generated at Stage 2, one per task
templates/         # Blank templates for PRD, PROJECT_SPEC, KANBAN, TASK_GUIDE, BRAINSTORMING_LOG
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
- `PRD.md` generated from `templates/PRD_template.md` at the end of Phase 0 — mandatory before brainstorming begins
- `grill-with-docs` runs in **requirement mode** (Stage 0.5a) to validate `PRD.md` before brainstorming, then in **terminology mode** (Stage 2) to sharpen language before task breakdown
- `BRAINSTORMING_LOG.md` generated from `templates/BRAINSTORMING_LOG_template.md` before planning begins
- `PROJECT_SPEC.md` and `PROJECT_KANBAN.md` are the twin sources of truth
- Each `TASK_GUIDE` carries a **Requirement Refs** field (FR/NFR/US IDs) that the Stage 4 Evidence Gate checks for coverage
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

**Custom skills in this repo:** `brainstorming`, `grill-with-docs`, `to-issues`, `tdd`, `diagnose`, `git-guardrails-claude-code`, `blast-radius`
**Built-in skills used:** `code-review`, `security-review`, `verify`, `run`, `update-config`, `fewer-permission-prompts`

---

## Custom skills

Cross-cutting helpers the Supervisor invokes at specific pipeline stages. `brainstorming` ships with the original system; the rest were vendored (and adapted to this framework) from community skill collections.

| Skill | Stage | Complexity | What it does |
|---|---|---|---|
| `brainstorming` | 0.5b | — | **Divergent** exploration — three implementation paths + adversarial review, written to `BRAINSTORMING_LOG.md` |
| `grill-with-docs` | 0.5a + 2 | C1–C2 | Two modes: **requirement mode** (Stage 0.5a) validates `PRD.md` — FR traceability, NFR completeness, scope clarity — before brainstorming; **terminology mode** (Stage 2) interrogates the plan one question at a time and sharpens fuzzy terminology into `PROJECT_SPEC.md` |
| `to-issues` | 2 | C1 | Breaks the locked plan into **tracer-bullet vertical slices** — each a complete end-to-end path — that become `PROJECT_KANBAN.md` rows and `TASK_GUIDE` files, labelled with Complexity/Risk/Priority |
| `tdd` | 3 | C1 | **Red → green → refactor**, one vertical slice at a time. Operationalizes the Karpathy Task Transformation Table (write the failing test first) |
| `diagnose` | 3 | C1 | Disciplined bug / perf-regression loop: build a feedback loop → reproduce → 3–5 falsifiable hypotheses → instrument → fix + regression-test → post-mortem |
| `git-guardrails-claude-code` | 1 setup | C0 | Installs a `PreToolUse` hook that blocks destructive git (`push`, `reset --hard`, `clean -f`, `branch -D`, `checkout/restore .`) before it runs — enforces "commit/push only when asked" mechanically |
| `blast-radius` | 4 | — | For Medium/High-risk tasks touching sensitive data: inventories PII/PHI/credentials, traces data flow, scores exposure vectors, and estimates regulatory + financial breach impact |

> These are **available** for the Supervisor to invoke at the mapped stage — not auto-run. The Supervisor decides based on each task's Complexity/Risk labels (e.g. `tdd`/`diagnose` for C1+ implementation, `blast-radius` only when Risk is Medium/High *and* sensitive data is in scope).

### Authoring a skill

New skills follow a house style so the Supervisor can rely on them. Start from **`templates/SKILL_template.md`** and keep these conventions:

1. **One folder per skill**: `.claude/skills/<name>/SKILL.md`, where `<name>` matches the frontmatter `name:` exactly (that's the `Skill({ skill: "<name>" })` handle).
2. **`description:` drives triggering** — it's the only text Claude sees when deciding to invoke. Say *what* it does and *when* (name the pipeline stage).
3. **Section order**: `Role` → `Karpathy Operational Commands` (only the relevant overrides) → `Workflow` → `Communication Protocol`.
4. **Adapt, don't copy** — when vendoring an external skill, strip external CLI/tool dependencies and route any state into `PROJECT_SPEC.md` rather than introducing new conventions.
5. **Self-contained** — if you reference a sub-file, vendor it; bundled scripts go in `scripts/` (`chmod +x` + a smoke test).
6. **Register it** in the `CLAUDE.md` custom-skill table *and* the Custom skills table above.

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
