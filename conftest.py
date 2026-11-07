"""Shared pytest setup for `tests/` and `.claude/hooks/tests/` (T263).

One marker, `posix_only(reason)`, skips a test on native Windows with a written reason:

    @pytest.mark.posix_only("creates a symlink, which needs Developer Mode on Windows")
    def test_x(): ...

    pytestmark = pytest.mark.posix_only("...")   # a whole module

The skip is `sys.platform == "win32"` only: on Linux and macOS the test runs as before.
A `posix_only` mark with no reason text is a collection error, so no test is skipped without
a written reason. Fix the code and delete the mark when a later task makes the test portable.
The Windows CI job is `.github/workflows/windows.yml`.

Two more markers skip a test when this machine lacks a thing it needs (T274). Each probes once per
session, only if a collected test carries the marker, and skips with the written reason. An empty
reason is a collection error, as for `posix_only`. A runner that has the thing (GitHub's Windows
runner can make symlinks) runs the test.

    @pytest.mark.needs_symlinks("links skills into a target; Windows needs Developer Mode")
    @pytest.mark.needs_bash("the script runs bash -c; System32 holds only a WSL stub")
"""
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

# marker name -> what the skip says about the machine
_NEEDS = {
    "needs_symlinks": "this machine cannot create a symlink",
    "needs_bash": "`bash -c \"exit 0\"` does not run on this machine",
}
_PROBE_CACHE = {}


def _probe_symlinks():
    """True when this process can create a symlink. Windows without Developer Mode raises OSError 1314."""
    folder = tempfile.mkdtemp(prefix="t274-probe-")
    try:
        target = os.path.join(folder, "target")
        with open(target, "w", encoding="utf-8") as f:
            f.write("x")
        os.symlink(target, os.path.join(folder, "link"))
        return True
    except (OSError, NotImplementedError):
        return False
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def _probe_bash():
    """True when `bash` runs. Run it: the WSL launcher stub in System32 is found on PATH but fails."""
    try:
        done = subprocess.run(["bash", "-c", "exit 0"], stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=30)
        return done.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


_PROBES = {"needs_symlinks": _probe_symlinks, "needs_bash": _probe_bash}


def _machine_can(name):
    if name not in _PROBE_CACHE:
        _PROBE_CACHE[name] = _PROBES[name]()
    return _PROBE_CACHE[name]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "posix_only(reason): skip on native Windows (sys.platform == 'win32'); the reason is required",
    )
    config.addinivalue_line(
        "markers",
        "needs_symlinks(reason): skip when this machine cannot create a symlink; the reason is required",
    )
    config.addinivalue_line(
        "markers",
        "needs_bash(reason): skip when `bash -c \"exit 0\"` does not run; the reason is required",
    )


def pytest_collection_modifyitems(config, items):
    for item in items:
        for mark in item.iter_markers(name="posix_only"):
            reason = (mark.args[0] if mark.args else mark.kwargs.get("reason", "")) or ""
            if not str(reason).strip():
                raise pytest.UsageError(f"{item.nodeid}: posix_only needs a non-empty reason")
            if sys.platform == "win32":
                item.add_marker(pytest.mark.skip(reason=f"POSIX-only: {reason}"))
            break
        for name, why in _NEEDS.items():
            marks = list(item.iter_markers(name=name))
            for mark in marks:
                reason = (mark.args[0] if mark.args else mark.kwargs.get("reason", "")) or ""
                if not str(reason).strip():
                    raise pytest.UsageError(f"{item.nodeid}: {name} needs a non-empty reason")
            if marks and not _machine_can(name):
                reason = marks[0].args[0] if marks[0].args else marks[0].kwargs["reason"]
                item.add_marker(pytest.mark.skip(reason=f"{name}: {why}: {reason}"))
