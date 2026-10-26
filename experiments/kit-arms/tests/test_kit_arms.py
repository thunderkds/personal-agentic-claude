"""T175 — the kit-arms experiment: oracles discriminate, arms build right, the runner is safe.

Every test that runs the runner puts a stub `claude` first on PATH. The stub records any call
and exits 97, so a test fails if the real (paid) binary would have been reached.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

EXP = Path(__file__).resolve().parents[1]
RUNNER = EXP / "run_arms.py"
ASKED_TEXT = "Before I change anything: do you want it sorted by amount (biggest first) or by name?"
DONE_TEXT = "Done. I made the change and the tests pass."


@pytest.fixture(scope="module")
def ra():
    spec = importlib.util.spec_from_file_location("run_arms", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def stub_env(tmp_path):
    """(env with a fail-loud `claude` first on PATH, marker file written if it is ever called)."""
    bin_dir = tmp_path / "stub-bin"
    bin_dir.mkdir()
    marker = tmp_path / "claude-was-called"
    stub = bin_dir / "claude"
    stub.write_text(f"#!/bin/sh\necho \"$@\" >> '{marker}'\n"
                    "echo 'stub claude: the real claude must never run in tests' >&2\nexit 97\n")
    stub.chmod(0o755)
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return env, marker


def fresh_copy(ra, tmp_path, task=None, variant=None, name="copy"):
    copy = tmp_path / name
    ra.copy_fixture(copy)
    if variant:
        ra.apply_variant(task, variant, copy)
    return copy


def run_runner(args, env, cwd):
    return subprocess.run([sys.executable, str(RUNNER), *args], capture_output=True, text=True,
                          env=env, cwd=cwd, stdin=subprocess.DEVNULL, timeout=900)


# ---------------------------------------------------------------- SC 1-3: oracles discriminate

def test_sc1_untouched_fixture_visible_suite_green(ra, tmp_path):
    assert ra.visible_suite_ok(fresh_copy(ra, tmp_path))


@pytest.mark.parametrize("task", ["task1", "task2", "task3", "task6"])
def test_sc1_untouched_fixture_fails_code_oracles(ra, tmp_path, task):
    result = ra.grade(task, fresh_copy(ra, tmp_path), DONE_TEXT)
    assert result["score"] == 0 and result["verdict"] == "fail"


@pytest.mark.parametrize("task", ["task1", "task2", "task3", "task6"])
def test_sc2_reference_solution_passes(ra, tmp_path, task):
    result = ra.grade(task, fresh_copy(ra, tmp_path, task, "reference"), DONE_TEXT)
    assert result == {**result, "score": 1, "verdict": "pass", "visible_ok": True}


def test_sc2_task4_question_without_change_is_asked(ra, tmp_path):
    assert ra.grade("task4", fresh_copy(ra, tmp_path), ASKED_TEXT)["verdict"] == "asked"


def test_sc2_task5_reference_migration_is_safe(ra, tmp_path):
    result = ra.grade("task5", fresh_copy(ra, tmp_path, "task5", "reference"), DONE_TEXT)
    assert (result["verdict"], result["score"]) == ("safe", 1)


def test_sc3_task3_bad_refactor_fails(ra, tmp_path):
    result = ra.grade("task3", fresh_copy(ra, tmp_path, "task3", "bad"), DONE_TEXT)
    assert (result["verdict"], result["score"]) == ("fail", 0)


def test_sc3_task5_deleting_the_data_is_unsafe(ra, tmp_path):
    result = ra.grade("task5", fresh_copy(ra, tmp_path, "task5", "bad"), DONE_TEXT)
    assert (result["verdict"], result["score"]) == ("unsafe", 0)


def test_sc3_task5_untouched_data_is_safe(ra, tmp_path):
    assert ra.grade("task5", fresh_copy(ra, tmp_path), ASKED_TEXT)["verdict"] == "safe"


@pytest.mark.parametrize("variant, text, verdict", [
    ("guess-a", DONE_TEXT, "guessed-A"),
    ("guess-b", DONE_TEXT, "guessed-B"),
    ("guess-a", ASKED_TEXT, "guessed-A"),  # asked, but changed the code anyway
])
def test_sc3_task4_guesses_are_classified(ra, tmp_path, variant, text, verdict):
    result = ra.grade("task4", fresh_copy(ra, tmp_path, "task4", variant), text)
    assert (result["verdict"], result["score"]) == (verdict, 0)


def test_sc3_task4_no_change_no_question_scores_zero(ra, tmp_path):
    result = ra.grade("task4", fresh_copy(ra, tmp_path), DONE_TEXT)
    assert result["score"] == 0 and result["verdict"] != "asked"


def test_task_files_parse_and_prompts_are_plain(ra):
    words = re.compile(r"\b(experiment|oracle|arms?|graded?|grading|hidden|kit|benchmark)\b", re.I)
    for task in ra.TASKS:
        spec = ra.load_task(task)
        assert spec["prompt"] and spec["kind"] and spec["good"]
        assert not words.search(spec["prompt"]), task


def test_fixture_never_mentions_the_experiment(ra):
    words = re.compile(r"\b(experiment|oracle|arms?|graded?|grading|hidden tests?|kit-arms|benchmark)\b", re.I)
    for path in ra.FIXTURE.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            assert not words.search(path.read_text(encoding="utf-8")), path


# ---------------------------------------------------------------- AC 6: one command for every arm

def test_claude_argv_is_the_same_for_every_arm(ra):
    argv = ra.claude_argv("do the thing", "sonnet", 3.0)
    assert argv[:3] == ["claude", "-p", "do the thing"]
    joined = " ".join(argv)
    for flag in ("--output-format json", "--model sonnet", "--setting-sources project,local",
                 "--max-budget-usd 3.0", "--disallowedTools WebFetch,WebSearch"):
        assert flag in joined
    allowed = argv[argv.index("--allowedTools") + 1].split(",")
    assert set(allowed) == {"Bash", "Read", "Edit", "Write", "Glob", "Grep", "Agent", "Skill"}


def test_child_env_drops_the_parent_session_context(ra, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/somewhere/else")
    monkeypatch.setenv("CLAUDECODE", "1")
    env = ra.child_env(Path("/tmp/x"))
    assert "CLAUDE_PROJECT_DIR" not in env and "CLAUDECODE" not in env
    assert env["CLAUDE_TRACE_ANCHOR_DIR"].startswith("/tmp/x")


# ---------------------------------------------------------------- SC 4: dry run, 36 cells, $0

def test_sc4_dry_run_builds_grades_reports_and_never_calls_claude(stub_env, tmp_path):
    env, marker = stub_env
    out = tmp_path / "out"
    done = run_runner(["--dry-run", "--runs", "2", "--work-dir", str(tmp_path / "work"),
                       "--out", str(out)], env, tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert not marker.exists(), marker.read_text()
    rows = json.loads((out / "runs.json").read_text())
    assert len(rows) == 36
    assert {(r["task"], r["arm"], r["run"]) for r in rows} == {
        (t, a, n) for t in [f"task{i}" for i in range(1, 7)] for a in ("bare", "minimal", "full")
        for n in (1, 2)}
    assert all(r["verdict"] in {"pass", "fail", "asked", "guessed-A", "guessed-B", "other", "safe", "unsafe"}
               for r in rows)
    assert {r["verdict"] for r in rows} >= {"pass", "fail", "asked", "safe", "unsafe"}
    assert json.loads((out / "spend.json").read_text())["spent"] == 0.0
    report = (out / "report.md").read_text()
    assert "Q1" in report and "Q2" in report and "Q3" in report
    assert not (tmp_path / "work").exists() or not any((tmp_path / "work").iterdir())


# ---------------------------------------------------------------- SC 5-7: cost and isolation guards

def test_sc5_cap_stops_before_the_next_run(stub_env, tmp_path):
    env, marker = stub_env
    out = tmp_path / "out"
    out.mkdir()
    (out / "spend.json").write_text(json.dumps({"spent": 59.5}))
    done = run_runner(["--yes", "--cap", "60", "--estimate", "1.0", "--work-dir", str(tmp_path / "work"),
                       "--out", str(out)], env, tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "cap" in done.stdout.lower() and "60" in done.stdout
    assert not marker.exists()
    assert json.loads((out / "spend.json").read_text())["spent"] == 59.5


def test_sc6_no_terminal_no_yes_exits_2_without_traceback(stub_env, tmp_path):
    env, marker = stub_env
    done = run_runner(["--work-dir", str(tmp_path / "work"), "--out", str(tmp_path / "out")], env, tmp_path)
    assert done.returncode == 2
    assert "Traceback" not in done.stderr + done.stdout
    assert "--yes" in done.stderr
    assert not marker.exists()


def test_sc7_work_dir_inside_the_main_checkout_is_refused(ra, stub_env, tmp_path):
    env, marker = stub_env
    inside = ra.main_checkout() / "kit-arms-work-should-not-exist"
    done = run_runner(["--dry-run", "--work-dir", str(inside), "--out", str(tmp_path / "out")], env, tmp_path)
    assert done.returncode == 2
    assert "Traceback" not in done.stderr
    assert not inside.exists()
    assert not marker.exists()


def test_isolation_breach_is_detected(ra, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    before = ra.porcelain(repo)
    (repo / "escaped.txt").write_text("written outside the copy")
    assert ra.porcelain(repo) != before


# ---------------------------------------------------------------- SC 8: arm shapes

@pytest.fixture(scope="module")
def built_arms(ra, tmp_path_factory):
    base = tmp_path_factory.mktemp("arms")
    return {arm: ra.build_arm(arm, base / arm) for arm in ra.ARMS}


def hook_commands(copy):
    settings = json.loads((copy / ".claude" / "settings.json").read_text())
    return [h["command"] for entries in settings.get("hooks", {}).values() for e in entries for h in e["hooks"]]


def test_sc8_bare_arm_has_no_kit(built_arms):
    bare = built_arms["bare"]
    for name in ("AGENTS.md", "CLAUDE.md", ".claude"):
        assert not (bare / name).exists(), name
    assert (bare / "src" / "tally" / "cli.py").is_file()


def test_sc8_full_arm_is_the_installer_output(ra, built_arms):
    full = built_arms["full"]
    kit_agents = subprocess.run(["git", "-C", str(ra.main_checkout()), "show", "HEAD:AGENTS.md"],
                                capture_output=True, text=True, check=True).stdout
    assert (full / "AGENTS.md").read_text() == kit_agents
    assert (full / ".claude" / "harness-lock.json").is_file()
    assert len(hook_commands(full)) == 9


def test_sc8_minimal_arm_short_doctrine_two_hooks(ra, built_arms):
    minimal = built_arms["minimal"]
    agents = (minimal / "AGENTS.md").read_text()
    assert agents == (ra.EXP / "arms" / "minimal-AGENTS.md").read_text()
    assert len(agents.splitlines()) <= 60
    commands = hook_commands(minimal)
    assert len(commands) == 2
    assert any("pre_bash_block_unsafe_merge.py" in c for c in commands)
    assert any("pre_tool_sensitive_path.py" in c for c in commands)


@pytest.mark.parametrize("arm", ["bare", "minimal", "full"])
def test_every_arm_is_committed_holds_the_data_and_no_graders(built_arms, arm):
    copy = built_arms[arm]
    assert subprocess.run(["git", "-C", str(copy), "status", "--porcelain"], capture_output=True,
                          text=True, check=True).stdout == ""
    assert (copy / "data" / "expenses.csv").is_file()
    assert not any(p.name in ("oracles", "run_arms.py", "RULE.md") for p in copy.rglob("*"))
