# TASK_GUIDE — T260: `self_review.py` keeps dropped and over-cap patterns for the next run; report path text fixed
**Date**: 2026-11-05
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `docs/prd/PRD_self-review.md` (FR-004..FR-007), `skills/self-review/SKILL.md`, `skills/self-review/scripts/self_review.py` (`evaluate`, `cmd_post`, `render_report`, `read_register`) and `tasks/TASK_REVIEW_T255.md` / `tasks/TASK_REVIEW_T256.md` (Stage 4 fix round 1, auto verify finding)

---

## Requirement (Pillar 1 — Adapt the requirement)

Registered 2026-11-05 by the user ("yes") after the first real `/self-review` run (report `reports/self-review/self-review-20261105T082737.md`, local only; miner output kept in the Supervisor scratchpad as `sr1_miner.json`). That run exposed three defects:

1. **In-run duplicate check drops a distinct pattern.** `evaluate()` drops a pattern as `repeats <fp> from this run` when its task set has Jaccard >= 0.5 with an already-kept pattern. `unverified-guide-or-report-claim` (T082, T083, T085, T105, T109: Supervisor guide premises and report claims not checked against source) was dropped as a repeat of `vacuous-assertion-or-noop-mutation-control` (8 tasks). Different defect, overlapping tasks. Task overlap alone is not sameness: reviews with many findings appear in many patterns.
2. **Over-cap patterns are lost.** `cmd_post` keeps `kept[CAP:]` only as one report line (`## Beyond the cap (not recorded, not proposed)`). The watermark moves past their files, so a later run never sees that evidence again. `pre-existing-red-baseline` (T094, T099, T101, T102, T103, T109) was lost this way. The same applies to a pattern the in-run check wrongly dropped.
3. **SKILL text is wrong about the report.** `skills/self-review/SKILL.md:73` says the report (`reports/self-review/`) is git-tracked. `.gitignore:46` ignores `reports/*`, so the report stays local; only the register is committed.

Also, from the T256 auto verify (`.claude/verify-runs/T256-84d1ee929c71.log`, minor): two `post` runs in the same second write the same report path, and the second overwrites the first.

**Restated intent**:
> A real recurring pattern the miner found with valid citations must not vanish because of the 3-per-run cap or a too-coarse duplicate check. Keep it in the register so a later run proposes it, without breaking the no-loop guarantee (FR-003, FR-005) or the cap (FR-006). Make the skill text say the truth about which output is tracked.

**Out of scope**:
- Re-injecting the two patterns lost on 2026-11-05 (the watermark has moved past their files). The Supervisor may re-run on those files after merge only if the user asks.
- Changing `MIN_TASKS`, `CAP`, the file cap or the miner prompt's ranking rule.
- Committing the report (keep `reports/*` ignored), any hook, any other skill.

**Requirement Refs**: `docs/prd/PRD_self-review.md` FR-004, FR-005, FR-006, FR-007; `skills/self-review/scripts/self_review.py` `evaluate` / `cmd_post`; `skills/self-review/SKILL.md:73`; `.gitignore:46`; `.claude/verify-runs/T256-84d1ee929c71.log`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user said "yes" 2026-11-05 to the three named problems
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T255, T256 (merged)

**Entry point**: `python3 skills/self-review/scripts/self_review.py post` (called from `skills/self-review/SKILL.md` Step 3)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | In-run duplicate: a pattern is a repeat of an already-kept pattern only if the fingerprints are equal, OR task-set Jaccard >= 0.5 AND title-word Jaccard >= 0.5. A test with the 2026-11-05 shape (5-task pattern inside an 8-task pattern, different titles) keeps both; a test with near-identical title and tasks still drops one. | defect 1 |
| 2 | A kept pattern beyond the cap is written to the register in a new state `waiting` (with tasks, title, file), and the report says so (`## Waiting for a later run`). It is not a proposal in this run: the run still shows at most 3 (FR-006). | defect 2 |
| 3 | A later `post` proposes `waiting` rows before new patterns from that run, ranked with the rest by task count, within the cap of 3. A proposed `waiting` row becomes `open`. Its evidence is the citations already checked when it was recorded (store what the report needs, or re-check them at head); it is not dropped because its files are older than the watermark. | defect 2 |
| 4 | A miner pattern matching a `waiting` row (fingerprint, `matches`, or the title-word hold) does not create a second row; the run counts it as that row. `decide` still acts only on `open` rows; `waiting` is never shown as "Still open". | no-loop FR-005 |
| 5 | `pre` with no new review files still stops with `nothing-new` even when `waiting` rows exist (no miner call). `post` with no new files but with `waiting` rows: decide in the guide's Approach and pin by test (recommended: `pre` reports `waiting: N` and the skill tells the user to run again after the next review lands, no miner call). | FR-003 |
| 6 | An old register without `waiting` rows reads unchanged; an unknown state still fails as before. | compatibility |
| 7 | Two `post` runs in the same second write two report files (no overwrite). | T256 verify finding |
| 8 | `skills/self-review/SKILL.md` Step 6 says the register is tracked and must be committed, and the report is local only (`reports/*` is gitignored). `docs/prd/PRD_self-review.md` FR-005 lists the `waiting` state. | defect 3 |
| 9 | Tests pin AC 1-8; full suite green. | all |

---

## Evaluation & Acceptance

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests/ .claude/hooks/tests/
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T260.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T260.md`. BEFORE: run `post` on a temp repo with a miner file holding the 2026-11-05 shape (two patterns, overlapping tasks, different titles) plus 4 qualifying patterns; show one `repeats ... from this run` drop and the `Beyond the cap (not recorded, not proposed)` line, and that the register has no row for them.

---

## Approach

**Vital slice**: the `waiting` state and the two-key duplicate check. Keep the register format one table; add one state, no new columns unless the stored citations need one (prefer re-checking citations at the head the row was recorded at, kept in an existing cell, over a new file).

**Chosen (AC 5)**: no new review file means no proposal, with or without `waiting` rows. `pre` still says `nothing-new` (no miner call) and adds `"waiting": N` to its JSON; the skill tells the user how many rows wait. `post` with no new files leaves every `waiting` row as it is (no re-check, no proposal) and lists it under `## Waiting for a later run`. Reason: FR-003 says no new file means no work, and `post` on `{"patterns":[]}` is the documented way to skip files, so it must not start proposals. Pinned by `test_t260_ac5_pre_with_no_new_files_stays_nothing_new_and_reports_waiting` and `test_t260_ac5_post_with_no_new_files_proposes_no_waiting_row`.

**Built**: one table, optional 8th column `detail` (JSON: head the evidence was checked at, label, proposed change, `file:line:text` per citation). The table has 8 columns only while a `waiting` row exists; otherwise the register stays at 7 columns, byte-for-byte as before. A `waiting` row is re-checked at the head it was recorded at (the cited line must still hold the stored text there), so moved or edited lines never pass; fix-task review citations are dropped (FX-2); a row left with < 3 tasks is removed and reported under `## Dropped`. Ranking: `waiting` rows first (task count, then register order), then new patterns (task count, then fingerprint), cap 3. A regressed pattern beyond the cap also becomes `waiting` (its fix task is forgotten, as when it becomes `open`) and comes back labelled `regressed`. The default report name gets `-2`, `-3` ... when the same-second name exists (the file is reserved with `O_EXCL`).

**Cut list**: no update of a `waiting` row from new miner evidence (a repeat is dropped as the row, FR-005); no automatic expiry of old `waiting` rows; the 2026-11-05 lost patterns are not re-injected (out of scope).

---

## Edge Case Checklist

- [ ] A `waiting` row whose cited files were later changed: the quote check must not silently pass on moved lines
- [ ] A `waiting` row and a new pattern that is its duplicate in the same run
- [ ] More than 3 `waiting` rows: the oldest stay `waiting`, nothing is lost
- [ ] Fix-task review citations stay dropped (FX-2) for `waiting` rows too
- [ ] Register written atomically after the report (FR-007 order unchanged)
- [ ] Pin tests on edited files (`tests/test_self_review*.py`, skill-list / site pins, Codex 8 KB cap on `SKILL.md`)
- [ ] ASD-STE100 for report text a human reads

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/self-review/scripts/self_review.py` | two-key in-run dedupe; `waiting` state; propose waiting first; unique report name |
| `skills/self-review/SKILL.md` | Step 6 tracked/local text; one line on `waiting` |
| `docs/prd/PRD_self-review.md` | FR-005 adds `waiting` |
| `tests/test_self_review.py` | tests for AC 1-7 |
| `tests/test_self_review_skill.py` | text pin for AC 8 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/self-review/register.md` | live register; written only by `self_review.py` on a real run |
| `.gitignore`, `.claude/hooks/*`, `.claude/settings.json` | out of scope |
| `skills/self-review/references/miner-prompt.md` | miner contract unchanged |

---

## Test Plan

Unit + CLI tests on a temp git repo (same harness as T255). Full suite green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T260.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
