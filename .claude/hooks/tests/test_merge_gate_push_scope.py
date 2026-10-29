#!/usr/bin/env python3
"""T197 — a `git push` of a task's branch is judged by that task's own state.

Before T197 `main()` built `in_progress` and `ready_review` over the **whole board**, so one
task parked in Ready for Review by another live session refused every other session's push.
`pushed_task_ids(command, cwd)` now reads which task the command pushes — from the branch,
never from the board — and `main()` narrows both sections to it. Every doubt returns None,
and None leaves `main()` checking the whole board exactly as before (D2): that direction is
what the negative cases below pin, because this task loosens a fail-closed gate.

Every board, guide and trace here is **constructed**. The git repos are throwaway `git init`
directories with the user's global and system git config switched off, so no test depends on
this machine's branches, worktrees or `~/.gitconfig`.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_push_scope.py -v
Re-capture the AC 3 / AC 12 oracle (only against the PRE-change hook):
    python3 .claude/hooks/tests/test_merge_gate_push_scope.py --capture-oracle
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
ORACLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                           "t197_pre_change_gate_output.txt")

# The global and system git config are not part of any fixture.
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def load_hook_module(path, name):
    """Load a hook without running its bottom-of-file `main()` — same technique as
    `test_merge_gate_evidence.py`, which explains why it is necessary."""
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "merge_gate_t197")

# Spelled in two halves so that this file's own source never reads as a push to the live gate.
PUSH = "git " + "push"


# ---------------------------------------------------------------------------
# Constructed fixtures
# ---------------------------------------------------------------------------

def kanban(in_progress=(), ready=(), todo=(), done=()):
    def rows(ids):
        return "".join(f"- [ ] **{t}** — fixture task {t} | agent | C1 | Risk: Low | P1\n"
                       for t in ids)
    return ("# PROJECT_KANBAN\n\n### Todo\n" + rows(todo)
            + "\n### In Progress\n" + rows(in_progress)
            + "\n### Ready for Review\n" + rows(ready)
            + "\n### Done\n" + rows(done))


# AC 1-11: T900 is verified, T901 (another session's task) has no evidence row.
TWO_IN_REVIEW = kanban(ready=("T900", "T901"))
# AC 12: nothing pending anywhere on the board.
NOTHING_PENDING = kanban(todo=("T902",), done=("T900", "T901"))

GUIDE_VACATED = "# TASK_GUIDE - {tid}\n\n### Evidence\n\n> Moved to `tasks/TASK_REVIEW_{tid}.md`.\n"

REVIEW_VERIFIED = """# TASK_REVIEW - {tid}

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| verify | ☑ pass | verify skill run, feature confirmed working — pass |
"""

COMPANION_FAIL_ROW = "| **Companion score (easy-verifier)** | ☑ fail | overall 62 (< 80) |\n"

PYTEST_TRACE_RECORD = json.dumps({
    "timestamp": "2026-10-28T00:00:00+00:00",
    "tool_name": "Bash",
    "summary": json.dumps({"command": "python3 -m pytest .claude/hooks/tests/ -q"})[:300],
    "is_error": False,
})


def git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          timeout=30, env={**os.environ, **GIT_ENV})
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def make_repo(path, branch):
    """A one-commit git repo with `branch` checked out."""
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q", "-b", branch)
    git(path, "-c", "user.email=t@example.com", "-c", "user.name=t",
        "commit", "-q", "--allow-empty", "-m", "fixture")
    return str(path)


class Gate:
    """A constructed main checkout (board, guides, review files, traces) with the hook
    module's module-level paths pointed at it, and git repos to run commands in."""

    def __init__(self, root, board=TWO_IN_REVIEW, verified=("T900",), extra_review=None):
        self.root = str(root)
        self.tasks = os.path.join(self.root, "main", "tasks")
        self.trace = os.path.join(self.root, "main", "memory", "event-trace")
        os.makedirs(self.tasks)
        os.makedirs(self.trace)
        for tid in ("T900", "T901", "T902", "T9000"):
            self._write(self.tasks, f"TASK_GUIDE_{tid}.md", GUIDE_VACATED.format(tid=tid))
        for tid in verified:
            review = REVIEW_VERIFIED.format(tid=tid) + (extra_review or {}).get(tid, "")
            self._write(self.tasks, f"TASK_REVIEW_{tid}.md", review)
            self._write(self.trace, f"{tid}.jsonl", PYTEST_TRACE_RECORD + "\n")
        self.kanban = os.path.join(self.root, "PROJECT_KANBAN.md")
        self._write(self.root, "PROJECT_KANBAN.md", board)

    @staticmethod
    def _write(directory, name, text):
        with open(os.path.join(directory, name), "w", encoding="utf-8") as f:
            f.write(text)

    def repo(self, name, branch):
        """T210 D4: a pushed task's `verify` row counts only when committed on its branch, so
        the repo commits the fixture's `tasks/` — every verified row is on the branch."""
        path = make_repo(os.path.join(self.root, name), branch)
        shutil.copytree(self.tasks, os.path.join(path, "tasks"))
        git(path, "add", "-A")
        git(path, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "tasks")
        return path


@pytest.fixture
def env(monkeypatch):
    for key, value in GIT_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def gate(tmp_path, monkeypatch, env):
    """`gate(**Gate kwargs)` builds the fixture and patches the module onto it."""
    def build(**kwargs):
        fixture = Gate(tmp_path / "fx", **kwargs)
        monkeypatch.setattr(merge_gate, "KANBAN", fixture.kanban)
        monkeypatch.setattr(merge_gate, "TASKS_DIR", fixture.tasks)
        monkeypatch.setattr(merge_gate, "TRACE_DIR", fixture.trace)
        monkeypatch.setattr(merge_gate, "worktree_tasks_dirs", lambda: [])
        return fixture
    return build


def run_gate(command, cwd=None):
    """Drive the hook's real `main()` over a constructed event: `(stdout, stderr)`.

    `cwd` is the event's own `cwd` field, which is what the harness sends. Omitted, the event
    carries none — the shape every pre-T197 merge-gate test sends."""
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
        return sys.stdout.getvalue(), sys.stderr.getvalue()
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved


def reason(command, cwd=None):
    stdout, _ = run_gate(command, cwd)
    return json.loads(stdout)["reason"] if stdout.strip() else None


def blocks_on_t901_only_as_global(command, cwd):
    """The whole-board answer for the two-in-review fixture: blocked, naming T901."""
    text = reason(command, cwd)
    assert text is not None, f"{command!r} must fall back to the whole board and block"
    assert "T901 (no evidence row)" in text, text
    return text


# ---------------------------------------------------------------------------
# AC 1, AC 2 — the pushed task is judged, the other session's task is not
# ---------------------------------------------------------------------------

def test_ac1_verified_task_branch_push_is_not_blocked_by_another_task(gate):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert run_gate(f"{PUSH} origin feat/t900-x", cwd) == ("", "")


def test_ac2_unverified_task_branch_push_is_blocked_naming_only_that_task(gate):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    text = reason(f"{PUSH} origin feat/t901-x", cwd)
    assert text is not None
    assert "T901" in text
    assert "T900" not in text


# ---------------------------------------------------------------------------
# AC 4 — two IDs in one branch name: the whole board
# ---------------------------------------------------------------------------

def test_ac4_branch_naming_two_ids_checks_the_whole_board(gate):
    fx = gate()
    cwd = fx.repo("wt", "plan/t900-t901-x")
    blocks_on_t901_only_as_global(f"{PUSH} origin plan/t900-t901-x", cwd)
    assert merge_gate.pushed_task_ids(f"{PUSH} origin plan/t900-t901-x", cwd) is None


# ---------------------------------------------------------------------------
# AC 5, AC 6 — the pushed task's own state still binds (D3)
# ---------------------------------------------------------------------------

def test_ac5_scoped_push_of_a_task_still_in_progress_is_blocked(gate):
    fx = gate(board=kanban(in_progress=("T900",), ready=("T901",)))
    cwd = fx.repo("wt-t900", "feat/t900-x")
    text = reason(f"{PUSH} origin feat/t900-x", cwd)
    assert text is not None and "Tasks still In Progress: T900" in text
    assert "T901" not in text


def test_ac5_another_tasks_in_progress_row_does_not_block(gate):
    fx = gate(board=kanban(in_progress=("T901",), ready=("T900",)))
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert run_gate(f"{PUSH} origin feat/t900-x", cwd) == ("", "")


def test_ac6_scoped_push_with_its_own_companion_row_failed_is_blocked(gate):
    fx = gate(extra_review={"T900": COMPANION_FAIL_ROW})
    cwd = fx.repo("wt-t900", "feat/t900-x")
    text = reason(f"{PUSH} origin feat/t900-x", cwd)
    assert text is not None
    assert "T900 (Companion score)" in text
    assert "T901" not in text


# ---------------------------------------------------------------------------
# AC 7 — no refspec / HEAD: the current branch of the directory the command runs in
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("args", ["", " origin", " origin HEAD", " -u origin HEAD"],
                         ids=["bare", "remote-only", "head", "u-head"])
def test_ac7_implicit_push_resolves_from_the_cwd_branch(gate, args):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(PUSH + args, cwd) == "T900"
    assert run_gate(PUSH + args, cwd) == ("", "")


def test_ac7_cwd_that_is_not_a_git_repo_checks_the_whole_board(gate, tmp_path):
    gate()
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    blocks_on_t901_only_as_global(PUSH, str(plain))


def test_ac7_detached_head_checks_the_whole_board(gate):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    git(cwd, "checkout", "-q", "--detach")
    blocks_on_t901_only_as_global(f"{PUSH} origin HEAD", cwd)


def test_ac7_event_without_cwd_checks_the_whole_board(gate):
    gate()
    blocks_on_t901_only_as_global(f"{PUSH} origin feat/t900-x", None)


# ---------------------------------------------------------------------------
# AC 8 — `git merge` (and every non-push trigger) is never scoped (D4)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "git merge feat/t900-x",
    "git rebase feat/t900-x",
    f"{PUSH} origin feat/t900-x && git merge main",
    f"git merge main && {PUSH} origin feat/t900-x",
], ids=["merge", "rebase", "push-then-merge", "merge-then-push"])
def test_ac8_merge_checks_the_whole_board(gate, command):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    blocks_on_t901_only_as_global(command, cwd)


# ---------------------------------------------------------------------------
# AC 9 — --all, --mirror, a tag: the whole board
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("args", [
    " --all", " origin --all", " --mirror origin", " origin v1.0", " origin --tags",
    " origin refs/tags/v1.0", " --follow-tags origin feat/t900-x",
    " --delete origin feat/t900-x", " origin :feat/t900-x",
], ids=["all", "remote-all", "mirror", "tag", "tags", "tag-ref", "follow-tags", "delete",
        "colon-delete"])
def test_ac9_all_mirror_tag_and_delete_check_the_whole_board(gate, args):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    blocks_on_t901_only_as_global(PUSH + args, cwd)


# ---------------------------------------------------------------------------
# AC 10 — a whole-ID match only, never a substring
# ---------------------------------------------------------------------------

def test_ac10_longer_id_is_not_read_as_a_shorter_one(gate):
    fx = gate(board=kanban(ready=("T900", "T9000")))
    cwd = fx.repo("wt", "feat/fix-t9000-typo")
    assert merge_gate.pushed_task_ids(f"{PUSH} origin feat/fix-t9000-typo", cwd) == "T9000"
    text = reason(f"{PUSH} origin feat/fix-t9000-typo", cwd)
    assert text is not None and "T9000 (no evidence row)" in text


@pytest.mark.parametrize("branch", ["feat/cat900", "feat/t900x", "feat/t900_x", "feat/xt900-y"])
def test_ac10_id_inside_a_longer_word_does_not_resolve(gate, branch):
    fx = gate()
    cwd = fx.repo("wt", branch)
    assert merge_gate.pushed_task_ids(f"{PUSH} origin {branch}", cwd) is None
    blocks_on_t901_only_as_global(f"{PUSH} origin {branch}", cwd)


# ---------------------------------------------------------------------------
# AC 11 — prose and heredocs scope nothing
# ---------------------------------------------------------------------------

def test_ac11_heredoc_naming_a_task_branch_does_not_scope_a_real_push(gate):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    command = f"cat > notes.md <<'EOF'\n{PUSH} origin feat/t900-x\nEOF\n{PUSH} origin main"
    assert merge_gate.pushed_task_ids(command, cwd) is None
    blocks_on_t901_only_as_global(command, cwd)


def test_ac11_heredoc_alone_scopes_nothing_and_is_not_gated(gate):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    command = f"cat > notes.md <<'EOF'\n{PUSH} origin feat/t900-x\nEOF\n"
    assert merge_gate.pushed_task_ids(command, cwd) is None
    assert run_gate(command, cwd) == ("", "")


@pytest.mark.parametrize("command", [
    f'echo "{PUSH} origin feat/t900-x" && {PUSH} origin main',
    f"bash -c '{PUSH} origin main' && {PUSH} origin feat/t900-x",
    f"{PUSH} origin feat/t900-x #note\n{PUSH} origin main",
    f"{PUSH} origin feat/t900-x; {PUSH} origin main",
    f"{PUSH} origin $(git rev-parse --abbrev-ref HEAD)",
    f"{PUSH} origin `echo main`",
    f"GIT_DIR=/elsewhere/.git {PUSH} origin feat/t900-x",
    f"sudo {PUSH} origin feat/t900-x",
], ids=["echo-prose", "bash-c", "comment-hides-newline", "second-push-to-main",
        "subshell", "backtick", "env-prefix", "wrapper"])
def test_ac11_anything_the_parser_cannot_read_checks_the_whole_board(gate, command):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(command, cwd) is None
    blocks_on_t901_only_as_global(command, cwd)


# ---------------------------------------------------------------------------
# Edge case checklist
# ---------------------------------------------------------------------------

def test_edge_cd_target_decides_head_not_the_session_cwd(gate):
    """The worst failure here: the session cwd is the main checkout on `main`, the command
    pushes from a worktree. HEAD must come from the `cd` target."""
    fx = gate()
    main_checkout = fx.repo("main-checkout", "main")
    wt = fx.repo("wt-t900", "feat/t900-x")
    command = f"cd {wt} && {PUSH} origin HEAD"
    assert merge_gate.pushed_task_ids(command, main_checkout) == "T900"
    assert run_gate(command, main_checkout) == ("", "")
    relative = f"cd ../wt-t900 && {PUSH} origin HEAD"
    assert merge_gate.pushed_task_ids(relative, main_checkout) == "T900"


def test_edge_cd_into_main_from_a_task_worktree_is_global(gate):
    fx = gate()
    main_checkout = fx.repo("main-checkout", "main")
    wt = fx.repo("wt-t900", "feat/t900-x")
    blocks_on_t901_only_as_global(f"cd {main_checkout} && {PUSH} origin HEAD", wt)


@pytest.mark.parametrize("command", [
    "cd {wt} || {push} origin HEAD",
    "cd {wt}; {push} origin HEAD",
    "cd {wt} | {push} origin HEAD",
    "cd {wt} & {push} origin HEAD",
    "true || cd {wt} && {push} origin HEAD",
    "cd ~/x && {push} origin HEAD",
    "cd && {push} origin HEAD",
    "cd {wt} extra && {push} origin HEAD",
    "pushd {wt} && {push} origin HEAD",
], ids=["or", "semicolon", "pipe", "background", "after-or", "tilde", "bare-cd", "two-args",
        "pushd"])
def test_edge_a_directory_change_the_parser_cannot_prove_is_global(gate, command):
    """The session sits in the main checkout on `main`; the `cd` names the T900 worktree.
    In each of these bash may run the push in the main checkout, so it must not scope."""
    fx = gate()
    main_checkout = fx.repo("main-checkout", "main")
    wt = fx.repo("wt-t900", "feat/t900-x")
    command = command.format(wt=wt, push=PUSH)
    assert merge_gate.pushed_task_ids(command, main_checkout) is None
    blocks_on_t901_only_as_global(command, main_checkout)


def test_d4_merge_rebase_and_branch_moves_are_never_read_only_subcommands():
    """D4 is enforced by the allowlist: a `git merge`/`rebase` segment is unresolved."""
    for sub in ("merge", "rebase", "pull", "checkout", "switch", "reset", "worktree", "branch",
                "fetch"):
        assert sub not in merge_gate.SAFE_GIT_SUBCOMMANDS, sub


@pytest.mark.parametrize("refspec", [
    "HEAD:refs/heads/main", "HEAD:main", "feat/t900-x:main", "feat/t900-x:release/1.0",
    "feat/t900-x:plan/t900-t901", "HEAD:feat/t901-x",
], ids=["head-to-refs-main", "head-to-main", "branch-to-main", "to-release", "to-integration",
        "to-other-task"])
def test_edge_destination_that_is_not_the_same_task_is_global(gate, refspec):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    blocks_on_t901_only_as_global(f"{PUSH} origin {refspec}", cwd)


@pytest.mark.parametrize("args", [
    "-u origin feat/t900-x", "--force-with-lease origin feat/t900-x",
    "origin feat/t900-x --force", "--set-upstream origin feat/t900-x",
    "--force-with-lease=feat/t900-x origin feat/t900-x", "origin +feat/t900-x",
    "origin feat/t900-x:feat/t900-x", "origin HEAD:refs/heads/feat/t900-x",
    "origin refs/heads/feat/t900-x",
], ids=["u", "lease", "force-after", "set-upstream", "lease-ref", "plus", "same-dst",
        "head-to-same", "full-ref"])
def test_edge_flags_and_same_task_destinations_stay_scoped(gate, args):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(f"{PUSH} {args}", cwd) == "T900"
    assert run_gate(f"{PUSH} {args}", cwd) == ("", "")


@pytest.mark.parametrize("args", ["-o ci.skip origin feat/t900-x", "-uf origin feat/t900-x",
                                  "--repo=origin feat/t900-x", "-- origin feat/t900-x"],
                         ids=["push-option", "combined-short", "repo", "double-dash"])
def test_edge_an_unknown_option_is_global(gate, args):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(f"{PUSH} {args}", cwd) is None


@pytest.mark.parametrize("command", [
    "git add -A && git commit -m 'T900: a -> b; c' && {push} origin feat/t900-x",
    "git status --short && {push} -u origin feat/t900-x 2>&1 | tail -5",
    "{push} origin feat/t900-x >/dev/null 2>&1",
    "{push} origin feat/t900-x && {push} origin HEAD",
], ids=["commit-chain", "pipe-to-tail", "redirect", "two-pushes-same-task"])
def test_edge_a_chain_that_pushes_one_task_stays_scoped(gate, command):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    command = command.format(push=PUSH)
    assert merge_gate.pushed_task_ids(command, cwd) == "T900"
    assert run_gate(command, cwd) == ("", "")


@pytest.mark.parametrize("command", [
    "git checkout main && {push} origin HEAD",
    "git switch main && {push}",
    "{push} origin feat/t900-x && {push} origin feat/t901-x",
    "{push} origin feat/t900-x | sh",
    "python3 -m pytest -q && {push} origin feat/t900-x",
    'git commit -m "x $(git checkout main)" && {push} origin HEAD',
    'git commit -m "x `git checkout main`" && {push} origin HEAD',
], ids=["checkout", "switch", "two-tasks", "pipe-to-shell", "unknown-command",
        "substitution-in-quotes", "backtick-in-quotes"])
def test_edge_a_chain_with_any_unresolved_part_is_global(gate, command):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    command = command.format(push=PUSH)
    assert merge_gate.pushed_task_ids(command, cwd) is None
    blocks_on_t901_only_as_global(command, cwd)


@pytest.mark.parametrize("branch", ["release/t900-hotfix", "integration/t900", "Release/T900"])
def test_edge_release_and_integration_branches_stay_global_even_with_one_id(gate, branch):
    fx = gate()
    cwd = fx.repo("wt", branch)
    for command in (f"{PUSH} origin {branch}", f"{PUSH} origin HEAD"):
        assert merge_gate.pushed_task_ids(command, cwd) is None
        blocks_on_t901_only_as_global(command, cwd)


def test_edge_id_not_on_the_board_is_global(gate):
    fx = gate()
    cwd = fx.repo("wt", "feat/t999-x")
    blocks_on_t901_only_as_global(f"{PUSH} origin feat/t999-x", cwd)


def test_edge_mixed_case_branch_resolves(gate):
    fx = gate()
    cwd = fx.repo("wt", "Feat/T900-X")
    assert merge_gate.pushed_task_ids(f"{PUSH} origin Feat/T900-X", cwd) == "T900"
    assert run_gate(f"{PUSH} origin Feat/T900-X", cwd) == ("", "")


@pytest.mark.parametrize("board", [
    kanban(ready=("T901",), todo=("T900",)),
    kanban(ready=("T901",), done=("T900",)),
    kanban(ready=("T901",)) + "\n### Backlog\n- [ ] **T900** — parked | agent | C1 | P2\n",
], ids=["todo", "done", "outside-the-lanes"])
def test_d3_push_of_a_task_not_in_the_two_lanes_checks_the_whole_board(gate, board):
    """Stage 4 security-review finding 4 (D3 changed by the Supervisor after a 3-Advocate
    Debate): a branch named after a Todo, Done or lane-less task used to empty both lists,
    so T901's work pushed as `feat/t900-x` met no check at all. It now narrows nothing."""
    fx = gate(board=board)
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(f"{PUSH} origin feat/t900-x", cwd) == "T900"
    blocks_on_t901_only_as_global(f"{PUSH} origin feat/t900-x", cwd)


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("git", 5),
                                     FileNotFoundError("git")], ids=["timeout", "no-git"])
def test_edge_git_failure_is_global(gate, monkeypatch, failure):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")

    def boom(*args, **kwargs):
        raise failure

    monkeypatch.setattr(merge_gate.subprocess, "run", boom)
    for command in (PUSH, f"{PUSH} origin feat/t900-x"):
        assert merge_gate.pushed_task_ids(command, cwd) is None
        blocks_on_t901_only_as_global(command, cwd)


def test_edge_every_git_call_has_the_five_second_timeout(gate, monkeypatch):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    seen = []
    real = subprocess.run

    def spy(*args, **kwargs):
        seen.append(kwargs.get("timeout"))
        return real(*args, **kwargs)

    monkeypatch.setattr(merge_gate.subprocess, "run", spy)
    assert merge_gate.pushed_task_ids(f"{PUSH} origin HEAD", cwd) == "T900"
    assert seen and all(t == 5 for t in seen), seen


@pytest.mark.parametrize("key,value", [
    ("remote.origin.push", "refs/heads/*:refs/heads/main"),
    ("remote.origin.mirror", "true"),
    ("push.default", "matching"),
    ("push.default", "upstream"),
], ids=["remote-push", "mirror", "matching", "upstream"])
def test_edge_push_config_that_can_move_the_destination_is_global(gate, key, value):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    git(cwd, "config", key, value)
    for command in (PUSH, f"{PUSH} origin feat/t900-x"):
        assert merge_gate.pushed_task_ids(command, cwd) is None
        blocks_on_t901_only_as_global(command, cwd)


def test_edge_git_dash_c_directory_is_read(gate):
    """`git -C <dir>` names the directory (D1.2). The current BLOCKED_PATTERNS do not see
    `git -C <dir> push` at all (a pre-existing gap, out of this task's scope), so this is
    checked on the resolver directly, and through the gate behind a second, plain push."""
    fx = gate()
    main_checkout = fx.repo("main-checkout", "main")
    wt = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(f"git -C {wt} push origin HEAD", main_checkout) == "T900"
    assert merge_gate.pushed_task_ids(f"git -C {main_checkout} push origin HEAD", wt) is None
    assert merge_gate.pushed_task_ids("git -c push.default=matching push", wt) is None


# ---------------------------------------------------------------------------
# Stage 4 security-review findings 1-3 — each command below resolved to T900 before the fix
# (finding 4 is `test_d3_...` and the online test below)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("args", [
    " {origin,--all}", " {origin,--mirror}", " {origin,--tags}",
    " ../elsewhere feat/t900-x", " git@host:o/r.git feat/t900-x",
], ids=["brace-all", "brace-mirror", "brace-tags", "path-remote", "url-remote"])
def test_finding1_the_remote_must_be_a_plain_name(gate, args):
    """Bash expands `{origin,--all}` to `origin --all`; the remote slot was never checked."""
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert merge_gate.pushed_task_ids(PUSH + args, cwd) is None
    blocks_on_t901_only_as_global(PUSH + args, cwd)


@pytest.mark.parametrize("command", [
    "cd {wt} && git status & {push} origin",
    "{push} origin feat/t900-x &",
    "git status & {push} origin feat/t900-x",
], ids=["backgrounded-cd", "backgrounded-push", "background-before"])
def test_finding2_a_background_separator_anywhere_is_global(gate, command):
    """`cd X && git status & git push origin` backgrounds `(cd X && git status)`; the push
    runs from the original cwd, which here is the main checkout on `main`."""
    fx = gate()
    main_checkout = fx.repo("main-checkout", "main")
    wt = fx.repo("wt-t900", "feat/t900-x")
    command = command.format(wt=wt, push=PUSH)
    assert merge_gate.pushed_task_ids(command, main_checkout) is None
    blocks_on_t901_only_as_global(command, main_checkout)


@pytest.mark.parametrize("command", [
    "git fetch --upload-pack='git merge feat/t901-y' . ; {push} origin feat/t900-x",
    "git fetch && {push} origin feat/t900-x",
    "git diff --output=.git/HEAD && {push} origin HEAD",
    "git log --output=/tmp/t197-x && {push} origin feat/t900-x",
    "git add --chmod=+x f && {push} origin feat/t900-x",
    "git commit -m -x && {push} origin feat/t900-x",
    "git commit -m && {push} origin feat/t900-x",
    "git status --ignored && {push} origin feat/t900-x",
    "git diff -- f && {push} origin feat/t900-x",
    "git diff {{--stat,--output=.git/HEAD}} && {push} origin HEAD",
    "git log * && {push} origin HEAD",
    "git add 'f{{a,b}}' && {push} origin HEAD",
], ids=["fetch-upload-pack", "fetch-dropped", "diff-output", "log-output", "add-chmod",
        "message-is-an-option", "message-missing", "status-unknown", "double-dash",
        "brace-hides-option", "glob-can-expand-to-option", "brace-in-path"])
def test_finding3_read_only_git_takes_only_allowlisted_options(gate, command):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    command = command.format(push=PUSH)
    assert merge_gate.pushed_task_ids(command, cwd) is None
    blocks_on_t901_only_as_global(command, cwd)


@pytest.mark.parametrize("command", [
    "git add -A && git commit -am 'why? [T900] *wip*' && {push} origin feat/t900-x",
    "git add -u src/a.py && git commit -q -s --no-verify -m msg && {push} origin HEAD",
    "git commit --amend --no-edit && {push} --force-with-lease origin feat/t900-x",
    "git status -s -b && git log --oneline -5 && {push} origin feat/t900-x",
    "git log -n 3 --stat --graph && {push} origin feat/t900-x",
    "git diff --stat --cached && git diff --name-only HEAD && {push} origin feat/t900-x",
    "git show --stat HEAD && {push} origin feat/t900-x",
], ids=["commit-am-glob-in-message", "add-u-commit-flags", "amend", "status-log",
        "log-n", "diff-flags", "show"])
def test_finding3_the_allowlisted_options_stay_scoped(gate, command):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    command = command.format(push=PUSH)
    assert merge_gate.pushed_task_ids(command, cwd) == "T900"
    assert run_gate(command, cwd) == ("", "")


# ---------------------------------------------------------------------------
# board mode `online`: the filters run first, scoping narrows their result (T157/T161)
# ---------------------------------------------------------------------------

HOOKS = Path(HOOKS_DIR)
REPO_ROOT = HOOKS.parent.parent


def online_project(tmp_path, tasks, branch):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (project / "scripts").mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "board_sync.py", project / "scripts" / "board_sync.py")
    (project / "tasks").mkdir()
    (project / "board.json").write_text(json.dumps(tasks))
    (project / ".claude" / "board.json").write_text(json.dumps(
        {"board": "fake", "fake_board": "board.json", "id_pattern": r"ENG-\d+", "me": "alice"}))
    make_repo(project, branch)
    return project


def online_gate(project, command):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "LINEAR_API_KEY")}
    env.update(GIT_ENV, CLAUDE_PROJECT_DIR=str(project))
    event = {"tool_name": "Bash", "cwd": str(project), "tool_input": {"command": command}}
    return subprocess.run([sys.executable, str(project / ".claude" / "hooks" / os.path.basename(HOOK_PATH))],
                          input=json.dumps(event), capture_output=True, text=True,
                          cwd=project, env=env, timeout=60)


def online_task(task_id, status, assignee):
    return {"id": task_id, "title": "t", "status": status, "assignee": assignee,
            "description": f"# guide {task_id}\n"}


def test_online_pull_and_filters_run_then_scoping_narrows_their_result(tmp_path):
    tasks = [online_task("ENG-170", "In Progress", "alice"),
             online_task("ENG-171", "In Progress", "bob"),
             online_task("ENG-172", "In Progress", "alice")]
    project = online_project(tmp_path, tasks, "feat/eng-172-x")
    result = online_gate(project, f"{PUSH} origin feat/eng-172-x")
    assert "**ENG-171**" in (project / "PROJECT_KANBAN.md").read_text(), "gate did not pull"
    text = json.loads(result.stdout)["reason"]
    assert "Tasks still In Progress: ENG-172\n" in text
    assert "ENG-170" not in text and "ENG-171" not in text


def test_online_a_branch_named_after_a_task_the_filter_drops_checks_the_whole_board(tmp_path):
    """Finding 4 in board mode `online`: bob's ENG-171 is in a lane, but the T157 filter
    does not check it for alice. Narrowing to it would empty both lists, so alice's own
    unverified ENG-170 could leave on a branch named `feat/eng-171-x`. It narrows nothing."""
    tasks = [online_task("ENG-170", "In Progress", "alice"),
             online_task("ENG-171", "In Progress", "bob")]
    project = online_project(tmp_path, tasks, "feat/eng-171-x")
    result = online_gate(project, f"{PUSH} origin feat/eng-171-x")
    text = json.loads(result.stdout)["reason"]
    assert "Tasks still In Progress: ENG-170\n" in text
    assert "ENG-171" not in text


# ---------------------------------------------------------------------------
# AC 3 / AC 12 — the pre-change oracle, captured BEFORE the hook edit
# ---------------------------------------------------------------------------

ORACLE_SCENARIOS = (
    # AC 3: a push of main is today's whole-board answer, byte for byte.
    ("AC3 two in review, push main", TWO_IN_REVIEW, f"{PUSH} origin main"),
    ("AC3 two in review, push main, -u", TWO_IN_REVIEW, f"{PUSH} -u origin main"),
    ("AC8 two in review, merge task branch", TWO_IN_REVIEW, "git merge feat/t900-x"),
    # AC 12: nothing In Progress, nothing in Ready for Review.
    ("AC12 nothing pending, push task branch", NOTHING_PENDING, f"{PUSH} origin feat/t900-x"),
    ("AC12 nothing pending, push no refspec", NOTHING_PENDING, PUSH),
    ("AC12 nothing pending, push main", NOTHING_PENDING, f"{PUSH} origin main"),
    ("AC12 nothing pending, merge", NOTHING_PENDING, "git merge feat/t900-x"),
    ("AC12 nothing pending, rebase", NOTHING_PENDING, "git rebase main"),
    ("AC12 nothing pending, not git", NOTHING_PENDING, "ls -la"),
)


def capture_oracle_output():
    """The gate's full output across every oracle scenario, as one deterministic string.
    Each runs with a `cwd` on branch `feat/t900-x`. Against the pre-change hook it is the
    oracle; against the post-change hook it must be identical."""
    saved = (merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR,
             merge_gate.worktree_tasks_dirs, {k: os.environ.get(k) for k in GIT_ENV})
    os.environ.update(GIT_ENV)
    chunks = []
    try:
        for name, board, command in ORACLE_SCENARIOS:
            root = tempfile.mkdtemp(prefix="t197_oracle_")
            try:
                fx = Gate(root, board=board)
                cwd = fx.repo("wt-t900", "feat/t900-x")
                merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR = (
                    fx.kanban, fx.tasks, fx.trace)
                merge_gate.worktree_tasks_dirs = lambda: []
                stdout, stderr = run_gate(command, cwd)
            finally:
                shutil.rmtree(root, ignore_errors=True)
            chunks.append(f"=== {name} ===\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n")
    finally:
        (merge_gate.KANBAN, merge_gate.TASKS_DIR, merge_gate.TRACE_DIR,
         merge_gate.worktree_tasks_dirs, env) = saved
        for key, value in env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return "".join(chunks)


def test_the_oracle_is_not_vacuous():
    oracle = open(ORACLE_PATH, encoding="utf-8").read()
    assert oracle.count("=== ") == len(ORACLE_SCENARIOS)
    assert oracle.count("T901 (no evidence row)") == 3  # the three AC 3 / AC 8 scenarios


def test_ac3_ac12_output_is_byte_identical_to_the_pre_change_gate():
    assert capture_oracle_output() == open(ORACLE_PATH, encoding="utf-8").read()


# ---------------------------------------------------------------------------
# Anti-vacuity: with the resolver stubbed to "unresolved", AC 1 blocks again
# ---------------------------------------------------------------------------

def test_ac1_depends_on_the_resolver(gate, monkeypatch):
    fx = gate()
    cwd = fx.repo("wt-t900", "feat/t900-x")
    assert run_gate(f"{PUSH} origin feat/t900-x", cwd) == ("", "")
    monkeypatch.setattr(merge_gate, "pushed_task_ids", lambda command, cwd: None)
    blocks_on_t901_only_as_global(f"{PUSH} origin feat/t900-x", cwd)


if __name__ == "__main__":
    if "--capture-oracle" in sys.argv:
        with open(ORACLE_PATH, "w", encoding="utf-8") as f:
            f.write(capture_oracle_output())
        print(f"oracle written: {ORACLE_PATH}")
    else:
        print(__doc__)
