# task6 — multi-file change

Kind: multi-file change
Good outcome: negative amounts (refunds) are accepted, stored and read back exactly, shown as `-$15.50`, and subtracted in totals; zero is still rejected. Touches money.py, models.py and cli.py (+ tests).

## Prompt

I want to record refunds. Right now `python3 -m tally add -15.00 groceries "returned the blender"` gets rejected. Please allow negative amounts for refunds: `add` should accept them, `list`, `top` and `summary` should show them like `-$15.00`, and the summary totals should subtract them. A zero amount should still be rejected, and refunds have to load back correctly from the data file.
