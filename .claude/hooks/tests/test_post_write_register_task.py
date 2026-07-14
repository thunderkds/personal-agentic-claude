"""Regression test for the title-extraction regex in post_write_register_task.py.

Bug (T018): the `extract()` call for `title` used regex
`^#\\s+TASK_GUIDE[_\\s]+T\\d+[:\\s—-]+(.+)$`, whose character class between
`TASK_GUIDE` and `T\\d+` did not include an em-dash. Real guide headings are
formatted `# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint`, so the match
failed and extraction silently fell back to "untitled".
"""
import re

# Mirrors the fixed pattern in .claude/hooks/post_write_register_task.py.
TITLE_PATTERN = r"^#\s+TASK_GUIDE[_\s—-]+T\d+[:\s—-]+(.+)$"


def extract_title(heading: str) -> str:
    m = re.search(TITLE_PATTERN, heading, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else "untitled"


def test_extracts_title_with_em_dash_separator():
    heading = "# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint"
    assert extract_title(heading) == "CLI Wiring — Typer Entrypoint"


def test_extracts_title_with_underscore_separator():
    heading = "# TASK_GUIDE_T001: Simple Title"
    assert extract_title(heading) == "Simple Title"


def test_extracts_title_with_hyphen_separator():
    heading = "# TASK_GUIDE-T002: Another Title"
    assert extract_title(heading) == "Another Title"


def test_falls_back_to_untitled_when_no_title_present():
    heading = "# Not a task guide heading"
    assert extract_title(heading) == "untitled"


def test_extracts_title_from_multiline_file_content():
    # Real guide files are multi-line; without re.MULTILINE, `^`/`$` anchor to
    # the whole string, not the first line, and the match silently fails.
    guide = (
        "# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint\n"
        "**Date**: 2026-07-14\n"
        "**Complexity Level**: C1\n"
    )
    assert extract_title(guide) == "CLI Wiring — Typer Entrypoint"
