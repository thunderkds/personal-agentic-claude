# task3 — refactor

Kind: refactor
Good outcome: one `format_amount(cents)` in `money.py`, used by every command; no cents-to-dollars arithmetic left in `cli.py`; every command's output byte-identical.

## Prompt

Small cleanup: in `src/tally/cli.py` the code that turns cents into a dollar string like `$1,234.56` is copy-pasted into almost every command. Please move it into one function, `format_amount(cents)`, in `src/tally/money.py` and make every command use it. This is a pure refactor — the output of every command must stay exactly the same.
