#!/usr/bin/env python3
"""T211 — the merge gate sees `git -C`/`-c` forms and resolves a merge whatever its options
(G5-G7, design D1-D4 in tasks/TASK_GUIDE_T211.md).

  * G5/D1 — global options between `git` and its verb (`-C <dir>`, `-c <k=v>`, `--git-dir`, …)
    no longer hide a push, merge, pull or rebase; `-C <dir>` moves the directory the T197 push
    scope resolves in, exactly like `cd <dir> &&`.
  * G6/D2 — `git merge` skips any option (and the argument of the options that take one), so
    `-X ours`, `--strategy`, … resolve to their branch and the T210 D4 committed-row rule
    applies. An octopus merge resolves every branch; any doubt about one blocks, naming it.
  * G7/D3 — `-c alias.<x>=…` in a `git` command is gated as a merge (whole board).
  * D4 — an unknown global option is skipped like a known one: fail closed.

The fixture (a real git repo on `main` plus worktree `wt-t900` on `feat/t900-x`) is T210's.
Git runs with the user's global and system config switched off.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_t211.py -v
"""
import os
import time

import pytest

from test_merge_gate_t210 import (  # noqa: F401  (`gate` is a fixture, used by name)
    G, MANUAL_PASS, MERGE, PUSH, REVIEW, gate, git, kanban, merge_gate, reason, write)

# Spelled in halves so this file's own text never reads as a command to the live gate.
PULL_, REBASE_ = G + "pull", G + "rebase"


def uncommitted(tid, branch):
    return f"verify row for {tid} is not committed on {branch} — commit it, then merge"


# ---------------------------------------------------------------------------
# AC 1 — global options between `git` and the verb (G5, D1, D4)
# ---------------------------------------------------------------------------

GATED = [
    G + "-C ../wt-x merge feat/x",
    G + "-C /abs push origin feat/x",
    G + "-c core.x=y merge feat/x",
    G + "--git-dir=.git push",
    G + "--no-pager pull",
    G + "-C x rebase main",
    # the rest of D1's list, each form
    G + "--git-dir .git push",
    G + "--work-tree=. merge feat/x",
    G + "--work-tree . merge feat/x",
    G + "--namespace=n push",
    G + "--namespace n push",
    G + "-P merge feat/x",
    G + "--bare push",
    G + "--no-replace-objects --literal-pathspecs pull",
    G + "--exec-path=/x push",
    G + "--exec-path push",
    G + "-C a -c b=c --no-pager -C d push origin main",
    # D4: unknown options are skipped like known ones
    G + "--unknown-opt push",
    G + "-x merge feat/x",
    G + "--x=y rebase main",
    # edge cases from the guide
    G + '-C "dir with space" push',
    G + "-Cdir push",
    G + "-cfoo=bar merge feat/x",
    # still code when a wrapper runs it (T099)
    'bash -c "' + G + '-C x push"',
    "cd x && " + G + "-C y pull",
    G + "-C x merge-file a b c",
]


@pytest.mark.parametrize("command", GATED)
def test_ac1_a_global_option_does_not_hide_the_verb(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    text = reason(command, fx.main)
    assert text is not None, f"{command!r} must be gated"
    assert "cannot push/merge" in text and "Tasks still In Progress: T900" in text


@pytest.mark.parametrize("command", [
    G + "-C x merge-base A B",
    G + "-C x log",
    G + "-C x merge-base --is-ancestor HEAD main",
    G + "--no-pager log --oneline",
    G + "-c core.x=y status",
    G + "-C x log --grep push",
])
def test_ac1_a_read_only_command_behind_global_options_is_allowed(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    assert reason(command, fx.main) is None


@pytest.mark.parametrize("command", GATED[:6])
def test_ac1_the_same_commands_are_allowed_with_a_clean_board(gate, command):
    fx = gate(kanban(done=("T900",)))
    assert reason(command, fx.main) is None


def test_ac1_a_long_run_of_global_options_is_classified_quickly(gate):
    """The shared prefix must not backtrack exponentially: each option consumes its argument."""
    fx = gate(kanban(in_progress=("T900",)))
    command = G + "-C -C " * 200 + "-c -c " * 200 + "--git-dir --git-dir " * 200 + "log"
    started = time.monotonic()
    assert reason(command, fx.main) is None
    assert reason(command[:-3] + "push", fx.main) is not None
    assert time.monotonic() - started < 5


# ---------------------------------------------------------------------------
# AC 2 — `git -C <worktree> push` narrows like `cd <worktree> && git push` (D1, T197)
# ---------------------------------------------------------------------------

def test_ac2_dash_c_push_resolves_to_the_task_like_cd(gate):
    fx = gate(kanban(ready=("T900", "T901")))
    dash_c = G + f"-C {fx.wt} push origin feat/t900-x"
    cd = f"cd {fx.wt} && " + PUSH + " origin feat/t900-x"
    assert merge_gate.pushed_task_ids(dash_c, fx.main) == "T900"
    assert merge_gate.pushed_task_ids(cd, fx.main) == "T900"
    assert merge_gate.branch_targets(dash_c, fx.main) == merge_gate.branch_targets(cd, fx.main)


def test_ac2_dash_c_push_is_judged_by_its_task_alone(gate):
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=False)
    dash_c = G + f"-C {fx.wt} push origin feat/t900-x"
    cd = f"cd {fx.wt} && " + PUSH + " origin feat/t900-x"
    text = reason(dash_c, fx.main)
    assert text is not None and uncommitted("T900", "feat/t900-x") in text, text
    assert "T901" not in text
    assert text == reason(cd, fx.main)
    git(fx.wt, "add", "-A")
    git(fx.wt, "commit", "-qm", "T900: verify row")
    assert reason(dash_c, fx.main) is None
    assert reason(cd, fx.main) is None


@pytest.mark.parametrize("command", [
    G + "-c push.default=matching push origin feat/t900-x",   # config can move the destination
    G + "-c remote.origin.mirror=true push origin feat/t900-x",
    G + "--git-dir=/other/.git push origin feat/t900-x",       # another repository
    G + "--namespace=n push origin feat/t900-x",
    G + "-Cdir push origin feat/t900-x",                       # attached form: not resolved
    G + "-c core.fsmonitor=x status && " + PUSH + " origin feat/t900-x",
])
def test_ac2_a_push_with_any_other_global_option_checks_the_whole_board(gate, command):
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=True)
    assert merge_gate.pushed_task_ids(command, fx.wt) is None
    text = reason(command, fx.wt)
    assert text is not None and "T901 (no evidence row)" in text


# ---------------------------------------------------------------------------
# AC 3 — a merge resolves to its branch whatever its options (G6, D2)
# ---------------------------------------------------------------------------

MERGE_OPTION_FORMS = [
    "-X ours", "-s recursive", "--strategy=ours", "--allow-unrelated-histories",
    "-Xours", "--strategy ours", "--strategy-option ours", "--strategy-option=ours", "-S",
    "--into-name main", "-m 'message with feat/x in it'", "-F msg.txt", "--no-ff -X ours -q",
    "--cleanup=strip", "--",
]


@pytest.mark.parametrize("options", MERGE_OPTION_FORMS)
def test_ac3_a_merge_with_any_option_resolves_to_its_branch(gate, options):
    fx = gate(kanban(ready=("T900",)))
    command = MERGE + f" {options} feat/t900-x"
    targets, doubts = merge_gate.branch_targets(command, fx.main)
    assert targets == [("T900", "feat/t900-x", fx.main)] and doubts == []


@pytest.mark.parametrize("options", ["-X ours", "-s recursive", "--strategy=ours",
                                     "--allow-unrelated-histories"])
def test_ac3_row_only_in_the_worktree_is_blocked_then_allowed_once_committed(gate, options):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    command = MERGE + f" {options} feat/t900-x"
    text = reason(command, fx.main)
    assert text is not None and uncommitted("T900", "feat/t900-x") in text, text
    git(fx.wt, "add", "-A")
    git(fx.wt, "commit", "-qm", "T900: verify row")
    assert reason(command, fx.main) is None


def test_ac3_a_global_dash_c_merge_needs_the_committed_row(gate):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    command = G + "-c core.x=y merge feat/t900-x"
    assert uncommitted("T900", "feat/t900-x") in (reason(command, fx.main) or "")
    command = G + f"-C {fx.main} merge -X ours feat/t900-x"
    assert uncommitted("T900", "feat/t900-x") in (reason(command, fx.wt) or "")


def test_edge_the_message_of_dash_m_is_not_a_branch(gate):
    fx = gate(kanban(ready=("T900",)))
    command = MERGE + ' -m "message with feat/t901-y in it" feat/t900-x'
    assert merge_gate.branch_targets(command, fx.main) == (
        [("T900", "feat/t900-x", fx.main)], [])


# ---------------------------------------------------------------------------
# AC 4 — an octopus merge: every branch, every doubt blocks (D2)
# ---------------------------------------------------------------------------

def add_t901(fx, monkeypatch, commit):
    """Worktree `wt-t901` on `feat/t901-y` with a manual verify pass, committed or not."""
    wt = os.path.join(fx.root, "wt-t901")
    git(fx.main, "worktree", "add", "-q", "-b", "feat/t901-y", wt)
    write(os.path.join(wt, "tasks", "TASK_REVIEW_T901.md"),
          REVIEW.format(tid="T901", result=MANUAL_PASS[0], notes=MANUAL_PASS[1]))
    if commit:
        git(wt, "add", "-A")
        git(wt, "commit", "-qm", "T901: verify row")
    monkeypatch.setattr(merge_gate, "worktree_tasks_dirs",
                        lambda: [os.path.join(fx.wt, "tasks"), os.path.join(wt, "tasks")])
    return wt


OCTOPUS = MERGE + " feat/t900-x feat/t901-y"


def test_ac4_octopus_with_both_rows_committed_is_allowed(gate, monkeypatch):
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=True)
    add_t901(fx, monkeypatch, commit=True)
    targets, doubts = merge_gate.branch_targets(OCTOPUS, fx.main)
    assert sorted(targets) == [("T900", "feat/t900-x", fx.main), ("T901", "feat/t901-y", fx.main)]
    assert doubts == []
    assert reason(OCTOPUS, fx.main) is None
    assert reason(MERGE + " -X ours feat/t900-x feat/t901-y", fx.main) is None


def test_ac4_octopus_with_the_second_row_uncommitted_names_that_branch(gate, monkeypatch):
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=True)
    add_t901(fx, monkeypatch, commit=False)
    text = reason(OCTOPUS, fx.main)
    assert text is not None and uncommitted("T901", "feat/t901-y") in text, text
    assert "T900" not in text


def test_ac4_octopus_with_the_first_row_uncommitted_names_that_branch(gate, monkeypatch):
    """M3: resolving an octopus to its first branch only would still pass this one; the test
    above is the one it turns RED."""
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=False)
    add_t901(fx, monkeypatch, commit=True)
    text = reason(OCTOPUS, fx.main)
    assert text is not None and uncommitted("T900", "feat/t900-x") in text, text
    assert "T901" not in text


@pytest.mark.parametrize("second", ["main", "feat/t901-gone", "plan/t900-t901"],
                         ids=["no-task", "no-such-branch", "two-tasks"])
def test_ac4_octopus_with_a_doubtful_branch_is_blocked_naming_it(gate, second):
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=True)
    if second == "plan/t900-t901":
        git(fx.main, "branch", second)
    command = MERGE + f" feat/t900-x {second}"
    targets, doubts = merge_gate.branch_targets(command, fx.main)
    assert doubts == [second]
    text = reason(command, fx.main)
    assert text is not None and second in text, text
    assert "octopus" in text


def test_ac4_a_single_unresolvable_branch_keeps_the_t210_working_tree_read(gate):
    """D2 changes octopus merges only: one branch naming no task is still the pre-T210 read."""
    fx = gate(kanban(ready=("T900",)))
    fx.review(commit=False)
    assert merge_gate.branch_targets(MERGE + " main", fx.main) == ([], [])
    assert reason(MERGE + " main", fx.main) is None


# ---------------------------------------------------------------------------
# AC 5 — `-c alias.<x>=…` is gated as a merge (G7, D3)
# ---------------------------------------------------------------------------

ALIASES = [
    G + "-c alias.p=push p",
    G + "-c alias.m='merge' m feat/x",
    G + '-c alias.m="merge" m feat/x',
    G + "-c Alias.p=push p",
    G + "-calias.p=push p",
    G + "-C x -c alias.p=push p origin main",
    G + "--config-env alias.p=VAR p",
    G + "--config-env=alias.p=VAR p",
    "echo hi; " + G + "-c alias.p=push p",
    "cd x && " + G + "-c 'alias.p=!f() { :; }; f' p",
]


@pytest.mark.parametrize("command", ALIASES)
def test_ac5_an_inline_alias_is_gated(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    text = reason(command, fx.main)
    assert text is not None, f"{command!r} must be gated"
    assert "Tasks still In Progress: T900" in text


def test_ac5_an_inline_alias_checks_the_whole_board(gate):
    """Gated as a merge: never narrowed to one task, even run from a task's worktree."""
    fx = gate(kanban(ready=("T900", "T901")))
    fx.review(commit=True)
    command = G + "-c alias.p=push p origin feat/t900-x"
    assert merge_gate.pushed_task_ids(command, fx.wt) is None
    assert merge_gate.branch_targets(command, fx.wt) == ([], [])
    text = reason(command, fx.wt)
    assert text is not None and "T901 (no evidence row)" in text


@pytest.mark.parametrize("command", ALIASES[:2])
def test_ac5_an_inline_alias_is_allowed_with_a_clean_board(gate, command):
    fx = gate(kanban(done=("T900",)))
    assert reason(command, fx.main) is None


# ---------------------------------------------------------------------------
# AC 6 — mentions stay mentions (T099 rules unchanged)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    'grep "' + G + '-C x push" notes.md',
    'grep -n "' + G + '-c alias.p=push p" notes.md',
    "cat > notes.md <<'EOF'\n" + G + "-C x push\n" + G + "-c alias.p=push p\nEOF",
    "echo " + G + "-c alias.p=push p",
    'echo "' + G + '--no-pager merge feat/x"',
    "printf '%s\\n' '" + G + "-C x pull'",
])
def test_ac6_a_mention_is_allowed(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    assert reason(command, fx.main) is None


@pytest.mark.parametrize("command", [
    'bash -c "' + G + '-c alias.p=push p"',
    "echo hi | " + G + "-c alias.p=push p",
    "xargs " + G + "-c alias.p=push p",
    "cat > f <<'EOF'\nbody\nEOF\n" + G + "-C x push",
])
def test_ac6_code_next_to_a_mention_is_still_gated(gate, command):
    fx = gate(kanban(in_progress=("T900",)))
    assert reason(command, fx.main) is not None


# ---------------------------------------------------------------------------
# AC 7 — the sign-off is on the record
# ---------------------------------------------------------------------------

def test_ac7_t211_is_authorised_to_change_the_gate():
    import merge_gate_guard
    assert "T211" in merge_gate_guard.AUTHORISED_TASKS
