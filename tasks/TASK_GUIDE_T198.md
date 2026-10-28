# TASK_GUIDE — T198: `wake` reads two sections of `memory/MEMORY.md`, not the whole file
**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `skills/wake/SKILL.md` and `skills/wake/scripts/dirty_worktrees.py` (the pattern to imitate)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28, verbatim: "so it serve as diff purpose, so I think we should make it better then, not the replace" — and, choosing from the improvement list, "Cheaper wake (T196) (Recommended)" (the board number is now T198: T196 and T197 went to another session).

**Restated intent**:
> `wake` is the mandatory first step of every Supervisor session. Today it reads all of `memory/MEMORY.md` (about 42 KB, about 10,400 tokens) and prints about 20 lines from two sections of it. Replace that read with a small script that prints only those two sections, so the briefing is the same and the session starts about 9,000 tokens lighter.

**Out of scope** (what this task explicitly does NOT do):
- No change to `memory/MEMORY.md` content or layout.
- No change to the other four `wake` sources (git log, board, dirty worktrees, learning records) or to the 50-line cap.
- No change to the easy-memory repo.

**Requirement Refs**: none (the kit has no `PRD.md` for this scope; the source is the user request above).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-28)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist (none needed)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `skills/wake/scripts/memory_sections.py` (the string must appear in `skills/wake/SKILL.md` Step 1)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `python3 skills/wake/scripts/memory_sections.py` run in a checkout prints the `### Decisions` and `### Learning Records` sections of `memory/MEMORY.md` and nothing else, one entry line per output line | same briefing |
| 2 | Newest entries come first in `MEMORY.md` (verified: the top entry of each section is the newest). When Decisions plus Learning Records together hold more than 20 entry lines, the script prints the first 5 entries of each section; otherwise it prints all of them | existing rule "10 most recent entries" in `SKILL.md` Step 4. **Supervisor decision (not stated by the user):** 5 from each section, so both kinds appear; the old rule did not say how the 10 split |
| 3 | If `MEMORY.md` is missing, the script prints `No MEMORY.md found.` and exits 0 | existing degradation rule |
| 4 | If neither section exists, the script prints the `## Index` block as-is; if that is also missing it prints nothing and exits 0 | existing edge case |
| 5 | `skills/wake/SKILL.md` Step 1 uses the script in place of "Read full file", and Step 4 says the script's output is the Key Memory content. The skill never reads the whole file | the saving |
| 6 | A new test covers AC 1 to 4 on fixture files and asserts the script output for the real `memory/MEMORY.md` is under 4,000 characters | Gate 5 |
| 7 | Negative: the script never writes a file and never exits non-zero | `wake` is read-only and never halts |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The real `memory/MEMORY.md` (about 42,000 characters) | Output under 4,000 characters, 10 entry lines, Decisions then Learning Records | `python3 skills/wake/scripts/memory_sections.py \| wc -c` |
| 2 | A fixture with 3 Decisions and 2 LR lines | All 5 lines printed | new test |
| 3 | No `memory/MEMORY.md` | `No MEMORY.md found.`, exit 0 | new test |
| 4 | A fixture with neither section but an `## Index` block | The block is printed | new test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_wake_memory_sections.py tests/test_dirty_worktrees.py -q && python3 skills/wake/scripts/memory_sections.py | wc -c
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T198.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T198.md`.

---

## Approach

**Pattern reference**: `skills/wake/scripts/dirty_worktrees.py` and `tests/test_dirty_worktrees.py` — read-only, fail-soft, run from the repo root, tested with fixtures.

**Vital slice**: the script plus the `SKILL.md` Step 1 and Step 4 edits.
**Cut list**:
- A cap on line width: not needed, entries are already one line.
- Sorting by date: entries are already newest first.

Parse by the `### ` headings: a section runs to the next `### ` or `## ` heading. An entry line starts with `- `.

---

## Edge Case Checklist

- [ ] `MEMORY.md` with Windows line endings
- [ ] A heading with trailing spaces
- [ ] An entry that wraps onto a second line (lines not starting with `- ` inside a section are ignored)
- [ ] Run from a worktree: the path is relative to the current directory, like the other wake scripts

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/wake/scripts/memory_sections.py` | new script |
| `skills/wake/SKILL.md` | Step 1 table row and Step 4 text |
| `tests/test_wake_memory_sections.py` | new test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/*` | the Supervisor owns memory writes |
| `PROJECT_KANBAN.md` | the Supervisor owns the board |
| `skills/wake/scripts/dirty_worktrees.py` | out of scope |

---

## Test Plan

Red first: write `tests/test_wake_memory_sections.py`, see it fail (script missing). Write the script and edit the skill. Run the Verification Command, then `python3 -m pytest tests -q -x`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T198.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review
