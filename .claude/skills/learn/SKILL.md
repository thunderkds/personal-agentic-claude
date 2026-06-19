---
name: learn
description: "Reflect & Encode reflex skill. Detects non-obvious insights in the recent conversation, writes durable Learning Records (LRs) to `memory/learning-records/`, and keeps MEMORY.md in sync. Use after any significant exchange — invoked automatically by the Supervisor when a user correction or new pattern surfaces, or manually by the user via `/learn`."
---

## Role: Learning Record Specialist

You are the Supervisor running a structured Reflect & Encode pass on the current conversation context. Your single job is to transform non-obvious insights that surfaced during this session into durable, traceable Learning Records (LRs) that future sessions can rely on — replacing the gap where insights evaporate between git pushes.

You produce LR files in `memory/learning-records/`, update `memory/MEMORY.md` hot tier, route confirmed facts to the appropriate cold file, and (conditionally) surface a skill promotion candidate.

### Karpathy Operational Commands

- **Ask vs. Guess**: If the boundary between "materiality pass" and "noise" is unclear for a given exchange, flag it to the Supervisor before writing an LR. Never guess that something qualifies.
- **Simplicity First**: One LR per discrete insight. Do not merge unrelated insights into one record. Do not restructure cold files — append only.
- **Surgical Changes**: Touch only `memory/learning-records/`, `memory/MEMORY.md`, and the single cold file the routing table designates. Never rewrite existing cold file sections; append under the relevant heading.
- **Goal-Driven Execution**: Success = every material insight from this session has an active LR, MEMORY.md is accurate, and no trivial exchange produced an LR.

---

### Workflow

#### Step 1 — Materiality Gate

Scan the recent conversation context for candidate insights. **Write an LR only when at least one of these signals is present:**

| Signal | Example |
|---|---|
| User corrects the Supervisor or an agent (explicit or implied) | "No, that's wrong — it should be X" |
| User discloses a prior-knowledge level, preference, or working-style | "I always prefer short PRs" |
| A non-obvious domain pattern is confirmed (demonstrated, not merely mentioned) | Third time the same edge case breaks the same assumption |
| A misconception is corrected (agent was wrong; user set it straight) | Agent claimed X; user showed it is actually Y |
| A "this was surprising" moment lands (unexpected behaviour, undocumented constraint) | "Turns out the API rate-limits per org, not per user" |

**Do NOT write an LR for any of the following — discard immediately:**

- Greetings, acknowledgements, "ok", "thanks", small-talk
- Material merely explained but not demonstrated or confirmed
- Terms already present verbatim in `memory/glossary.md`
- Activity logs ("we implemented X today", "T009 is done")
- Restatements of content already in `memory/decisions.md` or `memory/learnings.md`

If no signals pass the materiality gate, announce: "No material insights detected — no LRs written." and stop.

---

#### Step 2 — Classify

For each insight that passed Step 1, assign a type:

| Type | Meaning |
|---|---|
| `project` | Concerns the codebase, domain patterns, gotchas, spec clarifications, architectural decisions — applies to this project |
| `user` | Concerns the user's personal preferences, knowledge level, or working / interaction style — applies to all projects with this user |

One insight → one type. If an insight straddles both, split it into two separate records.

**Routing table (determines where the insight goes beyond the LR file):**

| Insight type | Write LR file | Also append to cold file |
|---|---|---|
| `project` + domain term or model | Yes | `memory/glossary.md` under `## Domain Models` or `## Terms` |
| `project` + pattern / gotcha / spec clarification | Yes | `memory/learnings.md` under the relevant heading |
| `project` + architectural or infrastructure decision | Yes | `memory/decisions.md` under the relevant heading |
| `user` + any | Yes | **Never** touch cold files — LR only |

> Scope-creep guard: a `user` insight **never** goes to `decisions.md`, `glossary.md`, or `learnings.md`. If you catch yourself routing a preference to a cold file, stop and re-classify.

---

#### Step 3 — Deduplicate

Before writing any LR, perform these checks in order:

1. **Scan existing LR bodies**: Read all `memory/learning-records/LR-*.md` files. Check whether the `## Insight` section of any existing LR captures the same fact, even with different wording.
2. **Scan cold files**: Grep `memory/learnings.md`, `memory/decisions.md`, and `memory/glossary.md` for the key phrase or concept.

**Decision:**

| Finding | Action |
|---|---|
| Already captured verbatim in an active LR or cold file | Skip — do not write a duplicate |
| Partially captured but the new insight adds material nuance or contradicts the existing record | Proceed to Step 5 (Supersession) |
| Not captured anywhere | Proceed to Step 4 (Number) |

---

#### Step 4 — Number

**At the moment you are ready to write the LR file** (not at skill start), scan `memory/learning-records/` to find the highest existing `LR-NNNN` number. Increment by 1. Use 4-digit zero-padded format: `LR-0001`, `LR-0002`, … `LR-0042`, etc.

Rationale: numbering at write time (not at skill start) prevents collision when two LRs are produced in the same skill invocation — assign the second number only after the first file is written.

---

#### Step 5 — Write LR File

Create the file at `memory/learning-records/LR-NNNN-kebab-slug.md` following the spec in `templates/LEARNING-RECORD-FORMAT.md`.

**Required frontmatter (all four fields are mandatory):**

```yaml
---
name: LR-NNNN-kebab-slug        # must match filename without .md
date: YYYY-MM-DD                 # today's ISO date
type: project | user
status: active
---
```

**Required body sections:**

- `## Insight` — 1–3 sentences. State the non-obvious thing learned. Write as a timeless fact, not a narrative.
- `## Evidence` — how this was observed or confirmed (user correction, pattern seen twice, explicit statement). Include the session date or task ID.
- `## Implications` — concrete directives for future sessions: "Always do X when Y." / "Never do Z unless the user explicitly asks."

If this LR supersedes an older one, also include `## Supersedes` listing the old LR IDs (see Step 6).

After writing, also append to the appropriate cold file per the routing table in Step 2 (for `project` insights only).

---

#### Step 6 — Supersede Contradicted LRs

If the new insight contradicts or substantially updates an existing active LR:

1. Open the old LR file. Change its frontmatter `status:` field from `active` to `superseded by LR-NNNN` (using the new LR's exact ID).
2. Append a `## Superseded by` section to the old LR body:
   ```markdown
   ## Superseded by
   - [LR-NNNN-new-slug](memory/learning-records/LR-NNNN-new-slug.md) — one-line reason
   ```
3. Add a `## Supersedes` section to the **new** LR body listing the old LR ID(s).
4. In `memory/MEMORY.md` (handled in Step 7): replace the old one-liner with the struck-through form.

Do NOT delete the old LR file — archive by supersession only.

---

#### Step 7 — Update MEMORY.md

Open `memory/MEMORY.md`. Under the `### Learning Records` section (create the section if it does not exist):

**For each new active LR written in this invocation**, append one line:
```
- [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — one-line summary (≤120 chars)
```

**For each LR superseded in Step 6**, find its existing one-liner in `MEMORY.md` and replace it with:
```
- ~~LR-NNNN old-slug — old summary~~ → see LR-MMMM
```

**Overflow check**: After all updates, count the total lines in `MEMORY.md`. If the count is at or above **190 lines**, flag to the Supervisor:
> "MEMORY.md is approaching the 200-line limit ([N] lines). Run `/compact-memory` before the next session."

Do NOT compact or prune entries yourself — that belongs to the `compact-memory` skill.

---

#### Step 8 — Skill Promotion (Conditional)

After all LRs for this invocation have been written, scan the full set of active LRs in `memory/learning-records/`:

- Compare LR `## Insight` and `## Implications` sections for pattern overlap: same domain area, same recurring behaviour, same type of correction appearing across ≥2 different LRs.
- If ≥2 active LRs share a discernible underlying pattern, surface the candidate to the user:

  > "Pattern detected across LR-NNNN and LR-MMMM: [one-line description of the shared pattern]. Want me to draft a `learn-[slug]` skill stub that encodes this pattern permanently?"

- **On user approval only**: draft a `SKILL.md` stub using the structure from `templates/SKILL_template.md`, output it as a fenced markdown code block, and instruct the user:
  > "Save this as `.claude/skills/learn-[slug]/SKILL.md` and register it in CLAUDE.md."

- **Never write the file automatically.** The promotion step outputs a code block and stops — the Write tool must not be called for the stub.

If no pattern overlap is found, skip this step silently.

---

### Communication Protocol

- **Default Notification**: "learn complete. [N] LR(s) written: [comma-separated IDs]. [N] superseded. MEMORY.md updated ([M] lines). [Skill promotion candidate surfaced / No promotion candidate.]"
- If zero LRs were written: "learn complete. No material insights detected — no LRs written."
