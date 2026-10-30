# BRAINSTORMING_LOG.md
**Generated**: 2026-07-17
**Task / Context**: Meta — prevent hallucinated/mis-scoped generated skills & agents from entering the harness
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (moderate ambiguity, resolved via user Q&A)

---

## The Problem Space

`teach` and `craft-agent` produce SKILL.md / agent .md drafts, but neither checks the draft's claims against the requirement it was drafted for. A drafted artifact can silently:
- claim a capability that traces to nothing the user asked for (hallucinated scope),
- call a `Skill()`/`Agent()` reference that doesn't exist,
- claim authority the Permanent Rules reserve elsewhere (e.g. writing to `memory/` directly).

Unlike a bad code change (caught by Stage 4 `code-review` for one task), a bad skill/agent definition is durable — it lives in `.claude/skills/` or `.claude/agents/` and silently affects every future session until someone notices. The user explicitly asked for this check to live "in the steps for loading, creating the skills/agents" — i.e. inside `teach`/`craft-agent`'s own workflow, not a separate audit pass that's easy to skip.

---

## Questions for the User

None outstanding — the core placement question was already resolved via forced choice: **shared gate in `write-better-skill`**, referenced by both `teach` and `craft-agent` before they emit a draft.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Shared Gate in write-better-skill | One "Fidelity Gate" reference section in `write-better-skill`; `teach`/`craft-agent` each add one workflow step pointing to it before Emit | Low | ~25 lines total | Low | ✅ Yes |
| B | Duplicated Gate per Skill | Same checklist written independently inside `teach` and `craft-agent`'s own workflow steps | Low | ~40 lines (duplicated) | Medium (drift between copies) | |
| C | Standalone Audit Skill | New skill (e.g. `audit-agents-skills`) invoked after a draft is produced, or periodically like `compound-refresh` | Medium | ~80 lines (new skill + registration) | Medium (extra invocation step, skippable) | |

### Option A — Shared Gate in write-better-skill
**Approach**: Add a "Fidelity Gate (Hallucination Check)" reference section to `write-better-skill` covering: (1) traceability of every claimed capability to the locked requirement, (2) resolution of every `Skill()`/`Agent()` reference inside the draft against actual files, (3) scope containment against Permanent Rules. `teach` and `craft-agent` each insert one gate-check step before their Emit step, pointing to this section, requiring "Fidelity gate: PASS" or a list of cuts/flags before the draft is output.
**Pros**: single source of truth (matches `write-better-skill`'s existing role as the craft reference both skills already consult); zero new skill to register; structurally can't be skipped since it sits inside the emit sequence both skills already run every time.
**Cons**: makes `write-better-skill` slightly less "pure craft" (gains one requirement-fidelity concern alongside structural craft concerns).
**Why it might fail**: if a future refactor ever inlines only part of `write-better-skill` into `teach`/`craft-agent` instead of referencing it whole, the gate could be silently dropped. Mitigated by having each skill's new step name the gate explicitly rather than assume implicit inheritance.

### Option B — Duplicated Gate per Skill
**Approach**: Write the same three-point checklist directly into `teach`'s and `craft-agent`'s own workflow steps, independently.
**Pros**: each skill fully self-contained; no cross-file dependency to trace.
**Cons**: violates the framework's own single-source-of-truth pruning rule (`write-better-skill` § Pruning); two copies drift the first time one gets refined and the other doesn't.
**Why it might fail**: reproduces exactly the "sediment/duplication" failure mode `write-better-skill` itself warns against.

### Option C — Standalone Audit Skill
**Approach**: New `audit-agents-skills` skill, modeled on `compound-refresh`, run either right after a draft or periodically over all of `.claude/skills/`+`.claude/agents/`.
**Pros**: also covers artifacts that entered the repo *before* this gate existed (retroactive audit) — the one thing A/B can't do.
**Cons**: adds a new skill to register/document/remember — precisely the "easy to skip" failure the user flagged by asking for the check to live in the creation steps, not a separate pass.
**Why it might fail**: becomes shelfware, like an unrun linter — nothing forces its invocation, so hallucinated drafts keep slipping through if a human forgets the extra step.

---

## 50% Rule Check

Option A is already the 50%-reduced version relative to B/C: one new section (~15 lines) + two one-line step insertions, versus a duplicated checklist (B) or an entire new skill with its own registration checklist and Stage placement (C).

---

## Recommended Path

**Option A — Shared Gate in write-better-skill**

Matches the existing architecture (`write-better-skill` is already the single reference both drafting skills consult), costs the least new surface, and is structurally unskippable because it's inserted into the mandatory Emit step both `teach` and `craft-agent` already execute every run — not a separate invocation a human has to remember.

---

## Surgical Scope

Files that **should** be touched:
- `.claude/skills/write-better-skill/SKILL.md` — add "Fidelity Gate (Hallucination Check)" section
- `.claude/skills/teach/SKILL.md` — insert one gate-check step before Emit
- `.claude/skills/craft-agent/SKILL.md` — insert one gate-check step before Emit the drafts
- `memory/MEMORY.md` — one-liner noting the new gate exists

Files that **must not** be touched:
- `.claude/skills/code-review/SKILL.md` — this gate is about draft-time fidelity for generated skills/agents, not the ordinary code-review pipeline; keep the two review surfaces distinct
- Any existing `.claude/agents/*.md` or `.claude/skills/*/SKILL.md` other than the three above — retroactive audit of pre-existing artifacts is explicitly out of scope for this change (that's the Option C tradeoff, not chosen)

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Draft has zero claims traceable to the requirement — must be caught and cut, not silently passed
- [ ] Draft references a `Skill()`/`Agent()` name that doesn't exist yet — must be flagged as "requires companion draft," not silently emitted
- [ ] Draft claims write access to `memory/` or another Permanent-Rules-reserved authority
- [ ] `craft-agent`'s existing "role already covered by base team" check (its step 2) must stay complementary to the new fidelity step, not redundant with it

---

## Next Actions

1. Run `grill-with-docs` to sharpen terminology (what counts as "traceable," what "companion draft" means operationally) and confirm whether a DDR is warranted for this change.
2. On approval, edit the three files listed under Surgical Scope.
3. Update `memory/MEMORY.md` with a one-liner pointing to this change.

---

## User Selection

> **Approved direction**: Option A — Shared Gate in write-better-skill
> Approved by user on 2026-07-17 (via forced-choice question resolving skill/agent gate placement).
