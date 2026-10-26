"""Command-line interface: `python -m tally <command> ...`."""

import argparse
import datetime as dt
import sys

from tally import __version__, recurring, reports, storage
from tally.models import new_expense, normalize_category, parse_date
from tally.money import parse_amount, split_evenly


def cmd_add(args):
    date = parse_date(args.date) if args.date else None
    expense = new_expense(args.amount, args.category, args.note or "", date=date)
    storage.append(expense)
    dollars = f"${expense.amount // 100:,}.{expense.amount % 100:02d}"
    print(f"Added {dollars} to {expense.category} on {expense.date.isoformat()}.")
    return 0


def cmd_list(args):
    expenses = storage.load()
    numbered = list(enumerate(expenses, start=1))
    if args.since:
        start = parse_date(args.since)
        numbered = [(n, e) for n, e in numbered if e.date >= start]
    if args.category:
        wanted = normalize_category(args.category)
        numbered = [(n, e) for n, e in numbered if e.category == wanted]
    if not numbered:
        print("No expenses.")
        return 0
    for number, e in numbered:
        dollars = f"${e.amount // 100:,}.{e.amount % 100:02d}"
        print(f"{number:>4}  {e.date.isoformat()}  {dollars:>11}  {e.category:<14} {e.note}")
    return 0


def cmd_summary(args):
    expenses = storage.load()
    if not expenses:
        print("No expenses.")
        return 0
    for category, cents in reports.by_category(expenses):
        dollars = f"${cents // 100:,}.{cents % 100:02d}"
        print(f"{category:<14} {dollars:>11}")
    grand = reports.total(expenses)
    dollars = f"${grand // 100:,}.{grand % 100:02d}"
    print(f"{'total':<14} {dollars:>11}")
    return 0


def cmd_top(args):
    if args.count < 1:
        raise ValueError("count must be at least 1")
    for e in reports.largest(storage.load(), args.count):
        dollars = f"${e.amount // 100:,}.{e.amount % 100:02d}"
        print(f"{dollars:>11}  {e.date.isoformat()}  {e.category:<14} {e.note}")
    return 0


def cmd_split(args):
    cents = parse_amount(args.amount)
    shares = split_evenly(cents, args.people)
    for person, share in enumerate(shares, start=1):
        dollars = f"${share // 100:,}.{share % 100:02d}"
        print(f"person {person}: {dollars}")
    return 0


def cmd_due(args):
    today = parse_date(args.today) if args.today else dt.date.today()
    due = recurring.still_due(recurring.load_bills(), storage.load(), today)
    if not due:
        print("Nothing due.")
        return 0
    for bill in due:
        dollars = f"${bill.amount // 100:,}.{bill.amount % 100:02d}"
        print(f"{bill.category:<14} {dollars:>11}  (day {bill.day}) {bill.note}".rstrip())
    return 0


def cmd_delete(args):
    expenses = storage.load()
    if not 1 <= args.number <= len(expenses):
        raise ValueError(f"no expense number {args.number} (see `tally list`)")
    removed = expenses.pop(args.number - 1)
    storage.save_all(expenses)
    print(f"Deleted {removed.date.isoformat()} {removed.category} {removed.note}".rstrip() + ".")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="tally", description="Track what you spend.")
    parser.add_argument("--version", action="version", version=f"tally {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="record an expense")
    add.add_argument("amount", help="e.g. 12.50")
    add.add_argument("category", help="e.g. food, rent, eating-out")
    add.add_argument("note", nargs="?", help="optional free text")
    add.add_argument("--date", help="YYYY-MM-DD (default: today)")
    add.set_defaults(func=cmd_add)

    lst = sub.add_parser("list", help="show expenses")
    lst.add_argument("--since", help="only expenses on or after YYYY-MM-DD")
    lst.add_argument("--category", help="only this category")
    lst.set_defaults(func=cmd_list)

    summary = sub.add_parser("summary", help="totals per category")
    summary.set_defaults(func=cmd_summary)

    top = sub.add_parser("top", help="the biggest single expenses")
    top.add_argument("count", nargs="?", type=int, default=3)
    top.set_defaults(func=cmd_top)

    split = sub.add_parser("split", help="split a bill evenly")
    split.add_argument("amount")
    split.add_argument("people", type=int)
    split.set_defaults(func=cmd_split)

    due = sub.add_parser("due", help="recurring bills not yet paid this month")
    due.add_argument("--today", help=argparse.SUPPRESS)
    due.set_defaults(func=cmd_due)

    delete = sub.add_parser("delete", help="delete an expense by its number in `tally list`")
    delete.add_argument("number", type=int)
    delete.set_defaults(func=cmd_delete)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, storage.StorageError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
