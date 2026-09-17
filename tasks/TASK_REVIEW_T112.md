# TASK_REVIEW — T112: First install never destroys a project's own files — they are backed up and named

> Sibling of `tasks/TASK_GUIDE_T112.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_install_backups.sh` (new, wired in ci.yml) — Supervisor re-run 2026-09-17 at `5614934`: `13 passed, 0 failed` |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | identical content (no .bak), existing .bak, non-git, M1 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor re-run: test_setup `18 passed, 0 failed`; test_install_update_smoke `9 passed, 0 failed`; test_harness_projection `41 passed, 0 failed`; test_t098_harness_presence `20 passed, 0 failed`; `shellcheck -x setup.sh lib/harness-fetch.sh tests/test_install_backups.sh` clean |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☑ pass | D1–D2 PROJECT_SPEC.md, D3 site #install, D4 RUNBOOK.md — quoted below under the doc list |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Repo pre-seeded with
`CLAUDE.md` = `# my project rules`, `AGENTS.md` = `# my agents`, then `setup.sh </dev/null`:

```
CLAUDE.md now: # Claude Project Supervisor Guidelines
AGENTS.md now: # AGENTS.md
```

Exit 0, no warning, no backup.

**BEFORE — directory case** (Common-Infrastructure-Agent, 2026-09-17, kit HEAD `d1f91de` = `main` + guide
retarget only, before any implementation commit). Scratch git repo under `mktemp -d`, pre-seeded with
`templates/mine.md` and `docs/claude-md/my-notes.md`, then `SUPERVISOR_REPO=file://<worktree> bash setup.sh </dev/null`:

```
== 2026-09-17T11:27:59Z BEFORE install (kit HEAD d1f91de)
docs/claude-md:
-rw-rw-r-- 1 hungnguyenhuu hungnguyenhuu   21 Sep 17 18:27 my-notes.md
templates:
-rw-rw-r-- 1 hungnguyenhuu hungnguyenhuu   16 Sep 17 18:27 mine.md
== running setup.sh </dev/null
exit=0
[info]  Wrote ./.claude/harness-lock.json (110 file hashes).
[info]  Setup complete. Harness copied into .../before.tIwuSI/proj
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  Harnesses:claude
== 2026-09-17T11:27:59Z AFTER install
docs/claude-md:
code-naming-conventions.md  folder-structure.md  memory-write-protocol.md
phase0-project-initiation.md  pipeline-stages.md  untrusted-content-boundary.md
templates:
ADR_template.md ... TASK_GUIDE_template.md TASK_REVIEW_template.md thinking_report_template.html
ls: cannot access 'templates/mine.md': No such file or directory
ls: cannot access 'docs/claude-md/my-notes.md': No such file or directory
bak count: 0
```

Premise confirmed by running: both project directories are replaced wholesale by `rm -rf` at
`lib/harness-fetch.sh:152`, exit 0, no warning, no backup.

**AFTER** (kit HEAD `db39284`; same probe, seeded with both the directory and the file cases):

```
== 2026-09-17T11:31:36Z seeded (kit HEAD db39284): templates/mine.md docs/claude-md/my-notes.md CLAUDE.md AGENTS.md
exit=0
[warn]  Backed up your existing './templates' to './templates.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
[warn]  Backed up your existing './docs/claude-md' to './docs/claude-md.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
[warn]  Backed up your existing './AGENTS.md' to './AGENTS.md.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
[warn]  Backed up your existing './CLAUDE.md' to './CLAUDE.md.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
[info]  Setup complete. Harness copied into <tmp>/proj
== 2026-09-17T11:31:37Z result
my own template                          # templates.bak/mine.md
my own claude-md doc                     # docs/claude-md.bak/my-notes.md
# my project rules                       # CLAUDE.md.bak
# my agents                              # AGENTS.md.bak
# Claude Project Supervisor Guidelines   # CLAUDE.md (kit)
# AGENTS.md                              # AGENTS.md (kit)
ADR_template.md ...                      # templates/ (kit)
backups in lock: 0
== identical re-run
exit=0 backup lines: 0
```

**DELTA**: Install now moves every differing pre-existing path (files and whole directories) to a named
`.bak` instead of deleting it, and leaves identical content alone.

**WITNESS**: Common-Infrastructure-Agent (implementer), 2026-09-17 11:27Z (BEFORE) / 11:31Z (AFTER),
scratch repos under the session scratchpad via `mktemp -d`. Independent re-run is for the Stage 4/5 reviewer.

---

## Implementer notes (for the reviewer — Evidence checkboxes above left for Stage 4/5)

**Verification Command at `db39284`:**

```
$ bash tests/test_install_backups.sh
PASS: SC1: CLAUDE.md moved to CLAUDE.md.bak, kit installed, backup named once
PASS: SC2: AGENTS.md moved to AGENTS.md.bak, kit installed, backup named
PASS: SC3: templates/ moved to templates.bak/ with mine.md intact; kit templates/ installed
PASS: SC4: identical AGENTS.md and templates/ left alone — no backup, no line
PASS: SC5: CLAUDE.md.bak untouched; backups went to .bak.1 then .bak.2
PASS: SC6: non-git dir rejected (exit 1), CLAUDE.md unchanged, no backup
PASS: SC7: no .bak path appears in any harness-lock.json
PASS: AC7: empty repo installs with zero backups
PASS: edge: symlinked templates -> link moved to templates.bak, target untouched
PASS: edge: own .claude/hooks (spaced filename) backed up, settings.json warning printed
PASS: edge: file at a directory path -> backed up, kit directory installed
PASS: M1: with the rm -rf restored, mine.md is destroyed — SC3 would fail
12 passed, 0 failed
$ bash tests/test_setup.sh                  -> ----- summary: 18 passed, 0 failed -----
$ bash tests/test_install_update_smoke.sh   -> 9 passed, 0 failed
$ bash tests/test_harness_projection.sh     -> test_harness_projection.sh: 41 passed, 0 failed
$ shellcheck -x setup.sh                    -> exit 0 (ShellCheck 0.11.0, from a scratch venv: not installed on this machine)
```

Red run before the implementation (same suite): 4 passed, 7 failed (SC1, SC2, SC3, SC5, both edges, M1).
Also green: `test_update.sh`, `test_settings_merge.sh`, `test_update_claude_md.sh`, `test_harness_fetch.sh`,
`test_t098_harness_presence.sh`, `test_shellcheck_clean.sh` (with `SHELLCHECK=` set), `test_ci_wires_shell_suites.py`,
`test_site_content.py`, `test_readme_current.sh`, `scripts/validate.sh`.

**New test file**: `tests/test_install_backups.sh`. Identical-content check uses `cmp -s` (files) and
`diff -rq` (directories), not the setup.sh hash helper — that helper lives in `setup.sh`, not the lib.

**Docs (new text):**
- D1 `PROJECT_SPEC.md` Critical Constraints: "`setup.sh` must never destroy a project's own files — before replacing any pre-existing path (`CLAUDE.md` or a MANIFEST path, file or directory) whose content differs from the kit's, install moves it to `<name>.bak` (or the next free `<name>.bak.N`; an existing backup is never overwritten) and names the backup in its output. Identical content is left alone with no backup (T112, ADR-0002)"
- D2 `PROJECT_SPEC.md` Known Risk Areas: "| Copy install over existing paths | Medium | Install copies kit files over paths the project may already own; a silent replace would destroy project data. Mitigated by `harness_backup_path`, which moves a differing path to `<name>.bak[.N]` and names it — see `docs/adr/0002-one-confirmed-menu-driven-installer.md` ("No silent loss") | `setup.sh`, `lib/harness-fetch.sh` |"
- D3 `site/index.html` `#install`: "Installing into an existing project never deletes what is already there: a file or folder the kit would replace is first moved to a backup (`CLAUDE.md.bak`, `templates.bak/`, …), and each backup is listed in the install output. Identical files are left alone."
- D4 `RUNBOOK.md`: "| `*.bak` files or folders (e.g. `CLAUDE.md.bak`, `templates.bak/`, `.bak.1`) appear after install | The project already had those paths with different content; install moved them aside instead of overwriting them (T112), and named each one in a `[warn]` line | Compare each backup with the kit's copy and merge what you need by hand, then delete the backup. If `.claude/hooks.bak` appears, repoint any of your own hook entries in `.claude/settings.json` at it |"

**Scope notes:**
- `.github/workflows/ci.yml` gained one step running the new suite. It is not in Files to Change, but
  `tests/test_ci_wires_shell_suites.py` fails without it. **Needs Supervisor approval** (role guide: no CI edits
  without it); revert is one 3-line hunk.
- A second `setup.sh` run over an existing install now backs up edited kit paths instead of overwriting
  them (unedited ones are identical, so nothing happens). This comes from the shared helper, not from a
  new menu; T114's menu is not built.
- Codex projections (`harness_project_manifest`), `update.sh`, `install_settings`, and
  `harness_install_canon_symlinks` are unchanged.

## Stage 4 — Supervisor review (2026-09-17, branch head `5614934`)

**code-review**: P0 0 · P1 0 · P2 0 · P3 0. Scope: `lib/harness-fetch.sh`, `setup.sh`, `tests/test_install_backups.sh`, `ci.yml`, docs.
Callers: `harness_copy_manifest` and `harness_backup_path` are called only from `setup.sh`. `update.sh` is untouched, so the update path is unchanged, as the guide requires.
Entry point `harness_copy_manifest` / `install_claude` present (reachability OK). `setup.sh` runs `set -e`, so `harness_copy_manifest`
returning 1 on a failed backup aborts the install. The agent's own P1 (unchecked `mv`) was fixed in `5614934` with a test.

**Supervisor mutants** (the agent's M1 not trusted alone):
- M2: file identical-content short-circuit replaced with `false` → `FAIL: SC4: identical content produced a backup` (12 passed, 1 failed)
- M3: `.bak.N` numbering loop replaced with `while false` → `FAIL: SC5: backup numbering` (12 passed, 1 failed)
Both reverted; `git status` clean afterwards.

**security-review** (Medium risk): no findings. All paths are quoted. A symlink is moved as the link itself (`-L` checked before any
content compare, so the link is never followed). A failed or unreadable `diff -rq` counts as "different", so the helper backs the path up
and never deletes it. Nothing is written outside the project directory.

**CI edit approved**: `ci.yml` step for the new suite is required by `tests/test_ci_wires_shell_suites.py`.

**Pending**: `/verify` (user-invoked).
