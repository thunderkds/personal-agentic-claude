# TASK_GUIDE — T137: A backup is named after the kit version it replaces, and Update's "overwrite" takes one too
**Date**: 2026-10-08
**Complexity Level**: C2 — 3+ files (`setup.sh`, `lib/harness-fetch.sh`, `lib/harness-update.sh`, tests, docs) and one design choice (the lock field's shape)
**Risk Level**: Medium — changes the installer's file-moving path; a mistake here loses a user's edits
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md`, then `lib/harness-fetch.sh` (`harness_backup_path`, ~line 227), `lib/harness-update.sh` (`lookup_lock_hash`, `extract_lock_pairs`, the conflict `case` ~line 225), `setup.sh` (`write_harness_lock`, ~line 412; plan printing ~line 687), `tests/test_install_backups.sh` and `tests/test_update.sh` (patterns to imitate)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-08: *"checking the posible to update the version for backup file when update"* — then, after the Supervisor's feasibility answer, chose **"Plan + implement"**.

**Diagnosis (Supervisor, 2026-10-08, read from the files):**
- `harness_backup_path` (`lib/harness-fetch.sh:243`) names backups `<dst>.bak`, `<dst>.bak.1`, `<dst>.bak.2` … — a counter, not a version.
- `.claude/harness-lock.json` records `claude_md_source` and per-file content hashes only. **No kit version is recorded anywhere**, so no backup can be named after one today.
- Update's conflict path, decision `o` (`lib/harness-update.sh:226-230`), calls `install_file` directly — **a customized file the user chooses to overwrite is replaced with no backup.** Only Reinstall backs up.
- The kit is fetched with `git clone --depth 1`, so the fetched commit is available as `git -C "$HARNESS_TEMP_DIR" rev-parse --short HEAD`.

**Restated intent:**
> Every install/update records the kit's short commit ID in the lock. Whenever the kit moves a
> user's file aside — Reinstall, first install, **and now Update's "overwrite"** — the backup is
> named after the kit version being *replaced*: `<dst>.bak-<old-commit>`. If the lock has no
> commit (an install made before this change) the name uses today's date, `<dst>.bak-<YYYYMMDD>`.
> A taken name never overwrites: a counter is appended (`.bak-<id>.1`, `.2`, …) exactly as now.

**Out of scope:**
- Restoring backups, listing them, or pruning old ones.
- Changing which files Update prompts about, the diff display, or the `s` (skip) / `eof` paths.
- `harness_install_canon_symlinks`' `<link>.bak` for a pre-T096 real directory (`lib/harness-fetch.sh:454-480`) — that path fails rather than numbering, a separate design; leave it.
- A semver/tag scheme. The commit ID is the version.

**Requirement Refs**: no `PRD.md` — N/A. ADR-0002 "No silent loss" is the governing decision; this task closes the Update-overwrite gap in it.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-08; user chose "Plan + implement" on this design)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `harness_backup_path`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | After install, update, and reinstall, `.claude/harness-lock.json` has a top-level `"kit_commit"` field holding the fetched clone's short commit ID | "records the kit's short commit ID" |
| 2 | Reinstall and first install name a backup `<dst>.bak-<commit recorded in the lock before this run>` | "named after the kit version being replaced" |
| 3 | With no lock, or a lock with no `kit_commit` (a pre-T137 install), the backup is `<dst>.bak-<YYYYMMDD>` (today's date, `date +%Y%m%d`) | "If the lock has no commit" |
| 4 | Update, decision `o` on a customized file: the user's file is moved to `<dst>.bak-<old-commit>` **before** the kit copy lands, and a `[warn]` line names the backup | "and now Update's overwrite" |
| 5 | A taken backup name is never overwritten: the second backup of the same path at the same version is `<name>.1`, the third `<name>.2` | "A taken name never overwrites" |
| 6 | `"kit_commit"` is **not** read as a file entry: `extract_lock_pairs` and `lookup_lock_hash` never return it, and Update never treats it as a removed file (see Edge Case 1 — a short SHA is hex, so the current regex *does* match it) | not breaking Update |
| 7 | The install/reinstall plan lines (`setup.sh` ~line 696-700) show the real backup name, not a hard-coded `.bak` | user sees what will happen |
| 8 | Docs describing backup names say the new form: `site/index.html` (Install + Update flow), `RUNBOOK.md:222`, and ADR-0002 line 70 gets a one-line "Amended by T137" note — not a rewrite | docs ride with code (board rule, 2026-09-12) |
| 9 | Update, decision `s` and `eof`: no backup is made, file untouched (unchanged behaviour, now asserted) | Out of scope stays out |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture kit at commit A installed; user edits `CLAUDE.md`; kit advances to commit B; Reinstall | `CLAUDE.md.bak-<A>` holds the user's edit; lock `kit_commit` = B | `tests/test_install_backups.sh` |
| 2 | Same, but Update with input `o` for `agents/backend.md` | `agents/backend.md.bak-<A>` holds the edit; file now = kit B copy | `tests/test_update.sh` |
| 3 | Lock with `kit_commit` removed by hand; Reinstall | backup suffix is `-$(date +%Y%m%d)` | test |
| 4 | `CLAUDE.md.bak-<A>` already exists; Reinstall again at same A | new backup is `CLAUDE.md.bak-<A>.1`, the first is byte-identical | test |
| 5 | Lock containing `"kit_commit": "abc1234"`; run Update | no `kit_commit` file is created, removed, or prompted about; removal plan does not list it | test |
| 6 | Update with input `s` | no `*.bak*` created | test |

**Mandatory mutation controls** (run each, paste RED output, revert):
- **M1**: in the Update `o` branch, delete the new backup call → SC2 must go RED.
- **M2**: make `extract_lock_pairs` match `kit_commit` again (revert your exclusion) → SC5 must go RED.
- **M3**: hard-code the suffix to `.bak` → SC1 and SC4 must go RED.

### Verification Command (exact, runnable)

```bash
bash tests/test_install_backups.sh && bash tests/test_update.sh && bash tests/test_update_removals.sh \
  && bash tests/test_install_update_smoke.sh && sh scripts/validate.sh \
  && shellcheck -x setup.sh update.sh lib/harness-update.sh lib/harness-fetch.sh \
  && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T137.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T137.md`.

---

## UI / Design Acceptance Criteria

> N/A — no UI component. The `site/index.html` change in AC8 is prose only; all three UI Evidence rows ☐ N/A.

---

## Approach

**Pattern reference**: `lib/harness-fetch.sh` `harness_backup_path` — keep its contract (missing → nothing; identical → nothing; else move to first free name, `[warn]`, return 1 on `mv` failure). Tests: imitate `tests/test_install_backups.sh`'s offline fixture kit (file:// clone).

**Vital slice**: the `kit_commit` lock field + a version suffix inside `harness_backup_path` + one backup call in Update's `o` branch.
**Cut list**: restore/list/prune commands; tag/semver names; the canon-symlink `.bak` path.

Recommended shape (Supervisor decision; push back if the code says otherwise):
1. `setup.sh` reads the *previous* `kit_commit` from the lock **before** the lock is rewritten, exports it (e.g. `HARNESS_PREV_COMMIT`), and `write_harness_lock` writes the new one from the temp clone.
2. `harness_backup_path` builds the base name `"$_bk_dst.bak-${HARNESS_PREV_COMMIT:-$(date +%Y%m%d)}"`, then numbers on collision as today. Keep it one function so Reinstall, first install and Update share it (its own comment says it is public so T114 does not re-implement it).
3. In Update's `o` branch, call `harness_backup_path "$_src" "$_dst" || <skip this file, keep the original, count it unresolved>` before `install_file`. On backup failure the original must stay — never overwrite after a failed backup.
4. Make the lock readers ignore `kit_commit` — scope them to the `"files"` block or exclude the key; choose whichever is the smaller, clearer diff.

---

## Edge Case Checklist

- [ ] **1. Hex collision**: `extract_lock_pairs` matches `"<key>": "<hex>"` anywhere; a short SHA *is* hex. Unfixed, Update would see `kit_commit` as an installed file and may try to remove `./kit_commit`. AC6/SC5/M2 exist for this.
- [ ] 2. The fixture kit in tests must be a real git repo with ≥2 commits so A ≠ B is observable.
- [ ] 3. Previous commit must be read *before* `write_harness_lock` runs, or every backup gets the *new* ID.
- [ ] 4. `rev-parse` failure (not expected after a clone, but) → empty → date fallback, never an empty suffix like `.bak-`.
- [ ] 5. Update with no terminal: `eof` path makes no backup (AC9).
- [ ] 6. A directory backup (`templates/`) gets the same suffix (`templates.bak-<id>/`).
- [ ] 7. `set -e` contexts: keep the explicit `mv` failure check.
- [ ] 8. POSIX `sh` only (setup.sh is `#!/bin/sh`); shellcheck clean.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `lib/harness-fetch.sh` | version suffix in `harness_backup_path`; update its header comment |
| `lib/harness-update.sh` | backup before overwrite in the `o` branch; lock readers ignore `kit_commit` |
| `setup.sh` | read previous commit; write `kit_commit`; real names in plan lines |
| `tests/test_install_backups.sh`, `tests/test_update.sh` | SC1–SC6 |
| `site/index.html` | Install (~line 250) + Update flow prose: backup names, and "overwrite" now backs up |
| `RUNBOOK.md` | line 222 row |
| `docs/adr/0002-one-confirmed-menu-driven-installer.md` | one "Amended by T137" line |
| `tasks/TASK_REVIEW_T137.md` | new, from `templates/TASK_REVIEW_template.md` |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/index.html` `#what-you-get` section | T138 adds the pipeline diagram there in parallel — edit only `#install` and `#update-flow` |
| `PROJECT_KANBAN.md` | Supervisor-only |
| `memory/` | Supervisor-only writes |
| `.claude/hooks/` | not part of this task |

---

## Test Plan

Extend the two shell suites with SC1–SC6 against the offline fixture kit; run the Verification Command; run M1–M3 and paste RED output into `tasks/TASK_REVIEW_T137.md`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Lint passes (shellcheck)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T137.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — user-run
- [ ] Supervisor notified: task ready for Stage 4 review
