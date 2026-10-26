"""Reading and writing the expenses file (CSV, one expense per line)."""

import csv
import os
from pathlib import Path

from tally.models import FIELDS, Expense

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = PROJECT_ROOT / "data" / "expenses.csv"
HEADER = ",".join(FIELDS)


class StorageError(Exception):
    """The expenses file exists but cannot be read."""


def data_path():
    """Where the expenses live: $TALLY_FILE if set, else data/expenses.csv."""
    override = os.environ.get("TALLY_FILE")
    return Path(override) if override else DEFAULT_PATH


def load(path=None):
    """All expenses in file order. A missing file means no expenses yet."""
    path = Path(path or data_path())
    if not path.exists():
        return []
    expenses = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for line_no, row in enumerate(reader, start=1):
            if not row or (line_no == 1 and row == list(FIELDS)):
                continue
            try:
                expenses.append(Expense.from_row(row))
            except ValueError as err:
                raise StorageError(f"{path}, line {line_no}: {err}") from None
    return expenses


def _ensure_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(HEADER + "\n", encoding="utf-8")


def append(expense, path=None):
    """Add one expense at the end of the file."""
    path = Path(path or data_path())
    _ensure_file(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(",".join(expense.to_row()) + "\n")


def save_all(expenses, path=None):
    """Rewrite the whole file. Used after a delete."""
    path = Path(path or data_path())
    tmp = path.with_suffix(".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    lines = [HEADER] + [",".join(e.to_row()) for e in expenses]
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
