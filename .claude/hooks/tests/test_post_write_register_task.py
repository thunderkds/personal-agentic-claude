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


# ---------------------------------------------------------------------------
# Regression test for the agent-extraction regex (T024).
#
# Bug: `(?:Assigned Agent|Agent)[:\s]+([a-z\-]+)` matched the substring
# "Agent guide" (from the `**Agent guide**: ...` line) instead of "Assigned
# agent", because the markdown bold markers (`**`) sit between "agent" and
# its colon on the intended line, breaking that match attempt and letting
# `re.search` fall through to the next "Agent" occurrence in the file —
# same boundary-matching bug class as the T018 title regex.
# ---------------------------------------------------------------------------
AGENT_PATTERN = r"Assigned\s+Agent\*{0,2}[:\s]+([a-z\-]+)"


def extract_agent(guide: str) -> str:
    m = re.search(AGENT_PATTERN, guide, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else "backend-developer"


def test_extracts_agent_when_agent_guide_line_precedes_in_scan_order():
    # Real guides list "Agent guide" immediately after "Assigned agent", and
    # both start with the word "Agent" — the old pattern's bare "Agent"
    # alternative could latch onto the wrong line.
    guide = (
        "**Assigned agent**: backend-developer\n"
        "**Agent guide**: `.claude/agents/backend.md`\n"
    )
    assert extract_agent(guide) == "backend-developer"


def test_extracts_agent_regardless_of_line_order():
    guide = (
        "**Agent guide**: `.claude/agents/backend.md`\n"
        "**Assigned agent**: qa-expert\n"
    )
    assert extract_agent(guide) == "qa-expert"


def test_falls_back_to_default_when_no_assigned_agent_line_present():
    guide = "**Agent guide**: `.claude/agents/backend.md`\n"
    assert extract_agent(guide) == "backend-developer"
