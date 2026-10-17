import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "lane_check.py")

GUIDE = """# TASK_GUIDE — T900: {title}
**Complexity Level**: {level}

**Restated intent**:
> do the thing

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `src/a.py` | edit |
| `tests/test_*.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `src/forbidden.py` | no |
"""


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_repo(tmp_path, files, level="C0", title="Do X"):
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "seed").write_text("s\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    for name, n in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n" * n)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "work")
    guide = tmp_path / "guide.md"
    guide.write_text(GUIDE.format(title=title, level=level))
    return repo, guide


def run(repo, guide):
    r = subprocess.run([sys.executable, SCRIPT, str(guide), "HEAD~1..HEAD"], cwd=repo,
                       capture_output=True, text=True)
    assert r.returncode == 0
    return r.stdout.strip()


def test_fits(tmp_path):
    repo, guide = make_repo(tmp_path, {"src/a.py": 5})
    assert run(repo, guide) == "lane: C0, 1 files, 5 lines, FITS"


def test_too_many_files(tmp_path):
    repo, guide = make_repo(tmp_path, {f"tests/test_{i}.py": 1 for i in range(6)})
    assert "EXCEEDS (files 6 > 2)" in run(repo, guide)


def test_unpredicted_listed(tmp_path):
    repo, guide = make_repo(tmp_path, {"src/a.py": 1, "src/other.py": 1, "src/forbidden.py": 1},
                            level="C1")
    out = run(repo, guide)
    assert "unpredicted: src/forbidden.py, src/other.py" in out


def test_gate2_floor(tmp_path):
    repo, guide = make_repo(tmp_path, {"src/a.py": 1}, level="C1", title="refactor X")
    assert "EXCEEDS (Gate 2 floor)" in run(repo, guide)


def test_missing_guide(tmp_path):
    repo, _ = make_repo(tmp_path, {"src/a.py": 1})
    out = run(repo, tmp_path / "nope.md")
    assert out.startswith("UNKNOWN (")


def test_no_complexity_is_unknown(tmp_path):
    repo, guide = make_repo(tmp_path, {"src/a.py": 1})
    guide.write_text("# old guide\n")
    assert run(repo, guide).startswith("UNKNOWN (")


def test_bookkeeping_excluded(tmp_path):
    repo, guide = make_repo(tmp_path, {"PROJECT_KANBAN.md": 50, "memory/decisions.md": 50,
                                       "tasks/TASK_REVIEW_T900.md": 50, "package-lock.json": 99})
    assert run(repo, guide) == "lane: C0, 0 files, 0 lines, FITS"


def test_binary_counts_file_zero_lines(tmp_path):
    repo, guide = make_repo(tmp_path, {"src/z.txt": 0})
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "a.py").write_bytes(b"\x00\x01\x02" * 10)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "bin")
    assert run(repo, guide) == "lane: C0, 1 files, 0 lines, FITS"


def test_rename_counts_once(tmp_path):
    repo, guide = make_repo(tmp_path, {"src/a.py": 20})
    git(repo, "mv", "src/a.py", "src/b.py")
    git(repo, "commit", "-qm", "mv")
    out = run(repo, guide)
    assert out.startswith("lane: C0, 1 files, 0 lines")
