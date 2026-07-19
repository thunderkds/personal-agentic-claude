"""Format/convention test for the Token Audit Log scaffold (T028, DDR-0001).

Validates that reports/token-audit_2026-07-17.md documents the required
convention elements and that its sample entries match the entry regex the
convention defines. Also asserts a malformed entry (missing the Task-ID/
overhead tag) is rejected by that same regex, so the format is actually
constraining rather than decorative (Hard-Stop Gate 5).
"""
import re
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parents[3] / "reports" / "token-audit_2026-07-17.md"

ENTRY_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2} \| "
    r"(cold-start|stage-[0-9.]+|spawn|cost) \| "
    r"(T\d+|overhead) \| "
    r"(hit|miss) \| "
    r"(haiku|sonnet|opus) \| "
    r".+$"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_scaffold_file_exists():
    assert REPORT_PATH.is_file()


def test_header_documents_required_convention_elements():
    text = _report_text().lower()
    required_phrases = [
        "window-close condition",
        "7 logged sessions or 14 calendar days",
        "task-tag",
        "cache",
        "model-tier",
        "/cost",
    ]
    for phrase in required_phrases:
        assert phrase in text, f"missing required convention element: {phrase!r}"


def test_sample_entries_match_entry_regex():
    text = _report_text()
    sample_block = text.split("## Sample entries")[1].split("## Real entries")[0]
    sample_lines = [
        line for line in sample_block.splitlines()
        if re.match(r"^\d{4}-\d{2}-\d{2} \|", line.strip())
    ]
    assert len(sample_lines) >= 3
    for line in sample_lines:
        assert ENTRY_REGEX.match(line), f"sample entry did not match format: {line!r}"


def test_malformed_entry_missing_task_tag_is_rejected():
    malformed = "2026-07-17 | spawn | hit | sonnet | missing the task-tag field"
    assert not ENTRY_REGEX.match(malformed)


def test_memory_md_hot_tier_stays_within_line_limit():
    memory_path = Path(__file__).resolve().parents[3] / "memory" / "MEMORY.md"
    lines = memory_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 200
