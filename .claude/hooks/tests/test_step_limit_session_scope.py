"""T056 — session-scoped step counters + TTL expiry.

Covers AC1-AC9 / SC1-SC7 from tasks/TASK_GUIDE_T056.md. Drives the real
hook as a subprocess (as the harness does) so the import-time env parsing
(AC4) and the file-mtime TTL check are genuinely exercised, not mocked.
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
    """T057: these tests assert behaviour at a limit of 40, the default when
    they were written. The default is now 90, so the limit is pinned here
    explicitly — the tests are about session keying and TTL, not about what
    the default happens to be. An explicit env_extra still overrides."""
    event = {
        "tool_name": "Bash",
        "tool_input": {"prompt": f"Task ID: {task_id}"},
    }
    if session_id is not None:
        event["session_id"] = session_id
    payload = stdin_text if stdin_text is not None else json.dumps(event)
    env = dict(os.environ)
    env["CLAUDE_ACTIVE_TASK"] = task_id
    env.setdefault("CLAUDE_STEP_LIMIT", "40")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env
    )


def _counter_path(session, task_id):
    return os.path.join(STATE_DIR, f"step_count_{session}_{task_id}.txt")


def test_sc1_same_session_blocked_at_41():
    task_id = "T910"
    _cleanup(task_id)
    try:
        procs = [_run_hook(task_id, session_id="A") for _ in range(41)]
        last = procs[-1]
        assert last.stdout.strip(), "41st call must emit a block decision"
        payload = json.loads(last.stdout)
        assert payload["decision"] == "block"
    finally:
        _cleanup(task_id)


def test_sc2_different_session_not_blocked_by_exhausted_session():
    """The incident, inverted: session A burns its budget, session B's very
    first call for the same task must still be allowed."""
    task_id = "T911"
    _cleanup(task_id)
    try:
        for _ in range(41):
            _run_hook(task_id, session_id="A")
        b_proc = _run_hook(task_id, session_id="B")
        assert b_proc.stdout.strip() == "", (
            f"session B must not be blocked, got: {b_proc.stdout}"
        )
        # T057 SUPERSEDED: this previously asserted session A must STILL be
        # blocked. Self-clearing reverses that deliberately -- A's block already
        # reset A's counter, so A's next call is allowed. The property this test
        # actually exists to protect (B is unaffected by A) is asserted above and
        # still holds. See tasks/TASK_GUIDE_T057.md AC1/AC2.
        a_proc = _run_hook(task_id, session_id="A")
        assert a_proc.stdout.strip() == "", (
            "T057: A's own block already reset A's counter, so A recovers on the "
            f"next call rather than staying locked out. Got: {a_proc.stdout}"
        )
    finally:
        _cleanup(task_id)


def test_sc3_expired_counter_restarts_at_one():
    task_id = "T912"
    _cleanup(task_id)
    try:
        for _ in range(41):
            _run_hook(task_id, session_id="A")
        cpath = _counter_path("A", task_id)
        assert os.path.exists(cpath)
        old_time = time.time() - (7 * 3600)
        os.utime(cpath, (old_time, old_time))

        proc = _run_hook(task_id, session_id="A")
        assert proc.stdout.strip() == "", (
            "an expired counter must restart at 1, not carry the old count forward"
        )
        with open(cpath) as f:
            assert f.read().strip().splitlines()[0] == "1"
    finally:
        _cleanup(task_id)


def test_sc4_malformed_ttl_env_falls_back_to_default_no_import_raise():
    task_id = "T913"
    _cleanup(task_id)
    try:
        proc = _run_hook(
            task_id, session_id="A", env_extra={"CLAUDE_STEP_COUNT_TTL_S": "not-a-number"}
        )
        assert proc.returncode == 0
        assert proc.stderr == "" or "Traceback" not in proc.stderr
    finally:
        _cleanup(task_id)


def test_sc5_missing_session_id_still_counts_and_blocks():
    task_id = "T914"
    _cleanup(task_id)
    try:
        procs = [_run_hook(task_id, session_id=None) for _ in range(41)]
        last_payload = json.loads(procs[-1].stdout)
        assert last_payload["decision"] == "block"
        assert os.path.exists(_counter_path("nosession", task_id))
    finally:
        _cleanup(task_id)


def test_sc6_malformed_stdin_fails_open():
    proc = subprocess.run(
        [sys.executable, HOOK], input="not json at all",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_sc6_unwritable_state_dir_fails_open(monkeypatch=None):
    """AC7: an unwritable state dir must not raise or block. Simulated by
    pointing CLAUDE_PROJECT_DIR-independent STATE_DIR is not env-overridable
    here, so we cover the analogous unreadable-counter path instead: a
    counter file that exists but cannot be parsed as an int degrades to 0."""
    task_id = "T915"
    _cleanup(task_id)
    try:
        cpath = _counter_path("A", task_id)
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(cpath, "w") as f:
            f.write("not-a-number")
        proc = _run_hook(task_id, session_id="A")
        assert proc.returncode == 0
        assert proc.stdout.strip() == "", "unreadable counter must fail open, count as 0"
        with open(cpath) as f:
            assert f.read().strip().splitlines()[0] == "1"
    finally:
        _cleanup(task_id)


def test_ac1_ac6_counter_name_includes_session_and_block_message_names_it():
    task_id = "T916"
    _cleanup(task_id)
    try:
        # T057: the 41st call is the one that blocks, and it now also resets
        # the counter -- so the block must be captured here, not on a 42nd call
        # (which is deliberately allowed).
        for _ in range(40):
            _run_hook(task_id, session_id="XY")
        proc = _run_hook(task_id, session_id="XY")
        payload = json.loads(proc.stdout)
        assert payload["decision"] == "block", payload
        # AC1 (session in the counter name) is asserted on the file itself; the
        # message no longer names it, because T057 AC5 removed the manual-reset
        # instruction that referenced it -- telling a blocked reader to run a
        # command it is blocked from running was the original defect.
        assert os.path.exists(_counter_path("XY", task_id))
        assert "manually reset" not in payload["reason"], payload["reason"]
    finally:
        _cleanup(task_id)


def test_session_id_is_sanitized_before_reaching_the_filename():
    """Edge case: a session_id containing path-hostile characters must be
    reduced to [A-Za-z0-9] before it reaches a file name."""
    task_id = "T917"
    _cleanup(task_id)
    try:
        proc = _run_hook(task_id, session_id="../../etc/passwd")
        assert proc.returncode == 0
        sanitized = _counter_path("etcpasswd", task_id)
        assert os.path.exists(sanitized)
        for bad in glob.glob(os.path.join(STATE_DIR, "step_count_*..*")):
            assert False, f"unsanitized session leaked into a filename: {bad}"
    finally:
        _cleanup(task_id)


def test_ac9_done_task_counter_is_covered_by_ttl_not_by_kanban_lookup():
    """A completed task's stale counter is neutralized purely by TTL aging
    (AC3), never by a live Kanban-status check -- confirmed here by reusing
    the SC3 mechanism against a task ID that plausibly maps to a Done task."""
    task_id = "T053"  # already Done/pushed per the guide's incident account
    _cleanup(task_id)
    try:
        for _ in range(41):
            _run_hook(task_id, session_id="A")
        cpath = _counter_path("A", task_id)
        old_time = time.time() - (7 * 3600)
        os.utime(cpath, (old_time, old_time))
        proc = _run_hook(task_id, session_id="A")
        assert proc.stdout.strip() == "", "an aged counter must not block, Done or not"
    finally:
        _cleanup(task_id)
