"""T171 - bench_context_search.py: unit tests (no server, no `claude`) and a live test that skips."""
import http.server
import json
import os
import subprocess
import sys
import threading
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bench_context_search as b  # noqa: E402

LIVE_URL = b.DEFAULT_URL


def sse(payload):
    return ("event: message\ndata: " + json.dumps(payload) + "\n\n").encode()


def tool_reply(obj):
    return {"jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": json.dumps(obj)}]}}


class FakeServer(http.server.BaseHTTPRequestHandler):
    hits = []          # what search_semantic returns
    seen_sessions = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeServer.seen_sessions.append(self.headers.get("mcp-session-id"))
        if "id" not in msg:
            self.send_response(202)
            self.end_headers()
            return
        if msg["method"] == "initialize":
            body = sse({"jsonrpc": "2.0", "id": msg["id"], "result": {"serverInfo": {}}})
        elif msg["params"]["name"] == "search_semantic":
            body = sse(tool_reply({"indexing": False, "hits": FakeServer.hits}))
        else:
            body = sse(tool_reply({"id": "x", "text": "slice text"}))
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("mcp-session-id", "SESS1")
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def fake_url():
    srv = http.server.HTTPServer(("127.0.0.1", 0), FakeServer)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FakeServer.seen_sessions = []
    yield f"http://127.0.0.1:{srv.server_port}/mcp"
    srv.shutdown()


# ---- scoring / helpers

def test_hit_at_rank_three_is_hit5_not_hit1():
    ranked = ["a.py", "b.py", "docs/x.md", "c.py"]
    assert b.hit_at(ranked, ["docs/x.md"], 1) == 0
    assert b.hit_at(ranked, ["docs/x.md"], 5) == 1


def test_hit_at_no_match_and_empty():
    assert b.hit_at(["a"], ["z"], 5) == 0
    assert b.hit_at([], ["z"], 5) == 0


def test_path_normalisation():
    assert b.norm_path("./a/b") == "a/b"
    assert b.hit_at(["./a/b"], ["a/b"], 1) == 1


def test_rank_files_by_match_count_then_path():
    out = "./b.py:1:x\n./a.py:3:x\n./b.py:9:x\n./c.py:2:x\n"
    assert b.rank_files(out) == ["b.py", "a.py", "c.py"]
    assert b.rank_files("") == []


def test_token_estimate_is_chars_over_four_rounded_up():
    assert b.est_tokens(0) == 0
    assert b.est_tokens(4) == 1
    assert b.est_tokens(5) == 2


def test_old_way_zero_matches_is_a_miss_not_a_crash(tmp_path):
    (tmp_path / "f.txt").write_text("nothing here")
    out = b.old_way({"grep_pattern": "zzz_no_such_thing"}, str(tmp_path))
    assert out["ranked"] == [] and out["chars"] == 0


def test_old_way_reads_top_file(tmp_path):
    (tmp_path / "hot.py").write_text("needle\nneedle\n")
    (tmp_path / "cold.py").write_text("needle\n")
    out = b.old_way({"grep_pattern": "needle"}, str(tmp_path))
    assert out["ranked"][0] == "hot.py"
    assert out["chars"] > len("needle\nneedle\n")


def test_old_way_skips_excluded_dirs(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "x").write_text("needle")
    assert b.old_way({"grep_pattern": "needle"}, str(tmp_path))["ranked"] == []


def test_fixture_shape_and_mix():
    qs = b.load_questions()
    assert 15 <= len(qs) <= 20
    kinds = [q["kind"] for q in qs]
    assert kinds.count("conceptual") >= 5 and kinds.count("symbol") >= 5 and kinds.count("doc") >= 3
    for q in qs:
        assert q["id"] and q["question"] and q["grep_pattern"] and q["expected_paths"]
    assert len({q["id"] for q in qs}) == len(qs)


# ---- MCP client against a fake server (SSE body, session id)

def test_context_way_scores_rank_three_against_fake_server(fake_url):
    FakeServer.hits = [{"id": "1", "path": "a.py"}, {"id": "2", "path": "b.py"},
                       {"id": "3", "path": "docs/x.md"}]
    c = b.McpClient(fake_url, "/root")
    c.start()
    q = {"id": "q", "question": "q", "expected_paths": ["docs/x.md"]}
    out = b.context_way(q, c)
    s = b.score(q, out, 0.1)
    assert (s["hit1"], s["hit5"]) == (0, 1)
    assert out["chars"] > 0
    assert "SESS1" in FakeServer.seen_sessions  # session id sent on later calls


def test_parse_sse_and_plain_json():
    assert b.parse_mcp_body(b'event: message\ndata: {"a": 1}\n\n', "text/event-stream") == {"a": 1}
    assert b.parse_mcp_body(b'{"a": 2}', "application/json") == {"a": 2}


# ---- report rendering

def test_report_rendering_and_section_replace(tmp_path):
    q = {"id": "q1", "kind": "doc", "question": "x", "expected_paths": ["p"]}
    row = {"q": q,
           "context": b.score(q, {"ranked": ["p"], "chars": 40, "indexing": False}, 0.2),
           "old": b.score(q, {"ranked": ["z", "p"], "chars": 400, "indexing": False}, 0.1)}
    summary = b.summarize_script([row])
    text = b.render_script([row], summary)
    assert "| q1 | doc |" in text and "**Verdict.**" in text
    assert "1/1" in text and "estimated" in text
    path = str(tmp_path / "r.md")
    b.write_section(path, "script", text, "Script mode")
    b.write_section(path, "agent", "agent body", "Real-agent mode")
    b.write_section(path, "script", "new body", "Script mode")
    out = open(path).read()
    assert out.count("Script mode") == 1 and "new body" in out and "agent body" in out


def test_agent_json_parsing_sums_all_usage():
    raw = json.dumps({"result": "see ./docs/x.md", "duration_ms": 2500, "total_cost_usd": 0.05,
                      "num_turns": 3, "usage": {"input_tokens": 1, "output_tokens": 2,
                                                "cache_creation_input_tokens": 3,
                                                "cache_read_input_tokens": 4}})
    r = b.parse_agent_json(raw, ["docs/x.md"])
    assert r["tokens"] == 10 and r["hit"] == 1 and r["seconds"] == 2.5 and r["cost"] == 0.05


def test_agent_commands_allow_only_read_tools():
    ctx = b.agent_command("context", "/r", "http://u/mcp")
    old = b.agent_command("old", "/r", "http://u/mcp")
    assert "Edit" not in " ".join(ctx + old) and "Write" not in " ".join(ctx + old)
    assert "Bash" not in " ".join(ctx + old)
    assert ctx[ctx.index("--tools") + 1] == ""
    assert old[old.index("--tools") + 1] == "Grep,Glob,Read"


# ---- CLI negative cases

def test_server_unreachable_exits_2_naming_url(tmp_path):
    url = "http://127.0.0.1:1/mcp"
    done = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "bench_context_search.py"),
                           "--url", url, "--report", str(tmp_path / "r.md")],
                          capture_output=True, text=True)
    assert done.returncode == 2
    assert f"easy-context server not reachable at {url}" in done.stderr


def test_agent_mode_without_claude_exits_2(tmp_path):
    env = dict(os.environ, PATH=str(tmp_path))
    done = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "bench_context_search.py"),
                           "--agent", "--yes"], capture_output=True, text=True, env=env)
    assert done.returncode == 2 and "claude" in done.stderr


# ---- live (skips when the server is down)

def _server_up():
    try:
        urllib.request.urlopen(LIVE_URL, timeout=2)
    except urllib.error.HTTPError:
        return True
    except OSError:
        return False
    return True


@pytest.mark.skipif(not _server_up(), reason="easy-context server not running")
def test_live_one_question_both_ways():
    c = b.McpClient(LIVE_URL, b.DEFAULT_ROOT)
    c.start()
    q = b.load_questions(limit=1)[0]
    out = b.context_way(q, c)
    assert out["ranked"] and out["chars"] > 0
