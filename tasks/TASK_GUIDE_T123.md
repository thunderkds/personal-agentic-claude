# TASK_GUIDE — T123: Install pytest for the CI menu-suite dependency
**Date**: 2026-09-23
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`.
2. Read `memory/MEMORY.md`.
3. Read this file completely.
4. Read `agents/common-infrastructure.md`.
5. Apply the C1 process from the role guide.

## Requirement (Pillar 1 — Adapt the requirement)

The CI workflow reaches `tests/test_cli_and_project_menus.sh`, whose SC8/D9 case
executes `python3 -m pytest tests/test_docs_match_installer.py`. The Ubuntu runner
does not install pytest, so the suite fails with `No module named pytest` even though
it passes in the development environment.

**Restated intent:**
> CI installs the dependency required by every command already run by its shell
> suites, and the complete existing workflow passes in a fresh Ubuntu-like
> environment.

**Out of scope:**

- Wiring all repository Python tests into CI; that is a separate follow-up.
- Changing the menu suite or its assertions.
- Changing application or installer behavior.

### Requirement Fidelity Gate

- [x] Restated intent matches the registered T123 requirement.
- [x] Acceptance criteria are limited to the missing CI dependency and workflow health.
- [x] The full Python-suite coverage question is explicitly out of scope.

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|---|---|
| 1 | The CI dependency-install step installs the Python package providing `python3 -m pytest` on `ubuntu-latest`. | CI has the dependency its existing shell suite invokes |
| 2 | `bash tests/test_cli_and_project_menus.sh` passes when pytest is available. | The previously failing CI step succeeds |
| 3 | The remaining CI shell suites and drift guard remain wired and pass. | No regression in the existing workflow |
| 4 | The workflow still runs zero standalone pytest suite; the broader Python coverage gap is not silently expanded into this task. | Scope boundary |

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|---|---|---|
| 1 | Fresh Ubuntu package environment | `python3 -m pytest --version` succeeds after workflow install | container replay or equivalent |
| 2 | Repository checkout with pytest installed | menu suite exits 0 and reports 24 passed, 0 failed | automated shell suite |
| 3 | Repository checkout | all workflow shell suites and `tests/test_ci_wires_shell_suites.py` pass | automated verification |
| 4 | `.github/workflows/ci.yml` | no standalone `pytest` run was added | static scope check |

### Verification Command (exact, runnable)

```bash
python3 -m pytest --version
bash tests/test_cli_and_project_menus.sh
for suite in tests/*.sh; do
  case "$suite" in
    tests/test_shellcheck_clean.sh) continue ;;
    *) bash "$suite" || exit 1 ;;
  esac
done
python3 tests/test_ci_wires_shell_suites.py
sh scripts/validate.sh
```

### Evidence

> Fill at Stage 4/5 in `tasks/TASK_REVIEW_T123.md`; do not pre-forge user-run evidence.

## Approach

Add `python3-pytest` to the existing `apt-get install` command in
`.github/workflows/ci.yml`, preserving the single dependency-install step. Verify
the exact previously masked shell suite, then replay all later workflow commands.

**Cut list:** standalone execution of the repository's approximately 854 Python
tests, dependency pinning, and changes to test code.

## Files to Change (Predicted)

- `.github/workflows/ci.yml`
- `tests/test_ci_wires_shell_suites.py`

## Files Must NOT Touch

- `tests/test_cli_and_project_menus.sh` — existing test is the consumer.
- `PROJECT_KANBAN.md` — Supervisor-owned tracking file; its T123 row already exists.
- `memory/MEMORY.md` — preserve the user's uncommitted handoff edits.

## Completion Checklist

- [ ] CI dependency added.
- [ ] Targeted menu suite passes with pytest available.
- [ ] Full existing workflow command sequence passes or environmental blockers are recorded.
- [ ] Scope check confirms no standalone pytest suite was added.
- [ ] Review evidence recorded in `tasks/TASK_REVIEW_T123.md`.
