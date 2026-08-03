#!/usr/bin/env python3
"""Regression tests for the T045 fix: `find_kanban_section` (pre_agent_validate_guide.py)
and `tasks_in_section` (pre_bash_block_unsafe_merge.py) must anchor their terminating
`###` lookahead to line start, not match a literal `###` quoted inside a row's text.

Reproduces the real 2026-07-23 defect: T039's Done row quoted the phrase
`` `### Hard-Stop Gates` `` while summarizing that task's review findings, which
truncated the Done section right there — every row below it (T042, T038, T022, ...)
became invisible to both hooks. See memory/learnings.md: "Never quote a `###`
heading inside a KANBAN row."

Run with: python3 -m pytest .claude/hooks/tests/test_kanban_section_parsing.py -v
"""
import importlib.util
import os
import re
import sys
import types

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))

VALIDATE_GUIDE_PATH = os.path.join(HOOKS_DIR, "pre_agent_validate_guide.py")
BLOCK_MERGE_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")


def _load(path, name):
    """pre_agent_validate_guide.py is import-safe (main() is guarded by
    `if __name__ == "__main__"`)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_bare_main_hook(path, name):
    """pre_bash_block_unsafe_merge.py ends in a bare `main()` call (no
    __main__ guard), which would block on stdin at import time. Strip only
    that trailing call — same pattern as test_merge_gate_evidence.py."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


validate_guide = _load(VALIDATE_GUIDE_PATH, "pre_agent_validate_guide")
block_merge = _load_bare_main_hook(BLOCK_MERGE_PATH, "pre_bash_block_unsafe_merge")


# --- Fixture reproducing the real 2026-07-23 board shape ---------------------------
# T039's Done row (verbatim, from git history at dd76c96) quotes `### Hard-Stop Gates`
# inline. T042, T038 follow it in the same Done section — the real board also has
# T022 further down, but two is enough to prove "everything below the quote vanishes".

FIXTURE_KANBAN = """# PROJECT_KANBAN.md

## Board

### Todo
- [ ] **T043** — Fix trace/step-limit task attribution | Common-Infrastructure-Agent | C2 | Risk: Medium | P0

### In Progress
- [ ] **T050** — In-flight task | Backend-Implementer | C1 | Risk: Low | P1

### Ready for Review

### Done
- [x] **T039** — Dedup the `## Skills vs Agents` section in CLAUDE.md — Stage 4: 1 P0 (false `verify` Evidence claim) + 2 P1 (AC5 checksum was vacuous — `^## ` couldn't match the real `### Hard-Stop Gates` H3, so both sides extracted empty strings and compared equal) | C2 | Completed: 2026-07-23
- [x] **T042** — Fix post_write_register_task.py Complexity/Risk/Priority extraction | C1 | Completed: 2026-07-21
- [x] **T038** — Fix setup.sh piped curl \\| sh install | C2 | Completed: 2026-07-19
"""


def _write_fixture_kanban(monkeypatch, module, text):
    """Point module.KANBAN at a temp file with the given text (does not touch
    the real PROJECT_KANBAN.md)."""
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    monkeypatch.setattr(module, "KANBAN", path)
    return path


# --- AC2 (validate_guide): every row survives a `###`-quoting Done row -------------

def test_find_kanban_section_survives_inline_hash_quote(monkeypatch):
    path = _write_fixture_kanban(monkeypatch, validate_guide, FIXTURE_KANBAN)
    try:
        assert validate_guide.find_kanban_section("T039") == "Done"
        assert validate_guide.find_kanban_section("T042") == "Done"
        assert validate_guide.find_kanban_section("T038") == "Done"
    finally:
        os.remove(path)


# --- AC3: generalization — `#`, `##`, `####` inline must not truncate either ------

def test_find_kanban_section_survives_various_inline_hash_counts(monkeypatch):
    fixture = FIXTURE_KANBAN.replace(
        "T039**",
        "T039** — mentions #hashtag, ## two, #### four,"
    )
    path = _write_fixture_kanban(monkeypatch, validate_guide, fixture)
    try:
        assert validate_guide.find_kanban_section("T039") == "Done"
        assert validate_guide.find_kanban_section("T042") == "Done"
        assert validate_guide.find_kanban_section("T038") == "Done"
    finally:
        os.remove(path)


# --- AC4: positive — real section boundaries are unchanged, no false-negative ------

def test_find_kanban_section_todo_never_resolves_as_done(monkeypatch):
    path = _write_fixture_kanban(monkeypatch, validate_guide, FIXTURE_KANBAN)
    try:
        assert validate_guide.find_kanban_section("T043") == "Todo"
        assert validate_guide.find_kanban_section("T050") == "In Progress"
        assert validate_guide.find_kanban_section("T999") is None
    finally:
        os.remove(path)


def test_find_kanban_section_on_real_current_board():
    """AC4: the actual live PROJECT_KANBAN.md — every task resolves to its
    true section (no regression on the real file)."""
    kanban_path = os.path.join(ROOT, "PROJECT_KANBAN.md")
    with open(kanban_path) as f:
        text = f.read()
    done_ids = re.findall(r"- \[x\] \*\*(T\d+)\*\*", text)
    assert done_ids, "fixture assumption broken: no Done tasks found on real board"
    for tid in done_ids:
        assert validate_guide.find_kanban_section(tid) == "Done", tid


# --- AC6: negative — empty / missing / malformed board still behaves as before -----

def test_find_kanban_section_missing_file(monkeypatch):
    monkeypatch.setattr(validate_guide, "KANBAN", os.path.join(ROOT, "no-such-file.md"))
    assert validate_guide.find_kanban_section("T001") is None


def test_find_kanban_section_empty_file(monkeypatch):
    path = _write_fixture_kanban(monkeypatch, validate_guide, "")
    try:
        assert validate_guide.find_kanban_section("T001") is None
    finally:
        os.remove(path)


# --- AC5 (block_merge): tasks_in_section returns the complete set -------------------

def _tasks_in_section_impl(kanban_text, section_title):
    """block_merge.tasks_in_section is a closure defined inside main(); exercise
    the same regex logic directly against fixture text the way main() would."""
    m = re.search(
        rf"### {re.escape(section_title)}\n(.*?)(?=^###|\Z)", kanban_text,
        re.DOTALL | re.MULTILINE,
    )
    if not m:
        return []
    block = m.group(1).strip()
    return [
        re.search(r"\*\*(T\d+)\*\*", line).group(1)
        for line in block.splitlines()
        if line.strip().startswith("- ") and re.search(r"\*\*(T\d+)\*\*", line)
    ]


def test_tasks_in_section_survives_inline_hash_quote_in_earlier_section():
    """The merge-gate half: an inline `###` in an *earlier* section (Done, which
    comes before In Progress in board order in some layouts) must not swallow a
    later section's rows. Uses a fixture where Done (with the quote) appears
    before In Progress."""
    fixture = """# PROJECT_KANBAN.md

### Done
- [x] **T039** — mentions `### Hard-Stop Gates` inline | C2 | Completed: 2026-07-23
- [x] **T042** — later Done row | C1 | Completed: 2026-07-21

### In Progress
- [ ] **T050** — should still be found | Backend-Implementer | C1 | Risk: Low | P1
- [ ] **T051** — also found | Backend-Implementer | C1 | Risk: Low | P1
"""
    assert _tasks_in_section_impl(fixture, "In Progress") == ["T050", "T051"]
    assert _tasks_in_section_impl(fixture, "Done") == ["T039", "T042"]


def test_tasks_in_section_on_real_pre_bash_block_unsafe_merge_module():
    """Confirms the actual module source (not the reimplementation above) now
    uses the anchored, MULTILINE pattern — reading the source is the only way
    to check the closure without invoking the full hook's stdin protocol."""
    with open(BLOCK_MERGE_PATH) as f:
        src = f.read()
    assert "re.MULTILINE" in src
    assert "(?=^###|\\Z)" in src


# --- AC7: pre_agent_validate_guide.py's existing tests still pass unchanged --------
# (exercised by running the full suite in Verification Command, not duplicated here)
