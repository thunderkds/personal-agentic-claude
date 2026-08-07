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


# --- Agent spawn cost capture (T061) --------------------------------------
# The harness hands PostToolUse the spawn's own accounting in `tool_response`;
# before T061 every field of it but `is_error` was discarded. These maps name
# exactly what is kept, harness key -> record key. The harness sends camelCase;
# every other field in this record is snake_case, so names are translated on
# the way in rather than passed through.
#
# Deliberately NOT copied: `prompt` and `content` (already covered by
# `summary`; duplicating them doubles trace size), `usage.iterations` (an
# unbounded list), and `usage.cache_creation.{ephemeral_5m,ephemeral_1h}` (a
# third nesting level whose totals are already in the two cache_* fields).
SPAWN_TOP_FIELDS = (
    ("totalTokens", "total_tokens"),
    ("totalToolUseCount", "tool_use_count"),
    ("totalDurationMs", "duration_ms"),
    ("resolvedModel", "resolved_model"),
    ("agentType", "agent_type"),
    ("status", "status"),
)
SPAWN_USAGE_FIELDS = (
    ("input_tokens", "input_tokens"),
    ("output_tokens", "output_tokens"),
    ("cache_creation_input_tokens", "cache_creation_input_tokens"),
    ("cache_read_input_tokens", "cache_read_input_tokens"),
)
SPAWN_TOOL_STATS_FIELDS = (
    ("readCount", "read_count"),
    ("searchCount", "search_count"),
    ("bashCount", "bash_count"),
    ("editFileCount", "edit_file_count"),
    ("linesAdded", "lines_added"),
    ("linesRemoved", "lines_removed"),
)


def _pick(source, field_map):
    """Copy only the keys that are actually present. A key that is absent from
    the source stays absent from the result — never carried through as None,
    which would make an unpopulated payload indistinguishable from a real
    zero."""
    if not isinstance(source, dict):
        return {}
    picked = {}
    for src_key, dest_key in field_map:
        if src_key in source:
            picked[dest_key] = source[src_key]
    return picked


def extract_spawn(tool_response):
    """Cost fields of an `Agent` spawn, or None when the payload carries none.

    Fail-open on the same contract as the rest of this hook family (see
    `lib/task_context.py`): a missing, None, string, or partial `tool_response`
    yields None — the record is then written with no `spawn` key at all —
    and nothing here may raise, because this runs on every tool call."""
    try:
        if not isinstance(tool_response, dict):
            return None
        spawn = _pick(tool_response, SPAWN_TOP_FIELDS)
        usage = _pick(tool_response.get("usage"), SPAWN_USAGE_FIELDS)
        if usage:
            spawn["usage"] = usage
        tool_stats = _pick(tool_response.get("toolStats"), SPAWN_TOOL_STATS_FIELDS)
        if tool_stats:
            spawn["tool_stats"] = tool_stats
        return spawn or None
    except Exception:
        return None


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

    # Agent only: every other tool's record shape is unchanged, byte for byte.
    if tool_name == "Agent":
        spawn = extract_spawn(tool_response)
        if spawn:
            record["spawn"] = spawn

    with open(trace_path, "a") as f:
        f.write(json.dumps(record) + "\n")

main()
