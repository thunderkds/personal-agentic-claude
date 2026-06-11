#!/usr/bin/env python3
"""
Stop hook — fires after Claude stops responding.

Scans PROJECT_KANBAN.md for tasks in "Ready for Review" and prints
a visible reminder to run Stage 4 review before merging.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")

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

    print("\n" + "=" * 60, file=sys.stderr)
    print("⚠️  SUPERVISOR: Tasks awaiting Stage 4 Review:", file=sys.stderr)
    for t in tasks:
        print(f"   {t}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Run: Skill({ skill: 'code-review' })", file=sys.stderr)
    print("For Medium/High risk: Skill({ skill: 'security-review' })", file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)

main()
