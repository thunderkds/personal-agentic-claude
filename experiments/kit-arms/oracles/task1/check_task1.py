"""task1 (feature): `summary --month YYYY-MM`."""
import pytest

CSV = """date,amount,category,note
2026-02-10,40.00,books,feb book
2026-03-01,1200.00,rent,march rent
2026-03-05,12.50,groceries,march shop
2026-03-20,7.25,groceries,march top-up
2026-04-02,99.99,books,april book
"""


def lines_by_first_word(text):
    return {line.split()[0]: line for line in text.splitlines() if line.strip()}


def test_month_counts_only_that_month(tally, data_file):
    data_file.write_text(CSV)
    result = tally("summary", "--month", "2026-03")
    assert result.returncode == 0, result.stderr
    lines = lines_by_first_word(result.stdout)
    assert "$1,200.00" in lines["rent"]
    assert "$19.75" in lines["groceries"]
    assert "$1,219.75" in lines["total"]
    for other in ("$40.00", "$99.99", "$139.99", "$1,359.74"):
        assert other not in result.stdout


@pytest.mark.parametrize("bad", ["2026-13", "march", "2026-3-01", "26-03"])
def test_bad_month_exits_2_with_error(tally, data_file, bad):
    data_file.write_text(CSV)
    result = tally("summary", "--month", bad)
    assert result.returncode == 2
    assert "error" in result.stderr.lower()


def test_without_month_output_is_unchanged(tally, data_file, pristine):
    data_file.write_text(CSV)
    assert tally("summary").stdout == pristine({"expenses.csv": CSV})("summary").stdout
