import pytest

from tally.money import parse_amount, split_evenly, to_plain


@pytest.mark.parametrize("text, cents", [
    ("12", 1200), ("12.5", 1250), ("12.50", 1250), ("0.07", 7),
    ("$1,200.00", 120000), (" 3.10 ", 310),
])
def test_parse_amount(text, cents):
    assert parse_amount(text) == cents


@pytest.mark.parametrize("text", ["", "abc", "12.345", "1.2.3", "--5", "12,5O"])
def test_parse_amount_rejects_garbage(text):
    with pytest.raises(ValueError):
        parse_amount(text)


def test_negative_amounts():
    assert parse_amount("-15.50") == -1550
    assert to_plain(-1550) == "-15.50"


def test_to_plain():
    assert to_plain(1250) == "12.50"
    assert to_plain(7) == "0.07"


def test_split_evenly_adds_up():
    assert split_evenly(100, 3) == [34, 33, 33]
    assert sum(split_evenly(1001, 7)) == 1001
