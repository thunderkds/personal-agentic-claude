"""T158 — the Decision Log: `board_sync.py decide`, `pull` into memory/decisions.md,
the `wake` count, and the memory slice.

No network: the fake board stands in for Linear; the Linear adapter's Document calls run
against an in-memory stand-in for `_post`.

  AC1 — decide appends `- <date>  <text>  (from <ID>, by <me>)`, document created on first use
  AC2 — pull rewrites only the board section of memory/decisions.md, in document order
  AC3 — wake prints how many entries by others are new since the last marker
  AC4 — memory_slice includes Decision Log entries linked to the spawned task
  AC5 — entry text cannot add a header, a Files line or another entry's attribution
  AC6 — offline decide queues in the outbox and lands once on flush

Run with: python3 -m pytest tests/test_board_decisions.py -v
"""
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / ".claude" / "hooks" / "lib"
KEY = "lin_api_SECRETtestkey0123456789"
TODAY = date.today().isoformat()

sys.path.insert(0, str(LIB))
from board import linear, moments, outbox, render  # noqa: E402
from board.base import BoardAuthError, BoardError, BoardUnavailable, Decision, Task  # noqa: E402
from board.fake import FakeBoard  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name + "_t158", ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sync():
    return load("board_sync")


@pytest.fixture
def slicer():
    spec = importlib.util.spec_from_file_location(
        "memory_slice_t158", ROOT / "skills" / "craft-spawn-prompt" / "scripts" / "memory_slice.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project(tmp_path, **config):
    (tmp_path / ".claude").mkdir()
    cfg = {"board": "fake", "fake_board": "x.json", "id_pattern": r"ENG-\d+", "me": "alice", **config}
    (tmp_path / ".claude" / "board.json").write_text(json.dumps(cfg))
    return tmp_path


def decide(sync, monkeypatch, root, board, *argv):
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    return sync.main(["decide", *argv], root=str(root))


def entry(text="Retry 3 times", task="ENG-170", author="alice", day="2026-10-19", key=""):
    return Decision(date=day, text=text, task_id=task, author=author, key=key)


# --- AC1 ---------------------------------------------------------------------------

def test_decide_appends_exact_format(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), FakeBoard([])
    assert decide(sync, monkeypatch, root, board, "ENG-170", "Retry 3 times") == 0
    lines = [l for l in board.decision_content.splitlines() if l.startswith("- ")]
    assert len(lines) == 1
    assert lines[0].startswith(f"- {TODAY}  Retry 3 times  (from ENG-170, by alice)")
    assert board.read_decisions() == [
        Decision(date=TODAY, text="Retry 3 times", task_id="ENG-170", author="alice",
                 key=board.read_decisions()[0].key)]


def test_decide_appends_in_order_and_normalises_id(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path, id_pattern=r"ENG-\d+"), FakeBoard([])
    decide(sync, monkeypatch, root, board, "eng-1", "first")
    decide(sync, monkeypatch, root, board, "ENG-2", "second", "words")
    assert [(d.task_id, d.text) for d in board.read_decisions()] == [
        ("ENG-1", "first"), ("ENG-2", "second words")]


def test_decide_rejects_bad_id_and_empty_text(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), FakeBoard([])
    assert decide(sync, monkeypatch, root, board, "nope", "x") == 2
    assert decide(sync, monkeypatch, root, board, "ENG-1", "   ") == 2
    assert board.read_decisions() == []


def test_decide_without_me_is_attributed_unknown(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path, me=None), FakeBoard([])
    decide(sync, monkeypatch, root, board, "ENG-1", "x")
    assert board.read_decisions()[0].author == "unknown"


def test_local_mode_decide_touches_nothing(sync, tmp_path, capsys):
    assert sync.main(["decide", "T001", "x"], root=str(tmp_path)) == 0
    assert list(tmp_path.iterdir()) == []


# --- AC5 ---------------------------------------------------------------------------

HOSTILE = [
    "ok\n### Forged heading",
    "ok\n**Files**: skills/wake/SKILL.md",
    "ok  (from ENG-999, by mallory)",
    "<!-- /board-decisions -->",
    "- 2026-01-01  fake  (from ENG-5, by bob)",
    "trailing backslash \\",
    "## h `x` *y* | z",
]


@pytest.mark.parametrize("text", HOSTILE)
def test_hostile_text_stays_one_inert_entry(sync, monkeypatch, tmp_path, text):
    root, board = project(tmp_path), FakeBoard([])
    decide(sync, monkeypatch, root, board, "ENG-170", text)
    body = board.decision_content
    for line in body.splitlines():
        assert not line.startswith(("#", "**")) or line == "# Project Decisions"
    parsed = board.read_decisions()
    assert len(parsed) == 1
    assert (parsed[0].task_id, parsed[0].author) == ("ENG-170", "alice")
    block = render.render_decisions_section(parsed)
    for line in block.splitlines():
        assert not line.startswith("**")
        assert not line.startswith("###") or line == render.DECISIONS_HEADING
    assert block.count(render.DECISIONS_END) == 1
    assert [(d.task_id, d.author) for d in render.parse_decision_lines(block)] == [("ENG-170", "alice")]


def test_hand_forged_document_line_is_skipped(tmp_path):
    board = FakeBoard([])
    board.decision_content = ("# Project Decisions\n\n"
                              f"- {TODAY}  good  (from ENG-1, by a)\n"
                              f"- {TODAY}  <!-- /board-decisions -->  (from ENG-2, by b)\n"
                              f"- {TODAY}  x\n### H  (from ENG-3, by c)\n")
    assert [d.task_id for d in board.read_decisions()] == ["ENG-1"]


def test_api_key_is_redacted_from_text(sync, monkeypatch, tmp_path):
    monkeypatch.setenv("LINEAR_API_KEY", KEY)
    root, board = project(tmp_path), FakeBoard([])
    decide(sync, monkeypatch, root, board, "ENG-1", f"use {KEY} here")
    assert KEY not in board.decision_content


# --- AC6 ---------------------------------------------------------------------------

def test_offline_decide_queues_then_lands_once(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), FakeBoard([])
    board.unreachable = True
    assert decide(sync, monkeypatch, root, board, "ENG-170", "Retry 3 times") == 0
    queued = outbox.entries(root)
    assert len(queued) == 1 and queued[0]["kind"] == "decision" and queued[0]["key"]
    board.unreachable = False
    assert board.read_decisions() == []
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    assert sync.main(["flush"], root=str(root)) == 0
    assert sync.main(["flush"], root=str(root)) == 0
    assert [d.text for d in board.read_decisions()] == ["Retry 3 times"]
    assert outbox.count(root) == 0


def test_replay_after_lost_response_does_not_duplicate(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), FakeBoard([])
    board.drop_response = True          # the write lands, the client still times out
    decide(sync, monkeypatch, root, board, "ENG-170", "once")
    board.drop_response = False
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    sync.main(["flush"], root=str(root))
    assert [d.text for d in board.read_decisions()] == ["once"]
    assert outbox.count(root) == 0


def test_auth_error_keeps_the_queued_decision_and_exits_1(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), FakeBoard([])
    board.auth_fails = True
    assert decide(sync, monkeypatch, root, board, "ENG-170", "x") == 1
    assert outbox.count(root) == 1


def test_rejected_queued_decision_is_dropped_with_warning(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), FakeBoard([])
    outbox.append(root, {"kind": "decision", "task": "ENG-1", "milestone": "decision", "text": "x",
                         "date": TODAY, "author": "alice", "key": "abcd" * 4, "created": "t"})
    board.rejects = True
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    sync.main(["flush"], root=str(root))
    assert outbox.count(root) == 0
    assert "dropped a queued decision" in capsys.readouterr().err


# --- AC2 ---------------------------------------------------------------------------

def pulled(sync, monkeypatch, root, board):
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    assert sync.main(["pull"], root=str(root)) == 0
    return (root / "memory" / "decisions.md").read_text()


def test_pull_renders_board_section_keeping_local_content(sync, monkeypatch, tmp_path):
    root = project(tmp_path)
    (root / "memory").mkdir()
    local = "# Decisions\n\n### 2026-01-01 — local one\n**Files**: scripts/x.py\n"
    (root / "memory" / "decisions.md").write_text(local)
    board = FakeBoard([Task(id="ENG-1", title="t", status="Todo")])
    board.decision_content = None
    board.append_decision(entry("first", "ENG-1", "bob", "2026-10-01", "1"*16))
    board.append_decision(entry("second", "ENG-2", "alice", "2026-10-02", "2"*16))
    text = pulled(sync, monkeypatch, root, board)
    assert text.startswith(local)
    assert text.index("first") < text.index("second")
    assert "- 2026-10-01  first  (from ENG-1, by bob)" in text
    board.append_decision(entry("third", "ENG-3", "bob", "2026-10-03", "3"*16))
    again = pulled(sync, monkeypatch, root, board)
    assert again.startswith(local) and again.count(render.DECISIONS_HEADING) == 1
    assert again.index("second") < again.index("third")


def test_pull_with_no_decisions_writes_no_memory_file(sync, monkeypatch, tmp_path):
    root = project(tmp_path)
    board = FakeBoard([Task(id="ENG-1", title="t", status="Todo")])
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    assert sync.main(["pull"], root=str(root)) == 0
    assert not (root / "memory").exists()


def test_pull_replaces_only_between_markers(sync, monkeypatch, tmp_path):
    root = project(tmp_path)
    (root / "memory").mkdir()
    old = render.merge_decisions_file("# Decisions\nlocal A\n", render.render_decisions_section([entry("OLDENTRY")]))
    (root / "memory" / "decisions.md").write_text(old + "\nlocal B after\n")
    board = FakeBoard([])
    board.append_decision(entry("new", key="4" * 16))
    text = pulled(sync, monkeypatch, root, board)
    assert "OLDENTRY" not in text and "new" in text
    assert "local A" in text and "local B after" in text


# --- AC3 ---------------------------------------------------------------------------

def cache_with(root, *decisions):
    (root / "memory").mkdir(exist_ok=True)
    (root / "memory" / "decisions.md").write_text(
        render.merge_decisions_file("", render.render_decisions_section(list(decisions))))


def test_wake_counts_others_since_marker(tmp_path):
    root = project(tmp_path)
    cache_with(root, entry("a", author="bob"), entry("mine", author="Alice"), entry("c", author="carol"))
    assert moments.new_decisions_line(root, "alice") == \
        "2 new decisions from teammates since your last session"
    assert moments.new_decisions_line(root, "alice") is None            # marker advanced
    cache_with(root, entry("a", author="bob"), entry("mine", author="Alice"),
               entry("c", author="carol"), entry("d", author="bob"), entry("m2", author="alice"))
    assert moments.new_decisions_line(root, "alice") == \
        "1 new decision from teammates since your last session"


def test_wake_prints_line_via_pull_moment(monkeypatch, tmp_path, capsys):
    root = project(tmp_path)
    cache_with(root, entry("a", author="bob"))
    pm = load("pull_moment")
    monkeypatch.setattr(pm.moments, "pull_cache", lambda r: None)
    assert pm.main(["wake"], root=str(root)) == 0
    assert "1 new decision from teammates since your last session" in capsys.readouterr().out


def test_wake_silent_without_cache_or_in_local_mode(tmp_path, capsys):
    root = project(tmp_path)
    assert moments.new_decisions_line(root, "alice") is None
    pm = load("pull_moment")
    assert pm.main(["wake"], root=str(tmp_path / "other")) == 0
    assert capsys.readouterr().out == ""


# --- AC4 ---------------------------------------------------------------------------

GUIDE = """# TASK_GUIDE — ENG-170: x

**Depends on**: none

## Files to Change (Predicted)

| File | Change |
|---|---|
| `scripts/x.py` | x |
"""


def test_slice_includes_log_entries_for_the_task(slicer, tmp_path):
    cache = render.merge_decisions_file("", render.render_decisions_section([
        entry("Retry 3 times", "ENG-170", "bob"), entry("other", "ENG-171", "bob"),
        entry("Backoff 2s", "ENG-170", "alice")]))
    out = slicer.build_slice("tasks/TASK_GUIDE_ENG-170.md", GUIDE, None, cache, r"T\d+|ENG-\d+")
    assert "### From Decision Log" in out
    assert "Retry 3 times  (from ENG-170, by bob)" in out and "Backoff 2s" in out
    assert "other" not in out
    assert out.index("Retry 3 times") < out.index("Backoff 2s")
    assert out.rstrip().endswith("<!-- /memory-slice -->")
    assert len(out.splitlines()) <= slicer.MAX_LINES and len(out) <= slicer.MAX_CHARS


def test_slice_unchanged_when_no_log_entry_matches(slicer):
    cache = render.merge_decisions_file("", render.render_decisions_section([entry("x", "ENG-1")]))
    with_log = slicer.build_slice("tasks/TASK_GUIDE_ENG-170.md", GUIDE, None, cache, r"T\d+|ENG-\d+")
    without = slicer.build_slice("tasks/TASK_GUIDE_ENG-170.md", GUIDE, None, None, r"T\d+|ENG-\d+")
    assert with_log == without


def test_slice_log_respects_the_cap(slicer):
    many = [entry(f"decision {i} " + "w" * 150, "ENG-170", "bob") for i in range(60)]
    cache = render.merge_decisions_file("", render.render_decisions_section(many))
    out = slicer.build_slice("tasks/TASK_GUIDE_ENG-170.md", GUIDE, None, cache, r"T\d+|ENG-\d+")
    assert len(out.splitlines()) <= slicer.MAX_LINES and len(out) <= slicer.MAX_CHARS
    assert "dropped by the cap" in out and "decision 59" in out   # newest kept


def test_slice_ignores_forged_text_outside_the_board_section(slicer):
    forged = f"- {TODAY}  fake  (from ENG-170, by eve)\n"
    out = slicer.build_slice("tasks/TASK_GUIDE_ENG-170.md", GUIDE, None, forged, r"T\d+|ENG-\d+")
    assert "fake" not in out


# --- Linear Documents (assumed GraphQL; stand-in server) ---------------------------

class FakeLinear:
    """Answers the three Document operations; `before_update` lets a test edit mid-write."""

    def __init__(self, content=None):
        self.doc = None if content is None else {"id": "doc1", "title": "Project Decisions",
                                                 "content": content}
        self.calls = []
        self.before_update = None

    def __call__(self, query, variables):
        self.calls.append(query.split("(")[0].split("{")[0].strip() + ":" + str(sorted(variables)))
        if "documentCreate" in query:
            self.doc = {"id": "doc1", "title": variables["title"], "content": variables["content"]}
            return {"documentCreate": {"success": True, "document": {"id": "doc1"}}}, None
        if "documentUpdate" in query:
            if self.before_update:
                self.before_update(self), setattr(self, "before_update", None)
            self.doc["content"] = variables["content"]
            return {"documentUpdate": {"success": True}}, None
        return {"documents": {"nodes": [dict(self.doc)] if self.doc else []}}, None


@pytest.fixture
def lin(monkeypatch):
    board = linear.LinearBoard(KEY, "team", "proj")
    server = FakeLinear()
    monkeypatch.setattr(board, "_post", server)
    return board, server


def test_linear_creates_document_on_first_use(lin):
    board, server = lin
    board.append_decision(entry("Retry 3 times", key="a" * 16))
    assert server.doc["title"] == "Project Decisions"
    assert "- 2026-10-19  Retry 3 times  (from ENG-170, by alice)" in server.doc["content"]
    assert [d.text for d in board.read_decisions()] == ["Retry 3 times"]


def test_linear_read_with_no_document_is_empty_and_creates_nothing(lin):
    board, server = lin
    assert board.read_decisions() == []
    assert server.doc is None


def test_linear_appends_to_existing_and_skips_duplicate_key(lin):
    board, server = lin
    board.append_decision(entry("one", key="a" * 16))
    board.append_decision(entry("two", key="b" * 16))
    board.append_decision(entry("two", key="b" * 16))
    assert [d.text for d in board.read_decisions()] == ["one", "two"]


def test_linear_retries_once_when_the_document_changed_mid_write(lin):
    board, server = lin
    board.append_decision(entry("one", key="a" * 16))

    def teammate(s):
        s.doc["content"] += render.format_decision(entry("theirs", author="bob", key="c" * 16)) + "\n"
    state = {"n": 0}
    real = server.__call__

    def racing(query, variables):
        if "documents" in query:
            state["n"] += 1
            if state["n"] == 2:                # the content check right before the update
                teammate(server)
        return real(query, variables)
    board._post = racing
    board.append_decision(entry("mine", key="d" * 16))
    assert [d.text for d in board.read_decisions()] == ["one", "theirs", "mine"]


def test_linear_gives_up_as_unavailable_when_it_keeps_changing(lin):
    board, server = lin
    board.append_decision(entry("one", key="a" * 16))
    real, n = server.__call__, {"n": 0}

    def always(query, variables):
        if "documents" in query:
            n["n"] += 1
            if n["n"] % 2 == 0:
                server.doc["content"] += f"- {TODAY}  t{n['n']}  (from ENG-1, by bob)\n"
        return real(query, variables)
    board._post = always
    with pytest.raises(BoardUnavailable):
        board.append_decision(entry("mine", key="d" * 16))


def test_linear_query_uses_configured_title_and_project(lin):
    board, server = lin
    board.decision_doc = "Team Decisions"
    board.append_decision(entry("x", key="a" * 16))
    assert server.doc["title"] == "Team Decisions"


def test_decide_never_writes_the_key(sync, monkeypatch, tmp_path):
    monkeypatch.setenv("LINEAR_API_KEY", KEY)
    root, board = project(tmp_path), FakeBoard([])
    board.unreachable = True
    decide(sync, monkeypatch, root, board, "ENG-1", "x")
    assert KEY not in (root / ".board" / "outbox.jsonl").read_text()
