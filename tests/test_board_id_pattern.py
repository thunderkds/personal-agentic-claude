"""T153 — task IDs come from board config, so gates accept `T142` and `ENG-170` side by side.

Every check drives a real entry point. Hooks run from a copy of `.claude/hooks` inside a
temp project (their ROOT is `__file__`-relative, so the copy reads the temp board and the
temp `.claude/board.json`); skill scripts run in place against a temp project.

  AC2 — `{"id_pattern": "ENG-\\d+"}`: merge gate lists T142 and ENG-170; Write registers
        TASK_GUIDE_ENG-170.md; spawn validator, resolve_task_id, memory_slice.py and
        token_meter.py resolve ENG-170.
  AC3 — dirty_worktrees.py maps `eng-170-dark-mode` to ENG-170 and `feat/t142-x` to T142.
  AC4 — malformed JSON / invalid regex: one stderr warning, `T\\d+` behavior.
  AC5 — normalize_task_id zero-pads T IDs and upper-cases board IDs.
AC1 (no config → unchanged) is the rest of the suite, plus the no-config cases below.

Run with: python3 -m pytest tests/test_board_id_pattern.py -v
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
MEMORY_SLICE = ROOT / "skills" / "craft-spawn-prompt" / "scripts" / "memory_slice.py"
DIRTY = ROOT / "skills" / "wake" / "scripts" / "dirty_worktrees.py"
TOKEN_METER = ROOT / "scripts" / "token_meter.py"

ENG = {"id_pattern": r"ENG-\d+"}
MIXED_BOARD = """# Board
**Last updated**: 2026-10-19
### Todo
### In Progress
- [ ] **T142** - old task
- [ ] **ENG-170** - dark mode
### Done
- [x] **ENG-160** - done one
"""
GUIDE = "# TASK_GUIDE — {tid}: title for {tid}\n**Assigned agent**: common-infrastructure\n"


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR")}
    env.update(extra)
    return env


def make_project(tmp_path, config=None, board=MIXED_BOARD, raw_config=None):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    if raw_config is not None:
        (project / ".claude" / "board.json").write_text(raw_config)
    elif config is not None:
        (project / ".claude" / "board.json").write_text(json.dumps(config))
    (project / "PROJECT_KANBAN.md").write_text(board)
    (project / "tasks").mkdir()
    for tid in ("T142", "ENG-170"):
        (project / "tasks" / f"TASK_GUIDE_{tid}.md").write_text(GUIDE.format(tid=tid))
    return project


def run_hook(project, hook, event):
    return subprocess.run([sys.executable, str(project / ".claude" / "hooks" / hook)],
                          input=json.dumps(event), capture_output=True, text=True, cwd=project,
                          env=clean_env(CLAUDE_PROJECT_DIR=str(project)), timeout=30)


def push(project):
    result = run_hook(project, "pre_bash_block_unsafe_merge.py",
                      {"tool_name": "Bash", "tool_input": {"command": "git push"}})
    assert result.returncode == 0, result.stderr
    return result


def in_progress_line(result):
    reason = json.loads(result.stdout)["reason"]
    return next(l for l in reason.splitlines() if "In Progress" in l)


def spawn(project, prompt):
    result = run_hook(project, "pre_agent_validate_guide.py",
                      {"tool_name": "Agent", "tool_input": {"prompt": prompt}})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout) if result.stdout.strip() else {}


def resolve(project, event, **env):
    code = ("import json, sys; sys.path.insert(0, sys.argv[1]); "
            "from task_context import resolve_task_id; "
            "print(json.dumps(resolve_task_id(json.loads(sys.argv[2]))))")
    result = subprocess.run(
        [sys.executable, "-c", code, str(project / ".claude" / "hooks" / "lib"), json.dumps(event)],
        capture_output=True, text=True, env=clean_env(CLAUDE_PROJECT_DIR=str(project), **env),
        timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# --- AC2: merge gate ---------------------------------------------------------------

def test_merge_gate_lists_both_ids(tmp_path):
    line = in_progress_line(push(make_project(tmp_path, ENG)))
    assert "T142" in line and "ENG-170" in line


def test_merge_gate_without_config_lists_only_t_ids(tmp_path):
    project = make_project(tmp_path)
    line = in_progress_line(push(project))
    assert "T142" in line and "ENG-170" not in line
    assert not (project / ".claude" / "board.json").exists()


def test_merge_gate_github_style_hash_ids(tmp_path):
    board = MIXED_BOARD.replace("**ENG-170**", "**#170**")
    line = in_progress_line(push(make_project(tmp_path, {"id_pattern": r"#\d+"}, board=board)))
    assert "T142" in line and "#170" in line


def ready_for_review_board(tmp_path, config):
    """ENG-170 in Ready for Review with a filled verify row and a real pytest trace."""
    board = "# Board\n### In Progress\n### Ready for Review\n- [ ] **ENG-170** - dark mode\n"
    project = make_project(tmp_path, config, board=board)
    (project / "tasks" / "TASK_REVIEW_ENG-170.md").write_text(
        "## Evidence\n\n| Check | Result | Notes |\n|---|---|---|\n"
        "| verify | ☑ pass | skill run, feature confirmed working — pass |\n")
    trace = project / "memory" / "event-trace"
    trace.mkdir(parents=True)
    (trace / "ENG-170.jsonl").write_text(json.dumps({
        "tool_name": "Bash", "is_error": False,
        "summary": json.dumps({"command": "python3 -m pytest -q"})}) + "\n")
    return project


def test_merge_gate_passes_board_id_with_evidence(tmp_path):
    result = push(ready_for_review_board(tmp_path, ENG))
    assert result.stdout.strip() == "", result.stdout


def test_merge_gate_board_id_without_evidence_blocks(tmp_path):
    project = ready_for_review_board(tmp_path, ENG)
    (project / "tasks" / "TASK_REVIEW_ENG-170.md").unlink()
    reason = json.loads(push(project).stdout)["reason"]
    assert "ENG-170 (no evidence row)" in reason


# --- AC2: register on Write ---------------------------------------------------------

def test_write_registers_board_id_guide(tmp_path):
    project = make_project(tmp_path, ENG, board="# Board\n### Todo\n### Done\n")
    guide = project / "tasks" / "TASK_GUIDE_ENG-171.md"
    guide.write_text(GUIDE.format(tid="ENG-171"))
    result = run_hook(project, "post_write_register_task.py",
                      {"tool_name": "Write", "tool_input": {"file_path": str(guide)}})
    assert result.returncode == 0, result.stderr
    board = (project / "PROJECT_KANBAN.md").read_text()
    assert "- [ ] **ENG-171** — title for ENG-171 |" in board


def test_write_without_config_ignores_board_id_guide(tmp_path):
    project = make_project(tmp_path, board="# Board\n### Todo\n### Done\n")
    guide = project / "tasks" / "TASK_GUIDE_ENG-171.md"
    guide.write_text(GUIDE.format(tid="ENG-171"))
    run_hook(project, "post_write_register_task.py",
             {"tool_name": "Write", "tool_input": {"file_path": str(guide)}})
    assert "ENG-171" not in (project / "PROJECT_KANBAN.md").read_text()


# --- AC2: spawn validator -----------------------------------------------------------

def test_spawn_validator_blocks_missing_board_id_guide(tmp_path):
    out = spawn(make_project(tmp_path, ENG), "Guide: tasks/TASK_GUIDE_ENG-171.md")
    assert out.get("decision") == "block" and "ENG-171" in out["reason"]


def test_spawn_validator_allows_existing_board_id_guide(tmp_path):
    project = make_project(tmp_path, ENG)
    for prompt in ("Guide: tasks/TASK_GUIDE_ENG-170.md", "Task ID: ENG-170", "Task ID: eng-170"):
        assert spawn(project, prompt).get("decision") != "block", prompt


def test_spawn_validator_blocks_missing_t_id_alongside(tmp_path):
    out = spawn(make_project(tmp_path, ENG),
                "tasks/TASK_GUIDE_ENG-170.md and tasks/TASK_GUIDE_T143.md")
    assert out.get("decision") == "block"
    assert "T143" in out["reason"] and "ENG-170" not in out["reason"]


def test_spawn_validator_hash_id(tmp_path):
    project = make_project(tmp_path, {"id_pattern": r"#\d+"})
    out = spawn(project, "Guide: tasks/TASK_GUIDE_#171.md")
    assert out.get("decision") == "block" and "#171" in out["reason"]


def test_spawn_validator_ignores_path_unsafe_id(tmp_path):
    """An over-broad pattern must never turn a prompt ID into a path outside tasks/."""
    project = make_project(tmp_path, {"id_pattern": r"[A-Z./]+-\d+"})
    out = spawn(project, "Task ID: ../X-1")
    assert out.get("decision") != "block", out


# --- AC2: task_context.resolve_task_id -------------------------------------------------

def test_resolve_task_id_from_board_id_guide_path(tmp_path):
    project = make_project(tmp_path, ENG)
    event = {"tool_name": "Read", "tool_input": {"file_path": "tasks/TASK_GUIDE_ENG-170.md"}}
    assert resolve(project, event) == "ENG-170"


def test_resolve_task_id_from_env_and_agent_prompt(tmp_path):
    project = make_project(tmp_path, ENG)
    assert resolve(project, {}, CLAUDE_ACTIVE_TASK="eng-170") == "ENG-170"
    event = {"tool_name": "Agent", "tool_input": {"prompt": "Task ID: ENG-170\nwork"}}
    assert resolve(project, event) == "ENG-170"


def test_resolve_task_id_from_state_file(tmp_path):
    project = make_project(tmp_path, ENG)
    state = project / ".claude" / "hooks" / ".state"
    state.mkdir()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (state / "active_task").write_text(f"ENG-170\n{now}\n")
    assert resolve(project, {}) == "ENG-170"


def test_resolve_task_id_without_config_ignores_board_ids(tmp_path):
    project = make_project(tmp_path)
    event = {"tool_name": "Read", "tool_input": {"file_path": "tasks/TASK_GUIDE_ENG-170.md"}}
    assert resolve(project, event) is None
    assert resolve(project, {}, CLAUDE_ACTIVE_TASK="ENG-170") is None


def test_resolve_task_id_rejects_path_unsafe_id(tmp_path):
    """An over-broad pattern must never put a path separator into a trace file name."""
    project = make_project(tmp_path, {"id_pattern": r"[A-Z./]+-\d+"})
    assert resolve(project, {}, CLAUDE_ACTIVE_TASK="../X-1") is None


# --- AC2: memory_slice.py -------------------------------------------------------------

def test_memory_slice_resolves_board_id_and_its_dependencies(tmp_path):
    project = make_project(tmp_path, ENG)
    guide = project / "tasks" / "TASK_GUIDE_ENG-170.md"
    guide.write_text("# TASK_GUIDE — ENG-170: dark mode\n\n"
                     "**Depends on**: ENG-160, T142, ST100\n")
    (project / "memory").mkdir()
    (project / "memory" / "MEMORY.md").write_text(
        "### Decisions\n- [ENG-170 own line](x.md)\n- [ENG-160 dep line](x.md)\n"
        "- [T142 dep line](x.md)\n- [T100 must not match](x.md)\n- [unrelated](x.md)\n")
    result = subprocess.run([sys.executable, str(MEMORY_SLICE), str(guide)],
                            capture_output=True, text=True, timeout=30, env=clean_env())
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "<!-- memory-slice:ENG-170 -->" in out
    for line in ("ENG-170 own line", "ENG-160 dep line", "T142 dep line"):
        assert line in out
    assert "T100 must not match" not in out and "unrelated" not in out


# --- AC2: token_meter.py --------------------------------------------------------------

def test_token_meter_resolves_board_id_spawn(tmp_path):
    project = make_project(tmp_path, ENG)
    transcripts = tmp_path / "transcripts" / "proj"
    transcripts.mkdir(parents=True)
    lines = [
        {"type": "user", "message": {"content": "Read tasks/TASK_GUIDE_ENG-170.md now"}},
        {"type": "assistant", "message": {"id": "m1", "content": [{"type": "text", "text": "ok"}],
                                          "usage": {"input_tokens": 10, "output_tokens": 5,
                                                    "cache_read_input_tokens": 0,
                                                    "cache_creation_input_tokens": 0}}},
    ]
    (transcripts / "agent-w1.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    env = clean_env()
    env.pop("CLAUDE_CONFIG_DIR", None)
    result = subprocess.run([sys.executable, str(TOKEN_METER), "--projects-dir",
                             str(tmp_path / "transcripts"), "--task", "ENG-170", "--json"],
                            cwd=project, capture_output=True, text=True, env=env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert [s["task"] for s in json.loads(result.stdout)["spawns"]["items"]] == ["ENG-170"]


# --- AC3: dirty_worktrees.py ---------------------------------------------------------

def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def dirty_repo(tmp_path, config):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "PROJECT_KANBAN.md").write_text(MIXED_BOARD)
    if config is not None:
        (repo / ".claude").mkdir()
        (repo / ".claude" / "board.json").write_text(json.dumps(config))
    (repo / "a.txt").write_text("a")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    trees = {}
    for name, branch in (("wt170", "eng-170-dark-mode"), ("wt142", "feat/t142-x"),
                         ("wtst", "feat/st100-eng-1700")):
        wt = tmp_path / name
        git(repo, "worktree", "add", "-q", "-b", branch, str(wt))
        (wt / "a.txt").write_text("changed")
        trees[name] = wt
    return repo, trees


def run_dirty(repo):
    result = subprocess.run([sys.executable, str(DIRTY)], cwd=repo, capture_output=True,
                            text=True, timeout=30)
    assert result.returncode == 0
    return sorted(result.stdout.splitlines())


def test_dirty_worktrees_maps_lowercase_board_branch(tmp_path):
    repo, trees = dirty_repo(tmp_path, ENG)
    assert run_dirty(repo) == sorted([f"ENG-170 {trees['wt170']} 1 modified, 0 untracked",
                                      f"T142 {trees['wt142']} 1 modified, 0 untracked"])


def test_dirty_worktrees_without_config_maps_t_ids_only(tmp_path):
    repo, trees = dirty_repo(tmp_path, None)
    assert run_dirty(repo) == [f"T142 {trees['wt142']} 1 modified, 0 untracked"]


# --- AC4: bad config falls back to T\d+ with one warning ----------------------------------

@pytest.mark.parametrize("raw", [
    '{"id_pattern": "("}',                 # invalid regex
    '{"id_pattern": ',                     # malformed JSON
    '["ENG-\\\\d+"]',                      # not an object
    '{"id_pattern": 7}',                   # not a string
    '{"id_pattern": "(ENG)-\\\\d+"}',      # capturing group would shift every site's groups
    '{"id_pattern": "\\\\d*"}',            # matches the empty string
])
def test_bad_config_warns_once_and_falls_back(tmp_path, raw):
    project = make_project(tmp_path, raw_config=raw)
    result = push(project)
    line = in_progress_line(result)
    assert "T142" in line and "ENG-170" not in line
    warnings = [l for l in result.stderr.splitlines() if "board.json" in l]
    assert len(warnings) == 1, result.stderr
    out = spawn(project, "Guide: tasks/TASK_GUIDE_T143.md")
    assert out.get("decision") == "block" and "T143" in out["reason"]


def test_config_without_id_pattern_is_local_mode_silently(tmp_path):
    result = push(make_project(tmp_path, {"board": "linear"}))
    assert "ENG-170" not in in_progress_line(result)
    # No T153 config warning. (A `board` key is board mode `online` since T154, so the
    # T157 pull/`me` warnings may name the file; they are not id_pattern warnings.)
    assert "ignoring" not in result.stderr


# --- AC5: normalize_task_id ------------------------------------------------------------

def test_normalize_task_id_canonical_forms():
    sys.path.insert(0, str(HOOKS / "lib"))
    try:
        from board.config import normalize_task_id
        import task_context
    finally:
        sys.path.pop(0)
    assert normalize_task_id("T7") == "T007"
    assert normalize_task_id("t44") == "T044"
    assert normalize_task_id("T1234") == "T1234"
    assert normalize_task_id("eng-170") == "ENG-170"
    assert normalize_task_id("#170") == "#170"
    assert task_context.normalize_task_id("44") == "T044"
    assert task_context.normalize_task_id("eng-170") == "ENG-170"


# --- boundaries: `T\d+` never matches inside another ID ----------------------------------

def test_t_alternative_respects_boundaries(tmp_path):
    sys.path.insert(0, str(HOOKS / "lib"))
    try:
        from board.config import task_id_pattern
    finally:
        sys.path.pop(0)
    import re
    project = make_project(tmp_path, ENG)
    pattern = re.compile(task_id_pattern(str(project), bounded=True))
    assert pattern.findall("ENG-170 ST100 T142 TENG-1 xENG-2 #T9") == ["ENG-170", "T142", "T9"]
