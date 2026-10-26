"""task3 (refactor): one format_amount in money.py, used by cli.py, output unchanged."""
import os
import re
import subprocess
import sys

import pytest

CSV = """date,amount,category,note
2026-03-01,1200.00,rent,march rent
2026-03-05,12.50,groceries,march shop
2026-03-06,0.07,groceries,one sweet
2026-03-20,1234.56,travel,flights home
2026-03-21,10.00,books,paperback
"""
BILLS = "category,amount,day,note\nrent,1200.00,1,flat\nphone,30.00,20,mobile\n"


def test_format_amount_lives_in_money(target_src):
    code = ("from tally.money import format_amount as f;"
            "print('|'.join(f(c) for c in (123456, 7, 0, 100, 100000000)))")
    env = dict(os.environ, PYTHONPATH=str(target_src), PYTHONDONTWRITEBYTECODE="1")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "$1,234.56|$0.07|$0.00|$1.00|$1,000,000.00"


def test_cli_uses_it_and_keeps_no_cents_arithmetic(target_src):
    cli = (target_src / "tally" / "cli.py").read_text()
    assert "format_amount" in cli
    assert not re.search(r"//\s*100|%\s*100|/\s*100\b|divmod\(", cli)


@pytest.mark.parametrize("args", [
    ("list",), ("list", "--category", "groceries"), ("summary",), ("top", "2"), ("top", "9"),
    ("split", "100.00", "3"), ("split", "84.60", "7"), ("due", "--today", "2026-04-25"),
    ("add", "1234.5", "books", "big order", "--date", "2026-03-22"),
])
def test_every_command_output_is_unchanged(tally, data_file, pristine, args):
    data_file.write_text(CSV)
    data_file.with_name("recurring.csv").write_text(BILLS)
    got = tally(*args)
    want = pristine({"expenses.csv": CSV, "recurring.csv": BILLS})(*args)
    assert (got.returncode, got.stdout) == (want.returncode, want.stdout)
