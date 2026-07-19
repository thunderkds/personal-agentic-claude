# TASK_GUIDE — T038: Fix setup.sh's piped-install (curl | sh) bootstrap failure
**Date**: 2026-07-19
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `docs/adr/0001-direct-repo-install-no-central-clone.md`
6. C2 — apply brainstorm/decompose/verify depth per the Complexity matrix in `.claude/agents/general-agent-template.md`. Hard-Stop Gate 2 floor: this touches core install "restructure" territory even though the change is localized.
7. Read `memory/codebase-map.md` for structural orientation before touching `setup.sh`

---

## Requirement (Pillar 1 — Adapt the requirement)

User reported a live failure running the documented Quick Start install command (`curl -fsSL .../setup.sh | sh`) against a real new project:

```
[error] Required library not found: /path/to/some/project/lib/harness-fetch.sh. Run setup.sh from a full checkout of the harness repo.
curl: (23) Failure writing output to destination
```

Root-caused and reproduced locally (`cat setup.sh | sh` in a scratch git repo → identical error). Root cause: `SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)` resolves correctly only when `setup.sh` is a real file on disk. When piped via `curl | sh`, `$0` is not a meaningful file path (typically resolves to the shell itself or the current directory), so `dirname -- "$0"` silently falls back to the current working directory — the user's own project, not anywhere `lib/harness-fetch.sh` exists. Since T031 split the fetch/copy logic out of `setup.sh` into a separately-sourced `lib/harness-fetch.sh`, the **primary documented install method** (`curl | sh`, step 1 of README's Quick Start, unchanged and re-verified as correct prose in T035) has been fundamentally broken for every new user — not caught by any of T031-T037's testing, all of which used real local checkouts (`bash "$SETUP"` with a real file path, never a piped invocation).

The secondary `curl: (23)` error is a downstream side effect: `setup.sh` exits on the missing-library error while `curl` is still streaming bytes into the pipe, breaking the pipe.

**Restated intent** (per user-approved direction, `AskUserQuestion` this session):
> When `lib/harness-fetch.sh` isn't found co-located with `setup.sh` (piped-install signature), bootstrap by doing a raw `git clone --depth 1` of the harness repo into a temp directory, then invoke the freshly-cloned `setup.sh` from that real location with the original arguments passed through, then clean up the bootstrap temp directory and exit with the real invocation's exit code. Reuse the real install logic entirely — do not duplicate `lib/harness-fetch.sh`'s fetch/copy logic inline.

**Out of scope**:
- Does not touch `update.sh` — confirmed via `README.md` grep that `update.sh` is never documented as a piped/curl invocation, only ever run from an existing full checkout (`sh /path/to/personal-agentic-claude/update.sh`); it has no exposure to this bug.
- Does not touch `lib/harness-fetch.sh` itself — the bootstrap logic is a small, self-contained addition to `setup.sh` only, using plain `git clone` directly (not `harness_fetch`, since the library containing that function is exactly what's missing at this point in execution).
- Does not attempt to avoid the double-fetch (bootstrap clone, then the real setup.sh's own fetch-into-temp-and-copy flow fetches again) — accepted as a one-time, per-install cost; matches this repo's own ADR-0001 precedent of favoring simplicity over fetch efficiency.

**Requirement Refs**: ADR-0001 (this bug is a gap in that decision's implementation, not a reversal of it — the direct-repo model itself is sound; only the piped-bootstrap entry point was missed); README.md Quick Start section (T035) documents `curl | sh` as the primary install command — this task makes that documented command actually work.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user-approved `AskUserQuestion` direction ("Self re-exec via fresh clone")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (no new terms; reuses existing bootstrap/fetch vocabulary)
- [x] Every Acceptance Criterion below traces to the requirement
- [x] Requirement Refs confirmed: ADR-0001 gap, README.md Quick Start command

---

## Dependencies & Reachability

**Depends on**: `None` — `lib/harness-fetch.sh` (T031) and `setup.sh` (T032) are correct and unchanged in their non-piped path; this task only adds a bootstrap branch that runs before the existing logic when the co-located library is missing.
**Entry point**: `README.md`'s Quick Start section — `curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh` is the literal, grep-able command this task makes work.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `cat setup.sh \| sh` (or equivalent piped invocation) run inside a scratch git-initialized directory with no local harness checkout present succeeds (exit 0) and produces the same installed artifacts as a normal checkout-based install | "bootstrap by cloning... invoke the freshly-cloned setup.sh" |
| 2 | The bootstrap path uses a plain `git clone --depth 1`, not `lib/harness-fetch.sh`'s functions (which aren't sourced yet at that point) | "using plain git clone directly" |
| 3 | Original arguments (e.g. `--pack=mobile`) are passed through to the re-invoked real `setup.sh` unchanged | "original arguments passed through" |
| 4 | The bootstrap temp directory is removed after the real `setup.sh` invocation completes, regardless of its exit code | "clean up the bootstrap temp directory" |
| 5 | The exit code of the piped invocation matches the real re-invoked `setup.sh`'s exit code (success stays success, failure stays failure — not silently swallowed) | "exit with the real invocation's exit code" |
| 6 | A normal (non-piped) invocation from a real checkout is completely unaffected — `lib/harness-fetch.sh` found co-located skips the bootstrap branch entirely | Out of scope — do not regress the already-correct non-piped path |
| 7 | Negative: bootstrap clone failure (bad network/URL) exits non-zero with a clear error, does not proceed to a broken re-invocation | verification isn't a rubber stamp |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Scratch git repo, `cat setup.sh \| sh </dev/null` (local file, simulating piped stdin) | Exit 0, all artifacts present, no `lib/harness-fetch.sh not found` error | automated shell run |
| 2 | Same, but via the REAL `curl -fsSL <raw-github-url> \| sh` against the actually-pushed `main` branch | Exit 0, same artifacts | manual live run (real network, real GitHub) |
| 3 | Normal non-piped `sh /real/checkout/path/setup.sh` | Behavior unchanged from before this task | regression check against existing `tests/test_setup.sh` |
| 4 | Bootstrap clone given a deliberately broken `SUPERVISOR_REPO` | Exits non-zero, clear error, bootstrap dir removed | manual negative-case run |
| 5 | Two consecutive piped runs | No leftover `/tmp/harness-bootstrap.*` directories after either | manual `ls /tmp` check |

### Verification Command (exact, runnable)

```bash
# Simulated piped install (local file, no lib/ co-located):
TARGET=$(mktemp -d) && cd "$TARGET" && git init -q && cat /path/to/setup.sh | sh </dev/null; echo "exit=$?"
# Regression:
bash tests/test_setup.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [broken bootstrap URL still fails correctly] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [run the REAL curl \| sh command against the real pushed repo, not just a local simulation] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | ☐ N/A | pure backend/tooling task |
| **UI: Design-system compliance** | ☐ N/A | pure backend/tooling task |
| **UI: Responsiveness** | ☐ N/A | pure backend/tooling task |

---

## Approach

Insert a bootstrap branch immediately where `setup.sh` currently checks for `$HARNESS_LIB` and exits on failure. If not found: resolve `SUPERVISOR_REPO` the same way `resolve_repo_url()` normally would (honor an existing override, else build from `GITHUB_USERNAME`, default `thunderkds`) — but inline, since `resolve_repo_url` may itself live after this point in the script or depend on nothing problematic; check exact placement during implementation. `git clone --depth 1` that URL into a fresh `mktemp -d`. On clone failure: clear error, `rm -rf`, exit non-zero. On success: invoke `sh "$BOOTSTRAP_DIR/setup.sh" "$@"` (passing through all original arguments) as a **regular subprocess call, not `exec`** — using `exec` would replace the current process and skip any cleanup path, leaking the bootstrap directory. Capture its exit code, `rm -rf "$BOOTSTRAP_DIR"`, then `exit` with that captured code.

---

## Edge Case Checklist

- [ ] Confirm `set -e` (already active in `setup.sh`) doesn't cause the script to exit before the bootstrap branch gets a chance to capture the re-invoked exit code and clean up — may need explicit `|| true` / capturing pattern rather than relying on `set -e`'s propagation
- [ ] The re-invoked `setup.sh` will itself do a SECOND full fetch (its own normal `harness_fetch`-based flow) — confirm this is accepted as a one-time cost, not silently broken by any state the bootstrap clone left behind
- [ ] `$@` must be passed through with correct quoting (`"$@"`, not `$*` or unquoted `$@`) so flags with spaces or multiple `--pack=` values survive re-invocation intact
- [ ] Piped `curl | sh` provides no meaningful stdin for interactive prompts even in the bootstrap-detection branch — confirm the bootstrap path doesn't accidentally try to read from stdin before the real re-invoked script gets a chance to (which already correctly defaults to non-interactive/greenfield when stdin isn't a TTY)
- [ ] Test with a `--pack=<name>` flag through the piped path specifically, not just the flagless default case, per Acceptance Criterion 3

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh` | Add the piped-install bootstrap branch |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `update.sh` | Confirmed out of scope — never piped in documented usage |
| `lib/harness-fetch.sh` | Bootstrap uses plain `git clone` directly; the library isn't sourced yet at the point this branch runs |
| `README.md` | Already correctly documents `curl \| sh` as the install method (T035) — this task makes that existing documentation true, not change it |

---

## Test Plan

(1) Simulated piped install via `cat setup.sh | sh` in a scratch dir — proves the bootstrap branch itself works without depending on network timing/availability for the *test infrastructure*, only for the bootstrap clone's own target. (2) A REAL `curl | sh` run against the actually-pushed `main` branch — the authoritative end-to-end proof, since the whole bug only manifests via genuine piping (the local-file simulation is a strong proxy but not 100% identical to a real curl pipe's `$0`/stdin semantics). (3) Full regression via `tests/test_setup.sh` to confirm the non-piped path is untouched.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes — `shellcheck` unavailable locally (ongoing gap); substitute `sh -n` / `dash -n` + note explicitly
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — MUST include a real `curl | sh` run against the real pushed repo, not just local simulation
- [ ] Supervisor notified: task ready for Stage 4 review
