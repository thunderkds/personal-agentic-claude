#!/usr/bin/env python3
"""T264: one portable file lock (`lib/filelock.py`) for the trace hook, the close-out and the verifier.

POSIX behaviour is driven for real (two processes). The Windows branch is driven with a fake
`msvcrt`, because CI on a Windows host is T263's job.

Run with: python3 -m pytest .claude/hooks/tests/test_filelock.py -q
"""
import json
import os
import subprocess
import sys

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(HOOKS_DIR, "lib")
sys.path.insert(0, LIB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import filelock  # noqa: E402
from test_trace_chain import Sandbox, bash_event  # noqa: E402

# Each worker: under the lock, read the line count, pause, append the next number. Without a
# working lock two workers read the same count and write the same number.
WORKER = """
import os, sys, time
sys.path.insert(0, {lib!r})
if sys.argv[3] == "mutated":
    import fcntl
    fcntl.flock = lambda *a, **k: None  # the lock call replaced by a no-op
from filelock import file_lock
path, tag = sys.argv[1], sys.argv[2]
for _ in range(200):
    with open(path, "a+") as f:
        with file_lock(f):
            f.seek(0)
            n = len(f.read().splitlines())
            time.sleep(0.0005)
            f.write("%d %s\\n" % (n + 1, tag))
            f.flush()
"""


def run_workers(path, mode):
    code = WORKER.format(lib=LIB)
    procs = [subprocess.Popen([sys.executable, "-c", code, path, tag, mode]) for tag in "ab"]
    assert all(p.wait(timeout=300) == 0 for p in procs)
    with open(path) as f:
        return f.read().splitlines()


def numbers_intact(lines):
    return [int(l.split()[0]) for l in lines] == list(range(1, 401))


# --- AC1 / AC3: the POSIX path, two real processes -----------------------------

def test_two_processes_append_400_whole_lines_in_order(tmp_path):
    lines = run_workers(str(tmp_path / "shared.txt"), "real")
    assert len(lines) == 400
    assert numbers_intact(lines)


def test_mutation_control_no_op_lock_goes_red(tmp_path):
    """The two-process test is only evidence if it fails without the lock."""
    lines = run_workers(str(tmp_path / "shared.txt"), "mutated")
    assert not numbers_intact(lines)


def test_exclusive_lock_excludes_and_shared_locks_coexist(tmp_path):
    if sys.platform == "win32":
        pytest.skip("POSIX lock semantics")
    path = str(tmp_path / "f")
    open(path, "w").close()
    probe = ("import fcntl, sys\n"
             "f = open(sys.argv[1], 'a')\n"
             "try:\n"
             "    fcntl.flock(f, fcntl.LOCK_%s | fcntl.LOCK_NB)\n"
             "    print('got')\n"
             "except OSError:\n"
             "    print('blocked')\n")

    def probe_mode(mode):
        return subprocess.run([sys.executable, "-c", probe % mode, path], capture_output=True,
                              text=True).stdout.strip()

    with open(path, "a") as f:
        with filelock.file_lock(f):
            assert probe_mode("SH") == "blocked"
        assert probe_mode("EX") == "got"
        with filelock.file_lock(f, shared=True):
            assert probe_mode("SH") == "got"
            assert probe_mode("EX") == "blocked"


def test_unlocks_when_the_body_raises(tmp_path):
    if sys.platform == "win32":
        pytest.skip("POSIX lock semantics")
    path = str(tmp_path / "f")
    with open(path, "a") as f:
        with pytest.raises(RuntimeError):
            with filelock.file_lock(f):
                raise RuntimeError("body failed")
    probe = ("import fcntl, sys\nf = open(sys.argv[1], 'a')\n"
             "fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)\nprint('got')\n")
    assert subprocess.run([sys.executable, "-c", probe, path], capture_output=True,
                          text=True).stdout.strip() == "got"


# --- AC4: the Windows branch, with a fake msvcrt -------------------------------

class FakeMsvcrt:
    LK_LOCK, LK_UNLCK, LK_NBLCK, LK_RLCK = 1, 0, 2, 3

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def locking(self, fd, mode, nbytes):
        self.calls.append((mode, nbytes, os.lseek(fd, 0, os.SEEK_CUR)))
        if self.fail:
            raise OSError("fake lock failure")


@pytest.fixture
def windows(monkeypatch):
    fake = FakeMsvcrt()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    monkeypatch.setitem(sys.modules, "fcntl", None)  # an import of it would raise
    return fake


def test_windows_locks_then_unlocks_one_byte_at_offset_zero(windows, tmp_path):
    path = tmp_path / "f"
    path.write_text("existing line\n")
    with open(path, "a") as f:  # append mode: the position is the end of file
        end = f.tell()
        assert end > 0
        with filelock.file_lock(f):
            assert [c[0] for c in windows.calls] == [windows.LK_LOCK]
        assert f.tell() == end  # the position is restored
    assert [c[0] for c in windows.calls] == [windows.LK_LOCK, windows.LK_UNLCK]
    assert all(c[1] == 1 and c[2] == 0 for c in windows.calls)  # one byte, offset 0, both calls


def test_windows_shared_takes_the_exclusive_lock(windows, tmp_path):
    with open(tmp_path / "f", "a") as f:
        with filelock.file_lock(f, shared=True):
            pass
    assert [c[0] for c in windows.calls] == [windows.LK_LOCK, windows.LK_UNLCK]


def test_windows_unlocks_when_the_body_raises(windows, tmp_path):
    with open(tmp_path / "f", "a") as f:
        with pytest.raises(RuntimeError):
            with filelock.file_lock(f):
                raise RuntimeError("body failed")
    assert [c[0] for c in windows.calls] == [windows.LK_LOCK, windows.LK_UNLCK]


def test_windows_lock_failure_raises_and_does_not_unlock(monkeypatch, tmp_path):
    fake = FakeMsvcrt(fail=True)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    with open(tmp_path / "f", "a") as f:
        with pytest.raises(OSError):
            with filelock.file_lock(f):
                pytest.fail("the body must not run when the lock failed")
    assert [c[0] for c in fake.calls] == [fake.LK_LOCK]


# --- AC5: each caller keeps its own failure rule -------------------------------

@pytest.fixture
def sb():
    s = Sandbox()
    yield s
    s.cleanup()


def test_trace_hook_still_appends_and_marks_a_lock_failure(sb):
    runner = ("import sys, runpy; sys.path.insert(0, %r); import filelock\n"
              "def boom(*a, **k): raise OSError('lock failed')\n"
              "filelock.file_lock = boom\n"
              "runpy.run_path(%r, run_name='__main__')" % (os.path.join(os.path.dirname(sb.hook), "lib"), sb.hook))
    result = subprocess.run([sys.executable, "-c", runner], input=json.dumps(bash_event(1)),
                            capture_output=True, text=True, env=sb.env())
    assert result.returncode == 0, result.stderr
    (rec,) = sb.records()
    assert rec["lock"] == "failed"
    assert sb.verify().stdout.splitlines()[-1].startswith("INTACT")


def test_trace_hook_without_the_helper_still_appends_and_marks_it(sb):
    os.remove(os.path.join(os.path.dirname(sb.hook), "lib", "filelock.py"))
    sb.run_hook(bash_event(1))
    (rec,) = sb.records()
    assert rec["lock"] == "failed"


def test_close_out_fails_closed_when_the_lock_fails(monkeypatch, tmp_path):
    import auto_closeout

    def boom(*a, **k):
        raise OSError("lock failed")

    monkeypatch.setattr(auto_closeout, "file_lock", boom)
    said = []
    with pytest.raises(OSError):  # the caller turns an exception into "done not moved"
        auto_closeout.close_out(str(tmp_path), "T900", str(tmp_path / "tasks" / "TASK_REVIEW_T900.md"),
                                "abc", "s", False, say=said.append)
    assert said == []  # nothing was read or moved


def test_no_hook_or_script_imports_fcntl_directly():
    root = os.path.dirname(os.path.dirname(HOOKS_DIR))
    for rel in (".claude/hooks/post_tool_trace.py", ".claude/hooks/lib/auto_closeout.py",
                "scripts/verify_trace.py"):
        with open(os.path.join(root, rel)) as f:
            assert "fcntl" not in f.read(), rel
