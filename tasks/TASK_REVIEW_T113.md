# TASK_REVIEW — T113: Update removes what upstream stopped shipping (unless edited), and kit tests stop shipping

> Sibling of `tasks/TASK_GUIDE_T113.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_update_removals.sh` — `30 passed, 0 failed` (SC1–SC10; SC1/2/3/5 = AC1/2/3/5, SC4+SC6 = AC4/AC6, SC7+SC10 = the T112 no-`.bak` criterion, SC8 = safety abort, SC9 = `..` lock key) |
| Verification command run | ☑ pass (with 1 flagged item) | all installer suites green (below); `shellcheck -x setup.sh update.sh scripts/validate.sh scripts/smoke-install.sh tests/test_harness_projection.sh` rc=0 (shellcheck-py in a scratch venv; none on PATH). pytest: `7 failed, 842 passed` vs `6 failed, 843 passed` on the base — the 6 are pre-existing (memory budget x5, README line cap); the +1 is `test_ci_wires_shell_suites` naming `test_update_removals.sh`: **needs a `ci.yml` step, which I may not edit — Supervisor approval needed** |
| Negative cases hold | ☑ pass | edited kept (SC2, SC5b), user-added kept (SC3), missing-upstream-path abort rc=2 (SC8), `..` key ignored (SC9). Mutations observed RED then reverted: M1 (`rm -f` → `:`) → sc1/sc3/sc5 FAIL; M2 (drop `!` line from MANIFEST) → sc6 FAIL; M2' (`harness_is_excluded` never matches) → sc4/sc5/sc10 FAIL; M3 (drop `..` guard) → sc9 FAIL; M4 (backup before exclusion check) → sc7/sc10 FAIL |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4, 2026-09-21: code-review scoped to `main...fix/t113-update-removals` (update.sh, lib/harness-fetch.sh, setup.sh, MANIFEST + tests). Independent re-run: test_update_removals 30/0, test_harness_projection 41/0, test_install_update_smoke 9/0. Findings: P0 0, P1 0, P2 1 (a lock path now a dir/symlink is warned as "you edited it" — wrong wording, file still kept), P3 2 (held excluded files in an unregistered temp dir if killed mid-install; `manifest_root_of` first-match with nested MANIFEST paths). security-review: no finding ≥8/10 — `..`/absolute keys rejected, hash-match + non-symlink leaf required before `rm`; intermediate-dir symlink noted as defence-in-depth (3/10, needs attacker-known file hash). CI edit approved: `ci.yml` step for test_update_removals.sh added (T111/T112 precedent). |
| Full smoke suite still green (no regression) | ☑ pass | the eight fixture-MANIFEST suites **run, not read**: test_harness_fetch 9/0, test_harness_projection 41/0, test_install_backups 13/0, test_settings_merge 40/0, test_setup 18/0, test_t098_harness_presence 20/0, test_update_claude_md 35/0, test_update 31/0; plus test_install_update_smoke 9/0, test_update_removals 30/0 |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☑ pass | D1 `site/index.html`: "**No longer shipped** — a file the kit dropped is removed if you never edited it, and kept (and named) if you did." D2 `RUNBOOK.md` health check gains `test ! -d .claude/hooks/tests &&`. D3 `MANIFEST` header: "── Exclusions (T113) … A line `!<path>` keeps <path> — and everything under it — out of the project …" |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit):

Upstream `git rm -r skills/optimize`, then update:

```
[warn]  upstream no longer ships 'skills/optimize/SKILL.md' — leaving your local copy untouched (not deleted).
optimize skill still present (orphan, still loaded by Claude)
```

Fresh install footprint:

```
     47 .claude/hooks
total files: 119
1.4M	.
tests count: 36        (.claude/hooks/tests/)
```

**BEFORE (implementer, live, 2026-09-21T03:59:54Z, `fix/t113-update-removals` @ `334ea79`, no implementation commit yet)**:
scratch project installed via `setup.sh` from a `file://` clone of this worktree; upstream then `git rm -r skills/optimize`; `update.sh`:

```
tests count: 36
[warn]  upstream no longer ships 'skills/optimize/SKILL.md' — leaving your local copy untouched (not deleted).
update rc=0
optimize skill still present (orphan)
```

**AFTER** (implementer, live, 2026-09-21T04:08:44Z, commit `48824ba`; same probes, upstream = `file://` clone of the committed code):

```
setup rc=0
tests count: 0  (dir present: no)
total files: 81
[info]  removed 'skills/optimize' — upstream no longer ships it and you never edited it.
update rc=0
optimize skill removed
```

AC7: `python3 -m pytest .claude/hooks/tests/ --collect-only -q` → `795 tests collected`; `git diff 334ea79 HEAD -- .claude/hooks` is empty, so the collected set is unchanged.

**DELTA**: a fresh install drops from 119 files (36 of them the kit's tests) to 81 with none, and an update now removes the unedited skill the kit dropped instead of warning and leaving it loaded.

**WITNESS**: Common-Infrastructure-Agent (implementer), 2026-09-21. Not independent — Stage 4 must re-run.

**Guide points the implementer had to decide (flag for Supervisor)**:
1. `tests/test_harness_projection.sh` AC9 asserted the *old* ADR-0001 behaviour ("canon keeps the upstream-removed skill") — not in the guide's Files to Change; flipped to the ADR-0002 behaviour. `tests/test_install_update_smoke.sh` AC1 awk got the `!` skip, as the guide directed.
2. Exclusion *inside* a copied directory (`!.claude/hooks/tests` under `.claude/hooks`) needed a staging path in `harness_copy_manifest` so the project's own tests dir stays in place (not swept into `.claude/hooks.bak`); the ordinary path is byte-for-byte unchanged, so test_install_backups' M1 mutation still lands.
3. Safety abort: empty fresh list or a whole MANIFEST path missing upstream → no deletions, `[error]`, lock entries kept, update exits 2.
