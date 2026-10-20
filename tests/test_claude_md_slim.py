"""T169 scope extension: CLAUDE.md stays at or under 200 lines and keeps the rules the cuts must not lose."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t)


def test_claude_md_is_at_most_200_lines():
    assert len(TEXT.splitlines()) <= 200


def test_wake_mandate_kept():
    n = _norm(TEXT)
    assert 'Skill({ skill: "wake" })' in n
    assert "not optional" in n
    assert "user jumps straight to a task" in n


def test_agent_template_pointer_and_base_rules_kept():
    n = _norm(TEXT)
    assert "agents/general-agent-template.md" in n
    assert "docs/claude-md/untrusted-content-boundary.md" in n
    assert "Complexity Level (C0–C3)" in n
    assert "Risk Level" in n


def test_phase0_trigger_kept_after_final_instruction_cut():
    assert "Start new project supervision" in TEXT
