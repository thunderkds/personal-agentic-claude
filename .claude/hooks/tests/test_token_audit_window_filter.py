"""Tests for T050 — scoping the token-audit generator to a window start date.

Covers TASK_GUIDE_T050.md's AC1-AC4:
  AC1 — default (no window_start) behavior is unchanged, unfiltered
  AC2 — a window_start filters build_entries() to only >= window_start records
  AC3 — a record dated exactly == window_start is a boundary inclusion, not exclusion
  AC4 — no entry-format/classification/cache-heuristic change; filtering only
Also covers the Edge Case Checklist:
  - an unparseable ("?") date is excluded (not crashed, not silently included)
    once a window filter is active
  - repeated runs with identical arguments remain idempotent
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import token_audit  # noqa: E402


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def test_default_window_start_none_includes_everything(tmp_path):
    """AC1: no window_start given -> unfiltered, same as before T050."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T100.jsonl",
        [
            {
                "timestamp": "2026-07-01T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            },
            {
                "timestamp": "2026-08-04T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            },
        ],
    )
    entries = token_audit.build_entries(str(trace_dir))
    assert len(entries) == 2


def test_window_start_excludes_records_before_it(tmp_path):
    """AC2: only records with derived date >= window_start are emitted."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T101.jsonl",
        [
            {
                "timestamp": "2026-07-21T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            },
            {
                "timestamp": "2026-08-04T09:00:00+00:00",
                "tool_name": "Skill",
                "summary": json.dumps({"skill": "wake"}),
                "is_error": False,
            },
        ],
    )
    entries = token_audit.build_entries(str(trace_dir), window_start="2026-08-04")
    assert len(entries) == 1
    assert entries[0][0] == "2026-08-04"
    assert entries[0][1] == "cold-start"


def test_window_start_boundary_is_inclusive(tmp_path):
    """AC3: a record dated exactly == window_start is included, not excluded."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T102.jsonl",
        [
            {
                "timestamp": "2026-08-04T00:00:01+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            }
        ],
    )
    entries = token_audit.build_entries(str(trace_dir), window_start="2026-08-04")
    assert len(entries) == 1
    assert entries[0][0] == "2026-08-04"


def test_unparseable_date_excluded_when_filter_active_not_crashed(tmp_path, capsys):
    """Edge case: a record whose timestamp can't be parsed to a date ("?")
    must not crash the filter and must not be silently included."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T103.jsonl",
        [
            {
                "timestamp": "not-a-real-timestamp",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            }
        ],
    )
    entries = token_audit.build_entries(str(trace_dir), window_start="2026-08-04")
    assert entries == []
    captured = capsys.readouterr()
    assert "WARNING" in captured.err


def test_entry_format_unchanged_by_filtering(tmp_path):
    """AC4: filtering does not alter entry shape/classification/cache heuristic."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T104.jsonl",
        [
            {
                "timestamp": "2026-08-04T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": json.dumps({"model": "sonnet"}),
                "is_error": False,
            },
            {
                "timestamp": "2026-08-04T10:05:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            },
        ],
    )
    unfiltered = token_audit.build_entries(str(trace_dir))
    filtered = token_audit.build_entries(str(trace_dir), window_start="2026-08-04")
    assert unfiltered == filtered
    # cache heuristic: first occurrence of a task-tag is `miss`, next is `hit`.
    caches = [e[3] for e in filtered]
    assert caches == ["miss", "hit"]


def test_generate_report_header_reflects_window_start(tmp_path):
    """New window's report header shows the new window's start date, not the
    stale module-level WINDOW_DATE constant."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T105.jsonl",
        [
            {
                "timestamp": "2026-08-04T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            }
        ],
    )
    report_path = tmp_path / "reports" / "token-audit_2026-08-04.md"
    token_audit.generate_report(
        str(trace_dir), str(report_path), window_start="2026-08-04"
    )
    text = report_path.read_text(encoding="utf-8")
    assert "Window opened 2026-08-04" in text


def test_generate_report_with_window_start_is_idempotent(tmp_path):
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T106.jsonl",
        [
            {
                "timestamp": "2026-08-04T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            }
        ],
    )
    report_path = tmp_path / "reports" / "token-audit_2026-08-04.md"
    token_audit.generate_report(str(trace_dir), str(report_path), window_start="2026-08-04")
    first = report_path.read_text(encoding="utf-8")
    token_audit.generate_report(str(trace_dir), str(report_path), window_start="2026-08-04")
    second = report_path.read_text(encoding="utf-8")
    assert first == second
