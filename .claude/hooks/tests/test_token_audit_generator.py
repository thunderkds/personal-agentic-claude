"""Tests for scripts/token_audit.py — the T040 Token Audit Log generator.

Covers TASK_GUIDE_T040.md's AC1-AC8:
  AC1 — entries emitted in DDR-0001 exact format
  AC2 — Agent->spawn, Skill(wake)->cold-start, Skill(stage-mapped)->stage-N
  AC3 — untagged records tag `overhead`, never dropped
  AC4 — reports/token-audit_2026-07-21.md exists, DDR-0001 header, opens 2026-07-21
  AC5 — idempotent: running twice produces byte-identical output
  AC6 — negative: no token count ever emitted/estimated/inferred
  AC7 — negative: reports/token-audit_2026-07-17.md left intact, closed-inconclusive
  AC8 — negative: reports/token-audit_2026-07-21.md is not gitignored
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import token_audit  # noqa: E402

ENTRY_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2} \| "
    r"(cold-start|stage-[0-9.]+|spawn) \| "
    r"(T\d+|overhead) \| "
    r"(hit|miss) \| "
    r"(haiku|sonnet|opus|\?) \| "
    r".+$"
)


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def test_fixture_trace_produces_spawn_cold_start_and_overhead_entries(tmp_path):
    """AC1, AC2, AC3: 1 Agent (T001) + 1 wake Skill (untagged) + 1 code-review
    Skill (untagged) -> spawn/T001, cold-start/overhead, stage-4/overhead."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T001.jsonl",
        [
            {
                "timestamp": "2026-07-21T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": json.dumps({"subagent_type": "backend-developer"}),
                "is_error": False,
            }
        ],
    )
    _write_jsonl(
        trace_dir / "_untagged.jsonl",
        [
            {
                "timestamp": "2026-07-21T09:00:00+00:00",
                "tool_name": "Skill",
                "summary": json.dumps({"skill": "wake"}),
                "is_error": False,
            },
            {
                "timestamp": "2026-07-21T09:30:00+00:00",
                "tool_name": "Skill",
                "summary": json.dumps({"skill": "code-review"}),
                "is_error": False,
            },
        ],
    )

    entries = token_audit.build_entries(str(trace_dir))
    assert len(entries) == 3

    events = sorted(e[1] for e in entries)
    assert events == ["cold-start", "spawn", "stage-4"]

    tags = {e[1]: e[2] for e in entries}
    assert tags["spawn"] == "T001"
    assert tags["cold-start"] == "overhead"
    assert tags["stage-4"] == "overhead"

    for entry in entries:
        line = f"{entry[0]} | {entry[1]} | {entry[2]} | {entry[3]} | {entry[4]} | {entry[5]}"
        assert ENTRY_REGEX.match(line), line


def test_non_agent_non_skill_records_are_not_emitted(tmp_path):
    """A plain Read/Bash record carries no Token Audit Log event on its own."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T002.jsonl",
        [
            {
                "timestamp": "2026-07-21T10:00:00+00:00",
                "tool_name": "Read",
                "summary": json.dumps({"file_path": "README.md"}),
                "is_error": False,
            }
        ],
    )
    entries = token_audit.build_entries(str(trace_dir))
    assert entries == []


def test_generator_is_idempotent(tmp_path):
    """AC5: running the generator twice on the same trace produces byte-identical output."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T003.jsonl",
        [
            {
                "timestamp": "2026-07-21T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            }
        ],
    )
    report_path = tmp_path / "reports" / "token-audit_2026-07-21.md"

    token_audit.generate_report(str(trace_dir), str(report_path))
    first = report_path.read_text(encoding="utf-8")

    token_audit.generate_report(str(trace_dir), str(report_path))
    second = report_path.read_text(encoding="utf-8")

    assert first == second


def test_absent_trace_dir_exits_clean_no_crash(tmp_path):
    """Negative: absent memory/event-trace/ -> no crash, no malformed file, 0 entries."""
    trace_dir = tmp_path / "does-not-exist"
    report_path = tmp_path / "reports" / "token-audit_2026-07-21.md"

    count = token_audit.generate_report(str(trace_dir), str(report_path))
    assert count == 0
    text = report_path.read_text(encoding="utf-8")
    assert "Window opened 2026-07-21" in text
    assert "no trace data found" in text


def test_empty_trace_dir_exits_clean(tmp_path):
    trace_dir = tmp_path / "event-trace"
    trace_dir.mkdir()
    report_path = tmp_path / "reports" / "token-audit_2026-07-21.md"

    count = token_audit.generate_report(str(trace_dir), str(report_path))
    assert count == 0
    assert report_path.is_file()


def test_malformed_jsonl_line_is_skipped_not_crashed(tmp_path, capsys):
    """Negative: a malformed line is skipped with a warning; other lines still emit."""
    trace_dir = tmp_path / "event-trace"
    trace_dir.mkdir(parents=True)
    good = {
        "timestamp": "2026-07-21T10:00:00+00:00",
        "tool_name": "Agent",
        "summary": "{}",
        "is_error": False,
    }
    with open(trace_dir / "T004.jsonl", "w", encoding="utf-8") as f:
        f.write("{not valid json\n")
        f.write(json.dumps(good) + "\n")

    entries = token_audit.build_entries(str(trace_dir))
    assert len(entries) == 1
    captured = capsys.readouterr()
    assert "WARNING" in captured.err


def test_no_token_counts_ever_appear_in_output(tmp_path):
    """AC6: negative — no synthesized/estimated token count anywhere in output."""
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T005.jsonl",
        [
            {
                "timestamp": "2026-07-21T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": json.dumps({"model": "opus"}),
                "is_error": False,
            }
        ],
    )
    report_path = tmp_path / "reports" / "token-audit_2026-07-21.md"
    token_audit.generate_report(str(trace_dir), str(report_path))
    text = report_path.read_text(encoding="utf-8").lower()
    # No numeric-followed-by-tokens pattern (e.g. "~6k tokens", "1200 tokens")
    # anywhere — a synthesized/estimated count, never legitimate here.
    assert not re.search(r"[\d~]\s*k?\s*tokens?\b", text)


def test_model_tier_extracted_when_present_else_question_mark(tmp_path):
    trace_dir = tmp_path / "event-trace"
    _write_jsonl(
        trace_dir / "T006.jsonl",
        [
            {
                "timestamp": "2026-07-21T10:00:00+00:00",
                "tool_name": "Agent",
                "summary": json.dumps({"model": "sonnet"}),
                "is_error": False,
            },
            {
                "timestamp": "2026-07-21T10:05:00+00:00",
                "tool_name": "Agent",
                "summary": "{}",
                "is_error": False,
            },
        ],
    )
    entries = token_audit.build_entries(str(trace_dir))
    tiers = [e[4] for e in entries]
    assert "sonnet" in tiers
    assert "?" in tiers


# --- AC7: reports/token-audit_2026-07-17.md is left intact, closed-inconclusive ---

def test_old_window_file_intact_and_closed_inconclusive():
    old_path = ROOT / "reports" / "token-audit_2026-07-17.md"
    text = old_path.read_text(encoding="utf-8")
    assert "CLOSED INCONCLUSIVE" in text
    # Original sample entries are still present, not deleted.
    assert "2026-07-17 | cold-start | overhead | miss | sonnet" in text


# --- AC4 / AC8: real report exists, DDR-0001 header, not gitignored ---

def test_real_report_generation_and_gitignore():
    report_path = ROOT / "reports" / "token-audit_2026-07-21.md"
    text = report_path.read_text(encoding="utf-8")
    assert "Window opened 2026-07-21" in text
    assert "window-close condition" in text.lower()

    result = subprocess.run(
        ["git", "check-ignore", "-q", "reports/token-audit_2026-07-21.md"],
        cwd=str(ROOT),
    )
    assert result.returncode != 0, "reports/token-audit_2026-07-21.md must NOT be gitignored (AC8)"
