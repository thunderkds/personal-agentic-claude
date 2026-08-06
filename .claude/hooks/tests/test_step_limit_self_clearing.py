"""T057 — self-clearing step-limit block + raised default limit.

Covers AC1-AC9 / SC1-SC7 from tasks/TASK_GUIDE_T057.md. Drives the real
hook as a subprocess so the import-time env parsing (AC4) and the
file-mtime TTL check are genuinely exercised, not mocked.

Note (AC8/T056 regression): the previous suite,
test_step_limit_session_scope.py, asserted the OLD (permanently-locked)
behaviour for its "same session stays blocked after exhaustion" case. That
assertion is the exact thing this task deliberately reverses (self-clearing
block), so it cannot both hold and be true post-T057 -- see the Supervisor
report accompanying this task for the flag, per AC9 ("do not silently edit
a pre-existing test").
"""
import glob
import json
import os
import subprocess
import sys
import time

HOOK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(HOOK_DIR, "pre_agent_step_limit.py")
STATE_DIR = os.path.join(HOOK_DIR, ".state")


def _cleanup(task_id):
    for f in glob.glob(os.path.join(STATE_DIR, f"step_count_*{task_id}*.txt")):
        os.remove(f)


def _run_hook(task_id, session_id=None, env_extra=None, stdin_text=None):
    event = {
        "tool_name": "Bash",
        "tool_input": {"prompt": f"Task ID: {task_id}"},
    }
    if session_id is not None:
        event["session_id"] = session_id
    payload = stdin_text if stdin_text is not None else json.dumps(event)
    env = dict(os.environ)
    env["CLAUDE_ACTIVE_TASK"] = task_id
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env
    )


def _counter_path(session, task_id):
    return os.path.join(STATE_DIR, f"step_count_{session}_{task_id}.txt")


def test_sc1_block_fires_with_env_limit():
    """AC1/AC3: at the (env-overridden) limit + 1, the hook still emits a
    block -- self-clearing does not mean it stops interrupting."""
    task_id = "T920"
    _cleanup(task_id)
    try:
        procs = [
            _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
            for _ in range(6)
        ]
        last = procs[-1]
        assert last.stdout.strip(), "the 6th call (limit=5) must emit a block decision"
        payload = json.loads(last.stdout)
        assert payload["decision"] == "block"
    finally:
        _cleanup(task_id)


def test_sc2_call_after_block_is_allowed():
    """AC1/AC2: the call immediately after a block recovers by itself --
    no lockout persists, no manual reset needed."""
    task_id = "T921"
    _cleanup(task_id)
    try:
        for _ in range(5):
            _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        blocked = _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        assert json.loads(blocked.stdout)["decision"] == "block"

        recovered = _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        assert recovered.stdout.strip() == "", (
            f"the call after a block must be allowed, got: {recovered.stdout}"
        )
    finally:
        _cleanup(task_id)


def test_sc3_counter_reads_zero_after_block():
    """AC1: the counter file after a block contains 0 (never a value above
    the limit)."""
    task_id = "T922"
    _cleanup(task_id)
    try:
        for _ in range(6):
            _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        cpath = _counter_path("A", task_id)
        with open(cpath) as f:
            lines = f.read().splitlines()
        assert lines[0] == "0", f"counter must reset to 0 after a block, got {lines[0]!r}"
    finally:
        _cleanup(task_id)


def test_sc4_env_override_still_wins_over_raised_default():
    """AC4: CLAUDE_STEP_LIMIT=5 blocks on the 6th call, not the new raised
    default."""
    task_id = "T923"
    _cleanup(task_id)
    try:
        for _ in range(5):
            out = _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
            assert out.stdout.strip() == "", "must not block before the override limit"
        sixth = _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        assert json.loads(sixth.stdout)["decision"] == "block"
    finally:
        _cleanup(task_id)


def test_sc5_third_block_escalates_message():
    """AC6: repeated blocks for the same task are tracked in a durable
    field; the 3rd+ block's message escalates."""
    task_id = "T924"
    _cleanup(task_id)
    try:
        limit_env = {"CLAUDE_STEP_LIMIT": "2"}
        block_msgs = []
        for _round in range(3):
            for _ in range(2):
                _run_hook(task_id, session_id="A", env_extra=limit_env)
            blocked = _run_hook(task_id, session_id="A", env_extra=limit_env)
            payload = json.loads(blocked.stdout)
            assert payload["decision"] == "block"
            block_msgs.append(payload["reason"])

        assert "interrupted" not in block_msgs[0]
        assert "interrupted" not in block_msgs[1]
        assert "interrupted 3 times" in block_msgs[2], block_msgs[2]
    finally:
        _cleanup(task_id)


def test_sc6_malformed_stdin_fails_open_no_decision():
    proc = subprocess.run(
        [sys.executable, HOOK], input="not json at all",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_ac5_block_message_no_longer_instructs_manual_reset():
    task_id = "T925"
    _cleanup(task_id)
    try:
        for _ in range(5):
            _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        blocked = _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        reason = json.loads(blocked.stdout)["reason"]
        assert "manually reset" not in reason
        assert ".state/step_count_" not in reason
    finally:
        _cleanup(task_id)


def test_ac4_default_limit_raised_above_40():
    """AC4: the new default exceeds 40 (env unset) -- 41 calls must NOT
    block under the raised default (regression guard against silently
    reverting the raise)."""
    task_id = "T926"
    _cleanup(task_id)
    try:
        env = dict(os.environ)
        env.pop("CLAUDE_STEP_LIMIT", None)
        env["CLAUDE_ACTIVE_TASK"] = task_id
        event = {
            "tool_name": "Bash",
            "tool_input": {"prompt": f"Task ID: {task_id}"},
            "session_id": "A",
        }
        last = None
        for _ in range(41):
            last = subprocess.run(
                [sys.executable, HOOK], input=json.dumps(event),
                capture_output=True, text=True, env=env,
            )
        assert last.stdout.strip() == "", (
            "41 calls must not block under a default raised above 40"
        )
    finally:
        _cleanup(task_id)


def test_ac7_unwritable_counter_still_fails_open():
    """AC7 regression, mirrors T056's coverage: a counter file that exists
    but cannot be parsed as an int degrades to 0, never raises, never
    blocks spuriously."""
    task_id = "T927"
    _cleanup(task_id)
    try:
        cpath = _counter_path("A", task_id)
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(cpath, "w") as f:
            f.write("not-a-number")
        proc = _run_hook(task_id, session_id="A")
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""
        with open(cpath) as f:
            assert f.read().splitlines()[0] == "1"
    finally:
        _cleanup(task_id)


def test_ac8_legacy_one_line_counter_file_does_not_crash():
    """AC8 regression risk (edge case checklist): a legacy one-line counter
    file (T056 format, no block_count line) must parse without crashing,
    treating block_count as 0."""
    task_id = "T928"
    _cleanup(task_id)
    try:
        cpath = _counter_path("A", task_id)
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(cpath, "w") as f:
            f.write("3")  # legacy one-line format, no trailing block_count
        proc = _run_hook(task_id, session_id="A")
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""
        with open(cpath) as f:
            lines = f.read().splitlines()
        assert lines[0] == "4"
        assert lines[1] == "0"
    finally:
        _cleanup(task_id)


def test_ac8_ttl_expiry_still_resets_count_to_one():
    """AC8: T056's TTL-expiry restart-at-1 behaviour is unchanged."""
    task_id = "T929"
    _cleanup(task_id)
    try:
        for _ in range(5):
            _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        cpath = _counter_path("A", task_id)
        old_time = time.time() - (7 * 3600)
        os.utime(cpath, (old_time, old_time))

        proc = _run_hook(task_id, session_id="A", env_extra={"CLAUDE_STEP_LIMIT": "5"})
        assert proc.stdout.strip() == ""
        with open(cpath) as f:
            assert f.read().splitlines()[0] == "1"
    finally:
        _cleanup(task_id)
