#!/usr/bin/env python3
"""Sync the board cache with the board: `pull` (T154), `push`, `flush`, `status` (T156).

    python3 scripts/board_sync.py pull
    python3 scripts/board_sync.py push status <ID> {todo,in-progress,ready-for-review,done}
    python3 scripts/board_sync.py push comment <ID> <milestone> <text...>
    python3 scripts/board_sync.py flush
    python3 scripts/board_sync.py status
    python3 scripts/board_sync.py init

`init` (T155) is the one interactive command: it asks how to connect, which team and project,
and writes `.claude/board.json` (nothing secret). No terminal, or a "no", changes nothing.

`push` sends at once (FR-009); when the board is unreachable (network error, timeout, 5xx,
429) the write is appended to `.board/outbox.jsonl` with a dedupe key and the command still
exits 0 with a `queued` notice. `flush` replays the queue in order; a comment already on the
board (matched by the key embedded in it) is dropped, not reposted. `status` prints
`N unsynced` for `wake`. With `git_auto_status: true` in `.claude/board.json`, Linear's git
integration owns In Progress/Done and `push status` refuses them. Milestones only
(started, red, green, review, verify, merged, blocked, question) — no free-form streaming.

    python3 scripts/board_sync.py decide <ID> "<text>"

`decide` (T158) appends a dated, attributed entry linked to <ID> to the Decision Log, one
shared board document (`decision_doc` in board.json, default "Project Decisions"; created on
first use). It goes through the same outbox as `push`. `pull` renders the log into the board
section of `memory/decisions.md`; content outside that section is never touched.

    python3 scripts/board_sync.py create --guide <draft.md>
    python3 scripts/board_sync.py update --guide <ID>

`create` (T159) is Stage 2 in board mode: the board assigns the task ID, the issue is created
with the draft's title, priority, `complexity:`/`risk:` labels, the board user as assignee and
the draft (minus its local title line) as description, and `tasks/TASK_GUIDE_<ID>.md` is
written from the board's copy. `update --guide <ID>` pushes the local guide back to the
description. Neither goes through the outbox: a new ID cannot be queued, and a failure exits 1
with nothing written. A draft missing Complexity, Risk or Priority is refused (exit 2).

    python3 scripts/board_sync.py triage [--mark]

`triage` (T160, FR-011) prints one line per *my* task (assignee == `me`) that is not Done or
closed and either has an incomplete guide (`guide_sections.missing_guide_sections`) or is new
to me / changed since the last-session marker `.board/triage_seen.json`:
`<ID> · <P0-P2|untriaged> · <reason> · <title>` — the title last, flattened to one line.
Teammates' tasks are never listed. Read-only unless `--mark`, which then records the hash of
each of my tasks' descriptions; `pull_moment.py wake` runs `triage --mark`, so a change shows
at one wake. With no marker yet, only incomplete guides are listed. Online mode only (exit 2).

Board mode `online` (`.claude/board.json` names a `board`): fetch every task of the
configured team/project and rewrite the board cache in today's formats —
`PROJECT_KANBAN.md` and `tasks/TASK_GUIDE_<ID>.md` (each issue description, verbatim).
The board is the whole truth: local rows the board lacks are dropped, with a warning.

Board mode `local` (no `.claude/board.json`, or no `board` in it): does nothing, exit 0.

Nothing is written until the whole board has been read; each file is then replaced via a
temp file + `os.replace`. Any failure exits non-zero and leaves the cache untouched.
`LINEAR_API_KEY` is read from the environment only and never printed (NFR-001).

Exit codes: 0 pulled (or local mode), 1 the board could not be read, 2 bad config.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks", "lib"))
from board import outbox, render  # noqa: E402
from board.base import BoardAuthError, BoardError, BoardUnavailable, Decision, Task  # noqa: E402
from board.config import board_id_pattern, config_path, load_config, normalize_task_id, task_id_pattern  # noqa: E402
from board.fake import FakeBoard  # noqa: E402
from board.linear import LinearBoard  # noqa: E402
from guide_sections import missing_guide_sections  # noqa: E402

KANBAN = "PROJECT_KANBAN.md"
MILESTONES = ("started", "red", "green", "review", "verify", "merged", "blocked", "question")
# CLI slug -> board cache section; the first two are what Linear's git integration moves.
STATUS_SECTIONS = {"todo": "Todo", "in-progress": "In Progress",
                   "ready-for-review": "Ready for Review", "done": "Done"}
GIT_OWNED = ("in-progress", "done")
DEFAULT_BOARD_NAMES = {"Todo": "Todo", "In Progress": "In Progress",
                       "Ready for Review": "In Review", "Done": "Done"}


class ConfigError(Exception):
    pass


def make_board(config, root):
    """(adapter, secret to redact or None) for the configured board."""
    kind = config.get("board")
    if kind == "linear":
        key = os.environ.get("LINEAR_API_KEY")
        if not key:
            raise ConfigError("LINEAR_API_KEY is not set. Add `export LINEAR_API_KEY=...` to your "
                              "shell profile; the key is never stored in a file")
        team = config.get("team")
        if not isinstance(team, str) or not team:
            raise ConfigError("`team` is missing from .claude/board.json")
        return LinearBoard(key, team, config.get("project") or None), key
    if kind == "fake":
        return FakeBoard.from_file(os.path.join(root, str(config.get("fake_board", "")))), None
    raise ConfigError(f"unknown board {render.one_line(kind)!r} in .claude/board.json")


def write_atomically(root, files):
    """Write every file to a temp file in its own directory, then `os.replace` them all."""
    staged = []
    try:
        for rel, text in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".board-tmp-")
            staged.append((tmp, path))
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        for tmp, path in staged:
            os.replace(tmp, path)
    finally:
        for tmp, _ in staged:
            if os.path.exists(tmp):
                os.unlink(tmp)


def dropped_local_rows(root, board_ids):
    try:
        with open(os.path.join(root, KANBAN), encoding="utf-8") as f:
            old = f.read()
    except OSError:
        return []
    pattern = task_id_pattern(root)
    found = re.findall(rf"^\s*-\s*\[.\]\s*\*\*({pattern})\*\*", old, re.MULTILINE)
    return sorted(set(found) - set(board_ids))


def pull(board, config, root):
    tasks = board.list_tasks()
    status_map = config.get("status_map")
    kanban = render.render_kanban(tasks, status_map if isinstance(status_map, dict) else None,
                                  today=date.today().isoformat())
    guides = render.guide_files(tasks)
    dropped = dropped_local_rows(root, [t.id for t in tasks])
    if dropped:
        print(f"[board] the board has no {', '.join(dropped)}; their local rows were dropped "
              f"(online mode: the board is the source of truth)", file=sys.stderr)
    extra = decisions_cache(board, config, root)
    write_atomically(root, {**guides, KANBAN: kanban, **extra})
    print(f"[board] pulled {len(tasks)} tasks: {KANBAN} and {len(guides)} guides written")
    return 0


DECISIONS_FILE = "memory/decisions.md"


def use_decision_doc(board, config):
    name = config.get("decision_doc")
    if isinstance(name, str) and name.strip() and hasattr(board, "decision_doc"):
        board.decision_doc = render.one_line(name)


def decisions_cache(board, config, root):
    """{DECISIONS_FILE: text} with the Decision Log in its board section, or {} when there is
    nothing to write (no entries and no section yet). Read before anything is written."""
    try:
        decisions = board.read_decisions()
    except BoardError as exc:   # the log must never fail the task pull
        print(f"[board] Decision Log not read ({exc}); {DECISIONS_FILE} left as is", file=sys.stderr)
        return {}
    try:
        with open(os.path.join(root, DECISIONS_FILE), encoding="utf-8") as f:
            existing = f.read()
    except OSError:
        existing = ""
    if not decisions and render.DECISIONS_BEGIN not in existing:
        return {}
    return {DECISIONS_FILE: render.merge_decisions_file(
        existing, render.render_decisions_section(decisions))}


def board_status_name(config, section):
    """The board's own name for a cache section: a `status_map` entry wins over the default."""
    status_map = config.get("status_map")
    if isinstance(status_map, dict):
        for name, mapped in status_map.items():
            if mapped == section and isinstance(name, str) and name:
                return name
    return DEFAULT_BOARD_NAMES[section]


def dedupe_key(task, milestone, text, created):
    return hashlib.sha256("\0".join((task, milestone, text, created)).encode()).hexdigest()[:16]


def comment_body(milestone, text, key):
    return f"[{milestone}] {text}\n\n— board-sync:{key}"


def deliver(board, entry):
    """Send one outbox entry. A comment already on the board is a success without a repost."""
    if entry.get("kind") == "comment":
        if board.has_comment(entry["task"], f"board-sync:{entry['key']}"):
            return
        board.add_comment(entry["task"], comment_body(entry["milestone"], entry["text"], entry["key"]))
    elif entry.get("kind") == "status":
        board.set_status(entry["task"], entry["name"])
    elif entry.get("kind") == "decision":
        board.append_decision(Decision(date=entry["date"], text=entry["text"], task_id=entry["task"],
                                       author=entry.get("author"), key=entry["key"]))
    else:
        raise BoardError("unknown outbox entry")


def replay(board, root):
    """Flush the outbox; returns the error that stopped it, or None."""
    def dropped(entry, exc):  # never the text or the key
        print(f"[board] dropped a queued {entry.get('kind')} for {entry.get('task')} "
              f"({entry.get('milestone')}): the board refused it ({exc})", file=sys.stderr)

    done, remaining, error = outbox.flush(root, lambda entry: deliver(board, entry), dropped)
    if done:
        print(f"[board] flushed {done} queued write(s)")
    if error is not None:
        if not isinstance(error, BoardError):
            error = BoardError(f"unexpected {type(error).__name__}")
        print(f"[board] {remaining} write(s) still queued: {error}", file=sys.stderr)
    return error


def flush(board, root):
    return 1 if replay(board, root) is not None else 0


def push(board, config, root, args):
    task = normalize_task_id(args.id)
    if not re.fullmatch(task_id_pattern(root), task):
        print(f"[board] {render.one_line(args.id)!r} is not a task ID", file=sys.stderr)
        return 2
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.kind == "comment":
        milestone = args.value
        if milestone not in MILESTONES:
            print(f"[board] milestone must be one of: {', '.join(MILESTONES)}", file=sys.stderr)
            return 2
        text = " ".join(args.text).strip()
        key = os.environ.get("LINEAR_API_KEY")
        if key:
            text = text.replace(key, "[redacted]")
        text = text.replace("board-sync:", "board-sync -")  # no forged dedupe marker
        if not text:
            print("[board] a comment needs text", file=sys.stderr)
            return 2
        entry = {"kind": "comment", "task": task, "milestone": milestone, "text": text,
                 "key": dedupe_key(task, milestone, text, created), "created": created}
    else:
        if args.value not in STATUS_SECTIONS:
            print(f"[board] status must be one of: {', '.join(STATUS_SECTIONS)}", file=sys.stderr)
            return 2
        if config.get("git_auto_status") is True and args.value in GIT_OWNED:
            print(f"[board] git_auto_status is on: the git integration moves {args.value}; "
                  f"only todo and ready-for-review are pushed", file=sys.stderr)
            return 2
        name = board_status_name(config, STATUS_SECTIONS[args.value])
        entry = {"kind": "status", "task": task, "milestone": args.value, "name": name,
                 "key": dedupe_key(task, args.value, name, created), "created": created}
    try:
        if outbox.count(root):                       # older writes first
            error = replay(board, root)
            if isinstance(error, BoardAuthError):    # keep order: queue behind, tell the user
                outbox.append(root, entry)
                return 1
            if error is not None:
                raise BoardUnavailable("earlier writes are still queued")
        deliver(board, entry)
    except BoardUnavailable:
        outbox.append(root, entry)
        print(f"[board] board unreachable: queued {entry['kind']} for {task} "
              f"({outbox.count(root)} unsynced); run `board_sync.py flush` later")
        return 0
    print(f"[board] pushed {entry['kind']} for {task}")
    return 0


def decide(board, config, root, args):
    task = normalize_task_id(args.id)
    if not re.fullmatch(task_id_pattern(root), task):
        print(f"[board] {render.one_line(args.id)!r} is not a task ID", file=sys.stderr)
        return 2
    text = render.one_line(" ".join(args.text))
    key = os.environ.get("LINEAR_API_KEY")
    if key:
        text = text.replace(key, "[redacted]")
    if not text:
        print("[board] a decision needs text", file=sys.stderr)
        return 2
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    me = config.get("me")
    entry = {"kind": "decision", "task": task, "milestone": "decision", "text": text,
             "date": date.today().isoformat(),
             "author": render.assignee_token(me) if isinstance(me, str) else None,
             "key": dedupe_key(task, "decision", text, created), "created": created}
    try:
        if outbox.count(root):                       # older writes first
            error = replay(board, root)
            if isinstance(error, BoardAuthError):
                outbox.append(root, entry)
                return 1
            if error is not None:
                raise BoardUnavailable("earlier writes are still queued")
        deliver(board, entry)
    except BoardUnavailable:
        outbox.append(root, entry)
        print(f"[board] board unreachable: queued decision for {task} "
              f"({outbox.count(root)} unsynced); run `board_sync.py flush` later")
        return 0
    except BoardAuthError:
        outbox.append(root, entry)
        raise
    print(f"[board] decision recorded for {task}")
    return 0


# ── create / update (T159) ───────────────────────────────────────────────────
# Copied from `.claude/hooks/post_write_register_task.py` (its regexes are inline in `main()`,
# so they cannot be imported). The title pattern differs: a draft's ID is still a placeholder.
DRAFT_TITLE = re.compile(r"^#\s+TASK_GUIDE\s*[—–-]+\s*\S+?:\s*(.+)$", re.MULTILINE)
DRAFT_FIELDS = (
    ("Complexity", r"Complexity(?:\s+Level)?\*{0,2}[:\s]+\*{0,2}(C[0-3])"),
    ("Risk", r"Risk(?:\s+Level)?\*{0,2}[:\s]+\*{0,2}(Low|Med(?:ium)?|High)"),
    ("Priority", r"Priority\*{0,2}[:\s]+\*{0,2}(P[0-2])"),
)


def parse_draft(text):
    """(Task, []) for a complete draft, else (None, names of the missing fields)."""
    found, missing = {}, []
    title = DRAFT_TITLE.search(text)
    if not title or not render.one_line(title.group(1)):
        missing.append("title (`# TASK_GUIDE — <ID>: <title>`)")
    for name, pattern in DRAFT_FIELDS:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            found[name] = m.group(1)
        else:
            missing.append(name)
    if missing:
        return None, missing
    risk = "medium" if found["Risk"].lower().startswith("med") else found["Risk"].lower()
    body = (text[:title.start()] + text[title.end():]).lstrip("\n")
    return Task(id="", title=render.one_line(title.group(1)), status="",
                priority=found["Priority"].upper(),
                labels=[f"complexity:{found['Complexity'].lower()}", f"risk:{risk}"],
                description=body), []


def create(board, root, args):
    try:
        with open(args.guide, encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        print(f"[board] cannot read the draft guide {render.one_line(args.guide)!r}", file=sys.stderr)
        return 2
    task, missing = parse_draft(text)
    if task is None:
        print(f"[board] the draft is missing: {', '.join(missing)}; nothing created", file=sys.stderr)
        return 2
    try:
        new_id = board.create_task(task)
    except BoardError as exc:
        raise BoardError(f"{exc}. A new task's ID comes from the board, so a create cannot be "
                         f"queued; nothing was written. If it timed out, check the board for the "
                         f"issue before retrying") from None
    if not (render.safe_tasks([Task(id=new_id, title="", status="")], warn=False)):
        print(f"[board] the board returned an unusable task ID {render.one_line(new_id)!r}; "
              f"no guide written", file=sys.stderr)
        return 1
    description = task.description
    try:
        held = board.get_task(new_id)
        if held is not None and held.description:
            description = held.description
    except BoardError:
        print(f"[board] {new_id} was created but not read back; its guide is the draft you sent",
              file=sys.stderr)
    cache = render.guide_files([Task(id=new_id, title="", status="", description=description)])
    write_atomically(root, cache)
    print(f"[board] created {new_id}: {', '.join(cache)} written")
    return 0


def update(board, root, args):
    task_id = normalize_task_id(args.guide)
    if not re.fullmatch(task_id_pattern(root), task_id):
        print(f"[board] {render.one_line(args.guide)!r} is not a task ID", file=sys.stderr)
        return 2
    try:
        with open(os.path.join(root, "tasks", f"TASK_GUIDE_{task_id}.md"), encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        print(f"[board] no readable tasks/TASK_GUIDE_{task_id}.md to push", file=sys.stderr)
        return 2
    try:
        board.update_task(Task(id=task_id, title="", status="",
                               description=render.vacate_review_sections(text, task_id)))
    except BoardError as exc:
        raise BoardError(f"{exc}. The guide edit was not queued; run update again when the "
                         f"board is reachable") from None
    print(f"[board] pushed the guide of {task_id} to its description")
    return 0


# ── triage (T160) ────────────────────────────────────────────────────────────
TRIAGE_SEEN = os.path.join(".board", "triage_seen.json")


def read_triage_seen(root):
    """{task ID: description hash} from the last `--mark`; None when there is no marker yet,
    {} when it is unreadable (then every task of mine shows as new: the side that hides nothing)."""
    path = os.path.join(root, TRIAGE_SEEN)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            seen = json.load(f)
    except (OSError, ValueError):
        return {}
    return seen if isinstance(seen, dict) else {}


def triage(board, config, root, args):
    me = config.get("me")
    me = render.assignee_token(me) if isinstance(me, str) else None
    if not me:
        print("[board] triage needs `me` (your board user) in .claude/board.json", file=sys.stderr)
        return 2
    status_map = config.get("status_map")
    status_map = render.merged_status_map(status_map if isinstance(status_map, dict) else None)
    seen = read_triage_seen(root)
    mine, lines = {}, []
    for task in render.safe_tasks(board.list_tasks(), warn=False):
        if (render.assignee_token(task.assignee) or "").casefold() != me.casefold():
            continue
        digest = hashlib.sha256((task.description or "").encode("utf-8")).hexdigest()
        mine[task.id] = digest
        if render.section_for(task, status_map) in ("Done", "Closed"):
            continue
        missing = missing_guide_sections(task.description or "")
        if missing:
            reason = f"not planned (missing: {', '.join(missing)})"
        elif seen is None or seen.get(task.id) == digest:
            continue
        elif task.id not in seen:
            reason = "new to you since last session"
        else:
            reason = "changed since last session"
        priority = task.priority if task.priority in ("P0", "P1", "P2") else "untriaged"
        lines.append(f"{task.id} · {priority} · {reason} · {render.one_line(task.title)}")
    for line in lines:
        print(line)
    if args.mark:
        write_atomically(root, {TRIAGE_SEEN: json.dumps(mine, indent=1, sort_keys=True) + "\n"})
    return 0


# ── init (T155) ──────────────────────────────────────────────────────────────
MCP_COMMAND = "claude mcp add --transport http linear https://mcp.linear.app/mcp"
CONNECTIONS = {"1": "api", "2": "mcp", "3": "both"}


class InitAbort(Exception):
    """The user gave no usable answer; nothing is written."""


def tty_ask(prompt):
    """One line from the terminal, or None when there is no terminal (or EOF)."""
    try:
        # Separate handles: "r+" on a tty raises UnsupportedOperation (not seekable).
        with open("/dev/tty", "w", encoding="utf-8") as out, open("/dev/tty", encoding="utf-8") as tty:
            out.write(prompt)
            out.flush()
            line = tty.readline()
    except OSError:
        return None
    return line.strip() if line else None


def _choose(ask, title, options, default=None, zero=None):
    """Numbered menu -> the chosen index (0-based). `default` is returned on Enter; `zero` is an
    extra "0) label" entry that returns -1."""
    lines = [title] + ([f"  0) {zero}"] if zero else []) + [f"  {i}) {render.one_line(label)}" for i, label in enumerate(options, 1)]
    prompt = "\n".join(lines) + "\n> "
    for _ in range(3):
        answer = ask(prompt)
        if answer is None:
            raise InitAbort("no answer")
        if answer == "" and default is not None:
            return default
        if zero and answer == "0":
            return -1
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
    raise InitAbort("no valid choice")


def _yes(ask, prompt):
    answer = ask(prompt)
    if answer is None:
        raise InitAbort("no answer")
    return answer.lower() in ("y", "yes")


def _id_pattern_for(team_key):
    """`<TEAMKEY>-\\d+`, the key escaped; None when board.config would not accept it."""
    if not re.fullmatch(r"[A-Za-z0-9]+", team_key or ""):
        return None
    pattern = rf"{re.escape(team_key.upper())}-\d+"
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".claude"))
        with open(config_path(tmp), "w", encoding="utf-8") as f:
            json.dump({"id_pattern": pattern}, f)
        return board_id_pattern(tmp)


def _status_map(ask, states):
    """Ask once per state the default map does not place; Enter keeps the default by type."""
    mapping = {}
    for state in states:
        name = state.get("name") if isinstance(state, dict) else None
        if not isinstance(name, str) or not name or name in render.DEFAULT_STATUS_MAP:
            continue
        idx = _choose(ask, f"Which board section is the status {render.one_line(name)!r}? "
                           f"(Enter = by its type, {render.one_line(state.get('type'))})",
                      list(render.SECTIONS), default=-1)
        if idx >= 0:
            mapping[name] = render.SECTIONS[idx]
    return mapping


def _fetch_choices(adapter, ask):
    me = render.assignee_token(adapter.viewer())
    if not me:
        raise BoardError("Linear gave no usable user name")
    teams = [t for t in adapter.list_teams() if isinstance(t, dict) and t.get("id") and t.get("key")]
    if not teams:
        raise BoardError("this Linear account has no teams")
    team = teams[_choose(ask, "Which team?", [f"{t['key']}  {t.get('name', '')}" for t in teams])]
    projects = [p for p in adapter.list_projects(team["id"]) if isinstance(p, dict) and p.get("id")]
    pick = _choose(ask, "Which project?", [p.get("name", "") for p in projects],
                   zero="(whole team)") if projects else -1
    project = projects[pick]["id"] if pick >= 0 else ""
    status_map = _status_map(ask, adapter.list_states(team["id"]))
    return {"team": team["id"], "project": project, "me": me, "status_map": status_map}, team["key"]


def init(root, ask, make_adapter, env, out, err):
    """Ask the board questions and write `.claude/board.json`. 0 done or declined, 1 could not
    finish, 2 the answers would give a config board.config rejects. Never writes the API key."""
    asked = [False]

    def guarded(prompt):
        answer = ask(prompt)
        if answer is not None:
            asked[0] = True
        return answer

    key = env.get("LINEAR_API_KEY") or ""
    try:
        if os.path.exists(config_path(root)):
            if not _yes(guarded, ".claude/board.json already exists. Overwrite it? [y/N] "):
                return 0
        connection = CONNECTIONS[str(1 + _choose(guarded, "How should agents reach Linear?",
                                                 ["API key (LINEAR_API_KEY in your shell)",
                                                  "Linear MCP server", "both"]))]
        chosen = {}
        if connection in ("mcp", "both"):
            out("To add Linear's official MCP server, run this yourself (Easy Kit installs nothing):")
            out(f"  {MCP_COMMAND}")
        if connection == "mcp":
            team_key = guarded("Your Linear team key (for example ENG): ")
            name = guarded("Your Linear display name: ")
            if team_key is None or name is None:
                raise InitAbort("no answer")
            team_key = team_key.strip()
            me = render.assignee_token(name)
            if not me:
                err("[board] init: no usable user name; nothing written")
                return 1
            chosen = {"me": me, "status_map": {}}
        else:
            if not key:
                out("LINEAR_API_KEY is not set. Create a key in Linear (Settings > API) and add "
                    "`export LINEAR_API_KEY=...` to your shell profile, then run "
                    "`python3 scripts/board_sync.py init` again. The key is never stored in a file.")
                return 1
            chosen, team_key = _fetch_choices(make_adapter(key), guarded)
        pattern = _id_pattern_for(team_key)
        if pattern is None:
            err(f"[board] init: the team key {render.one_line(team_key)!r} gives a task-ID pattern "
                f"board.json would reject; nothing written")
            return 2
        auto = _yes(guarded, "Does Linear's GitHub integration move issues to In Progress/Done "
                             "itself? [y/N] ")
    except InitAbort:
        if asked[0]:
            err("[board] init: no complete answer; nothing written")
            return 1
        return 0                                    # no terminal: stay in local mode, silently
    except BoardError as exc:
        message = str(exc).replace(key, "[redacted]") if key else str(exc)
        err(f"[board] init failed: {message}; nothing written")
        return 1
    except Exception as exc:  # never a traceback: it could echo board text or the key
        err(f"[board] init failed: unexpected {type(exc).__name__}; nothing written")
        return 1

    config = {"board": "linear", "connection": connection, **chosen, "id_pattern": pattern,
              "git_auto_status": auto}
    write_atomically(root, {os.path.join(".claude", "board.json"):
                            json.dumps(config, indent=2, ensure_ascii=False) + "\n"})
    out("[board] wrote .claude/board.json (board mode online). Your API key is not stored; "
        "keep LINEAR_API_KEY in your shell profile.")
    return 0


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("pull")
    sub.add_parser("flush")
    sub.add_parser("status")
    p_decide = sub.add_parser("decide")
    p_decide.add_argument("id")
    p_decide.add_argument("text", nargs="+", help="the decision")
    sub.add_parser("init")
    p_create = sub.add_parser("create")
    p_create.add_argument("--guide", required=True, help="the draft guide file")
    p_update = sub.add_parser("update")
    p_update.add_argument("--guide", required=True, help="the task ID whose local guide to push")
    p_triage = sub.add_parser("triage")
    p_triage.add_argument("--mark", action="store_true",
                          help="record the last-session marker after listing (wake does this)")
    p_push = sub.add_parser("push")
    p_push.add_argument("kind", choices=["status", "comment"])
    p_push.add_argument("id")
    p_push.add_argument("value", help="status slug, or comment milestone")
    p_push.add_argument("text", nargs="*", help="comment text")
    args = parser.parse_args(argv)

    if args.command == "init":
        return init(root, tty_ask, lambda key: LinearBoard(key, ""), os.environ,
                    print, lambda text: print(text, file=sys.stderr))

    config = load_config(root)
    if config is None and os.path.exists(config_path(root)):
        print("[board] .claude/board.json is unusable; nothing pulled", file=sys.stderr)
        return 2
    if args.command in ("create", "update", "triage") and not (config and config.get("board")):
        print(f"[board] {args.command} needs board mode online (no board in .claude/board.json)",
              file=sys.stderr)
        return 2
    if not config or not config.get("board"):
        print(f"[board] board mode is local (no board in .claude/board.json); nothing to {args.command}",
              file=sys.stderr)
        return 0
    if args.command == "status":                     # reads the local outbox only
        print(f"{outbox.count(root)} unsynced")
        return 0
    if args.command == "flush" and not outbox.count(root):
        return 0

    secret = None
    try:
        board, secret = make_board(config, root)
        use_decision_doc(board, config)
        if args.command == "pull":
            return pull(board, config, root)
        if args.command == "flush":
            return flush(board, root)
        if args.command == "decide":
            return decide(board, config, root, args)
        if args.command == "create":
            return create(board, root, args)
        if args.command == "update":
            return update(board, root, args)
        if args.command == "triage":
            return triage(board, config, root, args)
        return push(board, config, root, args)
    except ConfigError as exc:
        code, message = 2, str(exc)
    except BoardError as exc:
        code, message = 1, str(exc)
    except Exception as exc:  # never a traceback: it could echo board text or the key
        code, message = 1, f"unexpected {type(exc).__name__}"
    if secret:
        message = message.replace(secret, "[redacted]")
    tail = " The board cache was left unchanged." if args.command == "pull" else ""
    print(f"[board] {args.command} failed: {message}.{tail}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
