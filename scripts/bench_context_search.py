#!/usr/bin/env python3
"""Benchmark easy-context search against the old way (grep + Read) (T171).

    python3 scripts/bench_context_search.py                       # script mode (free, repeatable)
    python3 scripts/bench_context_search.py --agent --limit 5     # real-agent mode (costs tokens)

Question: to find code or evidence in this repo, is the easy-context MCP search faster,
more correct and cheaper in tokens than Grep/Glob + Read?

Definitions (the two methods, per question):
  Old way      `grep -rnIE <grep_pattern>` over the root (skips .git, __pycache__,
               node_modules, .pytest_cache and the benchmark's own artifacts), files ranked
               by match count (ties by path), then the top-ranked file is read in full.
               Text returned = the grep output + that file.
  Context way  `search_semantic(question, k=5)`, then `get_slice` of the top hit.
               Text returned = both tool results.
  Time         wall-clock seconds for the whole two-step flow; script mode reports the median
               of 3 runs. One warm-up call is made first and excluded.
  Correctness  hit@1 / hit@5: an `expected_paths` file is the first / one of the first five
               ranked files (grep: files by match count; context: hits in score order).
  Tokens       script mode: characters / 4, labeled "estimated". Real-agent mode: the
               `usage` of `claude -p --output-format json` (input + output + cache).

Real-agent mode runs `claude -p` twice per question (easy-context tools only, then
Grep/Glob/Read only). It is manual only, asks to confirm unless --yes, and allows no
tool that edits files.

Exit codes: 0 ok, 2 bad setup (server unreachable, `claude` missing, bad arguments).
"""
import argparse
import datetime
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
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
GREP_EXCLUDE_DIRS = [".git", "__pycache__", "node_modules", ".pytest_cache"]
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


def hit_at(ranked, expected, k):
    """1 if any expected path is among the first k ranked paths, else 0."""
    want = {norm_path(p) for p in expected}
    return int(any(norm_path(p) in want for p in ranked[:k]))


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


# ---------------------------------------------------------------- the two methods

def old_way(question, root):
    """Grep then Read the top file. Returns dict(ranked, chars)."""
    cmd = ["grep", "-rnIE", question["grep_pattern"]]
    cmd += [f"--exclude-dir={d}" for d in GREP_EXCLUDE_DIRS]
    cmd += [f"--exclude={f}" for f in GREP_EXCLUDE_FILES]
    cmd += ["."]
    done = subprocess.run(cmd, cwd=root, capture_output=True, text=True, errors="replace")
    ranked = rank_files(done.stdout)
    chars = len(done.stdout)
    if ranked:
        try:
            with open(os.path.join(root, ranked[0]), encoding="utf-8", errors="replace") as fh:
                chars += len(fh.read())
        except OSError:
            pass
    return {"ranked": ranked, "chars": chars, "indexing": False}


def context_way(question, client):
    """search_semantic then get_slice of the top hit."""
    text, data = client.call("search_semantic", {"query": question["question"], "k": K})
    hits = data.get("hits", [])
    chars = len(text)
    if hits:
        slice_text, _ = client.call("get_slice", {"slice_id": hits[0]["id"]})
        chars += len(slice_text)
    return {"ranked": [h["path"] for h in hits], "chars": chars,
            "indexing": bool(data.get("indexing"))}


def timed(fn, runs=TIMING_RUNS):
    """(median seconds, last result)."""
    times, result = [], None
    for _ in range(runs):
        start = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times), result


def score(q, outcome, seconds):
    return {"id": q["id"], "seconds": seconds,
            "hit1": hit_at(outcome["ranked"], q["expected_paths"], 1),
            "hit5": hit_at(outcome["ranked"], q["expected_paths"], 5),
            "chars": outcome["chars"], "tokens": est_tokens(outcome["chars"]),
            "top": outcome["ranked"][0] if outcome["ranked"] else "(none)",
            "indexing": outcome["indexing"]}


def run_script_mode(questions, client, root):
    context_way(questions[0], client)  # warm-up, excluded
    rows = []
    for q in questions:
        c_sec, c_out = timed(lambda: context_way(q, client))
        o_sec, o_out = timed(lambda: old_way(q, root))
        rows.append({"q": q, "context": score(q, c_out, c_sec), "old": score(q, o_out, o_sec)})
    return rows


# ---------------------------------------------------------------- real-agent mode

def agent_prompt(question):
    return ("Find the file in this repository that best answers the question below. "
            "Do not edit anything. Reply with the repo-relative path(s) of the most "
            f"relevant file(s), most relevant first, and one sentence why.\n\nQuestion: {question}")


def agent_command(method, root, url):
    """`claude -p` argv for one method; the prompt goes in on stdin."""
    base = ["claude", "-p", "--output-format", "json", "--no-session-persistence",
            "--setting-sources", "user", "--disable-slash-commands", "--strict-mcp-config",
            "--max-budget-usd", "1.5"]
    if method == "context":
        mcp = {"mcpServers": {"easy-context": {"type": "http", "url": url,
                                               "headers": {"X-Easy-Context-Root": root}}}}
        return base + ["--mcp-config", json.dumps(mcp), "--tools", "",
                       "--allowedTools", ",".join(CTX_TOOLS)]
    return base + ["--tools", ",".join(OLD_TOOLS), "--allowedTools", ",".join(OLD_TOOLS)]


def parse_agent_json(stdout, expected):
    data = json.loads(stdout)
    usage = data.get("usage", {})
    tokens = sum(int(usage.get(k) or 0) for k in (
        "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    answer = data.get("result", "") or ""
    return {"seconds": (data.get("duration_ms") or 0) / 1000, "tokens": tokens,
            "cost": float(data.get("total_cost_usd") or 0), "turns": data.get("num_turns"),
            "hit": int(any(norm_path(p) in answer for p in expected)),
            "error": bool(data.get("is_error"))}


def run_agent_once(method, q, root, url):
    cmd = agent_command(method, root, url)
    try:
        done = subprocess.run(cmd, input=agent_prompt(q["question"]), cwd=root,
                              capture_output=True, text=True, timeout=600)
        row = parse_agent_json(done.stdout, q["expected_paths"])
    except (subprocess.SubprocessError, ValueError, OSError) as err:
        row = {"seconds": 0, "tokens": 0, "cost": 0.0, "turns": None, "hit": 0, "error": True}
        print(f"  {q['id']} {method}: run failed: {err}", file=sys.stderr)
    return row


def run_agent_mode(questions, root, url):
    rows = []
    for q in questions:
        print(f"  agent run {q['id']} ...", file=sys.stderr)
        rows.append({"q": q, "context": run_agent_once("context", q, root, url),
                     "old": run_agent_once("old", q, root, url)})
    return rows


# ---------------------------------------------------------------- report

def med(values):
    return statistics.median(values) if values else 0


def summarize_script(rows):
    out = {}
    for m in ("context", "old"):
        rs = [r[m] for r in rows]
        out[m] = {"median_s": med([r["seconds"] for r in rs]),
                  "hit1": sum(r["hit1"] for r in rs), "hit5": sum(r["hit5"] for r in rs),
                  "tokens": sum(r["tokens"] for r in rs), "n": len(rs)}
    return out


def summarize_agent(rows):
    out = {}
    for m in ("context", "old"):
        rs = [r[m] for r in rows]
        out[m] = {"median_s": med([r["seconds"] for r in rs]), "hits": sum(r["hit"] for r in rs),
                  "tokens": sum(r["tokens"] for r in rs), "cost": sum(r["cost"] for r in rs),
                  "n": len(rs)}
    return out


def _ratio(a, b):
    return f"{b / a:.1f}x" if a else "n/a"


def verdict_script(s):
    c, o = s["context"], s["old"]
    faster = "faster" if c["median_s"] < o["median_s"] else "slower"
    return (f"Over {c['n']} questions the context way found the expected file first {c['hit1']} times "
            f"and in the top 5 {c['hit5']} times; the old way {o['hit1']} and {o['hit5']}. "
            f"The context way was {faster} (median {c['median_s']:.3f}s vs {o['median_s']:.3f}s) "
            f"and returned {c['tokens']} estimated tokens against {o['tokens']} "
            f"({_ratio(c['tokens'], o['tokens'])} the old way's). Tokens are chars / 4, an estimate.")


def verdict_agent(s):
    c, o = s["context"], s["old"]
    return (f"Over {c['n']} questions the context agent named an expected path {c['hits']} times and "
            f"the grep+Read agent {o['hits']} times. Median time {c['median_s']:.1f}s vs "
            f"{o['median_s']:.1f}s; total tokens {c['tokens']} vs {o['tokens']}; total cost "
            f"${c['cost']:.3f} vs ${o['cost']:.3f}. Both runs carry the same fixed prompt overhead, "
            f"so compare the difference, not the absolute size.")


def render_script(rows, summary, note=""):
    lines = ["| id | kind | ctx s | old s | ctx hit@1 | old hit@1 | ctx hit@5 | old hit@5 | ctx tok (est) | old tok (est) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c, o = r["context"], r["old"]
        lines.append(f"| {r['q']['id']} | {r['q']['kind']} | {c['seconds']:.3f} | {o['seconds']:.3f} | "
                     f"{c['hit1']} | {o['hit1']} | {c['hit5']} | {o['hit5']} | {c['tokens']} | {o['tokens']} |")
    lines += ["", "| method | median time (s) | hit@1 | hit@5 | total tokens (est) |", "|---|---|---|---|---|"]
    for name, m in (("context (search_semantic + get_slice)", "context"), ("old (grep + Read)", "old")):
        s = summary[m]
        lines.append(f"| {name} | {s['median_s']:.3f} | {s['hit1']}/{s['n']} | {s['hit5']}/{s['n']} | {s['tokens']} |")
    lines += ["", f"**Verdict.** {verdict_script(summary)}"]
    if note:
        lines += ["", note]
    return "\n".join(lines)


def render_agent(rows, summary):
    lines = ["| id | ctx s | old s | ctx tokens | old tokens | ctx $ | old $ | ctx hit | old hit |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c, o = r["context"], r["old"]
        lines.append(f"| {r['q']['id']} | {c['seconds']:.1f} | {o['seconds']:.1f} | {c['tokens']} | "
                     f"{o['tokens']} | {c['cost']:.4f} | {o['cost']:.4f} | {c['hit']} | {o['hit']} |")
    lines += ["", "| method | median time (s) | answers naming an expected path | total tokens (real) | total cost (USD) |",
              "|---|---|---|---|---|"]
    for name, m in (("context agent (easy-context tools only)", "context"), ("old agent (Grep, Glob, Read only)", "old")):
        s = summary[m]
        lines.append(f"| {name} | {s['median_s']:.1f} | {s['hits']}/{s['n']} | {s['tokens']} | {s['cost']:.3f} |")
    lines += ["", f"**Verdict.** {verdict_agent(summary)}"]
    return "\n".join(lines)


def write_section(path, name, body, title):
    """Put one named section in the report, replacing it if it exists."""
    block = f"<!-- section:{name} -->\n## {title}\n\n{body}\n<!-- /section:{name} -->\n"
    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    pat = re.compile(rf"<!-- section:{name} -->.*?<!-- /section:{name} -->\n", re.S)
    if pat.search(text):
        text = pat.sub(lambda _m: block, text)
    else:
        if not text:
            text = "# easy-context search vs grep + Read: benchmark (T171)\n\n"
        text += "\n" + block
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def report_path(today=None):
    today = today or datetime.date.today().isoformat()
    return os.path.join(ROOT, "reports", f"context-search-benchmark-{today}.md")


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--root", default=DEFAULT_ROOT, help="indexed repo root (sent as X-Easy-Context-Root)")
    ap.add_argument("--agent", action="store_true", help="real-agent mode (claude -p; costs tokens)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions")
    ap.add_argument("--yes", action="store_true", help="do not ask before real-agent runs")
    ap.add_argument("--report", default=None, help="report file (default reports/context-search-benchmark-<date>.md)")
    args = ap.parse_args(argv)
    path = args.report or report_path()
    questions = load_questions(limit=args.limit)

    if args.agent:
        if not shutil.which("claude"):
            print("claude CLI not found on PATH (needed for --agent)", file=sys.stderr)
            return 2
        runs = 2 * len(questions)
        print(f"Real-agent mode: {runs} `claude -p` runs on {len(questions)} questions; "
              f"expect roughly ${runs * 0.15:.2f}-${runs * 0.5:.2f} in token cost.")
        if not args.yes and input("Continue? [y/N] ").strip().lower() != "y":
            print("Cancelled.")
            return 0
        rows = run_agent_mode(questions, args.root, args.url)
        summary = summarize_agent(rows)
        write_section(path, "agent", render_agent(rows, summary), "Real-agent mode (claude -p)")
        print(verdict_agent(summary))
        print(f"Report: {path}")
        return 0

    client = McpClient(args.url, args.root)
    try:
        client.start()
        rows = run_script_mode(questions, client, args.root)
    except ServerError as err:
        print(str(err), file=sys.stderr)
        return 2
    summary = summarize_script(rows)
    note = ""
    if any(r["context"]["indexing"] for r in rows):
        note = "Note: the server reported `indexing: true`; the index was not finished, results may be incomplete."
    write_section(path, "script", render_script(rows, summary, note), "Script mode")
    print(verdict_script(summary))
    print(f"Report: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
