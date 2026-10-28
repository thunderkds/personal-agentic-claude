# TASK_GUIDE — T190: The merge gate binds a failed companion row, and stays silent when there is none
**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: this edits the merge gate. A wrong edit either blocks every push or opens a hole in
> the gate. T044's history shows a broken check in this exact file went unnoticed for three sessions.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely, then `PRD_companion-scoring.md` (FR-001, FR-004, FR-005, FR-006, FR-014) and `BRAINSTORMING_LOG_companion-scoring.md`
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` for directory layout and blast-radius hotspots
7. Read `.claude/hooks/pre_bash_block_unsafe_merge.py` **in full** before editing one line of it, and
   `.claude/hooks/tests/test_merge_gate_evidence.py` + `test_merge_gate_t095.py` for how it is tested

> **Live-session warning.** Tasks T188 and T189 are owned by another session working on auto-verify
> in this same checkout, and both touch `pre_bash_block_unsafe_merge.py`. Before you edit that file,
> run `git log --oneline -3` and `git status --short` and check whether their change has landed. If
> it has not, your edit and theirs will conflict in the `ready_review` loop. Report it and ask the
> Supervisor rather than merging the two by hand.

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28: *"checking the repos and adding the options to use the easy-ui and easy-verifier as
scoring to evaluate gate."* Then, on how binding it is: *"the scoring is a optional, so if users do not
use this one, we should run the normal flow, not required the mcp must run, or depend on that 100%"*
and *"if you use verifier mcp, and ui to check, the code must pass them. if not, just work on the
normal flow, that all"*.

**Restated intent**:
> A finished task may carry a measured score from the companion tools. If it does, that measurement
> is binding: a `fail` stops the merge. If it does not, nothing changes — no row to fill, no new stop,
> and no dependency on Docker, a Python package or any MCP server.

**Out of scope** (what this task explicitly does NOT do):
- Running either tool. This slice only reads rows. T191 and T192 write them.
- Any change to the `verify` row, `has_filled_verify_row`, `trace_shows_verification`, or
  `.claude/hooks/lib/verify_record.py`. That is a separate gate with its own history (T182).
- Generalising the check to every Evidence row (`Negative cases hold`, `Full smoke suite still
  green`). Deliberate cut — see Cut list.
- Doctrine text, glossary, skills, the site. T191–T194.

**Requirement Refs**:
- FR-001: the Companion score row exists in `templates/TASK_REVIEW_template.md`
- FR-004: an explicit `fail` in the Companion score row or a UI design row blocks push/merge
- FR-005: a `pass` is trusted only against an existing verifier report file
- FR-006: absent, blank, placeholder and `N/A` rows never block
- FR-014: with neither tool used, the gate's behaviour is unchanged, and a test asserts it

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, from the two quoted messages above)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — **Companion score** is this row; **evaluate gate** is easy-verifier's own asking round and is NOT this gate (T193 adds both terms; use them as defined here)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD_companion-scoring.md` and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: `None` — this is the first slice and everything else depends on it.

**Entry point**: `has_failed_companion_row`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_REVIEW_template.md` carries one new Evidence row whose Check cell reads `**Companion score (easy-verifier)**`, Result cell `☐ pass / ☐ fail / ☐ N/A`, and Notes cell naming all five of: `overall`, `change_risk`, the scope, the ref, and the report path | FR-001 |
| 2 | A Ready-for-Review task whose Companion score row Result cell carries a checked `☑ fail` blocks push/merge, and the blocked reason names the task ID and the row | FR-004 |
| 3 | The same block occurs for a checked `☑ fail` in any of the three UI design rows (`UI: Visual regression`, `UI: Design-system compliance`, `UI: Responsiveness`) | FR-004 |
| 4 | No block when the row is absent, blank, still the unchecked template placeholder, or `☑ N/A` with a written reason — in each case the gate's decision is the same as before this change | FR-006, FR-014 |
| 5 | A `☑ pass` Companion score row whose Notes cite no path, or a path that does not exist on disk, does not block, and the gate prints one advisory line to stderr naming the task and the absent report | FR-005, FR-006 |
| 6 | **Negative case:** the bare word `fail` inside a Notes cell prose (for example `no failures observed`, `the M2 mutation must fail`) never triggers a block. The check reads the checked box in the Result cell, never a substring anywhere in the row | FR-004 |
| 7 | **Negative case:** a `☑ fail` row on a task that is **not** in `Ready for Review` (Done, Todo, or absent from the board) does not block | FR-004 |
| 8 | Every pre-existing hook test still passes, and `sh scripts/validate.sh` reports PASS | FR-014 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A fixture repo: T900 in `Ready for Review`, its `TASK_REVIEW_T900.md` holding a filled `verify` row AND a `☑ fail` Companion score row | `{"decision": "block"}` whose reason names `T900` and the Companion score row | automated test |
| 2 | Same fixture, Companion score row `☑ pass` with Notes citing an existing report file | no block (and the existing verify-row result is unchanged) | automated test |
| 3 | Same fixture, Companion score row `☑ pass` with Notes citing `/nonexistent/report.html` | no block; one stderr line naming T900 and the absent report | automated test |
| 4 | Same fixture with **no** Companion score row and **no** UI rows at all | output byte-identical to the same fixture run against the pre-change hook | automated test |
| 5 | Same fixture, Notes cell containing the prose `no failures observed`, Result cell `☑ pass` | no block | automated test |
| 6 | Same fixture, `☑ fail` Companion score row, but T900 under `### Done` | no block | automated test |

> The AC-4 oracle is written by the Supervisor, not the implementing agent: capture the pre-change
> output first (`git stash` the edit, run the fixture, save stdout+stderr to a file in the scratchpad),
> then assert equality against it after the edit. Capturing it after the edit proves nothing.

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_merge_gate_companion_rows.py -q \
  && python3 -m pytest .claude/hooks/tests/ -q \
  && sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T190.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T190.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/pre_bash_block_unsafe_merge.py` — `VERIFY_ROW_PATTERN`
(lines 238–250) and `has_filled_verify_row` (327–358). Imitate three things exactly: a structural
pipe-delimited row regex rather than a substring search, the `UNCHECKED_PASS_PATTERN` guard that
disqualifies a template placeholder, and the multi-directory `Evidence` section resolution that
reads the guide first and then `TASK_REVIEW_Txxx.md`.

**Read the comment block at lines 69–106 before writing the regex.** It records why a substring
search was wrong here: a `\b(pytest|jest|verify)\b` search once matched the gate's own source code
and passed a merge on which no test had ever run. AC 6 is that defect, re-aimed at this row.

**Deliberate inversion, state it in a comment:** this file's idiom is fail-closed — every absence
resolves to "block". This check is the opposite: **only an explicit checked `fail` blocks, and every
absence resolves to "allow"**. That is FR-006 and FR-014, and it is the whole meaning of the feature
being optional. A future reader will try to "fix" this inconsistency, so the comment must say it is
intentional and name the user decision (D6) it comes from.

**This enforces doctrine that already exists.** `docs/claude-md/pipeline-stages.md`, Stage 5 step 1,
already reads *"Do not merge while any evidence row reads fail or is blank"*. Until now only the
`verify` row was enforced in code. This task does not invent a rule; it makes an existing sentence
true for these four rows.

**Vital slice**: the one function `has_failed_companion_row(task_id)` plus its call beside the
existing verify check in the `ready_review` loop. Four row names, one regex shape, one existence
check.

**Cut list**:
- Generalising to every Evidence row. Binding rows this feature was not asked to touch would block a
  push on a pre-existing `☑ fail` the moment it ships.
- Parsing the score numbers out of the Notes cell. The row's Result cell already carries the verdict;
  re-deriving the pass/fail from `overall` inside the hook would put the floor in two places.
- Any floor constant in this file. The floor lives in the `score` skill and the doctrine (FR-003).

---

## Edge Case Checklist

- [ ] `☑ fail` and `☑ pass` both present in one Result cell (a careless edit) — treat as fail, the stricter reading
- [ ] `☑ N/A` with no written reason — does not block (FR-006 lists `N/A` unconditionally), but the gate may note it
- [ ] The row exists in `TASK_GUIDE_Txxx.md` instead of `TASK_REVIEW_Txxx.md` — both locations resolve, same as the verify row (T064/T095)
- [ ] A report path containing a space, or `~`, or sitting outside the checkout (`EASY_VERIFIER_REPORTS_DIR` writes to `$HOME/.easy-verifier-reports/<repo>/`) — all must resolve; `~` is expanded
- [ ] A report path that exists but is a directory, not a file
- [ ] Two live sessions, two report files for one task — the check validates the path the row cites, never the newest in the directory
- [ ] An unreadable or malformed `TASK_REVIEW` file — must not raise; a parse failure resolves to "no companion row", so it never blocks (opposite of the verify row's fail-closed default, by design)
- [ ] Online board mode: the Ready-for-Review filter (`my_review_tasks`) already narrows which tasks are checked — the new check runs inside that same filtered loop, never outside it
- [ ] A task ID appearing in two sections of the board at once

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_REVIEW_template.md` | One new Evidence row (AC 1) |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | `has_failed_companion_row` + its call in the `ready_review` loop + the inversion comment |
| `.claude/hooks/tests/test_merge_gate_companion_rows.py` | New — AC 2–7 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/verify_record.py` | The `verify` row's own gate (T182). Mixing two gates in one task hides which one broke. |
| `has_filled_verify_row`, `trace_shows_verification`, `VERIFY_ROW_PATTERN` | Out of scope. The new check sits beside them, never inside them. |
| `skills/code-review/SKILL.md` | Path B was rejected. |
| `.claude/skills`, `.claude/agents` | Load-bearing relative symlinks. |
| `../_easy-family-ref/**` | Read-only reference repos. This feature changes the kit, not the tools. |
| `AGENTS.md` | 196 of 200 lines used. T193 owns the one line this feature gets there. |
| `tasks/TASK_GUIDE_T188.md`, `tasks/TASK_GUIDE_T189.md` | Another live session's tasks in this checkout. |

---

## Test Plan

1. New fixture-based tests for AC 2–7, following `test_merge_gate_evidence.py`'s fixture style
   (a temporary repo with a board and a `tasks/` directory, the hook invoked as a subprocess with the
   same stdin payload shape the harness sends).
2. AC 4's byte-identity test: capture the pre-change output into the scratchpad **before** editing,
   commit that captured file as the fixture's expected value, then assert equality.
3. Re-run the whole hook suite (41 test files) and `sh scripts/validate.sh`.
4. A real end-to-end check at Stage 5 `/verify`: a `☑ fail` row on a real Ready-for-Review task, a
   real `git push` attempt, the block observed, the row removed, the push attempt allowed.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — mandatory)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T190.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — a real push blocked by a real failed row, and allowed when the row is absent
- [ ] UI Evidence rows marked ☐ N/A with a justification (pure-hook task, no UI component)
- [ ] `memory/MEMORY.md` updated
- [ ] Supervisor notified: task ready for Stage 4 review
