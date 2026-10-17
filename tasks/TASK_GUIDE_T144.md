# TASK_GUIDE — T144: Stage 4 warns when a task's diff outgrows its declared Complexity
**Date**: 2026-10-16
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
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

From the user's improvement list, area 1: *"Make ceremony scale with risk… Enforce the declared lane at commit/ship time with a hook that checks the actual diff against the claimed complexity."* Grilled 2026-10-16: lanes scale **depth, never stages** (every stage and Hard-Stop Gate still runs); brainstorm answer: the check **warns at Stage 4, never blocks** until its limits are measured.

**Restated intent**:
> At Stage 4 the reviewer sees one line saying whether the branch's real diff fits the task's declared Complexity and its predicted files — so an under-labelled task is caught at review instead of slipping through with too little process.

**Out of scope**:
- Blocking anything — this is a report line
- Any new "lane" label: the existing Complexity label **is** the lane
- Changing what any stage does for a given Complexity (the role guides' Complexity matrices already own that)

**Requirement Refs**: no `PRD.md` — traces to `memory/decisions.md` "Improvement-list grilling (2026-10-16)" area (1) and the brainstorm answers that follow it.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "lane" = the Complexity label's depth profile (added to the glossary by this task)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, traced above

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `scripts/lane_check.py` (new), invoked from `skills/code-review/SKILL.md` Phase 0

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `lane_check.py <guide> <base>..<head>` prints one line: declared Complexity, changed-file count, changed-line count, and `FITS` or `EXCEEDS (<reason>)` | "checks the actual diff against the claimed complexity" |
| 2 | Budgets live in one table at the top of the script (C0/C1/C2 file and line limits); C3 has no ceiling | thresholds are guesses until measured |
| 3 | Files changed but **not** predicted in `## Files to Change (Predicted)` are listed as `unpredicted: <paths>` | predictions become checkable |
| 4 | Lock files, `__pycache__`, `PROJECT_KANBAN.md`, `memory/**`, `tasks/TASK_REVIEW_*` are excluded from the budget | bookkeeping is not task size |
| 5 | A guide whose text contains a Hard-Stop Gate 2 word (*refactor*, *restructure*, *migrate to pattern*, *clean architecture*, *QA suite*, *test coverage*) and declares below C2 prints `EXCEEDS (Gate 2 floor)` | Gate 2 kept |
| 6 | Exit code is always 0 (warn only); an unreadable guide prints `UNKNOWN (<reason>)`, never `FITS` | warn, never block; fail toward visibility |
| 7 | `code-review` Phase 0 runs it and pastes the line into the report; `PROJECT_SPEC.md` glossary gains "Lane" | reviewer sees it |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | C0 guide, diff of 1 predicted file / 5 lines | `FITS` | automated test |
| 2 | C0 guide, diff of 6 files | `EXCEEDS (files 6 > 2)` (numbers from the table) | automated test |
| 3 | Diff touches a file not in Files to Change | `unpredicted: <path>` listed | automated test |
| 4 | C1 guide titled "refactor X" | `EXCEEDS (Gate 2 floor)` | automated test |
| 5 | Guide path missing | `UNKNOWN (...)`, exit 0 | automated test |
| 6 | Diff only touches `PROJECT_KANBAN.md` + `memory/decisions.md` | counts 0, `FITS` | automated test |
| 7 | **Calibration**: run against the last 10 merged tasks (T128–T138) | table of results pasted into TASK_REVIEW; budgets chosen so ≤2 of 10 exceed | manual, recorded |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_lane_check.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T144.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T144.md`.

---

## Approach

**Pattern reference**: `skills/craft-spawn-prompt/scripts/memory_slice.py` — `table_paths()` already parses the Files to Change table; import or mirror it, do not write a third parser.

**Vital slice**: the one report line plus the unpredicted-files list.
**Cut list**:
- A per-Complexity "lane depth" table — the role guides' Complexity matrices already define depth; duplicating it would drift
- Line-weighting by file type
- A hook — the user chose warn-at-review

Get the diff with `git diff --numstat <range>`. Calibrate budgets with SC7 before finalising the table; record the chosen numbers and why in TASK_REVIEW.

---

## Edge Case Checklist

- [ ] Renames (`git diff --numstat -M`) count once, not twice
- [ ] Binary files show `-` in numstat — count the file, zero lines
- [ ] Glob rows in Files to Change (`tests/test_*.py`) match by prefix, as `memory_slice.py` does
- [ ] Old guides with no Complexity line → `UNKNOWN`, not C0

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/lane_check.py` | new |
| `tests/test_lane_check.py` | new |
| `skills/code-review/SKILL.md` | Phase 0: one step running the script and pasting its line |
| `PROJECT_SPEC.md` | glossary row "Lane" |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py` | warn-only by user decision — no hook |
| `agents/*.md` | Complexity matrices stay the single source of depth |
| `CLAUDE.md` | Hard-Stop Gates unchanged |

---

## Test Plan

Pytest with a temp git repo per case. SC7 is a recorded calibration run, not a test.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T144.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
