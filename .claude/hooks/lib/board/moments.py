"""Pull moments and "my task" (T157, FR-009, FR-010, FR-011).

The board cache is refreshed at four moments — session start (`wake`), before a spawn,
before Ready for Review, before merge — by running `scripts/board_sync.py pull` as a
subprocess with a short timeout. A failed or hanging pull never blocks work: the caller
gets one warning line and carries on with the cache it has.

Board mode is read from `.claude/board.json`: `online` when it names a `board`, `local`
when the file is missing or names none, `unusable` when it exists but cannot be read.
Callers decide what `unusable` means for them; each picks the side that cannot loosen a
gate. Local mode runs nothing and writes nothing.

Stdlib only, no network of its own.
"""
import hashlib
import os
import re
import subprocess
import sys

from board import outbox
from board.config import config_path, load_config, normalize_task_id, PATH_SAFE_ID

PULL_TIMEOUT_S = 10
STATE_DIR = os.path.join(".claude", "hooks", ".state")
# Printed by render.HEADER on every pulled PROJECT_KANBAN.md.
BOARD_CACHE_MARKER = "Board cache, pulled from the board by"


def board_mode(root):
    """`online`, `local` or `unusable`."""
    config = load_config(root)
    if config is None:
        return "unusable" if os.path.exists(config_path(root)) else "local"
    return "online" if config.get("board") else "local"


def unsynced_count(root):
    """Queued board writes in the outbox (T156's `outbox.count`); 0 if none or unreadable."""
    try:
        return outbox.count(root)
    except Exception:  # never let a broken outbox break a pull moment or the merge gate
        return 0


def pull_cache(root, timeout=PULL_TIMEOUT_S):
    """Run `board_sync.py pull`. None on success, else the warning line to show.

    Output is captured, never echoed: a hook's stdout is its decision channel, and
    board_sync's own messages are for a human running it by hand."""
    script = os.path.join(root, "scripts", "board_sync.py")
    try:
        done = subprocess.run([sys.executable, script, "pull"], cwd=root,
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
        if done.returncode == 0:
            return None
    except (OSError, subprocess.SubprocessError):
        pass
    return f"board unreachable — using cache ({unsynced_count(root)} unsynced)"


def safe_task_id(task_id):
    """Canonical ID if it may name a state file, else None."""
    canonical = normalize_task_id(task_id)
    return canonical if PATH_SAFE_ID.match(canonical) else None


def guide_hash(root, task_id):
    """sha256 of the cached `tasks/TASK_GUIDE_<ID>.md`, or `missing`."""
    try:
        with open(os.path.join(root, "tasks", f"TASK_GUIDE_{task_id}.md"), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return "missing"


def guide_hash_path(root, task_id):
    return os.path.join(root, STATE_DIR, f"guide_hash_{task_id}.txt")


# --- My task -----------------------------------------------------------------------

ASSIGNEE_FIELD = re.compile(r"@([A-Za-z0-9._-]+)")


def row_fields(line):
    """Split a rendered row on its unescaped `|`. render.escape backslash-escapes every
    `|` and `\\` in board text, so only the separators render.row writes survive."""
    fields, current, chars = [], [], iter(line)
    for ch in chars:
        if ch == "\\":
            current.append(ch + next(chars, ""))
        elif ch == "|":
            fields.append("".join(current))
            current = []
        else:
            current.append(ch)
    fields.append("".join(current))
    return fields


def row_assignees(line):
    """Every `@<token>` field after the title field."""
    return [m.group(1) for f in row_fields(line)[1:]
            for m in [ASSIGNEE_FIELD.fullmatch(f.strip())] if m]


def my_blocking_tasks(rows, me, kanban):
    """(IDs that block my push, warnings) for the In Progress `(id, line)` rows.

    Blocks on every row — the gate before T157 — when `me` is not usable or the cache
    is not a board render (a failed pull left a hand-written board). Otherwise a row
    blocks when its assignee is me (case-insensitive: a near-match blocks rather than
    passes) or when it carries more than one assignee field. Unassigned rows are warned
    about, not blocked."""
    all_ids = [task_id for task_id, _ in rows]
    me_token = re.sub(r"[^A-Za-z0-9._-]", "", me) if isinstance(me, str) else ""
    if not me_token:
        return all_ids, ["`me` is missing from .claude/board.json — every In Progress "
                         "task blocks (safe side)"]
    if BOARD_CACHE_MARKER not in kanban:
        return all_ids, ["PROJECT_KANBAN.md is not a board render — every In Progress "
                         "task blocks (safe side)"]
    blocking, warnings = [], []
    for task_id, line in rows:
        assignees = row_assignees(line)
        if not assignees:
            warnings.append(f"{task_id} is In Progress but unassigned — not blocking")
        elif len(assignees) > 1 or assignees[0].casefold() == me_token.casefold():
            blocking.append(task_id)
    return blocking, warnings
