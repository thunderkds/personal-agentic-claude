# TASK_GUIDE — T113: Update removes what upstream stopped shipping (unless edited), and kit tests stop shipping
**Date**: 2026-09-12
**Complexity Level**: C2 (Hard-Stop Gate 2 floor: installer restructure)
**Risk Level**: Medium
**Priority**: P2
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
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Probe, 2026-09-12, `main` `8115bc9`:

1. Upstream deleted `skills/optimize`; the project ran update:
   ```
   [warn]  upstream no longer ships 'skills/optimize/SKILL.md' — leaving your local copy untouched (not deleted).
   ```
   The skill stays in `skills/`, so Claude Code keeps loading a skill the kit removed
   (`carry_over_unprocessed`, `update.sh:299`).
2. A fresh install copies the kit's **own test suite** into every user project: 36 files under
   `.claude/hooks/tests/`, part of the 119 files / 1.4 MB a user commits. MANIFEST lists `.claude/hooks`
   as a whole directory.

ADR-0002: "A skill deleted upstream is removed if its lock hash still matches (never edited), and kept with
a warning if it was edited. Kit-internal tests (`.claude/hooks/tests/`) stop shipping into user projects."

**Restated intent**:
> After an update, a project holds only what the kit currently ships plus whatever the user changed — an
> unedited file the kit dropped is removed, an edited one is kept and named — and the kit's own test suite
> is never installed.

**Out of scope**:
- Moving `.claude/hooks/tests/` elsewhere in this repo (huge blast radius: pytest paths, CI, docs).
- Codex projections — already replaced wholesale on update (DDR-0007).
- Activated pack files (T117) — they are not lock entries, so this rule never touches them; do not add special handling.

**Requirement Refs**: none in `PRD.md`; authority ADR-0002.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, probe + ADR-0002, user-approved)
- [x] Domain terms align with glossary ("Manifest", "harness-lock.json")
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T109 — installer suites wired into CI

**Entry point**: `carry_over_unprocessed` in `update.sh`; MANIFEST exclusion handling in `lib/harness-fetch.sh`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Upstream deletes a skill; project copy unedited (hash == lock) → update deletes its files, removes now-empty directories, drops its lock entries, logs one "removed" line per skill | "unedited file the kit dropped is removed" |
| 2 | Upstream deletes a skill; project copy edited → kept, warned by path, lock entry kept (today's behaviour) | "edited one is kept and named" |
| 3 | A file the user added inside a kit directory (not in the lock) is never deleted, even if its directory's skill was removed upstream | never delete user files |
| 4 | MANIFEST supports an exclusion line (`!<path>`); `!.claude/hooks/tests` stops those files being copied at install, hashed into the lock, or reported as "new file" on update | "kit's own test suite is never installed" |
| 5 | An **existing** install that already has `.claude/hooks/tests/` unedited → the next update removes them via the AC1 rule | existing projects get the cleanup too |
| 6 | Every hook in `.claude/settings.json` still runs in an installed project without `.claude/hooks/tests/` (no hook imports from `tests/`) — each hook fed `{}` exits ≤ 1 | removing tests must not break hooks |
| 7 | This repo's own `python3 -m pytest .claude/hooks/tests/` still collects and runs the same tests (the exclusion affects installs only) | the kit's CI keeps its suite |
| 8 | Mutation control M1: disable deletion → AC1 test fails; M2: remove the `!` line → AC4 test fails | observed failing |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | install; upstream `git rm -r skills/optimize`; update | `skills/optimize` absent; no `skills/optimize/` key in lock; exit 0 | automated test |
| 2 | as SC1 but project `skills/optimize/SKILL.md` edited first | file present; stderr names it; lock keeps its entry | automated test |
| 3 | as SC1 with user-added `skills/optimize/NOTES.md` | `NOTES.md` present; kit files removed | automated test |
| 4 | fresh install | `.claude/hooks/tests` absent; no lock key starting `.claude/hooks/tests/` | automated test |
| 5 | project installed from the pre-task upstream (with tests), then updated from the new upstream | `.claude/hooks/tests` removed | automated test |
| 6 | installed project | each `.claude/hooks/*.py` fed `{}` exits ≤ 1 | automated test |
| 7 | this repo | pytest collects the same count as before (record the number) | automated |

### Verification Command (exact, runnable)

```bash
bash tests/test_update_removals.sh
bash tests/test_update.sh
bash tests/test_setup.sh
bash tests/test_install_update_smoke.sh
bash tests/test_harness_projection.sh
python3 -m pytest .claude/hooks/tests/ tests/ -q
shellcheck -x setup.sh update.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T113.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T113.md`.

---

## Approach

**Pattern reference**: `harness_manifest_path` / `harness_manifest_dest` (`lib/harness-fetch.sh:164-177`) —
MANIFEST line parsing lives in one place and every consumer calls it. Add exclusion parsing **there**, so
`harness_copy_manifest`, `build_fresh_file_list`, `write_harness_lock`, `is_under_manifest`,
`detect_symlinks` and `harness_project_manifest` all agree. A consumer that parses MANIFEST itself is how
T109's smoke-test defect happened.

**Vital slice**: the hash-matched deletion in `carry_over_unprocessed` plus one exclusion line.
**Cut list**:
- Glob patterns in exclusions — one literal path prefix is all that's needed.
- A `--prune` opt-in — ADR-0002 makes removal of unedited files the default.

---

## Edge Case Checklist

- [ ] Exclusion prefix must match path segments, not string prefixes: `!.claude/hooks/tests` must not exclude `.claude/hooks/tests_helper.py`
- [ ] Upstream temp clone missing a MANIFEST entry entirely (network hiccup / corrupt clone) must NOT trigger mass deletion — if the fresh file list is empty or a whole MANIFEST path is missing upstream, abort deletion with an error rather than delete everything under it
- [ ] Deleting a directory the user's shell is `cd`'d into is fine for a script, but never delete `skills/` or `agents/` roots themselves, even if empty
- [ ] The `.claude/skills` → `../skills` symlink is re-created after pruning (existing step order must stay)
- [ ] Hooks importing `tests/canon_paths.py` or any test helper → grep first; if found, that is a STOP-and-ask, not a silent move

---

## Documentation to Update

> Batch rule (user, 2026-09-12: "make sure the document also be updated"): these rows are **acceptance
> criteria**. Done requires each doc updated and its new text quoted in `tasks/TASK_REVIEW_T113.md`.
> Historical records are never rewritten.

| # | Doc | What is wrong today → what it must say |
|---|-----|----------------------------------------|
| D1 | `site/index.html` `#update-flow` bullet list (`:274-277`) | Only two cases listed → add the third: a file the kit no longer ships is removed if you never edited it, kept and named if you did |
| D2 | `RUNBOOK.md` Deploy step 4 health check (`:55-59`) | Add `test ! -d .claude/hooks/tests` so a release that ships the kit's test suite again fails the check |
| D3 | `MANIFEST` header comment | Document the `!<path>` exclusion syntax next to the existing destination-column explanation |

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `lib/harness-fetch.sh` | Exclusion-aware MANIFEST parsing used by every consumer |
| `update.sh` | Hash-matched deletion in `carry_over_unprocessed`; safety abort on empty/missing upstream paths |
| `setup.sh` | `write_harness_lock` honours exclusions (via the shared parser) |
| `MANIFEST` | Add `!.claude/hooks/tests`; document the `!` syntax in its header |
| `tests/test_update_removals.sh` | New — SC1–SC6 + M1/M2 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/tests/**` | Stays in this repo; only its shipping changes |
| `.claude/hooks/*.py` | Hook behaviour out of scope |
| `install_claude`, `install_settings` | T110/T111/T112 edit those |

---

## Test Plan

New `tests/test_update_removals.sh` (offline `file://` upstream clones — one pre-task snapshot, one with the
deletion/exclusion), one case per Success Criteria row plus mutation controls. Existing suites green; pytest
count for this repo unchanged.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — the installer now deletes files)
- [ ] `shellcheck -x setup.sh update.sh` clean
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T113.md` (Hard-Stop Gate 5)
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
