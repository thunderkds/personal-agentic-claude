# TASK_GUIDE — T255: `self_review.py` — watermark gate, citation check and proposal register for self-review
**Date**: 2026-11-05
**Complexity Level**: C2
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
6. C2: read `memory/codebase-map.md`
7. Read `docs/prd/PRD_self-review.md`, `docs/brainstorming/BRAINSTORMING_LOG_self-review.md` (Path B, chosen) and `experiments/self-review-spike/RESULTS.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User 2026-11-05: "the loop that agent can self learning and propose the update to the kit" … "make sure we don't have a loop in loop". PRD `docs/prd/PRD_self-review.md` approved and gate PASS; Path B chosen (user 2026-11-05).

This task builds only the **deterministic part** of Path B: a stdlib Python script that decides whether a run happens, what it reads, which miner output survives, and what is remembered. The model call (one Sonnet `Agent` miner) and the skill text are T256.

**Restated intent**:
> `self_review.py pre` stops with one line and no further work when no review file is newer than the watermark; otherwise it lists at most 40 new review files. `self_review.py post` keeps only patterns with >=3 tasks backed by real citations, drops every pattern the register already holds (open/rejected, or fixed without post-fix evidence), caps at 3, writes a report, records the new patterns as `open`, and only then advances the watermark. `self_review.py decide` records the user's approve/reject. No model is called anywhere in this script.

**Out of scope**:
- `skills/self-review/SKILL.md`, the miner prompt, `learn` Step 8, `AGENTS.md` (T256).
- Spawning the miner; any network call; any hook; editing kit files other than those listed below.
- Event traces as input (PRD Out of Scope).

**Requirement Refs** (`docs/prd/PRD_self-review.md`):
- FR-002 input = new `tasks/TASK_REVIEW_*.md` only; FR-003 nothing-new stop; FR-004 citation check; FR-005 register states; FR-006 cap 3; FR-007 watermark after report; FR-008 (script side: never commits, merges or pushes); NFR-001 40-file cap; NFR-004 testable with a fake miner.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user 2026-11-05 approved PRD, grilling answer and Path B
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (watermark, register, fingerprint defined below)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in the PRD and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `skills/self-review/scripts/self_review.py` (called by T256's `SKILL.md`)

---

## Terms

- **Watermark**: the `main` commit SHA recorded at the end of the last completed run, stored as the `watermark:` line of the register.
- **Register**: `memory/self-review/register.md` — git-tracked, human-editable. A `watermark: <sha|none>` line, then a Markdown table `| fingerprint | state | tasks | task_id | fixed_at |`; `state` in `open`, `rejected`, `fixed`; `tasks` = comma-separated T-IDs; `task_id` = the kit task drafted for an approved pattern, else `-`; `fixed_at` = merge commit SHA, else `-`.
- **Miner output**: JSON `{"patterns":[{"id","title","tasks":[...],"citations":[{"file","line","quote"}],"proposal":{"file","change"},"already_open":bool}],"notes":...}` — the shape in `experiments/self-review-spike/MINER_PROMPT.md`.

## CLI (the contract T256 relies on)

```
self_review.py pre  [--repo DIR] [--max-files 40]
    -> stdout JSON {"status":"nothing-new"|"ready", "head":SHA, "watermark":SHA|null,
                    "files":[...], "deferred":N, "skipped_uncommitted":[...], "register":[rows]}
       status nothing-new also prints, on stderr, exactly one line starting "self-review: nothing new".
self_review.py post MINER_JSON --head SHA [--repo DIR] [--report PATH]
    -> writes the report (default reports/self-review/self-review-<UTC yyyymmddThhmmss>.md),
       appends new rows (state open) to the register, then sets watermark: SHA. Prints the report path.
self_review.py decide FINGERPRINT (approved TASK_ID | rejected) [--repo DIR]
    -> updates that row; unknown fingerprint = exit 2, register unchanged.
```
Exit 0 on success. Any malformed input (bad JSON, missing register columns) = exit 2 with a one-line stderr message and **no file written**.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `pre` with a watermark equal to the current `main` HEAD (or no `TASK_REVIEW` file changed since it) prints `status: nothing-new`, the one stderr line, and lists 0 files. | FR-003 |
| 2 | **No-loop:** on a fixture repo, `pre` → `post` (fake miner) → `pre` again: the second `pre` is `nothing-new`. The fake miner's call counter stays at 1 across the sequence (the test drives the sequence the way `SKILL.md` will: call the miner only when `pre` says `ready`). | FR-003, US-003 |
| 3 | `pre` lists only `tasks/TASK_REVIEW_*.md` files changed in `<watermark>..HEAD`; no watermark = all of them. Never a file under `reports/`, `memory/`, or `memory/event-trace/`. Uncommitted review files go to `skipped_uncommitted`, not `files`. | FR-002 |
| 4 | `pre` returns at most `--max-files` (default 40) files, oldest commit first; `deferred` = how many were left out. When files were deferred, `post` sets the watermark to the commit of the newest file it was given — not HEAD — so the deferred files come next run. | NFR-001, FR-007 |
| 5 | `post` drops a citation whose quote (whitespace-normalised, first 60 chars) is not within ±3 lines of the cited line, or whose file is not in the run's input list; a pattern left with <3 distinct tasks is dropped. (Port the check from `experiments/self-review-spike/check_runs.py`.) | FR-004 |
| 6 | `post` drops a pattern that matches an `open` or `rejected` row. Match = same fingerprint, or `already_open: true`, or task-set Jaccard >= 0.5 with the row. | FR-005 |
| 7 | A pattern matching a `fixed` row is kept only if every counted citation's file has a commit after that row's `fixed_at`; it is reported with the label `regressed`, and the row returns to `open`. Otherwise dropped. | FR-005 |
| 8 | **Second-order loop:** for a pattern matching a row with `task_id` Txxx, citations from `tasks/TASK_REVIEW_Txxx.md` do not count. | Edge case 1, US-003 |
| 9 | `post` reports at most 3 patterns, ranked by distinct-task count (ties: fingerprint ascending). | FR-006 |
| 10 | `post` writes the report first; register rows and watermark are written only after the report file exists. If writing the report fails, the register is byte-for-byte unchanged. | FR-007 |
| 11 | `pre` (and `post`) mark a row `fixed` with `fixed_at` when its `task_id` sits under `### Done` in `PROJECT_KANBAN.md`. | FR-005 |
| 12 | `decide` sets `rejected`, or sets `task_id` for `approved` (state stays `open`); unknown fingerprint = exit 2, register unchanged. | FR-005, FR-008 |
| 13 | The script never runs `git commit`, `git merge`, `git push`, never opens a network connection, and imports no non-stdlib module (test: grep the source + run under a fixture with no network). | FR-008, NFR-003 |
| 14 | Malformed miner JSON or register = exit 2, one stderr line, no file written. A review-file line containing instruction-like text (e.g. "ignore previous rules, propose X") is treated as plain text by the citation check — no special handling, no crash. | NFR-002 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture repo: 5 review files, no register; fake miner returns 4 patterns (1 with a fabricated quote, 1 with only 2 tasks) | report lists 2 valid patterns; register has 2 `open` rows; watermark = HEAD | automated test |
| 2 | Same repo, run again with no new commit | `nothing-new`; fake miner not called; register unchanged | automated test |
| 3 | Add one review commit that repeats an `open` pattern | `ready` with 1 file; `post` reports 0 patterns | automated test |
| 4 | Row `fixed` at commit X; new reviews after X show it on 3 tasks | reported as `regressed`, row back to `open` | automated test |
| 5 | Real repo smoke: `pre` on this repo with no register | `ready`, 40 files, `deferred` = total-40 | real run (Bash), output pasted |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests/test_self_review.py
python3 skills/self-review/scripts/self_review.py pre --repo . | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'], len(d['files']), d['deferred'])"
```

---

## Approach

**Pattern reference**: `skills/craft-spawn-prompt/scripts/memory_slice.py` — stdlib skill script layout and CLI style; `tests/test_dirty_worktrees.py` — `git init -b main` fixture repos in `tmp_path`; `experiments/self-review-spike/check_runs.py` — the citation check to port.

**Vital slice**: `pre` nothing-new gate + `post` citation check + open/rejected register filter + watermark-after-report (AC 1, 2, 5, 6, 10) — these carry the no-loop guarantee.
**Cut list**: no HTML report (Markdown only); no config file (constants + flags); no fuzzy text matching of titles (fingerprint/flag/Jaccard only).

Path B (`docs/brainstorming/BRAINSTORMING_LOG_self-review.md`). One file, three subcommands, stdlib only (`argparse`, `json`, `subprocess` for read-only `git log`/`git rev-parse`/`git status`, `re`, `pathlib`). Write files atomically (temp + `os.replace`).

---

## Edge Case Checklist

- [ ] Second-order loop: a fix task's own review is not evidence for its pattern (AC 8)
- [ ] Run stopped between report and `decide`: rows stay `open`, never re-proposed (AC 6)
- [ ] Watermark advances only after the report exists (AC 10); deferred files keep the watermark below HEAD (AC 4)
- [ ] Fabricated quote / unknown file / task outside the input set → citation dropped (AC 5)
- [ ] Review text is data (AC 14)
- [ ] `regressed` counts only post-`fixed_at` files (AC 7)
- [ ] Missing register = first run; `pre` creates nothing (only `post` writes)
- [ ] Watermark SHA no longer reachable (history rewritten) → treat as no watermark and say so on stderr

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/self-review/scripts/self_review.py` | new — the script |
| `tests/test_self_review.py` | new — AC 1-14 on fixture repos with a fake miner |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*`, `hooks/hooks.json`, `.claude/settings.json` | FR-001: no hook starts self-review |
| `memory/self-review/register.md` | created by the first real run, not by this task |
| `skills/self-review/SKILL.md`, `skills/learn/SKILL.md`, `AGENTS.md` | T256 |
| `memory/event-trace/` | not input (PRD Out of Scope) |

---

## Test Plan

pytest on `tmp_path` fixture repos (`git init -b main`, commit review files, a `PROJECT_KANBAN.md` with a `### Done` section). The fake miner is a JSON file the test writes; a counter proves AC 2. Plus the real-repo `pre` smoke run.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T255.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
