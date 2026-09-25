"""T129 — craft-spawn-prompt names the mandatory startup reads; Stage 4 checks the report line.

  SC4 — the skill carries the startup-reads element: the literal first line, the
        `Startup reads:` report-line instruction, and the pre-flight flag.
  SC5 — the Stage 4 review checklist (code-review Phase 0.5 area) compares the agent's
        `Startup reads:` line against the block.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts)) as f:
        return f.read()


def test_sc4_skill_has_element_with_literal_first_line():
    skill = _read("skills", "craft-spawn-prompt", "SKILL.md")
    assert "**Startup reads** (before anything else, in this order):" in skill
    for path in ("PROJECT_SPEC.md", "tasks/TASK_GUIDE_Txxx.md", "agents/<role>.md"):
        assert path in skill


def test_sc4_skill_asks_for_the_report_line():
    assert "`Startup reads: <paths read>`" in _read("skills", "craft-spawn-prompt", "SKILL.md")


def test_sc4_preflight_flags_a_prompt_without_the_block():
    skill = _read("skills", "craft-spawn-prompt", "SKILL.md")
    step4 = skill.split("#### 4. Pre-flight", 1)[1].split("#### 5.", 1)[0]
    assert "**Startup reads**" in step4 and "flag" in step4.lower()


def test_sc5_stage4_checklist_compares_the_report_line():
    review = _read("skills", "code-review", "SKILL.md")
    assert "Startup reads:" in review
    assert "P1" in review.split("Startup reads:", 1)[1][:600]
