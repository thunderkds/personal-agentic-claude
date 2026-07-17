# BRAINSTORMING_LOG.md
**Generated**: 2026-07-17
**Task / Context**: Token-efficiency refactor — reducing billing spend across the Supervisor pipeline
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (moderate ambiguity, resolved via user Q&A)

---

## The Problem Space

The user wants to cut token/billing cost across sessions, inspired by the gRPC-vs-REST framing ("faster connection = less overhead"). That analogy maps loosely: gRPC saves *transport* overhead (binary framing, multiplexed connections), while LLM token cost is driven by *payload size and repetition*, not protocol. The real levers are:

- **Always-on fixed cost**: `CLAUDE.md` (580 lines) is injected via system reminder on every turn of every session. `memory/MEMORY.md` (95 lines) similarly. These are cache-friendly *within* a session (1hr TTL) but pay full price on every cold start.
- **Invocation-triggered cost**: skill files (`learn` 182 lines, `map-codebase` 165, `bugfix` 160, `code-review` 157 — all over the repo's own 150-line bloat threshold enforced by `slim-skills`) and agent guides (76–104 lines each) only cost tokens when actually invoked/spawned.
- **Unknown**: the user confirmed they do **not** currently know where spend concentrates — cold-start re-reads, long multi-spawn sessions, or verbose report output. No instrumentation exists today.

Non-negotiable constraint: whatever is proposed must not weaken the Hard-Stop Gates or the pipeline's correctness guarantees (`CLAUDE.md`, "Hard-Stop Gates" section) — this is a cost optimization, not a scope-cutting exercise.

---

## Questions for the User

1. Is there an acceptable window for a one-time "measure current spend" pass before any refactor lands (e.g., instrument the next 5–10 sessions), or does a fix need to ship without that data?
2. Are sub-agent spawns (Stage 3) currently re-reading the *full* `PROJECT_SPEC.md` + `TASK_GUIDE` + agent guide even when a prior spawn in the same session already paid that cost — i.e., is there any session-level spawn context reuse today, or does every `Agent()` call cold-start its context?

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | The Simple Path | Trim + cache-stabilize the two always-on files (CLAUDE.md, MEMORY.md) without touching pipeline logic | Low | ~50–100 lines removed | Low | |
| B | The Scalable Path | Instrument real per-stage token spend first, then target fixes at measured hotspots | Medium | ~80 lines (logging convention + audit doc) | Medium | ✅ Yes |
| C | The Minimalist Path | Run `slim-skills` on the 4 oversized skills only; leave CLAUDE.md/MEMORY.md untouched | Low | ~200 lines removed across 4 files | Low | |

### Option A — The Simple Path
**Approach**: Audit `CLAUDE.md` for content that's stable-but-verbose (e.g., the full skill table, repeated agent-template detail) and move rarely-changed detail into a referenced file loaded on-demand rather than always-injected. Keep `CLAUDE.md` itself lean and byte-stable turn-to-turn to maximize cache hits.
**Pros**: Directly attacks the single largest fixed per-turn cost; no new tooling; fast to do.
**Cons**: Purely structural — no evidence yet that CLAUDE.md size is actually the dominant cost vs. spawn overhead; risks silently dropping a rule that's load-bearing (Hard-Stop Gates live in this file).
**Why it might fail**: Without measurement, "the biggest file" isn't proven to be "the biggest cost" — sessions may be short enough that cold-start CLAUDE.md cost is negligible next to a handful of C3 spawns each re-reading 400+ lines of context.

### Option B — The Scalable Path
**Approach**: Add lightweight instrumentation — a per-stage-transition and per-`Agent()`-spawn note (approximate context size, cache-hit vs. cache-miss) written to a scratch audit doc for the next several sessions. Then run a follow-up brainstorm against real numbers to pick the actual fix (could turn out to be Option A, C, or something else — e.g. spawn-prompt dedup).
**Pros**: Matches the user's own answer ("unknown — measure first"); avoids optimizing the wrong thing; produces a defensible before/after comparison.
**Cons**: Slower to show savings; requires a second pass once data comes in; instrumentation itself has a small token cost.
**Why it might fail**: If instrumentation is too coarse (e.g. only total session cost from billing) it won't localize *which* stage/file is the driver — needs to be granular enough per-stage/per-spawn to be actionable, which adds real design work.

### Option C — The Minimalist Path
**Approach**: Run `Skill({ skill: "slim-skills" })` against the four skills already over the repo's own 150-line threshold (`learn`, `map-codebase`, `bugfix`, `code-review`). Ship it as a self-contained cleanup with the checksum gate the skill already provides.
**Pros**: Cheapest to execute — tooling already exists, no new design; zero risk to CLAUDE.md's Hard-Stop Gates; immediately actionable today.
**Cons**: These skills are invocation-triggered, not always-on — trimming them saves tokens only on the (relatively rare) turns they're actually loaded, likely a small fraction of total session spend versus the CLAUDE.md/MEMORY.md fixed cost paid every turn.
**Why it might fail**: Solves a real but probably minor problem while leaving the two suspected larger cost drivers (CLAUDE.md fixed injection, spawn-prompt redundancy) completely unaddressed — cleans the small pile, ignores the big one.

---

## 50% Rule Check

For Option B: instrumentation doesn't need a new dashboard or persistent service. It can piggyback on the existing Memory Write Protocol's diff-driven pass — append one line per stage transition to a scratch log noting approximate context size at that point, using data already visible in the conversation (no new API calls, no new skill scaffolding). That's the ~50%-less-code version: reuse existing memory-write plumbing instead of building a separate telemetry skill.

---

## Recommended Path

**Option B — The Scalable Path**

The user explicitly said they don't yet know where spend concentrates and chose "measure first" over guessing between cold-start cost and spawn-repetition cost. Shipping Option A or C now would be optimizing against a hypothesis, not a measurement — directly against this project's own Karpathy "Ask vs. Guess" principle. Option B is also cheap to de-risk: it's additive-only, doesn't touch CLAUDE.md's Hard-Stop Gates, and produces the evidence needed to make Option A/C (or a different fix entirely) a well-founded follow-up rather than a guess.

---

## Surgical Scope

Files that **should** be touched:
- `memory/learnings.md` — record the instrumentation approach as a new pattern once decided
- A new ephemeral audit doc (e.g. `memory/token-audit-<date>.md`) — per-stage size notes, not a permanent artifact

Files that **must not** be touched:
- `CLAUDE.md` — no trims/edits until data justifies a specific cut; premature edits risk dropping a Hard-Stop Gate
- `.claude/agents/*.md`, `.claude/skills/*/SKILL.md` — no slimming until measurement shows these are actually cost-material relative to CLAUDE.md/spawn overhead

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Instrumentation itself must stay cheap — don't let the audit log grow unbounded across sessions (rotate/cap it)
- [ ] Must distinguish cache-hit reads (near-zero marginal cost) from cache-miss reads (full price) when estimating spend — a naive line-count proxy will overstate cost for cached content
- [ ] Spawn-prompt cost must be measured per sub-agent type (C0 haiku vs C3 opus) since price-per-token differs — raw token count alone won't reflect billing dollars
- [ ] Don't let the measurement pass itself become a recurring manual chore — define a clear stop condition (e.g. "after 5–10 sessions, review and decide")

---

## Next Actions

1. Answer the two open questions above (spawn-reuse behavior today; acceptable measurement window) before Stage 2 planning.
2. If approved, define a lightweight instrumentation task (likely C1, Low risk — no schema/migration, no user-facing surface) and run it through Stage 2 `/plan` as a proper TASK_GUIDE per Hard-Stop Gate 1 (no implementation without a guide).
3. After the measurement window, re-run this brainstorm (or a follow-up) with real numbers to pick between trimming CLAUDE.md, deduping spawn prompts, or slimming oversized skills — possibly a combination.

---

## Evaluation Protocol (approved with direction)

Before/after comparison using the same instrument on both sides:

```
Phase 1: BASELINE   — B's measurement window (5–10 sessions), untouched pipeline
Phase 2: REFACTOR   — whatever the data says (A, spawn-dedup, output trimming…)
Phase 3: VALIDATION — same audit convention, 5–10 more sessions, compare
```

**Metrics (normalized, never raw totals):**
- Tokens per session cold-start (tests CLAUDE.md trim)
- Tokens per sub-agent spawn, grouped by C-level (tests spawn dedup)
- Tokens per Stage 4 review cycle (tests report trimming)
- Cache-hit ratio per session (tests cache stabilization)
- **$ per completed task by C-level** — the bottom-line number

**Data sources:** `/cost` output logged at end of each session (ground truth) + the per-stage audit-log entries (localization). OpenTelemetry export available but deemed overkill for this project.

**Success criterion (set before refactoring):** ≥20% reduction in $ per completed task at the same C-level, no Hard-Stop Gate regressions, measured over 5 sessions post-refactor.

**Rollback trigger:** <5% measured savings in the validation window → revert/stop iterating; guards against endless micro-optimization.

**Known noise:** usage pattern varies per week, cache behavior depends on session timing (1hr TTL), pricing may shift mid-window. 5–10 sessions per side reliably detects a big win (20%+), not a marginal one — acceptable, since an unmeasurable win wasn't worth the refactor.

---

## User Selection

> **Approved direction**: Option B — The Scalable Path (measure first), with Option C (`slim-skills` on the 4 oversized skills) running in parallel during the baseline window as a free rider — safe because skills are invocation-triggered and don't contaminate the always-on cost measurement. Option A deferred until baseline data justifies it.
> Approved by user on 2026-07-17.
