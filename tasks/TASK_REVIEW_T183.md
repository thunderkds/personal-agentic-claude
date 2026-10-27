# TASK_REVIEW — T183: Subagent definitions follow the "Creating a subagent" lesson

> Sibling of `tasks/TASK_GUIDE_T183.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_agent_frontmatter.py` (new, AC 1/2/3/5: 31 tests), `tests/test_site_content.py` (+3, AC 8). RED 32 failed/2 passed on 31450d4 (BEFORE below); AC 8 RED `2 failed, 64 passed` at a8e12de; GREEN 2026-10-27T14:12:44Z: `97 passed in 0.11s`. Mutants (missing color, bad colour, template back in agents/, duplicate name, block-scalar, 'proactively', site colour/trigger drift) each fail — pass |
| Verification command run | ☑ pass | 2026-10-27T14:12:44Z (Supervisor, wt-t183 @ f0a762f): `ls agents/` → `backend.md common-infrastructure.md frontend.md qa.md`; frontmatter+site tests `97 passed`; full suite `1481 passed, 25 subtests passed in 34.98s`; `scripts/validate.sh` rc=0 — pass |
| Negative cases hold | ☑ pass | `claude -p --agent general-agent-template` in wt-t183 → `--agent 'general-agent-template' not found. Available agents: backend-developer, claude, common-infrastructure, Explore, frontend-developer, general-purpose, Plan, qa-expert, statusline-setup` — pass |
| verify | ☑ pass | /verify run by user 2026-10-27, verdict PASS: fresh headless `claude -p` (2.1.311) on main lists `general-agent-template`; on wt-t183 it is gone and the 4 roles show 'Use when …' descriptions; `--agent backend-developer` session reads `templates/general-agent-template.md` (exists, `## Base Rules (Inherited by All Sub-Agents)`). AC 8 (site) added after /verify; checked by headless Chrome render (UI rows) — pass. `color` in the interactive UI not observable headless: check after restart |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review on `31450d4..HEAD` only (37 files; lane_check `EXCEEDS (files 36 > 14)` — expected, AC 3 enumerates every live reference). 0 P0/P1; P2: test does not enforce ≥2 trigger scenarios / scope facts (all 9 descriptions comply today). security-review scoped to the same diff (default scope main..github/main pulled T169–T176): no findings — pass |
| Full smoke suite still green (no regression) | ☑ pass | base 31450d4: `1447 passed, 25 subtests passed`; branch: `1481 passed, 25 subtests passed` (+31 frontmatter, +3 site). `scripts/test-claude-md-refs.sh` rc=1 on BOTH base and branch (pre-existing, not in suite) — pass |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | headless Chrome render of `#agent-roles` (/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/34b7996b-e6c8-4e62-8435-1d57d5296ca1/scratchpad/roles-1280.png, roles-768.png, roles-375.png): 4 role cards show swatch + colour name + 'Use when' line; template card unchanged, no swatch; LLM-vision verdict: matches AC 8 — pass |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | purple/green reuse `var(--purple)`/`var(--green)`; orange `#ff8c42`, blue `#4d8dff` are new literals (site has no orange/blue token); trigger text uses `var(--text)`, .9rem; no inline styles — pass |
| **UI: Responsiveness at target viewports** | ☑ pass | 375 / 768 / 1280 px rendered: text wraps inside cards, swatch stays inline with subtype, no horizontal overflow — pass |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**:

Captured 2026-10-27T11:05:43Z (UTC) on branch `feat/t183-subagent-frontmatter` at 31450d4, before any implementation commit, by common-infrastructure.

```text
$ date -u; ls agents/
2026-10-27T11:05:43Z
backend.md
common-infrastructure.md
frontend.md
general-agent-template.md
qa.md

$ python3 -m pytest tests/test_agent_frontmatter.py -q
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/backend.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/common-infrastructure.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/frontend.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/general-agent-template.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/qa.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/ai-agent/agents/ai-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/api/agents/api-designer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/data/agents/data-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/devops/agents/devops-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/mobile/agents/mobile-developer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/backend.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/common-infrastructure.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/frontend.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/general-agent-template.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/qa.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/ai-agent/agents/ai-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/api/agents/api-designer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/data/agents/data-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/devops/agents/devops-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/mobile/agents/mobile-developer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/backend.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/common-infrastructure.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/frontend.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/general-agent-template.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/qa.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/ai-agent/agents/ai-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/api/agents/api-designer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/data/agents/data-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/devops/agents/devops-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/mobile/agents/mobile-developer.md]
FAILED tests/test_agent_frontmatter.py::test_base_team_colors - AssertionErro...
FAILED tests/test_agent_frontmatter.py::test_template_lives_outside_agents_dir
32 failed, 2 passed in 0.11s
```

Frontmatter of the 4 base agents (verbatim, before the change) — no `color:`, descriptions say what the role *is*, not when to delegate:

```text
== agents/common-infrastructure.md
---
name: common-infrastructure
description: Environment and shared-config specialist. Handles worktree setup, migrations, shared services, and anything that cuts across backend and frontend. Always runs first before implementers start.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
== agents/backend.md
---
name: backend-developer
description: "The project's core backend engineering role — server-side APIs, services, business logic, and data-access layers. Builds production-ready code in the project's stack, scoped to a single TASK_GUIDE and built test-first, while actively guarding against over-engineering (Simplicity First)."
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
== agents/frontend.md
---
name: frontend-developer
description: "The project's core frontend engineering role — UI components, client-side state, interactions, and accessibility. Builds performant, accessible interfaces in the project's framework, scoped to a single TASK_GUIDE and built test-first, while guarding against over-engineering (Simplicity First)."
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
== agents/qa.md
---
name: qa-expert
description: "The project's quality and evaluation role — owns the smoke suite, regression safety, and independent verification of acceptance criteria. Acts as the Pillar 3 oracle: confirms a task actually works, with evidence, in a context separate from whoever implemented it."
tools: Read, Write, Edit, Grep, Glob, Bash
model: sonnet
---
```


**AFTER**: 2026-10-27T14:12:44Z, wt-t183 @ f0a762f

```text
$ ls agents/
backend.md  common-infrastructure.md  frontend.md  qa.md
$ python3 -m pytest tests/test_agent_frontmatter.py tests/test_site_content.py -q
97 passed in 0.11s
$ claude -p --agent general-agent-template 'Say OK.'
--agent 'general-agent-template' not found. Available agents: backend-developer, claude, common-infrastructure, Explore, frontend-developer, general-purpose, Plan, qa-expert, statusline-setup
```

New frontmatter (backend.md): `description: "Use when a TASK_GUIDE assigns server-side work — a new API endpoint, a service or business-logic change, or a data-access fix. …"` / `color: blue`.

**DELTA**: Claude Code no longer offers the base template as a spawnable agent; each role agent has a UI colour and a description that says when to delegate to it, the site shows both, and a test keeps every agent file that way.

**WITNESS**: Supervisor (not the implementing agent), 2026-10-27T14:12:44Z, Bash calls attributed to T183 via `.claude/hooks/.state/active_task`; /verify run by the user 2026-10-27.
