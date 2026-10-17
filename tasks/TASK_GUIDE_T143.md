# TASK_GUIDE — T143: CI re-runs the Verification Command of every task a PR moves to Done
**Date**: 2026-10-16
**Complexity Level**: C2
**Risk Level**: Medium
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
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

From the user's improvement list, area 2: *"Require a machine-recheckable `### Verify` (or equivalent) artifact before a task can be marked Done / shipped. Add a commit-time or ship-time check that the claimed verification commands actually pass."* Grilled 2026-10-16: the user chose **CI re-runs the block** — the local merge hook does not execute guide-authored commands.

**Restated intent**:
> When a PR moves a task to Done, CI runs that task's `### Verification Command` block and fails the PR if it fails — so "verified" is re-checked by a machine, not just claimed in the Evidence table.

**Out of scope**:
- Changing `pre_bash_block_unsafe_merge.py` (T099 just closed its matcher)
- Re-running guides of tasks *not* moved to Done by the PR
- Rewriting any of the existing 128 guides' Verification Command blocks

**Requirement Refs**: no `PRD.md` in this repo — traces to `memory/decisions.md` entry "Improvement-list grilling (2026-10-16)", area (2).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "guide fields", not "task manifest" (`MANIFEST` is the install file)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, no `PRD.md`; traced to the decisions entry above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `scripts/ci_verify_done_tasks.py` (new), called from a new step in `.github/workflows/ci.yml`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Given a base ref and head ref, the script lists exactly the task IDs whose `PROJECT_KANBAN.md` row changed from `- [ ]`/other to `- [x]` between them | "every task a PR moves to Done" |
| 2 | For each such task it extracts the fenced `bash` block under `### Verification Command` via `guide_sections` (guide first, review file second) and runs it from the repo root; any non-zero exit fails the job and names the task | "claimed verification commands actually pass" |
| 3 | A block whose first non-blank line is `# ci: skip — <reason>` is skipped **by name with the reason printed**; a skip with an empty reason fails | commands needing a worktree, network or `/verify` |
| 4 | A task moved to Done with **no** Verification Command section, an empty block, or only the template placeholder fails the job (fail closed) | "machine-recheckable artifact before Done" |
| 5 | The template gets a one-line note on the `# ci: skip — <reason>` convention; nothing else in the template changes | convention discoverable |
| 6 | CI runs the step on `pull_request` only, with no secrets referenced | guide-authored commands run in CI |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The Supervisor signs off on these oracles before spawn; the implementer must not be their sole author.

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture repo: commit A has T900 `- [ ]`, commit B has T900 `- [x]`, guide block `true` | exit 0, prints `T900: PASS` | automated test |
| 2 | Same, guide block `false` | exit 1, prints `T900: FAIL` | automated test |
| 3 | Block `# ci: skip — needs /verify` | exit 0, prints `T900: SKIP (needs /verify)` | automated test |
| 4 | Block `# ci: skip —` (no reason) | exit 1 | automated test |
| 5 | T900 moved to Done, guide has no Verification Command / placeholder only | exit 1, names T900 | automated test |
| 6 | A Done row whose prose bold-mentions `**T901**` (T093's shadowing shape) | only T900 is selected | automated test |
| 7 | **Mutation control**: make the "missing block" branch return success | test 5 goes RED | manual, Supervisor re-runs |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_ci_verify_done_tasks.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T143.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T143.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/lib/guide_sections.py` — `read_guide_section()` for guide-then-review resolution; `.claude/hooks/pre_bash_block_unsafe_merge.py`'s `tasks_in_section()` — row-anchored ID extraction (first bold ID on a `- ` line), which T093 proved immune to bold cross-references.

**Vital slice**: the Done-diff → extract → run → fail-closed path for one task.
**Cut list**:
- Running blocks in parallel (one or two tasks per PR today)
- Timeouts beyond a single per-task `timeout` (default 600 s)
- Back-filling `# ci: skip` markers into old guides (old guides only run if a PR moves them to Done)

Use `git show <ref>:PROJECT_KANBAN.md` for both sides — no checkout of the base. In CI, base is `${{ github.event.pull_request.base.sha }}` with `fetch-depth: 0`. Stdlib only.

---

## Edge Case Checklist

- [ ] Row moved Todo → Done in one PR *and* rewritten heavily — match by the row's own leading ID, never by prose
- [ ] `[~]` Closed rows are not Done
- [ ] Block runs with `bash -euo pipefail`? **No** — run exactly as written with `bash -c`; the guide author chose the semantics
- [ ] A block that `cd`s into a `wt-*` path must be `# ci: skip`, not silently pass
- [ ] Guide file padded vs unpadded ID (`T143` vs `T0143`) — `guide_sections` already handles it; reuse it
- [ ] A PR with no Done moves prints `no tasks moved to Done` and exits 0

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/ci_verify_done_tasks.py` | new — selection, extraction, run, report |
| `tests/test_ci_verify_done_tasks.py` | new — fixture git repo tests for SC1–SC6 |
| `.github/workflows/ci.yml` | new step on `pull_request`, `fetch-depth: 0` |
| `templates/TASK_GUIDE_template.md` | one-line `# ci: skip — <reason>` note under Verification Command |
| `MANIFEST` | only if the script must ship to consumer projects — decide and record why |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | merge matcher closed in T099; out of scope |
| `.claude/hooks/lib/guide_sections.py` | consume, don't change — three gates depend on it |
| `tasks/TASK_GUIDE_T0*.md`, `tasks/TASK_GUIDE_T1[0-3]*.md` | no back-fill of old guides |

---

## Test Plan

Pytest with a temporary git repo fixture (two commits of a minimal `PROJECT_KANBAN.md` + `tasks/`). Each SC is one test. Supervisor re-runs SC7 at Stage 4.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — mandatory; scope manually to `main..<branch>`)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T143.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
