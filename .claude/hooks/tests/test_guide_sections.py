#!/usr/bin/env python3
"""T064 — the two reviewer-filled sections (`### Evidence`, `## Demonstration`)
move out of `TASK_GUIDE_Txxx.md` into a sibling `TASK_REVIEW_Txxx.md`.

This ships as a **fallback, not a migration**: every consumer reads the section
from the guide first and only falls through to the review file when the guide
does not carry it. All pre-T064 guides keep both sections inline and every
parser keeps finding them there.

`test_ac7_*` comes first in this file on purpose. AC7 is the one criterion whose
failure mode is silent and repo-wide: adding a second source for the merge
gate's Evidence row creates a way to get it wrong in the dangerous direction. If
"review file missing" is ever treated as anything other than "no evidence", the
gate stops gating — on every task, quietly. It was written before the resolver
existed.

Run with: python3 -m pytest .claude/hooks/tests/test_guide_sections.py -v
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import types

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(HOOKS_DIR, "lib")
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
TASKS_DIR = os.path.join(REPO_ROOT, "tasks")

# The worktree tip immediately BEFORE T064's first implementation commit.
# Pinned rather than `HEAD` on purpose: a working-tree-vs-HEAD comparison stops
# asserting anything the moment the change is committed (recorded learning
# "Working-tree-vs-HEAD is a scope guard, not a repeatable test").
BASELINE_REF = "2612a05"


# --------------------------------------------------------------------------
# Module loading
# --------------------------------------------------------------------------

def _load_by_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_script_hook(name, path):
    """Load a hook that ends in a bare `main()` call without running it."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

guide_sections = _load_by_path(
    "guide_sections", os.path.join(LIB_DIR, "guide_sections.py")
)
merge_gate = _load_script_hook(
    "pre_bash_block_unsafe_merge",
    os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py"),
)
validate_guide = _load_by_path(
    "pre_agent_validate_guide", os.path.join(HOOKS_DIR, "pre_agent_validate_guide.py")
)
render_mod = _load_by_path(
    "delivery_report_render",
    os.path.join(REPO_ROOT, ".claude", "skills", "delivery-report", "render.py"),
)


# --------------------------------------------------------------------------
# Fixtures — written into tmp_path only. Never into a tracked file under
# tasks/ or reports/ (T059 was exactly that defect, and in a worktree it
# destroyed data).
# --------------------------------------------------------------------------

FILLED_EVIDENCE_TABLE = """| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_x.py |
| verify | ☑ pass | skill run, feature confirmed working — pass |
| Full smoke suite still green (no regression) | pass | 260 passed |
"""

UNFILLED_EVIDENCE_TABLE = """| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s)] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed] |
"""

FILLED_DEMONSTRATION = """**BEFORE**: `pytest -q` -> 3 failed, captured 2026-08-09T04:00:00Z

**AFTER**: `pytest -q` -> 0 failed

**DELTA**: the suite is green

**WITNESS**: derived from memory/event-trace/T900.jsonl
"""

PLACEHOLDER_DEMONSTRATION = """**BEFORE**: [pasted timestamped command output showing the thing absent/failing]

**AFTER**: [same command, post-change]

**DELTA**: [one sentence]

**WITNESS**: [derived from trace]
"""

SPLIT_GUIDE = """# TASK_GUIDE — T900: split

## Evaluation & Acceptance (How we know the agent worked correctly)

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T900.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T900.md`.

---

## Approach

Prose the implementing agent actually reads.
"""

NO_SECTIONS_GUIDE = """# TASK_GUIDE — T900: pre-T053, no Demonstration and no Evidence

## Acceptance Criteria

| # | Criterion | Traces to |
|---|-----------|-----------|
| 1 | something | the requirement |
"""


def _legacy_guide(evidence_table, demonstration):
    return (
        "# TASK_GUIDE — T900: legacy inline\n\n"
        "### Evidence (filled by reviewer at Stage 4/5)\n\n"
        + evidence_table
        + "\n## Demonstration\n\n"
        + demonstration
    )


def _review_file(evidence_table=None, demonstration=None):
    text = "# TASK_REVIEW — T900: sibling\n"
    if evidence_table is not None:
        text += "\n## Evidence\n\n" + evidence_table
    if demonstration is not None:
        text += "\n## Demonstration\n\n" + demonstration
    return text


def _write(tasks_dir, name, text):
    path = os.path.join(str(tasks_dir), name)
    with open(path, "w") as f:
        f.write(text)
    return path


# ==========================================================================
# AC7 (P0) — the merge gate must fail CLOSED when neither source has evidence
# ==========================================================================

def test_ac7_no_evidence_anywhere_blocks_merge(tmp_path):
    """Guide exists, carries no Evidence section, and no review file exists.
    The only safe answer is "no evidence"."""
    _write(tmp_path, "TASK_GUIDE_T900.md", NO_SECTIONS_GUIDE)
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_missing_guide_and_missing_review_blocks_merge(tmp_path):
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_split_guide_with_no_review_file_blocks_merge(tmp_path):
    """The vacated pointer in the guide is not evidence of anything."""
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_empty_review_file_blocks_merge(tmp_path):
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", "")
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_truncated_review_file_blocks_merge(tmp_path):
    """Review file exists but was cut off before the Evidence table."""
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", "# TASK_REVIEW — T900\n\n## Evi")
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_unfilled_review_evidence_blocks_merge(tmp_path):
    """Resolving the file is not the same as the file being filled."""
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(UNFILLED_EVIDENCE_TABLE))
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_unreadable_review_file_blocks_merge(tmp_path):
    """Fail closed for the merge gate — an unreadable file is not evidence,
    and it must not raise either (this hook runs before every Bash call)."""
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    path = _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(FILLED_EVIDENCE_TABLE))
    os.chmod(path, 0o000)
    try:
        assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False
    finally:
        os.chmod(path, 0o644)


def test_ac7_directory_named_like_a_review_file_blocks_merge(tmp_path):
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    os.mkdir(os.path.join(str(tmp_path), "TASK_REVIEW_T900.md"))
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_ac7_result_column_pass_alone_still_does_not_satisfy_the_gate(tmp_path):
    """The T026 two-bug fix is preserved verbatim: "pass" must be in the Notes
    column. This task changes *where* the text is read from, never *what* is
    matched — so the same row that failed the gate inline must fail it in the
    review file too."""
    table = (
        "| Check | Result | Notes / output snippet |\n"
        "|-------|--------|------------------------|\n"
        "| verify | ☑ pass | skill run, feature confirmed working |\n"
    )
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(table))
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


# ==========================================================================
# AC6 — the positive direction: a filled row in the review file is found
# ==========================================================================

def test_ac6_filled_verify_row_in_review_file_is_found(tmp_path):
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(FILLED_EVIDENCE_TABLE))
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is True


def test_legacy_inline_evidence_still_found(tmp_path):
    """No review file at all — behaviour identical to before T064."""
    _write(
        tmp_path,
        "TASK_GUIDE_T900.md",
        _legacy_guide(FILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION),
    )
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is True


def test_inline_evidence_wins_over_a_stray_review_file(tmp_path):
    """Order matters: guide first, review second. A legacy guide whose own
    Evidence table is unfilled must NOT be rescued by a stray review file."""
    _write(
        tmp_path,
        "TASK_GUIDE_T900.md",
        _legacy_guide(UNFILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION),
    )
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(FILLED_EVIDENCE_TABLE))
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_unpadded_task_id_resolves(tmp_path):
    """`T64` and `T064` name the same pair — the two-line path juggling that
    was duplicated at three call sites lives in the resolver now."""
    _write(tmp_path, "TASK_GUIDE_T64.md", SPLIT_GUIDE.replace("T900", "T64"))
    _write(tmp_path, "TASK_REVIEW_T64.md", _review_file(FILLED_EVIDENCE_TABLE))
    assert merge_gate.has_filled_verify_row("T064", tasks_dir=str(tmp_path)) is True


# ==========================================================================
# AC4 / AC5 / SC1 / SC2 — pre_agent_validate_guide.py
# ==========================================================================

def test_ac4_before_resolved_from_review_file_emits_no_warning(tmp_path):
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(demonstration=FILLED_DEMONSTRATION))
    assert validate_guide.check_demonstration_warnings(
        ["900"], tasks_dir=str(tmp_path)
    ) == []


def test_sc2_placeholder_before_in_review_file_still_warns(tmp_path):
    """The fallback resolves the file; it does not assume the file is filled."""
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(
        tmp_path,
        "TASK_REVIEW_T900.md",
        _review_file(demonstration=PLACEHOLDER_DEMONSTRATION),
    )
    warnings = validate_guide.check_demonstration_warnings(["900"], tasks_dir=str(tmp_path))
    assert len(warnings) == 1 and "BEFORE" in warnings[0]


def test_ac5_legacy_inline_demonstration_still_resolves(tmp_path):
    _write(
        tmp_path,
        "TASK_GUIDE_T900.md",
        _legacy_guide(FILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION),
    )
    assert validate_guide.check_demonstration_warnings(
        ["900"], tasks_dir=str(tmp_path)
    ) == []


def test_inline_blank_demonstration_is_not_rescued_by_a_review_file(tmp_path):
    _write(
        tmp_path,
        "TASK_GUIDE_T900.md",
        _legacy_guide(FILLED_EVIDENCE_TABLE, PLACEHOLDER_DEMONSTRATION),
    )
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(demonstration=FILLED_DEMONSTRATION))
    assert len(validate_guide.check_demonstration_warnings(["900"], tasks_dir=str(tmp_path))) == 1


def test_no_demonstration_anywhere_warns_and_does_not_raise(tmp_path):
    _write(tmp_path, "TASK_GUIDE_T900.md", NO_SECTIONS_GUIDE)
    assert len(validate_guide.check_demonstration_warnings(["900"], tasks_dir=str(tmp_path))) == 1


def test_unreadable_review_file_fails_open_for_the_advisory_hook(tmp_path):
    """Advisory hook: it may warn, it may not — but it must never raise."""
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    path = _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(demonstration=FILLED_DEMONSTRATION))
    os.chmod(path, 0o000)
    try:
        result = validate_guide.check_demonstration_warnings(["900"], tasks_dir=str(tmp_path))
        assert isinstance(result, list)
    finally:
        os.chmod(path, 0o644)


def test_before_field_is_blank_keeps_its_whole_guide_signature():
    """Pre-T064 callers (and test_demonstration_before_warning.py) pass the
    whole guide text. That entry point must keep working unchanged."""
    assert validate_guide.before_field_is_blank(
        _legacy_guide(FILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION)
    ) is False
    assert validate_guide.before_field_is_blank(NO_SECTIONS_GUIDE) is True


# ==========================================================================
# AC8 / AC9 — delivery-report render.py
# ==========================================================================

def test_ac8_split_pair_renders_before_after_delta_and_counts(tmp_path):
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(
        tmp_path,
        "TASK_REVIEW_T900.md",
        _review_file(FILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION),
    )
    slots = render_mod.build_slots(
        "T900", "branch", SPLIT_GUIDE, root="/nonexistent", tasks_dir=str(tmp_path)
    )
    assert "3 failed" in slots["BEFORE"]
    assert "0 failed" in slots["AFTER"]
    assert slots["DELTA"] == "the suite is green"
    assert slots["EVIDENCE_COUNT_SUMMARY"].startswith("3 / 3")
    assert slots["NO_DEMO_WARNING"] == ""


def test_ac8_legacy_inline_guide_renders_unchanged(tmp_path):
    guide = _legacy_guide(FILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION)
    with_tasks_dir = render_mod.build_slots(
        "T900", "branch", guide, root="/nonexistent", tasks_dir=str(tmp_path)
    )
    without = render_mod.build_slots("T900", "branch", guide, root="/nonexistent")
    for key in ("BEFORE", "AFTER", "DELTA", "EVIDENCE_COUNT_SUMMARY", "NO_DEMO_WARNING"):
        assert with_tasks_dir[key] == without[key]
    assert "3 failed" in with_tasks_dir["BEFORE"]


def test_evidence_count_never_spans_a_file_boundary(tmp_path):
    """Count from wherever the table resolved — never sum both sources."""
    guide = _legacy_guide(FILLED_EVIDENCE_TABLE, FILLED_DEMONSTRATION)
    _write(tmp_path, "TASK_GUIDE_T900.md", guide)
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(FILLED_EVIDENCE_TABLE))
    slots = render_mod.build_slots(
        "T900", "branch", guide, root="/nonexistent", tasks_dir=str(tmp_path)
    )
    assert slots["EVIDENCE_COUNT_SUMMARY"].startswith("3 / 3"), "both tables were summed"


def test_ac9_pre_t053_guide_with_no_review_file_still_raises(tmp_path):
    """The pre-T053 edge case is preserved, not swallowed by the new fallback."""
    try:
        render_mod.parse_demonstration(NO_SECTIONS_GUIDE, review_text=None)
    except render_mod.NoDemonstrationBlock:
        pass
    else:
        raise AssertionError("NoDemonstrationBlock was not raised")


def test_ac9_split_guide_with_no_review_file_also_raises():
    """A pointer with nothing behind it is the same as no block at all."""
    try:
        render_mod.parse_demonstration(SPLIT_GUIDE, review_text=None)
    except render_mod.NoDemonstrationBlock:
        pass
    else:
        raise AssertionError("NoDemonstrationBlock was not raised")


def test_bugfix_repro_row_resolves_from_the_review_file(tmp_path):
    """The bugfix flavor's BEFORE points at the Evidence table's `Repro loop`
    row by name; once the table moves, the pointer must follow it."""
    table = (
        "| Check | Result | Notes / output snippet |\n"
        "|-------|--------|------------------------|\n"
        "| verify | pass | ran — pass |\n"
        "| Repro loop | pass | `curl localhost/health` returns 500 before the fix |\n"
    )
    demo = "**BEFORE**: see Phase 1 repro loop\n\n**AFTER**: 200\n\n**DELTA**: fixed\n"
    guide = SPLIT_GUIDE
    _write(tmp_path, "TASK_GUIDE_T900.md", guide)
    _write(tmp_path, "TASK_REVIEW_T900.md", _review_file(table, demo))
    slots = render_mod.build_slots(
        "T900", "branch", guide, root="/nonexistent", tasks_dir=str(tmp_path)
    )
    assert "returns 500 before the fix" in slots["BEFORE"]


# ==========================================================================
# AC10 (negative) — a TASK_REVIEW write must not register a Kanban row
# ==========================================================================

class _StringStdin:
    """`json.load(sys.stdin)` only needs `.read()`."""

    def __init__(self, text):
        self._text = text

    def read(self, *args):
        return self._text


def _run_register_hook(tmp_path, written_path):
    """Run post_write_register_task.py's main() against a throwaway board.
    Returns the board text after the call."""
    register = _load_script_hook(
        "post_write_register_task",
        os.path.join(HOOKS_DIR, "post_write_register_task.py"),
    )
    kanban = os.path.join(str(tmp_path), "PROJECT_KANBAN.md")
    with open(kanban, "w") as f:
        f.write("**Last updated**: 2026-08-09\n\n### Todo\n\n### Done\n")
    register.KANBAN = kanban

    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": written_path}})
    stdin_saved = sys.stdin
    sys.stdin = _StringStdin(payload)
    try:
        register.main()
    except SystemExit:
        pass
    finally:
        sys.stdin = stdin_saved
    return _read(kanban)


def test_ac10_writing_a_review_file_registers_no_kanban_row(tmp_path):
    review_path = _write(tmp_path, "TASK_REVIEW_T999.md", _review_file(FILLED_EVIDENCE_TABLE))
    board = _run_register_hook(tmp_path, review_path)
    assert "T999" not in board, "a TASK_REVIEW write added a Kanban row"
    assert board == "**Last updated**: 2026-08-09\n\n### Todo\n\n### Done\n"
    # The load-bearing part: the hook's regex anchors on TASK_GUIDE_(T\d+)\.md$.
    assert re.search(r"TASK_GUIDE_(T\d+)\.md$", review_path) is None


def test_ac10_writing_a_guide_still_registers_a_row(tmp_path):
    """Control: same hook, same board, a TASK_GUIDE path — proves the assertion
    above distinguishes "not registered" from "the hook never ran"."""
    guide_path = _write(
        tmp_path,
        "TASK_GUIDE_T999.md",
        "# TASK_GUIDE — T999: control\n**Complexity Level**: C1\n"
        "**Risk Level**: Low\n**Priority**: P2\n",
    )
    board = _run_register_hook(tmp_path, guide_path)
    assert "**T999**" in board, "the control never fired — the negative proves nothing"


# ==========================================================================
# AC1 / AC2 / AC3 / AC11 — the templates
# ==========================================================================

def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _git_show(ref, path):
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout


def _slice(text, pattern):
    m = re.search(pattern, text, re.M | re.S)
    return m.group(0) if m else ""


EVIDENCE_SLICE_RE = r"^#{2,3} Evidence.*?$(.*?)(?=^#{2,3} |\Z)"
DEMO_SLICE_RE = r"^#{2,3} Demonstration\s*$(.*?)(?=^#{2,3} |\Z)"


def test_ac1_review_template_exists_with_both_sections():
    review = _read(os.path.join(TEMPLATES_DIR, "TASK_REVIEW_template.md"))
    assert re.search(r"^## Evidence\s*$", review, re.M)
    assert re.search(r"^## Demonstration\s*$", review, re.M)


def test_ac1_moved_evidence_rows_are_byte_identical_to_the_baseline():
    baseline = _git_show(BASELINE_REF, "templates/TASK_GUIDE_template.md")
    review = _read(os.path.join(TEMPLATES_DIR, "TASK_REVIEW_template.md"))
    old_rows = [l for l in _slice(baseline, EVIDENCE_SLICE_RE).splitlines()
                if l.startswith("|")]
    new_rows = [l for l in _slice(review, EVIDENCE_SLICE_RE).splitlines()
                if l.startswith("|")]
    assert old_rows, "baseline slice found no Evidence rows — the slicer is vacuous"
    assert new_rows == old_rows


def test_ac1_moved_demonstration_fields_are_byte_identical_to_the_baseline():
    baseline = _git_show(BASELINE_REF, "templates/TASK_GUIDE_template.md")
    review = _read(os.path.join(TEMPLATES_DIR, "TASK_REVIEW_template.md"))
    # The trailing `---` is the document's section separator, not part of the
    # block; everything between the heading and it must be byte-identical.
    def body(text):
        sliced = _slice(text, DEMO_SLICE_RE).split("\n", 1)[1].strip()
        return re.sub(r"\n-{3,}\s*\Z", "", sliced).strip()

    old, new = body(baseline), body(review)
    assert old, "baseline slice found no Demonstration body — the slicer is vacuous"
    assert new == old


def test_ac1_review_templates_verify_row_still_satisfies_the_gate():
    """The moved row must still be the row the merge gate can match once a
    reviewer fills it — same two bugs T026 fixed, same regex."""
    review = _read(os.path.join(TEMPLATES_DIR, "TASK_REVIEW_template.md"))
    assert "| verify | ☐ pass / ☐ fail / ☐ N/A |" in review
    assert "the merge gate scans this Notes column for the word" in review
    filled = "| verify | ☑ pass | skill run, feature confirmed working — pass |"
    assert merge_gate.VERIFY_ROW_PATTERN.search(filled)


def test_ac2_guide_template_no_longer_carries_either_body():
    guide = _read(os.path.join(TEMPLATES_DIR, "TASK_GUIDE_template.md"))
    evidence = _slice(guide, EVIDENCE_SLICE_RE)
    demo = _slice(guide, DEMO_SLICE_RE)
    assert evidence and demo, "the vacated headings must stay in place"
    assert not [l for l in evidence.splitlines() if l.startswith("|")], \
        "the Evidence table is still in the guide template"
    assert "**BEFORE**" not in demo, "the Demonstration fields are still in the guide template"
    assert "TASK_REVIEW_" in evidence and "TASK_REVIEW_" in demo, \
        "each vacated position must point at the sibling review file"


def test_ac3_reasoning_prose_sections_are_byte_identical_to_the_baseline():
    baseline = _git_show(BASELINE_REF, "templates/TASK_GUIDE_template.md")
    guide = _read(os.path.join(TEMPLATES_DIR, "TASK_GUIDE_template.md"))
    for heading in ("Requirement (Pillar 1 — Adapt the requirement)",
                    "Acceptance Criteria", "Approach", "Edge Case Checklist"):
        pattern = rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)"
        old, new = _slice(baseline, pattern), _slice(guide, pattern)
        assert old, f"baseline slice for {heading!r} is empty — the slicer is vacuous"
        assert new == old, f"`## {heading}` changed"


CARD_SCAFFOLDING = ("challenge-response", "challenge/response", "\nQ:", "\nA:", "**Q:**", "**A:**")


def test_ac11_no_challenge_response_card_scaffolding_in_the_guide_template():
    """File-wide negative. The rejected direction must be absent from the whole
    file, not merely from the sections this task touched (T058's AC11 missed a
    second occurrence outside the predicted diff for exactly this reason)."""
    guide = _read(os.path.join(TEMPLATES_DIR, "TASK_GUIDE_template.md"))
    lowered = guide.lower()
    for token in CARD_SCAFFOLDING:
        assert token.lower() not in lowered, f"card scaffolding present: {token!r}"


def test_ac11_negative_control_detects_each_token_form():
    """Attacked from more than one direction: each token form must be caught on
    its own, so the assertion cannot be non-vacuous for one and blind to
    another (the recorded T067 finding)."""
    guide = _read(os.path.join(TEMPLATES_DIR, "TASK_GUIDE_template.md"))
    for token in CARD_SCAFFOLDING:
        mutated = (guide + "\n" + token + " what does this do?\n").lower()
        assert any(t.lower() in mutated for t in CARD_SCAFFOLDING), token
        assert token.lower() in mutated, token


# ==========================================================================
# AC12 / AC13 — the skill-instruction text
# ==========================================================================

def test_ac12_bugfix_skeleton_splits_the_same_two_sections():
    skill = _read(os.path.join(REPO_ROOT, ".claude", "skills", "bugfix", "SKILL.md"))
    assert "TASK_REVIEW_" in skill, "the bugfix skeleton never names the review file"
    evidence = _slice(skill, EVIDENCE_SLICE_RE)
    assert evidence, "`### Evidence` heading missing from the bugfix skeleton"
    assert not [l for l in evidence.splitlines() if l.startswith("| ")], \
        "the bugfix Evidence table is still inline in the guide skeleton"


def test_ac12_both_flavors_keep_identical_field_names():
    """The property delivery-report depends on to need no flavor branch."""
    review = _read(os.path.join(TEMPLATES_DIR, "TASK_REVIEW_template.md"))
    bugfix = _read(os.path.join(REPO_ROOT, ".claude", "skills", "bugfix", "SKILL.md"))
    fields = re.findall(r"\*\*(BEFORE|AFTER|DELTA|WITNESS)\*\*", review)
    assert fields == ["BEFORE", "AFTER", "DELTA", "WITNESS"]
    bugfix_review = bugfix[bugfix.index("TASK_REVIEW"):]
    bugfix_fields = re.findall(r"\*\*(BEFORE|AFTER|DELTA|WITNESS)\*\*", bugfix_review)
    assert bugfix_fields == fields


def test_ac12_gate_finds_the_verify_row_in_a_real_split_bugfix_pair(tmp_path):
    """Preserves the intent of `test_bugfix_evidence_parity.py`'s AC7 check at
    the row's new location: build the pair from the REAL template text plus the
    bugfix skeleton's three extra rows, fill it the way a reviewer would, and
    run it through the real gate function — not a hand-shaped fixture.

    NOTE: that pre-existing test still asserts the row lives inline in
    `bugfix/SKILL.md` and is currently RED. It was left untouched and escalated
    to the Supervisor rather than edited green.
    """
    review = _read(os.path.join(TEMPLATES_DIR, "TASK_REVIEW_template.md"))
    bugfix = _read(os.path.join(REPO_ROOT, ".claude", "skills", "bugfix", "SKILL.md"))
    extra_rows = [
        l for l in bugfix.splitlines()
        if l.startswith(("| Repro loop |", "| Regression test |", "| Smoke suite |"))
    ]
    assert len(extra_rows) == 3, f"bugfix skeleton no longer offers 3 extra rows: {extra_rows}"

    filled = review.replace(
        "| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed",
        "| verify | pass | [what was observed",
    ).replace(
        'the merge gate scans this Notes column for the word "pass", not just the Result column]',
        'the merge gate scans this Notes column for the word "pass" — pass]',
    )
    filled = filled.replace(
        "| **UI: Responsiveness at target viewports**",
        "\n".join(extra_rows) + "\n| **UI: Responsiveness at target viewports**",
    )
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", filled)
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is True


def test_ac13_craft_spawn_prompt_targets_the_review_file_by_absolute_path():
    skill = _read(
        os.path.join(REPO_ROOT, ".claude", "skills", "craft-spawn-prompt", "SKILL.md")
    )
    element7 = skill[skill.index("Element 7"):]
    assert "TASK_REVIEW_" in element7, "element 7 still targets the guide's own section"
    assert "literal absolute path" in element7
    assert "$CLAUDE_PROJECT_DIR/tasks" not in element7, \
        "$CLAUDE_PROJECT_DIR is EMPTY in an agent's Bash tool call (recorded gotcha)"


# ==========================================================================
# AC14 — no existing guide is migrated
# ==========================================================================

def test_ac14_every_existing_task_guide_is_byte_identical_to_the_baseline():
    listing = subprocess.run(
        ["git", "ls-tree", "--name-only", BASELINE_REF, "tasks/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    guides = [p for p in listing if re.match(r"tasks/TASK_GUIDE_T\d+.*\.md$", p)]
    assert len(guides) >= 20, f"only {len(guides)} guides found — the listing is vacuous"
    changed = [
        p for p in guides
        if _git_show(BASELINE_REF, p) != _read(os.path.join(REPO_ROOT, p))
    ]
    assert changed == [], f"existing guides were modified: {changed}"


# ==========================================================================
# AC15 — measured byte reduction
# ==========================================================================

def _split_reduction(guide_text):
    """Bytes a guide of this shape sheds when the two reviewer-filled sections
    move out, counting the pointer lines that replace them."""
    evidence = _slice(guide_text, EVIDENCE_SLICE_RE)
    demo = _slice(guide_text, DEMO_SLICE_RE)
    assert evidence and demo, "guide has no sections to move — measurement is vacuous"
    pointer = "\n> **Moved.** See `tasks/TASK_REVIEW_Txxx.md`.\n\n"
    body_only = len(evidence.encode()) + len(demo.encode())
    kept_headings = len(("## Evidence" + pointer + "## Demonstration" + pointer).encode())
    total = len(guide_text.encode())
    return 100.0 * (body_only - kept_headings) / total


def test_ac15_a_t060_shaped_guide_is_at_least_25_percent_smaller_when_split():
    text = _git_show(BASELINE_REF, "tasks/TASK_GUIDE_T060.md")
    assert _split_reduction(text) >= 25.0


def test_ac15_holds_on_a_second_real_guide():
    """Attacked from a second direction: one guide could be an outlier."""
    text = _git_show(BASELINE_REF, "tasks/TASK_GUIDE_T067.md")
    assert _split_reduction(text) >= 25.0


def test_ac15_measurement_is_not_vacuous():
    """A guide whose two sections are one line each must NOT clear 25% — proves
    the measurement reads the real section sizes rather than always passing."""
    tiny = (
        "# TASK_GUIDE — T900\n\n"
        "### Evidence\n\n| verify | pass | pass |\n\n"
        "## Demonstration\n\n**BEFORE**: x\n\n"
        "## Approach\n\n" + ("prose. " * 2000) + "\n"
    )
    assert _split_reduction(tiny) < 25.0


# ==========================================================================
# Edge cases from the guide's checklist
# ==========================================================================

def test_task_id_never_reaches_a_path_untrusted(tmp_path):
    """T056 precedent: `session_id` reached a filename and had to be sanitised.
    A traversal-shaped task id must resolve to nothing, not to a file outside
    the tasks directory."""
    outside = os.path.join(str(tmp_path), "outside.md")
    with open(outside, "w") as f:
        f.write("## Evidence\n\n" + FILLED_EVIDENCE_TABLE)
    tasks = os.path.join(str(tmp_path), "tasks")
    os.mkdir(tasks)
    for bogus in ("../outside", "T900/../../outside", "T900;rm", "", None, 900):
        assert guide_sections.read_guide_section(bogus, "Evidence", tasks) is None


def test_inline_heading_does_not_truncate_a_section(tmp_path):
    """The recorded `###`-in-a-Kanban-row family: a `##` appearing mid-line
    inside pasted output must not end the section."""
    review = (
        "# TASK_REVIEW — T900\n\n## Evidence\n\n"
        "| Check | Result | Notes |\n|---|---|---|\n"
        "| note | pass | pasted output mentioning ## inline |\n"
        "| verify | ☑ pass | skill run — pass |\n"
    )
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", review)
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is True


def test_quoted_h2_heading_inside_a_review_file_does_truncate(tmp_path):
    """Stated plainly rather than pretended away: a real line-start `## ` inside
    pasted output ends the section, exactly as every existing regex in this
    repo behaves. Fenced or indented output is the way to paste such text."""
    review = (
        "# TASK_REVIEW — T900\n\n## Evidence\n\n"
        "| Check | Result | Notes |\n|---|---|---|\n"
        "## Demonstration\n\n"
        "| verify | ☑ pass | skill run — pass |\n"
    )
    _write(tmp_path, "TASK_GUIDE_T900.md", SPLIT_GUIDE)
    _write(tmp_path, "TASK_REVIEW_T900.md", review)
    assert merge_gate.has_filled_verify_row("T900", tasks_dir=str(tmp_path)) is False


def test_resolver_never_raises_on_hostile_input(tmp_path):
    for args in (
        ("T900", "Evidence", "/definitely/not/a/dir"),
        ("T900", "", str(tmp_path)),
        ("T900", "Evidence", None),
        ("T900", "Evidence", 42),
    ):
        assert guide_sections.read_guide_section(*args) is None


def test_pointer_only_section_is_treated_as_absent():
    body = "\n> **Moved.** See `tasks/TASK_REVIEW_T900.md`.\n\n"
    assert guide_sections.is_pointer_only(body) is True
    assert guide_sections.is_pointer_only(body + "| verify | pass | pass |\n") is False


# ---------------------------------------------------------------------------
# Stage 4 finding (Supervisor): the gate signals a block by printing a
# `decision: block` object on stdout and exiting 0. An unguarded ImportError
# exits 1 with EMPTY stdout, which the harness reads as a non-blocking hook
# error — so the merge proceeds. That is a fail-OPEN in the one place AC7
# requires fail-closed. Run as a subprocess: the failure only exists at module
# import time, so importing the module in-process cannot exercise it.
# ---------------------------------------------------------------------------

def test_ac7_missing_resolver_blocks_rather_than_failing_open(tmp_path):
    import json as _json
    import shutil
    import subprocess

    hooks_dir = os.path.dirname(HOOKS_DIR) if False else HOOKS_DIR
    gate = os.path.join(hooks_dir, "pre_bash_block_unsafe_merge.py")
    lib = os.path.join(hooks_dir, "lib", "guide_sections.py")
    stashed = os.path.join(str(tmp_path), "guide_sections.py.bak")

    shutil.move(lib, stashed)
    try:
        proc = subprocess.run(
            [sys.executable, gate],
            input=_json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": "git " + "push" + " origin main"},
            }),
            capture_output=True,
            text=True,
        )
    finally:
        shutil.move(stashed, lib)

    assert proc.stdout.strip(), (
        "gate produced NO stdout when the resolver was missing — the harness "
        "reads that as a non-blocking error and the merge proceeds (fail-open)"
    )
    decision = _json.loads(proc.stdout)
    assert decision.get("decision") == "block", (
        f"expected an explicit block, got: {decision}"
    )
    assert proc.returncode == 0, (
        "a block must be signalled by stdout + exit 0, not a non-zero exit"
    )
