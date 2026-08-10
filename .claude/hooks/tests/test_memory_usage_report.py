#!/usr/bin/env python3
"""T063 — `scripts/memory_usage_report.py` is a read-only measurement instrument.

The script exists to answer a question about memory usage from the event trace.
Its correctness as an *instrument* is what these tests guard: it must run with no
arguments, it must survive the shapes the trace actually takes in the wild
(absent directory, empty directory, half-written line), and above all it must
**write nothing** — T059 was a defect of exactly that shape, a script in this
family that wrote to a tracked data file and destroyed it inside a worktree.

  SC1  — runs against a populated trace: exit 0, every numbered section emitted
  SC2  — missing `memory/event-trace/`: exit 0, "ABSENT", no traceback (AC10)
  SC2b — present but empty `memory/event-trace/`: exit 0, "EMPTY" (AC10)
  SC3  — a malformed JSONL line is skipped and counted; exit 0 (AC10)
  SC4  — AC9, load-bearing: after a run, the resolved root's tree is byte-identical
         and the real repo's `git status --short` is unchanged
  SC5  — the reconciliation and channel numbers are derived, not hard-coded

**SC4 is the one that must not be vacuous.** "The script writes nothing" is
satisfied by any script that never writes, so it is asserted against a *whole-tree
hash snapshot* of the resolved root — every path, its size, and its content digest
— taken before and after. A mutation that writes anywhere under the root (whether
`memory/`, `reports/`, or a directory it creates itself) changes that snapshot.
The repo has six recorded vacuous-assertion incidents, the most recent
non-vacuous against one mutation and vacuous against another, so this is verified
from two independent directions: a write under `memory/` and a write under
`reports/`.

Run with: python3 -m pytest .claude/hooks/tests/test_memory_usage_report.py -v
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))  # <root>/.claude/hooks -> <root>
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "memory_usage_report.py")


def git_status():
    return subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT,
                          capture_output=True, text=True).stdout


# Captured at import, BEFORE any test has run the script. Comparing only
# before/after *inside* the test is not enough: an earlier test in this module
# also runs the script, so a script that creates a file in the real repo would
# already have created it by then and before == after would hold vacuously.
# Verified: this baseline is what makes the hard-coded-real-repo-write mutation
# go RED; without it that mutation passed all nine tests.
BASELINE_GIT_STATUS = git_status()


def snapshot_tree(root):
    """{relative path: (size, sha256)} for every file under `root`.

    Content-hashed rather than mtime-compared: an mtime check would miss a
    rewrite-with-same-timestamp, and would also produce false positives from
    unrelated tooling. `__pycache__` is excluded because importing anything at all
    legitimately creates it and it is not repo data.
    """
    entries = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                with open(full, "rb") as handle:
                    blob = handle.read()
            except OSError:
                continue
            entries[os.path.relpath(full, root)] = (len(blob), hashlib.sha256(blob).hexdigest())
    return entries


def run_script(root, script_path=SCRIPT_PATH):
    """Invoke the script with **no arguments** (AC8) against `root`."""
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = root
    return subprocess.run(
        [sys.executable, script_path],
        capture_output=True, text=True, env=env, cwd=tempfile.gettempdir(),
    )


def write_trace(root, files):
    """Build a fake checkout: `<root>/memory/event-trace/<name>.jsonl` per entry.

    Values are either a list of record dicts or a raw string (for the malformed
    line case).
    """
    trace = os.path.join(root, "memory", "event-trace")
    os.makedirs(trace, exist_ok=True)
    for name, content in files.items():
        with open(os.path.join(trace, name + ".jsonl"), "w") as handle:
            if isinstance(content, str):
                handle.write(content)
            else:
                for record in content:
                    handle.write(json.dumps(record) + "\n")
    return trace


def record(tool_name, summary, timestamp, spawn=None):
    out = {"timestamp": timestamp, "tool_name": tool_name, "summary": summary, "is_error": False}
    if spawn:
        out["spawn"] = spawn
    return out


WT = "/home/u/pets/wt-t900"


def populated_trace():
    """A miniature of the real shape: a Supervisor guide write, a sub-agent session
    in its own worktree (some of it landing in `_untagged` because the active-task
    pointer was armed mid-session), and an `Agent` record carrying T061 tool_stats
    that reconciles against the two together."""
    return {
        "T900": [
            record("Write", json.dumps({"file_path": "/home/u/pets/personal-agentic-claude/tasks/TASK_GUIDE_T900.md"}), "2026-08-07T09:00:00+00:00"),
            record("Read", json.dumps({"file_path": WT + "/tasks/TASK_GUIDE_T900.md"}), "2026-08-07T10:00:02+00:00"),
            record("Bash", json.dumps({"command": "cd " + WT + " && pytest"}), "2026-08-07T10:00:03+00:00"),
            record("Edit", json.dumps({"file_path": WT + "/a.py"}), "2026-08-07T10:00:04+00:00"),
            record("Agent", json.dumps({"prompt": "Task ID: T900\nWork only inside " + WT}), "2026-08-07T10:00:10+00:00",
                   spawn={"tool_use_count": 6, "tool_stats": {"read_count": 2, "bash_count": 2, "edit_file_count": 2}}),
        ],
        "_untagged": [
            record("Bash", json.dumps({"command": "git commit -m 'supervisor stage 2'"}), "2026-08-07T09:00:01+00:00"),
            record("Bash", json.dumps({"command": "ls -la " + WT + "/tasks"}), "2026-08-07T10:00:00+00:00"),
            record("Read", json.dumps({"file_path": WT + "/memory/MEMORY.md"}), "2026-08-07T10:00:01+00:00"),
            record("Write", json.dumps({"file_path": WT + "/b.py"}), "2026-08-07T10:00:05+00:00"),
        ],
    }


# --- SC1 -------------------------------------------------------------------

def test_runs_with_no_arguments_and_emits_every_section():
    with tempfile.TemporaryDirectory() as root:
        write_trace(root, populated_trace())
        result = run_script(root)
        assert result.returncode == 0, result.stderr
        for heading in ("1. The naive figure", "2. Where MEMORY.md reads actually happen",
                        "3. Sub-agent worktrees", "4. AC1", "5. AC3/AC4"):
            assert heading in result.stdout, "missing section %r in:\n%s" % (heading, result.stdout)


# --- SC5 -------------------------------------------------------------------

def test_reconciliation_is_derived_from_the_records():
    """The sub-agent reported 2 reads / 2 bash / 2 edit-like. One read and one edit
    landed in the T900 bucket; the other of each landed in `_untagged` inside the
    session window. The script must recombine them and mark EXACT — and must NOT
    sweep in the Supervisor's 09:00:01 commit, which predates the session."""
    with tempfile.TemporaryDirectory() as root:
        write_trace(root, populated_trace())
        out = run_script(root).stdout
        assert "bucket T900" in out
        # The Supervisor's own 09:00 guide Write predates the session and must be
        # excluded, not counted as the sub-agent's. Leaving it in is what produced
        # a false EXACT on the real T067 data.
        assert "excluded as pre-session (Supervisor's own): 1" in out
        for field in ("read", "bash", "edit_like", "total"):
            line = [l for l in out.splitlines() if l.strip().startswith(field)]
            assert line, "no %s row in:\n%s" % (field, out)
            assert "EXACT" in line[0], "%s did not reconcile: %s" % (field, line[0])


def test_locus_separates_worktree_reads_from_main_checkout():
    with tempfile.TemporaryDirectory() as root:
        write_trace(root, populated_trace())
        out = run_script(root).stdout
        assert "worktree:t900" in out
        assert "MEMORY.md reads=1" in out


def test_naive_figure_is_reproduced_not_silently_dropped():
    with tempfile.TemporaryDirectory() as root:
        write_trace(root, populated_trace())
        out = run_script(root).stdout
        # The MEMORY.md read is in _untagged, so the naive per-task figure is 0 of 1
        # — that gap is the whole point of the report and must stay visible.
        assert "task buckets with >=1 Read of MEMORY.md: 0 of 1" in out
        assert "_untagged Reads of MEMORY.md: 1" in out


# --- SC2 / SC2b / SC3 (AC10) ----------------------------------------------

def test_missing_trace_directory_reports_zero_and_exits_clean():
    with tempfile.TemporaryDirectory() as root:
        result = run_script(root)
        assert result.returncode == 0, result.stderr
        assert "ABSENT" in result.stdout
        assert "Traceback" not in result.stderr


def test_empty_trace_directory_reports_zero_and_exits_clean():
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "memory", "event-trace"))
        result = run_script(root)
        assert result.returncode == 0, result.stderr
        assert "EMPTY" in result.stdout or "records: 0" in result.stdout
        assert "Traceback" not in result.stderr


def test_malformed_jsonl_line_is_skipped_and_counted():
    with tempfile.TemporaryDirectory() as root:
        good = json.dumps(record("Read", json.dumps({"file_path": WT + "/memory/MEMORY.md"}),
                                 "2026-08-07T10:00:00+00:00"))
        write_trace(root, {"T900": good + "\n{ this is not json\n" + good + "\n"})
        result = run_script(root)
        assert result.returncode == 0, result.stderr
        assert "malformed lines skipped: 1" in result.stdout
        assert "records: 2" in result.stdout


# --- SC4 (AC9) — load-bearing ---------------------------------------------

def test_script_writes_nothing_anywhere():
    """Whole-tree content snapshot of the resolved root, before and after.

    Mutation-verified from two directions (see module docstring): a write under
    `memory/` and a write under `reports/` each turn this RED.
    """
    with tempfile.TemporaryDirectory() as root:
        write_trace(root, populated_trace())
        os.makedirs(os.path.join(root, "reports"), exist_ok=True)
        with open(os.path.join(root, "reports", "keep.md"), "w") as handle:
            handle.write("pre-existing\n")

        before = snapshot_tree(root)
        result = run_script(root)
        after = snapshot_tree(root)

        assert result.returncode == 0, result.stderr
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
        assert not added, "script created file(s): %s" % added
        assert not removed, "script deleted file(s): %s" % removed
        assert not changed, "script modified file(s): %s" % changed


def test_script_does_not_touch_the_real_repository():
    """Second direction on the same guarantee: a mutation with a *hard-coded* path
    into the real checkout would slip past the temp-root snapshot above."""
    with tempfile.TemporaryDirectory() as root:
        write_trace(root, populated_trace())
        result = run_script(root)
        after = git_status()
        assert result.returncode == 0, result.stderr
        assert after == BASELINE_GIT_STATUS, (
            "the real repo changed since this module was imported:\n%s\n--- became ---\n%s"
            % (BASELINE_GIT_STATUS, after))
