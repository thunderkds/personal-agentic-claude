"""T216 spike gate: logs every call; blocks `SPIKE_BLOCK_ME` only inside a kit project."""
import json
import os
import sys

PROBE = "SPIKE_BLOCK_ME"


def is_kit_project(cwd):
    return os.path.isfile(os.path.join(cwd, "PROJECT_KANBAN.md"))


def log(event):
    data_dir = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_dir:
        return
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "calls.jsonl"), "a") as f:
        f.write(json.dumps(event) + "\n")


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    kit = is_kit_project(cwd)
    command = tool_input.get("command", "")
    blocked = kit and PROBE in command
    log({
        "tool": payload.get("tool_name"),
        "subagent_type": tool_input.get("subagent_type"),
        "command": command,
        "cwd": cwd,
        "kit_project": kit,
        "blocked": blocked,
        "plugin_root_set": bool(os.environ.get("CLAUDE_PLUGIN_ROOT")),
    })
    if blocked:
        print(f"ekspike gate: '{PROBE}' is blocked in a kit project", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
