#!/usr/bin/env python3
"""T044 defects A and B — `post_agent_move_to_review.py`.

**Defect A (attribution).** The hook extracted its Task ID with
`re.findall(r"\\bT(\\d{3})\\b", prompt)` over the *entire* `Agent` spawn prompt.
Stage 3 mandates pasting `memory/MEMORY.md` verbatim into every spawn prompt,
and that file is full of prose task IDs — so a single spawn could move several
unrelated In-Progress rows to Ready for Review and delete their step counters.

**Defect B (lifecycle).** The hook is a `PostToolUse` matcher on `Agent`, which
fires when the tool call returns. For a background sub-agent that is when the
spawn is *issued*, not when the work finishes, so the board announced
Ready for Review before any work existed (observed live on T039).

Resolution: attribution now comes from `lib/task_context.py:resolve_task_id`
(structural only), and the hook no longer mutates `PROJECT_KANBAN.md` at all —
see the hook's own docstring for why no reliable completion signal is available.
These tests pin both halves: nothing is attributed from prose, and nothing is
written.

The hook is driven end-to-end the way the harness does it — event JSON on
stdin, over a subprocess, from a foreign cwd — inside an isolated
`<tmp>/.claude/hooks/` tree, because the hook resolves its own ROOT from
`__file__`.

Run with: python3 -m pytest .claude/hooks/tests/test_move_to_review.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_NAME = "post_agent_move_to_review.py"
HOOK_PATH = os.path.join(HOOKS_DIR, HOOK_NAME)

FOREIGN_CWD = tempfile.gettempdir()

KANBAN_TEXT = """# PROJECT KANBAN

**Last updated**: 2026-01-01

### In Progress
- [ ] **T099** the task this spawn is actually about | C2 | Medium | P0
- [ ] **T001** an unrelated in-flight task | C1 | Low | P1
- [ ] **T028** another unrelated in-flight task | C1 | Low | P2

### Ready for Review
- [ ] **T040** already waiting | C1 | Low | P1

### Done
- [x] **T043** structural task attribution | C2 | Medium | P0
"""

# A spawn prompt shaped exactly like a real Stage 3 one: a structural guide
# reference for the task at hand, followed by a verbatim MEMORY.md-style paste
# whose prose mentions several other task IDs.
SPAWN_PROMPT = """**Task ID**: T099
**Guide**: tasks/TASK_GUIDE_T099.md — read it completely before any code.

## memory/MEMORY.md (hot-tier)

- [T018/T019/T020: Kanban regex + reconciliation](decisions.md) — extract() needed re.MULTILINE
- [T028 done: Token Audit Log scaffold + test](decisions.md) — reports/token-audit live
- [T040](decisions.md) — blocked on T043; see also T001 and T041
"""

PROSE_ONLY_PROMPT = """Please look at T001 and T028 and tell me what changed in T040.
No structural reference anywhere in this text.
"""

COUNTER_TASKS = ("T099", "T001", "T028", "T040")


class HookSandbox:
    """Isolated `<tmp>/.claude/hooks/` tree so the hook's own ROOT resolution
    (three dirs up from `__file__`) lands in a throwaway directory."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="t044_move_sandbox_")
        self.hooks_dir = os.path.join(self.root, ".claude", "hooks")
        os.makedirs(self.hooks_dir)
        shutil.copy(HOOK_PATH, os.path.join(self.hooks_dir, HOOK_NAME))
        lib_src = os.path.join(HOOKS_DIR, "lib")
        if os.path.isdir(lib_src):
            shutil.copytree(lib_src, os.path.join(self.hooks_dir, "lib"))
        self.kanban_path = os.path.join(self.root, "PROJECT_KANBAN.md")
        with open(self.kanban_path, "w") as f:
            f.write(KANBAN_TEXT)
        self.state_dir = os.path.join(self.hooks_dir, ".state")
        os.makedirs(self.state_dir)
        for task_id in COUNTER_TASKS:
            with open(os.path.join(self.state_dir, f"step_count_{task_id}.txt"), "w") as f:
                f.write("7")

    def run(self, event, env_extra=None):
        env = dict(os.environ)
        env.pop("CLAUDE_ACTIVE_TASK", None)
        env.update(env_extra or {})
        payload = event if isinstance(event, str) else json.dumps(event)
        return subprocess.run(
            [sys.executable, os.path.join(self.hooks_dir, HOOK_NAME)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=FOREIGN_CWD,
            env=env,
        )

    def kanban(self):
        with open(self.kanban_path) as f:
            return f.read()

    def counters(self):
        return sorted(os.listdir(self.state_dir))

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def agent_event(prompt):
    return {"tool_name": "Agent", "tool_input": {"prompt": prompt}}


# ---------------------------------------------------------------------------
# AC2 / SC1 — a MEMORY.md paste must not touch unrelated rows or counters
# ---------------------------------------------------------------------------

def test_memory_paste_moves_no_unrelated_row():
    """The verified defect: T001/T028 were In Progress and T040 Ready for Review
    purely because the pasted memory text mentions them."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run(agent_event(SPAWN_PROMPT))
        assert result.returncode == 0, result.stderr
        assert sandbox.kanban() == KANBAN_TEXT, sandbox.kanban()
    finally:
        sandbox.cleanup()


def test_memory_paste_deletes_no_step_counter():
    sandbox = HookSandbox()
    try:
        result = sandbox.run(agent_event(SPAWN_PROMPT))
        assert result.returncode == 0, result.stderr
        assert sandbox.counters() == [
            f"step_count_{t}.txt" for t in sorted(COUNTER_TASKS)
        ], sandbox.counters()
    finally:
        sandbox.cleanup()


def test_advisory_names_only_the_structurally_resolved_task():
    """AC1: the ID comes from `resolve_task_id`, so only T099 may be named —
    the prose IDs in the pasted memory text must not appear."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run(agent_event(SPAWN_PROMPT))
        assert result.returncode == 0, result.stderr
        assert "T099" in result.stderr, result.stderr
        for other in ("T001", "T028", "T040", "T018"):
            assert other not in result.stderr, (other, result.stderr)
    finally:
        sandbox.cleanup()


def test_prose_only_prompt_resolves_to_nothing():
    """No structural reference → no task, no advisory naming any of the IDs."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run(agent_event(PROSE_ONLY_PROMPT))
        assert result.returncode == 0, result.stderr
        assert sandbox.kanban() == KANBAN_TEXT
        assert sandbox.counters() == [
            f"step_count_{t}.txt" for t in sorted(COUNTER_TASKS)
        ]
        for tid in ("T001", "T028", "T040"):
            assert tid not in result.stderr, (tid, result.stderr)
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# AC3 — the row is never moved automatically, not even for the right task
# ---------------------------------------------------------------------------

def test_kanban_is_never_written_even_for_the_correct_task():
    """`PostToolUse`/`Agent` fires at spawn issuance for a background agent, so
    a move here is a claim that work finished before it started. The hook must
    leave the board alone — including the `**Last updated**` line."""
    sandbox = HookSandbox()
    try:
        result = sandbox.run(agent_event("**Guide**: tasks/TASK_GUIDE_T099.md"))
        assert result.returncode == 0, result.stderr
        assert sandbox.kanban() == KANBAN_TEXT, sandbox.kanban()
        assert "**Last updated**: 2026-01-01" in sandbox.kanban()
    finally:
        sandbox.cleanup()


def test_env_attributed_spawn_still_writes_nothing():
    sandbox = HookSandbox()
    try:
        result = sandbox.run(
            agent_event("no structural reference here"),
            env_extra={"CLAUDE_ACTIVE_TASK": "T099"},
        )
        assert result.returncode == 0, result.stderr
        assert sandbox.kanban() == KANBAN_TEXT
        assert sandbox.counters() == [
            f"step_count_{t}.txt" for t in sorted(COUNTER_TASKS)
        ]
    finally:
        sandbox.cleanup()


def test_hook_source_contains_no_free_text_task_scan():
    """AC1: the local `\\bT(\\d{3})\\b` scan must be gone, not merely bypassed."""
    source = open(HOOK_PATH).read()
    assert "resolve_task_id" in source
    assert r"\bT(\d{3})\b" not in source
    assert r"\bT\d{3}\b" not in source


def test_docstring_explains_why_the_move_is_disabled():
    """AC3 requires the hook to *say* that it does not move the row and why —
    a silently inert hook is its own trap for the next reader."""
    source = open(HOOK_PATH).read()
    docstring = source.split('"""')[1]
    lowered = docstring.lower()
    assert "does not move" in lowered, docstring
    assert "subagentstop" in lowered, docstring
    assert "background" in lowered, docstring


# ---------------------------------------------------------------------------
# AC9 — fail open (this hook fires after every Agent call)
# ---------------------------------------------------------------------------

def test_malformed_stdin_exits_zero_silently():
    sandbox = HookSandbox()
    try:
        for payload in ("", "not json", "[]", "null", '{"tool_input": "a string"}'):
            result = sandbox.run(payload)
            assert result.returncode == 0, (payload, result.stderr)
            assert "Traceback" not in result.stderr, (payload, result.stderr)
        assert sandbox.kanban() == KANBAN_TEXT
    finally:
        sandbox.cleanup()


def test_non_agent_tool_is_ignored():
    sandbox = HookSandbox()
    try:
        result = sandbox.run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        assert result.returncode == 0, result.stderr
        assert result.stderr.strip() == "", result.stderr
        assert sandbox.kanban() == KANBAN_TEXT
    finally:
        sandbox.cleanup()


def test_missing_kanban_is_not_an_error():
    sandbox = HookSandbox()
    try:
        os.remove(sandbox.kanban_path)
        result = sandbox.run(agent_event(SPAWN_PROMPT))
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr, result.stderr
    finally:
        sandbox.cleanup()
