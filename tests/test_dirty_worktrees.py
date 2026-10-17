"""T150 - dirty_worktrees.py (SC1-SC5) and the spawn-mode doc strings (SC6)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "wake", "scripts", "dirty_worktrees.py")

BOARD = """# Board
### In Progress
- [ ] **T901** - one | see **T999** in text
- [ ] **T903** - three
- [ ] **T904** - four
- [ ] **T1000** - four digits
### Done
- [x] **T902** - two
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def run(cwd):
    r = subprocess.run([sys.executable, SCRIPT], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0
    return r.stdout


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "PROJECT_KANBAN.md").write_text(BOARD)
    (repo / "a.txt").write_text("a")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def add_tree(repo, tmp_path, name, branch, dirty):
    wt = tmp_path / name
    git(repo, "worktree", "add", "-q", "-b", branch, str(wt))
    if dirty:
        (wt / "a.txt").write_text("changed")
        (wt / "n1.txt").write_text("1")
        (wt / "n2.txt").write_text("2")
    return wt


def test_sc1_dirty_in_progress_worktree_reported(tmp_path):
    repo = make_repo(tmp_path)
    wt = add_tree(repo, tmp_path, "wt901", "feat/t901-x", True)
    out = run(repo)
    assert out.strip() == f"T901 {wt} 1 modified, 2 untracked"


def test_sc2_clean_worktree_silent(tmp_path):
    repo = make_repo(tmp_path)
    add_tree(repo, tmp_path, "wt901", "feat/t901-x", False)
    assert run(repo) == ""


def test_sc3_done_task_ignored(tmp_path):
    repo = make_repo(tmp_path)
    add_tree(repo, tmp_path, "wt902", "feat/t902-x", True)
    assert run(repo) == ""


def test_sc3_bold_cross_reference_is_not_a_row_id(tmp_path):
    repo = make_repo(tmp_path)
    add_tree(repo, tmp_path, "wt999", "feat/t999-x", True)
    assert run(repo) == ""


def test_sc4_two_tasks_one_worktree_one_line_each(tmp_path):
    repo = make_repo(tmp_path)
    add_tree(repo, tmp_path, "wt903", "feat/t903-t904-x", True)
    lines = run(repo).strip().splitlines()
    assert [l.split()[0] for l in lines] == ["T903", "T904"]


def test_four_digit_task_id_matches_whole_id(tmp_path):
    repo = make_repo(tmp_path)
    add_tree(repo, tmp_path, "wt1000", "feat/t1000-x", True)
    assert [l.split()[0] for l in run(repo).strip().splitlines()] == ["T1000"]


def test_status_takes_no_optional_index_lock():
    with open(SCRIPT) as f:
        assert '"--no-optional-locks"' in f.read()


def test_sc4_main_worktree_never_reported(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat/t901-main")
    (repo / "dirty.txt").write_text("x")
    assert run(repo) == ""


def test_sc5_no_board(tmp_path):
    repo = make_repo(tmp_path)
    add_tree(repo, tmp_path, "wt901", "feat/t901-x", True)
    os.remove(repo / "PROJECT_KANBAN.md")
    assert run(repo) == ""


def test_sc5_not_a_git_repo(tmp_path):
    (tmp_path / "PROJECT_KANBAN.md").write_text(BOARD)
    assert run(tmp_path) == ""


def test_sc5_missing_worktree_dir(tmp_path):
    repo = make_repo(tmp_path)
    wt = add_tree(repo, tmp_path, "wt901", "feat/t901-x", True)
    subprocess.run(["rm", "-rf", str(wt)], check=True)
    assert run(repo) == ""


def _read(*parts):
    with open(os.path.join(ROOT, *parts)) as f:
        return f.read()


def test_sc6_spawn_mode_rule_documented():
    stage = _read("docs", "claude-md", "pipeline-stages.md")
    assert "**Spawn mode**" in stage and "background `Agent()`" in stage
    assert "nested-userns" in stage
    assert "spawn mode" in _read("skills", "craft-spawn-prompt", "SKILL.md")
    wake = _read("skills", "wake", "SKILL.md")
    assert "dirty_worktrees.py" in wake and "uncommitted" in wake
