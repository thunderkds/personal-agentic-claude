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

from board import outbox, render
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


def split_by_assignee(rows, me, kanban, safe_side):
    """(mine, teammates', unassigned, warnings) for a section's `(id, line)` rows.

    Every row counts as mine — the gate before T157 — when `me` is not usable or the
    cache is not a board render (a failed pull left a hand-written board); `safe_side`
    ends the warning that says so. Otherwise a row is mine when its assignee is me
    (case-insensitive: a near-match counts as mine rather than passing) or when it
    carries more than one assignee field."""
    all_ids = [task_id for task_id, _ in rows]
    me_token = re.sub(r"[^A-Za-z0-9._-]", "", me) if isinstance(me, str) else ""
    if not me_token:
        return all_ids, [], [], [f"`me` is missing from .claude/board.json — {safe_side}"]
    if BOARD_CACHE_MARKER not in kanban:
        return all_ids, [], [], [f"PROJECT_KANBAN.md is not a board render — {safe_side}"]
    mine, teammates, unassigned = [], [], []
    for task_id, line in rows:
        assignees = row_assignees(line)
        if not assignees:
            unassigned.append(task_id)
        elif len(assignees) > 1 or assignees[0].casefold() == me_token.casefold():
            mine.append(task_id)
        else:
            teammates.append(task_id)
    return mine, teammates, unassigned, []


def my_blocking_tasks(rows, me, kanban):
    """(IDs that block my push, warnings) for the In Progress `(id, line)` rows.

    Mine block (see `split_by_assignee`); a teammate's are silent. Unassigned rows are
    warned about, not blocked."""
    mine, _, unassigned, warnings = split_by_assignee(
        rows, me, kanban, "every In Progress task blocks (safe side)")
    return mine, warnings + [f"{task_id} is In Progress but unassigned — not blocking"
                             for task_id in unassigned]


def my_review_tasks(rows, me, kanban):
    """(IDs whose verify evidence the gate checks, notes) for the Ready for Review
    `(id, line)` rows (T161).

    Mine are checked (see `split_by_assignee`), and so are unassigned rows: unlike an
    In Progress row, this one asks the gate to let work ship, so nobody owning it is a
    doubt, and every doubt checks. A teammate's are named in one note line, unchecked:
    their evidence lives in their checkout."""
    mine, teammates, unassigned, notes = split_by_assignee(
        rows, me, kanban, "every Ready for Review task is checked (safe side)")
    checked = set(mine + unassigned)
    if teammates:
        notes.append("teammates' Ready for Review tasks, not checked here: "
                     + ", ".join(teammates))
    return [task_id for task_id, _ in rows if task_id in checked], notes


# --- New decisions at wake (T158) ----------------------------------------------------

DECISIONS_SEEN = "decisions_seen.txt"


def new_decisions_line(root, me):
    """`N new decisions from teammates since your last session`, or None when there are none.

    Reads the board cache (`memory/decisions.md`), counts the entries after the position
    stored at the last call that were written by someone other than `me`, then moves the
    marker to the end. No marker yet: every teammate entry is new to this developer. Never
    raises; a missing or unreadable cache, or a state file that cannot be written, is None."""
    try:
        with open(os.path.join(root, "memory", "decisions.md"), encoding="utf-8") as f:
            entries = render.cached_decisions(f.read())
    except OSError:
        return None
    marker_path = os.path.join(root, STATE_DIR, DECISIONS_SEEN)
    try:
        with open(marker_path, encoding="utf-8") as f:
            seen = int(f.read().strip())
    except (OSError, ValueError):
        seen = 0
    if not 0 <= seen <= len(entries):    # the log shrank: start over from its end
        seen = len(entries)
    me_token = (render.assignee_token(me) or "") if isinstance(me, str) else ""
    fresh = [d for d in entries[seen:] if d.author.casefold() != me_token.casefold()]
    try:
        os.makedirs(os.path.dirname(marker_path), exist_ok=True)
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write(f"{len(entries)}\n")
    except OSError:
        pass
    if not fresh:
        return None
    noun = "decision" if len(fresh) == 1 else "decisions"
    return f"{len(fresh)} new {noun} from teammates since your last session"
