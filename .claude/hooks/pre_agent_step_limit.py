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

Counters live in .claude/hooks/.state/step_count_<session>_<task>.txt, keyed
on both the event's session_id and the task ID (T056) — a task-only key let
one session's exhausted budget block every other session that resolved to
the same task, including the Supervisor's. A counter file older than
CLAUDE_STEP_COUNT_TTL_S (default 6h) is treated as count 0 rather than
carried forward, so a task's counter cannot outlive it indefinitely (T056):
post_agent_move_to_review.py is deliberately inert as a writer (T044), so
nothing else ever resets these files.
"""
import json
import os
import re
import sys
import time

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
STATE_DIR = os.path.join(ROOT, ".claude", "hooks", ".state")
STEP_LIMIT = int(os.environ.get("CLAUDE_STEP_LIMIT", "40"))

STEP_COUNT_TTL_DEFAULT_S = 21600  # 6h

# Untrusted: session_id reaches a file name. Allow only this charset.
_SESSION_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9]")
_SESSION_MAX_LEN = 64


def _resolve_step_count_ttl_s():
    """Staleness window for step counters, overridable by env. Parsed
    defensively because this runs at import time — a bare int() would raise
    on a malformed value and take the whole module down before the
    try/except around the import even applies (mirrors
    task_context._resolve_max_age_s, T056)."""
    raw = os.environ.get("CLAUDE_STEP_COUNT_TTL_S", "").strip()
    if not raw:
        return STEP_COUNT_TTL_DEFAULT_S
    try:
        parsed = int(raw)
    except ValueError:
        return STEP_COUNT_TTL_DEFAULT_S
    return parsed if parsed > 0 else STEP_COUNT_TTL_DEFAULT_S


STEP_COUNT_TTL_S = _resolve_step_count_ttl_s()


def _sanitize_session_id(session_id):
    """Reduce an untrusted session_id to a safe file-name fragment. Falls
    back to a literal when absent, empty, non-string, or sanitizes to
    nothing — never produces an empty segment that could collide across
    sessions."""
    if not isinstance(session_id, str):
        return "nosession"
    cleaned = _SESSION_SANITIZE_PATTERN.sub("", session_id)[:_SESSION_MAX_LEN]
    return cleaned if cleaned else "nosession"

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

    session = _sanitize_session_id(
        event.get("session_id") if isinstance(event, dict) else None
    )

    counter_name = f"step_count_{session}_{task_id}.txt"
    counter_path = os.path.join(STATE_DIR, counter_name)

    try:
        os.makedirs(STATE_DIR, exist_ok=True)
    except Exception:
        sys.exit(0)

    count = 0
    if os.path.exists(counter_path):
        try:
            age_s = time.time() - os.path.getmtime(counter_path)
            # Clock skew (mtime in the future) is treated as fresh, never as
            # expired -- mirrors task_context._task_id_from_state_file's
            # age_s < 0 handling.
            if 0 <= age_s <= STEP_COUNT_TTL_S:
                with open(counter_path) as f:
                    count = int(f.read().strip() or "0")
        except Exception:
            count = 0

    count += 1

    try:
        with open(counter_path, "w") as f:
            f.write(str(count))
    except Exception:
        sys.exit(0)

    if count > STEP_LIMIT:
        result = {
            "decision": "block",
            "reason": (
                f"[hook:pre_agent_step_limit] {task_id} has exceeded "
                f"{STEP_LIMIT} tool calls without reaching Ready for Review. "
                "Killing the run to prevent an infinite loop / token waste. "
                "Supervisor: stop, inspect memory/event-trace/"
                f"{task_id}.jsonl, and either escalate to the user or "
                "manually reset .claude/hooks/.state/"
                f"{counter_name} after confirming the task isn't actually stuck."
            )
        }
        print(json.dumps(result))

main()
