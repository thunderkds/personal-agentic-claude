def test_add_and_list(tally):
    assert tally("add", "12.50", "Food", "groceries", "--date", "2026-03-02").returncode == 0
    assert tally("add", "1200", "rent", "--date", "2026-03-01").returncode == 0
    out = tally("list").stdout
    assert "$12.50" in out and "groceries" in out
    assert "$1,200.00" in out


def test_summary_totals(tally):
    tally("add", "10", "food", "--date", "2026-03-02")
    tally("add", "2.50", "food", "--date", "2026-03-03")
    tally("add", "40", "books", "--date", "2026-03-04")
    out = tally("summary").stdout
    assert "food" in out and "$12.50" in out
    assert "total" in out and "$52.50" in out


def test_bad_amount_exits_2(tally):
    result = tally("add", "twelve", "food")
    assert result.returncode == 2
    assert "error:" in result.stderr


def test_list_since(tally):
    tally("add", "1", "food", "old", "--date", "2026-01-01")
    tally("add", "2", "food", "new", "--date", "2026-02-01")
    out = tally("list", "--since", "2026-01-15").stdout
    assert "new" in out and "old" not in out


def test_bad_since_exits_2(tally):
    assert tally("list", "--since", "yesterday").returncode == 2


def test_delete(tally):
    tally("add", "1", "food", "keep", "--date", "2026-01-01")
    tally("add", "2", "food", "drop", "--date", "2026-01-02")
    assert tally("delete", "2").returncode == 0
    out = tally("list").stdout
    assert "keep" in out and "drop" not in out


def test_split(tally):
    out = tally("split", "100.00", "3").stdout
    assert "person 1: $33.34" in out and "person 3: $33.33" in out


def test_due(tally, data_file):
    data_file.with_name("recurring.csv").write_text(
        "category,amount,day,note\nrent,1200.00,1,flat\nphone,30.00,20,mobile\n"
    )
    tally("add", "1200", "rent", "--date", "2026-03-01")
    assert tally("due", "--today", "2026-03-10").stdout.strip() == "Nothing due."
    out = tally("due", "--today", "2026-04-25").stdout
    assert "rent" in out and "phone" in out
