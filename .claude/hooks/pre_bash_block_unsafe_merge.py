#!/usr/bin/env python3
"""
PreToolUse hook — fires before every Bash tool call.

Blocks git push/merge/rebase commands if:
  1. Any task in PROJECT_KANBAN.md is still In Progress or Ready for Review
  2. No Stage 5 verify evidence is found in any pending task guide

This enforces the pipeline gate: Stage 4 review + Stage 5 verify must
complete before code ships.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
TASKS_DIR = os.path.join(ROOT, "tasks")

BLOCKED_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bgit\s+merge\b",
    r"\bgit\s+rebase\b",
]

def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if event.get("tool_name") != "Bash":
        sys.exit(0)

    command = event.get("tool_input", {}).get("command", "")

    if not any(re.search(p, command) for p in BLOCKED_PATTERNS):
        sys.exit(0)

    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        sys.exit(0)

    def tasks_in_section(section_title):
        m = re.search(rf"### {re.escape(section_title)}\n(.*?)(?=###|\Z)", kanban, re.DOTALL)
        if not m:
            return []
        block = m.group(1).strip()
        return [re.search(r"\*\*(T\d+)\*\*", l).group(1)
                for l in block.splitlines()
                if l.strip().startswith("- ") and re.search(r"\*\*(T\d+)\*\*", l)]

    in_progress = tasks_in_section("In Progress")
    ready_review = tasks_in_section("Ready for Review")

    blockers = []

    if in_progress:
        blockers.append(f"Tasks still In Progress: {', '.join(in_progress)}")

    if ready_review:
        # Check each for verify evidence in their task guide
        unverified = []
        for tid in ready_review:
            guide_path = os.path.join(TASKS_DIR, f"TASK_GUIDE_{tid}.md")
            try:
                with open(guide_path) as f:
                    guide = f.read()
                # Look for a filled verify row in the Evidence table
                if not re.search(r"verify\s*\|[^|\n]+\|[^|\n]*pass", guide, re.IGNORECASE):
                    unverified.append(tid)
            except FileNotFoundError:
                unverified.append(tid)

        if unverified:
            blockers.append(
                f"Tasks in Ready for Review missing Stage 5 verify evidence: "
                f"{', '.join(unverified)}"
            )

    if blockers:
        result = {
            "decision": "block",
            "reason": (
                "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • "
                + "\n  • ".join(blockers)
                + "\nComplete Stage 4 review and Stage 5 verify first."
            )
        }
        print(json.dumps(result))

main()
