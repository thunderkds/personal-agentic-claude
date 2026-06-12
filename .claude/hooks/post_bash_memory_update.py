#!/usr/bin/env python3
"""
PostToolUse hook — fires after every Bash tool call.

When the command is `git push` or `git merge`, prompts the Supervisor
to run the diff-driven memory-update pass on the two-tier memory system.

Triggers: git push, git merge (and git pull, which internally runs git merge)
Does not fire: any other Bash command
"""
import json
import re
import sys

GIT_MEMORY_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bgit\s+merge\b",
    r"\bgit\s+pull\b",   # git pull runs git merge internally
]

MEMORY_UPDATE_PROMPT = """
[hook:post_bash] Git operation detected — memory update required.

Run the diff-driven memory-update pass now:
1. Run: git diff HEAD~1 --name-only
2. Grep memory/decisions.md, memory/glossary.md, memory/learnings.md for any reference to the changed files
3. Update matched entries in place (fix stale facts, expand with new context)
4. Append any new decisions or learnings from this session to the appropriate cold file
5. Summarize new/changed entries as one-liners in memory/MEMORY.md (keep hot tier ≤200 lines total)

Routing: architectural/infra decisions → decisions.md | biz terms/domain models → glossary.md | patterns/gotchas/spec clarifications → learnings.md
""".strip()


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if event.get("tool_name") != "Bash":
        sys.exit(0)

    command = event.get("tool_input", {}).get("command", "")

    if not any(re.search(p, command) for p in GIT_MEMORY_PATTERNS):
        sys.exit(0)

    print(MEMORY_UPDATE_PROMPT)


main()
