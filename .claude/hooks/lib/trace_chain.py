"""Hash chain + out-of-repo anchor for memory/event-trace/<task>.jsonl (T148).

Shared by the writer (`.claude/hooks/post_tool_trace.py`) and the verifier
(`scripts/verify_trace.py`), so both compute the hash and the anchor path the
same way.

Each chained trace line carries `prev` (the previous chained line's `hash`, or
"genesis" for the first one) and `hash` = sha256(prev + canonical JSON of the
line without `hash`). An in-file chain alone only catches careless edits: an
agent that rewrites a line can recompute every hash after it. So after each
append the writer also appends `<task> <line-no> <hash>` to

    ~/.claude/harness-anchors/<repo-slug>/<task>.anchors

which `.claude/settings.json` denies agents write access to
(`Edit(~/.claude/harness-anchors/**)`, `Bash(*harness-anchors*)`). The base directory
is overridable with CLAUDE_TRACE_ANCHOR_DIR (tests).

`<repo-slug>` = the project root's directory name (the hooks live at
`<root>/.claude/hooks`, so this is `git rev-parse --show-toplevel`'s basename)
plus the first 8 hex chars of sha256(remote.origin.url), or `noremote`. Moving
or renaming the checkout therefore changes the slug: its old anchors stay under
the old slug and the verifier reports ANCHOR MISMATCH until they are moved.
"""
import hashlib
import json
import os
import re
import subprocess

GENESIS = "genesis"
ANCHOR_DIR_ENV = "CLAUDE_TRACE_ANCHOR_DIR"
DEFAULT_ANCHOR_BASE = os.path.join("~", ".claude", "harness-anchors")

# Same reduction pre_agent_step_limit.py applies to session_id: anything that
# is not a plain name character is dropped, so no value can climb out of the
# anchor directory. `_` and `-` are kept because `_untagged` and slugs use them.
_NAME_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9_-]")
_NAME_MAX_LEN = 64


def safe_name(value, fallback):
    if not isinstance(value, str):
        return fallback
    cleaned = _NAME_SANITIZE_PATTERN.sub("", value)[:_NAME_MAX_LEN]
    return cleaned if cleaned else fallback


def canonical(record):
    """Canonical JSON of a record — key order and whitespace never affect the hash."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def chain_hash(record):
    """sha256(prev + canonical JSON of the record without `hash`)."""
    body = {k: v for k, v in record.items() if k != "hash"}
    payload = str(record.get("prev", "")) + canonical(body)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def repo_slug(root):
    try:
        url = subprocess.run(
            ["git", "-C", root, "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        url = ""
    suffix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8] if url else "noremote"
    return safe_name(os.path.basename(os.path.normpath(root)), "repo") + "-" + suffix


def anchor_path(root, task_id):
    base = os.environ.get(ANCHOR_DIR_ENV) or os.path.expanduser(DEFAULT_ANCHOR_BASE)
    if not os.path.isabs(base):
        # No HOME, or a relative override: never let the anchor land under the cwd,
        # which may be inside the repo the anchor is meant to be outside of.
        raise OSError("anchor directory is not absolute: %r" % base)
    return os.path.join(base, repo_slug(root), safe_name(task_id, "_untagged") + ".anchors")
