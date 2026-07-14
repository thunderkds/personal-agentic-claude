#!/usr/bin/env python3
"""
Regression tests for pre_agent_validate_guide.py's task-ID extraction
used for the hard-block decision (extract_structural_task_ids).

Covers the T022 fix: only structural references (TASK_GUIDE_Txxx.md
file-path or an explicit "Task ID:" declaration line) should count as
"this spawn is about task Txxx" — bare Txxx substrings in free prose
(e.g. pasted memory/MEMORY.md or memory/decisions.md content) must NOT
trigger the hard block.

Run with: python3 -m pytest .claude/hooks/tests/test_pre_agent_validate_guide.py -v
or:       python3 .claude/hooks/tests/test_pre_agent_validate_guide.py
"""
import importlib.util
import os
import sys

HOOK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pre_agent_validate_guide.py",
)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

spec = importlib.util.spec_from_file_location("pre_agent_validate_guide", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def test_structural_reference_to_existing_guide():
    """A literal TASK_GUIDE_Txxx.md reference to a guide that exists must
    still be extracted (guardrail intact)."""
    prompt = "Read tasks/TASK_GUIDE_T022.md in full before starting."
    ids = hook.extract_structural_task_ids(prompt)
    assert ids == ["022"], ids


def test_structural_reference_to_missing_guide():
    """A literal TASK_GUIDE_Txxx.md reference to a guide that does NOT
    exist must still be extracted, so the hard block still fires."""
    prompt = "Read tasks/TASK_GUIDE_T999_DOES_NOT_EXIST.md in full before starting."
    ids = hook.extract_structural_task_ids(prompt)
    assert ids == ["999"], ids
    assert not os.path.exists(
        os.path.join(hook.TASKS_DIR, "TASK_GUIDE_T999.md")
    )
    assert not os.path.exists(
        os.path.join(hook.TASKS_DIR, "TASK_GUIDE_T999_DOES_NOT_EXIST.md")
    )


def test_prose_mention_of_missing_id_not_extracted():
    """This is the false-positive being fixed: a prose/decision-log
    sentence mentioning an ID with no backing guide must NOT be
    extracted (would previously hard-block an unrelated spawn)."""
    prompt = (
        "Task pointer: spawn backend-developer for T022.\n\n"
        "memory/MEMORY.md (hot-tier context):\n"
        "- Decision log: confirmed T013/T014 have no guide and were "
        "superseded before Stage 2 re-planning; see decisions.md for "
        "T019: reconciled PROJECT_KANBAN.md drift.\n"
    )
    ids = hook.extract_structural_task_ids(prompt)
    # Only the explicit "for T022" spawn-target prose is NOT structural
    # either under this fix (bare mention, no Task ID: / TASK_GUIDE_ marker) —
    # so nothing should be extracted from this snippet at all.
    assert ids == [], ids


def test_prose_mention_of_id_with_existing_guide_not_extracted():
    """No regression case: a prose mention of an ID that DOES have a
    guide was never a real problem, but confirm it still isn't matched
    by the (deliberately narrower) structural extraction — the caller
    is responsible for declaring the spawn target structurally."""
    prompt = "See T019: reconciled PROJECT_KANBAN.md drift (has a guide)."
    ids = hook.extract_structural_task_ids(prompt)
    assert ids == [], ids


def test_task_id_declaration_line_extracted():
    """An explicit 'Task ID:' declaration line is a structural marker
    and must be extracted, bold or not."""
    assert hook.extract_structural_task_ids("**Task ID**: T022") == ["022"]
    assert hook.extract_structural_task_ids("Task ID: T022") == ["022"]


def test_real_memory_and_decisions_content_no_false_positive():
    """Verify against real files: build a realistic multi-line prompt
    from the actual memory/MEMORY.md + memory/decisions.md content as
    they exist right now, and confirm the structural extraction raises
    no false-positive matches for prose-only task-ID mentions."""
    memory_path = os.path.join(ROOT, "memory", "MEMORY.md")
    decisions_path = os.path.join(ROOT, "memory", "decisions.md")

    parts = []
    for path in (memory_path, decisions_path):
        if os.path.exists(path):
            with open(path) as f:
                parts.append(f.read())
    real_content = "\n".join(parts)

    prompt = (
        "Task pointer: spawn backend-developer for T022 "
        "(tasks/TASK_GUIDE_T022.md).\n\n"
        + real_content
    )
    ids = hook.extract_structural_task_ids(prompt)
    # decisions.md legitimately contains literal "tasks/TASK_GUIDE_Txxx.md"
    # mentions in its own historical "**Files**:" lines (e.g. documenting
    # which guide a past decision touched) — those are structural-*looking*
    # but every one of them has a real backing guide on disk, so the actual
    # requirement (no false-positive HARD BLOCK) still holds even though
    # they get extracted. Assert the real requirement: none of the
    # extracted IDs are "missing" — i.e. no false-positive block would fire.
    missing = [
        tid for tid in ids
        if not os.path.exists(os.path.join(hook.TASKS_DIR, f"TASK_GUIDE_T{tid.zfill(3)}.md"))
        and not os.path.exists(os.path.join(hook.TASKS_DIR, f"TASK_GUIDE_T{tid}.md"))
    ]
    assert missing == [], (
        f"False-positive block would fire for IDs with no backing guide: {missing} "
        f"(extracted: {ids})"
    )
    assert "022" in ids, ids


def test_synthetic_missing_guide_reference_still_blocks():
    """The guardrail itself must remain intact: a synthetic prompt
    containing a literal reference to a TASK_GUIDE that does not exist
    on disk must still be extracted so main() blocks the spawn."""
    prompt = (
        "Spawn context.\n"
        "Read tasks/TASK_GUIDE_T999_DOES_NOT_EXIST.md before starting.\n"
    )
    ids = hook.extract_structural_task_ids(prompt)
    assert ids == ["999"], ids


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        print(f"\n{failures} test(s) failed")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed")
