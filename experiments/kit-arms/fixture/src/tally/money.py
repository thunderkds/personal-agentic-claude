"""Amounts are kept as whole cents (int) everywhere inside tally.

Floats never touch money: "0.10" + "0.20" must be exactly 30 cents.
"""

import re

_AMOUNT_RE = re.compile(r"^(\d{1,9})(?:\.(\d{1,2}))?$")


def parse_amount(text):
    """Parse a user-typed amount like "12", "12.5" or "12.50" into cents.

    A leading "$" and thousands separators are accepted ("$1,200.00").
    Raises ValueError for anything else.
    """
    cleaned = text.strip().lstrip("$").replace(",", "")
    match = _AMOUNT_RE.match(cleaned)
    if not match:
        raise ValueError(f"not a valid amount: {text!r}")
    whole, frac = match.group(1), match.group(2) or ""
    return int(whole) * 100 + int(frac.ljust(2, "0") or 0)


def to_plain(cents):
    """Cents as the plain decimal string stored in the data file: 1250 -> "12.50"."""
    return f"{cents // 100}.{cents % 100:02d}"


def split_evenly(cents, parts):
    """Split an amount into `parts` shares that add back up to exactly `cents`.

    The first shares absorb the leftover cents: split_evenly(100, 3) -> [34, 33, 33].
    """
    if parts < 1:
        raise ValueError("parts must be at least 1")
    base, extra = divmod(cents, parts)
    return [base + 1 if i < extra else base for i in range(parts)]
