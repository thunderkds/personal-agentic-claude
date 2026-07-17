# TASK_GUIDE — T033: New update.sh — hash-lock compare + per-file conflict prompt
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
6. Read `memory/codebase-map.md`; read the existing `update.sh` (central-clone-pull model, to be entirely replaced) and T031/T032's outputs in full before starting

---

## Requirement (Pillar 1 — Adapt the requirement)

The current `update.sh` runs `git pull --ff-only` inside the central `~/.supervisor` clone — irrelevant once T032 removes the central clone entirely. Per ADR-0001, `update.sh` becomes a distinct, later operation on the *working repo itself*: re-fetch fresh via `lib/harness-fetch.sh` (T031), then for each `MANIFEST` path, compare the working repo's current file hash against the hash recorded in `.claude/harness-lock.json` (written by T032's `setup.sh`). Untouched files (hash still matches) overwrite silently. Files the user has customized (hash differs) get a diff shown and a per-file prompt: overwrite / skip / view diff again.

**Restated intent**:
> Replace `update.sh` entirely with a script that: requires the target to be a git repo, refuses if it detects a symlink at any `MANIFEST` path (old-model install — instructs the user to migrate, doesn't auto-convert), re-fetches the harness fresh, and for each `MANIFEST` path either silently overwrites (hash unchanged since install) or interactively prompts on a real diff (hash changed — user customized it).

**Out of scope**:
- Migration from the old symlink model is explicitly deferred (ADR-0001 Follow-up) — `update.sh` only **detects and refuses** on a symlink, it does not convert it.
- Packs are out of scope — `update.sh` does not touch `packs/`.
- `setup.sh` itself is not touched in this task (T032's responsibility) — this task only consumes what T032 produces (`.claude/harness-lock.json`).

**Requirement Refs**: ADR-0001 (Decision — `update.sh` bullet, "Migration for existing symlink-based installs is out of scope" bullet)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match ADR-0001's `update.sh` bullet
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary ("harness-lock.json")
- [ ] Every Acceptance Criterion below traces to ADR-0001
- [ ] Requirement Ref (ADR-0001) is fully covered by the Acceptance Criteria below

> An agent must NOT start implementing until this gate is checked. If anything here is unclear, STOP and ask the Supervisor.

---

## Dependencies & Reachability

**Depends on**: `T031 — lib/harness-fetch.sh must exist`, `T032 — setup.sh must write .claude/harness-lock.json in the shape update.sh reads`

**Entry point**: `bash update.sh` (repo root entrypoint, new script — replaces the old central-clone-pull `update.sh` entirely)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Running `update.sh` in a non-git directory exits non-zero with a clear error before touching any files | ADR-0001 Decision — git-readiness prerequisite check |
| 2 | Running `update.sh` when a `MANIFEST` path is a symlink (old-model install) exits non-zero with an explicit message instructing the user to migrate first — does not convert the symlink | ADR-0001 Decision — "update.sh detects a symlink... and refuses" |
| 3 | Running `update.sh` when every installed file's current hash still matches `.claude/harness-lock.json` overwrites all files silently with the freshly-fetched upstream versions, and re-records the (unchanged) hashes | ADR-0001 Decision — "untouched — safe... overwrite silently" |
| 4 | Running `update.sh` when one installed file's hash no longer matches the lock (user edited it) shows a diff for that file and prompts (overwrite / skip / view diff again) before proceeding to the next file — does not silently overwrite or silently skip | ADR-0001 Decision — "show a diff and prompt per-file" |
| 5 | After `update.sh` completes, `.claude/harness-lock.json` reflects the hashes of whatever the user actually chose to accept (overwritten files get the new upstream hash; skipped files keep their prior recorded hash) | ADR-0001 Decision — hash-lock re-recording |
| 6 | `update.sh` does not require or create any `$SUPERVISOR_PATH`/`~/.supervisor` directory | ADR-0001 Context — no persistent central clone |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Freshly-`setup.sh`-installed repo, no local edits, run `update.sh` | All files overwritten silently, no prompts, hashes match new lock | automated test |
| 2 | Same repo, one agent file manually edited, run `update.sh` non-interactively (simulate stdin) | Prompt fires for the edited file only; choosing "skip" leaves the edit intact and lock unchanged for that file | automated test |
| 3 | Repo with a symlink still present at a `MANIFEST` path | `update.sh` exits non-zero with migration-instruction message, no files touched | automated test |
| 4 | Non-git directory | `update.sh` exits non-zero before any action | automated test |

### Verification Command (exact, runnable)

```bash
# tests/test_update.sh (new): builds on T032's scratch-repo test harness — runs setup.sh first
# to produce a real installed repo + harness-lock.json, then exercises update.sh's four
# branches above (untouched-overwrite, edited-conflict-prompt, symlink-refusal, non-git-refusal).
bash tests/test_update.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | Run `setup.sh` then `update.sh` against a real scratch repo, edit one file, confirm the interactive prompt behaves as expected |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | N/A | Pure backend/tooling task — no UI component |
| **UI: Design-system compliance** | N/A | Pure backend/tooling task — no UI component |
| **UI: Responsiveness** | N/A | Pure backend/tooling task — no UI component |

---

## Approach

Reuse `lib/harness-fetch.sh` (T031) for the re-fetch step — identical to `setup.sh`'s own fetch call. For each `MANIFEST` path: compute the current on-disk hash, compare to `.claude/harness-lock.json`'s recorded value for that path (missing entry = treat as "never tracked," prompt same as a conflict, don't assume safe). On match: `cp -r` from the fresh temp fetch, update nothing else. On mismatch: `diff -u` (or equivalent) the working file against the freshly-fetched version, print it, prompt `[o]verwrite / [s]kip / [v]iew diff again`, loop on `v`, act on `o`/`s`. Symlink detection: before the hash-compare loop even starts, check every `MANIFEST` path with `[ -L "$path" ]` and abort the whole run with a migration-instruction message if any are found — don't process files one-by-one past that point (all-or-nothing at the top, not a per-file exception).

---

## Edge Case Checklist

- [ ] Non-interactive/piped `update.sh` invocation (no TTY on stdin) must have a defined fallback — likely: refuse to run destructively, print "conflicts detected, re-run interactively" rather than guessing overwrite-or-skip (mirrors `setup.sh`'s existing `prompt_packs`/`prompt_mode` non-interactive defaults)
- [ ] A `MANIFEST` path present upstream but not yet in `.claude/harness-lock.json` (e.g. a new resource added since last install) — treat as new, install directly, no conflict prompt (nothing to conflict with)
- [ ] A `MANIFEST` path that existed in the lock but is no longer in the upstream `MANIFEST` (resource removed upstream) — decide and document behavior: leave the local file alone with a warning, don't silently delete user content
- [ ] Hash comparison must use the same hash algorithm/normalization as T032's writer — cross-check against T032's actual implementation, not just this guide's prose, before finalizing

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `update.sh` | Full rewrite — replace central-clone-pull model entirely with hash-lock compare + per-file conflict prompt |
| `tests/test_update.sh` | New file — builds on T032's scratch-repo test harness |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh` | Already rewritten in T032 — this task only consumes its output (`.claude/harness-lock.json` shape) |
| `packs/`, `install_pack()` | Explicitly out of scope per ADR-0001 |

---

## Test Plan

Automated: scratch-repo tests covering all four branches in Success Criteria above (silent overwrite, conflict prompt with simulated stdin input, symlink refusal, non-git refusal). Manual: real end-to-end run — `setup.sh` then edit a file then `update.sh` — confirming the diff display and prompt are legible in an actual terminal.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — mandatory)
- [ ] Lint passes (`shellcheck update.sh`)
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in a real scratch repo
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
