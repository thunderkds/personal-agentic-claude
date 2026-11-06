"""T234 — skills and agents work under the `easy-kit:` prefix, and every script a skill calls is found.

  AC1 — no repo-relative script call is left in `skills/` or `agents/` (a plugin user's project holds
        none of the kit's files). The rule (D1, D4): a skill names a script by `${CLAUDE_SKILL_DIR}` —
        `${CLAUDE_SKILL_DIR}/scripts/x.py` for its own script, `${CLAUDE_SKILL_DIR}/../../scripts/x.py`
        for a shared one. Each such path must exist in the plugin layout and in the `setup.sh` layout.
  AC4 — hooks accept `backend-developer` and `easy-kit:backend-developer` alike.
  D3  — `AGENTS.md` names the plugin form of each agent; `craft-spawn-prompt` picks the form by mode.
  D5  — a script run from a plugin reads and writes the user's project, never the plugin folder.

The plugin folder is a copy of the kit in a temp folder, the project is another temp folder that holds
only what the test puts in it, and `CLAUDE_PROJECT_DIR` is unset, as it is in a `Bash` tool call.

Run with: python3 -m pytest tests/test_plugin_names.py -q
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
AGENTS = REPO / "agents"
SKILL_DIR_VAR = "${CLAUDE_SKILL_DIR}"
AGENT_NAMES = ("common-infrastructure", "backend-developer", "frontend-developer", "qa-expert")

# A command that runs a kit script: `python3 <path>`, `sh <path>`, `bash <path>`. A flag (`-m`) or a
# `${...}` first argument is no repo-relative path.
CALL = re.compile(r"(?<![\w/.-])(?:python3?|sh|bash)\s+[`\"']?(?![-$])([\w./-]+)")
REPO_PREFIXES = ("scripts/", "skills/", "lib/", ".claude/", "./")
# A path to a skill's bundled script written without the skill-dir variable.
BARE_SKILL_SCRIPT = re.compile(r"(?<![\w/}.-])skills/[a-z0-9-]+/scripts/[\w.-]+")

# Kit-maintainer steps: they run inside a checkout of the kit repo and write kit files, so a plugin
# user never runs them. One reason per entry.
KIT_REPO_ONLY = {
    ("skills/craft-spawn-prompt/references/sandbox.md", "scripts/gen_sandbox_profile.py"):
        "regenerates the kit's own templates/subagent-sandbox.settings.json after a kit edit",
}


def prompt_files():
    return sorted(list(SKILLS.rglob("*.md")) + list(AGENTS.glob("*.md")))


def rel(path):
    return path.relative_to(REPO).as_posix()


# --- AC1: no repo-relative script call left ----------------------------------------------------

def test_no_repo_relative_script_call_left_in_skills_or_agents():
    bad = []
    for path in prompt_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for target in CALL.findall(line):
                if target.startswith(REPO_PREFIXES) and (rel(path), target) not in KIT_REPO_ONLY:
                    bad.append(f"{rel(path)}:{n}: {target}")
            for target in BARE_SKILL_SCRIPT.findall(line):
                if (rel(path), target) not in KIT_REPO_ONLY:
                    bad.append(f"{rel(path)}:{n}: {target}")
    assert not bad, "repo-relative script paths (use ${CLAUDE_SKILL_DIR}):\n" + "\n".join(bad)


def test_the_check_catches_a_repo_relative_call():
    """Anti-vacuity: the pattern flags the forms the skills used before T234."""
    for line in ("Run `python3 scripts/pull_moment.py wake` first",
                 "python3 skills/wake/scripts/memory_sections.py",
                 "run `sh .claude/hooks/x.sh`",
                 "Copy `skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh` to"):
        found = CALL.findall(line) + BARE_SKILL_SCRIPT.findall(line)
        assert any(t.startswith(REPO_PREFIXES) or t.startswith("skills/") for t in found), line
    for line in ("python3 ${CLAUDE_SKILL_DIR}/../../scripts/pull_moment.py wake",
                 "python3 -m pytest .claude/hooks/tests -q"):
        assert not [t for t in CALL.findall(line) if t.startswith(REPO_PREFIXES)], line
        assert not BARE_SKILL_SCRIPT.findall(line), line


# Files that show the rule with a made-up script name; they call nothing.
RULE_EXAMPLES = ("skills/write-better-skill/SKILL.md",)


def skill_dir_paths():
    """(markdown file, skill dir, the path after the variable) for every use of the variable."""
    found = []
    for path in prompt_files():
        if rel(path) in RULE_EXAMPLES:
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\$\{CLAUDE_SKILL_DIR\}(/[\w./-]*[\w])", text):
            skill = SKILLS / path.relative_to(SKILLS).parts[0] if SKILLS in path.parents else None
            found.append((path, skill, m.group(1)))
    return found


def test_skills_use_the_skill_dir_variable():
    used = {rel(p) for p, _, _ in skill_dir_paths()}
    for name in ("wake", "craft-spawn-prompt", "code-review", "resolve-question",
                 "compact-advisor", "delivery-report", "settings-setup", "dotfiles",
                 "companion-setup", "git-guardrails-claude-code"):
        assert f"skills/{name}/SKILL.md" in used, name


def test_every_skill_dir_path_exists_in_the_plugin_layout():
    """Plugin layout: the skill dir is `<plugin>/skills/<name>`."""
    missing = []
    for path, skill, tail in skill_dir_paths():
        target = Path(os.path.normpath(skill / tail.lstrip("/")))
        if not target.exists():
            missing.append(f"{rel(path)}: {SKILL_DIR_VAR}{tail}")
    assert not missing, "\n".join(missing)


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_every_skill_dir_path_exists_in_the_setup_install_layout(tmp_path):
    """`setup.sh` layout: Claude Code names the skill dir `<project>/.claude/skills/<name>`, and
    `.claude/skills` is a relative symlink onto `<project>/skills`. The kernel resolves `..` after the
    symlink, so `../../scripts` is the project's `scripts/`."""
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(SKILLS, project / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "scripts", project / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    (project / ".claude" / "skills").symlink_to("../skills")
    missing = []
    for path, skill, tail in skill_dir_paths():
        target = project / ".claude" / "skills" / skill.name / tail.lstrip("/")
        # os.path.normpath would fold `..` lexically; the kernel does not, so ask the kernel.
        if not os.path.exists(str(target)):
            missing.append(f"{rel(path)}: {SKILL_DIR_VAR}{tail}")
    assert not missing, "\n".join(missing)


# --- D5: a script run from a plugin reads and writes the project --------------------------------

BOARD_JSON = [{"id": "ENG-170", "title": "mine", "status": "In Progress", "assignee": "alice",
               "description": "# guide ENG-170 v1\n"}]


def clean_env():
    return {k: v for k, v in os.environ.items()
            if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "LINEAR_API_KEY")}


def make_plugin(tmp_path):
    """The kit as a plugin cache holds it: code only, no board, no tasks, no memory."""
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    shutil.copytree(REPO / ".claude" / "hooks", plugin / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    shutil.copytree(REPO / "scripts", plugin / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SKILLS, plugin / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "templates", plugin / "templates")
    shutil.copytree(REPO / ".claude-plugin", plugin / ".claude-plugin")
    return plugin


def make_online_project(tmp_path):
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    (project / "tasks").mkdir()
    (project / "board.json").write_text(json.dumps(BOARD_JSON))
    (project / ".claude" / "board.json").write_text(json.dumps(
        {"board": "fake", "fake_board": "board.json", "id_pattern": r"ENG-\d+", "me": "alice"}))
    return project


def tree(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def run(args, cwd):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True,
                          cwd=cwd, env=clean_env(), timeout=60, stdin=subprocess.DEVNULL)


def test_pull_moment_from_a_plugin_pulls_the_board_into_the_project(tmp_path):
    plugin, project = make_plugin(tmp_path), make_online_project(tmp_path)
    before = tree(plugin)
    result = run([plugin / "scripts" / "pull_moment.py", "wake"], project)
    assert result.returncode == 0, result.stderr
    assert "board unreachable" not in result.stdout, result.stdout
    assert "**ENG-170**" in (project / "PROJECT_KANBAN.md").read_text()
    assert (project / "tasks" / "TASK_GUIDE_ENG-170.md").exists()
    assert tree(plugin) == before, "the plugin folder must stay as it was"


def test_board_sync_from_a_plugin_takes_the_project_root(tmp_path):
    plugin, project = make_plugin(tmp_path), make_online_project(tmp_path)
    before = tree(plugin)
    result = run([plugin / "scripts" / "board_sync.py", "pull"], project)
    assert result.returncode == 0, result.stderr
    assert (project / "PROJECT_KANBAN.md").exists()
    assert tree(plugin) == before, "the plugin folder must stay as it was"


def test_delivery_report_from_a_plugin_reads_and_writes_the_project(tmp_path):
    plugin, project = make_plugin(tmp_path), tmp_path / "project"
    (project / "tasks").mkdir(parents=True)
    (project / "PROJECT_KANBAN.md").write_text("# board\n")
    (project / "memory" / "event-trace").mkdir(parents=True)
    (project / "memory" / "event-trace" / "T900.jsonl").write_text(
        json.dumps({"timestamp": "2026-11-02T00:00:00Z", "tool": "Bash"}) + "\n")
    guide = project / "tasks" / "TASK_GUIDE_T900.md"
    guide.write_text("# TASK_GUIDE — T900: x\n")
    before = tree(plugin)
    result = run([plugin / "skills" / "delivery-report" / "render.py", "T900", guide, "feat-x"], project)
    assert result.returncode == 0, result.stderr
    assert "Derived from memory/event-trace/T900.jsonl: 1 tool-call record(s)" in result.stdout
    assert list((project / "reports").glob("delivery-report_feat-x_*.html"))
    assert tree(plugin) == before, "the plugin folder must stay as it was"


def test_stop_auto_verify_start_from_a_plugin_finds_the_project(tmp_path):
    plugin, project = make_plugin(tmp_path), tmp_path / "project"
    project.mkdir()
    (project / "PROJECT_KANBAN.md").write_text(
        "# Board\n\n### In Progress\n- [~] **T900** — open task | backend-developer | C1 | "
        "Risk: Low | P1\n\n### Ready for Review\n\n### Done\n")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = run([plugin / ".claude" / "hooks" / "stop_auto_verify.py", "--start", "T900"], project)
    assert "T900: not at Ready for Review on PROJECT_KANBAN.md — nothing started" in result.stdout, \
        (result.stdout, result.stderr)


def test_script_project_root_prefers_the_env_then_the_cwd_then_the_file(tmp_path, monkeypatch):
    sys.path.insert(0, str(REPO / ".claude" / "hooks" / "lib"))
    try:
        import project_root as pr
    finally:
        sys.path.pop(0)
    kit, deep, other = tmp_path / "kit", tmp_path / "kit" / "a" / "b", tmp_path / "other"
    deep.mkdir(parents=True)
    other.mkdir()
    (kit / "PROJECT_KANBAN.md").write_text("# board\n")
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(deep)
    assert pr.script_project_root() == str(kit), "the nearest folder above the cwd that holds a board"
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(other))
    assert pr.script_project_root() == str(other), "the env var still wins"
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    monkeypatch.chdir(other)
    # D7: this checkout holds `.claude-plugin/plugin.json`, so it is a plugin folder: no board above the
    # cwd means no project, never the folder the code sits in.
    assert pr.script_project_root() is None


# --- D3 / AC4: both agent names ------------------------------------------------------------------

def test_agents_md_role_table_names_the_plugin_form_of_each_agent():
    text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    rows = [l for l in text.splitlines() if re.match(r"\|.*`agents/[\w-]+\.md`", l)]
    assert len(rows) == 4, rows
    for name in AGENT_NAMES:
        row = next(l for l in rows if f"`{name}`" in l)
        assert f"`easy-kit:{name}`" in row, row


def test_craft_spawn_prompt_reports_the_name_for_the_mode():
    body = (SKILLS / "craft-spawn-prompt" / "SKILL.md").read_text(encoding="utf-8")
    assert "easy-kit:" in body
    assert "subagent_type" in body
    assert "Agent type '" in body or "not found" in body, "say what a wrong form does"


def test_each_agent_name_field_is_the_bare_name():
    """The plugin adds the prefix; the file keeps the bare name, so one file serves both modes (D2)."""
    names = sorted(re.search(r"^name: (\S+)$", p.read_text(encoding="utf-8"), re.M).group(1)
                   for p in AGENTS.glob("*.md"))
    assert names == sorted(AGENT_NAMES)


HOOKS = REPO / ".claude" / "hooks"
GUIDE = ("# TASK_GUIDE — T900: both names\n**Complexity Level**: C1\n**Risk Level**: Low\n"
         "**Priority**: P1\n**Assigned agent**: {agent}\n")


@pytest.mark.parametrize("agent", ["backend-developer", "easy-kit:backend-developer"])
def test_register_hook_keeps_the_whole_agent_name(tmp_path, agent):
    project = tmp_path / "p"
    (project / "tasks").mkdir(parents=True)
    (project / "PROJECT_KANBAN.md").write_text("# Board\n\n### Todo\n\n### Done\n")
    guide = project / "tasks" / "TASK_GUIDE_T900.md"
    guide.write_text(GUIDE.format(agent=agent))
    event = {"tool_name": "Write", "tool_input": {"file_path": str(guide)}}
    env = clean_env()
    env["CLAUDE_PROJECT_DIR"] = str(project)  # a hook gets it from the harness
    result = subprocess.run([sys.executable, str(HOOKS / "post_write_register_task.py")],
                            input=json.dumps(event), capture_output=True, text=True, cwd=project,
                            env=env, timeout=30)
    assert result.returncode == 0, result.stderr
    row = next(l for l in (project / "PROJECT_KANBAN.md").read_text().splitlines() if "**T900**" in l)
    assert f"| {agent} | C1 |" in row, row


def spawn_event(subagent_type):
    return {"tool_name": "Agent", "session_id": "s1",
            "tool_input": {"subagent_type": subagent_type,
                           "prompt": "Task ID: T900\nGuide: tasks/TASK_GUIDE_T900.md"}}


def test_spawn_hook_decides_the_same_for_both_forms(tmp_path):
    """The spawn hook blocks on the guide, never on the agent name."""
    project = tmp_path / "p"
    (project / "tasks").mkdir(parents=True)
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    answers = {}
    for form in ("backend-developer", "easy-kit:backend-developer"):
        env = clean_env()
        env["CLAUDE_PROJECT_DIR"] = str(project)
        result = subprocess.run([sys.executable, str(HOOKS / "pre_agent_validate_guide.py")],
                                input=json.dumps(spawn_event(form)), capture_output=True, text=True,
                                cwd=project, env=env, timeout=30)
        assert result.returncode == 0, result.stderr
        answers[form] = result.stdout
    assert answers["backend-developer"] == answers["easy-kit:backend-developer"]
    assert "T900" in answers["backend-developer"]


@pytest.mark.parametrize("agent_type", ["backend-developer", "easy-kit:backend-developer"])
def test_trace_hook_records_either_agent_type(tmp_path, agent_type):
    project = tmp_path / "p"
    project.mkdir()
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    event = {"tool_name": "Agent", "session_id": "s1",
             "tool_input": {"subagent_type": agent_type,
                            "prompt": "Task ID: T900\nGuide: tasks/TASK_GUIDE_T900.md"},
             "tool_response": {"agentType": agent_type, "status": "completed"}}
    env = clean_env()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env["CLAUDE_TRACE_ANCHOR_DIR"] = str(tmp_path / "anchors")
    result = subprocess.run([sys.executable, str(HOOKS / "post_tool_trace.py")],
                            input=json.dumps(event), capture_output=True, text=True, cwd=project,
                            env=env, timeout=30)
    assert result.returncode == 0, result.stderr
    trace = project / "memory" / "event-trace" / "T900.jsonl"
    assert trace.exists(), tree(project)
    assert json.loads(trace.read_text().splitlines()[-1])["spawn"]["agent_type"] == agent_type


def test_spawn_hook_names_the_scripts_it_mentions_by_paths_that_exist(tmp_path):
    """The hook tells the agent to run `board_sync.py` (guide incomplete) and `memory_slice.py` (no
    slice); from a plugin the project holds no copy, so each message carries the path of the kit the
    hook belongs to."""
    plugin = make_plugin(tmp_path)
    project = tmp_path / "project"
    (project / "tasks").mkdir(parents=True)
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    guide = project / "tasks" / "TASK_GUIDE_T900.md"
    env = clean_env()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    hook = plugin / ".claude" / "hooks" / "pre_agent_validate_guide.py"
    event = {"tool_name": "Agent", "session_id": "s1",
             "tool_input": {"prompt": "Task ID: T900\nRead tasks/TASK_GUIDE_T900.md"}}

    def spawn():
        return subprocess.run([sys.executable, str(hook)], input=json.dumps(event),
                              capture_output=True, text=True, cwd=project, env=env, timeout=30)

    guide.write_text("# TASK_GUIDE — T900: x\n")
    blocked = json.loads(spawn().stdout)["reason"]
    board_sync = re.search(r"`python3 (\S+board_sync\.py) update --guide <ID>`", blocked)
    assert board_sync, blocked
    assert board_sync.group(1) == str(plugin / "scripts" / "board_sync.py")
    assert Path(board_sync.group(1)).exists()

    guide.write_text((REPO / "tasks" / "TASK_GUIDE_T234.md").read_text(encoding="utf-8"))
    result = spawn()
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    named = re.search(r"`python3 (\S+memory_slice\.py) <guide>`", context)
    assert named, context
    assert named.group(1) == str(plugin / "skills" / "craft-spawn-prompt" / "scripts" / "memory_slice.py")
    assert Path(named.group(1)).exists()


# --- paths in messages are safe to paste ------------------------------------------------------

def make_plugin_at(tmp_path, name):
    plugin = make_plugin(tmp_path)
    plugin.rename(tmp_path / name)
    return tmp_path / name


def test_hook_messages_quote_a_plugin_path_with_a_space(tmp_path):
    import shlex
    plugin = make_plugin_at(tmp_path, "my plug$in")
    project = tmp_path / "project"
    (project / "tasks").mkdir(parents=True)
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    guide = project / "tasks" / "TASK_GUIDE_T900.md"
    env = clean_env()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    hook = plugin / ".claude" / "hooks" / "pre_agent_validate_guide.py"
    event = {"tool_name": "Agent", "session_id": "s1",
             "tool_input": {"prompt": "Task ID: T900\nRead tasks/TASK_GUIDE_T900.md"}}

    def spawn():
        return subprocess.run([sys.executable, str(hook)], input=json.dumps(event),
                              capture_output=True, text=True, cwd=project, env=env, timeout=30)

    guide.write_text("# TASK_GUIDE — T900: x\n")
    blocked = json.loads(spawn().stdout)["reason"]
    assert f"python3 {shlex.quote(str(plugin / 'scripts' / 'board_sync.py'))} update" in blocked, blocked
    guide.write_text((REPO / "tasks" / "TASK_GUIDE_T234.md").read_text(encoding="utf-8"))
    context = json.loads(spawn().stdout)["hookSpecificOutput"]["additionalContext"]
    slice_script = plugin / "skills" / "craft-spawn-prompt" / "scripts" / "memory_slice.py"
    assert f"python3 {shlex.quote(str(slice_script))} <guide>" in context, context


def test_pull_moment_unsynced_message_quotes_a_plugin_path_with_a_space(tmp_path):
    import shlex
    plugin = make_plugin_at(tmp_path, "my plug$in")
    project = make_online_project(tmp_path)
    (project / ".board").mkdir()
    (project / ".board" / "outbox.jsonl").write_text('{"a": 1}\n')
    result = run([plugin / "scripts" / "pull_moment.py", "wake"], project)
    sync = shlex.quote(str(plugin / "scripts" / "board_sync.py"))
    assert f"run python3 {sync} flush" in result.stdout, result.stdout


# --- the commands run, in both layouts, in a folder with a space ------------------------------
# T234 round 3: `${CLAUDE_SKILL_DIR}` is `<project>/.claude/skills/<name>` in a `setup.sh` install, and
# `.claude/skills` is a symlink. A script that finds its code by `abspath(__file__)` then lands in
# `<project>/.claude`, not the kit. These tests run every command the skills write.

SKILL_CMD = re.compile(r'python3 (?P<quote>"?)\$\{CLAUDE_SKILL_DIR\}(?P<tail>/[^"\s`]*)')
GUIDE_FOR_RUNS = ("# TASK_GUIDE — T900: x\n**Complexity Level**: C1\n**Risk Level**: Low\n"
                  "## Files to Change (Predicted)\n\n| File | Change |\n|---|---|\n| `src/a.py` | x |\n")
# Per script: the harmless arguments the test passes instead of the ones the skill shows. Every script
# a `${CLAUDE_SKILL_DIR}` command reaches has an entry; the test fails on a script with none.
SAFE_ARGS = {
    "pull_moment.py": ["wake"],                      # board mode local: a no-op, exit 0
    "board_sync.py": ["status"],                     # prints the unsynced count
    "lane_check.py": ["tasks/TASK_GUIDE_T900.md", "HEAD...HEAD"],
    "token_meter.py": ["--help"],                    # the real run reads the user's transcripts
    "memory_slice.py": ["tasks/TASK_GUIDE_T900.md"],
    "memory_sections.py": [],
    "dirty_worktrees.py": [],
    "check_companions.py": [],
    "render.py": ["T900", "tasks/TASK_GUIDE_T900.md", "feat-x", "{out}"],
    "apply_profile.py": ["--help"],                  # the real run writes .claude/settings.json
    "dotfiles.py": ["--help"],                       # the real run writes the user's home folders
    "tap_probe.py": ["--help"],                      # T248: the real run needs a page and an out dir
    "self_review.py": ["pre"],                       # T256: read-only; exit 0 on any git repo with a commit
}
CRASH_MARKERS = ("Traceback", "No such file", "ModuleNotFoundError", "can't open file")


def skill_commands():
    """(markdown file, skill name, quote, tail) for each `python3 ${CLAUDE_SKILL_DIR}...` command."""
    found = []
    for path in prompt_files():
        if rel(path) in RULE_EXAMPLES:
            continue
        for m in SKILL_CMD.finditer(path.read_text(encoding="utf-8")):
            name = path.relative_to(SKILLS).parts[0]
            found.append((path, name, m.group("quote"), m.group("tail")))
    return found


def test_every_skill_dir_command_quotes_the_variable():
    unquoted = [f"{rel(p)}: {t}" for p, _, q, t in skill_commands() if not q]
    assert not unquoted, "quote it: python3 \"${CLAUDE_SKILL_DIR}/...\"\n" + "\n".join(unquoted)
    assert skill_commands(), "no command found: the pattern is broken"


def build_layout(tmp_path, layout):
    """Return (skill dir parent, project) for the layout. Both folder names hold a space."""
    project = tmp_path / "my project"
    (project / "tasks").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    (project / "tasks" / "TASK_GUIDE_T900.md").write_text(GUIDE_FOR_RUNS)
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@e", "commit", "-qm", "x"]):
        subprocess.run(["git", *cmd], cwd=project, check=True, capture_output=True)
    if layout == "install":
        kit = project
        (kit / ".claude").mkdir(exist_ok=True)
    else:
        kit = tmp_path / "my plugin"
        (kit / ".claude").mkdir(parents=True)
    shutil.copytree(REPO / ".claude" / "hooks", kit / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    shutil.copytree(SKILLS, kit / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "scripts", kit / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "templates", kit / "templates")
    if layout == "install":
        (kit / ".claude" / "skills").symlink_to("../skills")
        return kit / ".claude" / "skills", project
    return kit / "skills", project


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [via build_layout]")
@pytest.mark.parametrize("layout", ["install", "plugin"])
def test_every_skill_dir_command_runs(tmp_path, layout):
    skills_parent, project = build_layout(tmp_path, layout)
    ran = set()
    for path, name, _, tail in skill_commands():
        script = skills_parent / name / tail.lstrip("/")
        base = os.path.basename(tail)
        assert base in SAFE_ARGS, f"{rel(path)}: no safe arguments for {base}"
        args = [a.replace("{out}", str(tmp_path / "out")) for a in SAFE_ARGS[base]]
        result = run([script, *args], project)
        label = f"{layout}: {rel(path)}: {base} {args}\n{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, label
        assert not any(m in result.stdout + result.stderr for m in CRASH_MARKERS), label
        if base == "lane_check.py":
            assert "UNKNOWN" not in result.stdout, label
        if base == "memory_slice.py":
            assert "memory-slice:T900" in result.stdout, label
        ran.add(base)
    assert ran == set(SAFE_ARGS), set(SAFE_ARGS) - ran


# --- D7: from a plugin, with no project, say so -------------------------------------------------

NO_PROJECT_TEXT = "no project found"


def test_a_plugin_run_from_an_empty_folder_says_no_project_and_writes_nothing(tmp_path):
    plugin = make_plugin(tmp_path)
    empty = tmp_path / "empty folder"
    empty.mkdir()
    before = tree(plugin)
    pull = run([plugin / "scripts" / "pull_moment.py", "wake"], empty)
    assert pull.returncode == 0 and NO_PROJECT_TEXT in pull.stdout, (pull.stdout, pull.stderr)
    sync = run([plugin / "scripts" / "board_sync.py", "pull"], empty)
    assert sync.returncode == 2 and NO_PROJECT_TEXT in sync.stderr, (sync.stdout, sync.stderr)
    render = run([plugin / "skills" / "delivery-report" / "render.py", "T900", "g.md", "b"], empty)
    assert render.returncode == 2 and NO_PROJECT_TEXT in render.stderr, (render.stdout, render.stderr)
    start = run([plugin / ".claude" / "hooks" / "stop_auto_verify.py", "--start", "T900"], empty)
    assert start.returncode == 1, (start.stdout, start.stderr)
    assert f"T900: {NO_PROJECT_TEXT}" in start.stdout and "nothing started" in start.stdout, start.stdout
    assert "PROJECT_KANBAN" not in start.stdout.replace("PROJECT_KANBAN.md or", ""), "never the plugin's board"
    assert tree(plugin) == before and tree(empty) == []


def test_a_setup_install_run_from_an_empty_folder_keeps_its_own_project(tmp_path):
    """No `.claude-plugin/plugin.json` in an install, so the code's own project is still the answer."""
    install = make_plugin(tmp_path)
    shutil.rmtree(install / ".claude-plugin")
    (install / "PROJECT_KANBAN.md").write_text("# Board\n\n### In Progress\n- [~] **T900** — x | a | C1 | Risk: Low | P1\n")
    empty = tmp_path / "empty folder"
    empty.mkdir()
    start = run([install / ".claude" / "hooks" / "stop_auto_verify.py", "--start", "T900"], empty)
    assert NO_PROJECT_TEXT not in start.stdout, start.stdout
    assert "T900: not at Ready for Review on PROJECT_KANBAN.md" in start.stdout, start.stdout


# --- D6: the Codex projection, and the real installer ---------------------------------------------

def hide_real_clis():
    """PATH without a folder that holds `claude` or `codex`: the CLI menu pre-selects what is on PATH."""
    dirs = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if not (os.access(os.path.join(d, "claude"), os.X_OK) or os.access(os.path.join(d, "codex"), os.X_OK))]
    return os.pathsep.join(dirs)


@pytest.fixture(scope="module")
def kit_snapshot(tmp_path_factory):
    """The working tree as a git repo of its own, so `setup.sh` clones what this checkout holds now,
    not the last commit (an install can run green over a tree that lacks the change)."""
    if not (shutil.which("script") and shutil.which("setsid") and shutil.which("git")):
        pytest.skip("needs script, setsid and git")
    snap = tmp_path_factory.mktemp("snap")
    names = subprocess.run(["git", "ls-files", "-z", "-c", "-o", "--exclude-standard"], cwd=REPO,
                           capture_output=True, check=True).stdout.split(b"\0")
    for raw in filter(None, names):
        name = raw.decode()
        if (REPO / name).is_file() or (REPO / name).is_symlink():
            dest = snap / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / name, dest, follow_symlinks=False)
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@e", "commit", "-qm", "snap"]):
        subprocess.run(["git", *cmd], cwd=snap, check=True, capture_output=True)
    return snap


def real_install(tmp_path, snap, answers, name):
    """Run the real `setup.sh` in a terminal (a pty) and answer its menus. Folder name holds a space."""
    project = tmp_path / name
    project.mkdir()
    for cmd in (["init", "-q"], ["-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "--allow-empty", "-m", "init"]):
        subprocess.run(["git", *cmd], cwd=project, check=True, capture_output=True)
    env = clean_env()
    env.update(PATH=hide_real_clis(), SUPERVISOR_REPO=f"file://{snap}", SHELL="/bin/sh")
    done = subprocess.run(["script", "-qec", f"sh '{snap / 'setup.sh'}'", "/dev/null"], input=answers,
                          capture_output=True, text=True, cwd=project, env=env, timeout=180)
    assert done.returncode == 0, done.stdout + done.stderr
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    (project / "tasks").mkdir(exist_ok=True)
    (project / "tasks" / "TASK_GUIDE_T900.md").write_text(GUIDE_FOR_RUNS)
    return project, done.stdout


def real_update(project, snap):
    env = clean_env()
    env.update(PATH=hide_real_clis(), SUPERVISOR_REPO=f"file://{snap}")
    return subprocess.run(["setsid", "-w", "sh", str(snap / "setup.sh")], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, cwd=project, env=env, timeout=180)


CODEX_ANSWERS = "\n2\n\n\n\n"    # Install, CLI menu: 2 = Codex, new project, packs, proceed
CLAUDE_ANSWERS = "\n1\n\n\n\n"   # same, CLI menu: 1 = Claude Code
# Not in MANIFEST, so no install holds it (a gap that predates T234: before it, the same call was
# `python3 scripts/token_meter.py`). The test fails if MANIFEST ever ships it, so the entry goes then.
NOT_SHIPPED = {"token_meter.py": "scripts/token_meter.py is not listed in MANIFEST"}


def codex_commands(project):
    """(file, script path as the Codex copy writes it) for each quoted python3 command in `.codex/skills`."""
    found = []
    for path in sorted((project / ".codex" / "skills").rglob("*")):
        if path.is_file() and path.suffix == ".md":
            for m in re.finditer(r'python3 "([^"\s$]+)"', path.read_text(encoding="utf-8")):
                found.append((path, m.group(1)))
    return found


def check_script(script, base, project, tmp_path, label):
    assert base in SAFE_ARGS, f"{label}: no safe arguments for {base}"
    args = [a.replace("{out}", str(tmp_path / "out")) for a in SAFE_ARGS[base]]
    result = run([script, *args], project)
    text = f"{label}: {base} {args}\n{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, text
    assert not any(m in result.stdout + result.stderr for m in CRASH_MARKERS), text
    if base == "lane_check.py":
        assert "UNKNOWN" not in result.stdout, text
    if base == "memory_slice.py":
        assert "memory-slice:T900" in result.stdout, text


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via kit_snapshot]")
def test_codex_only_install_rewrites_the_variable_and_every_command_runs(tmp_path, kit_snapshot):
    project, out = real_install(tmp_path, kit_snapshot, CODEX_ANSWERS, "my codex project")
    assert not (project / ".claude" / "skills").exists(), "a Codex-only install makes no Claude Code link"
    assert (project / "skills").is_dir() and (project / "scripts").is_dir()
    codex = project / ".codex" / "skills"
    # no copy keeps the variable; the source tree does
    left = [str(p.relative_to(project)) for p in codex.rglob("*")
            if p.is_file() and b"${CLAUDE_SKILL_DIR}" in p.read_bytes()]
    assert not left, left
    assert b"${CLAUDE_SKILL_DIR}" in (project / "skills" / "wake" / "SKILL.md").read_bytes()
    # references too, not only SKILL.md
    assert 'python3 "scripts/pull_moment.py" wake' in (codex / "wake" / "references" / "triage.md").read_text()
    # no skill is newly skipped by the cap: only the four that are over it in the source
    assert sorted(p.name for p in (SKILLS).iterdir() if (p / "SKILL.md").exists()
                  and not (codex / p.name).exists()) == ["bugfix", "craft-spawn-prompt", "diagnose", "write-better-skill"]
    cmds = codex_commands(project)
    assert {os.path.basename(c) for _, c in cmds} >= {"pull_moment.py", "board_sync.py", "lane_check.py",
                                                       "memory_sections.py", "render.py"}
    ran = set()
    for path, command in cmds:
        base = os.path.basename(command)
        if base in NOT_SHIPPED:
            assert not (project / "scripts" / base).exists(), f"{base} is shipped now: drop its exemption"
            continue
        check_script(project / command, base, project, tmp_path, f"codex: {path.relative_to(project)}: {command}")
        ran.add(base)
    assert ran, "no command ran"


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via kit_snapshot]")
def test_claude_install_runs_every_command_by_the_dot_claude_path(tmp_path, kit_snapshot):
    project, out = real_install(tmp_path, kit_snapshot, CLAUDE_ANSWERS, "my claude project")
    assert (project / ".claude" / "skills").is_symlink() and not (project / ".codex").exists()
    for path, name, _, tail in skill_commands():
        base = os.path.basename(tail)
        if base in NOT_SHIPPED:
            assert not (project / "scripts" / base).exists(), f"{base} is shipped now: drop its exemption"
            continue
        script = project / ".claude" / "skills" / name / tail.lstrip("/")
        check_script(script, base, project, tmp_path, f"claude: {rel(path)}: {tail}")


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via kit_snapshot]")
def test_update_rewrites_the_codex_copies_again_and_reports_nothing_edited(tmp_path, kit_snapshot):
    project, _ = real_install(tmp_path, kit_snapshot, CODEX_ANSWERS, "my codex project")

    def codex_files():
        return {str(p.relative_to(project)): p.read_bytes()
                for p in (project / ".codex" / "skills").rglob("*") if p.is_file()}
    before = codex_files()
    done = real_update(project, kit_snapshot)
    assert done.returncode == 0, done.stdout + done.stderr
    text = re.sub(r"\x1b\[[0-9;]*m", "", done.stdout)
    assert "You edited these" in text
    assert re.search(r"kept as they are:\s*\n\s*\(none\)", text), text
    assert "Update complete" in text
    assert codex_files() == before, "a second run must change no Codex copy"
    assert not any(b"${CLAUDE_SKILL_DIR}" in data for data in before.values())


def test_board_init_from_a_plugin_works_on_the_cwd_and_never_writes_the_plugin(tmp_path):
    """`init` makes the first board config, so a folder with no board is its project (T235 owns the
    rest of init). It must not report "no project found", and must not touch the plugin folder."""
    plugin = make_plugin(tmp_path)
    empty = tmp_path / "empty folder"
    empty.mkdir()
    before = tree(plugin)
    result = run([plugin / "scripts" / "board_sync.py", "init"], empty)
    assert NO_PROJECT_TEXT not in result.stdout + result.stderr, (result.stdout, result.stderr)
    assert tree(plugin) == before
