"""T235 — `/easy-kit:init` sets up a project, and plugin hooks stand down beside in-repo hooks.

A session fixture builds a plugin-shaped copy of the kit (`.claude-plugin/plugin.json` at its root,
the kit's own `PROJECT_KANBAN.md` included, as a real plugin cache holds it). Each test makes a temp
git repo and runs `scripts/plugin_init.py` from that copy with the repo as the cwd, as the
`commands/init.md` step does. Hooks run as subprocesses with JSON on stdin, as the harness runs them.
The sample push command lives in this file, not in a shell line, because the live gate reads Bash text.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

ELEVEN_HOOKS = (
    "post_agent_move_to_review.py", "post_bash_memory_update.py", "post_tool_trace.py",
    "post_write_register_task.py", "pre_agent_step_limit.py", "pre_agent_validate_guide.py",
    "pre_bash_block_unsafe_merge.py", "pre_tool_sensitive_path.py", "stop_auto_mode_check.py",
    "stop_auto_verify.py", "stop_review_reminder.py",
)
PUSH = "git push origin main"
BASH_PUSH = {"tool_name": "Bash", "tool_input": {"command": PUSH}, "session_id": "s1"}
OPEN_TASK = "- [~] **T900** — open task | backend-developer | C1 | Risk: Low | P1\n"
TASKED_READ = {"tool_name": "Read", "session_id": "s1",
               "tool_input": {"file_path": "tasks/TASK_GUIDE_T900.md"}}
EVENTS = {
    "post_agent_move_to_review.py": {"tool_name": "Agent", "session_id": "s1",
                                     "tool_input": {"prompt": "Task ID: T900"}},
    "post_bash_memory_update.py": BASH_PUSH,
    "post_tool_trace.py": TASKED_READ,
    "post_write_register_task.py": {"tool_name": "Write",
                                    "tool_input": {"file_path": "tasks/TASK_GUIDE_T900.md"}},
    "pre_agent_step_limit.py": TASKED_READ,
    "pre_agent_validate_guide.py": {"tool_name": "Agent", "session_id": "s1",
                                    "tool_input": {"prompt": "Task ID: T901\nGuide: tasks/TASK_GUIDE_T901.md"}},
    "pre_bash_block_unsafe_merge.py": BASH_PUSH,
    "pre_tool_sensitive_path.py": {"tool_name": "Write", "tool_input": {"file_path": ".env"}},
    "stop_auto_mode_check.py": {"session_id": "s1", "stop_hook_active": False},
    "stop_auto_verify.py": {"session_id": "s1"},
    "stop_review_reminder.py": {"session_id": "s1"},
}
# D2 + D7: every path init must create in an empty repo.
D2_FILES = ("CLAUDE.md", "AGENTS.md", "PROJECT_KANBAN.md", "memory/MEMORY.md", "memory/decisions.md",
            "memory/glossary.md", "memory/learnings.md", "memory/learning-records/.gitkeep")
D7_TREES = ("templates", "docs/claude-md", "agents")
D7_SCRIPTS = (".claude/hooks/stop_auto_verify.py", ".claude/hooks/lib/project_root.py",
              ".claude/hooks/lib/board/moments.py", "scripts/board_sync.py", "scripts/pull_moment.py",
              "skills/craft-spawn-prompt/scripts/memory_slice.py")
PLUGIN_PARTS = (".claude-plugin", ".claude/hooks", ".claude/sensitive-paths.txt", "scripts", "skills",
                "templates", "docs/claude-md", "agents", "commands", "hooks", "AGENTS.md", "CLAUDE.md",
                "PROJECT_KANBAN.md")


# --- fixtures and helpers -------------------------------------------------------------------------

@pytest.fixture(scope="session")
def plugin(tmp_path_factory):
    """A plugin cache: the parts of the kit the plugin carries, `.claude-plugin/` at the root."""
    root = tmp_path_factory.mktemp("cache") / "easy-kit" / "2.2.0"
    ignore = shutil.ignore_patterns("tests", "__pycache__", ".state")
    for part in PLUGIN_PARTS:
        src, dst = REPO / part, root / part
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, ignore=ignore) if src.is_dir() else shutil.copy2(src, dst)
    return root


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT", "CLAUDE_ACTIVE_TASK",
                        "CLAUDE_CODE_SESSION_ID",
                        "CLAUDE_AUTO_VERIFY_RUN", "CLAUDE_AUTO_VERIFY", "PYTHONDONTWRITEBYTECODE")}
    env.update(extra)
    return env


def git_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


@pytest.fixture
def repo(tmp_path):
    return git_repo(tmp_path / "project")


def run_init(plugin_root, cwd, *args):
    return subprocess.run([sys.executable, str(plugin_root / "scripts" / "plugin_init.py"), *args],
                          capture_output=True, text=True, timeout=60, cwd=str(cwd),
                          env=clean_env(CLAUDE_TRACE_ANCHOR_DIR=str(Path(cwd).parent / "anchors")))


def run_hook(hooks_dir, hook, stdin, project, cwd=None, args=(), set_env=True, plugin_root=None):
    env = clean_env(CLAUDE_TRACE_ANCHOR_DIR=str(Path(project).parent / "anchors"))
    if set_env:
        env["CLAUDE_PROJECT_DIR"] = str(project)
    if plugin_root is not None:  # the harness exports it to a plugin hook (checked live)
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    raw = stdin if isinstance(stdin, str) else json.dumps(stdin)
    return subprocess.run([sys.executable, str(Path(hooks_dir) / hook), *args], input=raw,
                          capture_output=True, text=True, timeout=30, cwd=str(cwd or project), env=env)


def decision(result):
    if not result.stdout.strip():
        return None
    data = json.loads(result.stdout)
    return data.get("decision") or data.get("hookSpecificOutput", {}).get("permissionDecision")


def snapshot(root):
    """Every file under root (no `.git`, no `__pycache__`) with its bytes and mtime."""
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in sorted(Path(root).rglob("*"))
            if p.is_file() and ".git" not in p.relative_to(root).parts and "__pycache__" not in p.parts}


def with_open_task(project):
    board = project / "PROJECT_KANBAN.md"
    text = board.read_text(encoding="utf-8")
    board.write_text(text.replace("### In Progress\n", "### In Progress\n" + OPEN_TASK, 1), encoding="utf-8")


def wire_in_repo_hooks(project):
    """In-repo mode: the kit's hooks copied to `<project>/.claude/hooks` and wired by the kit's settings."""
    shutil.copytree(REPO / ".claude" / "hooks", project / ".claude" / "hooks", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    shutil.copy2(REPO / ".claude" / "settings.json", project / ".claude" / "settings.json")


def is_kit_project(plugin_root, project):
    code = (f"import sys; sys.path.insert(0, {str(plugin_root / '.claude' / 'hooks' / 'lib')!r})\n"
            f"import project_root as pr; print(pr.is_kit_project({str(project)!r}))")
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          env=clean_env()).stdout.strip() == "True"


# --- AC 1 — an empty repo gets every D2 file and becomes a kit project ----------------------------

def test_ac1_init_creates_every_d2_file_and_the_project_counts_as_a_kit_project(plugin, repo):
    assert not is_kit_project(plugin, repo)
    result = run_init(plugin, repo)
    assert result.returncode == 0, result.stderr
    for rel in D2_FILES:
        assert (repo / rel).is_file(), rel
        assert f"+ created {rel}" in result.stdout.replace("\\", "/"), rel
    assert (repo / "tasks").is_dir()
    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    assert (repo / "AGENTS.md").read_bytes() == (REPO / "AGENTS.md").read_bytes()
    assert is_kit_project(plugin, repo)


def test_ac1_the_new_board_has_its_sections_and_no_task_rows(plugin, repo):
    """The template's sample rows include an In Progress T002: copied as-is it would block every push."""
    run_init(plugin, repo)
    board = (repo / "PROJECT_KANBAN.md").read_text(encoding="utf-8")
    for section in ("### Todo", "### In Progress", "### Ready for Review", "### Done", "## Blocked"):
        assert section in board
    assert "**T0" not in board and "T[NNN]" not in board and "[YYYY-MM-DD]" not in board


def test_ac1_an_initialized_project_is_gated_by_the_plugin_hook(plugin, repo):
    """Success Criterion 1 in unit form: a push passes on the empty board, an open task blocks it."""
    run_init(plugin, repo)
    hooks = plugin / ".claude" / "hooks"
    assert decision(run_hook(hooks, "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)) is None
    with_open_task(repo)
    result = run_hook(hooks, "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    assert decision(result) == "block" and "T900" in result.stdout


def test_d7_init_copies_templates_docs_and_agents(plugin, repo):
    run_init(plugin, repo)
    for tree in D7_TREES:
        kit = sorted(p.relative_to(plugin / tree) for p in (plugin / tree).rglob("*") if p.is_file())
        assert kit, tree
        for rel in kit:
            assert (repo / tree / rel).read_bytes() == (plugin / tree / rel).read_bytes(), f"{tree}/{rel}"


def test_d7a_repo_relative_commands_resolve_in_the_project(plugin, repo):
    """The doctrine's commands, run as written, from the project root, with no kit anywhere near."""
    run_init(plugin, repo)
    for rel in D7_SCRIPTS:
        assert (repo / rel).is_file(), rel
    (repo / "tasks" / "TASK_GUIDE_T900.md").write_text("# TASK_GUIDE — T900\n", encoding="utf-8")
    env = clean_env()

    def run(*cmd):
        return subprocess.run([sys.executable, *cmd], capture_output=True, text=True, timeout=30,
                              cwd=str(repo), env=env)

    review = run("scripts/pull_moment.py", "review", "T900")
    assert (review.returncode, review.stdout, review.stderr) == (0, "", "")
    status = run("scripts/board_sync.py", "status")
    assert status.returncode == 0 and "board mode is local" in status.stderr
    started = run(".claude/hooks/stop_auto_verify.py", "--start", "T999")
    assert started.returncode == 1 and "T999" in started.stdout and "Traceback" not in started.stderr
    sliced = run("skills/craft-spawn-prompt/scripts/memory_slice.py", "tasks/TASK_GUIDE_T900.md")
    assert sliced.returncode == 0, sliced.stderr


def test_d7_report_says_copies_go_stale_and_d5_names_teammates(plugin, repo):
    out = run_init(plugin, repo).stdout
    assert "stale" in out and "/easy-kit:init" in out
    assert "teammate" in out and "plugin" in out


# --- AC 2 — add only; a second run changes no byte ------------------------------------------------

def test_ac2_a_second_run_changes_no_byte(plugin, repo):
    run_init(plugin, repo)
    before = snapshot(repo)
    again = run_init(plugin, repo)
    assert again.returncode == 0, again.stderr
    assert snapshot(repo) == before
    assert "+ created" not in again.stdout
    assert "nothing changed" in again.stdout


def test_ac2_a_pre_existing_claude_md_is_unchanged_and_named(plugin, repo):
    (repo / "CLAUDE.md").write_text("# my own rules\n", encoding="utf-8")
    result = run_init(plugin, repo)
    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == "# my own rules\n"
    assert "= kept CLAUDE.md" in result.stdout
    assert "@AGENTS.md" in result.stdout  # tells the user the import line is missing


def test_ac2_a_file_inside_a_copied_tree_is_kept_and_named(plugin, repo):
    mine = repo / "templates" / "TASK_GUIDE_template.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("my guide\n", encoding="utf-8")
    result = run_init(plugin, repo)
    assert mine.read_text(encoding="utf-8") == "my guide\n"
    assert "= kept templates/TASK_GUIDE_template.md" in result.stdout.replace("\\", "/")
    assert (repo / "templates" / "PROJECT_KANBAN_template.md").is_file()


# --- AC 3 — settings keys are shown first, written only after approval, never changed -------------

def test_ac3_the_command_shows_a_dry_run_and_writes_only_after_approval():
    text = (REPO / "commands" / "init.md").read_text(encoding="utf-8")
    assert text.startswith("---\n") and "description:" in text.split("---", 2)[1]
    assert "plugin_init.py" in text
    dry, write = text.index("--dry-run"), text.rindex("apply_profile.py")
    assert dry < write and "approve" in text[dry:write]
    assert "legacy" in text and "high-security" in text


def test_ac3_dry_run_writes_nothing_and_the_write_keeps_every_key(plugin, repo):
    settings = repo / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"model": "opus", "permissions": {"deny": ["Read(./secret)"]}}),
                        encoding="utf-8")
    original = settings.read_bytes()
    apply = [sys.executable, str(plugin / "skills" / "settings-setup" / "scripts" / "apply_profile.py")]
    dry = subprocess.run(apply + ["legacy", "--dry-run"], capture_output=True, text=True, cwd=str(repo))
    assert "+ permissions.deny: Edit(~/.claude/harness-anchors/**)" in dry.stdout
    assert settings.read_bytes() == original
    subprocess.run(apply + ["legacy"], check=True, capture_output=True, cwd=str(repo))
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["model"] == "opus" and data["permissions"]["deny"][0] == "Read(./secret)"
    assert "Bash(*harness-anchors*)" in data["permissions"]["deny"]


def test_t251_the_legacy_profile_adds_the_transcript_deny_rules_add_only(plugin, repo):
    settings = repo / ".claude" / "settings.json"
    settings.parent.mkdir()
    own = "Edit(~/.claude/projects/**/*.jsonl)"  # a project that already has one of them
    settings.write_text(json.dumps({"permissions": {"deny": ["Read(./secret)", own]}}), encoding="utf-8")
    apply = [sys.executable, str(plugin / "skills" / "settings-setup" / "scripts" / "apply_profile.py")]
    dry = subprocess.run(apply + ["legacy", "--dry-run"], capture_output=True, text=True, cwd=str(repo))
    assert "+ permissions.deny: Bash(*.claude/projects/*)" in dry.stdout
    assert "+ permissions.deny: " + own not in dry.stdout
    subprocess.run(apply + ["legacy"], check=True, capture_output=True, cwd=str(repo))
    deny = json.loads(settings.read_text(encoding="utf-8"))["permissions"]["deny"]
    assert deny[:2] == ["Read(./secret)", own]
    assert deny.count(own) == 1 and deny.count("Bash(*.claude/projects/*)") == 1
    kit = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert set(kit["permissions"]["deny"]) <= set(deny)


def test_edge_settings_that_are_not_json_are_refused_and_left_alone(plugin, repo):
    settings = repo / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text("{ // a comment\n}", encoding="utf-8")
    apply = [sys.executable, str(plugin / "skills" / "settings-setup" / "scripts" / "apply_profile.py")]
    result = subprocess.run(apply + ["legacy"], capture_output=True, text=True, cwd=str(repo))
    assert result.returncode == 2 and "not valid JSON" in result.stderr
    assert settings.read_text(encoding="utf-8") == "{ // a comment\n}"


# --- AC 4 — both modes: one block, from the in-repo hook ------------------------------------------

def test_ac4_both_modes_a_blocked_push_shows_one_block_from_the_in_repo_hook(plugin, repo):
    run_init(plugin, repo)
    wire_in_repo_hooks(repo)
    with_open_task(repo)
    in_repo = run_hook(repo / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    from_plugin = run_hook(plugin / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    assert decision(in_repo) == "block" and "T900" in in_repo.stdout
    assert (from_plugin.returncode, from_plugin.stdout, from_plugin.stderr) == (0, "", "")


@pytest.mark.parametrize("hook", ELEVEN_HOOKS)
def test_ac4_every_plugin_hook_stands_down_silently_beside_its_in_repo_twin(plugin, repo, hook):
    run_init(plugin, repo)
    wire_in_repo_hooks(repo)
    with_open_task(repo)
    before = snapshot(repo)
    result = run_hook(plugin / ".claude" / "hooks", hook, EVENTS[hook], repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert snapshot(repo) == before


def test_ac4_wiring_without_the_hook_file_keeps_the_plugin_gate(plugin, repo):
    """A settings line that names a missing file runs no gate, so the plugin gate must not stand down."""
    run_init(plugin, repo)
    wire_in_repo_hooks(repo)
    (repo / ".claude" / "hooks" / "pre_bash_block_unsafe_merge.py").unlink()
    with_open_task(repo)
    result = run_hook(plugin / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    assert decision(result) == "block"


def test_ac4_settings_that_are_not_json_keep_the_plugin_gate(plugin, repo):
    run_init(plugin, repo)
    wire_in_repo_hooks(repo)
    (repo / ".claude" / "settings.json").write_text("{ not json", encoding="utf-8")
    with_open_task(repo)
    result = run_hook(plugin / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    assert decision(result) == "block"


def test_ac4_the_hook_copies_init_makes_are_not_wired_so_the_plugin_gate_runs(plugin, repo):
    """init copies `stop_auto_verify.py` and `lib/` (D7 a) but wires nothing: that is not in-repo mode."""
    run_init(plugin, repo)
    with_open_task(repo)
    result = run_hook(plugin / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    assert decision(result) == "block"


def test_ac4_an_in_repo_hook_never_stands_down(repo):
    wire_in_repo_hooks(repo)
    (repo / "PROJECT_KANBAN.md").write_text("# Board\n\n### In Progress\n" + OPEN_TASK, encoding="utf-8")
    result = run_hook(repo / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
    assert decision(result) == "block"


# --- AC 5 — a setup.sh install gains no command and no init skill ---------------------------------

def test_ac5_manifest_ships_no_commands_folder_and_no_init_skill():
    entries = [line.split()[0] for line in (REPO / "MANIFEST").read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.lstrip().startswith(("#", "!"))]
    assert not any(e == "commands" or e.startswith("commands/") for e in entries)
    assert not (REPO / "skills" / "init").exists()
    assert (REPO / "commands" / "init.md").is_file()


# --- D6, D7 (c), D8, edge cases -------------------------------------------------------------------

def test_d6a_with_the_env_unset_a_plugin_hook_finds_the_project_from_the_cwd(plugin, repo):
    """D6 (a): from a plugin, `project_root()` never answers with the plugin folder."""
    run_init(plugin, repo)
    with_open_task(repo)
    sub = repo / "src"
    sub.mkdir()
    hooks = plugin / ".claude" / "hooks"
    result = run_hook(hooks, "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo, cwd=sub, set_env=False,
                      plugin_root=plugin)
    assert decision(result) == "block" and "T900" in result.stdout


def test_d6a_with_the_env_unset_outside_a_kit_project_a_plugin_hook_is_silent(plugin, tmp_path):
    """The plugin ships the kit's own board; it must never be read as the user's."""
    plain = git_repo(tmp_path / "plain")
    result = run_hook(plugin / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, plain,
                      set_env=False, plugin_root=plugin)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_d6a_known_limit_with_both_variables_unset_the_answer_stays_the_code_path(plugin, tmp_path):
    """No harness variable at all: the kit's own checkout and a plugin cache look the same (both hold
    `.claude-plugin/`), so the T232 answer stays, and the hook reads the folder it sits in."""
    plain = git_repo(tmp_path / "plain")
    code = (f"import sys; sys.path.insert(0, {str(plugin / '.claude' / 'hooks' / 'lib')!r})\n"
            "import project_root as pr; print(pr.project_root())")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(plain),
                          env=clean_env())
    assert done.stdout.strip() == str(plugin)


def test_ac4_a_worker_call_with_arguments_never_stands_down(plugin, repo):
    """`wires_in_repo_hook` silences hook calls only: a hook gets no arguments, a worker does."""
    run_init(plugin, repo)
    wire_in_repo_hooks(repo)
    lib = plugin / ".claude" / "hooks" / "lib"
    code = (f"import sys; sys.path.insert(0, {str(lib)!r}); sys.argv = ['stop_auto_verify.py', '--run']\n"
            "import project_root as pr; pr.exit_outside_kit_project(); print('ran')")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          env=clean_env(CLAUDE_PROJECT_DIR=str(repo)))
    assert done.stdout.strip() == "ran"


def test_d6b_a_broken_project_root_helper_still_blocks_everywhere(plugin, tmp_path):
    """D6 (b), decided: keep fail-closed. With `project_root.py` broken no hook can tell a kit project
    from any other, and a gate that passes silently in a kit project is the failure gates exist to
    prevent. The block names the file to restore, and `claude plugin disable easy-kit` or the next
    plugin update clears it in an unrelated repo."""
    broken = tmp_path / "broken" / "easy-kit"
    shutil.copytree(plugin / ".claude-plugin", broken / ".claude-plugin")
    shutil.copytree(plugin / ".claude" / "hooks", broken / ".claude" / "hooks")
    (broken / ".claude" / "hooks" / "lib" / "project_root.py").write_text("def (:\n", encoding="utf-8")
    plain = git_repo(tmp_path / "plain")
    result = run_hook(broken / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, plain)
    assert decision(result) == "block" and "project_root.py" in result.stdout


def test_d7c_init_writes_to_the_cwd_repo_never_a_parent_board_or_the_plugin(plugin, tmp_path):
    parent = tmp_path / "workspace"
    parent.mkdir()
    (parent / "PROJECT_KANBAN.md").write_text("# parent board\n", encoding="utf-8")
    child = git_repo(parent / "child")
    plugin_before = snapshot(plugin)
    result = run_init(plugin, child)
    assert result.returncode == 0, result.stderr
    assert (child / "PROJECT_KANBAN.md").is_file()
    assert sorted(p.name for p in parent.iterdir()) == ["PROJECT_KANBAN.md", "child"]
    assert (parent / "PROJECT_KANBAN.md").read_text(encoding="utf-8") == "# parent board\n"
    assert snapshot(plugin) == plugin_before


def test_d8_init_reports_what_it_did_and_copies_no_bytecode(plugin, repo):
    """D8, decided: accept `__pycache__` in the plugin folder (a cache Python checks against the
    source; no state). init must never copy it into the project."""
    cache = plugin / ".claude" / "hooks" / "lib" / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "fake.cpython-3.pyc").write_bytes(b"\0")
    result = run_init(plugin, repo)
    assert result.stdout.strip() and "+ created" in result.stdout
    assert not [p for p in repo.rglob("__pycache__") if ".git" not in p.parts]


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [S_IRUSR]")
def test_d8_a_hook_from_a_read_only_plugin_folder_still_gates(plugin, repo, tmp_path):
    """Accepting bytecode is safe: where the plugin folder is read-only, Python skips the write."""
    ro = tmp_path / "ro" / "easy-kit"
    shutil.copytree(plugin / ".claude-plugin", ro / ".claude-plugin")
    shutil.copytree(plugin / ".claude" / "hooks", ro / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("__pycache__"))
    run_init(plugin, repo)
    with_open_task(repo)
    for d in [p for p in ro.rglob("*") if p.is_dir()] + [ro]:
        d.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        result = run_hook(ro / ".claude" / "hooks", "pre_bash_block_unsafe_merge.py", BASH_PUSH, repo)
        assert decision(result) == "block"
        assert not list(ro.rglob("__pycache__"))
    finally:
        for d in [ro] + [p for p in ro.rglob("*") if p.is_dir()]:
            d.chmod(stat.S_IRWXU)


def test_edge_a_path_that_blocks_a_copy_stops_with_a_message_and_overwrites_nothing(plugin, repo):
    (repo / "templates").write_text("a file, not a folder\n", encoding="utf-8")
    result = run_init(plugin, repo)
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert "cannot write" in result.stderr
    assert (repo / "templates").read_text(encoding="utf-8") == "a file, not a folder\n"
    assert "+ created CLAUDE.md" in result.stdout


def test_edge_init_outside_a_git_repo_refuses_and_writes_nothing(plugin, tmp_path):
    folder = tmp_path / "not-a-repo"
    folder.mkdir()
    result = run_init(plugin, folder)
    assert result.returncode == 2
    assert "git" in result.stderr
    assert list(folder.iterdir()) == []
