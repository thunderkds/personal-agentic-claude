#!/usr/bin/env python3
"""Sync the board cache with the board: `pull` (T154), `push`, `flush`, `status` (T156).

    python3 scripts/board_sync.py pull
    python3 scripts/board_sync.py push status <ID> {todo,in-progress,ready-for-review,done}
    python3 scripts/board_sync.py push comment <ID> <milestone> <text...>
    python3 scripts/board_sync.py flush
    python3 scripts/board_sync.py status

`push` sends at once (FR-009); when the board is unreachable (network error, timeout, 5xx,
429) the write is appended to `.board/outbox.jsonl` with a dedupe key and the command still
exits 0 with a `queued` notice. `flush` replays the queue in order; a comment already on the
board (matched by the key embedded in it) is dropped, not reposted. `status` prints
`N unsynced` for `wake`. With `git_auto_status: true` in `.claude/board.json`, Linear's git
integration owns In Progress/Done and `push status` refuses them. Milestones only
(started, red, green, review, verify, merged, blocked, question) — no free-form streaming.

Board mode `online` (`.claude/board.json` names a `board`): fetch every task of the
configured team/project and rewrite the board cache in today's formats —
`PROJECT_KANBAN.md` and `tasks/TASK_GUIDE_<ID>.md` (each issue description, verbatim).
The board is the whole truth: local rows the board lacks are dropped, with a warning.

Board mode `local` (no `.claude/board.json`, or no `board` in it): does nothing, exit 0.

Nothing is written until the whole board has been read; each file is then replaced via a
temp file + `os.replace`. Any failure exits non-zero and leaves the cache untouched.
`LINEAR_API_KEY` is read from the environment only and never printed (NFR-001).

Exit codes: 0 pulled (or local mode), 1 the board could not be read, 2 bad config.
"""
import argparse
import hashlib
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks", "lib"))
from board import outbox, render  # noqa: E402
from board.base import BoardError, BoardUnavailable  # noqa: E402
from board.config import config_path, load_config, normalize_task_id, task_id_pattern  # noqa: E402
from board.fake import FakeBoard  # noqa: E402
from board.linear import LinearBoard  # noqa: E402

KANBAN = "PROJECT_KANBAN.md"
MILESTONES = ("started", "red", "green", "review", "verify", "merged", "blocked", "question")
# CLI slug -> board cache section; the first two are what Linear's git integration moves.
STATUS_SECTIONS = {"todo": "Todo", "in-progress": "In Progress",
                   "ready-for-review": "Ready for Review", "done": "Done"}
GIT_OWNED = ("in-progress", "done")
DEFAULT_BOARD_NAMES = {"Todo": "Todo", "In Progress": "In Progress",
                       "Ready for Review": "In Review", "Done": "Done"}


class ConfigError(Exception):
    pass


def make_board(config, root):
    """(adapter, secret to redact or None) for the configured board."""
    kind = config.get("board")
    if kind == "linear":
        key = os.environ.get("LINEAR_API_KEY")
        if not key:
            raise ConfigError("LINEAR_API_KEY is not set. Add `export LINEAR_API_KEY=...` to your "
                              "shell profile; the key is never stored in a file")
        team = config.get("team")
        if not isinstance(team, str) or not team:
            raise ConfigError("`team` is missing from .claude/board.json")
        return LinearBoard(key, team, config.get("project") or None), key
    if kind == "fake":
        return FakeBoard.from_file(os.path.join(root, str(config.get("fake_board", "")))), None
    raise ConfigError(f"unknown board {render.one_line(kind)!r} in .claude/board.json")


def write_atomically(root, files):
    """Write every file to a temp file in its own directory, then `os.replace` them all."""
    staged = []
    try:
        for rel, text in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".board-tmp-")
            staged.append((tmp, path))
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        for tmp, path in staged:
            os.replace(tmp, path)
    finally:
        for tmp, _ in staged:
            if os.path.exists(tmp):
                os.unlink(tmp)


def dropped_local_rows(root, board_ids):
    try:
        with open(os.path.join(root, KANBAN), encoding="utf-8") as f:
            old = f.read()
    except OSError:
        return []
    pattern = task_id_pattern(root)
    found = re.findall(rf"^\s*-\s*\[.\]\s*\*\*({pattern})\*\*", old, re.MULTILINE)
    return sorted(set(found) - set(board_ids))


def pull(board, config, root):
    tasks = board.list_tasks()
    status_map = config.get("status_map")
    kanban = render.render_kanban(tasks, status_map if isinstance(status_map, dict) else None,
                                  today=date.today().isoformat())
    guides = render.guide_files(tasks)
    dropped = dropped_local_rows(root, [t.id for t in tasks])
    if dropped:
        print(f"[board] the board has no {', '.join(dropped)}; their local rows were dropped "
              f"(online mode: the board is the source of truth)", file=sys.stderr)
    write_atomically(root, {**guides, KANBAN: kanban})
    print(f"[board] pulled {len(tasks)} tasks: {KANBAN} and {len(guides)} guides written")
    return 0


def board_status_name(config, section):
    """The board's own name for a cache section: a `status_map` entry wins over the default."""
    status_map = config.get("status_map")
    if isinstance(status_map, dict):
        for name, mapped in status_map.items():
            if mapped == section and isinstance(name, str) and name:
                return name
    return DEFAULT_BOARD_NAMES[section]


def dedupe_key(task, milestone, text, created):
    return hashlib.sha256("\0".join((task, milestone, text, created)).encode()).hexdigest()[:16]


def comment_body(milestone, text, key):
    return f"[{milestone}] {text}\n\n— board-sync:{key}"


def deliver(board, entry):
    """Send one outbox entry. A comment already on the board is a success without a repost."""
    if entry.get("kind") == "comment":
        if board.has_comment(entry["task"], f"board-sync:{entry['key']}"):
            return
        board.add_comment(entry["task"], comment_body(entry["milestone"], entry["text"], entry["key"]))
    elif entry.get("kind") == "status":
        board.set_status(entry["task"], entry["name"])
    else:
        raise BoardError("unknown outbox entry")


def flush(board, root):
    def dropped(entry, exc):  # never the text or the key
        print(f"[board] dropped a queued {entry.get('kind')} for {entry.get('task')} "
              f"({entry.get('milestone')}): the board refused it ({exc})", file=sys.stderr)

    done, remaining, error = outbox.flush(root, lambda entry: deliver(board, entry), dropped)
    if done:
        print(f"[board] flushed {done} queued write(s)")
    if error is not None:
        if not isinstance(error, BoardError):
            error = BoardError(f"unexpected {type(error).__name__}")
        print(f"[board] {remaining} write(s) still queued: {error}", file=sys.stderr)
        return 1
    return 0


def push(board, config, root, args):
    task = normalize_task_id(args.id)
    if not re.fullmatch(task_id_pattern(root), task):
        print(f"[board] {render.one_line(args.id)!r} is not a task ID", file=sys.stderr)
        return 2
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.kind == "comment":
        milestone = args.value
        if milestone not in MILESTONES:
            print(f"[board] milestone must be one of: {', '.join(MILESTONES)}", file=sys.stderr)
            return 2
        text = " ".join(args.text).strip()
        key = os.environ.get("LINEAR_API_KEY")
        if key:
            text = text.replace(key, "[redacted]")
        text = text.replace("board-sync:", "board-sync -")  # no forged dedupe marker
        if not text:
            print("[board] a comment needs text", file=sys.stderr)
            return 2
        entry = {"kind": "comment", "task": task, "milestone": milestone, "text": text,
                 "key": dedupe_key(task, milestone, text, created), "created": created}
    else:
        if args.value not in STATUS_SECTIONS:
            print(f"[board] status must be one of: {', '.join(STATUS_SECTIONS)}", file=sys.stderr)
            return 2
        if config.get("git_auto_status") is True and args.value in GIT_OWNED:
            print(f"[board] git_auto_status is on: the git integration moves {args.value}; "
                  f"only todo and ready-for-review are pushed", file=sys.stderr)
            return 2
        name = board_status_name(config, STATUS_SECTIONS[args.value])
        entry = {"kind": "status", "task": task, "milestone": args.value, "name": name,
                 "key": dedupe_key(task, args.value, name, created), "created": created}
    try:
        if outbox.count(root):                       # older writes first
            if flush(board, root):
                raise BoardUnavailable("earlier writes are still queued")
        deliver(board, entry)
    except BoardUnavailable:
        outbox.append(root, entry)
        print(f"[board] board unreachable: queued {entry['kind']} for {task} "
              f"({outbox.count(root)} unsynced); run `board_sync.py flush` later")
        return 0
    print(f"[board] pushed {entry['kind']} for {task}")
    return 0


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("pull")
    sub.add_parser("flush")
    sub.add_parser("status")
    p_push = sub.add_parser("push")
    p_push.add_argument("kind", choices=["status", "comment"])
    p_push.add_argument("id")
    p_push.add_argument("value", help="status slug, or comment milestone")
    p_push.add_argument("text", nargs="*", help="comment text")
    args = parser.parse_args(argv)

    config = load_config(root)
    if config is None and os.path.exists(config_path(root)):
        print("[board] .claude/board.json is unusable; nothing pulled", file=sys.stderr)
        return 2
    if not config or not config.get("board"):
        print(f"[board] board mode is local (no board in .claude/board.json); nothing to {args.command}",
              file=sys.stderr)
        return 0
    if args.command == "status":                     # reads the local outbox only
        print(f"{outbox.count(root)} unsynced")
        return 0
    if args.command == "flush" and not outbox.count(root):
        return 0

    secret = None
    try:
        board, secret = make_board(config, root)
        if args.command == "pull":
            return pull(board, config, root)
        if args.command == "flush":
            return flush(board, root)
        return push(board, config, root, args)
    except ConfigError as exc:
        code, message = 2, str(exc)
    except BoardError as exc:
        code, message = 1, str(exc)
    except Exception as exc:  # never a traceback: it could echo board text or the key
        code, message = 1, f"unexpected {type(exc).__name__}"
    if secret:
        message = message.replace(secret, "[redacted]")
    tail = " The board cache was left unchanged." if args.command == "pull" else ""
    print(f"[board] {args.command} failed: {message}.{tail}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
