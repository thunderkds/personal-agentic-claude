#!/usr/bin/env python3
"""T044 defect C — `pre_bash_block_unsafe_merge.py:trace_shows_verification`
accepted any non-error trace record whose `summary` merely *contained*
`pytest|npm test|jest|go test|cargo test|verify`.

The gate exists specifically to close the "the agent claims it ran tests" gap.
A substring match cannot close it: a Supervisor *inspection* command that greps
for the word `pytest` satisfies it, so the gate passes a merge on which no test
ever ran. Two such records are real and are used verbatim as fixtures below —
they are the records that were observed satisfying the live gate on T043.

The distinction the gate must draw is **invoked** vs **mentioned**:
a runner token at a command boundary is an invocation; the same token inside a
quoted string, or as a `grep` argument, is data.

Run with: python3 -m pytest .claude/hooks/tests/test_merge_gate_evidence.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import types

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")


def load_hook_module(path, name):
    """Load a hook as a module *without* running its bottom-of-file `main()`.

    Every hook in this directory ends in a bare `main()` call so the harness can
    invoke it as a script; a plain `importlib` load would therefore execute
    `main()` at import time and block forever on `json.load(sys.stdin)`.
    Stripping only that trailing call keeps the module's real source — no
    duplicated regex, no re-derived pattern.
    """
    source = open(path).read()
    marker = "\nmain()"
    assert marker in source, f"{path} no longer ends in a bare main() call"
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(source.replace(marker, "\n"), path, "exec"), module.__dict__)
    return module


merge_gate = load_hook_module(HOOK_PATH, "pre_bash_block_unsafe_merge")

FOREIGN_CWD = tempfile.gettempdir()

# ---------------------------------------------------------------------------
# Fixtures — the two false-positive records, copied byte-for-byte from
# memory/event-trace/T043.jsonl (lines 19 and 21). Synthetic strings would be a
# weaker oracle than the actual data that fooled the gate.
# ---------------------------------------------------------------------------

REAL_FALSE_POSITIVE_GREP = (
    '{"timestamp": "2026-07-23T04:30:23.937548+00:00", "tool_name": "Bash", '
    '"summary": "{\\"command\\": \\"ls /home/hungnguyenhuu/workspace/pets/'
    'personal-agentic-claude/memory/event-trace/ | tail -8; echo \\\\\\"--- T043 '
    'trace: pytest records? ---\\\\\\"; grep -c \\\\\\"pytest\\\\\\" /home/'
    'hungnguyenhuu/workspace/pets/personal-agentic-claude/memory/event-trace/'
    'T043.jsonl 2>/dev/null || echo \\\\\\"no T043.jsonl in t", '
    '"is_error": false}'
)

REAL_FALSE_POSITIVE_REGEX_LITERAL = (
    '{"timestamp": "2026-07-23T04:30:38.213656+00:00", "tool_name": "Bash", '
    '"summary": "{\\"command\\": \\"python3 -c \\\\\\"\\\\nimport json,re\\\\n'
    "p='/home/hungnguyenhuu/workspace/pets/personal-agentic-claude/memory/"
    "event-trace/T043.jsonl'\\\\npat=re.compile(r'\\\\\\\\b(pytest|npm\\\\\\\\s+test|"
    "npm\\\\\\\\s+run\\\\\\\\s+test|yarn\\\\\\\\s+test|jest|go\\\\\\\\s+test|"
    "cargo\\\\\\\\s+test|verify)\\\\\\\\b',re.I)\\\\nrows=[json.loads(l) for l in "
    'open(p) if l", "is_error": false}'
)


def _record(command, tool_name="Bash", is_error=False):
    """Build a trace record the way post_tool_trace.py does: `summary` is the
    JSON-serialized tool_input, truncated to 300 chars."""
    summary = json.dumps({"command": command})[:300]
    return json.dumps(
        {
            "timestamp": "2026-07-30T00:00:00+00:00",
            "tool_name": tool_name,
            "summary": summary,
            "is_error": is_error,
        }
    )


class TraceSandbox:
    """Points the hook module's TRACE_DIR at a throwaway directory so the real
    repo's memory/event-trace/ is never read or written."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="t044_trace_")
        self._saved = merge_gate.TRACE_DIR
        merge_gate.TRACE_DIR = self.dir

    def write(self, task_id, lines):
        with open(os.path.join(self.dir, f"{task_id}.jsonl"), "w") as f:
            for line in lines:
                f.write(line + "\n")

    def write_raw(self, task_id, text):
        with open(os.path.join(self.dir, f"{task_id}.jsonl"), "w") as f:
            f.write(text)

    def cleanup(self):
        merge_gate.TRACE_DIR = self._saved
        import shutil

        shutil.rmtree(self.dir, ignore_errors=True)


def _gate(lines, task_id="T900"):
    sandbox = TraceSandbox()
    try:
        sandbox.write(task_id, lines)
        return merge_gate.trace_shows_verification(task_id)
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# AC5 / SC2 — the core proof: the two REAL records are rejected
# ---------------------------------------------------------------------------

def test_real_grep_inspection_record_is_rejected():
    """`ls … | tail -8; echo "… pytest records? …"; grep -c "pytest" …` — the
    word `pytest` is a grep argument and echo text, not an invocation."""
    assert _gate([REAL_FALSE_POSITIVE_GREP]) is False


def test_real_regex_literal_record_is_rejected():
    """`python3 -c "… pat=re.compile(r'\\b(pytest|npm\\s+test|…|jest|…)…')"` —
    every runner token lives inside a quoted regex literal."""
    assert _gate([REAL_FALSE_POSITIVE_REGEX_LITERAL]) is False


def test_both_real_records_together_are_rejected():
    """The exact state the live T043 trace was in: these were the *only* two
    qualifying records, and the gate would have passed the merge."""
    assert _gate([REAL_FALSE_POSITIVE_GREP, REAL_FALSE_POSITIVE_REGEX_LITERAL]) is False


# ---------------------------------------------------------------------------
# AC4 — mentioned-not-invoked, minimal synthetic cases
# ---------------------------------------------------------------------------

def test_runner_token_inside_a_quoted_string_is_rejected():
    assert _gate([_record('echo "remember to run pytest"')]) is False


def test_runner_token_as_a_grep_pattern_is_rejected():
    assert _gate([_record("grep -rn 'npm test' docs/")]) is False


def test_runner_token_inside_a_longer_word_is_rejected():
    assert _gate([_record("cat notes-about-pytest-usage.md")]) is False


def test_reading_a_file_named_after_a_runner_is_rejected():
    """Not a Bash record at all — a Read cannot invoke anything."""
    assert _gate([_record("irrelevant", tool_name="Read")]) is False


def test_verification_written_as_prose_is_rejected():
    assert _gate([_record("echo 'tests verify the acceptance criteria'")]) is False


def _truncated_record_with_description(command, description):
    """A record long enough that post_tool_trace.py's 300-char cut lands inside
    the `description` value, so `summary` is no longer parseable JSON and
    extract_command() must fall back to its regex path."""
    summary = json.dumps({"command": command, "description": description})[:300]
    try:
        json.loads(summary)
    except Exception:
        pass
    else:  # pragma: no cover - the fixture must actually be truncated
        raise AssertionError("fixture is not truncated; the fallback is untested")
    return json.dumps(
        {
            "timestamp": "2026-07-30T00:00:00+00:00",
            "tool_name": "Bash",
            "summary": summary,
            "is_error": False,
        }
    )


def test_runner_named_in_the_description_of_a_truncated_record_is_rejected():
    """A `description` is agent-authored prose — a claim, never an invocation.

    When the record is truncated the summary stops being valid JSON, so
    extract_command falls back to a regex. That fallback must stop at the
    command value's closing quote; otherwise a sibling field leaks in and a
    separator inside the prose ("...records; pytest was run") promotes the
    next word to a command head — reinstating defect C through a side door.
    """
    record = _truncated_record_with_description(
        "grep -rn evidence memory/event-trace/T043.jsonl " + "x" * 100,
        "inspect the trace records; pytest was already run earlier " + "y" * 150,
    )
    assert _gate([record]) is False


def test_truncated_record_still_reads_its_own_command():
    """The stop-at-closing-quote fix must not blind the fallback to a genuine
    invocation that is itself the thing being truncated."""
    record = _truncated_record_with_description(
        "python3 -m pytest .claude/hooks/tests/ -q " + "-x " * 40,
        "run the suite " + "z" * 200,
    )
    assert _gate([record]) is True


# ---------------------------------------------------------------------------
# AC6 — no false-negative regression: real invocations are still accepted
# ---------------------------------------------------------------------------

def test_pytest_module_invocation_is_accepted():
    assert _gate([_record("python3 -m pytest .claude/hooks/tests/ -q")]) is True


def test_bare_pytest_invocation_is_accepted():
    assert _gate([_record("pytest -q")]) is True


def test_smoke_install_script_is_accepted():
    assert _gate([_record("bash scripts/smoke-install.sh")]) is True


def test_npm_test_is_accepted():
    assert _gate([_record("npm test")]) is True


def test_npm_run_test_is_accepted():
    assert _gate([_record("npm run test -- --coverage")]) is True


def test_jest_invocation_is_accepted():
    assert _gate([_record("npx jest --ci")]) is True


def test_go_and_cargo_test_are_accepted():
    assert _gate([_record("go test ./...")]) is True
    assert _gate([_record("cargo test --all")]) is True


def test_the_task_guide_verification_command_is_accepted():
    """The exact command in TASK_GUIDE_T044.md — env-var prefix, `-m pytest`,
    `&&`-chained smoke script."""
    command = (
        "CLAUDE_ACTIVE_TASK=T044 python3 -m pytest .claude/hooks/tests/ -q "
        "&& bash scripts/smoke-install.sh"
    )
    assert _gate([_record(command)]) is True


def test_runner_after_a_shell_separator_is_accepted():
    assert _gate([_record("cd /repo && pytest tests/")]) is True


def test_verify_script_invocation_is_accepted():
    assert _gate([_record("./scripts/verify.sh")]) is True


# ---------------------------------------------------------------------------
# AC4 — an errored invocation is not evidence of verification
# ---------------------------------------------------------------------------

def test_errored_test_run_is_rejected():
    assert _gate([_record("python3 -m pytest -q", is_error=True)]) is False


def test_a_real_invocation_among_noise_is_accepted():
    assert _gate(
        [
            REAL_FALSE_POSITIVE_GREP,
            _record("python3 -m pytest -q", is_error=True),
            _record("python3 -m pytest .claude/hooks/tests/ -q"),
        ]
    ) is True


# ---------------------------------------------------------------------------
# AC8 — fail closed on missing / empty / malformed trace
# ---------------------------------------------------------------------------

def test_missing_trace_file_fails_closed():
    sandbox = TraceSandbox()
    try:
        assert merge_gate.trace_shows_verification("T901") is False
    finally:
        sandbox.cleanup()


def test_empty_trace_file_fails_closed():
    assert _gate([]) is False


def test_malformed_jsonl_fails_closed_without_raising():
    sandbox = TraceSandbox()
    try:
        sandbox.write_raw("T902", "not json at all\n{broken\n")
        assert merge_gate.trace_shows_verification("T902") is False
    finally:
        sandbox.cleanup()


def test_malformed_lines_do_not_hide_a_real_record():
    sandbox = TraceSandbox()
    try:
        sandbox.write_raw(
            "T903",
            "not json\n" + _record("python3 -m pytest -q") + "\n",
        )
        assert merge_gate.trace_shows_verification("T903") is True
    finally:
        sandbox.cleanup()


def test_record_with_non_string_summary_fails_closed():
    sandbox = TraceSandbox()
    try:
        sandbox.write_raw("T904", json.dumps({"tool_name": "Bash", "summary": None}) + "\n")
        assert merge_gate.trace_shows_verification("T904") is False
    finally:
        sandbox.cleanup()


# ---------------------------------------------------------------------------
# AC9 — fail open on malformed stdin (this hook fires on every Bash call)
# ---------------------------------------------------------------------------

def _run_hook(payload):
    return subprocess.run(
        [sys.executable, HOOK_PATH],
        input=payload,
        capture_output=True,
        text=True,
        cwd=FOREIGN_CWD,
    )


def test_malformed_stdin_exits_zero_silently():
    for payload in ("", "not json", "[]", "null", '{"tool_input": "a string"}'):
        result = _run_hook(payload)
        assert result.returncode == 0, (payload, result.stderr)
        assert "Traceback" not in result.stderr, (payload, result.stderr)


def test_non_bash_tool_is_ignored():
    result = _run_hook(json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}}))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""
