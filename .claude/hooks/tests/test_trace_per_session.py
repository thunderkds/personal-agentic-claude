#!/usr/bin/env python3
"""T196 AC 7: incident replay — two live callers, one checkout, no crossings.

The 2026-10-28 incident (`PROJECT_KANBAN.md` row T196): the T190 sub-agent wrote the shared
`.claude/hooks/.state/active_task` with `T190`; six minutes later another live session overwrote it
with `T188`. From then on every `Bash` call the T190 agent made was filed in `T188.jsonl` (89 records),
so `pre_bash_block_unsafe_merge.py:trace_shows_verification("T188")` was satisfied by T190's test run
without anyone lying.

This replays that shape through the real `post_tool_trace.py` (a subprocess, event JSON on stdin,
the way the harness runs it) and the real gate function:

  * session A's **sub-agent** — the event carries `agent_id`, and its transcript's first line is a
    spawn prompt with `Task ID: T190` (layout F3 in `tasks/TASK_GUIDE_T196.md`);
  * session B's **main session** — no `agent_id`, per-session state file says `T188`.

Both callers also wrote the old shared file, in the incident's order (T190, then T188), as the
instructions of the time told them to. A fixed resolver must ignore it (D2).

Run with: python3 -m pytest .claude/hooks/tests/test_trace_per_session.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOREIGN_CWD = tempfile.gettempdir()

SESSION_A = "5f0c1d2e-aaaa-4bbb-8ccc-000000000a01"
AGENT_A = "a54df34ef9d22bed6"
SESSION_B = "5f0c1d2e-aaaa-4bbb-8ccc-000000000b02"

SPAWN_PROMPT_A = (
    "Task ID: T190\n"
    "Guide: `tasks/TASK_GUIDE_T190.md` (read it in your worktree)\n"
    "memory slice: - T188 merged: minimal-track verify line\n"
)

# Interleaved as on 2026-10-28: A's test run lands *after* B's overwrite of the shared file.
CALLS = [
    ("A", "cd /w/wt-t190-gate && git status"),
    ("B", "cd /w/wt-t188 && git log --oneline -1"),
    ("A", "cd /w/wt-t190-gate && python3 -m pytest -q .claude/hooks/tests/"),
    ("B", "cd /w/wt-t188 && ls tasks/"),
    ("A", "cd /w/wt-t190-gate && git diff --stat"),
]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_merge_gate_module():
    """The gate without its bottom-of-file `main()` (same technique as test_task_context.py)."""
    path = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType("pre_bash_block_unsafe_merge")
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


class Checkout:
    """One throwaway checkout: the real trace hook + lib, a state dir, a transcripts dir."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="t196_replay_")
        hooks = os.path.join(self.root, ".claude", "hooks")
        os.makedirs(hooks)
        shutil.copy(os.path.join(HOOKS_DIR, "post_tool_trace.py"), hooks)
        shutil.copytree(os.path.join(HOOKS_DIR, "lib"), os.path.join(hooks, "lib"))
        self.hook = os.path.join(hooks, "post_tool_trace.py")
        self.state_dir = os.path.join(hooks, ".state")
        self.trace_dir = os.path.join(self.root, "memory", "event-trace")
        self.transcripts = os.path.join(self.root, "projects", "-w")
        os.makedirs(self.state_dir)
        os.makedirs(self.transcripts)
        self.anchor_dir = os.path.join(self.root, "anchors")

    def transcript_path(self, session_id):
        return os.path.join(self.transcripts, f"{session_id}.jsonl")

    def write_spawn_transcript(self, session_id, agent_id, prompt):
        sub = os.path.join(self.transcripts, session_id, "subagents")
        os.makedirs(sub, exist_ok=True)
        first = {"type": "user", "message": {"role": "user", "content": prompt},
                 "isSidechain": True, "agentId": agent_id, "sessionId": session_id}
        with open(os.path.join(sub, f"agent-{agent_id}.jsonl"), "w") as f:
            f.write(json.dumps(first) + "\n")

    def write_shared_file(self, task_id):
        with open(os.path.join(self.state_dir, "active_task"), "w") as f:
            f.write(f"{task_id}\n{_now()}\n")

    def write_session_file(self, session_id, task_id):
        d = os.path.join(self.state_dir, "active_task.d")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, session_id), "w") as f:
            f.write(f"{task_id}\n{_now()}\n")

    def bash(self, session_id, command, agent_id=None):
        event = {"session_id": session_id, "transcript_path": self.transcript_path(session_id),
                 "cwd": FOREIGN_CWD, "hook_event_name": "PostToolUse", "tool_name": "Bash",
                 "tool_input": {"command": command}, "tool_response": {"is_error": False}}
        if agent_id:
            event["agent_id"] = agent_id
            event["agent_type"] = "common-infrastructure"
        env = dict(os.environ)
        env.pop("CLAUDE_ACTIVE_TASK", None)
        env["CLAUDE_PROJECT_DIR"] = self.root
        env["CLAUDE_TRACE_ANCHOR_DIR"] = self.anchor_dir
        result = subprocess.run([sys.executable, self.hook], input=json.dumps(event),
                                capture_output=True, text=True, cwd=FOREIGN_CWD, env=env)
        assert result.returncode == 0, result.stderr

    def commands_in(self, task_file):
        path = os.path.join(self.trace_dir, task_file)
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(json.loads(line)["summary"])["command"] for line in f if line.strip()]

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def test_ac7_incident_replay_has_no_crossings_and_t188_is_not_verified_by_t190():
    co = Checkout()
    try:
        co.write_spawn_transcript(SESSION_A, AGENT_A, SPAWN_PROMPT_A)
        co.write_shared_file("T190")             # 05:34:10Z — the T190 agent, old instruction
        co.write_shared_file("T188")             # 05:40:25Z — session B overwrites it
        co.write_session_file(SESSION_B, "T188")  # session B, the D5 instruction

        for who, command in CALLS:
            if who == "A":
                co.bash(SESSION_A, command, agent_id=AGENT_A)
            else:
                co.bash(SESSION_B, command)

        a_calls = [c for who, c in CALLS if who == "A"]
        b_calls = [c for who, c in CALLS if who == "B"]
        in_t190, in_t188 = co.commands_in("T190.jsonl"), co.commands_in("T188.jsonl")
        crossings = ([c for c in in_t188 if "wt-t190-gate" in c]
                     + [c for c in in_t190 if "wt-t188" in c])
        print(f"T190.jsonl: {in_t190}\nT188.jsonl: {in_t188}\ncrossings: {len(crossings)}")

        gate = _load_merge_gate_module()
        gate.TRACE_DIR = co.trace_dir
        t188_verified = gate.trace_shows_verification("T188")
        print(f"trace_shows_verification('T188') = {t188_verified}")

        assert crossings == [], f"{len(crossings)} crossing(s): {crossings}"
        assert in_t190 == a_calls
        assert in_t188 == b_calls
        assert t188_verified is False, "T188 is verified by T190's test run"
        assert gate.trace_shows_verification("T190") is True
    finally:
        co.cleanup()
