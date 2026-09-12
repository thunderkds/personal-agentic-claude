"""
T109 — drift guard between the real tests/*.sh suites and the real
.github/workflows/ci.yml.

Both directions are checked at test time, never as a copied list of suite
names (a test that mirrors another file's list by copying it is a comment,
not a mechanism — memory/learnings.md, T105):

  1. every tests/*.sh file must be either wired as its own `run:` step in
     ci.yml, or named in EXCLUDED_SUITES below with a one-line reason a
     reviewer can check.
  2. every tests/*.sh path referenced by ci.yml must actually exist on disk.

Does not shell out to `grep` (this dev environment aliases it to ugrep,
which is not guaranteed in CI) — uses Python's own re module throughout.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CI_YML = os.path.join(ROOT, ".github", "workflows", "ci.yml")
TESTS_DIR = os.path.join(ROOT, "tests")

# Suites deliberately not wired as their own CI step, one reviewer-checkable
# reason each. Do not add an entry here to silence a suite that should be
# fixed or wired instead.
EXCLUDED_SUITES = {
    "test_shellcheck_clean.sh": (
        "mirrored pair with ci.yml's own 'Shellcheck install scripts' step "
        "(T105) — out of scope for T109, needs a shellcheck binary the lint "
        "step already installs, not a second one"
    ),
}


def _ci_yml_text():
    with open(CI_YML, encoding="utf-8") as f:
        return f.read()


def _real_test_suites():
    """Every tests/*.sh file that actually exists on disk right now."""
    return sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(TESTS_DIR, "*.sh"))
    )


_RUN_LINE_RE = re.compile(
    r"^\s*run:\s*(?:bash|sh)\s+tests/([A-Za-z0-9_.-]+\.sh)\s*$"
)


def _ci_referenced_suites(text):
    """Every tests/*.sh suite directly invoked by a ci.yml `run:` line —
    `run: bash tests/<name>.sh` or `run: sh tests/<name>.sh` (optional
    trailing whitespace) only. A mention inside another command (e.g. the
    shellcheck argument list), a comment, or a step name does not count."""
    wired = set()
    for line in text.splitlines():
        m = _RUN_LINE_RE.match(line)
        if m:
            wired.add(m.group(1))
    return sorted(wired)


def _ci_mentioned_suites(text):
    """Every tests/*.sh path mentioned anywhere in ci.yml, wired or not —
    used only to check that referenced paths actually exist on disk."""
    return sorted(set(re.findall(r"tests/([A-Za-z0-9_.-]+\.sh)", text)))


def test_every_real_suite_is_wired_or_excluded():
    text = _ci_yml_text()
    wired = set(_ci_referenced_suites(text))
    real = _real_test_suites()

    unaccounted = [
        name for name in real if name not in wired and name not in EXCLUDED_SUITES
    ]
    assert not unaccounted, (
        "tests/*.sh suite(s) neither run by ci.yml nor listed in "
        "EXCLUDED_SUITES with a reason: " + ", ".join(unaccounted)
    )


def test_every_ci_referenced_suite_exists():
    text = _ci_yml_text()
    referenced = _ci_mentioned_suites(text)
    real = set(_real_test_suites())

    missing = [name for name in referenced if name not in real]
    assert not missing, (
        "ci.yml references tests/*.sh path(s) that do not exist: "
        + ", ".join(missing)
    )


def test_ci_runs_the_drift_guard_itself():
    """Deleting the step that runs this guard must not silently disable it."""
    text = _ci_yml_text()
    self_check_re = re.compile(
        r"^\s*run:\s*python3\s+tests/test_ci_wires_shell_suites\.py\s*$",
        re.MULTILINE,
    )
    assert self_check_re.search(text), (
        "ci.yml has no run: step invoking "
        "'python3 tests/test_ci_wires_shell_suites.py' — the drift guard "
        "would never run in CI"
    )


def test_excluded_suites_still_exist_and_are_really_excluded():
    """An EXCLUDED_SUITES entry for a file that was deleted, or that ci.yml
    quietly started wiring anyway, is a stale exclusion — catch it rather
    than let it silently stop meaning anything."""
    text = _ci_yml_text()
    wired = set(_ci_referenced_suites(text))
    real = set(_real_test_suites())

    for name in EXCLUDED_SUITES:
        assert name in real, f"excluded suite '{name}' no longer exists on disk"
        assert name not in wired, (
            f"excluded suite '{name}' is now wired in ci.yml — "
            "remove it from EXCLUDED_SUITES"
        )


if __name__ == "__main__":
    _tests = [
        obj
        for name, obj in list(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    _failed = 0
    for _test in _tests:
        try:
            _test()
        except AssertionError as exc:
            _failed += 1
            print(f"FAIL: {_test.__name__}: {exc}")
        else:
            print(f"PASS: {_test.__name__}")
    print(f"----- summary: {len(_tests) - _failed} passed, {_failed} failed -----")
    raise SystemExit(1 if _failed else 0)
