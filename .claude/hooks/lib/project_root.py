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


NO_PROJECT = ("no project found: run this from inside a project that holds PROJECT_KANBAN.md or "
              ".claude/board.json. The kit's own folder is a plugin here and has no board of yours.")


def is_plugin_folder(path):
    """True when `path` is a plugin package (T233 `.claude-plugin/plugin.json`). A `setup.sh` install
    never holds one: it is not in MANIFEST."""
    return os.path.exists(os.path.join(path, ".claude-plugin", "plugin.json"))


def script_project_root():
    """The project for a script that a skill runs in a `Bash` tool call (T234 D5), or None (D7).

    None means: run from a plugin and no folder at or above the cwd holds a board. A plugin ships the
    kit's own `PROJECT_KANBAN.md`, so the path above this file is never an answer there. The caller
    prints `NO_PROJECT` and stops.

    `$CLAUDE_PROJECT_DIR` is empty there, and the path above this file is the plugin cache when the
    kit runs as a plugin. So: the variable if it is set, else the nearest folder at or above the cwd
    that holds a board, else the path above this file. `project_root()` stays as it was: a hook gets
    the variable from the harness, and a hook of a `setup.sh` install answers with its own project."""
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if os.path.isdir(env_root):
        return os.path.abspath(env_root)
    fallback = None if is_plugin_folder(_FILE_ROOT) else _FILE_ROOT
    try:
        here = os.path.abspath(os.getcwd())
    except OSError:  # the cwd was deleted
        return fallback
    while True:
        if is_kit_project(here):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return fallback
        here = parent


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
