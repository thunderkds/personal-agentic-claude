#!/usr/bin/env python3
"""T190 — the merge gate binds a failed companion row, and stays silent when
there is none.

Four Evidence rows become binding in `pre_bash_block_unsafe_merge.py`:
`Companion score (easy-verifier)` and the three `UI:` design rows. The rule is
the **inverse** of every other check in that file: only an explicit checked
`☑ fail` blocks, and every absence — no row, a blank row, the unchecked template
placeholder, `☑ N/A`, an unreadable file — allows. That inversion is the whole
meaning of the companion tools being optional (user decision D6; FR-006,
FR-014), so the byte-identity test below is the load-bearing one: with no
companion rows present the gate's output must be unchanged from the pre-change
hook, byte for byte, against an oracle captured BEFORE the edit.

Every fixture here is **constructed**. Nothing reads the live board, the live
`tasks/` directory or this machine's real `git worktree list`.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_companion_rows.py -v
Re-capture the AC-4 oracle (only against the PRE-change hook):
    python3 .claude/hooks/tests/test_merge_gate_companion_rows.py --capture-oracle
"""
import io
import json
import os
import shutil
import sys
import tempfile
import types

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
ORACLE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data",
    "t190_pre_change_gate_output.txt",
)


def load_hook_module(path, name):
    """Load a hook without running its bottom-of-file `main()` — same technique
    as `test_merge_gate_evidence.py`, which explains why it is necessary."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "merge_gate_t190")


# ---------------------------------------------------------------------------
# Constructed fixtures
# ---------------------------------------------------------------------------

KANBAN_READY_FOR_REVIEW = """# PROJECT_KANBAN

### Todo

### In Progress

### Ready for Review
- [ ] **T900** — fixture task | common-infrastructure | C2 | Risk: Medium | P0

### Done
"""

KANBAN_DONE = """# PROJECT_KANBAN

### Todo

### In Progress

### Ready for Review

### Done
- [x] **T900** — fixture task | common-infrastructure | C2 | Risk: Medium | P0
"""

KANBAN_TODO = """# PROJECT_KANBAN

### Todo
- [ ] **T900** — fixture task | common-infrastructure | C2 | Risk: Medium | P0

### In Progress

### Ready for Review

### Done
"""

# The post-T064 guide shape: the Evidence heading is vacated to a pointer, so
# resolution falls through to the review file.
GUIDE_WITH_VACATED_EVIDENCE = """# TASK_GUIDE - T900

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T900.md`.

---
"""

REVIEW_HEADER = """# TASK_REVIEW - T900

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☑ pass | 917 passed |
| verify | ☑ pass | verify skill run, feature confirmed working — pass |
"""

PYTEST_TRACE_RECORD = json.dumps({
    "timestamp": "2026-10-28T00:00:00+00:00",
    "tool_name": "Bash",
    "summary": json.dumps({"command": "python3 -m pytest .claude/hooks/tests/ -q"})[:300],
    "is_error": False,
})

HEREDOC_MENTIONING_A_PUSH = (
    "cat > notes.md <<'EOF'\n"
    "This document explains why the gate blocks a git push.\n"
    "EOF\n"
)

COMPANION = "Companion score (easy-verifier)"
UI_ROWS = (
    "UI: Visual regression (diff or verdict pasted)",
    "UI: Design-system compliance (tokens/colors/typography verified)",
    "UI: Responsiveness at target viewports",
)


def row(check, result, notes=""):
    return f"| **{check}** | {result} | {notes} |\n"


def review_with(*rows):
    return REVIEW_HEADER + "".join(rows)


class GateFixture:
    """A constructed checkout: a board, a vacated guide, a review file, and a
    trace record that satisfies the pre-existing `verify` check — so the only
    thing any test below can change the gate's answer with is a companion row.

    The review file is written into the **main** checkout's `tasks/` and the
    worktree enumeration is stubbed empty, so no test depends on git or on this
    machine's actual worktree list.
    """

    def __init__(self, review=None, kanban=KANBAN_READY_FOR_REVIEW, guide=None):
        self.root = tempfile.mkdtemp(prefix="t190_gate_")
        self.main_tasks = os.path.join(self.root, "main", "tasks")
        self.trace_dir = os.path.join(self.root, "main", "memory", "event-trace")
        for path in (self.main_tasks, self.trace_dir):
            os.makedirs(path)

        self._write(self.main_tasks, "TASK_GUIDE_T900.md",
                    GUIDE_WITH_VACATED_EVIDENCE if guide is None else guide)
        if review is not None:
            self._write(self.main_tasks, "TASK_REVIEW_T900.md", review)

        self.kanban = os.path.join(self.root, "PROJECT_KANBAN.md")
        with open(self.kanban, "w") as f:
            f.write(kanban)
        with open(os.path.join(self.trace_dir, "T900.jsonl"), "w") as f:
            f.write(PYTEST_TRACE_RECORD + "\n")

        self._saved = (merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR)
        merge_gate.KANBAN = self.kanban
        merge_gate.TASKS_DIR = self.main_tasks
        merge_gate.TRACE_DIR = self.trace_dir

    @staticmethod
    def _write(directory, name, text):
        with open(os.path.join(directory, name), "w") as f:
            f.write(text)

    def cleanup(self):
        merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR = self._saved
        shutil.rmtree(self.root, ignore_errors=True)


def run_gate(command, worktree_dirs=()):
    """Drive the hook's real `main()` over a constructed event.

    Returns `(stdout, stderr)` as raw strings — stdout is the hook's JSON
    decision (empty when it stays silent) and stderr carries its advisory
    lines. Both halves are compared byte-for-byte by the AC-4 oracle test, so
    neither is parsed here.
    """
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    saved = (sys.stdin, sys.stdout, sys.stderr, merge_gate.worktree_tasks_dirs)
    sys.stdin = io.StringIO(event)
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    merge_gate.worktree_tasks_dirs = lambda: list(worktree_dirs)
    try:
        try:
            merge_gate.main()
        except SystemExit:
            pass
        return sys.stdout.getvalue(), sys.stderr.getvalue()
    finally:
        sys.stdin, sys.stdout, sys.stderr, merge_gate.worktree_tasks_dirs = saved


def block_reason(command="git push origin feat/t900"):
    """The gate's block reason, or None when it stayed silent."""
    stdout, _ = run_gate(command)
    return json.loads(stdout)["reason"] if stdout.strip() else None


def gate(review, command="git push origin feat/t900", **kwargs):
    """`(block reason or None, stderr)` for one constructed review file."""
    fixture = GateFixture(review=review, **kwargs)
    try:
        stdout, stderr = run_gate(command)
        reason = json.loads(stdout)["reason"] if stdout.strip() else None
        return reason, stderr
    finally:
        fixture.cleanup()


# ---------------------------------------------------------------------------
# AC 2 / SC 1 — a checked `fail` in the Companion score row blocks
# ---------------------------------------------------------------------------

def test_checked_fail_companion_row_blocks_and_names_the_task_and_the_row():
    reason, _ = gate(review_with(row(COMPANION, "☑ fail",
                                     "overall 62 (< 80), change_risk 0 — no regression test")))
    assert reason is not None, "a ☑ fail Companion score row must block the push"
    assert "T900" in reason
    assert "Companion score" in reason


def test_checked_fail_blocks_even_though_the_verify_row_is_filled():
    """The two checks are independent: the fixture's `verify` row and trace
    record satisfy the pre-existing gate, so the block can only come from the
    new row."""
    assert gate(review_with())[0] is None, "fixture must be green without a companion row"
    assert gate(review_with(row(COMPANION, "☑ fail", "overall 62")))[0] is not None


# ---------------------------------------------------------------------------
# AC 3 — the same block for each of the three UI design rows
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ui_row", UI_ROWS, ids=["visual", "design-system", "responsive"])
def test_checked_fail_in_any_ui_design_row_blocks(ui_row):
    reason, _ = gate(review_with(row(ui_row, "☑ fail", "overflow at 375 px")))
    assert reason is not None, f"a ☑ fail {ui_row} row must block the push"
    assert "T900" in reason
    assert ui_row.split(" (")[0].split(" at ")[0] in reason


def test_a_failed_ui_row_blocks_whatever_produced_it():
    """Method-agnostic by design: the gate reads `fail`, not which tool wrote
    it. An LLM-vision fail blocks exactly as an easy-ui fail does."""
    reason, _ = gate(review_with(
        row(UI_ROWS[0], "☑ fail", "LLM vision verdict: header clipped, no easy-ui involved")))
    assert reason is not None


# ---------------------------------------------------------------------------
# AC 4 / SC 4 — every absence allows, and the no-row decision is unchanged
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("result,notes", [
    ("", ""),
    ("☐ pass / ☐ fail / ☐ N/A", "[overall + change_risk + scope + ref + report path]"),
    ("☑ N/A", "neither companion tool was run on this machine"),
    ("☑ N/A", ""),
    ("☐ fail", "the unchecked box is guidance, not an answer"),
], ids=["blank", "template-placeholder", "na-with-reason", "na-no-reason", "unchecked-fail"])
def test_absent_verdict_never_blocks(result, notes):
    reason, _ = gate(review_with(row(COMPANION, result, notes)))
    assert reason is None, reason


def test_no_companion_row_at_all_never_blocks():
    assert gate(review_with())[0] is None


def test_a_malformed_evidence_table_never_blocks():
    """A parse failure resolves to "no companion row" — the opposite of the
    `verify` row's fail-closed default, by design (D6)."""
    broken = REVIEW_HEADER + "| **Companion score (easy-verifier)** ☑ fail no pipes here\n"
    assert gate(broken)[0] is None


def test_an_unreadable_review_file_contributes_no_companion_block():
    """A parse failure must not raise, and must never be read as a failed row.

    The gate still blocks here — for the `verify` row, which fails **closed** on
    an unreadable file and is untouched by this task. The property under test is
    narrower: the companion check adds nothing to that reason.
    """
    if os.geteuid() == 0:
        pytest.skip("root bypasses file permissions")
    fixture = GateFixture(review=review_with(row(COMPANION, "☑ fail", "overall 62")))
    unreadable = os.path.join(fixture.main_tasks, "TASK_REVIEW_T900.md")
    try:
        os.chmod(unreadable, 0)
        stdout, stderr = run_gate("git push origin feat/t900")
        assert "Traceback" not in stderr, stderr
        assert "Companion score" not in stdout, stdout
        assert merge_gate.failed_companion_rows("T900", [fixture.main_tasks]) == []
    finally:
        os.chmod(unreadable, 0o644)
        fixture.cleanup()


# ---------------------------------------------------------------------------
# AC 5 / SC 2, SC 3 — a `pass` is trusted only against the report it cites
# ---------------------------------------------------------------------------

def test_pass_row_citing_an_existing_report_does_not_block_and_says_nothing():
    fixture = GateFixture(review=review_with())
    try:
        report = os.path.join(fixture.root, "score_changes_20261028.html")
        open(report, "w").write("<html>report</html>")
        GateFixture._write(
            fixture.main_tasks, "TASK_REVIEW_T900.md",
            review_with(row(COMPANION, "☑ pass",
                            f"overall 86 (>= 80), change_risk pass, scope changes, "
                            f"ref `main...HEAD`, report: `{report}`")))
        stdout, stderr = run_gate("git push origin feat/t900")
        assert stdout.strip() == "", stdout
        assert stderr.strip() == "", stderr
    finally:
        fixture.cleanup()


def test_pass_row_citing_a_missing_report_does_not_block_but_warns_once():
    reason, stderr = gate(review_with(
        row(COMPANION, "☑ pass",
            "overall 86, change_risk pass, scope changes, ref `main...HEAD`, "
            "report: /nonexistent/report.html")))
    assert reason is None, reason
    lines = [l for l in stderr.splitlines() if l.strip()]
    assert len(lines) == 1, lines
    assert "T900" in lines[0]
    assert "/nonexistent/report.html" in lines[0]


def test_pass_row_citing_no_path_does_not_block_but_warns_once():
    reason, stderr = gate(review_with(
        row(COMPANION, "☑ pass", "overall 86, change_risk pass — looked fine")))
    assert reason is None, reason
    lines = [l for l in stderr.splitlines() if l.strip()]
    assert len(lines) == 1, lines
    assert "T900" in lines[0]


def test_a_report_path_with_a_space_resolves():
    fixture = GateFixture(review=review_with())
    try:
        report = os.path.join(fixture.root, "score report.html")
        open(report, "w").write("<html>report</html>")
        GateFixture._write(
            fixture.main_tasks, "TASK_REVIEW_T900.md",
            review_with(row(COMPANION, "☑ pass", f"overall 86, report: `{report}`")))
        stdout, stderr = run_gate("git push origin feat/t900")
        assert stdout.strip() == "" and stderr.strip() == "", (stdout, stderr)
    finally:
        fixture.cleanup()


def test_a_tilde_report_path_is_expanded(monkeypatch):
    """`EASY_VERIFIER_REPORTS_DIR` writes to `$HOME/.easy-verifier-reports/<repo>/`,
    so a row may well cite a `~` path."""
    fixture = GateFixture(review=review_with())
    try:
        home = os.path.join(fixture.root, "home")
        os.makedirs(os.path.join(home, ".easy-verifier-reports", "kit"))
        report = os.path.join(home, ".easy-verifier-reports", "kit", "score.html")
        open(report, "w").write("<html>report</html>")
        monkeypatch.setenv("HOME", home)
        GateFixture._write(
            fixture.main_tasks, "TASK_REVIEW_T900.md",
            review_with(row(COMPANION, "☑ pass",
                            "overall 86, report: ~/.easy-verifier-reports/kit/score.html")))
        stdout, stderr = run_gate("git push origin feat/t900")
        assert stdout.strip() == "" and stderr.strip() == "", (stdout, stderr)
    finally:
        fixture.cleanup()


def test_a_report_path_that_is_a_directory_warns():
    fixture = GateFixture(review=review_with())
    try:
        reports = os.path.join(fixture.root, "reports")
        os.makedirs(reports)
        GateFixture._write(
            fixture.main_tasks, "TASK_REVIEW_T900.md",
            review_with(row(COMPANION, "☑ pass", f"overall 86, report: `{reports}`")))
        stdout, stderr = run_gate("git push origin feat/t900")
        assert stdout.strip() == "", stdout
        assert reports in stderr
    finally:
        fixture.cleanup()


def test_the_cited_path_is_checked_not_the_newest_in_the_directory():
    """Two live sessions, two reports for one task: the row's own citation is
    the only thing the gate resolves."""
    fixture = GateFixture(review=review_with())
    try:
        other = os.path.join(fixture.root, "score_other_session.html")
        open(other, "w").write("<html>other</html>")
        cited = os.path.join(fixture.root, "score_this_session.html")
        GateFixture._write(
            fixture.main_tasks, "TASK_REVIEW_T900.md",
            review_with(row(COMPANION, "☑ pass", f"overall 86, report: `{cited}`")))
        stdout, stderr = run_gate("git push origin feat/t900")
        assert stdout.strip() == "", stdout
        assert cited in stderr and "score_other_session" not in stderr
    finally:
        fixture.cleanup()


# --- FR-005 reads the `report:` label, not "the first path in the cell" (P1) --
#
# Both directions of the Stage 4 P1 are pinned here. The second is the one that
# matters: without the label, any unrelated existing path in the cell silenced
# the check, so a row citing no report at all passed FR-005.

def test_a_backticked_ref_before_the_report_path_is_not_mistaken_for_it():
    """FR-001 and T191's AC 11 require the ref in the same cell, and a ref is
    naturally backticked: `plan/t190-t194-companion-scoring...HEAD` carries a
    `/`. Reading the first path in the cell warned on this honest row."""
    fixture = GateFixture(review=review_with())
    try:
        report = os.path.join(fixture.root, "score.html")
        open(report, "w").write("<html>report</html>")
        notes = ("overall 86 (>= 80), change_risk pass, scope changes, "
                 f"ref `plan/t190-t194-companion-scoring...HEAD`, report: `{report}`")
        assert merge_gate.cited_report_path(notes, fixture.root) == report
        GateFixture._write(fixture.main_tasks, "TASK_REVIEW_T900.md",
                           review_with(row(COMPANION, "☑ pass", notes)))
        stdout, stderr = run_gate("git push origin feat/t900")
        assert stdout.strip() == "" and stderr.strip() == "", (stdout, stderr)
    finally:
        fixture.cleanup()


def test_an_unrelated_existing_path_cannot_silence_the_check():
    """Anti-vacuity for FR-005. `skills/score/SKILL.md` is a real file, so
    reading the first path in the cell made `os.path.isfile` true and suppressed
    the advisory for a row that cited no report whatsoever."""
    real_file = os.path.join(os.path.dirname(os.path.dirname(HOOKS_DIR)), "scripts", "validate.sh")
    assert os.path.isfile(real_file), real_file
    notes = f"overall 86, change_risk pass — see `{real_file}` for the runner"
    assert merge_gate.cited_report_path(notes, None) is None
    reason, stderr = gate(review_with(row(COMPANION, "☑ pass", notes)))
    assert reason is None, reason
    lines = [l for l in stderr.splitlines() if l.strip()]
    assert len(lines) == 1 and "cite no verifier report path" in lines[0], lines


def test_the_label_resolves_a_path_with_a_space_a_tilde_and_a_relative_path(monkeypatch):
    """The three shapes the edge-case checklist names, all after the label."""
    fixture = GateFixture(review=review_with())
    try:
        spaced = os.path.join(fixture.root, "score report.html")
        open(spaced, "w").write("x")
        assert merge_gate.cited_report_path(f"report: `{spaced}`", None) == spaced

        monkeypatch.setenv("HOME", fixture.root)
        assert merge_gate.cited_report_path("report: ~/score.html", None) == \
            os.path.join(fixture.root, "score.html")

        assert merge_gate.cited_report_path("report: reports/score.html", fixture.root) == \
            os.path.join(fixture.root, "reports", "score.html")
    finally:
        fixture.cleanup()


def test_no_report_label_means_no_citation():
    for notes in ("overall 86, change_risk pass",
                  "overall 86 — /home/u/score.html was written somewhere",
                  "see `main...HEAD`"):
        assert merge_gate.cited_report_path(notes, None) is None, notes


def test_a_missing_report_on_a_ui_row_is_not_checked():
    """FR-011: easy-ui is one named method among screenshot diff, LLM vision and
    Storybook snapshot, so a passing UI row cites no report file by design."""
    reason, stderr = gate(review_with(
        row(UI_ROWS[2], "☑ pass", "1280 px and 375 px, no overflow — LLM vision")))
    assert reason is None and stderr.strip() == "", (reason, stderr)


# ---------------------------------------------------------------------------
# AC 6 — the bare word `fail` in Notes prose is data, never a verdict
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("notes", [
    "no failures observed",
    "the M2 mutation must fail, and it does",
    "fail",
    "☑ fail was the pre-fix state; now passes",
], ids=["no-failures", "mutation-must-fail", "bare-word", "fail-glyph-in-notes"])
def test_the_word_fail_in_a_notes_cell_never_blocks(notes):
    fixture = GateFixture(review=review_with())
    try:
        report = os.path.join(fixture.root, "score.html")
        open(report, "w").write("<html>report</html>")
        GateFixture._write(
            fixture.main_tasks, "TASK_REVIEW_T900.md",
            review_with(row(COMPANION, "☑ pass", f"{notes} — report: `{report}`")))
        stdout, _ = run_gate("git push origin feat/t900")
        assert stdout.strip() == "", stdout
    finally:
        fixture.cleanup()


def test_the_word_fail_in_the_check_cell_never_blocks():
    reason, _ = gate(review_with(
        row("Companion score (easy-verifier) — fail means under the floor",
            "☑ pass", "overall 86, report missing")))
    assert reason is None, reason


def test_the_gate_reads_the_result_cell_not_the_whole_row():
    """The structural shape is the point: the same `fail` text blocks from the
    Result cell and is inert from the Notes cell."""
    assert gate(review_with(row(COMPANION, "☑ pass", "☑ fail")))[0] is None
    assert gate(review_with(row(COMPANION, "☑ fail", "☑ pass")))[0] is not None


def test_both_verdicts_in_one_result_cell_read_as_fail():
    """A careless edit leaves `☑ pass` and `☑ fail` side by side; the stricter
    reading wins."""
    assert gate(review_with(row(COMPANION, "☑ pass / ☑ fail", "overall 79")))[0] is not None


# ---------------------------------------------------------------------------
# The verdict spelling, and where the widening stops (Stage 4 P2)
#
# `fail\b` did not match `☑ failed`, so the `-ed` form was a silent allow — the
# worst failure mode this feature has, because nothing said why the gate stayed
# quiet. Both patterns now take `(?:ed)?`, symmetrically, and no further.
# ---------------------------------------------------------------------------

def test_a_checked_failed_blocks_like_a_checked_fail():
    reason, _ = gate(review_with(row(COMPANION, "☑ failed", "overall 62 (< 80)")))
    assert reason is not None, "`☑ failed` is a plausible human spelling and must block"
    assert "Companion score" in reason


@pytest.mark.parametrize("ui_row", UI_ROWS, ids=["visual", "design-system", "responsive"])
def test_a_checked_failed_blocks_in_a_ui_row_too(ui_row):
    assert gate(review_with(row(ui_row, "☑ failed", "overflow at 375 px")))[0] is not None


def test_a_checked_passed_is_still_read_as_a_pass_by_the_report_check():
    """The symmetry half: widening only the fail side would make `☑ passed`
    stop counting as a pass, so FR-005 would skip its report check on it."""
    reason, stderr = gate(review_with(
        row(COMPANION, "☑ passed", "overall 86, change_risk pass — looked fine")))
    assert reason is None, reason
    lines = [l for l in stderr.splitlines() if l.strip()]
    assert len(lines) == 1 and "cite no verifier report path" in lines[0], lines


@pytest.mark.parametrize("result", ["☑ failing", "☑ failure", "☑ failures", "☑ fails"],
                         ids=["failing", "failure", "failures", "fails"])
def test_the_widening_stops_at_the_ed_form(result):
    """Where the boundary is, asserted rather than assumed: `\b` after the
    optional `ed` is what keeps every prose variant out of the Result cell."""
    assert merge_gate.CHECKED_FAIL_PATTERN.search(result) is None, result
    assert gate(review_with(row(COMPANION, result, "overall 62")))[0] is None


def test_the_unchecked_template_guidance_is_still_not_a_verdict():
    """`UNCHECKED_PASS_PATTERN` and the `☐` box must be untouched by the
    widening — the template's own `☐ pass / ☐ fail / ☐ N/A` is guidance."""
    placeholder = "☐ pass / ☐ fail / ☐ N/A"
    assert merge_gate.CHECKED_FAIL_PATTERN.search(placeholder) is None
    assert merge_gate.CHECKED_PASS_PATTERN.search(placeholder) is None
    assert merge_gate.UNCHECKED_PASS_PATTERN.search(placeholder) is not None
    assert gate(review_with(row(COMPANION, placeholder, "[not filled in yet]")))[0] is None


# ---------------------------------------------------------------------------
# AC 7 — only a Ready-for-Review task is checked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kanban", [KANBAN_DONE, KANBAN_TODO], ids=["done", "todo"])
def test_a_failed_row_outside_ready_for_review_does_not_block(kanban):
    reason, _ = gate(review_with(row(COMPANION, "☑ fail", "overall 62")), kanban=kanban)
    assert reason is None, reason


def test_a_failed_row_on_a_task_absent_from_the_board_does_not_block():
    empty_board = "# PROJECT_KANBAN\n\n### Todo\n\n### In Progress\n\n### Ready for Review\n\n### Done\n"
    reason, _ = gate(review_with(row(COMPANION, "☑ fail", "overall 62")), kanban=empty_board)
    assert reason is None, reason


def test_a_command_that_is_not_a_push_or_merge_is_never_gated():
    reason, stderr = gate(review_with(row(COMPANION, "☑ fail", "overall 62")),
                          command="git status --short")
    assert reason is None and stderr.strip() == "", (reason, stderr)


# ---------------------------------------------------------------------------
# Both Evidence locations resolve (T064/T095), same as the `verify` row
# ---------------------------------------------------------------------------

def test_a_failed_row_in_the_task_guide_also_blocks():
    guide = GUIDE_WITH_VACATED_EVIDENCE.replace(
        "> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T900.md`.",
        "| Check | Result | Notes |\n|---|---|---|\n"
        "| verify | ☑ pass | verify skill run — pass |\n"
        + row(COMPANION, "☑ fail", "overall 62"))
    reason, _ = gate(None, guide=guide)
    assert reason is not None and "Companion score" in reason


def test_a_failed_row_in_a_worktree_blocks():
    """Stage 3 is worktree-isolated, so the review file lives on the task
    branch until it merges (T095 defect A)."""
    fixture = GateFixture(review=review_with())
    try:
        worktree_tasks = os.path.join(fixture.root, "wt-t900", "tasks")
        os.makedirs(worktree_tasks)
        GateFixture._write(worktree_tasks, "TASK_GUIDE_T900.md", GUIDE_WITH_VACATED_EVIDENCE)
        GateFixture._write(worktree_tasks, "TASK_REVIEW_T900.md",
                           review_with(row(COMPANION, "☑ fail", "overall 62")))
        os.remove(os.path.join(fixture.main_tasks, "TASK_REVIEW_T900.md"))
        stdout, _ = run_gate("git push origin feat/t900", worktree_dirs=[worktree_tasks])
        assert stdout.strip(), "a ☑ fail row in the worktree must block"
        assert "Companion score" in json.loads(stdout)["reason"]
    finally:
        fixture.cleanup()


# ---------------------------------------------------------------------------
# AC 4 / SC 4 — the pre-change oracle. Captured BEFORE the edit; equality here
# is what makes "optional" a measurement instead of a claim (FR-014).
# ---------------------------------------------------------------------------

NO_COMPANION_SCENARIOS = (
    ("filled verify row, push", review_with(), KANBAN_READY_FOR_REVIEW,
     "git push origin feat/t900"),
    ("filled verify row, merge", review_with(), KANBAN_READY_FOR_REVIEW,
     "git merge feat/t900"),
    ("filled verify row, rebase", review_with(), KANBAN_READY_FOR_REVIEW,
     "git rebase main"),
    ("no review file, push", None, KANBAN_READY_FOR_REVIEW,
     "git push origin feat/t900"),
    ("unfilled verify row, push",
     REVIEW_HEADER.replace("| verify | ☑ pass | verify skill run, feature confirmed working — pass |",
                           "| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed] |"),
     KANBAN_READY_FOR_REVIEW, "git push origin feat/t900"),
    ("task still in progress, push", review_with(),
     KANBAN_READY_FOR_REVIEW.replace("### In Progress\n",
                                     "### In Progress\n- [ ] **T901** — other | C1 | P1\n"),
     "git push origin feat/t900"),
    ("task done, push", review_with(), KANBAN_DONE, "git push origin feat/t900"),
    ("heredoc mentioning a push", review_with(), KANBAN_READY_FOR_REVIEW,
     HEREDOC_MENTIONING_A_PUSH),
    ("not a git command", review_with(), KANBAN_READY_FOR_REVIEW, "ls -la"),
)


def capture_no_companion_output():
    """The gate's full output across every no-companion-row scenario, as one
    deterministic string. Run against the pre-change hook it is the oracle;
    run against the post-change hook it must be identical."""
    chunks = []
    for name, review, kanban, command in NO_COMPANION_SCENARIOS:
        fixture = GateFixture(review=review, kanban=kanban)
        try:
            stdout, stderr = run_gate(command)
        finally:
            fixture.cleanup()
        chunks.append(
            f"=== {name} ===\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n"
        )
    return "".join(chunks)


def test_the_oracle_is_not_vacuous():
    """An oracle of nine empty outputs would prove nothing: at least one
    scenario must carry a real block message."""
    oracle = open(ORACLE_PATH, encoding="utf-8").read()
    assert "Pipeline gate failed" in oracle
    assert "T900 (no evidence row)" in oracle
    assert oracle.count("=== ") == len(NO_COMPANION_SCENARIOS)


def test_no_companion_rows_output_is_byte_identical_to_the_pre_change_gate():
    """SC 4: with no Companion score row and no UI rows, every byte the gate
    writes to stdout and stderr is what the pre-change hook wrote for the same
    input. This is FR-014 — the no-tool path is unchanged — as a measurement."""
    expected = open(ORACLE_PATH, encoding="utf-8").read()
    assert capture_no_companion_output() == expected


# ---------------------------------------------------------------------------
# Anti-vacuity — with the new check stubbed out, the blocking scenario must go
# back to passing the push. A test green with and without the change is noise.
# ---------------------------------------------------------------------------

def test_the_block_depends_on_the_new_check():
    failed = review_with(row(COMPANION, "☑ fail", "overall 62"))
    assert gate(failed)[0] is not None

    saved = merge_gate.failed_companion_rows
    try:
        merge_gate.failed_companion_rows = lambda task_id, tasks_dir=None: []
        assert gate(failed)[0] is None, "pre-change behaviour: no row is binding"
    finally:
        merge_gate.failed_companion_rows = saved


def test_the_advisory_depends_on_the_new_check():
    passed = review_with(row(COMPANION, "☑ pass", "overall 86, report: /nonexistent/x.html"))
    assert gate(passed)[1].strip() != ""

    saved = merge_gate.companion_report_advisories
    try:
        merge_gate.companion_report_advisories = lambda task_id, tasks_dir=None: []
        assert gate(passed)[1].strip() == ""
    finally:
        merge_gate.companion_report_advisories = saved


# ---------------------------------------------------------------------------
# AC 1 — the row exists in the template, in the shape the gate reads
# ---------------------------------------------------------------------------

REVIEW_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(HOOKS_DIR)), "templates", "TASK_REVIEW_template.md")


def test_the_template_carries_the_companion_score_row():
    template = open(REVIEW_TEMPLATE, encoding="utf-8").read()
    assert "| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A |" in template
    companion_line = [l for l in template.splitlines() if "Companion score" in l][0]
    for field in ("overall", "change_risk", "scope", "ref", "report:"):
        assert field in companion_line, f"the Notes cell never names {field}: {companion_line}"
    # The label is what `cited_report_path` reads; a placeholder without it would
    # teach every future row the shape FR-005 cannot check.
    assert merge_gate.REPORT_LABEL_PATTERN.search(companion_line)


def test_the_templates_unchecked_companion_row_does_not_block():
    """The row ships unchecked, so instantiating the template can never turn a
    push red (FR-006)."""
    template = open(REVIEW_TEMPLATE, encoding="utf-8").read()
    companion_line = [l for l in template.splitlines() if "Companion score" in l][0]
    assert gate(review_with(companion_line + "\n"))[0] is None


def test_the_companion_row_is_not_mistaken_for_the_verify_row():
    """`easy-verifier` contains `verify`. The T026 row pattern requires the word
    immediately before its `|`, so the new row must never satisfy it."""
    filled = "| **Companion score (easy-verifier)** | ☑ pass | overall 86 — pass |"
    assert merge_gate.VERIFY_ROW_PATTERN.search(filled) is None


if __name__ == "__main__":
    if "--capture-oracle" in sys.argv:
        with open(ORACLE_PATH, "w", encoding="utf-8") as f:
            f.write(capture_no_companion_output())
        print(f"oracle written: {ORACLE_PATH}")
    else:
        print(__doc__)
