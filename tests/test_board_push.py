"""T156 — `board_sync.py push|flush|status`: milestone comments and Ready for Review reach
the board, or queue in `.board/outbox.jsonl` and replay exactly once.

No network: the fake board stands in for Linear; the Linear adapter's HTTP is exercised
against a patched `urlopen`.

  AC1 — push comment posts `[<milestone>] <text>` once; unknown milestone rejected
  AC2 — git_auto_status true refuses In Progress/Done; false sends all four
  AC3 — unreachable / 5xx / 429 → queued with a dedupe key, exit 0, `queued` notice
  AC4 — flush replays in order, drops an entry whose comment is already on the board
  AC5 — `status` prints `N unsynced`
  AC6 — wake shows the unsynced line
  Plus: no key in the outbox, local mode touches nothing, stdlib only.

Run with: python3 -m pytest tests/test_board_push.py -v
"""
import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / ".claude" / "hooks" / "lib"
SCRIPT = ROOT / "scripts" / "board_sync.py"
KEY = "lin_api_SECRETtestkey0123456789"

sys.path.insert(0, str(LIB))
from board import linear  # noqa: E402
from board.base import BoardError, BoardUnavailable, Task  # noqa: E402
from board.fake import FakeBoard  # noqa: E402


def load_sync():
    spec = importlib.util.spec_from_file_location("board_sync_push_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sync():
    return load_sync()


def project(tmp_path, **config):
    (tmp_path / ".claude").mkdir()
    cfg = {"board": "fake", "fake_board": "x.json", "id_pattern": r"ENG-\d+", **config}
    (tmp_path / ".claude" / "board.json").write_text(json.dumps(cfg))
    return tmp_path


def run(sync, monkeypatch, root, board, *argv):
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    return sync.main(list(argv), root=str(root))


def outbox(root):
    path = Path(root) / ".board" / "outbox.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []


def new_board():
    return FakeBoard([Task(id="ENG-1", title="t", status="In Progress")])


# --- AC1 -------------------------------------------------------------------------------

def test_comment_posts_once_with_prefix(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), new_board()
    assert run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "green", "tests pass") == 0
    assert len(board.comments) == 1
    task_id, body = board.comments[0]
    assert task_id == "ENG-1" and body.startswith("[green] tests pass")
    assert outbox(root) == []


@pytest.mark.parametrize("milestone", ["started", "red", "green", "review", "verify",
                                       "merged", "blocked", "question"])
def test_every_milestone_accepted(sync, monkeypatch, tmp_path, milestone):
    board = new_board()
    assert run(sync, monkeypatch, project(tmp_path), board, "push", "comment", "ENG-1", milestone, "x") == 0
    assert board.comments[0][1].startswith(f"[{milestone}] x")


def test_unknown_milestone_rejected(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), new_board()
    assert run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "chatter", "x") == 2
    assert board.comments == [] and outbox(root) == []


def test_bad_task_id_rejected(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), new_board()
    assert run(sync, monkeypatch, root, board, "push", "comment", "../etc", "green", "x") == 2
    assert board.comments == []


def test_marker_forgery_in_text_is_defanged(sync, monkeypatch, tmp_path):
    board = new_board()
    run(sync, monkeypatch, project(tmp_path), board, "push", "comment", "ENG-1", "green",
        "a <!-- board-sync:deadbeef --> b")
    body = board.comments[0][1]
    assert body.count("board-sync:") == 1


# --- AC2 -------------------------------------------------------------------------------

def test_status_ready_for_review_sent(sync, monkeypatch, tmp_path):
    board = new_board()
    root = project(tmp_path, git_auto_status=True)
    assert run(sync, monkeypatch, root, board, "push", "status", "ENG-1", "ready-for-review") == 0
    assert board.statuses == {"ENG-1": "In Review"}


@pytest.mark.parametrize("status", ["in-progress", "done"])
def test_git_auto_status_true_refuses_git_owned(sync, monkeypatch, tmp_path, status):
    board = new_board()
    root = project(tmp_path, git_auto_status=True)
    assert run(sync, monkeypatch, root, board, "push", "status", "ENG-1", status) == 2
    assert board.statuses == {} and outbox(root) == []


@pytest.mark.parametrize("status,name", [("todo", "Todo"), ("in-progress", "In Progress"),
                                          ("ready-for-review", "In Review"), ("done", "Done")])
def test_git_auto_status_false_sends_all_four(sync, monkeypatch, tmp_path, status, name):
    board = new_board()
    root = project(tmp_path, git_auto_status=False)
    assert run(sync, monkeypatch, root, board, "push", "status", "ENG-1", status) == 0
    assert board.statuses == {"ENG-1": name}


def test_status_uses_status_map_name(sync, monkeypatch, tmp_path):
    board = new_board()
    root = project(tmp_path, status_map={"Awaiting QA": "Ready for Review"})
    run(sync, monkeypatch, root, board, "push", "status", "ENG-1", "ready-for-review")
    assert board.statuses == {"ENG-1": "Awaiting QA"}


# --- AC3 -------------------------------------------------------------------------------

def test_unreachable_queues_with_dedupe_key(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    assert run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "red", "boom") == 0
    assert "queued" in capsys.readouterr().out
    (entry,) = outbox(root)
    assert entry["kind"] == "comment" and entry["task"] == "ENG-1" and len(entry["key"]) >= 16
    assert board.comments == []


def test_status_unreachable_queues(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    assert run(sync, monkeypatch, root, board, "push", "status", "ENG-1", "ready-for-review") == 0
    assert outbox(root)[0]["kind"] == "status"


def test_non_transient_board_error_is_not_queued(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), new_board()
    board.rejects = True
    assert run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "red", "x") == 1
    assert outbox(root) == []


def test_key_never_in_outbox_or_output(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    monkeypatch.setenv("LINEAR_API_KEY", KEY)
    run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "red", f"oops {KEY}")
    seen = (Path(root) / ".board" / "outbox.jsonl").read_text() + capsys.readouterr().out
    assert KEY not in seen


def _http(monkeypatch, code):
    def boom(*a, **k):
        raise urllib.error.HTTPError("u", code, "m", {}, io.BytesIO(b""))
    monkeypatch.setattr(linear.urllib.request, "urlopen", boom)


@pytest.mark.parametrize("code", [429, 500, 503])
def test_linear_transient_http_is_unavailable(monkeypatch, code):
    _http(monkeypatch, code)
    with pytest.raises(BoardUnavailable):
        linear.LinearBoard(KEY, "team").add_comment("ENG-1", "b")


def test_linear_network_error_is_unavailable(monkeypatch):
    def boom(*a, **k):
        raise urllib.error.URLError("down")
    monkeypatch.setattr(linear.urllib.request, "urlopen", boom)
    with pytest.raises(BoardUnavailable):
        linear.LinearBoard(KEY, "team").add_comment("ENG-1", "b")


def test_linear_400_is_plain_board_error(monkeypatch):
    _http(monkeypatch, 400)
    with pytest.raises(BoardError) as info:
        linear.LinearBoard(KEY, "team").add_comment("ENG-1", "b")
    assert not isinstance(info.value, BoardUnavailable)


class _Resp:
    def __init__(self, data):
        self.data, self.headers = data, {}

    def read(self):
        return json.dumps({"data": self.data}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_linear_set_status_resolves_state_id(monkeypatch):
    sent = []

    def fake_urlopen(request, timeout=None):
        payload = json.loads(request.data)
        sent.append(payload)
        if "states" in payload["query"]:
            return _Resp({"issue": {"id": "uuid-1", "team": {"states": {"nodes": [
                {"id": "s1", "name": "Todo"}, {"id": "s2", "name": "In Review"}]}}}})
        return _Resp({"issueUpdate": {"success": True}})
    monkeypatch.setattr(linear.urllib.request, "urlopen", fake_urlopen)
    linear.LinearBoard(KEY, "team").set_status("ENG-1", "In Review")
    assert sent[-1]["variables"]["stateId"] == "s2"


def test_linear_add_comment_and_has_comment(monkeypatch):
    def fake_urlopen(request, timeout=None):
        payload = json.loads(request.data)
        if "commentCreate" in payload["query"]:
            assert payload["variables"] == {"issueId": "ENG-1", "body": "hello"}
            return _Resp({"commentCreate": {"success": True}})
        return _Resp({"issue": {"comments": {"nodes": [{"body": "x board-sync:abc y"}]}}})
    monkeypatch.setattr(linear.urllib.request, "urlopen", fake_urlopen)
    board = linear.LinearBoard(KEY, "team")
    board.add_comment("ENG-1", "hello")
    assert board.has_comment("ENG-1", "board-sync:abc") and not board.has_comment("ENG-1", "zzz")


# --- AC4 -------------------------------------------------------------------------------

def test_flush_replays_in_order_and_empties_outbox(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    for m, t in [("started", "a"), ("red", "b"), ("green", "c")]:
        run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", m, t)
    board.unreachable = False
    assert run(sync, monkeypatch, root, board, "flush") == 0
    assert [b.split("\n")[0] for _, b in board.comments] == ["[started] a", "[red] b", "[green] c"]
    assert outbox(root) == []


def test_timeout_after_server_write_is_not_reposted(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), new_board()
    board.drop_response = True            # server stores it, the client sees a timeout
    run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "green", "once")
    assert len(board.comments) == 1 and len(outbox(root)) == 1
    board.drop_response = False
    assert run(sync, monkeypatch, root, board, "flush") == 0
    assert len(board.comments) == 1 and outbox(root) == []


def test_flush_stops_at_first_unreachable_and_keeps_rest(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    for t in ("a", "b"):
        run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "red", t)
    assert run(sync, monkeypatch, root, board, "flush") == 1
    assert len(outbox(root)) == 2


def test_flush_replays_status(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    run(sync, monkeypatch, root, board, "push", "status", "ENG-1", "ready-for-review")
    board.unreachable = False
    run(sync, monkeypatch, root, board, "flush")
    assert board.statuses == {"ENG-1": "In Review"} and outbox(root) == []


def test_flush_with_no_outbox_creates_nothing(sync, monkeypatch, tmp_path):
    root = project(tmp_path)
    assert run(sync, monkeypatch, root, new_board(), "flush") == 0
    assert not (Path(root) / ".board").exists()


# --- AC5 / AC6 -------------------------------------------------------------------------

def test_status_counts_unsynced(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), new_board()
    board.unreachable = True
    for t in ("a", "b", "c"):
        run(sync, monkeypatch, root, board, "push", "comment", "ENG-1", "red", t)
    capsys.readouterr()
    assert run(sync, monkeypatch, root, board, "status") == 0
    assert capsys.readouterr().out.strip() == "3 unsynced"


def test_status_zero_when_no_outbox(sync, monkeypatch, tmp_path, capsys):
    root = project(tmp_path)
    run(sync, monkeypatch, root, new_board(), "status")
    assert capsys.readouterr().out.strip() == "0 unsynced"


def test_wake_names_the_unsynced_line():
    text = (ROOT / "skills" / "wake" / "SKILL.md").read_text()
    assert "board_sync.py status" in text and "unsynced" in text


# --- local mode, stdlib ----------------------------------------------------------------

@pytest.mark.parametrize("argv", [("push", "comment", "T1", "green", "x"),
                                  ("push", "status", "T1", "done"), ("flush",), ("status",)])
def test_local_mode_does_nothing(sync, tmp_path, capsys, argv):
    assert sync.main(list(argv), root=str(tmp_path)) == 0
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr().out == ""


def test_outbox_module_is_stdlib_only():
    import ast
    import sys as _s
    tree = ast.parse((LIB / "board" / "outbox.py").read_text())
    names = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
    names |= {n.module.split(".")[0] for n in ast.walk(tree)
              if isinstance(n, ast.ImportFrom) and n.level == 0}
    assert names <= set(_s.stdlib_module_names) | {"board"}
