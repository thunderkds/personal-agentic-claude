#!/usr/bin/env python3
"""
PostToolUse hook — fires after every Agent tool call.

When an agent finishes, extracts the task ID from the spawn prompt and
moves the task from "In Progress" to "Ready for Review" in PROJECT_KANBAN.md.
"""
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")

def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if event.get("tool_name") != "Agent":
        sys.exit(0)

    prompt = event.get("tool_input", {}).get("prompt", "")
    task_ids = re.findall(r"\bT(\d{3})\b", prompt, re.IGNORECASE)
    if not task_ids:
        sys.exit(0)

    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        sys.exit(0)

    changed = False
    for tid in task_ids:
        task_ref = f"T{tid}"
        # Find the line in "In Progress" section and move it
        in_progress_pattern = re.compile(
            r"(### In Progress\n)(.*?)(### Ready for Review)",
            re.DOTALL
        )
        m = in_progress_pattern.search(kanban)
        if not m:
            continue

        in_prog_block = m.group(2)
        lines = in_prog_block.splitlines(keepends=True)
        moved = []
        remaining = []
        for line in lines:
            if f"**{task_ref}**" in line:
                moved.append(line)
            else:
                remaining.append(line)

        if not moved:
            continue

        new_in_prog = "".join(remaining)
        new_review_lines = "".join(moved)

        kanban = in_progress_pattern.sub(
            lambda mo: f"### In Progress\n{new_in_prog}### Ready for Review\n{new_review_lines}",
            kanban,
            count=1
        )
        changed = True
        print(f"[hook:post_agent] Moved {task_ref} → Ready for Review", file=sys.stderr)

    if changed:
        today = date.today().isoformat()
        kanban = re.sub(r"\*\*Last updated\*\*:.*", f"**Last updated**: {today}", kanban)
        with open(KANBAN, "w") as f:
            f.write(kanban)

main()
