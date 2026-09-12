# TASK_GUIDE — T112: First install never destroys a project's own files — they are backed up and named
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

Probe, 2026-09-12, `main` `8115bc9`: installing into a repo that already had its own files:

```
CLAUDE.md now: # Claude Project Supervisor Guidelines     (was: "# my project rules")
AGENTS.md now: # AGENTS.md                                (was: "# my agents")
```

No warning, exit 0. If those files were uncommitted, they are gone for good. ADR-0001 made install
"always full-overwrite" on the assumption the target is empty; ADR-0002 replaces that.

**Same defect, wider — verified by reading, NOT yet by running (the agent's BEFORE capture must prove
it):** `harness_copy_manifest` (`lib/harness-fetch.sh:152`) does `[ -e "$_dst" ] && rm -rf "$_dst"` for
every MANIFEST path, which includes directories (`agents`, `skills`, `templates`, `docs/claude-md`,
`.cursor/rules`, `.claude/hooks`). A project with its own `templates/` or `docs/claude-md/` folder loses
the whole directory at install.

**Restated intent**:
> Installing Easy Kit into a project never deletes anything the project already had. A pre-existing path
> the kit would replace is moved to a backup, the backup is named in the output, and identical content is
> left alone without a backup.

**Out of scope**:
- The update path (hash-lock rules already protect edited files there).
- Re-running install over an existing install (lock present) — T114's "Reinstall (backs up your edits)" reuses this task's backup function; do not build that menu here.
- `.claude/settings.json` — T111 merges it.
- Restoring backups automatically.

**Requirement Refs**: none in `PRD.md`; authority ADR-0002 ("A pre-existing, non-kit `CLAUDE.md` / `AGENTS.md` is saved as `<name>.bak`").

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, probe + ADR-0002, user-approved)
- [x] Domain terms align with glossary ("Manifest", "General resources")
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T109 — installer suites wired into CI

**Entry point**: `harness_copy_manifest` and `install_claude` (called from `setup.sh` `main`, install with no lock)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Pre-existing `CLAUDE.md` with different content → moved to `CLAUDE.md.bak` byte-identical; kit `CLAUDE.md` installed; one output line names the backup | "backed up and named" |
| 2 | Same for `AGENTS.md` (a MANIFEST file path) | "never destroys a project's own files" |
| 3 | Pre-existing **directory** at a MANIFEST path (e.g. `templates/` with `mine.md`) → whole directory moved to `templates.bak/`, `mine.md` intact inside it; kit `templates/` installed | the `rm -rf` directory case |
| 4 | Pre-existing path whose content is identical to the kit's → no backup created, no backup line printed | "identical content is left alone" |
| 5 | `CLAUDE.md.bak` already exists → the new backup goes to `CLAUDE.md.bak.1` (then `.bak.2`, …); an existing backup is never overwritten | never lose a previous backup either |
| 6 | Non-git directory → still rejected before any write, including before any backup | ADR-0001 prerequisite unchanged |
| 7 | Empty git repo (no pre-existing paths) → output and resulting tree identical to today apart from nothing else; zero `.bak` paths | regression |
| 8 | Backups are not recorded in `.claude/harness-lock.json` | backups are the user's, not kit files |
| 9 | Mutation control M1: restore the `rm -rf` without backup → AC3 test fails | observed failing |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | repo with `CLAUDE.md` = `# my project rules` | `CLAUDE.md.bak` contains exactly that; `CLAUDE.md` = kit; stdout names `CLAUDE.md.bak` | automated test |
| 2 | repo with `AGENTS.md` = `# my agents` | as SC1 for `AGENTS.md` | automated test |
| 3 | repo with `templates/mine.md` | `templates.bak/mine.md` exists; `templates/TASK_GUIDE_template.md` exists | automated test |
| 4 | repo where `AGENTS.md` is already byte-identical to the kit's | no `AGENTS.md.bak` | automated test |
| 5 | repo with `CLAUDE.md` and `CLAUDE.md.bak` both present | `CLAUDE.md.bak` unchanged; `CLAUDE.md.bak.1` holds the prior `CLAUDE.md` | automated test |
| 6 | non-git dir with `CLAUDE.md` | exit 1; `CLAUDE.md` unchanged; no `.bak` | automated test |
| 7 | lock contents | no key ending in `.bak` or containing `.bak/` | automated test |

### Verification Command (exact, runnable)

```bash
bash tests/test_install_backups.sh
bash tests/test_setup.sh
bash tests/test_install_update_smoke.sh
bash tests/test_harness_projection.sh
shellcheck -x setup.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T112.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T112.md`.

---

## Approach

**Pattern reference**: `harness_install_canon_symlinks` in `lib/harness-fetch.sh:324` — it already moves a
pre-T096 real directory aside to `<link>.bak` and logs it. Imitate the move-and-log shape, but where it
**fails** when a backup already exists, this task picks the next free `.bak.N` (AC5): an installer that
refuses because a backup exists would block the user for no data-safety reason.

**Vital slice**: one backup helper (`harness_backup_path` or similar) called before each destructive copy on
the install path, with an identical-content short-circuit.
**Cut list**:
- Interactive "keep mine / take kit's" choice per file — ADR-0002 decided backup-and-proceed, shown on the plan screen (T114).
- Backing up on update — hash-lock already protects edits there.
- A summary file listing backups — the output lines are enough.

Identical-content check: files by content hash (reuse the existing hashing), directories by a recursive
comparison (`diff -rq` is POSIX-available; confirm). Export the helper from the lib so T114 can call it for
Reinstall without re-implementing it — note it in the function header.

---

## Edge Case Checklist

- [ ] `.claude/hooks` pre-existing as the user's own hooks directory → backed up like any other MANIFEST dir; the user's `settings.json` still points at their hooks — T111 keeps user entries, so warn in the output that user hooks now live in `.claude/hooks.bak`
- [ ] Path is a symlink → move the link itself, never follow and move the target
- [ ] A regular file where the kit has a directory (or vice versa) → backed up, kit type installed
- [ ] Filenames with spaces → quoted throughout
- [ ] Codex projection destinations (`.codex/skills`) are generated + gitignored — they keep today's replace behaviour, not backup (DDR-0007: projections are regenerated, never hand-edited)

---

## Documentation to Update

> Batch rule (user, 2026-09-12: "make sure the document also be updated"): these rows are **acceptance
> criteria**. Done requires each doc updated and its new text quoted in `tasks/TASK_REVIEW_T112.md`.
> Historical records are never rewritten.

| # | Doc | What is wrong today → what it must say |
|---|-----|----------------------------------------|
| D1 | `PROJECT_SPEC.md` Critical Constraints (`:74`) — "`setup.sh` must be idempotent — re-running must not break existing setup or overwrite project files" | Stated as met; it is not (probe). Rewrite to the rule this task enforces: first install moves any pre-existing path it would replace to `<name>.bak` (or `.bak.N`) and names it |
| D2 | `PROJECT_SPEC.md` Known Risk Areas row "Symlink creation … silent overwrite would destroy project data" (`:82`) | Describes the pre-ADR-0001 symlink model → reword to the copy model; mitigation = backup helper, with a pointer to ADR-0002 |
| D3 | `site/index.html` `#install` | Add one sentence: installing into an existing project backs up files it would replace (`CLAUDE.md.bak`, `templates.bak/`, …) and lists them |
| D4 | `RUNBOOK.md` — Common Failure Modes table | New row: symptom "`*.bak` files/folders appear after install", cause the project already had those paths, remediation: compare and merge by hand, then delete the backup |

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `lib/harness-fetch.sh` | Backup helper; `harness_copy_manifest` backs up instead of `rm -rf` on the install path |
| `setup.sh` | `install_claude` uses the helper |
| `tests/test_install_backups.sh` | New — SC1–SC7 + M1 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `update.sh` | Update path unchanged; T110/T113 edit it |
| `harness_project_manifest` destination replace | Projections are regenerated by design (DDR-0007) |
| `install_settings` | T111 |
| `harness_install_canon_symlinks` failure-on-existing-backup | Deliberate for the `.claude/{skills,agents}` link migration; not this task's call |

---

## Test Plan

New `tests/test_install_backups.sh` following `tests/test_setup.sh` conventions; first capture BEFORE on
`main` for SC3 (the unproven directory case) and paste it into the review file before any implementation
commit. Then SC1–SC7 + M1. Existing installer suites green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] `shellcheck -x setup.sh` clean (and `lib/harness-fetch.sh` via `-x`)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T112.md` (Hard-Stop Gate 5)
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
