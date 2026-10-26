"""Reading and writing the expenses file (JSON: a list of objects)."""

import json
import os
from pathlib import Path

from tally.models import FIELDS, Expense

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = PROJECT_ROOT / "data" / "expenses.json"


class StorageError(Exception):
    """The expenses file exists but cannot be read."""


def data_path():
    override = os.environ.get("TALLY_FILE")
    return Path(override) if override else DEFAULT_PATH


def load(path=None):
    path = Path(path or data_path())
    if not path.exists():
        return []
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
        return [Expense.from_row([str(item[f]) for f in FIELDS]) for item in items]
    except (ValueError, KeyError, TypeError) as err:
        raise StorageError(f"{path}: {err}") from None


def save_all(expenses, path=None):
    path = Path(path or data_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps([dict(zip(FIELDS, e.to_row())) for e in expenses], indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def append(expense, path=None):
    save_all(load(path) + [expense], path)
