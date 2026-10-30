"""
T214 — the old background-spawn markers stay out of git.

AC1: no file under .claude/markers/ is tracked.
AC2: .gitignore ignores .claude/markers/, so a new marker is never committed.
"""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_marker_file_is_tracked():
    tracked = subprocess.run(
        ["git", "ls-files", ".claude/markers"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert tracked == [], f"{len(tracked)} marker files still tracked"


def test_markers_folder_is_ignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".claude/markers/T999.pid"],
        cwd=ROOT,
    )
    assert result.returncode == 0, ".claude/markers/ must be in .gitignore"
