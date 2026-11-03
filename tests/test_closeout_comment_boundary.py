"""T244 — the auto close-out writes `Closed:` into the report, never into the template comment.

T242's review file held the filled `## Auto decisions` block, then the template's
`<!-- Optional: the final report ... ## Auto decisions ... -->` comment. The block ran on to the
commented heading, so `add_line` appended `Closed:` inside the comment, where a rendered page
hides it.

Run with: python3 -m pytest tests/test_closeout_comment_boundary.py -q
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "lib"))
import auto_closeout as ac  # noqa: E402
import auto_mode as am  # noqa: E402

REPORT = """# TASK_REVIEW — T999: example

## Auto decisions

Mode: auto
1. a decision — RULE: a rule
Memory: nothing new
Not done: merge (yours); auto verify: pass

<!-- Optional: the final report. Copy the block below out of this comment.
After an auto verify pass the hook adds `Closed:`.

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
-->

## Evidence
"""

CLOSED = "Closed: row moved to Done 2026-11-03 — auto verify pass"


def _comment_start(text):
    return text.index("<!-- Optional")


def test_section_ends_where_a_comment_begins():
    start, end, body = am.section(REPORT, am.AUTO_SECTION, skip_comments=True)
    assert "<!--" not in body, body
    assert end <= _comment_start(REPORT)


def test_closed_line_lands_in_the_report_block_not_the_comment(tmp_path):
    path = tmp_path / "TASK_REVIEW_T999.md"
    path.write_text(REPORT, encoding="utf-8")
    assert ac.add_line(str(path), "T999", False, CLOSED)
    text = path.read_text(encoding="utf-8")
    assert text.index(CLOSED) < _comment_start(text), text
    assert text.count(CLOSED) == 1


def test_add_line_is_still_once_only(tmp_path):
    path = tmp_path / "TASK_REVIEW_T999.md"
    path.write_text(REPORT, encoding="utf-8")
    ac.add_line(str(path), "T999", False, CLOSED)
    ac.add_line(str(path), "T999", False, CLOSED)
    assert path.read_text(encoding="utf-8").count(CLOSED) == 1


def test_a_block_with_no_comment_after_it_is_unchanged():
    text = "## Auto decisions\n\nMode: auto\n1. x — RULE: y\n\n## Evidence\n"
    start, end, body = am.section(text, am.AUTO_SECTION, skip_comments=True)
    assert body == "\nMode: auto\n1. x — RULE: y\n\n"
