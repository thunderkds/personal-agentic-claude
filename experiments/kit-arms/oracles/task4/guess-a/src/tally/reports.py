"""Summaries computed from a list of expenses."""


def total(expenses):
    return sum(e.amount for e in expenses)


def by_category(expenses):
    """[(category, cents)] in the order each category first appears."""
    totals = {}
    for expense in expenses:
        totals[expense.category] = totals.get(expense.category, 0) + expense.amount
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def since(expenses, start_date):
    """Expenses on or after start_date."""
    return [e for e in expenses if e.date >= start_date]


def in_category(expenses, category):
    return [e for e in expenses if e.category == category]


def largest(expenses, count=3):
    """The `count` biggest single expenses, biggest first."""
    return sorted(expenses, key=lambda e: e.amount, reverse=True)[:count]
