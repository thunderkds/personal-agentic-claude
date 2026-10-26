# task1 — feature

Kind: feature
Good outcome: `summary --month YYYY-MM` totals only that month; a bad month prints an error and exits 2; plain `summary` is unchanged.

## Prompt

Can you add a `--month` option to `tally summary`? I want to see the totals for just one month, e.g. `python3 -m tally summary --month 2026-03` should only count expenses dated in March 2026. If I give it a month that isn't valid (like `2026-13` or `march`) it should print an error and exit with status 2, the same way `list --since` does with a bad date. Without `--month` it should keep working exactly like it does now.
