import datetime as dt

import pytest

from tally.models import Expense, new_expense, normalize_category


def test_round_trip_row():
    e = Expense(dt.date(2026, 3, 2), 1250, "food", "groceries")
    assert Expense.from_row(e.to_row()) == e


def test_normalize_category():
    assert normalize_category("  Eating Out ") == "eating-out"


@pytest.mark.parametrize("amount", ["0", "0.00"])
def test_zero_amount_rejected(amount):
    with pytest.raises(ValueError):
        new_expense(amount, "food")


def test_negative_amount_rejected():
    with pytest.raises(ValueError):
        new_expense("-5.00", "food")


def test_bad_category_rejected():
    with pytest.raises(ValueError):
        new_expense("5", "!!!")


def test_month():
    assert Expense(dt.date(2026, 3, 31), 100, "food").month == "2026-03"
