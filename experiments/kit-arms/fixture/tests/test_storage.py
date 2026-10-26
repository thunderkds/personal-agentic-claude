import datetime as dt

import pytest

from tally import storage
from tally.models import Expense


def test_missing_file_is_empty(tmp_path):
    assert storage.load(tmp_path / "nope.csv") == []


def test_append_then_load(tmp_path):
    path = tmp_path / "e.csv"
    a = Expense(dt.date(2026, 1, 5), 900, "transport", "bus pass")
    b = Expense(dt.date(2026, 1, 6), 4550, "food", "")
    storage.append(a, path)
    storage.append(b, path)
    assert storage.load(path) == [a, b]
    assert path.read_text().splitlines()[0] == storage.HEADER


def test_save_all_rewrites(tmp_path):
    path = tmp_path / "e.csv"
    a = Expense(dt.date(2026, 1, 5), 900, "transport", "bus pass")
    storage.append(a, path)
    storage.save_all([], path)
    assert storage.load(path) == []


def test_corrupt_line_names_the_line(tmp_path):
    path = tmp_path / "e.csv"
    path.write_text("date,amount,category,note\n2026-01-05,abc,food,x\n")
    with pytest.raises(storage.StorageError, match="line 2"):
        storage.load(path)
