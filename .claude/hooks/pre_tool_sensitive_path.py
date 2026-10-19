#!/usr/bin/env python3
"""
PreToolUse hook (T146) — fires before every Edit, Write and Bash tool call.

Asks the human first when the call touches a path listed in
`.claude/sensitive-paths.txt` (`.env*`, secrets, production configs, infra),
unless the active task's guide predicted that exact path under
`## Files to Change (Predicted)`.

Decisions, and the direction every uncertainty resolves:

* Sensitive and not predicted -> `ask`, the reason naming the path and pattern.
* Sensitive and predicted, or not sensitive -> no output, exit 0: "no decision,
  normal permission flow applies". Deliberately NOT `allow` — `allow` skips the
  permission prompt for the *whole* call, which grants more than this hook's
  concern (see tasks/TASK_REVIEW_T146.md, "Assumption check").
* Malformed stdin, an unreadable pattern file, or a helper module that fails to
  import -> `ask`. Fail toward the human, never a silent allow (AC5).

Board mode `online` (T157, NFR-005): guides are pulled from the board, whose text anyone
with workspace access can write, so no guide's prediction exempts a sensitive path — it
always asks. An unusable `.claude/board.json` counts as online here (the safe side).

Bash: the command's heredoc bodies and its *data* quoted spans are removed with
`lib/shell_data.py` first — the only sanctioned way to separate command text from
data (T099's three fail-opens came from fresh regexes). Quoted spans T099 classes
as executable are kept, so `bash -c "cat > .env"` still asks. What is left is
split into tokens and each token is checked as a path.

Recorded limitations (cut list, TASK_GUIDE_T146):
* Paths built from variables (`cat "$F"`) are not resolved.
* A Bash command that only *reads* a sensitive path (`grep KEY .env`) asks too —
  reads and writes are not cheaply distinguishable in a command string.
"""
import glob
import itertools
import json
import os
import re
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_FILE_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
PATTERNS_RELPATH = os.path.join(".claude", "sensitive-paths.txt")
PREDICTED_HEADING = "Files to Change (Predicted)"
# What is passed to read_guide_section: its slicer puts `\b` after the heading,
# which can never match after a closing `)`. The slicer accepts a trailing
# qualifier, so the bare prefix resolves `## Files to Change (Predicted)`.
PREDICTED_LOOKUP = "Files to Change"
TAG = "[hook:sensitive-path]"

# Guarded like pre_bash_block_unsafe_merge.py: an unguarded ImportError exits 1
# with empty stdout, which the harness treats as a non-blocking error and lets
# the call through — the silent allow AC5 forbids. The failure is kept and
# turned into an `ask` in main().
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from guide_sections import read_guide_section  # noqa: E402
    from shell_data import strip_heredoc_bodies, strip_quoted_spans  # noqa: E402
    from task_context import resolve_task_id  # noqa: E402
    from board.moments import board_mode  # noqa: E402
    IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - exercised via subprocess test
    IMPORT_ERROR = exc

# Where a shell token ends. Quote characters are separators too, because a
# quoted span T099 keeps as code (`bash -c "cat > .env"`) arrives with its quotes.
TOKEN_SPLIT_PATTERN = re.compile(r"[\s;&|<>()`'\"=]+")
GLOB_CHARS = re.compile(r"[*?\[]")
MAX_GLOB_MATCHES = 200
BACKTICK_SPAN_PATTERN = re.compile(r"`([^`]+)`")
# A quoted word right after an output redirect (`>`, `>>`, `>|`, `&>`, `2>`).
# strip_quoted_spans treats every quoted span behind `echo`/`printf` as data,
# but a redirect target is where the output is written, not data.
QUOTED_REDIRECT_TARGET_PATTERN = re.compile(r"""(?:&|\d*)>[>|]?\s*(?:"([^"]*)"|'([^']*)')""")


def project_dir():
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    return env_root if env_root else _FILE_ROOT


# --- Pattern file ------------------------------------------------------------

def expand_braces(pattern):
    """`prod*.{yml,json}` -> [`prod*.yml`, `prod*.json`]. Nested groups recurse."""
    match = re.search(r"\{([^{}]*)\}", pattern)
    if not match:
        return [pattern]
    head, tail = pattern[:match.start()], pattern[match.end():]
    expanded = []
    for option in match.group(1).split(","):
        expanded.extend(expand_braces(head + option + tail))
    return expanded


def glob_to_regex(glob_pattern):
    """Translate one brace-free glob: `*` stays in a directory, `**` crosses them."""
    out = []
    i = 0
    while i < len(glob_pattern):
        if glob_pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob_pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob_pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob_pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob_pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def parse_patterns(text):
    """Return `[(raw_line, negated, has_slash, [compiled regex, ...]), ...]`.

    Windows separators are normalised to `/`. A pattern with no `/` matches a
    file name in any directory; one with a `/` matches from the project root.
    """
    patterns = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        negated = raw.startswith("!")
        body = raw[1:] if negated else raw
        body = body.replace("\\", "/").lstrip("/")
        if not body:
            continue
        regexes = [glob_to_regex(g) for g in expand_braces(body)]
        patterns.append((raw, negated, "/" in body, regexes))
    return patterns


def load_patterns(path):
    """Read and parse the pattern file. Raises OSError when it is unreadable."""
    with open(path, encoding="utf-8") as f:
        return parse_patterns(f.read())


# --- Path matching -----------------------------------------------------------

def _within(path, root):
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        return None
    if rel == "." or rel == ".." or rel.startswith(".." + os.sep):
        return None
    return rel.replace(os.sep, "/")


def path_forms(path, cwd, roots):
    """Every form a path is checked in, as `(anchored, path_string)` pairs.

    Anchored: relative to a root it lies under (the project dir or the call's
    cwd — a Stage 3 agent's cwd is its own worktree). Both the path as given and
    its resolved form are checked, so a symlink cannot route around a pattern.
    A path under no root is *floating*: a `/` pattern may match from any of its
    directories, which over-asks rather than guesses an anchor.
    """
    path = path.replace("\\", "/")
    absolute = os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))
    forms = []
    for candidate in {absolute, os.path.realpath(absolute)}:
        anchored = [rel for rel in (_within(candidate, r) for r in roots) if rel]
        if anchored:
            forms.extend((True, rel) for rel in anchored)
        else:
            forms.append((False, candidate.replace(os.sep, "/").lstrip("/")))
    return forms


def _pattern_matches(has_slash, regexes, anchored, path_string):
    if not has_slash:
        name = path_string.rsplit("/", 1)[-1]
        return any(rx.match(name) for rx in regexes)
    # Each path is also tried as a directory, so `infra/**` covers `infra`
    # itself: `rm -rf infra` removes the whole tree the pattern protects.
    if anchored:
        candidates = [path_string]
    else:
        parts = path_string.split("/")
        candidates = ["/".join(parts[i:]) for i in range(len(parts))]
    return any(rx.match(c) or rx.match(c + "/") for rx in regexes for c in candidates)


def matching_pattern(forms, patterns):
    """The pattern line that marks this path sensitive, or None. Last match wins."""
    for anchored, path_string in forms:
        verdict = None
        for raw, negated, has_slash, regexes in patterns:
            if _pattern_matches(has_slash, regexes, anchored, path_string):
                verdict = None if negated else raw
        if verdict:
            return verdict
    return None


# --- Bash tokens -------------------------------------------------------------

def command_tokens(command, cwd):
    """Path-like tokens of the command text left after shell_data strips data.

    A token carrying glob characters is expanded against the filesystem the way
    the shell would (`cat .env*`), and kept as written too. Quoted redirect
    targets are collected before shell_data strips them as data (`echo x > ".env"`).
    """
    unheredoc = strip_heredoc_bodies(command)
    tokens = [double or single
              for double, single in QUOTED_REDIRECT_TARGET_PATTERN.findall(unheredoc)
              if double or single]
    text = strip_quoted_spans(unheredoc)
    for token in TOKEN_SPLIT_PATTERN.split(text):
        if not token:
            continue
        tokens.append(token)
        if GLOB_CHARS.search(token):
            matches = glob.iglob(os.path.join(cwd, token), recursive=True)
            tokens.extend(itertools.islice(matches, MAX_GLOB_MATCHES))
    return tokens


# --- Predicted paths ---------------------------------------------------------

def predicted_paths(task_id, tasks_dirs):
    """Backticked paths in the first column of the task's predicted-files table."""
    if not task_id:
        return set()
    for tasks_dir in tasks_dirs:
        body = read_guide_section(task_id, PREDICTED_LOOKUP, tasks_dir)
        if body is None:
            continue
        paths = set()
        for line in body.splitlines():
            cells = line.strip().strip("|").split("|")
            if not line.strip().startswith("|") or not cells:
                continue
            for span in BACKTICK_SPAN_PATTERN.findall(cells[0]):
                normalized = span.strip().replace("\\", "/")
                while normalized.startswith("./"):
                    normalized = normalized[2:]
                if normalized:
                    paths.add(normalized)
        return paths
    return set()


def is_predicted(forms, predicted):
    return any(anchored and path_string in predicted for anchored, path_string in forms)


# --- Hook protocol -----------------------------------------------------------

def ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"{TAG} {reason}",
        }
    }))
    sys.exit(0)


def candidate_paths(tool_name, tool_input, cwd):
    if tool_name in ("Edit", "Write"):
        file_path = tool_input.get("file_path")
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError(f"{tool_name} call has no file_path")
        return [file_path]
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise ValueError("Bash call has no command string")
    return command_tokens(command, cwd)


def main():
    if IMPORT_ERROR is not None:
        ask(f"Sensitive-path check unavailable ({type(IMPORT_ERROR).__name__}: "
            f"{IMPORT_ERROR}) — cannot tell whether this call touches a sensitive "
            "path. Restore .claude/hooks/lib/.")

    try:
        event = json.load(sys.stdin)
        tool_name = event["tool_name"]
        tool_input = event["tool_input"]
        if not isinstance(tool_input, dict):
            raise ValueError("tool_input is not an object")
    except Exception as exc:
        ask(f"Malformed hook input ({type(exc).__name__}: {exc}) — cannot tell "
            "whether this call touches a sensitive path.")

    if tool_name not in ("Edit", "Write", "Bash"):
        sys.exit(0)

    root = project_dir()
    patterns_file = os.path.join(root, PATTERNS_RELPATH)
    try:
        patterns = load_patterns(patterns_file)
    except Exception as exc:
        ask(f"Sensitive-path list unreadable ({patterns_file}: "
            f"{type(exc).__name__}) — cannot tell whether this call touches a "
            "sensitive path. Restore .claude/sensitive-paths.txt.")

    try:
        cwd = event.get("cwd") if isinstance(event.get("cwd"), str) else None
        cwd = cwd or os.getcwd()
        roots = [root, cwd]
        hits = []
        for path in candidate_paths(tool_name, tool_input, cwd):
            forms = path_forms(path, cwd, roots)
            pattern = matching_pattern(forms, patterns)
            if pattern:
                hits.append((path, forms, pattern))
        if not hits:
            sys.exit(0)

        task_id = resolve_task_id(event)
        board_text = any(board_mode(r) != "local" for r in roots)
        predicted = set() if board_text else predicted_paths(
            task_id, [os.path.join(root, "tasks"), os.path.join(cwd, "tasks")]
        )
        unpredicted = [(p, pat) for p, forms, pat in hits if not is_predicted(forms, predicted)]
        if not unpredicted:
            sys.exit(0)
    except SystemExit:
        raise
    except Exception as exc:
        ask(f"Sensitive-path check failed ({type(exc).__name__}: {exc}) — "
            "asking rather than guessing.")

    listed = ", ".join(f"{p} (pattern `{pat}`)" for p, pat in unpredicted)
    owner = (f"the active task {task_id} does not list it under '## {PREDICTED_HEADING}'"
             if task_id else "no active task predicts it")
    if board_text:
        owner = ("board mode is online, where guides come from the board and cannot "
                 "pre-authorise a sensitive path")
    ask(f"This {tool_name} call touches a sensitive path: {listed}. "
        f"Listed in .claude/sensitive-paths.txt and {owner}.")


if __name__ == "__main__":
    main()
