# TASK_GUIDE — T009: Core `learn` SKILL.md — detection, LR writing, supersession, skill promotion
**Date**: 2026-06-19
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `templates/LEARNING-RECORD-FORMAT.md` (created by T008 — must be complete first)
6. Read `templates/SKILL_template.md`
7. Read `.claude/skills/compact-memory/SKILL.md` for prior art on memory-writing conventions
8. Apply C2 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**Depends on**: T008 (folder + format spec must exist)

---

## Requirement (Pillar 1 — Adapt the requirement)

Write `.claude/skills/learn/SKILL.md` — the Supervisor's "Reflect & Encode" reflex skill. When invoked (by the Supervisor automatically after a significant exchange, or by the user via `/learn`), it:

1. **Detects** non-obvious insights in the recent conversation context using a strict materiality gate.
2. **Classifies** each insight as `project` (domain pattern, gotcha, spec clarification) or `user` (preference, knowledge level, working style).
3. **Deduplicates** — greps existing cold files and all LR bodies before writing.
4. **Writes** one or more `memory/learning-records/LR-NNNN-slug.md` files following `templates/LEARNING-RECORD-FORMAT.md`.
5. **Supersedes** any existing LR that the new insight contradicts — marks it `superseded by LR-NNNN` in place.
6. **Updates** `memory/MEMORY.md` hot tier — adds one-liner for new LRs, removes/strikes one-liners for superseded LRs.
7. **Promotes** — if ≥2 existing LRs share the same underlying pattern, surfaces a candidate skill prompt to the user and (on approval) drafts a `SKILL.md` stub using `templates/SKILL_template.md`.

**Restated intent**: The `learn` skill transforms real-time conversation insights into durable, traceable learning records that future sessions can rely on — replacing the current gap where insights evaporate between git pushes.

**Out of scope**:
- Actually auto-saving the SKILL.md stub without user approval
- Rewriting or restructuring existing cold files (`learnings.md`, `decisions.md`, `glossary.md`)
- Registering the skill in `CLAUDE.md` or `README.md` (that's T010)
- Compacting or pruning existing LRs (that belongs to `compact-memory`)

**Requirement Refs**:
- Brainstorming decision 2026-06-19: Option B — Learning Record System with built-in skill promotion
- Brainstorming decision 2026-06-19: trigger = both Supervisor-auto + user `/learn`
- Brainstorming decision 2026-06-19: scope = project + user learnings, same LR format
- Brainstorming decision 2026-06-19: supersession = archive with `superseded by LR-NNNN`, never delete
- Brainstorming decision 2026-06-19: skill promotion = draft stub on ≥2 recurring LRs, user-approved

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `BRAINSTORMING_LOG.md` and `memory/MEMORY.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] T008 is complete — `memory/learning-records/` and `templates/LEARNING-RECORD-FORMAT.md` exist

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/skills/learn/SKILL.md` exists and frontmatter `name: learn` matches the folder | Skill registration requirement |
| 2 | SKILL.md documents a **materiality gate** step that explicitly lists what does NOT qualify as an LR (e.g. trivial exchanges, terms already in glossary, activity logs) | Noise gate requirement |
| 3 | SKILL.md documents the **classification step**: route `project` insights to project LRs, `user` insights to user LRs — both using `templates/LEARNING-RECORD-FORMAT.md` | Scope requirement |
| 4 | SKILL.md documents the **deduplication step**: grep existing LR bodies + cold files before writing | Duplication edge case |
| 5 | SKILL.md documents the **supersession step**: how to detect contradictions, update old LR status in-place, and remove the old one-liner from `MEMORY.md` | Supersession requirement |
| 6 | SKILL.md documents the **numbering step**: scan `memory/learning-records/` for highest LR number at write time (not at skill start) | Numbering collision edge case |
| 7 | SKILL.md documents the **MEMORY.md update step**: add one-liner under `### Learning Records` for each new LR; remove/strike one-liner for each superseded LR; check line count stays ≤200 | Hot tier overflow edge case |
| 8 | SKILL.md documents the **skill promotion step**: detect ≥2 LRs sharing a pattern → surface a candidate skill name + description to the user → on approval, draft a stub using `templates/SKILL_template.md` and print it for the user to save | Skill promotion requirement |
| 9 | SKILL.md includes a **routing table** mapping insight type to cold file (project-domain → `glossary.md`; project-pattern/gotcha → `learnings.md`; project-decision → `decisions.md`; user-* → LR only, not cold files) | Scope creep edge case |
| 10 | SKILL.md's `description` frontmatter field says WHAT + WHEN and names both triggers (Supervisor-auto + user `/learn`) | CLAUDE.md skill table requirement |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | Read `.claude/skills/learn/SKILL.md` | All 8 workflow steps present (materiality → classify → deduplicate → number → write → supersede → MEMORY.md → promote) | manual review against AC table |
| 2 | Simulate: a user correction is present in context | SKILL.md workflow produces an LR stub for a `project` insight and no LR for a trivial exchange | mental walkthrough |
| 3 | Simulate: 2 existing LRs with overlapping pattern | SKILL.md workflow surfaces a candidate skill prompt | mental walkthrough |
| 4 | Frontmatter `name:` value matches folder name `learn` | `grep "^name: learn" .claude/skills/learn/SKILL.md` exits 0 | automated check |

### Verification Command

```bash
grep "^name: learn" .claude/skills/learn/SKILL.md && \
grep -c "materiality" .claude/skills/learn/SKILL.md && \
grep -c "supersed" .claude/skills/learn/SKILL.md && \
grep -c "promotion" .claude/skills/learn/SKILL.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold (materiality gate explicitly bars trivial exchanges) | ☐ pass / ☐ fail | |
| `verify` skill — invoke `learn` mentally with a sample insight from this session | ☐ pass / ☐ fail | [what LR would be written] |
| Review scope bounded to `.claude/skills/learn/` only | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |

---

## Approach

Write `.claude/skills/learn/SKILL.md` following `templates/SKILL_template.md`. The skill runs entirely in-context (LLM prose instructions, no shell scripts). Structure the SKILL.md workflow as 8 numbered steps:

### Step 1 — Materiality Gate
Scan the recent conversation for signal. Write an LR **only** when:
- The user corrects the Supervisor or an agent (explicit or implied)
- The user discloses prior knowledge or working-style preference
- A non-obvious domain pattern is confirmed (not merely mentioned)
- A misconception is corrected
- A "this was surprising" moment lands

Do NOT write an LR for:
- Greetings, acknowledgements, "ok", "thanks"
- Material merely covered (explained but not demonstrated as understood)
- Terms already in `memory/glossary.md`
- Activity logs ("we implemented X today")

### Step 2 — Classify
Tag each insight:
- `type: project` — concerns the codebase, domain patterns, gotchas, spec clarifications
- `type: user` — concerns the user's preferences, knowledge level, or working style

### Step 3 — Deduplicate
Before writing, grep:
1. All existing `memory/learning-records/LR-*.md` bodies for the same insight
2. `memory/learnings.md`, `memory/decisions.md`, `memory/glossary.md` for the same fact

If already captured verbatim → skip. If partially captured → write a supersession (Step 5).

### Step 4 — Number
At write time, scan `memory/learning-records/` for the highest `LR-NNNN` number. Increment by 1. Use 4-digit zero-padded format: `LR-0001`, `LR-0002`, etc.

### Step 5 — Write LR file
Use `templates/LEARNING-RECORD-FORMAT.md`. File path: `memory/learning-records/LR-NNNN-kebab-slug.md`. Fill all required fields. Set `status: active`.

### Step 6 — Supersede contradicted LRs
If the new insight contradicts an existing LR:
1. Edit the old LR's `status:` field to `superseded by LR-NNNN` (where NNNN is the new LR).
2. Add a `## Superseded by` section to the old LR body linking to the new one.
3. In `MEMORY.md`, replace the old one-liner with `~~old text~~ → see LR-NNNN`.

### Step 7 — Update MEMORY.md
Under `### Learning Records`:
- Append one-liner for each new active LR: `- [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — one-line summary`
- Strike/replace one-liners for any superseded LR (Step 6)
- Count total lines in `MEMORY.md` — if approaching 200, flag to Supervisor to run `/compact-memory`

### Step 8 — Skill Promotion (conditional)
After writing the new LR(s), scan all active LRs for pattern overlap:
- If ≥2 LRs share the same underlying pattern (same domain, same behavior, same type of correction), surface to the user:
  > "Pattern detected across LR-NNNN and LR-MMMM: [one-line description]. Want me to draft a `learn-[slug]` skill stub?"
- On user approval: draft a `SKILL.md` stub using `templates/SKILL_template.md`, output it as a fenced code block, and instruct the user to save it to `.claude/skills/<name>/SKILL.md`. Do NOT write the file automatically.

### Routing table (Step 2 expansion)

| Insight type | Write to |
|---|---|
| `project` + domain term / model | `memory/glossary.md` + LR |
| `project` + pattern / gotcha / spec clarification | `memory/learnings.md` + LR |
| `project` + architectural decision | `memory/decisions.md` + LR |
| `user` + any | LR only (never cold files) |

---

## Edge Case Checklist

- [ ] **Noise gate miss**: skill writes an LR for a trivial exchange — materiality check must be the first step, not an afterthought
- [ ] **Duplication**: new LR repeats content already in `learnings.md` — deduplication grep must cover cold files, not just existing LRs
- [ ] **Supersession miss**: contradicted LR not caught because only title was checked — grep must scan LR bodies
- [ ] **Numbering collision**: two rapid invocations assign same number — number is determined at write time after a fresh directory scan, not at skill start
- [ ] **Hot tier overflow**: new LR one-liners push `MEMORY.md` past 200 lines — check line count before appending; flag if close
- [ ] **Scope creep**: user-preference LR routed to `decisions.md` — routing table must be explicit; `user` type → LR only
- [ ] **Stale superseded entry in MEMORY.md**: old one-liner persists after supersession — Step 6 must update MEMORY.md as part of the same action
- [ ] **Skill stub auto-saved**: skill writes SKILL.md without user approval — promotion step must output a code block and stop; never call Write tool

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/learn/SKILL.md` | Create (new skill) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/learnings.md` | Written to at runtime by the skill, not at authoring time |
| `memory/MEMORY.md` | Updated at runtime by the skill |
| `CLAUDE.md` | Registration belongs to T010 |
| `README.md` | Registration belongs to T010 |
| `setup.sh` | setup.sh update belongs to T010 |
| Any existing `.claude/skills/*/SKILL.md` | Observed only, never modified |

---

## Test Plan

- Read the SKILL.md top-to-bottom and mentally simulate 3 scenarios:
  1. A user correction mid-session → one new `project` LR written, `learnings.md` updated, MEMORY.md one-liner added
  2. A user preference disclosure → one new `user` LR written, cold files NOT touched
  3. Third LR written that contradicts LR-0001 → LR-0001 marked superseded, MEMORY.md updated
- Verify `grep "^name: learn" .claude/skills/learn/SKILL.md` exits 0
- Verify all 8 step headings are present in the SKILL.md body

---

## Completion Checklist

- [ ] `.claude/skills/learn/SKILL.md` created with all 8 workflow steps
- [ ] Frontmatter `name: learn` matches folder name
- [ ] Materiality gate is the first step with explicit exclusion list
- [ ] Routing table present
- [ ] Supersession procedure documented
- [ ] Skill promotion step present with user-approval gate (no auto-write)
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T009 ready for Stage 4 review
