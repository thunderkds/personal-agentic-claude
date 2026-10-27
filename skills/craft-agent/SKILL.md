---
name: craft-agent
description: Use when a project's requirement implies a sub-agent role the base team (Common-Infrastructure, Backend, Frontend, QA) doesn't cover — e.g. "we need a mobile/data/ML agent". Reads PROJECT_SPEC.md/PRD.md once and drafts the whole supplemental roster in one call. Also user-invokable as /craft-agent at any time. Optional and supplemental — the base team is always the Stage 1.5 default, never gated by this skill.
---

## Role: Supplemental Agent Drafter

Receives a locked requirement and the existing base team, and produces one or more complete, ready-to-save `agents/<name>.md` drafts for roles the base team doesn't cover. Never writes to `agents/` directly — hands off fenced code blocks the user saves and registers manually. Structural clone of `teach`, targeting agent definitions instead of skills.

### Karpathy Operational Commands
- **Ask vs. Guess**: If `PROJECT_SPEC.md`/`PRD.md` isn't locked, or the implied role set is unbounded, ask one clarifying question before drafting. Never invent roles.
- **Simplicity First**: Apply the 50% rule — if a single Agent Draft exceeds ~80 lines, prune before emitting. Draft only roles the base team genuinely doesn't cover.
- **Goal-Driven Execution**: Success = one fenced Agent Draft block per uncovered role, plus a Registration checklist, emitted in a single invocation.

---

### Workflow

#### 1. Confirm prerequisites

Require `PROJECT_SPEC.md` (or `PRD.md`) to exist and be locked. If missing or not locked, refuse and point back to Phase 0 / Stage 2 — do not draft.

#### 2. Enumerate supplemental roles

Cross-check the requirement against the base team (Common-Infrastructure-Agent, Backend-Implementer, Frontend-Implementer, QA-Automation-Agent) and every existing `agents/*.md` filename:
- If a role is already covered by the base team or an existing agent file, reuse that name — do not draft a near-duplicate.
- If a drafted name collides with an existing filename for a genuinely different role, flag the collision explicitly (never silently overwrite).
- If the requirement only needs base-team roles, report "no supplemental role needed" and stop — do not force a draft.
- If the role set is unbounded or unclear, ask one clarifying question. Do not fabricate roles.

#### 3. Draft each Agent Draft

For every genuinely uncovered role, draft:
- Name (kebab-case) and `subagent_type`
- `description` — one line (never a `|`/`>` block) that says *when* to delegate: start with "Use when" or "Use for" and name at least two concrete trigger scenarios from this pipeline (e.g. "a TASK_GUIDE assigns mobile app work — e.g. a new screen or a native API integration"), then the role's scope facts. Never write "proactively": agents are spawned only by the Supervisor through `craft-spawn-prompt` with a TASK_GUIDE
- `color` — one of `red, blue, green, yellow, purple, orange, pink, cyan`, distinct from the base team's (`orange` common-infrastructure, `blue` backend-developer, `purple` frontend-developer, `green` qa-expert) where a free colour remains
- Role and responsibilities (one paragraph, single job)
- Required skills / expertise
- Specific rules — role overrides; state "Inherits from `templates/general-agent-template.md`" explicitly, matching the shape of `backend.md`/`frontend.md`/`qa.md`
- **The four sections every role guide carries in its own words** — Mandatory Startup Sequence, Complexity & escalation, Available skills, Communication Protocol. These are *not* inherited: the harness auto-loads `agents/<name>.md` as the agent's system prompt, so a role guide always arrives while `templates/general-agent-template.md` arrives only if the agent opens it. Copy the shape from `backend.md` and adapt the wording to the role; a draft missing them ships a non-compliant agent (T066)
- **The `## Karpathy Engineering Principles (Compact)` table, copied VERBATIM from `backend.md`** — same guaranteed-channel reason as above, but it is a Permanent Rule rather than role-shaped guidance, so it is copied byte-identically and **not** adapted to the role. It no longer lives in `general-agent-template.md` and cannot be inherited from there; a draft without it ships a role born without a Permanent Rule (T069)
- CLI & exact spawn command
- Save path: `agents/<name>.md`

#### 4. Fidelity gate

Run each draft through `write-better-skill`'s **Fidelity Gate (Hallucination Check)**: every claimed responsibility/skill traces to `PROJECT_SPEC.md`/`PRD.md` or the user's literal words this session and is cut otherwise; every internal `Skill()`/`Agent()` reference resolves or is flagged `[UNRESOLVED: ...]`; no claim of authority the Permanent Rules reserve elsewhere (e.g. direct `memory/` writes — Supervisor-only). State "Fidelity gate: PASS" per draft, or list its cuts/flags, before emitting.

#### 5. Emit the drafts

Output one fenced code block per Agent Draft:

````
```
---
name: <kebab-case>
description: "Use when <trigger scenario 1>, <trigger scenario 2> ... <role scope facts>"
tools: ...
model: ...
color: <red|blue|green|yellow|purple|orange|pink|cyan>
---

Inherits Base Rules / Search-Before-You-Build from
templates/general-agent-template.md. Carries the ## Karpathy Engineering Principles (Compact)
table verbatim, plus its own Mandatory Startup Sequence, Complexity &
escalation, Available skills, and Communication Protocol. Overrides:
...
```
````

Then append a single **Registration checklist** (plain text, outside the code blocks) covering the whole roster:

```
Registration:
[ ] Save each draft to agents/<name>.md
[ ] Add row to PROJECT_SPEC.md "## Sub-Agent Team" table
[ ] Add one-liner to memory/MEMORY.md hot tier
[ ] Filename collisions: <none | list flagged names>
```

**Completion criterion**: prerequisites confirmed (or refusal issued); role enumeration cross-checked against base team + existing agent files; whole roster drafted in one pass (not one role per invocation); every draft states template inheritance and lists only overrides; Fidelity gate stated PASS or cuts/flags listed per draft; registration checklist appended once for the full roster.

---

### Communication Protocol
- **Default Notification**: "craft-agent complete. Drafted [N] supplemental Agent Draft(s) for roles: <list>. Fidelity gate: <PASS all|cuts/flags noted>. Base team unaffected. Save paths: `agents/<name>.md`."
