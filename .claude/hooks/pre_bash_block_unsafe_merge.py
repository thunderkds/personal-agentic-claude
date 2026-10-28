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
import subprocess
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
#
# `shell_data.strip_heredoc_bodies` (T095 defect C) and `strip_quoted_spans`
# (T099) are imported in the same guarded block for the same reason, though they
# fail in the opposite direction: losing them would make the gate classify
# heredoc bodies and quoted arguments as commands again (over-blocking, not
# under-blocking). Blocking on their absence keeps one rule here — an
# unavailable resolver is a block — rather than two.
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from guide_sections import read_guide_section  # noqa: E402
    from shell_data import strip_heredoc_bodies, strip_quoted_spans  # noqa: E402
    from board.config import load_config, task_id_pattern  # noqa: E402
    from board.moments import (  # noqa: E402
        board_mode, my_blocking_tasks, my_review_tasks, pull_cache)
    from verify_record import (  # noqa: E402
        AUTO_CHECKED_TAG, AUTO_ROW_TAG, auto_row_confirmed)
except Exception as exc:  # pragma: no cover - exercised via subprocess test
    print(json.dumps({
        "decision": "block",
        "reason": (
            "[hook:pre_bash] Evidence resolver unavailable "
            f"({type(exc).__name__}: {exc}) — cannot confirm Stage 5 verify "
            "evidence for any task, so this push/merge is blocked. Restore "
            ".claude/hooks/lib/guide_sections.py, "
            ".claude/hooks/lib/shell_data.py, .claude/hooks/lib/board/config.py, "
            ".claude/hooks/lib/board/moments.py and .claude/hooks/lib/verify_record.py."
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
#     is treated as a mention and rejected. Run the runner directly, unwrapped.
#     (Pre-T095 this said "or export CLAUDE_ACTIVE_TASK and run it unwrapped",
#     which carried the same false premise as the block message below: T047
#     measured that a hook is a *sibling* process of the tool call and never
#     inherits a `Bash` call's subshell, so an in-session `export` reaches
#     nothing. Attribution is a separate concern from this rule anyway — see
#     ATTRIBUTION_REMEDY.)
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


# --- Where the Evidence table can live (T095 defect A) ----------------------
#
# `TASKS_DIR` is always the **main checkout's** `tasks/`: `ROOT` derives from
# this file's own location and `settings.json` invokes every hook as
# `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/...`. But since T064 the Evidence
# table lives in `tasks/TASK_REVIEW_Txxx.md`, which the agent creates **in its
# worktree, on its task branch** — Stage 3 is worktree-isolated by mandate
# (`AGENTS.md`), so until the branch merges that file does not exist in the main
# checkout at all. Every worktree-isolated task therefore read as
# `(no evidence row)`; three consecutive sessions paid for it by hand-landing the
# review file on the integration branch before merging.
#
# The worktree list is an *additional place to look*, never a reason to skip the
# check. So every failure of the enumeration — git absent, non-zero exit, a
# timeout, unparsable output — degrades to "main checkout only", which is exactly
# the pre-T095 behaviour and still fails closed. It can never degrade to "allow".
#
# Resolving the file from the *branch* via `git show` was considered and rejected
# at grill: this gate runs BEFORE a push, when the commit may not exist in the
# main checkout's object store at all.
GIT_WORKTREE_TIMEOUT_S = 5


def worktree_tasks_dirs():
    """Each live worktree's `tasks/` directory, main checkout excluded.

    Never raises and never blocks for long: returns `[]` on any failure, and the
    caller still has the main checkout to search.
    """
    try:
        completed = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=GIT_WORKTREE_TIMEOUT_S,
        )
        if completed.returncode != 0:
            return []
        dirs = []
        for line in completed.stdout.splitlines():
            if not line.startswith("worktree "):
                continue
            path = line[len("worktree "):].strip()
            if not path or os.path.abspath(path) == os.path.abspath(ROOT):
                continue
            dirs.append(os.path.join(path, "tasks"))
        return dirs
    except Exception:
        return []


def evidence_search_dirs(tasks_dir=None):
    """The ordered directories to resolve a task's Evidence section across.

    `tasks_dir` keeps its existing single-directory shape — every current caller
    and test passes one path, or None for "the live repo". It additionally
    accepts a sequence of paths, which is how a test injects a constructed
    directory list instead of shelling out to git.

    **Main checkout first**, always: the common post-merge case then resolves on
    the first candidate, unchanged in behaviour and cost, and a worktree copy can
    never shadow evidence already integrated.
    """
    if tasks_dir is None:
        return [TASKS_DIR] + worktree_tasks_dirs()
    if isinstance(tasks_dir, str):
        return [tasks_dir]
    try:
        return [d for d in tasks_dir if isinstance(d, str) and d]
    except TypeError:
        return [TASKS_DIR]


def has_filled_verify_row(task_id, tasks_dir=None):
    """True only when the task's Evidence table — wherever it resolves: the main
    checkout first, then each live worktree, and within each of those the guide
    first then `TASK_REVIEW_Txxx.md` — carries a filled `verify` row. The first
    filled row found wins.

    **Fails closed.** A missing guide, a missing review file, an unreadable
    one, an absent Evidence section, an unfilled row, or a row still carrying
    the template's unchecked `☐ pass` placeholder all return False — in every
    searched directory, and when there are no directories to search. This is
    the one place in T064 where a wrong answer is silent and repo-wide: if
    "review file missing" ever became anything other than "no evidence", the
    merge gate would stop gating on every task at once.
    """
    for directory in evidence_search_dirs(tasks_dir):
        section = read_guide_section(task_id, "Evidence", directory)
        if not section:
            continue
        for match in VERIFY_ROW_PATTERN.finditer(section):
            if UNCHECKED_PASS_PATTERN.search(match.group("result")):
                continue
            notes = match.group("notes").lower()
            # T182: the Supervisor's own real-run check (T180) is never `/verify`, and an
            # `auto-run by hook` row counts only with its run record (D5) for this task and the
            # head commit of the checkout this row was read from.
            if AUTO_CHECKED_TAG in notes:
                continue
            if AUTO_ROW_TAG in notes and not auto_row_confirmed(
                    ROOT, os.path.dirname(os.path.abspath(directory)), task_id,
                    match.group("notes")):
                continue
            return True
    return False


# --- The companion score row and the three UI design rows (T190) ------------
#
# Four Evidence rows become binding here, named by their Check cell:
# `Companion score (easy-verifier)`, `UI: Visual regression`,
# `UI: Design-system compliance` and `UI: Responsiveness`. Only the **Result**
# cell decides, and only one spelling decides it: a checked `☑ fail`.
#
# **This check is deliberately fail-OPEN, and that inverts the rule every other
# check in this file follows. It is intentional — do not "fix" it.** Above,
# every absence resolves to *block*: a missing guide, an unreadable review file,
# an unparsable trace all mean "not verified". Here every absence resolves to
# *allow*: no row, a blank row, the unchecked template placeholder, `☑ N/A`, a
# malformed table, an unreadable file — none of them block.
#
# The reason is user decision D6 (2026-10-28): *"if you use verifier mcp, and ui
# to check, the code must pass them. if not, just work on the normal flow, that
# all"*. The companion tools (easy-verifier, easy-ui) are optional, so a machine
# with neither — no Docker, no Python package, no MCP server — must behave
# exactly as it did before this feature existed (FR-006, FR-014;
# `.claude/hooks/tests/data/t190_pre_change_gate_output.txt` is that assertion's
# oracle). Reading these rows fail-closed would require a score row on every
# task, which is how an optional tool becomes a mandatory one.
# The binding half is FR-015: a tool that *did* run is binding, and the only
# thing that tells this hook it ran is an explicit `☑ fail`.
#
# Structural, never a substring search — the T044 comment at the top of this
# file records what a `\bfail\b` scan over the row would cost: Notes prose such
# as "no failures observed" or "the M2 mutation must fail" would refuse a push.
# The Check cell is matched inside a pipe-delimited row and the verdict is read
# from the Result cell alone.
#
# Not generalised to the other Evidence rows (`Negative cases hold`, `Full smoke
# suite still green`). Deliberate cut: binding rows this feature was not asked
# to touch would block a push on a pre-existing `☑ fail` the moment it ships.
COMPANION_ROW_NAMES = (
    "Companion score",
    "UI: Visual regression",
    "UI: Design-system compliance",
    "UI: Responsiveness",
)


def _companion_row_pattern(name):
    """A pipe-delimited Evidence row whose Check cell contains `name`, with its
    Result and Notes cells captured separately. Line-anchored, and no cell can
    span a `|` or a newline — the same shape as `VERIFY_ROW_PATTERN`."""
    return re.compile(
        r"^[ \t]*\|[^|\n]*" + re.escape(name) + r"[^|\n]*\|"
        r"(?P<result>[^|\n]*)\|(?P<notes>[^|\n]*)",
        re.IGNORECASE | re.MULTILINE,
    )


COMPANION_ROW_PATTERNS = tuple(
    (name, _companion_row_pattern(name)) for name in COMPANION_ROW_NAMES)

# The checked box, attached to its verdict. `UNCHECKED_PASS_PATTERN` above is
# the same idea in the other direction: `☐ fail` is the template's guidance text,
# not an answer, so it must never match. Optional `**` because a reviewer may
# bold the verdict.
CHECKED_FAIL_PATTERN = re.compile(r"☑\s*\**\s*fail\b", re.IGNORECASE)
CHECKED_PASS_PATTERN = re.compile(r"☑\s*\**\s*pass\b", re.IGNORECASE)

# The verifier report a `pass` row cites, read after a literal `report:` label.
#
# **The label is load-bearing; do not drop it back to "the first path in the
# cell".** That is what this did until the Stage 4 P1 on T190, and it failed in
# both directions at once:
#   * False advisory on the common case. The Notes cell must also carry the ref
#     (FR-001, and T191's AC 11), and a ref is naturally written in backticks —
#     `plan/t190-t194-companion-scoring...HEAD`. That has a `/` in it, so the ref
#     was read as the report path, which does not exist, and an honest row warned.
#   * Silent inertness, which is the one that matters. A row citing **no report
#     at all** was excused by any unrelated backticked path that happened to sit
#     in the cell: `skills/score/SKILL.md` exists on disk, `os.path.isfile` said
#     true, and the advisory never fired. FR-005 is the whole "measured, not
#     claimed" protection for this row, so that made it inert while still
#     looking like a check — the same shape of defect as T044's substring scan.
#
# So: the path is the first backticked-or-bare path token **after** `report:`.
# No label means no citation, which the caller reports as "cites no verifier
# report path". Deterministic, unsatisfiable by an unrelated path elsewhere in
# the cell, and it survives the cell gaining more fields later.
REPORT_LABEL_PATTERN = re.compile(r"report\s*:", re.IGNORECASE)

# A backticked span first, so a path containing a space resolves whole; else a
# bare whitespace-delimited token. A candidate without a `/` is not a path — the
# same cell also carries `overall`, `change_risk`, the scope and the ref.
REPORT_PATH_PATTERN = re.compile(r"`([^`\n]+)`|([^\s|`]+)")


def cited_report_path(notes, checkout_root=None):
    """The verifier report path a Notes cell cites after its `report:` label,
    resolved, or None when the cell carries no label or no path after it.

    `~` is expanded (`EASY_VERIFIER_REPORTS_DIR` writes to
    `$HOME/.easy-verifier-reports/<repo>/`) and a relative path resolves against
    the checkout the row was read from. Never raises.
    """
    if not isinstance(notes, str):
        return None
    label = REPORT_LABEL_PATTERN.search(notes)
    if not label:
        return None
    for match in REPORT_PATH_PATTERN.finditer(notes, label.end()):
        candidate = (match.group(1) or match.group(2) or "").strip()
        if "/" not in candidate or "\x00" in candidate:
            continue
        try:
            path = os.path.expanduser(candidate)
            if not os.path.isabs(path):
                path = os.path.join(checkout_root or ROOT, path)
        except Exception:
            return None
        return path
    return None


def companion_rows(task_id, tasks_dir=None):
    """Every bound Evidence row present for `task_id`:
    `({row name: (result cell, notes cell)}, checkout root)`.

    Resolved exactly like `has_filled_verify_row`: main checkout first, then each
    live worktree, and within each the guide first then `TASK_REVIEW_Txxx.md`.
    The first directory carrying any bound row wins, and its checkout root is
    returned so a relative report path resolves against the right tree.

    Never raises. Every failure — a missing file, an unreadable one, an absent
    Evidence section, a malformed table — resolves to `({}, None)`, which means
    "no companion row" and therefore allows.
    """
    try:
        for directory in evidence_search_dirs(tasks_dir):
            section = read_guide_section(task_id, "Evidence", directory)
            if not section:
                continue
            rows = {}
            for name, pattern in COMPANION_ROW_PATTERNS:
                match = pattern.search(section)
                if match:
                    rows[name] = (match.group("result"), match.group("notes"))
            if rows:
                return rows, os.path.dirname(os.path.abspath(directory))
    except Exception:
        pass
    return {}, None


def failed_companion_rows(task_id, tasks_dir=None):
    """The bound rows whose Result cell carries a checked `☑ fail`, in table
    order — `[]` when there are none.

    Named for what it returns: the row names, not a verdict, because the block
    message must name the row it refuses on (AC 2), and
    `docs/claude-md/code-naming-conventions.md` reserves the `has_` prefix for
    booleans. An empty list is falsey, so the caller still reads as a predicate,
    and `[]` is the answer for every absence: see the inversion comment above.
    """
    rows, _ = companion_rows(task_id, tasks_dir)
    return [name for name in COMPANION_ROW_NAMES
            if name in rows and CHECKED_FAIL_PATTERN.search(rows[name][0])]


def companion_report_advisories(task_id, tasks_dir=None):
    """One line per `☑ pass` **Companion score** row whose cited verifier report
    is not a file on disk (FR-005: a `pass` is trusted only against the report
    it cites, the same rule the `verify` row follows against the event trace).

    Advisory only, never a block — an unresolvable citation costs a warning on
    stderr, so this cannot refuse a push on a path the hook merely failed to
    parse. The three UI rows are not checked: easy-ui is one named method among
    screenshot diff, LLM vision and Storybook snapshot (FR-011), and the other
    three cite no report file.
    """
    rows, checkout_root = companion_rows(task_id, tasks_dir)
    result, notes = rows.get("Companion score", (None, None))
    if result is None or not CHECKED_PASS_PATTERN.search(result):
        return []
    if CHECKED_FAIL_PATTERN.search(result):
        return []  # already blocking; one message about this row is enough
    path = cited_report_path(notes, checkout_root)
    if path is None:
        return [f"{task_id} Companion score row reads pass but its Notes cite no "
                f"verifier report path — that row is unscored, not a pass (FR-005)."]
    try:
        is_file = os.path.isfile(path)
    except Exception:
        is_file = False
    if not is_file:
        return [f"{task_id} Companion score row reads pass but the verifier report "
                f"it cites is not a file on disk: {path} — that row is unscored, "
                f"not a pass (FR-005)."]
    return []


# --- What to actually do about an unattributed Bash call (T095 defect B) ----
#
# This gate used to end its block with "a Bash command is attributed to a task
# **only** via CLAUDE_ACTIVE_TASK — run the task's verification command as
# `CLAUDE_ACTIVE_TASK=Txxx <command>`". Two things were wrong with it, and it
# was printed at the exact moment an operator is looking for a way out:
#
#   * The mechanism does not work from inside a session. T047 measured it: the
#     harness spawns a hook as a *sibling* process of the tool call, not a child
#     of the command inside it, so the hook inherits the harness's environment
#     and never the subshell a `Bash` call creates. Every record produced under
#     that instruction landed in `_untagged.jsonl`, and this gate then correctly
#     failed closed on it — blocking honest tasks.
#   * "only" was false. The env var *is* a working channel when it is set in the
#     process that launches the session; the state file is a second one, and the
#     only one reachable mid-session. `task_context.py`'s precedence list has
#     carried both since T047.
#
# The wording below is the one already written and proven in
# `craft-spawn-prompt` element 6 and `task_context.py`'s slot 2, condensed —
# deliberately reused rather than re-composed, because a third phrasing of this
# mechanism is exactly how the first two drifted apart. The absolute-path
# requirement is named because it is load-bearing: a sub-agent's cwd is its own
# worktree, so a relative path (or an unset `$CLAUDE_PROJECT_DIR`, which is
# empty inside a `Bash` tool call) silently writes a file the live hook never
# reads. That was T047's own Stage 4 P1 finding.
ATTRIBUTION_REMEDY = (
    "Note: if a task above is missing its trace record rather than its evidence "
    "row, attribute your Bash calls by writing the active-task state file first: "
    "`mkdir -p <main-checkout>/.claude/hooks/.state && printf '%s\\n%s\\n' "
    "\"Txxx\" \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" > "
    "<main-checkout>/.claude/hooks/.state/active_task` — using the literal "
    "absolute path of the main checkout (not $CLAUDE_PROJECT_DIR, which is empty "
    "inside a Bash tool call, and not a relative path, which resolves into your "
    "worktree). Valid for CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S seconds (default "
    "6h). CLAUDE_ACTIVE_TASK=Txxx <command> does NOT work from inside a session: "
    "a hook is a sibling process of the tool call and never inherits its "
    "subshell (T047). The env var only takes effect when set before the session "
    "starts."
)


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

    # Classify the command, not the data it carries (T095 defect C, T099).
    # Heredocs first, then quoted spans — that order is required, and
    # `strip_quoted_spans`'s docstring says why. A heredoc body is an argument
    # being written to a file, so a `git push` inside one is a mention. A quoted
    # span is a mention only when nothing will execute it: `grep "git push"` is
    # data, `bash -c "git push"` is a push, and the wrapper is what tells them
    # apart. Both strips remove less on any uncertainty, so this composition can
    # only ever over-block — never disarm the gate.
    #
    # Note this is NOT the same call as `invokes_test_runner`'s unconditional
    # `QUOTED_SPAN_PATTERN.sub`, and must not be collapsed into it: there a false
    # negative means "not verified" and refuses the merge; here it would mean
    # "not a push" and wave one through.
    scannable = strip_quoted_spans(strip_heredoc_bodies(command))
    if not any(re.search(p, scannable) for p in BLOCKED_PATTERNS):
        sys.exit(0)

    # T157: in board mode `online` the board cache is refreshed before it is evaluated
    # (the pre-merge pull moment). A failed or hanging pull is a warning, and the gate
    # evaluates the cache it already has. Local and unusable configs never pull.
    mode = board_mode(ROOT)
    notes = []
    if mode == "online":
        warning = pull_cache(ROOT)
        if warning:
            print(f"[hook:pre_bash] {warning}", file=sys.stderr)
            notes.append(warning)

    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        sys.exit(0)

    def tasks_in_section(section_title, id_pattern=r"T\d+", with_lines=False):
        row_id = re.compile(rf"\*\*({id_pattern})\*\*")
        m = re.search(
            rf"### {re.escape(section_title)}\n(.*?)(?=^###|\Z)", kanban,
            re.DOTALL | re.MULTILINE,
        )
        if not m:
            return []
        block = m.group(1).strip()
        return [(row_id.search(l).group(1), l) if with_lines else row_id.search(l).group(1)
                for l in block.splitlines()
                if l.strip().startswith("- ") and row_id.search(l)]

    # `T\d+`, plus the board's `id_pattern` when `.claude/board.json` sets one (T153).
    id_pattern = task_id_pattern(ROOT)
    in_progress = tasks_in_section("In Progress", id_pattern)
    ready_review = tasks_in_section("Ready for Review", id_pattern)

    # T157 / FR-011: online, the cache holds the whole team's board, so only my In
    # Progress tasks block. Every doubt (`me` unset, a cache that is not a board render,
    # two assignee fields on one row) resolves to blocking. T161: likewise only my Ready
    # for Review tasks (and unassigned ones) are checked for verify evidence; a filter
    # that raises checks every row.
    if mode == "online":
        in_progress, filter_notes = my_blocking_tasks(
            tasks_in_section("In Progress", id_pattern, with_lines=True),
            (load_config(ROOT) or {}).get("me"), kanban)
        try:
            ready_review, review_notes = my_review_tasks(
                tasks_in_section("Ready for Review", id_pattern, with_lines=True),
                (load_config(ROOT) or {}).get("me"), kanban)
        except Exception:
            review_notes = ["the Ready for Review filter failed — every Ready for Review "
                            "task is checked (safe side)"]
        filter_notes = filter_notes + review_notes
        notes.extend(filter_notes)
        for note in filter_notes:
            print(f"[hook:pre_bash] {note}", file=sys.stderr)

    blockers = []

    if in_progress:
        blockers.append(f"Tasks still In Progress: {', '.join(in_progress)}")

    if ready_review:
        # Check each for verify evidence in their task guide
        unverified = []
        failed_rows = []
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

            # T190: a companion score row or a UI design row that explicitly
            # reads `☑ fail` is binding. Everything else about those four rows
            # is silent — see the inversion comment above
            # `COMPANION_ROW_NAMES`: this check allows unless a fail is explicit.
            failed_rows.extend(f"{tid} ({row})" for row in failed_companion_rows(tid))
            for advisory in companion_report_advisories(tid):
                print(f"[hook:pre_bash] {advisory}", file=sys.stderr)

        if unverified:
            blockers.append(
                f"Tasks in Ready for Review missing Stage 5 verify evidence: "
                f"{', '.join(unverified)}"
            )

        if failed_rows:
            blockers.append(
                f"Tasks in Ready for Review with an Evidence row marked fail: "
                f"{', '.join(failed_rows)}"
            )

    if blockers:
        result = {
            "decision": "block",
            "reason": (
                "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • "
                + "\n  • ".join(blockers + [f"Board: {n}" for n in notes])
                + "\nComplete Stage 4 review and Stage 5 verify first."
                + "\n  " + ATTRIBUTION_REMEDY
            )
        }
        print(json.dumps(result))

main()
