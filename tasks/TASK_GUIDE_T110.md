# TASK_GUIDE — T110: Update delivers `CLAUDE.md`, through the same edit-safe rule as every other file
**Date**: 2026-09-12
**Complexity Level**: C2 (Hard-Stop Gate 2 floor: installer restructure)
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`
**Branch**: worktree off `feat/easy-kit-one-command`; merges back into it

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` ("No silent loss")

---

## Requirement (Pillar 1 — Adapt the requirement)

Probe, 2026-09-12, `main` `8115bc9`: an upstream commit changed a skill, `CLAUDE.md` and
`.claude/settings.json`; a project installed earlier then ran `update.sh`:

```
skill: UPDATED
CLAUDE.md: NOT updated
settings.json: NOT updated
```

`update.sh` builds its work list from `MANIFEST` only (`build_fresh_file_list`, `update.sh:172`).
`CLAUDE.md` is not a MANIFEST path — `setup.sh` copies it separately from one of two sources
(`install_claude`, `setup.sh:379`, source chosen by `prompt_mode`: `CLAUDE.md` for a new project,
`CLAUDE_LEGACY.md` for an existing one). Its hash *is* recorded in the lock, and `update.sh` merely
carries that entry forward (`carry_over_unprocessed`). So new Hard-Stop Gates and rule changes never
reach any project after its first install. (`settings.json` is T111.)

**Restated intent**:
> Updating an Easy Kit project delivers the current `CLAUDE.md` rules from the same source the project
> was installed with, overwriting only when the user has not edited the file, and asking otherwise.

**Out of scope**:
- `.claude/settings.json` — T111.
- Pre-existing, non-kit `CLAUDE.md` at first install — T112.
- Menus, `/dev/tty`, the single command — T114. The conflict prompt keeps reading exactly what it reads today.
- Switching a project between new/existing (greenfield/brownfield) during update.

**Requirement Refs**: none in `PRD.md`; authority ADR-0002 ("`CLAUDE.md` and `.claude/settings.json` are covered by update").

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, probe + approved breakdown)
- [x] Domain terms align with glossary ("Greenfield", "Brownfield", "harness-lock.json")
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T109 — install/update suites wired into CI, so this change lands against a live gate

**Entry point**: `update.sh` — `main` → `process_files`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | New-project install, `CLAUDE.md` unedited, upstream `CLAUDE.md` changed → after update the project's `CLAUDE.md` is byte-identical to upstream `CLAUDE.md`, no prompt, lock hash refreshed | "delivers the current rules … overwriting only when not edited" |
| 2 | Existing-project (brownfield) install, unedited, upstream `CLAUDE_LEGACY.md` changed → project `CLAUDE.md` equals upstream **`CLAUDE_LEGACY.md`**, never greenfield `CLAUDE.md` | "from the same source the project was installed with" |
| 3 | User edited `CLAUDE.md`, upstream changed → the existing conflict path runs (diff, `[o]/[s]/[v]`); with no input the edit is kept, logged, and the run exits 2 | "asking otherwise" |
| 4 | The install source is recorded at install time in `.claude/harness-lock.json` and survives two consecutive updates unchanged | source must not be lost by `write_new_lock` rewriting the lock |
| 5 | A lock written **before** this task (no source recorded) → the source is inferred from `CLAUDE.md`'s first heading line; if it matches neither upstream heading, the file is treated as a conflict (AC3 path) — **never** silently overwritten | existing installs must upgrade safely |
| 6 | An old lock still parses in the old way: `extract_lock_pairs` / `lookup_lock_hash` results for every file key are unchanged by the new source record | backward compatibility of the lock |
| 7 | `tests/test_update.sh` and `tests/test_setup.sh` pass with no existing case modified | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | scratch repo, greenfield install from local upstream clone; upstream `CLAUDE.md` gets a marker line + commit; `update.sh </dev/null` | exit 0; project `CLAUDE.md` contains marker; `cmp` with upstream exits 0 | automated test |
| 2 | same, brownfield install (answer `2` via pty); marker added to upstream `CLAUDE_LEGACY.md` | project `CLAUDE.md` contains marker; greenfield marker absent | automated test (pty) |
| 3 | greenfield install; user appends a line to `CLAUDE.md`; upstream changed; `update.sh </dev/null` | exit 2; user line still present; "conflict" + `CLAUDE.md` in stderr | automated test |
| 4 | install; update; update | lock's recorded source identical after each run | automated test |
| 5 | install, then strip the source record from the lock (simulating an old lock); upstream changed | AC1/AC2 behaviour via heading inference | automated test |
| 6 | old lock whose `CLAUDE.md` first line was hand-edited to an unknown heading | conflict path, exit 2 without input, file unchanged | automated test |
| 7 | M1: make update ignore the recorded source (always greenfield) | SC2 fails | mutation control |

### Verification Command (exact, runnable)

```bash
bash tests/test_update_claude_md.sh
bash tests/test_update.sh
bash tests/test_setup.sh
bash tests/test_install_update_smoke.sh
shellcheck -x setup.sh update.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T110.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T110.md`.

---

## Approach

**Pattern reference**: `tests/test_update.sh` — offline `SUPERVISOR_REPO=file://` upstream clone,
`mktemp -d` workspace, `PASS`/`FAIL` counters. For the brownfield answer, drive the real prompt through a
pty (`script -qec`), as `memory/learnings.md` records for T108: `[ -t 0 ]`-gated prompts are
unreachable from a pipe.

**Vital slice**: treating `CLAUDE.md` as one more entry in `process_files` whose *upstream* path is the
recorded source file. The comparison and prompt logic already exist and must be reused, not copied.
**Cut list**:
- Changing a project's greenfield/brownfield choice during update — not requested.
- A lock format version number — one additive field does not warrant it.

**Supervisor decision — where the source is recorded**: add a top-level, non-hex field to
`.claude/harness-lock.json`, e.g. `"claude_md_source": "CLAUDE_LEGACY.md"`. It is invisible to
`extract_lock_pairs` (which only matches hex hash values), so old readers ignore it (AC6). `write_new_lock`
currently rebuilds the file from file-hash pairs only — it **must** re-emit the field, or AC4 fails on the
first update. Heading inference for old locks (AC5) compares the project file's first line with the first
line of each upstream candidate in the temp clone, so no heading text is hardcoded.

---

## Edge Case Checklist

- [ ] `CLAUDE.md` deleted by the user → treated like any missing file ("new file installed" from the recorded source)
- [ ] Upstream temp clone lacks the recorded source file → loud error naming it, no overwrite
- [ ] CRLF in a user-edited `CLAUDE.md` changes the hash → conflict path, not silent overwrite (correct)
- [ ] The JSON key/value is written without breaking the lock's existing shape for `harness-lock.json` readers in `.claude/hooks/` — grep for readers first
- [ ] Two updates in a row produce no git diff on the second (idempotent)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `update.sh` | Include `CLAUDE.md` in processing with its recorded/inferred source; re-emit the source field in `write_new_lock` |
| `setup.sh` | `write_harness_lock` records `claude_md_source` |
| `tests/test_update_claude_md.sh` | New — SC1–SC6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `MANIFEST` | `CLAUDE.md` is not a 1:1 path copy (two sources, one destination); adding it would break brownfield |
| `CLAUDE.md`, `CLAUDE_LEGACY.md` content | Delivery mechanism only; rule text is not this task's |
| `.claude/settings.json` handling | T111 |
| `lib/harness-fetch.sh` copy functions | T112/T113 own changes there; avoid merge conflicts |

---

## Test Plan

New `tests/test_update_claude_md.sh` following `tests/test_update.sh` conventions, one case per Success
Criteria row, plus M1. Exit codes asserted directly (never through a pipe). Regression: the four existing
installer suites unchanged and green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] `shellcheck -x setup.sh update.sh` clean
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T110.md` (Hard-Stop Gate 5)
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor (Supervisor-only memory writes)
- [ ] Supervisor notified: task ready for Stage 4 review
