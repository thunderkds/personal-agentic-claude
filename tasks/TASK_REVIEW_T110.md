# TASK_REVIEW — T110: Update delivers `CLAUDE.md`, through the same edit-safe rule as every other file

> Sibling of `tasks/TASK_GUIDE_T110.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_update_claude_md.sh` — SC1(AC1), SC2(AC2), SC3(AC3), SC4(AC4), SC5(AC5,AC6), SC6(AC5,AC6), M1(AC7 mutation). `bash tests/test_update_claude_md.sh` → `----- summary: 23 passed, 0 failed -----`, exit 0 |
| Verification command run | ☑ pass | All 5 guide commands run directly (exit codes read, never piped through `tail`): `test_update_claude_md.sh` → 23/23 pass, exit 0; `test_update.sh` → 31/31 pass, exit 0; `test_setup.sh` → 18/18 pass, exit 0; `test_install_update_smoke.sh` → 9/9 pass, exit 0; `shellcheck -x setup.sh update.sh` → exit 0, no output |
| Negative cases hold | ☑ pass | SC3 (edited `CLAUDE.md` + upstream change → exit 2, edit kept, upstream marker absent), SC6 (unrecognized heading → exit 2, byte-unchanged), M1 (mutant that hardcodes greenfield resolution reproduces SC2's failure — proves SC2 is load-bearing, not vacuous) |
| verify | ☐ pass / ☐ fail / ☐ N/A | *(left for the Supervisor/user — `/verify`)* |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Touched only `setup.sh` (`write_harness_lock`), `update.sh` (`process_files`→`process_one_file` refactor + new `resolve_claude_md_source`/`process_claude_md`/`write_new_lock` signature), `tests/test_update_claude_md.sh` (new), `.github/workflows/ci.yml` (+1 step), `RUNBOOK.md` (D1), `site/index.html` (D2). `MANIFEST`, `CLAUDE.md`/`CLAUDE_LEGACY.md` content, `.claude/settings.json` handling, and `lib/harness-fetch.sh` left untouched per guide's "Files Must NOT Touch" |
| Full smoke suite still green (no regression) | ☑ pass | `test_update.sh` 31/31, `test_setup.sh` 18/18, `test_install_update_smoke.sh` 9/9 — all pre-existing cases pass unmodified; drift guard (`python3 tests/test_ci_wires_shell_suites.py`) 4/4 pass after wiring the new CI step |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☑ pass | D1 `RUNBOOK.md:192` now reads: *"`update.sh` (T110) delivers `CLAUDE.md` from the same source (`CLAUDE.md` or `CLAUDE_LEGACY.md`) the project was installed with, recorded as `claude_md_source` in `.claude/harness-lock.json`. It overwrites only when the project's `CLAUDE.md` is unedited since install; an edited `CLAUDE.md` goes through the same conflict prompt (`[o]/[s]/[v]`) as any other file"* — remediation cell updated to match. D2 `site/index.html` `#update-flow` now reads: *"It re-fetches the framework fresh, then for every `MANIFEST` file — plus `CLAUDE.md` — compares your project's current copy against the content hash recorded at the last install/update"* and adds: *"`CLAUDE.md` is delivered from the same source the project was installed with — a brownfield/existing project keeps receiving `CLAUDE_LEGACY.md`'s rules, never the greenfield `CLAUDE.md` — recorded per project in `.claude/harness-lock.json`."* Command lines at `:264-268` left untouched (T114) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Upstream clone
changed `CLAUDE.md`, `.claude/settings.json` and `skills/tdd/SKILL.md`; installed project then ran
`update.sh </dev/null`:

```
exit=0
skill: UPDATED
CLAUDE.md: NOT updated
settings.json: NOT updated
```

**BEFORE (Common-Infrastructure-Agent re-probe, 2026-09-12T15:13:22Z, `main` `992e293`, before any
implementation commit)**. Two independent scratch-repo runs, each against its own local
`SUPERVISOR_REPO=file://...` clone of this repo, upstream mutated (skill + both `CLAUDE.md` +
`CLAUDE_LEGACY.md`) and committed, then `update.sh </dev/null`:

Greenfield (new-project, plain pipe, no pty needed — mode defaults to `1`):
```
$ SUPERVISOR_REPO="file://.../upstream" bash setup.sh </dev/null   # install, unedited
[info] CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
$ # upstream: append MARKER-GREEN-BEFORE to CLAUDE.md, MARKER-LEGACY-BEFORE to CLAUDE_LEGACY.md,
$ #           append to skills/tdd/SKILL.md; git commit
$ SUPERVISOR_REPO="file://.../upstream" bash update.sh </dev/null
[info] Update complete. Re-recorded ./.claude/harness-lock.json
exit=0
$ grep -c MARKER-GREEN-BEFORE CLAUDE.md            → 0   (CLAUDE.md: NOT updated)
$ grep -c '# marker' skills/tdd/SKILL.md           → 1   (skill: UPDATED)
```

Brownfield (existing/legacy project, real prompt driven through a pty, `script -qec` with answers
`2` then Enter — the mode menu, then the packs menu):
```
$ printf '2\n\n' | script -qec "SUPERVISOR_REPO=file://.../upstream2 bash setup.sh" typescript
[info] CLAUDE source: CLAUDE_LEGACY.md | lock: .claude/harness-lock.json
$ head -1 CLAUDE.md
# CLAUDE LEGACY SUPERVISOR - Operating Protocol
$ # upstream2 (fresh clone, mutated AFTER this install so it measures a real update):
$ #           append MARKER-GREEN-B2 to CLAUDE.md, MARKER-LEGACY-B2 to CLAUDE_LEGACY.md,
$ #           append to skills/tdd/SKILL.md; git commit
$ SUPERVISOR_REPO="file://.../upstream2" bash update.sh </dev/null
[info] Update complete. Re-recorded ./.claude/harness-lock.json
exit=0
$ grep -c MARKER-LEGACY-B2 CLAUDE.md               → 0   (CLAUDE.md: NOT updated — legacy marker)
$ grep -c '# marker' skills/tdd/SKILL.md           → 1   (skill: UPDATED)
```

Both runs confirm the guide's restated defect: `update.sh` never touches `CLAUDE.md` for either
install source, while MANIFEST-listed files (the skill) update normally. Matches the Supervisor's
2026-09-12 `8115bc9` probe recorded above — reproduced independently on `992e293` immediately before
the first implementation commit.

**AFTER (Common-Infrastructure-Agent, 2026-09-12, post-change, this branch's `setup.sh`/`update.sh`)**.
Same two-run structure, against local upstream clones of this branch:

Greenfield:
```
$ SUPERVISOR_REPO="file://.../upstream" bash setup.sh </dev/null
$ head -1 CLAUDE.md → # Claude Project Supervisor Guidelines
$ grep claude_md_source .claude/harness-lock.json → "claude_md_source": "CLAUDE.md",
$ # upstream: append MARKER-GREEN-AFTER to CLAUDE.md and MARKER-LEGACY-AFTER to
$ #           CLAUDE_LEGACY.md; git commit
$ SUPERVISOR_REPO="file://.../upstream" bash update.sh </dev/null
[info] Update complete. Re-recorded ./.claude/harness-lock.json
update_exit=0
$ grep -c MARKER-GREEN-AFTER CLAUDE.md          → 1   (CLAUDE.md: UPDATED)
```

Brownfield (pty, answers `2` then Enter):
```
$ printf '2\n\n' | script -qec "SUPERVISOR_REPO=file://.../upstream2 bash setup.sh" typescript
$ head -1 CLAUDE.md → # CLAUDE LEGACY SUPERVISOR - Operating Protocol
$ # upstream2 (fresh clone): append MARKER-LEGACY-AFTER-B to CLAUDE_LEGACY.md and
$ #           MARKER-GREEN-AFTER-B to CLAUDE.md; git commit
$ SUPERVISOR_REPO="file://.../upstream2" bash update.sh </dev/null
[info] Update complete. Re-recorded ./.claude/harness-lock.json
update_exit=0
$ grep -c MARKER-LEGACY-AFTER-B CLAUDE.md       → 1   (legacy marker landed)
$ grep -c MARKER-GREEN-AFTER-B CLAUDE.md        → 0   (greenfield marker never appears)
```

**DELTA**: `update.sh` now delivers current `CLAUDE.md`/`CLAUDE_LEGACY.md` rule changes to an
already-installed project — from the same source it was installed with — instead of silently
freezing that file at its install-time content forever.

**WITNESS**: Common-Infrastructure-Agent (T110), 2026-09-12, run in scratch git repos per the
guide's BEFORE/AFTER probe protocol (`SUPERVISOR_REPO=file://...` local clones; brownfield driven
through a pty via `script -qec`).
