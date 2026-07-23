#!/usr/bin/env python3
"""
PostToolUse hook — fires after every tool call (all matchers).

Advanced event tracing: appends a structured record of what actually
happened to memory/event-trace/<task>.jsonl. This gives the Stage 4/5
"Verify" step (and pre_bash_block_unsafe_merge.py) a real history to
inspect instead of trusting the model's claim that it ran tests.

Attribution is structural only (see lib/task_context.py): a record is
filed under a Task ID because a guide path, an Agent spawn prompt, or
CLAUDE_ACTIVE_TASK says so — never because the text of a file the agent
read happens to mention a Task ID.

Records with no discoverable Task ID are written to
memory/event-trace/_untagged.jsonl instead of being dropped, so nothing
is silently lost.
"""
import json
import os
import sys
from datetime import datetime, timezone

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
TRACE_DIR = os.path.join(ROOT, "memory", "event-trace")
MAX_SUMMARY_LEN = 300

# Hooks run as standalone scripts from an arbitrary cwd, so the shared lib is
# imported off __file__, not off the import path. Fail open: a broken import
# must degrade to "unattributed", never crash a tool call.
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from task_context import resolve_task_id
except Exception:
    def resolve_task_id(event):
        return None


def summarize(tool_input):
    text = json.dumps(tool_input)
    return text[:MAX_SUMMARY_LEN]


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = event.get("tool_name", "unknown")
    tool_input = event.get("tool_input", {})
    tool_response = event.get("tool_response", {})

    task_id = resolve_task_id(event) or "_untagged"

    os.makedirs(TRACE_DIR, exist_ok=True)
    trace_path = os.path.join(TRACE_DIR, f"{task_id}.jsonl")

    is_error = bool(tool_response.get("is_error")) if isinstance(tool_response, dict) else False

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "summary": summarize(tool_input),
        "is_error": is_error,
    }

    with open(trace_path, "a") as f:
        f.write(json.dumps(record) + "\n")

main()
