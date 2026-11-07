"""T277 — `block-dangerous-git.py`, the Python twin of the git-guardrails `.sh` hook.

The `.sh` is the reference: the twin must give the same exit code (and the same BLOCKED text) for
the same hook input. AC 1 (table), 2 (parity with the `.sh`, POSIX only), 3 (bad input),
4-5 (the skill names both files and a Windows registration the converter accepts).

Run with: python3 -m pytest tests/test_git_guardrails_py.py -q
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "git-guardrails-claude-code" / "scripts"
PY_HOOK = SCRIPTS / "block-dangerous-git.py"
SH_HOOK = SCRIPTS / "block-dangerous-git.sh"
SKILL = REPO / "skills" / "git-guardrails-claude-code" / "SKILL.md"

sys.path.insert(0, str(REPO / "lib"))
import windows_hooks  # noqa: E402

# (command, blocked). The `.sh` decides: `grep -E` of nine patterns on the raw command text, so a
# pattern inside quotes, a heredoc or a longer word is blocked too, and a spelling the patterns do
# not name (two spaces, `git -C dir push`, `checkout -- .`) is allowed.
TABLE = [
    # blocked
    ("git push", True),
    ("git push origin main", True),
    ("git push --force origin main", True),
    ("git push --force-with-lease", True),
    ("git push -u origin feat/x", True),
    ("cd sub && git push", True),
    ("echo ok; git push", True),
    ('echo "git push"', True),                      # quoted text is blocked too
    ("git commit -F - <<EOF\ngit push\nEOF", True),  # so is a heredoc body
    ("git pushx", True),                           # prefix match, no word boundary
    ("git log --grep='git push'", True),
    ("echo push --force", True),                   # the bare `push --force` pattern
    ("git reset --hard", True),
    ("git reset --hard HEAD~1", True),
    ("somegit reset --hard", True),
    ("echo reset --hard", True),                   # the bare `reset --hard` pattern
    ("git clean -fd", True),
    ("git clean -fdx", True),
    ("git clean -f", True),
    ("git clean -f src/", True),
    ("git branch -D old", True),
    ("git checkout .", True),
    ("git checkout .gitignore", True),             # `git checkout \.` is a prefix match
    ("git restore .", True),
    ("git restore .claude", True),
    # allowed
    ("git status", False),
    ("git log --oneline", False),
    ("git diff HEAD", False),
    ("git commit -m 'fix it'", False),
    ("git add -A", False),
    ("git stash", False),
    ("git branch -d merged", False),               # lower-case -d is not -D
    ("git clean -n", False),
    ("git reset --soft HEAD~1", False),
    ("git reset HEAD file", False),
    ("git checkout main", False),
    ("git checkout -- .", False),                  # `-- .` is not `checkout .`
    ("git restore --staged .", False),
    ("git  push", False),                          # two spaces: the pattern has one
    ("git -C dir push", False),                    # `-C dir` splits the words
    ("GIT PUSH", False),                           # case-sensitive
    ("git pull", False),
    ("ls -la", False),
    ("", False),
]

BAD_INPUT = [
    ("empty stdin", b""),
    ("whitespace only", b"  \n"),
    ("not JSON", b"this is not json"),
    ("truncated JSON", b'{"tool_input":{"command":"git pu'),
    ("empty object", b"{}"),
    ("tool_input missing", b'{"other":1}'),
    ("tool_input empty", b'{"tool_input":{}}'),
    ("tool_input null", b'{"tool_input":null}'),
    ("tool_input a string", b'{"tool_input":"git push"}'),
    ("top level array", b"[]"),
    ("top level string", b'"git push"'),
    ("command null", b'{"tool_input":{"command":null}}'),
    ("command a number", b'{"tool_input":{"command":123}}'),
    ("invalid UTF-8", b'\xff\xfe{"tool_input":{"command":"git status"}}'),
]


def payload(command):
    return json.dumps({"tool_input": {"command": command}}).encode("utf-8")


def run(argv, stdin):
    return subprocess.run(argv, input=stdin, capture_output=True, timeout=30)


def run_py(stdin):
    return run([sys.executable, "-I", str(PY_HOOK)], stdin)


def run_sh(stdin):
    return run(["bash", str(SH_HOOK)], stdin)


def needs_posix_tools():
    if shutil.which("bash") is None or shutil.which("jq") is None:
        pytest.skip("the .sh hook needs bash and jq on PATH")


# --- AC 1: the table -------------------------------------------------------------------------

def test_the_table_is_wide_enough():
    assert len(TABLE) >= 20
    assert {b for _, b in TABLE} == {True, False}


@pytest.mark.parametrize("command,blocked", TABLE, ids=[c.replace("\n", "\\n") or "<empty>" for c, _ in TABLE])
def test_py_hook_decides_like_the_table(command, blocked):
    result = run_py(payload(command))
    assert result.returncode == (2 if blocked else 0), result.stderr.decode()
    assert b"Traceback" not in result.stderr
    if blocked:
        text = result.stderr.decode("utf-8")
        assert text.startswith("BLOCKED: '%s' matches dangerous pattern '" % command), text
        assert text.endswith("'. The user has prevented you from doing this.\n"), text
    else:
        assert result.stderr == b"" and result.stdout == b""


def test_the_message_names_the_first_matching_pattern():
    text = run_py(payload("git push --force")).stderr.decode()
    assert "dangerous pattern 'git push'." in text  # `git push` is listed before `push --force`
    text = run_py(payload("git checkout .")).stderr.decode()
    assert r"dangerous pattern 'git checkout \.'." in text


# --- AC 2: parity with the .sh ---------------------------------------------------------------

@pytest.mark.posix_only("runs the .sh hook, which needs bash and jq; a Windows runner has no jq")
@pytest.mark.parametrize("command,blocked", TABLE, ids=[c.replace("\n", "\\n") or "<empty>" for c, _ in TABLE])
def test_py_and_sh_agree_on_exit_code_and_message(command, blocked):
    needs_posix_tools()
    sh, py = run_sh(payload(command)), run_py(payload(command))
    assert sh.returncode == (2 if blocked else 0), "the table disagrees with the .sh: %r" % command
    assert (py.returncode, py.stderr) == (sh.returncode, sh.stderr)


@pytest.mark.posix_only("runs the .sh hook, which needs bash and jq; a Windows runner has no jq")
@pytest.mark.parametrize("name,raw", BAD_INPUT, ids=[n for n, _ in BAD_INPUT])
def test_py_and_sh_agree_on_bad_input(name, raw):
    needs_posix_tools()
    assert run_py(raw).returncode == run_sh(raw).returncode == 0


@pytest.mark.posix_only("runs the .sh hook, which needs bash and jq; a Windows runner has no jq")
def test_py_and_sh_agree_on_a_non_string_command():
    """`jq -r` prints a list as JSON text, so the `.sh` blocks `["git push"]`; the twin does too."""
    needs_posix_tools()
    raw = json.dumps({"tool_input": {"command": ["git push"]}}).encode()
    assert run_py(raw).returncode == run_sh(raw).returncode == 2


# --- AC 3: bad input -------------------------------------------------------------------------

@pytest.mark.parametrize("name,raw", BAD_INPUT, ids=[n for n, _ in BAD_INPUT])
def test_bad_input_never_blocks_and_never_shows_a_traceback(name, raw):
    result = run_py(raw)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert b"Traceback" not in result.stderr
    assert result.stdout == b""


def test_a_command_with_non_ascii_text_is_read_as_utf8():
    result = run_py(payload("git push origin né-branch"))
    assert result.returncode == 2
    assert "né-branch" in result.stderr.decode("utf-8")


# --- The file ----------------------------------------------------------------------------------

def test_the_py_file_is_stdlib_only_and_lf():
    text = PY_HOOK.read_bytes()
    assert b"\r\n" not in text
    imports = set(re.findall(rb"^\s*(?:import|from)\s+(\w+)", text, re.M))
    assert imports <= {b"json", b"sys", b"re"}, imports
    attr = subprocess.run(["git", "check-attr", "eol", "--", str(PY_HOOK.relative_to(REPO))],
                          cwd=REPO, capture_output=True, text=True, check=True).stdout
    assert attr.strip().endswith("eol: lf"), attr


# --- AC 4, 5: the skill ----------------------------------------------------------------------

def skill_text():
    return SKILL.read_text(encoding="utf-8")


def skill_json_blocks():
    return [json.loads(m) for m in re.findall(r"```json\n(.*?)\n```", skill_text(), re.S)]


def windows_hook_entries():
    found = []
    for block in skill_json_blocks():
        for group in block.get("hooks", {}).get("PreToolUse", []):
            found += [h for h in group["hooks"] if "args" in h]
    return found


def test_skill_names_both_files_and_both_ways_to_register():
    text = skill_text()
    assert "scripts/block-dangerous-git.sh" in text
    assert "scripts/block-dangerous-git.py" in text
    assert "Windows" in text
    assert '"command": "py"' in text and '"-3"' in text


def test_skill_stays_under_the_codex_cap_with_room_to_spare():
    # lib/harness-fetch.sh skips a Codex skill body over 8192 bytes
    assert len(SKILL.read_bytes()) < 6000


def test_the_windows_registration_is_in_the_converters_exec_form():
    entries = windows_hook_entries()
    assert len(entries) == 1, entries
    hook = entries[0]
    assert hook["type"] == "command" and hook["command"] == "py"
    assert hook["args"][0] == "-3" and len(hook["args"]) == 2
    assert hook["args"][1].endswith("/.claude/hooks/block-dangerous-git.py")
    # the converter leaves an exec-form entry as it is ...
    settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [hook]}]}}
    assert windows_hooks.to_windows_settings(settings, "py") == settings
    # ... and the entry is what it writes for the POSIX form of the same hook
    posix = {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/block-dangerous-git.py'}
    assert windows_hooks.convert_hook(posix, "py") == hook


def test_the_skill_check_can_fail():
    """Mutation control: an entry that is not exec form, or a wrong path, is not accepted."""
    hook = windows_hook_entries()[0]
    wrong = dict(hook, args=["-3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/other.py"])
    posix = {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/block-dangerous-git.py'}
    assert windows_hooks.convert_hook(posix, "py") != wrong
    assert windows_hooks.convert_hook(posix, "python") != hook  # no "-3" with launcher "python"


def test_the_windows_registration_matches_the_powershell_tool_too():
    """Review finding (P1): on Windows Claude Code can run git through the PowerShell tool. The kit's own
    hooks use "Bash|PowerShell" (.claude/settings.json); a "Bash"-only matcher lets a PowerShell
    `git push` past the guardrail."""
    import re
    text = SKILL.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)```", text, re.S)
    win = [b for b in blocks if "block-dangerous-git.py" in b]
    assert len(win) == 1, "expected one Windows JSON block"
    assert '"matcher": "Bash|PowerShell"' in win[0]
