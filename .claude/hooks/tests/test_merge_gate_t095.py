#!/usr/bin/env python3
"""T095 — the merge gate's three defects, one file.

  * **Defect A** — `has_filled_verify_row()` resolved the Evidence section under
    the *main checkout's* `tasks/` only, but Stage 3 writes
    `TASK_REVIEW_Txxx.md` in the agent's worktree, on the task branch. Every
    worktree-isolated task therefore read as `(no evidence row)`.
  * **Defect B** — the block message and the quoted-invocation comment both
    prescribed `CLAUDE_ACTIVE_TASK=Txxx <command>`, which T047 measured as
    non-functional (a hook is a *sibling* process of the tool call).
  * **Defect C** — the gate classified a command by its **data**: a `cat > file`
    heredoc whose body contained `git push` was blocked as a push.

Every fixture here is **constructed**. Nothing reads the live board, the live
`tasks/` directory, or the machine's real `git worktree list` — a test that did
would pass or fail depending on which worktrees happen to exist today.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_t095.py -v
"""
import pytest
import io
import json
import os
import sys
import tempfile
import types

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))

from shell_data import strip_heredoc_bodies  # noqa: E402


def load_hook_module(path, name):
    """Load a hook without running its bottom-of-file `main()` — same technique
    as `test_merge_gate_evidence.py`, which explains why it is necessary."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "merge_gate_t095")


# ---------------------------------------------------------------------------
# Constructed fixtures
# ---------------------------------------------------------------------------

KANBAN_READY_FOR_REVIEW = """# PROJECT_KANBAN

### Todo

### In Progress

### Ready for Review
- [ ] **T900** — fixture task | common-infrastructure | C2 | Risk: Medium | P0

### Done
"""

# The post-T064 guide shape: the Evidence heading is vacated to a pointer, so
# resolution has to fall through to the review file.
GUIDE_WITH_VACATED_EVIDENCE = """# TASK_GUIDE - T900

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T900.md`.

---
"""

REVIEW_WITH_FILLED_VERIFY_ROW = """# TASK_REVIEW - T900

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☑ pass | 707 passed |
| verify | ☑ pass | verify skill run, feature confirmed working — pass |
"""

PYTEST_TRACE_RECORD = json.dumps({
    "timestamp": "2026-08-31T00:00:00+00:00",
    "tool_name": "Bash",
    "summary": json.dumps({"command": "python3 -m pytest .claude/hooks/tests/ -q"})[:300],
    "is_error": False,
})

HEREDOC_MENTIONING_A_PUSH = (
    "cat > notes.md <<'EOF'\n"
    "This document explains why the gate blocks a git push.\n"
    "EOF\n"
)


class GateFixture:
    """A main checkout and a stand-in worktree, both constructed on disk, with
    the hook module's module-level paths pointed at them.

    The worktree is a plain directory, not a real `git worktree`: the gate is
    handed its `tasks/` path through the `tasks_dir` parameter, so the test
    exercises the resolution logic without depending on git or on this machine's
    actual worktree list.
    """

    def __init__(self, review_in_worktree=True, review_in_main=False):
        self.root = tempfile.mkdtemp(prefix="t095_gate_")
        self.main_tasks = os.path.join(self.root, "main", "tasks")
        self.worktree_tasks = os.path.join(self.root, "wt-t900", "tasks")
        self.trace_dir = os.path.join(self.root, "main", "memory", "event-trace")
        for path in (self.main_tasks, self.worktree_tasks, self.trace_dir):
            os.makedirs(path)

        self._write(self.main_tasks, "TASK_GUIDE_T900.md", GUIDE_WITH_VACATED_EVIDENCE)
        self._write(self.worktree_tasks, "TASK_GUIDE_T900.md", GUIDE_WITH_VACATED_EVIDENCE)
        if review_in_worktree:
            self._write(self.worktree_tasks, "TASK_REVIEW_T900.md", REVIEW_WITH_FILLED_VERIFY_ROW)
        if review_in_main:
            self._write(self.main_tasks, "TASK_REVIEW_T900.md", REVIEW_WITH_FILLED_VERIFY_ROW)

        self.kanban = os.path.join(self.root, "PROJECT_KANBAN.md")
        with open(self.kanban, "w") as f:
            f.write(KANBAN_READY_FOR_REVIEW)
        with open(os.path.join(self.trace_dir, "T900.jsonl"), "w") as f:
            f.write(PYTEST_TRACE_RECORD + "\n")

        self._saved = (merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR)
        merge_gate.KANBAN = self.kanban
        merge_gate.TASKS_DIR = self.main_tasks
        merge_gate.TRACE_DIR = self.trace_dir

    @staticmethod
    def _write(directory, name, text):
        with open(os.path.join(directory, name), "w") as f:
            f.write(text)

    @property
    def search_dirs(self):
        """What the live gate builds from `git worktree list --porcelain`:
        the main checkout first, then each worktree."""
        return [self.main_tasks, self.worktree_tasks]

    def cleanup(self):
        merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR = self._saved
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)


def run_gate(command, fixture, worktree_dirs=None):
    """Drive the hook's real `main()` over a constructed event, returning the
    block `reason` or None when the gate stayed silent.

    `worktree_dirs` stands in for the live `git worktree list` enumeration, so
    the fixture's directories are what the gate resolves evidence across.
    """
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    saved_stdin, saved_stdout = sys.stdin, sys.stdout
    saved_enumerator = merge_gate.worktree_tasks_dirs
    sys.stdin = io.StringIO(event)
    sys.stdout = io.StringIO()
    if worktree_dirs is not None:
        merge_gate.worktree_tasks_dirs = lambda: list(worktree_dirs)
    try:
        try:
            merge_gate.main()
        except SystemExit:
            pass
        printed = sys.stdout.getvalue().strip()
    finally:
        sys.stdin, sys.stdout = saved_stdin, saved_stdout
        merge_gate.worktree_tasks_dirs = saved_enumerator
    if not printed:
        return None
    return json.loads(printed)["reason"]


# ---------------------------------------------------------------------------
# Defect C — a heredoc body is data, not a command (AC7)
# ---------------------------------------------------------------------------

def test_heredoc_body_mentioning_a_push_is_not_treated_as_a_push():
    """AC7: the exact command that was rejected while writing this task's own
    guide — a file write, no git command outside the heredoc body."""
    fixture = GateFixture()
    try:
        assert run_gate(HEREDOC_MENTIONING_A_PUSH, fixture, worktree_dirs=[]) is None
    finally:
        fixture.cleanup()


def test_heredoc_body_mentioning_a_merge_is_not_treated_as_a_merge():
    command = "cat > notes.md <<EOF\nThe Supervisor will git merge this branch later.\nEOF\n"
    fixture = GateFixture()
    try:
        assert run_gate(command, fixture, worktree_dirs=[]) is None
    finally:
        fixture.cleanup()


# ---------------------------------------------------------------------------
# Defect C — anti-evasion (AC8). The highest-consequence direction in this file:
# an over-stripping fix silently disarms the gate.
# ---------------------------------------------------------------------------

def test_real_push_after_the_heredoc_terminator_is_still_blocked():
    """AC8: stripping stops at the terminator, so the `; git push` after it is
    still command text. Without this the fix becomes a way to smuggle a push."""
    fixture = GateFixture()
    try:
        reason = run_gate(
            HEREDOC_MENTIONING_A_PUSH + "; git push origin fix/t900",
            fixture,
            worktree_dirs=[],
        )
        assert reason is not None and "Pipeline gate failed" in reason
    finally:
        fixture.cleanup()


def test_real_push_before_the_heredoc_is_still_blocked():
    fixture = GateFixture()
    try:
        reason = run_gate(
            "git push origin fix/t900 && " + HEREDOC_MENTIONING_A_PUSH,
            fixture,
            worktree_dirs=[],
        )
        assert reason is not None and "Pipeline gate failed" in reason
    finally:
        fixture.cleanup()


def test_push_on_the_heredoc_header_line_is_still_blocked():
    """The header's own line stays command text — only the body is removed."""
    fixture = GateFixture()
    try:
        reason = run_gate(
            "git push && cat > notes.md <<'EOF'\nplain prose\nEOF\n",
            fixture,
            worktree_dirs=[],
        )
        assert reason is not None and "Pipeline gate failed" in reason
    finally:
        fixture.cleanup()


def test_unterminated_heredoc_body_is_not_stripped():
    """Fail-closed direction: with no terminator the body is left as command
    text and still scanned, so the gate over-blocks rather than under-blocks."""
    fixture = GateFixture()
    try:
        reason = run_gate("cat > notes.md <<'EOF'\ngit push origin main\n", fixture, worktree_dirs=[])
        assert reason is not None and "Pipeline gate failed" in reason
    finally:
        fixture.cleanup()


# --- strip_heredoc_bodies itself -------------------------------------------

def test_body_is_replaced_with_a_space_not_deleted():
    """Deleting the span could glue the surrounding words into a token that was
    never in the command — the same rule `QUOTED_SPAN_PATTERN` follows."""
    stripped = strip_heredoc_bodies("cat <<'E'\nbody\nE\npush")
    assert "body" not in stripped
    assert stripped == "cat <<'E'\n \npush"


def test_quoted_and_unquoted_terminators_both_match():
    for header in ("<<EOF", "<<'EOF'", '<<"EOF"', "<< EOF"):
        command = f"cat > f {header}\ngit push\nEOF\ntrue"
        assert "git push" not in strip_heredoc_bodies(command), header


def test_dash_form_allows_a_tab_indented_terminator():
    assert "git push" not in strip_heredoc_bodies("cat > f <<-EOF\ngit push\n\tEOF\ntrue")


def test_plain_form_does_not_end_at_an_indented_terminator():
    """`<<EOF` requires the terminator at column 0. Treating an indented line as
    a terminator would stop stripping early and resume scanning body text."""
    command = "cat > f <<EOF\nprose\n\tEOF\nmore prose\nEOF\ntrue"
    assert "prose" not in strip_heredoc_bodies(command)


def test_multiple_heredocs_are_each_stripped():
    command = "cat > a <<'E1'\ngit push\nE1\ncat > b <<'E2'\ngit merge\nE2\ntrue"
    stripped = strip_heredoc_bodies(command)
    assert "git push" not in stripped and "git merge" not in stripped


def test_here_string_is_not_mistaken_for_a_heredoc():
    """`<<<` has no body and no terminator; misreading it as a header would let
    the rest of the command line be swallowed."""
    command = "grep x <<< 'data'\ngit push"
    assert strip_heredoc_bodies(command) == command


def test_non_string_and_heredoc_free_input_pass_through():
    assert strip_heredoc_bodies(None) is None
    assert strip_heredoc_bodies("git push origin main") == "git push origin main"


# ---------------------------------------------------------------------------
# AC9 anti-vacuity — with the Defect C fix reverted, the heredoc write must go
# back to being blocked. A test that passes with and without the fix proves
# nothing.
# ---------------------------------------------------------------------------

def test_heredoc_allowance_depends_on_the_fix():
    fixture = GateFixture()
    saved = merge_gate.strip_heredoc_bodies
    try:
        assert run_gate(HEREDOC_MENTIONING_A_PUSH, fixture, worktree_dirs=[]) is None
        merge_gate.strip_heredoc_bodies = lambda command: command  # pre-T095 behaviour
        reverted = run_gate(HEREDOC_MENTIONING_A_PUSH, fixture, worktree_dirs=[])
        assert reverted is not None and "Pipeline gate failed" in reverted
    finally:
        merge_gate.strip_heredoc_bodies = saved
        fixture.cleanup()


# ---------------------------------------------------------------------------
# Defect A — evidence written in a worktree, on the task branch (AC1, AC2)
# ---------------------------------------------------------------------------

def test_filled_verify_row_in_a_worktree_is_found():
    """AC1: the filled `☑ pass` row exists ONLY under the worktree's tasks/ —
    the shape Stage 3 always produces, since the review file is created by the
    agent on its own branch and is absent from the main checkout until merge."""
    fixture = GateFixture(review_in_worktree=True)
    try:
        assert merge_gate.has_filled_verify_row("T900", fixture.search_dirs) is True
    finally:
        fixture.cleanup()


def test_gate_does_not_emit_no_evidence_row_for_worktree_evidence():
    """AC1 at the entry point: the same push that produced this task's BEFORE
    capture, with the worktree enumerated."""
    fixture = GateFixture(review_in_worktree=True)
    try:
        reason = run_gate(
            "git push origin fix/t900", fixture, worktree_dirs=[fixture.worktree_tasks]
        )
        assert reason is None, reason
    finally:
        fixture.cleanup()


def test_gate_still_blocks_when_the_review_file_exists_nowhere():
    """AC2: fail-closed preserved. Searching more places must never become a
    reason to skip the check."""
    fixture = GateFixture(review_in_worktree=False)
    try:
        reason = run_gate(
            "git push origin fix/t900", fixture, worktree_dirs=[fixture.worktree_tasks]
        )
        assert reason is not None
        assert "T900 (no evidence row)" in reason
    finally:
        fixture.cleanup()


def test_main_checkout_is_searched_first():
    """The common post-merge case resolves on the first candidate, unchanged in
    behaviour and cost, and a worktree copy can never shadow integrated
    evidence."""
    fixture = GateFixture(review_in_worktree=False, review_in_main=True)
    try:
        assert merge_gate.evidence_search_dirs(fixture.search_dirs)[0] == fixture.main_tasks
        assert merge_gate.has_filled_verify_row("T900", fixture.search_dirs) is True
    finally:
        fixture.cleanup()


def test_evidence_search_dirs_keeps_the_single_directory_shape():
    """`tasks_dir` is unchanged for every pre-T095 caller: a single path stays a
    single path, and no worktree enumeration happens for it."""
    assert merge_gate.evidence_search_dirs("/somewhere/tasks") == ["/somewhere/tasks"]


def test_evidence_search_dirs_defaults_to_main_checkout_first():
    saved = merge_gate.worktree_tasks_dirs
    try:
        merge_gate.worktree_tasks_dirs = lambda: ["/wt/tasks"]
        assert merge_gate.evidence_search_dirs() == [merge_gate.TASKS_DIR, "/wt/tasks"]
    finally:
        merge_gate.worktree_tasks_dirs = saved


def test_enumeration_failure_degrades_to_main_checkout_not_to_allow():
    """Every failure of `git worktree list` — git absent, non-zero exit, a
    timeout, unparsable output — must leave the main-checkout lookup intact.
    Degrading to "allow" here would stop the gate gating on every task at once.
    """
    saved = merge_gate.worktree_tasks_dirs

    def _raises():
        raise OSError("git not found")

    try:
        merge_gate.worktree_tasks_dirs = lambda: []
        assert merge_gate.evidence_search_dirs() == [merge_gate.TASKS_DIR]

        merge_gate.worktree_tasks_dirs = saved
        fixture = GateFixture(review_in_worktree=True)
        try:
            # No worktrees enumerated at all: the worktree-only evidence is
            # invisible, so the gate blocks — it does not allow.
            reason = run_gate("git push", fixture, worktree_dirs=[])
            assert reason is not None and "T900 (no evidence row)" in reason
        finally:
            fixture.cleanup()
    finally:
        merge_gate.worktree_tasks_dirs = saved


def test_worktree_tasks_dirs_returns_empty_when_git_is_unavailable(monkeypatch):
    def _boom(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(merge_gate.subprocess, "run", _boom)
    assert merge_gate.worktree_tasks_dirs() == []


def test_worktree_tasks_dirs_returns_empty_on_non_zero_exit(monkeypatch):
    class _Result:
        returncode = 128
        stdout = "fatal: not a git repository\n"

    monkeypatch.setattr(merge_gate.subprocess, "run", lambda *a, **k: _Result())
    assert merge_gate.worktree_tasks_dirs() == []


def test_worktree_tasks_dirs_parses_porcelain_and_drops_the_main_checkout(monkeypatch):
    class _Result:
        returncode = 0
        stdout = (
            f"worktree {merge_gate.ROOT}\nHEAD abc\nbranch refs/heads/main\n\n"
            "worktree /tmp/wt-t900\nHEAD def\nbranch refs/heads/fix/t900\n\n"
        )

    monkeypatch.setattr(merge_gate.subprocess, "run", lambda *a, **k: _Result())
    assert merge_gate.worktree_tasks_dirs() == [os.path.join("/tmp/wt-t900", "tasks")]


# ---------------------------------------------------------------------------
# AC3 — the six fail-closed inputs named in has_filled_verify_row's docstring.
# Each is checked with the worktree search path ACTIVE, so the Defect A fix is
# proven not to have opened any of them.
# ---------------------------------------------------------------------------

def _dirs_with(tmp_path, guide=None, review=None):
    main = tmp_path / "main" / "tasks"
    worktree = tmp_path / "wt" / "tasks"
    main.mkdir(parents=True)
    worktree.mkdir(parents=True)
    if guide is not None:
        (worktree / "TASK_GUIDE_T900.md").write_text(guide)
    if review is not None:
        (worktree / "TASK_REVIEW_T900.md").write_text(review)
    return [str(main), str(worktree)]


def test_fail_closed_missing_guide_and_missing_review_file(tmp_path):
    assert merge_gate.has_filled_verify_row("T900", _dirs_with(tmp_path)) is False


def test_fail_closed_missing_review_file_with_vacated_guide(tmp_path):
    dirs = _dirs_with(tmp_path, guide=GUIDE_WITH_VACATED_EVIDENCE)
    assert merge_gate.has_filled_verify_row("T900", dirs) is False


def test_fail_closed_absent_evidence_section(tmp_path):
    dirs = _dirs_with(
        tmp_path,
        guide=GUIDE_WITH_VACATED_EVIDENCE,
        review="# TASK_REVIEW - T900\n\n## Demonstration\n\nnothing here\n",
    )
    assert merge_gate.has_filled_verify_row("T900", dirs) is False


def test_fail_closed_unfilled_row(tmp_path):
    review = (
        "# TASK_REVIEW - T900\n\n## Evidence\n\n"
        "| Check | Result | Notes |\n|---|---|---|\n"
        "| verify | | |\n"
    )
    dirs = _dirs_with(tmp_path, guide=GUIDE_WITH_VACATED_EVIDENCE, review=review)
    assert merge_gate.has_filled_verify_row("T900", dirs) is False


def test_fail_closed_template_unchecked_pass_placeholder(tmp_path):
    review = (
        "# TASK_REVIEW - T900\n\n## Evidence\n\n"
        "| Check | Result | Notes |\n|---|---|---|\n"
        "| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must say pass] |\n"
    )
    dirs = _dirs_with(tmp_path, guide=GUIDE_WITH_VACATED_EVIDENCE, review=review)
    assert merge_gate.has_filled_verify_row("T900", dirs) is False


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [geteuid]")
def test_fail_closed_unreadable_review_file(tmp_path):
    if os.geteuid() == 0:
        import pytest

        pytest.skip("root bypasses file permissions")
    dirs = _dirs_with(
        tmp_path,
        guide=GUIDE_WITH_VACATED_EVIDENCE,
        review=REVIEW_WITH_FILLED_VERIFY_ROW,
    )
    unreadable = os.path.join(dirs[1], "TASK_REVIEW_T900.md")
    os.chmod(unreadable, 0)
    try:
        assert merge_gate.has_filled_verify_row("T900", dirs) is False
    finally:
        os.chmod(unreadable, 0o644)


def test_no_directories_to_search_fails_closed():
    assert merge_gate.has_filled_verify_row("T900", []) is False


# ---------------------------------------------------------------------------
# AC9 anti-vacuity — with the Defect A fix reverted, the worktree scenario must
# go red again.
# ---------------------------------------------------------------------------

def test_worktree_evidence_resolution_depends_on_the_fix():
    fixture = GateFixture(review_in_worktree=True)
    saved = merge_gate.evidence_search_dirs
    try:
        assert run_gate(
            "git push origin fix/t900", fixture, worktree_dirs=[fixture.worktree_tasks]
        ) is None

        # Pre-T095 behaviour: the main checkout's tasks/ and nothing else.
        merge_gate.evidence_search_dirs = lambda tasks_dir=None: [
            tasks_dir if isinstance(tasks_dir, str) else merge_gate.TASKS_DIR
        ]
        reverted = run_gate(
            "git push origin fix/t900", fixture, worktree_dirs=[fixture.worktree_tasks]
        )
        assert reverted is not None and "T900 (no evidence row)" in reverted
    finally:
        merge_gate.evidence_search_dirs = saved
        fixture.cleanup()


# ---------------------------------------------------------------------------
# Defect B — the remediation note prescribed a mechanism T047 measured as dead
# (AC4, AC5, AC6)
# ---------------------------------------------------------------------------

def _block_message():
    fixture = GateFixture(review_in_worktree=False)
    try:
        reason = run_gate("git push origin fix/t900", fixture, worktree_dirs=[])
        assert reason is not None, "fixture should block, or there is no message to check"
        return reason
    finally:
        fixture.cleanup()


def test_block_message_does_not_prescribe_the_env_var_wrapper():
    """AC4: `CLAUDE_ACTIVE_TASK=Txxx <command>` cannot attribute anything from
    inside a session — a hook is a sibling process of the tool call. The gate
    must not hand an operator that instruction at the moment it blocks them."""
    message = _block_message()
    assert "CLAUDE_ACTIVE_TASK=Txxx <command>`" not in message
    assert "run the task's verification command as" not in message


def test_block_message_names_the_state_file_with_an_absolute_path():
    """AC4: the working channel, and the one detail that makes it work — a
    relative path resolves into the agent's own worktree, which the live hook
    never reads (T047 Stage 4 P1)."""
    message = _block_message()
    assert ".claude/hooks/.state/active_task" in message
    assert "absolute path" in message
    assert "$CLAUDE_PROJECT_DIR" in message  # named as the thing NOT to use


def test_block_message_does_not_claim_the_env_var_is_the_only_channel():
    """AC5: "only" was false — the state file is a second working channel, and
    the env var itself works when set before the session starts."""
    message = _block_message()
    assert "attributed to a task only via" not in message
    assert "before the session" in message


def test_env_var_is_still_described_as_working_in_its_real_context():
    """AC5, the other half: the correction must not overshoot into "the env var
    never works" — `task_context.py` still honours it as precedence slot 1."""
    assert "only takes effect when set before the session starts" in merge_gate.ATTRIBUTION_REMEDY


def test_quoted_invocation_comment_no_longer_prescribes_an_in_session_export():
    """AC6: line 84's comment carried the same false premise and is corrected on
    the same grounds. Asserted against the file's source, since a comment has no
    runtime surface."""
    source = open(HOOK_PATH, encoding="utf-8").read()
    assert "or export\n#     CLAUDE_ACTIVE_TASK and run it unwrapped" not in source
    assert "Run the runner directly, unwrapped." in source
