"""T169: the Writing Principles (ASD-STE100) section in CLAUDE.md and its mirrors.

Names are read out of CLAUDE.md at test time, never hardcoded in the mirror check.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
ADAPTERS = [ROOT / "AGENTS.md", ROOT / ".cursor" / "rules" / "agent-base.mdc"]
HEADING = "## Writing Principles (ASD-STE100)"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _section() -> str:
    text = CLAUDE_MD.read_text(encoding="utf-8")
    assert HEADING in text, "CLAUDE.md has no Writing Principles section"
    m = re.search(re.escape(HEADING) + r"(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m
    return m.group(1)


def _names() -> list[str]:
    rows = re.findall(r"^\|\s*([A-Za-z][A-Za-z ,]*?)\s*\|", _section(), re.M)
    return [r for r in rows if r != "Principle"]


def test_four_named_rows_with_limits():
    sec = _section()
    assert _names() == [
        "One Term, One Meaning",
        "Short Sentences",
        "One Action, Active Voice",
        "No Noun Stacks",
    ]
    header = next(l for l in sec.splitlines() if l.startswith("| Principle"))
    assert "Problem Addressed" in header and "Operational Command" in header
    for limit in ("20 words", "25 words", "3 nouns"):
        assert limit in sec


def test_scope_and_exemptions():
    sec = _norm(_section())
    assert "only to text a human reads" in sec
    for item in ("chat replies", "HTML reports", "spawn prompts", "TASK_GUIDEs",
                 "sub-agent reports", "Kanban rows", "commits"):
        assert item in sec, item
    assert "verbatim list" in sec and "unchanged" in sec


def test_keep_the_term_glossary_and_link_word():
    sec = _norm(_section())
    assert "Keep the key term exactly" in sec
    assert "never replace it with a paraphrase" in sec
    assert "only if the reader may not know it" in sec
    assert "glossary term counts as one noun" in sec
    assert "link word" in sec and "because, so, unless, only if" in sec


def test_prose_sentences_within_25_words():
    prose = [l for l in _section().splitlines() if l.strip() and not l.startswith("|")]
    for line in prose:
        for sentence in re.split(r"(?<=[.!?:])\s+", re.sub(r"`[^`]*`", "X", line)):
            assert len(sentence.split()) <= 25, sentence


def test_no_role_guide_carries_the_table():
    for path in (ROOT / "agents").glob("*.md"):
        assert "One Term, One Meaning" not in path.read_text(encoding="utf-8"), path.name


def test_adapters_list_the_names():
    for path in ADAPTERS:
        text = _norm(path.read_text(encoding="utf-8"))
        assert "Writing Principles (ASD-STE100)" in text, path.name
        for name in _names():
            assert _norm(name) in text, (path.name, name)


def test_response_standard_bullet_points_to_section():
    text = CLAUDE_MD.read_text(encoding="utf-8")
    bullet = next(l for l in text.splitlines() if l.startswith("- Write for a reader"))
    assert "Writing Principles" in bullet
    assert "text a human reads" in bullet
