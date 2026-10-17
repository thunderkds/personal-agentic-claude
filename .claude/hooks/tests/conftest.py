"""Keep T148's trace anchors out of the real home during tests.

Every test that runs `post_tool_trace.py` would otherwise append anchors under
~/.claude/harness-anchors/. Subprocesses inherit os.environ, so setting the
override here, at collection time, covers them all. A test that needs its own
anchor directory sets CLAUDE_TRACE_ANCHOR_DIR in its subprocess env.
"""
import atexit
import os
import shutil
import tempfile

if not os.environ.get("CLAUDE_TRACE_ANCHOR_DIR"):
    _ANCHOR_DIR = tempfile.mkdtemp(prefix="t148_test_anchors_")
    os.environ["CLAUDE_TRACE_ANCHOR_DIR"] = _ANCHOR_DIR
    atexit.register(shutil.rmtree, _ANCHOR_DIR, True)
