"""T171 round 4 - bench_hybrid.py: paired diff + bootstrap CI, the pre-registered verdict, stream parsing."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bench_hybrid as h  # noqa: E402


def run(repo, qid, method, cost, correct=1, tools=(), kind="symbol", tokens=100):
    return {"repo": repo, "qid": qid, "kind": kind, "method": method, "cost": cost, "tokens": tokens,
            "correct": correct, "tools": list(tools), "error": False}


def test_paired_diff_uses_mean_of_runs_per_method():
    runs = [run("r", "q1", "hybrid", 0.10), run("r", "q1", "hybrid", 0.20), run("r", "q1", "grep_only", 0.05),
            run("r", "q1", "grep_only", 0.07), run("r", "q2", "hybrid", 0.02), run("r", "q2", "grep_only", 0.04),
            run("r", "q3", "hybrid", 1.0)]  # no grep_only partner: ignored
    d = h.paired_diffs(runs, "cost")
    assert d == pytest.approx([0.15 - 0.06, 0.02 - 0.04])
    assert h.paired_diffs(runs, "cost", repo="other") == []


def test_bootstrap_ci_known_input_is_deterministic_and_brackets_the_mean():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    a, b = h.bootstrap_ci(vals), h.bootstrap_ci(vals)
    assert a == b and a[0] == 3.0 and a[1] < 3.0 < a[2]
    assert h.bootstrap_ci([2.0, 2.0, 2.0]) == (2.0, 2.0, 2.0)
    assert h.bootstrap_ci([]) == (0.0, 0.0, 0.0)
    assert 1.0 <= a[1] and a[2] <= 5.0


CORR_EQ = {"a": {"hybrid": [10, 10], "grep_only": [10, 10]}, "b": {"hybrid": [9, 10], "grep_only": [9, 10]}}
CORR_BETTER = {"a": {"hybrid": [10, 10], "grep_only": [9, 10]}, "b": {"hybrid": [9, 10], "grep_only": [9, 10]}}
CORR_WORSE = {"a": {"hybrid": [8, 10], "grep_only": [9, 10]}, "b": {"hybrid": [9, 10], "grep_only": [9, 10]}}


def test_verdict_keep_when_cheaper_and_not_less_correct():
    assert h.verdict((-0.02, -0.04, -0.001), 0.05, CORR_EQ) == "KEEP"


def test_verdict_keep_when_more_correct_and_cost_within_ten_percent():
    assert h.verdict((0.003, -0.001, 0.004), 0.05, CORR_BETTER) == "KEEP"       # hi 0.004 <= 0.005
    assert h.verdict((0.003, -0.001, 0.006), 0.05, CORR_BETTER).startswith("INCONCLUSIVE")  # hi > 10%


def test_verdict_drop_when_dearer_and_not_more_correct():
    assert h.verdict((0.03, 0.01, 0.05), 0.05, CORR_EQ) == "DROP"
    assert h.verdict((0.03, 0.01, 0.05), 0.05, CORR_WORSE) == "DROP"


def test_verdict_not_drop_if_hybrid_strictly_more_correct_somewhere():
    assert h.verdict((0.03, 0.01, 0.05), 0.05, CORR_BETTER).startswith("INCONCLUSIVE")


def test_verdict_inconclusive_leans():
    assert h.verdict((0.01, -0.02, 0.03), 0.05, CORR_EQ) == "INCONCLUSIVE (leans drop)"
    assert h.verdict((-0.01, -0.03, 0.02), 0.05, CORR_EQ) == "INCONCLUSIVE (leans keep)"
    assert h.verdict((-0.02, -0.04, -0.001), 0.05, CORR_WORSE).startswith("INCONCLUSIVE")  # cheaper but less correct


STREAM = "\n".join(json.dumps(e) for e in [
    {"type": "system", "subtype": "init"},
    {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"},
                                                  {"type": "tool_use", "name": "mcp__easy-context__search_semantic", "input": {}}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {}}]}},
    {"type": "result", "result": "see lib/x.py", "duration_ms": 4000, "total_cost_usd": 0.05, "num_turns": 3,
     "session_id": "S", "is_error": False,
     "usage": {"input_tokens": 1, "output_tokens": 2, "cache_read_input_tokens": 3, "cache_creation_input_tokens": 4}}])


def test_parse_stream_extracts_tools_and_usage():
    row, tools = h.parse_stream(STREAM + "\nnot json\n", ["lib/x.py"])
    assert tools == ["mcp__easy-context__search_semantic", "Read"]
    assert row["tokens"] == 10 and row["cost"] == 0.05 and row["hit"] == 1
    with pytest.raises(ValueError):
        h.parse_stream('{"type": "system"}')


def test_route_adherence_and_overhead():
    runs = [run("r", "q1", "hybrid", 0.06, tools=[h.SEMANTIC], kind="conceptual"),
            run("r", "q2", "hybrid", 0.05, tools=["Grep"], kind="symbol"),
            run("r", "q2", "grep_only", 0.04, tools=["Grep"], kind="symbol"),
            run("r", "q1", "grep_only", 0.04, kind="conceptual")]
    assert h.route_adherence(runs) == {"conceptual": [1, 1], "symbol": [0, 1]}
    o = h.overhead(runs)
    assert o["n"] == 1 and o["diff"] == pytest.approx(0.01)


def test_commands_hybrid_adds_only_search_and_slice_tools():
    g, y = h.command("grep_only", "/r"), h.command("hybrid", "/r")
    assert "--output-format" in y and y[y.index("--output-format") + 1] == "stream-json" and "--verbose" in y
    assert g[g.index("--allowedTools") + 1] == "Grep,Glob,Read"
    allowed = y[y.index("--allowedTools") + 1].split(",")
    assert h.SEMANTIC in allowed and "mcp__easy-context__get_related" not in allowed
    assert "Edit" not in " ".join(g + y) and "Bash" not in " ".join(g + y)
    assert "--no-session-persistence" in g and "--no-session-persistence" in y


def test_prompts_share_the_base_and_hybrid_adds_the_routing_rule_verbatim():
    g, y = h.grep_prompt("Q?", "IGN"), h.hybrid_prompt("Q?", "IGN")
    assert y.startswith(g) and y.endswith(h.ROUTING_RULE) and "IGN" in g and h.ROUTING_RULE not in g


def test_analyze_end_to_end_small_fixture():
    runs = []
    for i in range(6):
        runs += [run("a", f"q{i}", "grep_only", 0.04), run("a", f"q{i}", "hybrid", 0.06, tools=[h.SEMANTIC]),
                 run("b", f"q{i}", "grep_only", 0.04), run("b", f"q{i}", "hybrid", 0.06)]
    a = h.analyze(runs)
    assert a["verdict"] == "DROP" and a["paired"]["cost"]["pooled"][0] == pytest.approx(0.02)
    assert "VERDICT: DROP" in h.render(a)
