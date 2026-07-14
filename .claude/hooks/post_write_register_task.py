#!/usr/bin/env python3
"""
PostToolUse hook — fires after every Write tool call.

When a TASK_GUIDE_Txxx.md is written to tasks/, auto-registers it in
PROJECT_KANBAN.md under the Todo section if not already present.
Parses the guide for agent, complexity, risk, and priority metadata.
"""
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
TASKS_DIR = os.path.join(ROOT, "tasks")

def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    if tool_name != "Write":
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    match = re.search(r"TASK_GUIDE_(T\d+)\.md$", file_path)
    if not match:
        sys.exit(0)

    task_id = match.group(1)

    # Read the guide to extract metadata
    try:
        with open(file_path) as f:
            guide = f.read()
    except FileNotFoundError:
        sys.exit(0)

    def extract(pattern, default="?"):
        m = re.search(pattern, guide, re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else default

    title    = extract(r"^#\s+TASK_GUIDE[_\s—-]+T\d+[:\s—-]+(.+)$", "untitled")
    agent    = extract(r"(?:Assigned Agent|Agent)[:\s]+([a-z\-]+)", "backend-developer")
    cx       = extract(r"Complexity[:\s]+(C[0-3])", "C1")
    risk     = extract(r"Risk[:\s]+(Low|Med(?:ium)?|High)", "Low")
    priority = extract(r"Priority[:\s]+(P[0-2])", "P1")

    # Normalise risk label
    risk = "Med" if risk.lower().startswith("med") else risk

    entry = f"- [ ] **{task_id}** — {title} | {agent} | {cx} | Risk: {risk} | {priority}"

    # Read kanban
    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        sys.exit(0)

    # Skip if already registered (any section)
    if f"**{task_id}**" in kanban:
        sys.exit(0)

    # Insert under ### Todo
    if "### Todo" in kanban:
        kanban = kanban.replace("### Todo\n", f"### Todo\n{entry}\n", 1)
    else:
        kanban += f"\n### Todo\n{entry}\n"

    # Bump last-updated date
    today = date.today().isoformat()
    kanban = re.sub(r"\*\*Last updated\*\*:.*", f"**Last updated**: {today}", kanban)

    with open(KANBAN, "w") as f:
        f.write(kanban)

    print(f"[hook:post_write] Registered {task_id} in PROJECT_KANBAN.md", file=sys.stderr)

main()
