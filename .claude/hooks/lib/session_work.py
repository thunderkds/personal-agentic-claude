"""T250: what this session did, read from its own transcript.

Two questions, one reader:

  * `verify_typed` — did the user type `/verify <ID>` in a session (G1)? Only a human entry counts:
    `type` user, `origin.kind` "human", not `isMeta`, not a sidechain, string content holding
    `<command-name>/verify</command-name>` and `<command-args>` whose first word is the task ID.
  * `load_work` + `worked_on` — did this session work on task X (G2, G3)? A non-read tool call by
    the session or one of its sub-agents (`<session>/subagents/agent-*.jsonl`): `Edit`, `Write`,
    `MultiEdit`, `NotebookEdit` of a file in the task's worktree or a `tasks/*_<ID>*` file; a `Bash`
    command that runs in the task's worktree or names one of those paths, unless it only reads; an
    `Agent` spawn whose prompt binds to the task (`Task ID:` line first, else the first guide path).

Every reader works line by line and never loads a whole transcript. Each one fails closed for its
caller: `verify_typed` is False on any doubt, and `load_work` is None (ownership unknown) when the
transcript is missing or unreadable, so the caller keeps its old, stricter answer.
"""
import glob
import json
import os
import re
import shlex
from datetime import datetime, timezone

import auto_mode
from shell_data import strip_heredoc_bodies
from task_context import _task_id_from_spawn_prompt

COMMAND_NAME = re.compile(r"<command-name>\s*/verify\s*</command-name>")
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def parse_ts(value):
    """An aware datetime from a transcript timestamp, or None."""
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _human_command_args(entry):
    """The `/verify` args of a human slash-command entry, or None for any other entry."""
    if not isinstance(entry, dict) or entry.get("type") != "user":
        return None
    if entry.get("isMeta") or entry.get("isSidechain") or entry.get("isCompactSummary"):
        return None
    origin = entry.get("origin")
    if not isinstance(origin, dict) or origin.get("kind") != "human":
        return None
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not COMMAND_NAME.search(content):
        return None
    args = COMMAND_ARGS.search(content)
    return args.group(1) if args else ""


def verify_typed(transcript_path, task_id, after=None, before=None):
    """True when `transcript_path` holds a human `/verify <task_id>` entry dated in
    `[after, before]` (aware datetimes; None leaves that side open). False on any doubt."""
    try:
        want = str(task_id).strip().upper()
        if not want or not transcript_path or not os.path.isfile(transcript_path):
            return False
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                if "/verify" not in line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                args = _human_command_args(entry)
                if args is None:
                    continue
                words = args.split()
                if not words or words[0].upper() != want:
                    continue
                ts = parse_ts(entry.get("timestamp"))
                if ts is None or (after and ts < after) or (before and ts > before):
                    continue
                return True
    except Exception:
        return False
    return False


# --- did this session work on task X (AC 4) ------------------------------------------------------
#
# Known limits, by design (a static read of what the session ran): a path held in a shell variable
# (`"$WT"`), a heredoc body (data, as in `shell_data`, even when an interpreter reads it), and a
# script that writes a task file without naming it on its command line are not seen as work.

WRITE_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
               "NotebookEdit": "notebook_path"}
SPAWN_TOOLS = ("Agent", "Task")
KEPT_TOOLS = frozenset(WRITE_TOOLS) | frozenset(SPAWN_TOOLS) | {"Bash"}

SEPARATORS = frozenset({";", "&&", "||", "|", "&", "|&", ";;", "(", ")"})
READ_ONLY_COMMANDS = frozenset({
    "cat", "head", "tail", "grep", "egrep", "fgrep", "rg", "ls", "wc", "stat", "file", "diff",
    "cmp", "echo", "printf", "pwd", "true", "false", "test", "[", "basename", "dirname",
    "realpath", "readlink", "jq"})
READ_ONLY_GIT = frozenset({"log", "status", "show", "diff", "rev-parse", "ls-files", "blame",
                           "merge-base", "cat-file", "describe", "shortlog", "grep"})
REDIRECT = re.compile(r"[<>&|]*>[<>&|]*")
HARMLESS_TARGET = re.compile(r"/dev/null|&?\d")
SED_WRITE = re.compile(r"(?:^|[;/}\s])w\s")
UNKNOWN_DIR = object()


def _session_files(transcript_path):
    """The session transcript first, then each of its sub-agents' transcripts."""
    base = os.path.splitext(os.path.basename(transcript_path))[0]
    pattern = os.path.join(os.path.dirname(transcript_path), glob.escape(base), "subagents",
                           "agent-*.jsonl")
    return [transcript_path] + sorted(glob.glob(pattern))


def load_work(transcript_path):
    """`[(tool name, input, cwd)]` for every call that may change a task — write tools, `Bash`,
    `Agent` — in the session and its sub-agents, or None when ownership cannot be read."""
    if not isinstance(transcript_path, str) or not os.path.isfile(transcript_path):
        return None
    calls = []
    try:
        for path in _session_files(transcript_path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if '"tool_use"' not in line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    message = entry.get("message") if isinstance(entry, dict) else None
                    content = message.get("content") if isinstance(message, dict) else None
                    if entry.get("type") != "assistant" or not isinstance(content, list):
                        continue
                    cwd = entry.get("cwd") if isinstance(entry.get("cwd"), str) else None
                    for block in content:
                        if (isinstance(block, dict) and block.get("type") == "tool_use"
                                and block.get("name") in KEPT_TOOLS
                                and isinstance(block.get("input"), dict)):
                            calls.append((block["name"], block["input"], cwd))
    except Exception:
        return None
    return calls


class _Task:
    """How one task's files and worktrees are named in a command."""

    def __init__(self, task_id, worktrees):
        self.task_id = str(task_id).strip().upper()
        self.worktrees = [os.path.normpath(w) for w in worktrees if isinstance(w, str)
                          and os.path.isabs(w)]
        self.file = re.compile(rf"(?<![A-Za-z0-9])tasks/[A-Za-z0-9_.-]*_{re.escape(self.task_id)}"
                               r"(?![0-9])", re.I)

    def inside(self, path):
        path = os.path.normpath(path)
        return any(path == w or path.startswith(w + os.sep) for w in self.worktrees)

    def named(self, token, directory):
        """True when `token` names one of the task's files or a path in its worktree."""
        if self.file.search(token):
            return True
        for part in [token] + token.split("=")[1:]:
            if any(part == w or part.startswith(w + os.sep) or (w + os.sep) in part
                   for w in self.worktrees):
                return True
            if (isinstance(directory, str) and part and not part.startswith("-")
                    and "$" not in part and "`" not in part
                    and self.inside(os.path.join(directory, part))):
                return True
        return False


def _segments(command):
    """The simple commands of `command` as token lists, heredoc bodies dropped; None when the
    text does not tokenize."""
    text = strip_heredoc_bodies(command).replace("\n", " ; ")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    segments, current = [], []
    for token in tokens:
        if token in SEPARATORS:
            segments.append(current)
            current = []
        else:
            current.append(token)
    segments.append(current)
    return [s for s in segments if s]


def _read_only(tokens):
    """True only for a command that cannot change a file: an allowlisted reader, a read-only `git`
    subcommand, or `sed` without in-place editing — and no output redirect to a real file."""
    for index, token in enumerate(tokens):
        if REDIRECT.fullmatch(token) and ">" in token:
            target = tokens[index + 1] if index + 1 < len(tokens) else ""
            if not HARMLESS_TARGET.fullmatch(target):
                return False
    head, args = os.path.basename(tokens[0]), tokens[1:]
    if head in READ_ONLY_COMMANDS:
        return True
    if head == "sed":
        return not any(a.startswith(("-i", "--in-place")) or SED_WRITE.search(a) for a in args)
    if head != "git":
        return False
    while args and args[0].startswith("-"):
        args = args[2:] if args[0] in ("-C", "-c") else args[1:]
    if any(a.startswith("--output") for a in args):
        return False
    if args and args[0] in READ_ONLY_GIT:
        return True
    return args[:2] == ["worktree", "list"]


def _bash_works(command, cwd, task):
    segments = _segments(command)
    if segments is None:  # unparsable: any mention of the task's paths is work
        return any(task.named(t, cwd) for t in strip_heredoc_bodies(command).split())
    directory = cwd
    for tokens in segments:
        if tokens[0] == "cd":
            target = tokens[1] if len(tokens) == 2 else None
            if (target and isinstance(directory, str) and "$" not in target
                    and "`" not in target and not target.startswith("~")):
                directory = os.path.normpath(os.path.join(directory, target))
            else:
                directory = UNKNOWN_DIR
            continue
        runs_in = directory is UNKNOWN_DIR or (isinstance(directory, str)
                                               and task.inside(directory))
        here = directory if isinstance(directory, str) else None
        if (runs_in or any(task.named(t, here) for t in tokens)) and not _read_only(tokens):
            return True
    return False


def worked_on(calls, task_id, worktrees):
    """True when one of `calls` (from `load_work`) changed task `task_id`, whose live worktrees are
    `worktrees` (absolute paths). Read-only calls never count."""
    task = _Task(task_id, worktrees)
    for name, tool_input, cwd in calls:
        if name in WRITE_TOOLS:
            path = tool_input.get(WRITE_TOOLS[name])
            if isinstance(path, str) and task.named(path, cwd):
                return True
        elif name in SPAWN_TOOLS:
            if _task_id_from_spawn_prompt(tool_input.get("prompt")) == task.task_id:
                return True
        elif isinstance(tool_input.get("command"), str):
            if _bash_works(tool_input["command"], cwd, task):
                return True
    return False


def task_worktrees(root, task_id, row=None):
    """The live worktrees that hold task `task_id`'s work: the one on the branch its board `row`
    names, and every one whose branch names the task. More is the safe side: work in any of them
    counts. The main checkout is never one of them."""
    branch = auto_mode.row_branch(row or "")
    found = []
    for path in auto_mode.worktree_dirs(root):
        name = auto_mode.branch_of(path)
        if name and (name == branch or auto_mode.names_task(name, task_id)):
            found.append(os.path.normpath(os.path.abspath(path)))
    return found
