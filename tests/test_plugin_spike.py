"""
T216 — throwaway plugin spike (experiments/plugin-spike/).

AC1: `claude plugin validate` accepts the marketplace and the plugin.
AC2: the gate hook blocks the probe command only inside a kit project
     (a folder with PROJECT_KANBAN.md) and stays silent everywhere else.
AC3: the gate hook lets every other command through.
"""
import json
import os
import shutil
import subprocess
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPIKE = os.path.join(ROOT, "experiments", "plugin-spike")
PLUGIN = os.path.join(SPIKE, "ekspike")
GATE = os.path.join(PLUGIN, "hooks", "gate.py")


def run_gate(cwd, command):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    }
    env = dict(os.environ, CLAUDE_PLUGIN_DATA=tempfile.mkdtemp())
    return subprocess.run(
        ["python3", GATE], input=json.dumps(payload),
        capture_output=True, text=True, env=env,
    )


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
@pytest.mark.parametrize("path", [SPIKE, PLUGIN])
def test_claude_validates_marketplace_and_plugin(path):
    result = subprocess.run(
        ["claude", "plugin", "validate", path], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_gate_blocks_probe_in_kit_project():
    kit = tempfile.mkdtemp()
    open(os.path.join(kit, "PROJECT_KANBAN.md"), "w").close()
    result = run_gate(kit, "echo SPIKE_BLOCK_ME")
    assert result.returncode == 2
    assert "ekspike gate" in result.stderr


def test_gate_is_silent_outside_kit_project():
    result = run_gate(tempfile.mkdtemp(), "echo SPIKE_BLOCK_ME")
    assert result.returncode == 0
    assert result.stdout == "" and result.stderr == ""


def test_gate_allows_other_commands_in_kit_project():
    kit = tempfile.mkdtemp()
    open(os.path.join(kit, "PROJECT_KANBAN.md"), "w").close()
    assert run_gate(kit, "echo hello").returncode == 0
