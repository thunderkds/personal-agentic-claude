#!/usr/bin/env python3
"""T061: post_tool_trace.py captures per-spawn cost telemetry for `Agent`.

Before this change the hook read `tool_response` and used exactly one field of
it (`is_error`); everything the spawn reported about what it cost — tokens by
cache disposition, tool-call mix, lines changed, resolved model, duration — was
discarded. 45 Agent records already in `memory/event-trace/` carry only
`['timestamp', 'tool_name', 'summary', 'is_error']`.

The load-bearing test here is **AC4, the golden comparison**: `Agent` is a small
fraction of traced calls, so a regression in the common path would be invisible
without pinning it. It is checked two ways — against literal record lines
captured from the pre-change hook, and differentially against the pre-change
source itself recovered from git at `82883a2`.

Scope note: these tests drive the real hook over a subprocess with event JSON on
stdin, the way the harness does, but the Agent payload is a **fixture**, not a
live spawn — a test cannot spawn a sub-agent to produce a real `tool_response`.
The fixture is pinned to the field names and arm-B numbers of the 2026-08-07
probe capture recorded in TASK_GUIDE_T061.md, so it is not invented, but it is
also not end-to-end.

Run with: python3 -m pytest .claude/hooks/tests/test_post_tool_trace_spawn.py -v
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
PRE_CHANGE_REF = "82883a2"
HOOK_REL_PATH = ".claude/hooks/post_tool_trace.py"

FOREIGN_CWD = tempfile.gettempdir()

# Verbatim from TASK_GUIDE_T061.md's 2026-08-07 probe capture: the `tool_response`
# key set the harness genuinely sends for an `Agent` call, with arm B's measured
# numbers. `prompt`/`content`/`iterations` are present here on purpose — they are
# what AC5 requires the record NOT to carry.
AGENT_TOOL_RESPONSE = {
    "status": "completed",
    "agentId": "agent_01abc",
    "agentType": "common-infrastructure",
    "resolvedModel": "claude-sonnet-5",
    "content": "Done. Ran echo and reported back." * 20,
    "prompt": "Task ID: T061\nRun echo." * 40,
    "totalTokens": 16981,
    "totalToolUseCount": 1,
    "totalDurationMs": 6875,
    "usage": {
        "input_tokens": 2,
        "output_tokens": 3,
        "cache_creation_input_tokens": 404,
        "cache_read_input_tokens": 16572,
        "cache_creation": {"ephemeral_5m": 404, "ephemeral_1h": 0},
        "service_tier": "standard",
        "iterations": [{"input_tokens": 2}, {"input_tokens": 0}],
    },
    "toolStats": {
        "readCount": 0,
        "searchCount": 0,
        "bashCount": 1,
        "editFileCount": 0,
        "linesAdded": 0,
        "linesRemoved": 0,
        "otherToolCount": 0,
    },
}

AGENT_EVENT = {
    "tool_name": "Agent",
    "tool_input": {
        "subagent_type": "common-infrastructure",
        "prompt": "Task ID: T061\nSee tasks/TASK_GUIDE_T061.md",
    },
    "tool_response": AGENT_TOOL_RESPONSE,
}

# Non-Agent events for the golden comparison. Deliberately includes an event
# whose tool_response is an error and one attributed via a path field, so the
# golden covers both branches of the untouched code path.
GOLDEN_EVENTS = [
    {
        "tool_name": "Bash",
        "tool_input": {"command": "python3 -m pytest -q", "description": "run tests"},
        "tool_response": {"stdout": "220 passed", "is_error": False},
    },
    {
        "tool_name": "Read",
        "tool_input": {"file_path": "/x/tasks/TASK_GUIDE_T061.md"},
        "tool_response": {"content": "..."},
    },
    {
        "tool_name": "Bash",
        "tool_input": {"command": "false"},
        "tool_response": {"is_error": True},
    },
]

# Captured from the pre-change hook (identical to `82883a2`) on 2026-08-07,
# timestamps elided. Key order is part of the pin: these are compared as strings.
GOLDEN_LINES = {
    "T061.jsonl": [
        '{"timestamp": "<TS>", "tool_name": "Read", '
        '"summary": "{\\"file_path\\": \\"/x/tasks/TASK_GUIDE_T061.md\\"}", '
        '"is_error": false}'
    ],
    "_untagged.jsonl": [
        '{"timestamp": "<TS>", "tool_name": "Bash", '
        '"summary": "{\\"command\\": \\"python3 -m pytest -q\\", '
        '\\"description\\": \\"run tests\\"}", "is_error": false}',
        '{"timestamp": "<TS>", "tool_name": "Bash", '
        '"summary": "{\\"command\\": \\"false\\"}", "is_error": true}',
    ],
}

TIMESTAMP_RE = re.compile(r'"timestamp": "[^"]*"')


def elide_timestamp(line):
    return TIMESTAMP_RE.sub('"timestamp": "<TS>"', line)


class HookSandbox:
    """Isolated <tmp>/.claude/hooks/ tree — the hook resolves TRACE_DIR three
    dirs up from __file__, so this keeps the real repo's memory/event-trace/
    untouched. CLAUDE_PROJECT_DIR points at the sandbox too, so no ambient
    .state/active_task can reach attribution and make results machine-dependent.
    """

    def __init__(self, hook_source=None):
        self.root = tempfile.mkdtemp(prefix="t061_hook_sandbox_")
        self.hooks_dir = os.path.join(self.root, ".claude", "hooks")
        os.makedirs(self.hooks_dir)
        self.hook_path = os.path.join(self.hooks_dir, "post_tool_trace.py")
        if hook_source is None:
            shutil.copy(os.path.join(HOOKS_DIR, "post_tool_trace.py"), self.hook_path)
        else:
            with open(self.hook_path, "w") as f:
                f.write(hook_source)
        shutil.copytree(os.path.join(HOOKS_DIR, "lib"), os.path.join(self.hooks_dir, "lib"))
        self.trace_dir = os.path.join(self.root, "memory", "event-trace")

    def run_hook(self, event):
        env = dict(os.environ)
        env.pop("CLAUDE_ACTIVE_TASK", None)
        env["CLAUDE_PROJECT_DIR"] = self.root
        payload = event if isinstance(event, str) else json.dumps(event)
        return subprocess.run(
            [sys.executable, self.hook_path],
            input=payload,
            capture_output=True,
            text=True,
            cwd=FOREIGN_CWD,
            env=env,
        )

    def lines(self, filename):
        path = os.path.join(self.trace_dir, filename)
        with open(path) as f:
            return [line.rstrip("\n") for line in f if line.strip()]

    def records(self, filename):
        return [json.loads(line) for line in self.lines(filename)]

    def only_record(self, filename="T061.jsonl"):
        recs = self.records(filename)
        assert len(recs) == 1, recs
        return recs[0]

    def trace_files(self):
        if not os.path.isdir(self.trace_dir):
            return []
        return sorted(os.listdir(self.trace_dir))

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


@pytest.fixture
def sandbox():
    sb = HookSandbox()
    try:
        yield sb
    finally:
        sb.cleanup()


def run_agent_event(sb, tool_response, missing=False):
    event = dict(AGENT_EVENT)
    if missing:
        event.pop("tool_response", None)
    else:
        event["tool_response"] = tool_response
    result = sb.run_hook(event)
    assert result.returncode == 0, result.stderr
    return result


# ---------------------------------------------------------------------------
# AC1 / AC2 / AC3 — the spawn object and its two sub-objects
# ---------------------------------------------------------------------------

def test_agent_record_carries_spawn_top_level_cost_fields(sandbox):
    """AC1."""
    run_agent_event(sandbox, AGENT_TOOL_RESPONSE)
    spawn = sandbox.only_record()["spawn"]
    assert spawn["total_tokens"] == 16981
    assert spawn["tool_use_count"] == 1
    assert spawn["duration_ms"] == 6875
    assert spawn["resolved_model"] == "claude-sonnet-5"
    assert spawn["agent_type"] == "common-infrastructure"
    assert spawn["status"] == "completed"


def test_agent_record_carries_usage_split_by_cache_disposition(sandbox):
    """AC2."""
    run_agent_event(sandbox, AGENT_TOOL_RESPONSE)
    usage = sandbox.only_record()["spawn"]["usage"]
    assert usage == {
        "input_tokens": 2,
        "output_tokens": 3,
        "cache_creation_input_tokens": 404,
        "cache_read_input_tokens": 16572,
    }


def test_agent_record_carries_tool_stats(sandbox):
    """AC3."""
    run_agent_event(sandbox, AGENT_TOOL_RESPONSE)
    stats = sandbox.only_record()["spawn"]["tool_stats"]
    assert stats == {
        "read_count": 0,
        "search_count": 0,
        "bash_count": 1,
        "edit_file_count": 0,
        "lines_added": 0,
        "lines_removed": 0,
    }


def test_spawn_field_names_are_snake_case_not_the_harness_camel_case(sandbox):
    """The harness sends totalTokens/toolStats/resolvedModel; every other field
    in this record is snake_case, so none of those names may survive."""
    run_agent_event(sandbox, AGENT_TOOL_RESPONSE)
    line = sandbox.lines("T061.jsonl")[0]
    for camel in ("totalTokens", "toolStats", "resolvedModel", "agentType",
                  "totalToolUseCount", "totalDurationMs"):
        assert camel not in line, f"harness camelCase key {camel} leaked into the record"


def test_tool_stats_of_all_zeros_is_still_recorded(sandbox):
    """A spawn that used no tools is a legitimate measurement, not a reason to
    omit the object — omitting it would make 'zero' unreadable from 'unknown'."""
    payload = dict(AGENT_TOOL_RESPONSE)
    payload["toolStats"] = {k: 0 for k in
                            ("readCount", "searchCount", "bashCount",
                             "editFileCount", "linesAdded", "linesRemoved")}
    run_agent_event(sandbox, payload)
    stats = sandbox.only_record()["spawn"]["tool_stats"]
    assert stats == {"read_count": 0, "search_count": 0, "bash_count": 0,
                     "edit_file_count": 0, "lines_added": 0, "lines_removed": 0}


# ---------------------------------------------------------------------------
# AC4 — golden comparison: non-Agent records are byte-identical
# ---------------------------------------------------------------------------

def test_non_agent_records_match_pinned_pre_change_golden(sandbox):
    """AC4, pinned form. Compared as whole lines (key order included) with only
    the timestamp elided."""
    for event in GOLDEN_EVENTS:
        assert sandbox.run_hook(event).returncode == 0
    assert sandbox.trace_files() == sorted(GOLDEN_LINES)
    for filename, expected in GOLDEN_LINES.items():
        actual = [elide_timestamp(line) for line in sandbox.lines(filename)]
        assert actual == expected, f"{filename} drifted from the pre-change golden"


def test_non_agent_records_match_the_pre_change_hook_differentially():
    """AC4, differential form: run the *actual* pre-change source recovered from
    git at 82883a2 alongside the current one over the same events. This is what
    catches a common-path regression the pinned literals above don't cover."""
    try:
        pre_change_source = subprocess.run(
            ["git", "show", f"{PRE_CHANGE_REF}:{HOOK_REL_PATH}"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"pre-change source unavailable at {PRE_CHANGE_REF}: {exc}")

    old = HookSandbox(hook_source=pre_change_source)
    new = HookSandbox()
    try:
        for event in GOLDEN_EVENTS:
            assert old.run_hook(event).returncode == 0
            assert new.run_hook(event).returncode == 0
        assert new.trace_files() == old.trace_files()
        for filename in old.trace_files():
            old_lines = [elide_timestamp(line) for line in old.lines(filename)]
            new_lines = [elide_timestamp(line) for line in new.lines(filename)]
            assert new_lines == old_lines, f"{filename} differs from the pre-change hook"
    finally:
        old.cleanup()
        new.cleanup()


# ---------------------------------------------------------------------------
# AC5 — negative: the spawn's prompt/content are never copied in
# ---------------------------------------------------------------------------

def test_record_never_carries_the_spawn_prompt_or_content(sandbox):
    """AC5. `summary` already carries the prompt going in; copying the response's
    `prompt`/`content` back out doubles trace size for no gain."""
    run_agent_event(sandbox, AGENT_TOOL_RESPONSE)
    record = sandbox.only_record()
    spawn = record["spawn"]
    assert "prompt" not in spawn and "content" not in spawn, spawn
    assert "agentId" not in spawn, spawn
    assert "iterations" not in spawn.get("usage", {}), spawn
    assert "cache_creation" not in spawn.get("usage", {}), spawn
    assert "otherToolCount" not in spawn.get("tool_stats", {}), spawn
    # Whole-line check: the response body must not appear anywhere in the record
    # beyond the summary, which is capped and derived from tool_input.
    line = sandbox.lines("T061.jsonl")[0]
    assert "Done. Ran echo and reported back." not in line


def test_summary_truncation_is_unaffected_by_the_new_field(sandbox):
    """AC10."""
    event = {
        "tool_name": "Agent",
        "tool_input": {"file_path": "tasks/TASK_GUIDE_T061.md", "prompt": "x" * 5000},
        "tool_response": AGENT_TOOL_RESPONSE,
    }
    assert sandbox.run_hook(event).returncode == 0
    record = sandbox.only_record()
    assert len(record["summary"]) == 300
    assert record["spawn"]["total_tokens"] == 16981


# ---------------------------------------------------------------------------
# AC6 — fail-open: no spawn key, no crash
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tool_response,missing", [
    (None, True),            # key absent entirely
    (None, False),           # key present but null
    ("truncated payload", False),  # string, as seen in truncated-payload fallbacks
    ({}, False),             # empty dict
    ({"is_error": True}, False),   # dict with no cost fields at all
])
def test_unusable_tool_response_yields_no_spawn_key(sandbox, tool_response, missing):
    """AC6. Absent, never a crash and never a partial object of Nones."""
    result = run_agent_event(sandbox, tool_response, missing=missing)
    assert result.returncode == 0, result.stderr
    record = sandbox.only_record()
    assert "spawn" not in record, record
    assert record["tool_name"] == "Agent"
    assert set(record) == {"timestamp", "tool_name", "summary", "is_error"}


def test_error_flag_still_derived_from_tool_response(sandbox):
    """AC8 — is_error is unchanged, including when spawn data is present."""
    payload = dict(AGENT_TOOL_RESPONSE)
    payload["is_error"] = True
    run_agent_event(sandbox, payload)
    record = sandbox.only_record()
    assert record["is_error"] is True
    assert record["spawn"]["total_tokens"] == 16981


def test_failed_spawn_still_records_its_cost(sandbox):
    """A spawn that errored still cost tokens; status is reported, not gated on."""
    payload = {k: v for k, v in AGENT_TOOL_RESPONSE.items() if k != "status"}
    payload["is_error"] = True
    run_agent_event(sandbox, payload)
    spawn = sandbox.only_record()["spawn"]
    assert "status" not in spawn
    assert spawn["total_tokens"] == 16981


# ---------------------------------------------------------------------------
# AC7 — partial payloads keep what is present
# ---------------------------------------------------------------------------

def test_missing_tool_stats_still_emits_usage(sandbox):
    """AC7 / SC4."""
    payload = {k: v for k, v in AGENT_TOOL_RESPONSE.items() if k != "toolStats"}
    run_agent_event(sandbox, payload)
    spawn = sandbox.only_record()["spawn"]
    assert "usage" in spawn
    assert "tool_stats" not in spawn


def test_missing_usage_still_emits_tool_stats(sandbox):
    """AC7, mirrored."""
    payload = {k: v for k, v in AGENT_TOOL_RESPONSE.items() if k != "usage"}
    run_agent_event(sandbox, payload)
    spawn = sandbox.only_record()["spawn"]
    assert "tool_stats" in spawn
    assert "usage" not in spawn


@pytest.mark.parametrize("bad", ["not-a-dict", 7, [1, 2], None])
def test_non_dict_usage_and_tool_stats_are_skipped_not_crashed(sandbox, bad):
    """AC6/AC7 one layer down: the sub-objects get the same guard the top level
    does — this hook family has repeatedly shipped defects *below* the logic
    under review."""
    payload = dict(AGENT_TOOL_RESPONSE)
    payload["usage"] = bad
    payload["toolStats"] = bad
    result = run_agent_event(sandbox, payload)
    assert result.returncode == 0, result.stderr
    spawn = sandbox.only_record()["spawn"]
    assert "usage" not in spawn and "tool_stats" not in spawn
    assert spawn["total_tokens"] == 16981


def test_partial_usage_keeps_only_present_keys_never_none(sandbox):
    """AC6's 'never a partial object with None values', at the usage level."""
    payload = dict(AGENT_TOOL_RESPONSE)
    payload["usage"] = {"input_tokens": 5}
    run_agent_event(sandbox, payload)
    usage = sandbox.only_record()["spawn"]["usage"]
    assert usage == {"input_tokens": 5}


# ---------------------------------------------------------------------------
# AC9 — attribution unchanged
# ---------------------------------------------------------------------------

def test_attribution_still_routes_the_record_by_resolve_task_id(sandbox):
    """AC9 — the record still lands in <task>.jsonl, and an Agent event with no
    structural reference still lands in _untagged.jsonl."""
    run_agent_event(sandbox, AGENT_TOOL_RESPONSE)
    assert sandbox.trace_files() == ["T061.jsonl"]

    unattributed = {
        "tool_name": "Agent",
        "tool_input": {"prompt": "no structural reference here"},
        "tool_response": AGENT_TOOL_RESPONSE,
    }
    assert sandbox.run_hook(unattributed).returncode == 0
    assert sandbox.trace_files() == ["T061.jsonl", "_untagged.jsonl"]
    assert "spawn" in sandbox.records("_untagged.jsonl")[0]


# ---------------------------------------------------------------------------
# Record size
# ---------------------------------------------------------------------------

def test_record_line_stays_small(sandbox):
    """`summary` is capped at MAX_SUMMARY_LEN; the new object is a fixed set of
    scalars, so a single JSONL line cannot grow with payload size."""
    payload = dict(AGENT_TOOL_RESPONSE)
    payload["content"] = "x" * 500000
    payload["usage"] = dict(AGENT_TOOL_RESPONSE["usage"])
    payload["usage"]["iterations"] = [{"input_tokens": i} for i in range(5000)]
    run_agent_event(sandbox, payload)
    assert len(sandbox.lines("T061.jsonl")[0]) < 1000
