#!/usr/bin/env python3
"""T210 — the merge gate closes four gaps (G1-G4, design D1-D4 in tasks/TASK_GUIDE_T210.md).

  * G1/D1 — `git pull` (fetch + merge) is gated like `git merge`, in every form.
  * G2/D2 — a test run wrapped in `timeout <N>` counts as a test run.
  * G3/D3 — a read-only `git merge-base` is never blocked; `merge-file`/`merge-tree` still are.
  * G4/D4 — for a merge or a narrowed push of a task branch, the `verify` row counts only when it
    is committed on that branch. A row that is only in a working tree gets its own message. When
    the branch cannot be resolved, the gate keeps the pre-T210 behaviour (working trees).

Every board, guide, trace and git repo here is constructed. Git runs with the user's global and
system config switched off.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_t210.py -v
"""
import io
import json
import os
import subprocess
import sys
import types

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def load_hook_module(path, name):
    """Load the hook without running its bottom-of-file `main()` (see test_merge_gate_evidence)."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "merge_gate_t210")
import verify_record  # noqa: E402  (on sys.path: the hook put its lib/ there)

# Spelled in halves so this file's own text never reads as a command to the live gate.
G = "git "
PULL, MERGE, PUSH = G + "pull", G + "merge", G + "push"

GUIDE_VACATED = "# TASK_GUIDE - {tid}\n\n## Evidence\n\n> Moved to `tasks/TASK_REVIEW_{tid}.md`.\n"
REVIEW = ("# TASK_REVIEW - {tid}\n\n## Evidence\n\n| Check | Result | Notes |\n|---|---|---|\n"
          "| verify | {result} | {notes} |\n")
MANUAL_PASS = ("☑ pass", "verify skill run, feature confirmed working — pass")
UNCOMMITTED = "verify row for T900 is not committed on feat/t900-x — commit it, then merge"


def kanban(in_progress=(), ready=(), done=()):
    rows = lambda ids: "".join(f"- [ ] **{t}** — fixture {t} | agent | C1 | Risk: Low | P1\n"
                               for t in ids)
    return ("# PROJECT_KANBAN\n\n### Todo\n\n### In Progress\n" + rows(in_progress)
            + "\n### Ready for Review\n" + rows(ready) + "\n### Done\n" + rows(done))


def trace_record(command):
    return json.dumps({"timestamp": "2026-10-29T00:00:00+00:00", "tool_name": "Bash",
                       "summary": json.dumps({"command": command})[:300], "is_error": False})


def git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), "-c", "user.email=t@example.com",
                           "-c", "user.name=t", *args], capture_output=True, text=True,
                          timeout=30, env={**os.environ, **GIT_ENV})
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def write(path, text):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class Fixture:
    """A constructed main checkout that is a real git repo on `main`, plus the task worktree
    `wt-t900` on `feat/t900-x`, with the hook module pointed at it."""

    def __init__(self, root, board):
        self.root = str(root)
        self.main = os.path.join(self.root, "main")
        self.tasks = os.path.join(self.main, "tasks")
        self.trace = os.path.join(self.main, "memory", "event-trace")
        os.makedirs(self.tasks)
        os.makedirs(self.trace)
        self.kanban = os.path.join(self.main, "PROJECT_KANBAN.md")
        write(self.kanban, board)
        git(self.main, "init", "-q", "-b", "main")
        git(self.main, "commit", "-q", "--allow-empty", "-m", "base")
        self.wt = os.path.join(self.root, "wt-t900")
        git(self.main, "worktree", "add", "-q", "-b", "feat/t900-x", self.wt)
        for tid in ("T900", "T901"):
            write(os.path.join(self.trace, f"{tid}.jsonl"),
                  trace_record("python3 -m pytest -q") + "\n")

    def task_file(self, name, text, commit=False, where=None):
        write(os.path.join(where or self.wt, "tasks", name), text)
        if commit:
            git(where or self.wt, "add", "-A")
            git(where or self.wt, "commit", "-qm", f"T900: {name}")

    def review(self, result=MANUAL_PASS, commit=False):
        self.task_file("TASK_GUIDE_T900.md", GUIDE_VACATED.format(tid="T900"), commit=True)
        self.task_file("TASK_REVIEW_T900.md", REVIEW.format(tid="T900", result=result[0],
                                                          notes=result[1]), commit=commit)


@pytest.fixture
def gate(tmp_path, monkeypatch):
    for key, value in GIT_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("CLAUDE_TRACE_ANCHOR_DIR", str(tmp_path / "anchors"))

    def build(board):
        fx = Fixture(tmp_path / "fx", board)
        monkeypatch.setattr(merge_gate, "KANBAN", fx.kanban)
        monkeypatch.setattr(merge_gate, "TASKS_DIR", fx.tasks)
        monkeypatch.setattr(merge_gate, "TRACE_DIR", fx.trace)
        monkeypatch.setattr(merge_gate, "worktree_tasks_dirs",
                            lambda: [os.path.join(fx.wt, "tasks")])
        return fx
    return build


def reason(command, cwd=None):
    """Drive the hook's real `main()`; the block reason, or None when it allows."""
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    if cwd is not None:
        event["cwd"] = cwd
    saved = (sys.stdin, sys.stdout, sys.stderr)
    sys.stdin, sys.stdout, sys.stderr = io.StringIO(json.dumps(event)), io.StringIO(), io.StringIO()
    try:
        try:
            merge_gate.main()
        except SystemExit:
            pass
        out = sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved
    return json.loads(out)["reason"] if out.strip() else None


# ---------------------------------------------------------------------------
# AC 1 — `git pull` is a merge (G1, D1)
# ---------------------------------------------------------------------------

PULLS = [PULL, PULL + " --ff-only", PULL + " --rebase origin main", "cd x && " + PULL,
         'bash -c "' + PULL + '"', PULL + "\n"]


@pytest.mark.parametrize("command", PULLS,
                         ids=["bare", "ff-only", "rebase", "after-cd", "bash-c", "newline"])
def test_ac1_pull_is_blocked_with_the_merge_message_while_a_task_is_open(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    text = reason(command, fx.main)
    assert text is not None, f"{command!r} must be gated like a merge"
    assert "cannot push/merge" in text and "Tasks still In Progress: T900" in text


@pytest.mark.parametrize("command", PULLS[:4], ids=["bare", "ff-only", "rebase", "after-cd"])
def test_ac1_pull_is_allowed_with_a_clean_board(gate, command):
    fx = gate(kanban(done=("T900",)))
    assert reason(command, fx.main) is None


def test_ac1_a_quoted_mention_of_pull_is_data(gate):
    fx = gate(kanban(in_progress=("T900",)))
    assert reason('grep -n "' + PULL + '" notes.md', fx.main) is None


# ---------------------------------------------------------------------------
# AC 2 — `git merge-base` is read-only (G3, D3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command", [G + "merge-base --is-ancestor A B", G + "merge-base A B",
                                     "cd x && " + G + "merge-base --is-ancestor HEAD main"])
def test_ac2_merge_base_is_allowed_while_a_task_is_open(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    assert reason(command, fx.main) is None


@pytest.mark.parametrize("command", [MERGE + " feat/x", G + "merge-file a b c",
                                     G + "merge-tree a b",
                                     G + "merge-base A B && " + MERGE + " feat/x"],
                         ids=["merge", "merge-file", "merge-tree", "merge-base-then-merge"])
def test_ac2_merge_and_the_other_merge_subcommands_stay_blocked(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    text = reason(command, fx.main)
    assert text is not None and "Tasks still In Progress: T900" in text


# ---------------------------------------------------------------------------
# AC 3 — a `timeout`-wrapped test run counts (G2, D2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command", ["timeout 900 python3 -m pytest -q",
                                     "timeout -k 5 60s pytest",
                                     "(timeout 300 python3 -m pytest .claude/hooks/tests -q)",
                                     "timeout --signal=KILL 1.5m python3 -m pytest",
                                     "cd /x && timeout 900 python3 -m pytest -q"])
def test_ac3_a_timeout_wrapped_test_run_counts(command):
    assert merge_gate.invokes_test_runner(command)


@pytest.mark.parametrize("command", ["timeout 900 echo pytest", "timeout pytest",
                                     "timeout 900 grep pytest log.txt", "echo timeout 900 pytest"])
def test_ac3_timeout_does_not_make_a_mention_a_run(command):
    assert not merge_gate.invokes_test_runner(command)


def test_ac3_a_trace_whose_only_run_is_timeout_wrapped_verifies(tmp_path, monkeypatch):
    write(tmp_path / "T900.jsonl", trace_record("timeout 900 python3 -m pytest -q") + "\n")
    monkeypatch.setattr(merge_gate, "TRACE_DIR", str(tmp_path))
    assert merge_gate.trace_shows_verification("T900")


# ---------------------------------------------------------------------------
# AC 4 — the verify row must be committed on the branch (G4, D4)
# ---------------------------------------------------------------------------

def test_ac4_merge_with_the_row_only_in_the_working_tree_is_blocked_with_the_d4_message(gate):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    assert merge_gate.has_filled_verify_row("T900")  # the working tree does hold it
    text = reason(MERGE + " --no-ff feat/t900-x", fx.main)
    assert text is not None and UNCOMMITTED in text, text
    assert "T900 (no evidence row)" not in text


def test_ac4_merge_after_committing_the_row_is_allowed(gate):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    assert reason(MERGE + " feat/t900-x", fx.main) is not None
    git(fx.wt, "add", "-A")
    git(fx.wt, "commit", "-qm", "T900: verify row")
    assert reason(MERGE + " feat/t900-x", fx.main) is None


def test_ac4_narrowed_push_with_the_row_only_in_the_working_tree_is_blocked(gate):
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=False)
    text = reason(PUSH + " origin feat/t900-x", fx.wt)
    assert text is not None and UNCOMMITTED in text, text
    assert "T901" not in text  # still narrowed to T900 (T197)


def test_ac4_narrowed_push_after_committing_the_row_is_allowed(gate):
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=True)
    assert reason(PUSH + " origin feat/t900-x", fx.wt) is None
    assert reason(PUSH + " -u origin HEAD", fx.wt) is None


def test_ac4_no_row_anywhere_keeps_the_no_evidence_message(gate):
    fx = gate(kanban(ready=("T900",)))
    text = reason(MERGE + " feat/t900-x", fx.main)
    assert text is not None and "T900 (no evidence row)" in text
    assert "not committed" not in text


def test_ac4_merge_still_checks_the_whole_board(gate):
    """D4 changes where T900's row is read; it never narrows a merge (T197 D4)."""
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=True)
    text = reason(MERGE + " feat/t900-x", fx.main)
    assert text is not None and "T901 (no evidence row)" in text
    assert "T900" not in text


def test_ac4_the_auto_verify_flow_passes_once_the_hook_row_is_committed(gate):
    """T207/T208: the run verifies commit V; the hook writes the row after V; the Supervisor
    commits only the review file. The committed row is confirmed against the branch tip."""
    fx = gate(kanban(ready=("T900",)))
    fx.task_file("TASK_GUIDE_T900.md", GUIDE_VACATED.format(tid="T900"), commit=True)
    verified = git(fx.wt, "rev-parse", "HEAD")
    verify_record.write_record(merge_gate.ROOT, "T900", verified, "pass", "s-1", "log.txt")
    cells = verify_record.row_cells(verified, "pass", "s-1", "log.txt")
    fx.task_file("TASK_REVIEW_T900.md", REVIEW.format(tid="T900", result=cells[0],
                                                      notes=cells[1]))
    text = reason(MERGE + " feat/t900-x", fx.main)
    assert text is not None and UNCOMMITTED in text, text
    git(fx.wt, "add", "-A")
    git(fx.wt, "commit", "-qm", "T900: hook-written verify row")
    assert reason(MERGE + " feat/t900-x", fx.main) is None


def test_ac4_a_committed_auto_row_with_more_code_after_it_is_not_confirmed(gate):
    fx = gate(kanban(ready=("T900",)))
    fx.task_file("TASK_GUIDE_T900.md", GUIDE_VACATED.format(tid="T900"), commit=True)
    verified = git(fx.wt, "rev-parse", "HEAD")
    verify_record.write_record(merge_gate.ROOT, "T900", verified, "pass", "s-1", "log.txt")
    cells = verify_record.row_cells(verified, "pass", "s-1", "log.txt")
    fx.task_file("TASK_REVIEW_T900.md", REVIEW.format(tid="T900", result=cells[0],
                                                      notes=cells[1]), commit=True)
    fx.task_file("../code.py", "x = 2\n", commit=True)  # code changed after the verified run
    assert reason(MERGE + " feat/t900-x", fx.main) is not None


def test_ac4_guide_first_a_row_committed_in_the_guide_counts(gate):
    fx = gate(kanban(ready=("T900",)))
    fx.task_file("TASK_GUIDE_T900.md", REVIEW.format(tid="T900", result=MANUAL_PASS[0],
                                                     notes=MANUAL_PASS[1]), commit=True)
    assert reason(MERGE + " feat/t900-x", fx.main) is None


def test_ac4_guide_first_a_filled_guide_section_shadows_the_review_file(gate):
    """Same precedence as `read_guide_section`: a guide Evidence table with no pass wins over a
    review file that has one."""
    fx = gate(kanban(ready=("T900",)))
    fx.task_file("TASK_GUIDE_T900.md", REVIEW.format(tid="T900", result="☐ pass / ☐ fail",
                                                     notes="[to fill]"), commit=True)
    fx.task_file("TASK_REVIEW_T900.md", REVIEW.format(tid="T900", result=MANUAL_PASS[0],
                                                      notes=MANUAL_PASS[1]), commit=True)
    assert reason(MERGE + " feat/t900-x", fx.main) is not None


def test_ac4_a_minimal_track_verify_line_is_read_from_the_branch(gate):
    """Minimal track: no Evidence table, the `verify:` line of the Decision record counts —
    read from the branch too, never only from the working tree."""
    fx = gate(kanban(ready=("T900",)))
    verified = git(fx.wt, "rev-parse", "HEAD")
    verify_record.write_record(merge_gate.ROOT, "T900", verified, "pass", "s-2", "log.txt")
    line = verify_record.record_line(verified, "pass", "s-2", "log.txt")
    record = ("# MINIMAL_LOG\n\n## T900 — fixture\n\n**Track:** minimal\n"
              f"**Checked:** tests pass\n- {line}\n**Not done:** merge (yours)\n")
    fx.task_file("MINIMAL_LOG.md", record)
    assert merge_gate.has_filled_verify_row("T900")
    assert UNCOMMITTED in (reason(MERGE + " feat/t900-x", fx.main) or "")
    git(fx.wt, "add", "-A")
    git(fx.wt, "commit", "-qm", "T900: Decision record")
    assert reason(MERGE + " feat/t900-x", fx.main) is None


@pytest.mark.parametrize("branch", ["feat/t900-x", "fix/sub/t900-deep"])
def test_edge_branch_names_with_slashes_resolve(gate, branch):
    fx = gate(kanban(ready=("T900",)))
    if branch != "feat/t900-x":
        git(fx.main, "branch", branch, "feat/t900-x")
    assert merge_gate.branch_target(MERGE + " " + branch, fx.main) == ("T900", branch, fx.main)


# ---------------------------------------------------------------------------
# AC 5 — branch not resolvable: today's behaviour (working trees), never weaker
# ---------------------------------------------------------------------------

# T211 D2 retired two cases here: a merge option (`--strategy=ours`) now resolves to its branch,
# and an octopus merge resolves every branch and blocks on doubt — see test_merge_gate_t211.py AC 3/4.
@pytest.mark.parametrize("command", [
    MERGE + " main",                          # names no task
    MERGE + " feat/t900-gone",                # names T900, but no such branch
    PULL + " origin feat/t900-x",             # pull: the merged commit is not local yet
    PUSH + " origin feat/t900-x && " + MERGE + " main",
], ids=["no-task", "no-such-branch", "pull", "push-and-merge"])
def test_ac5_unresolved_branch_reads_the_working_trees_as_before(gate, command):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    assert merge_gate.branch_target(command, fx.main) is None or "gone" in command
    assert reason(command, fx.main) is None  # pre-T210: the working-tree row allows


def test_ac5_unresolved_branch_still_blocks_without_any_row(gate):
    fx = gate(kanban(ready=("T900",)))
    text = reason(MERGE + " --strategy=ours feat/t900-x", fx.main)
    assert text is not None and "T900 (no evidence row)" in text


def test_ac5_detached_head_push_reads_the_working_trees_as_before(gate):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    git(fx.wt, "checkout", "-q", "--detach")
    assert merge_gate.branch_target(PUSH + " origin HEAD", fx.wt) is None
    assert reason(PUSH + " origin HEAD", fx.wt) is None


def test_ac5_a_git_failure_resolving_the_tip_reads_the_working_trees(gate, monkeypatch):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    real = merge_gate._git
    monkeypatch.setattr(merge_gate, "_git", lambda d, *a: None if a[:1] == ("rev-parse",)
                        and a[-1].endswith("^{commit}") else real(d, *a))
    assert merge_gate.committed_verify_row("T900", "feat/t900-x", fx.main) is None
    assert reason(MERGE + " feat/t900-x", fx.main) is None
