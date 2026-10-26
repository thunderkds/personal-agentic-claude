# TASK_GUIDE — T176: Kit-arms experiment, part 2 — run the 36 cells under the $60 cap and report against the pre-registered rule
**Date**: 2026-10-26
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: this task spends real money (cap $60) and launches agents. It changes no kit file.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt. Read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely, and `tasks/TASK_GUIDE_T175.md` (what was built)
4. Read `agents/common-infrastructure.md`
5. Read `experiments/kit-arms/RULE.md` — the rule is frozen; you apply it, you never edit it

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-26: "2, I want to have a full picture" — a measured comparison of the full kit, a minimal kit and plain Claude Code. Decisions D1–D4 are in `tasks/TASK_GUIDE_T175.md` (3 arms, fixture app, $60 cap, split build/run).

**Restated intent**:
> Run the T175 experiment once, as pre-registered (6 tasks × 3 arms × 2 runs = 36 cells, cap $60), and
> report what each layer of the kit adds — correctness, safety, scope, cost, time — with the frozen
> rule's verdicts, so the user can decide what to keep, slim or cut.

**Out of scope**: changing `RULE.md`, the fixture, the tasks or the oracles after the first paid run; changing the kit; re-running cells to "improve" a result (a crashed run is re-run once and the crash is reported).

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-26)
- [x] Terms as in T175 (arm, oracle, cell)
- [x] Every AC traces to the Requirement
- [x] Refs covered

---

## Dependencies & Reachability

**Depends on**: T175 — the runner, fixture, oracles and the committed `RULE.md` must be in `main`, and the user must have read `RULE.md`, `arms/minimal-AGENTS.md` and the 6 prompts.

**Entry point**: `experiments/kit-arms/run_arms.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | All 36 cells run with `run_arms.py --runs 2 --cap 60 --yes` from a scratch copy, on one model for all arms (the model is named in the report); total spend ≤ $60.00, read from the persisted spend file. If the cap stops the run early, the report says which cells did not run and applies the rule only to complete task × arm pairs. | D3 |
| 2 | `experiments/kit-arms/results/` holds the raw JSON (every run's row: cost, tokens, wall time, turns, final text, diff stat, verdict) and `REPORT.md`: per-arm totals, per-task table, the Q1/Q2 verdicts exactly as `RULE.md` defines them, the small-sample caveat, and 3–5 short excerpts of agent behaviour that explain a result (e.g. what each arm did on task 4 and task 5). | full picture |
| 3 | `RULE.md` is byte-identical to its pre-registration commit (`git diff <that commit> -- experiments/kit-arms/RULE.md` empty). | method |
| 4 | Isolation held: the main checkout's `git status --porcelain` is unchanged after the batch; no arm copy is left under the repo. | Risk |

### Verification Command

```bash
git diff "$(git log --format=%h -1 -- experiments/kit-arms/RULE.md)" -- experiments/kit-arms/RULE.md | wc -l && python3 -c "import json;d=json.load(open('experiments/kit-arms/results/spend.json'));print(d['total_usd']);assert d['total_usd']<=60" && test -s experiments/kit-arms/results/REPORT.md
```

### Evidence

> **Moved.** Filled by the reviewer in `tasks/TASK_REVIEW_T176.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T176.md`.

---

## Approach

**Pattern reference**: T171's round-4 run (`feat/t171-context-search-bench`, `0fe8311` → `8c55e7a`): rule frozen first, one batch, report against the rule.
**Vital slice**: the batch run + `REPORT.md` with the rule's verdicts.
**Cut list**: charts; extra runs beyond 2 per cell; cross-model comparison.

---

## Edge Case Checklist

- [ ] A run that hits the kit's step-limit hook or asks a question at once is a valid outcome — grade it, do not re-run it.
- [ ] A crashed run (no JSON from `claude -p`) is re-run once; a second crash is reported as `crash` and scored 0.
- [ ] Spend estimate vs actual drifting high: stop at the cap, report partial results honestly.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `experiments/kit-arms/results/*.json`, `REPORT.md` | results (new) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `experiments/kit-arms/RULE.md`, `fixture/`, `tasks/`, `oracles/`, `arms/` | frozen by T175 |
| every kit file | the kit is the thing measured |

---

## Test Plan

No new code; the Verification Command checks rule freeze, cap and report presence. The Supervisor reads `REPORT.md` against the raw JSON (spot-check 6 rows) at Stage 4.

---

## Completion Checklist

- [ ] Batch run done within cap
- [ ] `REPORT.md` written against the frozen rule
- [ ] Supervisor spot-check of raw rows
- [ ] `Skill({ skill: "verify" })` (user-only)
- [ ] Supervisor notified

---

## Questions Log
