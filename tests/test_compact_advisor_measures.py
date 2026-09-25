"""T126 SC6 — compact-advisor decides on a measured context size, not a feeling."""
import re
from pathlib import Path

SKILL = " ".join((Path(__file__).resolve().parent.parent / "skills" / "compact-advisor"
                  / "SKILL.md").read_text().split())


def test_sc6_names_the_measuring_command():
    assert "python3 scripts/token_meter.py --current --json" in SKILL
    assert "context_now" in SKILL


def test_sc6_keeps_the_fallback_when_the_command_fails():
    assert re.search(r"fail", SKILL, re.IGNORECASE)
    assert "judgment signals" in SKILL


def test_sc6_no_longer_claims_the_size_is_unknowable():
    assert "no tool exposes your own context size" not in SKILL


def test_sc6_150k_is_a_reference_not_a_trigger():
    assert "150k" in SKILL
    assert "reference point" in SKILL
    assert re.search(r"not a trigger", SKILL)
