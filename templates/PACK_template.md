# PACK.md — [Pack Name]
**Pack**: `[pack-name]`
**Domain**: [short domain description]
**Core framework version tested**: 1.14+

---

## When to use this pack

[1–2 sentences: what type of project should have the Supervisor activate this pack.]

**Select this pack when your project involves:**
- [signal 1]
- [signal 2]
- [signal 3]

**Do NOT select if:** [counter-signal — when the core framework is sufficient without this pack]

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `[agent-name]` | Agent | [one-line role description] |
| `[skill-name]` | Skill | [one-line skill description] |
| `[skill-name]` | Skill | [one-line skill description] |

**Boundary from core agents:**
- Core `backend-developer` / `frontend-developer` handles: [what core handles]
- This pack's `[agent-name]` handles: [what the pack agent handles that core doesn't]

---

## Activate

This pack ships inactive in every project's `packs/` catalog: no CLI loads it (ADR-0002). Ask the
Supervisor to activate it. After you approve, the Supervisor copies the pack's files into the
project's agents and skills:

```sh
cp packs/[pack-name]/agents/*.md agents/
cp -R packs/[pack-name]/skills/* skills/
```

`setup.sh` takes no options; it never installs a pack.

---

## Agents installed

### `[agent-name]`
**File**: `packs/[pack-name]/agents/[agent-name].md`
[2–3 sentence description of the agent's mindset and when the Supervisor should spawn it.]

---

## Skills installed

### `[skill-name]`
**File**: `packs/[pack-name]/skills/[skill-name]/SKILL.md`
[1–2 sentence description: what it checks, when to invoke it.]

### `[skill-name]`
**File**: `packs/[pack-name]/skills/[skill-name]/SKILL.md`
[1–2 sentence description: what it checks, when to invoke it.]
