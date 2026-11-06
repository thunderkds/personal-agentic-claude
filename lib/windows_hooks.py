#!/usr/bin/env python3
"""windows_hooks.py — turn the kit's POSIX hook entries into the Windows exec form (T266, ADR-0003 decision 3).

Usage:
    python3 lib/windows_hooks.py <in-settings.json> <out-settings.json> --launcher py|python

Exit codes:
    0  written
    2  refused (unknown launcher, unreadable or invalid input) — nothing was written

A kit hook entry `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/x.py` (or the plugin's
`python3 "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/x.py"`) becomes
`{"type": "command", "command": "py", "args": ["-3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py"]}`;
with launcher "python" there is no "-3". Exec form spawns `command` with `args` directly: no shell,
no quoting, and Claude Code substitutes the `${...}` placeholder into each `args` element.
Every other key of the entry (matcher, description, timeout, ...) is kept. Any command that is not
exactly that shape — a user entry, or one already converted — is left as it is, so a second run
changes nothing. The Windows installer (T268) picks the launcher and calls this.
"""

import argparse
import copy
import json
import re
import sys

LAUNCHER_ARGS = {"py": ["-3"], "python": []}

KIT_COMMAND_RE = re.compile(
    r'^python3\s+"?\$(?:\{(?P<braced>CLAUDE_PROJECT_DIR|CLAUDE_PLUGIN_ROOT)\}|(?P<bare>CLAUDE_PROJECT_DIR))"?'
    r'/(?P<path>\.claude/hooks/[\w.-]+\.py)"?$')


def convert_hook(hook, launcher):
    """One hook dict in exec form, or the same dict when it is not a kit command."""
    if not isinstance(hook, dict) or hook.get("type") != "command" or "args" in hook:
        return hook
    command = hook.get("command")
    found = KIT_COMMAND_RE.match(command.strip()) if isinstance(command, str) else None
    if not found:
        return hook
    root = found.group("braced") or found.group("bare")
    converted = dict(hook)
    converted["command"] = launcher
    converted["args"] = LAUNCHER_ARGS[launcher] + ["${%s}/%s" % (root, found.group("path"))]
    return converted


def to_windows_settings(settings, launcher):
    """A new settings dict with every kit hook entry in exec form. `settings` is not changed."""
    if launcher not in LAUNCHER_ARGS:
        raise ValueError("launcher must be one of %s, not %r" % (", ".join(LAUNCHER_ARGS), launcher))
    result = copy.deepcopy(settings)
    events = result.get("hooks") if isinstance(result, dict) else None
    for groups in (events.values() if isinstance(events, dict) else ()):
        for group in (groups if isinstance(groups, list) else ()):
            hooks = group.get("hooks") if isinstance(group, dict) else None
            if isinstance(hooks, list):
                group["hooks"] = [convert_hook(h, launcher) for h in hooks]
    return result


def die(reason):
    sys.stderr.write("windows_hooks: %s\n" % reason)
    sys.exit(2)


def main(argv):
    parser = argparse.ArgumentParser(description="Write the Windows exec form of a settings file.")
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--launcher", required=True, choices=sorted(LAUNCHER_ARGS))
    args = parser.parse_args(argv[1:])  # exits 2 on an unknown launcher, before any write
    try:
        with open(args.source, encoding="utf-8") as handle:
            settings = json.load(handle)
    except (OSError, ValueError) as exc:
        die("cannot read %s: %s" % (args.source, exc))
    if not isinstance(settings, dict):
        die("%s does not contain a JSON object" % args.source)
    content = json.dumps(to_windows_settings(settings, args.launcher), indent=2, ensure_ascii=False) + "\n"
    with open(args.target, "w", encoding="utf-8") as handle:
        handle.write(content)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
