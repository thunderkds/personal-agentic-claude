"""Shared fixtures for the code oracles. TALLY_SRC = the src/ of the copy under grading."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PRISTINE_SRC = Path(__file__).resolve().parents[1] / "fixture" / "src"


def make_runner(src, data_file):
    def run(*args):
        env = dict(os.environ, PYTHONPATH=str(src), TALLY_FILE=str(data_file), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, "-m", "tally", *args], capture_output=True, text=True,
                              env=env, cwd=str(data_file.parent), timeout=60)
    return run


@pytest.fixture
def target_src():
    return Path(os.environ["TALLY_SRC"])


@pytest.fixture
def data_file(tmp_path):
    (tmp_path / "target").mkdir()
    return tmp_path / "target" / "expenses.csv"


@pytest.fixture
def tally(target_src, data_file):
    return make_runner(target_src, data_file)


@pytest.fixture
def pristine(tmp_path):
    """Runner for the untouched fixture, seeded with the same files: pristine(files)(*args)."""
    def seeded(files):
        folder = tmp_path / "pristine"
        folder.mkdir(exist_ok=True)
        for name, text in files.items():
            (folder / name).write_text(text)
        return make_runner(PRISTINE_SRC, folder / "expenses.csv")
    return seeded
