# TASK_GUIDE — T202: `main` is green again — the 15 budget/corpus test failures fixed without raising any cap
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: edits the four base role guides (doctrine every spawn loads) and the hot memory tier. No hook code changes.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full — this task edits it
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` for layout and hotspots

---

## Requirement (Pillar 1 — Adapt the requirement)

`main` @ `e4c7115` (pushed to GitHub 2026-10-29) has 15 failing tests in `python3 -m pytest -q .claude/hooks/tests/ tests/`. The Supervisor measured all 15 on 2026-10-29. Three causes:

- **A — role guides over budget (9 tests).** T183 (`05a23df`) and T195 (`140ccaa`) added lines to the four base role guides.
  - `test_vital_slice.py::test_ac11_line_cap[...]` (4): `agents/backend.md` 150 > 145, `agents/common-infrastructure.md` 143 > 137, `agents/frontend.md` 146 > 142, `agents/qa.md` 135 > 129. The failure text says: "Tighten the prose — do not raise the cap (DDR-0005 §6)."
  - `test_agent_guide_dedup.py::test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline[...]` (4) and `test_t069_ac9_report_per_role_pair_size` (1): per-role loaded size above the `BASELINE_REF = "8fc4dd2"` figure (measured: 13164 vs < 12748, 13986 vs < 13581, 14347 vs < 13928, 12157 vs <= 11663 — map each pair to its role from the test output).
- **B — hot tier over budget (5 tests).** `memory/MEMORY.md` is 43,019 chars; `HOT_TIER_CHAR_BUDGET = 42_000` (`.claude/hooks/tests/test_token_audit_format.py:91`). Fails `test_token_audit_format.py::test_memory_md_hot_tier_stays_within_char_budget` and 4 tests in `test_memory_channel_and_budget.py` (live-file test plus 3 mutation tests that need headroom under the cap). The failure text says: "Run `/compact-memory` to shrink the file — do NOT raise HOT_TIER_CHAR_BUDGET, it is a ratchet".
- **C — corpus test predates T182 (1 test).** `test_verify_row_fill_detection.py::test_ac6_old_vs_new_pattern_over_real_corpus_differs_only_on_placeholders` flags `tasks/TASK_REVIEW_T197.md:41`, an `auto-run by hook` verify row. The real gate (`has_filled_verify_row`, `.claude/hooks/pre_bash_block_unsafe_merge.py:329`) correctly rejects it in the test's temp copy, because T182 accepts such a row only with its run record for that task and head commit. The gate is right; the test's list of allowed differences does not know this T182 shape.

**Restated intent**:
> Make the full suite match its own rules again by shrinking what grew, not by moving the limits:
> tighten the four role guides' prose and compact `memory/MEMORY.md` until every budget test passes,
> and teach the corpus test that an `auto-run by hook` row the old pattern accepted and the real gate
> rejects (no run record) is an allowed difference. No guidance is lost: every rule a guide states
> today is still stated afterwards, and every hot-tier pointer still reaches its cold-tier entry.

**Out of scope**: raising or re-pointing any cap, budget or `BASELINE_REF`; changing any hook or `has_filled_verify_row`; editing cold-tier files except to receive text moved out of the hot tier; the other 18 Todo tasks.

**Requirement Refs**: Hard-Stop Gate 5 (suite must pass); DDR-0005 §6 (line caps are tightened, never raised); Memory Write Protocol (hot-tier ratchet).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-10-29: "yes" to "register T202, make `main` green again")
- [x] Terms: **role guide**, **hot tier**, **cold tier**, **memory slice** as in `PROJECT_SPEC.md` / AGENTS.md
- [x] Every AC traces to cause A, B or C
- [x] Refs covered

---

## Dependencies & Reachability

**Depends on**: None (branch from `main` @ `e4c7115` or later).

**Entry point**: `python3 -m pytest -q .claude/hooks/tests/ tests/` — the full suite every Stage 4/5 runs.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Each of `agents/backend.md`, `agents/common-infrastructure.md`, `agents/frontend.md`, `agents/qa.md` is at or under its `LINE_CAPS` entry in `test_vital_slice.py`, and every `test_agent_guide_dedup.py` per-role size test passes. No cap, budget or baseline constant in any test file changes. | A |
| 2 | Guidance kept: for each role guide, every rule, gate, tool name and file path present before the edit is still present after it (same file, or a pointer to the shared file that already states it, e.g. `templates/general-agent-template.md`). The diff removes repetition and wordiness only. The reviewer checks this line by line; the agent lists each removed sentence and where its content still lives in `tasks/TASK_REVIEW_T202.md`. | A |
| 3 | `memory/MEMORY.md` is at most **41,000** chars (1,000 under the cap, so the next index lines and the mutation tests have room), measured with `python3 -c "print(len(open('memory/MEMORY.md').read()))"`. `HOT_TIER_CHAR_BUDGET` stays `42_000`. | B |
| 4 | Every hot-tier index line removed or shortened keeps its target: each `(decisions.md)` / `(learnings.md)` / LR pointer that existed before still resolves to an entry in that cold file; any detail cut from a hot-tier line already exists in, or is moved into, the cold file it points to. Section order and the newest-first rule in `### Decisions` / `### Learning Records` are kept (`skills/wake/scripts/memory_sections.py` still prints both sections). | B |
| 5 | `test_ac6_old_vs_new_pattern_over_real_corpus_differs_only_on_placeholders` passes by allowing exactly one more difference shape: old pattern True, real gate False, row notes contain `auto-run by hook`. A placeholder-shaped or any other row that differs still fails the test (add a small test proving a non-auto, non-placeholder difference is still reported). | C |
| 6 | `python3 -m pytest -q .claude/hooks/tests/ tests/` → 0 failed. | A, B, C |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | branch head | full suite 0 failed | pytest |
| 2 | `git diff main -- '.claude/hooks/tests/*.py' tests/` | no change to `LINE_CAPS`, `HOT_TIER_CHAR_BUDGET`, `BASELINE_REF` or any numeric budget | grep the diff |
| 3 | `memory/MEMORY.md` | ≤ 41,000 chars; `memory_sections.py` prints Decisions + Learning Records | python one-liner + run script |
| 4 | each role guide diff | removed-sentence table in the review file; no rule lost | Supervisor line-by-line review |
| 5 | corpus test with a synthetic non-auto mismatching row | still fails | new test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q .claude/hooks/tests/ tests/ 2>&1 | tail -2 && python3 -c "print(len(open('memory/MEMORY.md').read()))" && wc -l agents/backend.md agents/common-infrastructure.md agents/frontend.md agents/qa.md && python3 skills/wake/scripts/memory_sections.py | head -3 && git diff main -- .claude/hooks/tests tests | grep -E '^[-+].*(LINE_CAPS|HOT_TIER_CHAR_BUDGET|BASELINE_REF)' | wc -l
```

Expected: `0 failed` absent / all passed; a number ≤ 41000; each guide at or under its cap; Decisions header printed; `0`.

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T202.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T202.md`.

---

## Approach

**Pattern reference**: earlier role-guide tightening for the same caps — `git log --oneline -- agents/backend.md` (T065/T069 dedup: rules stated once in `templates/general-agent-template.md`, role guides point to it). For the hot tier, `skills/compact-memory/SKILL.md` (consolidate, keep pointers, move detail to cold files).
**Vital slice**: the four guides under cap (AC 1–2) and `MEMORY.md` under 41,000 (AC 3–4).
**Cut list**: per-entry 150-char target for every hot-tier line (advisory, 47% over today — fix only what reaches 41,000); any restructure of the role guides beyond wording.

Tightening order for the guides: (1) sentences that repeat `templates/general-agent-template.md` or AGENTS.md → replace with the existing pointer; (2) wordy sentences → shorter, same meaning; (3) only then merge adjacent bullets. Never drop a "not", a number, a tool name or a path. The T195 easy-memory lines (`memory_search` / `memory_read`, "skip if absent") and T183 frontmatter must keep their meaning.

---

## Edge Case Checklist

- [ ] `test_agent_guide_dedup.py` measures a *loaded size* that may include the general template: shrinking the template counts for all four roles, but the template has its own tests — run them.
- [ ] `memory_sections.py` relies on newest-first order and the `### Decisions` / `### Learning Records` headers — do not rename them.
- [ ] The AC11/AC10 mutation tests in `test_memory_channel_and_budget.py` add characters to a copy and need headroom: 41,000 gives ~1,000.
- [ ] A hot-tier line may be the only place a fact lives (no cold entry): move the fact into the cold file before shortening the line.
- [ ] `.claude/agents` is a relative symlink onto `agents/` — edit `agents/*.md`, never the link.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `agents/backend.md`, `agents/common-infrastructure.md`, `agents/frontend.md`, `agents/qa.md` | tighten prose to cap |
| `memory/MEMORY.md` | compact to ≤ 41,000 chars |
| `memory/decisions.md`, `memory/learnings.md` | only to receive detail moved out of the hot tier |
| `.claude/hooks/tests/test_verify_row_fill_detection.py` | allow the `auto-run by hook` shape; add the still-fails test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py` (non-test) | the gate is correct |
| any cap/budget/baseline constant in tests | the whole point is not to move the limits |
| `AGENTS.md`, `CLAUDE.md` | own line caps; not part of the failures |
| `.claude/agents`, `.claude/skills` symlinks | load-bearing |

---

## Test Plan

Full suite before (capture the 15 FAILED lines as BEFORE) and after (0 failed). One new test for AC 5. Supervisor reviews every removed guide sentence against AC 2.

---

## Completion Checklist

- [ ] Implementation done (agent)
- [ ] BEFORE captured before the first implementation commit (agent)
- [ ] Removed-sentence table in `tasks/TASK_REVIEW_T202.md` (agent)
- [ ] Stage 4 `code-review` + `security-review` (Supervisor)
- [ ] Tests written AND pass — output pasted into the review file (Hard-Stop Gate 5)
- [ ] `verify` (user)
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Questions Log
