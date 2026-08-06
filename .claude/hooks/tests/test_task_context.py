#!/usr/bin/env python3
"""Regression tests for T043: task attribution in post_tool_trace.py and
pre_agent_step_limit.py.

Bug: both hooks resolved "which task is this tool call about?" with a bare
`re.search(r"\\bT\\d{3}\\b", ...)` over the whole tool payload —
`post_tool_trace.py` over `tool_input` + `tool_response` combined,
`pre_agent_step_limit.py` over `tool_input`. So merely *reading* a file whose
body happens to contain a task ID filed the trace record under that ID, and an
`Edit` whose prose mentioned an old task ID counted a step against it (and could
block on the limit).

Attribution must come from a **structural** signal — a `TASK_GUIDE_Txxx.md` path
in a path-valued field, an `Agent` spawn prompt's structural reference, or the
`CLAUDE_ACTIVE_TASK` env var — never from free text.

These tests drive the real hooks end-to-end the way the harness does: event JSON
on stdin, over a subprocess, invoked **from a different cwd** so an import-path
failure in the real invocation shape cannot hide behind a direct import.
Each test copies the hooks (and `lib/`) into an isolated temp tree
(`<tmp>/.claude/hooks/...`) because each hook resolves its own ROOT from
`__file__` — this keeps the real repo's `memory/event-trace/` and
`.claude/hooks/.state/` untouched.

Run with: python3 -m pytest .claude/hooks/tests/test_task_context.py -v
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_PATH = os.path.join(HOOKS_DIR, "lib", "task_context.py")

_spec = importlib.util.spec_from_file_location("task_context", LIB_PATH)
task_context = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(task_context)

# Deliberately not the repo root and not the sandbox: running the hook from an
# unrelated cwd is what proves the lib import resolves off __file__, not off cwd.
FOREIGN_CWD = tempfile.gettempdir()

# A real record line copied verbatim from memory/event-trace/T001.jsonl as it
# existed *before* this change — the byte-compatibility fixture for AC8.
PRE_CHANGE_TRACE_LINE = (
    '{"timestamp": "2026-07-23T04:01:23.954543+00:00", "tool_name": "Read", '
    '"summary": "{\\"file_path\\": \\"/home/x/.claude/agents/general-agent-template.md\\"}", '
    '"is_error": false}'
)


class HookSandbox:
    """Isolated <tmp>/.claude/hooks/ tree so each hook's own ROOT resolution
    (three dirs up from __file__) lands in a throwaway directory."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="t043_hook_sandbox_")
        self.hooks_dir = os.path.join(self.root, ".claude", "hooks")
        os.makedirs(self.hooks_dir)
        for name in ("post_tool_trace.py", "pre_agent_step_limit.py"):
            shutil.copy(os.path.join(HOOKS_DIR, name), os.path.join(self.hooks_dir, name))
        lib_src = os.path.join(HOOKS_DIR, "lib")
        if os.path.isdir(lib_src):
            shutil.copytree(lib_src, os.path.join(self.hooks_dir, "lib"))
        self.trace_dir = os.path.join(self.root, "memory", "event-trace")
        self.state_dir = os.path.join(self.hooks_dir, ".state")

    def run_hook(self, hook_name, event, env_extra=None):
        env = dict(os.environ)
        env.pop("CLAUDE_ACTIVE_TASK", None)
        env.pop("CLAUDE_STEP_LIMIT", None)
        env.update(env_extra or {})
        payload = event if isinstance(event, str) else json.dumps(event)
        return subprocess.run(
            [sys.executable, os.path.join(self.hooks_dir, hook_name)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=FOREIGN_CWD,
            env=env,
        )

    def trace_files(self):
        if not os.path.isdir(self.trace_dir):
            return []
        return sorted(os.listdir(self.trace_dir))

    def trace_records(self, filename):
        path = os.path.join(self.trace_dir, filename)
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def counter_files(self):
        if not os.path.isdir(self.state_dir):
            return []
        return sorted(os.listdir(self.state_dir))

    def counter_value(self, task_id, session="nosession"):
        """T057: the counter file is now two lines (count\nblock_count).
        These tests are about attribution, not file format, so return the
        count only — line 2 is asserted by the T057 suite itself."""
        with open(os.path.join(self.state_dir, f"step_count_{session}_{task_id}.txt")) as f:
            return f.read().strip().splitlines()[0]

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


READ_KANBAN_EVENT = {
    "tool_name": "Read",
    "tool_input": {"file_path": "PROJECT_KANBAN.md"},
    "tool_response": {"content": "- [x] **T001** setup.sh + MANIFEST | Completed"},
}

EDIT_PROSE_EVENT = {
    "tool_name": "Edit",
    "tool_input": {
        "file_path": "memory/learnings.md",
        "old_string": "old text",
        "new_string": "Same regex class as in T028 — see the decision log.",
    },
}


# ---------------------------------------------------------------------------
# SC1 / AC2 — tool_response is never an attribution source
# ---------------------------------------------------------------------------

def test_read_of_file_whose_body_mentions_a_task_id_is_untagged():
    """The verified trace defect: reading PROJECT_KANBAN.md filed the record
    under whichever task ID appeared first in the file body, because the body
    arrives in tool_response."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", READ_KANBAN_EVENT)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], (
            f"expected only _untagged.jsonl, got {sandbox.trace_files()}"
        )
        records = sandbox.trace_records("_untagged.jsonl")
        assert len(records) == 1, records
        assert records[0]["tool_name"] == "Read", records[0]
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# SC2 / AC4 — prose mentions never attribute (step-limit false positive)
# ---------------------------------------------------------------------------

def test_edit_whose_prose_mentions_a_task_id_counts_no_step():
    """The documented step-limit false positive: an Edit whose *text* mentions
    an old task ID incremented that task's counter (and could block on it)."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("pre_agent_step_limit.py", EDIT_PROSE_EVENT)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "", result.stdout
        assert sandbox.counter_files() == [], sandbox.counter_files()
    finally:
        sandbox.cleanup()


def test_edit_whose_prose_mentions_a_task_id_is_untagged_in_the_trace():
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", EDIT_PROSE_EVENT)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], sandbox.trace_files()
    finally:
        sandbox.cleanup()


def test_bash_command_mentioning_a_task_id_is_not_attributed():
    """`command` is free text, not a path-valued field."""
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": "grep -n 'T017' memory/learnings.md"},
    }
    sandbox = HookSandbox()
    try:
        trace = sandbox.run_hook("post_tool_trace.py", event)
        assert trace.returncode == 0, trace.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], sandbox.trace_files()

        limit = sandbox.run_hook("pre_agent_step_limit.py", event)
        assert limit.returncode == 0, limit.stderr
        assert sandbox.counter_files() == [], sandbox.counter_files()
    finally:
        sandbox.cleanup()


def test_bash_command_containing_a_guide_path_is_not_attributed():
    """Documented decision (task_context module docstring): a Bash `command`
    string is never scanned, even when it legitimately contains a guide path —
    scanning command text is exactly the defect being removed."""
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": "cat tasks/TASK_GUIDE_T012.md"},
    }
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], sandbox.trace_files()
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# SC3 / AC7 — the Agent-spawn path still attributes
# ---------------------------------------------------------------------------

AGENT_SPAWN_EVENT = {
    "tool_name": "Agent",
    "tool_input": {
        "subagent_type": "common-infrastructure",
        "prompt": (
            "Task ID: T099\n\nYour task guide is `tasks/TASK_GUIDE_T099.md`.\n\n"
            "memory/MEMORY.md (hot tier):\n- T001 setup.sh + MANIFEST\n"
        ),
    },
}


def test_agent_spawn_prompt_guide_path_attributes_in_both_hooks():
    sandbox = HookSandbox()
    try:
        trace = sandbox.run_hook("post_tool_trace.py", AGENT_SPAWN_EVENT)
        assert trace.returncode == 0, trace.stderr
        assert sandbox.trace_files() == ["T099.jsonl"], sandbox.trace_files()

        limit = sandbox.run_hook("pre_agent_step_limit.py", AGENT_SPAWN_EVENT)
        assert limit.returncode == 0, limit.stderr
        assert sandbox.counter_files() == ["step_count_nosession_T099.txt"], sandbox.counter_files()
        assert sandbox.counter_value("T099") == "1"
    finally:
        sandbox.cleanup()


def test_prompt_field_of_a_non_agent_tool_is_not_scanned():
    """Only `Agent` spawns carry a task-scoped prompt; any other tool's
    `prompt`-ish field is free text."""
    event = {
        "tool_name": "Read",
        "tool_input": {
            "file_path": "README.md",
            "prompt": "see tasks/TASK_GUIDE_T099.md",
        },
    }
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], sandbox.trace_files()
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# SC4 / AC3(a) — CLAUDE_ACTIVE_TASK overrides everything
# ---------------------------------------------------------------------------

def test_env_override_wins_over_payload_text():
    sandbox = HookSandbox()
    try:
        trace = sandbox.run_hook(
            "post_tool_trace.py", READ_KANBAN_EVENT, {"CLAUDE_ACTIVE_TASK": "T099"}
        )
        assert trace.returncode == 0, trace.stderr
        assert sandbox.trace_files() == ["T099.jsonl"], sandbox.trace_files()

        limit = sandbox.run_hook(
            "pre_agent_step_limit.py", EDIT_PROSE_EVENT, {"CLAUDE_ACTIVE_TASK": "T099"}
        )
        assert limit.returncode == 0, limit.stderr
        assert sandbox.counter_files() == ["step_count_nosession_T099.txt"], sandbox.counter_files()
    finally:
        sandbox.cleanup()


def test_malformed_env_override_is_ignored_not_trusted():
    """A junk CLAUDE_ACTIVE_TASK must degrade to unattributed — it is also the
    only attacker-controllable input that reaches a file name."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook(
            "post_tool_trace.py",
            {"tool_name": "Read", "tool_input": {"file_path": "README.md"}},
            {"CLAUDE_ACTIVE_TASK": "../../etc/passwd"},
        )
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], sandbox.trace_files()
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# AC3(b) — a guide path in a path-valued field is a real structural signal
# ---------------------------------------------------------------------------

def test_write_of_a_new_task_guide_attributes_via_file_path():
    """Edge case from the guide: writing tasks/TASK_GUIDE_T044.md is how new
    guides get traced — it must keep working."""
    event = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/home/x/repo/tasks/TASK_GUIDE_T044.md",
            "content": "# TASK_GUIDE — T044\nSee also T001 and T017.\n",
        },
    }
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["T044.jsonl"], sandbox.trace_files()
    finally:
        sandbox.cleanup()


def test_lowercase_guide_path_normalizes_to_the_same_bucket():
    """`t044` in a path must not silently become a different bucket."""
    event = {
        "tool_name": "Read",
        "tool_input": {"file_path": "tasks/task_guide_t044.md"},
    }
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["T044.jsonl"], sandbox.trace_files()
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# SC5 — fail-open contract
# ---------------------------------------------------------------------------

def test_malformed_stdin_exits_zero_silently_in_both_hooks():
    sandbox = HookSandbox()
    try:
        for hook in ("post_tool_trace.py", "pre_agent_step_limit.py"):
            result = sandbox.run_hook(hook, "this is not json {")
            assert result.returncode == 0, (hook, result.returncode, result.stderr)
            assert result.stdout.strip() == "", (hook, result.stdout)
            assert result.stderr.strip() == "", (hook, result.stderr)
    finally:
        sandbox.cleanup()


def test_empty_stdin_exits_zero_silently_in_both_hooks():
    sandbox = HookSandbox()
    try:
        for hook in ("post_tool_trace.py", "pre_agent_step_limit.py"):
            result = sandbox.run_hook(hook, "")
            assert result.returncode == 0, (hook, result.returncode, result.stderr)
            assert result.stderr.strip() == "", (hook, result.stderr)
    finally:
        sandbox.cleanup()


def test_non_dict_tool_input_does_not_crash_either_hook():
    sandbox = HookSandbox()
    try:
        for hook in ("post_tool_trace.py", "pre_agent_step_limit.py"):
            result = sandbox.run_hook(hook, {"tool_name": "Weird", "tool_input": "T017"})
            assert result.returncode == 0, (hook, result.returncode, result.stderr)
            assert result.stderr.strip() == "", (hook, result.stderr)
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# SC6 / AC8 — the trace record schema is byte-compatible
# ---------------------------------------------------------------------------

def test_trace_record_schema_matches_pre_change_records():
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", READ_KANBAN_EVENT)
        assert result.returncode == 0, result.stderr
        new_record = sandbox.trace_records("_untagged.jsonl")[0]
        old_record = json.loads(PRE_CHANGE_TRACE_LINE)
        assert set(new_record) == set(old_record), (set(new_record), set(old_record))
        assert set(new_record) == {"timestamp", "tool_name", "summary", "is_error"}
        for key in old_record:
            assert type(new_record[key]) is type(old_record[key]), key
    finally:
        sandbox.cleanup()


def test_is_error_is_still_read_from_tool_response():
    """tool_response stops being an *attribution* source; it is still the
    source of the is_error flag."""
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": "false"},
        "tool_response": {"is_error": True, "content": "boom"},
    }
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        record = sandbox.trace_records("_untagged.jsonl")[0]
        assert record["is_error"] is True, record
    finally:
        sandbox.cleanup()


def test_summary_is_still_the_truncated_tool_input_json():
    event = {
        "tool_name": "Read",
        "tool_input": {"file_path": "README.md"},
        "tool_response": {"content": "x" * 5000},
    }
    sandbox = HookSandbox()
    try:
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        record = sandbox.trace_records("_untagged.jsonl")[0]
        assert record["summary"] == json.dumps({"file_path": "README.md"}), record
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# AC6 — the step-limit guardrail itself must survive the attribution fix
# ---------------------------------------------------------------------------

def test_step_limit_still_blocks_once_an_attributed_task_exceeds_the_limit():
    sandbox = HookSandbox()
    env = {"CLAUDE_ACTIVE_TASK": "T099", "CLAUDE_STEP_LIMIT": "2"}
    try:
        first = sandbox.run_hook("pre_agent_step_limit.py", EDIT_PROSE_EVENT, env)
        second = sandbox.run_hook("pre_agent_step_limit.py", EDIT_PROSE_EVENT, env)
        assert first.stdout.strip() == "", first.stdout
        assert second.stdout.strip() == "", second.stdout

        third = sandbox.run_hook("pre_agent_step_limit.py", EDIT_PROSE_EVENT, env)
        decision = json.loads(third.stdout)
        assert decision["decision"] == "block", decision
        assert "T099" in decision["reason"], decision
        # T057: the blocking call now resets the counter in the same
        # invocation, so it reads 0 rather than continuing to climb. The
        # property this test protects -- that an attributed task IS blocked
        # once it exceeds the limit -- is asserted just above and still holds.
        assert sandbox.counter_value("T099") == "0"
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# AC1 / AC3 — resolve_task_id precedence, unit level
# ---------------------------------------------------------------------------

class EnvOverride:
    """Set/clear CLAUDE_ACTIVE_TASK for the duration of a block."""

    def __init__(self, value):
        self.value = value
        self.previous = None

    def __enter__(self):
        self.previous = os.environ.get(task_context.ENV_VAR)
        if self.value is None:
            os.environ.pop(task_context.ENV_VAR, None)
        else:
            os.environ[task_context.ENV_VAR] = self.value
        return self

    def __exit__(self, *exc):
        if self.previous is None:
            os.environ.pop(task_context.ENV_VAR, None)
        else:
            os.environ[task_context.ENV_VAR] = self.previous
        return False


def resolve(event, env=None):
    with EnvOverride(env):
        return task_context.resolve_task_id(event)


def test_env_var_takes_precedence_over_a_guide_path():
    event = {"tool_name": "Read", "tool_input": {"file_path": "tasks/TASK_GUIDE_T044.md"}}
    assert resolve(event, "T099") == "T099"
    assert resolve(event, None) == "T044"


def test_env_var_is_case_insensitive_and_normalized():
    event = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    assert resolve(event, "t099") == "T099"
    assert resolve(event, " T099 ") == "T099"


def test_malformed_env_var_values_are_ignored():
    event = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    for junk in ("", "T99", "T0999", "task-99", "../../etc/passwd", "T099 T100", "099"):
        assert resolve(event, junk) is None, junk


def test_only_path_valued_fields_are_scanned():
    for field in task_context.PATH_FIELDS:
        event = {"tool_name": "Read", "tool_input": {field: "tasks/TASK_GUIDE_T044.md"}}
        assert resolve(event) == "T044", field

    for field in ("command", "content", "new_string", "old_string", "description", "pattern"):
        event = {"tool_name": "Bash", "tool_input": {field: "tasks/TASK_GUIDE_T044.md"}}
        assert resolve(event) is None, field


def test_path_fields_are_scanned_in_declared_order():
    event = {
        "tool_name": "NotebookEdit",
        "tool_input": {
            "notebook_path": "tasks/TASK_GUIDE_T044.md",
            "path": "tasks/TASK_GUIDE_T055.md",
        },
    }
    assert task_context.PATH_FIELDS.index("notebook_path") < task_context.PATH_FIELDS.index("path")
    assert resolve(event) == "T044"


def test_agent_prompt_structural_markers_are_recognized():
    for prompt in (
        "Your task guide is `tasks/TASK_GUIDE_T099.md`.",
        "Task ID: T099",
        "**Task ID**: T099",
        "Read tasks/TASK_GUIDE_T099_EXTRA.md first.",
    ):
        event = {"tool_name": "Agent", "tool_input": {"prompt": prompt}}
        assert resolve(event) == "T099", prompt


def test_agent_prompt_prose_mention_is_not_a_structural_marker():
    """The MEMORY.md-paste landmine: a spawn prompt always carries the whole
    hot-tier memory index, which is full of prose task IDs."""
    event = {
        "tool_name": "Agent",
        "tool_input": {
            "prompt": (
                "memory/MEMORY.md (hot tier):\n"
                "- T042 merged: register-hook metadata regexes\n"
                "- T039 merged: CLAUDE.md Skills-vs-Agents dedup\n"
            )
        },
    }
    assert resolve(event) is None


def test_prompt_is_only_scanned_for_agent_calls():
    tool_input = {"prompt": "Task ID: T099"}
    assert resolve({"tool_name": "Agent", "tool_input": tool_input}) == "T099"
    assert resolve({"tool_name": "Read", "tool_input": tool_input}) is None


def test_task_ids_are_normalized_to_three_digits_upper_case():
    assert task_context.normalize_task_id("44") == "T044"
    assert task_context.normalize_task_id("044") == "T044"
    event = {"tool_name": "Read", "tool_input": {"file_path": "tasks/task_guide_t44.md"}}
    assert resolve(event) == "T044"


def test_resolve_never_raises_on_malformed_events():
    for event in (None, "", 42, [], {}, {"tool_input": None}, {"tool_input": "T017"},
                  {"tool_input": {"file_path": 17}},
                  {"tool_name": "Agent", "tool_input": {"prompt": None}}):
        assert resolve(event) is None, event


def test_neither_hook_defines_its_own_task_id_regex_any_more():
    """AC1: attribution lives in exactly one place."""
    for hook_name in ("post_tool_trace.py", "pre_agent_step_limit.py"):
        with open(os.path.join(HOOKS_DIR, hook_name)) as f:
            source = f.read()
        assert "def find_task_id" not in source, hook_name
        assert "T\\d{3}" not in source, hook_name
        assert "from task_context import resolve_task_id" in source, hook_name


# ---------------------------------------------------------------------------
# T047 — active-task state file: the channel a Bash tool call can actually
# write to from inside a running session. See task_context.py precedence
# slot 2 and the T047 report for the empirical probe this is grounded in.
# ---------------------------------------------------------------------------

import tempfile as _tempfile
import types as _types
from datetime import datetime, timedelta, timezone


def _load_merge_gate_module():
    """Load pre_bash_block_unsafe_merge.py without running its bottom-of-file
    `main()` (same technique as test_merge_gate_evidence.py's
    `load_hook_module`, duplicated here rather than imported to keep this
    file runnable standalone via its own __main__ block)."""
    path = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = _types.ModuleType("pre_bash_block_unsafe_merge")
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


class StateFileOverride:
    """Point task_context.ACTIVE_TASK_FILE at a throwaway path for the
    duration of a block, restoring it after. Unit-level equivalent of
    EnvOverride for the new state-file channel."""

    def __init__(self, content=None):
        self.content = content
        self.dir = None
        self.previous = None

    def __enter__(self):
        self.dir = _tempfile.mkdtemp(prefix="t047_state_")
        self.previous = task_context.ACTIVE_TASK_FILE
        task_context.ACTIVE_TASK_FILE = os.path.join(self.dir, "active_task")
        if self.content is not None:
            with open(task_context.ACTIVE_TASK_FILE, "w") as f:
                f.write(self.content)
        return self

    def __exit__(self, *exc):
        task_context.ACTIVE_TASK_FILE = self.previous
        shutil.rmtree(self.dir, ignore_errors=True)
        return False


# ---------------------------------------------------------------------------
# T048 — ambient-state isolation, applied by default to the whole suite.
#
# Without this, every in-process call to resolve_task_id() (via the
# `resolve()` helper above) reads the *real* module-level
# `task_context.ACTIVE_TASK_FILE`, which is exactly the path
# `craft-spawn-prompt` Element 6 now instructs every agent to arm. A test's
# outcome must not depend on whether that ambient file happens to exist on
# the machine running the suite (see module precedence slot 2 and the T048
# task guide). The nine pre-T047 tests below assert what the *lower*
# precedence slots resolve to; they were written before slot 2 existed and
# never isolated it, so a real armed file made slot 2 short-circuit them.
#
# Fix: wrap each *test function*, not each `resolve()` call, in a fresh
# `StateFileOverride()` (content=None -> points ACTIVE_TASK_FILE at an
# empty throwaway path). Tests that want to genuinely exercise slot 2 keep
# nesting their own `StateFileOverride(content=...)` *inside* this default
# — the innermost context wins for the duration of its `with` block, so
# explicit arming (and AC5's mutation control) is unaffected. This is the
# same mechanism T047 already proved correct for its own new tests, now
# applied suite-wide instead of opt-in per test (AC4) — not a second,
# competing isolation mechanism.
#
# Applied at two levels so both entry points documented in the module
# docstring behave identically:
#   - pytest: an autouse fixture, scoped to this module, wraps every test.
#   - `python3 test_task_context.py` direct execution: the __main__ runner
#     below wraps each manual test call with the identical StateFileOverride.
# ---------------------------------------------------------------------------

try:
    import pytest as _pytest

    @_pytest.fixture(autouse=True)
    def _isolate_ambient_active_task_state():
        with StateFileOverride():
            yield
except ImportError:
    _pytest = None


def _fresh_state_content(task_id, age_seconds=0):
    written_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    return f"{task_id}\n{written_at.isoformat()}\n"


def test_state_file_attributes_when_env_and_payload_are_silent():
    event = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}}
    with StateFileOverride(_fresh_state_content("T047")):
        assert resolve(event) == "T047"


def test_env_var_still_wins_over_state_file():
    event = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}}
    with StateFileOverride(_fresh_state_content("T047")):
        assert resolve(event, "T099") == "T099"


def test_state_file_wins_over_path_field_and_agent_prompt():
    event = {"tool_name": "Read", "tool_input": {"file_path": "tasks/TASK_GUIDE_T044.md"}}
    with StateFileOverride(_fresh_state_content("T047")):
        assert resolve(event) == "T047"


def test_missing_state_file_falls_through_to_next_slot():
    event = {"tool_name": "Read", "tool_input": {"file_path": "tasks/TASK_GUIDE_T044.md"}}
    with StateFileOverride(None):
        assert resolve(event) == "T044"


def test_malformed_state_file_content_is_ignored_not_trusted():
    """Negative control: junk task ID text must degrade to absent, exactly
    like a malformed CLAUDE_ACTIVE_TASK — never trusted as a literal path
    component."""
    event = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}}
    for junk in ("", "not-a-task\n2026-07-31T00:00:00+00:00\n", "T99\n2026-07-31T00:00:00+00:00\n",
                 "../../etc/passwd\n2026-07-31T00:00:00+00:00\n", "T047\n"):
        with StateFileOverride(junk):
            assert resolve(event) is None, repr(junk)


def test_stale_state_file_is_rejected():
    """The T043 mis-attribution class: a pointer left over from a finished
    task must not silently attribute a new task's work to the old one."""
    event = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}}
    with StateFileOverride(_fresh_state_content("T047", age_seconds=task_context.ACTIVE_TASK_MAX_AGE_S + 1)):
        assert resolve(event) is None


def test_state_file_at_exactly_the_age_boundary_is_still_fresh():
    event = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}}
    with StateFileOverride(_fresh_state_content("T047", age_seconds=task_context.ACTIVE_TASK_MAX_AGE_S - 1)):
        assert resolve(event) == "T047"


def test_state_file_corrupt_timestamp_degrades_to_absent():
    event = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}}
    with StateFileOverride("T047\nnot-a-timestamp\n"):
        assert resolve(event) is None


# ---------------------------------------------------------------------------
# T047 AC1/AC2 — real end-to-end path: a Bash tool call the way an agent
# actually issues one (structural signal on disk, never CLAUDE_ACTIVE_TASK
# passed inline), through the real hook subprocess, then a real
# trace_shows_verification check.
# ---------------------------------------------------------------------------

def test_end_to_end_bash_test_run_via_state_file_is_traced_and_verifies():
    """AC1 + AC2. Mirrors exactly how an agent issues a test command — the
    state file is written first (as craft-spawn-prompt now instructs), then
    a real `Bash` tool call event (no CLAUDE_ACTIVE_TASK on it at all) is
    fed through the real post_tool_trace.py subprocess."""
    sandbox = HookSandbox()
    try:
        os.makedirs(sandbox.state_dir, exist_ok=True)
        with open(os.path.join(sandbox.state_dir, "active_task"), "w") as f:
            f.write(_fresh_state_content("T047"))

        event = {
            "tool_name": "Bash",
            "tool_input": {"command": "python3 -m pytest .claude/hooks/tests/ -q"},
            "tool_response": {"is_error": False},
        }
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["T047.jsonl"], sandbox.trace_files()

        merge_gate = _load_merge_gate_module()
        merge_gate.TRACE_DIR = sandbox.trace_dir  # point the gate at the sandbox

        assert merge_gate.trace_shows_verification("T047") is True
    finally:
        sandbox.cleanup()


def test_state_file_resolves_off_claude_project_dir_not_the_executing_copy():
    """T047 Stage 4 P1 regression guard.

    The original fix resolved STATE_DIR off `__file__` arithmetic alone —
    correct only because, in production, the harness always execs the hook
    at exactly `$CLAUDE_PROJECT_DIR/.claude/hooks/*.py` (see settings.json),
    so `__file__` and `$CLAUDE_PROJECT_DIR` always happened to coincide. A
    Stage-3 sub-agent's cwd is its own *worktree*, and the corrected
    craft-spawn-prompt instruction writes the state file to an absolute
    path under the *main checkout* — a genuinely different directory from
    wherever `task_context.py`'s own `__file__` happens to sit if a copy is
    ever invoked from elsewhere (e.g. a worktree's own hook copy, run
    directly, or any subprocess context where `__file__` and
    `$CLAUDE_PROJECT_DIR` diverge). A test where both roots are the same
    directory (the original `HookSandbox` shape) cannot distinguish 'reads
    off $CLAUDE_PROJECT_DIR' from 'reads off __file__' — this test makes
    them two genuinely different directories so only the fixed code passes.

    Runs `task_context.py` itself as a subprocess (not through
    `post_tool_trace.py`, whose own `TRACE_DIR` is a separate, unrelated
    __file__-anchored constant this task did not touch) so it isolates
    exactly the STATE_DIR resolution this Stage-4 fix changed.
    """
    executing_copy_dir = _tempfile.mkdtemp(prefix="t047_executing_copy_")
    main_checkout_root = _tempfile.mkdtemp(prefix="t047_main_checkout_")
    try:
        assert executing_copy_dir != main_checkout_root

        # task_context.py physically lives 3 dirs below its own __file__'s
        # notion of ROOT: <root>/.claude/hooks/lib/task_context.py
        copy_lib_dir = os.path.join(executing_copy_dir, ".claude", "hooks", "lib")
        os.makedirs(copy_lib_dir)
        shutil.copy(LIB_PATH, os.path.join(copy_lib_dir, "task_context.py"))

        # The state file exists only under main_checkout_root — where the
        # corrected craft-spawn-prompt instruction actually writes it.
        main_state_dir = os.path.join(main_checkout_root, ".claude", "hooks", ".state")
        os.makedirs(main_state_dir)
        with open(os.path.join(main_state_dir, "active_task"), "w") as f:
            f.write(_fresh_state_content("T047"))

        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "import task_context\n"
            "print(task_context.resolve_task_id({'tool_name': 'Bash', "
            "'tool_input': {'command': 'python3 -m pytest -q'}}))\n"
        ) % copy_lib_dir

        env = dict(os.environ)
        env.pop("CLAUDE_ACTIVE_TASK", None)
        env["CLAUDE_PROJECT_DIR"] = main_checkout_root

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=executing_copy_dir,  # a third, unrelated cwd — not the answer either
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "T047", (
            "resolve_task_id must read the state file from $CLAUDE_PROJECT_DIR "
            f"(main_checkout_root), not from __file__'s own directory. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    finally:
        shutil.rmtree(executing_copy_dir, ignore_errors=True)
        shutil.rmtree(main_checkout_root, ignore_errors=True)


def test_end_to_end_no_state_file_and_no_test_run_stays_untagged_and_fails_gate():
    """AC4 negative: a task with no state file set and no qualifying record
    still gets no verification credit."""
    sandbox = HookSandbox()
    try:
        event = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls tasks/"},
            "tool_response": {"is_error": False},
        }
        result = sandbox.run_hook("post_tool_trace.py", event)
        assert result.returncode == 0, result.stderr
        assert sandbox.trace_files() == ["_untagged.jsonl"], sandbox.trace_files()

        trace_path = os.path.join(sandbox.trace_dir, "T047.jsonl")
        assert not os.path.exists(trace_path)
    finally:
        sandbox.cleanup()


def test_malformed_max_age_env_var_does_not_disable_attribution():
    """T047 Stage 4 P1 regression guard.

    `ACTIVE_TASK_MAX_AGE_S` is resolved at *import* time — one layer below
    `resolve_task_id`'s never-raises contract. A bare `int(os.environ[...])`
    raises `ValueError` on a non-numeric value, and because both callers wrap
    `from task_context import ...` in `except Exception`, that would silently
    disable attribution repo-wide — including the path-field precedence that
    has nothing to do with this setting. Import must survive and fall back to
    the default.

    Runs as a real subprocess so the env var is present at genuine import
    time; setting it inside this process would be too late, the module is
    already imported.
    """
    root = _tempfile.mkdtemp(prefix="t047_maxage_")
    try:
        state_dir = os.path.join(root, ".claude", "hooks", ".state")
        os.makedirs(state_dir)
        with open(os.path.join(state_dir, "active_task"), "w") as f:
            f.write(_fresh_state_content("T047"))

        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "import task_context\n"
            "print(task_context.ACTIVE_TASK_MAX_AGE_S)\n"
            "print(task_context.resolve_task_id({'tool_name': 'Bash', "
            "'tool_input': {'command': 'python3 -m pytest -q'}}))\n"
        ) % os.path.join(HOOKS_DIR, "lib")

        for bad_value in ("6h", "", "not-a-number", "-1", "0"):
            env = dict(os.environ)
            env.pop("CLAUDE_ACTIVE_TASK", None)
            env["CLAUDE_PROJECT_DIR"] = root
            env["CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S"] = bad_value

            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True, text=True, env=env,
            )
            assert result.returncode == 0, (
                f"import raised for {bad_value!r}: {result.stderr}"
            )
            lines = result.stdout.strip().splitlines()
            assert lines[0] == "21600", (
                f"{bad_value!r} should fall back to the default, got {lines[0]}"
            )
            assert lines[1] == "T047", (
                f"attribution broke for {bad_value!r}: {lines[1]}"
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            # T048: same default isolation the pytest autouse fixture
            # applies, so this manual runner matches pytest's result
            # regardless of ambient .claude/hooks/.state/active_task.
            with StateFileOverride():
                t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        print(f"\n{failures} test(s) failed")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed")
