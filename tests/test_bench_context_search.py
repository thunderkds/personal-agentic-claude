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
    assert len(qs) >= 35
    kinds = [q["kind"] for q in qs]
    assert kinds.count("conceptual") >= 5 and kinds.count("symbol") >= 5 and kinds.count("doc") >= 3
    for k in ("multi_hop", "exact_text", "callers", "negative"):
        assert kinds.count(k) >= 4, k
    for q in qs:
        assert q["id"] and q["question"] and q["grep_pattern"]
        assert bool(q["expected_paths"]) == (q["kind"] != "negative")
    assert len({q["id"] for q in qs}) == len(qs)
    assert len(b.lifecycle_chains()) >= 4


def test_fixture_expected_paths_exist_in_this_repo():
    for q in b.load_questions():
        for path in q["expected_paths"]:
            assert os.path.exists(os.path.join(ROOT, path)), (q["id"], path)


# ---- MCP client against a fake server (SSE body, session id)

def test_context_way_scores_rank_three_against_fake_server(fake_url):
    FakeServer.hits = [{"id": "1", "path": "a.py"}, {"id": "2", "path": "b.py"},
                       {"id": "3", "path": "docs/x.md"}]
    c = b.McpClient(fake_url, "/root")
    c.start()
    q = {"id": "q", "kind": "doc", "question": "q", "expected_paths": ["docs/x.md"]}
    out = b.context_way(q, c)
    s = b.score(q, out, 0.1)
    assert (s["hit1"], s["hit5"]) == (0, 1)
    assert out["chars"] > 0
    assert "SESS1" in FakeServer.seen_sessions  # session id sent on later calls


def test_parse_sse_and_plain_json():
    assert b.parse_mcp_body(b'event: message\ndata: {"a": 1}\n\n', "text/event-stream") == {"a": 1}
    assert b.parse_mcp_body(b'{"a": 2}', "application/json") == {"a": 2}


# ---- report rendering

def _row(q, ctx_ranked, old_ranked):
    return {"q": q,
            "context": b.score(q, {"ranked": ctx_ranked, "chars": 40, "indexing": False}, 0.2, "context"),
            "old": b.score(q, {"ranked": old_ranked, "chars": 400, "indexing": False}, 0.1, "old"),
            "old_bounded": b.score(q, {"ranked": old_ranked, "chars": 100, "indexing": False}, 0.1, "old_bounded")}


def test_report_rendering_has_all_sections_and_json_roundtrip(tmp_path):
    q = {"id": "q1", "kind": "doc", "question": "x", "expected_paths": ["p"], "grep_pattern": "x"}
    rows = [_row(q, ["p"], ["z", "p"])]
    data = {"date": "2026-10-21",
            "script": {"rows": rows, "summary": b.summarize_script(rows), "per_kind": b.summarize_kinds(rows)},
            "upkeep": {"full_reindex_s": 9.0, "noop_reindex_s": 0.3, "touch_1_reindex_s": 0.4,
                       "touch_10_reindex_s": 0.8, "add_1_new_file_reindex_s": 0.5, "files": 5, "slices": 9,
                       "staleness": {"new_file_found": True, "after_edit_old_text_still_returned": True,
                                     "after_edit_new_text_found": False},
                       "git_status_unchanged": True}}
    md, js = str(tmp_path / "r.md"), str(tmp_path / "r.json")
    b.save_data(data, md, js)
    text = open(md).read()
    assert "## Recommendation" in text and "## Script mode" in text and "## Index upkeep" in text
    assert "| q1 | doc |" in text and "old, bounded" in text and "estimated" in text
    assert "old text until the file was re-indexed" in text
    assert json.load(open(js))["script"]["rows"][0]["q"]["id"] == "q1"


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
    assert "--no-session-persistence" in ctx and "--resume" not in ctx
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


# ---- round 2 (R1-R7): scoring kinds, bounded old way, budget, lifecycle

def test_multi_hop_hit5_needs_all_hit1_needs_any():
    q = {"id": "m", "kind": "multi_hop", "expected_paths": ["a.py", "t.py"]}
    out = {"ranked": ["a.py", "x", "y"], "chars": 4, "indexing": False}
    s = b.score(q, out, 0.1, "old")
    assert (s["hit1"], s["hit5"]) == (1, 0)
    out["ranked"] = ["a.py", "x", "t.py"]
    assert b.score(q, out, 0.1, "old")["hit5"] == 1


def test_negative_scoring_grep_right_when_nothing_found_context_unscored():
    q = {"id": "n", "kind": "negative", "expected_paths": []}
    none = {"ranked": [], "chars": 0, "indexing": False}
    some = {"ranked": ["a.py"], "chars": 9, "indexing": False}
    assert b.score(q, none, 0.1, "old")["hit5"] == 1
    assert b.score(q, some, 0.1, "old_bounded")["hit1"] == 0
    assert b.score(q, some, 0.1, "context")["hit1"] is None


def test_summary_skips_unscored_rows():
    qn = {"id": "n", "kind": "negative", "expected_paths": []}
    qd = {"id": "d", "kind": "doc", "expected_paths": ["p"]}
    rows = [_row(qn, ["a"], []), _row(qd, ["p"], ["p"])]
    sm = b.summarize_script(rows)
    assert sm["context"]["n"] == 1 and sm["old"]["n"] == 2
    assert b.summarize_kinds(rows)["negative"]["context"]["n"] == 0


def test_old_bounded_reads_a_window_not_the_whole_file(tmp_path):
    (tmp_path / "big.py").write_text("\n".join(f"line{i}" for i in range(500)) + "\nneedle\n" + "x\n" * 500)
    full = b.old_way({"grep_pattern": "needle"}, str(tmp_path))
    bounded = b.old_bounded({"grep_pattern": "needle"}, str(tmp_path))
    assert bounded["ranked"] == ["big.py"] == full["ranked"]
    assert bounded["chars"] < full["chars"] / 5


def test_old_bounded_caps_the_file_list_and_misses_cleanly(tmp_path):
    for i in range(80):
        (tmp_path / f"f{i:02d}.txt").write_text("needle\n")
    out = b.old_bounded({"grep_pattern": "needle"}, str(tmp_path))
    assert len(out["ranked"]) == 80 and out["chars"] < 80 * 20  # list capped at 50 lines + 81-line read
    assert b.old_bounded({"grep_pattern": "zzz"}, str(tmp_path)) == {"ranked": [], "chars": 0, "indexing": False}


def test_grade_answer_per_kind():
    multi = {"kind": "callers", "expected_paths": ["a.py", "b.py"]}
    assert b.grade_answer(multi, "a.py and b.py") == 1
    assert b.grade_answer(multi, "only a.py") == 0
    one = {"kind": "doc", "expected_paths": ["d/x.md"]}
    assert b.grade_answer(one, "see ./d/x.md") == 1
    neg = {"kind": "negative", "expected_paths": []}
    assert b.grade_answer(neg, "NOT FOUND") == 1
    assert b.grade_answer(neg, "**NOT FOUND**\n\nThe closest file, docs/x.md, is unrelated.") == 1
    assert b.grade_answer(neg, "I think it is docs/x.md. NOT FOUND otherwise") == 0
    assert b.grade_answer(neg, "It is in lib/x.py") == 0


def test_budget_aborts_before_passing_the_cap(tmp_path):
    bud = b.Budget(cap=1.0, path=str(tmp_path / "s.json"), per_run=0.5)
    bud.check()
    bud.add(0.6)
    with pytest.raises(b.BudgetExceeded):
        bud.check()
    assert b.Budget(cap=1.0, path=str(tmp_path / "s.json")).spent == pytest.approx(0.6)  # persisted


def test_run_agent_mode_stops_when_budget_is_hit(monkeypatch, tmp_path):
    calls = []

    def fake(q, method, root, url, budget, **kw):
        budget.check()
        calls.append((q["id"], method))
        budget.add(0.4)
        return {"correct": 1, "tokens": 1, "cost": 0.4, "seconds": 1}

    monkeypatch.setattr(b, "run_claude", fake)
    qs = [{"id": f"q{i}", "kind": "doc", "question": "x", "expected_paths": ["p"]} for i in range(5)]
    res = b.run_agent_mode(qs, "/r", "u", b.Budget(cap=1.0, per_run=0.5), repeat_ids=[])
    assert res["aborted"] and len(calls) == 2 and len(res["rows"]) == 1


def test_agent_command_resume_and_persistence():
    cmd = b.agent_command("context", "/r", "http://u/mcp", persist=True, resume="SID", fork=True)
    assert "--no-session-persistence" not in cmd
    assert cmd[cmd.index("--resume") + 1] == "SID" and "--fork-session" in cmd


def test_lifecycle_chain_records_each_step_and_waits(monkeypatch, tmp_path):
    seen, slept = [], []

    def fake(q, method, root, url, budget, **kw):
        seen.append((q["id"], kw.get("resume")))
        return {"session_id": "S1", "correct": 1, "cost": 0.01, "seconds": 1.0, "input": 2, "output": 3,
                "cache_read": 100, "cache_creation": 7, "tokens": 112, "error": False, "answer": ""}

    monkeypatch.setattr(b, "run_claude", fake)
    chain = {"id": "L", "q1": "a", "q1_expected": ["p"], "q2_followup": "f", "q2_standalone": "s", "q2_expected": ["p"]}
    ticks = iter([0, 10, 20, 30, 40])
    steps = b.run_chain("context", chain, "/r", "u", b.Budget(cap=99), waits=(372,),
                        sleep=slept.append, clock=lambda: next(ticks))
    assert [s["label"] for s in steps] == ["q1", "same_session", "fresh", "resume_after_372s"]
    assert slept == [362]  # waits until 372s after Q1, not 372s more
    assert [r for _, r in seen] == [None, "S1", None, "S1"]
    summ = b.summarize_lifecycle(steps)
    assert summ["resume_after_372s"]["context"]["cache_read"] == 100
    assert "cache_creation" in b.render_lifecycle({"summary": summ})


def test_spread_min_median_max():
    reps = [{"id": "q", "method": "old", "tokens": t, "cost": t / 100, "seconds": 1, "correct": 1} for t in (10, 30, 20)]
    sp = b.spread(reps)["q"]["old"]
    assert sp["tokens"] == [10, 20, 30] and sp["correct"] == [3, 3]


def test_upkeep_probe_leaves_the_checkout_clean(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-qm", "i"], check=True)
    store = {}

    class Fake:
        def call(self, name, args):
            return "", {}

    monkeypatch.setattr(b, "reindex", lambda client, force=False: (0.1, {"files": 1, "slices": 2}))
    monkeypatch.setattr(b, "search_has", lambda client, query, needle, path_hint=None: needle.endswith("4417"))
    out = b.run_upkeep(Fake(), str(tmp_path))
    assert out["git_status_unchanged"] and not os.path.exists(tmp_path / "zz_staleness_probe.md")
    assert out["staleness"]["after_edit_old_text_still_returned"] and not out["staleness"]["after_edit_new_text_found"]


def test_regrade_recomputes_from_stored_answers():
    q = {"id": "n", "kind": "negative", "expected_paths": []}
    ok = {"error": False, "answer": "NOT FOUND\nnothing about x in lib/y.py", "correct": 0, "tokens": 1, "cost": 0.1, "seconds": 1}
    bad = dict(ok, answer="it is lib/y.py")
    data = {"agent": {"rows": [{"q": q, "context": dict(ok), "old": dict(bad)}], "repeats": []}}
    out = b.regrade(data)["agent"]
    assert out["summary"]["context"]["correct"] == 1 and out["summary"]["old"]["correct"] == 0


# ---- round 3 (T1-T6): --questions, per-target grep scope, read-only upkeep, comparison

TAPCHAT = os.path.join(ROOT, "tests", "fixtures", "context_search_questions_tapchat.json")


def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("dist/\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.ts").write_text("needle\nneedle\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "b.md").write_text("needle\n")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "a.js").write_text("needle\n" * 50)  # ignored build output
    (tmp_path / "untracked.txt").write_text("needle\n" * 90)
    subprocess.run(["git", "-C", str(tmp_path), "add", ".gitignore", "src", "docs"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-qm", "i"], check=True)
    return tmp_path


@pytest.fixture
def scope():
    saved = dict(b.GREP_SCOPE)
    yield b.GREP_SCOPE
    b.GREP_SCOPE.clear()
    b.GREP_SCOPE.update(saved)


def test_tracked_grep_ignores_build_output_and_untracked(tmp_path, scope):
    repo = _git_repo(tmp_path)
    scope["tracked"] = True
    out = b.old_way({"grep_pattern": "needle"}, str(repo))
    assert out["ranked"] == ["src/a.ts", "docs/b.md"]
    out = b.old_bounded({"grep_pattern": "needle"}, str(repo))
    assert out["ranked"] == ["src/a.ts", "docs/b.md"]


def test_working_tree_grep_counts_untracked_files(tmp_path, scope):
    repo = _git_repo(tmp_path)
    scope["tracked"] = False
    scope["exclude_dirs"] = b.GREP_EXCLUDE_DIRS + ["dist"]
    ranked = b.old_way({"grep_pattern": "needle"}, str(repo))["ranked"]
    assert ranked[0] == "untracked.txt" and "dist/a.js" not in ranked


def test_per_target_exclude_dirs_apply_in_tracked_mode(tmp_path, scope):
    repo = _git_repo(tmp_path)
    scope["tracked"] = True
    scope["exclude_dirs"] = b.GREP_EXCLUDE_DIRS + ["docs"]
    assert b.old_way({"grep_pattern": "needle"}, str(repo))["ranked"] == ["src/a.ts"]


def test_tracked_grep_does_not_touch_the_repo(tmp_path, scope):
    repo = _git_repo(tmp_path)
    before = subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout
    scope["tracked"] = True
    b.old_way({"grep_pattern": "needle"}, str(repo))
    b.old_bounded({"grep_pattern": "needle"}, str(repo))
    assert subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout == before


def test_questions_option_selects_the_fixture_and_default_is_unchanged():
    assert b.load_questions()[0]["id"] == "c01"
    tap = b.load_questions(TAPCHAT)
    assert len(tap) >= 35 and tap != b.load_questions()
    assert len(b.lifecycle_chains(TAPCHAT)) == 2


def test_tapchat_fixture_mix():
    qs = b.load_questions(TAPCHAT)
    kinds = [q["kind"] for q in qs]
    for k in ("conceptual", "symbol", "callers", "multi_hop", "exact_text"):
        assert kinds.count(k) >= 6, k
    assert kinds.count("negative") >= 4 and kinds.count("doc") >= 3
    assert all(bool(q["expected_paths"]) == (q["kind"] != "negative") for q in qs)


def test_tapchat_ground_truth_exists_when_the_repo_is_present():
    root = "/home/hungnguyenhuu/workspace/project/beautifly/github/tapchat-apis"
    if not os.path.isdir(root):
        pytest.skip("tapchat-apis not on this machine")
    for q in b.load_questions(TAPCHAT):
        for path in q["expected_paths"]:
            assert os.path.exists(os.path.join(root, path)), (q["id"], path)


def test_upkeep_without_probe_writes_nothing(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    calls = []
    monkeypatch.setattr(b, "reindex", lambda client, force=False: (calls.append(force) or 0.1, {"files": 3, "slices": 4}))
    monkeypatch.setattr(b.os, "utime", lambda *a, **k: pytest.fail("touched a file"))
    out = b.run_upkeep(object(), str(repo), probe=False)
    assert calls == [True, False] and out["git_status_unchanged"] and "staleness" not in out
    assert "Timing only" in b.render_upkeep(out)


def test_report_scope_and_comparison_sections(tmp_path):
    q = {"id": "q1", "kind": "doc", "question": "x", "expected_paths": ["p"], "grep_pattern": "x"}
    rows = [_row(q, ["p"], ["p"])]
    ag = {"rows": [], "per_kind": {}, "summary": {m: {"n": 1, "correct": 1, "median_s": 1, "tokens": 10, "cost": 0.1} for m in ("context", "old")}}
    mk = lambda: {"script": {"rows": rows, "summary": b.summarize_script(rows), "per_kind": b.summarize_kinds(rows)}, "agent": ag}  # noqa: E731
    data = dict(mk(), grep_scope="`git grep` over git-tracked files only; skipped directories: dist.")
    md, js = str(tmp_path / "r.md"), str(tmp_path / "r.json")
    b.save_data(data, md, js, compare=("repo A", mk(), "repo B", data))
    text = open(md).read()
    assert "## This repo vs tapchat-apis" in text and "repo A" in text and "git grep" in text
    assert b.report_paths("2026-10-22", "tapchat")[1].endswith("context-search-benchmark-tapchat-2026-10-22.json")
