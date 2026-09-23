# TASK_GUIDE — T122: CI goes green — `validate.sh` reads MANIFEST's `!` exclusions as paths
**Date**: 2026-09-23
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`
**Branch**: worktree off `main`; merges back into `main`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (path — read it in full)
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Apply the C1 process from the Complexity matrix in your role guide

---

## Requirement (Pillar 1 — Adapt the requirement)

**Every CI run on `main` has failed since 2026-09-22.** One step fails:
`Validate framework integrity` → `sh scripts/validate.sh`.

Supervisor probe, 2026-09-23, `main`:

```
== MANIFEST entries resolve on disk ==
  [ok]   agents
  [ok]   skills
  [ok]   .claude/hooks
  [ok]   templates
  [ok]   docs/claude-md
  [ok]   AGENTS.md
  [ok]   .cursor/rules
  [FAIL] MANIFEST entry not found: !.claude/hooks/tests
validate.sh: FAIL
EXIT=1
```

Every other check in the script passes. T113 (`48824ba`) introduced MANIFEST exclusion syntax and
added `!.claude/hooks/tests` so the kit's own tests stop shipping to installed projects.
`scripts/validate.sh:31` filters comments and blank lines out of MANIFEST but **not** exclusions:

```sh
line=$(printf '%s' "$line" | tr -d '\r' | awk '$0 !~ /^[[:space:]]*(#|$)/ { print $1 }')
```

so it tries to resolve a file literally named `!.claude/hooks/tests`.

**Restated intent**:
> `validate.sh` understands that a MANIFEST line beginning `!` declares an exclusion, not a path,
> and CI is green again. Every other MANIFEST reader is checked for the same gap in the same pass.

**This is a syntax extension that reached some of its consumers and not others** — that, not the one
missing character, is the defect. The Supervisor has already surveyed the readers; **confirm this
survey rather than trusting it**, and say in the review whether you agree:

| Reader | Filter today | Verdict |
|---|---|---|
| `lib/harness-fetch.sh:285` (`harness_manifest_path`) | `(#\|$\|!)` | correct — excludes `!` |
| `lib/harness-fetch.sh:292` (`harness_manifest_exclusions`) | `$1 ~ /^![^[:space:]]/` | correct — consumes `!` |
| `setup.sh:837` (plan "Copies in" line) | `grep -v '^[[:space:]]*[#!]'` | correct — excludes `!` |
| `scripts/validate.sh:31` | `(#\|$)` | **the live defect** |
| `lib/harness-fetch.sh:310` (`harness_manifest_dest`) | `(#\|$)` | **latent — investigate, do not assume** |

`harness_manifest_dest` takes one line at a time. It looks reachable only through callers that
already dropped `!` lines, which would make it safe today and a trap tomorrow. **Establish which it
is by reading its call sites**, then either fix it with the same `case` or record in the review why
it needs none. Do not "fix" it blind — an unnecessary edit here is scope creep.

**Out of scope, register as a separate row if you think it is needed**: wiring pytest into CI.
`grep -c pytest .github/workflows/ci.yml` is **0** — none of the ~853 Python tests has ever gated a
merge (the open T109 follow-up). That is a real gap and it is *why* a Supervisor-introduced break in
`site/index.html` on 2026-09-23 was invisible to CI while this shell exit code was not. **It is a
scope increase, not a bug fix — do not fold it into this task.**

**Requirement Refs**: none in `PRD.md`.

### Requirement Fidelity Gate
- [x] Restated intent confirmed (Supervisor; probe output pasted above, reproduced locally)
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: none. **Do not** branch off or merge into `feat/t116-pack-catalog` — T116 is finished
and awaiting merge; this task lands first so T116's CI run is the first honest signal in two days.

**Entry point**: `.github/workflows/ci.yml` step `Validate framework integrity`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `sh scripts/validate.sh` exits **0** on a clean checkout of this branch | "CI is green again" |
| 2 | Its MANIFEST section reports **no** entry beginning `!`, and still reports every non-excluded entry `[ok]` — the fix skips exclusions, it does not skip the check | "understands … not a path" |
| 3 | A MANIFEST entry that genuinely does not exist still `[FAIL]`s and still exits non-zero | the gate must keep gating |
| 4 | An automated test covers AC1–AC3 and is wired into `.github/workflows/ci.yml`; `tests/test_ci_wires_shell_suites.py` stays green | no gate without a test |
| 5 | Every MANIFEST reader in the Supervisor's table is confirmed or corrected, with `harness_manifest_dest`'s verdict stated and justified in `tasks/TASK_REVIEW_T122.md` | "checked for the same gap" |
| 6 | Mutation control M1: revert the `!` handling in `validate.sh` → the AC1/AC2 test fails. M2: delete a real MANIFEST path from disk → the AC3 test fails | observed failing |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | clean branch checkout | `sh scripts/validate.sh`; `echo $?` → `0` | automated |
| 2 | MANIFEST with `!.claude/hooks/tests` | no `[FAIL]` line mentioning `!`; `agents`, `skills`, `.claude/hooks`, `templates`, `docs/claude-md`, `AGENTS.md`, `.cursor/rules` each `[ok]` | automated |
| 3 | MANIFEST with an added line `no-such-path-xyz` | `[FAIL]` and exit non-zero | automated |
| 4 | MANIFEST with `!no-such-path-xyz` | exit 0 — an exclusion naming a non-existent path is not an error | automated |

### Verification Command (exact, runnable)

```bash
sh scripts/validate.sh; echo "exit=$?"
bash tests/test_manifest_exclusions.sh
python3 tests/test_ci_wires_shell_suites.py
bash tests/test_setup.sh
bash tests/test_update.sh
bash tests/test_harness_projection.sh
shellcheck -x scripts/validate.sh lib/harness-fetch.sh
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T122.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T122.md`. BEFORE is the probe output above, re-run and timestamped by you
> on this branch before your first implementation commit.

---

## Approach

**Pattern reference**: `lib/harness-fetch.sh:285` — the same filter, already correct. Match its shape
rather than inventing a new one; `awk '$0 !~ /^[[:space:]]*(#|$|!)/'` is the one-token difference.

**Vital slice**: the `validate.sh` filter plus a test that pins all four SC rows.

**Cut list** (deliberately not built):
- Wiring pytest into CI — named above, out of scope, its own row.
- Any refactor of MANIFEST parsing into a shared helper. Four readers with four small filters is
  fine; extracting a library here is speculation and touches three files that are working.
- Teaching `validate.sh` to *verify* exclusions (that the excluded path exists, or that it is
  actually excluded from an install). That is a different, larger check.

---

## Documentation to Update

| # | Doc | What it must say |
|---|-----|------------------|
| D1 | `MANIFEST` header comment | The `!` prefix is documented where the syntax lives, naming that validators must skip these lines — the comment block already explains `agents`/`packs`; add exclusions to it if absent |

Historical records (`tasks/`, `memory/`, RUNBOOK's release log) are never rewritten.

---

## Files You May Touch
- `scripts/validate.sh`
- `lib/harness-fetch.sh` — only if AC5 concludes `harness_manifest_dest` needs the fix
- `tests/test_manifest_exclusions.sh` (new)
- `.github/workflows/ci.yml`
- `MANIFEST` (comment only — **never** change which paths are listed or excluded)
- `tasks/TASK_REVIEW_T122.md`

## Files You May NOT Touch
- Any `setup.sh` / `update.sh` install logic
- `PROJECT_KANBAN.md` (the Supervisor owns the board)
- Anything under `packs/`, `skills/`, `agents/`
