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
  2. A ``TASK_GUIDE_Txxx.md`` reference inside a **path-valued** ``tool_input``
     field (``file_path``, ``notebook_path``, ``path``). Path fields only, an
     explicit list — a whole-payload scan is the defect being removed. This is
     what makes writing/reading a task's own guide attribute to it.
  3. ``Agent`` calls only: a structural reference inside ``tool_input.prompt`` —
     a ``TASK_GUIDE_Txxx.md`` path, or an explicit ``Task ID:`` declaration
     line. Only an ``Agent`` spawn prompt is task-scoped by construction; any
     other tool's prompt-ish field is free text.
  4. Otherwise ``None`` — unattributed. The caller decides what that means
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

ENV_VAR = "CLAUDE_ACTIVE_TASK"

# tool_input fields whose value is a file-system path. Explicit list by design.
PATH_FIELDS = ("file_path", "notebook_path", "path")

ENV_TASK_PATTERN = re.compile(r"T(\d{3})\Z", re.IGNORECASE)
GUIDE_PATH_PATTERN = re.compile(r"TASK_GUIDE_T(\d+)(?:_[A-Z0-9_]+)?\.md", re.IGNORECASE)
TASK_ID_DECLARATION_PATTERN = re.compile(
    r"(?:\*\*Task ID\*\*|Task ID)\s*:\s*T(\d+)\b", re.IGNORECASE
)


def normalize_task_id(digits):
    """`44` -> `T044`; digit strings longer than 3 are kept as-is."""
    return "T" + str(digits).zfill(3)


def _task_id_from_env():
    raw = os.environ.get(ENV_VAR, "")
    match = ENV_TASK_PATTERN.match(raw.strip())
    return normalize_task_id(match.group(1)) if match else None


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
