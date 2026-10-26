import os
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))


@pytest.fixture
def data_file(tmp_path, monkeypatch):
    path = tmp_path / "expenses.csv"
    monkeypatch.setenv("TALLY_FILE", str(path))
    return path


@pytest.fixture
def tally(data_file):
    """Run the real CLI against a throwaway data file; returns CompletedProcess."""

    def run(*args):
        env = dict(os.environ, PYTHONPATH=str(SRC), TALLY_FILE=str(data_file))
        return subprocess.run(
            [sys.executable, "-m", "tally", *args],
            capture_output=True, text=True, env=env, timeout=30,
        )

    return run
