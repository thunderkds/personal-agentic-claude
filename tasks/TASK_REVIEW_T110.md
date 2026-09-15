# TASK_REVIEW — T110: Update delivers `CLAUDE.md`, through the same edit-safe rule as every other file

> Sibling of `tasks/TASK_GUIDE_T110.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_update_claude_md.sh` — SC1(AC1), SC2(AC2), SC3(AC3), SC4(AC4), SC5(AC5,AC6), SC6(AC5,AC6), SC7(AC4, Stage-4 P1), SC8(Stage-4 P2), M1/M2/M3 mutations. Round 2: `bash tests/test_update_claude_md.sh` → `----- summary: 35 passed, 0 failed -----`, exit 0 |
| Verification command run | ☑ pass | Round 2, all commands run directly (exit codes read, never piped through `tail`): `test_update_claude_md.sh` → 35/35 pass, exit 0; `test_update.sh` → 31/31 pass, exit 0; `test_setup.sh` → 18/18 pass, exit 0; `test_install_update_smoke.sh` → 9/9 pass, exit 0; `python3 tests/test_ci_wires_shell_suites.py` → 4/4 pass, exit 0; `docker run --rm -v "$PWD:/mnt" -w /mnt koalaman/shellcheck:stable -x setup.sh update.sh` → exit 0, no output (see shellcheck row below for full transcript incl. the test-file-only info notes) |
| Negative cases hold | ☑ pass | SC3 (edited `CLAUDE.md` + upstream change → exit 2, edit kept, upstream marker absent), SC6 (unrecognized heading → exit 2, byte-unchanged), SC8 (untrusted lock value rejected, stderr warns, marker never lands), M1/M2/M3 (each mutant reproduces the failure of the SC it targets, proving none of SC2/SC7/SC8 is vacuous) |
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

---

### BEFORE (round 2) — Common-Infrastructure-Agent, 2026-09-14T10:22Z, `fix/t110-update-claude-md` `9319d09`, before any round-2 implementation commit

Scratch repos under `$SCRATCH/t110r2` (`SCRATCH` = the session scratchpad dir); upstream is a local
`file://` clone of this branch at `9319d09`.

**(i) Brownfield, user edited `CLAUDE.md` line 1, upstream `CLAUDE_LEGACY.md` changed, `o` via pty**

```
$ printf '2\n\n' | script -qec "SUPERVISOR_REPO=file://.../upstream1 bash setup.sh" /dev/null
[info]  CLAUDE source: CLAUDE_LEGACY.md | lock: .claude/harness-lock.json
$ git add -A && git commit -m install
$ sed -i '1s/.*/# USER EDITED FIRST LINE (round2 BEFORE)/' CLAUDE.md
$ head -1 CLAUDE.md → # USER EDITED FIRST LINE (round2 BEFORE)
$ # upstream1: echo MARKER-LEGACY-R2-BEFORE >> CLAUDE_LEGACY.md; git commit
$ printf 'o\n' | script -qec "SUPERVISOR_REPO=file://.../upstream1 bash update.sh" /dev/null
[warn]  conflict: 'CLAUDE.md' has local changes since install
[info]  diff (current vs upstream) for CLAUDE.md:
--- ./CLAUDE.md
+++ /tmp/harness-fetch.vZJTZ3/CLAUDE_LEGACY.md
@@ -1,4 +1,4 @@
-# USER EDITED FIRST LINE (round2 BEFORE)
+# CLAUDE LEGACY SUPERVISOR - Operating Protocol
...
+MARKER-LEGACY-R2-BEFORE
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: [info]  overwrote: CLAUDE.md
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
update_exit=0
$ tail -1 CLAUDE.md → MARKER-LEGACY-R2-BEFORE
$ head -1 CLAUDE.md → # CLAUDE LEGACY SUPERVISOR - Operating Protocol
$ grep claude_md_source .claude/harness-lock.json → "claude_md_source": "CLAUDE_LEGACY.md",
```

Round-1 code already honours the recorded source correctly here (the conflict diff was taken
against `CLAUDE_LEGACY.md`, not the greenfield `CLAUDE.md`, and `[o]` installed the legacy
content) — this confirms the Stage-4 finding is about **missing test coverage** (no SC exercises
this divergent brownfield-plus-edit path), not a live behavioral bug in this exact case.

**(ii) Lock's `claude_md_source` points outside the allowlist, at a real file in the scratch dir**

```
$ printf '1\n\n' | script -qec "SUPERVISOR_REPO=file://.../upstream1 bash setup.sh" /dev/null
$ head -1 CLAUDE.md → # Claude Project Supervisor Guidelines
$ echo MARKER-EVIL-FILE-CONTENT-R2 > $SCRATCH/t110r2/evil.md
$ # rewrote .claude/harness-lock.json: "claude_md_source": "../claude-1000/.../scratchpad/t110r2/evil.md"
$ SUPERVISOR_REPO="file://.../upstream1" bash update.sh </dev/null
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
update_exit=0
$ cat CLAUDE.md → MARKER-EVIL-FILE-CONTENT-R2
$ grep claude_md_source .claude/harness-lock.json → "claude_md_source": "../claude-1000/.../scratchpad/t110r2/evil.md",
```

Confirms: an arbitrary relative path in the committed lock is used unvalidated as a source path —
`../claude-1000/.../evil.md` resolves one level above `$HARNESS_TEMP_DIR` (itself always exactly
`/tmp/harness-fetch.XXXXXX`) straight into a file outside the fetched harness, and its content
silently lands in the project's `CLAUDE.md` with no prompt (no local edit → hash matched → fast
overwrite path).

**WITNESS (round 2)**: Common-Infrastructure-Agent (T110), 2026-09-14, scratch git repos, before
any round-2 implementation commit.

---

## Round 2 (Stage 4 findings)

| Finding | Closed by |
|---------|-----------|
| **P1** — no test proves the recorded `claude_md_source` is honoured | New **SC7**: brownfield install, edit `CLAUDE.md` line 1 (changes its hash, triggers the *existing* per-file conflict prompt — independent of heading inference), bump upstream `CLAUDE_LEGACY.md`, answer `[o]` via a plain pipe (this prompt is not `[ -t 0 ]`-gated). Asserts the fresh `CLAUDE_LEGACY.md` marker lands, the greenfield content never appears, and the lock still records `CLAUDE_LEGACY.md`. New mutation **M2** disables the `if [ -n "$_recorded" ]` branch entirely (forces heading inference always) and confirms SC7 then fails: the edited first line matches no known heading, so the run falls into the heading-conflict path and diffs against greenfield `CLAUDE.md` instead — proving SC7 actually exercises the record-honouring code, not a vacuous pass. BEFORE (round 2) probe above shows round-1 code already behaved correctly here; the gap was coverage, not behavior. |
| **P2** — recorded value used unvalidated as a path | `resolve_claude_md_source` (`update.sh`) now allowlists the recorded `claude_md_source` to exactly `CLAUDE.md` or `CLAUDE_LEGACY.md`; any other value is rejected with `log_warn "recorded claude_md_source '<value>' is not an allowed value (CLAUDE.md or CLAUDE_LEGACY.md) — falling back to heading inference."` and falls through to the existing heading-inference/conflict path — no path stripping or normalization, per the Supervisor's decision. New **SC8**: lock's `claude_md_source` rewritten (via `python3` string replace) to a relative path that escapes `$HARNESS_TEMP_DIR` (always exactly one level under `$TMPDIR`, per `lib/harness-fetch.sh:91`) into a real scratch file holding a unique marker. Asserts the marker never reaches `CLAUDE.md`, stderr carries the rejection warning, and the rewritten lock ends up with an allowlisted (or absent) value. New mutation **M3** collapses the allowlist's `CLAUDE.md|CLAUDE_LEGACY.md)` case arm into `*)` (accept-anything, round-1 shape) and confirms SC8 then fails: the untrusted file's content lands in `CLAUDE.md` unmodified. BEFORE (round 2) probe above reproduces the live exploit pre-fix. |
| **P2** — shellcheck evidence | Real `docker run --rm -v "$PWD:/mnt" -w /mnt koalaman/shellcheck:stable -x setup.sh update.sh` output pasted below (round 2), not just a claimed result. |
| **P3** (optional) — fieldless lock + user-deleted `CLAUDE.md` falls back to greenfield even for brownfield | **Skipped.** Guide marks this optional ("do it only if a few lines") and out of scope: the guide's own Edge Case Checklist already documents the current behavior ("`CLAUDE.md` deleted by the user → treated like any missing file … from the recorded source") as verified-correct for the *recorded-source* path; the residual gap is only the *fieldless-lock-and-deleted-file* double-unknown case, which the Requirement's "Out of scope" list (no cross-mode heuristics beyond heading inference) and the Supervisor's guide already treat as acceptable degraded behavior, not a defect. Left as-is to avoid inventing new inference logic beyond what SC5/AC5 specify. |

### Round 2 shellcheck transcript

```
$ docker run --rm -v "$PWD:/mnt" -w /mnt koalaman/shellcheck:stable -x setup.sh update.sh
$ echo "SHELLCHECK_EXIT=$?"
SHELLCHECK_EXIT=0
```

(No stdout/stderr output at all — clean run, exit 0. `tests/test_update_claude_md.sh` was also
checked; it emits pre-existing-style SC2015/SC2016 *info*-level notes shared with the SC1–SC6
patterns already in the file before round 2 — not part of the guide's exact verification command,
left as-is for consistency with the surrounding test code.)

---

## Round 2 — Stage 4 re-review (Supervisor, 2026-09-15)

Verdict: **P0 0 / P1 0 / P2 0 / P3 0.** All three carried round-1 findings closed, each confirmed by
the Supervisor's *own* mutants applied to `update.sh` in `wt-t110` (not the agent's M2/M3 harness),
with the file restored from a backup copy afterwards and `git status` clean.

| Carried finding | Supervisor's independent check | Result |
|---|---|---|
| P1 — recorded `claude_md_source` untested | Forced `_recorded=""` in `resolve_claude_md_source` | `FAIL: SC7: CLAUDE.md picked up greenfield content — recorded source was not honoured` (+2 more SC7 failures). Round 1's mutant passed SC1–SC6; SC7 catches it. |
| P2 — recorded source used unvalidated as a path | Collapsed the allowlist's `CLAUDE.md\|CLAUDE_LEGACY.md)` arm to `*)` | `FAIL: SC8: the untrusted lock value's file content landed in CLAUDE.md` (+ missing-warning + lock-drift failures). The exploit reproduces without the fix. |
| P2 — shellcheck output not pasted | `docker run --rm -v "$PWD:/mnt" -w /mnt koalaman/shellcheck:stable -x setup.sh update.sh` | No output, exit 0 — independently reproduced. |

Structural note (checked, not a finding): a rejected value falls through to heading inference, which
can only yield an allowlisted name or `conflict`, so it can never reach `FINAL_CLAUDE_MD_SOURCE` and
never survives into the rewritten lock. SC8's third assertion holds for that reason, not by luck.

Security-review of the round-2 delta: **no findings at or above the bar.** The only non-test change
*is* the remediation for round 1's path-traversal candidate (scored 6, carried as a P2); that
candidate is superseded. Considered and deliberately not filed: `log_warn` echoes the rejected value
to stderr unescaped — log-content spoofing from a file the user already owns, below the P3 gate.

Supervisor re-ran, in `wt-t110`:

```
tests/test_update_claude_md.sh      ----- summary: 35 passed, 0 failed -----
tests/test_update.sh                ----- summary: 31 passed, 0 failed -----
tests/test_setup.sh                 ----- summary: 18 passed, 0 failed -----
tests/test_install_update_smoke.sh  9 passed, 0 failed
tests/test_ci_wires_shell_suites.py ----- summary: 4 passed, 0 failed -----   (T109 drift guard sees the new suite as CI-wired)
tests/test_shellcheck_clean.sh      cannot self-verify locally (no shellcheck binary on PATH); covered by the containerised run above and by CI's own gate
```

Docs D1/D2 confirmed landed: `RUNBOOK.md:192` no longer says "by design", and `site/index.html`
`#update-flow` names `CLAUDE.md` and the brownfield `CLAUDE_LEGACY.md` rule.

HTML report: `reports/code-review_fix-t110-update-claude-md_20260915T094750.html` (Risk 0%, Quality 95%, Effort 0%).

**Next**: user runs `/verify`, then PR `fix/t110-update-claude-md` → `feat/easy-kit-one-command`.
