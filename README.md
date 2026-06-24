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
| `.claude/agents/` | Core sub-agent definitions (common-infrastructure, backend, frontend, qa) |
| `.claude/skills/` | Custom skills (strategy, ideate, brainstorming, grill-with-docs, tdd, code-review, resolve-pr-feedback, compound, compound-refresh, optimize, ship, learn, wake, …) |
| `.claude/hooks/` | Pipeline enforcement hooks (auto-kanban, gate checks, merge blocks, memory updates) |
| `.claude/settings.json` | Hook wiring *(deployed as a per-project copy — projects append their own permissions)* |
| `templates/` | Blank templates for PRD, PROJECT_SPEC, KANBAN, TASK_GUIDE, HTML report, Pack, etc. |
| `packs/` | Optional domain packs — each adds agents + skills for a specific project type |
| `CLAUDE.md` | Supervisor instructions (greenfield) |
| `CLAUDE_LEGACY.md` | Supervisor instructions (brownfield / existing codebase) |
| `tasks/` | *(per project)* Task guides generated at Stage 2 |
| `memory/MEMORY.md` | *(per project)* Hot-tier memory index — ≤200 lines, injected into every sub-agent spawn prompt |
| `memory/decisions.md` | *(per project)* Architectural + infrastructure decisions |
| `memory/glossary.md` | *(per project)* Canonical biz-domain terms and core domain models |
| `memory/learnings.md` | *(per project)* Specs clarifications, patterns, gotchas |
| `memory/learning-records/` | *(per project)* Sequential LR-NNNN-slug.md files written by the `learn` skill at runtime |
| `memory/codebase-map.md` | *(per project, generated)* Structural snapshot — directory tree, entry points, blast-radius hotspots. Written by `/map-codebase` at Stage 1; C2/C3 agents read it cold |

Shared resources (`agents`, `skills`, `hooks`, `templates`, `packs`) are **symlinked** from `~/.supervisor` so all projects update automatically. `.claude/settings.json` is **copied** (projects add their own permissions to it). Project-specific files are created fresh and never overwritten.

---

## Packs (optional domain extensions)

The core framework ships four agents (backend, frontend, common-infrastructure, qa) for every project. **Packs** add domain-specific agents and skills on top — selected at install time, never replacing core resources.

| Pack | Domain | Agent | Skills |
|------|--------|-------|--------|
| `mobile` | Flutter, React Native, Swift, Kotlin | `mobile-developer` | `ui-accessibility`, `platform-compatibility` |
| `data` | Pipelines, notebooks, ETL, dbt | `data-engineer` | `notebook-review`, `pipeline-safety` |
| `devops` | Terraform, K8s, CI/CD, Docker | `devops-engineer` | `infra-safety`, `deployment-checklist` |
| `ai-agent` | LLM apps, RAG, MCP servers | `ai-engineer` | `prompt-review`, `eval-design` |
| `api` | REST/gRPC, OpenAPI, auth flows | `api-designer` | `contract-review`, `auth-checklist` |

**Install packs interactively** — `setup.sh` prompts for pack selection when run from a TTY.

**Install a specific pack** into an existing project:
```sh
sh ~/.supervisor/setup.sh --pack=mobile
sh ~/.supervisor/setup.sh --pack=mobile --pack=api   # multiple packs
```

Pack agents and skills are symlinked into the project's `.claude/agents/` and `.claude/skills/` alongside the core resources. Each pack ships a `PACK.md` describing when to use it and what it adds.

**Updates:** because pack files are symlinked from `~/.supervisor`, running `sh ~/.supervisor/update.sh` pulls the latest version of all packs automatically — no per-project step needed.

---

### Pack details

#### `mobile` — Mobile app development
**When to use:** any project targeting iOS, Android, Flutter, or React Native.

| Resource | Type | Purpose |
|----------|------|---------|
| `mobile-developer` | Agent | Owns mobile lifecycle (cold start, backgrounding), app-store constraints, offline-first, ≥44 pt touch targets |
| `ui-accessibility` | Skill | WCAG 2.2 AA audit — VoiceOver/TalkBack, touch targets, color contrast, motion sensitivity. **Mandatory** before any UI Stage 4 |
| `platform-compatibility` | Skill | iOS/Android API-level guards, permissions, platform branches, Flutter/RN specifics |

**Boundary from core:** `mobile-developer` ≠ `frontend-developer` — mobile lifecycle and app-store constraints are out of scope for the web-focused frontend agent.

---

#### `data` — Data pipelines & analytics
**When to use:** ETL/ELT pipelines, Spark/dbt jobs, Jupyter notebooks, or any data engineering work.

| Resource | Type | Purpose |
|----------|------|---------|
| `data-engineer` | Agent | Pipeline idempotency, schema evolution, watermarks, exactly-once semantics |
| `notebook-review` | Skill | Reproducibility (Restart & Run All), no secrets in outputs, env pinning, output hygiene |
| `pipeline-safety` | Skill | Idempotency check, data-loss vectors, incremental filter boundaries, backfill ≥7 days. **Mandatory** on any write/delete/schema change |

**Boundary from core:** `data-engineer` ≠ `backend-developer` — pipeline idempotency and schema evolution rules differ from application service patterns.

---

#### `devops` — Infrastructure & deployment
**When to use:** Terraform/Pulumi IaC, Kubernetes, Helm, CI/CD pipelines, ArgoCD.

| Resource | Type | Purpose |
|----------|------|---------|
| `devops-engineer` | Agent | Rollback-first mindset, `prevent_destroy` on stateful resources, drift detection |
| `infra-safety` | Skill | Destructive ops audit, IAM least-privilege, no wildcards, public exposure, cost delta >$50/month flag. **Mandatory** before any infra apply |
| `deployment-checklist` | Skill | Pinned artifacts, readiness/liveness probes, rollback command documented, smoke test, 15-min post-deploy monitoring |

---

#### `ai-agent` — LLM & AI applications
**When to use:** LLM API integrations, RAG pipelines, tool-use agents, MCP servers.

| Resource | Type | Purpose |
|----------|------|---------|
| `ai-engineer` | Agent | Eval-before-prompt mandatory (C2+ tasks), pinned model IDs, token budget tracking, structured output schema always |
| `prompt-review` | Skill | Injection defence, hallucination surface, output-format robustness, guardrails, token efficiency, versioning |
| `eval-design` | Skill | Golden dataset (min 20 examples, 60/25/15 distribution), eval methods (exact/LLM-judge/reference), regression detection, pass/fail thresholds. **Mandatory** at Pillar 1 for C2+ LLM tasks |

---

#### `api` — API design & contracts
**When to use:** REST/gRPC/GraphQL services, OpenAPI specs, auth flows.

| Resource | Type | Purpose |
|----------|------|---------|
| `api-designer` | Agent | Contract-before-code, breaking-change detection mandatory, spec reviewed before any implementation |
| `contract-review` | Skill | Breaking change classification (additive = safe; rename/remove/type-change/add-required = breaking), status code coverage, auth on every endpoint, pagination, versioning |
| `auth-checklist` | Skill | Token lifecycle (≤15 min access tokens), OAuth2/OIDC (PKCE, state, nonce), JWT `alg` validation, scope minimisation, API-key hashing, session fixation prevention. **Mandatory** on any auth-touching task |

---

### Creating a custom pack

1. Copy `templates/PACK_template.md` and read the header comments.
2. Create the directory structure:
   ```
   packs/<your-pack-name>/
     PACK.md
     agents/<agent-name>.md   # use a namespaced name, e.g. "ml-ops-engineer"
     skills/<skill-name>/
       SKILL.md
   ```
3. Follow the same format as an existing pack (e.g. `packs/api/`).
4. Name pack agents distinctly — they must not collide with core agent filenames (`backend.md`, `frontend.md`, `common-infrastructure.md`, `qa.md`).
5. Install the new pack: `sh ~/.supervisor/setup.sh --pack=<your-pack-name>`

The Supervisor picks the right agent per task at Stage 1.5 — list your pack agent in the team design table alongside the core agents and specify when it applies.

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
| `templates/thinking_report_template.html` | `.claude/skills/thinking-report/SKILL.md` |

---

## Codebase Map (Structural Memory)

The `map-codebase` skill generates `memory/codebase-map.md` — a structural snapshot of the repo
that sub-agents can read instead of re-exploring the codebase from scratch on every task.

```
Skill({ skill: "map-codebase" })
```

Run it once at Stage 1 setup when joining an existing project. Re-run via `/map-codebase` after
any major refactor. No external dependencies — uses `find` and `git` only.

**What it produces (`memory/codebase-map.md`):**

| Section | Source | Purpose |
|---------|--------|---------|
| Directory Tree (depth 3) | `find`, gitignore-aware | Orients agents to where code lives |
| Entry Points | `find` by filename pattern (`main.*`, `index.*`, `app.*`, …) | Shows where execution begins |
| Blast-Radius Hotspots | `git log --name-only` commit frequency | Files changed most often = highest review risk when touched |

**How agents use it:**
- C2/C3 agents read it at startup to avoid redundant `grep`/`find` discovery chains
- At Stage 4, reviewers use the Hotspots section to bound review scope to the real blast radius
- The Supervisor annotates a `## Core Modules` section manually after generation — that intent layer is what the shell can't produce

**Design decision:** cold-tier only (never auto-injected into prompts). C0/C1 agents skip it entirely. Only agents that genuinely need structural context pay the read cost.

---

## Custom Skills

All skills live in `.claude/skills/<name>/SKILL.md` and are auto-discovered by Claude Code. Invoke any skill via `Skill({ skill: "<name>" })` or the `/name` slash command.

### Phase 0 — Strategy & Ideation

| Skill | When to use |
|---|---|
| `strategy` | Phase 0 before brainstorming: create/update `STRATEGY.md` — product north star covering target problem, approach, audience, and success metrics. Grounds all downstream ideation. |
| `ideate` | Stage 0.5a before brainstorming: generate 25–50 raw ideas across four divergent frames, adversarially filter to 5–7 survivors, let user select a direction. Prevents investing a deep brainstorm in a weak idea. |
| `brainstorming` | Stage 0.5b: deep divergent exploration of the selected direction — three architectural paths, adversarial review, scope boundaries. Upgraded with scope tiers (lightweight/standard/deep), one-question-per-turn dialogue, visual probe gate, and codebase claim verification. |

### Stage 0.5–2 — Planning & Grilling

| Skill | When to use |
|---|---|
| `grill-with-docs` | Stage 2: convergent grilling — sharpen terminology, lock intent, record ADRs before task breakdown. |
| `to-issues` | Stage 2: break the plan into tracer-bullet vertical-slice tasks (feeds KANBAN + TASK_GUIDEs). |
| `thinking-report` | After brainstorming, grilling, or planning locks a direction: render Decision box + Trade-Off Matrix + Assumptions list as HTML. |

### Stage 3 — Implementation

| Skill | When to use |
|---|---|
| `tdd` | Red-green-refactor implementation, one vertical slice at a time. |
| `migration-safety` | Mandatory go/no-go gate for any task touching DB schema/migrations — reversibility, backward-compat, zero-downtime. |
| `optimize` | When a concrete measurable metric (latency, coverage %, search relevance) needs systematic improvement. Defines a baseline → hypothesis backlog → parallel experiments → converges on best result. Optional — invoke only when a metric target exists. |
| `run` | Launch the app to observe behavior during development. |

### Stage 4 — Review

| Skill | When to use |
|---|---|
| `code-review` | Mandatory for every task (C1+). Project override of built-in: adds P0–P3 severity, 0/25/50/75/100 confidence anchors, cross-reviewer dedup + promotion, always-on + conditional reviewer personas, model tiering, and auto-applies safe P0/P1 fixes. |
| `security-review` | Task Risk Level is Medium or High — independent of complexity. |
| `blast-radius` | Risk Medium/High and task touches sensitive data (PII/PHI/credentials/payment): quantifies data-breach impact — inventory, exposure scoring, regulatory/financial estimate. |
| `html-report` | After each Stage 4 review skill: render findings as a self-contained HTML report. Args: `skill=<name> task=<TASK_ID> branch=<branch>`. |

### Stage 4 → 5 — PR Feedback Loop

| Skill | When to use |
|---|---|
| `resolve-pr-feedback` | After Stage 4 when a PR has open reviewer comments: triage validity, implement fixes, commit, reply with context. Full-PR mode (all threads) or targeted mode (single comment URL). |

### Stage 5 — Integration & Knowledge

| Skill | When to use |
|---|---|
| `verify` | Confirm the feature works end-to-end in the running app before merge. |
| `ship` | Post-merge: produce a deployment plan, rollback plan, and release notes; append a runbook entry. |
| `compound` | Post-Stage-5 after any non-trivial fix or discovery: document the problem→solution into `docs/solutions/[category]/`. Complements `learn` (session LRs) with structured, agent-discoverable artifacts. |

### Maintenance & Meta

| Skill | When to use |
|---|---|
| `compound-refresh` | On-demand: audit `docs/solutions/` against the live codebase. Classifies each doc Keep/Update/Consolidate/Replace/Delete; fixes drift; flags ambiguous cases for human review. |
| `learn` | Inline during/after any significant exchange: detect insights, corrections, or confirmed patterns → write to `memory/learning-records/`. Auto-fires on Supervisor detection; also `/learn`. |
| `wake` | **Mandatory first action every session**: reads git log, KANBAN, MEMORY.md, and active LRs; emits ≤50-line briefing. Also `/wake` for a live snapshot mid-session. |
| `map-codebase` | Stage 1 setup (and after major refactors): generate `memory/codebase-map.md` — directory tree, entry points, blast-radius hotspots. |
| `compact-memory` | On-demand: compact and prune the two-tier memory system when cold files are bloated or stale. Human-invoked, Supervisor executes. |
| `diagnose` | Stage 3 when something is broken/failing: disciplined reproduce → minimise → hypothesise → instrument → fix → regression-test loop. |
| `teach` | Auto-fires when user asks to write/create a new skill: consults `write-better-skill` and emits a ready-to-save SKILL.md draft. |
| `write-better-skill` | Craft reference for writing skills in this framework — invocation choice, leading words, completion criteria, failure modes. Consulted by `teach`; also audits existing skills. |
| `git-guardrails-claude-code` | Stage 1 one-time setup: install a PreToolUse hook blocking destructive git commands. |

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

The framework uses a **two-tier hot/cold memory** design to keep agents aligned across sessions, plus a **structural layer** for codebase topology.

```
memory/MEMORY.md          ← Hot tier (≤200 lines, always injected into spawn prompts)
memory/decisions.md       ← Cold tier: architectural + infrastructure decisions
memory/glossary.md        ← Cold tier: canonical biz-domain terms + core domain models
memory/learnings.md       ← Cold tier: specs clarifications, patterns, gotchas
memory/codebase-map.md    ← Structural tier: directory tree, entry points, blast-radius hotspots
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
| Structural snapshot of the codebase needed | `memory/codebase-map.md` (via `/map-codebase`) |

---

## Prerequisites

- `git`
- `curl`
- POSIX `sh`

---

## Options

| Variable / Flag | Default | Purpose |
|-----------------|---------|---------|
| `SUPERVISOR_PATH` | `~/.supervisor` | Override the central clone location |
| `GITHUB_USERNAME` | `thunderkds` | Install from a fork instead of the canonical repo |
| `--pack=<name>` | *(none)* | Install one or more domain packs (repeatable; see Packs section) |
| `--copy` | *(symlink)* | Copy instead of symlinking — files do not auto-update |

**Greenfield vs Brownfield** — chosen interactively during `setup.sh`. Brownfield uses `CLAUDE_LEGACY.md` which adds legacy-codebase guidance (risk hotspots, strangler-fig patterns).

**`--copy` mode** — copies instead of symlinking. Files do not auto-update; merge upstream changes manually from `~/.supervisor/<path>`.

**Git submodule alternative** — add as `.supervisor` submodule for pinned versioning; symlink resources manually; update with `git submodule update --remote`.
