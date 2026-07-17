---
name: learn
description: "Reflect & Encode reflex skill. Detects non-obvious insights in the recent conversation, writes durable Learning Records (LRs) to `memory/learning-records/`, and keeps MEMORY.md in sync. Use after any significant exchange — invoked automatically by the Supervisor when a user correction or new pattern surfaces, or manually by the user via `/learn`."
---

## Role: Learning Record Specialist

Transform non-obvious insights from this session into durable Learning Records in `memory/learning-records/`, update `memory/MEMORY.md`, route confirmed facts to the appropriate cold file, and (conditionally) surface a skill promotion candidate.

### Karpathy Operational Commands

- **Ask vs. Guess**: If the boundary between "materiality pass" and "noise" is unclear, flag it to the Supervisor before writing an LR. Never guess that something qualifies.
- **Surgical Changes**: Touch only `memory/learning-records/`, `memory/MEMORY.md`, and the single cold file the routing table designates. Append only — never rewrite existing cold file sections.
- **Simplicity First**: One LR per discrete insight; never merge unrelated insights.

---

### Workflow

#### Step 1 — Materiality Gate

**Write an LR only when at least one of these signals is present:**

| Signal | Example |
|---|---|
| User corrects the Supervisor or an agent | "No, that's wrong — it should be X" |
| User discloses a preference, knowledge level, or working style | "I always prefer short PRs" |
| A non-obvious domain pattern is confirmed (demonstrated, not merely mentioned) | Third time the same edge case breaks the same assumption |
| A misconception is corrected (agent was wrong; user set it straight) | Agent claimed X; user showed Y |
| A "this was surprising" moment lands (unexpected behaviour, undocumented constraint) | "API rate-limits per org, not per user" |

**Do NOT write an LR for any of the following — discard immediately:**

- Greetings, acknowledgements, "ok", "thanks", small-talk
- Material merely explained but not demonstrated or confirmed
- Terms already present verbatim in `memory/glossary.md`
- Activity logs ("we implemented X today", "T009 is done")
- Restatements of content already in `memory/decisions.md` or `memory/learnings.md`

If no signals pass, announce: "No material insights detected — no LRs written." and stop.

#### Step 2 — Classify

Assign each insight one type: `project` (codebase, domain patterns, gotchas, spec clarifications, architecture) or `user` (personal preferences, knowledge level, working style). One insight → one type; if it straddles both, split into two records.

**Routing table (where the insight goes beyond the LR file):**

| Insight type | Write LR file | Also append to cold file |
|---|---|---|
| `project` + domain term or model | Yes | `memory/glossary.md` |
| `project` + pattern / gotcha / spec clarification | Yes | `memory/learnings.md` |
| `project` + architectural or infrastructure decision | Yes | `memory/decisions.md` |
| `user` + any | Yes | **Never** touch cold files — LR only |

> Scope-creep guard: a `user` insight **never** goes to `decisions.md`, `glossary.md`, or `learnings.md`. If you catch yourself routing a preference to a cold file, stop and re-classify.

#### Step 3 — Deduplicate

Check in order: (1) all `memory/learning-records/LR-*.md` `## Insight` sections; (2) grep the three cold files for the key phrase.

| Finding | Action |
|---|---|
| Already captured verbatim in an active LR or cold file | Skip — do not write a duplicate |
| Partially captured but new insight adds nuance or contradicts | Proceed to Step 5 (Supersession) |
| Not captured anywhere | Proceed to Step 4 (Number) |

#### Step 4 — Number

**At the moment you are ready to write the LR file** (not at skill start), scan `memory/learning-records/` for the highest `LR-NNNN`, increment by 1, 4-digit zero-padded. This prevents collision when one invocation writes multiple LRs — assign the second number only after the first file is written.

#### Step 5 — Write LR File

Create `memory/learning-records/LR-NNNN-kebab-slug.md` per `templates/LEARNING-RECORD-FORMAT.md`.

**Required frontmatter (all four fields are mandatory):**

```yaml
---
name: LR-NNNN-kebab-slug        # must match filename without .md
date: YYYY-MM-DD                 # today's ISO date
type: project | user
status: active
---
```

**Required body sections:** `## Insight` (1–3 sentences, timeless fact) · `## Evidence` (how observed/confirmed, with session date or task ID) · `## Implications` (concrete directives: "Always do X when Y").

If this LR supersedes an older one, also include `## Supersedes` (see Step 6). Then append to the cold file per the Step 2 routing table (`project` insights only).

#### Step 6 — Supersede Contradicted LRs

If the new insight contradicts or substantially updates an existing active LR:

1. In the old LR, change frontmatter `status:` from `active` to `superseded by LR-NNNN`.
2. Append to the old LR body: `## Superseded by` — `- [LR-NNNN-new-slug](memory/learning-records/LR-NNNN-new-slug.md) — one-line reason`
3. Add `## Supersedes` to the **new** LR listing the old ID(s).
4. In `MEMORY.md` (Step 7): replace the old one-liner with the struck-through form.

Do NOT delete the old LR file — archive by supersession only.

#### Step 7 — Update MEMORY.md

Under `### Learning Records` (create if missing):

- Each new active LR: `- [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — one-line summary (≤120 chars)`
- Each superseded LR: replace its line with `- ~~LR-NNNN old-slug — old summary~~ → see LR-MMMM`

**Overflow check**: if `MEMORY.md` is at or above **190 lines**, flag:
> "MEMORY.md is approaching the 200-line limit ([N] lines). Run `/compact-memory` before the next session."

Do NOT compact or prune entries yourself — that belongs to the `compact-memory` skill.

#### Step 8 — Skill Promotion (Conditional)

Scan all active LRs for pattern overlap (same domain area / recurring behaviour / correction type across ≥2 LRs). If found, surface:

> "Pattern detected across LR-NNNN and LR-MMMM: [shared pattern]. Want me to draft a `learn-[slug]` skill stub that encodes this pattern permanently?"

**On user approval only**: draft a `SKILL.md` stub per `templates/SKILL_template.md`, output it as a fenced markdown code block, and instruct: "Save this as `.claude/skills/learn-[slug]/SKILL.md` and register it in CLAUDE.md."

**Never write the file automatically** — the promotion step outputs a code block and stops; the Write tool must not be called for the stub. If no overlap, skip silently.

---

### Communication Protocol

- **Default Notification**: "learn complete. [N] LR(s) written: [comma-separated IDs]. [N] superseded. MEMORY.md updated ([M] lines). [Skill promotion candidate surfaced / No promotion candidate.]"
- If zero LRs were written: "learn complete. No material insights detected — no LRs written."
