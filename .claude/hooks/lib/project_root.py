#!/usr/bin/env python3
"""Where a hook finds the user's project (T232).

Two roots. Code location stays `__file__`-based in each hook (`HOOKS_DIR`, `lib/` imports). Project
data (`PROJECT_KANBAN.md`, `tasks/`, `memory/`, `reports/`, `.claude/verify-runs`,
`.claude/hooks/.state`) comes from `project_root()`, because a hook that runs from a plugin cache
holds none of that in its own folder, and that folder changes on every plugin update.

`exit_outside_kit_project()` is why a plugin hook is safe in every repo where the plugin is on: it
runs before a hook imports the rest of `lib/`, so even a broken gate stays silent outside a kit
project. A hook at `<root>/.claude/hooks` (the `setup.sh` install) never stands down this way.

This module imports only the standard library. Each hook decides what its own failure to import
this module means.
"""
import os
import sys

_LIB_DIR = os.path.dirname(os.path.abspath(__file__))
_HOOKS_DIR = os.path.dirname(_LIB_DIR)
_FILE_ROOT = os.path.dirname(os.path.dirname(_HOOKS_DIR))


def project_root():
    """`$CLAUDE_PROJECT_DIR` when it is set and a directory, else the path above this file."""
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    return os.path.abspath(env_root) if os.path.isdir(env_root) else _FILE_ROOT


def is_kit_project(root):
    """True when `root` holds a local board, or the config of an online board."""
    return (os.path.exists(os.path.join(root, "PROJECT_KANBAN.md"))
            or os.path.exists(os.path.join(root, ".claude", "board.json")))


def exit_outside_kit_project():
    """Exit 0 with no output when this code runs from outside the project's `.claude/hooks` and the
    project is not a kit project. An in-repo hook returns and keeps today's behaviour exactly."""
    root = project_root()
    in_repo = (os.path.realpath(os.path.join(root, ".claude", "hooks"))
               == os.path.realpath(_HOOKS_DIR))
    if not in_repo and not is_kit_project(root):
        sys.exit(0)
