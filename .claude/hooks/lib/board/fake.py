"""In-memory board loaded from a JSON fixture (T154). Tests use it; no network.

Selected with `{"board": "fake", "fake_board": "<path to JSON list of tasks>"}`.
"""
import json

from board.base import BoardAdapter, BoardError, BoardUnavailable, Task


class FakeBoard(BoardAdapter):
    def __init__(self, tasks):
        self.tasks = list(tasks)
        self.comments = []        # (task_id, body), in arrival order
        self.statuses = {}        # task_id -> board status name
        self.unreachable = False  # test switch: every write raises BoardUnavailable
        self.drop_response = False  # test switch: the write lands, the client still times out
        self.rejects = False      # test switch: every write raises a non-transient BoardError

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
        if self.unreachable:
            raise BoardUnavailable("fake board unreachable")
        return any(t == task_id and marker in b for t, b in self.comments)

    def set_status(self, task_id, status):
        self._write_check()
        self.statuses[task_id] = status
        self._after_write()
