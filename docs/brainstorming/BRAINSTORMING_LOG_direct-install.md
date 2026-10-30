# BRAINSTORMING_LOG.md
**Generated**: 2026-07-17
**Task / Context**: Replace central `~/.supervisor` clone + symlink model with direct install/update into the working repo
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Deep (architectural choice, major downstream impact on every installed project + the pack system)

---

## The Problem Space

Today `setup.sh` clones the harness to `~/.supervisor` once, then every target project symlinks `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `templates/`, and `CLAUDE.md` back to files living in that central clone (`clone_or_verify`, `install_path`, `install_claude` — setup.sh:46-69, 193-273). Updating the harness today means `cd ~/.supervisor && git pull`; every symlinking project picks the change up automatically since the files were never actually copied.

The user wants each working repo to become the unit of installation: no dependency on a central clone anywhere. Concretely this means:
- `setup.sh` fetches the harness fresh (from GitHub, no persistent local clone) and writes real file copies directly into the working repo.
- `update` becomes a distinct, later operation — must handle the case where installed files have since been edited locally.
- A **git-readiness check on the working repo itself** is a new prerequisite the user flagged explicitly — today `check_git` (setup.sh:38-43) only checks that the `git` binary exists, not that the current directory is itself a git repository. Since files will be direct, uncommitted copies (not symlinks pointing elsewhere), the working repo's own git history becomes the only safety net for "what did setup/update just change" — so confirming the target is a real git repo (and ideally has a clean-ish working tree) before writing matters more than it did under the symlink model.

Confirmed constraints from Q&A:
- **Setup** = first-time install. Always full overwrite, no conflict logic — user accepts the harness as given.
- **Update** = later re-run. Must distinguish "file untouched since install" (safe to overwrite) from "file the user customized" (must not silently clobber) — requires tracking what was installed, not just diffing against upstream.
- **Packs are out of scope** for this change — `install_pack()` keeps its current form; only the base MANIFEST install + `CLAUDE.md` + the new update flow are being redesigned.

---

## Questions for the User

None outstanding on architecture direction. Remaining open items are implementation-level (see Next Actions) — deferred to `grill-with-docs` / Stage 2, not blocking here.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Temp Clone, Copy Out, Discard | `git clone --depth 1` to a `mktemp -d`, copy MANIFEST paths + CLAUDE.md into the working repo, `rm -rf` the temp dir | Low | ~40 lines changed | Low | ✅ Yes |
| B | Partial/Sparse Clone | `git clone --filter=blob:none --sparse`, checkout only MANIFEST paths, copy out, discard | Medium | ~60 lines changed | Medium | |
| C | Tarball Download (no git clone) | `curl`/`wget` the GitHub codeload tarball URL, `tar -x` into temp, copy out, discard | Medium | ~55 lines changed | Medium | |

### Option A — Temp Clone, Copy Out, Discard
**Approach**: Same `git clone` call already in use today (`clone_or_verify`), just retargeted at a `mktemp -d` instead of `$SUPERVISOR_PATH`, with a cleanup trap (`trap 'rm -rf "$tmp"' EXIT`) so the temp clone never persists. `install_path`/`install_claude` change from `ln -s "$src" "$dst"` to `cp -r "$src" "$dst"` unconditionally (setup = always overwrite).
**Pros**: Smallest possible diff — reuses the exact clone mechanism already proven to work (auth, `GITHUB_USERNAME` fork override, error handling all unchanged); no new dependency (curl/tar) beyond git, which `check_git` already requires.
**Cons**: `git clone` (even `--depth 1`) fetches the full tree of the default branch — slightly more bandwidth than a true sparse fetch, though this repo is small enough (a few hundred KB) that it's immaterial.
**Why it might fail**: If cleanup (`trap`) isn't wired correctly, temp clones could accumulate in `/tmp` across repeated runs — mitigated by using `mktemp -d` (auto-unique) and an EXIT trap that fires even on early `exit 1`.

### Option B — Partial/Sparse Clone
**Approach**: `git clone --filter=blob:none --no-checkout`, then `git sparse-checkout set .claude/agents .claude/skills .claude/hooks templates`, then checkout and copy.
**Pros**: Fetches only the blobs actually needed, in principle more bandwidth-efficient for a large upstream repo.
**Cons**: Sparse-checkout + partial-clone flags have historically inconsistent behavior across git versions (older git silently ignores `--filter`); adds failure modes (partial clone fallback logic) for a bandwidth saving that's irrelevant at this repo's size.
**Why it might fail**: A user on an old git version gets a full clone anyway (silent flag ignore) while the script's error handling assumes sparse succeeded — a correctness risk for a performance win nobody asked for, violating Simplicity First.

### Option C — Tarball Download (no git clone)
**Approach**: `curl -L https://github.com/<user>/personal-agentic-claude/archive/refs/heads/main.tar.gz | tar -xz -C "$tmp"`, then copy MANIFEST paths out.
**Pros**: Drops the `git` dependency for the *fetch* step specifically (though git is still required for the target repo's own git-readiness check); slightly faster for a one-shot fetch since there's no `.git` history downloaded at all.
**Cons**: Introduces a new dependency (`curl` or `wget`, plus `tar`) that isn't already required; GitHub-specific URL shape breaks portability if `GITHUB_USERNAME`-based forks live elsewhere, or if the repo ever moves off GitHub; loses `git`'s built-in integrity/auth handling (private-repo forks would need token wiring that `git clone` gets for free via SSH/HTTPS credential helpers already configured on the user's machine).
**Why it might fail**: A fork on a private GitHub repo currently clones fine via the user's existing git credentials; a raw tarball URL wouldn't authenticate the same way without extra token-passing code — a regression for the exact `GITHUB_USERNAME` fork-override feature `resolve_repo_url` already supports (setup.sh:11-15).

---

## 50% Rule Check

Option A is already the 50%-less version: it changes two call sites (`clone_or_verify`'s destination path, `install_path`/`install_claude`'s `ln -s` → `cp -r`) and adds one `trap` line — versus Option B's new sparse-checkout state machine or Option C's new auth-and-URL-shape logic for a fetch mechanism that has to reinvent what `git clone` already does correctly.

---

## Recommended Path

**Option A — Temp Clone, Copy Out, Discard**

Reuses the exact fetch mechanism already battle-tested in this script (fork override via `GITHUB_USERNAME`, error handling, auth via the user's existing git credentials) and only changes *where* the clone lands and *what* happens to it afterward. Options B and C both trade a real correctness/compatibility cost for a performance or dependency win that doesn't matter at this repo's size — over-engineering relative to Simplicity First.

**Update mechanism (applies regardless of fetch option chosen, only relevant post-install):**
Track what was installed via a small manifest of content hashes (e.g. `.claude/.harness-installed.json`: `{ "path": "sha256" }`), written at setup time. On `update`: re-fetch fresh (same temp-clone-and-discard as setup), then for each MANIFEST path — if the local file's current hash matches the recorded installed hash, it's untouched → overwrite silently; if it differs, the user edited it → show a diff and prompt per-file (overwrite / skip / view diff again), per the user's own refinement of the conflict-handling question. Re-record hashes for whatever the user chose to accept.

---

## Surgical Scope

Files that **should** be touched:
- `setup.sh` — `clone_or_verify` (retarget to temp dir + trap cleanup), `install_path`/`install_claude`/`install_settings` (drop symlink branch, always `cp`), new `update` command/flag, new hash-manifest read/write logic
- `MANIFEST` — no content change expected, but review whether `.claude/hooks` needs updating given hooks may now be per-project real files instead of symlinks (permission/executable-bit implications)
- `README.md` (if it documents the symlink model) — update install/update instructions
- New file: `.claude/.harness-installed.json` (or similar) — per-project hash manifest, git-tracked so `update` has state to compare against even from a fresh clone of the *target* project

Files that **must not** be touched:
- `packs/` and `install_pack()` — explicitly out of scope per user answer; packs keep the current model until a follow-up
- `.claude/settings.json` handling — already copy-only, no symlink to remove; behavior stays as-is
- Any individual project's already-installed `.claude/agents/*.md`/`.claude/skills/*/SKILL.md` content — this change is to the *installer*, not a retroactive migration of existing installs (that's a separate concern: how does an existing symlink-based project migrate to the new model?)

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Target directory is not a git repository — new prerequisite check (`git -C . rev-parse --git-dir`) must fail loudly before writing any files, since git is now the only undo mechanism
- [ ] Target repo has uncommitted changes at the *exact paths setup/update is about to overwrite* — warn (at minimum) before overwriting, since there's no symlink to safely "just point elsewhere" anymore
- [ ] Existing symlink-based installs (from before this change) running the new `update` — must detect a symlink at a MANIFEST path and handle it explicitly (replace with a real copy + hash, or refuse and instruct manual migration) rather than silently misbehaving
- [ ] Network failure mid-fetch (temp clone partially completes) — must not leave the working repo half-updated; fetch fully into temp first, only copy into the working repo once the temp fetch succeeds completely
- [ ] `.claude/hooks/*` files likely need an executable bit — `cp -r` preserves permissions from the source, confirm the temp-cloned files retain the same mode bits a direct `git clone` would have set
- [ ] Concurrent/interrupted temp-dir cleanup — `trap` must fire on both normal exit and signal interruption (Ctrl-C mid-install) so temp clones don't accumulate

---

## Next Actions

1. Run `grill-with-docs` to sharpen terminology (e.g. what exactly counts as "installed, untouched" for the hash manifest; canonical name for the new manifest file; whether `update` is a new `setup.sh` flag like `--update` or a separate script) and confirm whether this clears the DDR gate (my read: likely **yes** — hard to reverse for existing installs, surprising relative to the documented symlink model, and a genuine trade-off against Option B/C — 3-of-3 could even be ADR-eligible given it changes the deployment architecture every existing project depends on).
2. Since this touches `setup.sh`'s core install logic, this clears CLAUDE.md Hard-Stop Gate 2's Complexity floor (contains "restructure") — starts at **C2/Medium Risk minimum** at Stage 2 planning, regardless of how small the diff looks.
3. Decide migration story for existing symlink-based installs as a follow-up question (flagged, not blocking this brainstorm) — could be a one-time `update --migrate` path that detects symlinks and converts them.

---

## User Selection

> **Approved direction**: Option A — Temp Clone, Copy Out, Discard, with hash-manifest-tracked interactive-per-file conflict resolution for `update` only (setup always overwrites). Packs explicitly out of scope.
> Approved by user on 2026-07-17.
