# TASK_GUIDE — T271: Native Windows support, step 8 — `update.ps1` and the Update action of `setup.ps1`
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
7. Read `docs/windows-support-plan.md`, `docs/adr/0003-native-windows-support.md` and `tasks/TASK_GUIDE_T268.md` (the installer this task extends) and `tasks/TASK_REVIEW_T268.md` (its Evidence and review fixes)
8. Read what you are porting, end to end: `lib/harness-update.sh` (949 lines: `run_update`, `run_reinstall`, `process_one_file`, `carry_over_unprocessed`, `write_new_lock`, `plan_update`, `plan_reinstall`, `write_update_log`, the lock readers), `update.sh`, and `setup.sh` `choose_action`, `choose_update_mode`, `run_install`. Then read `setup.ps1` and `lib/harness.ps1` as they are on your branch base

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: for the Windows installer, "Pure PowerShell port" and "Install + update.ps1". T268 built install and reinstall; this task adds Update.

**Restated intent**:
> A Windows user who installed the kit with `setup.ps1` runs `setup.ps1` (or `update.ps1`) again and can choose Update: files the user has not touched are replaced by the new kit version, files the user changed are kept or backed up as the shell Update does, new kit files are added, files the kit stopped shipping are removed only when untouched, the settings merge is run again and the Windows hook conversion is run again after it, a canon copy (junction fallback) is refreshed, and `harness-lock.json` is rewritten. Reinstall also removes files the kit stopped shipping, as `run_reinstall` does. All PowerShell; the shell scripts stay byte-identical.

**Decisions already made (do not reopen)**:
- User: pure PowerShell, update included. T268's library (`lib/harness.ps1`) is the base: reuse its functions, add the update functions in `lib/harness-update.ps1` (dot-sourced by `setup.ps1`), keep the same naming style and a one-line comment naming the shell function each ports.
- T266: after every settings merge run `lib/windows_hooks.py <file> <file> --launcher <py|python>`, because the merge replaces a converted entry with the POSIX form (same key). This is the contract the T266 review recorded; a test must prove it.
- ADR-0003 decision 5: a canon copy (recorded as `canon_copies` in the lock) is re-copied on update, and its drift (the project's copy differs from the kit's) is reported, not silently overwritten when the user changed it.
- Claude Code only; no Codex/Cursor projections (same cut as T268).

**Out of scope (cut list)**: Codex and Cursor re-projection (`reproject_harnesses`, `resolve_projection_harnesses`), board mode `online`, the piped bootstrap, packs, the interactive per-file conflict prompt beyond what `-Yes`/a non-interactive run needs (see AC 5), any change to `setup.sh`, `update.sh`, `lib/*.sh` and to T266/T268's Python helpers.

**Requirement Refs**: `docs/windows-support-plan.md` T-W7; `docs/adr/0003-native-windows-support.md` decisions 3-5. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T268 (merged into the base of this branch; `setup.ps1` and `lib/harness.ps1` exist)

**Entry point**: `update.ps1`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `update.ps1` is a thin alias: it runs `setup.ps1` with the Update action selected (the `EASYKIT_ACTION=update` seam of `update.sh`), refuses with the shell's message when nothing is installed (no `harness-lock.json`), and passes `-Yes` through. `setup.ps1` with an existing install now offers Update, Reinstall, Cancel (Enter = Cancel, as T268), and shows a plan screen for Update (`plan_update`: files to replace, add, keep, remove; the asks) | `update.sh`, `choose_action`, `plan_update` |
| 2 | Per-file decisions follow `process_one_file`: file untouched since install (lock hash equals the project's current hash) → replaced with the kit's new copy; file the user changed and the kit changed → handled per AC 5; file the user changed and the kit did not → kept; file new in the kit → added; same content → nothing | `process_one_file` |
| 3 | Removals follow `carry_over_unprocessed` / `deletion_is_safe` / `plan_removals`: a file the kit no longer ships is removed only when untouched (lock hash equals current), empty directories are pruned (`prune_empty_dirs`), a user-changed file is kept and named; nothing outside the lock's recorded paths and the MANIFEST roots is ever removed | `carry_over_unprocessed` |
| 4 | `CLAUDE.md`/`CLAUDE_LEGACY.md` follow `process_claude_md` and the recorded `claude_md_source` (the user's edited CLAUDE.md is never overwritten silently: backup rule of T268 AC 6) | `process_claude_md`, `resolve_claude_md_source` |
| 5 | Conflicts (user changed and kit changed): with a terminal, prompt per file as `prompt_conflict` does (keep / overwrite with backup / skip); with `-Yes` or no terminal, the safe default is KEEP the user's file and write the kit's copy beside it as `<name>.kit-new` (or the shell's equivalent: read `prompt_conflict` and `update_decided_by` and keep the same default and wording), never overwrite silently | `prompt_conflict` |
| 6 | Settings: re-run the T268 settings flow (`Install-HarnessSettings` or its update twin = `update_settings`): merge with `lib/merge-settings.py`, then `lib/windows_hooks.py --launcher` on the merged file. A test merges a project whose settings already hold converted exec-form entries and proves the result is exec form again with no duplicate kit entry and the user's own hook kept | T266 review contract |
| 7 | Canon links: a junction is left alone (it points at the project's own `skills/`/`agents/`, already updated); a canon COPY recorded in `canon_copies` is refreshed from the project's updated `skills/`/`agents/` unless the copy differs from the lock's recorded hashes (user-changed: keep, warn). The new lock keeps `canon_copies` | ADR-0003 decision 5 |
| 8 | `write_new_lock` parity: the new `.claude/harness-lock.json` has the same schema and hashes as the shell's (same helper test as T268 AC 10), records the new kit commit, keeps `claude_md_source`, drops removed files, adds new ones | `write_new_lock` |
| 9 | An update log entry is written as `write_update_log` does (same file, same entry shape) | `write_update_log` |
| 10 | Reinstall also removes files the kit stopped shipping, as `run_reinstall` does (T268 left this out on purpose); same safety rules as AC 3 | `run_reinstall` |
| 11 | Update is idempotent: a second Update run with no kit change replaces nothing, adds nothing, removes nothing, changes no hash and writes no backup | `run_update` |
| 12 | Failure safety: any failure before the lock is rewritten leaves the old lock in place; a failed replace never loses the user's file (backup first, as T268); a failed step names what was and was not done | `run_update` |
| 13 | CI: `tests/windows/smoke-install.ps1` (or a sibling `smoke-update.ps1`) gains an update scenario on `windows-latest`: install, change the kit source (a second local kit commit), run Update, assert replaced/added/removed/kept files, exec-form hooks still intact, lock updated, second Update a no-op. The workflow shape test is extended so the step cannot be dropped | Windows CI |
| 14 | `setup.sh`, `update.sh`, `lib/*.sh`, `lib/merge-settings.py`, `lib/windows_hooks.py` are byte-identical to the base | Surgical Changes |
| 15 | Same hygiene as T268: only 5.1-safe syntax, `-LiteralPath`/.NET I/O only, argument arrays for native calls, no `Remove-Item -Recurse` on a path that may be a junction (use T268's `Remove-HarnessPath`), no BOM and no CRLF in written files, pure ASCII source. The static test from T268 covers the new files | PowerShell 5.1 and data safety |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Install from kit commit A, then a kit commit B that edits file X, adds Y and deletes Z; Update | X replaced (untouched), Y added, Z removed, lock lists X,Y not Z | Docker pwsh smoke |
| 2 | Same, but the user edited X before Update and B changed X | X kept, `X.kit-new` written (default under `-Yes`), a line names it | Docker pwsh smoke |
| 3 | Same, user edited Z (which B deletes) | Z kept and named | Docker pwsh smoke |
| 4 | A project settings.json already in exec form | After Update still exec form, one entry per kit hook, user hook kept | Docker pwsh smoke |
| 5 | Second Update with no change | No change at all (hash of the whole tree identical) | Docker pwsh smoke |
| 6 | A forced failure mid-update (read-only destination) | Old lock intact, user file intact, message names the step | Docker pwsh smoke |
| 7 | Update with the replace step neutered (mutation) | Success Criterion 1 test goes red | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_setup_ps1_static.py tests/test_setup_ps1_pwsh.py tests/test_update_ps1_pwsh.py tests/test_windows_ci_workflow.py -q && python3 -m pytest .claude/hooks/tests tests -q
```

`tests/test_update_ps1_pwsh.py` uses the same Docker harness as T268's test (reuse its helpers; the image is already pulled and pinned by digest; no new pull, no new mounts beyond T268's). It also runs `setup.sh`/`update.sh` on a twin project to compare lock parity where AC 8 says so.

---

## Approach

**Pattern reference**: `lib/harness-update.sh` (the port target), `lib/harness.ps1` and `setup.ps1` (T268: structure, naming, backup and removal helpers), `tests/test_setup_ps1_pwsh.py` (the Docker harness).

**Vital slice**: Update (AC 1-9, 11-12), Reinstall removals (AC 10), the converter re-run (AC 6), canon copy refresh (AC 7). The interactive per-file prompt is the lowest-value part: implement the safe default first (AC 5), then the prompt.
**Cut list**: as under Out of scope.

Linux pwsh cannot prove junctions, CRLF or `core.symlinks=false`; say so in the Evidence, and rely on the CI scenario (AC 13) for Windows, unverified until the first PR.

Write the tests first (red), then the code. Keep the shell as the oracle: where AC 8 says parity, run the shell on a twin and compare.

---

## Edge Case Checklist

- [ ] The user deleted a kit file: Update does not resurrect it silently if the shell does not (read `process_one_file`)
- [ ] The project moved folders (a junction's absolute target is stale): Update re-creates the junction or says so
- [ ] A kit file that became a directory or the reverse
- [ ] Case-only renames on a case-insensitive file system
- [ ] A locked file during replace (antivirus): fail with the file named, old lock kept
- [ ] The update log file absent on first update
- [ ] `-Yes` with no TTY never blocks on `Read-Host`
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `tests/test_docs_match_installer.py` for "update.sh" claims and installer file lists

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `update.ps1` | New thin alias |
| `lib/harness-update.ps1` | New: the update functions |
| `setup.ps1` | Update action wired in, plan screen, dot-source the new library |
| `lib/harness.ps1` | Only if a shared helper is needed; keep T268's behaviour |
| `tests/test_update_ps1_pwsh.py` | New Docker pwsh tests |
| `tests/windows/smoke-install.ps1` (or `smoke-update.ps1`) | Update scenario |
| `.github/workflows/windows.yml`, `tests/test_windows_ci_workflow.py` | The update step and its shape test |
| `tests/test_setup_ps1_static.py` | Cover the new files |
| Pre-existing pin tests | Grep `tests/` and `.claude/hooks/tests/` for installer file lists, the workflow step list and `setup.ps1` text pins; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/*.sh`, `lib/merge-settings.py`, `lib/windows_hooks.py` | Fixed behaviour |
| `.claude/hooks/*` | Not this task |
| `docs/windows-support-plan.md`, `memory/`, `PROJECT_KANBAN.md` | Supervisor |

---

## Test Plan

Docker-pwsh smoke scenarios 1-6 (with a second local kit commit as the "new version"), the mutation control, the static test on the new files, the workflow shape test, the full Python suites. Windows-only behaviour is covered by the CI scenario, unverified until the first PR.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Lint passes
