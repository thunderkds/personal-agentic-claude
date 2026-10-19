#!/usr/bin/env python3
"""T157 — in board mode `online` only my In Progress tasks block my push, and the gate
pulls the board cache first.

  AC1 — teammate's ENG-171 In Progress (assignee != me) does not block `git push`; my
        ENG-170 does.
  AC2 — local mode: no pull, no new file, today's block (the existing merge-gate tests
        are the byte-identity check; here: no subprocess and no file appears).
  AC5 — the pre-merge pull runs before the gate evaluates.
  FR-010 — a failed pull warns `board unreachable — using cache (N unsynced)` and the
        gate evaluates the cache.
  Edge cases — `me` missing → block on all + warn; unassigned → not blocking, warned;
        a title forging `| @me` cannot change whose task a row is; a cache that is not a
        board render (pull failed) → block on all; unusable board.json → today's gate.

Every project is a temp copy (hooks + `scripts/board_sync.py`), so each `__file__`-relative
ROOT resolves to it. The board is the fake adapter: no network.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_my_tasks.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
ROOT = HOOKS.parent.parent
GATE = "pre_bash_block_unsafe_merge.py"
PUSH = {"tool_name": "Bash", "tool_input": {"command": "git push"}}
UNREACHABLE = "board unreachable — using cache"

sys.path.insert(0, str(HOOKS / "lib"))


def task(task_id, status, assignee, title="t"):
    return {"id": task_id, "title": title, "status": status, "assignee": assignee,
            "description": f"# guide {task_id}\n"}


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "LINEAR_API_KEY")}
    env.update(extra)
    return env


def make_project(tmp_path, tasks=None, config="online", me="alice", kanban=None):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (project / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "board_sync.py", project / "scripts" / "board_sync.py")
    (project / "tasks").mkdir()
    (project / "board.json").write_text(json.dumps(tasks or []))
    if config == "online":
        cfg = {"board": "fake", "fake_board": "board.json", "id_pattern": r"ENG-\d+"}
        if me is not None:
            cfg["me"] = me
        (project / ".claude" / "board.json").write_text(json.dumps(cfg))
    elif config == "broken":
        (project / ".claude" / "board.json").write_text("{not json")
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


def pulled_kanban(tmp_path, tasks):
    """A board-cache render of `tasks`, as T154's pull writes it."""
    from board import render
    from board.base import Task
    return render.render_kanban([Task(**t) for t in tasks], today="2026-10-19")


# --- AC1: only my In Progress tasks block ------------------------------------------------

def test_teammate_in_progress_does_not_block_mine_does(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "In Progress", "alice"),
                                      task("ENG-171", "In Progress", "bob")])
    text = reason(run_gate(project))
    assert "Tasks still In Progress: ENG-170\n" in text
    assert "ENG-171" not in text


def test_only_teammate_in_progress_lets_push_through(tmp_path):
    project = make_project(tmp_path, [task("ENG-171", "In Progress", "bob"),
                                      task("ENG-104", "Done", "alice")])
    result = run_gate(project)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "**ENG-171**" in (project / "PROJECT_KANBAN.md").read_text(), "gate did not pull"


def test_me_matches_case_insensitively_toward_blocking(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "In Progress", "Alice")])
    assert "Tasks still In Progress: ENG-170" in reason(run_gate(project))


def test_forged_assignee_in_title_cannot_reassign_a_row(tmp_path):
    project = make_project(tmp_path, [
        task("ENG-170", "In Progress", "alice", title="mine | @bob"),
        task("ENG-171", "In Progress", "bob", title="theirs | @alice"),
    ])
    text = reason(run_gate(project))
    assert "Tasks still In Progress: ENG-170\n" in text
    assert "ENG-171" not in text


# --- Edge cases: fail toward blocking ------------------------------------------------

def test_me_missing_blocks_on_all_and_warns(tmp_path):
    project = make_project(tmp_path, [task("ENG-170", "In Progress", "alice"),
                                      task("ENG-171", "In Progress", "bob")], me=None)
    result = run_gate(project)
    text = reason(result)
    assert "Tasks still In Progress: ENG-170, ENG-171\n" in text
    assert "`me`" in text and "`me`" in result.stderr


def test_unassigned_in_progress_does_not_block_but_warns(tmp_path):
    project = make_project(tmp_path, [task("ENG-172", "In Progress", None)])
    result = run_gate(project)
    assert result.stdout.strip() == ""
    assert "ENG-172" in result.stderr and "unassigned" in result.stderr


def test_cache_that_is_not_a_board_render_blocks_on_all(tmp_path):
    local_board = "# PROJECT_KANBAN\n### In Progress\n- [ ] **T142** — local row\n### Done\n"
    project = make_project(tmp_path, kanban=local_board)
    (project / "board.json").unlink()  # pull fails → the hand-written cache stays
    result = run_gate(project)
    assert "Tasks still In Progress: T142" in reason(result)
    assert UNREACHABLE in result.stderr


def test_unusable_board_config_keeps_todays_gate_and_does_not_pull(tmp_path):
    # Unusable config → IDs fall back to `T\d+` (T153), and no assignee filter applies.
    kanban = pulled_kanban(tmp_path, [task("T171", "In Progress", "bob")])
    project = make_project(tmp_path, config="broken", kanban=kanban)
    marker = project / "pulled"
    (project / "scripts" / "board_sync.py").write_text(
        f"open({str(marker)!r}, 'w').close()\n")
    result = run_gate(project)
    assert "Tasks still In Progress: T171\n" in reason(result)
    assert not marker.exists()


# --- AC5 / FR-010: the pre-merge pull ---------------------------------------------------

def test_pre_merge_pull_runs_before_the_gate_evaluates(tmp_path):
    stale = pulled_kanban(tmp_path, [task("ENG-170", "In Progress", "alice")])
    project = make_project(tmp_path, [task("ENG-170", "Done", "alice")], kanban=stale)
    result = run_gate(project)
    assert result.stdout.strip() == "", "the stale cache was evaluated, not the pulled board"
    assert "### Done\n- [x] **ENG-170**" in (project / "PROJECT_KANBAN.md").read_text()


def test_failed_pull_warns_and_gate_uses_cache(tmp_path):
    cache = pulled_kanban(tmp_path, [task("ENG-170", "In Progress", "alice")])
    project = make_project(tmp_path, kanban=cache)
    (project / "board.json").unlink()
    (project / ".board").mkdir()
    (project / ".board" / "outbox.jsonl").write_text('{"a": 1}\n{"a": 2}\n\n{"a": 3}\n')
    result = run_gate(project)
    assert "Tasks still In Progress: ENG-170" in reason(result)
    assert f"{UNREACHABLE} (3 unsynced)" in result.stderr
    assert (project / "PROJECT_KANBAN.md").read_text() == cache


def test_hanging_pull_times_out_and_never_stalls_the_hook(tmp_path):
    from board import moments
    project = make_project(tmp_path)
    (project / "scripts" / "board_sync.py").write_text("import time\ntime.sleep(30)\n")
    started = time.monotonic()
    warning = moments.pull_cache(str(project), timeout=1)
    assert time.monotonic() - started < 10
    assert warning == f"{UNREACHABLE} (0 unsynced)"


def test_hook_pull_timeout_is_short():
    from board import moments
    assert 0 < moments.PULL_TIMEOUT_S <= 10


# --- AC2: local mode — no pull, no new file ------------------------------------------

def test_local_mode_never_pulls_and_writes_nothing(tmp_path):
    kanban = "# PROJECT_KANBAN\n### In Progress\n- [ ] **T900** — local\n### Done\n"
    project = make_project(tmp_path, config=None, kanban=kanban)
    marker = project / "pulled"
    (project / "scripts" / "board_sync.py").write_text(
        f"open({str(marker)!r}, 'w').close()\n")
    before = sorted(p for p in project.rglob("*") if "__pycache__" not in p.parts)
    result = run_gate(project)
    after = sorted(p for p in project.rglob("*") if "__pycache__" not in p.parts)
    assert "Tasks still In Progress: T900\n" in reason(result)
    assert not marker.exists()
    assert before == after
    assert result.stderr == ""
