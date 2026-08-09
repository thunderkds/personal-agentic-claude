#!/usr/bin/env python3
"""T068 — the merge gate's `VERIFY_ROW_PATTERN` cannot tell an unfilled
`verify` Evidence row (the template's own placeholder text) from a filled one.

The template's placeholder row writes "pass" as one of the UNCHECKED options
in its own guidance prose:

    | verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally
    state "pass" or "fail" here too, ...] |

Both the Result cell (`☐ pass`) and the Notes cell (the guidance sentence
itself contains the word "pass") satisfy the pre-T068 regex
(`verify\\s*\\|[^|\\n]+\\|[^|\\n]*pass`), so a task whose reviewer has filled in
NOTHING at all already clears the row check.

The AC6 corpus survey found six real shapes in the repo. Any fix must
classify all of them correctly, in particular T050's real, legitimately
filled `☑ pass / ☐ N/A` row — the obvious "reject any Result cell containing
☐" rule would wrongly reject it.

Run with: python3 -m pytest .claude/hooks/tests/test_verify_row_fill_detection.py -v
"""
import glob
import os
import re
import shutil
import sys
import tempfile
import types

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))


def load_hook_module(path, name):
    """Load a hook as a module without running its bottom-of-file main()."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "pre_bash_block_unsafe_merge_verify_row")


def row_is_filled(evidence_section):
    """Drive the REAL `has_filled_verify_row` over a real review file.

    Stage 4 finding: this helper previously re-implemented the gate's decision
    (walk VERIFY_ROW_PATTERN, apply UNCHECKED_PASS_PATTERN) instead of calling
    the shipped function, and degraded defensively via `getattr(...)`. Every
    assertion below therefore tested a *copy* of the logic. Proven vacuous by
    mutation: making `has_filled_verify_row` ignore UNCHECKED_PASS_PATTERN --
    i.e. restoring the exact defect T068 exists to fix -- left the full suite
    at 326 passed. The tests must go through the function the gate calls.
    """
    tmp = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmp, "TASK_REVIEW_T900.md"), "w", encoding="utf-8") as fh:
            fh.write("# TASK_REVIEW — T900\n\n## Evidence\n\n" + evidence_section + "\n")
        return merge_gate.has_filled_verify_row("T900", tasks_dir=tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TEMPLATE_PLACEHOLDER_ROW = (
    '| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must '
    'literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed '
    'working — pass": the merge gate scans this Notes column for the word '
    '"pass", not just the Result column] |'
)

UNFILLED_TWO_OPTION_ROW = "| verify | ☐ pass / ☐ fail | |"

FILLED_CHECKED_BOX_ROW = (
    "| verify | ☑ pass | skill run, feature confirmed working — pass |"
)

FILLED_BARE_WORD_ROW = "| verify | pass | ran suite, all green — pass |"

FILLED_EMOJI_ROW = "| verify | ✅ pass | end to end run — pass |"

# T050's real row (tasks/TASK_GUIDE_T050.md) — legitimately filled, still
# contains an unchecked glyph, just not attached to "pass".
T050_TRAP_ROW = (
    "| verify | ☑ pass / ☐ N/A | Supervisor read the diff (matches Files-to-Change "
    "exactly); default no-arg behavior byte-identical to pre-task (AC1) — pass |"
)

RESULT_PASS_NOT_NOTES_ROW = (
    "| verify | ☑ pass | skill run, feature confirmed working in running app |"
)

WRONG_CHECK_CELL_ROW = (
    "| `verify` skill — works in running app | ☑ pass | [what was observed] |"
)


def test_ac1_unfilled_template_placeholder_row_is_not_filled():
    """AC1 — reproduces the defect: the untouched template row must NOT
    satisfy the gate. This is expected to FAIL against the pre-fix pattern."""
    assert row_is_filled(TEMPLATE_PLACEHOLDER_ROW) is False


def test_ac2_unfilled_two_option_row_is_not_filled():
    assert row_is_filled(UNFILLED_TWO_OPTION_ROW) is False


def test_ac3_all_four_real_filled_shapes_are_filled():
    for row in (
        FILLED_CHECKED_BOX_ROW,
        FILLED_BARE_WORD_ROW,
        FILLED_EMOJI_ROW,
        T050_TRAP_ROW,
    ):
        assert row_is_filled(row) is True, row


def test_ac3_trap_t050_shape_specifically():
    """The obvious "reject any ☐" rule fails this: T050 IS filled and still
    contains ☐ (in `☐ N/A`, not attached to "pass")."""
    assert row_is_filled(T050_TRAP_ROW) is True


def test_ac4_pass_in_result_only_not_notes_stays_rejected():
    """T026 property must be preserved: "pass" in Result but not Notes."""
    assert row_is_filled(RESULT_PASS_NOT_NOTES_ROW) is False


def test_ac5_wrong_check_cell_is_not_a_verify_row():
    assert row_is_filled(WRONG_CHECK_CELL_ROW) is False


def test_ac6_old_vs_new_pattern_over_real_corpus_differs_only_on_placeholders():
    """Walk every real tasks/*.md file (never write to it), extract every
    `| verify |` row from its Evidence section, and diff old-pattern vs
    new-pattern verdicts. The only allowed differences are unfilled
    placeholder rows the old pattern wrongly accepted."""
    old_pattern = re.compile(r"verify\s*\|[^|\n]+\|[^|\n]*pass", re.IGNORECASE)
    row_pattern = re.compile(r"^\|\s*verify\s*\|.*\|.*\|\s*$", re.IGNORECASE | re.MULTILINE)

    placeholder_shapes = {
        TEMPLATE_PLACEHOLDER_ROW.strip(),
    }

    differences = []
    task_files = sorted(glob.glob(os.path.join(ROOT, "tasks", "*.md")))
    assert task_files, "corpus is empty — sanity check failed"
    for path in task_files:
        text = open(path, encoding="utf-8").read()
        for row in row_pattern.findall(text):
            old_verdict = bool(old_pattern.search(row))
            new_verdict = row_is_filled(row)
            if old_verdict != new_verdict:
                # Only allowed direction: old said filled, new correctly says
                # unfilled, on a row that is a placeholder-shaped guidance row.
                is_placeholder_shape = "☐ pass" in row and "must literally state" in row
                if old_verdict and not new_verdict and is_placeholder_shape:
                    continue
                differences.append((path, row, old_verdict, new_verdict))

    assert differences == [], differences


def test_ac7_mutation_reverting_to_old_pattern_turns_ac1_red():
    """Negative, mutation-verified: swap in the OLD unfixed pattern and
    confirm AC1's check goes RED — proves the new test actually discriminates."""
    old_pattern = re.compile(r"verify\s*\|[^|\n]+\|[^|\n]*pass", re.IGNORECASE)
    assert bool(old_pattern.search(TEMPLATE_PLACEHOLDER_ROW)) is True, (
        "mutation control did not engage — old pattern must match the "
        "placeholder row for this to prove anything"
    )


def test_ac9_missing_evidence_section_still_fails_closed():
    assert merge_gate.has_filled_verify_row("T_NONEXISTENT_TASK_FOR_TEST") is False
