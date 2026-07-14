#!/usr/bin/env python3
"""
PreToolUse hook — fires before every Agent tool call.

Extracts a task ID (Txxx) from the spawn prompt and blocks the spawn
if the corresponding tasks/TASK_GUIDE_Txxx.md does not exist.

Also reads the target guide's `Depends on:` field (if present) and warns
— non-blocking — if the referenced task isn't Done yet on
PROJECT_KANBAN.md, or doesn't exist at all. This is advisory only: it
never sets "decision": "block", so intentional parallel/stub work is
never prevented.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS_DIR = os.path.join(ROOT, "tasks")
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")


def find_kanban_section(task_ref):
    """Return which board section (Todo/In Progress/Ready for Review/Done)
    contains task_ref, or None if it isn't found anywhere on the board."""
    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        return None

    for section in ("Done", "Ready for Review", "In Progress", "Todo"):
        m = re.search(rf"### {re.escape(section)}\n(.*?)(?=###|\Z)", kanban, re.DOTALL)
        if m and f"**{task_ref}**" in m.group(1):
            return section
    return None


def extract_structural_task_ids(prompt):
    """Extract task IDs that are *structurally* referenced in the spawn
    prompt — i.e. this spawn is genuinely about that task — as opposed to
    a bare Txxx substring appearing anywhere in pasted prose (e.g. a
    decision-log sentence from memory/MEMORY.md). Two structural markers
    are recognized:
      1. A literal TASK_GUIDE_Txxx.md file-path reference.
      2. An explicit "Task ID:" declaration line (with or without the
         "**...**" markdown-bold wrapper).
    Free-text mentions like "confirmed T013/T014 have no guide" or
    "T019: reconciled ..." are intentionally NOT matched.
    """
    ids = set()
    ids.update(re.findall(r"TASK_GUIDE_T(\d+)(?:_[A-Z0-9_]+)?\.md", prompt, re.IGNORECASE))
    ids.update(re.findall(r"(?:\*\*Task ID\*\*|Task ID)\s*:\s*T(\d+)\b", prompt, re.IGNORECASE))
    return sorted(ids)


def check_dependency_warnings(task_ids):
    """For each spawned task, read its guide's `Depends on:` field and
    return a list of non-blocking warning strings."""
    warnings = []
    for tid in task_ids:
        task_ref = f"T{tid.zfill(3)}"
        guide_path = os.path.join(TASKS_DIR, f"TASK_GUIDE_{task_ref}.md")
        if not os.path.exists(guide_path):
            guide_path = os.path.join(TASKS_DIR, f"TASK_GUIDE_T{tid}.md")
        try:
            with open(guide_path) as f:
                guide = f.read()
        except FileNotFoundError:
            continue

        m = re.search(r"\*\*Depends on\*\*:\s*(.+)", guide)
        if not m:
            continue
        dep_line = m.group(1).strip()
        if dep_line.lower().startswith("none") or dep_line.startswith("[Txxx"):
            continue

        dep_match = re.search(r"\bT(\d{3})\b", dep_line, re.IGNORECASE)
        if not dep_match:
            continue
        dep_ref = f"T{dep_match.group(1)}"

        section = find_kanban_section(dep_ref)
        if section is None:
            warnings.append(
                f"{task_ref} declares 'Depends on: {dep_ref}' but {dep_ref} was not "
                f"found anywhere on PROJECT_KANBAN.md — unknown dependency, check for a typo."
            )
        elif section != "Done":
            warnings.append(
                f"{task_ref} declares 'Depends on: {dep_ref}', which is currently "
                f"'{section}' (not Done). Confirm this is intentional (e.g. parallel "
                f"stub work) before proceeding."
            )
    return warnings


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if event.get("tool_name") != "Agent":
        sys.exit(0)

    prompt = event.get("tool_input", {}).get("prompt", "")

    task_ids = extract_structural_task_ids(prompt)
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

    warnings = check_dependency_warnings(task_ids)
    if warnings:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": (
                    "[hook:pre_agent] Dependency warning (advisory, not blocking):\n  • "
                    + "\n  • ".join(warnings)
                ),
            }
        }))

if __name__ == "__main__":
    main()
