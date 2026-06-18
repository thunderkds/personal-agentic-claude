# PACK.md — AI Agent
**Pack**: `ai-agent`
**Domain**: LLM applications, RAG pipelines, Claude/OpenAI tool-use, MCP servers, multi-agent systems
**Core framework version tested**: 1.14+

---

## When to use this pack

Select when the project builds on top of LLM APIs — chat interfaces, autonomous agents, RAG pipelines, tool-calling workflows, or MCP servers. The core agents can call an API; this pack adds the AI-specific mindset: token budget awareness, evaluation-driven development, prompt injection defence, and hallucination surface management.

**Select this pack when your project involves:**
- Claude / OpenAI / Gemini API integration as a core feature
- RAG (Retrieval-Augmented Generation) pipelines
- Autonomous agent loops or multi-agent orchestration
- MCP (Model Context Protocol) server development
- LLM-as-judge evaluation systems or golden dataset management

**Do NOT select if:** the project uses an LLM only for a minor utility feature (e.g. a single summarisation call) — the core `backend-developer` is sufficient.

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `ai-engineer` | Agent | LLM-app implementer: token budgets, evals, prompt safety, latency/quality trade-offs |
| `prompt-review` | Skill | Audit prompts for injection risk, hallucination surface, format fragility |
| `eval-design` | Skill | Design LLM evaluation rubrics: golden datasets, LLM-as-judge, regression detection |

**Boundary from core agents:**
- Core `backend-developer` handles: API routing, auth, data persistence, service orchestration
- This pack's `ai-engineer` handles: prompt engineering, context window management, LLM provider integration, evaluation strategy, output parsing robustness, safety/refusal handling

---

## Install

```sh
sh ~/.supervisor/setup.sh --pack ai-agent
```

---

## Agents installed

### `ai-engineer`
**File**: `packs/ai-agent/agents/ai-engineer.md`
Implements LLM-powered features with evaluation-driven development: define the eval before writing the prompt. Tracks token costs, latency, and quality regressions. Treats every prompt as a contract that must be tested, versioned, and reviewed.

---

## Skills installed

### `prompt-review`
**File**: `packs/ai-agent/skills/prompt-review/SKILL.md`
Reviews system and user prompts for injection risk, hallucination surface, output format fragility, missing guardrails, and token efficiency. Invoke before Stage 4 review of any task that adds or modifies prompts.

### `eval-design`
**File**: `packs/ai-agent/skills/eval-design/SKILL.md`
Designs an evaluation framework for an LLM feature: golden dataset structure, LLM-as-judge rubric, regression detection strategy, and pass/fail thresholds. Invoke at Pillar 1 (before implementation) for any C2+ LLM task.
