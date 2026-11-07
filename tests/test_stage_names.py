"""T239 — the pipeline reads Stage 0 to Stage 5, with no half numbers.

  AC1 — no `Stage 0.5`, `Stage 1.5`, `0.5a`, `0.5b`, `Phase 0`, `Step 1.5`, `5-Stage` or the old doc name
        outside the D7 history paths and the one mapping note (with an anti-vacuity check).
  AC2 — `pipeline-stages.md` has headings Stage 0 to Stage 5; Stage 0 keeps its three steps, in order,
        each with its stop (D2); Stage 1 has the steps Environment and Agent team.
  AC3 — `READINESS_LINES` and every check of `pre_agent_validate_guide.py` are unchanged; only the text of
        the readiness warning moved (D3).
  AC4 — each row of the `## Auto mode` stop table keeps its rule and its log label (D4).
  AC5 — the Agent team step asks only when `craft-agent` proposes a new role, and `AGENTS.md`,
        `craft-agent` and `brainstorming` agree (D5).
  AC6 — the Stage 0 doc was renamed; no link to the old name is left and `MANIFEST` carries the new one (D6).
  D6  — `scripts/token_audit.py` tags use `stage-0` and `stage-1`.
  AC7 — both site pages show Stage 0 to 5, each skill once.

Run with: python3 -m pytest tests/test_stage_names.py -q
"""
import ast
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "docs" / "claude-md" / "pipeline-stages.md"
TRACKS = ROOT / "docs" / "claude-md" / "tracks.md"
HOOK = ".claude/hooks/pre_agent_validate_guide.py"

# The commit just before T239 (the board commit that opened it). Repoint when a later task edits the
# compared parts: the hook (AC3) or the `## Auto mode` stop table (AC4).
BASE_REF = "055b9c6b"

OLD_NAMES = [
    r"Stage 0\.5", r"Stage 1\.5", r"0\.5a", r"0\.5b", r"Phase 0(?!\.\d)", r"Step 1\.5",
    r"5-[Ss]tage", r"phase0-project-initiation",
]
OLD_RE = re.compile("|".join(OLD_NAMES))

# D7: history stays. `docs/ddr/` is a decision record like `docs/adr/`; `PROJECT_KANBAN*.md` are boards;
# the root `BRAINSTORMING_LOG.md` is an old brainstorming log.
HISTORY = ("tasks/", "memory/", "docs/archive/", "docs/brainstorming/", "docs/prd/", "docs/adr/",
           "docs/ddr/", "reports/", "experiments/", "PROJECT_KANBAN", "BRAINSTORMING_LOG.md",
           "tests/test_stage_names.py", "tests/fixtures/site_story_baseline.json",
           "tests/test_agents_md_primary.py")  # its REPLACED_SPANS hold the pre-T239 wording of AGENTS.md on purpose

# A skill may number the phases of its own workflow (`#### Phase 0 — Determine Scope`); that is not a
# pipeline stage. A heading with this shape is skipped, and so are the listed lines.
OWN_PHASE_HEADING = re.compile(r"^#{2,5} Phase 0 ")
SITE_BASELINES = ("tests/test_site_visual_first.py", "tests/test_site_story.py")
# These two keep a baseline of the page text before T239: a record, not a claim.
BASELINE_RECORD = re.compile(r'^\s*(\("[0-9a-f]{12}", |"[0-9a-f]{12,16}": )')
OWN_PHASE_LINES = {
    ("skills/compound/SKILL.md", "If a high-overlap doc was found in Phase 0:"):
        "points at the `compound` skill's own Phase 0 (Classify the Problem)",
}


def _git(*args, check=True):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=check, capture_output=True, text=True).stdout


def _tracked():
    return [p for p in _git("ls-files").splitlines() if (ROOT / p).is_file()]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _at_base(rel):
    return _git("show", f"{BASE_REF}:{rel}")


def _hits(rel, text):
    """(line number, line) of every old stage name in `text`, with the allowed cases left out."""
    mapping_note = re.search(r"^\*\*Old names\.\*\*.*?(?=\n\s*\n|\Z)", text, re.M | re.S)
    skip = set()
    if rel == "docs/claude-md/pipeline-stages.md" and mapping_note:
        start = text[: mapping_note.start()].count("\n")
        skip = set(range(start + 1, start + 2 + mapping_note.group(0).count("\n")))
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        if n in skip or not OLD_RE.search(line):
            continue
        if OWN_PHASE_HEADING.match(line) or (rel in SITE_BASELINES and BASELINE_RECORD.match(line)):
            continue
        if any(rel == p and frag in line for (p, frag) in OWN_PHASE_LINES):
            continue
        found.append((n, line.strip()[:120]))
    return found


# --- AC1 ----------------------------------------------------------------------------------------------

def test_ac1_no_old_stage_name_is_left_outside_history_and_the_mapping_note():
    scanned, left = 0, []
    for rel in _tracked():
        if rel.startswith(HISTORY) or rel.endswith((".png", ".woff2", ".jpg", ".ico", ".patch")):
            continue
        try:
            text = _read(rel)
        except UnicodeDecodeError:
            continue
        scanned += 1
        left += [f"{rel}:{n}: {line}" for n, line in _hits(rel, text)]
    assert scanned > 200, f"the sweep scanned only {scanned} files"
    assert not left, "old stage names left:\n" + "\n".join(left)


def test_ac1_the_sweep_is_not_vacuous():
    """The patterns match the real text of the commit before T239, and the mapping note is the one exemption."""
    before = _at_base("docs/claude-md/pipeline-stages.md")
    for needle in ("Stage 0.5", "Stage 1.5", "0.5a", "0.5b", "Phase 0"):
        assert OLD_RE.search(needle), needle
        assert needle in before, f"{needle!r} is not in the pre-T239 pipeline doc, so the check proves nothing"
    assert _hits("docs/claude-md/pipeline-stages.md", before), "the sweep must catch the pre-T239 doc"
    assert _hits("x.md", "Stage 1.5 is old") and _hits("x.md", "see 0.5b")
    assert not _hits("x.md", "the code-review Phase 0.5 check")
    note = "**Old names.** Phase 0 was Stage 0.5a.\n\nrest\n"
    assert not _hits("docs/claude-md/pipeline-stages.md", note)
    assert _hits("docs/claude-md/other.md", note), "the mapping note is exempt in the pipeline doc only"
    assert _hits("docs/claude-md/pipeline-stages.md", note + "Stage 0.5 again\n")


def test_ac1_the_pipeline_doc_holds_the_mapping_note_once():
    text = _read("docs/claude-md/pipeline-stages.md")
    notes = re.findall(r"^\*\*Old names\.\*\*.*$", text, re.M)
    assert len(notes) == 1
    for old in ("Phase 0", "0.5a", "0.5b", "Stage 1.5"):
        assert old in notes[0], f"the mapping note does not name {old}"
    for new in ("Requirements", "Grilling", "Direction", "Agent team"):
        assert new in notes[0], f"the mapping note does not name {new}"


# --- AC2 ----------------------------------------------------------------------------------------------

def _stage_section(n):
    text = _read("docs/claude-md/pipeline-stages.md")
    m = re.search(rf"^## Stage {n}\b.*?(?=^## Stage |\Z)", text, re.M | re.S)
    assert m, f"no Stage {n} section"
    return m.group(0)


def test_ac2_headings_run_stage_0_to_stage_5():
    text = _read("docs/claude-md/pipeline-stages.md")
    assert text.startswith("# Stage 0–5 Agentic Pipeline")
    assert re.findall(r"^## Stage (\S+?):", text, re.M) == ["0", "1", "2", "3", "4", "5"]


def test_ac2_stage_0_keeps_three_steps_in_order_each_with_its_stop():
    sec = _stage_section(0)
    steps = re.findall(r"^### Step (\w+)", sec, re.M)
    assert steps == ["Requirements", "Grilling", "Direction"], steps
    parts = re.split(r"^### Step ", sec, flags=re.M)[1:]
    for name, body in zip(steps, parts):
        assert re.search(r"\*\*Stop:", body), f"step {name} has no stop"
    grill = parts[1]
    assert 'skill: "grill-with-docs"' in grill and "PRD gate: PASS" in grill
    direction = parts[2]
    assert 'skill: "brainstorming"' in direction and "approve" in direction.lower()
    assert "Do not merge the three stops" in sec


def test_ac2_stage_1_has_the_steps_environment_then_agent_team():
    sec = _stage_section(1)
    assert re.findall(r"^### Step ([\w ]+?) —", sec, re.M) == ["Environment", "Agent team"]
    assert "counts as done only when the `Codebase map` and `Tech stack`" in sec


# --- AC3 ----------------------------------------------------------------------------------------------

def _tree_without_warning(src):
    # T275: the hook names its launcher through `python_launcher()` (POSIX text unchanged: `python3`).
    # Put the base spelling back, so this pin keeps comparing what T239 pinned and nothing else.
    src = src.replace("project_root, python_launcher\n", "project_root\n").replace("`{python_launcher()} ", "`python3 ")
    tree = ast.parse(src)
    tree.body = [n for n in tree.body if not (isinstance(n, ast.FunctionDef) and n.name == "check_readiness_warning")]
    return ast.dump(tree)


def test_ac3_readiness_lines_and_every_check_are_unchanged():
    now, base = _read(HOOK), _at_base(HOOK)
    assert _tree_without_warning(now) == _tree_without_warning(base), "more than the warning text changed"
    assert "READINESS_LINES" in now and "def check_readiness_warning" in now


def test_ac3_the_warning_names_stages_by_their_new_names():
    text = _read(HOOK)
    warning = text[text.index("def check_readiness_warning"):text.index("def emit_readiness")]
    assert "Stage 0" in warning and "Stage 1" in warning
    assert not OLD_RE.search(warning)


# --- AC4 ----------------------------------------------------------------------------------------------

def _stop_table(text):
    sec = re.search(r"^### Every user stop and its auto rule.*?(?=^### )", text, re.M | re.S).group(0)
    rows = [r for r in sec.splitlines() if re.match(r"^\| \d+ \|", r)]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows]


def test_ac4_each_auto_mode_row_keeps_its_rule_and_its_log_label():
    now, base = _stop_table(_read("docs/claude-md/tracks.md")), _stop_table(_at_base("docs/claude-md/tracks.md"))
    assert len(base) == 21, "the base table must have 21 rows (anti-vacuity)"
    assert len(now) == len(base)
    for a, b in zip(now, base):
        assert a[0] == b[0]
        assert a[2] == b[2], f"row {a[0]}: the rule changed"
        assert a[3] == b[3], f"row {a[0]}: the log label changed"


# --- AC5 ----------------------------------------------------------------------------------------------

CONDITION = re.compile(r"only (?:when|if) `craft-agent` proposes (?:a|an) (?:new )?role", re.I)


def test_ac5_the_agent_team_step_asks_only_when_craft_agent_proposes_a_role():
    sec = _stage_section(1)
    step = sec[sec.index("### Step Agent team"):]
    assert CONDITION.search(step), "the Agent team step does not state the conditional stop"
    assert "Approve or request any modifications" in step
    assert re.search(r"base team alone[^.]*(ask nothing|no question)", step, re.I)
    assert "Auto mode" in step


def test_ac5_agents_md_craft_agent_and_brainstorming_agree():
    agents = _read("AGENTS.md")
    bullet = next(l for l in agents.splitlines() if l.startswith("- **Stage 1, step Agent team**"))
    assert CONDITION.search(bullet), bullet
    craft = _read("skills/craft-agent/SKILL.md")
    assert re.search(r"Agent team", craft) and re.search(r"asks nothing|ask nothing|no question", craft)
    brain = _read("skills/brainstorming/SKILL.md")
    assert "before Stage 1 begins" in brain
    for text in (agents, craft, brain):
        assert not re.search(r"approve the (sub-agent )?team on every", text)


# --- AC6 and D6 ---------------------------------------------------------------------------------------

def test_ac6_the_stage_0_doc_has_its_new_name_everywhere():
    assert (ROOT / "docs/claude-md/stage0-define.md").is_file()
    assert not (ROOT / "docs/claude-md/phase0-project-initiation.md").exists()
    manifest = [l.split("#")[0].split() for l in _read("MANIFEST").splitlines() if l.strip()]
    assert any(parts and parts[0] == "docs/claude-md" for parts in manifest), "MANIFEST must ship docs/claude-md"
    assert "docs/claude-md/stage0-define.md" in _read("AGENTS.md")
    text = _read("docs/claude-md/stage0-define.md")
    for name in ("Initialization", "Ambiguity Resolution Protocol", "Project Context Document"):
        assert re.search(rf"^### .*{name}", text, re.M), f"no named section for {name}"


def test_d6_token_audit_tags_use_stage_0_and_stage_1():
    ns = {}
    src = _read("scripts/token_audit.py")
    start = src.index("STAGE_MAP = {")
    exec(src[start:src.index("\n}\n", start) + 3], ns)
    m = ns["STAGE_MAP"]
    assert m["brainstorming"] == m["ideate"] == "stage-0"
    assert m["craft-agent"] == "stage-1" and m["map-codebase"] == "stage-1"
    assert "stage-0.5" not in m.values() and "stage-1.5" not in m.values()
    assert "N = 0–5" in src and "stage-0.5" in src, "the doc must say old logs may carry the old tags"


# --- AC7 ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("page,ordered", [("site/index.html", True), ("site/docs.html", True)])
def test_ac7_the_skill_flow_runs_stage_0_to_stage_5(page, ordered):
    html = _read(page)
    flow = re.search(r'<ol class="skill-flow".*?</ol>', html, re.S).group(0)
    assert re.findall(r'data-stage="([^"]+)"', flow) == ["0", "1", "2", "3", "4", "5"]
    assert "Stage 0" in flow and "Stage 1" in flow
    assert re.findall(r'data-next="(\w+)"', flow) == ["right", "down", "left", "down", "right"]


def test_ac7_the_docs_page_lists_every_skill_once_under_the_new_stages():
    html = _read("site/docs.html")
    skills = re.search(r'<section id="skills">.*?</section>', html, re.S).group(0)
    chips = re.findall(r'<span class="chip">([^<]+)</span>', skills)
    assert len(chips) == 37 == len(set(chips)), (len(chips), len(set(chips)))
    desc = re.search(r'<desc id="pipeline-diagram-desc">(.*?)</desc>', html, re.S).group(1)
    assert desc.startswith("Six steps in order") and "Stage 0 define" in desc
