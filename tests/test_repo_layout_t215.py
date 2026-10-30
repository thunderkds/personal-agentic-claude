"""
T215 — repo root tidy + one-line Done/Closed board rows, same meaning.

AC1: the 12 `BRAINSTORMING_LOG_<topic>.md` live in `docs/brainstorming/`, the 3 `PRD_<topic>.md`
     in `docs/prd/`, byte-identical; none remain at the root (root `BRAINSTORMING_LOG.md` stays).
AC2: no tracked file names a moved file by its old root path.
AC3: every row T215 shortened is one line, <= 400 chars, and keeps checkbox, ID, Complexity, the
     Risk/Priority/Guide it had, and a closing outcome.
AC4: `docs/archive/KANBAN_DONE_DETAIL.md` keeps each original Done/Closed row verbatim, in order,
     and the board points at it under `### Done`.
AC5: the hooks' own parsers still find every task in its section.

The before-state is frozen in `tests/fixtures/t215/board_before.json` (from `5fd0bd00`). The board
keeps moving after T215, so AC5 is checked durably: a frozen Done/Closed ID stays in Done/Closed,
and no frozen ID of any other section is lost. AC7 (board <= 100 KB) is a one-time size check in
the guide's Verification Command, not here: future Done rows are not shortened (cut list).
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "t215", "board_before.json")
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
ARCHIVE = os.path.join(ROOT, "docs", "archive", "KANBAN_DONE_DETAIL.md")
ARCHIVE_REL = "docs/archive/KANBAN_DONE_DETAIL.md"
HOOKS = os.path.join(ROOT, ".claude", "hooks")
ROW = re.compile(r"^- \[([ x~])\] \*\*(T\d+)\*\*", re.M)
MOVED_NAME = re.compile(r"(?<![\w/.-])((?:BRAINSTORMING_LOG|PRD)_[A-Za-z0-9-]+\.md)")
DONE_TITLE = "Done"
CLOSED_TITLE = "Closed (investigated, will not do)"

sys.path.insert(0, os.path.join(HOOKS, "lib"))
import auto_mode as am  # noqa: E402


def _fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _board():
    with open(KANBAN, encoding="utf-8", newline="") as f:
        return f.read()


def _new_path(old):
    return ("docs/brainstorming/" if old.startswith("BRAINSTORMING_LOG_") else "docs/prd/") + old


def _section_rows(board, prefix):
    """{task_id: row} for the `### <prefix>...` section, read the way find_kanban_section reads it."""
    m = re.search(rf"^### {re.escape(prefix)}[^\n]*\n(.*?)(?=^##|\Z)", board, re.S | re.M)
    body = m.group(1) if m else ""
    return {hit.group(2): line for line in body.splitlines() for hit in [ROW.match(line)] if hit}


# --- AC1 -------------------------------------------------------------------------------------

def test_moved_files_left_the_root_and_kept_their_bytes():
    moved = _fixture()["moved_files"]
    assert len(moved) == 15
    for old, digest in moved.items():
        assert not os.path.exists(os.path.join(ROOT, old)), f"{old} is still at the repo root"
        new = os.path.join(ROOT, _new_path(old))
        with open(new, "rb") as f:
            assert hashlib.sha256(f.read()).hexdigest() == digest, f"{_new_path(old)} content changed"
    assert len([n for n in moved if n.startswith("BRAINSTORMING_LOG_")]) == 12
    assert os.path.isfile(os.path.join(ROOT, "BRAINSTORMING_LOG.md")), "root BRAINSTORMING_LOG.md must stay"


# --- AC2 -------------------------------------------------------------------------------------

def test_no_tracked_file_names_a_moved_file_by_its_old_root_path():
    moved = set(_fixture()["moved_files"])
    # The archive is verbatim history; the T215 guide/review/test/fixture describe the move itself.
    skip = {ARCHIVE_REL, "tasks/TASK_GUIDE_T215.md", "tasks/TASK_REVIEW_T215.md",
            "tests/test_repo_layout_t215.py", "tests/fixtures/t215/board_before.json"}
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True,
                           text=True).stdout.split("\0")
    stale = []
    for rel in files:
        if not rel or rel in skip or not os.path.isfile(os.path.join(ROOT, rel)):
            continue
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        stale += [f"{rel}: {m.group(1)}" for m in MOVED_NAME.finditer(text) if m.group(1) in moved]
    assert not stale, "old root paths still referenced:\n" + "\n".join(stale)


# --- AC3 -------------------------------------------------------------------------------------

def test_every_shortened_row_is_one_short_line_with_its_fields():
    board = _board()
    current = {**_section_rows(board, DONE_TITLE), **_section_rows(board, "Closed")}
    for row in _fixture()["done_closed_rows"]:
        tid, line = row["id"], current.get(row["id"])
        assert line is not None, f"{tid} has no Done/Closed row"
        assert len(line) <= 400, f"{tid} row is {len(line)} chars"
        assert re.match(rf"^- \[[x~]\] \*\*{tid}\*\* — \S", line), f"{tid}: checkbox/ID/title lost"
        assert re.search(r"\bC[0-3]\b", line), f"{tid}: Complexity lost"
        if row["guide"]:
            assert f"Guide: `{row['guide']}`" in line, f"{tid}: Guide path lost"
        assert re.search(r"\b(Done|Closed|Completed)\b", line), f"{tid}: closing outcome lost"


def test_shortened_rows_keep_risk_and_priority_they_had():
    archived = dict(_archive_entries())
    board = _board()
    current = {**_section_rows(board, DONE_TITLE), **_section_rows(board, "Closed")}
    for tid, original in archived.items():
        risk = re.search(r"Risk: \w+", original)
        if risk:
            assert risk.group(0) in current[tid], f"{tid}: lost `{risk.group(0)}`"
        prio = re.search(r"\| (P[0-2])(?= \||$)", original)
        if prio:
            assert re.search(rf"\| {prio.group(1)}(?= \||$)", current[tid]), f"{tid}: lost {prio.group(1)}"


# --- AC4 -------------------------------------------------------------------------------------

def _archive_entries():
    with open(ARCHIVE, encoding="utf-8", newline="") as f:
        text = f.read()
    return re.findall(r"^## (T\d+)\n\n(.*)$", text, re.M)


def test_archive_keeps_every_original_row_verbatim_in_board_order():
    entries = _archive_entries()
    frozen = _fixture()["done_closed_rows"]
    assert [tid for tid, _ in entries] == [r["id"] for r in frozen]
    for (tid, line), row in zip(entries, frozen):
        assert hashlib.sha256(line.encode("utf-8")).hexdigest() == row["sha256"], f"{tid} not verbatim"


def test_board_points_at_the_archive_under_done():
    done = re.search(r"^### Done[^\n]*\n(.*?)(?=^##|\Z)", _board(), re.S | re.M).group(1)
    assert sum(ARCHIVE_REL in line for line in done.splitlines() if not ROW.match(line)) == 1


# --- AC5 -------------------------------------------------------------------------------------

def _validate_guide():
    path = os.path.join(HOOKS, "pre_agent_validate_guide.py")
    spec = importlib.util.spec_from_file_location("t215_validate_guide", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.KANBAN = KANBAN
    return module


def test_hook_parsers_still_place_every_frozen_task():
    sections = _fixture()["sections"]
    board = _board()
    find = _validate_guide().find_kanban_section
    done_now = {tid for tid, _ in am.board_rows(board, (DONE_TITLE,))}
    closed_now = {tid for tid, _ in am.board_rows(board, (CLOSED_TITLE,))}
    for tid in sections["Done"]:
        assert tid in done_now, f"{tid} left Done (auto_mode.board_rows)"
        assert find(tid) == "Done", f"{tid}: find_kanban_section -> {find(tid)}"
    for tid in sections[CLOSED_TITLE]:
        assert tid in closed_now, f"{tid} left Closed (auto_mode.board_rows)"
    on_board = {m.group(2) for m in ROW.finditer(board)}
    for title in ("Todo", "In Progress", "Ready for Review", "Blocked"):
        lost = [tid for tid in sections[title] if tid not in on_board]
        assert not lost, f"{title} IDs lost from the board: {lost}"
    assert "T213" in done_now and find("T213") == "Done"
