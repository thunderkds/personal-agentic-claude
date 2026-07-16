# TASK_GUIDE — T025: craft-agent skill (optional, supplemental agent-drafting) + Stage 1.5 wiring
**Date**: 2026-07-16
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)
1. Read `PROJECT_SPEC.md` (glossary now includes **Base team**, **Agent Draft**, **craft-agent** — added this session)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `.claude/skills/teach/SKILL.md` in full — `craft-agent` is a structural clone of it (draft-only output, registration checklist, Ask-vs-Guess clarify step)
6. Read `.claude/skills/write-better-skill/SKILL.md` for craft conventions (leading word, no-op test, information hierarchy)
7. Read `CLAUDE.md` Stage 1.5 section and the "Skills vs Agents" custom-skill table — both need a small edit

---

## Requirement (Pillar 1 — Adapt the requirement)

User request: "the skill that can generate the agent following the requirement" — a new skill, analogous to `teach` (which drafts SKILL.md), that drafts `.claude/agents/*.md` sub-agent definitions from a requirement. Explored via `Skill({ skill: "brainstorming" })` (`BRAINSTORMING_LOG.md`, 2026-07-16, Option A approved) and sharpened via `Skill({ skill: "grill-with-docs", args: "mode=requirement" })` → switched to terminology mode (no `PRD.md` exists for this internal framework task; same precedent as T023).

**Restated intent**: `craft-agent` is an **optional, supplemental** skill — the **base team** (Common-Infrastructure-Agent, Backend-Implementer, Frontend-Implementer, QA-Automation-Agent) is always the Stage 1.5 starting point for every project, unconditionally. `craft-agent` is invoked only when a project's requirement implies a role the base team doesn't cover. When invoked, it reads `PROJECT_SPEC.md`/`PRD.md` once and proposes the **whole supplemental roster** in one call (not one role per invocation), emitting fenced **Agent Draft** blocks + a registration checklist — it never writes `.claude/agents/*.md` directly. Every Agent Draft states inheritance from `general-agent-template.md` and lists only overrides (matching backend.md/frontend.md/qa.md today).

**Out of scope**:
- Does not replace or modify the base team's default inclusion in Stage 1.5 — that stays unconditional.
- Does not write files to `.claude/agents/` directly — draft-only, mirrors `teach`.
- Does not spawn agents or call `Agent()` — this is a drafting skill only.
- Does not build a shared "craft-lib" abstraction with `teach` (BRAINSTORMING_LOG Option B, rejected — no second consumer exists yet).

**Requirement Refs**: none (internal framework tooling, no `PRD.md`).

### Requirement Fidelity Gate (sign off BEFORE implementation)
- [x] Restated intent confirmed to match the request (Supervisor, informed by approved brainstorming Option A + user's correction that craft-agent must be optional/supplemental, not required)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (Base team / Agent Draft / craft-agent added via `grill-with-docs` this session)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `Skill({ skill: "craft-agent" })` — invoked from `CLAUDE.md` Stage 1.5 (conditionally, only when the base team doesn't cover a needed role) and standalone on user request (mirrors `/teach`).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/skills/craft-agent/SKILL.md` exists, is user- and model-invokable, and its `description` triggers on "need an additional/new agent role" — not on every new project | Optional/supplemental framing |
| 2 | Skill's workflow requires `PROJECT_SPEC.md`/`PRD.md` to be locked before drafting; refuses and points back to Phase 0/Stage 2 if missing | Edge case checklist item 1 |
| 3 | Skill drafts the **whole supplemental roster** in one invocation (not one role per call) | Whole-team mode Q&A decision |
| 4 | Skill output is a fenced Agent Draft block per role + a Registration checklist (save path, CLAUDE.md agent table row, MEMORY.md one-liner) — no direct `Write` to `.claude/agents/` | Draft-only mode Q&A decision |
| 5 | Every drafted agent explicitly states "inherits from general-agent-template.md" and lists only overrides | Mandatory inheritance Q&A decision |
| 6 | Skill checks the requirement's implied roles against the base team and existing `.claude/agents/*.md` filenames; reuses an existing name instead of drafting a near-duplicate, and flags any filename collision instead of silently overwriting | Edge case checklist items 2 & 5 |
| 7 | `CLAUDE.md` Stage 1.5 states the base team is unconditional and `craft-agent` is invoked only for roles beyond it (not a required step every pass) | User's explicit correction this session |
| 8 | `CLAUDE.md` "Skills vs Agents" custom-skill table has a new row for `craft-agent` | Registration parity with other skills |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `PROJECT_SPEC.md` exists with a requirement implying one extra role (e.g. a domain-specific agent not covered by base team) | Skill drafts one Agent Draft block, inheriting from general-agent-template.md, plus a Registration checklist | Manual dry-run walkthrough (no runtime harness in this repo — same precedent as T023) |
| 2 | `PROJECT_SPEC.md`/`PRD.md` missing | Skill refuses to draft, points back to Phase 0/Stage 2 | Manual dry-run walkthrough |
| 3 | Requirement implies a role that duplicates an existing base-team or already-drafted agent name | Skill reuses the existing name / flags the collision, does not silently draft a duplicate | Manual dry-run walkthrough |
| 4 | `CLAUDE.md` Stage 1.5 read end-to-end | Base team wording is unconditional; craft-agent is conditional/optional, not a required step | Manual read-through + grep for "base team" / "craft-agent" |

### Verification Command (exact, runnable)

```bash
# Structural checks — no test harness exists in this repo (same precedent as T018/T023)
test -f .claude/skills/craft-agent/SKILL.md && echo "skill file exists"
grep -n "craft-agent" CLAUDE.md
grep -n "base team\|Base team" CLAUDE.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | No automated test suite exists in this doc/skill-framework repo (confirmed precedent: T018, T023). Evidence = manual dry-run walkthroughs pasted below, per those tasks' established substitute. |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | (missing PROJECT_SPEC.md case, duplicate-role case) |
| `verify` skill — works in running app | ☐ N/A | No running app — this is a Skill/CLAUDE.md doc change, not runtime product code |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | Scope: `.claude/skills/craft-agent/SKILL.md` (new), `CLAUDE.md` (2 edits), `memory/MEMORY.md` (1 line, post-merge) |
| Full smoke suite still green (no regression) | ☐ N/A | No smoke suite in this repo |
| UI rows | ☐ N/A | Not a UI task — no UI/Design AC section below |

---

## Approach

Structurally clone `.claude/skills/teach/SKILL.md`'s shape (Role → Karpathy overrides → numbered Workflow with a checkable completion criterion per step → Communication Protocol), adapted for whole-team draft output instead of single-skill output:

1. **Clarify intent** — if no `PROJECT_SPEC.md`/`PRD.md` is locked, or the implied role set is unbounded, ask one question (Ask-vs-Guess), don't fabricate.
2. **Enumerate supplemental roles** — cross-check requirement against the base team + existing `.claude/agents/*.md`; only roles genuinely uncovered get drafted.
3. **Draft each Agent Draft** — name, role, required skills, override-only rules (state template inheritance), CLI spawn command, `.claude/agents/` reference — apply teach's ~80-line-per-file guideline analog.
4. **Emit** — one fenced block per Agent Draft + a Registration checklist (save path, CLAUDE.md agent table row, MEMORY.md one-liner, filename-collision flag if any).

Then two small `CLAUDE.md` edits: (a) custom-skill table row, (b) Stage 1.5 section — state base team is unconditional, `craft-agent` fires only for uncovered roles.

---

## Edge Case Checklist

- [ ] `PROJECT_SPEC.md` / `PRD.md` missing or not locked — refuse to draft, point back to Phase 0/Stage 2
- [ ] Requirement implies a role duplicating an existing base-team agent — reuse the existing name, don't draft a near-duplicate
- [ ] Requirement too vague to bound a team — ask one clarifying question, don't fabricate roles
- [ ] Draft exceeds a reasonable per-agent length — mirror teach's 80-line cap as a guideline
- [ ] Generated agent name collides with an existing `.claude/agents/<name>.md` on disk — flag explicitly in the Registration checklist, never silently overwrite

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/craft-agent/SKILL.md` | New skill file, cloned from `teach`'s shape |
| `CLAUDE.md` | Add `craft-agent` row to custom-skill table; update Stage 1.5 to state base team is unconditional, craft-agent conditional |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/teach/SKILL.md` | Stays skill-only per rejected Option C — not overloaded with agent-drafting logic |
| `.claude/agents/*.md` | craft-agent drafts blocks for the user to save; never writes these directly |
| `templates/PROJECT_KANBAN_template.md`, `templates/TASK_GUIDE_template.md` | Unrelated to this task |

---

## Test Plan

Manual dry-run walkthroughs (no automated test harness exists in this repo, per T018/T023 precedent):
1. Dry-run against a synthetic requirement implying one extra role beyond the base team — confirm single Agent Draft + Registration checklist output, correct inheritance statement.
2. Dry-run with no `PROJECT_SPEC.md` present — confirm refusal + pointer to Phase 0/Stage 2.
3. Dry-run with a requirement that only needs base-team roles — confirm the skill reports "no supplemental role needed," doesn't force a draft.
4. Dry-run with a role name colliding with an existing `.claude/agents/*.md` file — confirm collision flagged in the Registration checklist.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Risk: Low)
- [ ] Lint passes — N/A (Markdown only)
- [ ] Tests written AND pass — manual dry-run walkthroughs pasted into Evidence table (Hard-Stop Gate 5, per T018/T023 substitute precedent)
- [ ] `Skill({ skill: "verify" })` run — N/A, no running app surface (doc/skill change)
- [ ] `memory/MEMORY.md` updated (craft-agent decision + one-liner)
- [ ] Supervisor notified: task ready for Stage 4 review
