"""Regression tests for T042: Complexity/Risk/Priority extraction in
post_write_register_task.py.

Bug: the three field regexes (`Complexity[:\\s]+`, `Risk[:\\s]+`,
`Priority[:\\s]+`) could not cross the markdown emphasis and label word the
template actually writes (`**Complexity Level**: C2`), so every field
silently fell back to a plausible-looking default (C1 / Low / P1) instead of
the real value — and instead of visibly failing.

These tests drive the real hook end-to-end the way the PostToolUse harness
does: feed the event JSON on stdin, over a subprocess. The hook resolves its
own ROOT from `__file__` (three directories up from the hook script), so
each test copies the hook into an isolated temp tree
(`<tmp>/.claude/hooks/post_write_register_task.py`,
`<tmp>/tasks/`, `<tmp>/PROJECT_KANBAN.md`) rather than touching the real
repo's PROJECT_KANBAN.md / tasks/.

Run with: python3 -m pytest .claude/hooks/tests/test_post_write_register_task_metadata.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "post_write_register_task.py",
)

KANBAN_STUB = """# PROJECT_KANBAN.md
**Last updated**: 2026-01-01

## Board

### Todo

### In Progress

### Ready for Review

### Done
"""


class HookSandbox:
    """Isolated <tmp>/.claude/hooks/, <tmp>/tasks/, <tmp>/PROJECT_KANBAN.md
    tree so the hook's own ROOT resolution (three dirs up from __file__)
    lands inside a throwaway directory instead of the real repo."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="t042_hook_sandbox_")
        hooks_dir = os.path.join(self.root, ".claude", "hooks")
        os.makedirs(hooks_dir)
        os.makedirs(os.path.join(self.root, "tasks"))
        self.hook_path = os.path.join(hooks_dir, "post_write_register_task.py")
        shutil.copy(HOOK_SRC, self.hook_path)
        self.kanban_path = os.path.join(self.root, "PROJECT_KANBAN.md")
        with open(self.kanban_path, "w") as f:
            f.write(KANBAN_STUB)

    def write_guide(self, task_id, body):
        path = os.path.join(self.root, "tasks", f"TASK_GUIDE_{task_id}.md")
        with open(path, "w") as f:
            f.write(body)
        return path

    def run_hook(self, file_path):
        event = {"tool_name": "Write", "tool_input": {"file_path": file_path}}
        result = subprocess.run(
            [sys.executable, self.hook_path],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        return result

    def kanban_text(self):
        with open(self.kanban_path) as f:
            return f.read()

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def _todo_row(kanban_text, task_id):
    for line in kanban_text.splitlines():
        if f"**{task_id}**" in line:
            return line
    return None


TEMPLATE_FORMAT_GUIDE = """# TASK_GUIDE — T900: Synthetic Fixture
**Date**: 2026-07-21
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P0
**Assigned agent**: common-infrastructure

## Requirement
Synthetic fixture guide for T042 regression tests.
"""


def test_extracts_full_template_format_metadata():
    """AC1: guide using the real template's `**X Level**: value` format
    registers with its real Complexity/Risk/Priority, not defaults."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T900", TEMPLATE_FORMAT_GUIDE)
        result = sandbox.run_hook(path)
        assert result.returncode == 0, result.stderr
        row = _todo_row(sandbox.kanban_text(), "T900")
        assert row is not None, sandbox.kanban_text()
        assert "C2" in row, row
        assert "High" in row, row
        assert "P0" in row, row
    finally:
        sandbox.cleanup()


MISSING_COMPLEXITY_GUIDE = """# TASK_GUIDE — T901: Missing Complexity Field
**Date**: 2026-07-21
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure

## Requirement
Synthetic fixture: Complexity Level line deliberately deleted.
"""


def test_missing_field_registers_as_visible_unknown_not_a_default():
    """AC2/AC4: a genuinely absent field must read `?`, never fall back to
    a plausible-looking value like `C1`."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T901", MISSING_COMPLEXITY_GUIDE)
        result = sandbox.run_hook(path)
        assert result.returncode == 0, result.stderr
        row = _todo_row(sandbox.kanban_text(), "T901")
        assert row is not None, sandbox.kanban_text()
        assert " ?  " in row or " ? |" in row or row.split("|")[2].strip() == "?", row
        assert "C1" not in row, row
    finally:
        sandbox.cleanup()


ABBREVIATED_RISK_GUIDE = """# TASK_GUIDE — T905: Abbreviated Risk Spelling
**Date**: 2026-07-21
**Complexity Level**: C1
**Risk Level**: Med
**Priority**: P1
**Assigned agent**: common-infrastructure

## Requirement
Synthetic fixture: `**Risk Level**: Med` (abbreviated spelling, not the full
`Medium`) — must exercise the normalizer, not just be captured verbatim.
"""


def test_abbreviated_risk_spelling_normalizes_to_medium():
    """AC5 (direct): the pattern's `Med(?:ium)?` alternative can capture the
    bare abbreviation `Med` (e.g. `**Risk Level**: Med`), which the
    normalizer must convert to the canonical `Medium` spelling — not leave
    as `Med` in the Kanban row."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T905", ABBREVIATED_RISK_GUIDE)
        result = sandbox.run_hook(path)
        assert result.returncode == 0, result.stderr
        row = _todo_row(sandbox.kanban_text(), "T905")
        assert row is not None, sandbox.kanban_text()
        assert "Risk: Medium" in row, row
    finally:
        sandbox.cleanup()


def test_duplicate_task_id_is_a_no_op():
    """AC3/AC6: if the task ID is already registered anywhere in the
    Kanban, the hook must exit 0 without touching the file."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T900", TEMPLATE_FORMAT_GUIDE)
        first = sandbox.run_hook(path)
        assert first.returncode == 0, first.stderr
        kanban_after_first = sandbox.kanban_text()

        second = sandbox.run_hook(path)
        assert second.returncode == 0, second.stderr
        kanban_after_second = sandbox.kanban_text()

        assert kanban_after_first == kanban_after_second
        assert kanban_after_second.count("**T900**") == 1
    finally:
        sandbox.cleanup()


BARE_FORMAT_GUIDE = """# TASK_GUIDE — T902: Bare Field Format
**Date**: 2026-07-21
Complexity: C3
Risk: Low
Priority: P2
Assigned agent: common-infrastructure

## Requirement
Synthetic fixture: bare `Field: value` format, no ** emphasis, no "Level"
label word — the widened pattern must still match this, not just the
template's exact punctuation (AC4's anti-regression clause).
"""


def test_bare_format_still_matches_widened_pattern():
    """AC4: the fix must widen the pattern (tolerate optional label word
    and emphasis), not swap the old rigid format for a new rigid format."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T902", BARE_FORMAT_GUIDE)
        result = sandbox.run_hook(path)
        assert result.returncode == 0, result.stderr
        row = _todo_row(sandbox.kanban_text(), "T902")
        assert row is not None, sandbox.kanban_text()
        assert "C3" in row, row
        assert "P2" in row, row
    finally:
        sandbox.cleanup()


ADVERSARIAL_PROSE_GUIDE = r"""# TASK_GUIDE — T903: Adversarial Prose Fixture
**Date**: 2026-07-21
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure

## Requirement

| Line | Regex | Template writes | Result |
|---|---|---|---|
| `:51` | `Complexity[:\s]+(C[0-3])` | `**Complexity Level**: C2` | no match |
| `:52` | `Risk[:\s]+(Low|Med(?:ium)?|High)` | `**Risk Level**: Medium` | no match |
| `:53` | `Priority[:\s]+(P[0-2])` | `**Priority**: P1` | no match |
"""


def test_regex_widening_does_not_match_prose_mentions_elsewhere():
    """Edge case from the guide: this file's own Requirement table contains
    the literal strings `Complexity[:\\s]+` and `**Complexity Level**: C2`
    as prose describing the bug, not a real field. The real field (header,
    C1/Medium/P1) must win because it appears first in the file — the
    widened pattern must not spuriously match the later prose table
    instead."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T903", ADVERSARIAL_PROSE_GUIDE)
        result = sandbox.run_hook(path)
        assert result.returncode == 0, result.stderr
        row = _todo_row(sandbox.kanban_text(), "T903")
        assert row is not None, sandbox.kanban_text()
        assert "C1" in row, row
        assert "C2" not in row, row
        assert "Medium" in row, row
        assert "P1" in row, row
    finally:
        sandbox.cleanup()


TITLE_AND_AGENT_REGRESSION_GUIDE = """# TASK_GUIDE — T904: Title And Agent Regression Guard
**Date**: 2026-07-21
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: qa-expert
**Agent guide**: `.claude/agents/qa.md`

## Requirement
Synthetic fixture guarding the T018/T024 title and agent extraction fixes.
"""


def test_title_and_agent_extraction_unaffected_by_the_fix():
    """AC7 (negative): the T018 title regex and T024 agent regex must keep
    behaving exactly as before this fix."""
    sandbox = HookSandbox()
    try:
        path = sandbox.write_guide("T904", TITLE_AND_AGENT_REGRESSION_GUIDE)
        result = sandbox.run_hook(path)
        assert result.returncode == 0, result.stderr
        row = _todo_row(sandbox.kanban_text(), "T904")
        assert row is not None, sandbox.kanban_text()
        assert "Title And Agent Regression Guard" in row, row
        assert "qa-expert" in row, row
    finally:
        sandbox.cleanup()


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        print(f"\n{failures} test(s) failed")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed")
