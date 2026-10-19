"""In-memory board loaded from a JSON fixture (T154). Tests use it; no network.

Selected with `{"board": "fake", "fake_board": "<path to JSON list of tasks>"}`.
"""
import json

from board import render
from board.base import BoardAdapter, BoardAuthError, BoardError, BoardUnavailable, Task


class FakeBoard(BoardAdapter):
    def __init__(self, tasks):
        self.tasks = list(tasks)
        self.comments = []        # (task_id, body), in arrival order
        self.statuses = {}        # task_id -> board status name
        self.unreachable = False  # test switch: every write raises BoardUnavailable
        self.drop_response = False  # test switch: the write lands, the client still times out
        self.auth_fails = False   # test switch: every call raises BoardAuthError
        self.rejects = False      # test switch: every write raises a non-transient BoardError
        self.decision_content = None  # the Decision Log document text; None until first use (T158)
        self.id_prefix = "ENG"    # create_task numbers new issues <id_prefix>-<n> (T159)
        self.viewer_name = "tester"  # the assignee a created issue gets (the board user)

    @classmethod
    def from_file(cls, path):
        try:
            with open(path, encoding="utf-8") as f:
                return cls(Task(**item) for item in json.load(f))
        except (OSError, ValueError, TypeError) as exc:
            raise BoardError(f"cannot load fake board ({type(exc).__name__})") from None

    def list_tasks(self):
        return list(self.tasks)

    def get_task(self, task_id):
        return next((t for t in self.tasks if t.id == task_id), None)

    def _write_check(self):
        if self.auth_fails:
            raise BoardAuthError("Linear rejected the API key (HTTP 401/403); check LINEAR_API_KEY")
        if self.rejects:
            raise BoardError("fake board rejected the write")
        if self.unreachable:
            raise BoardUnavailable("fake board unreachable")

    def _after_write(self):
        if self.drop_response:
            raise BoardUnavailable("fake board timed out after the write")

    def add_comment(self, task_id, body):
        self._write_check()
        self.comments.append((task_id, body))
        self._after_write()

    def has_comment(self, task_id, marker):
        if self.auth_fails:
            raise BoardAuthError("Linear rejected the API key (HTTP 401/403); check LINEAR_API_KEY")
        if self.unreachable:
            raise BoardUnavailable("fake board unreachable")
        return any(t == task_id and marker in b for t, b in self.comments)

    def create_task(self, task):
        """The board assigns the ID (T159): one past the highest `<id_prefix>-<n>` held."""
        self._write_check()
        numbers = [int(t.id.rsplit("-", 1)[1]) for t in self.tasks
                   if t.id.startswith(self.id_prefix + "-") and t.id.rsplit("-", 1)[1].isdigit()]
        created = Task(id=f"{self.id_prefix}-{max(numbers, default=0) + 1}", title=task.title,
                       status="Todo", status_type="unstarted", priority=task.priority,
                       labels=list(task.labels), assignee=self.viewer_name,
                       description=task.description)
        self.tasks.append(created)
        self._after_write()
        return created.id

    def update_task(self, task):
        """Replace the description of the held task with `task.id` (T159)."""
        self._write_check()
        held = self.get_task(task.id)
        if held is None:
            raise BoardError("the board has no such task")
        held.description = task.description
        self._after_write()

    def set_status(self, task_id, status):
        self._write_check()
        self.statuses[task_id] = status
        self._after_write()

    def read_decisions(self):
        if self.auth_fails:
            raise BoardAuthError("Linear rejected the API key (HTTP 401/403); check LINEAR_API_KEY")
        if self.unreachable:
            raise BoardUnavailable("fake board unreachable")
        return render.parse_decision_lines(self.decision_content or "")

    def append_decision(self, decision):
        self._write_check()
        if self.decision_content is None:
            self.decision_content = render.decision_document([])
        if not (decision.key and f"<!--bs:{decision.key}-->" in self.decision_content):
            self.decision_content += render.format_decision(decision) + "\n"
        self._after_write()
