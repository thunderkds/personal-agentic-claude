"""T274 - the `needs_symlinks` and `needs_bash` markers in the root `conftest.py`.

A Windows machine may lack a thing a test needs: the right to make a symlink, or a working `bash`
(System32 holds a WSL launcher stub that exists but fails). Each marker probes once per session and
skips the marked test with its written reason when the probe fails. An empty reason is a collection
error, like the T263 platform marker. The probes are patched here, so Linux proves the Windows behaviour.

Run with: python3 -m pytest tests/test_windows_markers.py -q
"""
import importlib.util
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONFTEST = ROOT / "conftest.py"
MARKERS = ("needs_symlinks", "needs_bash")
# The T263 marker, spelled in two parts: docs/windows-parity.md counts the lines that hold the whole word,
# and this file skips no test on Windows, so it must not get a row in that skip inventory.
PLATFORM_MARKER = "posix_" + "only"
EPERM_WINDOWS = 1314  # ERROR_PRIVILEGE_NOT_HELD: what os.symlink raises without Developer Mode


def _load_conftest():
    """A fresh copy of the root conftest, so each test starts with an empty probe cache."""
    spec = importlib.util.spec_from_file_location("t274_root_conftest", CONFTEST)
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

    @property
    def skip_reasons(self):
        return [m.mark.kwargs["reason"] for m in self.added if m.mark.name == "skip"]


def _mark(name, *args):
    return getattr(pytest.mark, name)(*args).mark


def _symlink_denied(monkeypatch):
    def deny(*args, **kwargs):
        raise OSError(EPERM_WINDOWS, "A required privilege is not held by the client")
    monkeypatch.setattr(os, "symlink", deny)


def _bash_result(monkeypatch, returncode=None, error=None):
    """Make `bash -c ...` return `returncode`, or raise `error`. Other commands run for real."""
    real = subprocess.run
    calls = []

    def fake(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "bash":
            calls.append(cmd)
            if error is not None:
                raise error
            return subprocess.CompletedProcess(cmd, returncode, b"", b"")
        return real(cmd, *args, **kwargs)
    monkeypatch.setattr(subprocess, "run", fake)
    return calls


# --- AC 1, 2: needs_symlinks ------------------------------------------------------------------

def test_symlinks_denied_skips_with_the_written_reason(monkeypatch):
    conf = _load_conftest()
    _symlink_denied(monkeypatch)
    item = _Item(_mark("needs_symlinks", "links the dotfiles skills into a target"))
    conf.pytest_collection_modifyitems(None, [item])
    assert len(item.skip_reasons) == 1
    assert "links the dotfiles skills into a target" in item.skip_reasons[0]


def _symlink_allowed(monkeypatch):
    """A machine that can make a symlink, whatever this machine can do (a Windows run without Developer Mode)."""
    monkeypatch.setattr(os, "symlink", lambda *args, **kwargs: None)


def test_symlinks_allowed_does_not_skip(monkeypatch):
    conf = _load_conftest()
    _symlink_allowed(monkeypatch)
    item = _Item(_mark("needs_symlinks", "links the dotfiles skills into a target"))
    conf.pytest_collection_modifyitems(None, [item])
    assert item.added == [], "a machine that can make a symlink must run the test"


def test_symlink_probe_leaves_no_temp_file(monkeypatch, tmp_path):
    conf = _load_conftest()
    monkeypatch.setattr(conf.tempfile, "tempdir", str(tmp_path))
    _symlink_allowed(monkeypatch)
    conf.pytest_collection_modifyitems(None, [_Item(_mark("needs_symlinks", "r"))])
    _symlink_denied(monkeypatch)
    conf._PROBE_CACHE.clear()
    conf.pytest_collection_modifyitems(None, [_Item(_mark("needs_symlinks", "r"))])
    assert list(tmp_path.iterdir()) == []


def test_symlink_probe_not_implemented_counts_as_denied(monkeypatch):
    conf = _load_conftest()

    def missing(*args, **kwargs):
        raise NotImplementedError("symlinks are not supported on this platform")
    monkeypatch.setattr(os, "symlink", missing)
    item = _Item(_mark("needs_symlinks", "r"))
    conf.pytest_collection_modifyitems(None, [item])
    assert len(item.skip_reasons) == 1


# --- AC 1, 2: needs_bash ----------------------------------------------------------------------

def test_bash_that_fails_skips_with_the_written_reason(monkeypatch):
    """The WSL launcher stub in System32 is found on PATH but exits non-zero: probe by running it."""
    conf = _load_conftest()
    calls = _bash_result(monkeypatch, returncode=1)
    item = _Item(_mark("needs_bash", "the script runs bash -c"))
    conf.pytest_collection_modifyitems(None, [item])
    assert len(item.skip_reasons) == 1 and "the script runs bash -c" in item.skip_reasons[0]
    assert calls == [["bash", "-c", "exit 0"]]


@pytest.mark.parametrize("error", [FileNotFoundError("bash"), subprocess.TimeoutExpired("bash", 30)])
def test_bash_that_cannot_run_skips(monkeypatch, error):
    conf = _load_conftest()
    _bash_result(monkeypatch, error=error)
    item = _Item(_mark("needs_bash", "r"))
    conf.pytest_collection_modifyitems(None, [item])
    assert len(item.skip_reasons) == 1


def test_bash_that_runs_does_not_skip(monkeypatch):
    conf = _load_conftest()
    _bash_result(monkeypatch, returncode=0)
    item = _Item(_mark("needs_bash", "the script runs bash -c"))
    conf.pytest_collection_modifyitems(None, [item])
    assert item.added == []


# --- AC 1: the reason is required -------------------------------------------------------------

@pytest.mark.parametrize("name", MARKERS)
@pytest.mark.parametrize("probe_passes", [True, False])
def test_mutation_control_a_mark_without_a_reason_is_refused(monkeypatch, name, probe_passes):
    """The check comes before the probe: an empty reason is an error even where the test would run."""
    conf = _load_conftest()
    if not probe_passes:
        _symlink_denied(monkeypatch)
        _bash_result(monkeypatch, returncode=1)
    for bad in (_mark(name), _mark(name, ""), _mark(name, "   ")):
        with pytest.raises(pytest.UsageError, match=name):
            conf.pytest_collection_modifyitems(None, [_Item(bad)])


@pytest.mark.parametrize("name", MARKERS)
def test_the_reason_may_be_given_as_a_keyword(monkeypatch, name):
    conf = _load_conftest()
    _symlink_denied(monkeypatch)
    _bash_result(monkeypatch, returncode=1)
    item = _Item(getattr(pytest.mark, name)(reason="a keyword reason").mark)
    conf.pytest_collection_modifyitems(None, [item])
    assert "a keyword reason" in item.skip_reasons[0]


def test_both_markers_are_registered():
    class _Config:
        lines = []

        def addinivalue_line(self, key, line):
            self.lines.append(line)

    _Config.lines = []
    _load_conftest().pytest_configure(_Config())
    joined = "\n".join(_Config.lines)
    for name in (PLATFORM_MARKER,) + MARKERS:
        assert f"{name}(reason)" in joined


# --- AC 1: the probe runs once per session ------------------------------------------------------

def test_each_probe_runs_once_per_session(monkeypatch):
    conf = _load_conftest()
    calls = _bash_result(monkeypatch, returncode=1)
    symlink_calls = []

    def deny(*args, **kwargs):
        symlink_calls.append(args)
        raise OSError(EPERM_WINDOWS, "denied")
    monkeypatch.setattr(os, "symlink", deny)
    items = [_Item(_mark("needs_symlinks", "r"), _mark("needs_bash", "r")) for _ in range(5)]
    conf.pytest_collection_modifyitems(None, items)
    conf.pytest_collection_modifyitems(None, items)
    assert len(calls) == 1 and len(symlink_calls) == 1
    assert all(len(i.skip_reasons) == 4 for i in items)  # two marks x two passes


def test_no_probe_runs_when_no_test_carries_the_marker(monkeypatch):
    conf = _load_conftest()
    calls = _bash_result(monkeypatch, returncode=1)

    def boom(*args, **kwargs):
        raise AssertionError("os.symlink must not be probed")
    monkeypatch.setattr(os, "symlink", boom)
    conf.pytest_collection_modifyitems(None, [_Item(), _Item(_mark(PLATFORM_MARKER, "r"))])
    assert calls == []


# --- Edge: a test with the T263 marker and a new marker keeps both reasons --------------------------

def test_the_platform_marker_and_needs_symlinks_keep_both_reasons(monkeypatch):
    conf = _load_conftest()
    monkeypatch.setattr(conf.sys, "platform", "win32")
    _symlink_denied(monkeypatch)
    item = _Item(_mark(PLATFORM_MARKER, "chmod bits"), _mark("needs_symlinks", "makes a link"))
    conf.pytest_collection_modifyitems(None, [item])
    joined = " | ".join(item.skip_reasons)
    assert "chmod bits" in joined and "makes a link" in joined


# --- Edge: the marker works on a class and as pytestmark, through real pytest -------------------

def _nested_pytest(cwd, args, work, bash_fails=False):
    """Run pytest in `cwd` with symlinks denied (a sitecustomize in `work`) and, if asked, a failing bash first on PATH."""
    shim = work / "shim"
    shim.mkdir(exist_ok=True)
    (shim / "sitecustomize.py").write_text(textwrap.dedent("""\
        import os, pathlib

        def _deny(*a, **k):
            raise OSError(1314, "A required privilege is not held by the client")

        os.symlink = _deny
        pathlib.Path.symlink_to = _deny
        """))
    env = dict(os.environ, PYTHONPATH=str(shim))
    if bash_fails:
        fake = work / "fakebin"
        fake.mkdir(exist_ok=True)
        bash = fake / "bash"
        bash.write_text("#!/bin/sh\nexit 1\n")
        bash.chmod(0o755)
        env["PATH"] = str(fake) + os.pathsep + env["PATH"]
    return subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "--strict-markers",
                           "-rs", "-q", *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=300)


@pytest.mark.skipif(sys.platform == "win32", reason="the fake bash is a sh script")
def test_markers_work_on_a_function_a_class_and_pytestmark(tmp_path):
    (tmp_path / "conftest.py").write_text(CONFTEST.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "test_fn.py").write_text(textwrap.dedent("""\
        import pytest

        @pytest.mark.needs_symlinks("fn needs a link")
        def test_fn():
            raise AssertionError("must be skipped")

        @pytest.mark.needs_bash("class needs bash")
        class TestK:
            def test_a(self):
                raise AssertionError("must be skipped")

        def test_free():
            pass
        """))
    (tmp_path / "test_mod.py").write_text(textwrap.dedent("""\
        import pytest

        pytestmark = pytest.mark.needs_symlinks("module needs a link")

        def test_m():
            raise AssertionError("must be skipped")
        """))
    work = tmp_path / "work"
    work.mkdir()
    result = _nested_pytest(tmp_path, ["test_fn.py", "test_mod.py"], work, bash_fails=True)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "1 passed, 3 skipped" in out, out
    for reason in ("fn needs a link", "class needs bash", "module needs a link"):
        assert reason in out, out


@pytest.mark.skipif(sys.platform == "win32", reason="the fake bash is a sh script")
def test_an_empty_reason_is_a_collection_error_through_real_pytest(tmp_path):
    (tmp_path / "conftest.py").write_text(CONFTEST.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "test_bad.py").write_text(textwrap.dedent("""\
        import pytest

        @pytest.mark.needs_bash("")
        def test_bad():
            pass
        """))
    work = tmp_path / "work"
    work.mkdir()
    result = _nested_pytest(tmp_path, ["test_bad.py"], work)
    assert result.returncode != 0
    assert "needs_bash needs a non-empty reason" in result.stdout + result.stderr


# --- AC 3, 4 and Success Criterion 4: the real suite skips cleanly when both probes fail ----------

NEEDS_SYMLINKS = [
    "tests/test_dotfiles.py",
    "tests/test_plugin_names.py::test_every_skill_dir_path_exists_in_the_setup_install_layout",
    "tests/test_plugin_names.py::test_every_skill_dir_command_runs[install]",
]
NEEDS_BASH = ["tests/test_ci_verify_done_tasks.py"]


@pytest.mark.skipif(sys.platform == "win32", reason="the fake bash is a sh script")
def test_the_marked_tests_skip_when_the_machine_has_no_symlinks_and_no_bash(tmp_path):
    """Mutation control: delete one marker from those files and this test goes red.

    With every symlink denied and a `bash` that fails, no marked test may fail: each one is skipped.
    """
    result = _nested_pytest(ROOT, [*NEEDS_SYMLINKS, *NEEDS_BASH], tmp_path, bash_fails=True)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert not re.search(r"\d+ (failed|error)", out), out
    skipped = int(re.search(r"(\d+) skipped", out).group(1))
    assert skipped >= 38, f"expected the 31 symlink tests and the 7 bash tests to skip, got {skipped}\n{out}"
