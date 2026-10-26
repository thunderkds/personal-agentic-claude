"""task6 (multi-file): refunds — negative amounts accepted, stored, shown and subtracted."""
import pytest


def line_of(text, word):
    return next(line for line in text.splitlines() if line.split() and line.split()[0] == word)


def test_refund_is_accepted_listed_and_subtracted(tally):
    assert tally("add", "100", "groceries", "big shop", "--date", "2026-03-01").returncode == 0
    added = tally("add", "-15.50", "groceries", "returned the blender", "--date", "2026-03-02")
    assert added.returncode == 0, added.stderr
    listed = tally("list")
    assert listed.returncode == 0, listed.stderr
    assert "-$15.50" in listed.stdout and "returned the blender" in listed.stdout
    summary = tally("summary").stdout
    assert "$84.50" in line_of(summary, "groceries")
    assert "$84.50" in line_of(summary, "total")


@pytest.mark.parametrize("amount, shown", [("-0.05", "-$0.05"), ("-1234.56", "-$1,234.56"), ("-15", "-$15.00")])
def test_refunds_load_back_exactly(tally, amount, shown):
    assert tally("add", amount, "books", "refund", "--date", "2026-03-03").returncode == 0
    assert shown in tally("list").stdout
    assert shown in tally("top", "5").stdout


def test_total_can_go_negative(tally):
    tally("add", "-15.00", "groceries", "returned the blender", "--date", "2026-03-02")
    assert "-$15.00" in line_of(tally("summary").stdout, "total")


@pytest.mark.parametrize("zero", ["0", "0.00", "-0", "-0.00"])
def test_zero_is_still_rejected(tally, zero):
    assert tally("add", zero, "groceries").returncode == 2


def test_positive_amounts_unchanged(tally):
    tally("add", "1200", "rent", "--date", "2026-03-01")
    assert "$1,200.00" in tally("list").stdout
    assert "-$" not in tally("summary").stdout
