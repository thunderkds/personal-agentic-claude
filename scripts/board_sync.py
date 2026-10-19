#!/usr/bin/env python3
"""Sync the board cache with the board (T154: `pull` only).

    python3 scripts/board_sync.py pull

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
import os
import re
import sys
import tempfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks", "lib"))
from board import render  # noqa: E402
from board.base import BoardError  # noqa: E402
from board.config import config_path, load_config, task_id_pattern  # noqa: E402
from board.fake import FakeBoard  # noqa: E402
from board.linear import LinearBoard  # noqa: E402

KANBAN = "PROJECT_KANBAN.md"


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


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["pull"])
    parser.parse_args(argv)

    config = load_config(root)
    if config is None and os.path.exists(config_path(root)):
        print("[board] .claude/board.json is unusable; nothing pulled", file=sys.stderr)
        return 2
    if not config or not config.get("board"):
        print("[board] board mode is local (no board in .claude/board.json); nothing to pull",
              file=sys.stderr)
        return 0

    secret = None
    try:
        board, secret = make_board(config, root)
        return pull(board, config, root)
    except ConfigError as exc:
        code, message = 2, str(exc)
    except BoardError as exc:
        code, message = 1, str(exc)
    except Exception as exc:  # never a traceback: it could echo board text or the key
        code, message = 1, f"unexpected {type(exc).__name__}"
    if secret:
        message = message.replace(secret, "[redacted]")
    print(f"[board] pull failed: {message}. The board cache was left unchanged.", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
