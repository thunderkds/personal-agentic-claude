"""task2 (bug fix): notes with commas and quotes survive a write and a read."""


def test_comma_and_quote_notes_round_trip(tally):
    assert tally("add", "18.40", "eating-out", "pho, then bubble tea", "--date", "2026-03-02").returncode == 0
    assert tally("add", "5", "groceries", 'milk "the good one", 2L', "--date", "2026-03-03").returncode == 0
    listed = tally("list")
    assert listed.returncode == 0, listed.stderr
    assert "pho, then bubble tea" in listed.stdout
    assert 'milk "the good one", 2L' in listed.stdout
    summary = tally("summary")
    assert summary.returncode == 0, summary.stderr
    assert "$23.40" in summary.stdout


def test_delete_rewrites_comma_notes_intact(tally):
    tally("add", "1", "groceries", "plain note", "--date", "2026-03-01")
    tally("add", "2", "groceries", "apples, pears", "--date", "2026-03-02")
    tally("add", "3", "groceries", "bread, eggs, milk", "--date", "2026-03-03")
    assert tally("delete", "1").returncode == 0
    listed = tally("list")
    assert listed.returncode == 0, listed.stderr
    assert "apples, pears" in listed.stdout and "bread, eggs, milk" in listed.stdout
    assert "plain note" not in listed.stdout


def test_existing_plain_file_still_loads(tally, data_file):
    data_file.write_text("date,amount,category,note\n2026-01-01,3.00,groceries,plain\n")
    listed = tally("list")
    assert listed.returncode == 0 and "plain" in listed.stdout
