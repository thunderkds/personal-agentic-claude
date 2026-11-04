#!/usr/bin/env python3
"""T252 — the Stop check judges only this session's work, also for a task whose report is already
marked auto mode (T250 G3 covered only a task found by file time).

  AC 1 — marked, failing, this session did not work on it: no block, one stderr note.
  AC 2 — the same task, this session worked on it: the block, same reasons.
  AC 3 — ownership cannot be told (reader raises, unreadable transcript, none): the block.
  Stage 4 P1 — a marked minimal-track record is always checked (no ownership question).
  AC 5 — end to end through the hook's `main()` (stdin JSON, synthetic transcript in `tmp_path`).

Run with: python3 -m pytest .claude/hooks/tests/test_t252_marked_ownership.py -q
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_t250_session_ownership import (  # noqa: E402
    T249_LIKE_ROW, SID, _ago, auto_request, bash, gate_project, run_stop, session, tool_use,
    write_transcript,
)

MARKED_REVIEW = ("# TASK_REVIEW — T900\n\n## Auto decisions\n\nMode: auto\n"
                 "1. kept the file — RULE: `docs/claude-md/tracks.md` `### Backups`\n"
                 "Not done: merge (yours)\n\n## Evidence\n\n| Check | Result | Notes |\n")  # no `Memory:` line


def marked_project(tmp_path):
    """T900 In Progress; its review is marked `Mode: auto` and lacks the `Memory:` line."""
    project = gate_project(tmp_path, in_progress=(T249_LIKE_ROW,),
                           files={"tasks/TASK_REVIEW_T900.md": MARKED_REVIEW})
    trace = project / "memory" / "event-trace"
    trace.mkdir(parents=True)
    (trace / "T900.jsonl").write_text(json.dumps({
        "tool_name": "Bash", "is_error": False,
        "summary": json.dumps({"command": "python3 -m pytest -q"})}) + "\n", encoding="utf-8")
    return project


def grep_only(project):
    return tool_use("Grep", {"pattern": "Mode", "path": str(project / "tasks" / "TASK_REVIEW_T900.md")},
                    _ago(300))


def write_review(project):
    return tool_use("Write", {"file_path": str(project / "tasks" / "TASK_REVIEW_T900.md"),
                              "content": "x"}, _ago(300), cwd=str(project))


def test_ac1_ac5_a_marked_task_this_session_did_not_work_on_is_not_checked(tmp_path):
    project = marked_project(tmp_path)
    t = session(tmp_path, project, [auto_request(), grep_only(project)])
    reason, stderr = run_stop(project, t)
    assert reason is None, reason
    assert stderr.count("T900") == 1 and "did not work on it" in stderr, stderr


def test_ac1_a_not_checked_task_is_not_stamped(tmp_path):
    project = marked_project(tmp_path)
    t = session(tmp_path, project, [auto_request(), grep_only(project)])
    run_stop(project, t)
    assert (project / "tasks" / "TASK_REVIEW_T900.md").read_text(encoding="utf-8") == MARKED_REVIEW


def test_ac1_a_marked_task_is_not_checked_without_an_auto_request_too(tmp_path):
    project = marked_project(tmp_path)
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_stop(project, t)
    assert reason is None, reason


def test_ac2_ac5_a_marked_task_this_session_worked_on_blocks(tmp_path):
    project = marked_project(tmp_path)
    t = session(tmp_path, project, [auto_request(), write_review(project)])
    reason, _ = run_stop(project, t)
    assert reason and "T900" in reason and "Memory:" in reason, reason


def test_ac2_a_sub_agent_of_this_session_counts(tmp_path):
    project = marked_project(tmp_path)
    t = session(tmp_path, project, [auto_request()])
    write_transcript(t.parent / SID / "subagents" / "agent-a1.jsonl", [write_review(project)])
    reason, _ = run_stop(project, t)
    assert reason and "T900" in reason, reason


def test_ac3_an_ownership_reader_that_raises_keeps_the_check(tmp_path):
    project = marked_project(tmp_path)
    lib = project / ".claude" / "hooks" / "lib" / "session_work.py"
    lib.write_text(lib.read_text(encoding="utf-8") + "\n\ndef load_work(_path):\n"
                   "    raise RuntimeError('ownership reader broke')\n", encoding="utf-8")
    t = session(tmp_path, project, [auto_request(), grep_only(project)])
    reason, stderr = run_stop(project, t)
    assert reason and "T900" in reason and "Memory:" in reason, (reason, stderr)
    assert "session ownership unknown (RuntimeError)" in stderr


def test_ac3_no_transcript_keeps_the_check(tmp_path):
    project = marked_project(tmp_path)
    reason, _ = run_stop(project, tmp_path / "missing.jsonl")
    assert reason and "T900" in reason, reason


def test_ac3_an_unreadable_sub_agent_transcript_keeps_the_check(tmp_path):
    project = marked_project(tmp_path)
    t = session(tmp_path, project, [auto_request()])
    sub = write_transcript(t.parent / SID / "subagents" / "agent-a1.jsonl", [bash("ls")])
    sub.chmod(0)
    try:
        if os.access(sub, os.R_OK):
            pytest.skip("running as a user that reads mode-0 files")
        reason, _ = run_stop(project, t)
        assert reason and "T900" in reason, reason
    finally:
        sub.chmod(0o600)


MIN_ROW = ("- [ ] **T900** — Sort the names | Supervisor | C0 | Risk: Low | P2 "
           "| Track: minimal | Record: `tasks/MINIMAL_LOG.md`")
MIN_LOG = ("# Minimal log\n\n## T900 — Sort the names · minimal\nMode: auto\n"
           "Asked: sort\nDecisions:\n1. sorted — RULE: `docs/claude-md/tracks.md` `### Backups`\n"
           "Checked: tests\nFiles: a.py\nNot done: merge (yours)\n")


def test_edge_a_marked_minimal_track_task_is_still_checked_without_work_by_this_session(tmp_path):
    """Stage 4 P1: a minimal-track task done in the main checkout leaves no `tasks/*_<ID>*` write,
    so ownership cannot be told from the transcript; its marked record keeps today's check."""
    project = gate_project(tmp_path, in_progress=(MIN_ROW,), files={"tasks/MINIMAL_LOG.md": MIN_LOG})
    t = session(tmp_path, project, [auto_request(), bash("ls", cwd=str(project))])
    reason, stderr = run_stop(project, t)
    assert reason and "T900" in reason, (reason, stderr)
    assert "did not work on it" not in stderr, stderr
