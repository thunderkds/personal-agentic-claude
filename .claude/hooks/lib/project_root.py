#!/usr/bin/env python3
"""Where a hook finds the user's project (T232).

Two roots. Code location stays `__file__`-based in each hook (`HOOKS_DIR`, `lib/` imports). Project
data (`PROJECT_KANBAN.md`, `tasks/`, `memory/`, `reports/`, `.claude/verify-runs`,
`.claude/hooks/.state`) comes from `project_root()`, because a hook that runs from a plugin cache
holds none of that in its own folder, and that folder changes on every plugin update.

`exit_outside_kit_project()` is why a plugin hook is safe in every repo where the plugin is on: it
runs before a hook imports the rest of `lib/`, so even a broken gate stays silent outside a kit
project. A hook at `<root>/.claude/hooks` (the `setup.sh` install) never stands down this way.

T235: beside in-repo kit hooks that the project's settings wire, a plugin hook stands down the
same way (`wires_in_repo_hook`), so one set of gates runs.

This module imports only the standard library. Each hook decides what its own failure to import
this module means.
"""
import json
import os
import sys

_LIB_DIR = os.path.dirname(os.path.abspath(__file__))
_HOOKS_DIR = os.path.dirname(_LIB_DIR)
_FILE_ROOT = os.path.dirname(os.path.dirname(_HOOKS_DIR))


def project_root():
    """`$CLAUDE_PROJECT_DIR` when it is set and a directory, else the path above this file.

    T235 D6 (a): run from a plugin, the path above this file is the plugin cache, which ships the
    kit's own board. There the answer is the nearest kit project at or above the cwd, else the cwd.
    "From a plugin" means `$CLAUDE_PLUGIN_ROOT` names the path above this file: the harness exports
    it to a plugin hook (checked live, 2026-11-03). `.claude-plugin/` alone cannot tell, because the
    kit's own checkout holds one too. With neither variable set, the answer stays the path above."""
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if os.path.isdir(env_root):
        return os.path.abspath(env_root)
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if not plugin_root or os.path.realpath(plugin_root) != os.path.realpath(_FILE_ROOT):
        return _FILE_ROOT
    try:
        cwd = os.path.abspath(os.getcwd())
    except OSError:  # the cwd was deleted: no project, and never the plugin's own board
        return os.path.abspath(os.sep)
    return _nearest_kit_project(cwd) or cwd


def _nearest_kit_project(here):
    while True:
        if is_kit_project(here):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


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


def wires_in_repo_hook(root, name):
    """True when `<root>/.claude/settings.json` runs `.claude/hooks/<name>` and that file exists (T235
    D4). Settings that are not valid JSON load no hook, and a wired file that is missing runs no gate,
    so both answer False: the plugin's gate keeps running."""
    if not name or not os.path.isfile(os.path.join(root, ".claude", "hooks", name)):
        return False
    try:
        with open(os.path.join(root, ".claude", "settings.json"), encoding="utf-8") as handle:
            events = json.load(handle).get("hooks")
    except (OSError, ValueError, AttributeError):
        return False
    target = ".claude/hooks/" + name
    for groups in (events.values() if isinstance(events, dict) else ()):
        for group in (groups if isinstance(groups, list) else ()):
            entries = group.get("hooks") if isinstance(group, dict) else None
            for entry in (entries if isinstance(entries, list) else ()):
                command = entry.get("command") if isinstance(entry, dict) else None
                if (isinstance(command, str) and target in command
                        and "CLAUDE_PLUGIN_ROOT" not in command):
                    return True
    return False


def exit_outside_kit_project():
    """Exit 0 with no output when this code runs from outside the project's `.claude/hooks` and the
    project is not a kit project, or the project wires its own copy of this hook (T235 D4: both modes
    present, the in-repo set wins because the project chose it; each gate runs once). Only a hook
    call stands down that way: the harness runs a hook with no arguments, and a worker such as
    `stop_auto_verify.py --run` gets some. An in-repo hook returns and keeps today's behaviour exactly."""
    root = project_root()
    in_repo = (os.path.realpath(os.path.join(root, ".claude", "hooks"))
               == os.path.realpath(_HOOKS_DIR))
    if in_repo:
        return
    if not is_kit_project(root):
        sys.exit(0)
    if len(sys.argv) == 1 and wires_in_repo_hook(root, os.path.basename(sys.argv[0])):
        sys.exit(0)
