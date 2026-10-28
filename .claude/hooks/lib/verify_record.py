"""Auto verify (T182): the run record (D5) and the hook-written `verify` row (D4).

Shared by the writer (`.claude/hooks/stop_auto_verify.py`, which runs `/verify` headless and writes
both) and the reader (`.claude/hooks/pre_bash_block_unsafe_merge.py`, which accepts an
`auto-run by hook` row only with a matching record).

The record is JSON at

    <anchor base>/<repo-slug>/verify-runs/<task>-<40-hex commit>.json

with the same base as T148's trace anchors (`CLAUDE_TRACE_ANCHOR_DIR`, else
`~/.claude/harness-anchors`). `.claude/settings.json` denies agents write access there:
`Edit(~/.claude/harness-anchors/**)` covers the Edit and Write tools, `Bash(*harness-anchors*)` any
shell command that names the directory. A record anywhere else is never read. Like the anchors, this
raises the bar, it is not a proof: the human operator can write there, a Bash deny rule is
pattern-based, and an agent that runs `stop_auto_verify.py` itself with a fake `claude` first on
its PATH gets a record from the script, because no deny rule names that command.
"""
import json
import os
import re
import subprocess

import auto_mode
from trace_chain import ANCHOR_DIR_ENV, DEFAULT_ANCHOR_BASE, repo_slug, safe_name

AUTO_ROW_TAG = "auto-run by hook"
AUTO_CHECKED_TAG = "auto-checked"
VERDICTS = ("pass", "fail", "blocked")
RESULT_CELL = {"pass": "☑ pass", "fail": "☑ fail", "blocked": "☐ blocked"}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ROW_COMMIT = re.compile(r"\bcommit ([0-9a-f]{40})\b")
ROW_SESSION = re.compile(r"\bsession ([A-Za-z0-9-]+)")
GIT_TIMEOUT_S = 5

# T188 D3 — the minimal track has no Evidence table, so the result is one line under the Decision
# record's `Checked:` field, in the shape the Evidence row uses:
#
#     - verify: ☑ pass — auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<f>
#
# `CHECKED_FIELD` is that field's header plus the bullet lines directly under it. The writer appends
# at its end and the reader looks only inside it, so a `verify:` line anywhere else in the record is
# never read as this one. The record's `Not done:` line cannot match `VERIFY_LINE`: it starts
# `**Not done:**`, and the slot it carries reads `auto verify:`, not a line-leading `verify:`.
MINIMAL_LOG_REL = auto_mode.MINIMAL_LOG_REL
VERIFY_LINE_PREFIX = "verify: "
# A bullet is `-`, `+`, or a `*` that does not start a `**bold**` field name: `[-*]` would read the
# record's own `**Files:**` and `**Not done:**` lines as bullets of the `Checked:` field, and the
# appended line would then land after them instead of inside the field (caught by a real run).
BULLET = r"(?:[-+]|\*(?!\*))"
CHECKED_FIELD = re.compile(rf"^[ \t]*(?:\*\*)?Checked:(?:\*\*)?[^\n]*(?:\n[ \t]*{BULLET}[^\n]*)*",
                           re.M)
VERIFY_LINE = re.compile(rf"^[ \t]*{BULLET}?[ \t]*verify:[ \t]*(?P<result>[^—\n]*?)[ \t]*"
                         r"(?:—[ \t]*(?P<notes>[^\n]*))?$", re.M | re.I)


def record_dir(root):
    base = os.environ.get(ANCHOR_DIR_ENV) or os.path.expanduser(DEFAULT_ANCHOR_BASE)
    if not os.path.isabs(base):
        raise OSError("record directory is not absolute: %r" % base)
    return os.path.join(base, repo_slug(root), "verify-runs")


def record_path(root, task_id, sha):
    if not isinstance(sha, str) or not SHA_PATTERN.match(sha):
        raise ValueError("not a full commit hash: %r" % (sha,))
    return os.path.join(record_dir(root), f"{safe_name(task_id, '_untagged')}-{sha}.json")


def write_record(root, task_id, sha, verdict, session, log):
    path = record_path(root, task_id, sha)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"task": task_id, "commit": sha, "verdict": verdict, "session": session,
                   "log": log}, f)
    os.replace(tmp, path)
    return path


def read_record(root, task_id, sha):
    """The record as a dict, or None (missing, unreadable, not a JSON object)."""
    try:
        with open(record_path(root, task_id, sha), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _git(checkout, *args):
    done = subprocess.run(["git", "-C", checkout, *args], capture_output=True, text=True,
                          timeout=GIT_TIMEOUT_S)
    if done.returncode != 0:
        raise OSError(done.stderr.strip())
    return done.stdout


def head_commit(checkout):
    """The checkout's HEAD as a full hash, or None."""
    try:
        sha = _git(checkout, "rev-parse", "HEAD").strip()
    except Exception:
        return None
    return sha if SHA_PATTERN.match(sha) else None


def same_code(checkout, task_id, verified, head, report_rel=None):
    """True when `head` is the verified commit, or differs from it only in the file that holds this
    task's result (the Supervisor committed the hook-written row or line). Any doubt is False.

    `report_rel` is that file, relative to the checkout: the task's review file by default, and
    `tasks/MINIMAL_LOG.md` for a minimal-track task (T188 D5).
    """
    if not verified or not head:
        return False
    if verified == head:
        return True
    try:
        changed = _git(checkout, "diff", "--name-only", verified, head).split()
    except Exception:
        return False
    return set(changed) <= {report_rel or f"tasks/TASK_REVIEW_{task_id}.md"}


def row_cells(sha, verdict, session, log, reason=""):
    """The D4 `verify` row's Result and Notes cells. Notes for a run that did not pass never
    contain "pass" (the merge gate looks for that word in Notes)."""
    notes = f"{AUTO_ROW_TAG}, session {session}, commit {sha}, log {log} — {verdict}"
    if reason:
        notes += f" ({reason})"
    notes = re.sub(r"[|\n\r]", " ", notes)
    if verdict != "pass":
        notes = re.sub(r"pass", "p-ss", notes, flags=re.IGNORECASE)
    return RESULT_CELL[verdict], notes


def auto_row_confirmed(root, checkout, task_id, notes, report_rel=None):
    """D5: an `auto-run by hook` row counts only when the record for this task and the row's commit
    exists, names the same task, commit and session, says pass, and the commit is the checkout's
    head (or differs from it only in the file that holds the result)."""
    commit = ROW_COMMIT.search(notes or "")
    session = ROW_SESSION.search(notes or "")
    if not commit or not session:
        return False
    sha = commit.group(1)
    record = read_record(root, task_id, sha)
    if not record:
        return False
    if (record.get("task"), record.get("commit"), record.get("verdict"), record.get("session")) != (
            task_id, sha, "pass", session.group(1)):
        return False
    return same_code(checkout, task_id, sha, head_commit(checkout), report_rel)


def record_line(sha, verdict, session, log, reason=""):
    """The D3 `verify:` line for a minimal-track Decision record (T188), bullet excluded.

    Same facts as the Evidence row's two cells, on one line. A line that did not pass never
    contains the word "pass": the merge gate reads that word as the result.
    """
    tail = f"{AUTO_ROW_TAG}, session {session}, commit {sha}, log {log}"
    if reason:
        tail += f" ({reason})"
    tail = re.sub(r"[\n\r]", " ", tail)
    if verdict != "pass":
        tail = re.sub(r"pass", "p-ss", tail, flags=re.IGNORECASE)
    return f"{VERIFY_LINE_PREFIX}{RESULT_CELL[verdict]} — {tail}"


def checked_field(body):
    """The `Checked:` field of a Decision record `body` — its header plus the bullets under it —
    as a match, or None. The one place the D3 `verify:` line is written and read."""
    return CHECKED_FIELD.search(body or "")


def record_verify_line(body):
    """(match, result, notes) of the `verify:` line inside the record body's `Checked:` field, or
    (None, "", ""). Offsets are into `body`."""
    field = checked_field(body)
    if field is None:
        return None, "", ""
    hit = VERIFY_LINE.search(body, field.start(), field.end())
    if hit is None:
        return None, "", ""
    return hit, (hit.group("result") or "").strip(), (hit.group("notes") or "").strip()


def minimal_verify_line(task_id, tasks_dir):
    """(result, notes) of the `verify:` line in this task's Decision record under `tasks_dir`, or
    None. For the merge gate, which must never raise: every failure returns None."""
    try:
        text = auto_mode.read(os.path.join(tasks_dir, auto_mode.MINIMAL_LOG))
        if text is None:
            return None
        block = auto_mode.record_block(text, task_id, skip_comments=True)
        if block is None:
            return None
        hit, result, notes = record_verify_line(block[2])
        return None if hit is None else (result, notes)
    except Exception:
        return None
