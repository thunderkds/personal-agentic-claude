# BRAINSTORMING_LOG.md
**Generated**: 2026-09-12
**Task / Context**: Easy Kit install/update scripts (`setup.sh`, `update.sh`, `lib/harness-fetch.sh`) — make them work as documented, and simple to use (few options)
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Deep (install contract touches every user repo; two findings are silent data loss; 43 files reference `setup.sh`)

> Supersedes the 2026-08-17 hook-wiring-drift log (T074, shipped and closed). Recoverable from git history.

---

## The Problem Space

### Evidence — measured, not inferred

Two probe runs on 2026-09-12 against committed `main` (`8115bc9`), in scratch git repos with
`SUPERVISOR_REPO=file://<kit>` and `HOME` isolated. Interactive prompts driven through a pty (`script -qec`).

**Works**: fresh non-interactive install (30 skills, 5 agents, hooks, settings.json, 110-hash lock,
relative `.claude/{skills,agents}` links); piped bootstrap incl. `sh -c "$(…)" -- --harness codex`;
unmodified skill updates; customized skill kept on update (exits 2 without a TTY); Codex projection +
presence-based re-projection; brownfield `CLAUDE_LEGACY.md` survives update; second update is a
no-op (0 dirty files); all 8 settings.json hook paths resolve and every hook exits ≤1 on `{}`;
worktree resolves the canon links; bad flag / non-git dir fail before any write.

**Broken**:

| # | Defect | Measured |
|---|---|---|
| 1 | Packs install nothing | `install_pack` reads `$SUPERVISOR_PATH/packs` (`~/.supervisor`), never created since ADR-0001 (which deferred packs, `docs/adr/0001-…md:25,55`). `--pack=mobile` and interactive `1, 5` both warn "not found in central clone — skipping", then log "Packs requested: mobile api". |
| 2 | Update never delivers `CLAUDE.md` / `settings.json` | Upstream changed skill + CLAUDE.md + settings.json → only the skill arrived. Neither file is in `MANIFEST`; `build_fresh_file_list` walks MANIFEST only. New gates and new hooks never reach existing projects. |
| 3 | No runnable update command | `update.sh` is not installed into the project and has no curl bootstrap (`update.sh:59-62` exits). Site offers `sh update.sh` (fails) and `sh /path/to/personal-agentic-claude/update.sh` (needs a clone). |
| 4 | Re-running setup silently clobbers edits | Customized `skills/diagnose/SKILL.md` overwritten, exit 0, no prompt. |
| 5 | Install clobbers a project's own `CLAUDE.md` / `AGENTS.md` | Pre-existing `# my project rules` replaced without warning; uncommitted content is unrecoverable. |
| 6 | Existing `settings.json` → zero hooks, silently | `install_settings` returns early with no message; nothing merges hook wiring. |
| 7 | Skill deleted upstream survives update | Warned, kept; Claude still loads it. |
| 8 | Kit-internal tests ship into user repos | 36 files under `.claude/hooks/tests/`; install = 119 files, 1.4 MB. |
| 9 | CI does not run the install/update suites | `ci.yml` runs `smoke-install.sh` + `test_harness_projection.sh` only; `tests/test_setup.sh` (253 l), `test_update.sh` (408 l), `test_install_update_smoke.sh` (236 l) never run in CI. |

**Option sprawl** (user asked for fewer): `--copy` (no-op for base), `--pack=` (broken; `--pack x` rejected),
interactive pack menu, `--harness`/`--harness=`, `SUPERVISOR_REPO` + `GITHUB_USERNAME` (two knobs, one
purpose), `SUPERVISOR_PATH` (exists only for broken packs), test seams visible to users
(`HARNESS_SKILL_BODY_CAP`, `SETUP_SH_DIR`, `SETUP_SH_DEFINE_ONLY`), and the `sh -c "$(curl …)" --` form.

### Non-negotiables

- Git history remains the undo path; never write before the git-repo check.
- A user's local edits are never destroyed without an explicit choice.
- ADR-0001's temp-clone-copy-discard model stays (no central clone returns).
- Codex skill-body cap stays skip-not-truncate.

---

## Questions for the User

Resolved in this session (2026-09-12):

1. **Do packs stay an installer feature?** → **No install-time pack choice.** Packs are identified from the
   business domain: the Supervisor analyzes and *suggests* packs, and the client decides later.
2. **Where do pack files come from after approval?** → **Ship a dormant catalog.** All of `packs/`
   (5 packs, 20 files, ~200 KB) is copied inactive; activation copies the chosen pack into the canon.
3. **Script shape?** → **One command**, auto-detecting install vs update, **but it confirms and lets the
   user choose another action** rather than acting silently.

4. **No parameters at all (user, 2026-09-12).** "One single command; the options should be chosen by the
   user from a list, not params the user must remember and push in at initialize." Every choice is a
   numbered menu. The user delegated the remaining calls: "Following it and choose the good one."

Decided by the Supervisor under that delegation — each still open to challenge in `grill-with-docs`:

5. **No `/dev/tty` (CI, Docker, `ssh` without `-t`)** → proceed with the *safe* defaults and print every
   one: install = Claude Code + greenfield; update = keep all local edits, unresolved conflicts exit 2.
   Never reinstall without a TTY. Tests drive the menus through a pty (`script -qec`, proven at T108).
6. **Existing user `CLAUDE.md` / `AGENTS.md`** → saved to `<name>.bak` before the kit copy, shown in the
   plan screen before confirmation. No extra question; never silent, never lost.
7. **`settings.json`** → merge kit hook entries into the existing file with `python3` (already a hard
   prerequisite — every wired hook is `python3 …`). User permissions untouched. If `python3` is absent,
   fail the hook step loudly — hooks could not run anyway.
8. **Pack activation** → a Supervisor skill (`select-packs`) at Phase 0/Stage 1: reads each dormant
   `packs/*/PACK.md` "When to use", recommends, asks the client via a pick list, copies the approved
   pack into `agents/`/`skills/`. Installing kit content is configuration, not project implementation —
   recorded in a DDR so Gate 1 is interpreted explicitly, not by convenience.
9. **Upstream-deleted skill** → removed if its lock hash still matches (never edited); kept + warned if edited.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Two Scripts, Fixed | Keep setup/update; fix defects 1–9 in place | Low | ~+150 / −120 | Low | |
| B | One Confirmed Entrypoint | `setup.sh` becomes the only command: detect → show plan → confirm/choose; `update.sh` a thin alias; dormant pack catalog | Medium | ~+220 / −260 | Medium | ✅ Yes |
| C | Silent Auto Entrypoint | Like B, no confirmation menu, flags only | Medium | ~+160 / −260 | Medium | |

### Option A — Two Scripts, Fixed
**Approach**: Setup refuses when a lock exists ("use update"); update gains a curl bootstrap and covers
`CLAUDE.md` + `settings.json`; packs copied from the temp clone; wire the 3 suites into CI.
**Pros**: Smallest diff; zero doc/test renames; each fix independently shippable.
**Cons**: Users still learn two commands and two URLs; keeps the pack menu the user just rejected;
duplicated flag parsing, hashing and repo resolution survive in both files (`compute_file_hash`,
`resolve_repo_url`, `check_*` are copy-pasted today).
**Why it might fail**: Contradicts two locked answers (no install-time packs; one command). Fixes the
symptoms while the surface the user called too complex stays the same size.

### Option B — One Confirmed Entrypoint
**Approach**: Keep the name `setup.sh` (43 referencing files, the curl URL already public) as the single
entrypoint. It detects state and prints a plan, then asks via `/dev/tty`:
`No install found → [I]nstall / [c]ancel`; `Install found → [U]pdate (keeps your edits) / [r]einstall
(backs up edits) / [c]ancel`. `update.sh` becomes a ≤10-line alias that runs the update action. Shared
functions move into `lib/harness-fetch.sh`. Remove `--copy`, `--pack=`, the pack menu,
`SUPERVISOR_PATH`, `install_abs`, `install_pack`. Ship `packs/` as a dormant catalog in `MANIFEST`;
activation happens later in the pipeline. Update covers `CLAUDE.md` + `settings.json` through the
same hash-lock conflict path. Stop shipping `.claude/hooks/tests/`. CI runs all install/update suites.
**Revised 2026-09-12 per user: zero flags.** Every choice is a numbered menu, at most three screens:
1. **Action** — `No install found: 1) Install  2) Cancel` / `Install found: 1) Update (keeps your edits)  2) Reinstall (backs up edits)  3) Cancel`
2. **CLIs** (install/reinstall only) — multi-pick `1) Claude Code  2) Codex`, pre-selected from `command -v claude/codex`; update re-derives from what is present
3. **Project type** (install/reinstall only) — `1) New project (CLAUDE.md)  2) Existing/legacy project (CLAUDE_LEGACY.md)`

Then a plan screen (what will be written, what is backed up) and `Proceed? [Y/n]`. `--harness`,
`--copy`, `--pack=` and the `sh -c "$(curl …)" --` form all go; `SUPERVISOR_REPO` stays only as an
undocumented developer/test seam.
**Pros**: One line for users forever; matches all three locked answers; re-running can no longer wipe
edits by accident; net code *shrinks*; old docs/URLs keep working through the name + alias.
**Cons**: Largest behavior change; `curl | sh` stdin is the script, so the prompt must read `/dev/tty`
and handle its absence; settings.json merge in POSIX sh is genuinely awkward; existing tests that
parse setup's `case` block (`tests/test_pack_docs_flags.py`) and pack-choice parsing
(`tests/test_pack_choice_parsing.sh`, T108) must be retired or rewritten — T108's fix gets deleted.
**Why it might fail**: The confirm menu becomes new option sprawl if it grows past 3 choices;
`/dev/tty` probing differs across macOS/Linux/containers; bundling 9 defects into one task produces a
C3 that fails review — must be split (see Next Actions).

### Option C — Silent Auto Entrypoint
**Approach**: B's detection and cleanup, but no menu: lock absent → install, lock present → update;
`--reinstall` flag to force.
**Pros**: Simplest code; no TTY handling; identical behavior in CI and terminals.
**Cons**: The user explicitly asked for confirmation and the ability to choose another action.
**Why it might fail**: A wrong detection (lock deleted, partial install, worktree) acts with no chance
to stop it — the exact silent-surprise class behind defects 4 and 5.

---

## 50% Rule Check

For Option B, the same goal with half the code:
- **No new entrypoint file** — reuse `setup.sh`'s name and bootstrap; `update.sh` shrinks from 509 lines to an alias.
- **Pack activation needs no script** — `.claude/{skills,agents}` already link to the plain-root canon,
  so activation is copying `packs/<p>/agents/*` and `packs/<p>/skills/*` into `agents/`/`skills/`;
  the lock + update path already handles files it did not ship (carry-over).
- **settings.json**: don't write a JSON merger in sh — detect missing hook entries and print the exact
  block to add, loudly, exit non-zero only on the explicit update action. (Pending Q6.)
- **Delete, don't rewrite**: `install_abs`, `install_pack`, `prompt_packs`, `resolve_pack_choices`,
  `--copy`, `SUPERVISOR_PATH` — roughly 140 lines out of `setup.sh` before anything is added.

---

## Recommended Path

**Option B — One Confirmed Entrypoint**, delivered as a sequence of small tasks, not one.

It is the only option consistent with all three user decisions, and it reduces total script size
while fixing every measured defect. Keeping the `setup.sh` name makes the change invisible to anyone
holding the published curl line, which is the cheapest backward-compatibility available.

---

## Surgical Scope

Files that **should** be touched:
- `setup.sh` — becomes the single confirmed entrypoint; pack installer code removed
- `update.sh` — reduced to an alias onto the update action
- `lib/harness-fetch.sh` — receives the functions currently duplicated across both scripts
- `MANIFEST` — add `packs`; exclude `.claude/hooks/tests`
- `.github/workflows/ci.yml` — run `tests/test_setup.sh`, `test_update.sh`, `test_install_update_smoke.sh`
- `tests/test_setup.sh`, `tests/test_update.sh`, `tests/test_install_update_smoke.sh`, `scripts/smoke-install.sh` — new behaviors
- `tests/test_pack_docs_flags.py`, `tests/test_pack_choice_parsing.sh` — retire or rewrite with the flags they guard
- `README.md`, `site/index.html`, `RUNBOOK.md`, `AGENTS.md`, `PROJECT_SPEC.md` — one install/update line
- `docs/claude-md/folder-structure.md:35-41`, `CLAUDE.md:66-67`, `CLAUDE_LEGACY.md` (sync policy), `packs/*/PACK.md`, `templates/PACK_template.md` — pack activation wording
- A new DDR amending ADR-0001's pack deferral

Files that **must not** be touched:
- `.claude/hooks/*.py` — hook behavior is out of scope; only their shipping manifest changes
- `skills/*` bodies other than a pack-recommendation pointer — no skill rewrites ride along
- `docs/adr/0001-direct-repo-install-no-central-clone.md` — amended by a DDR, never edited in place
- `memory/` — Supervisor-only writes, Stage 5

---

## Edge Case Checklist for TASK_GUIDE

- [ ] `curl | sh`: stdin is the script — the confirm prompt reads `/dev/tty`, never fd 0
- [ ] No `/dev/tty` (CI, Docker, `ssh` without `-t`): defined default, printed, and testable (Q4)
- [ ] `sh -c "$(curl …)" --` still passes flags through the bootstrap re-invocation
- [ ] Lock present but canon deleted / partial install → detection doesn't claim "update" over a broken tree
- [ ] Old `~/.supervisor` symlink-model install still refused with a migration message
- [ ] Pre-existing user `CLAUDE.md` / `AGENTS.md` never destroyed without a backup or explicit choice (Q5)
- [ ] Existing `settings.json` without kit hooks → loud, specific message, never silent (Q6)
- [ ] Activated pack files are not reported as "upstream no longer ships" orphans, nor overwritten by update
- [ ] Pack agent/skill name colliding with a core name → refused, not overwritten
- [ ] Upstream-deleted skill: unmodified → removed; modified → kept + warned (Q8)
- [ ] Brownfield choice (`CLAUDE_LEGACY.md`) preserved when update now covers `CLAUDE.md`
- [ ] `.claude/hooks/tests` removal from install doesn't break any hook import at runtime
- [ ] Codex-only project: update doesn't create `.claude/` links; Codex cap still skip-not-truncate
- [ ] Exit codes asserted directly in tests, never through a pipe (`| tail` masks them — seen in this probe)
- [ ] `grep` in this environment wraps ugrep — tests use `command grep` (learnings: T107)

---

## Next Actions

For Stage 2 — split, in dependency order:

1. **CI safety net first** (C1/Low): wire the 3 existing install/update suites into `ci.yml`; fix whatever is already red. Every later task then lands against a real gate.
2. **Update coverage + no silent loss** (C2/Medium): `CLAUDE.md` + `settings.json` through the hash-lock path; never clobber pre-existing user `CLAUDE.md`/`AGENTS.md`; upstream-deleted-skill rule; stop shipping `.claude/hooks/tests`.
3. **One confirmed entrypoint** (C2/Medium): detection + `/dev/tty` confirm menu in `setup.sh`; `update.sh` alias + curl bootstrap; remove `--copy`, `SUPERVISOR_PATH`, test seams from user-facing docs; single install line in README/site.
4. **Dormant pack catalog + domain-driven activation** (C2/Medium): remove pack menu/`--pack=`/`install_pack`; ship `packs/`; Supervisor recommends from `PACK.md` "When to use" at Phase 0/Stage 1; activation path + DDR amending ADR-0001.
5. Run `grill-with-docs` on this log to close Q4–Q8 before any TASK_GUIDE is written.

---

## User Selection

> **Approved direction**: Option B — One Confirmed Entrypoint, revised to **zero flags, menu-driven**.
> Approved by user on 2026-09-12 ("one single command … choose from the list … choose the good one").
> Q5–Q9 decided by the Supervisor under delegation; to be stress-tested in `grill-with-docs`.
>
> **grill-with-docs outcome (2026-09-12)**, each a user answer:
> - **Branch**: one integration branch off `main`; `main` receives the set in one reviewed merge at the end.
> - **Record tier**: new **ADR-0002** (`docs/adr/0002-one-confirmed-menu-driven-installer.md`, Proposed),
>   partially superseding ADR-0001 and amending DDR-0007.
> - **Terminology**: users see "CLI" and "Easy Kit"; "harness" stays internal; identifiers not renamed.
> - **Pack activation**: `select-packs` copies verbatim kit-shipped pack files after client approval —
>   an explicit, bounded Gate 1 interpretation written into ADR-0002.
