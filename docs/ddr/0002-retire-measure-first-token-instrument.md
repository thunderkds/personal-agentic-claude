# 0002. Retire the measure-first token instrument; candidate refactors already shipped

> **What this is**: A Design Decision Record superseding [DDR-0001](0001-measure-first-token-refactor.md) per its own Amendment 1 clause: *"If the reopened window also comes up short, that conclusion belongs in a superseding DDR, not another amendment."*
> **Gate**: 2-of-3 — (2) surprising without context ✅ (the instrument failed a second time, on a different axis than the first failure), (3) genuine trade-off ✅ (retire vs. re-instrument). Not (1) hard to reverse (additive-only), so not ADR-eligible.

---

**Status**: Accepted
**Date**: 2026-08-05
**Deciders**: hungnguyenhuu (user) · Supervisor
**Related**: [DDR-0001](0001-measure-first-token-refactor.md) · T030 (this analysis) · T040 (event-derived generator) · T049 (CLAUDE.md split) · T029 (slim-skills run)

---

## Context

DDR-0001 committed to measuring token spend before refactoring for it, with a ≥20% $/task reduction success criterion and a <5% rollback trigger, evaluated against `/cost` ground-truth lines pasted manually at each session's end. Amendment 1 (2026-07-21) already recorded one instrument failure — the manual convention produced 1 of 7 required sessions in 4 days — and replaced hand-typed entries with an automated generator (`scripts/token-audit.sh`, T040) deriving event-stream entries (cold-start / stage transitions / spawns) from `memory/event-trace/*.jsonl`.

T030 (this task) is the first attempt to actually read that data and evaluate the success criterion. It found a second, more fundamental failure: **the `/cost` ground-truth line — the one figure the success/rollback criteria are computed from — was never pasted into either window's report, not once.** The automated half of the instrument worked (105 event entries in window 1, 7 in window 2, both correctly tagged by task/cache/stage), but it was only ever half the instrument. Amendment 1 explicitly flagged this as a "known ceiling" requiring a manual paste; that manual step failed exactly the same way the original per-session logging convention failed in Amendment 1 — nobody was nagged to do it, so nobody did.

Window 1's report additionally turned out to not be scoped to the reopened window at all: it contains unfiltered trace history back to 2026-07-14 (before DDR-0001 existed), because T050's `--window-start` flag defaults to unfiltered for back-compat and was never passed when the file was regenerated. The "4/7 sessions" closure basis recorded in memory conflated distinct calendar dates in that file with actual logged sessions.

Separately — and this is the material fact driving the decision below — both candidate refactors DDR-0001 was gatekeeping have **already shipped**, for reasons unrelated to token cost:
- **Option A** (trim/cache-stabilize `CLAUDE.md`): completed by **T049** (2026-08-04), which split CLAUDE.md 565→198 lines into `docs/claude-md/*.md` files, motivated by readability/maintainability, not token spend. Current `CLAUDE.md` is 198 lines.
- **Option C** (`slim-skills` run): completed by **T029** (2026-07-19) — `learn` 182→128, `map-codebase` 165→130; `bugfix`/`code-review` were already at or near the repo's 150-line floor.

There is no third candidate refactor still pending a decision. The thing DDR-0001 was built to gate no longer has a decision to make.

## Decision

We **retire the measure-first token-audit program**. `T030` closes as moot, not merely unblocked-then-skipped: not because the measurement failed (though it did, twice, on two different axes), but because the refactors it was gatekeeping already happened for independent reasons and there is nothing left to decide against a $/task threshold.

We do **not** re-instrument. A third attempt at automatic-or-manual `/cost` capture is not justified: the workflow has now failed to sustain a manual per-session logging step twice in a row (Amendment 1's entry convention, and this DDR's `/cost` paste), which is itself evidence that manual instrumentation doesn't survive contact with this workflow regardless of how it's specified.

`reports/token-audit_2026-07-21.md` and `reports/token-audit_2026-08-04.md` are retained as-is (historical record of both failure modes) but no new window opens. `scripts/token-audit.sh` / `token_audit.py` are left in place (T040/T050 working code, harmless if unused) but are no longer invoked as part of any active measurement window.

If token/billing cost becomes a concern again in the future, the right instrument is a **structural, automatic** cost source (e.g., a platform-level billing export or API usage log the Supervisor can read directly) — not a step that depends on a human remembering to paste a number at the right moment. That is a new problem for a new DDR when and if it recurs, not a reason to keep this one open.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| Retire — accept A/C already shipped, close moot | No further wasted instrumentation effort; honest about a repeated manual-step failure; nothing left to decide | Never actually validates DDR-0001's ≥20% hypothesis with real numbers | **Selected** — the hypothesis is now untestable *and* moot at once; chasing it further has no payoff |
| Re-instrument a 3rd window with a stricter manual `/cost` nag | Might finally get real numbers | Same manual-step failure mode twice already; no reason to expect a 3rd attempt succeeds; both candidate refactors already shipped so there's nothing to validate against even with data | Rejected — fixing the process without a live decision left to inform is optimizing a hypothesis nobody needs anymore |
| Build automatic cost capture now (billing API / export) | Solves the root cause (manual step is the failure point) | No such source is currently available to the Supervisor; speculative scope for a problem that isn't currently blocking anything | Deferred — becomes a live decision only if cost concern resurfaces |

## Consequences

### Positive
- T030 closes with a clear, honest answer instead of staying blocked indefinitely on data that will never arrive
- No further effort sunk into a measurement convention that has now failed twice
- The two refactors DDR-0001 cared about did in fact happen — just not because of this instrument

### Negative (accepted trade-offs)
- DDR-0001's ≥20%/<5% hypothesis is never confirmed or denied with real data — permanently open question
- If a future refactor is proposed for token-cost reasons, there is no baseline to compare against; it will need fresh judgment, same as DDR-0001 explicitly tried to avoid

### Follow-up
- [x] T030: closed as moot (this DDR is the deliverable)
- [ ] If token/billing cost resurfaces as a concern: new DDR proposing a structural (non-manual-step) cost source before any further refactor gate

---

**Amends**: This record supersedes DDR-0001 in full. DDR-0001's Status is updated to `Superseded by DDR-0002` (see cross-reference below); its Context/Decision/Consequences sections are left intact as history.
