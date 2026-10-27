"""Path resolution across the T096 canon relocation.

T096 moved the kit's canon out of the Claude-branded directory:

    .claude/skills/  ->  skills/
    .claude/agents/  ->  agents/

`.claude/skills` and `.claude/agents` remain as committed relative symlinks so
Claude Code still discovers them, but the *tracked* path is now the plain-root
one.

Several suites byte-pin a file against a historical baseline ref via
``git show <ref>:<path>``. Those refs predate the move, so the file exists there
under its old `.claude/`-prefixed path and `git show` fails on the new one. The
`git mv` preserved history, so the content is reachable — only the name changed.

`read_at` asks for the current path first and falls back to the pre-move path
when the ref is older than the move. It deliberately does not hard-code the move
commit: ancestry checks would break the moment the branch is rebased, whereas
"does this path exist at that ref" is true regardless of how history is reshaped.
"""

from __future__ import annotations

import subprocess

# Current path -> the path the same file had before T096.
_PRE_MOVE_PREFIX = {"skills/": ".claude/skills/", "agents/": ".claude/agents/"}

# T183 moved the base template out of agents/ (Claude Code registers every agents/*.md as an
# agent type). Current path -> its path before T183; T096's prefix map then applies to that.
_T183_RENAMES = {"templates/general-agent-template.md": "agents/general-agent-template.md"}


def pre_move_path(rel: str) -> str | None:
    """`rel` as it was named before T096, or None if T096 did not move it."""
    for new, old in _PRE_MOVE_PREFIX.items():
        if rel.startswith(new):
            return old + rel[len(new):]
    return None


def read_at(root, rel: str, ref: str) -> bytes:
    """Bytes of `rel` at `ref`, transparently handling the T096 rename."""
    candidates = [rel]
    if rel in _T183_RENAMES:
        candidates.append(_T183_RENAMES[rel])
    for name in list(candidates):
        older = pre_move_path(name)
        if older is not None:
            candidates.append(older)

    last = None
    for candidate in candidates:
        proc = subprocess.run(
            ["git", "-C", str(root), "show", f"{ref}:{candidate}"],
            capture_output=True,
        )
        if proc.returncode == 0:
            return proc.stdout
        last = proc

    raise RuntimeError(
        f"cannot read {rel} at {ref} (tried {candidates}): "
        f"{last.stderr.decode('utf-8', 'replace').strip()}"
    )
