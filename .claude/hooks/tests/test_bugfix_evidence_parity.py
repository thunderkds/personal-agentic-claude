#!/usr/bin/env python3
"""T055 — bugfix Evidence-table parity with the gate-visible implementation shape.

Before this task, `.claude/skills/bugfix/SKILL.md`'s Step 3 guide skeleton produced a 3-row
free-text Evidence table with no `verify` row at all. `pre_bash_block_unsafe_merge.py`'s merge
gate scans a task guide for a row whose Check cell is `verify` and whose *Notes* column contains
the word "pass" (T026: two compounding bugs — wrong check-column text, and "pass" checked in the
wrong column). On a bugfix task that row structurally did not exist, so the gate was not failing —
it had nothing to bind to.

This test exercises the real gate function end-to-end (`pre_bash_block_unsafe_merge.main`, not a
re-implemented regex) against guides shaped like the *new* bugfix skeleton, proving:
  SC1 — a properly-filled bugfix guide's `verify` row (Notes says "pass") lets the gate resolve
        True (merge proceeds, no blocker text for the task)
  SC2 — the same guide with the `verify` row Notes left blank: gate resolves False (blocked)
  SC3 — "pass" written in the Result column but not Notes (the exact T026 defect): still False
  SC4 — an OLD bugfix guide (original 3-row table, no `verify` row at all): still False, exactly
        as today — no silent retro-pass for already-closed bugfix guides

Run with: python3 -m pytest .claude/hooks/tests/test_bugfix_evidence_parity.py -v
"""
import json
import os
import shutil
import sys
import tempfile
import types

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")


def load_hook_module(path, name):
    """Load the hook as a module without executing its trailing bare `main()` call
    (mirrors test_merge_gate_evidence.py's loader — see that file for why)."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "pre_bash_block_unsafe_merge_t055")

TASK_ID = "T900"

# A real Bash invocation record so trace_shows_verification() also resolves True —
# the gate requires BOTH the guide's Evidence row AND a matching trace record.
VERIFIED_TRACE_LINE = json.dumps(
    {
        "timestamp": "2026-08-06T00:00:00+00:00",
        "tool_name": "Bash",
        "summary": json.dumps({"command": "python3 -m pytest .claude/hooks/tests -q"}),
        "is_error": False,
    }
)

# The new bugfix Evidence table shape (post-T055), Result column filled per row.
NEW_TABLE_HEADER = (
    "### Evidence (filled by reviewer at Stage 4/5)\n"
    "| Check | Result | Notes / output snippet |\n"
    "|-------|--------|------------------------|\n"
)

OLD_TABLE = (
    "### Evidence\n"
    "| Check | Command / observation | Result |\n"
    "|---|---|---|\n"
    "| Repro loop | ran | pass |\n"
    "| Regression test | added | pass |\n"
    "| Smoke suite | green | pass |\n"
)


def _new_table(verify_result_cell, verify_notes_cell):
    return (
        NEW_TABLE_HEADER
        + "| **New test(s) cover Acceptance Criteria** | pass | tests/test_x.py |\n"
        + "| Verification command run | pass | ok |\n"
        + "| Negative cases hold | pass | |\n"
        + f"| verify | {verify_result_cell} | {verify_notes_cell} |\n"
        + "| Review scope bounded to the change's blast radius | pass | |\n"
        + "| Full smoke suite still green (no regression) | pass | |\n"
        + "| **UI: Visual regression** | N/A | |\n"
        + "| **UI: Design-system compliance** | N/A | |\n"
        + "| **UI: Responsiveness** | N/A | |\n"
        + "| Repro loop | pass | |\n"
        + "| Regression test | pass | |\n"
        + "| Smoke suite | pass | |\n"
    )


class GateSandbox:
    """Points the loaded hook module's KANBAN/TASKS_DIR/TRACE_DIR at a throwaway
    directory tree, so the real repo's own files are never read or written."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="t055_gate_")
        self.tasks_dir = os.path.join(self.root, "tasks")
        self.trace_dir = os.path.join(self.root, "trace")
        os.makedirs(self.tasks_dir)
        os.makedirs(self.trace_dir)
        self.kanban_path = os.path.join(self.root, "PROJECT_KANBAN.md")

        self._saved = (merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR)
        merge_gate.KANBAN = self.kanban_path
        merge_gate.TASKS_DIR = self.tasks_dir
        merge_gate.TRACE_DIR = self.trace_dir

    def write_kanban(self, task_id):
        with open(self.kanban_path, "w") as f:
            f.write(
                "## Board\n\n"
                "### In Progress\n\n"
                "### Ready for Review\n"
                f"- **{task_id}** — bugfix parity test task\n"
            )

    def write_guide(self, task_id, evidence_table):
        with open(os.path.join(self.tasks_dir, f"TASK_GUIDE_{task_id}.md"), "w") as f:
            f.write(f"# Bug Fix Task Guide — {task_id}\n\n" + evidence_table)

    def write_trace(self, task_id, lines):
        with open(os.path.join(self.trace_dir, f"{task_id}.jsonl"), "w") as f:
            for line in lines:
                f.write(line + "\n")

    def cleanup(self):
        merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR = self._saved
        shutil.rmtree(self.root, ignore_errors=True)


def _run_gate(evidence_table, task_id=TASK_ID, with_trace=True):
    """Run the real hook `main()` against a fake stdin `git merge` event, with the
    guide/KANBAN/trace state set up by the caller. Returns the printed decision
    dict, or None if the gate did not block (i.e. resolved True / allowed)."""
    sandbox = GateSandbox()
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    try:
        sandbox.write_kanban(task_id)
        sandbox.write_guide(task_id, evidence_table)
        if with_trace:
            sandbox.write_trace(task_id, [VERIFIED_TRACE_LINE])

        payload = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "git merge feature-branch"}}
        )
        sys.stdin = types.SimpleNamespace(read=lambda: payload)
        # json.load(sys.stdin) calls .read() internally when given a file-like;
        # simplest to monkeypatch json.load's target directly instead.
        import io

        sys.stdin = io.StringIO(payload)

        captured = io.StringIO()
        sys.stdout = captured
        merge_gate.main()
        sys.stdout = old_stdout

        out = captured.getvalue().strip()
        if not out:
            return None
        return json.loads(out)
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# SC1 — properly filled new-shape guide: gate allows (no block for this task)
# ---------------------------------------------------------------------------

def test_sc1_properly_filled_bugfix_verify_row_is_not_blocked():
    table = _new_table("pass / fail", "skill run, feature confirmed working — pass")
    result = _run_gate(table)
    assert result is None, f"expected gate to allow, got: {result}"


# ---------------------------------------------------------------------------
# SC2 — verify row Notes left blank: gate blocks
# ---------------------------------------------------------------------------

def test_sc2_blank_verify_notes_is_blocked():
    table = _new_table("pass / fail", "")
    result = _run_gate(table)
    assert result is not None and result["decision"] == "block"
    assert TASK_ID in result["reason"]


# ---------------------------------------------------------------------------
# SC3 — "pass" in Result column, not Notes: the exact T026 defect, must stay caught
# ---------------------------------------------------------------------------

def test_sc3_pass_in_result_column_only_is_blocked():
    table = _new_table("pass", "reviewer observed the fix working")
    result = _run_gate(table)
    assert result is not None and result["decision"] == "block"
    assert TASK_ID in result["reason"]


# ---------------------------------------------------------------------------
# SC4 — old 3-row bugfix guide: still blocked, no silent retro-pass
# ---------------------------------------------------------------------------

def test_sc4_old_three_row_bugfix_guide_is_still_blocked():
    result = _run_gate(OLD_TABLE)
    assert result is not None and result["decision"] == "block"
    assert "no evidence row" in result["reason"]


# ---------------------------------------------------------------------------
# AC7 — the gate can actually find the `verify` row in a guide generated from
# the updated skeleton (this is the literal skeleton text from SKILL.md, not a
# hand-shaped fixture) — proven by a test, not by inspection
# ---------------------------------------------------------------------------

def test_ac7_gate_finds_verify_row_in_real_skeleton_shaped_guide():
    skill_path = os.path.join(
        os.path.dirname(HOOKS_DIR), "skills", "bugfix", "SKILL.md"
    )
    with open(skill_path) as f:
        skill_text = f.read()

    assert "| verify | ☐ pass / ☐ fail / ☐ N/A |" in skill_text, (
        "bugfix SKILL.md skeleton no longer contains a verify row in the gate's "
        "expected shape"
    )

    # Fill the skeleton's checkbox cells the way a reviewer would, then run the
    # real guide-shaped text (not a synthetic table) through the gate.
    filled = skill_text.replace(
        "| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed",
        "| verify | pass | [what was observed",
    ).replace(
        "the merge gate scans this Notes column for the word \"pass\"]",
        "the merge gate scans this Notes column for the word \"pass\" — pass]",
    )
    result = _run_gate(filled)
    assert result is None, f"expected gate to allow a filled real-skeleton guide, got: {result}"
