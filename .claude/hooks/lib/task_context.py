#!/usr/bin/env python3
"""Shared task attribution for hooks — answers "which task is this tool call
about?" from a *structural* signal only.

Used by `post_tool_trace.py` (which trace file a record lands in) and
`pre_agent_step_limit.py` (which task a tool call is counted against). Both
previously took the first `T\\d{3}` substring found anywhere in the tool
payload, so merely *reading* a file whose body mentions a task ID attributed the
call to that task. A wrong tag is worse than a missing one: attribution comes
from where the work is happening, never from what the text happens to mention.

The structural-reference idea is lifted from
`pre_agent_validate_guide.py:extract_structural_task_ids` (T022), which already
solved the same problem for the agent-spawn hard block.

Precedence — first match wins:

  1. ``CLAUDE_ACTIVE_TASK`` env var, when it is well-formed (``T`` + 3 digits,
     case-insensitive). Anything else is ignored rather than trusted — this is
     the only externally-supplied value that reaches a file name.

     **Known-dead in practice (T047):** a hook process is spawned by the
     harness as a *sibling* of the tool call, not a child of the command run
     inside it. It inherits the harness's own environment, never the
     subshell an ``export FOO=bar && cmd`` or ``FOO=bar cmd`` creates inside a
     single ``Bash`` tool call. This precedence slot still fires correctly
     when the var is set in the process that launched the whole session
     (e.g. a sub-agent's terminal, before ``claude`` starts) — it just cannot
     be set *from inside* a running session. See slot 2.
  2. **The active-task state file** (T047), ``.claude/hooks/.state/active_task``
     — a plain two-line file (``Txxx`` on line 1, an ISO-8601 UTC
     "written at" timestamp on line 2) that any tool call *inside a running
     session* can write with a shell redirect, which is the channel slot 1
     cannot reach mid-session. Rejected when malformed, unreadable, or older
     than ``CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S`` seconds (default 21600 = 6h)
     — a stale pointer left over from a finished task is worse than no
     pointer (the exact T043 mis-attribution class), so age alone degrades it
     to absent rather than trusting it forever. There is no automated
     completion signal that clears it (see `post_agent_move_to_review.py`'s
     docstring for why); clearing is manual, same as the step-limit counters.

     **Path resolution (T047 Stage 4 fix — see `_resolve_root`).** The state
     file's root is ``$CLAUDE_PROJECT_DIR`` when set, never ``__file__``
     arithmetic alone. The harness always invokes hooks as
     ``$CLAUDE_PROJECT_DIR/.claude/hooks/*.py`` (see `settings.json`) — the
     *main checkout*, regardless of which worktree's cwd triggered the tool
     call. A Stage-3 sub-agent's cwd is its own worktree, so a naive
     ``__file__``-relative path written a level below (as the first cut of
     this fix did) resolves to two *different* files: the agent writes
     ``<worktree>/.claude/hooks/.state/active_task``, the live hook reads
     ``<main-checkout>/.claude/hooks/.state/active_task``. Anchoring to
     ``$CLAUDE_PROJECT_DIR`` closes that gap — both agent-side shell
     redirects (`craft-spawn-prompt`'s instruction) and this module resolve
     the same root the harness already uses for hook wiring itself.
     **Known limitation, not solved here:** because the root is shared by
     every worktree using the same checkout, two tasks whose Bash calls are
     in flight at the same time can still race and mis-attribute each
     other's calls. Safe for the common case this task was scoped to fix (one
     task's verification run at a time); not a fix for true concurrent
     Stage 3 execution. Flagged to the Supervisor rather than solved here.
  3. A ``TASK_GUIDE_Txxx.md`` reference inside a **path-valued** ``tool_input``
     field (``file_path``, ``notebook_path``, ``path``). Path fields only, an
     explicit list — a whole-payload scan is the defect being removed. This is
     what makes writing/reading a task's own guide attribute to it.
  4. ``Agent`` calls only: a structural reference inside ``tool_input.prompt`` —
     a ``TASK_GUIDE_Txxx.md`` path, or an explicit ``Task ID:`` declaration
     line. Only an ``Agent`` spawn prompt is task-scoped by construction; any
     other tool's prompt-ish field is free text.
  5. Otherwise ``None`` — unattributed. The caller decides what that means
     (`_untagged.jsonl` for the trace; no counting for the step limit).

Deliberate decisions:

* **A ``Bash`` ``command`` string is never scanned**, even when it legitimately
  contains a guide path (``cat tasks/TASK_GUIDE_T012.md``). Command text is free
  text that can quote arbitrary file content; scanning it is the same class of
  guess this module exists to remove. Such a call is unattributed.
* **``tool_response`` is never read.** A tool's *output* describes what a file
  says, not what the agent is working on.
* Task IDs are matched case-insensitively and normalized to upper case with at
  least 3 digits (``t44`` and ``T044`` are the same bucket, never two).

``resolve_task_id`` never raises: any unexpected input degrades to ``None``, so
a hook that runs on every tool call in the repo can never crash or block on it.
"""
import os
import re
from datetime import datetime, timezone

ENV_VAR = "CLAUDE_ACTIVE_TASK"

# tool_input fields whose value is a file-system path. Explicit list by design.
PATH_FIELDS = ("file_path", "notebook_path", "path")

ENV_TASK_PATTERN = re.compile(r"T(\d{3})\Z", re.IGNORECASE)
GUIDE_PATH_PATTERN = re.compile(r"TASK_GUIDE_T(\d+)(?:_[A-Z0-9_]+)?\.md", re.IGNORECASE)
TASK_ID_DECLARATION_PATTERN = re.compile(
    r"(?:\*\*Task ID\*\*|Task ID)\s*:\s*T(\d+)\b", re.IGNORECASE
)

_LIB_DIR = os.path.dirname(os.path.abspath(__file__))
_HOOKS_DIR = os.path.dirname(_LIB_DIR)
_FILE_ROOT = os.path.dirname(os.path.dirname(_HOOKS_DIR))


def _resolve_root():
    """Where the active-task state file lives. Prefer $CLAUDE_PROJECT_DIR —
    the harness sets it to the main checkout for every hook invocation
    (settings.json already relies on it for every hook command), regardless
    of which worktree's cwd triggered the tool call. Falling back to
    __file__ arithmetic would silently resolve to whichever copy of this
    module happens to execute (the worktree's, in a subprocess-sandboxed
    test) — which is exactly the split that made the state file unreadable
    by the real hook (T047 Stage 4 review): an agent's `mkdir -p
    .claude/hooks/.state && ... > .claude/hooks/.state/active_task`, run
    from a worktree cwd, wrote to `<worktree>/.claude/hooks/.state/`, while
    the live hook — always invoked as `$CLAUDE_PROJECT_DIR/.claude/hooks/*.py`
    — read `<main-checkout>/.claude/hooks/.state/`. Different files, so the
    agent's own writes were invisible to the hook it was trying to satisfy.
    Env var wins when set (even to a bogus/missing path — `os.path.join` and
    a later `open()` failure both degrade to "file not found", handled by
    `_task_id_from_state_file`'s own never-raises contract); otherwise fall
    back to __file__ arithmetic so the module still works when
    $CLAUDE_PROJECT_DIR is unset (e.g. this module invoked directly in a
    test or a checkout with no harness wrapping it)."""
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    return env_root if env_root else _FILE_ROOT


# Structural, writable-from-a-Bash-tool-call channel (T047). See module
# docstring, precedence slot 2, for why this exists and its known limits.
# Resolved once at import time — matches every other module-level constant
# here (PATH_FIELDS, the compiled patterns); see resolve_task_id's
# never-raises contract for what happens if the resolved path is bogus.
STATE_DIR = os.path.join(_resolve_root(), ".claude", "hooks", ".state")
ACTIVE_TASK_FILE = os.path.join(STATE_DIR, "active_task")
ACTIVE_TASK_MAX_AGE_S = int(
    os.environ.get("CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S", "21600")  # 6h
)


def normalize_task_id(digits):
    """`44` -> `T044`; digit strings longer than 3 are kept as-is."""
    return "T" + str(digits).zfill(3)


def _task_id_from_env():
    raw = os.environ.get(ENV_VAR, "")
    match = ENV_TASK_PATTERN.match(raw.strip())
    return normalize_task_id(match.group(1)) if match else None


def _task_id_from_state_file():
    """Read + validate the active-task state file. Never raises: any read
    error, bad format, or stale timestamp degrades to None (falls through to
    the next precedence slot), never to a trusted-but-wrong task ID."""
    try:
        with open(ACTIVE_TASK_FILE) as f:
            lines = f.read().splitlines()
        if len(lines) < 2:
            return None

        match = ENV_TASK_PATTERN.match(lines[0].strip())
        if not match:
            return None

        written_at = datetime.fromisoformat(lines[1].strip().replace("Z", "+00:00"))
        if written_at.tzinfo is None:
            written_at = written_at.replace(tzinfo=timezone.utc)
        age_s = (datetime.now(timezone.utc) - written_at).total_seconds()
        if age_s < 0 or age_s > ACTIVE_TASK_MAX_AGE_S:
            return None

        return normalize_task_id(match.group(1))
    except Exception:
        return None


def _task_id_from_path_fields(tool_input):
    for field in PATH_FIELDS:
        value = tool_input.get(field)
        if not isinstance(value, str):
            continue
        match = GUIDE_PATH_PATTERN.search(value)
        if match:
            return normalize_task_id(match.group(1))
    return None


def _task_id_from_agent_prompt(tool_input):
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return None
    for pattern in (GUIDE_PATH_PATTERN, TASK_ID_DECLARATION_PATTERN):
        match = pattern.search(prompt)
        if match:
            return normalize_task_id(match.group(1))
    return None


def resolve_task_id(event):
    """Return the Task ID (`Txxx`) this hook event structurally belongs to, or
    None when nothing structural says which task it is. Never raises."""
    try:
        task_id = _task_id_from_env()
        if task_id:
            return task_id

        task_id = _task_id_from_state_file()
        if task_id:
            return task_id

        tool_input = event.get("tool_input") if isinstance(event, dict) else None
        if not isinstance(tool_input, dict):
            return None

        task_id = _task_id_from_path_fields(tool_input)
        if task_id:
            return task_id

        if event.get("tool_name") == "Agent":
            return _task_id_from_agent_prompt(tool_input)

        return None
    except Exception:
        return None
