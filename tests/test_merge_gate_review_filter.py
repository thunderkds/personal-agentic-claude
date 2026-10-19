"""T161 — in board mode `online` only my Ready for Review tasks are checked for verify
evidence before a push; a teammate's are listed in a note, not a blocker.

  AC1 — teammate's ENG-171 in Ready for Review without evidence does not block `git push`;
        a stderr note names it.
  AC2 — my own ENG-170 without evidence still blocks with today's message.
  AC3 — `me` unset, a cache that is not a board render, or a row with two assignee fields
        → every Ready for Review row is checked, with T157's safe-side note.
  AC4 — an unassigned Ready for Review row is checked (blocks), unlike In Progress.
  AC5 — local mode: the same rows block exactly as today, nothing on stderr.
  Fail closed — an exception in the filter checks every row.

Every project is a temp copy (hooks + `scripts/board_sync.py`), so each `__file__`-relative
ROOT resolves to it. The board is the fake adapter: no network.

Run with: python3 -m pytest tests/test_merge_gate_review_filter.py -v
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
GATE = "pre_bash_block_unsafe_merge.py"
PUSH = {"tool_name": "Bash", "tool_input": {"command": "git push"}}
UNREACHABLE = "board unreachable — using cache"
MISSING = "Tasks in Ready for Review missing Stage 5 verify evidence: "

sys.path.insert(0, str(HOOKS / "lib"))


def task(task_id, assignee, title="t", status="In Review"):
    return {"id": task_id, "title": title, "status": status, "assignee": assignee,
            "description": f"# guide {task_id}\n"}


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "LINEAR_API_KEY")}
    env.update(extra)
    return env


def make_project(tmp_path, tasks=None, online=True, me="alice", kanban=None):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (project / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "board_sync.py", project / "scripts" / "board_sync.py")
    (project / "tasks").mkdir()
    (project / "board.json").write_text(json.dumps(tasks or []))
    if online:
        cfg = {"board": "fake", "fake_board": "board.json", "id_pattern": r"ENG-\d+"}
        if me is not None:
            cfg["me"] = me
        (project / ".claude" / "board.json").write_text(json.dumps(cfg))
    if kanban is not None:
        (project / "PROJECT_KANBAN.md").write_text(kanban)
    return project


def run_gate(project, event=PUSH):
    return subprocess.run([sys.executable, str(project / ".claude" / "hooks" / GATE)],
                          input=json.dumps(event), capture_output=True, text=True,
                          cwd=project, env=clean_env(CLAUDE_PROJECT_DIR=str(project)),
                          timeout=60)


def reason(result):
    assert result.stdout.strip(), f"expected a block; stderr={result.stderr!r}"
    return json.loads(result.stdout)["reason"]


def blocker_line(text):
    return next(line for line in text.splitlines() if MISSING in line)


def pulled_kanban(tasks):
    """A board-cache render of `tasks`, as T154's pull writes it."""
    from board import render
    from board.base import Task
    return render.render_kanban([Task(**t) for t in tasks], today="2026-10-19")


def offline(project):
    """The pull fails, so the gate evaluates the cache already on disk."""
    (project / "board.json").unlink()


# --- AC1 / AC2: only my Ready for Review tasks are checked --------------------------

def test_mine_blocks_teammate_is_named_in_a_note(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "alice"), task("ENG-171", "bob")])
    result = run_gate(project)
    text = reason(result)
    assert blocker_line(text).endswith(MISSING + "ENG-170 (no evidence row)")
    assert "ENG-171" in result.stderr


def test_only_teammate_review_row_lets_push_through(tmp_path):
    project = make_project(tmp_path, [task("ENG-171", "bob")])
    result = run_gate(project)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "ENG-171" in result.stderr
    assert "**ENG-171**" in (project / "PROJECT_KANBAN.md").read_text(), "gate did not pull"


def test_me_matches_case_insensitively_toward_checking(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "Alice")])
    assert blocker_line(reason(run_gate(project))).endswith(MISSING + "ENG-170 (no evidence row)")


def test_a_different_token_is_a_teammate_not_me(tmp_path):
    # `alice2` is not `alice` (only case is folded): a different person's row, noted.
    project = make_project(tmp_path, [task("ENG-171", "alice2")])
    result = run_gate(project)
    assert result.stdout.strip() == ""
    assert "ENG-171" in result.stderr


def test_forged_assignee_in_title_cannot_reassign_a_row(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "alice", title="mine | @bob"),
                                      task("ENG-171", "bob", title="theirs | @alice")])
    assert blocker_line(reason(run_gate(project))).endswith(MISSING + "ENG-170 (no evidence row)")


# --- AC3: every doubt checks every row ------------------------------------------------

def test_me_missing_checks_every_row_and_warns(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "alice"), task("ENG-171", "bob")],
                           me=None)
    result = run_gate(project)
    text = reason(result)
    assert blocker_line(text).endswith(
        MISSING + "ENG-170 (no evidence row), ENG-171 (no evidence row)")
    assert "`me` is missing from .claude/board.json — every Ready for Review task is checked" \
        in result.stderr


def test_cache_that_is_not_a_board_render_checks_every_row(tmp_path):
    local_board = ("# PROJECT_KANBAN\n### Ready for Review\n"
                   "- [ ] **ENG-171** — t | @bob\n### Done\n")
    project = make_project(tmp_path, kanban=local_board)
    offline(project)
    result = run_gate(project)
    assert blocker_line(reason(result)).endswith(MISSING + "ENG-171 (no evidence row)")
    assert "not a board render — every Ready for Review task is checked" in result.stderr
    assert UNREACHABLE in result.stderr


def test_row_with_two_assignee_fields_is_checked(tmp_path):
    cache = pulled_kanban([task("ENG-171", "bob")]).replace("| @bob |", "| @bob | @carol |")
    assert "@bob | @carol" in cache
    project = make_project(tmp_path, kanban=cache)
    offline(project)
    assert blocker_line(reason(run_gate(project))).endswith(MISSING + "ENG-171 (no evidence row)")


# --- AC4: unassigned is checked ---------------------------------------------------------

def test_unassigned_review_row_is_checked(tmp_path):
    project = make_project(tmp_path, [task("ENG-172", None)])
    assert blocker_line(reason(run_gate(project))).endswith(MISSING + "ENG-172 (no evidence row)")


# --- Fail closed: a broken filter checks every row ----------------------------------

def test_filter_exception_checks_every_row(tmp_path):
    project = make_project(tmp_path, [task("ENG-171", "bob")])
    moments = project / ".claude" / "hooks" / "lib" / "board" / "moments.py"
    moments.write_text(moments.read_text()
                       + "\n\ndef my_review_tasks(*args, **kwargs):\n    raise RuntimeError\n")
    result = run_gate(project)
    assert blocker_line(reason(result)).endswith(MISSING + "ENG-171 (no evidence row)")
    assert "Ready for Review filter failed — every Ready for Review task is checked" \
        in result.stderr


# --- AC5: local mode unchanged ----------------------------------------------------------

def test_local_mode_checks_every_row_exactly_as_today(tmp_path):
    kanban = ("# PROJECT_KANBAN\n### Ready for Review\n"
              "- [ ] **T900** — mine | @alice\n- [ ] **T901** — theirs | @bob\n### Done\n")
    project = make_project(tmp_path, online=False, kanban=kanban)
    result = run_gate(project)
    text = reason(result)
    assert text.startswith(
        "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • "
        + MISSING + "T900 (no evidence row), T901 (no evidence row)\n"
        "Complete Stage 4 review and Stage 5 verify first.\n")
    assert "Board:" not in text
    assert result.stderr == ""
