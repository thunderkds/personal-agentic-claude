#!/usr/bin/env python3
"""T267 — the merge gate sees git writes spelled for PowerShell, and the PowerShell tool.

Before T267 two gaps let a push or merge through on native Windows (BEFORE capture in
`tasks/TASK_REVIEW_T267.md`):

  * detection is a regex over the command text, and `GIT_VERB_PREFIX` needs whitespace after
    `git`, so `git.exe push`, ``git` push`` and `& "C:\\…\\git.exe" push` never matched;
  * `main()` left at once for every tool but `Bash`, so a `PowerShell` tool call was never read.

The fix (Debate, 3 Advocates): no PowerShell lexer. A syntax-blind fallback
(`WINDOWS_GIT_FALLBACK`, `windows_git_write`) runs beside `BLOCKED_PATTERNS` on the raw text with
backticks and quote characters removed. It is on only on a Windows host, for the PowerShell tool,
or when the text carries a PowerShell marker. A command it flags goes to the same board check as a
plain `git push`; the POSIX tokenizer cannot read these spellings, so it never narrows them.

Every board, guide and trace is constructed; nothing reads the live board.

Run with: python3 -m pytest .claude/hooks/tests/test_windows_merge_gate.py -q
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time
import types

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")


def load_hook_module(name, mutate=None):
    """Load the hook without running its bottom-of-file `main()`; `mutate` rewrites the source
    first (the mutation controls). A mutation whose target is missing fails loudly."""
    source = open(HOOK_PATH, encoding="utf-8").read()
    marker = "\nmain()"
    assert marker in source, "the hook no longer ends in a bare main() call"
    if mutate is not None:
        old, new = mutate
        assert old in source, f"mutation target not found: {old!r}"
        source = source.replace(old, new)
    module = types.ModuleType(name)
    module.__file__ = HOOK_PATH
    exec(compile(source.replace(marker, "\n"), HOOK_PATH, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module("merge_gate_t267")

# Spelled in pieces so this file's own text never reads as a push to the live gate.
GIT = "git"
PUSH, MERGE, PULL = GIT + " push", GIT + " merge", GIT + " pull"


# ---------------------------------------------------------------------------
# Constructed fixtures
# ---------------------------------------------------------------------------

def kanban(in_progress=(), ready=()):
    def rows(ids):
        return "".join(f"- [ ] **{t}** — fixture task {t} | agent | C1 | Risk: Low | P1\n"
                       for t in ids)
    return ("# PROJECT_KANBAN\n\n### Todo\n\n### In Progress\n" + rows(in_progress)
            + "\n### Ready for Review\n" + rows(ready) + "\n### Done\n")


GUIDE_VACATED = "# TASK_GUIDE - {tid}\n\n### Evidence\n\n> Moved to `tasks/TASK_REVIEW_{tid}.md`.\n"
REVIEW_VERIFIED = """# TASK_REVIEW - {tid}

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| verify | ☑ pass | verify skill run, feature confirmed working — pass |
"""


def trace_record(tool_name="Bash"):
    return json.dumps({
        "timestamp": "2026-11-06T00:00:00+00:00",
        "tool_name": tool_name,
        "summary": json.dumps({"command": "python3 -m pytest .claude/hooks/tests/ -q"})[:300],
        "is_error": False,
    })


# The three boards every verdict is compared on.
BOARDS = {
    # An In Progress task, no evidence: every git write blocks.
    "in_progress": dict(board=kanban(in_progress=("T900",)), verified=()),
    # A Ready for Review task with no evidence row: every git write blocks.
    "unverified": dict(board=kanban(ready=("T901",)), verified=()),
    # A Ready for Review task with complete evidence: every git write is allowed.
    "complete": dict(board=kanban(ready=("T900",)), verified=("T900",)),
}
# Review P0-1: T901 In Progress with no evidence, T900 in Ready for Review and verified, so only
# a push narrowed to T900 is allowed.
NARROW_BOARD = dict(board=kanban(in_progress=("T901",), ready=("T900",)), verified=("T900",))
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


@pytest.fixture
def gate(tmp_path, monkeypatch):
    """`gate(name, platform="win32")` builds board `name` and points the module at it."""
    def build(name, platform="win32", module=None):
        module = module or merge_gate
        spec = NARROW_BOARD if name == "narrow" else BOARDS[name]
        root = tmp_path / name
        tasks = root / "tasks"
        trace = root / "memory" / "event-trace"
        tasks.mkdir(parents=True, exist_ok=True)
        trace.mkdir(parents=True, exist_ok=True)
        for tid in ("T900", "T901"):
            (tasks / f"TASK_GUIDE_{tid}.md").write_text(GUIDE_VACATED.format(tid=tid), "utf-8")
        for tid in spec["verified"]:
            (tasks / f"TASK_REVIEW_{tid}.md").write_text(REVIEW_VERIFIED.format(tid=tid), "utf-8")
            (trace / f"{tid}.jsonl").write_text(trace_record() + "\n", "utf-8")
        (root / "PROJECT_KANBAN.md").write_text(spec["board"], "utf-8")
        monkeypatch.setattr(module, "KANBAN", str(root / "PROJECT_KANBAN.md"))
        monkeypatch.setattr(module, "TASKS_DIR", str(tasks))
        monkeypatch.setattr(module, "TRACE_DIR", str(trace))
        monkeypatch.setattr(module, "worktree_tasks_dirs", lambda: [])
        monkeypatch.setattr(sys, "platform", platform)
        return root
    return build


def run_gate(command, tool_name="Bash", module=None, tool_input=None, cwd=None):
    """Drive the hook's real `main()` over one event: the block reason, or None for allow."""
    module = module or merge_gate
    event = {"tool_name": tool_name,
             "tool_input": tool_input if tool_input is not None else {"command": command}}
    if cwd is not None:
        event["cwd"] = cwd
    saved = (sys.stdin, sys.stdout, sys.stderr)
    sys.stdin, sys.stdout, sys.stderr = io.StringIO(json.dumps(event)), io.StringIO(), io.StringIO()
    try:
        try:
            module.main()
        except SystemExit:
            pass
        out = sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved
    return json.loads(out)["reason"] if out.strip() else None


# ---------------------------------------------------------------------------
# AC 4 / AC 8: each PowerShell spelling gets the plain command's verdict
# ---------------------------------------------------------------------------

# (PowerShell spelling, the plain command it means)
SPELLINGS = [
    (GIT + ".exe push origin main", PUSH + " origin main"),
    (GIT + "` push", PUSH),
    ('& "C:\\Program Files\\Git\\cmd\\' + GIT + '.exe" push', PUSH),
    ('$g="' + GIT + '"; & $g push', PUSH),
    ("$env:X='1'; " + PUSH, PUSH),
    ("echo 'it''s'; " + MERGE + " feat", MERGE + " feat"),
    ('iex "' + PUSH + '"', PUSH),
    ("cmd /c " + PUSH, PUSH),
    (GIT + ".exe -C . pull", PULL),
    # Beyond the AC 4 list: case, line continuation, a variable set on another line.
    (GIT.upper() + ".EXE PUSH", PUSH),
    (GIT + " `\n  push origin main", PUSH + " origin main"),
    ('$g = "C:\\Git\\' + GIT + '.exe"\n& $g push', PUSH),
    ("Invoke-Expression $c  # $c holds: push", PUSH),
    ("& $g -c alias.p=push p", PUSH),
    # Self-review gaps: the verb sits in a variable after the git word, and a Unicode line
    # separator that `str.splitlines` would split on but a shell need not.
    ("$a='push'; " + GIT + " $a origin main", PUSH + " origin main"),
    ("$a=@('push'); " + GIT + ".exe @a", PUSH),
    (GIT + ".exe push", PUSH),
    (GIT + ".exe\x85push", PUSH),
]


# Review P0-2: spellings with no `git` word before the verb on the same line, read only by the
# PowerShell tool's one rule (a verb word anywhere, after removing escapes, `+` and quotes).
POWERSHELL_SPELLINGS = [
    ("Start-Process -ArgumentList push,origin,main " + GIT, PUSH + " origin main"),
    ("Start-Process -ArgumentList 'push' -FilePath " + GIT, PUSH),
    ("$p = @{\n FilePath = '" + GIT + "'\n ArgumentList = 'push'\n}\nStart-Process @p -Wait", PUSH),
    (GIT + " (\n'push')", PUSH),
    ("[Diagnostics.Process]::Start(\n'" + GIT + "',\n'push')", PUSH),
    ("Set-Alias g " + GIT + "\ng push origin main", PUSH + " origin main"),
    ("New-Alias g " + GIT + "\ng push origin main", PUSH + " origin main"),
    ("sal g " + GIT + "\ng push origin main", PUSH + " origin main"),
    ("$g='" + GIT + "'\n. $g push", PUSH),
    ("& ${g} push", PUSH),
    ("& $($g) push", PUSH),
    ("& ('gi'+'t') push", PUSH),
    ("cmd /c gi^t pu^sh", PUSH),
    ("g\u2019it push", PUSH),
    ("& $g pu\u201csh\u201d", PUSH),
]


@pytest.mark.parametrize("board", sorted(BOARDS))
@pytest.mark.parametrize("spelling,plain", POWERSHELL_SPELLINGS)
def test_review_p0_2_powershell_spelling_gets_the_plain_verdict(gate, board, spelling, plain):
    gate(board)
    assert run_gate(spelling, "PowerShell") == run_gate(plain, "Bash"), spelling


def test_review_p2_powershell_mention_of_a_verb_over_blocks_known_decision(gate):
    """Known decision: for the PowerShell tool a verb word anywhere is gated, so a commit message
    or a search that names one is blocked while a task is In Progress. Over-blocking is the
    accepted direction; the Bash tool on Linux is unchanged."""
    gate("in_progress")
    for command in (GIT + ' commit -m "merge gate fix"', "Select-String merge notes.txt",
                    "Push-Location C:\\src"):
        assert run_gate(command, "PowerShell") is not None, command
    gate("in_progress", platform="linux")
    assert run_gate(GIT + ' commit -m "merge gate fix"', "Bash") is None


@pytest.mark.parametrize("tool_name", ["Bash", "PowerShell"])
@pytest.mark.parametrize("board", sorted(BOARDS))
@pytest.mark.parametrize("spelling,plain", SPELLINGS)
def test_ac4_spelling_gets_the_plain_commands_verdict(gate, board, spelling, plain, tool_name):
    gate(board)
    expected = run_gate(plain, "Bash")
    if board == "complete":
        assert expected is None, "fixture: the plain command must be allowed on a complete board"
    else:
        assert expected is not None, "fixture: the plain command must block on this board"
    assert run_gate(spelling, tool_name) == expected, (spelling, tool_name)


def test_ac4_encoded_command_is_gated_although_no_verb_is_visible(gate):
    """`-EncodedCommand` hides the verb in base64, so the marker alone sends it to the board."""
    gate("in_progress")
    expected = run_gate(PUSH)
    for command in ("powershell -EncodedCommand ZwBpAHQAIABwAHUAcwBoAA==",
                    "pwsh.exe -enc ZwBpAHQAIABwAHUAcwBoAA==",
                    "powershell -e ZwBpAHQAIABwAHUAcwBoAA=="):
        assert run_gate(command, "PowerShell") == expected, command


# ---------------------------------------------------------------------------
# AC 5: commands that write nothing stay allowed on win32
# ---------------------------------------------------------------------------

READ_ONLY = ["git status", "git.exe status", "git log", "git.exe merge-base a b", "echo hello",
             "Get-ChildItem", "git.exe log --oneline -5", "Get-Content $env:TEMP\\x.txt"]


@pytest.mark.parametrize("tool_name", ["Bash", "PowerShell"])
@pytest.mark.parametrize("command", READ_ONLY)
def test_ac5_non_write_commands_are_allowed_on_win32(gate, command, tool_name):
    gate("in_progress")
    assert run_gate(command, tool_name) is None, command


def test_edge_quoted_mention_over_blocks_on_win32_known_decision(gate):
    """Quotes are removed, not read: `echo "… git push …"` with PowerShell in play is gated.
    Over-blocking is the accepted direction (`pre_bash_block_unsafe_merge.py` "Seeing more text
    than bash runs can only make this global")."""
    gate("in_progress")
    assert run_gate('echo "run ' + PUSH + ' later"', "PowerShell") is not None
    gate("in_progress", platform="linux")
    assert run_gate('echo "run ' + PUSH + ' later"', "Bash") is None  # POSIX: unchanged


# ---------------------------------------------------------------------------
# AC 2: activation — win32, the PowerShell tool, or a PowerShell marker
# ---------------------------------------------------------------------------

def test_review_p1_1_markers_do_not_turn_the_fallback_on_for_bash_on_linux(gate):
    """Review P1-1: off Windows the Bash tool runs bash, so the fallback is off and the
    pre-T267 verdict stands, PowerShell-looking text or not."""
    gate("in_progress", platform="linux")
    assert run_gate(GIT + ".exe push origin main") is None
    assert run_gate(GIT + "` push") is None


def test_ac2_powershell_tool_turns_the_fallback_on_off_windows(gate):
    gate("in_progress", platform="linux")
    assert run_gate("& $g push", "PowerShell") is not None


def test_ac2_detector_is_off_on_posix_without_a_marker(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert not merge_gate.windows_git_write("git log --oneline | grep push", "Bash")
    monkeypatch.setattr(sys, "platform", "win32")
    assert merge_gate.windows_git_write("git log --oneline | grep push", "Bash")  # over-match


# Recorded with the pre-T267 hook (eb76a9af) on the in_progress board, platform linux, tool Bash:
# True = blocked. T267 must not move any of them.
LINUX_BASELINE = [
    (PUSH, True),
    (PUSH + " origin main", True),
    (MERGE + " feat", True),
    (PULL + " --rebase", True),
    (GIT + " rebase main", True),
    (GIT + " -C . pull", True),
    ("bash -c '" + PUSH + "'", True),
    (GIT + " status", False),
    (GIT + " log --oneline | grep push", False),
    (GIT + " merge-base a b", False),
    ('echo "' + PUSH + '"', False),
    ('grep -r "' + PUSH + '" .claude/', False),
    ("cat > f <<'E'\n" + PUSH + "\nE", False),
    ("git log; echo push", False),
    ("ls -la", False),
    # Review P1-1: these blocked on the first T267 cut through the PowerShell-marker activation.
    (GIT + " commit -F - <<'EOF'\nfix: the gate now reads `" + PUSH + "`\nEOF", False),
    (GIT + " commit -m 'merge gate reads `" + GIT + ".exe`'", False),
    (GIT + " log --grep=push -- x.exe", False),
    (GIT + ".exe push origin main", False),
    (GIT + "` push", False),
]


@pytest.mark.parametrize("command,blocked", LINUX_BASELINE)
def test_ac2_linux_plain_commands_match_the_recorded_baseline(gate, command, blocked):
    gate("in_progress", platform="linux")
    assert (run_gate(command) is not None) is blocked, command


# ---------------------------------------------------------------------------
# AC 3: a flagged command never narrows; it takes the whole-board path
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("spelling,_plain", SPELLINGS)
def test_ac3_flagged_spellings_are_unresolved(spelling, _plain, tmp_path):
    assert merge_gate.pushed_task_ids(spelling, str(tmp_path)) is None


def test_ac3_unreadable_input_still_blocks(gate):
    gate("complete")
    saved = (sys.stdin, sys.stdout)
    sys.stdin, sys.stdout = io.StringIO("{not json"), io.StringIO()
    try:
        with pytest.raises(SystemExit):
            merge_gate.main()
        assert '"decision": "block"' in sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout = saved


# ---------------------------------------------------------------------------
# AC 8 / AC 9: the PowerShell tool is read, every other tool is not
# ---------------------------------------------------------------------------

def test_ac8_powershell_tool_plain_push_blocks_like_bash(gate):
    gate("in_progress", platform="linux")
    expected = run_gate(PUSH + " origin main", "Bash")
    assert expected is not None
    assert run_gate(PUSH + " origin main", "PowerShell") == expected


def test_ac8_powershell_trace_record_counts_as_a_test_run(gate):
    root = gate("complete")
    (root / "memory" / "event-trace" / "T900.jsonl").write_text(
        trace_record("PowerShell") + "\n", "utf-8")
    assert merge_gate.trace_shows_verification("T900")
    assert run_gate(PUSH, "PowerShell") is None


@pytest.mark.parametrize("tool_name", ["Read", "Write", "Edit", "Agent", None])
def test_ac9_other_tools_are_ignored(gate, tool_name):
    gate("in_progress")
    assert run_gate(PUSH, tool_name) is None
    assert run_gate(None, tool_name, tool_input={"file_path": "/x", "content": PUSH}) is None


def test_ac9_bash_plain_push_is_unchanged(gate):
    gate("in_progress", platform="linux")
    assert "Tasks still In Progress: T900" in run_gate(PUSH)


@pytest.mark.parametrize("tool_name", [["Bash"], {"x": 1}, 7])
def test_review_p3_non_string_tool_name_is_ignored_without_raising(gate, tool_name):
    gate("in_progress")
    assert run_gate(PUSH, tool_name) is None


def git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          timeout=30, env={**os.environ, **GIT_ENV})
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def test_review_p0_1_powershell_call_is_never_narrowed(gate, tmp_path, monkeypatch):
    """shlex reads `\\"` as an escaped quote; PowerShell does not, so there the text below runs a
    second push of main. A PowerShell call therefore checks the whole board (T901 blocks), while
    the Bash tool, where shlex's reading is bash's, keeps the T197 narrowing (T900 alone)."""
    for key, value in GIT_ENV.items():
        monkeypatch.setenv(key, value)
    root = gate("narrow")
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "feat/t900-x")
    shutil.copytree(root / "tasks", repo / "tasks")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "tasks")
    command = (PUSH + ' --force-with-lease="x\\"; ' + PUSH + ' origin main #\\"" origin feat/t900-x')
    assert run_gate(command, "Bash", cwd=str(repo)) is None  # fixture: Bash narrows to T900
    blocked = run_gate(command, "PowerShell", cwd=str(repo))
    assert blocked is not None and "T901" in blocked
    assert run_gate(PUSH + " origin feat/t900-x", "PowerShell", cwd=str(repo)) is not None


# ---------------------------------------------------------------------------
# Edge: the detector stays linear
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "git " * 2500,                    # many git words, no verb: the quadratic case of a lazy regex
    "git.exe " * 1250,
    "& $g " * 2000,
    "`" * 10000,
    ("git " * 2500)[:10000] + "\n" + "x" * 10000,
])
def test_edge_detector_is_fast_on_10k_input(text, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    start = time.perf_counter()
    merge_gate.windows_git_write(text, "PowerShell")
    assert time.perf_counter() - start < 1.0


def test_edge_detector_is_fast_on_100k_input(monkeypatch):
    """A hook that times out is a non-blocking error: the call would run. Linear, not quadratic."""
    monkeypatch.setattr(sys, "platform", "win32")
    start = time.perf_counter()
    assert not merge_gate.windows_git_write("git " * 25000, "PowerShell")
    assert not merge_gate.windows_git_write("git " * 25000, "Bash")
    assert time.perf_counter() - start < 1.0


# ---------------------------------------------------------------------------
# Mutation controls: each test above that guards a new branch goes red without it
# ---------------------------------------------------------------------------

def test_mutation_without_the_fallback_branch_git_exe_push_passes(gate):
    mutant = load_hook_module("merge_gate_t267_no_fallback", mutate=(
        "and not windows_git_write(command, tool_name)", ""))
    gate("in_progress", module=mutant)
    assert run_gate(GIT + ".exe push origin main", module=mutant) is None  # the bypass is back
    gate("in_progress")
    assert run_gate(GIT + ".exe push origin main") is not None


def test_mutation_bash_only_check_lets_the_powershell_tool_through(gate):
    mutant = load_hook_module("merge_gate_t267_bash_only", mutate=(
        "tool_name not in SHELL_TOOLS:", 'tool_name != "Bash":'))
    gate("in_progress", module=mutant)
    assert run_gate(PUSH + " origin main", "PowerShell", module=mutant) is None
    gate("in_progress")
    assert run_gate(PUSH + " origin main", "PowerShell") is not None
