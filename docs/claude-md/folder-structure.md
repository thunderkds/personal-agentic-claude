# Folder Structure Requirements (Mandatory)

> Extracted from `CLAUDE.md` — full detail for the mandatory root-level folder structure. See `CLAUDE.md` for the pointer back to this file.

The project root **must** contain these folders:

1. `.claude/agents/` folder containing:
   - .claude/agents/general-agent-template.md
   - .claude/agents/common-infrastructure.md
   - .claude/agents/backend.md
   - .claude/agents/frontend.md
   - .claude/agents/qa.md

2. `.claude/skills/` folder containing custom project skills (Claude Code auto-discovers skills here):
   - .claude/skills/brainstorming/SKILL.md
   - *(pack skills are symlinked here when a pack is installed)*

3. `tasks/` folder
   Contains one TASK_GUIDE_Txxx.md file for **every** task after Stage 2 is approved.

4. `templates/` folder containing:
   - templates/PRD_template.md
   - templates/PROJECT_SPEC_template.md
   - templates/PROJECT_KANBAN_template.md
   - templates/TASK_GUIDE_template.md
   - templates/BRAINSTORMING_LOG_template.md
   - templates/SKILL_template.md
   - templates/ADR_template.md
   - templates/DDR_template.md
   - templates/RUNBOOK_template.md
   - templates/report_template.html
   - templates/thinking_report_template.html
   - templates/PACK_template.md

5. `packs/` folder (in the central clone) containing optional domain packs:
   - packs/mobile/ — Flutter, React Native, Swift, Kotlin
   - packs/data/ — Pipelines, notebooks, ETL, dbt
   - packs/devops/ — Terraform, K8s, CI/CD
   - packs/ai-agent/ — LLM apps, RAG, MCP servers
   - packs/api/ — REST/gRPC, OpenAPI, auth flows
   *(Each pack contains agents/ + skills/ + PACK.md. Installed via `setup.sh --pack=<name>`.)*

6. `memory/` folder containing:
   - memory/MEMORY.md (hot-tier index — ≤50,000 characters, referenced by path in every sub-agent spawn prompt and read by the agent)
   - memory/decisions.md (cold tier — architectural/infra decisions)
   - memory/glossary.md (cold tier — domain terms & domain models)
   - memory/learnings.md (cold tier — requirement clarifications, patterns, gotchas)
