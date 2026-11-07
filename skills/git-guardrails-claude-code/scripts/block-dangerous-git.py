#!/usr/bin/env python3
"""block-dangerous-git.py — Python twin of block-dangerous-git.sh (T277), for Windows without bash.

A Claude Code PreToolUse hook. Reads the hook JSON on stdin and blocks a Bash command that
matches a dangerous git pattern: prints the BLOCKED text on stderr and exits 2. Any other
command, and any input it cannot read, exits 0 (a hook error never blocks). It decides exactly
as the .sh does: the same patterns, in the same order, searched as regular expressions in the
raw command text. A pattern inside quotes or a heredoc therefore blocks too. Keep both files in step.
"""

import json
import re
import sys

DANGEROUS_PATTERNS = [
    "git push",
    "git reset --hard",
    "git clean -fd",
    "git clean -f",
    "git branch -D",
    r"git checkout \.",
    r"git restore \.",
    "push --force",
    "reset --hard",
]


def command_text(raw):
    """The command as `jq -r '.tool_input.command'` prints it, or "" when the input has none."""
    try:
        command = json.loads(raw.decode("utf-8", errors="replace"))["tool_input"]["command"]
    except (ValueError, KeyError, TypeError):
        return ""
    return command if isinstance(command, str) else json.dumps(command, indent=2, ensure_ascii=False)


def main():
    command = command_text(sys.stdin.buffer.read())
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            message = ("BLOCKED: '%s' matches dangerous pattern '%s'. "
                       "The user has prevented you from doing this.\n" % (command, pattern))
            sys.stderr.buffer.write(message.encode("utf-8"))  # bytes: a Windows console code page cannot fail
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
