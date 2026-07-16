# BRAINSTORMING_LOG.md
**Generated**: 2026-07-16
**Task / Context**: New skill `craft-agent` — generates .claude/agents/*.md sub-agent definitions from a requirement (PROJECT_SPEC.md/PRD.md), used by Stage 1.5 and standalone.
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (moderate ambiguity, 2-3 viable directions, resolved via user Q&A)

---

## The Problem Space

Stage 1.5 ("Sub-Agent Architecture") already defaults to a base core team for every project — Common-Infrastructure-Agent, Backend-Implementer, Frontend-Implementer, QA-Automation-Agent (`.claude/agents/*.md`, always present). That default is not in question and `craft-agent` does not replace it. The gap is narrower: when a project's requirement implies a role *beyond* that base team (e.g. a domain-specific agent a pack doesn't cover), the Supervisor currently improvises that one extra agent.md ad hoc with no repeatable structure. This mirrors the gap `teach` closed for skills (`teach` drafts SKILL.md; nothing analogous exists for agent.md). The user wants a `craft-agent` skill that, **only when an additional role is actually needed**, reads the requirement and drafts that supplemental `.claude/agents/*.md` file(s) — fed by `/brainstorming` + `/grill-with-docs` output (sharpened, unambiguous requirement) rather than raw Phase 0 answers.

**Correction (2026-07-16, post-user feedback)**: `craft-agent` is optional and supplemental, never a required or default step. Stage 1.5 still starts from the base 4-agent team unconditionally; `craft-agent` is invoked only if that base team doesn't cover a role the requirement needs.

The user also pointed to https://www.mattpeters.co.uk/blog/01-agents-md-ai-context as a reference for what a well-formed agent-context file looks like — its core idea is that an agent definition should read as *durable, scoped context* (role boundaries, conventions, what NOT to touch) rather than a one-off task script. That matches this repo's existing `general-agent-template.md` inheritance pattern (backend.md/frontend.md/qa.md state only overrides), so no new structure is needed — it validates Option A below rather than changing it.

Non-negotiable constraints established via Q&A:
- **Whole-team mode**: one invocation proposes the full roster (not one role per call).
- **Draft-only, no direct writes**: emits fenced `.md` blocks + a registration checklist — matches `teach`'s convention, keeps the skill read-only, keeps a human save step in the loop.
- **Mandatory template inheritance**: every generated agent states "inherits from general-agent-template.md" and lists only overrides — matches backend.md/frontend.md/qa.md today.

---

## Questions for the User

None outstanding — invocation grain, write mode, and template inheritance were resolved via `AskUserQuestion` before this log was written.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | The Simple Path | New `craft-agent` skill, structurally cloned from `teach`, reused Stage 1.5 wiring | Low | ~90 lines (SKILL.md only) | Low | ✅ Yes |
| B | The Scalable Path | `craft-agent` skill + shared `agent-craft-lib` reference doc consumed by both `craft-agent` and `teach` for common drafting rules | Medium | ~90 + ~40 lines | Low-Medium | |
| C | The Minimalist Path | Extend `teach` itself to detect "agent" vs "skill" intent and branch internally | Low | ~30 lines added to teach | Medium | |

### Option A — The Simple Path
**Approach**: Net-new `.claude/skills/craft-agent/SKILL.md`, same shape as `teach`: clarify intent → resolve team size/roles from PROJECT_SPEC.md/PRD.md → draft N agent.md blocks (each stating template inheritance + overrides only) → emit fenced blocks + registration checklist. CLAUDE.md Stage 1.5 gets one line pointing to it.
**Pros**: Fully consistent with the existing `teach` pattern the user already trusts; smallest surface area; no new abstractions; easy to review in one pass.
**Cons**: Some drafting logic (tone rules, no-op test, leading-word concept) is duplicated conceptually from `teach`/`write-better-skill` rather than shared.
**Why it might fail**: If agent-drafting rules diverge from skill-drafting rules over time, the duplication could drift out of sync — but there's no evidence yet that they will (agents and skills are structurally different artifacts).

### Option B — The Scalable Path
**Approach**: Same as A, but factor out shared "drafting craft" (no-op test, ask-vs-guess gating, registration-checklist shape) into a `write-better-skill`-style reference doc both `teach` and `craft-agent` consult.
**Pros**: DRY; a future third "craft-X" skill (e.g. craft-template) reuses the same base.
**Cons**: Speculative — no third craft-skill exists or is requested; adds an indirection layer for a problem that doesn't exist yet.
**Why it might fail**: Violates Simplicity First / the 50% rule — solving for a hypothetical future need the user never asked for.

### Option C — The Minimalist Path
**Approach**: Add a branch inside `teach`'s Step 1 ("is this a skill or an agent intent?") and reuse its workflow for both artifact types.
**Pros**: Zero new files.
**Cons**: `teach`'s description/trigger phrasing is skill-specific ("write, create, design a new skill") — overloading it blurs its trigger for model-invocation matching, and its Registration checklist/output shape differs (SKILL.md path+CLAUDE.md skill table vs agent.md path+CLAUDE.md agent table).
**Why it might fail**: Two artifact types crammed into one skill produces exactly the kind of unfocused trigger `write-better-skill` warns against — degrades `teach`'s own reliability.

---

## 50% Rule Check

Option A is already near-minimal (~90 lines, one file, no new abstractions). The only further cut considered — skipping the registration checklist — was rejected: it's the one thing preventing silent, unreviewed agent-file writes, which the user explicitly required (draft-only mode).

---

## Recommended Path

**Option A — The Simple Path**

Cleanest fit for stated constraints (whole-team, draft-only, mandatory inheritance), structurally identical to a pattern already proven in this repo (`teach`), and touches only new files plus one line in CLAUDE.md's skill table + Stage 1.5 section.

---

## Surgical Scope

Files that **should** be touched:
- `.claude/skills/craft-agent/SKILL.md` — new skill file (created)
- `CLAUDE.md` — add `craft-agent` row to the custom-skill table; update Stage 1.5 to invoke it
- `memory/MEMORY.md` — one-line decision entry after merge

Files that **must not** be touched:
- `.claude/skills/teach/SKILL.md` — stays skill-only, not overloaded (rejects Option C)
- `.claude/agents/*.md` — craft-agent drafts blocks for the *user* to save; it never writes these directly
- `templates/PROJECT_KANBAN_template.md`, `templates/TASK_GUIDE_template.md` — unrelated to this task

---

## Edge Case Checklist for TASK_GUIDE

- [ ] PROJECT_SPEC.md / PRD.md missing or not yet locked — craft-agent must refuse to draft and point back to Phase 0/Stage 2, not guess a team
- [ ] Requirement implies a role that duplicates an existing default core agent (Common-Infra/Backend/Frontend/QA) — craft-agent must reuse the existing name, not draft a near-duplicate
- [ ] Requirement is too vague to bound a team (no clear domain boundaries) — ask one clarifying question per the Ask-vs-Guess rule, don't fabricate roles
- [ ] Draft exceeds reasonable length per agent (no line cap defined for agent.md) — mirror teach's 80-line skill cap as a per-agent-file guideline
- [ ] Generated agent name collides with an existing `.claude/agents/<name>.md` on disk — flag the collision explicitly in the registration checklist rather than silently proposing an overwrite

---

## Next Actions

1. Run `grill-with-docs` to sharpen the exact requirement wording/terminology for `craft-agent` before Stage 2 breakdown (per user's explicit /grill-with-docs mention).
2. Proceed to Stage 2 (`/plan`): create/update PROJECT_SPEC.md + PROJECT_KANBAN.md, assign Complexity/Risk/Priority, generate TASK_GUIDE_Txxx.md for this work (Hard-Stop Gate 1 — no code without a guide).
3. Draft `.claude/skills/craft-agent/SKILL.md` structurally cloned from `teach`, incorporating the Edge Case Checklist above.
4. Update CLAUDE.md's custom-skill table and Stage 1.5 section to reference `craft-agent`.

---

## User Selection

> **Approved direction**: Option A — The Simple Path (corrected: `craft-agent` is optional/supplemental to the existing base 4-agent team, never a required or default step)
> Approved by user on 2026-07-16.
