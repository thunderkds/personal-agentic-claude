"""Structural test for TASK_GUIDE_template.md's `Pattern reference` field (T046).

The field is advisory — no hook enforces it — so the only thing keeping it
alive is this test. It asserts three things about the REAL template file
(never an inline copy, which would prove nothing about what ships):

1. the `**Pattern reference**:` field exists, with a bracketed placeholder
   and a concrete example naming a file that actually exists in this repo;
2. the field lives inside `## Approach` — the section an implementing agent
   reads at the point of implementation guidance;
3. the field carries an explicit opt-out value, so genuinely novel work has
   an honest answer instead of a blank or an invented reference.

Section slicing anchors on `^## ` with re.MULTILINE. Per `memory/learnings.md`
(the T045 defect), an unanchored `##` lookahead truncates at the first inline
`##` in any line — this file's own docstring contains such markers.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = REPO_ROOT / "templates" / "TASK_GUIDE_template.md"

FIELD_LABEL = "**Pattern reference**:"
OPT_OUT_TEXT = "None — no comparable prior art in this repo"
EXAMPLE_PATH_PATTERN = r"Example:\s*`Pattern reference:\s*([^\s`]+)"


def read_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def extract_section(markdown: str, heading: str) -> str:
    """Return the body between `## <heading>` and the next `^## ` heading.

    Returns "" when the heading is absent, so a caller asserting on the slice
    fails rather than silently matching the whole document.
    """
    pattern = rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)"
    match = re.search(pattern, markdown, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def has_pattern_reference_field(text: str) -> bool:
    return FIELD_LABEL in text


def has_placeholder(text: str) -> bool:
    """The field line offers a bracketed placeholder to fill in."""
    for line in text.splitlines():
        if line.startswith(FIELD_LABEL) and re.search(r"\[[^\]]+\]", line):
            return True
    return False


def has_opt_out(text: str) -> bool:
    return OPT_OUT_TEXT in text


def example_path(text: str) -> str:
    match = re.search(EXAMPLE_PATH_PATTERN, text)
    return match.group(1) if match else ""


# --- AC1: field exists, with placeholder and a concrete in-repo example ---

def test_template_has_pattern_reference_field():
    assert has_pattern_reference_field(read_template())


def test_pattern_reference_field_offers_a_placeholder():
    assert has_placeholder(read_template())


def test_pattern_reference_example_names_a_file_that_exists_in_this_repo():
    # Deliberately couples the template to the example's target: if that file
    # is renamed or deleted, the template's example has gone stale and the
    # field starts teaching a path no agent can open. That is the defect.
    path = example_path(read_template())
    assert path, "no `Example: `Pattern reference: <path>`` line found"
    assert (REPO_ROOT / path).exists(), f"example points at a missing file: {path}"


# --- AC2: the field is inside `## Approach`, not merely somewhere in the file ---

def test_pattern_reference_field_lives_in_the_approach_section():
    approach = extract_section(read_template(), "Approach")
    assert approach, "`## Approach` section not found in the template"
    assert has_pattern_reference_field(approach)


# --- AC3: explicit opt-out for genuinely novel work ---

def test_pattern_reference_field_has_an_explicit_opt_out():
    assert has_opt_out(extract_section(read_template(), "Approach"))


# --- AC4 (negative): the assertions above can actually fail ---

def remove_field_block(markdown: str) -> str:
    """Drop the field line and its `>` continuation lines."""
    lines = markdown.splitlines(keepends=True)
    kept, dropping = [], False
    for line in lines:
        if line.startswith(FIELD_LABEL):
            dropping = True
            continue
        if dropping and (line.startswith(">") or not line.strip()):
            continue
        dropping = False
        kept.append(line)
    return "".join(kept)


def test_deleting_the_field_makes_the_assertions_fail():
    mutated = remove_field_block(read_template())
    assert not has_pattern_reference_field(mutated)
    assert not has_pattern_reference_field(extract_section(mutated, "Approach"))


def test_field_outside_the_approach_section_fails_the_scoped_assertion():
    # The exact vacuous-assertion trap this repo has hit three times: a bare
    # `in template` check still passes when the field drifts out of Approach.
    original = read_template()
    field_line = next(
        line for line in original.splitlines() if line.startswith(FIELD_LABEL)
    )
    mutated = remove_field_block(original) + "\n" + field_line + "\n"

    assert has_pattern_reference_field(mutated), "naive whole-file check still passes"
    assert not has_pattern_reference_field(extract_section(mutated, "Approach"))


def test_stripping_the_opt_out_wording_fails_the_opt_out_assertion():
    mutated = read_template().replace(OPT_OUT_TEXT, "")
    assert not has_opt_out(extract_section(mutated, "Approach"))


def test_section_slicer_is_anchored_to_line_start_headings():
    # Guards the T045 defect: an inline `##` inside a line must not end the
    # slice. Without `^## `, the slice would stop at "see ## below".
    markdown = (
        "## Approach\n"
        "prose mentioning an inline ## marker\n"
        f"{FIELD_LABEL} something\n"
        "## Next Section\n"
        "unrelated\n"
    )
    approach = extract_section(markdown, "Approach")
    assert has_pattern_reference_field(approach)
    assert "unrelated" not in approach
