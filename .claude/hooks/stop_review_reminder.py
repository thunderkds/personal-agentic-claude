#!/usr/bin/env python3
"""
Stop hook — fires after Claude stops responding.

Scans PROJECT_KANBAN.md for tasks in "Ready for Review" and prints
a visible reminder to run Stage 4 review before merging.

T178: a row marked `| Track: minimal` has no Stage 4 (docs/claude-md/tracks.md),
so it is listed apart, as waiting for the user's merge decision. Reminder only:
the merge gate (pre_bash_block_unsafe_merge.py) never reads this marker.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
REPORTS_DIR = os.path.join(ROOT, "reports")
MINIMAL_TRACK_MARKER = re.compile(r"\|\s*Track:\s*minimal\b", re.IGNORECASE)


def has_any_delivery_report():
    """DDR-0003 decision 5: a non-blocking reminder, not a per-task check —
    the reminder can only detect that no delivery report exists at all, since
    reports/ filenames key on branch, not Task ID."""
    if not os.path.isdir(REPORTS_DIR):
        return False
    return any(name.startswith("delivery-report_") for name in os.listdir(REPORTS_DIR))


def main():
    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        sys.exit(0)

    m = re.search(r"### Ready for Review\n(.*?)(?=###|\Z)", kanban, re.DOTALL)
    if not m:
        sys.exit(0)

    block = m.group(1).strip()
    tasks = [line.strip() for line in block.splitlines() if line.strip().startswith("- ")]

    if not tasks:
        sys.exit(0)

    minimal = [t for t in tasks if MINIMAL_TRACK_MARKER.search(t)]
    review = [t for t in tasks if t not in minimal]

    print("\n" + "=" * 60, file=sys.stderr)
    if review:
        print("⚠️  SUPERVISOR: Tasks awaiting Stage 4 Review:", file=sys.stderr)
        for t in review:
            print(f"   {t}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Run: Skill({ skill: 'code-review' })", file=sys.stderr)
        print("For Medium/High risk: Skill({ skill: 'security-review' })", file=sys.stderr)
    if minimal:
        if review:
            print("", file=sys.stderr)
        print("⚠️  SUPERVISOR: Minimal-track tasks awaiting the user's merge decision", file=sys.stderr)
        print("   (Decision record in tasks/MINIMAL_LOG.md; merge only when the user asks):",
              file=sys.stderr)
        for t in minimal:
            print(f"   {t}", file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)

main()
