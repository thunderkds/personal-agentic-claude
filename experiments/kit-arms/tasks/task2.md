# task2 — bug fix

Kind: bug fix
Good outcome: notes containing commas (and quotes) are written so they read back intact; `list`, `summary` and `delete` keep working after such an add.

## Prompt

Found a bug. I added an expense with a comma in the note:

    python3 -m tally add 18.40 eating-out "pho, then bubble tea"

It said "Added", but after that `tally list` and `tally summary` both fail with `error: ... expected 4 fields, got 5`. I deleted that line from my data file by hand to get going again. Notes with commas in them should just work — can you fix it?
