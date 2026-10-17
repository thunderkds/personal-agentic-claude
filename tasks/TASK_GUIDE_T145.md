# TASK_GUIDE — T145: A spawned agent inherits past decisions about its files, and compound leads with the general lesson
**Date**: 2026-10-16
**Complexity Level**: C1
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
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` — skip for C0/C1 single-file work

---

## Requirement (Pillar 1 — Adapt the requirement)

From the user's improvement list, area 4: *"Make /compound produce more general, reusable lessons instead of one-off issue notes… Explicit 'inheritance' path so future agents automatically see past decisions that affect the same modules or files."* Grilled 2026-10-16: **file-keyed inheritance, no RAG**.

**What already exists (verified 2026-10-16)**: `skills/craft-spawn-prompt/scripts/memory_slice.py` (T125) already keys on the guide's Files to Change paths — but it only searches `memory/MEMORY.md` index lines. Cold `memory/decisions.md` entries already end with a `**Files**:` line naming the files they decided about, and the slice never reads them.

**Restated intent**:
> A spawned agent's memory slice also includes the cold `decisions.md` entries whose `**Files**:` line overlaps the task's predicted files — and a new `compound` doc opens with the reusable lesson and when it applies, before the incident detail.

**Out of scope**:
- Embeddings, RAG, any index service
- A new `touches:` field — `**Files**:` already is one
- Back-filling `**Files**:` onto old entries that lack it

**Requirement Refs**: no `PRD.md` — traces to `memory/decisions.md` "Improvement-list grilling (2026-10-16)" area (4).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, traced above

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `memory_slice.py` (`build_slice`), consumed by `craft-spawn-prompt` element 4

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `memory_slice.py` additionally reads `memory/decisions.md`, splits it into entries (a bold-led paragraph through the next blank-line-separated bold lead), and selects entries whose `**Files**:` line matches any existing key | "past decisions that affect the same files" |
| 2 | Selected cold entries print as their **first line only** (the bold title) plus `→ memory/decisions.md`, under a `### From decisions.md` heading inside the same slice markers | stays a slice, not a paste |
| 3 | The existing cap (30 lines / 4,000 chars) covers hot + cold output together; cold entries are dropped before hot lines | T125 budget kept |
| 4 | A missing `decisions.md` is silent — output identical to today | no regression |
| 5 | `compound`'s doc template gains `## The General Lesson` (one or two sentences) and `## Applies When` (a concrete condition) as the **first** two sections; the skill rejects a draft whose Applies When is empty | "general, reusable lessons" |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Guide predicting `lib/harness-fetch.sh`; decisions entry with `**Files**: lib/harness-fetch.sh, …` | its title line appears under `### From decisions.md` | automated test |
| 2 | Entry with no `**Files**:` line mentioning the path only in prose | **not** selected | automated test |
| 3 | 40 matching cold entries | output within cap; header states how many dropped | automated test |
| 4 | No `decisions.md` | byte-identical to pre-change output on the existing fixtures | automated test (existing `tests/test_memory_slice.py` still green, unmodified) |
| 5 | Live run against `tasks/TASK_GUIDE_T137.md` | includes the T137 decisions entry title | manual, pasted |
| 6 | **Mutation control**: drop the cold-entry pass | test 1 RED | Supervisor re-runs |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_memory_slice.py -q && python3 skills/craft-spawn-prompt/scripts/memory_slice.py tasks/TASK_GUIDE_T137.md
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T145.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T145.md`.

---

## Approach

**Pattern reference**: `memory_slice.py` itself — reuse `extract_keys()` and `key_pattern()` unchanged; add one function for cold entries.

**Vital slice**: decisions.md entries matched by their `**Files**:` line.
**Cut list**:
- `learnings.md` / `glossary.md` (no `**Files**:` convention there yet)
- `docs/solutions/` matching (not present in this repo; revisit when a consumer project uses compound)
- Ranking cold entries beyond "fewest key hits dropped first"

---

## Edge Case Checklist

- [ ] `**Files**:` wraps across two lines in several entries — join continuation lines before matching
- [ ] Generic basenames (`SKILL.md`) still map to directory names, as for hot lines
- [ ] An entry matched by both a hot index line and its cold body appears once in each section, not merged
- [ ] Very long decisions.md (2,000+ lines) — single pass, no quadratic scan

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/craft-spawn-prompt/scripts/memory_slice.py` | cold-entry pass |
| `tests/test_memory_slice.py` | new tests appended; existing ones untouched |
| `skills/compound/SKILL.md` | template's first two sections + empty-Applies-When rejection |
| `skills/craft-spawn-prompt/SKILL.md` | one line: the slice may include decisions.md titles |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/decisions.md` | read-only input; no back-fill |
| `memory/MEMORY.md` | hot-tier budget unchanged |

---

## Test Plan

Extend `tests/test_memory_slice.py` with fixture decisions files. Existing tests must pass unmodified (SC4).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T145.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
