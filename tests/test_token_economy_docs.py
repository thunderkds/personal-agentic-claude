"""T127 — the verbatim-preserve rule, the token-economy doc and the over-engineering persona.

SC2: CLAUDE.md points at docs/claude-md/token-economy.md; it does not carry the doc's body.
SC3: the doc states the five verbatim items, the point-not-paste rule, that the Evidence table
     still carries full output, and names scripts/token_meter.py.
SC4: skills/code-review/SKILL.md has an over-engineering-reviewer row with an activation
     condition and the four checks, cites "Search Before You Build" and none of its rungs.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
DOC = ROOT / "docs" / "claude-md" / "token-economy.md"
REVIEW = ROOT / "skills" / "code-review" / "SKILL.md"
TEMPLATE = ROOT / "agents" / "general-agent-template.md"
POINTER = "docs/claude-md/token-economy.md"


def _persona_row() -> str:
    for line in REVIEW.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and "over-engineering-reviewer" in line:
            return line
    return ""


def test_sc2_claude_md_points_and_does_not_carry_the_body():
    text = CLAUDE_MD.read_text(encoding="utf-8")
    assert POINTER in text, "CLAUDE.md has no pointer to docs/claude-md/token-economy.md"
    assert DOC.exists(), f"{POINTER} does not exist; the pointer is dangling"
    # The doc's own body sentences must not be pasted into CLAUDE.md.
    for body in ("point to evidence by path:line", "Evidence table still carries full output"):
        assert body not in text, f"CLAUDE.md carries the doc body ({body!r}); it must point, not copy"


def test_sc3_doc_states_the_five_items_the_pointer_rule_and_the_meter():
    doc = DOC.read_text(encoding="utf-8")
    for item in ("code", "exact error text", "file paths", "commands", "security warnings"):
        assert item in doc, f"token-economy.md does not list verbatim item {item!r}"
    assert "point to evidence by path:line" in doc
    assert "TASK_REVIEW_Txxx.md" in doc
    assert "Evidence table still carries full output" in doc
    assert "scripts/token_meter.py" in doc


def test_sc4_code_review_has_the_over_engineering_persona():
    row = _persona_row()
    assert row, "no over-engineering-reviewer persona row in skills/code-review/SKILL.md"
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert len(cells) == 2 and len(cells[1]) > 40, f"persona has no concrete activation condition: {row}"
    low = row.lower()
    for check in ("one caller", "≤ 10 lines", "config", "stdlib"):
        assert check in low, f"persona row misses the check {check!r}"
    text = REVIEW.read_text(encoding="utf-8")
    assert "Search Before You Build" in text, "persona does not cite Search Before You Build by name"
    rungs = re.findall(r"^\d+\.\s+(.+?)\s+—", TEMPLATE.read_text(encoding="utf-8"), re.M)
    assert len(rungs) >= 6, "could not read the ladder rungs from the template; the check would be vacuous"
    for rung in rungs:
        assert rung not in text, f"code-review copies a ladder rung: {rung!r}"
