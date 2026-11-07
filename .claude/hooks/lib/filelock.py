"""One portable advisory file lock for hooks and scripts (T264).

    with file_lock(handle):                 # exclusive
    with file_lock(handle, shared=True):    # shared (read)

`handle` is an open file object. The lock is held until the `with` block ends and is always
released there, also when the body raises. The helper never swallows an error: when locking
fails or is unavailable it raises, and each caller keeps its own rule (the trace hook appends
anyway and marks the line, the close-out fails closed).

POSIX: `fcntl.flock`, `LOCK_EX` or `LOCK_SH`. Same call as before T264.

Windows: `msvcrt.locking` on ONE byte at offset 0, never at the end of the file. The lock
is mandatory there, so it is taken on the same byte for every user of the file. The helper
flushes, moves the position to 0 for the call, and puts the position back afterwards (so an
append-mode handle keeps writing at the end). `msvcrt` has no shared lock: `shared=True`
takes the exclusive lock instead, so two readers wait for each other. `LK_LOCK` retries for
about ten seconds and then raises `OSError`; there is no longer wait and no retry here.

The platform is read at call time, and `fcntl` / `msvcrt` are imported only on their own
platform, so no import of this module can fail on either.
"""
import sys
from contextlib import contextmanager


@contextmanager
def file_lock(handle, shared=False):
    if sys.platform == "win32":
        with _windows_lock(handle):
            yield
    else:
        with _posix_lock(handle, shared):
            yield


@contextmanager
def _posix_lock(handle, shared):
    import fcntl
    fcntl.flock(handle.fileno(), fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _windows_lock(handle):
    import msvcrt
    fd = handle.fileno()
    _lock_byte_zero(handle, lambda: msvcrt.locking(fd, msvcrt.LK_LOCK, 1))
    try:
        yield
    finally:
        _lock_byte_zero(handle, lambda: msvcrt.locking(fd, msvcrt.LK_UNLCK, 1))


def _lock_byte_zero(handle, call):
    handle.flush()
    position = handle.tell()
    handle.seek(0)
    try:
        call()
    finally:
        handle.seek(position)
