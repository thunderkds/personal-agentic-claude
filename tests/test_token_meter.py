"""T124 — token meter over Claude Code session transcripts.

Every check drives the real entry point (`python3 scripts/token_meter.py`) with
`subprocess` against the committed synthetic fixtures under
`tests/fixtures/transcripts/` (T085/T093: behavioural claims need the real entry
point). Expected numbers are hand-computed in the comments next to each assert.

Prices throughout: $5 / $25 per MTok (claude-opus-5), i.e. 5e-6 $/input token,
25e-6 $/output token. Call cost = (input + 2*w1h + 1.25*w5m + 0.1*read) * 5e-6
+ output * 25e-6. Tokens estimated from characters are chars / 3.5.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "token_meter.py"
FIX = ROOT / "tests" / "fixtures" / "transcripts"
SENTINEL = "SENTINEL-7f3a9c"


def run(*args, env=None):
    full_env = dict(os.environ)
    full_env.pop("CLAUDE_CONFIG_DIR", None)
    full_env.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, env=full_env, timeout=60)


def run_json(*args, env=None):
    result = run(*args, "--json", env=env)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# --- SC1 (AC3, AC4) — de-dup + pricing -------------------------------------

def test_sc1_calls_are_deduplicated_and_spend_is_exact():
    """basic: msg_1 is streamed as two entries with the same message.id.

    msg_1: (100000 + 2*1000000[1h])            *5e-6 + 50000*25e-6  = 10.50 + 1.25 = 11.75
    msg_2: (10000 + 1.25*200000[5m] + 0.1*1e6)  *5e-6 + 20000*25e-6  =  1.80 + 0.50 =  2.30
    msg_3: (0 + 1.25*400000[no split→5m] + 0.1*1.2e6)*5e-6 + 100000*25e-6 = 3.10 + 2.50 = 5.60
    total 19.65. M1 (no de-dup) → 31.40; M2 (1h at 1.25x) → 15.90.
    Components: input 0.55, cache_write 13.75, cache_read 1.10, output 4.25.
    """
    data = run_json("--projects-dir", FIX / "basic" / "projects")
    summary = data["summary"]
    assert summary["api_calls"] == 3
    assert summary["transcripts"] == 1 and summary["main"] == 1 and summary["sub"] == 0
    assert round(summary["spend_usd"], 2) == 19.65
    comps = summary["components"]
    assert round(comps["input"]["usd"], 2) == 0.55
    assert round(comps["cache_write"]["usd"], 2) == 13.75
    assert round(comps["cache_read"]["usd"], 2) == 1.10
    assert round(comps["output"]["usd"], 2) == 4.25
    assert sum(c["share_pct"] for c in comps.values()) == pytest.approx(100.0)


def test_sc1_text_output_names_the_spend_and_components():
    result = run("--projects-dir", FIX / "basic" / "projects")
    assert result.returncode == 0, result.stderr
    assert "$19.65" in result.stdout
    for label in ("input", "cache write", "cache read", "output"):
        assert label in result.stdout


def test_price_overrides_are_applied():
    """--price-in 10 --price-out 50 doubles every term: 39.30."""
    data = run_json("--projects-dir", FIX / "basic" / "projects", "--price-in", "10", "--price-out", "50")
    assert round(data["summary"]["spend_usd"], 2) == 39.30


def test_default_root_is_claude_config_dir_projects():
    data = run_json(env={"CLAUDE_CONFIG_DIR": str(FIX / "basic")})
    assert data["summary"]["api_calls"] == 3


# --- SC2 / SC3 (AC5) — spawns ------------------------------------------------

def spawns_of(data):
    return {s["task"]: s for s in data["spawns"]["items"]}


def test_sc2_spawn_pre_edit_reading():
    """agent-a1: prompt names TASK_GUIDE_T901 (78 chars). Calls s1..s5, Edit issued by s3.

    pre-edit results: tu_a 700 chars + tu_b 1050 chars (list-of-blocks) = 1750/3.5 = 500 tokens.
    tu_c (the Edit's own result) and tu_d (Read after the edit) are NOT pre-edit (M3 → 1520).
    calls before edit = 2 (s1, s2). context at edit = s3: 10 + 400 + 5300 = 5710.
    fixed prefix = s1: 10 + 5000 + 0 = 5010.
    cost: s1 .05255 + s2 .00805 + s3 .0117 + s4 .0164 + s5 .0147 = .1034.
    carry: tu_a 200 tok first sent in s2 (1h write 2x, then read by s3..s5: 3*0.1) → 200*5e-6*2.3 = .0023
           tu_b 300 tok first sent in s3 (2x, read by s4,s5)                   → 300*5e-6*2.2 = .0033
    pre-edit carry share = .0056 / .1034 = 5.4159%.
    """
    data = run_json("--projects-dir", FIX / "spawn")
    spawn = spawns_of(data)["T901"]
    assert spawn["calls"] == 5
    assert spawn["spawn_prompt_chars"] == 78
    assert spawn["fixed_prefix_tokens"] == 5010
    assert spawn["pre_edit_tokens"] == 500
    assert spawn["calls_before_edit"] == 2
    assert spawn["context_at_edit"] == 5710
    assert spawn["edited"] is True
    assert spawn["cost_usd"] == pytest.approx(0.1034)
    assert spawn["pre_edit_carry_share_pct"] == pytest.approx(5.4159, abs=1e-3)
    assert spawn["transcript"] == "agent-a1.jsonl"


def test_sc3_non_spawn_is_not_listed_and_short_spawn_is_excluded_from_medians():
    """sess-main.jsonl never names a TASK_GUIDE → not a spawn. agent-a2 (T902, list-of-blocks
    first message) has 1 call → listed, excluded from medians, which are then T901's own values."""
    data = run_json("--projects-dir", FIX / "spawn")
    spawns = spawns_of(data)
    assert set(spawns) == {"T901", "T902"}
    assert "sess-main.jsonl" not in {s["transcript"] for s in data["spawns"]["items"]}
    assert spawns["T902"]["in_medians"] is False
    assert data["spawns"]["excluded_short"] == 1
    assert data["spawns"]["median"]["pre_edit_tokens"] == 500
    assert data["spawns"]["median"]["calls_before_edit"] == 2


def test_task_filter_keeps_only_that_task():
    data = run_json("--projects-dir", FIX / "spawn", "--task", "T902")
    assert [s["task"] for s in data["spawns"]["items"]] == ["T902"]


# --- SC4 (AC7) — counterfactual -------------------------------------------

def test_sc4_bash_counterfactual_and_recall_risk():
    """500-line stdout, 'FAILED x' on line 250. Rule keeps lines 1-40, error lines, 441-500.
    Elided = lines 41..440 minus 250 = 399 lines * (35 chars + newline) = 14364 chars = 4104 tokens.
    Carry: first sent in b2 (1h, 2x) and read once more by b3 → 4104*5e-6*2.1 = .043092.
    b2's text quotes line 300 (elided, 35 chars ≥ 25) → recall risk 1."""
    data = run_json("--projects-dir", FIX / "bash", "--bash-lines", "200")
    cf = data["counterfactual"]
    assert cf["bash_outputs"] == 1
    assert cf["qualifying"] == 1
    assert cf["saved_tokens"] == 4104
    assert cf["saving_usd"] == pytest.approx(0.043092)
    assert cf["recall_risk"] == 1

    data = run_json("--projects-dir", FIX / "bash", "--bash-lines", "600")
    assert data["counterfactual"]["qualifying"] == 0
    assert data["counterfactual"]["recall_risk"] == 0


def test_recall_window_is_three_outputs():
    """bash_late: the only quote of an elided line is in the 4th output after the result → 0."""
    data = run_json("--projects-dir", FIX / "bash_late", "--bash-lines", "200")
    assert data["counterfactual"]["qualifying"] == 1
    assert data["counterfactual"]["recall_risk"] == 0


def test_counterfactual_absent_without_flag():
    assert run_json("--projects-dir", FIX / "bash")["counterfactual"] is None


# --- SC5 (AC8) — no content ever printed --------------------------------------

@pytest.mark.parametrize("args", [
    [],
    ["--json"],
    ["--bash-lines", "1"],
    ["--bash-lines", "1", "--json"],
    ["--task", "T903"],
    ["--task", "T903", "--json"],
])
def test_sc5_sentinel_never_printed_in_directory_modes(args):
    result = run("--projects-dir", FIX / "sentinel", *args)
    assert result.returncode == 0, result.stderr
    assert SENTINEL not in result.stdout + result.stderr
    assert "T903" in result.stdout  # the spawn was found, so its content was read


@pytest.mark.parametrize("args", [[], ["--json"]])
def test_sc5_sentinel_never_printed_in_session_mode(args):
    path = FIX / "sentinel" / "proj-d" / "sess-sent" / "subagents" / "agent-s1.jsonl"
    result = run("--session", path, *args)
    assert result.returncode == 0, result.stderr
    assert SENTINEL not in result.stdout + result.stderr


# --- SC6 (AC6) — session view -------------------------------------------------

def test_sc6_session_composition_excludes_prompt_snapshot():
    """sess-comp: calls c1 (1h), c2 (1h), c3 (5m); latest context = c3: 20 + 30 + 1500 = 1550.
    spend: c1 .0103 + c2 .0058 + c3 .0011625 = .0172625.
    skill_listing 350 chars = 100 tok, first sent in c1 (2x) + read by c2,c3 → 100*5e-6*2.2 = .0011.
    Read result 700 chars = 200 tok, first sent in c2 (2x) + read by c3 → 200*5e-6*2.1 = .0021.
    'fin' (c3's own output) is never sent back → carries 0.
    prompt_snapshot (35000 chars) must not appear at all."""
    data = run_json("--session", FIX / "session" / "proj-e" / "sess-comp.jsonl")
    session = data["session"]
    assert session["calls"] == 3
    assert session["latest_context_tokens"] == 1550
    assert session["spend_usd"] == pytest.approx(0.0172625)
    comp = session["composition"]
    assert "attachment:prompt_snapshot" not in comp
    assert set(comp) == {"attachment:skill_listing", "user_text", "assistant_text",
                         "tool_input", "tool_result:Read"}
    assert comp["attachment:skill_listing"]["carry_usd"] == pytest.approx(0.0011)
    assert comp["tool_result:Read"]["carry_usd"] == pytest.approx(0.0021)


def test_session_text_output():
    result = run("--session", FIX / "session" / "proj-e" / "sess-comp.jsonl")
    assert result.returncode == 0, result.stderr
    assert "tool_result:Read" in result.stdout
    assert "attachment:prompt_snapshot" not in result.stdout
    assert "1,550" in result.stdout


# --- SC7 / SC8 (AC10) — loud on drift ------------------------------------------

def test_sc7_nothing_parses_exits_2_naming_usage():
    result = run("--projects-dir", FIX / "nousage")
    assert result.returncode == 2
    assert "usage" in result.stderr
    assert "sess-nousage.jsonl" in result.stderr


def test_unparsed_file_is_listed_by_basename_beside_a_good_one():
    data = run_json("--projects-dir", FIX / "mixed")
    assert data["summary"]["unparsed"] == ["sess-drift.jsonl"]
    assert data["summary"]["api_calls"] == 1


def test_empty_or_missing_projects_dir_exits_2():
    with tempfile.TemporaryDirectory() as empty:
        result = run("--projects-dir", empty)
        assert result.returncode == 2
        assert "no transcripts" in result.stderr
        result = run("--projects-dir", os.path.join(empty, "absent"))
        assert result.returncode == 2


def test_sc8_malformed_line_is_skipped_and_counted():
    data = run_json("--projects-dir", FIX / "malformed")
    assert data["summary"]["malformed_lines"] == 1
    assert data["summary"]["api_calls"] == 2


def test_symlinked_directory_outside_root_is_not_followed():
    with tempfile.TemporaryDirectory() as root:
        os.symlink(FIX / "basic" / "projects" / "proj-a", os.path.join(root, "link"))
        result = run("--projects-dir", root)
        assert result.returncode == 2  # nothing inside the root itself


# --- SC9 (AC9) — JSON shape ------------------------------------------------------

def test_sc9_json_keys_are_as_documented():
    data = run_json("--projects-dir", FIX / "spawn", "--bash-lines", "200")
    assert set(data) == {"projects_dir", "prices", "summary", "spawns", "counterfactual"}
    assert set(data["summary"]) == {"transcripts", "main", "sub", "api_calls", "spend_usd",
                                    "components", "malformed_lines", "unparsed"}
    assert set(data["summary"]["components"]) == {"input", "cache_write", "cache_read", "output"}
    assert set(data["spawns"]) == {"items", "median", "excluded_short"}
    assert set(data["spawns"]["items"][0]) == {
        "transcript", "task", "calls", "spawn_prompt_chars", "fixed_prefix_tokens",
        "pre_edit_tokens", "calls_before_edit", "context_at_edit", "edited", "edit_via", "cost_usd",
        "pre_edit_carry_share_pct", "in_medians"}
    assert set(data["counterfactual"]) == {"bash_lines", "bash_outputs", "qualifying",
                                           "saved_tokens", "saving_usd", "saving_share_pct",
                                           "recall_risk", "recall_risk_pct"}
    session = run_json("--session", FIX / "session" / "proj-e" / "sess-comp.jsonl")
    assert set(session) == {"prices", "session"}
    assert set(session["session"]) == {"transcript", "calls", "spend_usd", "latest_context_tokens",
                                       "context_now", "context_peak", "calls_over_150k",
                                       "top_content_kinds", "composition", "malformed_lines"}


def test_every_json_key_is_documented_in_the_module_docstring():
    source = SCRIPT.read_text()
    docstring = source.split('"""')[1]
    for key in ("projects_dir", "prices", "summary", "spawns", "counterfactual", "session",
                "pre_edit_carry_share_pct", "recall_risk_pct", "latest_context_tokens",
                "composition", "excluded_short", "unparsed", "context_now", "context_peak",
                "calls_over_150k", "top_content_kinds"):
        assert key in docstring, key


# --- SC10 (AC1) — read-only ------------------------------------------------------

def test_sc10_source_never_writes():
    source = SCRIPT.read_text()
    assert not re.search(r"open\([^)]*['\"][wax]\+?b?['\"]", source)
    assert not re.search(r"mode\s*=\s*['\"][wax]", source)
    # Write *calls*, not bare words: the Bash-write detector (T128) legitimately holds the
    # strings "mkdir" and "write_text" as patterns it looks for in other programs' commands.
    for forbidden in (r"\bos\.(?:mkdir|makedirs|remove|unlink|rename|replace)\(",
                      r"\.write_(?:text|bytes)\(", r"(?<!stdout)\.write\(", r"\bshutil\b"):
        assert not re.search(forbidden, source), forbidden


def test_run_leaves_fixture_tree_unchanged():
    def snapshot():
        return {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in FIX.rglob("*")}
    before = snapshot()
    run("--projects-dir", FIX, "--bash-lines", "200")
    assert snapshot() == before


def test_entries_without_message_id_are_separate_calls(tmp_path):
    """Stage 4 finding: id-less entries once collapsed into one call (silent undercount)."""
    usage = {"input_tokens": 10, "output_tokens": 10,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
    for name in ("a", "b"):
        project = tmp_path / name
        project.mkdir()
        lines = [json.dumps({"type": "assistant", "message": {"usage": usage, "content": []}})] * 3
        (project / "s.jsonl").write_text("\n".join(lines) + "\n")
    data = run_json("--projects-dir", tmp_path)
    assert data["summary"]["api_calls"] == 6


# --- T126 — --current resolves the running session's transcript -------------------

def _usage(ctx_read):
    return {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": ctx_read,
            "cache_creation_input_tokens": 0}


def _call(mid, ctx, text="x", tool=None):
    block = ({"type": "tool_use", "id": "t_" + mid, "name": "Bash", "input": {"command": text}}
             if tool else {"type": "text", "text": text})
    return json.dumps({"type": "assistant", "message": {"id": mid, "usage": _usage(ctx - 1),
                                                          "content": [block]}})


def _slug_dir(tmp_path, cwd):
    root = tmp_path / "projects"
    slug = re.sub(r"[/.]", "-", str(cwd))
    (root / slug).mkdir(parents=True)
    return root, root / slug


def _set_mtime(path, t):
    os.utime(path, (t, t))


def test_current_picks_newest_top_level_transcript_and_ignores_subagents(tmp_path):
    """SC1 + SC2. M1 (oldest) and M2 (include subagents/) turn this RED."""
    cwd = tmp_path / "work.dir" / "wt"
    cwd.mkdir(parents=True)
    root, slug = _slug_dir(tmp_path, cwd)
    (slug / "a.jsonl").write_text(_call("m1", 100000) + "\n")
    (slug / "b.jsonl").write_text(_call("m2", 100000) + "\n")
    (slug / "b").mkdir()
    (slug / "b" / "subagents").mkdir()
    (slug / "b" / "subagents" / "agent-z.jsonl").write_text(_call("m3", 100000) + "\n")
    _set_mtime(slug / "a.jsonl", 1000)
    _set_mtime(slug / "b.jsonl", 2000)
    _set_mtime(slug / "b" / "subagents" / "agent-z.jsonl", 3000)
    data = run_json("--current", "--cwd", cwd, "--projects-dir", root)
    assert data["session"]["transcript"] == "b.jsonl"


def test_current_missing_slug_dir_exits_2_naming_the_path(tmp_path):
    """SC3."""
    root = tmp_path / "projects"
    root.mkdir()
    result = run("--current", "--cwd", tmp_path / "nowhere", "--projects-dir", root)
    assert result.returncode == 2
    assert str(root / re.sub(r"[/.]", "-", str(tmp_path / "nowhere"))) in result.stderr


def test_current_reports_context_now_peak_and_over_150k(tmp_path):
    """SC4: contexts 100k, 160k, 170k -> now 170k, peak 170k, over-150k 2."""
    cwd = tmp_path / "w"
    cwd.mkdir()
    root, slug = _slug_dir(tmp_path, cwd)
    (slug / "s.jsonl").write_text("\n".join(
        [_call("m1", 100000), _call("m2", 160000), _call("m3", 170000)]) + "\n")
    s = run_json("--current", "--cwd", cwd, "--projects-dir", root)["session"]
    assert (s["context_now"], s["context_peak"], s["calls_over_150k"]) == (170000, 170000, 2)
    assert len(s["top_content_kinds"]) <= 3


def test_current_peak_can_exceed_now(tmp_path):
    cwd = tmp_path / "w"
    cwd.mkdir()
    root, slug = _slug_dir(tmp_path, cwd)
    (slug / "s.jsonl").write_text("\n".join([_call("m1", 200000), _call("m2", 50000)]) + "\n")
    s = run_json("--current", "--cwd", cwd, "--projects-dir", root)["session"]
    assert (s["context_now"], s["context_peak"], s["calls_over_150k"]) == (50000, 200000, 1)


def test_current_never_prints_transcript_content(tmp_path):
    """SC5: extends T124 SC5 to --current."""
    cwd = tmp_path / "w"
    cwd.mkdir()
    root, slug = _slug_dir(tmp_path, cwd)
    (slug / "s.jsonl").write_text(_call("m1", 1000, SENTINEL, tool=True) + "\n"
                                  + _call("m2", 2000, SENTINEL) + "\n")
    for extra in ([], ["--json"]):
        result = run("--current", "--cwd", cwd, "--projects-dir", root, *extra)
        assert result.returncode == 0, result.stderr
        assert SENTINEL not in result.stdout + result.stderr


def test_current_rejects_combination_with_session(tmp_path):
    assert run("--current", "--session", tmp_path / "x.jsonl").returncode == 2


def test_top_content_kinds_are_ranked_by_share_not_first_seen(tmp_path):
    """T126 Stage 4 finding: the top kinds were the first three kinds seen, not the largest."""
    usage = {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 1000,
             "cache_creation_input_tokens": 1000}
    def call(i, content):
        return {"type": "assistant", "message": {"id": f"m{i}", "usage": usage, "content": content}}
    lines = [
        {"type": "user", "message": {"role": "user", "content": "hi"}},                   # small, first seen
        call(1, [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}]),
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "x" * 50_000}]}},  # large, seen later
        call(2, []), call(3, []),
    ]
    path = tmp_path / "s.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    top = run_json("--session", path)["session"]["top_content_kinds"]
    assert top[0]["kind"] == "tool_result:Bash"
    assert [k["share_pct"] for k in top] == sorted((k["share_pct"] for k in top), reverse=True)


# --- T128 — a Bash command that writes is the agent's first edit -------------------

STATE_WRITE = "printf '%s\\n' T900 > /abs/repo/.claude/hooks/.state/active_task"


def _bash_spawn(tmp_path, commands, tools=None):
    """A T900 spawn issuing one call per entry; call 0's Bash result is 700 chars, later 350."""
    lines = [json.dumps({"type": "user", "message": {"content": "Read TASK_GUIDE_T900 now"}})]
    for i, command in enumerate(commands):
        name, payload = (tools or {}).get(i, ("Bash", {"command": command}))
        lines.append(json.dumps({"type": "assistant", "message": {
            "id": "m%d" % i, "usage": _usage(1000 * (i + 1)),
            "content": [{"type": "tool_use", "id": "t%d" % i, "name": name, "input": payload}]}}))
        lines.append(json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t%d" % i,
             "content": "r" * (700 if i == 0 else 350)}]}}))
    directory = tmp_path / "proj"
    directory.mkdir()
    (directory / "agent-w1.jsonl").write_text("\n".join(lines) + "\n")
    return run_json("--projects-dir", tmp_path, "--task", "T900")["spawns"]["items"][0]


def test_t128_sc1_bash_write_is_the_first_edit(tmp_path):
    row = _bash_spawn(tmp_path, ["cat f", "cat > x.py <<'EOF'\nprint(1)\nEOF", "cat x.py"])
    assert row["edited"] is True and row["edit_via"] == "bash"
    assert row["calls_before_edit"] == 1
    assert row["pre_edit_tokens"] == 200      # only the first result (700 chars / 3.5)


WRITES = [
    "echo hi > out.txt", "echo hi >> out.txt", "echo hi &> out.txt", "ls | tee out.txt",
    "sed -i 's/a/b/' f", "cp a b", "mv a b", "rm -f a", "touch a", "m" "kdir -p d",
    "git commit -m msg", "git apply p.diff", "git mv a b", "git rm a", "patch -p1 < p.diff",
    "python3 - <<'EOF'\np = 'f'\nopen(p, 'w').write('x')\nEOF",
    "python3 -c \"open('f', 'a').write('x')\"",
    "python3 - <<'EOF'\nfrom pathlib import Path\nPath('f').write" "_text('x')\nEOF",
    "cd d && git status; echo x > f",
]


@pytest.mark.parametrize("command", WRITES)
def test_t128_sc2_each_write_form_is_detected(tmp_path, command):
    row = _bash_spawn(tmp_path, ["cat f", command])
    assert row["edit_via"] == "bash", command
    assert row["calls_before_edit"] == 1


NOT_WRITES = [
    STATE_WRITE, "echo x > /dev/null", "cmd 2>&1", "cmd >&2", "cmd &>/dev/null",
    "grep x f > /tmp/out", "cmd 2>/dev/null", "mkdir -p /abs/repo/.claude/hooks/.state",
    "grep '>' f", 'echo "a > b"', "git log", "git status",
    "python3 -c \"print(open('f').read())\"", "ls | tee /dev/null",
]


@pytest.mark.parametrize("command", NOT_WRITES)
def test_t128_sc3_sc4_state_and_read_only_look_alikes_are_not_edits(tmp_path, command):
    row = _bash_spawn(tmp_path, ["cat f", command, "cat g"])
    assert row["edited"] is False and row["edit_via"] is None, command


def test_t128_sc5_edit_tool_first_wins_over_a_later_bash_write(tmp_path):
    row = _bash_spawn(tmp_path, ["cat f", "ignored", "echo x > f"],
                      tools={1: ("Edit", {"file_path": "f"})})
    assert row["edit_via"] == "tool" and row["calls_before_edit"] == 1


def test_t128_sc5_bash_write_first_wins_over_a_later_edit_tool(tmp_path):
    row = _bash_spawn(tmp_path, ["cat f", "echo x > f", "ignored"],
                      tools={2: ("Edit", {"file_path": "f"})})
    assert row["edit_via"] == "bash" and row["calls_before_edit"] == 1


def test_t128_sc6_sentinel_in_a_bash_write_is_never_printed(tmp_path):
    _bash_spawn(tmp_path, ["cat f", "echo %s > out.txt" % SENTINEL])
    for extra in ([], ["--json"]):
        result = run("--projects-dir", tmp_path, "--task", "T900", *extra)
        assert result.returncode == 0, result.stderr
        assert SENTINEL not in result.stdout + result.stderr
        assert "T900" in result.stdout
