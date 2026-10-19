"""In-memory board loaded from a JSON fixture (T154). Tests use it; no network.

Selected with `{"board": "fake", "fake_board": "<path to JSON list of tasks>"}`.
"""
import json

from board.base import BoardAdapter, BoardError, Task


class FakeBoard(BoardAdapter):
    def __init__(self, tasks):
        self.tasks = list(tasks)

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
