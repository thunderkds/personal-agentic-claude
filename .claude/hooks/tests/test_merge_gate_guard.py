#!/usr/bin/env python3
"""T188 P2 — the merge-gate tripwire itself, tested against a synthetic history.

`merge_gate_guard.unauthorised_gate_commits` is the one definition of who may change
`.claude/hooks/pre_bash_block_unsafe_merge.py`, asserted by two suites. Until now it had never been
shown to reject anything: it read `all("T182" in subject ...)`, and the T188 commit that legitimately
changed the gate named both T188 and T182, so it passed — as would any later commit that merely
mentioned T182 while changing the gate. A check that has never rejected anything is not a check
(T044 defect C, same lesson).

Every test builds a throwaway git repo, so the live repo's history is never read.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_guard.py -v
"""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merge_gate_guard as guard  # noqa: E402

GATE = guard.GATE_REL


def _git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def _repo(tmp_path):
    """A repo whose first commit adds the gate file, and that first commit's sha."""
    repo = tmp_path / "repo"
    (repo / os.path.dirname(GATE)).mkdir(parents=True)
    (repo / GATE).write_text("# the gate\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base: add the gate")
    return repo, _git(repo, "rev-parse", "HEAD")


def _change(repo, subject, text="# the gate, changed\n"):
    (repo / GATE).write_text(text, encoding="utf-8")
    _git(repo, "commit", "-qam", subject)


def test_no_commit_touching_the_gate_is_clean(tmp_path):
    repo, base = _repo(tmp_path)
    (repo / "other.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feat(T999): a change that is not the gate")
    assert guard.unauthorised_gate_commits(repo, base) == []


@pytest.mark.parametrize("task", guard.AUTHORISED_TASKS)
def test_an_authorised_task_may_change_the_gate(tmp_path, task):
    repo, base = _repo(tmp_path)
    _change(repo, f"feat({task}): the run-record rule this task owns in the gate")
    assert guard.unauthorised_gate_commits(repo, base) == []


def test_the_live_subject_shape_passes(tmp_path):
    """The real T188 subject: it names both IDs, and both are authorised."""
    repo, base = _repo(tmp_path)
    _change(repo, "feat(T188): GREEN — T182's D5 record rule now covers a Decision record's "
                  "verify: line")
    assert guard.unauthorised_gate_commits(repo, base) == []


def test_an_unauthorised_task_is_reported(tmp_path):
    """The case the substring check could not see any more."""
    repo, base = _repo(tmp_path)
    _change(repo, "feat(T999): relax the merge gate a little")
    [problem] = guard.unauthorised_gate_commits(repo, base)
    assert "T999" in problem and "names no task authorised" in problem


def test_merely_naming_an_unauthorised_id_is_not_enough(tmp_path):
    repo, base = _repo(tmp_path)
    _change(repo, "chore: tidy the gate")
    assert len(guard.unauthorised_gate_commits(repo, base)) == 1


def test_one_unauthorised_commit_among_authorised_ones_is_reported(tmp_path):
    repo, base = _repo(tmp_path)
    _change(repo, "feat(T182): the record rule", "# v2\n")
    _change(repo, "fix(T999): quietly widen the gate", "# v3\n")
    _change(repo, "feat(T188): the same rule on a Decision record", "# v4\n")
    problems = guard.unauthorised_gate_commits(repo, base)
    assert len(problems) == 1 and "T999" in problems[0]


def test_an_uncommitted_change_to_the_gate_is_reported(tmp_path):
    repo, base = _repo(tmp_path)
    (repo / GATE).write_text("# edited, not committed\n", encoding="utf-8")
    [problem] = guard.unauthorised_gate_commits(repo, base)
    assert "uncommitted" in problem


def test_a_base_ref_that_does_not_resolve_fails_closed(tmp_path):
    repo, _ = _repo(tmp_path)
    [problem] = guard.unauthorised_gate_commits(repo, "0" * 40)
    assert "git log failed" in problem and "cannot confirm" in problem


def test_the_allowlist_names_the_tasks_that_own_rules_in_the_gate():
    assert guard.AUTHORISED_TASKS == ("T182", "T188", "T190", "T197", "T196", "T210",
                                    "T211")
    text = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "merge_gate_guard.py"), encoding="utf-8").read()
    for task in guard.AUTHORISED_TASKS:
        assert f"#   {task} —" in text, f"{task} is on the allowlist with no rule recorded for it"
