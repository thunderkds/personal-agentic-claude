#!/usr/bin/env python3
"""
PreToolUse hook — fires before every Bash tool call.

Blocks git push/merge/rebase/pull commands if:
  1. Any task in PROJECT_KANBAN.md is still In Progress or Ready for Review
  2. No Stage 5 verify evidence is found in any pending task guide

This enforces the pipeline gate: Stage 4 review + Stage 5 verify must
complete before code ships.

T211: git's global options between `git` and the verb (`git -C <dir> push`, `git -c k=v merge`,
`git --no-pager pull`, an unknown `--x`) do not hide it, and `git -c alias.<x>=… <x>` (or
`--config-env alias.<x>=…`) is gated as a merge. Known limit, by design: an alias set in a git
config file, or through the `GIT_CONFIG_*` environment variables, is out of reach of a static
check of the command text — this hook does not read git config. Shell aliases and functions,
scripts that call git, and `gh pr merge` are out of scope too.
"""
import json
import os
import re
import shlex
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
    from guide_sections import (  # noqa: E402
        GUIDE_PREFIX, REVIEW_PREFIX, _candidate_paths, is_pointer_only, normalize_task_id,
        read_guide_section, slice_section)
    from shell_data import (  # noqa: E402
        DATA_COMMAND_PATTERN, strip_heredoc_bodies, strip_quoted_spans)
    from board.config import load_config, task_id_pattern  # noqa: E402
    from board.moments import (  # noqa: E402
        board_mode, my_blocking_tasks, my_review_tasks, pull_cache)
    from verify_record import (  # noqa: E402
        AUTO_CHECKED_TAG, AUTO_ROW_TAG, MINIMAL_LOG_REL, ROW_COMMIT, ROW_SESSION, SHA_PATTERN,
        auto_row_confirmed, minimal_verify_line, read_record, record_verify_line, same_code)
    from auto_mode import record_block  # noqa: E402
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

# T210: `git pull` fetches and merges, so it is a merge (D1), in every form (`--ff-only` and
# `--rebase` both move the branch). `git merge-base` is a read-only query and is the only
# `merge-*` subcommand exempted (D3): `merge-file` and `merge-tree` stay blocked.
#
# T211 (D1, D4): any run of git's global options may come between `git` and the verb. The ones
# that take an argument are `GIT_OPTIONS_WITH_ARG` (separate, attached `-Cdir`, or `--opt=value`);
# every other `-` word is skipped as a flag, known (`--no-pager`, `-P`, `--bare`,
# `--no-replace-objects`, `--literal-pathspecs`, `--exec-path[=<p>]`) or not (D4: fail closed).
# `_git_actions` resolves only `-C`, `-c`, `--no-pager` and `-P` of these and treats any other
# option as unresolved, so narrowing can never read a command classification did not. An argument
# may be quoted (`-C "dir with space"`). Each option consumes its argument with no alternative
# parse — the flag clause never starts with an arg-taking name — so matching stays linear.
GIT_OPTIONS_WITH_ARG = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env")
_GIT_ARG = r"""(?:"[^"\n]*"|'[^'\n]*'|[^\s;&|"'])+"""
_GIT_SHORT_WITH_ARG = "".join(o[1] for o in GIT_OPTIONS_WITH_ARG if not o.startswith("--"))
_GIT_LONG_WITH_ARG = "|".join(re.escape(o[2:]) for o in GIT_OPTIONS_WITH_ARG if o.startswith("--"))
GIT_GLOBAL_OPTION = (
    rf"(?:-[{_GIT_SHORT_WITH_ARG}]\s*{_GIT_ARG}"
    rf"|--(?:{_GIT_LONG_WITH_ARG})(?:=|\s+){_GIT_ARG}"
    rf"|-(?![{_GIT_SHORT_WITH_ARG}]|-(?:{_GIT_LONG_WITH_ARG})(?:[=\s]|$))[^\s;&|]*)"
)
GIT_VERB_PREFIX = rf"\bgit(?:\s+{GIT_GLOBAL_OPTION})*\s+"
BLOCKED_PATTERNS = [
    GIT_VERB_PREFIX + r"push\b",
    GIT_VERB_PREFIX + r"merge\b(?!-base\b)",
    GIT_VERB_PREFIX + r"rebase\b",
    GIT_VERB_PREFIX + r"pull\b",
]

# T211 (D3): `git -c alias.p=push p` defines and runs an alias in one command, so the verb never
# appears. `-c alias.` (or `--config-env alias.`) anywhere in a `git` command gates it as a merge:
# the whole board. Matched per command segment, and skipped only when that segment's command is
# one T099's `DATA_COMMAND_PATTERN` names (`echo git -c alias.p=push p` prints it) — the same
# keep-unless-known-data direction as `strip_quoted_spans`.
GIT_ALIAS_PATTERN = re.compile(
    r"\bgit\b.*?\s(?:-c\s*|--config-env(?:=|\s+))[\"']?(?i:alias)\.")


def defines_git_alias(scannable):
    """True when a command segment of `scannable` runs `git` with an inline alias (T211 D3)."""
    return any(GIT_ALIAS_PATTERN.search(segment) and not DATA_COMMAND_PATTERN.match(segment)
               for segment in COMMAND_SEPARATOR_PATTERN.split(scannable))

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

# Wrappers that pass through to the real command. T210 (D2): `timeout [options] <duration>`,
# where `-k`/`-s` take a separate argument (`timeout -k 5 60s pytest`). The duration is
# required, so `timeout pytest` stays a mention.
BENIGN_COMMAND_PREFIX = re.compile(
    r"^(?:(?:sudo|env|time|nohup|npx|uv\s+run|poetry\s+run|pipenv\s+run|"
    r"pnpm\s+exec|yarn\s+exec|"
    r"timeout(?:\s+(?:-[ks]\s+\S+|-[-\w=]+))*\s+\d+(?:\.\d+)?[smhd]?)\s+)+",
    re.IGNORECASE,
)

# A subshell's opening paren: `(timeout 300 python3 -m pytest)` runs the runner (T210 AC 3).
# One paren only — `((` opens an arithmetic expression, not a command.
SUBSHELL_OPEN = re.compile(r"^\((?!\()\s*")

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
    """Peel a subshell paren, leading env assignments and benign wrappers until nothing changes."""
    while True:
        shorter = BENIGN_COMMAND_PREFIX.sub("", ENV_ASSIGNMENT_PREFIX.sub(
            "", SUBSHELL_OPEN.sub("", candidate)))
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

    T188 D5 adds one more place to look, and only after every Evidence table has
    said no: a **minimal-track** task has no guide and no review file, so its
    result is the `verify:` line in its Decision record
    (`tasks/MINIMAL_LOG.md`). That line is read under exactly T182's rule and
    nothing weaker — it counts only when it is an `auto-run by hook` line whose
    run record exists for this task and the checkout's head commit and says
    pass. A hand-typed line counts for nothing there, including one that claims
    the user ran `/verify`: before T188 a minimal-track task at Ready for Review
    always blocked, so reading a line the hook did not write would be the one
    way this change could make the gate weaker.
    """
    for directory in evidence_search_dirs(tasks_dir):
        checkout = os.path.dirname(os.path.abspath(directory))
        if verify_row_passes(
                read_guide_section(task_id, "Evidence", directory),
                lambda notes, rel: auto_row_confirmed(ROOT, checkout, task_id, notes, rel)):
            return True
    for directory in evidence_search_dirs(tasks_dir):
        checkout = os.path.dirname(os.path.abspath(directory))
        if minimal_line_passes(
                minimal_verify_line(task_id, directory),
                lambda notes, rel: auto_row_confirmed(ROOT, checkout, task_id, notes, rel)):
            return True
    return False


def verify_row_passes(section, confirm):
    """True when an Evidence `section` holds a filled `verify` pass row. `confirm(notes, None)`
    decides an `auto-run by hook` row (T182 D5): against which commit is the caller's choice."""
    if not section:
        return False
    for match in VERIFY_ROW_PATTERN.finditer(section):
        if UNCHECKED_PASS_PATTERN.search(match.group("result")):
            continue
        notes = match.group("notes").lower()
        # T182: the Supervisor's own real-run check (T180) is never `/verify`, and an
        # `auto-run by hook` row counts only with its run record (D5) for this task and the
        # head commit of the checkout (or branch) this row was read from.
        if AUTO_CHECKED_TAG in notes:
            continue
        if AUTO_ROW_TAG in notes and not confirm(match.group("notes"), None):
            continue
        return True
    return False


def minimal_line_passes(line, confirm):
    """True when a minimal-track `verify:` line `(result, notes)` is a confirmed hook pass (T188
    D5). A hand-typed line counts for nothing."""
    if not line:
        return False
    result, notes = line
    if "☑" not in result or "pass" not in result.lower():
        return False
    low = notes.lower()
    if AUTO_CHECKED_TAG in low or AUTO_ROW_TAG not in low:
        return False
    return confirm(notes, MINIMAL_LOG_REL)


# --- The verify row must be committed on the branch (T210 D4) -----------------
#
# The working-tree read above let T207 and T208 merge with a pass their merged commit did not
# contain: the auto verify run writes its row into the worktree AFTER the branch's last commit.
# So for a merge, or a narrowed push, of one task's branch, that task's row is read from the
# branch tip with `git show <tip>:tasks/...` — guide first, review second, then the minimal-track
# Decision record, the same order as `has_filled_verify_row`. An `auto-run by hook` row is
# confirmed against the tip, not the checkout's HEAD: a merge runs on `main`.
#
# The T095 note above rejected `git show` because a pushed commit may not be in the main
# checkout's object store. This reads in the directory the command runs in, where the merged or
# pushed ref must resolve for the command itself to work.
#
# Never weaker than before: when the tip cannot be resolved, the caller falls back to
# `has_filled_verify_row` (the working trees), exactly the pre-T210 rule.
UNCOMMITTED_ROW_MESSAGE = "verify row for {tid} is not committed on {branch} — commit it, then merge"


def _auto_row_confirmed_at(directory, task_id, notes, tip, report_rel=None):
    """`verify_record.auto_row_confirmed`, with the branch `tip` in place of the checkout HEAD."""
    commit, session = ROW_COMMIT.search(notes or ""), ROW_SESSION.search(notes or "")
    if not commit or not session:
        return False
    sha = commit.group(1)
    record = read_record(ROOT, task_id, sha)
    if not record or (record.get("task"), record.get("commit"), record.get("verdict"),
                      record.get("session")) != (task_id, sha, "pass", session.group(1)):
        return False
    return same_code(directory, task_id, sha, tip, report_rel)


def committed_verify_row(task_id, branch, directory):
    """True/False: whether `branch`'s tip, read in `directory`, commits a filled `verify` row (or a
    confirmed minimal-track `verify:` line) for `task_id`. None when the tip cannot be resolved —
    the caller then keeps the pre-T210 working-tree read. Never raises."""
    try:
        done = _git(directory, "rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}")
        tip = done.stdout.strip() if done is not None and done.returncode == 0 else ""
        normalized = normalize_task_id(task_id, ROOT)
        if not SHA_PATTERN.match(tip) or not normalized:
            return None

        def show(rel):
            shown = _git(directory, "show", f"{tip}:{rel}")
            return shown.stdout if shown is not None and shown.returncode == 0 else None

        def confirm(notes, rel):
            return _auto_row_confirmed_at(directory, task_id, notes, tip, rel)

        sections = (slice_section(show(rel), "Evidence")
                    for prefix in (GUIDE_PREFIX, REVIEW_PREFIX)
                    for rel in _candidate_paths("tasks", prefix, normalized))
        if verify_row_passes(next((s for s in sections if s is not None
                                   and not is_pointer_only(s)), None), confirm):
            return True
        block = record_block(show(MINIMAL_LOG_REL) or "", task_id, skip_comments=True)
        hit, result, notes = record_verify_line(block[2]) if block else (None, "", "")
        return minimal_line_passes((result, notes) if hit else None, confirm)
    except Exception:
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
#
# `(?:ed)?` is deliberate and the two patterns must stay symmetric. `fail\b`
# alone did not match `☑ failed` — `\b` cannot sit between `l` and `e` — so a
# reviewer who wrote the `-ed` form of the one word that makes this gate fire
# got a **silent allow** (Stage 4 P2). The template prescribes `fail`, but on the
# blocking side the safe direction is to catch more, not less. Widening only the
# fail side would trade that gap for another: `☑ passed` would stop being read
# as a pass, so `companion_report_advisories` would skip the FR-005 report check
# on it. Bounded there on purpose: `failing`, `failure` and every prose variant
# belong in the Notes cell, and `\b` after the optional `ed` is what keeps them
# out.
CHECKED_FAIL_PATTERN = re.compile(r"☑\s*\**\s*fail(?:ed)?\b", re.IGNORECASE)
CHECKED_PASS_PATTERN = re.compile(r"☑\s*\**\s*pass(?:ed)?\b", re.IGNORECASE)

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


# --- Which task a `git push` touches (T197) ---------------------------------
#
# Until T197 `main()` checked the whole board on every trigger, so one task parked
# in Ready for Review by another live session refused every other session's push.
# Now a `git push` of one task's branch is judged by that task alone (D3), and
# `pushed_task_ids` is the only thing that decides "one task's branch".
#
# **This loosens a fail-closed gate, so the resolver is built the other way
# round: it says which task only when it can prove it, and returns None on every
# doubt.** None leaves `main()` exactly as it was — the whole board (D2). It
# reads the branch from the command, never from the board (D1):
#   * the source ref the command names (`src:dst` → `src`), or for `HEAD` or no
#     refspec, the current branch of the directory the push runs in — the event's
#     `cwd`, moved by a leading `cd <dir> &&` or `git -C <dir>`;
#   * that name must hold exactly one whole task ID (`feat/t9000-x` is T9000, never
#     T900; `plan/t190-t194` is two IDs, so None), and `main()` then also requires
#     that task to be one it checks: a row in In Progress or Ready for Review that the
#     online filters kept. Any other task keeps the whole board.
# Everything else is None, by allowlist, never by denylist: an unknown option
# (`--all`, `--mirror`, `--tags`, `-o`), a remote that is not a plain name (bash
# expands `{origin,--all}` to `origin --all`), a tag, a deletion, a destination that
# is not the same task (`HEAD:main`, `release/*`), `git merge`/`rebase` anywhere in
# the command (D4), any segment that is not `cd`, a read-only `git` subcommand with
# only its allowlisted options, or a pipe reader of the push's output, a `&` anywhere
# (a backgrounded `cd` does not move the push), `$`/backticks/subshells/unknown
# redirections, a `{` or `}` anywhere (brace expansion can turn a word into an
# option), a glob in a path argument, a `cd` whose effect is not certain (`||`, `;`,
# a pipe, `~`), a detached HEAD, a git that fails or takes over 5 s, and push config
# that can move the destination (`remote.*.push`, `remote.*.mirror`, a
# `push.default` other than simple/current).
#
# Tokenized with stdlib `shlex` — a tokenizer, not a shell parser — with
# **comments switched off**: shlex reads `#` mid-word as a comment and would drop
# a following line, so `... feat/t900-x #x` + newline + a push of main would read
# as one scoped push. Seeing more text than bash runs can only make this global.
#
# Stated trust boundaries, both residual:
#   * The scoping trusts the branch name. T901's work pushed on `feat/t900-x` is
#     checked against T900 when T900 is itself in In Progress or Ready for Review,
#     so it needs T900's evidence and no longer T901's. When T900 is in neither, the
#     push checks the whole board, T901 included.
#   * `git commit` can run the repo's own hooks, which run code no name check sees
#     (they could switch the branch before the push reads `HEAD`).
PUSH_SEPARATORS = frozenset({";", "&&", "||", "|"})  # `&` is not here: it is a None
SHELL_PUNCTUATION = frozenset("();<>|&")
EXPANSION_CHARS = frozenset("{}$`")  # brace, parameter and command expansion
GLOB_CHARS = frozenset("*?[")
REMOTE_NAME_PATTERN = re.compile(r"[A-Za-z0-9._-]+")

# The two redirections agents append to a push. Removed before tokenizing; any
# other `<`/`>` survives as a token and makes the command unresolved.
OUTPUT_REDIRECT_PATTERN = re.compile(r"(?<!\S)(?:[12]?>&[12]|(?:[12]|&)?>>?\s*/dev/null)(?!\S)")

SAFE_REF_PATTERN = re.compile(r"[A-Za-z0-9._/-]+")
SAFE_PATH_PATTERN = re.compile(r"[A-Za-z0-9._/+-]+")  # no `~`, `$` or glob: no expansion
GLOBAL_REF_ROOTS = frozenset({"release", "integration"})

# Subcommands that cannot change which branch is checked out or merge anything, each
# with the only options it may carry. Never add `merge` or `rebase`: their absence is
# how D4 keeps a merge on the whole board. `fetch` is out: `--upload-pack` runs a
# command. Any other `-` token is None, so `--output=<path>` cannot rewrite `.git/HEAD`.
SAFE_GIT_OPTIONS = {
    "add": frozenset({"-A", "-a", "--all", "-u"}),
    "commit": frozenset({"-m", "-a", "-am", "--amend", "--no-edit", "-q", "-s", "--signoff",
                         "--no-verify"}),
    "status": frozenset({"-s", "--short", "-b", "--branch", "--porcelain"}),
    "log": frozenset({"--oneline", "-n", "--stat", "--graph"}),
    "diff": frozenset({"--stat", "--name-only", "--name-status", "--cached", "--staged",
                       "--shortstat"}),
    "show": frozenset({"--stat", "--name-only", "--oneline", "-s"}),
}
SAFE_GIT_SUBCOMMANDS = frozenset(SAFE_GIT_OPTIONS)
MESSAGE_OPTIONS = frozenset({"-m", "-am"})  # `git commit`: the next token is the message
LOG_COUNT_PATTERN = re.compile(r"-\d+")
PIPE_READERS = frozenset({"tail", "head", "cat", "grep", "wc"})
SCOPED_PUSH_FLAGS = frozenset({
    "-u", "--set-upstream", "-f", "--force", "--force-with-lease", "--force-if-includes",
    "-n", "--dry-run", "-v", "--verbose", "-q", "--quiet", "--no-verify", "--progress",
})
SAFE_PUSH_DEFAULTS = frozenset({"simple", "current"})
PUSH_CONFIG_KEYS = r"^(push\.default|remote\..*\.(push|mirror))$"


def _git(directory, *args):
    """`git -C <directory> <args>` with the 5-second timeout, or None on any failure."""
    try:
        return subprocess.run(["git", "-C", directory, *args], capture_output=True,
                              text=True, timeout=GIT_WORKTREE_TIMEOUT_S)
    except Exception:
        return None


def _current_branch(directory):
    """The branch checked out in `directory`; None when detached, not a repo, or git failed."""
    done = _git(directory, "rev-parse", "--abbrev-ref", "HEAD")
    if done is None or done.returncode != 0:
        return None
    name = done.stdout.strip()
    return name if name and name != "HEAD" else None


def _push_config_is_plain(directory):
    """True only when no config in `directory` can send a push somewhere its refspec
    does not say: no `remote.*.push`, no `remote.*.mirror`, `push.default` simple/current."""
    done = _git(directory, "config", "--get-regexp", PUSH_CONFIG_KEYS)
    if done is None:
        return False
    if done.returncode == 1 and not done.stdout.strip():
        return True  # none of the keys is set
    if done.returncode != 0:
        return False
    for line in done.stdout.splitlines():
        key, _, value = line.partition(" ")
        if key.lower() != "push.default" or value.strip().lower() not in SAFE_PUSH_DEFAULTS:
            return False
    return True


def _ref_task_id(name, id_regex):
    """The one task ID a branch name holds, upper-cased, or None."""
    if name.startswith("refs/heads/"):
        name = name[len("refs/heads/"):]
    if (not SAFE_REF_PATTERN.fullmatch(name) or name.startswith("refs/")
            or name.split("/")[0].lower() in GLOBAL_REF_ROOTS):
        return None
    ids = {match.group(0).upper() for match in id_regex.finditer(name)}
    return ids.pop() if len(ids) == 1 else None


def _push_task_id(args, directory, id_regex, sources=None):
    """The one task a single `git push <args>` run in `directory` pushes, or None.
    `sources`, when a list, collects `(directory, source branch)` per refspec (T210 D4)."""
    if directory is None:
        return None
    positionals = []
    for arg in args:
        if arg.startswith("-"):
            if arg in SCOPED_PUSH_FLAGS or arg.startswith("--force-with-lease="):
                continue
            return None
        positionals.append(arg)
    if positionals and not REMOTE_NAME_PATTERN.fullmatch(positionals[0]):
        return None  # a URL, a path, or a word bash expands (`{origin,--all}`)
    branch = _current_branch(directory)
    if branch is None or not _push_config_is_plain(directory):
        return None
    ids = set()
    for spec in positionals[1:] or ["HEAD"]:  # positionals[0] is the remote
        src, colon, dst = (spec[1:] if spec.startswith("+") else spec).partition(":")
        # Only the source may be `HEAD` (the current branch); an empty source is a delete.
        names = [branch if src == "HEAD" else src] + ([dst] if colon else [])
        for name in names:
            task_id = _ref_task_id(name, id_regex)
            if task_id is None:
                return None
            ids.add(task_id)
        if sources is not None:
            sources.append((directory, names[0]))
    return ids.pop() if len(ids) == 1 else None


def _read_only_git_args_ok(subcommand, args):
    """True only when every option is on `subcommand`'s allowlist and no path argument
    carries a glob (a file named `--output=.git/HEAD` would expand into an option).
    A commit message is the token after `-m`/`-am`; it may hold a glob, never a `-`."""
    allowed = SAFE_GIT_OPTIONS[subcommand]
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("-"):
            if arg not in allowed and not (subcommand == "log" and LOG_COUNT_PATTERN.fullmatch(arg)):
                return False
            if subcommand == "commit" and arg in MESSAGE_OPTIONS:
                index += 1
                if index >= len(args) or args[index].startswith("-"):
                    return False
        elif GLOB_CHARS & set(arg):
            return False
        index += 1
    return True


def _command_segments(command):
    """`[(tokens, separator before, separator after)]` for each simple command, or None
    when the text holds anything this resolver does not read."""
    text = OUTPUT_REDIRECT_PATTERN.sub(" ", strip_heredoc_bodies(command)).replace("\n", " ; ")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    segments, current, before = [], [], None
    for token in tokens:
        if token in PUSH_SEPARATORS:
            segments.append((current, before, token))
            current, before = [], token
        elif set(token) <= SHELL_PUNCTUATION or EXPANSION_CHARS & set(token):
            return None  # `&` lands here too: a background job never moves the push
        else:
            current.append(token)
    segments.append((current, before, None))
    return [segment for segment in segments if segment[0]]


def _git_actions(command, cwd):
    """`[(git args, directory)]` for every `git` segment that is not an allowlisted read-only
    one, in order, or None when the command holds anything else this resolver does not read."""
    if not isinstance(command, str) or not isinstance(cwd, str) or not os.path.isabs(cwd):
        return None
    segments = _command_segments(command)
    if not segments:
        return None
    directory, actions = cwd, []
    for tokens, before, after in segments:
        head, args = tokens[0], tokens[1:]
        if head == "cd":
            # Only `cd <dir> &&` certainly runs the next command in <dir>.
            certain = (len(args) == 1 and before in (None, ";", "&&") and after == "&&"
                       and directory is not None and SAFE_PATH_PATTERN.fullmatch(args[0]))
            directory = os.path.normpath(os.path.join(directory, args[0])) if certain else None
            continue
        if before == "|" and head in PIPE_READERS:
            continue  # reads the push's output in a subshell; cannot move the push
        if head != "git":
            return None
        # T211 D1: git's global options. `-C <dir>` moves the directory, like `cd <dir> &&`.
        # `-c <k=v>` can change what a push or a read-only command does (`push.default`,
        # `core.fsmonitor`), so it is read only before `merge`, where it cannot change which tip
        # is merged. `--no-pager`/`-P` change nothing. Every other option — another repository,
        # work tree or ref namespace, an attached form, an unknown flag — is unresolved.
        where, configured = directory, False
        while args and args[0].startswith("-"):
            if args[0] in ("--no-pager", "-P"):
                args = args[1:]
                continue
            if args[0] not in ("-C", "-c") or len(args) < 2:
                return None
            if args[0] == "-C":
                if where is None or not SAFE_PATH_PATTERN.fullmatch(args[1]):
                    return None
                where = os.path.normpath(os.path.join(where, args[1]))
            configured = configured or args[0] == "-c"
            args = args[2:]
        if not args or (configured and args[0] != "merge"):
            return None
        if args[0] in SAFE_GIT_SUBCOMMANDS:
            if not _read_only_git_args_ok(args[0], args[1:]):
                return None
            continue
        actions.append((args, where))
    return actions


def _resolve_pushed_task(command, cwd, id_pattern, sources=None):
    actions = _git_actions(command, cwd)
    if not actions:
        return None
    id_regex = re.compile(id_pattern or task_id_pattern(ROOT, bounded=True), re.IGNORECASE)
    found = set()
    for args, where in actions:
        if args[0] != "push":
            return None
        task_id = _push_task_id(args[1:], where, id_regex, sources)
        if task_id is None:
            return None
        found.add(task_id)
    return found.pop() if len(found) == 1 else None


def pushed_task_ids(command, cwd, id_pattern=None):
    """The one task ID (upper-cased) that every `git push` in `command` pushes, or None.

    None means "unresolved — check the whole board" and is the answer to every doubt;
    see the T197 comment above. `cwd` is the event's own `cwd`. `id_pattern` is a
    bounded regex source, defaulting to the board's (`task_id_pattern`). Never raises.
    """
    try:
        return _resolve_pushed_task(command, cwd, id_pattern)
    except Exception:
        return None


# T211 D2: the `git merge` options that take a separate argument. Every other `-` word is skipped
# alone (`--opt=value` and `-Xours` are one word), so any option leaves the branches resolvable.
MERGE_OPTIONS_WITH_ARG = frozenset({"-m", "-F", "-s", "--strategy", "-X", "--strategy-option",
                                    "--into-name"})
OCTOPUS_DOUBT_MESSAGE = ("octopus merge: cannot confirm {branch} — each branch must name exactly "
                         "one task and resolve to a commit")


def _merge_sources(args, where):
    """`[(directory, branch)]` for every branch `git merge <args>` names, in order."""
    names, index = [], 0
    while index < len(args):
        if args[index] in MERGE_OPTIONS_WITH_ARG:
            index += 2  # the option and its argument (a message, a strategy, …)
            continue
        if not args[index].startswith("-"):
            names.append(args[index])
        index += 1
    return [(where, name) for name in names]


def branch_targets(command, cwd, id_pattern=None):
    """`(targets, doubts)` for what `command` merges or pushes (T210 D4, T211 D2), never raising.

    `targets` is `[(task ID, branch, directory)]`, each branch whose task's verify row must be
    committed on it. One merged or pushed branch that cannot be resolved gives `([], [])`: the
    pre-T210 working-tree read. An octopus merge (two or more branches) resolves every branch, and
    each one that names no single task, or whose tip does not resolve, is a `doubts` entry (a
    block). `git pull` and `git rebase` are always `([], [])`: what they merge is not a local tip.
    """
    try:
        actions = _git_actions(command, cwd)
        if not actions:
            return [], []
        id_regex = re.compile(id_pattern or task_id_pattern(ROOT, bounded=True), re.IGNORECASE)
        sources = []
        if len(actions) == 1 and actions[0][0][0] == "merge":
            sources = _merge_sources(actions[0][0][1:], actions[0][1])
        elif _resolve_pushed_task(command, cwd, id_pattern, sources) is None:
            return [], []
        if len(set(sources)) == 1:
            directory, branch = sources[0]
            task_id = _ref_task_id(branch, id_regex) if directory is not None else None
            return ([(task_id, branch, directory)] if task_id else []), []
        if actions[0][0][0] != "merge" or len(sources) < 2:
            return [], []
        targets, doubts = [], []
        for directory, branch in sources:
            task_id = _ref_task_id(branch, id_regex)
            tip = None if directory is None else _git(
                directory, "rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}")
            if task_id is None or tip is None or tip.returncode != 0:
                doubts.append(branch)
            else:
                targets.append((task_id, branch, directory))
        return targets, doubts
    except Exception:
        return [], []


def branch_target(command, cwd, id_pattern=None):
    """The one `(task ID, branch, directory)` `command` merges or pushes, or None (T210 D4)."""
    targets, doubts = branch_targets(command, cwd, id_pattern)
    return targets[0] if len(targets) == 1 and not doubts else None


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
    "row, attribute your Bash calls. A sub-agent whose spawn prompt carries "
    "`Task ID: Txxx` or a `tasks/TASK_GUIDE_Txxx.md` path is attributed from its "
    "own transcript and writes nothing. Otherwise write this session's state file "
    "first: `mkdir -p <main-checkout>/.claude/hooks/.state/active_task.d && "
    "printf '%s\\n%s\\n' \"Txxx\" \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" > "
    "<main-checkout>/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID` "
    "— using the literal "
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
    if (not any(re.search(p, scannable) for p in BLOCKED_PATTERNS)
            and not defines_git_alias(scannable)):
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

    # T197: a push of one task's branch is judged by that task alone, on top of the
    # online filters above, never instead of them. It narrows only when that task is
    # one the gate checks — its row is in In Progress or Ready for Review, and online
    # the filters kept it. Narrowing to any other task (Todo, Done, outside the two
    # lanes, a teammate's row) would empty both lists, so a branch named after it
    # would meet no check at all (Stage 4 finding 4; D3 as revised). An unresolved
    # push, and every such task, keep the whole board (D2).
    scoped = pushed_task_ids(command, event.get("cwd"))
    if scoped is not None and scoped in {tid.upper() for tid in [*in_progress, *ready_review]}:
        in_progress = [tid for tid in in_progress if tid.upper() == scoped]
        ready_review = [tid for tid in ready_review if tid.upper() == scoped]

    blockers = []

    if in_progress:
        blockers.append(f"Tasks still In Progress: {', '.join(in_progress)}")

    if ready_review:
        # Check each for verify evidence in their task guide
        unverified = []
        failed_rows = []
        uncommitted = []
        # T210 D4: the task branches this command merges or pushes, where they can be resolved;
        # T211 D2: every branch of an octopus merge, and the ones it cannot confirm.
        targets, doubts = branch_targets(command, event.get("cwd"))
        uncommitted.extend(OCTOPUS_DOUBT_MESSAGE.format(branch=branch) for branch in doubts)
        for tid in ready_review:
            # Look for a filled verify row in the Evidence table — in the guide,
            # or in the sibling TASK_REVIEW file it may have moved to (T064) —
            # AND a matching real tool call in the event trace. The text claim
            # alone is not trusted (the model can lie about success). Every
            # absence resolves to False, so this stays fail-closed.
            # T210 D4: for a merged or pushed task, the row must be committed on each of its
            # branches; a branch without it wins, and an unresolvable tip (None) otherwise keeps
            # the working-tree read.
            verdicts = [(committed_verify_row(tid, branch, directory), branch)
                        for task_id, branch, directory in targets if task_id == tid.upper()]
            missing_on = next((branch for found, branch in verdicts if found is False), None)
            committed = (False if missing_on is not None
                         else True if verdicts and all(found for found, _ in verdicts) else None)
            has_evidence_row = has_filled_verify_row(tid) if committed is None else committed
            has_trace = trace_shows_verification(tid)
            if committed is False and has_filled_verify_row(tid):
                uncommitted.append(UNCOMMITTED_ROW_MESSAGE.format(tid=tid, branch=missing_on))
            elif not has_evidence_row or not has_trace:
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

        blockers.extend(uncommitted)

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
