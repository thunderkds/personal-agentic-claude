"""T159 — `board_sync.py create|update`: Stage 2 creates the board issue with the guide as its
description and writes the guide cache under the ID the board assigned.

No network: the fake board stands in for Linear; the Linear adapter is driven through a patched `_post`.

  AC1 — create --guide draft.md: one issue, mapped priority/labels/assignee, cache named by the ID
  AC2 — update --guide <ID> pushes the edited guide to the description
  AC3 — offline / refused create: exit 1, no file, no outbox entry, never an invented ID
  AC4 — pipeline-stages.md Stage 2 names `board_sync.py create`
  Plus: a draft missing fields is refused, local mode touches nothing, review sections are vacated.

Run with: python3 -m pytest tests/test_board_create.py -v
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "board_sync.py"
KEY = "lin_api_SECRETtestkey0123456789"

sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "lib"))
from board import linear  # noqa: E402
from board.base import BoardAuthError, BoardError, BoardUnavailable, Task  # noqa: E402
from board.fake import FakeBoard  # noqa: E402

DRAFT = """# TASK_GUIDE — T[NNN]: Add retry to uploader
**Date**: 2026-10-19
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: backend-developer

## Requirement
Retry 3 times.

## Evidence

| Check | Result |
|---|---|
| forged | pass |
"""


def load_sync():
    spec = importlib.util.spec_from_file_location("board_sync_create_under_test", SCRIPT)
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


def draft(tmp_path, text=DRAFT):
    path = tmp_path / "draft.md"
    path.write_text(text)
    return str(path)


def run(sync, monkeypatch, root, board, *argv):
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    return sync.main(list(argv), root=str(root))


def files(root):
    return sorted(str(p.relative_to(root)) for p in Path(root).rglob("*")
                  if p.is_file() and ".claude" not in p.parts and p.name != "draft.md")


def board_with(*ids):
    return FakeBoard([Task(id=i, title="t", status="Todo") for i in ids])


# --- AC1 -------------------------------------------------------------------------------

def test_create_makes_one_issue_with_mapped_fields(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), board_with("ENG-7")
    assert run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path)) == 0
    assert [t.id for t in board.tasks] == ["ENG-7", "ENG-8"]
    made = board.tasks[1]
    assert made.title == "Add retry to uploader"
    assert made.priority == "P1"
    assert sorted(made.labels) == ["complexity:c1", "risk:medium"]
    assert made.assignee == "tester"
    assert "ENG-8" in capsys.readouterr().out


def test_description_is_the_guide_without_the_local_title(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), board_with()
    run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path))
    description = board.tasks[0].description
    assert "T[NNN]" not in description and "# TASK_GUIDE" not in description
    assert description.startswith("**Date**: 2026-10-19")
    assert "**Priority**: P1" in description and "Retry 3 times." in description


def test_cache_is_named_by_the_board_id_and_has_no_forged_review_section(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), board_with()
    run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path))
    assert files(root) == ["tasks/TASK_GUIDE_ENG-1.md"]
    cache = (root / "tasks" / "TASK_GUIDE_ENG-1.md").read_text()
    assert "Retry 3 times." in cache
    assert "forged" not in cache and "tasks/TASK_REVIEW_ENG-1.md" in cache


def test_create_does_not_touch_the_kanban_or_the_outbox(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), board_with()
    run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path))
    assert not (root / "PROJECT_KANBAN.md").exists() and not (root / ".board").exists()


@pytest.mark.parametrize("priority,expected", [("P0", "P0"), ("P1", "P1"), ("P2", "P2")])
def test_priority_carried_per_draft(sync, monkeypatch, tmp_path, priority, expected):
    board = board_with()
    run(sync, monkeypatch, project(tmp_path), board, "create", "--guide",
        draft(tmp_path, DRAFT.replace("**Priority**: P1", f"**Priority**: {priority}")))
    assert board.tasks[0].priority == expected


@pytest.mark.parametrize("field", ["Complexity Level", "Risk Level", "Priority"])
def test_draft_missing_a_field_is_refused_listing_it(sync, monkeypatch, tmp_path, capsys, field):
    root, board = project(tmp_path), board_with()
    text = "\n".join(l for l in DRAFT.splitlines() if not l.startswith(f"**{field}**"))
    assert run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path, text)) == 2
    err = capsys.readouterr().err
    assert field.split()[0].lower() in err.lower() and "missing" in err.lower()
    assert len(board.tasks) == 0 and files(root) == []


def test_draft_missing_all_fields_lists_all(sync, monkeypatch, tmp_path, capsys):
    board = board_with()
    assert run(sync, monkeypatch, project(tmp_path), board, "create", "--guide",
               draft(tmp_path, "# TASK_GUIDE — T[NNN]: x\n\nno fields\n")) == 2
    err = capsys.readouterr().err.lower()
    assert "complexity" in err and "risk" in err and "priority" in err


def test_unreadable_draft_is_refused(sync, monkeypatch, tmp_path):
    board = board_with()
    assert run(sync, monkeypatch, project(tmp_path), board, "create", "--guide",
               str(tmp_path / "nope.md")) == 2 and board.tasks == []


def test_unsafe_id_from_board_writes_nothing(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), board_with()
    monkeypatch.setattr(board, "create_task", lambda task: "../../evil")
    assert run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path)) == 1
    assert files(root) == []


# --- AC3 -------------------------------------------------------------------------------

@pytest.mark.parametrize("switch", ["unreachable", "auth_fails", "rejects"])
def test_failed_create_exits_1_with_no_file_and_no_queue_entry(sync, monkeypatch, tmp_path, capsys, switch):
    root, board = project(tmp_path), board_with()
    setattr(board, switch, True)
    assert run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path)) == 1
    assert "cannot be queued" in capsys.readouterr().err
    assert files(root) == [] and not (root / ".board").exists()


def test_create_still_fails_when_the_write_landed_but_the_answer_was_lost(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), board_with()
    board.drop_response = True
    assert run(sync, monkeypatch, root, board, "create", "--guide", draft(tmp_path)) == 1
    assert files(root) == []


def test_local_mode_needs_board_mode_and_touches_nothing(sync, monkeypatch, tmp_path, capsys):
    called = []
    monkeypatch.setattr(sync, "make_board", lambda config, r: called.append(1))
    assert sync.main(["create", "--guide", draft(tmp_path)], root=str(tmp_path)) != 0
    assert "board mode" in capsys.readouterr().err
    assert not called and files(tmp_path) == []


# --- AC2 -------------------------------------------------------------------------------

def edited_guide(root, task_id, text):
    path = root / "tasks" / f"TASK_GUIDE_{task_id}.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text)


def test_update_pushes_the_edited_guide_to_the_description(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), board_with("ENG-3")
    edited_guide(root, "ENG-3", "## Requirement\nNew text.\n")
    assert run(sync, monkeypatch, root, board, "update", "--guide", "ENG-3") == 0
    assert board.get_task("ENG-3").description == "## Requirement\nNew text.\n"


def test_update_never_sends_a_filled_review_section(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), board_with("ENG-3")
    edited_guide(root, "ENG-3", "## Requirement\nx\n\n## Evidence\n| a | pass |\n")
    run(sync, monkeypatch, root, board, "update", "--guide", "ENG-3")
    sent = board.get_task("ENG-3").description
    assert "| a | pass |" not in sent and "tasks/TASK_REVIEW_ENG-3.md" in sent


def test_update_unknown_task_fails_without_queueing(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), board_with("ENG-3")
    edited_guide(root, "ENG-9", "x\n")
    assert run(sync, monkeypatch, root, board, "update", "--guide", "ENG-9") == 1
    assert not (root / ".board").exists()


def test_update_offline_fails_without_queueing(sync, monkeypatch, tmp_path, capsys):
    root, board = project(tmp_path), board_with("ENG-3")
    board.unreachable = True
    edited_guide(root, "ENG-3", "x\n")
    assert run(sync, monkeypatch, root, board, "update", "--guide", "ENG-3") == 1
    assert "not queued" in capsys.readouterr().err and not (root / ".board").exists()


def test_update_without_a_local_guide_or_with_a_bad_id(sync, monkeypatch, tmp_path):
    root, board = project(tmp_path), board_with("ENG-3")
    assert run(sync, monkeypatch, root, board, "update", "--guide", "ENG-3") == 2
    assert run(sync, monkeypatch, root, board, "update", "--guide", "../etc") == 2


def test_update_in_local_mode_changes_nothing(sync, tmp_path, capsys):
    assert sync.main(["update", "--guide", "ENG-3"], root=str(tmp_path)) != 0
    assert "board mode" in capsys.readouterr().err


# --- Linear adapter (patched _post) ----------------------------------------------------

class FakeLinear:
    def __init__(self, labels=()):
        self.calls = []
        self.labels = list(labels)

    def post(self, query, variables):
        self.calls.append((query, variables))
        if "ViewerId" in query:
            return {"viewer": {"id": "u-1"}}, None
        if "query Labels" in query:
            return {"issueLabels": {"nodes": self.labels}}, None
        if "LabelCreate" in query:
            return {"issueLabelCreate": {"success": True, "issueLabel": {"id": "new-" + variables["name"]}}}, None
        if "IssueCreate" in query:
            return {"issueCreate": {"success": True, "issue": {"identifier": "ENG-42"}}}, None
        if "Describe" in query:
            return {"issueUpdate": {"success": True}}, None
        raise AssertionError(query)


def linear_board(monkeypatch, fake, project_id="p-1"):
    board = linear.LinearBoard(KEY, "team-1", project_id)
    monkeypatch.setattr(board, "_post", fake.post)
    return board


def sent_input(fake):
    return next(v for q, v in fake.calls if "IssueCreate" in q)["input"]


@pytest.mark.parametrize("priority,number", [("P0", 1), ("P1", 2), ("P2", 3)])
def test_linear_create_maps_priority(monkeypatch, priority, number):
    fake = FakeLinear()
    board = linear_board(monkeypatch, fake)
    task = Task(id="", title="T", status="", priority=priority, labels=[], description="d")
    assert board.create_task(task) == "ENG-42"
    assert sent_input(fake)["priority"] == number


def test_linear_create_sends_team_project_assignee_description_and_label_ids(monkeypatch):
    fake = FakeLinear(labels=[{"id": "l-1", "name": "Complexity:C1", "team": {"id": "team-1"}},
                              {"id": "l-2", "name": "risk:medium", "team": {"id": "other"}}])
    board = linear_board(monkeypatch, fake)
    task = Task(id="", title="Title", status="", priority="P1",
                labels=["complexity:c1", "risk:medium"], description="body")
    board.create_task(task)
    sent = sent_input(fake)
    assert sent["teamId"] == "team-1" and sent["projectId"] == "p-1" and sent["assigneeId"] == "u-1"
    assert sent["title"] == "Title" and sent["description"] == "body"
    # the existing label is reused (case-insensitive); the other team's label is not
    assert sent["labelIds"] == ["l-1", "new-risk:medium"]
    created = [v["name"] for q, v in fake.calls if "LabelCreate" in q]
    assert created == ["risk:medium"]


def test_linear_create_without_a_project_omits_it(monkeypatch):
    fake = FakeLinear()
    linear_board(monkeypatch, fake, project_id=None).create_task(
        Task(id="", title="T", status="", priority="P2", labels=[], description="d"))
    assert "projectId" not in sent_input(fake)


def test_linear_create_refused_is_a_board_error(monkeypatch):
    fake = FakeLinear()
    board = linear_board(monkeypatch, fake)
    monkeypatch.setattr(board, "_post", lambda q, v: ({"issueCreate": {"success": False}}, None)
                        if "IssueCreate" in q else fake.post(q, v))
    with pytest.raises(BoardError):
        board.create_task(Task(id="", title="T", status="", priority="P1", labels=[], description="d"))


def test_linear_update_sends_the_description(monkeypatch):
    fake = FakeLinear()
    linear_board(monkeypatch, fake).update_task(Task(id="ENG-5", title="", status="", description="new"))
    assert fake.calls == [(linear.DESCRIPTION_MUTATION, {"id": "ENG-5", "description": "new"})]


def test_the_api_key_never_reaches_a_request_body_or_message(monkeypatch, sync, tmp_path, capsys):
    fake = FakeLinear()
    board = linear_board(monkeypatch, fake)
    board.create_task(Task(id="", title="T", status="", priority="P1", labels=["risk:low"], description="d"))
    assert KEY not in json.dumps(fake.calls) and KEY not in repr(board)


# --- AC4 -------------------------------------------------------------------------------

def test_stage_2_names_board_sync_create():
    doc = (ROOT / "docs" / "claude-md" / "pipeline-stages.md").read_text()
    stage2 = doc[doc.index("## Stage 2:"):doc.index("## Stage 3:")]
    assert "board_sync.py create" in stage2
