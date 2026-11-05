"""T257: `tdd` and the review template make each new test or mutation control prove it can go red.

Each pin is a pure function of the text, so the same function runs on the current file (must hold)
and on the verbatim prior content kept below (must NOT hold). The second run is the RED proof: a pin
that also holds on the prior content would be vacuous.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TDD = os.path.join(ROOT, "skills", "tdd", "SKILL.md")
TEMPLATE = os.path.join(ROOT, "templates", "TASK_REVIEW_template.md")
CODEX_CAP = 8192  # lib/harness-fetch.sh skips a Codex skill body over 8 KB

# Verbatim prior content (base e0093fed) of the parts T257 changes.
PRIOR_TDD = """#### 2. Tracer Bullet
Write ONE test for the first behavior -> it fails (RED) -> write minimal code -> it passes (GREEN). This proves the path works end-to-end.

### Checklist Per Cycle
[ ] Test describes behavior, not implementation
[ ] Test uses the public interface only
[ ] Test would survive an internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
"""
PRIOR_ROW = "| Negative cases hold | ☐ pass / ☐ fail | |"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def ac1(text):
    return ("git show" in text and "prior content" in text
            and bool(re.search(r"paste[^\n]*RED|RED[^\n]*paste", text)))


def ac2(text):
    return "mutation control" in text and "git diff --stat" in text and "non-empty" in text


def ac3(text):
    return all(form in text for form in ("x <= x", "not in", "mirror", "no CI step"))


def ac4(text):
    row = next((l for l in text.splitlines() if l.startswith("| Negative cases hold")), "")
    return "red run" in row and "mutation diff" in row


def test_ac1_red_against_prior_content_step():
    assert ac1(read(TDD))


def test_ac2_mutation_control_needs_nonempty_diff():
    assert ac2(read(TDD))


def test_ac3_vacuous_forms_listed():
    assert ac3(read(TDD))


def test_ac4_template_negative_cases_row_asks_for_red_run_or_mutation_diff():
    assert ac4(read(TEMPLATE))


def test_ac5_tdd_skill_under_codex_cap():
    assert os.path.getsize(TDD) < CODEX_CAP


def test_pins_fail_on_prior_content():
    """RED control: every pin rejects the prior content, so none is vacuous."""
    assert not ac1(PRIOR_TDD)
    assert not ac2(PRIOR_TDD)
    assert not ac3(PRIOR_TDD)
    assert not ac4(PRIOR_ROW)
