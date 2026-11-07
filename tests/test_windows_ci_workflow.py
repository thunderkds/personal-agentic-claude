"""T263 — the Windows CI job and the shared `posix_only` skip marker.

The workflow itself runs on GitHub only; these tests check its shape (AC 1, 2, 5, 6), that every
`posix_only` mark carries a written reason (AC 3), and that the skip is `win32`-only (AC 4).
The mutation controls prove the shape check can fail.

Run with: python3 -m pytest tests/test_windows_ci_workflow.py -q
"""
import ast
import glob
import importlib.util
import os
import re

import pytest

yaml = pytest.importorskip("yaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "windows.yml")
CONFTEST = os.path.join(ROOT, "conftest.py")
TEST_GLOBS = ("tests/*.py", ".claude/hooks/tests/*.py")

SHA_REF = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
TAG_REF = re.compile(r"^[\w.-]+/[\w.-]+@v\d+\.\d+\.\d+$")
GATE_JOB = "Repo gate (Git Bash)"  # T277: scripts/validate.sh under Git Bash, a job of its own


def _text():
    with open(WORKFLOW, encoding="utf-8") as f:
        return f.read()


def _gate_problems(data):
    """T277 AC 6: the job `Repo gate (Git Bash)` runs `bash scripts/validate.sh`, and may not be red-tolerant."""
    gates = [j for j in (data.get("jobs") or {}).values() if j.get("name") == GATE_JOB]
    if len(gates) != 1:
        return [f"needs exactly one job named {GATE_JOB!r}"]
    job, problems = gates[0], []
    steps = job.get("steps") or []
    if job.get("runs-on") != "windows-latest":
        problems.append("the repo gate must run on windows-latest")
    if "continue-on-error" in job or any("continue-on-error" in s for s in steps):
        problems.append("the repo gate must not set continue-on-error")
    if not any(s.get("shell") == "bash" and re.search(r"^bash scripts/validate\.sh\s*$", str(s.get("run", "")))
               for s in steps):
        problems.append("a step must run `bash scripts/validate.sh` with shell: bash")
    for s in steps:
        if "uses" in s and not (SHA_REF.match(s["uses"]) or TAG_REF.match(s["uses"])):
            problems.append(f"{s['uses']} is not pinned to a full SHA or an exact version tag")
        if str(s.get("uses", "")).startswith("actions/checkout@") \
                and s.get("with", {}).get("persist-credentials") is not False:
            problems.append("the repo gate checkout must set persist-credentials: false")
    if not any(str(s.get("uses", "")).startswith("actions/checkout@") for s in steps):
        problems.append("the repo gate needs actions/checkout")
    return problems


def _problems(text):
    """Every way the workflow text departs from AC 1, 2, 5 and 6. An empty list means it conforms."""
    data = yaml.safe_load(text)
    problems = []
    on = data.get("on", data.get(True))  # YAML 1.1 reads the bare key `on` as True
    if not isinstance(on, dict) or not {"push", "pull_request"} <= set(on):
        problems.append("must run on push and pull_request")
    if isinstance(on, dict) and "pull_request_target" in on:
        problems.append("must not use pull_request_target (it runs with secrets on fork code)")
    if data.get("permissions") != {"contents": "read"}:
        problems.append("permissions must be exactly contents: read")
    if re.search(r"\bsecrets\.", text):
        problems.append("must not use secrets")
    jobs = data.get("jobs") or {}
    win = [j for j in jobs.values() if j.get("runs-on") == "windows-latest"]
    if not win:
        problems.append("needs a job on runs-on: windows-latest")
        return problems
    steps = win[0].get("steps") or []
    uses = [s["uses"] for s in steps if "uses" in s]
    for action in ("actions/checkout", "actions/setup-python"):
        if not any(u.startswith(action + "@") for u in uses):
            problems.append(f"needs {action}")
    for u in uses:
        if not (SHA_REF.match(u) or TAG_REF.match(u)):
            problems.append(f"{u} is not pinned to a full SHA or an exact version tag")
    for s in steps:
        if str(s.get("uses", "")).startswith("actions/checkout@") \
                and s.get("with", {}).get("persist-credentials") is not False:
            problems.append("the checkout step must set persist-credentials: false")
    py = [s for s in steps if str(s.get("uses", "")).startswith("actions/setup-python@")]
    if not py or py[0].get("with", {}).get("python-version") != "3.12":
        problems.append('setup-python must pin python-version: "3.12" (a string)')
    runs = " ".join(str(s.get("run", "")) for s in steps)
    for needle in ("python -I -m pytest", "tests/", ".claude/hooks/tests/"):
        if needle not in runs:
            problems.append(f"a run step must contain {needle!r}")
    shells = {str(s.get("shell")) for s in steps if "tests/windows/smoke-install.ps1" in str(s.get("run", ""))}
    if not {"powershell", "pwsh"} <= shells:
        problems.append("the setup.ps1 smoke (T268) must run under shell: powershell (5.1) and shell: pwsh")
    shells = {str(s.get("shell")) for s in steps if "tests/windows/smoke-update.ps1" in str(s.get("run", ""))}
    if not {"powershell", "pwsh"} <= shells:
        problems.append("the update.ps1 smoke (T271) must run under shell: powershell (5.1) and shell: pwsh")
    problems += _gate_problems(data)
    head = text.split("\nname:", 1)[0]
    if "required" not in head or "status checks" not in head.lower():
        problems.append("header comment must say how to make the job required")
    return problems


def test_workflow_matches_the_acceptance_criteria():
    assert _problems(_text()) == []


@pytest.mark.parametrize("old,new", [
    ("windows-latest", "ubuntu-latest"),
    ("11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2", "v4"),
    ("a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0", "main"),
    ("contents: read", "contents: write"),
    ('"3.12"', '"3"'),
    ("python -I -m pytest", "python -m pytest"),
    ("  pull_request:\n", ""),
    ("  pull_request:\n", "  pull_request_target:\n"),
    ("persist-credentials: false", "persist-credentials: true"),
    ("run: python -I -m pip install pytest pyyaml", "run: echo ${{ secrets.TOKEN }}"),
    ("shell: powershell\n", "shell: pwsh\n"),
    ("run: ./tests/windows/smoke-install.ps1", "run: echo skipped"),
    ("run: ./tests/windows/smoke-update.ps1", "run: echo skipped"),
    ("name: Repo gate (Git Bash)", "name: Repo gate"),
    ("name: Repo gate (Git Bash)\n    runs-on: windows-latest", "name: Repo gate (Git Bash)\n    runs-on: ubuntu-latest"),
    ("name: Repo gate (Git Bash)\n", "name: Repo gate (Git Bash)\n    continue-on-error: true\n"),
    ("        run: bash scripts/validate.sh\n", "        run: bash scripts/validate.sh\n        continue-on-error: true\n"),
    ("run: bash scripts/validate.sh", "run: echo skipped"),
    ("shell: bash\n", "shell: pwsh\n"),
    ("shell: powershell\n        env:\n          SUPERVISOR_REPO: ${{ github.workspace }}\n        run: ./tests/windows/smoke-update.ps1",
     "shell: pwsh\n        env:\n          SUPERVISOR_REPO: ${{ github.workspace }}\n        run: ./tests/windows/smoke-update.ps1"),
])
def test_mutation_control_a_broken_workflow_is_caught(old, new):
    text = _text()
    assert old in text, old
    mutated = text.replace(old, new, 1)
    assert mutated != text
    assert _problems(mutated), f"{old!r} -> {new!r} went unnoticed"


def test_the_repo_gate_job_is_valid_yaml_and_separate_from_the_python_tests_job():
    """T277 AC 6, 7: the file parses, and the gate is its own job, so its result shows on its own."""
    data = yaml.safe_load(_text())
    jobs = data["jobs"]
    by_name = {j.get("name"): k for k, j in jobs.items()}
    assert GATE_JOB in by_name and "Python tests (Windows)" in by_name
    assert by_name[GATE_JOB] != by_name["Python tests (Windows)"]
    assert not any("validate.sh" in str(s.get("run", "")) for s in jobs[by_name["Python tests (Windows)"]]["steps"])


def _posix_only_marks():
    """(file, line, reason-or-None) for every `posix_only` decorator or `pytestmark` in the suites."""
    found = []
    for pattern in TEST_GLOBS:
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            if os.path.abspath(path) == os.path.abspath(__file__):
                continue  # this file builds bad marks on purpose, to test the refusal
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                        and node.func.attr == "posix_only":
                    arg = node.args[0] if node.args else None
                    reason = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
                    found.append((os.path.relpath(path, ROOT), node.lineno, reason))
    return found


def test_every_posix_only_mark_has_its_own_written_reason():
    marks = _posix_only_marks()
    assert marks, "no posix_only mark found: the Windows job would run every POSIX-only test"
    bad = [(p, n) for p, n, r in marks if not r or len(r.strip()) < 20]
    assert bad == [], f"posix_only without a written reason: {bad}"


def _load_conftest():
    spec = importlib.util.spec_from_file_location("t263_root_conftest", CONFTEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Item:
    def __init__(self, *marks):
        self.nodeid = "tests/test_x.py::test_x"
        self._marks = marks
        self.added = []

    def iter_markers(self, name=None):
        return [m for m in self._marks if m.name == name]

    def add_marker(self, mark):
        self.added.append(mark)


def test_the_skip_is_win32_only(monkeypatch):
    conf = _load_conftest()
    mark = pytest.mark.posix_only("creates a symlink, which needs Developer Mode on Windows").mark

    monkeypatch.setattr(conf.sys, "platform", "win32")
    on_windows = _Item(mark)
    conf.pytest_collection_modifyitems(None, [on_windows])
    assert [m.name for m in (x.mark for x in on_windows.added)] == ["skip"]
    assert "Developer Mode" in on_windows.added[0].mark.kwargs["reason"]

    for platform in ("linux", "darwin"):
        monkeypatch.setattr(conf.sys, "platform", platform)
        elsewhere = _Item(mark)
        conf.pytest_collection_modifyitems(None, [elsewhere])
        assert elsewhere.added == [], f"posix_only must not skip on {platform}"


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_mutation_control_a_mark_without_a_reason_is_refused(monkeypatch, platform):
    conf = _load_conftest()
    monkeypatch.setattr(conf.sys, "platform", platform)
    with pytest.raises(pytest.UsageError):
        conf.pytest_collection_modifyitems(None, [_Item(pytest.mark.posix_only().mark)])
    with pytest.raises(pytest.UsageError):
        conf.pytest_collection_modifyitems(None, [_Item(pytest.mark.posix_only("  ").mark)])
