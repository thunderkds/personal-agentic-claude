#!/usr/bin/env python3
"""T250 — the gates judge only the work this session did, and a blocked auto verify run falls back
to the user's own `/verify <ID>`, proven from the session transcript.

  AC 1, 2 — a minimal-track `- verify: ☑ pass — /verify by the user, session <sid>, commit <sha>`
            line passes `has_filled_verify_row` only with a human `/verify <ID>` entry in that
            session's transcript, dated between the commit and the line's own commit, and the same
            code as the head. Everything else fails closed.
  AC 3    — `stop_auto_verify.py --start` starts nothing for the user line and never edits it.
  AC 4    — `lib/session_work.py`: "did this session work on task X", from its transcript.
  AC 5    — merge gate: an In Progress task blocks only when this session worked on it, the merge
            brings in its branch, or ownership cannot be decided.
  AC 7    — Stop check: a task whose files changed in an `[auto]` window is checked only when this
            session worked on it.
  AC 8    — each new path fails closed.

Fixture transcripts copy the shape of real Claude Code entries (`type`, `timestamp`, `origin.kind`,
`message.content`, `tool_use` blocks, `cwd`); no line of a real transcript is committed.

Run with: python3 -m pytest .claude/hooks/tests/test_t250_session_ownership.py -q
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parent.parent
ROOT = HOOKS.parent.parent
sys.path.insert(0, str(HOOKS / "lib"))

import session_work as sw  # noqa: E402

SID = "aaaaaaaa-1111-2222-3333-444444444444"
OTHER_SID = "bbbbbbbb-1111-2222-3333-444444444444"


# ── fixture transcript entries (real shapes, invented content) ───────────────────────────────
def human(text, ts="2026-11-04T06:05:12.960Z", **extra):
    entry = {"type": "user", "message": {"role": "user", "content": text}, "timestamp": ts,
             "origin": {"kind": "human"}, "isSidechain": False, "sessionId": SID,
             "cwd": "/repo"}
    entry.update(extra)
    return entry


def slash_verify(args, ts="2026-11-04T06:05:12.960Z", **extra):
    return human("<command-message>verify</command-message>\n<command-name>/verify</command-name>\n"
                 f"<command-args>{args}</command-args>", ts, **extra)


def tool_use(name, tool_input, ts="2026-11-04T06:06:14.144Z", cwd="/repo"):
    return {"type": "assistant", "timestamp": ts, "cwd": cwd, "sessionId": SID,
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "toolu_x", "name": name, "input": tool_input}]}}


def write_transcript(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    return path


# ── AC 1/2 — the user's `/verify <ID>` entry ─────────────────────────────────────────────────
def test_ac1_a_human_slash_verify_for_the_task_is_found(tmp_path):
    t = write_transcript(tmp_path / f"{SID}.jsonl", [slash_verify("T900")])
    assert sw.verify_typed(str(t), "T900") is True


def test_ac1_extra_words_after_the_id_still_name_the_task(tmp_path):
    t = write_transcript(tmp_path / f"{SID}.jsonl", [slash_verify("T900 please")])
    assert sw.verify_typed(str(t), "T900") is True


@pytest.mark.parametrize("entry", [
    slash_verify("T901"),                                   # another task
    slash_verify("T9000"),                                  # a longer ID
    slash_verify(""),                                       # no args
    slash_verify("T900", origin={"kind": "task-notification", "producer": "session-task"}),
    slash_verify("T900", isMeta=True),                      # a skill body / reminder
    slash_verify("T900", origin=None),                      # no origin: not proven human
    slash_verify("T900", isSidechain=True),                 # a sub-agent's prompt
    {"type": "user", "timestamp": "2026-11-04T06:05:12.960Z", "origin": {"kind": "human"},
     "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_x",
                 "content": "<command-name>/verify</command-name><command-args>T900</command-args>"}]}},
    {"type": "assistant", "timestamp": "2026-11-04T06:05:12.960Z", "message": {"role": "assistant",
     "content": "<command-name>/verify</command-name><command-args>T900</command-args>"}},
], ids=["other-task", "longer-id", "no-args", "task-notification", "isMeta", "no-origin",
        "sidechain", "tool-result", "assistant"])
def test_ac2_no_matching_human_verify_is_not_a_pass(tmp_path, entry):
    t = write_transcript(tmp_path / f"{SID}.jsonl", [entry])
    assert sw.verify_typed(str(t), "T900") is False


def test_ac2_a_missing_or_unreadable_transcript_is_not_a_pass(tmp_path):
    assert sw.verify_typed(str(tmp_path / "nope.jsonl"), "T900") is False
    assert sw.verify_typed(None, "T900") is False
    bad = tmp_path / "bad.jsonl"
    bad.write_bytes(b"\xff\xfe not json\n")
    assert sw.verify_typed(str(bad), "T900") is False


def test_ac1_the_entry_must_fall_inside_the_time_bounds(tmp_path):
    t = write_transcript(tmp_path / f"{SID}.jsonl", [slash_verify("T900", "2026-11-04T06:05:12Z")])
    at = sw.parse_ts
    assert sw.verify_typed(str(t), "T900", after=at("2026-11-04T06:00:00Z"),
                           before=at("2026-11-04T07:00:00Z")) is True
    assert sw.verify_typed(str(t), "T900", after=at("2026-11-04T06:10:00Z")) is False
    assert sw.verify_typed(str(t), "T900", before=at("2026-11-04T06:00:00Z")) is False


# ── AC 4 — did this session work on task X ───────────────────────────────────────────────────
WT = "/work/wt-t900"   # the task's worktree, as `git worktree list` names it
MAIN = "/work/repo"    # the main checkout: the session's cwd


def worked(tmp_path, entries, task="T900", worktrees=(WT,), sub_entries=None):
    t = write_transcript(tmp_path / f"{SID}.jsonl", entries)
    if sub_entries is not None:
        write_transcript(tmp_path / SID / "subagents" / "agent-a1.jsonl", sub_entries)
    calls = sw.load_work(str(t))
    assert calls is not None
    return sw.worked_on(calls, task, list(worktrees))


def bash(command, cwd=MAIN):
    return tool_use("Bash", {"command": command, "description": "x"}, cwd=cwd)


@pytest.mark.parametrize("entry", [
    tool_use("Edit", {"file_path": f"{MAIN}/tasks/TASK_GUIDE_T900.md", "old_string": "a",
                      "new_string": "b"}),
    tool_use("Write", {"file_path": f"{WT}/src/app.py", "content": "x"}),
    tool_use("Write", {"file_path": f"{MAIN}/tasks/TASK_REVIEW_T900.md", "content": "x"}),
    tool_use("NotebookEdit", {"notebook_path": f"{WT}/n.ipynb", "new_source": "x"}),
    bash(f"cd {WT} && git commit -qm 'T900 work'"),
    bash("cd ../wt-t900 && python3 -m pytest -q"),
    bash("cat > tasks/TASK_REVIEW_T900.md <<'EOF'\nhello\nEOF"),
    bash("sed -i 's/a/b/' tasks/TASK_GUIDE_T900.md"),
    bash("sort -o tasks/TASK_GUIDE_T900.md tasks/TASK_GUIDE_T900.md"),
    bash("echo done >> ../wt-t900/notes.txt"),
    bash("python3 -m pytest -q", cwd=f"{WT}/sub"),
    bash("git -C ../wt-t900 commit -qm x"),
    bash("bash -c 'echo x > tasks/TASK_REVIEW_T900.md'"),
    bash("eval \"rm ../wt-t900/old.txt\""),
    tool_use("Agent", {"description": "T900 implement", "subagent_type": "backend-developer",
                       "prompt": "Task ID: T900\nGuide: tasks/TASK_GUIDE_T900.md\n"}),
], ids=["edit-guide", "write-in-worktree", "write-review", "notebook", "cd-worktree-commit",
        "cd-relative-pytest", "heredoc-into-review", "sed-in-place", "sort-output", "append-into-worktree",
        "cwd-in-worktree", "git-C-commit", "bash-c-string", "eval-string", "agent-spawn"])
def test_ac4_a_non_read_call_on_the_task_is_work(tmp_path, entry):
    assert worked(tmp_path, [entry]) is True


@pytest.mark.parametrize("entry", [
    tool_use("Read", {"file_path": f"{MAIN}/tasks/TASK_GUIDE_T900.md"}),
    tool_use("Grep", {"pattern": "x", "path": f"{WT}/tasks"}),
    tool_use("Glob", {"pattern": "tasks/*T900*"}),
    bash("grep -n 'Risk' tasks/TASK_GUIDE_T900.md | head -3"),
    bash("cat tasks/TASK_REVIEW_T900.md 2>/dev/null"),
    bash("sed -n '1,40p' ../wt-t900/tasks/TASK_GUIDE_T900.md"),
    bash("git -C ../wt-t900 log -1 --format='%h %s'; git -C ../wt-t900 status --short | head -3"),
    bash(f"cd {WT} && git log --oneline -3"),
    bash(f"cd {WT} && grep -n x tasks/MINIMAL_LOG.md | cut -c1-80 | sort | tr a b | nl"),
    bash("grep -n '\\*\\*T900\\*\\*' PROJECT_KANBAN.md"),  # names the ID, not its files
    bash("python3 - <<'EOF'\np='tasks/TASK_REVIEW_T901.md'\n# quotes tasks/TASK_REVIEW_T900.md\nEOF"),
    bash("cat tasks/TASK_REVIEW_T9000.md > /tmp/x"),
    # a real shape: a scratch dir held in a variable — not known to be the task's worktree
    bash("S=/tmp/scratch/blind; cd $S; mkdir -p judge key; cp build-a/x judge/"),
    # code or a message passed as one quoted argument is not a file argument
    bash("python3 -c \"print(list(shlex.split('cat a > tasks/X_T900.md')))\""),
    bash("git commit -qm 'record: T900 is in tasks/TASK_REVIEW_T900.md'"),
    tool_use("Edit", {"file_path": f"{MAIN}/tasks/TASK_GUIDE_T9000.md", "old_string": "a",
                      "new_string": "b"}),
    tool_use("Write", {"file_path": f"{MAIN}/tasks/TASK_GUIDE_T901.md",
                       "content": "T900's tasks/TASK_REVIEW_T900.md is another session's"}),
    tool_use("Agent", {"description": "T901 implement", "subagent_type": "backend-developer",
                       "prompt": "Task ID: T901\nT900 is another session's task; only read "
                                 "tasks/TASK_GUIDE_T900.md.\n"}),
], ids=["Read", "Grep", "Glob", "bash-grep", "bash-cat", "bash-sed-print", "git-C-log-status",
        "cd-worktree-log", "cd-worktree-pipe-readers", "bash-names-id-only", "heredoc-body-mentions", "longer-id-path", "cd-variable",
        "python-c-code", "commit-message",
        "edit-longer-id", "write-other-task-mentions", "agent-for-other-task"])
def test_ac4_a_read_or_unrelated_call_is_not_work(tmp_path, entry):
    assert worked(tmp_path, [entry]) is False


SPACED_WT = "/work/my wt-t900"   # a worktree under a folder whose name holds a space


@pytest.mark.parametrize("entry", [
    tool_use("Edit", {"file_path": f"{SPACED_WT}/a.py", "old_string": "a", "new_string": "b"}),
    tool_use("Write", {"file_path": f"{SPACED_WT}/src/app.py", "content": "x"}),
    tool_use("NotebookEdit", {"notebook_path": f"{SPACED_WT}/n.ipynb", "new_source": "x"}),
    tool_use("Write", {"file_path": "/work/My Projects/repo/tasks/TASK_REVIEW_T900.md",
                       "content": "x"}),
    bash(f"cp a '{SPACED_WT}/my file'"),
    bash(f"cd '{SPACED_WT}' && git commit -qm 'T900 work'"),
], ids=["edit-spaced-worktree", "write-spaced-worktree", "notebook-spaced-worktree",
        "write-task-file-under-spaced-folder", "bash-cp-into-spaced-path", "bash-cd-spaced-worktree"])
def test_ac4_a_path_holding_a_space_is_still_work(tmp_path, entry):
    assert worked(tmp_path, [entry], worktrees=(SPACED_WT,)) is True


def test_ac4_a_bash_argument_with_a_space_into_the_worktree_is_work(tmp_path):
    assert worked(tmp_path, [bash(f"cp a '{WT}/my file'")]) is True


def test_ac4_a_message_naming_a_spaced_worktree_is_not_work(tmp_path):
    assert worked(tmp_path, [bash(f"git commit -qm 'see {SPACED_WT}/a.py'")],
                  worktrees=(SPACED_WT,)) is False


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_ac4_an_edit_through_a_symlinked_path_is_work(tmp_path):
    real = tmp_path / "real-wt-t900"
    (real / "src").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real)
    edit = tool_use("Edit", {"file_path": f"{link}/src/app.py", "old_string": "a", "new_string": "b"})
    assert worked(tmp_path, [edit], worktrees=(str(real),)) is True
    # and the other way round: the worktree listed through the link, the edit by its real path
    edit = tool_use("Edit", {"file_path": f"{real}/src/app.py", "old_string": "a", "new_string": "b"})
    assert worked(tmp_path, [edit], worktrees=(str(link),)) is True
    assert worked(tmp_path, [bash(f"cd {link}/src && python3 run.py")],
                  worktrees=(str(real),)) is True


def test_ac4_a_sub_agent_of_this_session_counts(tmp_path):
    edit = tool_use("Edit", {"file_path": f"{WT}/src/app.py", "old_string": "a", "new_string": "b"})
    assert worked(tmp_path, [bash("ls")], sub_entries=[edit]) is True


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0)]")
def test_ac4_ownership_is_unknown_without_a_readable_transcript(tmp_path):
    assert sw.load_work(None) is None
    assert sw.load_work(str(tmp_path / "missing.jsonl")) is None
    unreadable = tmp_path / f"{SID}.jsonl"
    unreadable.write_text("{}\n")
    unreadable.chmod(0)
    try:
        if os.access(unreadable, os.R_OK):
            pytest.skip("running as a user that reads mode-0 files")
        assert sw.load_work(str(unreadable)) is None
    finally:
        unreadable.chmod(0o600)


# ── AC 5 — the merge gate blocks only on this session's In Progress work ────────────────────
GATE = "pre_bash_block_unsafe_merge.py"
IN_PROGRESS_ROW = ("- [ ] **T900** — Another session's experiment | common-infrastructure | C2 | "
                   "Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T900.md`")


def _git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def gate_project(tmp_path, in_progress=(IN_PROGRESS_ROW,), ready=(), files=None):
    """A temp kit project: the hooks, a board, and one commit."""
    project = tmp_path / "repo"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (project / "tasks").mkdir()
    (project / "tasks" / "TASK_GUIDE_T900.md").write_text("# T900\n", encoding="utf-8")
    for rel, text in (files or {}).items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    (project / "PROJECT_KANBAN.md").write_text(
        "# Kanban\n\n### Todo\n\n### In Progress\n" + "\n".join(in_progress) +
        "\n\n### Ready for Review\n" + "\n".join(ready) + "\n\n### Done\n", encoding="utf-8")
    _git(project, "init", "-q", "-b", "main")
    _git(project, "config", "user.email", "t@example.com")
    _git(project, "config", "user.name", "t")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", "base")
    return project


def gate_env(project, **extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "LINEAR_API_KEY")}
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env.update(extra)
    return env


def run_gate(project, command, transcript=None, env=None):
    event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(project),
             "session_id": SID}
    if transcript is not None:
        event["transcript_path"] = str(transcript)
    done = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / GATE)],
                          input=json.dumps(event), capture_output=True, text=True, cwd=project,
                          env=env or gate_env(project), timeout=60)
    out = json.loads(done.stdout) if done.stdout.strip() else {}
    return out.get("reason", "") if out.get("decision") == "block" else None, done.stderr


def session(tmp_path, project, entries):
    for e in entries:
        e.setdefault("cwd", str(project))
    return write_transcript(tmp_path / "projects" / f"{SID}.jsonl", entries)


ROW_WITH_BRANCH = IN_PROGRESS_ROW + " | Started 2026-11-04: branch `exp/t900-x`, worktree `../wt-t900`"


def commit_on(project, branch, start, rel, text):
    """Create `branch` at `start` with one commit adding `rel`; HEAD goes back to main."""
    _git(project, "checkout", "-q", "-b", branch, start)
    (project / rel).write_text(text, encoding="utf-8")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", f"{branch}: {rel}")
    _git(project, "checkout", "-q", "main")


def t900_in_its_worktree(tmp_path, project):
    """As T249: the task's branch, with unfinished work, checked out in its own worktree."""
    commit_on(project, "exp/t900-x", "main", "t900.txt", "unfinished\n")
    _git(project, "worktree", "add", "-q", str(tmp_path / "wt-t900"), "exp/t900-x")


def test_ac5_another_sessions_in_progress_task_does_not_block_an_unrelated_merge(tmp_path):
    project = gate_project(tmp_path)
    t900_in_its_worktree(tmp_path, project)
    commit_on(project, "fix/t901-x", "main", "t901.txt", "done\n")
    t = session(tmp_path, project, [
        tool_use("Grep", {"pattern": "Risk", "path": str(project / "tasks" / "TASK_GUIDE_T900.md")}),
        bash("grep -n Risk tasks/TASK_GUIDE_T900.md", cwd=str(project))])
    reason, stderr = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason is None, reason
    assert "T900" in stderr and "not blocking" in stderr


def test_ac5_an_unrelated_branch_does_not_block_with_the_row_branch_only(tmp_path):
    project = gate_project(tmp_path, in_progress=(ROW_WITH_BRANCH,))
    commit_on(project, "exp/t900-x", "main", "t900.txt", "unfinished\n")
    commit_on(project, "fix/t901-x", "main", "t901.txt", "done\n")
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason is None, reason


@pytest.mark.parametrize("where", ["row", "worktree"])
def test_ac5_a_branch_cut_from_the_tasks_branch_still_blocks(tmp_path, where):
    """A branch named for T901 but cut from T900's branch brings in T900's unfinished commits."""
    project = gate_project(tmp_path, in_progress=(ROW_WITH_BRANCH if where == "row"
                                                  else IN_PROGRESS_ROW,))
    if where == "row":
        commit_on(project, "exp/t900-x", "main", "t900.txt", "unfinished\n")
    else:
        t900_in_its_worktree(tmp_path, project)
    commit_on(project, "fix/t901-x", "exp/t900-x", "t901.txt", "done\n")
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason and "Tasks still In Progress: T900" in reason


def test_ac5_a_task_branch_already_merged_does_not_block(tmp_path):
    project = gate_project(tmp_path, in_progress=(ROW_WITH_BRANCH,))
    commit_on(project, "exp/t900-x", "main", "t900.txt", "first part\n")
    _git(project, "merge", "-q", "--no-ff", "-m", "merge first part", "exp/t900-x")
    commit_on(project, "fix/t901-x", "exp/t900-x", "t901.txt", "done\n")
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason is None, reason


@pytest.mark.parametrize("case", ["no-branch-known", "row-branch-missing", "merged-ref-missing"])
def test_ac5_ac8_a_branch_that_cannot_be_compared_keeps_the_blocker(tmp_path, case):
    project = gate_project(tmp_path, in_progress=(
        IN_PROGRESS_ROW if case == "no-branch-known" else ROW_WITH_BRANCH,))
    if case == "merged-ref-missing":
        commit_on(project, "exp/t900-x", "main", "t900.txt", "unfinished\n")
    else:
        commit_on(project, "fix/t901-x", "main", "t901.txt", "done\n")
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason and "Tasks still In Progress: T900" in reason


def test_ac5_a_task_this_session_edited_still_blocks(tmp_path):
    project = gate_project(tmp_path)
    t = session(tmp_path, project, [tool_use("Edit", {
        "file_path": str(project / "tasks" / "TASK_GUIDE_T900.md"), "old_string": "a",
        "new_string": "b"}, cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason and "Tasks still In Progress: T900" in reason


def test_ac5_work_in_the_tasks_worktree_blocks(tmp_path):
    project = gate_project(tmp_path)
    wt = tmp_path / "wt-t900"
    _git(project, "worktree", "add", "-q", "-b", "exp/t900-x", str(wt))
    t = session(tmp_path, project, [bash(f"cd {wt} && python3 run.py", cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
    assert reason and "Tasks still In Progress: T900" in reason


def test_ac5_a_merge_that_brings_in_the_tasks_branch_blocks(tmp_path):
    project = gate_project(tmp_path)
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_gate(project, "git merge --no-ff exp/t900-x", t)
    assert reason and "Tasks still In Progress: T900" in reason


@pytest.mark.parametrize("command", [
    "git merge --no-ff main",             # names no task: what it brings in is unknown
    "git merge --no-ff fix/t901-x feat/x",  # one branch names no task
    "git push origin main",               # not a merge: today's whole-board rule
    "git pull",
    "git merge --abort",
])
def test_ac5_a_command_whose_branches_are_unknown_keeps_every_blocker(tmp_path, command):
    project = gate_project(tmp_path)
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    reason, _ = run_gate(project, command, t)
    assert reason and "Tasks still In Progress: T900" in reason


def test_ac5_ac8_no_transcript_blocks(tmp_path):
    project = gate_project(tmp_path)
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x")
    assert reason and "Tasks still In Progress: T900" in reason
    reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", tmp_path / "missing.jsonl")
    assert reason and "Tasks still In Progress: T900" in reason


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0)]")
def test_ac8_an_unreadable_transcript_blocks(tmp_path):
    project = gate_project(tmp_path)
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    t.chmod(0)
    try:
        if os.access(t, os.R_OK):
            pytest.skip("running as a user that reads mode-0 files")
        reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
        assert reason and "Tasks still In Progress: T900" in reason
    finally:
        t.chmod(0o600)


def _load_gate(project):
    source = (project / ".claude" / "hooks" / GATE).read_text(encoding="utf-8")
    head, marker, tail = source.rpartition("\nmain()")
    assert marker and not tail.strip()
    module = type(sys)("t250_gate")
    module.__file__ = str(project / ".claude" / "hooks" / GATE)
    old = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = str(project)
    try:
        exec(compile(head + "\n", module.__file__, "exec"), module.__dict__)
    finally:
        if old is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = old
    return module


def test_ac8_an_ownership_error_keeps_every_blocker(tmp_path, monkeypatch):
    project = gate_project(tmp_path)
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    gate = _load_gate(project)

    def boom(*_a, **_k):
        raise RuntimeError("ownership reader broke")
    monkeypatch.setattr(gate.session_work, "worked_on", boom)
    kept = gate.session_owned_in_progress(
        [("T900", IN_PROGRESS_ROW)], "git merge --no-ff fix/t901-x", str(project), str(t))
    assert kept == ["T900"]


# ── AC 1/2 through the gate — the user's `/verify` line on the minimal track ────────────────
RFR_MIN_ROW = ("- [ ] **T900** — Sort the names | Supervisor | C0 | Risk: Low | P2 "
               "| Track: minimal | Record: `tasks/MINIMAL_LOG.md`")
def blocked_hook_line(sha="a" * 40):
    return ("- verify: ☐ blocked — auto-run by hook, session cccccccc-0000, commit "
            f"{sha}, log .claude/verify-runs/T900-{sha[:12]}.log (no single verdict line)")


BLOCKED_HOOK_LINE = blocked_hook_line()
CODE_AT = "2026-11-04T06:00:00+00:00"
LINE_AT = "2026-11-04T06:10:00+00:00"


def user_line(sha, sid=SID):
    return f"- verify: ☑ pass — /verify by the user, session {sid}, commit {sha}"


def minimal_log(checked_lines):
    return ("# Minimal-track Decision records\n\n## T900 — Sort the names · minimal\n"
            '**Asked:** "sort the names"\n**Decisions:**\n- sort A–Z\n**Checked:**\n'
            "- Suite: `pytest -q` — 12 passed\n" + "".join(f"{l}\n" for l in checked_lines) +
            "**Files:** `src/app.py`\n**Not done:** merge (yours)\n")


def commit_at(project, when, message):
    env = dict(os.environ, GIT_COMMITTER_DATE=when, GIT_AUTHOR_DATE=when)
    subprocess.run(["git", "-C", str(project), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "commit", "-qm", message], check=True, env=env)
    return _git(project, "rev-parse", "HEAD")


def min_project(tmp_path, line_for=lambda sha: [user_line(sha)], code_change_after=False):
    """T900 at Ready for Review on the minimal track: code committed at 06:00, the Decision record
    with its `verify:` line(s) committed at 06:10. Returns (project, code sha)."""
    project = gate_project(tmp_path, in_progress=(), ready=(RFR_MIN_ROW,),
                           files={"src/app.py": "print('v1')\n"})
    trace = project / "memory" / "event-trace"
    trace.mkdir(parents=True)
    (trace / "T900.jsonl").write_text(json.dumps({"tool_name": "Bash", "is_error": False,
                                      "summary": json.dumps({"command": "python3 -m pytest -q"})})
                                      + "\n", encoding="utf-8")
    sha = commit_at(project, CODE_AT, "T900: sort")
    (project / "tasks" / "MINIMAL_LOG.md").write_text(minimal_log(line_for(sha)), encoding="utf-8")
    commit_at(project, LINE_AT, "record(T900)")
    if code_change_after:
        (project / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
        commit_at(project, LINE_AT, "T900: more code")
    return project, sha


def verify_session(tmp_path, project, entries, sid=SID):
    for e in entries:
        e.setdefault("cwd", str(project))
    return write_transcript(tmp_path / "projects" / f"{sid}.jsonl", entries)


MERGE_OTHER = "git merge --no-ff fix/t901-x"


def test_ac1_the_users_verify_line_with_the_transcript_entry_passes(tmp_path):
    project, _ = min_project(tmp_path)
    t = verify_session(tmp_path, project, [slash_verify("T900", "2026-11-04T06:05:12.960Z")])
    reason, _ = run_gate(project, MERGE_OTHER, t)
    assert reason is None, reason


def test_ac1_it_passes_after_a_blocked_hook_line_too(tmp_path):
    project, _ = min_project(tmp_path, line_for=lambda sha: [BLOCKED_HOOK_LINE, user_line(sha)])
    t = verify_session(tmp_path, project, [slash_verify("T900 please", "2026-11-04T06:05:12Z")])
    reason, _ = run_gate(project, MERGE_OTHER, t)
    assert reason is None, reason


def test_ac1_it_passes_when_merging_the_tasks_own_branch(tmp_path):
    project, _ = min_project(tmp_path)
    _git(project, "branch", "fix/t900-x")
    t = verify_session(tmp_path, project, [slash_verify("T900", "2026-11-04T06:05:12Z")])
    reason, _ = run_gate(project, "git merge --no-ff fix/t900-x", t)
    assert reason is None, reason


def test_ac1_the_named_session_may_be_another_sessions_file_in_the_same_folder(tmp_path):
    project, _ = min_project(tmp_path, line_for=lambda sha: [user_line(sha, OTHER_SID)])
    verify_session(tmp_path, project, [slash_verify("T900", "2026-11-04T06:05:12Z")], sid=OTHER_SID)
    current = verify_session(tmp_path, project, [bash("ls")])
    reason, _ = run_gate(project, MERGE_OTHER, current)
    assert reason is None, reason


@pytest.mark.parametrize("entries", [
    [slash_verify("T901", "2026-11-04T06:05:12Z")],
    [slash_verify("T900", "2026-11-04T06:05:12Z",
                  origin={"kind": "task-notification", "producer": "session-task"})],
    [slash_verify("T900", "2026-11-04T06:05:12Z", isMeta=True)],
    [human("please mark T900 as verified", "2026-11-04T06:05:12Z")],
    [slash_verify("T900", "2026-11-04T05:59:00Z")],   # before the verified code was committed
    [slash_verify("T900", "2026-11-04T06:11:00Z")],   # after the line was committed
], ids=["other-task", "task-notification", "isMeta", "not-a-slash-command", "before-the-code",
        "after-the-line"])
def test_ac2_without_a_matching_human_verify_the_line_blocks(tmp_path, entries):
    project, _ = min_project(tmp_path)
    t = verify_session(tmp_path, project, entries)
    reason, _ = run_gate(project, MERGE_OTHER, t)
    assert reason and "T900 (no evidence row)" in reason


def test_ac2_ac8_no_transcript_or_a_missing_session_file_blocks(tmp_path):
    project, _ = min_project(tmp_path, line_for=lambda sha: [user_line(sha, OTHER_SID)])
    reason, _ = run_gate(project, MERGE_OTHER)
    assert reason and "T900 (no evidence row)" in reason
    current = verify_session(tmp_path, project, [slash_verify("T900", "2026-11-04T06:05:12Z")])
    reason, _ = run_gate(project, MERGE_OTHER, current)  # OTHER_SID's file does not exist
    assert reason and "T900 (no evidence row)" in reason


@pytest.mark.parametrize("line_for", [
    lambda sha: [user_line(sha[:12])],                              # short hash
    lambda sha: [user_line("b" * 40)],                              # not a commit here
    lambda sha: [user_line(sha, "../../etc/passwd")],               # not a session id
    lambda sha: [user_line(sha).replace("☑ pass", "☐ pass")],       # unchecked
    lambda sha: [f"- verify: ☑ pass — user ran /verify T900, session {SID}, commit {sha}"],
], ids=["short-sha", "unknown-sha", "bad-session-id", "unchecked", "other-wording"])
def test_ac2_a_malformed_user_line_blocks(tmp_path, line_for):
    project, _ = min_project(tmp_path, line_for=line_for)
    t = verify_session(tmp_path, project, [slash_verify("T900", "2026-11-04T06:05:12Z")])
    reason, _ = run_gate(project, MERGE_OTHER, t)
    assert reason and "T900 (no evidence row)" in reason


def test_ac2_a_commit_with_other_code_blocks(tmp_path):
    project, _ = min_project(tmp_path, code_change_after=True)
    t = verify_session(tmp_path, project, [slash_verify("T900", "2026-11-04T06:05:12Z")])
    reason, _ = run_gate(project, MERGE_OTHER, t)
    assert reason and "T900 (no evidence row)" in reason


# ── AC 3 — the auto verify hook leaves the user's line alone ────────────────────────────────
def verify_hook_env(tmp_path, project):
    """A stub `claude` that only records it was called and prints nothing (a blocked verdict)."""
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    calls = tmp_path / "calls.txt"
    stub = stub_dir / "claude"
    stub.write_text(f"#!/bin/sh\necho called >> {calls}\n", encoding="utf-8")
    stub.chmod(0o755)
    env = gate_env(project, PATH=f"{stub_dir}{os.pathsep}/usr/bin:/bin",
                   CLAUDE_TRACE_ANCHOR_DIR=str(tmp_path / "anchors"))
    return env, calls, project / ".claude" / "hooks" / "stop_auto_verify.py"


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [via verify_hook_env]")
@pytest.mark.parametrize("with_blocked_line", [False, True], ids=["user-line-only", "after-blocked"])
def test_ac3_start_starts_nothing_and_never_edits_the_user_line(tmp_path, with_blocked_line):
    # As T246: the hook's blocked line is for the same code the user then verified.
    project, _ = min_project(tmp_path, line_for=lambda sha: (
        [blocked_hook_line(sha)] if with_blocked_line else []) + [user_line(sha)])
    before = (project / "tasks" / "MINIMAL_LOG.md").read_text(encoding="utf-8")
    env, calls, hook = verify_hook_env(tmp_path, project)
    for argv in ([str(hook), "--start", "T900"], [str(hook)]):
        done = subprocess.run([sys.executable, *argv], input=json.dumps({"hook_event_name": "Stop"}),
                              capture_output=True, text=True, cwd=project, env=env, timeout=30)
        if "--start" in argv:
            assert done.returncode == 1, (done.stdout, done.stderr)
    assert not calls.exists(), "a headless /verify run started"
    assert (project / "tasks" / "MINIMAL_LOG.md").read_text(encoding="utf-8") == before


def test_ac3_tracks_md_states_the_user_line_shape():
    text = (ROOT / "docs" / "claude-md" / "tracks.md").read_text(encoding="utf-8")
    section = text.split("\n### Auto verify (Stop hook)\n", 1)[1].split("\n### ", 1)[0]
    assert "- verify: ☑ pass — /verify by the user, session <id>, commit <sha>" in section


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [via verify_hook_env]")
def test_ac3_a_new_run_for_other_code_rewrites_only_the_hooks_line(tmp_path):
    project, sha = min_project(tmp_path, line_for=lambda sha: [BLOCKED_HOOK_LINE, user_line(sha)])
    env, calls, hook = verify_hook_env(tmp_path, project)
    done = subprocess.run([sys.executable, str(hook), "--start", "T900"], capture_output=True,
                          text=True, cwd=project, env=env, timeout=30)
    assert done.returncode == 0, (done.stdout, done.stderr)  # the hook's line is for other code
    log = project / "tasks" / "MINIMAL_LOG.md"
    deadline = time.monotonic() + 20
    while BLOCKED_HOOK_LINE in log.read_text(encoding="utf-8") and time.monotonic() < deadline:
        time.sleep(0.1)
    text = log.read_text(encoding="utf-8")
    assert BLOCKED_HOOK_LINE not in text, "the run never wrote its line"
    assert text.count(user_line(sha)) == 1


# ── AC 7 — the Stop check charges a task to this session only when it worked on it ──────────
STOP = "stop_auto_mode_check.py"
T249_LIKE_ROW = ("- [ ] **T900** — Another session's experiment | common-infrastructure | C2 | "
                 "Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T900.md`")


def _ago(seconds):
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()


def stop_project(tmp_path):
    """T900 In Progress; its guide and review (no `## Auto decisions`) were just written — inside
    the `[auto]` window this session opened 10 minutes ago."""
    project = gate_project(tmp_path, in_progress=(T249_LIKE_ROW,), files={
        "tasks/TASK_REVIEW_T900.md": "# TASK_REVIEW — T900\n\n## Evidence\n\n| Check | Result | Notes |\n"})
    trace = project / "memory" / "event-trace"
    trace.mkdir(parents=True)
    (trace / "T900.jsonl").write_text(json.dumps({"tool_name": "Bash", "is_error": False,
                                      "summary": json.dumps({"command": "python3 -m pytest -q"})})
                                      + "\n", encoding="utf-8")
    return project


def run_stop(project, transcript):
    event = {"session_id": SID, "transcript_path": str(transcript), "hook_event_name": "Stop",
             "stop_hook_active": False}
    done = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / STOP)],
                          input=json.dumps(event), capture_output=True, text=True, cwd=project,
                          env=gate_env(project), timeout=60)
    out = json.loads(done.stdout) if done.stdout.strip() else {}
    return (out.get("reason", "") if out.get("decision") == "block" else None), done.stderr


def auto_request():
    return human("continue [auto]", _ago(600))


def test_ac7_another_sessions_task_changed_in_the_window_is_not_checked(tmp_path):
    project = stop_project(tmp_path)
    t = session(tmp_path, project, [auto_request(), tool_use("Grep", {
        "pattern": "Mode", "path": str(project / "tasks" / "TASK_REVIEW_T900.md")}, _ago(300))])
    reason, stderr = run_stop(project, t)
    assert reason is None, reason


def test_ac7_a_task_this_session_wrote_in_the_window_is_still_checked(tmp_path):
    project = stop_project(tmp_path)
    t = session(tmp_path, project, [auto_request(), tool_use("Write", {
        "file_path": str(project / "tasks" / "TASK_REVIEW_T900.md"), "content": "x"}, _ago(300),
        cwd=str(project))])
    reason, _ = run_stop(project, t)
    assert reason and "T900" in reason and "Auto decisions" in reason


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0)]")
def test_ac7_ac8_unreadable_ownership_keeps_the_check(tmp_path):
    project = stop_project(tmp_path)
    t = session(tmp_path, project, [auto_request()])
    sub = write_transcript(t.parent / SID / "subagents" / "agent-a1.jsonl", [bash("ls")])
    sub.chmod(0)
    try:
        if os.access(sub, os.R_OK):
            pytest.skip("running as a user that reads mode-0 files")
        reason, _ = run_stop(project, t)
        assert reason and "T900" in reason
    finally:
        sub.chmod(0o600)


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0)]")
def test_ac5_ac8_an_unreadable_sub_agent_transcript_keeps_the_gates_blocker(tmp_path):
    project = gate_project(tmp_path)
    t = session(tmp_path, project, [bash("ls", cwd=str(project))])
    sub = write_transcript(t.parent / SID / "subagents" / "agent-a1.jsonl", [bash("ls")])
    sub.chmod(0)
    try:
        if os.access(sub, os.R_OK):
            pytest.skip("running as a user that reads mode-0 files")
        reason, _ = run_gate(project, "git merge --no-ff fix/t901-x", t)
        assert reason and "Tasks still In Progress: T900" in reason
    finally:
        sub.chmod(0o600)


def test_ac7_ac8_an_ownership_reader_that_raises_keeps_the_check(tmp_path):
    """AC 8 for AC 7 without chmod: `session_work.load_work` raises inside the Stop hook. The
    transcript is another session's case (a `Grep` only), which alone would leave T900 unchecked."""
    project = stop_project(tmp_path)
    lib = project / ".claude" / "hooks" / "lib" / "session_work.py"
    lib.write_text(lib.read_text(encoding="utf-8") + "\n\ndef load_work(_path):\n"
                   "    raise RuntimeError('ownership reader broke')\n", encoding="utf-8")
    t = session(tmp_path, project, [auto_request(), tool_use("Grep", {
        "pattern": "Mode", "path": str(project / "tasks" / "TASK_REVIEW_T900.md")}, _ago(300))])
    reason, stderr = run_stop(project, t)
    assert reason and "T900" in reason and "Auto decisions" in reason, (reason, stderr)
    assert "session ownership unknown (RuntimeError)" in stderr
