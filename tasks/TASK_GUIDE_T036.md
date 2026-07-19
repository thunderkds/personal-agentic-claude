# TASK_GUIDE — T036: Fix scripts/smoke-install.sh for the direct-repo install model
**Date**: 2026-07-19
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `docs/adr/0001-direct-repo-install-no-central-clone.md` — the decision this script must reflect
6. C1 — apply brainstorm/decompose/verify depth per the Complexity matrix in `.claude/agents/general-agent-template.md`; single-file focused fix so lightweight process is appropriate

---

## Requirement (Pillar 1 — Adapt the requirement)

`.github/workflows/ci.yml` runs `sh scripts/smoke-install.sh` on every push to `main` and every PR. Confirmed live (2026-07-19): this script fails immediately — `[error] Required library not found: .../lib/harness-fetch.sh` — because it was written for the pre-ADR-0001 symlink/central-clone model and was never updated when T031/T032/T033 rewrote `setup.sh`. It (a) copies only `setup.sh` itself into a throwaway target directory, not `lib/harness-fetch.sh` which the new `setup.sh` sources relative to its own location, and (b) sets `SUPERVISOR_PATH` pointing at the local checkout, but the new `setup.sh` no longer reads install content from `SUPERVISOR_PATH` at all (that variable is now packs-only) — the new script always fetches fresh via `git clone` (`SUPERVISOR_REPO`/`GITHUB_USERNAME`). This means CI has been failing on every push since T031-T033 merged (2026-07-17), silently, because nobody checked Actions status.

**Restated intent**:
> Rewrite `scripts/smoke-install.sh` to actually exercise the current `setup.sh`: point `SUPERVISOR_REPO` at the local checkout via a `file://` URL (the same pattern already proven in `tests/test_setup.sh` and `tests/test_install_update_smoke.sh`) so `setup.sh` clones from the real local repo state with no network dependency, then assert the same artifacts as before land correctly.

**Out of scope**:
- Does not touch `setup.sh`, `update.sh`, or `lib/harness-fetch.sh` — those are correct; this script's assumptions are what's stale.
- Does not add update.sh coverage to this script — that's already covered by `tests/test_update.sh` and `tests/test_install_update_smoke.sh`; this script's job is specifically the CI-wired install smoke check.
- Does not change `.github/workflows/ci.yml` itself unless the fixed script needs a different invocation (e.g., a working-directory or env-var change) — check whether the fix requires a workflow change; if it does, make the minimal one needed and call it out explicitly, don't leave it undone.

**Requirement Refs**: ADR-0001 (this script directly encodes the old model's assumptions, contradicting the new Decision); no `PRD.md` FR — internal CI/tooling task, same precedent as T024/T026.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the live-reproduced failure (Supervisor, direct run: `sh scripts/smoke-install.sh` → `Required library not found`)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (no new terms; reuses `SUPERVISOR_REPO`/`file://` fixture pattern already established by T031-T034's own test suites)
- [x] Every Acceptance Criterion below traces to the requirement
- [x] Requirement Refs: ADR-0001 confirmed; N/A PRD precedent confirmed

---

## Dependencies & Reachability

**Depends on**: `None` — `setup.sh`/`update.sh` (T031-T033) are already merged and correct; this task only fixes the stale test harness around them.
**Entry point**: `.github/workflows/ci.yml` — the `Install smoke test` step invokes `sh scripts/smoke-install.sh` on every push/PR to `main`. This is the literal, grep-able consumer.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `sh scripts/smoke-install.sh` run from a full local checkout exits 0 | "actually exercise the current setup.sh" |
| 2 | The script fetches from the local checkout via `SUPERVISOR_REPO=file://$ROOT` (or equivalent), not by copying a single file or relying on `SUPERVISOR_PATH` for the core install | matches the real fetch mechanism (`lib/harness-fetch.sh`'s `git clone`) |
| 3 | All previously-asserted artifacts (`CLAUDE.md`, `.claude/agents`, `.claude/skills`, `.claude/hooks`, `templates`, `.claude/settings.json`, `memory/MEMORY.md` + 3 sibling files, `tasks`) are still asserted present after install | preserves existing test coverage, no silent scope reduction |
| 4 | The script still asserts greenfield `CLAUDE.md` content and that installed files are real (not symlinks) | preserves existing behavioral assertions |
| 5 | `shellcheck scripts/smoke-install.sh` has no new findings beyond what already existed (CI's own shellcheck step must stay green) | CI step 2 (`Shellcheck install scripts`) must not regress |
| 6 | Negative: if `setup.sh`'s fetch step were to fail (e.g. bad `SUPERVISOR_REPO`), the script must still exit non-zero and not report false success | verification isn't a rubber stamp |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Full local checkout, current `main` | `sh scripts/smoke-install.sh` exits 0, all `[ok]` lines, `smoke-install.sh: PASS` | automated shell run |
| 2 | Same, but with a deliberately-broken `SUPERVISOR_REPO` (e.g. nonexistent path) | Script exits non-zero, does not print `PASS` | manual negative-case run |

### Verification Command (exact, runnable)

```bash
sh scripts/validate.sh && sh scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `scripts/smoke-install.sh` itself (fixed, no new file) is the oracle — run live, not claimed. Confirmed reproducing the original failure first (`Required library not found: .../lib/harness-fetch.sh`), then confirmed the fix resolves it — pass |
| Verification command run | ☑ pass | `sh scripts/validate.sh && sh scripts/smoke-install.sh` — both exit 0: `validate.sh: PASS` (all MANIFEST/frontmatter/path checks), `smoke-install.sh: PASS` (all 15 artifact/behavior assertions `[ok]`) |
| Negative cases hold | ☑ pass | `SUPERVISOR_REPO="file:///nonexistent/path/xyz"` → `[error] Failed to clone ...`, exit=1, zero artifacts written to target — proves the script isn't a rubber stamp |
| verify | ☑ pass | Ran the exact CI invocation (`sh scripts/smoke-install.sh` from repo root) live — matches `.github/workflows/ci.yml`'s `Install smoke test` step exactly. Also independently re-ran all 4 existing shell test suites for regression: `test_setup.sh` 15/15, `test_update.sh` 22/22, `test_harness_fetch.sh` 9/9, `test_install_update_smoke.sh` 9/9 (79 total across all suites incl. 24 pytest) — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff isolated to `scripts/smoke-install.sh`; `setup.sh`/`update.sh`/`lib/harness-fetch.sh` read for context, not modified; `.github/workflows/ci.yml` needed no change (invocation `sh scripts/smoke-install.sh` from repo root is unchanged) |
| Full smoke suite still green (no regression) | ☑ pass | 79/79 across `.claude/hooks/tests/` (24) + `tests/test_setup.sh` (15) + `tests/test_update.sh` (22) + `tests/test_harness_fetch.sh` (9) + `tests/test_install_update_smoke.sh` (9), 0 failures |
| **UI: Visual regression** | ☐ N/A | pure CI/tooling task |
| **UI: Design-system compliance** | ☐ N/A | pure CI/tooling task |
| **UI: Responsiveness** | ☐ N/A | pure CI/tooling task |

---

## Approach

Model the fix on the exact fetch pattern already proven three times in this repo (`tests/test_setup.sh`, `tests/test_update.sh`, `tests/test_install_update_smoke.sh`): build/point at a local fixture, set `SUPERVISOR_REPO="file://$ROOT"` (or a throwaway fixture repo, matching whichever those suites use), run the real `setup.sh` non-interactively (`</dev/null`) from a scratch git-initialized target directory, then keep the existing artifact assertions. Since `$ROOT` here is a full checkout (unlike a purpose-built minimal fixture), a plain `git clone --depth 1 file://$ROOT` will pick up the *actual current repo state* — which is more realistic for a "does the real installer still work" CI gate than a synthetic fixture, and needs no new fixture-building code.

---

## Edge Case Checklist

- [ ] `setup.sh` refuses to run if invoked from inside a directory matching its own `$SCRIPT_DIR` heuristics — confirm the scratch `$TARGET` directory doesn't collide with `$ROOT` in a way that trips this
- [ ] CI's checkout is a shallow/full clone from GitHub Actions — confirm `file://$ROOT` works against a CI-checked-out working tree, not just a local dev machine's `.git`
- [ ] `--copy` flag: confirm whether it's still meaningful to pass in the fixed script (per T035's README fix, `--copy` is now a no-op for core resources) — if meaningless, drop it rather than keep a stale flag for its own sake
- [ ] Don't accidentally leave a real network dependency (a real GitHub URL) where a `file://` local fetch was intended — CI runners have network, but a spurious network call slows CI and adds flakiness for no reason

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/smoke-install.sh` | Rewrite fetch mechanism to match the current `setup.sh`/`lib/harness-fetch.sh` model |
| `.github/workflows/ci.yml` | Only if the fixed script needs a different invocation — check, don't assume |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/harness-fetch.sh` | Already correct (T031-T033); this task fixes the stale test around them |
| `tests/test_setup.sh`, `tests/test_update.sh`, `tests/test_install_update_smoke.sh` | Separate, already-correct test suites — do not duplicate their coverage here |

---

## Test Plan

The fixed `scripts/smoke-install.sh` run live (per Verification Command) is the test plan — this task fixes a test script, so the test script itself, once fixed and run successfully, is the evidence.

---

## Completion Checklist

- [x] Implementation done
- [x] Self-review: `Skill({ skill: "code-review" })` run — 1 P1 found and fixed (the "no central-clone" assertion was vacuous: `SUPERVISOR_PATH` was never set in the invocation, so the check trivially passed regardless of real behavior; fixed by pointing it at a sentinel path, mirroring `tests/test_setup.sh`'s `NO_CLONE` pattern). 0 P0, 0 P2, 1 P3 (noted, not applied — out of scope). Re-verified green after the fix.
- [x] Lint passes — `shellcheck` not available in this env (same gap as T031); substituted `sh -n` + `dash -n` syntax checks, both clean, noted explicitly per that precedent
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `Skill({ skill: "verify" })` run — confirmed CI's exact invocation now succeeds
- [ ] Supervisor notified: task ready for Stage 4 review
