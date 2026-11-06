"""Shared pytest setup for `tests/` and `.claude/hooks/tests/` (T263).

One marker, `posix_only(reason)`, skips a test on native Windows with a written reason:

    @pytest.mark.posix_only("creates a symlink, which needs Developer Mode on Windows")
    def test_x(): ...

    pytestmark = pytest.mark.posix_only("...")   # a whole module

The skip is `sys.platform == "win32"` only: on Linux and macOS the test runs as before.
A `posix_only` mark with no reason text is a collection error, so no test is skipped without
a written reason. Fix the code and delete the mark when a later task makes the test portable.
The Windows CI job is `.github/workflows/windows.yml`.
"""
import sys

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "posix_only(reason): skip on native Windows (sys.platform == 'win32'); the reason is required",
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
