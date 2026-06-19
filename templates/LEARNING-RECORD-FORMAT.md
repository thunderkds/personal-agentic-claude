# Learning Record (LR) Format Specification

This file is the single source of truth for how a Learning Record (LR) file is structured.
Both the `learn` skill and any agent writing LRs must follow this spec exactly.

---

## Naming Convention

```
LR-NNNN-kebab-slug.md
```

- `NNNN` is a zero-padded 4-digit sequence number: `LR-0001`, `LR-0002`, … `LR-9999`.
  Do NOT use `LR-1` or `LR-01` — always 4 digits.
- `kebab-slug` is a short, lowercase, hyphen-separated description of the insight (2–5 words).
- Files live in `memory/learning-records/`.

Example: `memory/learning-records/LR-0001-supervisor-fires-learn-on-corrections.md`

---

## Frontmatter (Required)

Every LR file must open with YAML frontmatter containing all four fields:

```yaml
---
name: LR-NNNN-kebab-slug        # must match the filename (without .md)
date: YYYY-MM-DD                 # ISO date the record was created or last updated
type: project | user             # project = domain/pattern/gotcha for this codebase
                                 # user    = user preference, knowledge, or interaction style
status: active | superseded by LR-NNNN
                                 # use "superseded by LR-NNNN" (exact LR id) when replaced
---
```

All four fields are required. No field may be left blank.

---

## Body Sections

### Required Sections

#### `## Insight`
1–3 sentences. State the non-obvious thing that was learned. Avoid restating what is already obvious from the code or docs. Write as a timeless fact, not a narrative.

#### `## Evidence`
Explain how this insight was observed or confirmed:
- User correction (e.g. "user said X was wrong when agent did Y")
- Pattern seen at least twice in the same project
- Explicit user statement or preference

Cite the session date or task ID where relevant.

#### `## Implications`
What this insight unlocks or restricts in future sessions. Write concrete directives:
- "Always do X when Y."
- "Never do Z unless the user explicitly asks."

### Optional Section

#### `## Supersedes`
List older LR IDs that this record replaces, one per line. Only include when `status` in frontmatter is `superseded by LR-NNNN`.

```
## Supersedes
- LR-0003-old-slug
```

---

## Status Values

| Value | Meaning |
|-------|---------|
| `active` | Insight is current and should be applied in sessions |
| `superseded by LR-NNNN` | A newer LR (identified by its full ID) replaces this one; do not apply |

When an LR is superseded, update its frontmatter `status` field and add a `## Supersedes` section to the new LR.

---

## Filled Example

```markdown
---
name: LR-0001-supervisor-fires-learn-on-corrections
date: 2026-06-19
type: project
status: active
---

## Insight
The Supervisor agent triggers the `learn` skill automatically whenever the user corrects
an agent output, not only when the user explicitly says "remember this". Corrections are
the primary signal for new learning records.

## Evidence
Observed during T009 implementation (2026-06-19): user corrected the Supervisor's phrasing
of the `learn` skill trigger condition. The correction was explicit ("no, it should fire on
corrections too") and unprompted.

## Implications
- Always treat any user correction as a candidate learning record; do not wait for "remember
  this" phrasing.
- When the `learn` skill is invoked, check whether an existing active LR covers the same
  topic before creating a new one — prefer updating status to superseded and writing a new LR.
```

---

## Blank Template Stub

Copy this stub to `memory/learning-records/LR-NNNN-your-slug.md` and fill in every field:

```markdown
---
name: LR-NNNN-kebab-slug
date: YYYY-MM-DD
type: project | user
status: active
---

## Insight
[1–3 sentences: the non-obvious thing learned.]

## Evidence
[How it was observed — user correction, pattern seen twice, explicit statement. Include session date or task ID.]

## Implications
[What this unlocks or restricts in future sessions. Use concrete directives: "Always …" / "Never … unless …".]
```
