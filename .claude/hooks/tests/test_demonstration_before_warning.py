"""T053 — blank-BEFORE advisory in pre_agent_validate_guide.py.

Covers SC1-SC4 from tasks/TASK_GUIDE_T053.md. Exercises the real hook
end-to-end through main() where the observable behaviour is stdout, and
the field parser directly where the case is about parsing.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys

HOOK = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pre_agent_validate_guide.py",
)


def _load():
    spec = importlib.util.spec_from_file_location("validate_guide", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_hook(prompt):
    """Run the hook as a real subprocess, as the harness does."""
    event = json.dumps({"tool_name": "Agent", "tool_input": {"prompt": prompt}})
    proc = subprocess.run(
        [sys.executable, HOOK], input=event, capture_output=True, text=True
    )
    return proc


FILLED = """# TASK_GUIDE — T900: filled

## Demonstration

**BEFORE**: `grep -c foo bar.md` -> 0, captured 2026-08-06T10:00:00Z

**AFTER**: same command -> 1

**DELTA**: the thing exists now

**WITNESS**: derived from trace
"""

BLANK = """# TASK_GUIDE — T901: blank

## Demonstration

**BEFORE**: [pasted timestamped command output showing the thing absent/failing]

**AFTER**: [same command, post-change]

**DELTA**: [one sentence]

**WITNESS**: [derived from trace]
"""

LEGACY = """# TASK_GUIDE — T902: pre-dates the Demonstration block
**Complexity Level**: C2
**Risk Level**: Medium

## Acceptance Criteria

Nothing here mentions a demonstration section at all.
"""

# The word BEFORE appears in prose, but the field itself is filled.
PROSE = """# TASK_GUIDE — T903: prose mentions BEFORE

## Demonstration

**BEFORE**: run `pytest -q` -> 3 failed. Note the capture must happen
BEFORE any implementation commit exists, per DDR-0003.

**AFTER**: `pytest -q` -> 0 failed
"""


def test_sc1_blank_before_is_flagged():
    mod = _load()
    assert mod.before_field_is_blank(BLANK) is True


def test_sc2_filled_before_is_not_flagged():
    mod = _load()
    assert mod.before_field_is_blank(FILLED) is False


def test_sc4_legacy_guide_without_demonstration_is_flagged_not_errored():
    """A guide predating this change has no Demonstration section. It must
    warn, never raise -- SC4."""
    mod = _load()
    assert mod.before_field_is_blank(LEGACY) is True


def test_prose_containing_the_word_before_does_not_false_positive():
    """Edge case from the guide: the regex must key off the **BEFORE**:
    field marker, not the word appearing in prose."""
    mod = _load()
    assert mod.before_field_is_blank(PROSE) is False


def test_sc3_missing_guide_fails_open_and_does_not_block():
    """A referenced guide that does not exist must not raise and must not
    emit a blank-BEFORE warning (the missing-guide block path owns that
    case) -- SC3 fail-open."""
    mod = _load()
    assert mod.check_demonstration_warnings(["999"]) == []


def test_hook_never_blocks_on_a_blank_before():
    """AC6/AC7: the advisory is non-blocking. Real guides on disk are used
    so this exercises the true end-to-end path."""
    proc = _run_hook("See tasks/TASK_GUIDE_T053.md")
    assert proc.returncode == 0
    if proc.stdout.strip():
        payload = json.loads(proc.stdout)
        assert "decision" not in payload, "advisory path must never block"


def test_hook_fails_open_on_malformed_input():
    proc = subprocess.run(
        [sys.executable, HOOK], input="not json at all",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "decision" not in proc.stdout


def test_existing_field_extraction_is_unaffected_by_the_new_section():
    """AC8: adding the Demonstration H2 must not perturb any existing
    field-anchored parse of a guide."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(HOOK)))
    with open(os.path.join(root, "templates", "TASK_GUIDE_template.md")) as f:
        tmpl = f.read()
    import re
    assert re.search(r"\*\*Complexity Level\*\*", tmpl)
    assert re.search(r"\*\*Risk Level\*\*", tmpl)
    assert re.search(r"\*\*Depends on\*\*", tmpl)
    assert re.search(r"^## Demonstration\s*$", tmpl, re.MULTILINE)
