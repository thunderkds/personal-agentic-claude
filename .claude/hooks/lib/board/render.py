"""Board → board cache, in today's exact file formats (T154, FR-002, FR-005, FR-012).

Board-independent: takes `Task`s, returns text. `render_kanban` produces a
`PROJECT_KANBAN.md` every existing hook parses unchanged; `guide_files` maps each
task's description, verbatim, to `tasks/TASK_GUIDE_<ID>.md`.

Board text is untrusted (NFR-005). A row is one line built by this module; every board
field placed in it is flattened to one line and has the characters the hooks parse
escaped, so no title can open a section (`### Done`), forge a row (`- [ ] **T999**`),
or add a `| field`. Labels and assignees are reduced to fixed shapes.
"""
import re
import sys
import unicodedata

from board.config import PATH_SAFE_ID

SECTIONS = ("Todo", "In Progress", "Ready for Review", "Done", "Closed")
HEADINGS = {"Closed": "Closed (will not do)"}
CHECKBOX = {"Done": "x", "Closed": "~"}

# FR-012. Board status name → board cache section. `status_map` in `.claude/board.json`
# overrides or extends it (teams rename states); a name in neither falls back on the
# board's state type, so a renamed "started" state still blocks the merge gate.
DEFAULT_STATUS_MAP = {
    "Backlog": "Todo", "Triage": "Todo", "Todo": "Todo",
    "In Progress": "In Progress", "In Review": "Ready for Review", "Done": "Done",
    "Canceled": "Closed", "Cancelled": "Closed", "Duplicate": "Closed",
}
STATE_TYPE_MAP = {
    "triage": "Todo", "backlog": "Todo", "unstarted": "Todo", "started": "In Progress",
    "completed": "Done", "canceled": "Closed",
}
RISKS = {"low": "Low", "med": "Medium", "medium": "Medium", "high": "High"}

HEADER = """# PROJECT_KANBAN.md
**Last updated**: {today}

> Board cache, pulled from the board by `python3 scripts/board_sync.py pull`. Do not edit it by hand:
> the board is the source of truth, and the next pull overwrites this file.

---

## Board
"""
FOOTER = """## Blocked

---

## Stage Tracker
"""
AGENT = re.compile(r"Assigned\s+Agent\*{0,2}[:\s]+([a-z\-]+)", re.IGNORECASE)


def one_line(text):
    """Every whitespace or control character (each line break `str.splitlines` honours
    among them) becomes one space."""
    chars = (" " if ch.isspace() or unicodedata.category(ch).startswith("C") else ch
             for ch in str(text or ""))
    return " ".join("".join(chars).split())


def escape(text):
    """One line, with the characters the KANBAN parsers key on backslash-escaped."""
    return re.sub(r"([\\`*#|])", r"\\\1", one_line(text))


def assignee_token(name):
    """`@<token>` field value: letters, digits, `.`, `_`, `-` only, or None."""
    token = re.sub(r"[^A-Za-z0-9._-]", "", one_line(name))
    return token or None


def section_for(task, status_map):
    section = status_map.get(task.status) or STATE_TYPE_MAP.get(task.status_type)
    if section is None:
        print(f"[board] {task.id}: unmapped status {one_line(task.status)!r}; shown as Todo",
              file=sys.stderr)
    return section or "Todo"


def merged_status_map(config_map):
    merged = dict(DEFAULT_STATUS_MAP)
    for name, section in (config_map or {}).items():
        if section in SECTIONS:
            merged[name] = section
        else:
            print(f"[board] status_map: ignoring {one_line(name)!r} → {one_line(section)!r} "
                  f"(not one of {', '.join(SECTIONS)})", file=sys.stderr)
    return merged


def label_fields(labels):
    complexity, risk = "?", "?"
    for label in labels or []:
        m = re.fullmatch(r"complexity:(c[0-3])", str(label).strip(), re.IGNORECASE)
        if m:
            complexity = m.group(1).upper()
        m = re.fullmatch(r"risk:([a-z]+)", str(label).strip(), re.IGNORECASE)
        if m and m.group(1).lower() in RISKS:
            risk = RISKS[m.group(1).lower()]
    return complexity, risk


def row(task, section):
    agent = AGENT.search(task.description or "")
    complexity, risk = label_fields(task.labels)
    fields = [f"- [{CHECKBOX.get(section, ' ')}] **{task.id}** — {escape(task.title)}",
              agent.group(1) if agent else "?", complexity, f"Risk: {risk}",
              task.priority if task.priority in ("P0", "P1", "P2") else "?"]
    who = assignee_token(task.assignee)
    if who:
        fields.append(f"@{who}")
    fields.append(f"Guide: `tasks/TASK_GUIDE_{task.id}.md`" if task.description
                  else "Guide: missing")
    return " | ".join(fields)


# A board ID that may name a file and sit inside `**…**`: a strict subset of
# PATH_SAFE_ID with at most one leading `#` (GitHub `#170`), so no ID spells `###`.
ROW_SAFE_ID = re.compile(r"\A#?[A-Z0-9][A-Z0-9_-]{0,62}\Z")


def safe_tasks(tasks, warn=True):
    """Tasks whose ID is row- and path-safe; the rest are skipped (with a warning)."""
    kept = []
    for task in tasks:
        task_id = str(task.id)
        if ROW_SAFE_ID.match(task_id) and PATH_SAFE_ID.match(task_id):
            kept.append(task)
        elif warn:
            print(f"[board] skipping task with unsafe ID {one_line(task_id)!r}", file=sys.stderr)
    return kept


def sort_key(task):
    m = re.fullmatch(r"(.*?)(\d+)", task.id)
    return (m.group(1), int(m.group(2))) if m else (task.id, 0)


def render_kanban(tasks, status_map=None, today=""):
    status_map = merged_status_map(status_map)
    by_section = {s: [] for s in SECTIONS}
    for task in safe_tasks(tasks):
        by_section[section_for(task, status_map)].append(task)
    parts = [HEADER.format(today=today)]
    for section in SECTIONS:
        rows = [row(t, section) for t in sorted(by_section[section], key=sort_key)]
        parts.append("\n".join([f"### {HEADINGS.get(section, section)}", *rows]) + "\n")
    parts.append(FOOTER)
    return "\n".join(parts)


# Sections a reviewer fills (T064): the merge and spawn gates read them guide-first, so a
# board description that carried one could forge gate input (Stage 4, NFR-005). Matched
# like `guide_sections.slice_section`, and every occurrence is vacated to a pointer, which
# `guide_sections` treats as absent and resolves from `tasks/TASK_REVIEW_<ID>.md`.
REVIEW_SECTION = re.compile(r"^(#{2,3}\s*(?:Evidence|Demonstration)\b[^\n]*)$.*?(?=^#{2,3}\s|\Z)",
                            re.MULTILINE | re.DOTALL | re.IGNORECASE)


def vacate_review_sections(description, task_id):
    pointer = (f"\\1\n\n> **Moved.** See `tasks/TASK_REVIEW_{task_id}.md` "
               "(review sections are never taken from the board).\n\n")
    return REVIEW_SECTION.sub(pointer, description)


def guide_files(tasks):
    """`{"tasks/TASK_GUIDE_<ID>.md": description}` for each task with a description,
    verbatim except that any Evidence/Demonstration section is vacated to a pointer."""
    return {f"tasks/TASK_GUIDE_{t.id}.md": vacate_review_sections(t.description, t.id)
            for t in safe_tasks(tasks, warn=False) if t.description}


# --- Decision Log (T158, FR-008) ---------------------------------------------------
#
# The board document and the `memory/decisions.md` board section share one line shape:
#     - 2026-10-19  Retry 3 times  (from ENG-170, by alice)
# The document line may end with ` <!--bs:<key>-->`, the dedupe key. Text is untrusted
# (NFR-005): one line, with every character the parsers key on backslash-escaped, so it can
# neither end the line's attribution nor open a header, a `**Files**:` line or a marker. A
# line read back must already be in that shape (`DECISION_LINE`), so rendering is idempotent: `Decision.text` is plain text everywhere (unescaped when
# parsed, escaped exactly once by `format_decision`)
# and a hand-edited document line that is not skipped cannot carry anything either.

DECISIONS_HEADING = "### Decision Log (pulled from the board — do not edit)"
DECISIONS_BEGIN = "<!-- board-decisions:begin -->"
DECISIONS_END = "<!-- board-decisions:end -->"
DECISIONS_TITLE = "Project Decisions"
SPECIALS = "\\`*#|()<>"
DECISION_LINE = re.compile(
    r"- (\d{4}-\d{2}-\d{2})  ((?:[^\\`*#|()<>]|\\[\\`*#|()<>])+)  "
    r"\(from ([A-Z0-9#_-]{1,64}), by ([A-Za-z0-9._-]{1,64})\)(?: <!--bs:([0-9a-f]{16})-->)?")


def escape_decision(text):
    return re.sub(f"([{re.escape(SPECIALS)}])", r"\\\1", one_line(text))


def unescape_decision(text):
    return re.sub(f"\\\\([{re.escape(SPECIALS)}])", r"\1", text)


def format_decision(decision, with_key=True):
    line = (f"- {decision.date}  {escape_decision(decision.text)}  "
            f"(from {decision.task_id}, by {assignee_token(decision.author) or 'unknown'})")
    return f"{line} <!--bs:{decision.key}-->" if with_key and decision.key else line


def parse_decision_lines(text):
    """`Decision`s from every well-formed entry line of `text`, in order; others are skipped."""
    from board.base import Decision
    found = []
    for line in text.splitlines():
        m = DECISION_LINE.fullmatch(line)
        if m:
            found.append(Decision(date=m.group(1), text=unescape_decision(m.group(2)),
                                  task_id=m.group(3),
                                  author=m.group(4), key=m.group(5) or ""))
    return found


def decision_document(decisions):
    return "\n".join([f"# {DECISIONS_TITLE}", "", *(format_decision(d) for d in decisions)]) + "\n"


def render_decisions_section(decisions):
    lines = [DECISIONS_BEGIN, DECISIONS_HEADING, ""]
    lines += [format_decision(d, with_key=False) for d in decisions]
    return "\n".join([*lines, DECISIONS_END]) + "\n"


def board_section(text):
    """The text between the board-decisions markers of a cache file ('' if there are none)."""
    start = text.find(DECISIONS_BEGIN)
    end = text.find(DECISIONS_END, start + 1) if start >= 0 else -1
    return text[start:end] if end >= 0 else ""


def cached_decisions(text):
    return parse_decision_lines(board_section(text))


def merge_decisions_file(existing, section):
    """`existing` with its board section replaced by `section`; local content is untouched.
    No section yet: it is appended after the local content."""
    start = existing.find(DECISIONS_BEGIN)
    end = existing.find(DECISIONS_END, start + 1) if start >= 0 else -1
    if end >= 0:
        return existing[:start] + section + existing[end + len(DECISIONS_END) + 1:]
    if not existing:
        return section
    return existing.rstrip("\n") + "\n\n" + section
