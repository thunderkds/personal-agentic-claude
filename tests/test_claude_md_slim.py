"""T169 scope extension: CLAUDE.md stays at or under 200 lines and keeps the rules the cuts must not lose.

REPOINTED by T173 (`CLAUDE.md` -> `AGENTS.md`): the doctrine moved to AGENTS.md and CLAUDE.md is
the one-line import `@AGENTS.md`, so the cap and the kept rules apply to AGENTS.md (T173 AC 7).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "AGENTS.md").read_text(encoding="utf-8")


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
    assert "templates/general-agent-template.md" in n
    assert "docs/claude-md/untrusted-content-boundary.md" in n
    assert "Complexity Level (C0–C3)" in n
    assert "Risk Level" in n


def test_phase0_trigger_kept_after_final_instruction_cut():
    assert "Start new project supervision" in TEXT
