#!/usr/bin/env python3
"""Start a process detached, and kill it with its children, on POSIX and Windows (T265).

POSIX: `start_new_session=True` (setsid) makes the child lead its own process group, so it
survives the hook that started it; `kill_tree` sends SIGKILL to that whole group.
Windows: `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS` detaches the child; `kill_tree` runs
`taskkill /T /F /PID <pid>`, which kills the process and every process it started.

Never a shell, never a command string: `argv` is a list, and the PID handed to `taskkill` must be
an `int`. Use `kill_tree` only on a process that `start_detached` started.

This module imports only the standard library.
"""
import os
import subprocess
import sys

# Win32 process-creation flags (the `subprocess` constants exist only on Windows).
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008


def _windows():
    return sys.platform == "win32"


def start_detached(argv, **popen_kwargs):
    """`subprocess.Popen(argv, **popen_kwargs)`, detached from the caller's session or console."""
    if isinstance(argv, (str, bytes)):
        raise TypeError("start_detached needs an argument list, not a command string")
    if popen_kwargs.get("shell"):
        raise ValueError("start_detached never runs a shell")
    if _windows():
        popen_kwargs["creationflags"] = (popen_kwargs.get("creationflags", 0)
                                         | CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS)
        return subprocess.Popen(argv, **popen_kwargs)
    return subprocess.Popen(argv, start_new_session=True, **popen_kwargs)


def kill_tree(proc):
    """Kill `proc` and its children. A process that already exited is a no-op, never an error."""
    pid = proc.pid
    if not isinstance(pid, int) or isinstance(pid, bool):
        raise TypeError(f"pid must be an int, not {type(pid).__name__}")
    if proc.poll() is not None:
        return  # exited and reaped: its PID (and group ID) may now belong to another process
    if _windows():
        try:
            done = subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)],
                                  stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
            if done.returncode == 0:
                return
        except (OSError, subprocess.SubprocessError):
            pass
        _kill_parent(proc)
        return
    import signal  # SIGKILL exists only on POSIX
    try:
        os.killpg(pid, signal.SIGKILL)  # the group `start_new_session` made; not reaped, so ours
    except OSError:
        _kill_parent(proc)


def _kill_parent(proc):
    try:
        proc.kill()  # a no-op once the process has been reaped
    except OSError:
        pass
