# TASK_GUIDE — T215: Tidy the repo root and shorten the board's Done rows (same meaning)
**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: Medium
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
6. Read `memory/codebase-map.md` for directory layout and blast-radius hotspots

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-30: "currently, the repos is messy with the file and the old setup also, let recheck and update the repos for clean". Asked whether to tidy the 13 root BRAINSTORMING_LOG / PRD files and the 343 KB `PROJECT_KANBAN.md` (174 Done rows), the user answered: "do in this session also, shorten, summary, anything keep the repos clean but same meaning".

**Restated intent**:
> The repo root holds only live entry files, and `PROJECT_KANBAN.md` is short enough to read. No fact is lost: every moved file keeps its content, every shortened board row keeps its full original text in an archive file, and every gate, hook, script and test that reads these files still works.

**Out of scope**:
- `CLAUDE_LEGACY.md`, `MANIFEST`, `setup.sh`, `update.sh`, `lib/`, `.cursor/`, `vercel.json`, `README.md`, `RUNBOOK.md`, `PROJECT_SPEC.md`, `PROJECT_*_SITE.md` — live kit or deploy files, referenced by tests/installer.
- Root `BRAINSTORMING_LOG.md` — the `brainstorming` skill's output path and a `scripts/validate.sh` allow-listed name; stays at root.
- Todo / In Progress / Ready for Review / Blocked rows and the Stage Tracker — unchanged.
- Rewriting history text inside `tasks/*.md`, `memory/*.md` beyond path updates.
- Local, git-ignored folders (`reports/*.html`, `memory/event-trace/`, `.claude/verify-runs/`).

**Requirement Refs**: none in `PRD.md` (repo-hygiene chore requested directly by the user).

### Requirement Fidelity Gate

- [x] Restated intent confirmed to match the user's request (Supervisor, from the user's answer quoted above)
- [x] Domain terms align with `PROJECT_SPEC.md` (board, Done row, gate)
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] No `PRD.md` refs (chore)

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: Standalone — N/A: file layout + board text; consumers are the hooks/scripts listed under Files to Change.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The 12 `BRAINSTORMING_LOG_<topic>.md` files live in `docs/brainstorming/`, the 3 `PRD_<topic>.md` files in `docs/prd/`, moved with `git mv` (byte-identical content); none remain at the root | "repo root clean" |
| 2 | No tracked file references an old root path of a moved file (`git grep` for each old bare path outside `docs/brainstorming/`, `docs/prd/` returns nothing that resolves to the root) — every reference now names the new path | "same meaning" — links still resolve |
| 3 | Each row under `### Done` and `### Closed (investigated, will not do)` in `PROJECT_KANBAN.md` is one line, ≤ 400 characters, keeping: checkbox, `**Txxx**`, title (may be shortened but keeps its meaning), agent, Complexity, Risk, Priority, `Guide:` path when the original had one, and a closing outcome (`Done <date>` / `Closed <date>` + one-clause result) | "shorten, summary" |
| 4 | The full original text of every shortened row is in `docs/archive/KANBAN_DONE_DETAIL.md`, verbatim, one entry per task ID, in the same order; `PROJECT_KANBAN.md` has one pointer line under `### Done` naming that file | "same meaning" — audit trail kept |
| 5 | The set of task IDs per board section is unchanged before vs after (Todo, In Progress, Ready for Review, Done, Closed, Blocked) — checked by a script that parses the board the way the hooks do (`.claude/hooks/lib/auto_mode.py` `board_rows`, `pre_agent_validate_guide.py` section lookup) | gates keep working |
| 6 | Full suites pass: `python3 -m pytest -q tests .claude/hooks/tests` and `bash scripts/validate.sh` → `PASS` | gates keep working |
| 7 | `PROJECT_KANBAN.md` is ≤ 100 KB after the change | "shorten" |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | repo after the change | `ls BRAINSTORMING_LOG_*.md PRD_*.md` at root finds nothing; `docs/brainstorming/` has 12, `docs/prd/` has 3 | new test `tests/test_repo_layout_t215.py` |
| 2 | the board before (`git show main:PROJECT_KANBAN.md`) and after | same task IDs in each section; every Done/Closed row ≤ 400 chars and one line | new test (compares against a frozen ID list captured from `main` at `080edf90`, stored as a fixture) |
| 3 | `docs/archive/KANBAN_DONE_DETAIL.md` | contains each Done/Closed ID's original row text verbatim | new test (fixture: sha256 of each original row) |
| 4 | a Done task ID, e.g. T213 | `pre_agent_validate_guide.py` still reports it as `Done`; `stop_auto_mode_check` still sees it in its Done set | existing hook tests + one new assertion |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests/test_repo_layout_t215.py && python3 -m pytest -q tests .claude/hooks/tests && bash scripts/validate.sh && test $(wc -c < PROJECT_KANBAN.md) -le 102400
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T215.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T215.md`.

---

## Approach

**Pattern reference**: `tests/test_vercel_config.py` — plain pytest, `ROOT` from `__file__`, one AC per test. For board parsing reuse `.claude/hooks/lib/auto_mode.py` (`board_rows`) rather than a new parser.

**Vital slice**: the move + reference update (AC 1–2) and the Done/Closed row shortening with verbatim archive (AC 3–5).
**Cut list**:
- No automation to shorten future Done rows (one-time pass; a future task can add it).
- No reorganisation of `tasks/` (324 files) — they are referenced by ID from hooks.

Steps:
1. Capture before-state from `main`: per-section ID lists and the original text of every Done/Closed row → test fixtures. Write the test first; run it red.
2. `git mv` the 15 files. Update references with exact-path replacements (`BRAINSTORMING_LOG_x.md` → `docs/brainstorming/BRAINSTORMING_LOG_x.md`, `PRD_x.md` → `docs/prd/PRD_x.md`), including relative links in moved files that point at root files (fix with `../../`). Do not touch a bare `BRAINSTORMING_LOG.md` or `PRD.md`.
3. Write `docs/archive/KANBAN_DONE_DETAIL.md` (short header + verbatim rows, `## Txxx` per entry). Then rewrite each Done/Closed row to the short form. Write the one-clause outcome from the row's own last status text — never invent a fact.
4. Run the full suites and `validate.sh`. Fix any test that pins a moved path by updating the path, not by loosening the test.

---

## Edge Case Checklist

- [ ] A Done row that spans several lines (continuation lines) — the archive must keep all lines; the short row is one line.
- [ ] Hooks/tests that grep the board for text that only existed in long rows (e.g. `Track: minimal`, `Record:` markers, evidence paths, `verify` rows used by `.claude/hooks/pre_bash_block_unsafe_merge.py` or `tests/test_ci_verify_done_tasks.py`) — keep any marker a reader needs in the short row.
- [ ] The same task ID mentioned inside another row's text — section lookup must not change.
- [ ] `scripts/board_sync.py` online-mode render — must still parse.
- [ ] A moved file referenced from `.claude/hooks/tests/*` with a hard path.
- [ ] Windows/CRLF or trailing spaces in rows — archive must stay byte-verbatim.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `BRAINSTORMING_LOG_*.md` (12), `PRD_*.md` (3) | `git mv` to `docs/brainstorming/`, `docs/prd/` |
| files that reference them (`git grep`) | path update only |
| `PROJECT_KANBAN.md` | Done/Closed rows shortened; one pointer line |
| `docs/archive/KANBAN_DONE_DETAIL.md` | new — verbatim original rows |
| `tests/test_repo_layout_t215.py`, `tests/fixtures/t215_*` | new tests + frozen before-state |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` and other hook code | the board format must stay readable by today's hooks; change the data, not the readers |
| `BRAINSTORMING_LOG.md`, `PRD.md` (if present) | live skill/validate paths |
| Todo/In Progress/Ready for Review rows, `## Blocked`, `## Stage Tracker` | out of scope |

---

## Test Plan

New `tests/test_repo_layout_t215.py` (AC 1, 3, 4, 5, 7) red first, then green; full `tests` + `.claude/hooks/tests` suites; `scripts/validate.sh`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T215.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
