# tally

A small command-line expense tracker. Plain Python 3, no dependencies.

I use it to keep track of what I spend each month: I add expenses as they
happen and look at the summary at the end of the month.

## Usage

```sh
export PYTHONPATH=src          # or: pip install -e . if you add packaging later

python3 -m tally add 12.50 groceries "Lidl weekly shop"
python3 -m tally add 1200 rent --date 2026-03-01
python3 -m tally list
python3 -m tally list --since 2026-03-01 --category groceries
python3 -m tally summary        # total per category
python3 -m tally top 5          # the 5 biggest expenses
python3 -m tally split 84.60 3  # split a bill three ways
python3 -m tally due            # recurring bills not paid yet this month
python3 -m tally delete 7       # delete expense #7 (numbers from `tally list`)
```

Categories are lowercased and spaces become dashes ("Eating Out" ->
`eating-out`). Bad input prints `error: ...` and exits with status 2.

## Data

My expenses live in `data/expenses.csv` (one row per expense, with a header
line) and my recurring bills in `data/recurring.csv`. The `data/` folder is
**not** in git — it is my real spending history, so don't lose it.

Set `TALLY_FILE=/some/other/file.csv` to point tally at a different file
(the tests do this so they never touch my data).

Amounts are stored and computed as whole cents; floats never touch money.

## Layout

```
src/tally/
  cli.py        argparse commands
  models.py     the Expense record and its validation
  money.py      parsing amounts, cents helpers
  storage.py    reading/writing the CSV file
  reports.py    totals and filters
  recurring.py  recurring bills and what is still due
tests/          pytest suite
```

## Tests

```sh
python3 -m pytest tests
```
