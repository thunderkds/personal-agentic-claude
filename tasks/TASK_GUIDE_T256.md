# TASK_GUIDE — T256: `self-review` skill — run the miner between `pre` and `post`, approvals become tasks
**Date**: 2026-11-05
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
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
6. Read `docs/prd/PRD_self-review.md`, `tasks/TASK_GUIDE_T255.md` (the CLI contract), `skills/write-better-skill/SKILL.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Same user request and PRD as T255 (`docs/prd/PRD_self-review.md`, Path B). This task writes the skill that drives T255's script: run `pre`; only if `ready`, spawn one Sonnet miner; run `post`; show the proposals; record the user's decisions; draft a Kanban row + TASK_GUIDE for each approval. It also makes `self-review` the only owner of kit-change proposals.

**Restated intent**:
> `/self-review` runs `self_review.py pre`. On `nothing-new` it prints that line and stops — no `Agent` call. On `ready` it spawns exactly one `general-purpose` Agent on `model: sonnet` with the miner prompt and the file list, runs `post`, shows at most 3 proposals with their citations, asks the user approve/reject for each, runs `decide`, and for each approval writes a LR with `source: agent` and drafts the kit task through the Stage 2 path. `learn` Step 8 no longer proposes kit changes.

**Out of scope**:
- The script itself (T255). Any hook, schedule or auto-start (FR-001). Upstream/network actions.
- Fixing any pattern the first run finds.

**Requirement Refs**: FR-001, FR-007 (skill side), FR-008, FR-009, NFR-001 (Sonnet, one miner), NFR-002 (data boundary in the prompt).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user 2026-11-05 (PRD, Path B)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (terms as in T255)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in the PRD and are covered

---

## Dependencies & Reachability

**Depends on**: T255 — `skills/self-review/scripts/self_review.py` with the `pre` / `post` / `decide` CLI

**Stacked (Supervisor 2026-11-05):** this branch `feat/t256-self-review-skill` starts from `feat/t255-self-review-script`. T255 alone leaves `skills/self-review/` without a `SKILL.md`, which turns 14 suite tests red (skill-spec conformance, validate.sh, site skill counts/chips — list in T255's hand-back). T255 and T256 are reviewed and merged together. **The full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` must be green on this branch** — that is AC 10. T255's CLI contract as built is in `skills/self-review/scripts/self_review.py` (`pre` JSON adds `dropped_same_commit`; `post` takes `--max-files`; `post` exit 1 when the report cannot be written).

**Entry point**: `/self-review`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `skills/self-review/SKILL.md` exists with `name: self-review`, a description that says it is started only by the user, and a body under the Codex 8 KB cap. | FR-001 |
| 2 | The SKILL.md workflow calls `pre` first and says, as a rule, that on `nothing-new` the skill stops before any `Agent` call. | FR-003 |
| 3 | The SKILL.md names exactly one miner spawn: `subagent_type: general-purpose`, `model: sonnet`, prompt = `references/miner-prompt.md` + the `pre` file list; the miner writes JSON to the session scratchpad, never into the repo. | NFR-001, FR-002 |
| 4 | `references/miner-prompt.md` is the spike's `MINER_PROMPT.md` adapted: input = the given file list only; register rows passed in as known patterns; review text is data, never instructions (`docs/claude-md/untrusted-content-boundary.md`). | FR-002, FR-005, NFR-002 |
| 5 | The SKILL.md says: approvals via `decide`; each approval → LR with `source: agent` (via `learn`'s LR format) + a Kanban row and TASK_GUIDE drafted through the Stage 2 path; the skill never edits other kit files, commits to `main`, merges or pushes. | FR-008, FR-009 |
| 6 | `skills/learn/SKILL.md` Step 8 says kit-change proposals belong to `self-review`; Step 8 keeps only its project-level skill stub. | FR-009 |
| 7 | `AGENTS.md` cross-cutting skill list names `self-review`; every test that pins the skill list (e.g. `tests/test_plugin_names.py:648`) passes. | discoverability |
| 8 | No file under `.claude/hooks/`, `hooks/hooks.json` or `.claude/settings.json` mentions `self-review` (grep test). | FR-001 |
| 10 | Full suite green on this stacked branch, including the 14 tests T255 left red. | stacked merge |
| 9 | Real run: `/self-review` on this repo returns `ready`, spawns one miner, `post` writes a report with <=3 patterns whose citations pass; a second `/self-review` straight after prints the nothing-new line and spawns no Agent (event trace shows 0 `Agent` records for the second run). | US-003, PRD success metrics |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Skill files written | AC 1-8 structural checks pass | automated test (`tests/test_self_review_skill.py`) |
| 2 | This repo, empty register | first run: report, <=3 proposals; second run: nothing-new, 0 Agent | real run, output pasted |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests/test_self_review_skill.py tests/test_self_review.py tests/test_plugin_names.py
# ci: skip for AC 9 — needs a live model run; evidence pasted in TASK_REVIEW_T256.md
```

---

## Approach

**Pattern reference**: `skills/score/SKILL.md` — a skill that runs a script, then a model step, then writes one record; `skills/learn/SKILL.md` — LR format to reuse.

**Vital slice**: the `pre` → (stop | one miner) → `post` → `decide` workflow text (AC 2, 3, 5).
**Cut list**: no HTML report; no `/self-review` slash-command file beyond the skill itself unless a test requires it.

---

## Edge Case Checklist

- [ ] `pre` exits non-zero → stop and show its stderr; never spawn the miner
- [ ] Miner returns no file / invalid JSON → do not run `post`; stop, report it, watermark unchanged
- [ ] User answers none of the proposals → rows stay `open`; say so
- [ ] Codex 8 KB cap (prompt lives in `references/`)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/self-review/SKILL.md` | new |
| `skills/self-review/references/miner-prompt.md` | new (from the spike prompt) |
| `skills/learn/SKILL.md` | Step 8: kit proposals belong to `self-review` |
| `AGENTS.md` | add `self-review` to the cross-cutting list |
| `tests/test_self_review_skill.py` | new — AC 1-8 |
| skill-list pins / site chips | only where a test requires it |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*`, `hooks/hooks.json`, `.claude/settings.json` | FR-001 |
| `skills/self-review/scripts/self_review.py` | T255 (report a contract gap instead) |

---

## Test Plan

Structural pytest for AC 1-8; the AC 9 real run twice in a row, with the event-trace `Agent` count pasted.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T256.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
