# TASK_GUIDE — T051: Create root AGENTS.md for Codex/cross-CLI auto-read
**Date**: 2026-08-04
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Complexity is **C1** — 1-2 new/changed files, known pattern (mirrors T049's `docs/claude-md`
   MANIFEST precedent), no design decision left open (already resolved via brainstorming +
   grill-with-docs, see `memory/decisions.md` "Root AGENTS.md — create it for real")

---

## Requirement (Pillar 1 — Adapt the requirement)

User (2026-08-04, via `/brainstorming` then `/grill-with-docs`, approved): create a static root
`AGENTS.md` so Codex CLI auto-reads it without the user having to manually prompt Codex to
generate one each session. `docs/MULTI_AGENT.md` already sketches this under "Optional: a shared
AGENTS.md" but the file was never actually created.

**Restated intent**: Ship the `AGENTS.md` file the existing docs already describe — a thin mirror
of `.claude/agents/general-agent-template.md`'s essentials (not a second source of truth) — at this
repo's root, AND add it to `MANIFEST` so `setup.sh`/`update.sh` deploy it to every downstream
project too (user-approved scope, not repo-local-only).

**Out of scope**:
- No changes to `general-agent-template.md`'s actual rules content — this task only adds a footer
  staleness-guard note (see Approach) pointing at `AGENTS.md`, it does not rewrite the template.
- No generator script (brainstorming converged on static file — a ~15-line mirror doesn't justify
  generator machinery per Simplicity First).
- No changes to the Codex/Cursor dispatch recipes already in `docs/MULTI_AGENT.md` — only its
  "Optional: AGENTS.md" section needs updating to say the file now exists (was previously phrased
  as a suggestion to create one yourself).

**Requirement Refs**: No `PRD.md` (framework self-maintenance, same as T049/T050). Traceability:
user's confirmed request + `memory/decisions.md`'s "Root AGENTS.md — create it for real" entry.

### Requirement Fidelity Gate
- [x] Restated intent confirmed to match the user's request (grill-with-docs dialogue, user approved)
- [x] Domain terms align — "thin mirror, not a second source of truth" is `docs/MULTI_AGENT.md`'s
      own existing phrasing, reused verbatim
- [ ] Every Acceptance Criterion below traces to a line in the Requirement — agent verifies before starting

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `AGENTS.md` (repo root) — the literal filename Codex CLI auto-reads. Also
`Standalone` in the sense that no application code calls it; it's read by an external tool.

---

## Acceptance Criteria

| # | Criterion | Traces to |
|---|---|---|
| 1 | `AGENTS.md` exists at repo root, containing at minimum the 4 bullets `docs/MULTI_AGENT.md` already sketches (read `PROJECT_SPEC.md`/`TASK_GUIDE`/base rules first; work only in assigned worktree, touch only predicted files; build test-first, done only when verification passes; stop and ask on ambiguity — never guess) | "create AGENTS.md" |
| 2 | `MANIFEST` gains an `AGENTS.md` line so `setup.sh`/`update.sh` deploy it | user-approved scope: not repo-local only |
| 3 | `general-agent-template.md` gains a short footer note: if its Base Rules/Karpathy Principles change, check `AGENTS.md` is still an accurate thin mirror | staleness-guard from the brainstorming decision (no generator, so a manual reminder is the mitigation) |
| 4 | `docs/MULTI_AGENT.md`'s "Optional: a shared AGENTS.md" section is updated to reflect the file now exists (drop the "if you want... create a root AGENTS.md" framing; point at the real file instead) | keep docs from contradicting reality |
| 5 | `AGENTS.md` explicitly states it is a thin mirror and `CLAUDE.md` + `.claude/agents/` remain canonical — so a future reader doesn't treat it as a second source of truth | brainstorming's explicit non-negotiable |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|---|---|---|
| 1 | Repo root | `AGENTS.md` file exists, non-empty, contains all 4 base-rule bullets | automated: grep for each bullet's key phrase |
| 2 | `MANIFEST` | Contains a line `AGENTS.md` | automated: grep |
| 3 | `general-agent-template.md` | Contains a footer note mentioning `AGENTS.md` | automated: grep |
| 4 | `docs/MULTI_AGENT.md` | No longer says "if you want... create a root AGENTS.md" (past-tense/present-tense framing updated) | manual read |

### Verification Command

```bash
test -f AGENTS.md && echo "AGENTS.md exists"
grep -q "^AGENTS.md$" MANIFEST && echo "MANIFEST updated"
grep -qi "AGENTS.md" .claude/agents/general-agent-template.md && echo "template footer present"
grep -qi "canonical" AGENTS.md && echo "non-second-source-of-truth statement present"
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes |
|-------|--------|-------|
| **New test(s) cover Acceptance Criteria** | ☐ pass / ☐ fail | docs-only task — verification script above is the "test"; no unit-test framework applies |
| Verification command run | ☐ pass / ☐ fail | paste real output |
| Negative cases hold | ☐ pass / ☐ fail | confirm `AGENTS.md` does NOT duplicate the full Karpathy Principles table or Hard-Stop Gates — thin mirror only, per non-negotiable |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to blast radius | ☐ pass / ☐ fail | `AGENTS.md`, `MANIFEST`, `general-agent-template.md`, `docs/MULTI_AGENT.md` only |
| Full smoke suite still green | ☐ pass / ☐ fail | `pytest .claude/hooks/tests/` — no hook code touched |
| UI rows | ☑ N/A | no UI |

---

## Approach

**Pattern reference**: `docs/MULTI_AGENT.md` lines 100-113 ("Optional: a shared AGENTS.md") — the
exact 4 bullets to mirror are already written there; don't re-derive them from scratch. Also
`memory/decisions.md` T049 entry — same MANIFEST-addition pattern for a new deployable root/path.

**AGENTS.md suggested shape** (agent may adjust wording, must keep the 4 bullets + canonical-pointer
statement from AC5):

```markdown
# AGENTS.md

This is a thin mirror for non-Claude agentic CLIs (Codex, etc.). `CLAUDE.md` and
`.claude/agents/` remain canonical — if anything here conflicts with those, they win.

Before any work:
- Read `PROJECT_SPEC.md`, your `tasks/TASK_GUIDE_Txxx.md`, and these base rules.
- Work only inside your assigned worktree; touch only the predicted files (Surgical Changes).
- Build test-first; a task is done only when its verification command passes.
- Stop and ask on any ambiguity — never guess.

See `docs/MULTI_AGENT.md` for full dispatch recipes and what does/doesn't port across CLIs.
```

**Footer note for `general-agent-template.md`** (append near the end, don't restructure the file):
a one-line reminder that edits to Base Rules/Karpathy Principles should be checked against
`AGENTS.md` for staleness — mirrors the pattern used for `CLAUDE_LEGACY.md` sync policy.

---

## Edge Case Checklist

- [ ] `AGENTS.md` must not duplicate the full Karpathy Principles table, Hard-Stop Gates, or
      pipeline stages — that would make it a second source of truth, the exact failure mode
      `docs/MULTI_AGENT.md` already warns against
- [ ] Confirm `setup.sh`'s MANIFEST-copy loop handles a single top-level file entry correctly
      (not just directories) — check an existing single-file MANIFEST-style precedent or read
      `lib/harness-fetch.sh`'s `harness_copy_manifest` before assuming
- [ ] Don't touch the Codex/Cursor dispatch recipe code blocks in `docs/MULTI_AGENT.md` — only the
      "Optional: AGENTS.md" section's prose

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `AGENTS.md` | New — thin mirror per Approach |
| `MANIFEST` | Add `AGENTS.md` line |
| `.claude/agents/general-agent-template.md` | Add footer staleness-guard note |
| `docs/MULTI_AGENT.md` | Update "Optional: a shared AGENTS.md" section to reflect the file now exists |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md`, `docs/claude-md/*.md` | Out of scope — this task is about non-Claude CLI support, not the Claude-side pipeline docs |
| Codex/Cursor dispatch recipe code blocks in `docs/MULTI_AGENT.md` | Already correct, out of scope |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not mandated (Low risk)
- [ ] Tests written AND pass — verification script output pasted into Evidence
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (new decision: AGENTS.md shipped)
- [ ] Supervisor notified: ready for Stage 4 review
