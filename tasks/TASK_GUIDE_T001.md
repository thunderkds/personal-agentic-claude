# TASK_GUIDE — T001: setup.sh + MANIFEST
**Date**: 2026-06-10
**Complexity Level**: C1
**Risk Level**: Medium
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

Create `setup.sh` and `MANIFEST` — the core installer for the supervisor framework. Running `setup.sh` in any project must clone the supervisor repo to a central location, symlink all general resources listed in `MANIFEST` into the project, prompt the user to select greenfield or brownfield mode, and scaffold project-specific folders.

**Restated intent**:
> A developer runs `bash setup.sh` (or `curl | bash`) in a new project and the supervisor framework is fully wired up in under 30 seconds, with no manual file copying.

**Out of scope**:
- `update.sh` (T002)
- README documentation (T003)
- `.gitignore` (T004)
- Windows non-WSL support

**Requirement Refs**:
- FR-001: Clone repo to `~/.supervisor` (overridable via `SUPERVISOR_PATH`)
- FR-002: Prompt greenfield vs brownfield; symlink correct `CLAUDE.md`
- FR-003: Symlink `.claude/agents/`, `.claude/skills/`, `templates/`
- FR-004: Create fresh `tasks/` and `memory/` folders
- FR-005: Seed `memory/MEMORY.md` with minimal index header
- FR-006: Idempotent — safe to re-run
- FR-008: `--copy` flag copies instead of symlinking
- FR-009: Works on macOS, Linux, WSL
- FR-010: Exit with clear error if Git not installed
- FR-011: Colored, structured log output (info / warning / error)
- NFR-004: POSIX-compatible shell only

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Running `setup.sh` on a clean directory creates `~/.supervisor` (git clone) and symlinks `.claude/agents/`, `.claude/skills/`, `templates/`, and `CLAUDE.md` | FR-001, FR-002, FR-003 |
| 2 | Running `setup.sh` a second time exits 0 with no errors and makes no changes | FR-006 |
| 3 | When user selects greenfield, `./CLAUDE.md` symlinks to `~/.supervisor/CLAUDE.md`; brownfield symlinks to `CLAUDE_LEGACY.md` | FR-002 |
| 4 | `tasks/` and `memory/` directories exist after setup; `memory/MEMORY.md` contains the index header | FR-004, FR-005 |
| 5 | `setup.sh --copy` copies files instead of symlinking; re-run with `--copy` does not error | FR-008 |
| 6 | If Git is not installed, script exits 1 with a human-readable error before making any filesystem changes | FR-010 |
| 7 | If `./CLAUDE.md` already exists as a real file (not a symlink), script warns and prompts before overwriting | Edge case |
| 8 | All log lines use color codes (green=info, yellow=warn, red=error); output is readable without color (plain text fallback when not a TTY) | FR-011 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Empty project dir, Git installed, network available | `setup.sh` exits 0; symlinks created; `memory/MEMORY.md` exists | Manual run + `ls -la` |
| 2 | Re-run `setup.sh` in same dir | Exits 0, no duplicate symlinks, no errors | Manual run |
| 3 | `setup.sh --copy` in clean dir | Real files copied, not symlinks (`ls -la` shows no `->`) | Manual run + `ls -la` |
| 4 | Git not installed (simulate with `PATH` override) | Exits 1 with "Git is required" message before any filesystem change | Manual test |
| 5 | `SUPERVISOR_PATH=/tmp/mysupervisor setup.sh` | Clones to `/tmp/mysupervisor` instead of `~/.supervisor` | Manual run |

### Verification Command

```bash
# Run in a temp project dir
mkdir /tmp/test-supervisor && cd /tmp/test-supervisor
bash /path/to/setup.sh
ls -la .claude/ CLAUDE.md tasks/ memory/MEMORY.md
# Re-run (idempotency check)
bash /path/to/setup.sh
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

Use Option B (Symlink Manager + Manifest) from `BRAINSTORMING_LOG.md`:

1. **`MANIFEST`** — one resource path per line (relative to repo root), `#` for comments. Example:
   ```
   .claude/agents
   .claude/skills
   templates
   ```

2. **`setup.sh` structure**:
   - Helper functions: `log_info`, `log_warn`, `log_error` (colored, TTY-aware)
   - `check_git` — exit early if git missing
   - `clone_or_verify` — clone to `$SUPERVISOR_PATH` if not present; verify it's a git repo if it is
   - `prompt_mode` — ask greenfield/brownfield; return chosen CLAUDE file
   - `do_symlink` / `do_copy` — loop over `MANIFEST`, create symlinks or copy
   - `scaffold_project` — create `tasks/`, `memory/`, seed `MEMORY.md`
   - `main` — orchestrate; parse `--copy` flag

3. Apply the 50% rule: no per-path success messages — single summary at end. Logging helper is 5 lines max.

---

## Edge Case Checklist

- [ ] Target `.claude/` folder already exists with real files — warn, prompt before overwriting
- [ ] `~/.supervisor` exists but is not a git repo — detect (`git -C path rev-parse`) and abort with message
- [ ] `SUPERVISOR_PATH` set to non-existent path — `mkdir -p` before clone
- [ ] Script run from inside `~/.supervisor` itself — detect (`realpath` comparison) and abort
- [ ] `--copy` flag on second run after symlink install — detect existing symlinks, warn and skip (don't convert silently)
- [ ] Git not installed — check before any filesystem changes
- [ ] Target project already has a real `CLAUDE.md` — prompt before overwriting
- [ ] `MANIFEST` line points to a path that doesn't exist in the central repo — warn, skip, continue
- [ ] WSL: use `uname -r` to detect WSL; symlinks in WSL Linux filesystem work correctly (document Windows NTFS caveat)
- [ ] `memory/MEMORY.md` already exists — do not truncate; skip seeding silently

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh` | Create new |
| `MANIFEST` | Create new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | Supervisor rules — not part of installer |
| `CLAUDE_LEGACY.md` | Same |
| `.claude/agents/**` | Agent definitions — read-only from installer |
| `.claude/skills/**` | Skill definitions — read-only from installer |
| `templates/**` | Templates — read-only from installer |
| `tasks/` | Must not exist in this repo |
| `memory/` | Must not exist in this repo |

---

## Test Plan

1. Manual smoke test on macOS: fresh temp dir → run `setup.sh` → verify symlinks + scaffold
2. Manual idempotency test: re-run `setup.sh` → verify exit 0, no errors
3. Manual `--copy` test: run with flag → verify real files, not symlinks
4. Simulated no-Git test: `PATH="" bash setup.sh` → verify early exit with message
5. `SUPERVISOR_PATH` override test

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk: Medium)
- [ ] Lint passes (`shellcheck setup.sh`)
- [ ] All manual test cases above pass
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated if new patterns learned
- [ ] Supervisor notified: T001 ready for Stage 4 review
