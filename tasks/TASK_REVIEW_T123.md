# T123 Review — Install pytest for the CI menu-suite dependency

## Review status

**Local implementation:** ready for review  
**Published branch:** not pushed  
**GitHub CI run:** not yet observed

## Findings

No actionable findings in the local diff. The change installs `python3-pytest`
alongside the existing `shellcheck` package and adds a regression assertion to
the existing CI drift guard. The broader Python-suite wiring remains out of scope.

## Verification evidence

| Check | Result | Evidence |
|---|---|---|
| Targeted previously masked suite | PASS | `bash tests/test_cli_and_project_menus.sh` → `24 passed, 0 failed` |
| CI drift guard | PASS | `python3 -m pytest -q tests/test_ci_wires_shell_suites.py` → `5 passed` |
| Framework validation | PASS | `sh scripts/validate.sh` → `validate.sh: PASS` |
| Existing shell suites | PASS | All 16 suites under `tests/*.sh` except the shellcheck mirror passed; latest aggregate ended `30 passed, 0 failed` for the final suite and no suite returned non-zero |
| Shell syntax | PASS | `sh -n scripts/validate.sh setup.sh update.sh lib/harness-fetch.sh lib/harness-update.sh` |
| Diff formatting | PASS | `git diff --check` |
| Standalone pytest scope | PASS | No `run:` step invokes pytest; workflow only installs `python3-pytest` and runs the existing shell-suite drift guard |

## Supervisor Stage 4/5 evidence (2026-09-24)

**Container replay (SC1, SC3) — fresh `ubuntu:24.04`, every `run:` line of `ci.yml` executed in order
from a tarball of the working tree:**

```
/usr/bin/python3: No module named pytest          <- before step 1 (BEFORE)
STEP 1 rc=0 :: sudo apt-get update && sudo apt-get install -y shellcheck python3-pytest
STEP 2 rc=0 :: shellcheck -x setup.sh update.sh ...
STEP 3 rc=0 :: sh scripts/validate.sh
...
STEP 18 rc=0 :: bash tests/test_cli_and_project_menus.sh     <- the step that failed in CI
STEP 19 rc=0 :: bash tests/test_manifest_exclusions.sh
STEP 20 rc=0 :: python3 tests/test_ci_wires_shell_suites.py
pytest 7.4.4                                      <- after step 1 (AFTER)
```

All 20 steps rc=0, including 19–20 that CI had never reached.

**Control — same container, `python3-pytest` NOT installed:**

```
CONTROL menu suite rc=1
/usr/bin/python3: No module named pytest
23 passed, 1 failed
```

The fix is the cause, not coincidence.

**Mutation control on the new test** — removing `python3-pytest` from `ci.yml`:
`FAIL: test_ci_installs_pytest_for_shell_suite_dependency ... ----- summary: 4 passed, 1 failed -----`;
restored → `5 passed, 0 failed`. The runner collects `test_*` dynamically, so CI executes the new test.

**Stage 4 `code-review`: 0 P0 / 0 P1 / 0 P2 / 2 P3 (optional, not applied).**
P3a: step still named "Install shellcheck" though it now installs pytest. P3b: the new assertion is a
whole-file substring match, so a comment containing `python3-pytest` would satisfy it. Neither
affects correctness. `security-review`: not required (Risk Low).

## Remaining release evidence

The workflow must be pushed or run by the user so the actual `ubuntu-latest`
job can confirm package installation and the steps after the formerly failing
menu suite. This local evidence does not claim GitHub CI is green.
