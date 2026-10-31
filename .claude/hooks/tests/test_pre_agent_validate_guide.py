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



# --------------------------------------------------------------------------
# T125 SC5 — a spawn prompt that names a guide but carries no memory slice
# gets a non-blocking warning; with the marker the hook says nothing about it.
# Driven through the hook's real stdin protocol, against a real guide.
# --------------------------------------------------------------------------
import json
import subprocess

SLICE_MARKER = "<!-- memory-slice:T125 -->"
READS_BLOCK = "**Startup reads** (before anything else, in this order):\n- PROJECT_SPEC.md"


def _run_hook(prompt):
    event = {"tool_name": "Agent", "tool_input": {"prompt": prompt}}
    return subprocess.run(
        [sys.executable, HOOK_PATH], input=json.dumps(event),
        capture_output=True, text=True, timeout=30,
    )


def test_t125_sc5_guide_without_slice_marker_warns_and_is_allowed():
    result = _run_hook("Task ID: T125\nRead tasks/TASK_GUIDE_T125.md")
    assert result.returncode == 0
    assert "memory-slice" in result.stderr, result.stderr
    out = json.loads(result.stdout)
    assert "decision" not in out, "the missing-slice check must never block"
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "no `<!-- memory-slice:` marker" in context
    assert "memory_slice.py" in context


def test_t125_sc5_guide_with_slice_marker_is_silent_about_it():
    prompt = ("Task ID: T125\nRead tasks/TASK_GUIDE_T125.md\n" + READS_BLOCK + "\n"
              + SLICE_MARKER + "\nmemory/MEMORY.md — 0 of 1\n<!-- /memory-slice -->")
    result = _run_hook(prompt)
    assert result.returncode == 0
    # T223: this repo's real PROJECT_SPEC.md has no `## Readiness` yet, so stderr now carries the
    # readiness warning; this test still pins that the slice and startup-reads checks stay quiet.
    assert "memory-slice" not in result.stderr and "startup-reads" not in result.stderr
    assert "memory-slice" not in result.stdout
    assert '"decision"' not in result.stdout


def test_t125_sc5_task_id_only_prompt_is_not_asked_for_a_slice():
    """AC5 keys on a named TASK_GUIDE — a bare `Task ID:` line is not a guide path."""
    assert hook.check_memory_slice_warning("Task ID: T125\nno guide path here") == []
    assert hook.check_memory_slice_warning("Read tasks/TASK_GUIDE_T125.md") != []


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


# --------------------------------------------------------------------------
# T129 SC1-3 — a spawn prompt that names a guide but has no `**Startup reads**`
# block gets a non-blocking warning, independent of the memory-slice one.
# --------------------------------------------------------------------------
SLICE_BLOCK = SLICE_MARKER.replace("T125", "T129") + "\nx\n<!-- /memory-slice -->"


def test_t129_sc1_guide_without_startup_reads_warns_and_is_allowed():
    result = _run_hook("Task ID: T129\nRead tasks/TASK_GUIDE_T129.md\n" + SLICE_BLOCK)
    assert result.returncode == 0
    assert "startup-reads" in result.stderr, result.stderr
    out = json.loads(result.stdout)
    assert "decision" not in out, "the startup-reads check must never block"
    assert "**Startup reads**" in out["hookSpecificOutput"]["additionalContext"]


def test_t129_sc1_prose_mention_does_not_count_as_the_block():
    prompt = ("Task ID: T129\nRead tasks/TASK_GUIDE_T129.md\n"
              "Remember your startup reads, please.\n" + SLICE_BLOCK)
    assert hook.check_startup_reads_warning(prompt) != []
    assert hook.check_startup_reads_warning(
        "Read tasks/TASK_GUIDE_T129.md\nsee **Startup reads** above") != []


def test_t129_sc2_guide_with_startup_reads_is_silent_about_it():
    result = _run_hook("Task ID: T129\nRead tasks/TASK_GUIDE_T129.md\n"
                       + READS_BLOCK + "\n" + SLICE_BLOCK)
    assert result.returncode == 0
    assert "startup-reads" not in result.stderr
    assert "Startup reads" not in result.stdout
    assert '"decision"' not in result.stdout


def test_t129_sc3_prompt_naming_no_guide_is_not_asked_for_startup_reads():
    assert hook.check_startup_reads_warning("Task ID: T129\nno guide path here") == []


def test_t129_edge_each_warning_fires_independently():
    no_slice = "Read tasks/TASK_GUIDE_T129.md\n" + READS_BLOCK
    no_reads = "Read tasks/TASK_GUIDE_T129.md\n" + SLICE_BLOCK
    assert hook.check_memory_slice_warning(no_slice) and not hook.check_startup_reads_warning(no_slice)
    assert hook.check_startup_reads_warning(no_reads) and not hook.check_memory_slice_warning(no_reads)


# --------------------------------------------------------------------------
# T223 — project readiness. While `PROJECT_SPEC.md` `## Readiness` is missing or
# incomplete, a spawn that names a task is allowed but gets one loud warning that
# names every gap. Every case runs in a temp project root (a copy of the hooks),
# never against this repo's real PROJECT_SPEC.md.
# --------------------------------------------------------------------------
import io
import shutil

import pytest

READINESS_HEAD = "⚠ HIGH RISK — project readiness incomplete:"
MERMAID_FLOW = "# Main flow\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
T223_GUIDE = ("# TASK_GUIDE — {tid}: title\n**Assigned agent**: backend-developer\n\n"
              "## Requirement\n\nr\n\n## Acceptance Criteria\n\na\n\n### Verification Command\n\nv\n")
# A prompt that trips none of the other advisories except the guide's blank BEFORE.
FULL_PROMPT = ("Task ID: {tid}\nGuide: tasks/TASK_GUIDE_{tid}.md\n" + READS_BLOCK + "\n"
               "<!-- memory-slice:{tid} -->\nx\n<!-- /memory-slice -->")


def _readiness(**override):
    lines = {
        "Requirements": "`PRD.md`",
        "Direction": "BRAINSTORMING_LOG.md",
        "Codebase map": "memory/codebase-map.md",
        "Tech stack": "Python 3.12, FastAPI, SQLite, Fly.io",
        "Main flow": "`docs/flow.md`",
        "Approved by": "user 2026-10-31",
    }
    lines.update(override)
    body = "".join(f"- **{k}**: {v}\n" for k, v in lines.items() if v is not None)
    return "# PROJECT_SPEC.md\n\n## Architecture Summary\n\nx\n\n## Readiness\n\n" + body + "\n## Tasks\n\n"


def _t223_project(tmp_path, spec=None, flow=MERMAID_FLOW, guides=("T001",)):
    root = tmp_path / "proj"
    (root / ".claude").mkdir(parents=True)
    shutil.copytree(os.path.dirname(HOOK_PATH), root / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    for rel, text in (("PRD.md", "# PRD\n"), ("BRAINSTORMING_LOG.md", "# log\n"),
                      ("memory/codebase-map.md", "# map\n"), ("docs/flow.md", flow)):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        if text is not None:
            (root / rel).write_text(text, encoding="utf-8")
    (root / "tasks").mkdir()
    for tid in guides:
        (root / "tasks" / f"TASK_GUIDE_{tid}.md").write_text(T223_GUIDE.format(tid=tid))
    if spec is not None:
        (root / "PROJECT_SPEC.md").write_text(spec, encoding="utf-8")
    return root


def _spawn(root, prompt):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR")}
    event = {"tool_name": "Agent", "tool_input": {"prompt": prompt}}
    result = subprocess.run([sys.executable, str(root / ".claude" / "hooks" / "pre_agent_validate_guide.py")],
                            input=json.dumps(event), capture_output=True, text=True, cwd=root,
                            env=env, timeout=30)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout) if result.stdout.strip() else {}
    assert out.get("decision") != "block", out
    return result, out.get("hookSpecificOutput", {}).get("additionalContext", "")


def _gaps(tmp_path, **kw):
    return hook.readiness_gaps(str(_t223_project(tmp_path, **kw)))


def test_t223_sc1_idea_radar_shape_warns_and_is_allowed(tmp_path):
    root = _t223_project(tmp_path, spec="# PROJECT_SPEC.md\n\n## Architecture Summary\n\nSee docs/SPEC.md.\n")
    (root / "docs" / "SPEC.md").write_text("# SPEC\n")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('scaffold')\n")
    result, context = _spawn(root, FULL_PROMPT.format(tid="T001"))
    assert context.startswith(READINESS_HEAD), context
    assert "no `## Readiness` section" in context
    assert "design nobody checked" in context and "rework" in context
    assert "Phase 0" in context and "Stage 0.5" in context and "Stage 1" in context and "`Waived`" in context
    assert READINESS_HEAD in result.stderr, result.stderr
    assert "Demonstration BEFORE" in context, "the other advisories must stay"


def test_t223_no_spec_is_a_gap(tmp_path):
    assert _gaps(tmp_path) == ["no `PROJECT_SPEC.md` at the project root"]


def test_t223_sc2_complete_section_gives_no_gap_and_no_warning(tmp_path):
    root = _t223_project(tmp_path, spec=_readiness())
    assert hook.readiness_gaps(str(root)) == []
    result, context = _spawn(root, FULL_PROMPT.format(tid="T001"))
    assert "readiness" not in context and "readiness" not in result.stderr, context


@pytest.mark.parametrize("label", ["Requirements", "Direction", "Codebase map", "Tech stack",
                                   "Main flow", "Approved by"])
def test_t223_each_missing_line_is_named(tmp_path, label):
    assert _gaps(tmp_path, spec=_readiness(**{label: None})) == [f"`{label}` line missing"]


@pytest.mark.parametrize("value", ["", "[languages, frameworks, storage, hosting]", "   "])
def test_t223_empty_or_placeholder_line_is_named(tmp_path, value):
    assert _gaps(tmp_path, spec=_readiness(**{"Tech stack": value})) == [
        "`Tech stack` is empty or a `[...]` placeholder"]


def test_t223_path_that_does_not_exist_is_named(tmp_path):
    assert _gaps(tmp_path, spec=_readiness(Direction="`docs/brainstorm.md` (approved)")) == [
        "`Direction` file `docs/brainstorm.md` does not exist"]


@pytest.mark.parametrize("path", ["../outside.md", "/etc/hosts"])
def test_t223_path_outside_root_is_a_gap(tmp_path, path):
    (tmp_path / "outside.md").write_text("x")
    assert _gaps(tmp_path, spec=_readiness(Requirements=path)) == [
        f"`Requirements` path `{path}` is outside the project root"]


def test_t223_sc3_main_flow_without_mermaid_is_named(tmp_path):
    root = _t223_project(tmp_path, spec=_readiness(), flow="# Main flow\n\nA then B.\n")
    assert hook.readiness_gaps(str(root)) == ["`Main flow` file `docs/flow.md` has no ```mermaid block"]
    _, context = _spawn(root, FULL_PROMPT.format(tid="T001"))
    assert context.startswith(READINESS_HEAD) and "```mermaid" in context, context


@pytest.mark.parametrize("value", ["approved", "user", "2026-10-31", "[user YYYY-MM-DD]", "user 10/31/2026"])
def test_t223_approved_by_must_name_user_and_date(tmp_path, value):
    gaps = _gaps(tmp_path, spec=_readiness(**{"Approved by": value}))
    assert len(gaps) == 1 and gaps[0].startswith("`Approved by`"), gaps


@pytest.mark.parametrize("value", ["none — blank scaffold", '"none — blank scaffold"', "`none - blank scaffold`"])
def test_t223_blank_scaffold_codebase_map_is_valid(tmp_path, value):
    assert _gaps(tmp_path, spec=_readiness(**{"Codebase map": value})) == []


def test_t223_sc4_waived_line_gives_no_warning(tmp_path):
    spec = "# PROJECT_SPEC.md\n\n## Readiness\n\n- **Waived**: user 2026-10-31 — prototype\n"
    root = _t223_project(tmp_path, spec=spec)
    assert hook.readiness_gaps(str(root)) == []
    _, context = _spawn(root, FULL_PROMPT.format(tid="T001"))
    assert READINESS_HEAD not in context


def test_t223_template_waived_placeholder_does_not_waive(tmp_path):
    spec = _readiness(**{"Approved by": "", "Waived": "[user YYYY-MM-DD — reason]"})
    assert _gaps(tmp_path, spec=spec) == ["`Approved by` is empty or a `[...]` placeholder"]


def test_t223_warning_is_one_block_for_a_multi_task_prompt(tmp_path):
    root = _t223_project(tmp_path, guides=("T001", "T002"))
    prompt = FULL_PROMPT.format(tid="T001") + "\nAlso tasks/TASK_GUIDE_T002.md"
    result, context = _spawn(root, prompt)
    assert context.count(READINESS_HEAD) == 1 and result.stderr.count(READINESS_HEAD) == 1


def test_t223_no_task_id_gets_no_readiness_warning(tmp_path):
    result, context = _spawn(_t223_project(tmp_path), "Look around the repo and summarise it.")
    assert result.stdout == "" and READINESS_HEAD not in result.stderr


def test_t223_missing_guide_block_keeps_priority(tmp_path):
    root = _t223_project(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    result = subprocess.run([sys.executable, str(root / ".claude" / "hooks" / "pre_agent_validate_guide.py")],
                            input=json.dumps({"tool_name": "Agent",
                                              "tool_input": {"prompt": "Task ID: T777"}}),
                            capture_output=True, text=True, cwd=root, env=env, timeout=30)
    out = json.loads(result.stdout)
    assert out["decision"] == "block" and "missing TASK_GUIDE for: T777" in out["reason"]
    assert READINESS_HEAD not in result.stdout + result.stderr


def test_t223_crash_in_readiness_check_fails_open(tmp_path, monkeypatch, capsys):
    root = _t223_project(tmp_path)

    def boom(_root):
        raise RuntimeError("forced")

    monkeypatch.setattr(hook, "readiness_gaps", boom)
    monkeypatch.setattr(hook, "ROOT", str(root))
    monkeypatch.setattr(hook, "TASKS_DIR", str(root / "tasks"))
    monkeypatch.setattr(hook, "KANBAN", str(root / "PROJECT_KANBAN.md"))
    event = {"tool_name": "Agent", "tool_input": {"prompt": FULL_PROMPT.format(tid="T001")}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event)))
    try:
        hook.main()
    except SystemExit as exc:
        assert exc.code in (0, None)
    captured = capsys.readouterr()
    assert READINESS_HEAD not in captured.out + captured.err
    assert '"decision"' not in captured.out
    assert "Demonstration BEFORE" in captured.out, "a readiness crash must not drop the other advisories"
