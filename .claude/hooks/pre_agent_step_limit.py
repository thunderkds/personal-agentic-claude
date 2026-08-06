#!/usr/bin/env python3
"""
PreToolUse hook — fires before every tool call (all matchers).

Deterministic guardrail against runaway loops: counts tool calls per
Task ID and blocks once a task exceeds CLAUDE_STEP_LIMIT (default 90)
calls. This forces the run to stop and report instead of letting a
stuck task burn tool calls / tokens indefinitely.

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

T057 — self-clearing block: `Bash` and `Read` are both blocked by this
hook's own decision, and `Write` only skips the block when the counter file
does not already exist, so a session that hits the limit had no tool left
that could clear its own counter — 2026-08-06 recorded four hard lockouts,
each requiring a human to run `rm` by hand. This hook now resets the
counter to 0 in the SAME invocation that emits the block: the current
(over-limit) call still dies — the guard still interrupts a runaway — but
the very next call from any session for this task is allowed again. No
session can be left permanently unable to act, and no manual `rm` is ever
required. Trade-off, accepted deliberately: a genuinely stuck loop is now
interrupted every STEP_LIMIT calls rather than halted for good. That is an
acceptable trade because the guard's observed cost (four lockouts, two lost
agent runs, zero real runaways actually caught) has outweighed its
benefit. A separate, durable `block_count` field (persisted alongside
`count`, and NOT reset when `count` resets) lets the block message escalate
its wording after repeated blocks on the same task, so a truly stuck loop
remains visible even though it is no longer permanently halted (AC6).

Counter file format (two lines): line 1 is `count`, line 2 is
`block_count`. A legacy one-line file (written by T056, before block_count
existed) is read as `block_count` 0 — it must not crash the parse.
"""
import json
import os
import re
import sys
import time

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
STATE_DIR = os.path.join(ROOT, ".claude", "hooks", ".state")

# Raised from 40 (T057). Evidence: T054 legitimately consumed 42 calls,
# making concrete forward progress on every one, doing a real ~7-file C2
# task; T056 took 38 on a comparable hook change. 40 sat below both
# observed legitimate workloads, so it was tripping on real work, not on
# runaways (0 real runaways were ever caught by this guard). 90 gives
# roughly 2x headroom over the largest observed legitimate run (42) while
# still being low enough to interrupt an actual infinite loop long before
# it burns an unbounded number of tool calls/tokens.
STEP_LIMIT = int(os.environ.get("CLAUDE_STEP_LIMIT", "90"))

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


def _parse_counter_contents(raw):
    """Parse a counter file's contents into (count, block_count). Accepts
    both the current two-line format and T056's legacy one-line format
    (block_count implicitly 0). Never raises -- any malformed line degrades
    that field to 0, mirroring the pre-T057 int() fail-open behaviour."""
    lines = raw.splitlines()
    count = 0
    block_count = 0
    if len(lines) >= 1:
        try:
            count = int(lines[0].strip() or "0")
        except Exception:
            count = 0
    if len(lines) >= 2:
        try:
            block_count = int(lines[1].strip() or "0")
        except Exception:
            block_count = 0
    return count, block_count


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
    block_count = 0
    if os.path.exists(counter_path):
        try:
            age_s = time.time() - os.path.getmtime(counter_path)
            # Clock skew (mtime in the future) is treated as fresh, never as
            # expired -- mirrors task_context._task_id_from_state_file's
            # age_s < 0 handling.
            if 0 <= age_s <= STEP_COUNT_TTL_S:
                with open(counter_path) as f:
                    count, block_count = _parse_counter_contents(f.read())
            # else: expired. count resets to 0 (T056 behaviour, unchanged).
            # block_count ALSO resets here: an expired counter means enough
            # wall-clock time (6h+) has passed that this is treated as a
            # fresh attempt at the task, not a continuation of the same
            # stuck loop, so the escalation history should not carry
            # forward across that gap either. (Edge case, decided
            # deliberately per TASK_GUIDE_T057.md.)
        except Exception:
            count = 0
            block_count = 0

    count += 1

    if count > STEP_LIMIT:
        # Self-clearing (T057): reset count to 0 and bump the durable
        # block_count BEFORE emitting the block decision, so a crash after
        # the write (e.g. json.dumps/print failing) can never leave the
        # counter sitting above the limit -- the reset is the part that
        # must not be skipped, the message is best-effort on top of it.
        block_count += 1
        try:
            with open(counter_path, "w") as f:
                f.write(f"0\n{block_count}")
        except Exception:
            # Fail open: even if we can't persist the reset, never block
            # silently-forever -- still emit the block for THIS call, but
            # do not raise. The next call will simply recompute from
            # whatever is on disk (or absent), same as any other
            # unwritable-state-dir case.
            pass

        escalation = ""
        if block_count >= 3:
            escalation = (
                f" This task has now been interrupted {block_count} times "
                "-- it may be genuinely stuck; consider escalating to the "
                "user instead of retrying again."
            )

        result = {
            "decision": "block",
            "reason": (
                f"[hook:pre_agent_step_limit] {task_id} has exceeded "
                f"{STEP_LIMIT} tool calls without reaching Ready for Review. "
                "Killing this call to prevent an infinite loop / token "
                "waste. Stop and report to the Supervisor; inspect "
                f"memory/event-trace/{task_id}.jsonl if available. The "
                "counter has been reset automatically, so the next tool "
                "call for this task will be allowed." + escalation
            )
        }
        print(json.dumps(result))
        return

    try:
        with open(counter_path, "w") as f:
            f.write(f"{count}\n{block_count}")
    except Exception:
        sys.exit(0)


main()
