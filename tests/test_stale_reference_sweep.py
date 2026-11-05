"""T259: `code-review` gains a stale-reference sweep; the TASK_GUIDE template gains a matching
Edge Case Checklist line.

Doc-content asserts in the style of `tests/test_t245_ux_evaluate.py`. Each test names the
Acceptance Criterion of `tasks/TASK_GUIDE_T259.md` it covers. The asserts read only the sweep
paragraph (or the one checklist line), so a mention elsewhere in the file cannot satisfy them.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CODE_REVIEW = ROOT / "skills" / "code-review" / "SKILL.md"
TEMPLATE = ROOT / "templates" / "TASK_GUIDE_template.md"
CODEX_CAP = 8192  # lib/harness-fetch.sh skips a Codex skill body over 8 KB


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sweep_paragraph(path: Path = CODE_REVIEW) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\*\*Stale-reference sweep[^\n]*(?:\n[^\n]+)*", text, re.M)
    assert m, "skills/code-review/SKILL.md has no '**Stale-reference sweep' paragraph"
    return _norm(m.group(0))


def _template_line(path: Path = TEMPLATE) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^- \[ \] Stale references[^\n]*", text, re.M)
    assert m, "templates/TASK_GUIDE_template.md Edge Case Checklist has no 'Stale references' line"
    return _norm(m.group(0))


def test_ac1_sweep_names_each_changed_fact_kind():
    para = _sweep_paragraph().lower()
    for fact in ("flag", "count", "path", "channel", "skill name", "version", "green"):
        assert fact in para, f"sweep does not name the fact kind {fact!r}"


def test_ac1_sweep_names_each_place_to_grep():
    para = _sweep_paragraph()
    for place in ("README", "site/", "docs/claude-md/", "docstrings", "comments", "agents/",
                  "PROJECT_KANBAN.md", "test comments"):
        assert place in para, f"sweep does not name the place {place!r}"
    assert "grep" in para.lower()


def test_ac1_sweep_sits_in_phase_0_5():
    text = CODE_REVIEW.read_text(encoding="utf-8")
    phase05 = text.index("#### Phase 0.5")
    phase1 = text.index("#### Phase 1")
    assert phase05 < text.index("**Stale-reference sweep") < phase1


def test_ac2_hit_outside_files_to_change_is_p2_with_file_line():
    para = _sweep_paragraph()
    assert "P2" in para
    assert "Files to Change" in para
    assert "file:line" in para


def test_ac3_template_checklist_has_stale_reference_line():
    line = _template_line()
    assert "grep" in line.lower()
    assert "old wording" in line
    text = TEMPLATE.read_text(encoding="utf-8")
    checklist = text[text.index("## Edge Case Checklist"):text.index("## Files to Change")]
    assert line in _norm(checklist)


def test_ac4_code_review_skill_stays_under_codex_cap():
    assert CODE_REVIEW.stat().st_size <= CODEX_CAP


def test_neg_readers_reject_prior_content(tmp_path):
    """Negative case: the readers fail on content with no sweep and no checklist line."""
    bare_skill = tmp_path / "SKILL.md"
    bare_skill.write_text("#### Phase 0.5\nStartup-reads check\n#### Phase 1\n", encoding="utf-8")
    bare_tpl = tmp_path / "tpl.md"
    bare_tpl.write_text("## Edge Case Checklist\n- [ ] [edge case 1]\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        _sweep_paragraph(bare_skill)
    with pytest.raises(AssertionError):
        _template_line(bare_tpl)
