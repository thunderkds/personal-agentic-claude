# TASK_GUIDE — T263: Native Windows support, step 2 — Windows CI job for the Python tests
**Date**: 2026-11-06
**Complexity Level**: C2
**Risk Level**: Medium
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
6. C2: read `memory/codebase-map.md`
7. Read `docs/windows-support-plan.md` (this task is T-W2 of it)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: native Windows support for the kit ("by pass the wsl, focus on the native window"; "start as parallel if can be").

**Restated intent**:
> Add a GitHub Actions job on `windows-latest` that runs the kit's Python tests, so every later Windows change (T264..T268) is checked on a real Windows runner. POSIX-only tests are skipped with a written reason, never deleted.

**Out of scope**:
- Fixing the failures the job reports (T264..T267 do that). The job may start red.
- The `setup.ps1` smoke install (T268 adds it).
- Making the job a required status check in GitHub settings (the user does that; this task writes the instruction).
- Shell tests (`tests/*.sh`): not run on Windows.

**Requirement Refs**: `docs/windows-support-plan.md` T-W2. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: `None` (the plan lists T262, but the CI job needs no part of the ADR; they run in parallel)

**Entry point**: `.github/workflows/windows.yml`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.github/workflows/windows.yml` is valid YAML, has a job on `runs-on: windows-latest`, uses `actions/checkout` and `actions/setup-python` with Python 3.12 (exact version pinned), and runs `python -I -m pytest` on `tests/` and `.claude/hooks/tests/` | "runs the Python tests" |
| 2 | The job runs on `push` and `pull_request`, with `permissions: contents: read` and no secrets | Risk Medium: least privilege |
| 3 | Each POSIX-only Python test is skipped on Windows through one shared marker (`pytest.mark.skipif(sys.platform == "win32", reason="…")` in a `conftest.py` helper), each with its own reason text | "skipped with a written reason" |
| 4 | Negative: on Linux the same tests still run (the skip is `win32`-only); the Linux test count does not drop | Surgical Changes |
| 5 | A short instruction in the workflow's header comment says how to make the job required in branch protection | Out of scope note |
| 6 | The three `.github/` action references are pinned to a full commit SHA or an exact version tag, not `@main` or `@v4` floating | supply chain |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The workflow file | Parses with `yaml.safe_load`; has the keys of AC 1, 2 and 6 | automated test |
| 2 | A test file listed as POSIX-only | Carries the shared skip marker with a non-empty reason | automated test |
| 3 | Full Linux run | Same number of passed tests as before this task | `pytest` count before / after |
| 4 | Workflow with `runs-on: ubuntu-latest` | The test of row 1 goes red | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_windows_ci_workflow.py -q
```

The job itself runs on GitHub only. Record the pass count before and after in the Evidence row. State in the Evidence that the Windows run is unverified until the first push.

---

## Approach

**Pattern reference**: `scripts/ci_verify_done_tasks.py` and any existing workflow under `.github/` (check first; if none, use the minimal shape).

**Vital slice**: one workflow, one shared skip helper, and the list of POSIX-only tests found by running `grep -ln "import pty\|fcntl\|os.killpg\|/bin/sh\|bash" tests/*.py .claude/hooks/tests/*.py`.
**Cut list**: matrix over several Python versions; caching; coverage upload; a macOS job.

Build the skip list from evidence: run the grep above, then mark only the tests that fail for a POSIX-only reason. Do not guess.

---

## Edge Case Checklist

- [ ] Windows path separators in test assertions: list failures, mark them, do not edit the code under test (that is T264..T267)
- [ ] `python -I` is used so a planted file in the cwd cannot shadow a stdlib module
- [ ] A test that runs a `.sh` file is skipped, not failed
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/` and `docs/claude-md/` for "CI" and a workflow list

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.github/workflows/windows.yml` | New |
| `tests/conftest.py` (or the existing one) | Shared `posix_only` marker |
| POSIX-only test files found by the grep | Add the marker, with a reason |
| `tests/test_windows_ci_workflow.py` | New test with the mutation control |
| Pre-existing pin tests | Grep `tests/` and `.claude/hooks/tests/` for a pin on `.github/` contents, a root-listing or the test count; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py`, `scripts/*.py`, `setup.sh`, `lib/*.sh` | Code fixes belong to T264..T268 |
| `.claude/settings.json` | T266 |

---

## Test Plan

The new test loads the workflow with `yaml.safe_load` and asserts the keys; a second test scans the POSIX-only list and asserts the marker has a reason. The mutation control rewrites `runs-on` in a temp copy and expects the test to fail.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk; the workflow runs repo code on CI)
- [ ] Lint passes
