#!/usr/bin/env python3
"""
PreToolUse hook — fires before every tool call (all matchers).

Deterministic guardrail against runaway loops: counts tool calls per
Task ID and blocks once a task exceeds CLAUDE_STEP_LIMIT (default 40)
calls. This forces the Supervisor to stop and escalate to the user
instead of letting a stuck task burn tool calls / tokens indefinitely.

The Task ID is resolved structurally (see lib/task_context.py) — a call
is counted against a task only when a guide path, an Agent spawn prompt,
or CLAUDE_ACTIVE_TASK says so. A call whose text merely mentions a Task
ID is unattributed and counted against nothing.

Counters live in .claude/hooks/.state/step_count_<task>.txt and are
reset by post_agent_move_to_review.py once a task reaches Ready for Review.
"""
import json
import os
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
STATE_DIR = os.path.join(ROOT, ".claude", "hooks", ".state")
STEP_LIMIT = int(os.environ.get("CLAUDE_STEP_LIMIT", "40"))

# Hooks run as standalone scripts from an arbitrary cwd, so the shared lib is
# imported off __file__, not off the import path. Fail open: a broken import
# must degrade to "unattributed", never block a tool call.
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from task_context import resolve_task_id
except Exception:
    def resolve_task_id(event):
        return None


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    task_id = resolve_task_id(event)
    if not task_id:
        sys.exit(0)

    os.makedirs(STATE_DIR, exist_ok=True)
    counter_path = os.path.join(STATE_DIR, f"step_count_{task_id}.txt")

    count = 0
    if os.path.exists(counter_path):
        try:
            with open(counter_path) as f:
                count = int(f.read().strip() or "0")
        except Exception:
            count = 0

    count += 1

    with open(counter_path, "w") as f:
        f.write(str(count))

    if count > STEP_LIMIT:
        result = {
            "decision": "block",
            "reason": (
                f"[hook:pre_agent_step_limit] {task_id} has exceeded "
                f"{STEP_LIMIT} tool calls without reaching Ready for Review. "
                "Killing the run to prevent an infinite loop / token waste. "
                "Supervisor: stop, inspect memory/event-trace/"
                f"{task_id}.jsonl, and either escalate to the user or "
                "manually reset .claude/hooks/.state/step_count_"
                f"{task_id}.txt after confirming the task isn't actually stuck."
            )
        }
        print(json.dumps(result))

main()
