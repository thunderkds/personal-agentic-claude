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
     be set *from inside* a running session. See slots 2 and 3.
  2. **Spawn binding** (T196) — sub-agent calls only. The harness puts
     ``agent_id`` on every hook event a sub-agent's tool call fires, and
     nothing on a main-session call. The sub-agent's transcript is
     ``<dirname(transcript_path)>/<session_id>/subagents/agent-<agent_id>.jsonl``
     and its first line is the spawn prompt, verbatim. The task is read with
     the same two patterns slot 5 uses, but in the opposite order: an explicit
     ``Task ID:`` line wins, and the first ``TASK_GUIDE_Txxx.md`` path counts
     only when there is none — a prompt may cite another task's guide as
     context, and a binding attributes every call. The agent writes
     nothing. The result is cached at
     ``.state/agent_task/<session_id>/<agent_id>`` so later calls do not
     re-read the transcript. That transcript layout is internal to Claude Code
     and undocumented (measured on 2.1.312, `tasks/TASK_GUIDE_T196.md` F1–F3):
     if it moves, this slot yields nothing and resolution falls through.
  3. **The per-session state file** (T196; replaces T047's shared file),
     ``.claude/hooks/.state/active_task.d/<session_id>`` — a plain two-line file
     (``Txxx`` on line 1, an ISO-8601 UTC "written at" timestamp on line 2)
     that a ``Bash`` tool call inside a running session writes with a shell
     redirect, using ``$CLAUDE_CODE_SESSION_ID`` (set in every ``Bash`` call's
     environment, equal to the hook's ``session_id``, F2). The
     ``<session_id>`` comes from the event, never from the file. Rejected when
     malformed, unreadable, or older than ``CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S``
     seconds (default 21600 = 6h) — a stale pointer left over from a finished
     task is worse than no pointer (the T043 mis-attribution class). Nothing
     clears it automatically; the age rule degrades it.

     **Why per session (T196).** T047's file was ``.state/active_task``, one
     per checkout. On 2026-10-28 the T190 agent wrote it and, six minutes
     later, another live session overwrote it with ``T188``: 89 of T190's
     calls were filed under T188, and ``trace_shows_verification("T188")``
     passed on T190's test run without anyone lying. A sub-agent shares its
     parent's ``session_id`` — slot 2 is what separates sibling sub-agents.
     **The shared file is no longer read** (D2): a file left there is ignored.
     **Residual:** two sub-agents of one session spawned *without* a structural
     ID in their prompt both fall through to that session's file.

     **Path resolution (T047 Stage 4 fix — see `_resolve_root`).** The state
     root is ``$CLAUDE_PROJECT_DIR`` when set, never ``__file__`` arithmetic
     alone. The harness always invokes hooks as
     ``$CLAUDE_PROJECT_DIR/.claude/hooks/*.py`` (see `settings.json`) — the
     *main checkout*, regardless of which worktree's cwd triggered the tool
     call. A writer must therefore use the main checkout's literal absolute
     path: a cwd-relative path from a worktree writes a file the hook never
     reads, and ``$CLAUDE_PROJECT_DIR`` is empty inside a ``Bash`` tool call.

     **Path safety (D3).** ``session_id`` and ``agent_id`` reach a file name
     only when they match ``SAFE_KEY`` (letters, digits, ``_``, ``-``; 1–128);
     otherwise slots 2 and 3 are skipped. The transcript path is derived only
     from the event's absolute ``transcript_path``, and is only ever read.
  4. A ``TASK_GUIDE_Txxx.md`` reference inside a **path-valued** ``tool_input``
     field (``file_path``, ``notebook_path``, ``path``). Path fields only, an
     explicit list — a whole-payload scan is the defect being removed. This is
     what makes writing/reading a task's own guide attribute to it.
  5. ``Agent`` calls only: a structural reference inside ``tool_input.prompt`` —
     a ``TASK_GUIDE_Txxx.md`` path, or an explicit ``Task ID:`` declaration
     line. Only an ``Agent`` spawn prompt is task-scoped by construction; any
     other tool's prompt-ish field is free text.
  6. Otherwise ``None`` — unattributed. The caller decides what that means
     (`_untagged.jsonl` for the trace; no counting for the step limit).

Deliberate decisions:

* **A ``Bash`` ``command`` string is never scanned**, even when it legitimately
  contains a guide path (``cat tasks/TASK_GUIDE_T012.md``). Command text is free
  text that can quote arbitrary file content; scanning it is the same class of
  guess this module exists to remove. Such a call is unattributed.
* **``tool_response`` is never read.** A tool's *output* describes what a file
  says, not what the agent is working on. The one file slot 2 reads is the
  sub-agent's own transcript, and only its first line: the spawn prompt, which
  is task-scoped by construction exactly as slot 5's ``Agent`` prompt is.
* Task IDs are matched case-insensitively and normalized to upper case with at
  least 3 digits (``t44`` and ``T044`` are the same bucket, never two).

``resolve_task_id`` never raises: any unexpected input degrades to ``None``, so
a hook that runs on every tool call in the repo can never crash or block on it.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

# Board IDs (T153). This module must never fail to import (both callers would lose
# attribution repo-wide), so an absent `board` package degrades to today's `T` IDs.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from board.config import (  # noqa: E402
        PATH_SAFE_ID,
        normalize_task_id as _canonical_task_id,
        task_id_pattern,
    )
except Exception:  # pragma: no cover - exercised by copying this file alone
    PATH_SAFE_ID = re.compile(r"\AT\d+\Z")

    def _canonical_task_id(task_id):
        return "T" + str(task_id).strip().lstrip("Tt").zfill(3)

    def task_id_pattern(root=None, local=r"T\d+", bounded=False):
        return rf"(?<![A-Za-z0-9_])(?:{local})(?![A-Za-z0-9_])" if bounded else local

ENV_VAR = "CLAUDE_ACTIVE_TASK"

# tool_input fields whose value is a file-system path. Explicit list by design.
PATH_FIELDS = ("file_path", "notebook_path", "path")

# The `T` alternatives below are today's patterns; `task_id_pattern` adds the board's
# `id_pattern` (T153) when `.claude/board.json` sets one. Built per call, not at import:
# the config lives under `_resolve_root()`, and a hook process is short-lived anyway.
ENV_TASK_LOCAL = r"T\d{3}"


def _env_task_pattern():
    return re.compile(rf"({task_id_pattern(_resolve_root(), ENV_TASK_LOCAL)})\Z", re.IGNORECASE)


def _guide_path_pattern():
    return re.compile(rf"TASK_GUIDE_({task_id_pattern(_resolve_root())})(?:_[A-Z0-9_]+)?\.md",
                      re.IGNORECASE)


def _task_id_declaration_pattern():
    return re.compile(rf"(?:\*\*Task ID\*\*|Task ID)\s*:\s*"
                      rf"({task_id_pattern(_resolve_root(), bounded=True)})", re.IGNORECASE)


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
    .claude/hooks/.state && ... > .claude/hooks/.state/active_task` (T047's
    shared file, no longer read since T196), run from a worktree cwd, wrote to `<worktree>/.claude/hooks/.state/`, while
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


# Structural channels, per caller (T196). See module docstring, precedence
# slots 2 and 3. Resolved once at import time — matches every other
# module-level constant here (PATH_FIELDS, the compiled patterns); see
# resolve_task_id's never-raises contract for what happens if the resolved
# path is bogus. T047's shared `STATE_DIR/active_task` is deliberately not
# named here: it is no longer read (D2).
STATE_DIR = os.path.join(_resolve_root(), ".claude", "hooks", ".state")
ACTIVE_TASK_DIR = os.path.join(STATE_DIR, "active_task.d")  # slot 3: <session_id>
AGENT_TASK_DIR = os.path.join(STATE_DIR, "agent_task")     # slot 2 cache: <session_id>/<agent_id>
ACTIVE_TASK_MAX_AGE_DEFAULT_S = 21600  # 6h

# D3: the only shape of `session_id` / `agent_id` allowed into a file name.
SAFE_KEY = re.compile(r"\A[A-Za-z0-9_-]{1,128}\Z")
# The first transcript line is the whole spawn prompt; read no more than this.
TRANSCRIPT_FIRST_LINE_MAX_BYTES = 1 << 20  # 1 MB


def _resolve_max_age_s():
    """Staleness window for the state file, overridable by env.

    Parsed defensively because this runs at **import** time, one layer below
    `resolve_task_id`'s never-raises contract. A bare `int(os.environ[...])`
    raises `ValueError` on any non-numeric value (`"6h"`), and both callers
    wrap their `from task_context import ...` in `except Exception` — so a
    single malformed env var would silently disable attribution *repo-wide*,
    including the path-field precedence that has nothing to do with this
    setting. Fail to the default rather than taking the whole module down
    (T047 Stage 4 review).
    """
    raw = os.environ.get("CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S", "").strip()
    if not raw:
        return ACTIVE_TASK_MAX_AGE_DEFAULT_S
    try:
        parsed = int(raw)
    except ValueError:
        return ACTIVE_TASK_MAX_AGE_DEFAULT_S
    return parsed if parsed > 0 else ACTIVE_TASK_MAX_AGE_DEFAULT_S


ACTIVE_TASK_MAX_AGE_S = _resolve_max_age_s()


def normalize_task_id(task_id):
    """`44` / `t44` -> `T044` (digit strings longer than 3 are kept as-is); a board ID
    is upper-cased (`eng-170` -> `ENG-170`). None when the result could not safely
    name a file (an over-broad `id_pattern` must not reach a trace path)."""
    canonical = _canonical_task_id(task_id)
    return canonical if PATH_SAFE_ID.match(canonical) else None


def _task_id_from_env():
    raw = os.environ.get(ENV_VAR, "")
    match = _env_task_pattern().match(raw.strip())
    return normalize_task_id(match.group(1)) if match else None


def _safe_key(value):
    """`value` when it may name a file (D3), else None."""
    return value if isinstance(value, str) and SAFE_KEY.match(value) else None


def _task_id_from_cache(cache_path):
    try:
        with open(cache_path) as f:
            match = _env_task_pattern().match(f.read().strip())
        return normalize_task_id(match.group(1)) if match else None
    except Exception:
        return None


def _write_cache(cache_path, task_id):
    """Best effort: a read-only state dir still resolves, from the transcript."""
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            f.write(task_id + "\n")
    except Exception:
        pass


def _spawn_prompt(transcript_path, session_id, agent_id):
    """The sub-agent's spawn prompt: the first line of its own transcript (F3),
    or None when that line is missing, too long, or not a user message."""
    if not isinstance(transcript_path, str) or not os.path.isabs(transcript_path):
        return None
    path = os.path.join(os.path.dirname(transcript_path), session_id, "subagents",
                        f"agent-{agent_id}.jsonl")
    with open(path, "rb") as f:
        first = f.readline(TRANSCRIPT_FIRST_LINE_MAX_BYTES + 1)
    if len(first) > TRANSCRIPT_FIRST_LINE_MAX_BYTES:
        return None
    record = json.loads(first.decode("utf-8"))
    if not isinstance(record, dict):
        return None
    message = record.get("message")
    if record.get("type") != "user" or not isinstance(message, dict):
        return None
    if message.get("role") != "user" or not isinstance(message.get("content"), str):
        return None
    return message["content"]


def _task_id_from_spawn_prompt(prompt):
    """Slot 2's reading of a spawn prompt: an explicit `Task ID:` declaration
    wins; the first guide path counts only when there is none. Slot 5 scans
    guide paths first, which is acceptable for one `Agent` record but not here:
    a binding attributes every call the sub-agent makes and is cached, so a
    prompt that cites another task's guide before its own `Task ID:` line
    (T196 Stage 4 P2) must not bind to that other task."""
    if not isinstance(prompt, str):
        return None
    for pattern in (_task_id_declaration_pattern(), _guide_path_pattern()):
        match = pattern.search(prompt)
        if match:
            return normalize_task_id(match.group(1))
    return None


def _task_id_from_spawn_binding(event):
    """Slot 2: the task a sub-agent's spawn prompt structurally names. Never
    raises; a non-binding prompt is not cached, so it is simply re-checked."""
    try:
        session_id = _safe_key(event.get("session_id"))
        agent_id = _safe_key(event.get("agent_id"))
        if not session_id or not agent_id:
            return None
        cache_path = os.path.join(AGENT_TASK_DIR, session_id, agent_id)
        task_id = _task_id_from_cache(cache_path)
        if task_id:
            return task_id
        prompt = _spawn_prompt(event.get("transcript_path"), session_id, agent_id)
        task_id = _task_id_from_spawn_prompt(prompt)
        if task_id:
            _write_cache(cache_path, task_id)
        return task_id
    except Exception:
        return None


def _task_id_from_state_file(event):
    """Slot 3: read + validate this session's state file. Never raises: an
    unsafe session ID, any read error, bad format, or stale timestamp degrades
    to None (falls through to the next precedence slot), never to a
    trusted-but-wrong task ID."""
    try:
        session_id = _safe_key(event.get("session_id"))
        if not session_id:
            return None
        with open(os.path.join(ACTIVE_TASK_DIR, session_id)) as f:
            lines = f.read().splitlines()
        if len(lines) < 2:
            return None

        match = _env_task_pattern().match(lines[0].strip())
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
        match = _guide_path_pattern().search(value)
        if match:
            return normalize_task_id(match.group(1))
    return None


def _task_id_from_agent_prompt(tool_input):
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return None
    for pattern in (_guide_path_pattern(), _task_id_declaration_pattern()):
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

        if not isinstance(event, dict):
            return None

        task_id = _task_id_from_spawn_binding(event)
        if task_id:
            return task_id

        task_id = _task_id_from_state_file(event)
        if task_id:
            return task_id

        tool_input = event.get("tool_input")
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
