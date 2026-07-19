# 0001. Direct-to-repo install/update, no persistent central clone

**Status**: Accepted
**Date**: 2026-07-17
**Deciders**: User (thunderkds), Supervisor
**Related**: BRAINSTORMING_LOG_direct-install.md · supersedes the symlink-from-`~/.supervisor` model documented in `PROJECT_SPEC.md` glossary ("Central clone", "General resources")

---

## Context

Since inception, `setup.sh` has cloned this repo once to a central location (`~/.supervisor`, overridable via `SUPERVISOR_PATH`), then every target project symlinks `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `templates/`, and `CLAUDE.md` back to files living in that central clone. Updating the harness meant `cd ~/.supervisor && git pull` — every symlinking project picked up the change automatically since files were never actually copied into the project.

The user wants each working repo to be fully self-contained: no dependency on any central clone, anywhere. This is hard to reverse for every project already installed under the symlink model (they'd need an explicit migration step to adopt the new model — deferred as a follow-up, not part of this decision). It is surprising relative to the documented architecture (`PROJECT_SPEC.md` glossary's "Central clone" and "General resources — shared, symlinked" entries describe exactly the model being replaced). And it is the result of a genuine trade-off: three real fetch mechanisms were considered (temp git clone, partial/sparse clone, tarball download), each with different dependency and correctness profiles, and the update-conflict handling required designing new state (a hash-tracking lockfile) that didn't exist before.

---

## Decision

We will replace the central-clone-and-symlink model with a **temp-clone-copy-discard** install:

- **`setup.sh`** (first-time install): `git clone --depth 1` the harness repo into a `mktemp -d` (with an `EXIT` trap for cleanup), copy `MANIFEST`-listed paths and `CLAUDE.md`/`CLAUDE_LEGACY.md` as real file copies into the working repo, then discard the temp clone. Always full-overwrite — no conflict handling, since this is a fresh install and the user accepts the harness as given. Requires the fetch+copy logic factored into a shared lib file (`lib/harness-fetch.sh`), since `update.sh` needs the same mechanism.
- **`update.sh`** (new, separate script — not a `setup.sh --update` flag): sources the same shared fetch lib, re-fetches fresh into a temp clone, then for each `MANIFEST` path compares the working repo's current file hash against the recorded hash in `.claude/harness-lock.json` (a new git-tracked lockfile written at install/update time). If the hash still matches what was installed, overwrite silently (untouched — safe). If it differs, the user has customized the file — show a diff and prompt per-file (overwrite / skip / view diff again) rather than silently clobbering or silently going stale.
- **New prerequisite check**: both scripts must confirm the working directory is itself a git repository (`git -C . rev-parse --git-dir`) before writing anything — under the new model, the working repo's own git history is the only undo mechanism (no symlink to safely leave untouched), so this check is load-bearing in a way it wasn't before.
- **Packs are out of scope**: `packs/` and `install_pack()` keep their current symlink-from-central-clone behavior until a follow-up revisits them under the same model.
- **Migration for existing symlink-based installs is out of scope**: `update.sh` detects a symlink at a `MANIFEST` path and refuses with an explicit message rather than silently converting it. Migration itself is a separate, deferred Stage-2 task.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| Temp clone, copy out, discard | Reuses the exact `git clone` mechanism already proven (fork override via `GITHUB_USERNAME`, auth via existing git credentials, error handling); smallest diff | Fetches the full default-branch tree, not just needed paths — immaterial at this repo's size | **Selected** |
| Partial/sparse clone (`--filter=blob:none` + `sparse-checkout`) | More bandwidth-efficient fetch in principle | Inconsistent behavior across git versions (older git silently ignores `--filter`); adds failure modes for a performance win nobody asked for | Correctness risk for an unneeded optimization — violates Simplicity First |
| Tarball download (`curl`/`tar`, no git clone) | Drops the `git` dependency for the fetch step; slightly faster one-shot fetch | New dependency (`curl`/`tar`); GitHub-specific URL shape breaks the `GITHUB_USERNAME` fork-override feature; loses git's built-in auth for private forks | Regresses an existing supported feature (private fork installs) for no material gain |

---

## Consequences

### Positive
- Each project becomes independently installable/updatable with zero dependency on `~/.supervisor` or any shared local state.
- `update.sh` can now distinguish "safe to overwrite" from "user customized this" via the hash-lock, closing a gap the old symlink model never had to solve (symlinks always reflected upstream live, so there was never a divergence to detect).
- The git-readiness prerequisite check catches a real failure mode early (writing harness files into a non-git directory would leave the user with no undo path at all).

### Negative (accepted trade-offs)
- Loses "edit once in the central clone, every project picks it up instantly" — each project now has its own real copy that must be explicitly updated.
- `update.sh`'s per-file interactive conflict prompt adds real interaction cost when a user has customized multiple harness files — no longer a silent `git pull`.
- Existing symlink-based installs get no automatic upgrade path in this decision; they must wait for the deferred migration follow-up.

### Follow-up
- [ ] Stage 2 `/plan`: TASK_GUIDEs for `lib/harness-fetch.sh`, `setup.sh` rewrite, new `update.sh`, `.claude/harness-lock.json` shape — starts at **C2/Medium Risk minimum** per CLAUDE.md Hard-Stop Gate 2 (touches core install "restructure").
- [ ] Follow-up task: migration path for existing symlink-based installs (`update.sh --migrate` or similar), once the base model ships and is proven.
- [ ] Follow-up task (optional): revisit whether packs (`packs/`, `install_pack()`) should move to the same model.
- [ ] `README.md` (if it documents the symlink model) needs its install/update instructions updated to match.
