"""T258: the TASK_GUIDE template makes the Stage 2 author list pre-existing pin tests (AC 1-3)."""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "TASK_GUIDE_template.md"


def _section(heading):
    text = TEMPLATE.read_text(encoding="utf-8")
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start:end if end != -1 else len(text)]


def _pin_row():
    rows = [r for r in _section("## Files to Change (Predicted)").splitlines()
            if r.startswith("| Pre-existing pin tests")]
    assert len(rows) == 1, "Files to Change needs exactly one 'Pre-existing pin tests' row"
    return rows[0]


def test_ac1_row_names_what_to_list_and_the_handling():
    row = _pin_row()
    for word in ("text", "size", "line count", "location", "baseline ref",
                 "repoint", "narrow", "escalate"):
        assert word in row, word


def test_ac2_row_names_how_to_find_them():
    row = _pin_row()
    for word in (".claude/hooks/tests/", "tests/", "grep", "test_agent_guide_dedup.py",
                 "test_vital_slice.py", "memory budget"):
        assert word in row, word


def test_ac3_edge_case_checklist_has_the_preflight_line():
    lines = [l for l in _section("## Edge Case Checklist").splitlines()
             if l.startswith("- [ ]") and "pin test" in l.lower()]
    assert len(lines) == 1
    assert "Pre-existing pin tests" in lines[0]
