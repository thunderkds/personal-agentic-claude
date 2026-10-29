"""T191: the `score` skill (Companion score row, easy-verifier).

Doc-content asserts, in the style of `tests/test_resolve_question.py`. Each test names the
Acceptance Criterion of `tasks/TASK_GUIDE_T191.md` it covers. The skill is a prompt, so the
load-bearing sentences are pinned here: a sentence that can be deleted without a test going red
will be deleted by the next person who needs the bytes.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORE = ROOT / "skills" / "score" / "SKILL.md"
CODEX_CAP = 8192  # lib/harness-fetch.sh skips a Codex skill body over 8 KB


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _text(path: Path) -> str:
    assert path.is_file(), f"{path.relative_to(ROOT)} does not exist"
    return path.read_text(encoding="utf-8")


def frontmatter_problems(text: str) -> list[str]:
    """What is wrong with a SKILL.md's frontmatter; an empty list means valid."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ["no frontmatter"]
    fm = m.group(1)
    problems = []
    if not re.search(r"^name: score$", fm, re.M):
        problems.append("name is not `score` (must match the directory)")
    if not re.search(r"^description: \S", fm, re.M):
        problems.append("description is empty or missing")
    return problems


def over_cap(data: bytes) -> bool:
    return len(data) > CODEX_CAP


# --- AC 1 -----------------------------------------------------------------------------

def test_ac1_frontmatter_valid():
    assert frontmatter_problems(_text(SCORE)) == []


def test_ac1_validate_sh_accepts_the_skill():
    res = subprocess.run(["sh", "scripts/validate.sh"], cwd=ROOT, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-800:] + res.stderr[-800:]
    assert "skills/score/SKILL.md" in res.stdout


def test_ac1_size_is_within_the_codex_cap():
    size = len(SCORE.read_bytes())
    assert not over_cap(SCORE.read_bytes()), f"{size} bytes > {CODEX_CAP}"


def test_ac1_cap_check_rejects_8193_bytes():
    """Success Criterion 5: the cap check is not vacuous."""
    assert over_cap(b"x" * 8193)
    assert not over_cap(b"x" * 8192)


def test_ac1_frontmatter_check_rejects_a_bad_skill():
    assert frontmatter_problems("# no frontmatter\n")
    assert frontmatter_problems("---\nname: other\ndescription: x\n---\n")
    assert frontmatter_problems("---\nname: score\n---\n")


# --- AC 2 -----------------------------------------------------------------------------

def test_ac2_ladder_in_order_with_what_each_rung_needs():
    t = _text(SCORE)
    mcp = t.index("**Registered MCP**")
    cli = t.index("python -m easy_verifier.adapters.cli score --repo <absolute> --scope changes --ref <base>...HEAD < /dev/null")
    na = t.index("`☑ N/A`, naming the missing tool and the rung reached")
    assert mcp < cli < na
    assert "including the asking round" in t
    assert "score only, it never asks" in t


# --- AC 3 -----------------------------------------------------------------------------

def test_ac3_every_cli_invocation_ends_with_dev_null():
    t = _text(SCORE)
    cmds = re.findall(r"python -m? ?[^`\n]*", t)
    cmds = [c for c in cmds if "easy_verifier" in c]
    assert len(cmds) >= 3, cmds  # probe, score, write-report
    for c in cmds:
        assert c.rstrip().endswith("< /dev/null"), c


def test_ac3_says_why_stdin_must_be_closed():
    t = _norm(_text(SCORE))
    assert "`score` reads findings from stdin when stdin is not a terminal, so an agent shell that leaves it open waits forever" in t


# --- AC 4 -----------------------------------------------------------------------------

def test_ac4_changes_scope_three_dot_ref_and_the_wrong_forms():
    t = _norm(_text(SCORE))
    assert "--scope changes" in t and "--ref <base>...HEAD" in t
    assert "A bare branch name or a two-dot range scores one commit against its parent, the wrong thing on a multi-commit branch" in t
    assert "not always `main`" in t


# --- AC 5 -----------------------------------------------------------------------------

def test_ac5_floor_stated_exactly_once():
    t = _text(SCORE)
    assert t.count("≥ 80") == 1
    assert "`overall ≥ 80`" in t


def test_ac5_failing_change_risk_rule_fails_the_row():
    t = _norm(_text(SCORE))
    assert "A failing `change_risk` rule sets the row to `fail` whatever `overall` says, because `change_risk` is never averaged into `overall`" in t


# --- AC 6 -----------------------------------------------------------------------------

def test_ac6_chore_abstention_is_not_a_failure():
    t = _norm(_text(SCORE))
    assert '`change_kind: chore`' in t and '"chore: no test expectation"' in t
    assert "That abstention is not a failing rule. Never write `fail` for it" in t


# --- AC 7 -----------------------------------------------------------------------------

def test_ac7_findings_handed_over_and_never_blended():
    t = _norm(_text(SCORE))
    assert "preceding `code-review` findings" in t
    assert "separate **assessment** and **divergence**" in t
    assert "never blends findings into the rating" in t


# --- AC 8 -----------------------------------------------------------------------------

def test_ac8_change_kind_confirm_or_override_with_reason_and_signals():
    t = _norm(_text(SCORE))
    assert "confirm or override the detected kind" in t
    assert '"reason": "<one line>"' in t
    assert "Cite the signals the payload listed" in t


# --- AC 9 -----------------------------------------------------------------------------

def test_ac9_gate_answer_shape_and_held_evidence_sources():
    t = _norm(_text(SCORE))
    assert '{dimension: {"score": 0-100, "confidence": 0-1, "evidence_refs": [...]' in t
    for source in ("a `code-review` finding", "an Acceptance Criterion of the task's guide", "an easy-ui session report"):
        assert source in t, source
    assert "listed `evidence_refs`" in t  # the engine rejects a ref outside the dimension's pack


# --- AC 10 ----------------------------------------------------------------------------

def test_ac10_unanswerable_gate_stays_abstained_and_why():
    t = _norm(_text(SCORE))
    assert "A gate you cannot answer from held evidence stays abstained, and the row says so" in t
    assert "Never submit a rating you cannot cite" in t
    assert "The engine weights an answer at `0.5 × confidence`, so a confident guess moves the number that blocks merges" in t


# --- AC 11, 12 ------------------------------------------------------------------------

def test_ac11_row_cites_report_with_the_five_fields_and_label():
    t = _norm(_text(SCORE))
    assert "`write_report`" in t
    assert "`report: <absolute path>`" in t
    for field in ("`overall`", "`change_risk`", "`scope changes`", "the ref", "report:"):
        assert field in t, field
    assert "The gate reads the path after the literal `report:` label" in t


def test_ac12_notes_record_abstentions():
    t = _norm(_text(SCORE))
    assert "every entry of `overall.abstentions`" in t
    assert "never read as a zero" in t


# --- AC 13 ----------------------------------------------------------------------------

def test_ac13_unbacked_pass_is_not_a_pass():
    t = _norm(_text(SCORE))
    assert "An unbacked pass is not a pass" in t
    assert "Never write `☑ pass` without a report path that exists on disk; rewrite it as `N/A`" in t


# --- guide edge cases -----------------------------------------------------------------

def test_edge_security_and_exposure_statements_present():
    t = _norm(_text(SCORE))
    assert "Never copy a raw matched secret" in t  # NFR-003
    assert "`127.0.0.1:8766` with no authentication" in t  # NFR-004
    assert "never run it yourself" in t
    assert "shows up in the task's own diff" in t  # reports/ in the evaluated repo
    assert "not the newest file in the directory" in t


def test_edge_failing_rule_and_overall_abstention_are_defined():
    """Found in the real CLI run: a failing rule is `passed: false`; `overall` can itself abstain."""
    t = _norm(_text(SCORE))
    assert "A failing rule is an entry of `change_risk.inputs` with `passed: false`" in t
    assert "If `overall` itself is an abstention" in t and "write `☑ N/A` with that reason code" in t
