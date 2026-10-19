"""Linear board adapter (T154): GraphQL over `urllib.request`, stdlib only (NFR-003).

The API key is passed in by the caller, who reads it from `LINEAR_API_KEY`. It is sent in
the `Authorization` header and nowhere else: it is not stored under a public attribute,
and no `BoardError` message is built from anything that could contain it.

One request per page of 100 issues (NFR-002). A 429, or `X-RateLimit-Requests-Remaining`
reaching 0 with pages left, stops the pull — never a retry loop.
"""
import json
import urllib.error
import urllib.request

from board.base import BoardAdapter, BoardError, Task

URL = "https://api.linear.app/graphql"
TIMEOUT = 30

# FR-012: Linear priority 1 Urgent, 2 High, 3 Medium, 4 Low; 0 No priority (untriaged).
PRIORITY = {1: "P0", 2: "P1", 3: "P2", 4: "P2"}

ISSUE_FIELDS = """identifier title description priority
      state { name type } assignee { displayName } labels { nodes { name } }"""
LIST_QUERY = """query Issues($filter: IssueFilter, $after: String) {
  issues(first: 100, after: $after, filter: $filter) {
    nodes { %s }
    pageInfo { hasNextPage endCursor }
  }
}""" % ISSUE_FIELDS
GET_QUERY = "query Issue($id: String!) { issue(id: $id) { %s } }" % ISSUE_FIELDS


def task_from_node(node):
    state = node.get("state") or {}
    assignee = node.get("assignee") or {}
    return Task(
        id=str(node.get("identifier") or ""),
        title=node.get("title") or "",
        status=state.get("name") or "",
        status_type=state.get("type") or "",
        priority=PRIORITY.get(node.get("priority")),
        labels=[l.get("name", "") for l in (node.get("labels") or {}).get("nodes") or []],
        assignee=assignee.get("displayName"),
        description=node.get("description") or "",
    )


class LinearBoard(BoardAdapter):
    def __init__(self, api_key, team, project=None):
        self._auth = {"Authorization": api_key}
        self.team = team
        self.project = project

    def __repr__(self):
        return f"LinearBoard(team={self.team!r}, project={self.project!r})"

    def _post(self, query, variables):
        """(data, rate-limit headroom or None). Raises BoardError on any failure."""
        request = urllib.request.Request(
            URL, data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={"Content-Type": "application/json", **self._auth}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = json.loads(response.read())
                remaining = response.headers.get("X-RateLimit-Requests-Remaining")
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise BoardError("Linear rate limit reached (HTTP 429); try again later") from None
            raise BoardError(f"Linear returned HTTP {exc.code}") from None
        except urllib.error.URLError:
            raise BoardError("cannot reach Linear (network error)") from None
        except (OSError, ValueError):
            raise BoardError("no usable answer from Linear (timeout or invalid response)") from None
        if not isinstance(body, dict) or body.get("errors") or not isinstance(body.get("data"), dict):
            raise BoardError("Linear rejected the query (GraphQL error)")
        try:
            remaining = int(remaining) if remaining is not None else None
        except ValueError:
            remaining = None
        return body["data"], remaining

    def list_tasks(self):
        flt = {"team": {"id": {"eq": self.team}}}
        if self.project:
            flt["project"] = {"id": {"eq": self.project}}
        tasks, after = [], None
        while True:
            data, remaining = self._post(LIST_QUERY, {"filter": flt, "after": after})
            try:
                issues = data["issues"]
                tasks += [task_from_node(n) for n in issues["nodes"]]
                more, after = issues["pageInfo"]["hasNextPage"], issues["pageInfo"]["endCursor"]
            except (KeyError, TypeError, AttributeError):
                raise BoardError("unexpected answer shape from Linear") from None
            if not more:
                return tasks
            if remaining is not None and remaining <= 0:
                raise BoardError("Linear rate limit exhausted before the last page; try again later")

    def get_task(self, task_id):
        data, _ = self._post(GET_QUERY, {"id": task_id})
        node = data.get("issue")
        return task_from_node(node) if isinstance(node, dict) else None
