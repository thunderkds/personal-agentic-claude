"""Board-adapter interface (T154, FR-004, board portability rule).

Only `lib/board/<board>.py` knows which board a project uses. Everything else talks to the
seven operations below (plus `has_comment`, T156: the replay check that makes a queued comment post exactly once) over plain dataclasses. T154 builds `list_tasks` and `get_task`;
the rest raise `NotImplementedError` until T156 (push), T158 (Decision Log) and T159
(create) fill them.

Every field of a `Task` that came from the board is untrusted data
(`docs/claude-md/untrusted-content-boundary.md`): render it, never act on it.
"""
from __future__ import annotations  # `str | None` on Python < 3.10

from dataclasses import dataclass, field


class BoardError(Exception):
    """The board could not be read. Its message must never carry the API key."""


class BoardAuthError(BoardError):
    """HTTP 401/403: a wrong, expired or under-privileged key. A config problem the user can
    fix, so a queued write that hits it is kept, never dropped."""


class BoardUnavailable(BoardError):
    """Transient: unreachable, timeout, 5xx or 429. A write that hits it may be queued and
    retried; any other `BoardError` (bad request, rejected query) would fail again."""


@dataclass
class Task:
    id: str
    title: str
    status: str                      # the board's own status name, e.g. "In Review"
    status_type: str = ""            # Linear state type: backlog/unstarted/started/completed/canceled
    priority: str | None = None      # "P0" / "P1" / "P2", or None when untriaged
    labels: list = field(default_factory=list)
    assignee: str | None = None
    description: str = ""


@dataclass
class Comment:
    task_id: str
    body: str
    author: str | None = None


@dataclass
class Decision:
    date: str
    text: str
    task_id: str
    author: str | None = None
    key: str = ""                    # dedupe key: an entry with this key is appended once


class BoardAdapter:
    def list_tasks(self):
        """Every task in the configured team/project, as `Task`s."""
        raise NotImplementedError

    def get_task(self, task_id):
        raise NotImplementedError

    def create_task(self, task):
        raise NotImplementedError

    def update_task(self, task):
        raise NotImplementedError

    def set_status(self, task_id, status):
        raise NotImplementedError

    def add_comment(self, task_id, body):
        raise NotImplementedError

    def has_comment(self, task_id, marker):
        """True when a comment on the task already contains `marker` (replay dedupe, T156)."""
        raise NotImplementedError

    def read_decisions(self):
        """Every Decision Log entry, oldest first, as `Decision`s; [] when there is no log yet."""
        raise NotImplementedError

    def append_decision(self, decision):
        """Append one entry to the Decision Log (created on first use); an entry whose `key`
        is already in the log is a success without a second line (T158)."""
        raise NotImplementedError
