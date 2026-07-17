# TASK_GUIDE — T030: Post-baseline analysis — pick the token refactor from real data
**Date**: 2026-07-17
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Supervisor + user (HITL — analysis and decision task; no sub-agent spawn, no code written under this guide)
**Agent guide**: N/A — Supervisor-level task; process defined by DDR-0001 and this guide

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` (glossary: Token Audit Log, Measurement Window, Cold-start cost, $ per completed task)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `docs/ddr/0001-measure-first-token-refactor.md` — thresholds and window rules
5. Read the closed-window `reports/token-audit_2026-07-17.md` in full — it is the primary input

---

## Requirement (Pillar 1 — Adapt the requirement)

Per DDR-0001: when the baseline Measurement Window closes (7 logged sessions or 14 calendar days after T028 lands, whichever first), analyze the Token Audit Log and select the actual refactor — or conclude none is warranted.

**Restated intent**:
> Compute the normalized metrics from the baseline window, identify where spend actually concentrates, and run a follow-up brainstorm against those numbers to choose between: trimming CLAUDE.md (deferred Option A), spawn-prompt dedup, report-output trimming, or explicitly stopping ("savings too small to refactor for"). Record the outcome as DDR-0002 (or a status update on DDR-0001 if the outcome is "stop").

**Out of scope**:
- Implementing the chosen refactor — that gets its own Stage 2 task(s) with fresh TASK_GUIDEs
- Extending the window "for more data" beyond the close condition — the window rule exists to prevent stalling; if data is thin, that itself is a finding

**Requirement Refs**:
- No `PRD.md` FR applies — internal framework task. Traces to DDR-0001 Follow-up items 2–3.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (BRAINSTORMING_LOG.md User Selection + DDR-0001, 2026-07-17)
- [x] Domain terms align with glossary (all four metric terms locked this session)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A precedent confirmed

---

## Dependencies & Reachability

**Depends on**: T028 — the Token Audit Log scaffold must exist AND its Measurement Window must have closed (7 sessions or 14 days)
**Entry point**: Standalone — N/A: decision/analysis task; output is a DDR + a follow-up brainstorm, not reachable code.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Window-close condition verified and stated (session count or day count, with dates) before any analysis begins | "when the baseline window closes" |
| 2 | All four normalized metrics computed from the log and presented: cold-start tokens/session, tokens/spawn by C-level, tokens/Stage-4 cycle, $ per completed task by C-level (with `/cost` ground-truth reconciliation) | "compute the normalized metrics" |
| 3 | A follow-up `brainstorming` session runs against the numbers and the user selects a direction (a refactor OR explicit stop) | "choose between…" |
| 4 | The decision is recorded: DDR-0002 if a refactor is chosen (2-of-3 gate re-checked), or DDR-0001 status/consequences updated if the outcome is "stop" | "record the outcome" |
| 5 | Negative: if fewer than 3 sessions were logged (discipline failed), the analysis reports the instrument failure honestly instead of extrapolating from noise | measurement integrity |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Closed-window audit log | metrics table in the analysis output, each number traceable to log lines | manual review by user |
| 2 | Metrics table | user-approved direction recorded in BRAINSTORMING_LOG.md + DDR | document check |
| 3 | Log with <3 sessions | analysis declares data insufficient; no refactor recommendation issued | manual review |

### Verification Command (exact, runnable)

```bash
ls docs/ddr/ && grep -c "^2026" reports/token-audit_2026-07-17.md
```

> Hard-Stop Gate 5 note: this is a Supervisor-level analysis/decision task producing documents, not code — no test suite applies. The oracle is the user's approval of the metrics table and direction (AC 3), plus the DDR artifact (AC 4). Any refactor chosen here gets its own TASK_GUIDE with full test gates. Supervisor signed off on this oracle at Stage 2.

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [oracle = user-approved metrics table + DDR path, per Gate-5 note above] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [insufficient-data path honored if triggered] |
| verify | ☐ pass / ☐ fail | [direction recorded and DDR readable] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | [no code touched — expect trivially green] |
| **UI: Visual regression** | ☐ N/A | no UI component |
| **UI: Design-system compliance** | ☐ N/A | no UI component |
| **UI: Responsiveness** | ☐ N/A | no UI component |

---

## Approach

Analysis before advocacy: compute all four metrics first, *then* brainstorm — never reverse the order (prevents anchoring on a favorite fix). Apply DDR-0001's decision rules mechanically: a candidate refactor is only recommendable if the metric it targets is a material share of measured spend; the ≥20%/<5% thresholds govern the *later* validation window, not this selection step. "Stop — not worth it" is a first-class outcome, not a failure.

---

## Edge Case Checklist

- [ ] Sessions where audit entries were forgotten mid-session — partial data must be flagged per-session, not silently averaged in
- [ ] `/cost` totals vs. summed entry estimates will disagree — reconcile to `/cost` as ground truth; entry estimates only localize proportions
- [ ] Model/pricing changes during the window would skew $-comparisons — note any that occurred
- [ ] T029's skill pruning lands mid-window — it only affects invocation-triggered costs; confirm it isn't misread as an always-on cost change
- [ ] If the window closed by the 14-day cap with very few sessions, low activity itself argues against any refactor (little spend to save)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `BRAINSTORMING_LOG.md` | follow-up brainstorm session output |
| `docs/ddr/0002-*.md` OR `docs/ddr/0001-measure-first-token-refactor.md` | new DDR for chosen refactor, or status update on stop |
| `memory/decisions.md` | one-liner + DDR pointer |
| `memory/MEMORY.md` | hot-tier one-liner; remove/close the T028 logging-reminder line |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | still deferred — only a *subsequent* implementation task (with its own guide) may touch it |
| `.claude/skills/*/SKILL.md`, `.claude/agents/*.md` | analysis task writes no implementation |
| `reports/token-audit_2026-07-17.md` | closed-window data is read-only evidence — never edited post-close |

---

## Test Plan

Document-level verification only (per Gate-5 note): metrics table user-approved; DDR written/updated and linked from `memory/decisions.md`; insufficient-data path honored if applicable.

---

## Completion Checklist

- [ ] Window-close condition verified and stated
- [ ] Four metrics computed and reconciled to `/cost`
- [ ] Follow-up brainstorm run; user selected a direction
- [ ] DDR-0002 written (or DDR-0001 updated) + `memory/decisions.md` pointer
- [ ] `PROJECT_KANBAN.md` updated
- [ ] If a refactor was chosen: Stage 2 re-entered to generate its TASK_GUIDE(s)
