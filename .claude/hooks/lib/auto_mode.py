"""The one reader of auto-mode tasks (T188 D1).

Two Stop hooks act on the tasks the user started with `[auto]` (T180):

  * ``stop_auto_mode_check.py`` — blocks the stop when the final report does not hold up;
  * ``stop_auto_verify.py`` — starts the real ``/verify`` for a task at Ready for Review (T182).

Before T188 each one found those tasks itself, and they disagreed: the verify hook dropped every
``| Track: minimal`` board row and read the marker only from ``tasks/TASK_REVIEW_<ID>.md``, so a
minimal-track ``[auto]`` task never got a run. This module is the single answer to "which tasks are
in auto mode, on which track, and which file holds each one's report". Both hooks call it; neither
keeps a second copy.

**Per task it answers three things** (`resolve`):

  * the **track**, from the board row: ``| Track: minimal`` means minimal, anything else extended;
  * the **report file** — ``tasks/TASK_REVIEW_<ID>.md`` (extended) or the task's own record inside
    ``tasks/MINIMAL_LOG.md`` (minimal). Since T203 a live worktree's copy wins over the main
    checkout's (`find_for_task`): main may hold only the Stage 2 placeholder, and the task's code
    and HEAD are in its worktree. The worktree is the one whose branch the board row names, never
    picked by `git worktree list` order; `ambiguous` says no worktree could be told apart;
  * how the task is **marked**, kept as separate facts rather than one verdict, because the two
    hooks need different thresholds and both must read the same facts:

      - ``marker``  — ``Mode: auto`` alone on a line, outside every HTML comment (T180's marker,
        unchanged by T188 D4). ``stop_auto_verify.py`` requires exactly this, so a report still
        inside its template's comment starts no run.
      - ``strict``  — the marker is the *first* line of the report block. ``stop_auto_mode_check.py``
        check (1).
      - ``auto_section`` / ``tagged`` — an extended report carrying ``## Auto decisions``, or a
        Decision record whose text carries the literal ``[auto]`` tag. ``marked`` is the union, which
        is what ``stop_auto_mode_check.py`` treats as "this task is an auto-mode run".

**Never widens, never raises on its own.** `read` raises `Unreadable` for a file that exists but
cannot be read, so each caller keeps its own fail-open line on stderr; everything else degrades to
"not found". Offsets returned by `section` / `record_block` are into the text that was passed in —
pass the raw file text when you intend to write it back, and `skip_comments=True` so a commented
template copy is never the thing you edit.
"""
import glob
import os
import re
import subprocess
from collections import namedtuple

MARKER = "Mode: auto"
TAG = "[auto]"
AUTO_SECTION = "## Auto decisions"
MINIMAL_LOG = "MINIMAL_LOG.md"
MINIMAL_LOG_REL = os.path.join("tasks", MINIMAL_LOG)
GUIDE_PREFIX = "TASK_GUIDE_"
REVIEW_PREFIX = "TASK_REVIEW_"
MINIMAL_ROW_STANDIN = "| Track: minimal"  # for a task found from its file, not from a board row

COMMENT = re.compile(r"<!--.*?-->", re.S)
ROW_ID = re.compile(r"\*\*([A-Za-z]+-?\d+)\*\*")
MINIMAL_ROW = re.compile(r"\|\s*Track: minimal\b")
TASK_ID = re.compile(r"[A-Za-z]+-?\d+")
NEWEST_RECORD = re.compile(r"^## ([A-Za-z]+-?\d+) — [^\n]*\n(.*?)(?=^## |\Z)", re.S | re.M)
GIT_TIMEOUT_S = 5


class Unreadable(Exception):
    """A file that exists but could not be read. The caller decides what to say about it."""


def read(path, root=None):
    """Text of `path`, None when it does not exist, Unreadable on any other failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as exc:
        name = os.path.relpath(path, root) if root else path
        raise Unreadable(f"cannot read {name} ({type(exc).__name__})")


def worktree_dirs(root):
    """Each live worktree's path, the main checkout excluded; [] on any failure.

    An additional place to look, never a reason to skip: git absent, a non-zero exit, a timeout or
    unparsable output all degrade to "main checkout only".
    """
    try:
        done = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=root,
                              capture_output=True, text=True, timeout=GIT_TIMEOUT_S)
        if done.returncode != 0:
            return []
        paths = [l[len("worktree "):].strip() for l in done.stdout.splitlines()
                 if l.startswith("worktree ")]
        return [p for p in paths if p and os.path.abspath(p) != os.path.abspath(root)]
    except Exception:
        return []


def checkouts(root):
    """The main checkout first, then each live worktree."""
    return [root] + worktree_dirs(root)


def tasks_dirs(root):
    """Each checkout's `tasks/`, main checkout first."""
    return [os.path.join(c, "tasks") for c in checkouts(root)]


def checkout_of(tasks_dir):
    """`<checkout>/tasks` -> `<checkout>`."""
    return os.path.dirname(os.path.abspath(tasks_dir))


def find(name, dirs):
    """First existing `<dir>/<name>`, main checkout first; else the main-checkout path."""
    for d in dirs:
        path = os.path.join(d, name)
        if os.path.exists(path):
            return path
    return os.path.join(dirs[0], name)


def branch_of(checkout):
    """The branch checked out in `checkout`, or None (detached, git absent, any failure)."""
    try:
        done = subprocess.run(["git", "-C", checkout, "rev-parse", "--abbrev-ref", "HEAD"],
                              capture_output=True, text=True, timeout=GIT_TIMEOUT_S)
        name = done.stdout.strip() if done.returncode == 0 else ""
        return name if name and name != "HEAD" else None
    except Exception:
        return None


def names_task(branch, task_id):
    """True when `branch` names `task_id`, case-insensitive and word-bounded: `feat/t951-x` names
    T951, `feat/t9510` and `xt951` do not (the shape of T197's push-scope resolver)."""
    return bool(branch and re.search(rf"(?<![A-Za-z0-9]){re.escape(task_id)}(?![0-9])", branch,
                                     re.I))


ROW_BRANCH = re.compile(r"\bbranch `([^`\s]+)`")
ROW_WORKTREE_BRANCH = re.compile(r"\bworktree `[^`]+` \(`([^`\s]+)`\)")


def row_branch(row):
    """The task's branch as its main-checkout board row names it, or None. Read from the newest
    `Started …` segment only (the Supervisor writes it at Stage 3): ``branch `<name>` `` or
    ``worktree `../<dir>` (`<name>`)``."""
    for seg in reversed([g for g in re.split(r"\s\|\s", row or "") if g.strip().startswith("Started")]):
        hit = ROW_BRANCH.search(seg) or ROW_WORKTREE_BRANCH.search(seg)
        if hit:
            return hit.group(1)
    return None


def find_for_task(name, dirs, task_id, holds=None, branch=None):
    """T203: the task's own copy of `name`, as `(path, ambiguous)`.

    The Supervisor creates `tasks/TASK_REVIEW_<ID>.md` on main at Stage 2 as a placeholder, while the
    task's real report, code and HEAD live in its worktree (Stage 4 P1). Which worktree is decided by
    the trusted source, the main checkout's board row, never by `git worktree list` order (security
    review: a decoy `git worktree add ../a-t951 -b fix/t951-x` would otherwise win):

      * the row names a branch -> the live worktree with exactly that branch checked out, if its copy
        exists (and passes `holds`); else no worktree copy — `find`'s main-first order;
      * the row names none -> the one worktree whose branch names the task; zero or several among the
        worktrees holding a copy -> `find`'s order and `ambiguous=True`, so no run starts;
      * no worktree holds a copy -> `find`'s order, not ambiguous.
    """
    found = []
    for d in dirs[1:]:
        path = os.path.join(d, name)
        if os.path.exists(path) and (holds is None or holds(path)):
            found.append(d)
    if branch:
        exact = [d for d in found if branch_of(checkout_of(d)) == branch]
        return (os.path.join(exact[0], name), False) if exact else (find(name, dirs), False)
    if not found:
        return find(name, dirs), False
    named = [d for d in found if names_task(branch_of(checkout_of(d)), task_id)]
    if len(named) == 1:
        return os.path.join(named[0], name), False
    return find(name, dirs), True


def _holds_record(task_id):
    def holds(path):
        try:
            text = read(path)
        except Unreadable:
            return False
        return text is not None and record_block(COMMENT.sub("", text), task_id) is not None
    return holds


def comment_spans(text):
    return [(m.start(), m.end()) for m in COMMENT.finditer(text or "")]


def section(text, heading_pattern, skip_comments=False):
    """(start, end, body) of the block under the first heading matching `heading_pattern`, or None.

    With `skip_comments`, a heading inside an HTML comment is passed over — that is the copy of a
    template, not the report, and writing into it would edit the instructions.
    """
    spans = comment_spans(text) if skip_comments else []
    for m in re.finditer(rf"^{heading_pattern}[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        if any(a <= m.start() < b for a, b in spans):
            continue
        return m.start(1), m.end(1), m.group(1)
    return None


def record_block(text, task_id, skip_comments=False):
    """(start, end, body) of the newest Decision record for `task_id` in a `MINIMAL_LOG.md` text.

    Records are newest first, so the first heading that names this task is the newest one — matched
    by task ID, never by position.
    """
    return section(text, rf"## {re.escape(task_id)} — ", skip_comments)


def first_line(body):
    lines = [l for l in body.splitlines() if l.strip()]
    return lines[0] if lines else ""


def board_rows(kanban, titles=("In Progress", "Ready for Review")):
    """[(task_id, row line)] for every task row under those board sections, in board order."""
    rows = []
    for title in titles:
        m = re.search(rf"^### {re.escape(title)}\n(.*?)(?=^###|\Z)", kanban or "", re.S | re.M)
        for line in (m.group(1).splitlines() if m else []):
            hit = ROW_ID.search(line)
            if line.strip().startswith("- ") and hit:
                rows.append((hit.group(1), line))
    return rows


def file_candidates(dirs, skip):
    """D9: the auto-mode tasks found from their files, so a project with no board is still checked.

    Every `TASK_REVIEW_*.md` that is marked, plus the newest `MINIMAL_LOG.md` record when it is.
    `skip` holds the IDs a board row already covers. Returns ({task_id: row stand-in}, notes),
    where each note is `(message, subject)` for the caller's own stderr line.
    """
    found, notes = {}, []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, f"{REVIEW_PREFIX}*.md"))):
            task_id = os.path.basename(path)[len(REVIEW_PREFIX):-len(".md")]
            if task_id in skip or task_id in found or not TASK_ID.fullmatch(task_id):
                continue
            try:
                task = resolve(task_id, "", dirs)
            except Unreadable as exc:
                notes.append((str(exc), task_id))
                continue
            if task.marked:
                found[task_id] = ""
    try:
        log = COMMENT.sub("", read(find(MINIMAL_LOG, dirs)) or "")
    except Unreadable as exc:
        notes.append((str(exc), "the newest Decision record"))
        log = ""
    newest = NEWEST_RECORD.search(log)
    if newest and newest.group(1) not in skip and newest.group(1) not in found:
        body = newest.group(2)
        if MARKER in body.splitlines() or TAG in body:
            found[newest.group(1)] = MINIMAL_ROW_STANDIN
    return found, notes


_AutoTask = namedtuple("AutoTask", "task_id track report_path guide_path text body marker strict "
                                   "auto_section tagged exists row ambiguous",
                       defaults=(False,))


class AutoTask(_AutoTask):
    """One task's auto-mode facts. `body` is its report block, HTML comments removed."""

    __slots__ = ()

    @property
    def minimal(self):
        return self.track == "minimal"

    @property
    def marked(self):
        """True when this task is an auto-mode run at all — the loosest reading, used by
        `stop_auto_mode_check.py`. `stop_auto_verify.py` requires `marker` instead."""
        return self.marker or self.auto_section or self.tagged

    @property
    def clean(self):
        """The whole report file with HTML comments removed ('' when there is no file)."""
        return COMMENT.sub("", self.text or "")

    @property
    def checkout(self):
        """The checkout that holds the report file — where this task's code and HEAD are."""
        return os.path.dirname(os.path.dirname(os.path.abspath(self.report_path)))

    @property
    def touched(self):
        """The task's own files that exist, for an mtime comparison against the `[auto]` request."""
        paths = [self.report_path] if self.exists else []
        if self.guide_path:
            paths.append(self.guide_path)
        return [p for p in paths if os.path.exists(p)]


def resolve(task_id, row, dirs):
    """The one resolution of a task's track, report file and auto-mode marks (D1).

    `row` is its board row (or `""`, or `MINIMAL_ROW_STANDIN` for a task found from its file).
    Raises `Unreadable` when the report file exists but cannot be read.
    """
    row = row or ""
    if MINIMAL_ROW.search(row):
        path, ambiguous = find_for_task(MINIMAL_LOG, dirs, task_id, _holds_record(task_id),
                                        row_branch(row))
        text = read(path)
        block = record_block(COMMENT.sub("", text), task_id) if text is not None else None
        body = block[2] if block else ""
        return AutoTask(task_id, "minimal", path, None, text, body,
                        marker=MARKER in body.splitlines(),
                        strict=first_line(body) == MARKER,
                        auto_section=False,
                        tagged=TAG in body,
                        exists=block is not None, row=row, ambiguous=ambiguous)
    branch = row_branch(row)
    path, ambiguous = find_for_task(f"{REVIEW_PREFIX}{task_id}.md", dirs, task_id, branch=branch)
    text = read(path)
    clean = COMMENT.sub("", text or "")
    block = section(clean, AUTO_SECTION)
    body = block[2] if block else ""
    return AutoTask(task_id, "extended", path, find_for_task(f"{GUIDE_PREFIX}{task_id}.md", dirs, task_id, branch=branch)[0], text, body,
                    marker=MARKER in clean.splitlines(),
                    strict=bool(block) and first_line(body) == MARKER,
                    auto_section=bool(block),
                    tagged=False,
                    exists=text is not None, row=row, ambiguous=ambiguous)
