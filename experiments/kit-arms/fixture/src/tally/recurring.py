"""Recurring bills (rent, phone, subscriptions) and which ones are still due.

Recurring bills live in data/recurring.csv next to the expenses file:

    category,amount,day,note
    rent,1200.00,1,flat on Elm St

`day` is the day of the month the bill is normally paid (1-28).
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from tally import storage
from tally.models import CATEGORY_RE
from tally.money import parse_amount

FIELDS = ("category", "amount", "day", "note")


@dataclass(frozen=True)
class Bill:
    category: str
    amount: int  # cents
    day: int
    note: str = ""

    def __post_init__(self):
        if not CATEGORY_RE.match(self.category):
            raise ValueError(f"bad category {self.category!r}")
        if self.amount <= 0:
            raise ValueError("amount must be greater than zero")
        if not 1 <= self.day <= 28:
            raise ValueError("day must be between 1 and 28")


def bills_path():
    return Path(storage.data_path()).with_name("recurring.csv")


def load_bills(path=None):
    path = Path(path or bills_path())
    if not path.exists():
        return []
    bills = []
    with path.open(newline="", encoding="utf-8") as handle:
        for line_no, row in enumerate(csv.DictReader(handle), start=2):
            try:
                bills.append(Bill(
                    category=row["category"],
                    amount=parse_amount(row["amount"]),
                    day=int(row["day"]),
                    note=row.get("note") or "",
                ))
            except (KeyError, TypeError, ValueError) as err:
                raise storage.StorageError(f"{path}, line {line_no}: {err}") from None
    return bills


def still_due(bills, expenses, today):
    """Bills whose day has come this month but no matching expense was recorded.

    A bill counts as paid when an expense in the same category, in the same
    month as `today`, is at least 90% of the bill's amount.
    """
    month = today.strftime("%Y-%m")
    this_month = [e for e in expenses if e.month == month]
    due = []
    for bill in bills:
        if bill.day > today.day:
            continue
        paid = any(
            e.category == bill.category and e.amount * 10 >= bill.amount * 9
            for e in this_month
        )
        if not paid:
            due.append(bill)
    return due
