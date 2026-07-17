# TASK_GUIDE — T031: lib/harness-fetch.sh — shared temp-clone-copy-discard fetch
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
6. Read `memory/codebase-map.md` — this touches the repo's own install tooling, confirm no other script depends on the current `clone_or_verify`/`install_path` shape besides `setup.sh`/`update.sh`

---

## Requirement (Pillar 1 — Adapt the requirement)

User wants each working repo to be fully self-contained on install — no dependency on a persistent central `~/.supervisor` clone. `docs/adr/0001-direct-repo-install-no-central-clone.md` (ADR-0001) locks the mechanism: `git clone --depth 1` into a `mktemp -d` (EXIT-trap cleaned up), copy `MANIFEST`-listed paths + `CLAUDE.md`/`CLAUDE_LEGACY.md` out as real files, discard the temp clone. This mechanism must be shared between `setup.sh` (T032) and the new `update.sh` (T033), so it's factored into one lib file first.

**Restated intent**:
> Extract the temp-clone-copy-discard fetch mechanism into `lib/harness-fetch.sh`, a sourceable shell library exposing functions both `setup.sh` and `update.sh` can call, so the fetch logic exists in exactly one place.

**Out of scope**:
- Do not modify `setup.sh` or `update.sh` themselves in this task — that's T032/T033. This task only creates the library and leaves the existing scripts untouched (they'll be rewired in the dependent tasks).
- Do not implement the hash-lock comparison or conflict-prompt logic — that belongs to T033.
- Packs (`packs/`, `install_pack()`) are explicitly out of scope per ADR-0001.

**Requirement Refs**: ADR-0001 (Decision section — "temp-clone-copy-discard", "shared lib file")

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match ADR-0001's Decision section
- [x] Domain terms align with `PROJECT_SPEC.md` glossary ("Temp-clone-copy-discard")
- [x] Every Acceptance Criterion below traces to ADR-0001
- [x] Requirement Ref (ADR-0001) is fully covered by the Acceptance Criteria below

> An agent must NOT start implementing until this gate is checked. If anything here is unclear, STOP and ask the Supervisor.

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `lib/harness-fetch.sh` — sourced by `setup.sh` (T032) and `update.sh` (T033); standalone until then.
> `Standalone — N/A: this task produces a library with no caller yet; T032/T033 wire it in.`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `lib/harness-fetch.sh` defines a function (e.g. `harness_fetch <repo_url> <dest_tmp_dir>`) that clones the repo with `--depth 1` into a caller-supplied temp dir | ADR-0001 Decision — "git clone --depth 1 ... into a mktemp -d" |
| 2 | A second function (e.g. `harness_copy_manifest <tmp_dir> <target_dir> <manifest_path>`) reads `MANIFEST`, and for each listed path copies it (`cp -r`) from the temp clone into the target directory, creating parent dirs as needed | ADR-0001 Decision — "copy MANIFEST-listed paths ... as real file copies" |
| 3 | Library sets an `EXIT` trap (or exposes a cleanup function the caller registers) that `rm -rf`s the temp dir on both normal exit and interrupt (Ctrl-C) | ADR-0001 Consequences / Edge Case Checklist — "temp clone must not persist... trap must fire on signal interruption" |
| 4 | Fetch fails loudly (non-zero exit, clear error message) and does not leave a partially-populated target directory if the `git clone` step itself fails (e.g. network error) | ADR-0001 Edge Case Checklist — "must not leave the working repo half-updated" |
| 5 | The library does not modify `setup.sh`, `update.sh`, or any file outside `lib/` | Out of scope — task isolation for T032/T033 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A valid repo URL and empty target dir, `MANIFEST` listing e.g. `.claude/agents` | Target dir contains a real copy (not symlink) of `.claude/agents/`, temp dir is gone after the call returns | automated test |
| 2 | An invalid/unreachable repo URL | Function exits non-zero, prints an error, target dir is untouched (no partial copy) | automated test |
| 3 | Fetch interrupted mid-clone (simulate via SIGINT or a killed subprocess) | Temp dir does not persist in `/tmp` after the interrupt | automated test |

### Verification Command (exact, runnable)

```bash
# Supervisor/QA writes a shell test harness (e.g. tests/test_harness_fetch.sh) that sources
# lib/harness-fetch.sh, runs it against a local fixture repo (or file:// path to avoid network
# flakiness), and asserts on file presence + temp-dir absence.
bash tests/test_harness_fetch.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_harness_fetch.sh` — 9/9 assertions pass under **both bash and dash (POSIX)**. Covers AC1 (fetch), AC2 (MANIFEST copy + absent-entry skip), AC3 (temp removed on normal exit AND on SIGINT), AC4 (bad URL → non-zero + error + untouched target). Output: `----- summary: 9 passed, 0 failed -----` (bash exit=0, dash exit=0) |
| Verification command run | ☑ pass | `bash tests/test_harness_fetch.sh` → all 9 PASS, exit 0. Real-world smoke: `harness_fetch https://github.com/thunderkds/personal-agentic-claude.git` succeeded, copied `.claude/*` + `templates` as real dirs, temp dir cleaned on process exit. Zero `/tmp/harness-fetch.*` leaks after a fresh run. |
| Negative cases hold | ☑ pass | Bad `file://` URL → `harness_fetch` returns rc=1, prints `[error] Failed to clone ...`, target dir left empty (no partial copy). Absent MANIFEST entry (`does/not/exist`) warned + skipped, not aborted. |
| `verify` skill — works in running app | ☑ N/A | Library has no standalone runtime surface until T032/T033 wire it in; verify at T032/T033 instead. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff isolated to new `lib/harness-fetch.sh` + `tests/test_harness_fetch.sh`. `git status --short` shows only `lib/` and `tests/`. `setup.sh`/`update.sh` untouched. |
| Full smoke suite still green (no regression) | ☑ pass | Existing hook suite `python3 -m pytest .claude/hooks/tests/ -q` → `12 passed in 0.02s`. New shell suite `bash tests/test_harness_fetch.sh` → 9 passed. |
| **UI: Visual regression** | N/A | Pure backend/tooling task — no UI component |
| **UI: Design-system compliance** | N/A | Pure backend/tooling task — no UI component |
| **UI: Responsiveness** | N/A | Pure backend/tooling task — no UI component |

---

## Approach

Model the two core functions closely on the existing logic already in `setup.sh`'s `clone_or_verify()` and `install_path()` (setup.sh:46-69, 193-231) — same `git clone` invocation shape, same `MANIFEST` comment/blank-line skipping (`case "$line" in '#'*|'') continue ;;`). The only structural change is: destination is always a `mktemp -d`, not `$SUPERVISOR_PATH`, and the copy step always uses `cp -r` (no symlink branch — that's dead code being removed in T032, not duplicated here).

---

## Edge Case Checklist

- [x] `mktemp -d` must produce a unique dir per invocation — no collision across concurrent runs (uses `mktemp -d "${TMPDIR:-/tmp}/harness-fetch.XXXXXX"`)
- [x] Cleanup trap must fire even if the calling script `exit 1`s early elsewhere (single `EXIT` trap does the cleanup; `INT`/`TERM`/`HUP` re-exit into it — verified by test3 SIGINT case)
- [x] MANIFEST parsing must strip `\r` (CRLF-safe) exactly as the current `setup.sh` main loop does (setup.sh:377) — `_line=$(printf '%s' "$_line" | tr -d '\r')`
- [x] A `MANIFEST` entry that doesn't exist in the fetched clone should warn and skip, not abort the whole fetch (matches current `install_path`'s behavior at setup.sh:199-202) — verified by test1 `does/not/exist` assertion

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `lib/harness-fetch.sh` | New file — `harness_fetch()`, `harness_copy_manifest()`, cleanup trap helper |
| `tests/test_harness_fetch.sh` | New file — shell test harness for the above (or equivalent test runner already used in this repo — check for an existing `tests/` convention first) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh` | Rewired in T032, not this task — keep this task's diff isolated to the new library |
| `update.sh` | Rewired in T033, not this task |
| `packs/`, `install_pack()` in `setup.sh` | Explicitly out of scope per ADR-0001 |

---

## Test Plan

Shell-level unit tests against a local fixture (a tiny `file://` git repo created in the test setup, or a throwaway GitHub test fixture if the repo already has a pattern for this — check `tests/` first) covering: successful fetch+copy, unreachable-repo failure, and cleanup-on-interrupt. Manual smoke: run `harness_fetch` against this repo's own real GitHub URL once to confirm the real-world path works end-to-end.

---

## Completion Checklist

- [x] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run — deferred to Supervisor Stage 4 (sub-agent has no `Skill` tool)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — mandatory) — deferred to Supervisor Stage 4
- [~] Lint passes — `shellcheck` **not installed** in this environment; fell back to `sh -n lib/harness-fetch.sh` (syntax OK) + full run under both `bash` and `dash` (POSIX). Supervisor to run `shellcheck` at Stage 4 if available.
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `Skill({ skill: "verify" })` run — N/A, see Evidence table note; verified via T032
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned) — flagged to Supervisor below (Supervisor-only writes)
- [x] Supervisor notified: task ready for Stage 4 review
