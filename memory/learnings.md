# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

<!-- - 2026-06-12 — T001: clarification text (source: user answer / ADR link) -->

## Patterns

- 2026-06-18 — `html-report` skill: always use `<pre>` in the findings table for finding descriptions — do NOT manually HTML-escape. `<pre>` handles `<`, `>`, `&` in code snippets safely without extra processing. (source: grill session, edge case checklist)
- 2026-06-18 — Report filename convention: `reports/<skill>_<branch>_<YYYYMMDDTHHMMSS>.html` — skill name identifies type, branch identifies code under review, timestamp makes it sortable and collision-free across sessions. (source: grill session Q2)
- 2026-06-18 — `html-report` scoring rubric: Risk 0–30 → green/Healthy, 31–65 → yellow/Needs Attention, 66–100 → red/Critical. Overall badge is the worst of (Risk color, inverse-Quality color). Integer 0–100 for all three dimensions; bare number in slot (no `%` — hardcoded in template HTML). (source: SKILL.md)

- 2026-06-18 — `thinking-report` Trade-Off Matrix: always add `col-chosen` as a second class on both `<th>` and `<td>` cells in the chosen option column — omitting it on `<td>` leaves the column body unstyled (green header, white cells). (source: templates/thinking_report_template.html)
- 2026-06-18 — `thinking-report` trigger: auto-invoked by the Supervisor after Stage 0.5b direction approval and Stage 2 plan confirmation — not manually triggered per-task. Args: `session=<brainstorming|grilling|planning> task=<TASK_ID> branch=<branch>`. (source: CLAUDE.md Stage 0.5b + Stage 2)
- 2026-06-18 — Assumptions list tags: use `tag-resolved` (green) for confirmed answers, `tag-assumption` (amber) for unconfirmed givens, `tag-deferred` (purple) for intentionally postponed decisions. Minimum 2 items required by SKILL.md. (source: .claude/skills/thinking-report/SKILL.md)

- 2026-06-18 — Pack mandatory gates by domain: `mobile` → `ui-accessibility` before any UI Stage 4; `data` → `pipeline-safety` on any write/delete/schema change; `devops` → `infra-safety` before any infra apply; `ai-agent` → `eval-design` at Pillar 1 for C2+ LLM tasks; `api` → `contract-review` at Pillar 1 on any spec change. (source: pack agent SKILL.md files)
- 2026-06-18 — Pack agent boundary from core: `mobile-developer` ≠ `frontend-developer` (mobile lifecycle, app-store, platform APIs vs web DOM/CSS); `data-engineer` ≠ `backend-developer` (pipeline idempotency, schema evolution vs app services); `api-designer` ≠ `backend-developer` (contract-first, versioning, consumer-driven vs business logic). (source: PACK.md boundary sections)
- 2026-06-18 — `install_pack()` in setup.sh: iterates `packs/<name>/agents/*.md` → symlinks to `.claude/agents/`; iterates `packs/<name>/skills/*/` → symlinks to `.claude/skills/`. Uses same symlink/copy logic as `install_abs()`. (source: setup.sh)

## Patterns (learn skill)

- 2026-06-19 — `learn` materiality gate: write an LR only for user corrections, preference disclosures, confirmed non-obvious patterns, corrected misconceptions, or "surprising" moments. Never for greetings, activity logs, or terms already in glossary.md. (source: .claude/skills/learn/SKILL.md)
- 2026-06-19 — LR numbering must happen at write time (not at skill start) — prevents collision when two LRs are produced in one invocation. Scan `memory/learning-records/` for highest LR-NNNN immediately before each Write call. (source: .claude/skills/learn/SKILL.md Step 4)
- 2026-06-19 — `user` type LRs never route to cold files (decisions.md / glossary.md / learnings.md) — LR only. Routing a user preference to a cold file is a scope-creep bug. (source: .claude/skills/learn/SKILL.md routing table)
- 2026-06-19 — Skill promotion gate: output SKILL.md stub as a fenced code block and stop — never call Write tool automatically. User must save manually and register in CLAUDE.md. (source: .claude/skills/learn/SKILL.md Step 8)

## Patterns (wake skill)

- 2026-06-19 — `wake` graceful degradation is per-section, not per-skill — if KANBAN is missing, only Section 2 gets a fallback note; other sections still render from their live sources. (source: .claude/skills/wake/SKILL.md)
- 2026-06-19 — `wake` ≤50-line cap is enforced by a 4-step truncation sequence applied after composing all sections: (1) Section 1 → 5 commits, (2) Section 4 → 1 LR, (3) Section 3 → 5 entries, (4) append truncation note. (source: .claude/skills/wake/SKILL.md Step 6)
- 2026-06-19 — `wake` is strictly read-only — no Write, Edit, or Create step anywhere. Attempting to add a write step violates the out-of-scope constraint. (source: .claude/skills/wake/SKILL.md Karpathy Overrides)
- 2026-06-19 — Mid-session `/wake` invocation: prepend `"Note: invoked mid-session — this is a live snapshot, not a session-start state."` as first line of briefing. (source: .claude/skills/wake/SKILL.md edge case table)

## Patterns (teach + write-better-skill)

- 2026-06-19 — Split skill authoring into two skills: `write-better-skill` (pure reference, craft principles) + `teach` (orchestrator, emits draft). Matches mattpocock's own principle: split by invocation when another skill must reach the reference independently. (source: .claude/skills/teach/SKILL.md, .claude/skills/write-better-skill/SKILL.md)
- 2026-06-19 — `write-better-skill` must be model-invoked (no `disable-model-invocation`) so `teach` can reach it as an internal call. If it were user-invoked, no skill could reference it. (source: mattpocock invocation section — "other skills can reach it" requires model-invoked)
- 2026-06-19 — `teach` completion criterion is checklist-based: description has trigger phrasing (not identity prose), leading word identified or absence noted, every step has a checkable criterion, no-op test passed on all lines, registration checklist appended. (source: .claude/skills/teach/SKILL.md Step 5)

- 2026-06-22 — "Refactor to clean architecture" and similar structural refactors are NOT small tasks. Evaluate by blast radius (files touched, callers affected), not by how casual the request sounds. Start at C2/Medium Risk; require a TASK_GUIDE before any code. (source: LR-0001, user correction)
- 2026-06-22 — Pipeline bypass root causes confirmed by user: (1) perceived task smallness, (2) no TASK_GUIDE acting as a gate, (3) Supervisor role drift into implementation. Absence of a TASK_GUIDE is a hard blocker — no implementation without it. (source: LR-0002, user correction)
- 2026-06-22 — Agent files (.claude/agents/backend.md, frontend.md, qa.md) and CLAUDE_LEGACY.md all contained "Update memory/MEMORY.md if new patterns were learned" — contradicting the Memory Write Protocol. The correct instruction is "Flag learnings to the Supervisor — never write to memory/ directly." When syncing CLAUDE.md changes into agent files or CLAUDE_LEGACY.md, always verify no memory-write instructions creep in for sub-agents. (source: fix/agent-memory-write-protocol)

- 2026-07-01 — `.claude/agents/*.md` pin `model:` frontmatter to the generic alias `sonnet` (not a version-pinned ID like `claude-sonnet-4-6`), so it auto-resolves to the latest Sonnet (currently Sonnet 5) without an edit. Only hardcoded example model IDs in doc/skill text (e.g. `.claude/skills/html-report/SKILL.md`, `packs/ai-agent/agents/ai-engineer.md`) need manual bumping when a new model ships. (source: chore/update-model-refs-sonnet5)

## Gotchas

- 2026-06-18 — `{{RISK_SCORE}}` slot must be a bare integer (e.g. `72`), not `72%`. The `%` is hardcoded in `templates/report_template.html` and also used in `style="width:{{RISK_SCORE}}%"` — a `%` in the slot value would produce `width:72%%` and break the progress bar. (source: templates/report_template.html)
- 2026-07-16 — `.claude/hooks/pre_bash_block_unsafe_merge.py`'s Evidence-row check regex is `verify\s*\|[^|\n]+\|[^|\n]*pass` — the Check-column cell must contain the literal word `verify` with only whitespace before the next `|`. `TASK_GUIDE_template.md`'s own example row (`` `verify` skill — works in running app | ☐ pass / ☐ fail / ☐ N/A ``) does NOT match this regex because of the trailing "skill — works in running app" text between "verify" and the pipe — discovered live on T025 when `git merge` was blocked twice despite a filled, truthful Evidence row. Additionally the gate cross-checks `memory/event-trace/<task>.jsonl` for a real non-error Bash call whose command text matches `pytest|npm test|...|verify` — a text claim alone is never enough (fail-closed by design). Fix: write the Check cell as exactly `| verify | ☑ pass | ... |`, and if there's no running app, actually re-run the TASK_GUIDE's Verification Command for real (not just cite it) so a genuine trace record exists. (source: T025, tasks/TASK_GUIDE_T025.md, .claude/hooks/pre_bash_block_unsafe_merge.py)
