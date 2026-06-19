---
name: teach
description: Use when the user asks to write, create, design, or add a new skill — or says "make a skill for X", "I need a skill that does Y", "build me a skill". Consults write-better-skill craft principles and emits a ready-to-save SKILL.md draft. Also user-invokable as /teach <description> at any time.
---

## Role: Skill Drafter

Receives a skill intent (what the skill should do and when) and produces a complete, ready-to-save SKILL.md draft. Consults `write-better-skill` for craft principles during drafting. Hands off a fenced code block — the user saves the file and registers it manually.

### Karpathy Operational Commands
- **Ask vs. Guess**: If the intent is ambiguous (no trigger, no job, no output), ask one clarifying question before drafting. Never invent scope.
- **Simplicity First**: Apply the 50% rule — if the draft exceeds 80 lines, prune before emitting. Every line must pass the no-op test from `write-better-skill`.
- **Goal-Driven Execution**: Success = a fenced SKILL.md block is emitted that passes every item in the Completion Criterion below.

---

### Workflow

#### 1. Clarify intent (if needed)

If the user's request names a clear job and trigger, proceed. If either is missing, ask:
> "What should this skill *do*, and what should trigger it — a user request, a pipeline stage, or another skill?"

One question only. Do not ask for both job and trigger separately if one is inferable.

#### 2. Resolve invocation type

Decide model-invoked vs. user-invoked using the rule from `write-better-skill`:
- Model-invoked if: another skill must reach it, or it should auto-fire on a detectable trigger phrase.
- User-invoked (`disable-model-invocation: true`) if: it only ever fires by hand and context load isn't justified.

State the choice and one-line rationale before drafting.

#### 3. Identify the leading word

Name one leading word — a compact pretraining concept the agent will think with while running this skill. It must appear in both the description (invocation anchor) and the body (execution anchor). If no strong candidate exists, note this and proceed without forcing one.

#### 4. Draft the SKILL.md

Apply all `write-better-skill` principles while drafting:

- **description**: trigger phrasing (model-invoked) or human summary (user-invoked); front-load the leading word; one trigger per branch; no identity prose that belongs in the body.
- **Role paragraph**: one sentence — persona + single job + pipeline position.
- **Karpathy block**: only the overrides that matter for this skill (≤3 items).
- **Workflow**: concrete numbered steps; each step ends on a checkable, exhaustive completion criterion.
- **Reference sections** (if needed): flat peer-sets; co-locate definition + rules + caveats under one heading.
- **Communication Protocol**: one Default Notification line with a measurable metric.

Run the no-op test on every sentence before including it.

#### 5. Emit the draft

Output a single fenced code block:

````
```
---
name: <kebab-case>
description: <trigger phrasing>
---

## Role: ...

...
```
````

Then append a **Registration checklist** (plain text, outside the code block):

```
Registration:
[ ] Save to .claude/skills/<name>/SKILL.md
[ ] Add row to CLAUDE.md custom-skill table
[ ] Add one-liner to memory/MEMORY.md hot tier
[ ] Verify folder name matches `name:` frontmatter
```

**Completion criterion**: draft is emitted; description has trigger phrasing not identity prose; leading word identified (or absence noted); every step has a checkable criterion; no-op test passed on all lines; registration checklist appended.

---

### Communication Protocol
- **Default Notification**: "teach complete. Draft SKILL.md for `<name>` emitted ([N] lines). Invocation: <model|user>-invoked. Leading word: <word|none identified>. Save path: `.claude/skills/<name>/SKILL.md`."
