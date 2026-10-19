#!/usr/bin/env python3
"""Board config: which task IDs a project uses (T153, FR-006, board portability rule).

`<root>/.claude/board.json` may carry `"id_pattern"`, a regex for the board's task IDs
(Linear `ENG-\\d+`, GitHub `#\\d+`, Jira `PROJ-\\d+`). Every hook and script that
recognises a task ID builds its regex from `task_id_pattern()`, which returns the site's
own `T\\d+`-shaped pattern unchanged when there is no config, and `(?:<local>|<board>)`
when there is — old `Txxx` tasks keep working in board mode `online`.

Fails toward today's behavior. Missing file, or no `id_pattern` key → local pattern,
silently (board mode `local`). Malformed JSON, a non-object, a non-string pattern, a
regex that does not compile, one with a capturing group (it would shift every site's
group numbers), or one that matches the empty string → one stderr warning per process,
then the local pattern. No gate can become more permissive than it is today.

Stdlib only, no network, never writes. Never raises.
"""
import json
import os
import re
import sys

CONFIG_NAME = "board.json"
LOCAL_PATTERN = r"T\d+"

# An ID is a whole token: not preceded or followed by a word character. Spelled as
# lookarounds, not `\b`, so a pattern starting with `#` still has a boundary.
ID_START = r"(?<![A-Za-z0-9_])"
ID_END = r"(?![A-Za-z0-9_])"

_DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
_warned = set()


def _warn(path, problem):
    if path not in _warned:
        _warned.add(path)
        print(f"[board] ignoring {path}: {problem}; task IDs fall back to {LOCAL_PATTERN}",
              file=sys.stderr)


def config_path(root=None):
    return os.path.join(root or _DEFAULT_ROOT, ".claude", CONFIG_NAME)


def load_config(root=None):
    """The parsed `.claude/board.json` dict, or None when the file is missing or unusable."""
    path = config_path(root)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except Exception as exc:
        _warn(path, f"not valid JSON ({type(exc).__name__})")
        return None
    if not isinstance(data, dict):
        _warn(path, "top level is not a JSON object")
        return None
    return data


def board_id_pattern(root=None):
    """The configured `id_pattern` after validation, or None."""
    config = load_config(root)
    if not config or "id_pattern" not in config:
        return None
    pattern = config["id_pattern"]
    path = config_path(root)
    if not isinstance(pattern, str) or not pattern:
        _warn(path, "id_pattern is not a non-empty string")
        return None
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        _warn(path, f"id_pattern is not a valid regex ({exc})")
        return None
    if compiled.groups:
        _warn(path, "id_pattern has a capturing group; use (?:...)")
        return None
    if compiled.fullmatch(""):
        _warn(path, "id_pattern matches the empty string")
        return None
    return pattern


def task_id_pattern(root=None, local=LOCAL_PATTERN, bounded=False):
    """Regex source matching one task ID, with no capturing group.

    `local` is the calling site's own `T`-ID pattern, returned unchanged when there is no
    board config. `bounded=True` wraps the result in `ID_START`/`ID_END`."""
    board = board_id_pattern(root)
    pattern = f"(?:{local}|{board})" if board else local
    return f"{ID_START}(?:{pattern}){ID_END}" if bounded else pattern


def normalize_task_id(task_id):
    """Canonical form: `7` / `t7` / `T7` → `T007`; a board ID is upper-cased
    (`eng-170` → `ENG-170`)."""
    text = str(task_id).strip()
    match = re.fullmatch(r"[Tt]?(\d+)", text)
    if match:
        return "T" + match.group(1).zfill(3)
    return text.upper()


# A canonical ID that reaches a file name (trace, step counter, guide) must be this shape,
# whatever the configured pattern allowed.
PATH_SAFE_ID = re.compile(r"\A[A-Z0-9#_-]{1,64}\Z")
