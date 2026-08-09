#!/usr/bin/env python3
"""
PreToolUse hook — fires before every Bash tool call.

Blocks git push/merge/rebase commands if:
  1. Any task in PROJECT_KANBAN.md is still In Progress or Ready for Review
  2. No Stage 5 verify evidence is found in any pending task guide

This enforces the pipeline gate: Stage 4 review + Stage 5 verify must
complete before code ships.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
TASKS_DIR = os.path.join(ROOT, "tasks")
TRACE_DIR = os.path.join(ROOT, "memory", "event-trace")

# The Evidence table may live in the guide or in the sibling TASK_REVIEW file
# (T064). Imported off __file__, like post_tool_trace.py does for task_context.
#
# This gate must fail **closed**, and an unguarded import does NOT achieve that
# (Stage 4 finding). This hook signals a block by printing a `decision: block`
# JSON object on stdout and exiting 0; a bare ImportError exits 1 with *empty*
# stdout, which the harness reads as a non-blocking hook error and the merge
# proceeds — the precise direction AC7 exists to prevent. So the import is
# guarded and its failure is turned into an explicit block.
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from guide_sections import read_guide_section  # noqa: E402
except Exception as exc:  # pragma: no cover - exercised via subprocess test
    print(json.dumps({
        "decision": "block",
        "reason": (
            "[hook:pre_bash] Evidence resolver unavailable "
            f"({type(exc).__name__}: {exc}) — cannot confirm Stage 5 verify "
            "evidence for any task, so this push/merge is blocked. Restore "
            ".claude/hooks/lib/guide_sections.py."
        ),
    }))
    sys.exit(0)

BLOCKED_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bgit\s+merge\b",
    r"\bgit\s+rebase\b",
]

# --- Evidence matching: "invoked" vs "merely mentioned" (T044 defect C) ------
#
# This used to be a single `\b(pytest|npm test|jest|…|verify)\b` substring search
# over the trace record's `summary`. That made the gate satisfiable by a *claim*:
# a Supervisor inspection command such as `grep -c "pytest" …T043.jsonl`, or a
# `python3 -c "…re.compile(r'\b(pytest|jest|verify)\b')…"`, both qualified — and
# on T043 those were the only two qualifying records, so the gate would have
# passed a merge on which no test had ever run. A check that has never rejected
# anything is not a check.
#
# The rule now is structural: a runner token counts only where a shell would
# actually *execute* it — at the head of a command, after stripping leading
# environment assignments and benign wrappers. Two consequences follow:
#   * A token inside a quoted string is data (an `echo` argument, a `grep`
#     pattern, a regex literal), so quoted spans are removed before matching.
#   * Only a `Bash` record can invoke anything; a `Read` of a file named after a
#     test runner is not evidence.
#
# Residual limit, stated plainly: this still trusts that a recorded command
# *ran*. `is_error: false` supports that but does not prove it, and the trace
# records the command, not its exit status of the tests themselves. The goal is
# to close the gap between "a string looked like a test" and "a test command was
# invoked" — not certainty this design cannot deliver.
#
# Deliberately not a shell parser (Simplicity First). Boundary anchoring is
# enough to reject both real false-positive records while accepting every
# genuine invocation the project uses.
#
# Two known limits, both erring toward fail-closed:
#   * An invocation wrapped entirely in quotes (`bash -c "python3 -m pytest"`)
#     is treated as a mention and rejected. Run the runner directly, or export
#     CLAUDE_ACTIVE_TASK and run it unwrapped.
#   * The gate proves a runner was *invoked*, not that a test suite *passed*
#     (`pytest --version` would qualify). `is_error: false` excludes a failing
#     run, which is the strongest signal the trace carries.

# Quoted spans are data, not commands. Replaced with a space, not deleted, so
# removal cannot glue two separate words into a spurious invocation.
QUOTED_SPAN_PATTERN = re.compile(r"\"[^\"]*\"|'[^']*'")

# Where a shell starts a new command.
COMMAND_SEPARATOR_PATTERN = re.compile(r"[;&|\n]+|\$\(|`")

# `CLAUDE_ACTIVE_TASK=T044 python3 -m pytest …` — the assignment is not the command.
ENV_ASSIGNMENT_PREFIX = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)+")

# Wrappers that pass through to the real command.
BENIGN_COMMAND_PREFIX = re.compile(
    r"^(?:(?:sudo|env|time|nohup|npx|uv\s+run|poetry\s+run|pipenv\s+run|"
    r"pnpm\s+exec|yarn\s+exec)\s+)+",
    re.IGNORECASE,
)

# Anchored at the head of a command — `match`, never `search`.
TEST_INVOCATION_PATTERN = re.compile(
    r"^(?:"
    r"(?:python3?|py)\s+-m\s+(?:pytest|unittest)\b"
    r"|pytest\b"
    r"|jest\b"
    r"|tox\b"
    r"|(?:npm|yarn|pnpm)\s+(?:run\s+)?test\b"
    r"|go\s+test\b"
    r"|cargo\s+test\b"
    r"|(?:bash|sh|zsh)\s+\S*(?:test|verify|smoke)\S*"
    r"|\.{0,2}/\S*(?:test|verify|smoke)\S*"
    r")",
    re.IGNORECASE,
)


def strip_command_prefixes(candidate):
    """Peel leading env assignments and benign wrappers until nothing changes."""
    while True:
        shorter = BENIGN_COMMAND_PREFIX.sub("", ENV_ASSIGNMENT_PREFIX.sub("", candidate))
        if shorter == candidate:
            return candidate
        candidate = shorter


# A trace record's `summary` is the JSON-serialized `tool_input`, truncated by
# post_tool_trace.py to 300 chars — so the command arrives JSON-escaped, and
# often as invalid JSON. Both layers must be peeled before shell quoting means
# anything: `{"command": "echo \"pytest\""}` is a quoted mention, not a run.
COMMAND_FIELD_PATTERN = re.compile(r'"command"\s*:\s*"')
JSON_ESCAPE_PATTERN = re.compile(r"\\(.)")
JSON_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f"}

# The command value's body, stopping at its first *unescaped* closing quote.
# Without this bound the fallback swallowed every sibling field, and a
# `description` is agent-authored prose — a separator inside it ("...records;
# pytest was run") would promote the next word to a command head, reinstating
# defect C through a side door.
COMMAND_VALUE_BODY_PATTERN = re.compile(r'(?:[^"\\]|\\.)*')


def extract_command(summary):
    """Recover the Bash command from a trace record's `summary`, or None."""
    if not isinstance(summary, str):
        return None
    try:
        payload = json.loads(summary)
    except Exception:
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("command"), str):
        return payload["command"]
    match = COMMAND_FIELD_PATTERN.search(summary)
    if not match:
        return None
    # Truncated record: take only the command value's own body, then unescape it
    # in one left-to-right pass, so a literal `\\` can never be re-read as the
    # start of another escape.
    fragment = COMMAND_VALUE_BODY_PATTERN.match(summary, match.end()).group(0)
    return JSON_ESCAPE_PATTERN.sub(
        lambda m: JSON_ESCAPES.get(m.group(1), m.group(1)), fragment
    )


def invokes_test_runner(command):
    """True only if `command` contains a test-runner invocation at a command
    boundary — not merely a mention of one inside a quoted string or argument."""
    if not isinstance(command, str):
        return False
    unquoted = QUOTED_SPAN_PATTERN.sub(" ", command)
    for part in COMMAND_SEPARATOR_PATTERN.split(unquoted):
        if TEST_INVOCATION_PATTERN.match(strip_command_prefixes(part.strip())):
            return True
    return False


def trace_shows_verification(task_id):
    """Check memory/event-trace/<task>.jsonl for a real, non-error `Bash` call
    that *invoked* a test runner — not text in the task guide claiming it
    passed, and not a command that merely mentions a runner's name.
    Missing/empty/malformed trace = not verified (fail closed)."""
    trace_path = os.path.join(TRACE_DIR, f"{task_id}.jsonl")
    if not os.path.exists(trace_path):
        return False
    try:
        with open(trace_path) as f:
            for line in f:
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                if not isinstance(record, dict):
                    continue
                if record.get("is_error"):
                    continue
                if record.get("tool_name") != "Bash":
                    continue
                if invokes_test_runner(extract_command(record.get("summary"))):
                    return True
    except Exception:
        return False
    return False

# The T026 two-bug fix, byte-for-byte: the Check cell must be the literal word
# `verify` immediately before its `|`, AND the word "pass" must appear in the
# *Notes* column, not only the Result column. T064 changed **where** this text
# is read from; it must never change **what** is matched.
# Same three-part shape as before T068 (Check cell literally `verify`, Result
# and Notes are the two pipe-delimited cells that follow, "pass" required in
# the third/Notes cell — the T026 property) but Result/Notes are now captured
# separately so an *unchecked* box can be told apart from a filled one.
VERIFY_ROW_PATTERN = re.compile(
    r"verify\s*\|(?P<result>[^|\n]*)\|(?P<notes>[^|\n]*pass[^|\n]*)",
    re.IGNORECASE,
)

# The template's own placeholder guidance text writes "pass" as one of the
# unchecked options: `☐ pass / ☐ fail / ☐ N/A`. That is guidance, not a filled
# answer, so a literal unchecked "☐ pass" in the Result cell disqualifies the
# row — but only that exact combination. A legitimately filled
# `☑ pass / ☐ N/A` row (the shape occurs in tasks/TASK_GUIDE_T063.md) must NOT
# trip this: the guard checks for ☐ directly attached to "pass", not for ☐
# appearing anywhere in the cell.
UNCHECKED_PASS_PATTERN = re.compile(r"☐\s*pass\b", re.IGNORECASE)


def has_filled_verify_row(task_id, tasks_dir=None):
    """True only when the task's Evidence table — wherever it resolves, guide
    first then `TASK_REVIEW_Txxx.md` — carries a filled `verify` row.

    **Fails closed.** A missing guide, a missing review file, an unreadable
    one, an absent Evidence section, an unfilled row, or a row still carrying
    the template's unchecked `☐ pass` placeholder all return False. This is
    the one place in T064 where a wrong answer is silent and repo-wide: if
    "review file missing" ever became anything other than "no evidence", the
    merge gate would stop gating on every task at once.
    """
    section = read_guide_section(task_id, "Evidence", tasks_dir or TASKS_DIR)
    if not section:
        return False
    for match in VERIFY_ROW_PATTERN.finditer(section):
        if not UNCHECKED_PASS_PATTERN.search(match.group("result")):
            return True
    return False


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Fail open on any payload shape this hook doesn't understand — it runs
    # before every Bash call, so a traceback here breaks all work.
    if not isinstance(event, dict) or event.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        sys.exit(0)
    command = tool_input.get("command", "")
    if not isinstance(command, str):
        sys.exit(0)

    if not any(re.search(p, command) for p in BLOCKED_PATTERNS):
        sys.exit(0)

    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        sys.exit(0)

    def tasks_in_section(section_title):
        m = re.search(
            rf"### {re.escape(section_title)}\n(.*?)(?=^###|\Z)", kanban,
            re.DOTALL | re.MULTILINE,
        )
        if not m:
            return []
        block = m.group(1).strip()
        return [re.search(r"\*\*(T\d+)\*\*", l).group(1)
                for l in block.splitlines()
                if l.strip().startswith("- ") and re.search(r"\*\*(T\d+)\*\*", l)]

    in_progress = tasks_in_section("In Progress")
    ready_review = tasks_in_section("Ready for Review")

    blockers = []

    if in_progress:
        blockers.append(f"Tasks still In Progress: {', '.join(in_progress)}")

    if ready_review:
        # Check each for verify evidence in their task guide
        unverified = []
        for tid in ready_review:
            # Look for a filled verify row in the Evidence table — in the guide,
            # or in the sibling TASK_REVIEW file it may have moved to (T064) —
            # AND a matching real tool call in the event trace. The text claim
            # alone is not trusted (the model can lie about success). Every
            # absence resolves to False, so this stays fail-closed.
            has_evidence_row = has_filled_verify_row(tid)
            has_trace = trace_shows_verification(tid)
            if not has_evidence_row or not has_trace:
                unverified.append(tid if has_evidence_row else f"{tid} (no evidence row)")
                if has_evidence_row and not has_trace:
                    unverified[-1] = f"{tid} (evidence row present but no verified tool call in memory/event-trace/{tid}.jsonl)"

        if unverified:
            blockers.append(
                f"Tasks in Ready for Review missing Stage 5 verify evidence: "
                f"{', '.join(unverified)}"
            )

    if blockers:
        result = {
            "decision": "block",
            "reason": (
                "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • "
                + "\n  • ".join(blockers)
                + "\nComplete Stage 4 review and Stage 5 verify first."
                + "\n  Note: a Bash command is attributed to a task only via"
                + " CLAUDE_ACTIVE_TASK — run the task's verification command as"
                + " `CLAUDE_ACTIVE_TASK=Txxx <command>` or no trace record is"
                + " filed under it."
            )
        }
        print(json.dumps(result))

main()
