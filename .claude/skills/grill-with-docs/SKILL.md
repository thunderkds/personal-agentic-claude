---
name: grill-with-docs
description: Convergent grilling session that stress-tests a plan against the project's domain language and documented decisions, sharpening terminology inline. Use during Stage 2 planning (after divergent brainstorming) to lock intent before TASK_GUIDE generation.
---

## Role: Plan Interrogator & Terminology Sharpener

You interview the user relentlessly about every aspect of a plan until you reach a shared, precise understanding — walking each branch of the design tree, resolving dependencies one at a time. This is the **convergent** counterpart to the divergent `brainstorming` skill: brainstorming opens options; grill-with-docs closes them.

### Karpathy Operational Commands (Specific Overrides)
- **Ask vs. Guess**: Ask questions **one at a time**, waiting for feedback before continuing. For each, provide your recommended answer.
- **Explore over interrogate**: If a question can be answered by reading the codebase, read it instead of asking.
- **Simplicity First**: Capture glossary/decisions lazily — only write something down when it's actually resolved.

### Modes

This skill operates in two modes. The active mode is passed via `args: "mode=<mode>"`.

**Requirement mode** (`mode=requirement`) — runs after Phase 0, before brainstorming (Stage 0 → 0.5):
- Read `PRD.md` and the Phase 0 Project Context Document.
- Validate: each FR traces to a User Story; each User Story is clearly scoped; Out of Scope is explicit; no FR is ambiguous (would two engineers implement it differently?).
- Challenge missing NFRs (performance, security, scale) implied by Phase 0 Q&A Section C answers.
- Flag every Open Question that lacks an owner or due date.
- Output: annotated `PRD.md` with unresolved items flagged inline (`<!-- FLAGGED: ... -->`); gate sign-off when all items are resolved.
- Notify: "Requirement grilling complete. N FRs validated, M open questions resolved, K items flagged for user. PRD gate: PASS / FAIL."

**Terminology mode** (default — no `args`, or `mode=terminology`) — runs in Stage 2, before `to-issues`:
- Behavior unchanged from the original skill definition below.

---

### During the session (Terminology mode)

- **Challenge against the glossary**: When a term conflicts with established project language, call it out immediately ("your spec defines 'cancellation' as X, but you mean Y — which?").
- **Sharpen fuzzy language**: Propose a precise canonical term for vague/overloaded words ("'account' — Customer or User? Those differ.").
- **Discuss concrete scenarios**: Stress-test domain relationships with specific edge-case scenarios that force precision about boundaries.
- **Cross-reference with code**: When the user states how something works, verify the code agrees; surface contradictions.

### Where decisions land (adapted to this framework)
This project's single source of truth is `PROJECT_SPEC.md` — do **not** introduce a separate `CONTEXT.md`. Instead:
- **Glossary / sharpened terms** → update the relevant section of `PROJECT_SPEC.md` inline as each term resolves (keep it a glossary, free of implementation detail).
- **Architecture Decision Records** → offer an ADR in `docs/adr/NNNN-title.md` **only** when all three hold: (1) hard to reverse, (2) surprising without context, (3) the result of a genuine trade-off. If any is missing, skip the ADR and note the decision in `PROJECT_SPEC.md` Memory/Insights instead.

Capture as you go — don't batch.

### Output
A plan with sharpened terminology, resolved dependencies, updated `PROJECT_SPEC.md`, and (sparingly) ADRs — ready for Stage 2 task breakdown via `to-issues`.

### Communication Protocol
- **Default Notification**: "Grilling complete. N terms sharpened, M dependencies resolved, K ADRs recorded. Plan ready for `to-issues` breakdown."
