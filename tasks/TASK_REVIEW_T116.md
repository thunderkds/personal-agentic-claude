# TASK_REVIEW — T116: Every pack ships as a dormant catalog; the broken install-time pack installer is removed

> Sibling of `tasks/TASK_GUIDE_T116.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | Implementer: `tests/test_pack_catalog.sh` (new; SC1–SC5, AC7, edge T112 backup, M1/M2 self-run) → `15 passed, 0 failed` @ `543b0d5` 2026-09-23T06:27Z; `tests/test_docs_match_installer.py` extended (D5 + `test_owned_exemptions_are_still_needed`). Reviewer to re-run and tick. |
| Verification command run | ☐ pass / ☐ fail | Implementer run @ `543b0d5`: all 15 shell suites rc=0; pytest `1 failed, 853 passed` — the one failure (`test_memory_cap_matches_enforced_budget`, site says 45,000, enforced 42,000 since `d99976d`) is **pre-existing**: it fails identically on `git archive e893453` (`1 failed, 21 passed`). Not touched (out of scope). shellcheck rc=0. |
| Negative cases hold | ☐ pass / ☐ fail | no CLI sees pack skills, M1/M2 — implementer: M1 fails with `.codex contains a packs path`, M2 with `packs/ai-agent/PACK.md missing`; suite also run against pre-change `setup.sh`+`MANIFEST` (`bfedde5`): `4 passed, 11 failed`. D5 control: re-adding `sh ~/.supervisor/setup.sh --pack=mobile` to `site/index.html` → `1 failed` (`site/index.html:471: '~/.supervisor'`, `'--pack='`), restored → `6 passed`. |
| verify | ☑ pass / ☐ fail / ☐ N/A | User-invoked `/verify`, 2026-09-23T07:48Z, HEAD `4f3fac7`, driven at the real CLI surface (pty, `file://` kit, real `claude`+`codex` on PATH; no suite run as evidence). Piped `cat setup.sh \| sh` install with Enter defaults: no packs question, plan lists `packs`, catalog line printed, rc=0. **Harness check:** `claude -p` in the installed project listed 49 skills incl. core (`brainstorming`, `tdd`, `wake`) and **0 of 10** pack skills; control — copying `packs/mobile/skills/ui-accessibility` into `skills/` → 50, `ui-accessibility` listed. Probes: `1, 5` typed at `Proceed?` → `Please enter y or n.`; Ctrl-C at CLI menu → `Cancelled — nothing was changed.`, 0 files; no-op Update clean; upstream `packs/devops/PACK.md` edit → refreshed silently; local+upstream edit on `packs/data/PACK.md` → plan names it, `conflict:` + diff, `s` keeps `MY NOTE`; Reinstall → edit moved to `packs/data/PACK.md.bak`, catalog line printed. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ pass / ☐ fail | D1–D2 site #packs/#options, D3 PROJECT_SPEC.md, D4 README, D5 docs-agreement test extended + mutation control |
| `tests/test_pack_choice_parsing.sh` retired — reason | ☐ pass / ☐ fail | Implementer: deleted with `resolve_pack_choices`, the parser it tested (AC5); its `ci.yml` step now runs `tests/test_pack_catalog.sh`; `tests/test_ci_wires_shell_suites.py` discovers suites by glob, so no entry to remove — it stays green (`9 passed` with the docs test). |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | installer + MANIFEST; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Common-Infrastructure-Agent, 2026-09-23T06:17:46Z–06:18:02Z, branch head `e893453`,
before any implementation commit). Kit = `git archive HEAD` committed into a scratch repo, served as
`SUPERVISOR_REPO=file://…/kit`; target = empty scratch git repo; interactive path driven through a
pty (`run_in_pty` from `tests/lib/pty.sh` = `script -qec`), answers `1` Install, `1` Claude Code,
`1` New project, `1, 5` packs, Enter to Proceed. `--pack=mobile` is not reproduced: since T115 every
argument exits 1 before anything is written (guide, *Drift* §1).

**B1 — interactive menu, machine with no central clone** (`SUPERVISOR_PATH=<nonexistent>`, the case
every post-ADR-0001 user is in), rc=0:
```
        Enter numbers separated by spaces, or press Enter to skip:
Plan: Install Easy Kit into …/scratchpad/before/clean
  - CLIs: Claude Code
  - Project type: New project (CLAUDE.md)
  - Copies in: agents, skills, .claude/hooks, templates, docs/claude-md, AGENTS.md, .cursor/rules, CLAUDE.md
  …
Proceed? [Y/n] [info]  Installed .claude/settings.json (copy). Restart Claude Code to activate hooks.
[info]  Wrote ./.claude/harness-lock.json (74 file hashes).
[warn]  Pack 'mobile' not found in central clone (…/before/no-clone/packs/mobile) — skipping.
[warn]  Pack 'api' not found in central clone (…/before/no-clone/packs/api) — skipping.
[info]  Setup complete. Easy Kit copied into …/scratchpad/before/clean
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  CLIs: Claude Code
[info]  Packs requested: mobile api
$ ls agents | grep -cE 'mobile|api-'   → 0
$ ls -d packs                          → No such file or directory
```

**B2 — same answers, default `SUPERVISOR_PATH` on this machine, where a v1 `~/.supervisor` clone
still exists.** Worse than "installs nothing": the pack path writes **absolute symlinks out of the
project** into the canon, through the `.claude/agents -> ../agents` link, none of them in the lock:
```
[info]  Pack 'mobile' installed.
[info]  Pack 'api' installed.
[info]  Packs requested: mobile api
agents/api-designer.md     -> /home/hungnguyenhuu/.supervisor/packs/api/agents/api-designer.md
agents/mobile-developer.md -> /home/hungnguyenhuu/.supervisor/packs/mobile/agents/mobile-developer.md
skills/auth-checklist      -> /home/hungnguyenhuu/.supervisor/packs/api/skills/auth-checklist/
skills/contract-review     -> /home/hungnguyenhuu/.supervisor/packs/api/skills/contract-review/
skills/platform-compatibility -> /home/hungnguyenhuu/.supervisor/packs/mobile/skills/platform-compatibility/
skills/ui-accessibility    -> /home/hungnguyenhuu/.supervisor/packs/mobile/skills/ui-accessibility/
```

**B3 — no terminal** (`setsid -w sh setup.sh </dev/null`), rc=0:
```
[info]  No terminal — no packs installed. Re-run in a terminal to pick packs from the menu.
…
[info]  Setup complete. Easy Kit copied into …/scratchpad/before/notty
$ ls -d packs → No such file or directory
```

In every BEFORE run the project receives **no `packs/` directory**: no catalog exists.

*Historical, not reproducible since T115* — Supervisor probe, 2026-09-12, `main` `8115bc9`:

`--pack=mobile`:
```
[warn]  Pack 'mobile' not found in central clone (…/home/.supervisor/packs/mobile) — skipping.
[info]  Packs requested: mobile
NO mobile agent installed
```

Interactive menu via pty, answer `1, 5`:
```
[warn]  Pack 'mobile' not found in central clone (…/.supervisor/packs/mobile) — skipping.
[warn]  Pack 'api' not found in central clone (…/.supervisor/packs/api) — skipping.
[info]  Packs requested: mobile api
```

**AFTER** (Common-Infrastructure-Agent, 2026-09-23T06:27:15Z, branch head `543b0d5`, same method as
BEFORE; answers `1` Install, `1 2` Claude Code + Codex, `1` New project, Enter to Proceed — there is no
packs question to answer), rc=0:
```
Plan: Install Easy Kit into …/after/tty
  - CLIs: Claude Code, Codex
  - Project type: New project (CLAUDE.md)
  - Copies in: agents, skills, .claude/hooks, templates, docs/claude-md, packs, AGENTS.md, .cursor/rules, CLAUDE.md
  …
Proceed? [Y/n] [info]  Setting up Codex: copying the kit's skills into its folder.
  …
[info]  Projected 26 item(s) for 'codex'.
  …
[info]  Wrote ./.claude/harness-lock.json (94 file hashes).
[info]  Setup complete. Easy Kit copied into …/after/tty
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  CLIs: Claude Code, Codex
[info]  Pack catalog: every pack is in packs/, inactive. Your Supervisor recommends packs for this project.
$ ls packs                                → ai-agent api data devops mobile
$ diff -r kit/packs tty/packs             → clean
$ grep -c '"packs/' .claude/harness-lock.json → 20      (lock 74 → 94 hashes)
$ find -L .claude .codex -name 'mobile-developer*' -o … ui-accessibility / pipeline-safety / api-designer → (nothing)
```
No terminal (`setsid -w sh setup.sh </dev/null`), rc=0: the plan's `Copies in:` includes `packs`, the
same catalog line prints, and there is no `No terminal — no packs installed` line.

**DELTA**: Before, the installer asked about packs and then either installed nothing or symlinked
into a v1 `~/.supervisor` clone outside the project, and no project had a `packs/`; after, it asks
nothing, every project gets all five packs as hash-locked, CLI-invisible files, and one line says so.

**WITNESS**: Common-Infrastructure-Agent (implementer), 2026-09-23T06:17Z (BEFORE) and 06:27Z (AFTER).
Reviewer re-run pending (Stage 4).

---

## Implementer notes (T116 agent)

**Docs (D1–D5), new text quoted**

- D1 `site/index.html` `#packs` lead: "Packs add domain-specific agents and skills on top, never replacing
  core resources. Every project ships all packs, inactive: they sit in `packs/` and no CLI loads them."
  Closing paragraph: "The installer never asks about packs. Your Supervisor recommends packs for your
  project from its business domain, and activates each pack you approve by copying it into `agents/`
  and `skills/`. Update keeps the `packs/` catalog current like any other kit file." Pack table kept.
- D2 `site/index.html` `#options`: the `SUPERVISOR_PATH` row is removed; `GITHUB_USERNAME` remains.
- D3 `PROJECT_SPEC.md` Known Risk Areas: "SUPERVISOR_PATH handling" replaced by "| Pack activation name
  collision | Medium | An activated pack's agent or skill name could collide with a core one in
  `agents/` or `skills/`; ADR-0002 requires activation to refuse, never overwrite. The shipped catalog
  itself is inert (T116: `packs` carries no MANIFEST destination pair) — activation is owned by T117 |".
- D4 `README.md`: **unchanged** — it has no pack install instruction; its two pack mentions (`:57`,
  `:71`) only point at the site / list pack names.
- D5 `tests/test_docs_match_installer.py`: `FORBIDDEN` gains `"SUPERVISOR_PATH", "~/.supervisor",
  "--pack="`. **Supervisor decision needed:** the only live hit is
  `docs/claude-md/folder-structure.md:41` ("Installed via `setup.sh --pack=<name>`"), a file on this
  guide's Must-NOT-Touch list (T117). It is carried as one pinned `OWNED_EXEMPTIONS` entry (owner
  T117); `test_owned_exemptions_are_still_needed` fails once T117 removes that text, forcing the
  exemption's deletion. The guide's D5 did not anticipate that `docs/claude-md/*.md` is in `LIVE_DOCS`.

**Forward-looking doc claim.** D1's wording (guide-mandated) says the Supervisor "recommends … and
activates"; `select-packs` is T117 and not yet shipped. Until T117 merges, the site describes
behaviour a user will not yet get — the Supervisor should decide whether T116 and T117 ship together.

**Edge Case Checklist**
- No pack migration: `command grep` finds no `~/.supervisor`/`SUPERVISOR_PATH` in `setup.sh`,
  `update.sh`, `lib/*.sh` (SC5), so nothing creates or expects a symlink into it. BEFORE B2 shows old
  projects on a machine with a v1 clone *may* hold absolute `agents/*`/`skills/*` symlinks into
  `~/.supervisor` from the old pack path; those were never in the lock, so update neither tracks nor
  removes them. Not migrated (out of scope); flagged.
- `packs` as an unrelated symlink: update refuses, rc=1, `[error] MANIFEST path './packs' is a symlink
  (old symlink-model install).` — existing, correct `detect_symlinks` behaviour for MANIFEST paths,
  though the "old symlink-model" wording is inaccurate for that case.
- Pre-existing own `packs/` → moved to `packs.bak/` before the catalog lands (T112; tested in the suite).
- Pack removed upstream later → T113 orphan rule applies via the lock (20 `packs/` entries); no extra code.
- `tests/test_site_content.py` kept passing for everything T116 touches (the singular "pack" token the
  README-promised-topics test needs is kept in D1).

**Stage 4 code-review (self-run, 2026-09-23)**: 0 P0 / 1 P1 (fixed) / 1 P2 / 3 P3. P1: no test covered a
pre-catalog project gaining `packs/` on Update — the path every existing user takes. Probed first
(pre-T116 install from `e893453`, then Update to HEAD: rc=0, 20 `new file installed: packs/…`, 20 lock
entries), then added as a suite case → `16 passed, 0 failed`; mutated to update against the no-packs
kit → `15 passed, 1 failed` naming that case. Side effect observed: with `prompt_packs` gone, `^D` at the
project-type menu now ends `Cancelled — nothing was changed.` rc=0 — T121's silent exit is gone.

**Cut / not done**: `SUPERVISOR_PATH="$NO_CLONE"` env assignments remain in several older test suites
(`test_setup.sh`, `test_settings_merge.sh`, `test_harness_projection.sh`); now inert, left untouched
(outside Files to Change).
