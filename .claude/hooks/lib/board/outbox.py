"""Outbox: the local queue of board writes that could not be delivered (T156, FR-010).

`.board/outbox.jsonl`, one JSON object per line, append-only with `fsync` (the pattern of
`post_tool_trace.py`). An entry holds only task id, kind, milestone/status, text, a dedupe
key and a timestamp — never the API key or any environment. `flush` replays entries in
order under an exclusive lock so two sessions cannot replay the same entry; it rewrites the
file via a temp file + `os.replace` with whatever could not be delivered yet.
"""
import contextlib
import json
import os
import tempfile

try:
    import fcntl
except ImportError:  # Windows: no advisory lock; single-session use stays correct
    fcntl = None


from board.base import BoardAuthError, BoardError, BoardUnavailable  # noqa: E402

DIR = ".board"
NAME = "outbox.jsonl"


def path(root):
    return os.path.join(root, DIR, NAME)


@contextlib.contextmanager
def _locked(root):
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    with open(os.path.join(root, DIR, "outbox.lock"), "a") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def entries(root):
    try:
        with open(path(root), encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    found = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            found.append(item)
    return found


def count(root):
    return len(entries(root))


def append(root, entry):
    with _locked(root):
        with open(path(root), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())


def _rewrite(root, items):
    fd, tmp = tempfile.mkstemp(dir=os.path.join(root, DIR), prefix=".outbox-tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path(root))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def flush(root, deliver, on_drop=None):
    """Replay in order. `deliver(entry)` returns on success (or already-delivered) and raises
    on failure. A `BoardError` that is neither `BoardUnavailable` nor `BoardAuthError` is permanent (the board will
    refuse it again): the entry is dropped, `on_drop(entry, exc)` is told, and the replay
    goes on. Anything else (unreachable, bad key, unexpected) stops it, keeping that entry and the rest.
    Returns (delivered count, remaining count, the exception that stopped it or None)."""
    if not os.path.exists(path(root)):
        return 0, 0, None
    with _locked(root):
        items = entries(root)
        done, consumed, error = 0, 0, None
        for item in items:
            try:
                deliver(item)
                done += 1
            except (BoardUnavailable, BoardAuthError) as exc:
                error = exc
                break
            except BoardError as exc:
                if on_drop:
                    on_drop(item, exc)
            except Exception as exc:  # unexpected: stop, keep order
                error = exc
                break
            consumed += 1
        _rewrite(root, items[consumed:])
        return done, len(items) - consumed, error
