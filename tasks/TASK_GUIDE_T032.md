# TASK_GUIDE — T032: Rewrite setup.sh for direct-to-repo install
**Date**: 2026-07-17
**Complexity Level**: C2
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
5. C2 — apply brainstorm/decompose/verify depth from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Read `memory/codebase-map.md` — `setup.sh` is a hub file (every project installation depends on it); read T031's output (`lib/harness-fetch.sh`) in full before touching this file

---

## Requirement (Pillar 1 — Adapt the requirement)

`docs/adr/0001-direct-repo-install-no-central-clone.md` (ADR-0001) replaces `setup.sh`'s central-clone + symlink model with direct file copies via the shared `lib/harness-fetch.sh` (T031). This task rewires `setup.sh` itself: drop `clone_or_verify`'s persistent `$SUPERVISOR_PATH` clone, drop the symlink branch of `install_path`/`install_claude`/`install_settings`, always copy, add the new git-repo-on-target prerequisite check, and write `.claude/harness-lock.json` (content hash per installed `MANIFEST` path) so T033's `update.sh` has state to compare against.

**Restated intent**:
> `setup.sh` becomes a fresh-install script: it fetches the harness via `lib/harness-fetch.sh` into a temp dir, copies every `MANIFEST` path + `CLAUDE.md`/`CLAUDE_LEGACY.md` into the working repo as real files (always overwriting — no conflict logic, this is first-time install), refuses to run if the working directory isn't a git repo, and records the installed-file hashes to `.claude/harness-lock.json`.

**Out of scope**:
- Do not implement `update.sh`'s conflict-handling logic — that's T033. `setup.sh` never prompts about conflicts; it always overwrites.
- Packs (`install_pack()`) keep their current symlink-from-central-clone behavior — do not touch that function or its call sites in this task.
- Migration for existing symlink-based installs is explicitly deferred (ADR-0001 Follow-up) — do not add auto-migration logic here.

**Requirement Refs**: ADR-0001 (Decision — `setup.sh` bullet), user statement "the setup will be the initialize, users should accept the overwrite all"

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match ADR-0001's `setup.sh` bullet and the user's explicit "always overwrite" instruction
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary ("Temp-clone-copy-discard", "harness-lock.json")
- [ ] Every Acceptance Criterion below traces to ADR-0001
- [ ] Requirement Ref (ADR-0001) is fully covered by the Acceptance Criteria below

> An agent must NOT start implementing until this gate is checked. If anything here is unclear, STOP and ask the Supervisor.

---

## Dependencies & Reachability

**Depends on**: `T031 — lib/harness-fetch.sh must exist and expose harness_fetch()/harness_copy_manifest()`

**Entry point**: `bash setup.sh` (repo root entrypoint, unchanged invocation from today)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Running `setup.sh` in a git-initialized empty-ish target directory produces real file copies (not symlinks) of every `MANIFEST` path and `CLAUDE.md` (or `CLAUDE_LEGACY.md` per mode prompt) | ADR-0001 Decision — "copy ... as real file copies" |
| 2 | Running `setup.sh` in a directory that is **not** a git repository exits non-zero with a clear error, before writing any files | ADR-0001 Decision — "new prerequisite check... git-readiness" |
| 3 | After a successful run, `.claude/harness-lock.json` exists and contains one hash entry per installed `MANIFEST` path | ADR-0001 Decision — "write .claude/harness-lock.json" |
| 4 | Running `setup.sh` a second time in the same directory overwrites every installed file unconditionally — no prompt, no skip (matches existing files always replaced) | ADR-0001 Decision — "setup.sh always full-overwrite" |
| 5 | No `$SUPERVISOR_PATH`/`~/.supervisor` directory is created or required at any point during `setup.sh`'s run | ADR-0001 Context — "no persistent central clone anywhere" |
| 6 | `install_pack()` and its call sites are unchanged from the current file | Out of scope — packs excluded per ADR-0001 |
| 7 | `.claude/settings.json` install behavior (copy-only, never overwrite an existing one) is preserved unchanged | ADR-0001 Consequences — ".claude/settings.json handling ... stays as-is" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Empty git-initialized target dir, run `bash setup.sh` non-interactively | `.claude/agents/`, `.claude/skills/`, `templates/`, `CLAUDE.md` present as real files; `.claude/harness-lock.json` present with correct hashes | automated test |
| 2 | Non-git target dir, run `bash setup.sh` | Exits non-zero, no files written | automated test |
| 3 | Re-run `setup.sh` after manually editing an installed file | Edited file is silently overwritten back to upstream (setup always overwrites) | automated test |

### Verification Command (exact, runnable)

```bash
# tests/test_setup.sh (new, or extend T031's harness): spins up a scratch git-initialized
# temp directory, runs `bash setup.sh` against it (non-interactive mode / --pack= flags as
# needed), asserts file presence, harness-lock.json shape, and the non-git-dir rejection case.
bash tests/test_setup.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_setup.sh` — 15/15 assertions pass (re-run independently by reviewer, not just cited from the implementer's report). Covers AC1 (real copies, all MANIFEST paths), AC2 (non-git rejection, zero files written), AC3 (harness-lock.json content, permission-independent hash), AC4 (unconditional overwrite on re-run), AC5 (no central-clone dir created), AC7 (settings.json copy-only). |
| Verification command run | ☑ pass | `bash tests/test_setup.sh` → `----- summary: 15 passed, 0 failed -----` (reviewer's own run, worktree `.claude/worktrees/agent-a60c669423604cff2`). |
| Negative cases hold | ☑ pass | test2: non-git target → rc=1, zero files written, clear "not a git repository" error. test3: locally-edited file silently restored to upstream content on re-run. |
| `verify` skill — works in running app | ☑ pass | Drove the real CLI directly (not the author's test suite): offline fixture repo, `bash setup.sh` non-interactive → exit 0, all files landed, `.claude/harness-lock.json` valid JSON with correct per-file hashes. Probed a symlink-at-MANIFEST-path scenario (old-model leftover) — correctly overwritten to a real dir, target of the old symlink untouched. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff isolated to `setup.sh` (modified) + `tests/test_setup.sh` (new). `git diff main --stat` confirms no other files touched; `install_pack()`/`packs/` untouched per AC6. |
| Full smoke suite still green (no regression) | ☑ pass | `bash tests/test_harness_fetch.sh` (T031's suite) → `9 passed, 0 failed` — reviewer's own re-run, confirms no regression from T032's changes. |
| **UI: Visual regression** | N/A | Pure backend/tooling task — no UI component |
| **UI: Design-system compliance** | N/A | Pure backend/tooling task — no UI component |
| **UI: Responsiveness** | N/A | Pure backend/tooling task — no UI component |

---

## Approach

Keep `resolve_repo_url`, `prompt_packs`, `prompt_mode`, `install_pack`, `install_settings`, and the logging helpers unchanged. Replace `clone_or_verify()`'s body to call `lib/harness-fetch.sh`'s `harness_fetch()` against a `mktemp -d` instead of `$SUPERVISOR_PATH`. Replace `install_path()`/`install_claude()`'s symlink branch (`ln -s`) with unconditional `cp -r` (drop the `--copy` flag's now-redundant distinction, or keep `--copy` as a no-op alias for backward-compat CLI usage — Supervisor's call at Stage 2 approval time). Add a new `check_target_is_git_repo()` function (mirrors `check_git`'s shape) run early in `main()`, before `clone_or_verify`. Add hash-writing (`sha256sum` or `shasum -a 256` — check what's already available/used elsewhere in this repo's tooling) at the end of `main()`, iterating the same `MANIFEST` list already being installed.

---

## Edge Case Checklist

- [ ] `--copy` flag's meaning changes now that there's no symlink mode to opt out of — decide whether to keep it as a harmless no-op (for scripts/docs that already reference it) or remove it and warn if passed
- [ ] `mode_choice` (greenfield/brownfield CLAUDE.md selection) interactive prompt logic is unaffected — only the *installation mechanism* changes, not the CLAUDE.md source-selection UX
- [ ] Hash computation must be stable/reproducible (same content → same hash) regardless of file permission bits, so `update.sh` (T033) doesn't false-positive on a chmod-only change
- [ ] `scaffold_project()` (tasks/, memory/ creation) is unaffected — those were never symlinked and stay exactly as-is

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh` | Rewrite `clone_or_verify`, `install_path`, `install_claude`; add git-repo-check function; add harness-lock.json writer; source `lib/harness-fetch.sh` |
| `tests/test_setup.sh` | New file — scratch-repo test harness |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `update.sh` | Rewritten in T033, not this task |
| `packs/`, `install_pack()` | Explicitly out of scope per ADR-0001 |
| `.claude/settings.json` install logic | Already correct (copy-only); preserve unchanged |

---

## Test Plan

Automated: scratch git-initialized temp dirs exercising fresh install, non-git-dir rejection, re-run overwrite behavior, and harness-lock.json shape/hash correctness. Manual: one real end-to-end run against an actual scratch project directory, confirming `.claude/agents/*.md` etc. are real files (`file` command or `[ ! -L path ]` check) not symlinks.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — mandatory)
- [ ] Lint passes (`shellcheck setup.sh`)
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in a real scratch repo
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
