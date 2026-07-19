"""Regression test for TASK_GUIDE_template.md's example `verify` Evidence row (T026).

Two compounding bugs in the template's original example row
`` | `verify` skill — works in running app | (pass/fail) | [what was observed] | ``
against `.claude/hooks/pre_bash_block_unsafe_merge.py`'s gate regex
(`verify\\s*\\|[^|\\n]+\\|[^|\\n]*pass`):

1. The Check-column cell must be the literal word `verify` immediately
   followed (after only whitespace) by a `|` — the extra text
   "skill — works in running app" between "verify" and the pipe broke this.
2. Less obviously: the regex's third group (`[^|\\n]*pass`) must find the
   substring "pass" somewhere in the THIRD column (Notes/observation), not
   the second (Result) column — a filled Result cell of "☑ pass" alone does
   NOT satisfy the gate if the Notes column doesn't also contain "pass".

Both discovered live blocking T025's merge (bug 1) and confirmed by direct
regex testing during T026 (bug 2, not previously documented).
"""
import re

# Mirrors the real gate regex in .claude/hooks/pre_bash_block_unsafe_merge.py.
GATE_PATTERN = r"verify\s*\|[^|\n]+\|[^|\n]*pass"


def row_matches_gate(row: str) -> bool:
    return re.search(GATE_PATTERN, row, re.IGNORECASE) is not None


def test_fixed_verify_row_matches_gate_when_notes_state_pass():
    fixed_row = (
        "| verify | ☑ pass | skill run, feature confirmed working "
        "in running app — pass |"
    )
    assert row_matches_gate(fixed_row)


def test_result_column_alone_saying_pass_is_not_sufficient():
    # Confirms bug 2: "pass" only in the Result column, not the Notes
    # column, does NOT satisfy the gate — a real, easy-to-miss trap.
    row_with_pass_only_in_result = (
        "| verify | ☑ pass | skill run, feature confirmed working "
        "in running app |"
    )
    assert not row_matches_gate(row_with_pass_only_in_result)


def test_old_broken_verify_row_does_not_match_gate():
    # Negative fixture: proves this test actually distinguishes fixed from
    # broken, rather than trivially passing on any row.
    old_row = (
        "| `verify` skill — works in running app | ☑ pass | "
        "[what was observed] |"
    )
    assert not row_matches_gate(old_row)


def test_fixed_row_present_in_template_file():
    template = open("templates/TASK_GUIDE_template.md").read()
    assert "| verify | ☐ pass / ☐ fail / ☐ N/A |" in template
    assert "`verify` skill — works in running app" not in template
    assert "the merge gate scans this Notes column for the word" in template
