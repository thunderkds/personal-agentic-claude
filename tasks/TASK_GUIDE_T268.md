# TASK_GUIDE — T268: Native Windows support, step 7 — `setup.ps1`, the PowerShell installer (install and reinstall)
**Date**: 2026-11-06
**Complexity Level**: C3
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`
6. C3: read `memory/codebase-map.md`
7. Read `docs/windows-support-plan.md` and `docs/adr/0003-native-windows-support.md` (decisions 3, 4, 5)
8. Read the shell installer you are porting, end to end: `setup.sh` (910 lines), `lib/harness-fetch.sh` (546 lines), `MANIFEST`, and the Python helpers `lib/merge-settings.py` and `lib/windows_hooks.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: native Windows support for the kit ("by pass the wsl, focus on the native window"; "this will be the new version that support window"); installer language "as you recommend" (a PowerShell port), then, for T268: **"Pure PowerShell port"** and **"Install + update.ps1"** (update is T271, which depends on this task).

**Restated intent**:
> A Windows user with Git, Python and PowerShell (5.1 or 7) runs `setup.ps1` inside a git repository and gets what `setup.sh` gives a Claude Code user: the kit's files copied from the MANIFEST (with the `!` exclusions), existing files backed up before they are replaced, the `.claude/skills` and `.claude/agents` links onto the plain-root canon (junction first, else a copy), `.claude/settings.json` merged and converted to the Windows hook form, scaffold files, `.gitignore` entry and `.claude/harness-lock.json` written. All of it is PowerShell; the only Python is the two existing helpers.

**Decisions already made (do not reopen)**:
- ADR-0003 decision 3: the Python launcher is `py -3`, else `python`. Decision 5: canon links are a directory junction, else a real copy plus a drift check (`update` re-copies it: T271).
- T266: after merging settings, run `lib/windows_hooks.py <settings> <settings> --launcher py|python` (the kit entries become exec form). An update replaces a converted entry with the POSIX form (same key), so T271 must run the converter again after every merge; here it runs once after the merge.
- Scope (vital slice, Simplicity First): Claude Code only. Cut list below.

**Out of scope (cut list)**:
- `update.ps1` and the Update action (T271). `setup.ps1` detects an existing install (a `harness-lock.json`) and, for now, offers Reinstall or Cancel only, with a clear message that Update arrives with T271.
- Codex and Cursor projections (`.codex/skills`, `.cursor/rules`, `harness_project_manifest`), the CLI menu, board mode `online` (`offer_board_mode`), the piped `irm | iex` bootstrap, packs activation.
- Any change to `setup.sh`, `update.sh`, `lib/*.sh`: they stay byte-identical.
- Windows ARM, cmd.exe, WSL.

**Requirement Refs**: `docs/windows-support-plan.md` T-W7; `docs/adr/0003-native-windows-support.md` decisions 3, 4, 5. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-06; the user chose "Pure PowerShell port" and "Install + update.ps1" in answer to the Supervisor's design question)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `setup.ps1`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `setup.ps1` and `lib/harness.ps1` exist. Both start with `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'`. They contain no PowerShell-7-only syntax (`&&`, `\|\|` as pipeline chain, `??`, `?:` ternary, `-Parallel`), so Windows PowerShell 5.1 runs them; no `python3`, no `sh`, no `bash`, no `/dev/null` | PowerShell 5.1 and 7 |
| 2 | Preconditions run before any file is written: `git` on PATH; the current directory is inside a git work tree; a Python launcher is found (`py -3`, else `python`, each probed by running it with `-c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"`, so the Microsoft Store stub is rejected). A failed precondition prints one `[error]` line naming the fix and exits 1 with nothing written | `check_git`, `check_target_is_git_repo` |
| 3 | Fetch: `git clone --depth 1 <url> <temp dir>`. URL = `$env:SUPERVISOR_REPO` if set, else the rule of `kit_repo_url` (`GITHUB_USERNAME`, default `thunderkds`, try `easy-kit.git`, then `personal-agentic-claude.git` for a user other than `thunderkds`). The temp dir is removed in a `finally`, also on error | `harness_fetch`, `kit_repo_url` |
| 4 | MANIFEST parsing matches `lib/harness-fetch.sh`: comments and blank lines skipped; field 1 is the path; trailing `<harness>=<dest>` pairs ignored (Claude Code only); a `!<path>` line excludes that path and everything under it on whole path segments. A directory entry is copied recursively; an excluded path is never copied, backed up or recorded | `harness_copy_manifest`, `harness_is_excluded` |
| 5 | Copy preserves bytes (no re-encoding, no line-ending rewrite): use `Copy-Item`/`[IO.File]::Copy`, never `Get-Content \| Set-Content` | `.gitattributes` / LF |
| 6 | Backup-then-overwrite: a pre-existing destination that differs from the kit's copy (or is a directory/link/type mismatch) is moved to `<dst>.bak-<id>` (`<id>` = the previous kit commit when the lock records one, else today's `yyyyMMdd`), or the next free `<dst>.bak-<id>.N`; an identical file gets no backup; a taken backup name is never reused; a failed move stops before the destination is replaced. A `[warn]` line names each backup. Same rules as `harness_backup_name`/`harness_backup_path` | `harness_backup_*` |
| 7 | `CLAUDE.md` / `CLAUDE_LEGACY.md` choice and install follow `install_claude` (source file chosen as in `setup.sh`, backup before replace) | `install_claude` |
| 8 | Canon links: `.claude/skills` and `.claude/agents` are created as directory junctions onto `<root>\skills` and `<root>\agents` (`New-Item -ItemType Junction`). If the junction cannot be made, the directory is copied instead and both facts are printed (`[warn]`) and recorded in the lock as `canon_copies`. A real directory already there is moved to a backup first; a regular file there (a symlink checked out with `core.symlinks=false`) is backed up and replaced. Both paths are added to `.git/info/exclude` so git does not store the duplicated contents | ADR-0003 decision 5 |
| 9 | Settings: if `.claude/settings.json` is absent, copy the kit's; else merge with `<py> lib/merge-settings.py <upstream> <project> <root>` (exit 2 = refused: print the block to add by hand, finish the rest, exit 2 at the end, as `merge_settings` does). Then convert the merged file with `<py> lib/windows_hooks.py <file> <file> --launcher py\|python` (the launcher found in AC 2). The result has no `python3` in any kit hook command | T266 contract |
| 10 | `.claude/harness-lock.json` is written with the same schema and the same SHA-256 content hashes as `write_harness_lock` (every installed file, repo-relative paths with `/`, directories expanded to files), plus `canon_copies` when AC 8 fell back. A Python test reads a lock written by `setup.ps1` with the same loader `lib/harness-update.sh` uses (find it) and accepts it | `write_harness_lock` |
| 11 | `scaffold_project` (memory/MEMORY.md, PROJECT_KANBAN.md etc., only when absent) and `ensure_gitignore_entry` are ported with the same file contents and the same idempotence (a second run adds no duplicate entry) | `scaffold_project` |
| 12 | Interactive flow: a plan screen lists what will be installed, backed up and replaced, then `Confirm [Y/n]`. `-Yes` skips the prompt (CI). With a `harness-lock.json` present the choices are Reinstall or Cancel (Update message as above). `Cancel` writes nothing and exits 0 | `choose_action`, `confirm_plan` |
| 13 | Reinstall (a second run) is idempotent: files identical to the kit's copy produce no backup and the lock hash set is unchanged | `run_install` |
| 14 | The CI smoke: `.github/workflows/windows.yml` gains a step that runs `tests/windows/smoke-install.ps1` on `windows-latest` (creates a temp git repo, runs `setup.ps1 -Yes` with `SUPERVISOR_REPO` pointing at the checkout, asserts the files, the junction or copy, the lock, the exec-form hooks, and a second-run idempotence). The step uses the same SHA-pinned actions and `permissions: contents: read` | Windows CI |
| 15 | `setup.sh`, `update.sh`, `lib/*.sh` are byte-identical to the base (`git diff --stat` shows none of them) | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A fresh temp git repo and `SUPERVISOR_REPO=<this checkout>` | Every MANIFEST path present, no `!` path present, lock written, settings converted | pwsh smoke (Docker) and the CI smoke |
| 2 | The same repo with one kit file edited | A `.bak-<id>` copy holds the edit; the kit file replaces it | pwsh smoke |
| 3 | A second run | No new backups; lock hashes unchanged | pwsh smoke |
| 4 | `python3` absent, `py` absent, `python` present | `setup.ps1` finds `python` | pwsh smoke with a fake PATH |
| 5 | No Python at all | One `[error]` line, exit 1, no file written | pwsh smoke |
| 6 | `setup.ps1` with a banned token injected (`python3`, `&&`) | The static test fails | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py -q && python3 -m pytest .claude/hooks/tests tests -q
```

`tests/test_setup_ps1_pwsh.py` runs the smoke in PowerShell on Linux through Docker (`mcr.microsoft.com/powershell`, pin the tag in the test) and skips with a reason when `docker` or the image is absent. It never pulls an image: the implementer pulls it once by hand (`docker pull`, say so in the Evidence) and may remove it afterwards.

---

## Approach

**Pattern reference**: `setup.sh` (flow: `main`, `run_install`, `plan_install`), `lib/harness-fetch.sh` (library of small functions with the contracts in AC 3-6), `lib/windows_hooks.py` (T266: the converter you call), `.github/workflows/windows.yml` (T263: CI job to extend).

**Vital slice**: install and reinstall for Claude Code, driven by the MANIFEST, with backups, links, settings and lock. Library functions go in `lib/harness.ps1` (dot-sourced by `setup.ps1`) so T271 can reuse them; keep functions small and named like the shell ones (`Invoke-HarnessFetch`, `Copy-HarnessManifest`, `Backup-HarnessPath`, ...) with a one-line comment naming the shell function each ports.

**Cut list**: as under Out of scope.

Local testing: this machine has no `pwsh`; Docker is available. Pull the official PowerShell image once, run `setup.ps1` inside it against a temp repo, and fix what fails. Linux PowerShell cannot prove junctions, `core.symlinks`, CRLF or Windows paths, so the CI smoke (AC 14) is the real check; say so in the Evidence and mark the Windows run unverified until the first PR.

Write the static test first (it goes red on a missing file), then the pwsh smoke, then the code.

---

## Edge Case Checklist

- [ ] Paths with spaces and non-ASCII characters; use `-LiteralPath` everywhere, never wildcard-expanding `-Path`
- [ ] A read-only destination file (attribute) is cleared before overwrite, or the failure stops with a message
- [ ] `Join-Path` / `[IO.Path]::GetRelativePath` is not in 5.1: write a small helper; lock paths always use `/`
- [ ] `git` output encoding: do not parse localized output; use `git rev-parse --is-inside-work-tree` and exit codes
- [ ] The temp clone is removed even when the script throws or the user presses Ctrl+C
- [ ] `Start-Process`/`&` calls pass arguments as arrays, never a built string
- [ ] The junction target is an absolute path: say in the final message that moving the project folder needs a re-run
- [ ] `-Yes` run with no TTY never blocks on `Read-Host`
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `tests/test_docs_match_installer.py` for "setup.sh" claims, an installer-file list or a MANIFEST count

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.ps1` | New: entry point, flow, plan screen |
| `lib/harness.ps1` | New: the library |
| `tests/windows/smoke-install.ps1` | New: the CI smoke |
| `tests/test_setup_ps1_static.py` | New: banned tokens, strict mode, 5.1-safe syntax |
| `tests/test_setup_ps1_pwsh.py` | New: Docker pwsh smoke (skips when absent) |
| `.github/workflows/windows.yml` | New step for the smoke (T263 file) |
| `MANIFEST` | Do NOT list `setup.ps1`/`lib/harness.ps1` if `setup.sh`/`lib/*.sh` are not listed (check first) |
| Pre-existing pin tests | Known candidates: `tests/test_docs_match_installer.py`, `tests/test_windows_ci_workflow.py` (workflow shape pins: keep it green, extend its allowed steps), `tests/test_manifest_exclusions.sh`, README current-ness tests. Grep `tests/` and `.claude/hooks/tests/` for installer file lists and for the workflow's step list; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/*.sh`, `lib/merge-settings.py`, `lib/windows_hooks.py` | Behaviour of the shell installer and the T266 helpers is fixed |
| `.claude/hooks/*` | Not this task |
| `docs/windows-support-plan.md`, `memory/` | Supervisor |

---

## Test Plan

Static Python test of the PowerShell source (banned tokens, strict mode); Docker-pwsh smoke of the five Success Criteria; extension of the existing workflow-shape test so it still passes with the new step; the full Python suites; a mutation control per the guide. The Windows-only behaviours (junction, CRLF checkout, `core.symlinks=false`) are covered by the CI smoke, which has not run when this task is reviewed.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Lint passes
