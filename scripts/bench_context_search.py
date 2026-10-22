#!/usr/bin/env python3
"""Benchmark easy-context search against the old way (grep + Read) (T171).

    python3 scripts/bench_context_search.py                       # script mode (free, repeatable)
    python3 scripts/bench_context_search.py --agent --limit 5     # real-agent mode (costs tokens)

Question: to find code or evidence in this repo, is the easy-context MCP search faster,
more correct and cheaper in tokens than Grep/Glob + Read?

Definitions (the three script-mode methods, per question):
  Old way      `grep -rnIE <grep_pattern>` over the root (skips .git, __pycache__,
               node_modules, .pytest_cache, event-trace logs and the benchmark's own artifacts), files ranked
               by match count (ties by path), then the top-ranked file is read in full.
               Text returned = the grep output + that file.
  Old, bounded How a careful agent works: `grep -rcIE` (file:count list, capped at 50 lines),
               same ranking, then a ranged Read of +-40 lines around the first match in the
               top file. Text returned = the capped list + those lines.
  Context way  `search_semantic(question, k=5)`, then `get_slice` of the top hit.
               Text returned = both tool results.
  Time         wall-clock seconds for the whole flow; script mode reports the median of 3
               runs. One warm-up call is made first and excluded.
  Correctness  hit@1 / hit@5: an `expected_paths` file is the first / one of the first five
               ranked files (grep: files by match count; context: hits in score order).
               multi_hop and callers questions need EVERY expected file in the top five for
               hit@5 (any for hit@1). negative questions expect no file: grep methods are
               right when they find none; the semantic search always returns hits, so it is
               graded only in agent mode.
  Tokens       script mode: characters / 4, labeled "estimated". Agent modes: the `usage` of
               `claude -p --output-format json` (input + output + cache).

Modes:
  (default)    script mode, three methods, every question
  --agent      real agents (`claude -p`): every question once per method (easy-context tools
               only vs Grep/Glob/Read only), plus repeats of 5 fixed questions for spread
  --lifecycle  4 two-question chains per method: Q2 in the same session, resumed after the
               prompt cache expired, and in a closed + fresh session
  --upkeep     index cost: full and incremental re-index, plus a staleness probe that uses
               a new untracked file and removes it again
Real-agent runs ask to confirm unless --yes, allow no tool that edits files, and stop when
cumulative cost would pass --cap (default $12). Output: a Markdown report and a JSON file
with every raw row, in reports/.

Exit codes: 0 ok, 2 bad setup (server unreachable, `claude` missing, bad arguments).
"""
import argparse
import concurrent.futures
import datetime
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(ROOT, "tests", "fixtures", "context_search_questions.json")
DEFAULT_URL = "http://127.0.0.1:8767/mcp"
# The checkout the server indexes (a worktree is not indexed); sent as X-Easy-Context-Root.


def main_checkout(path):
    """The main checkout of the repo `path` belongs to (the worktree's common git dir parent)."""
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                cwd=path, capture_output=True, text=True, check=True).stdout.strip()
        return os.path.dirname(common) if common.endswith(".git") else path
    except (OSError, subprocess.SubprocessError):
        return path


DEFAULT_ROOT = os.environ.get("EASY_CONTEXT_ROOT") or main_checkout(ROOT)
# event-trace holds the benchmark session's own logged commands (they quote every question).
GREP_EXCLUDE_DIRS = [".git", "__pycache__", "node_modules", ".pytest_cache", "event-trace"]
# Files that quote the benchmark's own questions would pollute both methods.
GREP_EXCLUDE_FILES = ["context_search_questions.json", "TASK_GUIDE_T171.md", "TASK_REVIEW_T171.md",
                      "TASK_GUIDE_T172.md", "TASK_REVIEW_T172.md", "context-search-benchmark-*.md"]
CTX_TOOLS = ["mcp__easy-context__search_semantic", "mcp__easy-context__get_slice",
             "mcp__easy-context__get_related"]
OLD_TOOLS = ["Grep", "Glob", "Read"]
TIMING_RUNS = 3
K = 5


class ServerError(Exception):
    pass


# ---------------------------------------------------------------- MCP client

def parse_mcp_body(body, content_type=""):
    """JSON-RPC message from a streamable-HTTP body: SSE (`data:` line) or plain JSON."""
    text = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    if "event-stream" in content_type or text.lstrip().startswith(("event:", "data:")):
        data = [ln[5:].strip() for ln in text.splitlines() if ln.startswith("data:")]
        if not data:
            raise ServerError("no data: line in event-stream response")
        return json.loads(data[-1])
    return json.loads(text)


class McpClient:
    def __init__(self, url, root, timeout=60):
        self.url, self.root, self.timeout = url, root, timeout
        self.session = None
        self._id = 0

    def _post(self, payload):
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream",
                   "X-Easy-Context-Root": self.root}
        if self.session:
            headers["mcp-session-id"] = self.session
        req = urllib.request.Request(self.url, json.dumps(payload).encode(), headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                sid = resp.headers.get("mcp-session-id")
                if sid:
                    self.session = sid
                ctype = resp.headers.get("content-type", "")
        except (urllib.error.URLError, OSError) as err:
            raise ServerError(f"easy-context server not reachable at {self.url}") from err
        return parse_mcp_body(body, ctype) if body.strip() else None

    def rpc(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        reply = self._post(msg)
        if reply is None or "error" in reply:
            raise ServerError(f"{method} failed: {reply}")
        return reply["result"]

    def start(self):
        self.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                "clientInfo": {"name": "bench_context_search", "version": "1"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, name, arguments):
        """(text the tool returned, parsed JSON of it)."""
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        text = "".join(part.get("text", "") for part in result.get("content", []))
        if result.get("isError"):
            raise ServerError(f"{name} returned an error: {text[:200]}")
        try:
            return text, json.loads(text)
        except ValueError:
            return text, {}


# ---------------------------------------------------------------- helpers

def est_tokens(chars):
    return math.ceil(chars / 4)


def norm_path(path):
    path = path.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def hit_at(ranked, expected, k, need_all=False):
    """1 if an expected path is among the first k ranked paths, else 0.

    need_all (multi_hop, callers): every expected path must be in the first k.
    """
    want = {norm_path(p) for p in expected}
    got = {norm_path(p) for p in ranked[:k]}
    return int(want <= got) if need_all else int(bool(want & got))


def rank_files(grep_output):
    """Paths from `grep -rn` output ordered by match count (desc), ties by path."""
    counts = {}
    for line in grep_output.splitlines():
        m = re.match(r"^(.+?):\d+:", line)
        if m:
            counts[norm_path(m.group(1))] = counts.get(norm_path(m.group(1)), 0) + 1
    return [p for p, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def load_questions(path=QUESTIONS, limit=None):
    with open(path, encoding="utf-8") as fh:
        questions = json.load(fh)["questions"]
    return questions[:limit] if limit else questions


# ---------------------------------------------------------------- the three script-mode methods

ALL_KINDS = ("multi_hop", "callers")  # hit@5 needs every expected path
KIND_ORDER = ["conceptual", "symbol", "doc", "multi_hop", "exact_text", "callers", "negative"]
METHODS = ("context", "old", "old_bounded")
METHOD_LABEL = {"context": "context (search_semantic + get_slice)",
                "old": "old (grep -n + Read whole top file)",
                "old_bounded": "old, bounded (file list capped 50 + Read +-40 lines)"}
BOUNDED_LIST_CAP = 50
BOUNDED_CONTEXT_LINES = 40


# Grep scope for the old way. `tracked` greps only git-tracked files (`git grep`), so ignored
# build output (dist, coverage, node_modules) never counts; `exclude_dirs` always apply.
GREP_SCOPE = {"tracked": False, "exclude_dirs": list(GREP_EXCLUDE_DIRS)}


def grep_run(flags, pattern, root):
    """Run grep (or git grep when GREP_SCOPE['tracked']); stdout text, same line format."""
    dirs, files = GREP_SCOPE["exclude_dirs"], GREP_EXCLUDE_FILES
    if GREP_SCOPE["tracked"]:
        cmd = ["git", "grep", "--no-color", flags.replace("r", "").replace("E", ""), "-E", pattern, "--", "."]
        cmd += [f":(exclude){d}" for d in dirs] + [f":(exclude,glob)**/{f}" for f in files]
        env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")  # never write to the target's .git
    else:
        cmd = ["grep", flags, pattern] + [f"--exclude-dir={d}" for d in dirs]
        cmd += [f"--exclude={f}" for f in files] + ["."]
        env = None
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, errors="replace", env=env).stdout


def old_way(question, root):
    """Grep then Read the top file in full. Returns dict(ranked, chars)."""
    out = grep_run("-rnIE", question["grep_pattern"], root)
    ranked = rank_files(out)
    chars = len(out)
    if ranked:
        try:
            with open(os.path.join(root, ranked[0]), encoding="utf-8", errors="replace") as fh:
                chars += len(fh.read())
        except OSError:
            pass
    return {"ranked": ranked, "chars": chars, "indexing": False}


def rank_counts(count_output):
    """`grep -rc` output (`path:count`) -> [(path, count)] for count > 0, by count desc, path."""
    counts = []
    for line in count_output.splitlines():
        m = re.match(r"^(.+):(\d+)$", line)
        if m and int(m.group(2)) > 0:
            counts.append((norm_path(m.group(1)), int(m.group(2))))
    return sorted(counts, key=lambda pc: (-pc[1], pc[0]))


def ranged_read(root, path, pattern, context=BOUNDED_CONTEXT_LINES):
    """Text of the lines within +-context of the first match of pattern in path."""
    done = subprocess.run(["grep", "-nIE", "-m1", pattern, path], cwd=root, capture_output=True,
                          text=True, errors="replace")
    m = re.match(r"^(\d+):", done.stdout)
    first = int(m.group(1)) if m else 1
    try:
        with open(os.path.join(root, path), encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return ""
    lo = max(0, first - 1 - context)
    return "\n".join(lines[lo:first + context])


def old_bounded(question, root):
    """How a careful agent works: file list ranked by match count (capped), ranged Read."""
    counts = rank_counts(grep_run("-rcIE", question["grep_pattern"], root))
    listing = "\n".join(f"{p}:{c}" for p, c in counts[:BOUNDED_LIST_CAP])
    chars = len(listing)
    if counts:
        chars += len(ranged_read(root, counts[0][0], question["grep_pattern"]))
    return {"ranked": [p for p, _ in counts], "chars": chars, "indexing": False}


def context_way(question, client):
    """search_semantic then get_slice of the top hit."""
    text, data = client.call("search_semantic", {"query": question["question"], "k": K})
    hits = data.get("hits", [])
    chars = len(text)
    if hits:
        slice_text, _ = client.call("get_slice", {"slice_id": hits[0]["id"]})
        chars += len(slice_text)
    return {"ranked": [h["path"] for h in hits], "chars": chars,
            "indexing": bool(data.get("indexing")),
            "top_score": hits[0].get("score") if hits else None}


def timed(fn, runs=TIMING_RUNS):
    """(median seconds, last result)."""
    times, result = [], None
    for _ in range(runs):
        start = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times), result


def score(q, outcome, seconds, method="old"):
    """Per-question, per-method row.

    Correctness: hit@1 = an expected file is ranked first; hit@5 = an expected file is in the
    first five (multi_hop / callers: ALL expected files are). negative questions expect
    nothing: a grep method is correct when it finds no file; the semantic search always
    returns hits, so its correctness is not scored here (None) - only agent mode grades it.
    """
    if q["kind"] == "negative":
        hit1 = hit5 = None if method == "context" else int(not outcome["ranked"])
    else:
        hit1 = hit_at(outcome["ranked"], q["expected_paths"], 1)
        hit5 = hit_at(outcome["ranked"], q["expected_paths"], 5, need_all=q["kind"] in ALL_KINDS)
    return {"id": q["id"], "seconds": seconds, "hit1": hit1, "hit5": hit5,
            "chars": outcome["chars"], "tokens": est_tokens(outcome["chars"]),
            "top": outcome["ranked"][0] if outcome["ranked"] else "(none)",
            "top_score": outcome.get("top_score"), "indexing": outcome["indexing"]}


def run_script_mode(questions, client, root):
    context_way(questions[0], client)  # warm-up, excluded
    rows = []
    for q in questions:
        row = {"q": q}
        c_sec, c_out = timed(lambda: context_way(q, client))
        row["context"] = score(q, c_out, c_sec, "context")
        o_sec, o_out = timed(lambda: old_way(q, root))
        row["old"] = score(q, o_out, o_sec, "old")
        b_sec, b_out = timed(lambda: old_bounded(q, root))
        row["old_bounded"] = score(q, b_out, b_sec, "old_bounded")
        rows.append(row)
    return rows


def _tally(scores):
    h1 = [s["hit1"] for s in scores if s["hit1"] is not None]
    h5 = [s["hit5"] for s in scores if s["hit5"] is not None]
    return {"n": len(h1), "hit1": sum(h1), "hit5": sum(h5)}


def summarize_script(rows):
    out = {}
    for m in METHODS:
        rs = [r[m] for r in rows if m in r]
        out[m] = dict(_tally(rs), median_s=med([r["seconds"] for r in rs]),
                      tokens=sum(r["tokens"] for r in rs))
    return out


def summarize_kinds(rows, methods=METHODS):
    """{kind: {method: {n, hit1, hit5}}} from script rows."""
    out = {}
    for kind in KIND_ORDER:
        rs = [r for r in rows if r["q"]["kind"] == kind]
        if rs:
            out[kind] = {m: _tally([r[m] for r in rs if m in r]) for m in methods}
    return out


# ---------------------------------------------------------------- real-agent mode

PER_RUN_BUDGET = 0.5   # --max-budget-usd for one `claude -p` run
SPEND_CAP = 12.0       # cumulative across R3 + R4
REPEAT_IDS = ["c02", "s03", "m01", "e02", "k04"]
REPEATS = 3
NOT_FOUND_RE = re.compile(r"not found", re.I)


class BudgetExceeded(Exception):
    pass


class Budget:
    """Cumulative spend across `claude -p` runs; persisted so a second batch continues it."""

    def __init__(self, cap=SPEND_CAP, path=None, per_run=PER_RUN_BUDGET):
        self.cap, self.path, self.per_run = cap, path, per_run
        self.spent, self.runs = 0.0, 0
        self._lock = threading.Lock()
        if path and os.path.exists(path):
            with open(path) as fh:
                saved = json.load(fh)
            self.spent, self.runs = saved.get("spent", 0.0), saved.get("runs", 0)

    def check(self):
        if self.spent + self.per_run > self.cap:
            raise BudgetExceeded(f"spend ${self.spent:.2f} + next run's cap ${self.per_run:.2f} "
                                 f"would pass the ${self.cap:.2f} cap")

    def add(self, cost):
        with self._lock:
            self.spent += cost
            self.runs += 1
            if self.path:
                with open(self.path, "w") as fh:
                    json.dump({"spent": self.spent, "runs": self.runs}, fh)


PROMPT_IGNORE = ("Ignore memory/event-trace/ and tasks/TASK_*_T171.md, tasks/TASK_*_T172.md: "
                 "they log this benchmark.")


def agent_prompt(question):
    return ("Find the file in this repository that best answers the question below. "
            "Do not edit anything. Reply with the repo-relative path(s) of the most "
            "relevant file(s), most relevant first, and one sentence why. If the repository has "
            "nothing that answers it, reply exactly NOT FOUND and name no file. " + PROMPT_IGNORE + "\n\n"
            f"Question: {question}")


def agent_command(method, root, url, persist=False, resume=None, fork=False):
    """`claude -p` argv for one method; the prompt goes in on stdin."""
    base = ["claude", "-p", "--output-format", "json"]
    if not persist:
        base.append("--no-session-persistence")
    base += ["--setting-sources", "user", "--disable-slash-commands", "--strict-mcp-config",
             "--max-budget-usd", str(PER_RUN_BUDGET)]
    if resume:
        base += ["--resume", resume] + (["--fork-session"] if fork else [])
    if method == "context":
        mcp = {"mcpServers": {"easy-context": {"type": "http", "url": url,
                                               "headers": {"X-Easy-Context-Root": root}}}}
        return base + ["--mcp-config", json.dumps(mcp), "--tools", "",
                       "--allowedTools", ",".join(CTX_TOOLS)]
    return base + ["--tools", ",".join(OLD_TOOLS), "--allowedTools", ",".join(OLD_TOOLS)]


def grade_answer(q, answer):
    """1 if the agent's answer is right for this question's kind, else 0.

    negative: the answer opens with NOT FOUND, as the prompt tells the agent to reply (later
    sentences may name files that were checked and rejected). multi_hop / callers: names
    every expected path. Others: names any expected path.
    """
    answer = answer or ""
    if q["kind"] == "negative":
        first = next((ln for ln in answer.splitlines() if ln.strip()), "")
        return int(bool(NOT_FOUND_RE.match(first.strip(" *_`#>-"))))
    named = [norm_path(p) in answer for p in q["expected_paths"]]
    return int(all(named) if q["kind"] in ALL_KINDS else any(named))


def parse_agent_json(stdout, expected):
    data = json.loads(stdout)
    usage = data.get("usage", {})
    n = lambda k: int(usage.get(k) or 0)  # noqa: E731
    answer = data.get("result", "") or ""
    return {"seconds": (data.get("duration_ms") or 0) / 1000,
            "input": n("input_tokens"), "output": n("output_tokens"),
            "cache_read": n("cache_read_input_tokens"), "cache_creation": n("cache_creation_input_tokens"),
            "tokens": n("input_tokens") + n("output_tokens") + n("cache_read_input_tokens")
                      + n("cache_creation_input_tokens"),
            "cost": float(data.get("total_cost_usd") or 0), "turns": data.get("num_turns"),
            "hit": int(any(norm_path(p) in answer for p in expected)),
            "error": bool(data.get("is_error")), "session_id": data.get("session_id"),
            "answer": answer[:600]}


def run_claude(q, method, root, url, budget, **cmd_kwargs):
    """One `claude -p` run, graded for question dict q; spend charged to budget."""
    budget.check()
    cmd = agent_command(method, root, url, **cmd_kwargs)
    prompt = q.get("prompt") or agent_prompt(q["question"])
    try:
        done = subprocess.run(cmd, input=prompt, cwd=root, capture_output=True, text=True,
                              timeout=900)
        row = parse_agent_json(done.stdout, q["expected_paths"])
    except (subprocess.SubprocessError, ValueError, OSError) as err:
        row = {"seconds": 0, "input": 0, "output": 0, "cache_read": 0, "cache_creation": 0,
               "tokens": 0, "cost": 0.0, "turns": None, "hit": 0, "error": True,
               "session_id": None, "answer": f"run failed: {err}"}
        print(f"  {q['id']} {method}: run failed: {err}", file=sys.stderr)
    row["correct"] = grade_answer(q, row["answer"]) if not row["error"] else 0
    budget.add(row["cost"])
    return row


def run_agent_mode(questions, root, url, budget, repeat_ids=REPEAT_IDS, repeats=REPEATS):
    """All questions once per method, then `repeats` more runs of the fixed repeat questions."""
    rows, rep, aborted = [], [], None
    try:
        for q in questions:
            print(f"  agent run {q['id']} (${budget.spent:.2f} spent)", file=sys.stderr)
            rows.append({"q": q, "context": run_claude(q, "context", root, url, budget),
                         "old": run_claude(q, "old", root, url, budget)})
        for q in [x for x in questions if x["id"] in repeat_ids]:
            for m in ("context", "old"):
                for i in range(repeats):
                    print(f"  repeat {q['id']} {m} #{i + 1} (${budget.spent:.2f} spent)", file=sys.stderr)
                    r = run_claude(q, m, root, url, budget)
                    r.update(id=q["id"], method=m)
                    rep.append(r)
    except BudgetExceeded as err:
        aborted = str(err)
        print(f"ABORT: {err}", file=sys.stderr)
    return {"rows": rows, "repeats": rep, "aborted": aborted}


def summarize_agent(rows):
    out = {}
    for m in ("context", "old"):
        rs = [r[m] for r in rows]
        out[m] = {"n": len(rs), "correct": sum(r["correct"] for r in rs),
                  "median_s": med([r["seconds"] for r in rs]),
                  "tokens": sum(r["tokens"] for r in rs), "cost": sum(r["cost"] for r in rs)}
    return out


def agent_per_kind(rows):
    out = {}
    for kind in KIND_ORDER:
        rs = [r for r in rows if r["q"]["kind"] == kind]
        if rs:
            out[kind] = {m: {"n": len(rs), "correct": sum(r[m]["correct"] for r in rs),
                             "tokens": sum(r[m]["tokens"] for r in rs),
                             "cost": sum(r[m]["cost"] for r in rs)} for m in ("context", "old")}
    return out


def spread(repeats):
    """{qid: {method: {metric: [min, median, max]}}} over the repeat runs."""
    out = {}
    for r in repeats:
        out.setdefault(r["id"], {}).setdefault(r["method"], []).append(r)
    for qid, by_m in out.items():
        for m, rs in by_m.items():
            by_m[m] = {k: [min(x[k] for x in rs), statistics.median(x[k] for x in rs),
                           max(x[k] for x in rs)] for k in ("tokens", "cost", "seconds")}
            by_m[m]["correct"] = [sum(x["correct"] for x in rs), len(rs)]
    return out


# ---------------------------------------------------------------- lifecycle (R4)

LIFECYCLE_WAIT_S = 372        # just over the 5-minute prompt-cache time-to-live
LIFECYCLE_LONG_WAIT_S = 3720  # just over the 1-hour cache tier; first chain only


def lifecycle_chains(path=QUESTIONS):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("lifecycle_chains", [])


def run_chain(method, chain, root, url, budget, waits=(LIFECYCLE_WAIT_S,), sleep=time.sleep,
              clock=time.monotonic):
    """Q1, then Q2 three ways: same session, fresh session, resumed after each wait."""
    steps = []

    def step(label, text, expected, **kw):
        q = {"id": f"{chain['id']}:{label}", "kind": "lifecycle", "question": text,
             "expected_paths": expected}
        row = run_claude(q, method, root, url, budget, **kw)
        row.update(chain=chain["id"], method=method, label=label)
        steps.append(row)
        return row

    first = step("q1", chain["q1"], chain["q1_expected"], persist=True)
    t0 = clock()
    sid = first["session_id"]
    if not sid:
        return steps
    step("same_session", chain["q2_followup"], chain["q2_expected"], persist=True, resume=sid, fork=True)
    step("fresh", chain["q2_standalone"], chain["q2_expected"])
    for wait in waits:
        sleep(max(0, wait - (clock() - t0)))
        step(f"resume_after_{wait}s", chain["q2_followup"], chain["q2_expected"],
             persist=True, resume=sid, fork=True)
    return steps


def run_lifecycle(chains, root, url, budget, expiry_waits=True):
    jobs = [(m, c, (((LIFECYCLE_WAIT_S, LIFECYCLE_LONG_WAIT_S) if i == 0 else (LIFECYCLE_WAIT_S,))
                    if expiry_waits else ()))
            for i, c in enumerate(chains) for m in ("context", "old")]
    steps, aborted = [], None
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futs = [pool.submit(run_chain, m, c, root, url, budget, w) for m, c, w in jobs]
        for fut in futs:
            try:
                steps += fut.result()
            except BudgetExceeded as err:
                aborted = str(err)
    return {"steps": steps, "aborted": aborted}


def summarize_lifecycle(steps):
    """{label: {method: mean of each metric over chains, n, correct}}."""
    out = {}
    for s in steps:
        out.setdefault(s["label"], {}).setdefault(s["method"], []).append(s)
    for label, by_m in out.items():
        for m, rs in by_m.items():
            by_m[m] = dict({k: statistics.mean(r[k] for r in rs) for k in
                            ("input", "output", "cache_read", "cache_creation", "cost", "seconds")},
                           n=len(rs), correct=sum(r["correct"] for r in rs))
    return out


# ---------------------------------------------------------------- index upkeep (R5)

def wait_index(client, job, timeout=1800, poll=0.2):
    """Poll list_indexes until this job is done or failed; returns the index entry."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _, data = client.call("list_indexes", {})
        for entry in data.get("indexes", []):
            if entry.get("project_id") == job.get("project_id") and entry.get("job_id") == job.get("job_id") \
                    and entry.get("status") in ("done", "failed"):
                return entry
        time.sleep(poll)
    raise ServerError("index job did not finish in time")


def reindex(client, force=False):
    """(seconds, entry) for one index_path run over the whole root."""
    start = time.perf_counter()
    _, job = client.call("index_path", {"path": ".", "force": force})
    entry = wait_index(client, job)
    return time.perf_counter() - start, entry


def search_has(client, query, needle, path_hint=None):
    """Does any hit for query contain needle in its text?"""
    _, data = client.call("search_semantic", {"query": query, "k": K})
    return any(needle in h.get("text", "") and (path_hint is None or h.get("path") == path_hint)
               for h in data.get("hits", []))


def tracked_files(root, n):
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=root, capture_output=True, text=True).stdout
    return out.split()[:n]


def git_dirty(root):
    return subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True,
                          text=True).stdout.splitlines()


def run_upkeep(client, root, probe_name="zz_staleness_probe.md", probe=True):
    """Time full and no-op re-index; with probe=True also touch files and probe staleness.

    probe=False never writes to the root (not even an mtime): timing of the index only.
    """
    before = git_dirty(root)
    result = {}
    result["full_reindex_s"], entry = reindex(client, force=True)
    result["files"], result["slices"] = entry.get("files"), entry.get("slices")
    result["noop_reindex_s"], _ = reindex(client)
    if not probe:
        result["git_status_unchanged"] = git_dirty(root) == before
        return result
    for n in (1, 10):
        for f in tracked_files(root, n):
            os.utime(os.path.join(root, f))  # touch: mtime only, content unchanged
        result[f"touch_{n}_reindex_s"], _ = reindex(client)
    probe = os.path.join(root, probe_name)
    token_a, token_b = "zzprobealpha4417", "zzprobebeta9082"
    stale = {}
    try:
        with open(probe, "w") as fh:
            fh.write(f"# Staleness probe\n\nThe sentinel word is {token_a}.\n")
        result["add_1_new_file_reindex_s"], _ = reindex(client)
        stale["new_file_found"] = search_has(client, f"sentinel word {token_a}", token_a, probe_name)
        with open(probe, "w") as fh:
            fh.write(f"# Staleness probe\n\nThe sentinel word is {token_b}.\n")
        stale["after_edit_old_text_still_returned"] = search_has(client, f"sentinel word {token_a}", token_a, probe_name)
        stale["after_edit_new_text_found"] = search_has(client, f"sentinel word {token_b}", token_b, probe_name)
        reindex(client)
        stale["after_reindex_new_text_found"] = search_has(client, f"sentinel word {token_b}", token_b, probe_name)
        os.remove(probe)
        stale["after_delete_before_reindex_still_returned"] = search_has(client, f"sentinel word {token_b}", token_b, probe_name)
        reindex(client)
        stale["after_delete_and_reindex_still_returned"] = search_has(client, f"sentinel word {token_b}", token_b, probe_name)
    finally:
        if os.path.exists(probe):
            os.remove(probe)
    result["staleness"] = stale
    result["git_status_unchanged"] = git_dirty(root) == before
    return result


def regrade(data):
    """Recompute `correct` and the agent summaries from the stored answers (no new runs)."""
    agent = data.get("agent")
    if not agent:
        return data
    for r in agent["rows"]:
        for m in ("context", "old"):
            if not r[m]["error"]:
                r[m]["correct"] = grade_answer(r["q"], r[m]["answer"])
    kinds = {r["q"]["id"]: r["q"] for r in agent["rows"]}
    for r in agent.get("repeats", []):
        r["correct"] = 0 if r["error"] else grade_answer(kinds[r["id"]], r["answer"])
    agent["summary"] = summarize_agent(agent["rows"])
    agent["per_kind"] = agent_per_kind(agent["rows"])
    agent["spread"] = spread(agent.get("repeats", []))
    return data


# ---------------------------------------------------------------- report

def med(values):
    values = list(values)
    return statistics.median(values) if values else 0


def _ratio(a, b):
    return f"{b / a:.1f}x" if a else "n/a"


def _pct(k, n):
    return f"{k}/{n}" if n else "n/a"


def render_script(data):
    rows, summary, kinds = data["rows"], data["summary"], data["per_kind"]
    lines = ["| id | kind | ctx s | old s | bnd s | ctx h1 | old h1 | bnd h1 | ctx h5 | old h5 | bnd h5 | ctx tok | old tok | bnd tok |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    show = lambda v: "n/a" if v is None else v  # noqa: E731
    for r in rows:
        c, o, d = r["context"], r["old"], r["old_bounded"]
        lines.append(f"| {r['q']['id']} | {r['q']['kind']} | {c['seconds']:.3f} | {o['seconds']:.3f} | {d['seconds']:.3f} | "
                     f"{show(c['hit1'])} | {show(o['hit1'])} | {show(d['hit1'])} | {show(c['hit5'])} | {show(o['hit5'])} | "
                     f"{show(d['hit5'])} | {c['tokens']} | {o['tokens']} | {d['tokens']} |")
    lines += ["", "Tokens are estimated (chars / 4). h1 / h5 = hit@1 / hit@5. n/a = not scored "
              "(semantic search on a negative question always returns hits; agent mode grades it).",
              "", "| method | median time (s) | hit@1 | hit@5 | total tokens (est) |", "|---|---|---|---|---|"]
    for m in METHODS:
        s = summary[m]
        lines.append(f"| {METHOD_LABEL[m]} | {s['median_s']:.3f} | {_pct(s['hit1'], s['n'])} | "
                     f"{_pct(s['hit5'], s['n'])} | {s['tokens']} |")
    lines += ["", "**Accuracy per question kind (script mode, hit@1 / hit@5)**", "",
              "| kind | n | context | old | old, bounded |", "|---|---|---|---|---|"]
    for kind, by_m in kinds.items():
        cells = " | ".join(f"{by_m[m]['hit1']}/{by_m[m]['n']} , {by_m[m]['hit5']}/{by_m[m]['n']}" if by_m[m]["n"]
                           else "n/a" for m in METHODS)
        lines.append(f"| {kind} | {sum(1 for r in rows if r['q']['kind'] == kind)} | {cells} |")
    return "\n".join(lines)


def render_agent(data):
    rows, summary = data["rows"], data["summary"]
    lines = ["| id | kind | ctx s | old s | ctx tokens | old tokens | ctx $ | old $ | ctx ok | old ok |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c, o = r["context"], r["old"]
        lines.append(f"| {r['q']['id']} | {r['q']['kind']} | {c['seconds']:.1f} | {o['seconds']:.1f} | {c['tokens']} | "
                     f"{o['tokens']} | {c['cost']:.4f} | {o['cost']:.4f} | {c['correct']} | {o['correct']} |")
    lines += ["", "| method | median time (s) | correct | total tokens (real) | total cost (USD) |", "|---|---|---|---|---|"]
    for name, m in (("context agent (easy-context tools only)", "context"), ("old agent (Grep, Glob, Read only)", "old")):
        s = summary[m]
        lines.append(f"| {name} | {s['median_s']:.1f} | {s['correct']}/{s['n']} | {s['tokens']} | {s['cost']:.3f} |")
    lines += ["", "**Correctness and cost per question kind (real agents)**", "",
              "| kind | n | ctx correct | old correct | ctx tokens | old tokens | ctx $ | old $ |", "|---|---|---|---|---|---|---|---|"]
    for kind, by_m in data["per_kind"].items():
        c, o = by_m["context"], by_m["old"]
        lines.append(f"| {kind} | {c['n']} | {c['correct']}/{c['n']} | {o['correct']}/{o['n']} | {c['tokens']} | "
                     f"{o['tokens']} | {c['cost']:.3f} | {o['cost']:.3f} |")
    if data.get("spread"):
        lines += ["", f"**Run-to-run spread ({REPEATS} repeats per method; min / median / max)**", "",
                  "| question | method | tokens | cost (USD) | time (s) | correct |", "|---|---|---|---|---|---|"]
        for qid, by_m in data["spread"].items():
            for m in ("context", "old"):
                s = by_m.get(m)
                if s:
                    lines.append(f"| {qid} | {m} | {' / '.join(f'{v:.0f}' for v in s['tokens'])} | "
                                 f"{' / '.join(f'{v:.3f}' for v in s['cost'])} | "
                                 f"{' / '.join(f'{v:.1f}' for v in s['seconds'])} | {s['correct'][0]}/{s['correct'][1]} |")
    if data.get("aborted"):
        lines += ["", f"**Aborted:** {data['aborted']}"]
    return "\n".join(lines)


def render_lifecycle(data):
    summ = data["summary"]
    order = ["q1", "same_session", "fresh"] + sorted(k for k in summ if k.startswith("resume_after"))
    names = {"q1": "Q1 (cold start, new session)", "same_session": "Q2 same session (resume right away)",
             "fresh": "Q2 closed + fresh session (re-find)"}
    lines = ["Mean per step over the chains. `cache_read` = prompt tokens re-read from cache; "
             "`cache_creation` = prompt tokens written to cache (reload cost).", "",
             "| step | method | n | correct | input | output | cache_read | cache_creation | cost (USD) | time (s) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for label in order:
        for m in ("context", "old"):
            s = summ.get(label, {}).get(m)
            if s:
                lines.append(f"| {names.get(label, 'Q2 resumed after ' + label.split('_')[-1] + ' wait')} | {m} | {s['n']} | "
                             f"{s['correct']}/{s['n']} | {s['input']:.0f} | {s['output']:.0f} | {s['cache_read']:.0f} | "
                             f"{s['cache_creation']:.0f} | {s['cost']:.4f} | {s['seconds']:.1f} |")
    if data.get("aborted"):
        lines += ["", f"**Aborted:** {data['aborted']}"]
    return "\n".join(lines)


def render_upkeep(u):
    lines = ["| operation | seconds |", "|---|---|",
             f"| full re-index (force, {u.get('files')} files / {u.get('slices')} slices) | {u['full_reindex_s']:.2f} |",
             f"| re-index, nothing changed | {u['noop_reindex_s']:.2f} |"]
    if "touch_1_reindex_s" in u:
        lines += [f"| re-index after touching 1 file (mtime only) | {u['touch_1_reindex_s']:.2f} |",
                  f"| re-index after touching 10 files (mtime only) | {u['touch_10_reindex_s']:.2f} |",
                  f"| re-index after adding 1 new file | {u.get('add_1_new_file_reindex_s', 0):.2f} |", "",
                  "Touching changes only the file's mtime, so the index skips the unchanged content: "
                  "those rows show the cost of the scan alone.", ""]
    else:
        lines += ["", "Timing only: no file was touched or added in the target (read-only run), so there is no "
                  "incremental or staleness measurement here.", ""]
    st = u.get("staleness")
    if st:
        lines += ["**Staleness probe** (a new untracked file is indexed, edited, searched before re-index, then removed):", ""]
        labels = {"new_file_found": "new file found by search after indexing",
                  "after_edit_old_text_still_returned": "after edit, before re-index: search still returns the OLD text",
                  "after_edit_new_text_found": "after edit, before re-index: search finds the NEW text",
                  "after_reindex_new_text_found": "after re-index: search finds the new text",
                  "after_delete_before_reindex_still_returned": "after delete, before re-index: deleted file still returned",
                  "after_delete_and_reindex_still_returned": "after delete and re-index: deleted file still returned"}
        lines += [f"- {labels[k]}: **{'yes' if st[k] else 'no'}**" for k in labels if k in st]
        lines.append("")
    lines.append(f"Target `git status` unchanged afterwards: **{'yes' if u['git_status_unchanged'] else 'NO'}**.")
    return "\n".join(lines)


def recommendation(data):
    """Recommendation paragraph built only from numbers present in data."""
    parts = []
    s = data.get("script")
    if s:
        sm = s["summary"]
        c, o, d = sm["context"], sm["old"], sm["old_bounded"]
        parts.append(
            f"On {sm['context']['n'] + 0} scored questions in script mode, the context way hit@5 {c['hit5']}/{c['n']} "
            f"against {o['hit5']}/{o['n']} (grep + whole-file Read) and {d['hit5']}/{d['n']} (bounded grep + ranged Read). "
            f"Estimated tokens: {c['tokens']} vs {o['tokens']} vs {d['tokens']}; median time "
            f"{c['median_s']:.3f}s vs {o['median_s']:.3f}s vs {d['median_s']:.3f}s.")
    a = data.get("agent")
    if a:
        am = a["summary"]
        c, o = am["context"], am["old"]
        parts.append(
            f"With real agents the context agent was right {c['correct']}/{c['n']} times and the grep+Read agent "
            f"{o['correct']}/{o['n']}; total tokens {c['tokens']} vs {o['tokens']}, cost ${c['cost']:.2f} vs ${o['cost']:.2f}, "
            f"median time {c['median_s']:.1f}s vs {o['median_s']:.1f}s.")
        wins = [k for k, v in a["per_kind"].items() if v["context"]["correct"] > v["old"]["correct"]]
        loses = [k for k, v in a["per_kind"].items() if v["context"]["correct"] < v["old"]["correct"]]
        if wins:
            parts.append("Context search was more accurate on: " + ", ".join(wins) + ".")
        if loses:
            parts.append("Grep + Read was more accurate on: " + ", ".join(loses) + ".")
    u = data.get("upkeep")
    if u and "staleness" not in u:
        parts.append(f"Upkeep: a full re-index takes {u['full_reindex_s']:.1f}s and a no-op one {u['noop_reindex_s']:.1f}s.")
    elif u:
        st = u["staleness"]
        stale = ("search returned the old text until the file was re-indexed"
                 if st.get("after_edit_old_text_still_returned") and not st.get("after_edit_new_text_found")
                 else "search saw the edit before a re-index")
        parts.append(f"Upkeep: a full re-index takes {u['full_reindex_s']:.1f}s and an incremental one "
                     f"{u['touch_10_reindex_s']:.1f}s for 10 touched files; after an edit, {stale}.")
    if a:
        cheaper = [k for k, v in a["per_kind"].items()
                   if v["context"]["tokens"] < v["old"]["tokens"] and v["context"]["correct"] >= v["old"]["correct"]]
        rest = [k for k in a["per_kind"] if k not in cheaper]
        am = a["summary"]
        c, o = am["context"], am["old"]
        if o["cost"] <= c["cost"]:
            lead = (f"Recommendation: use Grep/Glob/Read by default, with ranged reads: it cost ${o['cost']:.2f} against "
                    f"${c['cost']:.2f} and was right {o['correct']}/{o['n']} times against {c['correct']}/{c['n']}.")
        else:
            lead = (f"Recommendation: use context search by default: it cost ${c['cost']:.2f} against ${o['cost']:.2f} "
                    f"and was right {c['correct']}/{c['n']} times against {o['correct']}/{o['n']}.")
        parts.append(
            lead + " Reach for context search first when you have no keyword to grep - a natural-language "
            f"question about intent or a decision. By real-agent tokens, context search was cheaper and at least "
            f"as accurate on: {', '.join(cheaper) or 'no question kind'}; "
            f"grep + Read was cheaper or more accurate on: {', '.join(rest) or 'no question kind'}.")
    life = data.get("lifecycle")
    if life:
        sm = life["summary"]
        get = lambda label, m: sm.get(label, {}).get(m)  # noqa: E731
        bits = []
        for m in ("context", "old"):
            same, fresh = get("same_session", m), get("fresh", m)
            if same and fresh:
                bits.append(f"{m}: Q2 cost ${same['cost']:.3f} resumed in the same session vs ${fresh['cost']:.3f} "
                            f"in a closed + fresh one (cache_creation {same['cache_creation']:.0f} vs {fresh['cache_creation']:.0f} tokens)")
        if bits:
            tail = "."
            if any(k.startswith("resume_after") for k in sm):
                tail = (". A resume after the 5-minute cache window still read most of its prompt from cache, so the "
                        "cache did not visibly expire; parallel chains share one prompt prefix and keep it warm, "
                        "which this test cannot separate from expiry.")
            parts.append("Session lifecycle: " + "; ".join(bits) + tail)
    return " ".join(parts)


def render_comparison(name_a, a, name_b, b):
    """Side-by-side of two benchmark JSON datasets (documents-heavy repo vs code-heavy repo)."""
    def script(d, m):
        return d["script"]["summary"][m]

    def agent(d, m):
        return d["agent"]["summary"][m]

    lines = [f"| measure | {name_a} | {name_b} |", "|---|---|---|"]
    if "script" in a and "script" in b:
        for m in METHODS:
            sa, sb = script(a, m), script(b, m)
            lines.append(f"| script hit@5, {m} | {sa['hit5']}/{sa['n']} | {sb['hit5']}/{sb['n']} |")
        for m in METHODS:
            lines.append(f"| script est. tokens, {m} | {script(a, m)['tokens']} | {script(b, m)['tokens']} |")
    if "agent" in a and "agent" in b:
        for m in ("context", "old"):
            sa, sb = agent(a, m), agent(b, m)
            lines.append(f"| agent correct, {m} | {sa['correct']}/{sa['n']} | {sb['correct']}/{sb['n']} |")
            lines.append(f"| agent tokens, {m} | {sa['tokens']} | {sb['tokens']} |")
            lines.append(f"| agent cost USD, {m} | {sa['cost']:.2f} | {sb['cost']:.2f} |")
        ra = agent(a, "context")["cost"] / max(agent(a, "old")["cost"], 1e-9)
        rb = agent(b, "context")["cost"] / max(agent(b, "old")["cost"], 1e-9)
        lines.append(f"| agent cost ratio context / old | {ra:.2f}x | {rb:.2f}x |")
    if "upkeep" in a and "upkeep" in b:
        lines.append(f"| full re-index (s) | {a['upkeep']['full_reindex_s']:.1f} ({a['upkeep'].get('files')} files) | "
                     f"{b['upkeep']['full_reindex_s']:.1f} ({b['upkeep'].get('files')} files) |")
    return "\n".join(lines)


def build_markdown(data, compare=None):
    out = [f"# easy-context search vs grep + Read: benchmark (T171, {data.get('date', '')})", ""]
    if data.get("recommendation_text"):
        out += ["## Recommendation", "", data["recommendation_text"], ""]
    if data.get("spend"):
        out += [f"Real-agent spend this round: **${data['spend']['spent']:.2f}** over {data['spend']['runs']} `claude -p` runs "
                f"(cap ${data['spend'].get('cap', SPEND_CAP):.0f}).", ""]
    if "script" in data:
        out += ["## Script mode", "", render_script(data["script"]), ""]
    if "agent" in data:
        out += ["## Real-agent mode (claude -p)", "", render_agent(data["agent"]), ""]
    if "lifecycle" in data:
        out += ["## Session lifecycle: same session, resume after cache expiry, closed + fresh", "",
                render_lifecycle(data["lifecycle"]), ""]
    if "upkeep" in data:
        out += ["## Index upkeep and staleness", "", render_upkeep(data["upkeep"]), ""]
    if data.get("grep_scope"):
        out += ["## Grep scope used for the old way", "", data["grep_scope"], ""]
    if compare:
        out += ["## This repo vs tapchat-apis", "", render_comparison(*compare), ""]
    return "\n".join(out)


def report_paths(today=None, label=""):
    today = today or datetime.date.today().isoformat()
    base = os.path.join(ROOT, "reports", f"context-search-benchmark-{label + '-' if label else ''}{today}")
    return base + ".md", base + ".json"


def load_data(json_path):
    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_data(data, md_path, json_path, compare=None):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    data["recommendation_text"] = recommendation(data)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(build_markdown(data, compare))


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--root", default=DEFAULT_ROOT, help="indexed repo root (sent as X-Easy-Context-Root)")
    ap.add_argument("--agent", action="store_true", help="real-agent mode: all questions + repeats (claude -p; costs tokens)")
    ap.add_argument("--lifecycle", action="store_true", help="session lifecycle scenario (claude -p; costs tokens; ~1 hour)")
    ap.add_argument("--upkeep", action="store_true", help="index upkeep and staleness probe (re-indexes the root)")
    ap.add_argument("--questions", default=QUESTIONS, help="question file (default: this repo's fixture)")
    ap.add_argument("--label", default="", help="report name label, e.g. tapchat")
    ap.add_argument("--grep-tracked", action="store_true", help="old way greps only git-tracked files (git grep)")
    ap.add_argument("--grep-exclude-dir", action="append", default=[], help="extra directory the old way skips (repeatable)")
    ap.add_argument("--prompt-ignore", default=None, help="sentence telling agents which paths to ignore")
    ap.add_argument("--no-probe", action="store_true", help="--upkeep: timing only; write nothing in the root")
    ap.add_argument("--no-expiry-wait", action="store_true", help="--lifecycle: skip the cache-expiry waits")
    ap.add_argument("--compare-with", default=None, help="JSON of another run; adds a comparison section")
    ap.add_argument("--regrade", action="store_true", help="re-grade stored agent answers and rebuild the report (free)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions")
    ap.add_argument("--repeats", type=int, default=REPEATS, help="repeat runs per fixed question and method")
    ap.add_argument("--cap", type=float, default=SPEND_CAP, help="abort when cumulative real-agent cost would pass this (USD)")
    ap.add_argument("--yes", action="store_true", help="do not ask before real-agent runs")
    ap.add_argument("--report", default=None, help="markdown report file (the JSON sits beside it)")
    args = ap.parse_args(argv)
    md_path, json_path = report_paths(label=args.label)
    GREP_SCOPE["tracked"] = args.grep_tracked
    GREP_SCOPE["exclude_dirs"] = list(GREP_EXCLUDE_DIRS) + args.grep_exclude_dir
    global PROMPT_IGNORE
    if args.prompt_ignore is not None:
        PROMPT_IGNORE = args.prompt_ignore
    if args.report:
        md_path = args.report
        json_path = os.path.splitext(args.report)[0] + ".json"
    questions = load_questions(args.questions, limit=args.limit)
    data = load_data(json_path)
    data["grep_scope"] = (("`git grep` over git-tracked files only" if args.grep_tracked else "`grep -r` over the working tree")
                          + "; skipped directories: " + ", ".join(GREP_SCOPE["exclude_dirs"]) + ".")
    compare = None
    if args.compare_with:
        with open(args.compare_with, encoding="utf-8") as fh:
            compare = ("this repo (Markdown-heavy)", json.load(fh), "tapchat-apis (code-heavy)", data)
    data["date"] = datetime.date.today().isoformat()
    budget = Budget(args.cap, os.path.splitext(json_path)[0] + ".spend.json")

    if args.regrade:
        save_data(regrade(data), md_path, json_path, compare)
        print(f"Regraded. Report: {md_path}")
        return 0

    if args.agent or args.lifecycle:
        if not shutil.which("claude"):
            print("claude CLI not found on PATH (needed for --agent / --lifecycle)", file=sys.stderr)
            return 2
        runs = 2 * len(questions) + (2 * args.repeats * len(REPEAT_IDS) if args.agent else 0)
        if args.lifecycle:
            runs = 2 * 4 * len(lifecycle_chains(args.questions))
        print(f"Real-agent mode: about {runs} `claude -p` runs; cap ${args.cap:.2f} "
              f"(already spent ${budget.spent:.2f}).")
        if not args.yes and input("Continue? [y/N] ").strip().lower() != "y":
            print("Cancelled.")
            return 0
        if args.agent:
            res = run_agent_mode(questions, args.root, args.url, budget, repeats=args.repeats)
            data["agent"] = {"rows": res["rows"], "summary": summarize_agent(res["rows"]),
                             "per_kind": agent_per_kind(res["rows"]), "spread": spread(res["repeats"]),
                             "repeats": res["repeats"], "aborted": res["aborted"]}
        if args.lifecycle:
            res = run_lifecycle(lifecycle_chains(args.questions), args.root, args.url, budget, not args.no_expiry_wait)
            data["lifecycle"] = {"steps": res["steps"], "summary": summarize_lifecycle(res["steps"]),
                                 "aborted": res["aborted"]}
        data["spend"] = {"spent": budget.spent, "runs": budget.runs, "cap": args.cap}
        save_data(data, md_path, json_path, compare)
        print(f"Spent ${budget.spent:.2f} over {budget.runs} runs. Report: {md_path}\nJSON: {json_path}")
        return 0

    client = McpClient(args.url, args.root)
    try:
        client.start()
        if args.upkeep:
            data["upkeep"] = run_upkeep(client, args.root, probe=not args.no_probe)
        else:
            rows = run_script_mode(questions, client, args.root)
            data["script"] = {"rows": rows, "summary": summarize_script(rows), "per_kind": summarize_kinds(rows),
                              "indexing_note": any(r["context"]["indexing"] for r in rows)}
    except ServerError as err:
        print(str(err), file=sys.stderr)
        return 2
    save_data(data, md_path, json_path, compare)
    print(f"Report: {md_path}\nJSON: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
