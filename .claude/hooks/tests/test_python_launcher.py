#!/usr/bin/env python3
"""T275: a command a hook message tells the agent to run names a Python launcher that exists.

  AC 1 — `python_launcher()` (in `lib/project_root.py`): `python3` on POSIX; on `win32` `py -3`
         when `py` is on PATH, else `python`.
  AC 2 — both spawn-hook messages that name a script print exactly what they printed before on POSIX.
  AC 3 — with `sys.platform` patched to `win32`, both messages hold `py -3 <quoted path>` and no `python3`.
  AC 6 — `AGENTS.md` holds the one written rule for the instructions (2 to 3 lines).
  AC 7 — no hook code builds a `python3 <command>` string for the agent, except through the helper.

Windows itself cannot be run here: the `win32` cases patch `sys.platform` and `shutil.which` in a
child process that runs the real hook. Re-run this file on Windows to see the real launcher.

Run with: python3 -m pytest .claude/hooks/tests/test_python_launcher.py -q
"""
import ast
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import textwrap

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
HOOK = os.path.join(HOOKS_DIR, "pre_agent_validate_guide.py")
LIB = os.path.join(HOOKS_DIR, "lib", "project_root.py")
BOARD_SYNC = os.path.join(ROOT, "scripts", "board_sync.py")
MEMORY_SLICE = os.path.join(ROOT, "skills", "craft-spawn-prompt", "scripts", "memory_slice.py")

spec = importlib.util.spec_from_file_location("project_root_t275", LIB)
project_root_lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_root_lib)


# --- AC 1: the helper -----------------------------------------------------------------------

def test_launcher_is_python3_on_posix(monkeypatch):
    for platform in ("linux", "darwin"):
        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setattr("shutil.which", lambda name, *a, **k: "/usr/bin/py")  # never asked on POSIX
        assert project_root_lib.python_launcher() == "python3"


def test_launcher_is_py_3_on_windows_when_py_is_on_path(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("shutil.which", lambda name, *a, **k: "C:\\Windows\\py.exe" if name == "py" else None)
    assert project_root_lib.python_launcher() == "py -3"


def test_launcher_is_python_on_windows_when_py_is_absent(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("shutil.which", lambda name, *a, **k: None)
    assert project_root_lib.python_launcher() == "python"


# --- AC 2 and 3: the two spawn-hook messages ------------------------------------------------

INCOMPLETE_GUIDE = "# TASK_GUIDE — T900: x\n"
OLD_BLOCK_REASON = (
    "[hook:pre_agent] Cannot spawn agent — incomplete TASK_GUIDE for: T900 (missing: Requirement, "
    "Acceptance Criteria, Verification Command). Fill those sections first (Stage 2); in board mode "
    "push them with `python3 {script} update --guide <ID>`."
)
OLD_SLICE_BULLET = (
    "Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none "
    "of the memory lines its task touches. Run `python3 {script} <guide>` and paste its output "
    "verbatim (craft-spawn-prompt element 4)."
)

WRAPPER = textwrap.dedent("""
    import runpy, shutil, sys
    platform, py_found, hook = sys.argv[1:4]
    if platform != "real":
        sys.platform = platform
    if py_found != "real":
        shutil.which = lambda name, *a, **k: ("C:\\\\Windows\\\\py.exe" if name == "py" and py_found == "yes" else None)
    sys.argv = [hook]
    runpy.run_path(hook, run_name="__main__")
""")


def spawn(tmp_path, guide_text, platform="real", py_found="real"):
    """Run the real spawn hook for a prompt naming T900. Returns its JSON output."""
    project = tmp_path / "project"
    (project / "tasks").mkdir(parents=True, exist_ok=True)
    (project / "PROJECT_KANBAN.md").write_text("# Board\n")
    (project / "tasks" / "TASK_GUIDE_T900.md").write_text(guide_text, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_ACTIVE_TASK", "LINEAR_API_KEY")}
    env["CLAUDE_PROJECT_DIR"] = str(project)
    event = {"tool_name": "Agent", "session_id": "s1",
             "tool_input": {"prompt": "Task ID: T900\nRead tasks/TASK_GUIDE_T900.md"}}
    result = subprocess.run([sys.executable, "-c", WRAPPER, platform, py_found, HOOK],
                            input=json.dumps(event), capture_output=True, text=True,
                            cwd=str(project), env=env, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def complete_guide():
    with open(os.path.join(ROOT, "tasks", "TASK_GUIDE_T234.md"), encoding="utf-8") as handle:
        return handle.read()


def block_reason(tmp_path, **kw):
    return spawn(tmp_path, INCOMPLETE_GUIDE, **kw)["reason"]


def slice_bullet(tmp_path, **kw):
    context = spawn(tmp_path, complete_guide(), **kw)["hookSpecificOutput"]["additionalContext"]
    return next(line for line in context.splitlines() if "memory-slice" in line)


def test_posix_block_message_is_byte_identical_to_before(tmp_path):
    expected = OLD_BLOCK_REASON.format(script=shlex.quote(BOARD_SYNC))
    assert block_reason(tmp_path, platform="linux") == expected


def test_posix_memory_slice_message_is_byte_identical_to_before(tmp_path):
    expected = "  • " + OLD_SLICE_BULLET.format(script=shlex.quote(MEMORY_SLICE))
    assert slice_bullet(tmp_path, platform="linux") == expected


def test_windows_with_py_names_py_3_in_both_messages(tmp_path):
    blocked = block_reason(tmp_path, platform="win32", py_found="yes")
    assert f"`py -3 {shlex.quote(BOARD_SYNC)} update --guide <ID>`" in blocked
    assert "python3" not in blocked
    bullet = slice_bullet(tmp_path, platform="win32", py_found="yes")
    assert f"`py -3 {shlex.quote(MEMORY_SLICE)} <guide>`" in bullet
    assert "python3" not in bullet


def test_windows_without_py_names_python_in_both_messages(tmp_path):
    blocked = block_reason(tmp_path, platform="win32", py_found="no")
    assert f"`python {shlex.quote(BOARD_SYNC)} update --guide <ID>`" in blocked
    assert "python3" not in blocked
    bullet = slice_bullet(tmp_path, platform="win32", py_found="no")
    assert f"`python {shlex.quote(MEMORY_SLICE)} <guide>`" in bullet
    assert "python3" not in bullet


# --- AC 6: the written rule -----------------------------------------------------------------

def test_agents_md_holds_the_python_launcher_rule():
    with open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    start = lines.index("## Permanent Rules")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("#"))
    rule = [i for i in range(start, end) if "Windows" in lines[i]]
    assert len(rule) == 1, "the Permanent Rules hold exactly one Windows launcher rule"
    block = [lines[rule[0]]]
    for line in lines[rule[0] + 1:end]:
        if not line.startswith("  "):
            break
        block.append(line)
    text = " ".join(block)
    assert 2 <= len(block) <= 3, "the rule is 2 to 3 lines"
    for word in ("`python3`", "`py -3`", "`python`", "`py`"):
        assert word in text, f"the rule must name {word}"


# --- AC 7: no other hook message builds `python3 <command>` -----------------------------------

def _string_constants(tree):
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node


# One reason per entry. A note written into a generated file is no message to the agent, and a
# launcher in it would make the file differ per system (its golden fixture is byte-pinned).
NOTE_NOT_A_MESSAGE = {
    ".claude/hooks/lib/board/render.py":
        "HEADER is a static note in the generated PROJECT_KANBAN.md; the AGENTS.md rule covers it",
}


def test_no_hook_code_builds_a_python3_command_string():
    found = []
    for base, _dirs, names in os.walk(HOOKS_DIR):
        if os.path.basename(base) in ("tests", "__pycache__"):
            continue
        for name in sorted(n for n in names if n.endswith(".py")):
            path = os.path.join(base, name)
            if os.path.relpath(path, ROOT).replace(os.sep, "/") in NOTE_NOT_A_MESSAGE:
                continue
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in _string_constants(tree):
                if "python3 " in node.value:
                    found.append(f"{os.path.relpath(path, ROOT)}:{node.lineno}: {node.value[:70]!r}")
    assert not found, "a hook builds `python3 <command>` for the agent; use python_launcher():\n" + "\n".join(found)


def test_the_scan_catches_a_python3_command_string():
    tree = ast.parse('msg = f"Run `python3 {path}` first"\n')
    assert [n for n in _string_constants(tree) if "python3 " in n.value]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
