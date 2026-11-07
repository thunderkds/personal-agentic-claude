"""T265: `lib/proc.py` starts a run detached and kills it with its children, on POSIX and Windows.

The POSIX tests use real processes and only the PIDs they hold (never `pkill`/`pgrep -f`, which
match their own shell). The Windows tests force `sys.platform` to `win32` and replace
`subprocess.Popen` and `subprocess.run` with fakes: no real Windows run here (that is T263's CI).
"""
import os
import signal
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import proc as proc_mod  # noqa: E402

POSIX = pytest.mark.skipif(os.name != "posix", reason="real process-group test needs POSIX")


def _gone(pid):
    """True when `pid` no longer runs. A zombie (killed, not yet reaped by its new parent) counts as
    gone: it runs no code."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] == "Z"
    except OSError:
        return False


def _wait_gone(pid, seconds=5.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if _gone(pid):
            return True
        time.sleep(0.05)
    return _gone(pid)


def _start_parent_with_grandchild():
    """`sh` that starts `sleep 60` and waits; returns (proc, grandchild pid)."""
    p = proc_mod.start_detached(["sh", "-c", "sleep 60 & echo $!; wait"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
    line = p.stdout.readline()
    return p, int(line)


# ── AC 3 / Success 1 — POSIX: the parent and its grandchild both die ─────────────────────────
@POSIX
def test_posix_kill_tree_kills_parent_and_grandchild():
    p, grandchild = _start_parent_with_grandchild()
    try:
        assert os.getsid(p.pid) == p.pid != os.getsid(0), "start_detached did not start a new session"
        assert not _gone(grandchild), "fixture: the grandchild is not running"
        proc_mod.kill_tree(p)
        p.wait(timeout=5)
        assert _wait_gone(grandchild), f"grandchild {grandchild} survived kill_tree"
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)  # cleanup: only the group this test created
        except OSError:
            pass
        p.stdout.close()


# ── Review P1 — the leader exited, its group lives on: kill_tree still kills the group ──────
@POSIX
def test_posix_kill_tree_kills_the_group_after_the_leader_exited(tmp_path):
    pidfile = tmp_path / "pid"
    p = proc_mod.start_detached(["sh", "-c", 'sleep 30 & echo $! > "$1"; exit 0', "sh", str(pidfile)],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            p.communicate(timeout=1)  # the grandchild holds the pipes open
        grandchild = int(pidfile.read_text())
        assert not _gone(grandchild), "fixture: the grandchild is not running"
        proc_mod.kill_tree(p)
        assert _wait_gone(grandchild), f"grandchild {grandchild} survived kill_tree"
        p.communicate(timeout=5)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)  # cleanup: only the group this test created
        except OSError:
            pass


# ── AC 5 / Success 3 — an exited process: no raise, second call a no-op ──────────────────────
@POSIX
def test_posix_kill_tree_on_exited_process_does_not_raise():
    p = proc_mod.start_detached(["sh", "-c", "exit 0"])
    p.wait(timeout=5)
    proc_mod.kill_tree(p)
    proc_mod.kill_tree(p)


@POSIX
def test_posix_kill_tree_twice_is_a_no_op():
    p, grandchild = _start_parent_with_grandchild()
    try:
        proc_mod.kill_tree(p)
        p.wait(timeout=5)
        proc_mod.kill_tree(p)
        assert _wait_gone(grandchild)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)  # cleanup: only the group this test created
        except OSError:
            pass
        p.stdout.close()


@POSIX
def test_posix_start_detached_passes_kwargs_and_no_shell():
    p = proc_mod.start_detached(["sh", "-c", "echo $0"], stdout=subprocess.PIPE, text=True)
    out, _ = p.communicate(timeout=5)
    assert out.strip() == "sh"


# ── AC 4 / Success 2 — Windows branch, with fakes ────────────────────────────────────────────
class _FakeProc:
    def __init__(self, pid=4242, returncode=None):
        self.pid = pid
        self.returncode = returncode
        self.killed = 0

    def poll(self):
        return self.returncode

    def kill(self):
        self.killed += 1


@pytest.fixture
def win(monkeypatch):
    calls = {"popen": [], "run": []}

    def fake_popen(argv, **kwargs):
        calls["popen"].append((argv, kwargs))
        return _FakeProc()

    def fake_run(argv, **kwargs):
        calls["run"].append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(proc_mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(proc_mod.subprocess, "run", fake_run)
    return calls


def test_windows_start_detached_uses_creationflags_not_new_session(win):
    proc_mod.start_detached(["claude", "-p", "/verify T1"], stdout=subprocess.PIPE)
    [(argv, kwargs)] = win["popen"]
    assert argv == ["claude", "-p", "/verify T1"]
    assert kwargs["creationflags"] == 0x00000200 | 0x08000000  # NEW_PROCESS_GROUP | NO_WINDOW
    assert "start_new_session" not in kwargs
    assert not kwargs.get("shell")
    assert kwargs["stdout"] is subprocess.PIPE


def test_windows_kill_tree_runs_taskkill_as_an_argument_list(win):
    proc_mod.kill_tree(_FakeProc(pid=4242))
    [(argv, kwargs)] = win["run"]
    assert argv == ["taskkill", "/T", "/F", "/PID", "4242"]
    assert not kwargs.get("shell")


def test_windows_kill_tree_on_exited_process_runs_nothing(win):
    p = _FakeProc(returncode=0)
    proc_mod.kill_tree(p)
    proc_mod.kill_tree(p)
    assert win["run"] == [] and p.killed == 0


def test_windows_kill_tree_runs_taskkill_without_polling_first(win):
    """Review P2a: poll() would reap an exited leader and skip taskkill for its live children."""
    p = _FakeProc(pid=7)
    p.poll = lambda: pytest.fail("kill_tree called poll()")
    proc_mod.kill_tree(p)
    assert win["run"] == [(["taskkill", "/T", "/F", "/PID", "7"], win["run"][0][1])]


def test_windows_kill_tree_falls_back_to_kill_when_taskkill_is_missing(win, monkeypatch):
    def missing(argv, **kwargs):
        raise FileNotFoundError("taskkill")
    monkeypatch.setattr(proc_mod.subprocess, "run", missing)
    p = _FakeProc()
    proc_mod.kill_tree(p)
    assert p.killed == 1


# ── AC 6 — a non-int PID raises TypeError before any command runs ─────────────────────────────
@pytest.mark.parametrize("bad", ["4242", "4242 & calc", 42.0, None, True])
def test_kill_tree_rejects_a_non_int_pid_before_running_anything(win, bad):
    p = _FakeProc(pid=bad)
    with pytest.raises(TypeError):
        proc_mod.kill_tree(p)
    assert win["run"] == [] and p.killed == 0


@POSIX
def test_posix_kill_tree_rejects_a_non_int_pid(monkeypatch):
    sent = []
    monkeypatch.setattr(proc_mod.os, "killpg", lambda *a: sent.append(a))
    with pytest.raises(TypeError):
        proc_mod.kill_tree(_FakeProc(pid="0"))
    assert sent == []


# ── High risk: no shell, no command string ─────────────────────────────────────────────────────
@pytest.mark.parametrize("kwargs", [{"shell": True}])
def test_start_detached_refuses_shell(win, kwargs):
    with pytest.raises(ValueError):
        proc_mod.start_detached(["x"], **kwargs)
    assert win["popen"] == []


def test_start_detached_refuses_a_command_string(win):
    with pytest.raises(TypeError):
        proc_mod.start_detached("claude -p /verify")
    assert win["popen"] == []


# ── AC 2 — the hook uses the helper; no direct killpg / SIGKILL / start_new_session is left ──
def test_stop_auto_verify_uses_the_helper_only():
    hook = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "stop_auto_verify.py")
    with open(hook, encoding="utf-8") as f:
        text = f.read()
    for word in ("killpg", "SIGKILL", "start_new_session"):
        assert word not in text, f"{word} is still in stop_auto_verify.py"
    assert text.count("start_detached(") == 2 and text.count("kill_tree(") == 1
