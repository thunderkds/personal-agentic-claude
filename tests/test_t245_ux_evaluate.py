"""T245: the `ux-evaluate` skill, its row in the frontend guide, the template's UX block and the
one `code-review` row that calls it.

Doc-content asserts in the style of `tests/test_companion_scoring_skills.py`. Each test names the
Acceptance Criterion of `tasks/TASK_GUIDE_T245.md` it covers. The skill is a prompt, so its
load-bearing sentences are pinned: a sentence that can be deleted without a test going red will be
deleted by the next person who needs the bytes.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ux-evaluate" / "SKILL.md"
FRONTEND = ROOT / "agents" / "frontend.md"
TEMPLATE = ROOT / "templates" / "TASK_GUIDE_template.md"
CODE_REVIEW = ROOT / "skills" / "code-review" / "SKILL.md"
CODEX_CAP = 8192  # lib/harness-fetch.sh skips a Codex skill body over 8 KB


def _text(path: Path) -> str:
    assert path.is_file(), f"{path.relative_to(ROOT)} does not exist"
    return path.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def frontmatter_problems(text: str) -> list[str]:
    """What is wrong with the skill's frontmatter; an empty list means valid."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ["no frontmatter"]
    fm = m.group(1)
    problems = []
    if not re.search(r"^name: ux-evaluate$", fm, re.M):
        problems.append("name is not `ux-evaluate` (must match the directory)")
    if not re.search(r"^description: \S", fm, re.M):
        problems.append("description is empty or missing")
    return problems


def over_cap(data: bytes) -> bool:
    return len(data) > CODEX_CAP


# --- AC 1: the skill file --------------------------------------------------------------

def test_ac1_frontmatter_valid():
    assert frontmatter_problems(_text(SKILL)) == []


def test_ac1_validate_sh_accepts_the_skill():
    res = subprocess.run(["sh", "scripts/validate.sh"], cwd=ROOT, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-800:] + res.stderr[-800:]
    assert "skills/ux-evaluate/SKILL.md" in res.stdout


def test_ac1_size_is_within_the_codex_cap():
    size = len(SKILL.read_bytes())
    assert not over_cap(SKILL.read_bytes()), f"{size} bytes > {CODEX_CAP}"


def test_ac1_cap_check_rejects_8193_bytes():
    """The cap check is not vacuous."""
    assert over_cap(b"x" * 8193)
    assert not over_cap(b"x" * 8192)


def test_ac1_frontmatter_check_rejects_a_bad_skill():
    assert frontmatter_problems("# no frontmatter\n")
    assert frontmatter_problems("---\nname: other\ndescription: x\n---\n")
    assert frontmatter_problems("---\nname: ux-evaluate\n---\n")


def test_ac1_description_says_when_to_use_it():
    t = _text(SKILL)
    desc = re.search(r"^description: (.*)$", t, re.M).group(1)
    assert "UI" in desc
    assert "Ready for Review" in desc
    assert "code-review" in desc


# --- AC 2: the workflow ----------------------------------------------------------------

def test_ac2_workflow_names_rows_widths_read_and_verdict_table():
    t = _text(SKILL)
    for needle in (
        "### 4. UX Acceptance Criteria",  # (a) the rows it reads
        "Entry point",
        "375",  # (b) both widths
        "1280",
        "--screenshot",  # (b) headless Chrome
        "easy-ui",
        "`Read`",  # (c) every image is opened
    ):
        assert needle in t, f"skill lacks {needle!r}"
    assert "| Verdict |" in t or "Verdict |" in t, "no verdict table template"


def test_ac2_workflow_steps_are_in_order():
    t = _text(SKILL)
    rows = t.index("### 4. UX Acceptance Criteria")
    shot = t.index("--screenshot")
    read = t.index("`Read`")
    verdict = t.index("Verdict |")
    assert rows < shot < read < verdict


def test_ac2_works_when_read_by_an_agent_and_when_called_as_a_skill():
    t = _norm(_text(SKILL))
    assert "no `Skill` tool" in t, "skill must say an agent without the Skill tool reads and follows it"


# --- AC 3: negative paths --------------------------------------------------------------

def test_ac3_negative_paths_are_named():
    t = _text(SKILL)
    for needle in ("not checked", "no UX criteria", "not checkable"):
        assert needle in t, f"skill lacks the {needle!r} outcome"


def test_ac3_not_checked_never_maps_to_pass():
    """Success Criterion 5: an unchecked row is never a pass."""
    t = _norm(_text(SKILL))
    assert re.search(r"not checked[^.]*never (a )?`?pass`?", t, re.I), (
        "the skill must say a `not checked` row is never `pass`"
    )
    assert re.search(r"not checkable[^.]*never (a )?`?pass`?", t, re.I), (
        "the skill must say a `not checkable` row is never `pass`"
    )


def test_ac3_no_ux_rows_tells_the_caller_to_ask_the_supervisor():
    t = _norm(_text(SKILL))
    m = re.search(r"no UX criteria[^.]*\.", t)
    assert m and "Supervisor" in t[m.start(): m.start() + 300]


# --- AC 4: agents/frontend.md ----------------------------------------------------------

def test_ac4_frontend_skills_table_has_a_ux_evaluate_row():
    t = _text(FRONTEND)
    rows = [l for l in t.splitlines() if l.startswith("|") and "ux-evaluate" in l]
    assert rows, "no ux-evaluate row in agents/frontend.md"
    assert "skills/ux-evaluate/SKILL.md" in t


def test_ac4_frontend_checklist_has_a_ux_line_that_reads_the_file():
    t = _text(FRONTEND)
    m = re.search(r"^- UX:.*(?:\n  .*)*", t, re.M)
    assert m, "no `- UX:` line in the Implementation checklist"
    line = _norm(m.group(0))
    assert "Read" in line and "skills/ux-evaluate/SKILL.md" in line
    assert "Skill" in line  # says why: a sub-agent has no Skill tool
    assert "fail" in line and "report" in line


def test_ac4_frontend_pillar_3_names_the_method():
    t = _text(FRONTEND)
    p3 = re.search(r"\*\*Pillar 3.*?(?=\n## )", t, re.S).group(0)
    assert "ux-evaluate" in p3


def test_ac4_frontend_lines_stay_in_the_budget():
    assert len(_text(FRONTEND).splitlines()) <= 142  # .claude/hooks/tests/test_vital_slice.py LINE_CAPS


# --- AC 5: the template ----------------------------------------------------------------

def test_ac5_template_has_the_ux_block_between_layout_and_approach():
    t = _text(TEMPLATE)
    layout = t.index("### 3. Layout / Responsiveness")
    ux = t.index("### 4. UX Acceptance Criteria")
    approach = t.index("\n## Approach")
    assert layout < ux < approach
    block = t[ux:approach]
    for header in ("User story", "User goal", "Flow / state", "Pass condition (observable)"):
        assert header in block, f"UX block lacks the {header!r} column"


def test_ac5_template_guidance_names_story_states_and_observable():
    block = _norm(_text(TEMPLATE).split("### 4. UX Acceptance Criteria")[1].split("\n## Approach")[0])
    assert "US-" in block, "rows must cite a PRD.md US-ID"
    for state in ("empty", "loading", "error", "success"):
        assert state in block, f"guidance omits the {state} state"
    assert "screenshot" in block
    assert "ux-evaluate" in block


def test_ac5_ux_block_is_not_called_a_design_evidence_row():
    """One term, one meaning: the UX rows are not the three UI design Evidence rows."""
    for path in (SKILL, TEMPLATE, FRONTEND):
        t = _norm(_text(path))
        assert "UI design Evidence row" not in t.replace("not the UI design Evidence rows", ""), path.name


# --- AC 6: code-review calls the skill, copies no rules --------------------------------

def test_ac6_code_review_has_one_conditional_row_that_calls_the_skill():
    t = _text(CODE_REVIEW)
    rows = [l for l in t.splitlines() if l.startswith("|") and "ux-evaluate" in l]
    assert len(rows) == 1, rows
    row = rows[0]
    assert 'Skill({ skill: "ux-evaluate" })' in row
    assert "P1" in row and "P2" in row


def test_ac6_code_review_has_no_ux_reviewer_persona():
    t = _text(CODE_REVIEW)
    assert "ux-reviewer" not in t
    assert t.count("ux-evaluate") == 1, "no UX rules are copied into code-review"


def test_ac6_code_review_stays_within_the_codex_cap():
    size = len(CODE_REVIEW.read_bytes())
    assert not over_cap(CODE_REVIEW.read_bytes()), f"{size} bytes > {CODEX_CAP}"


# --- AC 7: the site lists the new skill on both pages ----------------------------------

def test_ac7_both_site_pages_name_the_skill():
    for page in ("index.html", "docs.html"):
        assert "ux-evaluate" in _text(ROOT / "site" / page), f"site/{page} lacks ux-evaluate"
