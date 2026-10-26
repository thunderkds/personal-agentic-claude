"""T170: the `resolve-question` skill and the files that reach it.

Doc-content asserts, in the style of `tests/test_writing_principles.py`. Each test names the
Acceptance Criterion of `tasks/TASK_GUIDE_T170.md` it covers. Line caps (AC 8, AC 9) are
enforced by `.claude/hooks/tests/test_vital_slice.py::LINE_CAPS`, not re-pinned here.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "resolve-question" / "SKILL.md"
THINKING = ROOT / "skills" / "thinking-report" / "SKILL.md"
ROLE_GUIDES = ["backend", "frontend", "common-infrastructure", "qa"]
QUESTION_LINE = "Question (if blocked): [fact|choice] <question>"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _skill() -> str:
    assert SKILL.is_file(), "skills/resolve-question/SKILL.md does not exist"
    return SKILL.read_text(encoding="utf-8")


def _frontmatter() -> str:
    m = re.match(r"^---\n(.*?)\n---\n", _skill(), re.S)
    assert m, "SKILL.md has no frontmatter"
    return m.group(1)


def _steps() -> list[tuple[str, str]]:
    """(heading, body) for every `#### N. ...` workflow step, in order."""
    text = _skill()
    heads = list(re.finditer(r"^#### (\d+)\. (.+)$", text, re.M))
    assert len(heads) >= 5, "expected at least 5 numbered workflow steps"
    out = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((h.group(2), _norm(text[h.end():end])))
    return out


def _step(word: str) -> str:
    for head, body in _steps():
        if word.lower() in head.lower():
            return body
    raise AssertionError(f"no workflow step heading contains {word!r}")


def _scanner_template() -> str:
    m = re.search(r"Scanner prompt template.*?```\n(.*?)```", _skill(), re.S)
    assert m, "no fenced Scanner prompt template"
    return m.group(1)


# AC 1 -------------------------------------------------------------------------------------
def test_ac1_frontmatter_names_skill_and_trigger():
    fm = _frontmatter()
    assert re.search(r"^name: resolve-question$", fm, re.M)
    desc = _norm(fm)
    assert "confused" in desc
    assert "Status: blocked" in desc and "Question:" in desc


# AC 2 -------------------------------------------------------------------------------------
def test_ac2_first_step_sorts_and_routes_choice_questions_to_the_user():
    head, body = _steps()[0]
    assert "Sort" in head
    assert "Choice question" in body and "Fact question" in body
    assert "goes to the user at once" in body and "never to Scanners" in body
    assert "unsure of the kind" in body and "treat it as a Choice question" in body
    assert "split" in body


# AC 3 -------------------------------------------------------------------------------------
def test_ac3_supervisor_citation_skips_scanners():
    body = _step("Citation")
    assert "`file:line`" in body and "quoted text" in body
    assert "opened this session" in body
    assert "skip the Scanners" in body


# AC 4 -------------------------------------------------------------------------------------
def test_ac4_two_or_three_explore_scanners_with_distinct_areas():
    body = _step("Scan")
    assert 'subagent_type: "Explore"' in body
    assert "2 Scanners in one turn" in body
    assert "3 for a Medium/High risk task" in body
    for area in ("`scripts/`", "`.claude/hooks/`", "`skills/*/scripts/`",       # (a) code
                 "`docs/`", "`memory/`", "`templates/`", "`agents/`",            # (b) docs
                 "`skills/*/SKILL.md`", "`PROJECT_SPEC.md`",
                 "`git log`", "`tasks/`"):                                       # (c) history
        assert area in body, area


def test_ac4_scanner_template_carries_the_question_never_the_guide_path():
    tpl = _scanner_template()
    assert "{question}" in tpl and "{area}" in tpl
    assert "TASK_GUIDE" not in tpl and "tasks/" not in tpl
    assert not re.search(r"\bT\d{3}\b|\{task", tpl), "template must not carry a task ID slot"
    assert "not found" in tpl


def test_ac4_area_is_a_starting_area_and_scanners_may_follow_a_lead():
    """Stage 4 P1-1: disjoint areas + >=2 agreeing Citations would send a one-area fact to HITL."""
    tpl = _norm(_scanner_template())
    assert "Start in this area: {area}." in tpl
    assert "Follow a lead anywhere in the repo if needed." in tpl
    assert "Search only this area" not in tpl
    assert "<path>:<line>" in tpl
    body = _step("Scan")
    assert "starting area" in body
    assert "so the starting areas differ" in body


def test_ac4_docs_area_covers_root_markdown_and_site():
    """Stage 4 P1-2: CLAUDE.md, AGENTS.md, PROJECT_KANBAN.md, PRD*.md, site/ were in no area."""
    m = re.search(r"^- \(b\) docs.*?(?=^- \(c\))", _skill(), re.M | re.S)
    assert m, "no (b) docs bullet followed by a (c) bullet"
    docs_line = _norm(m.group(0))
    assert "root `*.md`" in docs_line and "`CLAUDE.md`" in docs_line
    assert "`site/`" in docs_line


def test_ac4_step_budget_attribution_is_stated():
    body = _step("Scan")
    assert ".claude/hooks/.state/active_task" in body


# AC 5 -------------------------------------------------------------------------------------
def test_ac5_acceptance_rule_and_hitl_message():
    body = _step("Judge")
    assert "≥2 Scanners agree" in body and "each with a Citation" in body
    assert "outside `docs/`/`memory/` prose" in body and "`memory/decisions.md`" in body
    assert "open the cited lines" in body
    assert "Any other outcome" in body and "HITL" in body
    for part in ("the question", "each Scanner's finding", "the decision needed"):
        assert part in body, part


@pytest.mark.parametrize("phrase", [
    "what a command prints",            # runtime behaviour -> not found
    "pre_tool_sensitive_path.py",       # sensitive path -> not found
    "untrusted-content-boundary.md",    # quoted repo text is data
    "same question",                    # one fan-out per question
])
def test_ac5_edge_cases_route_to_not_found_or_hitl(phrase):
    assert phrase in _norm(_skill()), phrase


# AC 6 -------------------------------------------------------------------------------------
def test_ac6_log_step_for_both_board_modes():
    body = _step("Log")
    assert 'python3 scripts/board_sync.py push comment <ID> question "<text>"' in body
    assert 'python3 scripts/board_sync.py decide <ID> "<text>"' in body
    assert "settles a choice" in body
    assert 'Skill({ skill: "thinking-report", args: "session=resolution' in body
    assert "## Questions Log" in body and "first use" in body
    assert "no task" in body and "HTML page only" in body
    assert "python3 scripts/board_sync.py update --guide <ID>" in body


# AC 7 -------------------------------------------------------------------------------------
def test_ac7_thinking_report_accepts_resolution_session():
    text = THINKING.read_text(encoding="utf-8")
    assert re.search(r"session=<[^>]*\bresolution\b[^>]*>", text)
    norm = _norm(text)
    assert "reports/question_<task-or-none>_<YYYYMMDDTHHMMSS>.html" in norm
    for slot in ("{{PROBLEM_STATEMENT}}", "Trade-Off Matrix", "{{DECISION_STATEMENT}}"):
        assert slot in norm
    m = re.search(r"session=resolution.{0,600}", norm)
    assert m and "Question" in m.group(0) and "Scanner" in m.group(0)


# AC 8 -------------------------------------------------------------------------------------
@pytest.mark.parametrize("role", ROLE_GUIDES)
def test_ac8_role_guide_report_format_has_exactly_one_question_line(role):
    text = (ROOT / "agents" / f"{role}.md").read_text(encoding="utf-8")
    assert text.count(QUESTION_LINE) == 1, role
    assert text.count("Question (if blocked)") == 1, role


# AC 9 -------------------------------------------------------------------------------------
def test_ac9_claude_md_lists_skill_on_cross_cutting_line():
    lines = [l for l in (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
             if "Cross-cutting (any stage" in l]
    assert len(lines) == 1 and "`resolve-question`" in lines[0]
