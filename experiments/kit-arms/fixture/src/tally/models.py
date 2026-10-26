"""The Expense record and its validation rules."""

import datetime as dt
import re
from dataclasses import dataclass

from tally.money import parse_amount, to_plain

CATEGORY_RE = re.compile(r"^[a-z][a-z0-9-]{0,29}$")
FIELDS = ("date", "amount", "category", "note")


@dataclass(frozen=True)
class Expense:
    date: dt.date
    amount: int  # cents
    category: str
    note: str = ""

    def __post_init__(self):
        if not isinstance(self.amount, int) or self.amount <= 0:
            raise ValueError("amount must be greater than zero")
        if not CATEGORY_RE.match(self.category):
            raise ValueError(
                f"bad category {self.category!r}: use lowercase letters, digits and dashes"
            )
        if "\n" in self.note or "\r" in self.note:
            raise ValueError("note must be a single line")

    @property
    def month(self):
        """The expense's month as "YYYY-MM"."""
        return self.date.strftime("%Y-%m")

    def to_row(self):
        return [self.date.isoformat(), to_plain(self.amount), self.category, self.note]

    @classmethod
    def from_row(cls, row):
        if len(row) != len(FIELDS):
            raise ValueError(f"expected {len(FIELDS)} fields, got {len(row)}: {row!r}")
        date_text, amount_text, category, note = row
        return cls(
            date=parse_date(date_text),
            amount=parse_amount(amount_text),
            category=category,
            note=note,
        )


def parse_date(text):
    """Parse "YYYY-MM-DD". Raises ValueError with a readable message."""
    try:
        return dt.date.fromisoformat(text.strip())
    except ValueError:
        raise ValueError(f"not a valid date (use YYYY-MM-DD): {text!r}") from None


def normalize_category(text):
    """User input "Eating Out" -> "eating-out"."""
    return "-".join(text.strip().lower().split())


def new_expense(amount_text, category_text, note="", date=None):
    """Build an Expense from raw command-line strings."""
    return Expense(
        date=date or dt.date.today(),
        amount=parse_amount(amount_text),
        category=normalize_category(category_text),
        note=note.strip(),
    )
