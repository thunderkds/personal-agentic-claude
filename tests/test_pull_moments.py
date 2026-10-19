"""T157 — the pull moments (FR-009, FR-010) and board text as gate input (NFR-005).

  AC3 — `wake`, `craft-spawn-prompt` (pre-spawn) and the Ready-for-Review step each invoke
        the pull; a failed pull prints `board unreachable — using cache (N unsynced)` and
        continues (exit 0).
  AC4 — spawn records the guide hash; at Ready for Review a changed hash prints
        `<ID>'s guide changed while you were working — review against the new version?`.
  Local mode — zero network, zero new files.
  Edge case (T154 Stage 4) — in board mode `online` a sensitive path predicted only by a
        pulled guide's `Files to Change` still asks in `pre_tool_sensitive_path.py`.

No network: the fake board adapter stands in for Linear.

Run with: python3 -m pytest tests/test_pull_moments.py -v
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
UNREACHABLE = "board unreachable — using cache"
CHANGED = "ENG-170's guide changed while you were working — review against the new version?"
GUIDE = "# guide ENG-170 v1\n\n## Files to Change (Predicted)\n\n| File | Change |\n|---|---|\n| `.env` | x |\n"


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "LINEAR_API_KEY")}
    env.update(extra)
    return env


def write_board(project, description=GUIDE):
    (project / "board.json").write_text(json.dumps([
        {"id": "ENG-170", "title": "mine", "status": "In Progress", "assignee": "alice",
         "description": description}]))


def make_project(tmp_path, online=True):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    shutil.copy(ROOT / ".claude" / "sensitive-paths.txt", project / ".claude")
    (project / "scripts").mkdir()
    for name in ("board_sync.py", "pull_moment.py"):
        shutil.copy(ROOT / "scripts" / name, project / "scripts" / name)
    (project / "tasks").mkdir()
    write_board(project)
    if online:
        (project / ".claude" / "board.json").write_text(json.dumps(
            {"board": "fake", "fake_board": "board.json", "id_pattern": r"ENG-\d+",
             "me": "alice"}))
    return project


def moment(project, *args):
    return subprocess.run([sys.executable, str(project / "scripts" / "pull_moment.py"), *args],
                          capture_output=True, text=True, cwd=project, env=clean_env(),
                          timeout=60)


def files(project):
    return sorted(str(p.relative_to(project)) for p in project.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


# --- AC3: every moment pulls; a failed pull warns and continues ----------------------

def test_wake_moment_pulls_the_board_cache(tmp_path):
    project = make_project(tmp_path)
    result = moment(project, "wake")
    assert result.returncode == 0, result.stderr
    assert "**ENG-170**" in (project / "PROJECT_KANBAN.md").read_text()
    assert (project / "tasks" / "TASK_GUIDE_ENG-170.md").read_text() == GUIDE


def test_wake_after_a_good_pull_names_unsynced_writes(tmp_path):
    """T156+T157 merge: the wake moment carries T156's unsynced line (one wake step, 8 KB cap)."""
    project = make_project(tmp_path)
    (project / ".board").mkdir()
    (project / ".board" / "outbox.jsonl").write_text('{"a": 1}\n{"a": 2}\n')
    result = moment(project, "wake")
    assert result.returncode == 0, result.stderr
    assert "⚠ 2 unsynced board writes — run python3 scripts/board_sync.py flush" in result.stdout
    (project / ".board" / "outbox.jsonl").write_text("")
    assert "unsynced" not in moment(project, "wake").stdout


def test_failed_pull_warns_with_unsynced_count_and_exits_zero(tmp_path):
    project = make_project(tmp_path)
    (project / "board.json").unlink()
    (project / ".board").mkdir()
    (project / ".board" / "outbox.jsonl").write_text('{"a": 1}\n{"a": 2}\n')
    for args in (["wake"], ["spawn", "ENG-170"], ["review", "ENG-170"]):
        result = moment(project, *args)
        assert result.returncode == 0, args
        assert f"{UNREACHABLE} (2 unsynced)" in result.stdout, args


# --- AC4: spawn records the guide hash; review flags a change ------------------------

def test_spawn_records_hash_and_unchanged_guide_is_not_flagged(tmp_path):
    project = make_project(tmp_path)
    assert moment(project, "spawn", "ENG-170").returncode == 0
    assert (project / ".claude" / "hooks" / ".state" / "guide_hash_ENG-170.txt").is_file()
    result = moment(project, "review", "ENG-170")
    assert result.returncode == 0
    assert "changed while you were working" not in result.stdout


def test_review_flags_a_guide_changed_since_spawn(tmp_path):
    project = make_project(tmp_path)
    moment(project, "spawn", "eng-170")
    write_board(project, GUIDE.replace("v1", "v2"))
    result = moment(project, "review", "ENG-170")
    assert result.returncode == 0
    assert CHANGED in result.stdout


def test_review_flags_a_guide_removed_since_spawn(tmp_path):
    project = make_project(tmp_path)
    moment(project, "spawn", "ENG-170")
    write_board(project, "")
    (project / "tasks" / "TASK_GUIDE_ENG-170.md").unlink()
    assert CHANGED in moment(project, "review", "ENG-170").stdout


def test_review_without_spawn_record_says_so(tmp_path):
    project = make_project(tmp_path)
    result = moment(project, "review", "ENG-170")
    assert result.returncode == 0
    assert "no spawn-time guide hash" in result.stdout


def test_unsafe_task_id_is_refused_and_writes_nothing(tmp_path):
    project = make_project(tmp_path)
    before = files(project)
    result = moment(project, "spawn", "../../evil")
    assert result.returncode == 2
    assert files(project) == before


# --- Local mode: zero network, zero new files ------------------------------------------

def test_local_mode_moments_do_nothing(tmp_path):
    project = make_project(tmp_path, online=False)
    marker = project / "pulled"
    (project / "scripts" / "board_sync.py").write_text(
        f"open({str(marker)!r}, 'w').close()\n")
    before = files(project)
    for args in (["wake"], ["spawn", "T157"], ["review", "T157"]):
        result = moment(project, *args)
        assert (result.returncode, result.stdout) == (0, ""), args
    assert files(project) == before


# --- NFR-005: a pulled guide cannot pre-authorise a sensitive path --------------------

def sensitive(project, task_id="ENG-170"):
    event = {"tool_name": "Edit", "tool_input": {"file_path": ".env"}, "cwd": str(project)}
    return subprocess.run(
        [sys.executable, str(project / ".claude" / "hooks" / "pre_tool_sensitive_path.py")],
        input=json.dumps(event), capture_output=True, text=True, cwd=project, timeout=30,
        env=clean_env(CLAUDE_PROJECT_DIR=str(project), CLAUDE_ACTIVE_TASK=task_id))


def test_online_pulled_guide_prediction_still_asks(tmp_path):
    project = make_project(tmp_path)
    moment(project, "wake")
    out = json.loads(sensitive(project).stdout)["hookSpecificOutput"]
    assert out["permissionDecision"] == "ask"
    assert "board" in out["permissionDecisionReason"]


def test_unusable_board_config_still_asks(tmp_path):
    project = make_project(tmp_path)
    moment(project, "wake")
    (project / ".claude" / "board.json").write_text("{not json")
    out = json.loads(sensitive(project).stdout)["hookSpecificOutput"]
    assert out["permissionDecision"] == "ask"


def test_local_guide_prediction_still_exempts(tmp_path):
    project = make_project(tmp_path, online=False)
    (project / "tasks" / "TASK_GUIDE_T900.md").write_text(GUIDE)
    result = sensitive(project, "T900")
    assert result.returncode == 0 and result.stdout.strip() == ""


# --- AC3 wiring: each moment is named where it happens --------------------------------

def test_each_moment_is_wired_where_it_happens():
    wiring = {
        "skills/wake/SKILL.md": "python3 scripts/pull_moment.py wake",
        "skills/craft-spawn-prompt/SKILL.md": "python3 scripts/pull_moment.py spawn",
        "docs/claude-md/pipeline-stages.md": "python3 scripts/pull_moment.py review",
    }
    for path, command in wiring.items():
        assert command in (ROOT / path).read_text(), path


def test_pull_moment_ships_with_the_kit():
    lines = (ROOT / "MANIFEST").read_text().splitlines()
    assert "scripts/pull_moment.py" in [line.split()[0] for line in lines if line.strip()]
