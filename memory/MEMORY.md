# MEMORY.md — Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 200 lines. One-line summaries + links to cold files.
> Injected in full into every sub-agent spawn prompt.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary (≤150 chars) -->

### Decisions
- [CLAUDE_LEGACY.md sync policy](decisions.md) — mirror new skills + session-startup gates + Hard-Stop Gates from CLAUDE.md into CLAUDE_LEGACY.md on each addition; bump version
- [Hard-stop gates in Permanent Rules](decisions.md) — 4 Supervisor self-checks: no TASK_GUIDE=no work; refactor/QA floors at C2/Medium; KANBAN current before session ends; one project per KANBAN
- [Codebase Map](codebase-map.md) — structural snapshot (tree, entry points, hotspots) in memory/codebase-map.md; cold-tier; C2/C3 agents read it; refresh via /map-codebase
- [LLM-as-Renderer for HTML reports](decisions.md) — html-report skill renders Stage 4 output inline; no shell post-processor; built-ins (code-review, security-review) can't be modified
- [reports/ is local-only](decisions.md) — generated HTML reports excluded from git; local browser viewing only
- [thinking-report is separate from html-report](decisions.md) — Stage 0.5–2 decision reasoning vs Stage 4 review findings; different templates, different triggers
- [thinking-report MVP: matrix only, no flowchart](decisions.md) — CSS flowchart deferred; matrix answers "why this option?" reliably with less implementation risk
- [Dark neon theme on HTML report templates](decisions.md) — both templates use #0a0a12 bg + cyan/green/purple/amber neon palette with glow effects; matches user's dashboard aesthetic preference
- [learn skill: Learning Record System](decisions.md) — LR files in memory/learning-records/; supersession archive; skill promotion on ≥2 LRs with user approval; closes passive-memory gap
- [teach + write-better-skill: two-skill craft system](decisions.md) — teach auto-fires on skill-writing requests → emits draft SKILL.md; write-better-skill is the consulted craft reference (mattpocock port)
- [wake skill: mandatory cold-start briefing](decisions.md) — reads git/KANBAN/MEMORY/LRs live; ≤50-line output; hard gate before first Supervisor response each session

### Patterns & Gotchas
- [Agent files must not tell sub-agents to write memory](learnings.md) — backend/frontend/qa.md + CLAUDE_LEGACY.md had "Update MEMORY.md" — fixed to "flag to Supervisor"; watch for this on every sync
- [html-report findings use `<pre>`](learnings.md) — never manually HTML-escape finding text; wrap in `<pre>` to handle `<`, `>`, `&` safely
- [Report filename: skill_branch_timestamp.html](learnings.md) — `reports/<skill>_<branch>_<YYYYMMDDTHHMMSS>.html`; sortable, collision-free
- [html-report scoring rubric](learnings.md) — Risk 0–30=green, 31–65=yellow, 66–100=red; all dimension slots are bare integers (no `%`)
- [{{RISK_SCORE}} must be bare integer](learnings.md) — no `%` in slot value; `%` is hardcoded in template HTML and CSS width attribute

### Patterns & Gotchas (thinking-report)
- [col-chosen on both th and td](learnings.md) — must apply to header AND body cells in chosen column; omitting on td leaves body unstyled
- [thinking-report trigger](learnings.md) — auto after Stage 0.5b direction approval and Stage 2 confirmation; args: session=<type> task=<ID> branch=<branch>
- [Assumptions tag classes](learnings.md) — tag-resolved (green) / tag-assumption (amber) / tag-deferred (purple); min 2 items required

### Decisions (Packs)
- [Packs are additive-only, core unchanged](decisions.md) — pack agents/skills symlink alongside core; never replace core resources
- [Pack install: --pack=<name> flag or interactive prompt](decisions.md) — no packs in non-interactive mode by default; users opt in explicitly
- [Pack structure: agents/ + skills/ + PACK.md](decisions.md) — pack agents use namespaced names (e.g. mobile-developer) to avoid core collisions

### Patterns (Packs)
- [Pack mandatory gates by domain](learnings.md) — mobile→ui-accessibility; data→pipeline-safety; devops→infra-safety; ai-agent→eval-design; api→contract-review
- [Pack agent boundary from core](learnings.md) — mobile≠frontend (lifecycle/app-store); data≠backend (pipeline idempotency); api≠backend (contract-first)
- [install_pack() in setup.sh](learnings.md) — iterates agents/*.md and skills/*/ from pack dir; symlinks into .claude/agents/ and .claude/skills/

### Patterns (learn skill)
- [learn materiality gate](learnings.md) — write LR only for corrections, preference disclosures, confirmed patterns, corrected misconceptions; never for greetings or activity logs
- [LR numbering at write time](learnings.md) — scan directory for highest LR-NNNN immediately before each Write call; prevents collision in multi-LR invocations
- [user type → LR only](learnings.md) — user-preference insights never route to cold files; scope-creep guard in routing table
- [skill promotion: code block only](learnings.md) — never auto-save SKILL.md stub; output fenced block and stop; user saves + registers manually

### Decisions (New Skills — 2026-06-24 batch)
- [strategy skill](decisions.md) — STRATEGY.md north star (problem/approach/audience/metrics); grounds ideate + brainstorming; distinct from PRD
- [ideate skill](decisions.md) — pre-brainstorm divergent filter; 25–50 raw ideas → adversarial filter → 5–7 survivors; prevents deep brainstorm on weak direction
- [resolve-pr-feedback skill](decisions.md) — post-Stage-4 PR thread resolution; triage validity → fix → commit → reply; full-PR or single-thread mode
- [compound skill](decisions.md) — post-Stage-5 problem→solution capture to docs/solutions/; complements learn (LRs) with searchable structured artifacts
- [compound-refresh skill](decisions.md) — on-demand audit of docs/solutions/; Keep/Update/Consolidate/Replace/Delete classification; fixes documentation drift
- [optimize skill](decisions.md) — optional metric-driven iteration loop; baseline → hypothesis backlog → experiments → converge; hard + judge metrics
- [code-review project override](decisions.md) — .claude/skills/code-review/SKILL.md overrides built-in; adds P0–P3 severity, confidence anchors, dedup+promotion, conditional personas, model tiering
- [brainstorming upgrade](decisions.md) — added scope tiers (lightweight/standard/deep), one-question-per-turn gate, visual probe gate, claim verification before doc-write

### Learning Records
<!-- One-liner per active LR: - [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — summary -->
<!-- Superseded LRs: ~~old text~~ → see LR-NNNN -->

### Glossary
- [Report / Report Slot / Scoring Dimension / Report Session](glossary.md) — canonical terms for the html-report skill and Stage 4 reporting system
- [Thinking Report / Trade-Off Matrix / Thinking Session](glossary.md) — canonical terms for the thinking-report skill and Stage 0.5–2 decision system
- [Pack / Core framework / Pack agent](glossary.md) — canonical terms for the optional pack system

