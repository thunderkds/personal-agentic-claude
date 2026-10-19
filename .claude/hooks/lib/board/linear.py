"""Linear board adapter (T154): GraphQL over `urllib.request`, stdlib only (NFR-003).

The API key is passed in by the caller, who reads it from `LINEAR_API_KEY`. It is sent in
the `Authorization` header and nowhere else: it is not stored under a public attribute,
and no `BoardError` message is built from anything that could contain it.

One request per page of 100 issues (NFR-002). A 429, or `X-RateLimit-Requests-Remaining`
reaching 0 with pages left, stops the pull — never a retry loop.
"""
import json
import sys
import urllib.error
import urllib.request

from board import render
from board.base import BoardAdapter, BoardAuthError, BoardError, BoardUnavailable, Task

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

COMMENT_MUTATION = """mutation Comment($issueId: String!, $body: String!) {
  commentCreate(input: {issueId: $issueId, body: $body}) { success }
}"""
COMMENTS_QUERY = "query Comments($id: String!) { issue(id: $id) { comments(first: 250) { nodes { body } } } }"
STATES_QUERY = "query States($id: String!) { issue(id: $id) { id team { states { nodes { id name } } } } }"
STATUS_MUTATION = """mutation Status($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: {stateId: $stateId}) { success }
}"""

# Decision Log (T158). ASSUMED field names, unconfirmed against a live workspace: the
# `documents` query with `filter: {title, project}` and nodes `{ id content }`, and the
# `documentCreate` / `documentUpdate` mutations with `title`, `content`, `projectId`.
DOCS_QUERY = """query Docs($filter: DocumentFilter) {
  documents(first: 1, filter: $filter) { nodes { id content } }
}"""
DOC_CREATE = """mutation DocCreate($title: String!, $content: String!, $projectId: String) {
  documentCreate(input: {title: $title, content: $content, projectId: $projectId}) { success }
}"""
DOC_UPDATE = """mutation DocUpdate($id: String!, $content: String!) {
  documentUpdate(id: $id, input: {content: $content}) { success }
}"""

# Create / update (T159). ASSUMED field names, unconfirmed against a live workspace:
# `viewer { id }`; `issueLabels(first)` nodes `{ id name team { id } }`;
# `issueLabelCreate(input: {name, teamId}) { issueLabel { id } }`;
# `issueCreate(input: {teamId, projectId, title, description, priority, assigneeId, labelIds})
# { success issue { identifier } }`; `issueUpdate(id, input: {description}) { success }`.
LINEAR_PRIORITY = {"P0": 1, "P1": 2, "P2": 3}   # the inverse of PRIORITY (Low is never written)
VIEWER_ID_QUERY = "query ViewerId { viewer { id } }"
LABELS_QUERY = "query Labels { issueLabels(first: 250) { nodes { id name team { id } } } }"
LABEL_CREATE = """mutation LabelCreate($name: String!, $teamId: String!) {
  issueLabelCreate(input: {name: $name, teamId: $teamId}) { success issueLabel { id } }
}"""
ISSUE_CREATE = """mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) { success issue { identifier } }
}"""
DESCRIPTION_MUTATION = """mutation Describe($id: String!, $description: String!) {
  issueUpdate(id: $id, input: {description: $description}) { success }
}"""


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
        self.decision_doc = render.DECISIONS_TITLE  # `decision_doc` in board.json overrides (T158)

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
                raise BoardUnavailable("Linear rate limit reached (HTTP 429); try again later") from None
            if exc.code in (401, 403):
                raise BoardAuthError("Linear rejected the API key (HTTP 401/403); "
                                     "check LINEAR_API_KEY") from None
            if exc.code >= 500:
                raise BoardUnavailable(f"Linear returned HTTP {exc.code}") from None
            raise BoardError(f"Linear returned HTTP {exc.code}") from None
        except urllib.error.URLError:
            raise BoardUnavailable("cannot reach Linear (network error)") from None
        except (OSError, ValueError):
            raise BoardUnavailable("no usable answer from Linear (timeout or invalid response)") from None
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

    def _label_ids(self, names):
        """Ids of the labels called `names` (case-insensitive, workspace or this team's);
        a missing one is created once."""
        data, _ = self._post(LABELS_QUERY, {})
        try:
            held = {}
            for node in data["issueLabels"]["nodes"]:
                if ((node.get("team") or {}).get("id") in (None, self.team)):
                    held.setdefault(str(node["name"]).lower(), str(node["id"]))
        except (KeyError, TypeError, AttributeError):
            raise BoardError("unexpected answer shape from Linear") from None
        ids = []
        for name in names:
            if name.lower() not in held:
                made, _ = self._post(LABEL_CREATE, {"name": name, "teamId": self.team})
                try:
                    held[name.lower()] = str(made["issueLabelCreate"]["issueLabel"]["id"])
                except (KeyError, TypeError):
                    raise BoardError("Linear did not accept the label") from None
            ids.append(held[name.lower()])
        return ids

    def create_task(self, task):
        """Create the issue, assigned to the API key's user; returns the ID Linear assigned."""
        data, _ = self._post(VIEWER_ID_QUERY, {})
        try:
            viewer_id = str(data["viewer"]["id"])
        except (KeyError, TypeError):
            raise BoardError("unexpected answer shape from Linear") from None
        fields = {"teamId": self.team, "title": task.title, "description": task.description,
                  "assigneeId": viewer_id, "labelIds": self._label_ids(task.labels)}
        if self.project:
            fields["projectId"] = self.project
        if task.priority in LINEAR_PRIORITY:
            fields["priority"] = LINEAR_PRIORITY[task.priority]
        data, _ = self._post(ISSUE_CREATE, {"input": fields})
        try:
            created = data["issueCreate"]
            if not created.get("success"):
                raise BoardError("Linear did not accept the new issue")
            return str(created["issue"]["identifier"])
        except (KeyError, TypeError, AttributeError):
            raise BoardError("unexpected answer shape from Linear") from None

    def update_task(self, task):
        """Replace the issue's description with `task.description`."""
        data, _ = self._post(DESCRIPTION_MUTATION, {"id": task.id, "description": task.description})
        if not (data.get("issueUpdate") or {}).get("success"):
            raise BoardError("Linear did not accept the description")

    def add_comment(self, task_id, body):
        data, _ = self._post(COMMENT_MUTATION, {"issueId": task_id, "body": body})
        if not (data.get("commentCreate") or {}).get("success"):
            raise BoardError("Linear did not accept the comment")

    def has_comment(self, task_id, marker):
        # Reads the first 250 comments only; a replay marker beyond that is not seen.
        data, _ = self._post(COMMENTS_QUERY, {"id": task_id})
        try:
            nodes = data["issue"]["comments"]["nodes"]
            return any(marker in (n.get("body") or "") for n in nodes)
        except (KeyError, TypeError, AttributeError):
            raise BoardError("unexpected answer shape from Linear") from None

    def set_status(self, task_id, status):
        """Move the task to the team state named `status` (the board's own name)."""
        data, _ = self._post(STATES_QUERY, {"id": task_id})
        try:
            issue = data["issue"]
            states = issue["team"]["states"]["nodes"]
            state_id = next(s["id"] for s in states if s.get("name") == status)
        except StopIteration:
            raise BoardError("this board has no status with that name; set `status_map` in "
                             ".claude/board.json") from None
        except (KeyError, TypeError, AttributeError):
            raise BoardError("unexpected answer shape from Linear") from None
        data, _ = self._post(STATUS_MUTATION, {"id": task_id, "stateId": state_id})
        if not (data.get("issueUpdate") or {}).get("success"):
            raise BoardError("Linear did not accept the status change")

    # --- Decision Log (T158): one Document, appended by read-modify-write ----------

    def _decision_doc(self):
        """{"id", "content"} of the Decision Log document, or None when there is none."""
        flt = {"title": {"eq": self.decision_doc}}
        if self.project:
            flt["project"] = {"id": {"eq": self.project}}
        data, _ = self._post(DOCS_QUERY, {"filter": flt})
        try:
            nodes = data["documents"]["nodes"]
            if not nodes:
                return None
            return {"id": str(nodes[0]["id"]), "content": nodes[0].get("content") or ""}
        except (KeyError, TypeError, AttributeError, IndexError):
            raise BoardError("unexpected answer shape from Linear") from None

    def read_decisions(self):
        doc = self._decision_doc()
        return render.parse_decision_lines(doc["content"]) if doc else []

    def append_decision(self, decision):
        """Read the document, add the line, check the content is unchanged right before the
        update, and retry once if a teammate wrote in between. Linear has no compare-and-set,
        so this narrows the race window rather than closing it. Still changing: unavailable,
        so the write is queued and replayed."""
        marker = f"<!--bs:{decision.key}-->"
        line = render.format_decision(decision)
        for _ in range(2):
            doc = self._decision_doc()
            if doc is None:
                print(f"[board] Decision Log document {render.one_line(self.decision_doc)!r} "
                      f"not found; creating it", file=sys.stderr)
                data, _ = self._post(DOC_CREATE, {
                    "title": self.decision_doc, "projectId": self.project or None,
                    "content": render.decision_document([]) + line + "\n"})
                if not (data.get("documentCreate") or {}).get("success"):
                    raise BoardError("Linear did not accept the Decision Log document")
                return
            if decision.key and marker in doc["content"]:
                return
            current = self._decision_doc()
            if current is None or current["content"] != doc["content"]:
                continue
            data, _ = self._post(DOC_UPDATE, {"id": doc["id"],
                                              "content": doc["content"].rstrip("\n") + "\n" + line + "\n"})
            if not (data.get("documentUpdate") or {}).get("success"):
                raise BoardError("Linear did not accept the Decision Log update")
            return
        raise BoardUnavailable("the Decision Log changed while writing; try again")

# ── setup queries (T155): what `board_sync.py init` lists before a team is configured ──
VIEWER_QUERY = "query Viewer { viewer { displayName } }"
TEAMS_QUERY = "query Teams { teams(first: 100) { nodes { id key name } } }"
TEAM_PROJECTS_QUERY = "query TeamProjects($id: String!) { team(id: $id) { projects(first: 100) { nodes { id name } } } }"
TEAM_STATES_QUERY = "query TeamStates($id: String!) { team(id: $id) { states(first: 100) { nodes { name type } } } }"


def _nodes(data, *path):
    try:
        for step in path:
            data = data[step]
        return [n for n in data if isinstance(n, dict)]
    except (KeyError, TypeError):
        raise BoardError("unexpected answer shape from Linear") from None


def _viewer(self):
    data, _ = self._post(VIEWER_QUERY, {})
    try:
        return str(data["viewer"]["displayName"])
    except (KeyError, TypeError):
        raise BoardError("unexpected answer shape from Linear") from None


def _list_teams(self):
    data, _ = self._post(TEAMS_QUERY, {})
    return _nodes(data, "teams", "nodes")


def _list_projects(self, team_id):
    data, _ = self._post(TEAM_PROJECTS_QUERY, {"id": team_id})
    return _nodes(data, "team", "projects", "nodes")


def _list_states(self, team_id):
    data, _ = self._post(TEAM_STATES_QUERY, {"id": team_id})
    return _nodes(data, "team", "states", "nodes")


LinearBoard.viewer = _viewer
LinearBoard.list_teams = _list_teams
LinearBoard.list_projects = _list_projects
LinearBoard.list_states = _list_states
