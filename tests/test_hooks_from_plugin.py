"""T232 — hooks copied to a plugin cache read and write the user's project, never their own folder.

Every test copies `.claude/hooks` to a temp folder (a fake plugin cache) and runs the hook as a
subprocess, with `CLAUDE_PROJECT_DIR` naming a temp project, as the harness does. The live hook
matches text in Bash commands, so the sample push commands live in this file and not in a shell line.

`__pycache__` is left out of every "nothing under the cache" check: the Python interpreter writes it
beside any imported module, and it is a cache of the code, not hook state (D3).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOKS_SRC = REPO / ".claude" / "hooks"

ELEVEN_HOOKS = (
    "post_agent_move_to_review.py", "post_bash_memory_update.py", "post_tool_trace.py",
    "post_write_register_task.py", "pre_agent_step_limit.py", "pre_agent_validate_guide.py",
    "pre_bash_block_unsafe_merge.py", "pre_tool_sensitive_path.py", "stop_auto_mode_check.py",
    "stop_auto_verify.py", "stop_review_reminder.py",
)
# The hooks that computed ROOT from __file__ before T232.
EIGHT_HOOKS = (
    "post_write_register_task.py", "post_tool_trace.py", "pre_agent_step_limit.py",
    "stop_review_reminder.py", "stop_auto_mode_check.py", "pre_agent_validate_guide.py",
    "stop_auto_verify.py", "pre_bash_block_unsafe_merge.py",
)

PUSH = "git push origin main"
BOARD = ("# Board\n\n### Todo\n\n### In Progress\n"
         "- [~] **T900** — open task | backend-developer | C1 | Risk: Low | P1\n\n"
         "### Ready for Review\n\n### Done\n")
SPAWN_NO_GUIDE = {"tool_name": "Agent", "session_id": "s1",
                  "tool_input": {"prompt": "Task ID: T901\nGuide: tasks/TASK_GUIDE_T901.md"}}
BASH_PUSH = {"tool_name": "Bash", "tool_input": {"command": PUSH}, "session_id": "s1"}
TASKED_READ = {"tool_name": "Read", "session_id": "s1",
               "tool_input": {"file_path": "tasks/TASK_GUIDE_T900.md"}}

# For each hook, an event that would make it speak or write in a kit project.
EVENTS = {
    "post_agent_move_to_review.py": {"tool_name": "Agent", "session_id": "s1",
                                     "tool_input": {"prompt": "Task ID: T900"}},
    "post_bash_memory_update.py": BASH_PUSH,
    "post_tool_trace.py": TASKED_READ,
    "post_write_register_task.py": {"tool_name": "Write",
                                    "tool_input": {"file_path": "tasks/TASK_GUIDE_T900.md"}},
    "pre_agent_step_limit.py": TASKED_READ,
    "pre_agent_validate_guide.py": SPAWN_NO_GUIDE,
    "pre_bash_block_unsafe_merge.py": BASH_PUSH,
    "pre_tool_sensitive_path.py": {"tool_name": "Write", "tool_input": {"file_path": ".env"}},
    "stop_auto_mode_check.py": {"session_id": "s1", "stop_hook_active": False},
    "stop_auto_verify.py": {"session_id": "s1"},
    "stop_review_reminder.py": {"session_id": "s1"},
}


def copy_hooks(dest):
    shutil.copytree(HOOKS_SRC, dest,
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    return dest


@pytest.fixture
def cache(tmp_path):
    return copy_hooks(tmp_path / "plugin-cache" / "easy-kit" / "1.0.0" / "hooks")


@pytest.fixture
def kit(tmp_path):
    project = tmp_path / "kit-project"
    (project / "tasks").mkdir(parents=True)
    (project / "PROJECT_KANBAN.md").write_text(BOARD, encoding="utf-8")
    return project


@pytest.fixture
def plain(tmp_path):
    project = tmp_path / "plain-project"
    project.mkdir()
    return project


def clean_env(tmp_root, **extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_PROJECT_DIR", "CLAUDE_ACTIVE_TASK", "CLAUDE_CODE_SESSION_ID",
                        "CLAUDE_AUTO_VERIFY_RUN", "CLAUDE_AUTO_VERIFY")}
    env["CLAUDE_TRACE_ANCHOR_DIR"] = str(Path(tmp_root) / "anchors")
    env.update(extra)
    return env


def run_hook(hooks_dir, hook, stdin, project=None, args=(), **env):
    raw = stdin if isinstance(stdin, str) else json.dumps(stdin)
    if project is not None:
        env.setdefault("CLAUDE_PROJECT_DIR", str(project))
    return subprocess.run([sys.executable, str(Path(hooks_dir) / hook), *args], input=raw,
                          capture_output=True, text=True, timeout=30,
                          cwd=str(project or hooks_dir), env=clean_env(Path(hooks_dir).parent, **env))


def files_under(root):
    return sorted(str(p.relative_to(root)) for p in Path(root).rglob("*")
                  if "__pycache__" not in p.parts and not p.is_dir())


def decision(result):
    """`block`, `ask`, or None when the hook printed no decision."""
    if not result.stdout.strip():
        return None
    data = json.loads(result.stdout)
    return data.get("decision") or data.get("hookSpecificOutput", {}).get("permissionDecision")


def break_module(hooks_dir, module):
    (Path(hooks_dir) / "lib" / f"{module}.py").write_text(
        'raise ImportError("broken for T232 test")\n', encoding="utf-8")


# --- AC 1, AC 2 — the hooks act on the project from a plugin cache ------------------------------

def test_merge_gate_blocks_a_push_from_the_plugin_cache(cache, kit):
    result = run_hook(cache, "pre_bash_block_unsafe_merge.py", BASH_PUSH, kit)
    assert result.returncode == 0
    assert decision(result) == "block"
    assert "T900" in result.stdout


def test_spawn_gate_blocks_a_task_with_no_guide_from_the_plugin_cache(cache, kit):
    result = run_hook(cache, "pre_agent_validate_guide.py", SPAWN_NO_GUIDE, kit)
    assert decision(result) == "block"
    assert "T901" in result.stdout


def test_trace_lands_in_the_project_and_nothing_lands_in_the_cache(cache, kit):
    before = files_under(cache)
    result = run_hook(cache, "post_tool_trace.py", TASKED_READ, kit)
    assert result.returncode == 0
    assert (kit / "memory" / "event-trace" / "T900.jsonl").is_file()
    assert files_under(cache) == before


def test_step_counter_lands_in_the_project_and_nothing_lands_in_the_cache(cache, kit):
    before = files_under(cache)
    run_hook(cache, "pre_agent_step_limit.py", TASKED_READ, kit)
    counters = list((kit / ".claude" / "hooks" / ".state").glob("step_count_*T900.txt"))
    assert len(counters) == 1
    assert files_under(cache) == before


@pytest.mark.parametrize("hook", ELEVEN_HOOKS)
def test_no_hook_writes_under_its_own_code_in_a_kit_project(cache, kit, hook):
    before = files_under(cache)
    run_hook(cache, hook, EVENTS[hook], kit)
    assert files_under(cache) == before


def test_register_hook_writes_the_project_board(cache, kit):
    guide = kit / "tasks" / "TASK_GUIDE_T905.md"
    guide.write_text("# TASK_GUIDE — T905: new\n", encoding="utf-8")
    event = {"tool_name": "Write", "tool_input": {"file_path": str(guide)}}
    run_hook(cache, "post_write_register_task.py", event, kit)
    assert "**T905**" in (kit / "PROJECT_KANBAN.md").read_text(encoding="utf-8")


def test_review_reminder_reads_the_project_board(cache, kit):
    (kit / "PROJECT_KANBAN.md").write_text(BOARD.replace(
        "### Ready for Review\n", "### Ready for Review\n- [ ] **T902** — waiting\n"),
        encoding="utf-8")
    result = run_hook(cache, "stop_review_reminder.py", {}, kit)
    assert "T902" in result.stderr


# --- AC 3 — silent outside a kit project ----------------------------------------------------------

@pytest.mark.parametrize("hook", ELEVEN_HOOKS)
def test_hook_is_silent_and_writes_nothing_outside_a_kit_project(cache, plain, hook):
    before = files_under(cache)
    result = run_hook(cache, hook, EVENTS[hook], plain)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert files_under(plain) == []
    assert files_under(cache) == before


@pytest.mark.parametrize("hook", ELEVEN_HOOKS)
def test_bad_input_stays_silent_outside_a_kit_project(cache, plain, hook):
    result = run_hook(cache, hook, "not json", plain)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


@pytest.mark.parametrize("hook", ELEVEN_HOOKS)
def test_a_broken_gate_module_stays_silent_outside_a_kit_project(cache, plain, hook):
    break_module(cache, "guide_sections")
    break_module(cache, "auto_mode")
    result = run_hook(cache, hook, EVENTS[hook], plain)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_a_broken_helper_fails_closed_outside_a_kit_project_too(cache, plain):
    """Known limit, listed in the review file: with the helper itself broken no hook can tell a kit
    project from any other, so the gates keep their fail-closed result."""
    break_module(cache, "project_root")
    assert decision(run_hook(cache, "pre_bash_block_unsafe_merge.py", BASH_PUSH, plain)) == "block"


def test_missing_project_dir_stays_silent_from_the_plugin_cache(cache, tmp_path):
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path / "gone")}
    result = run_hook(cache, "pre_bash_block_unsafe_merge.py", BASH_PUSH, **env)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_start_entry_says_why_when_run_outside_a_kit_project(cache, plain):
    """`--start` is a command, not a hook, and exit 0 means a run started."""
    result = run_hook(cache, "stop_auto_verify.py", "", plain, args=("--start", "T900"))
    assert result.returncode == 1
    assert "nothing started" in result.stdout


# --- D2 — a kit marker, and in-repo hooks keep today's behaviour -----------------------------------

def test_board_json_alone_marks_a_kit_project(cache, plain):
    (plain / ".claude").mkdir()
    (plain / ".claude" / "board.json").write_text("{}", encoding="utf-8")
    (plain / "tasks").mkdir()
    result = run_hook(cache, "pre_agent_validate_guide.py", SPAWN_NO_GUIDE, plain)
    assert decision(result) == "block"


def in_repo_copy(tmp_path):
    root = tmp_path / "in-repo"
    copy_hooks(root / ".claude" / "hooks")
    return root


@pytest.mark.parametrize("env_set", [False, True], ids=["env-unset", "env-set"])
def test_in_repo_hook_is_not_silenced_when_the_project_has_no_kit_files(tmp_path, env_set):
    """Sensitive-path check with no pattern file: today it asks, so it must still ask."""
    root = in_repo_copy(tmp_path)
    hooks = root / ".claude" / "hooks"
    event = EVENTS["pre_tool_sensitive_path.py"]
    env = {"CLAUDE_PROJECT_DIR": str(root)} if env_set else {}
    assert decision(run_hook(hooks, "pre_tool_sensitive_path.py", event, **env)) == "ask"


def test_in_repo_merge_gate_reads_its_own_root_with_the_env_unset(tmp_path):
    root = in_repo_copy(tmp_path)
    (root / "PROJECT_KANBAN.md").write_text(BOARD, encoding="utf-8")
    result = run_hook(root / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH)
    assert decision(result) == "block"


def test_in_repo_merge_gate_falls_back_when_the_env_path_does_not_exist(tmp_path):
    root = in_repo_copy(tmp_path)
    (root / "PROJECT_KANBAN.md").write_text(BOARD, encoding="utf-8")
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path / "gone")}
    result = run_hook(root / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, **env)
    assert decision(result) == "block"


def helper_answer(hooks_dir, code, **env):
    script = f"import sys; sys.path.insert(0, {str(Path(hooks_dir) / 'lib')!r})\n" \
             f"import project_root as pr\nprint({code})"
    done = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          env=clean_env(Path(hooks_dir).parent, **env))
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def test_helper_prefers_the_env_directory(cache, kit):
    assert helper_answer(cache, "pr.project_root()", CLAUDE_PROJECT_DIR=str(kit)) == str(kit)


@pytest.mark.parametrize("value", ["", "   ", "/no/such/dir/t232"])
def test_helper_falls_back_to_the_code_path(tmp_path, value):
    root = in_repo_copy(tmp_path)
    hooks = root / ".claude" / "hooks"
    assert helper_answer(hooks, "pr.project_root()", CLAUDE_PROJECT_DIR=value) == str(root)


def test_helper_kit_test(cache, kit, plain):
    assert helper_answer(cache, f"pr.is_kit_project({str(kit)!r})") == "True"
    assert helper_answer(cache, f"pr.is_kit_project({str(plain)!r})") == "False"


# --- Edge cases of the guide ----------------------------------------------------------------------

def test_a_call_from_a_linked_worktree_keeps_state_in_the_project(cache, kit, tmp_path):
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    event = dict(TASKED_READ, cwd=str(worktree))
    run_hook(cache, "pre_agent_step_limit.py", event, kit)
    assert list((kit / ".claude" / "hooks" / ".state").glob("step_count_*T900.txt"))
    assert files_under(worktree) == []


def test_active_task_state_is_read_from_the_project(cache, kit):
    state = kit / ".claude" / "hooks" / ".state" / "active_task.d"
    state.mkdir(parents=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (state / "s1").write_text(f"T900\n{stamp}\n", encoding="utf-8")
    run_hook(cache, "post_tool_trace.py", {"tool_name": "Bash", "session_id": "s1",
                                           "tool_input": {"command": "true"}}, kit)
    assert (kit / "memory" / "event-trace" / "T900.jsonl").is_file()


def git(project, *args):
    subprocess.run(["git", "-C", str(project), "-c", "user.name=t", "-c", "user.email=t@t",
                    *args], check=True, capture_output=True, text=True)


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0o755)]")
def test_detached_verify_run_from_the_cache_keeps_finding_the_project(cache, kit, tmp_path):
    """`stop_auto_verify.py:354` strips CLAUDE_PROJECT_DIR for the headless `claude` only: the
    detached `--run` process keeps it, so it writes the result into the project."""
    (kit / "PROJECT_KANBAN.md").write_text(BOARD.replace(
        "### Ready for Review\n",
        "### Ready for Review\n- [ ] **T902** — waiting | Started 2026-11-02: branch `main`\n"),
        encoding="utf-8")
    review = kit / "tasks" / "TASK_REVIEW_T902.md"
    review.write_text("# TASK_REVIEW\n\n## Evidence\n\n| Check | Result | Notes |\n|---|---|---|\n"
                      "| verify | ☐ pass / ☐ fail / ☐ N/A | [x] |\n", encoding="utf-8")
    git(kit, "init", "-q", "-b", "main")
    git(kit, "add", ".")
    git(kit, "commit", "-qm", "seed")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    seen = tmp_path / "claude-env.json"
    stub = bin_dir / "claude"
    stub.write_text(
        f"#!{sys.executable}\nimport json, os\n"
        f"json.dump({{'dir': os.environ.get('CLAUDE_PROJECT_DIR'), 'cwd': os.getcwd()}}, "
        f"open({str(seen)!r}, 'w'))\n"
        "print(json.dumps({'subtype': 'success', 'is_error': False, 'session_id': 's9', "
        "'result': '**Verdict:** PASS'}))\n", encoding="utf-8")
    stub.chmod(0o755)
    before = files_under(cache)
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    run_hook(cache, "stop_auto_verify.py", {}, kit, **env)
    deadline = time.time() + 20
    while time.time() < deadline and "auto-run by hook" not in review.read_text(encoding="utf-8"):
        time.sleep(0.1)
    assert "auto-run by hook" in review.read_text(encoding="utf-8")
    called = json.loads(seen.read_text(encoding="utf-8"))
    assert called["dir"] is None
    assert os.path.realpath(called["cwd"]) == os.path.realpath(str(kit))
    assert list((kit / ".claude" / "verify-runs").glob("T902-*.log"))
    assert files_under(cache) == before


# --- AC 4 — D4: bad input and a broken import, pinned per hook -------------------------------------

AUTO_REVIEW = "# TASK_REVIEW\n\n## Auto decisions\n\nMode: auto\n1. picked it — RULE: `AGENTS.md`\n"


def auto_task(project):
    (project / "tasks" / "TASK_REVIEW_T900.md").write_text(AUTO_REVIEW, encoding="utf-8")


def test_d4_merge_gate_blocks_on_bad_stdin(cache, kit):
    assert decision(run_hook(cache, "pre_bash_block_unsafe_merge.py", "not json", kit)) == "block"


@pytest.mark.parametrize("event", [
    [], {"tool_name": "Bash", "tool_input": "text"}, {"tool_name": "Bash", "tool_input": {"command": 1}},
], ids=["not-object", "input-not-object", "command-not-string"])
def test_d4_merge_gate_blocks_on_an_unreadable_payload(cache, kit, event):
    assert decision(run_hook(cache, "pre_bash_block_unsafe_merge.py", event, kit)) == "block"


@pytest.mark.parametrize("module", ["project_root", "guide_sections"])
def test_d4_merge_gate_blocks_on_a_broken_import(cache, kit, module):
    break_module(cache, module)
    assert decision(run_hook(cache, "pre_bash_block_unsafe_merge.py", BASH_PUSH, kit)) == "block"


def test_d4_spawn_gate_blocks_on_bad_stdin(cache, kit):
    assert decision(run_hook(cache, "pre_agent_validate_guide.py", "not json", kit)) == "block"


@pytest.mark.parametrize("event", [
    [], {"tool_name": "Agent", "tool_input": "text"}, {"tool_name": "Agent", "tool_input": {"prompt": 1}},
], ids=["not-object", "input-not-object", "prompt-not-string"])
def test_d4_spawn_gate_blocks_on_an_unreadable_payload(cache, kit, event):
    result = run_hook(cache, "pre_agent_validate_guide.py", event, kit)
    assert (result.returncode, decision(result)) == (0, "block")


def test_d4_spawn_gate_blocks_when_the_helper_is_broken(cache, kit):
    break_module(cache, "project_root")
    assert decision(run_hook(cache, "pre_agent_validate_guide.py", SPAWN_NO_GUIDE, kit)) == "block"


def test_d4_spawn_gate_keeps_the_missing_guide_block_with_a_broken_guide_reader(cache, kit):
    break_module(cache, "guide_sections")
    assert decision(run_hook(cache, "pre_agent_validate_guide.py", SPAWN_NO_GUIDE, kit)) == "block"


def test_d4_spawn_gate_keeps_its_documented_fail_open_on_the_guide_check(cache, kit):
    """Kept: the hook's docstring says a crash in the completeness check fails open."""
    break_module(cache, "guide_sections")
    (kit / "tasks" / "TASK_GUIDE_T901.md").write_text("# an incomplete guide\n", encoding="utf-8")
    result = run_hook(cache, "pre_agent_validate_guide.py", SPAWN_NO_GUIDE, kit)
    assert decision(result) is None


@pytest.mark.parametrize("stdin", ["not json", {"tool_name": "Write", "tool_input": "text"}],
                         ids=["not-json", "input-not-object"])
def test_d4_sensitive_path_check_asks_on_bad_stdin(cache, kit, stdin):
    assert decision(run_hook(cache, "pre_tool_sensitive_path.py", stdin, kit)) == "ask"


@pytest.mark.parametrize("module", ["project_root", "shell_data"])
def test_d4_sensitive_path_check_asks_on_a_broken_import(cache, kit, module):
    break_module(cache, module)
    event = EVENTS["pre_tool_sensitive_path.py"]
    assert decision(run_hook(cache, "pre_tool_sensitive_path.py", event, kit)) == "ask"


def test_d4_step_limit_keeps_its_documented_fail_open_on_bad_stdin(cache, kit):
    """Kept: the docstring says no session may be left unable to act, and an unattributed call is
    counted against nothing."""
    result = run_hook(cache, "pre_agent_step_limit.py", "not json", kit)
    assert (result.returncode, result.stdout) == (0, "")


@pytest.mark.parametrize("module", ["project_root", "task_context"])
def test_d4_step_limit_keeps_its_documented_fail_open_on_a_broken_import(cache, kit, module):
    break_module(cache, module)
    result = run_hook(cache, "pre_agent_step_limit.py", TASKED_READ, kit)
    assert (result.returncode, result.stdout) == (0, "")


def test_d4_auto_check_warns_on_bad_stdin_with_nothing_to_check(cache, kit):
    result = run_hook(cache, "stop_auto_mode_check.py", "not json", kit)
    assert (result.returncode, decision(result)) == (0, None)
    assert "unreadable" in result.stderr


def test_d4_auto_check_blocks_once_on_bad_stdin_with_a_failing_task(cache, kit):
    auto_task(kit)
    first = run_hook(cache, "stop_auto_mode_check.py", "not json", kit)
    assert decision(first) == "block"
    report = (kit / "tasks" / "TASK_REVIEW_T900.md").read_text(encoding="utf-8")
    assert "Paused: auto-mode check failed — " in report
    second = run_hook(cache, "stop_auto_mode_check.py", "not json", kit)
    assert (second.returncode, decision(second)) == (0, None)


@pytest.mark.parametrize("module", ["project_root", "auto_mode"])
@pytest.mark.parametrize("event", [{"stop_hook_active": False}, {}], ids=["flag-false", "no-flag"])
def test_d4_auto_check_blocks_the_first_stop_on_a_broken_import(cache, kit, module, event):
    break_module(cache, module)
    result = run_hook(cache, "stop_auto_mode_check.py", event, kit)
    assert (result.returncode, decision(result)) == (0, "block")


@pytest.mark.parametrize("stdin", [{"stop_hook_active": True}, "not json"],
                         ids=["second-fire", "bad-stdin"])
def test_d4_auto_check_never_loops_on_a_broken_import(cache, kit, stdin):
    break_module(cache, "auto_mode")
    result = run_hook(cache, "stop_auto_mode_check.py", stdin, kit)
    assert (result.returncode, decision(result)) == (0, None)
    assert "unavailable" in result.stderr


def test_d4_auto_check_stays_out_of_the_headless_verify_run_on_a_broken_import(cache, kit):
    break_module(cache, "auto_mode")
    result = run_hook(cache, "stop_auto_mode_check.py", {}, kit, CLAUDE_AUTO_VERIFY_RUN="1")
    assert (result.returncode, result.stdout) == (0, "")


# --- AC 6 — no data path computed from __file__ ----------------------------------------------------

@pytest.mark.parametrize("hook", EIGHT_HOOKS)
def test_no_data_path_comes_from_file(hook):
    source = (HOOKS_SRC / hook).read_text(encoding="utf-8")
    assert not re.search(r"^\s*ROOT\s*=.*(__file__|HOOKS_DIR|dirname)", source, re.M)
    for line in source.splitlines():
        if "__file__" in line and not line.lstrip().startswith("#"):
            allowed = (line.startswith("HOOKS_DIR = ") or "sys.path.insert" in line
                       or "subprocess.Popen" in line)
            assert allowed, line
    assert "from project_root import" in source


@pytest.mark.parametrize("path", ["lib/task_context.py", "lib/board/config.py"])
def test_library_roots_come_from_the_helper(path):
    source = (HOOKS_SRC / path).read_text(encoding="utf-8")
    assert "project_root" in source
    assert "_FILE_ROOT" not in source


# --- T233 round 2 — the sensitive-path list ships with the plugin ----------------------------------
# A kit project made by a plugin holds no `.claude/sensitive-paths.txt`. The hook then reads the
# plugin's own copy, one level above its hooks folder (`<plugin>/.claude/sensitive-paths.txt`).

HARMLESS_BASH = {"tool_name": "Bash", "tool_input": {"command": "ls -la"}, "session_id": "s1"}
SENSITIVE_WRITE = EVENTS["pre_tool_sensitive_path.py"]
SENSITIVE_HOOK = "pre_tool_sensitive_path.py"
PLUGIN_LIST = "# plugin copy\n.env\n.env.*\n"


@pytest.fixture
def plugin_list(cache):
    path = cache.parent / "sensitive-paths.txt"
    path.write_text(PLUGIN_LIST, encoding="utf-8")
    return path


def test_plugin_list_lets_a_harmless_bash_call_through(cache, kit, plugin_list):
    result = run_hook(cache, SENSITIVE_HOOK, HARMLESS_BASH, kit)
    assert (result.returncode, result.stdout) == (0, "")


def test_plugin_list_still_asks_for_a_sensitive_path(cache, kit, plugin_list):
    assert decision(run_hook(cache, SENSITIVE_HOOK, SENSITIVE_WRITE, kit)) == "ask"


def test_project_list_wins_over_the_plugin_list(cache, kit, plugin_list):
    (kit / ".claude").mkdir()
    (kit / ".claude" / "sensitive-paths.txt").write_text("secret.txt\n", encoding="utf-8")
    assert run_hook(cache, SENSITIVE_HOOK, SENSITIVE_WRITE, kit).stdout == ""
    event = {"tool_name": "Write", "tool_input": {"file_path": "secret.txt"}}
    assert decision(run_hook(cache, SENSITIVE_HOOK, event, kit)) == "ask"


def test_no_list_anywhere_still_asks(cache, kit):
    assert decision(run_hook(cache, SENSITIVE_HOOK, HARMLESS_BASH, kit)) == "ask"


def test_unreadable_plugin_list_still_asks(cache, kit, plugin_list):
    plugin_list.unlink()
    plugin_list.mkdir()  # exists, but cannot be read as a file
    assert decision(run_hook(cache, SENSITIVE_HOOK, HARMLESS_BASH, kit)) == "ask"


def test_unreadable_project_list_asks_and_does_not_fall_back(cache, kit, plugin_list):
    (kit / ".claude" / "sensitive-paths.txt").mkdir(parents=True)
    assert decision(run_hook(cache, SENSITIVE_HOOK, HARMLESS_BASH, kit)) == "ask"
