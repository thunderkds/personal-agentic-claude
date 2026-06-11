#!/usr/bin/env python3
"""
PreToolUse hook — fires before every Agent tool call.

Extracts a task ID (Txxx) from the spawn prompt and blocks the spawn
if the corresponding tasks/TASK_GUIDE_Txxx.md does not exist.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS_DIR = os.path.join(ROOT, "tasks")

def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if event.get("tool_name") != "Agent":
        sys.exit(0)

    prompt = event.get("tool_input", {}).get("prompt", "")

    task_ids = re.findall(r"\bT(\d+)\b", prompt, re.IGNORECASE)
    if not task_ids:
        # No task ID in prompt — allow through; Supervisor will handle
        sys.exit(0)

    missing = []
    for tid in task_ids:
        guide = os.path.join(TASKS_DIR, f"TASK_GUIDE_T{tid.zfill(3)}.md")
        # Also try without zero-padding
        guide_raw = os.path.join(TASKS_DIR, f"TASK_GUIDE_T{tid}.md")
        if not os.path.exists(guide) and not os.path.exists(guide_raw):
            missing.append(f"T{tid}")

    if missing:
        result = {
            "decision": "block",
            "reason": (
                f"[hook:pre_agent] Cannot spawn agent — missing TASK_GUIDE for: "
                f"{', '.join(missing)}. "
                f"Run Stage 2 planning first to generate the guide(s) in tasks/."
            )
        }
        print(json.dumps(result))
        sys.exit(0)

main()
