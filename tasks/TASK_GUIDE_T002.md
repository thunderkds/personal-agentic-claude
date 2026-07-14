# TASK_GUIDE — T002: update.sh
**Date**: 2026-06-10
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Create `update.sh` — pulls the latest supervisor framework from the central clone, reports what changed, and shows version/last-update info. Running `update.sh` in any project (or directly) must be the single command that propagates upstream improvements.

**Restated intent**:
> A developer runs `bash ~/.supervisor/update.sh` (or the project-local symlink) and their central clone is updated, with a clear report of what changed.

**Out of scope**:
- Re-running `setup.sh` logic (symlinks are already in place after T001)
- Automatic propagation to all installed projects — user must run `update.sh` per project or centrally

**Requirement Refs**:
- FR-006: Idempotent — safe to re-run
- FR-007: `git pull` the central repo; report version/last-update info
- FR-009: Works on macOS, Linux, WSL
- FR-010: Exit with clear error if Git not installed
- FR-011: Colored, structured log output
- NFR-004: POSIX-compatible shell only

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Running `update.sh` runs `git pull` on `$SUPERVISOR_PATH` and exits 0 | FR-007 |
| 2 | After pull, script prints the latest commit hash, date, and message | FR-007 |
| 3 | If `MANIFEST` changed upstream, script warns: "New resources available — re-run setup.sh to deploy" | FR-007 |
| 4 | If Git not installed, exits 1 with clear message before any action | FR-010 |
| 5 | If `$SUPERVISOR_PATH` does not exist, exits 1 with "Run setup.sh first" message | FR-007 |
| 6 | Running `update.sh` twice in a row exits 0 both times | FR-006 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Central clone exists and is up to date | Exits 0; prints "Already up to date" or commit info | Manual run |
| 2 | Upstream has new commits | Exits 0; prints new commit summary | Manual test with a local branch |
| 3 | `SUPERVISOR_PATH` not set, `~/.supervisor` missing | Exits 1 with "Run setup.sh first" | Manual test |

### Verification Command

```bash
bash ~/.supervisor/update.sh
echo "Exit code: $?"
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | |
| Review scope bounded to blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

1. Resolve `SUPERVISOR_PATH` (env var → `~/.supervisor` default)
2. Check git installed; check `$SUPERVISOR_PATH` is a git repo
3. Capture pre-pull HEAD SHA
4. Run `git -C "$SUPERVISOR_PATH" pull --ff-only`
5. Capture post-pull HEAD SHA; print commit log between the two
6. Diff `MANIFEST` between old and new HEAD — warn if changed
7. Print last-update summary line

Reuse the same `log_info` / `log_warn` / `log_error` helpers from `setup.sh` (source them, or copy the 5-line block).

---

## Edge Case Checklist

- [ ] `SUPERVISOR_PATH` not set and `~/.supervisor` does not exist — clear "run setup.sh first" message
- [ ] Git not installed — exit before any filesystem access
- [ ] No network / git pull fails — exit 1 with git's error message forwarded
- [ ] Repo has local uncommitted changes (user edited central clone) — `git pull` may fail; warn and suggest `git stash`
- [ ] `--ff-only` fails due to diverged history — surface git error clearly; do not force-reset

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `update.sh` | Create new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh` | Separate concern |
| `MANIFEST` | Data file — not touched by update logic |
| `.claude/**`, `templates/**` | General resources — updated via git pull, not script edits |

---

## Test Plan

1. Manual run with up-to-date central clone → verify clean "up to date" output
2. Manual run with `SUPERVISOR_PATH` pointing to nonexistent dir → verify exit 1 message
3. Simulate no-Git: `PATH="" bash update.sh` → verify early exit

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes (`shellcheck update.sh`)
- [ ] All manual test cases above pass
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: T002 ready for Stage 4 review
