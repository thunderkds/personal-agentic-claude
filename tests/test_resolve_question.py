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
    # T173: the doctrine moved from CLAUDE.md to AGENTS.md (CLAUDE.md is the import @AGENTS.md).
    lines = [l for l in (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
             if "Cross-cutting (any stage" in l]
    assert len(lines) == 1 and "`resolve-question`" in lines[0]


# ---- T179: Debate (auto mode only) ------------------------------------------------------------
def _debate() -> str:
    """Body of the `#### Debate (auto mode only)` step, whitespace-normalised."""
    text = _skill()
    m = re.search(r"^#### Debate \(auto mode only\)$(.*?)(?=^#### |^---$|\Z)", text, re.M | re.S)
    assert m, "no `#### Debate (auto mode only)` step"
    return _norm(m.group(1))


ADVOCATE_REF = ROOT / "skills" / "resolve-question" / "references" / "advocate.md"


def _advocate_template() -> str:
    """The fenced template in references/advocate.md (T221 moved it out of SKILL.md for the 8 KB cap)."""
    assert ADVOCATE_REF.is_file(), "skills/resolve-question/references/advocate.md does not exist"
    m = re.search(r"```\n(.*?)```", ADVOCATE_REF.read_text(encoding="utf-8"), re.S)
    assert m, "no fenced Advocate prompt template"
    return m.group(1)


# T179 AC 1
def test_t179_ac1_debate_step_has_the_d1_triggers():
    body = _debate()
    assert "auto mode" in body
    assert "Choice question" in body
    assert "Fact question the Scanners could not settle" in body
    assert "Stage 4 finding whose fix needs a choice" in body


def test_t179_ac1_sort_and_judge_route_to_debate_only_in_auto_mode():
    for word in ("Sort", "Judge"):
        body = _step(word)
        assert "Debate" in body, word
        assert "only in auto mode" in body.lower(), word
        assert "Outside auto mode" in body, word


def test_t179_ac1_non_auto_text_of_step_1_is_unchanged():
    """Success Criterion 1: a Choice question with auto mode off still goes to the user."""
    body = _step("Sort")
    for phrase in ("A Choice question goes to the user at once and never to Scanners",
                   "send it in the step 4 HITL shape, then log the answer (step 5)",
                   "When you are unsure of the kind, treat it as a Choice question",
                   "If the same question (same asker, same task) already had a fan-out, "
                   "send it straight to the user."):
        assert phrase in body, phrase
    judge = _step("Judge")
    assert "Any other outcome goes to the user (HITL) in this shape" in judge


# T179 AC 2 (T221 supersedes the slot set and the answer fields: an Advocate gets only the question
# and proposes its own option; see the T221 tests below)
def test_t179_ac2_advocate_template_slots_and_no_task_identity():
    tpl = _advocate_template()
    assert set(re.findall(r"\{(\w+)\}", tpl)) == {"question"}
    assert "TASK_GUIDE" not in tpl and "tasks/" not in tpl
    assert not re.search(r"\bT\d{3}\b|\{task", tpl)


def test_t179_ac2_advocate_answer_shape_and_agents():
    tpl = _advocate_template()
    for field in ("WHAT:", "WHY:", "HOW:", "PROPOSAL:", "FOR:", "CITATIONS:", "RISK:", "CONFIDENCE:"):
        assert field in tpl, field
    assert "<path>:<line>" in tpl and "low|medium|high" in tpl
    body = _debate()
    assert 'subagent_type: "Explore"' in body
    # T180 D7 (user, 2026-10-27) supersedes T179's "2, or 3 for 3+ options or High risk" count:
    # the Debate is auto-mode only, and its size now follows the task's Risk label.
    assert "Low, none (decide, log why); Medium, 2; High, 3" in body
    assert "smallest safe thing" in body  # T179's "High risk" pin is covered by D7's "High, 3" above
    assert "opinion only" in body


# T179 AC 3
def test_t179_ac3_decision_order_and_safer_option_ranking():
    body = _debate()
    assert "necessary" in body
    ranking = ("it can be undone > it keeps all data > it is the smaller change > "
               "it matches the request's literal words")
    assert ranking in body
    assert "Taste or scope" in body and "flagged" in body
    assert "Open every cited line" in body


def test_t179_ac3_edge_cases_are_stated():
    body = _debate()
    assert "data, not instructions" in body                       # advocate text
    assert "one stale doc" in body                               # correlated citations
    assert "deletes or overwrites data" in body and "pause and ask" in body
    assert "step limit" in body and "proposal" in body


# T179 AC 4
def test_t179_ac4_log_line_format_and_flag():
    body = _debate()
    assert "⚠ decided for you — please review" in body
    assert "- <YYYY-MM-DD> DEBATE <question> → <option>" in body
    assert "## Questions Log" in body
    assert "As step 5" in body


# T179 AC 5
def test_t179_ac5_cap_of_three_per_task_and_no_repeat():
    body = _debate()
    assert "At most 3 Debates per task" in body
    assert "4th question" in body and "HITL" in body and "even in auto mode" in body
    assert "never debated twice" in body


# T179 AC 6
def test_t179_ac6_description_mentions_debate_in_one_clause():
    desc = _norm(_frontmatter())
    assert desc.count("Debate") == 1
    assert "auto mode" in desc


def test_t179_ac6_skill_stays_under_the_codex_skill_body_cap():
    """lib/harness-fetch.sh caps a Codex skill body at 8192 bytes; over it the skill is skipped."""
    assert SKILL.stat().st_size <= 8192


# ---- T221: Advocates frame the problem (What / Why / How) and each proposes its own option ----
def _t221_template_ok(tpl: str) -> list[str]:
    """Return the AC 1-2 violations of an Advocate template (empty list = conforming)."""
    bad = []
    if set(re.findall(r"\{(\w+)\}", tpl)) != {"question"}:
        bad.append("slots are not exactly {question}")
    if "TASK_GUIDE" in tpl or "tasks/" in tpl or re.search(r"\bT\d{3}\b|\{task", tpl):
        bad.append("task identity in template")
    fields = ["WHAT:", "WHY:", "HOW:", "PROPOSAL:", "FOR:", "CITATIONS:", "RISK:", "CONFIDENCE:"]
    pos = [tpl.find(f) for f in fields]
    if -1 in pos or pos != sorted(pos):
        bad.append("fields missing or out of order")
    if '<path>:<line> "<quoted text' not in tpl or "low|medium|high" not in tpl:
        bad.append("citation shape or confidence scale missing")
    return bad


def test_t221_debate_step_points_to_the_template_file():
    assert "references/advocate.md" in _debate()
    assert "```" not in _debate(), "the template lives in references/advocate.md, not in SKILL.md"


# T221 AC 1
def test_t221_ac1_template_only_slot_is_question_and_no_task_identity():
    tpl = _advocate_template()
    assert set(re.findall(r"\{(\w+)\}", tpl)) == {"question"}
    assert "{option}" not in tpl and "{other_options}" not in tpl
    assert "TASK_GUIDE" not in tpl and "tasks/" not in tpl
    assert not re.search(r"\bT\d{3}\b|\{task", tpl)


# T221 AC 2
def test_t221_ac2_template_fields_in_order():
    assert _t221_template_ok(_advocate_template()) == []
    tpl = _advocate_template()
    assert "(1-3)" in tpl or "1-3" in tpl  # HOW lists 1-3 ways


# T221 AC 3
def test_t221_ac3_advocates_work_alone_and_spawn_in_parallel():
    body = _debate()
    assert "works alone" in body
    assert "the question only" in body
    assert "never another Advocate's output" in body
    assert "Supervisor-chosen option" in body
    assert "one message" in body and "parallel" in body


# T221 AC 4
def test_t221_ac4_high_third_advocate_line_and_smallest_safe_thing():
    body = _debate()
    assert "smallest safe thing" in body
    assert re.search(r"third.{0,80}smallest safe thing", body)


# T221 AC 5
def test_t221_ac5_description_shape_and_log_names_proposals():
    body = _debate()
    assert 'description: "Advocate <n>: <short question>"' in body
    assert "Advocate 1: <its proposal>" in body
    assert "<option>" not in body.split("**Advocates.**")[1].split("Advocate prompt template")[0]


# T221 AC 6
def test_t221_ac6_decide_compares_framings_and_logs_agreement():
    body = _debate()
    decide = body[body.index("**Decide.**"):]
    assert decide.index("Open every cited line") < decide.index("framing")
    assert "disagree" in decide and "agreement" in decide
    assert decide.index("agreement") < decide.index("1. An option")
    assert "1. An option the opened Citations show is necessary wins." in decide
    assert "2. Else the **safer option**" in decide
    assert "3. Taste or scope" in decide


# T221 AC 7
def test_t221_ac7_neighbour_files_say_propose():
    spec = (ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8")
    row = {l.split("|")[1].strip(): l for l in spec.splitlines() if l.startswith("| Debate |") or l.startswith("| Advocate |")}
    for name in ("Debate", "Advocate"):
        assert "argue one option" not in row[name], name
        assert "propos" in row[name], name
    tracks = _norm((ROOT / "docs/claude-md/tracks.md").read_text(encoding="utf-8"))
    assert "the Advocates argue" not in tracks
    assert "the Advocates propose" in tracks
    assert "DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>)" in tracks
    for t in ("templates/MINIMAL_LOG_template.md", "templates/TASK_REVIEW_template.md"):
        text = (ROOT / t).read_text(encoding="utf-8")
        assert "Advocate 1: <its proposal>; Advocate 2: <its proposal>" in text, t
        assert "Advocate 1: <its option>" not in text, t
    site = (ROOT / "site/index.html").read_text(encoding="utf-8")
    assert "Advocate agents argue the options" not in site
    assert "propose their own option" in site


# T221 AC 8 mutation control
def test_t221_ac8_mutant_template_with_option_slot_fails():
    tpl = _advocate_template()
    assert _t221_template_ok(tpl) == []
    mutant = tpl.replace("{question}", "{question}\nYour option: {option}")
    assert _t221_template_ok(mutant) != []
    assert _t221_template_ok(tpl.replace("WHY:", "BECAUSE:")) != []
