# 0002. One confirmed, menu-driven installer; packs become a dormant catalog activated by domain

**Status**: Accepted (user, 2026-09-12)
**Date**: 2026-09-12
**Deciders**: User (thunderkds), Supervisor
**Related**: partially supersedes `ADR-0001` (script split + always-full-overwrite clauses) · amends `DDR-0007` (install-time CLI selection via `--harness`) · supersedes `memory/decisions.md` 2026-06-18 "Pack install via setup.sh: --pack=<name> flag + interactive prompt" · `BRAINSTORMING_LOG.md` (2026-09-12) · tasks: Stage 2 pending

---

## Context

A 2026-09-12 end-to-end probe of `setup.sh` / `update.sh` against committed `main` (`8115bc9`), run in
scratch git repos with the menus driven through a pty, measured nine defects. The four that shape this
decision:

1. **Packs install nothing.** `install_pack` still reads `~/.supervisor/packs`, the central clone
   ADR-0001 removed. ADR-0001 deferred packs "until a follow-up revisits them"; no follow-up happened.
   `--pack=mobile` and the interactive menu both log "skipping" and then "Packs requested: mobile api".
2. **No runnable update.** `update.sh` is not installed into projects and cannot bootstrap from
   `curl | sh`; the published docs give two update commands, one of which cannot work.
3. **Re-running `setup.sh` silently overwrites local edits**, because ADR-0001 made setup "always
   full-overwrite" on the assumption it only ever runs once. It also replaces a project's own
   `CLAUDE.md` / `AGENTS.md` without warning.
4. **Update never delivers `CLAUDE.md` or `settings.json`**, so new gates and hooks never reach
   existing projects.

Separately, the user judged the surface too complex: users must remember flags (`--harness`,
`--pack=`, the no-op `--copy`) and a non-obvious `sh -c "$(curl …)" --` form just to pass them. The
user's requirement: **one single command; every option chosen from a list, never a parameter the user
must remember.**

**Hard to reverse**: the command users run is published in the README, the site and every existing
project's history; habits and scripts form around it. **Surprising without context**: ADR-0001 states
the opposite in so many words — "`update.sh` (new, separate script — not a `setup.sh --update`
flag)". **Genuine trade-off**: three shapes were weighed (below), and a zero-flag installer gives up
scriptability that flags provide.

---

## Decision

We will make `setup.sh` the **single Easy Kit command**, with **no flags**, and move pack choice out of
installation entirely.

**One command, menus only.** `setup.sh` detects whether a lock (`.claude/harness-lock.json`) exists,
then offers numbered menus, at most three screens:

1. **Action** — no install found: `1) Install  2) Cancel`; install found: `1) Update (keeps your
   edits)  2) Reinstall (backs up your edits)  3) Cancel`.
2. **CLIs** (install / reinstall only) — multi-pick `1) Claude Code  2) Codex`, pre-selected from what
   is on `PATH`. Update re-derives the set from what is present, as DDR-0007's presence rule already does.
3. **Project type** (install / reinstall only) — `1) New project (CLAUDE.md)  2) Existing/legacy project (CLAUDE_LEGACY.md)`.

A plan screen then lists what will be written and what will be backed up, and asks `Proceed? [Y/n]`.

- Menus read **`/dev/tty`**, never stdin: under `curl | sh`, stdin is the script itself.
- **No `/dev/tty`** (CI, containers, `ssh` without `-t`): proceed with the safe defaults and print each
  one — install = Claude Code + new project; update = keep every local edit, unresolved conflicts exit 2.
  **Reinstall never runs without a TTY.**
- `update.sh` remains only as a thin alias for the update action, so existing references keep working.
- Removed: `--harness`, `--pack=`, `--copy`, the pack menu, `SUPERVISOR_PATH`, `install_pack`,
  `install_abs`. `SUPERVISOR_REPO` survives as an undocumented developer/test seam only.
- User-facing text says **"CLI"** and **"Easy Kit"**, never "harness". Internal identifiers
  (`harness-lock.json`, `lib/harness-fetch.sh`) are not renamed — renaming the lock breaks every
  existing install.

**No silent loss — this replaces ADR-0001's "always full-overwrite".**

- Every path, install included, goes through the hash-lock conflict rule ADR-0001 designed for update.
- A pre-existing, non-kit `CLAUDE.md` / `AGENTS.md` is saved as `<name>.bak` before the kit copy, and
  the plan screen shows it.
- `CLAUDE.md` and `.claude/settings.json` are covered by update. `settings.json` is **merged** with
  `python3`, a hard prerequisite already, because every wired hook runs as `python3 …`. Kit hook entries
  are added and user permissions are left alone; if `python3` is missing, the hook step fails loudly.
- A skill deleted upstream is removed if its lock hash still matches (never edited), and kept with a
  warning if it was edited.
- Kit-internal tests (`.claude/hooks/tests/`) stop shipping into user projects.

**Packs: a dormant catalog, activated by business domain.**

- The installer copies all of `packs/` into the project as a **Pack catalog**: present on disk,
  invisible to every CLI, because nothing under `packs/` is linked or projected.
- At Phase 0 / Stage 1 the Supervisor runs a `select-packs` skill. It reads each `PACK.md` "When to
  use / Do NOT select" section against the project's business domain, recommends packs, and asks the
  client to choose from a list.
- On approval, `select-packs` copies that pack's `agents/*.md` and `skills/*/` into the plain-root
  canon (`agents/`, `skills/`), which makes it an **Activated pack**. A pack name that collides with a
  core agent or skill is refused, never overwritten.
- **Hard-Stop Gate 1 interpretation, stated so it cannot stretch:** copying *kit-shipped* pack files
  after explicit client approval is configuration, not project implementation, so the Supervisor-run
  skill may do it. That permission covers verbatim copies from `packs/` into `agents/`/`skills/` and
  nothing else. Any edit to those files, or any file not shipped in `packs/`, is implementation and
  goes through a TASK_GUIDE.

**Unchanged from ADR-0001**: temp-clone-copy-discard, the git-repository prerequisite check before any
write, the hash-lock mechanism itself, and refusal of old symlink-model installs.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| **One zero-flag entrypoint with confirm menus; dormant pack catalog** | One command forever; nothing to remember; re-running can't wipe edits; net script size shrinks; keeps the public `setup.sh` URL | Largest behaviour change; `/dev/tty` handling; loses flag-driven scripting; T108's pack-choice parsing is deleted | **Selected** |
| Two scripts, fixed in place (ADR-0001 shape kept) | Smallest diff; no doc or test renames | Two commands and two URLs; keeps install-time pack choice the user rejected; duplicated code in both scripts survives | Contradicts the user's "one command" and "packs chosen from the domain" requirements |
| One entrypoint that auto-detects silently, `--reinstall` flag | Simplest code; identical in CI and terminal | No chance to stop a wrong detection (lock deleted, partial install); still a flag to remember | User explicitly required confirmation and a choice of action |
| Packs fetched on demand at activation (no catalog shipped) | Leaner project tree | Needs network mid-session plus one more script | ~200 KB catalog is cheaper than a second fetch path; user chose the catalog |

---

## Consequences

### Positive
- Users learn one line, and never a flag.
- The `setup.sh` name and URL stay, so existing READMEs, forks and muscle memory keep working.
- The five measured silent failures (packs, update coverage, clobbered edits, clobbered `CLAUDE.md`,
  missing hooks) become either fixed or loud.
- Pack choice moves to the moment the Supervisor actually knows the business domain.

### Negative (accepted trade-offs)
- No flag-driven automation: CI and scripted installs get the printed safe defaults only.
- Existing tests that parse setup's flag `case` block (`tests/test_pack_docs_flags.py`) and T108's
  `tests/test_pack_choice_parsing.sh` are retired with the features they guarded.
- `select-packs` writes to the canon, which is a deliberate, bounded Gate 1 interpretation (above) that
  reviewers must hold to its limit.
- Projects that previously ran `setup.sh --pack=…` got nothing, so there is no pack migration to perform.

### Follow-up
- [ ] Build on one integration branch cut from `main`; `main` receives the set in one reviewed merge after every task passes `/verify` (`memory/decisions.md`, 2026-09-12).
- [ ] Stage 2 split, in order: (1) wire `tests/test_setup.sh`, `test_update.sh` and `test_install_update_smoke.sh` into CI; (2) update coverage + no-silent-loss rules; (3) the confirmed menu entrypoint + `update.sh` alias; (4) Pack catalog + `select-packs`. Each starts at C2/Medium per Hard-Stop Gate 2 (installer restructure), except (1).
- [ ] On acceptance: set ADR-0001 status to "Partially superseded by ADR-0002"; add an amendment note to DDR-0007; sync `CLAUDE.md`, `CLAUDE_LEGACY.md`, `docs/claude-md/folder-structure.md`, `README.md`, `site/index.html`, `RUNBOOK.md`, `packs/*/PACK.md`.
- [ ] Open, not decided here: the 2026-08-25 "v2 is the working branch; main is frozen" rule no longer matches practice (`main` is 35 commits ahead of `v2`).
