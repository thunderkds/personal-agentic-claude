"""T180 — auto mode: with the user's literal `[auto]` tag, either track runs to its end without a
question to the user, and ends with a final report of every decision.

AC 1 — `docs/claude-md/tracks.md` `## Auto mode`: the D1 tag and track line, D2, one table row per
       user stop with its auto rule, the D5 stops that stay, the D6 never-list. `AGENTS.md` points
       at it inside the existing `## Tracks` paragraph (no new line: AGENTS.md is at its 196 cap).
AC 2 — `templates/TASK_REVIEW_template.md` has an optional `## Auto decisions` section in the D4
       shape; `templates/MINIMAL_LOG_template.md` gains the same lines. The marker `Mode: auto` is
       one literal line a hook can read (T182 keys on it); a copied template is not marked.
AC 3 — `skills/resolve-question/SKILL.md` says where auto mode comes from, fixes T179's two P2s
       (step 1 `Done when:`; how the Debate cap is counted), and stays <= 8192 bytes. Every place in
       `docs/claude-md/pipeline-stages.md` that waits for the user names its auto rule.
AC 4 — the merge gate (`pre_bash_block_unsafe_merge.py`, unchanged) still blocks a merge whose
       `verify` row says only `auto-checked, not /verify`.
AC 5 — glossary: Auto mode, Final report.

Run with: python3 -m pytest tests/test_auto_mode.py -v
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"

# The one definition of who may change the merge gate, beside the other suite that asserts it.
sys.path.insert(0, str(HOOKS / "tests"))
import merge_gate_guard  # noqa: E402

MERGE_GATE = HOOKS / "pre_bash_block_unsafe_merge.py"
AGENTS_MD = ROOT / "AGENTS.md"
TRACKS_MD = ROOT / "docs" / "claude-md" / "tracks.md"
PIPELINE_MD = ROOT / "docs" / "claude-md" / "pipeline-stages.md"
REVIEW_TEMPLATE = ROOT / "templates" / "TASK_REVIEW_template.md"
MINIMAL_TEMPLATE = ROOT / "templates" / "MINIMAL_LOG_template.md"
SKILL = ROOT / "skills" / "resolve-question" / "SKILL.md"
SPEC = ROOT / "PROJECT_SPEC.md"

# The one literal string a hook reads (D1). T182's hook keys on it; change it only with T182.
AUTO_TAG = "[auto]"
MODE_MARKER = "Mode: auto"
FLAG = "⚠ decided for you — please review"
AUTO_CHECKED = "auto-checked, not /verify"
TRACK_LINE_TAIL = "I won't stop for questions; every decision goes in the final report."
BASE_REF = "e50fe56"  # T180's branch base: the merge gate as T178/T179 left it


def _read(path: Path) -> str:
    assert path.exists(), f"{path.relative_to(ROOT)} does not exist"
    return path.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _section(text: str, heading: str) -> str:
    """The body under `## <heading>`, up to the next `## ` heading (### subsections included)."""
    m = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"no '## {heading}' section"
    return m.group(1)


def _subsection(text: str, heading: str) -> str:
    m = re.search(rf"^### {re.escape(heading)}[^\n]*\n(.*?)(?=^##+ |\Z)", text, re.M | re.S)
    assert m, f"no '### {heading}' subsection"
    return m.group(1)


def _auto() -> str:
    return _section(_read(TRACKS_MD), "Auto mode")


def is_auto_request(request: str) -> bool:
    """D1, as the doc states it: only the literal bracketed tag, exactly as written."""
    return AUTO_TAG in request


def has_auto_marker(text: str) -> bool:
    """Reference reader of the marker (the shape T182's hook keys on): outside any HTML comment,
    the first non-blank line under `## Auto decisions` (extended) or under a Decision record's
    `## <ID> — ` heading (minimal) is exactly `Mode: auto`."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for m in re.finditer(r"^## (?:Auto decisions|\S+ — [^\n]+)$\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        lines = [l for l in m.group(1).splitlines() if l.strip()]
        if lines and lines[0] == MODE_MARKER:
            return True
    return False


# ── AC 1 — tracks.md `## Auto mode` ───────────────────────────────────────────────────────
def test_ac1_tag_is_the_literal_bracketed_auto_with_the_d1_example():
    body = _norm(_auto())
    assert "`[auto]`" in body
    assert "`move the data from CSV to JSON [auto]`" in body
    assert re.search(r"[Oo]nly the bracketed tag counts, exactly as written", body)
    assert re.search(r"bare word \*auto\*[^.]*auto-save[^.]*not the tag", body), body


@pytest.mark.parametrize("request_text,auto", [
    ("move the data from CSV to JSON [auto]", True),
    ("[auto] fix the comma bug", True),
    ("add auto-save to the editor", False),
    ("run this in auto mode", False),
    ("auto", False),
    ("fix the bug [Auto]", False),
    ("fix the bug (auto)", False),
])
def test_ac1_only_the_literal_tag_turns_auto_mode_on(request_text, auto):
    """Success Criteria 1 and 2: `[auto]` turns it on; "add auto-save" without the tag does not."""
    assert is_auto_request(request_text) is auto


def test_ac1_track_line_examples_for_both_tracks():
    body = _auto()
    for track in ("extended", "minimal"):
        line = f"Track: {track} · auto — <reasons>. {TRACK_LINE_TAIL}"
        assert re.search(rf"^{re.escape(line)}$", body, re.M), f"no literal track line: {line}"
    assert re.search(r"[Ww]ithout the tag, both tracks behave as", _norm(body))


def test_ac1_marker_is_one_documented_literal_line():
    body = _norm(_auto())
    assert f"`{MODE_MARKER}`" in body
    assert "T182" in body and "hook" in body
    assert "exactly as written, alone on its line" in body
    assert "HTML comment" in body, "the doc must say a copied template is not marked"


def test_ac1_d2_minimal_track_stop_becomes_a_debate_and_record_carries_flags():
    sub = _norm(_subsection(_auto(), "Minimal track in auto mode"))
    # D7: the stop is decided by the task's Risk (Low: no Debate), not always a Debate.
    assert re.search(r"unclear request[^.]*is decided by `### Debate size by Risk`", sub), sub
    assert "Decision record" in sub and "`templates/MINIMAL_LOG_template.md`" in sub
    flow = _norm(_section(_read(TRACKS_MD), "Minimal-track flow"))
    assert re.search(r"[Ii]n auto mode[^.]*Debate", flow), "the one stop must point at auto mode"


def _stop_rows():
    sub = _subsection(_auto(), "Every user stop and its auto rule")
    rows = [l for l in sub.splitlines() if l.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", l)]
    assert len(rows) >= 2, "the stop list is not a table"
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[1:]]


# Every place the agent found where a track waits for the user today (startup step 5). Each key
# must name exactly one table row: one row per stop.
STOP_KEYS = {
    "phase0": r"Phase 0",
    "grill": r"Resolve all flagged items with the user",
    "adr": r"ADR-eligible",
    "brainstorm": r"`brainstorming`",
    "one_time_setup": r"`fewer-permission-prompts`",
    "cli_list": r"lists the CLIs",
    "agent_guide": r"missing agent guide",
    "git_status": r"`git status`",
    "project_spec": r"save or confirm `PROJECT_SPEC\.md`",
    "domain_models": r"domain models",
    "team": r"Approve or request any modifications",
    "breakdown": r"task breakdown",
    "fidelity": r"Requirement Fidelity Gate",
    "spawn_model": r"`craft-spawn-prompt`",
    "blocked": r"`Status: blocked`",
    "pull_moment": r"pull moment 3",
    "finding": r"finding whose fix needs a choice",
    "verify": r"`/verify`",
    "merge": r"merge, Done",
    "compact": r"compact",
    "minimal_unclear": r"[Mm]inimal track: an unclear request",
}


@pytest.mark.parametrize("key", sorted(STOP_KEYS))
def test_ac1_one_row_per_stop(key):
    hits = [r for r in _stop_rows() if re.search(STOP_KEYS[key], r[1])]
    assert len(hits) == 1, f"stop {key!r}: expected one row, found {len(hits)}"
    row = hits[0]
    assert len(row) == 4 and row[2] and row[3], f"row {row[0]} lacks a rule or a log tag"


def test_ac1_table_has_no_row_outside_the_stop_list():
    rows = _stop_rows()
    assert len(rows) == len(STOP_KEYS), [r[1] for r in rows]
    assert [r[0] for r in rows] == [str(i) for i in range(1, len(rows) + 1)]


def _row(key):
    return next(r for r in _stop_rows() if re.search(STOP_KEYS[key], r[1]))


def test_ac1_d3_rules_from_the_guide():
    assert re.search(r"recommended direction[^.]*alternatives", _row("brainstorm")[2])
    grill = _row("grill")[2]
    assert "Citations" in grill and "Choice question" in grill and "Debate" in grill
    assert "`auto (Supervisor)`" in _row("fidelity")[2]
    assert "Debate" in _row("finding")[2]
    assert "Debate" in _row("blocked")[2]
    assert "Debate" in _row("minimal_unclear")[2]


def test_ac1_d3_empty_cli_model_table_rule():
    cli = _row("cli_list")
    assert "`## CLI Model Table`" in cli[2] and "row 14" in cli[2]
    spawn = _row("spawn_model")
    assert spawn[0] == "14"
    assert "no `## CLI Model Table` row" in spawn[1] and "empty cell" in spawn[1]
    assert "the CLI that runs this session" in spawn[2]
    assert "the model this session runs as" in spawn[2]
    assert "Never invent another CLI's model name" in spawn[2]
    assert "`SAFER OPTION`" in spawn[3] and "⚠" in spawn[3]


def test_ac1_d3_stage5_is_an_auto_check_never_verify():
    rule = _row("verify")[2]
    assert f"`{AUTO_CHECKED}`" in rule
    assert re.search(r"`verify` Evidence row stays unchecked", rule)
    assert "T182" in rule and "or the user does" in rule
    assert re.search(r"[Nn]ever in auto mode", _row("merge")[2])
    assert "Ready for Review" in _row("merge")[2]


def test_ac1_every_debate_safer_option_and_taste_row_is_flagged():
    for row in _stop_rows():
        tag = row[3]
        if "DEBATED" in tag or "SAFER OPTION" in tag or "taste" in tag:
            assert "⚠" in tag, f"row {row[0]} must carry the review flag: {tag}"
    legend = _norm(_subsection(_auto(), "Every user stop and its auto rule"))
    assert f"`{FLAG}`" in legend


D5_STOPS = (
    "a safety-hook block",
    "an action that deletes or overwrites data with no backup",
    "the 4th Debate in a task",
    "a paid action outside the task's own work",
    "a login or secret the Supervisor does not have",
    "the same sub-agent hitting the step limit twice",
)


def test_ac1_d5_stops_that_stay():
    sub = _norm(_subsection(_auto(), "Stops that stay"))
    for stop in D5_STOPS:
        assert stop in sub, stop
    assert re.search(r"one message that says why", sub)
    assert "`Paused:`" in sub and "final report" in sub


# T189 D7: `### Never in auto mode` names only what stays the user's in every mode — merge, push and
# `ship`; the memory pass and Done moved to the automatic side. The Supervisor's own limits (D6 of
# T180) are unchanged and now live in `### The Supervisor never`.
D6_NEVER = (r"^- merge;$", r"^- push;$", r"^- `ship`\.$")
D6_SUPERVISOR_NEVER = (r"runs `/verify` or writes its `verify` Evidence row", r"moves a task to Done",
                       r"moves a task down a track")


def test_ac1_d6_never_in_auto_mode():
    raw = _subsection(_auto(), "Never in auto mode")
    for item in D6_NEVER:
        assert re.search(item, raw, re.M), item
    assert [l for l in raw.splitlines() if l.startswith("- ")] == ["- merge;", "- push;", "- `ship`."]
    sub = _norm(_subsection(_auto(), "The Supervisor never"))
    for item in D6_SUPERVISOR_NEVER:
        assert re.search(item, sub), item
    assert "only T182's hook writes it" in sub
    assert re.search(r"merge gate cannot tell who wrote the row", sub)


def test_ac1_edge_cases():
    sub = _norm(_subsection(_auto(), "Edge cases"))
    assert re.search(r"ask me before[^.]*explicit ask wins", sub)
    assert re.search(r"moves up[^.]*stays in auto mode[^.]*when it moved", sub)
    assert re.search(r"usage limit[^.]*clean point[^.]*report so far", sub)
    assert re.search(r"[Tt]wo `\[auto\]` tasks[^.]*own report[^.]*Debate count", sub)


def _agents_tracks_paragraph() -> str:
    lines = _read(AGENTS_MD).splitlines()
    i = lines.index("## Tracks")
    return lines[i + 1]


def test_ac1_agents_md_pointer_sits_in_the_tracks_paragraph():
    para = _agents_tracks_paragraph()
    assert "`[auto]`" in para and "**auto mode**" in para
    assert "`## Auto mode`" in para and "`docs/claude-md/tracks.md`" in para
    assert f"`Track: <track> · auto — <reasons>. {TRACK_LINE_TAIL}`" in para
    assert re.search(r"bare word \*auto\* is not the tag", para)
    assert re.search(r"never merges, pushes, moves a task to Done or runs `/verify`", para)
    # D7 / AC 6 re-run 1 (task 5 wrote its report only in chat): the file is the report.
    assert "final report, written to its file before the run ends (the chat message is a copy)" in para


def test_ac1_agents_md_gains_no_line_and_stays_under_the_byte_cap():
    lines = _read(AGENTS_MD).splitlines()
    i = lines.index("## Tracks")
    assert lines[i + 2] == "", "## Tracks must stay one paragraph (AGENTS.md has 0 lines of headroom)"
    assert len(lines) <= 196
    assert len(AGENTS_MD.read_bytes()) <= 32768


# ── AC 2 — the final report in both templates ─────────────────────────────────────────────
D4_LINES = (
    MODE_MARKER,
    "— RULE: <the rule>",
    '— FACT: <path>:<line> "<quoted text>"',
    f"— DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) {FLAG}",
    f"— SAFER OPTION: <why> {FLAG}",
    "Paused:",
    "auto verify: running (T182)",
    "/verify (yours)",
    AUTO_CHECKED,
)


def _review_auto_block() -> str:
    m = re.search(r"<!--(.*?## Auto decisions.*?)-->", _read(REVIEW_TEMPLATE), re.S)
    assert m, "no commented `## Auto decisions` shape in the review template"
    return m.group(1)


@pytest.mark.parametrize("line", D4_LINES)
def test_ac2_review_template_has_the_d4_shape(line):
    assert line in _review_auto_block(), line


def test_ac2_review_template_report_lines_in_order():
    block = _review_auto_block()
    order = ["## Auto decisions", MODE_MARKER, "1. ", "Checks:", "Not done: merge (yours)"]
    at = 0
    for needle in order:
        hit = block.find(needle, at)
        assert hit != -1, f"{needle!r} missing or out of order"
        at = hit
    note = _norm(block)
    assert "Optional" in note and "same block is the Supervisor's final chat message" in note


def test_ac2_review_template_sections_still_resolve():
    """The commented block sits before `## Evidence`, so the merge gate and the delivery report
    slice Evidence and Demonstration exactly as before."""
    sys.path.insert(0, str(HOOKS / "lib"))
    from guide_sections import slice_section
    text = _read(REVIEW_TEMPLATE)
    evidence = slice_section(text, "Evidence")
    assert "| verify |" in evidence and "Auto decisions" not in evidence
    demo = slice_section(text, "Demonstration")
    assert "**WITNESS**" in demo and "<!--" not in demo and "Auto decisions" not in demo


@pytest.mark.parametrize("line", D4_LINES)
def test_ac2_minimal_template_gains_the_same_lines(line):
    assert line in _read(MINIMAL_TEMPLATE), line


def test_ac2_minimal_template_keeps_the_t178_record_first():
    text = _read(MINIMAL_TEMPLATE)
    plain = text.find("## <ID> — <title> · <track>")
    auto = text.find("## <ID> — <title> · minimal\nMode: auto")
    assert -1 < plain < auto, "the auto-mode record shape follows the T178 shape"


def test_ac2_a_copied_template_is_not_marked():
    assert not has_auto_marker(_read(REVIEW_TEMPLATE))
    assert not has_auto_marker(_read(MINIMAL_TEMPLATE))


def test_ac2_a_filled_report_is_marked_and_a_lookalike_is_not():
    filled = (_read(REVIEW_TEMPLATE).split("<!--", 1)[0]
              + f"## Auto decisions\n\n{MODE_MARKER}\n1. kept recurring.csv — SAFER OPTION: "
              f"it keeps all data {FLAG}\n\n## Evidence\n")
    assert has_auto_marker(filled)
    record = f"## T901 — Sort by date · minimal\n{MODE_MARKER}\n**Asked:** \"sort [auto]\"\n"
    assert has_auto_marker(record)
    for lookalike in ("## Auto decisions\n\nmode: auto\n", "## Auto decisions\n\nMode: auto.\n",
                      "## Auto decisions\n\n1. x\nMode: auto\n",
                      "## T901 — x · minimal\n**Asked:** \"Mode: auto\"\n"):
        assert not has_auto_marker(lookalike), lookalike


# ── AC 3 — resolve-question and the pipeline doc ──────────────────────────────────────────
def _skill_step(n: int) -> str:
    text = _read(SKILL)
    m = re.search(rf"^#### {n}\. [^\n]*\n(.*?)(?=^#### |\Z)", text, re.M | re.S)
    assert m, f"no step {n}"
    return m.group(1)


def test_ac3_skill_says_where_auto_mode_comes_from():
    text = _norm(_read(SKILL))
    assert re.search(r"\*\*Auto mode\*\* = [^.]*`\[auto\]`", text), "no Auto mode term"
    assert "`docs/claude-md/tracks.md`" in text


def test_ac3_p2a_step1_routing_line_before_done_when_with_the_auto_exception():
    step = _skill_step(1)
    route = step.find("Only in auto mode, a Choice question goes to the Debate step.")
    done = step.find("Done when:")
    assert -1 < route < done, "the auto routing line must come before `Done when:`"
    done_when = _norm(step[done:])
    assert re.search(r"sent to the user \(auto mode: to the Debate step\)", done_when), done_when


def test_ac3_p2b_debate_cap_says_how_it_is_counted():
    text = _read(SKILL)
    cap = _norm(re.search(r"\*\*Cap\.\*\*(.*?)(?=\n\n)", text, re.S).group(1))
    assert "At most 3 Debates per task" in cap
    assert re.search(r"[Cc]ount the `DEBATE` lines under the guide's `## Questions Log`", cap), cap
    assert re.search(r"`task=none`[^.]*per session", cap), cap


def test_ac3_skill_stays_under_the_codex_cap():
    assert SKILL.stat().st_size <= 8192


def _chunks(text: str):
    """Paragraph-sized chunks: a list item or a paragraph, split on blank lines."""
    return [c for c in re.split(r"\n\s*\n", text) if c.strip()]


# A chunk of pipeline-stages.md that waits for the user today matches one of these.
USER_STOP = re.compile(
    r"[Aa]sk the user|[Tt]he user must|user approv|explicit user approval|[Pp]lease (?:run|list)|"
    r"Approve or request|Are they correct|Guide the user|STOPs and asks|stops and asks|"
    r"Resolve all flagged items with the user|Address all findings|"
    r'skill: "verify"|Merge the worktree|skill: "ship"', re.S)


def test_ac3_every_pipeline_stop_names_its_auto_rule():
    chunks = [c for c in _chunks(_read(PIPELINE_MD)) if USER_STOP.search(c)]
    assert len(chunks) >= 14, f"stop scan found only {len(chunks)} chunks"
    missing = [c.strip().splitlines()[0][:90] for c in chunks if not re.search(r"[Aa]uto mode", c)]
    assert not missing, f"stops with no auto-mode rule: {missing}"


def test_ac3_pipeline_head_points_at_the_auto_mode_table():
    head = _norm(_read(PIPELINE_MD).split("## Stage 0.5", 1)[0])
    assert re.search(r"[Aa]uto mode[^.]*`\[auto\]`", head)
    assert "`## Auto mode`" in head and "`docs/claude-md/tracks.md`" in head


def test_ac3_pipeline_cli_model_table_auto_rule():
    stage1 = _section(_read(PIPELINE_MD), "Stage 1: Environment")
    item2 = next(c for c in _chunks(stage1) if "Multi-CLI Authentication" in c)
    norm = _norm(item2)
    assert re.search(r"[Ii]n auto mode[^.]*CLI that runs this session[^.]*model this session runs as",
                     norm), norm
    assert "`SAFER OPTION`" in norm


# ── AC 4 — the merge gate still holds ─────────────────────────────────────────────────────
ROW = "- [ ] **T951** — Move the data from CSV to JSON | common-infrastructure | C3 | Risk: High | P1"


def _review_file(verify_notes: str, verify_result: str = "☐ pass / ☐ fail / ☐ N/A",
                 auto_section: str = "") -> str:
    return (f"# TASK_REVIEW — T951: Move the data\n\n{auto_section}"
            "## Evidence\n\n| Check | Result | Notes / output snippet |\n|---|---|---|\n"
            "| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | tests/x.py |\n"
            f"| verify | {verify_result} | {verify_notes} |\n\n"
            "## Demonstration\n\n**BEFORE**: x\n")


def _project(tmp_path, review_text):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (project / "tasks").mkdir()
    (project / "PROJECT_KANBAN.md").write_text(
        "# Kanban\n\n### Todo\n\n### In Progress\n\n"
        f"### Ready for Review\n{ROW}\n\n### Done\n", encoding="utf-8")
    (project / "tasks" / "TASK_REVIEW_T951.md").write_text(review_text, encoding="utf-8")
    # The Supervisor's own real run is in the trace: the gate's second half is satisfied.
    (project / "memory" / "event-trace").mkdir(parents=True)
    (project / "memory" / "event-trace" / "T951.jsonl").write_text(json.dumps(
        {"tool_name": "Bash", "summary": json.dumps({"command": "python3 -m pytest -q"}),
         "is_error": False}) + "\n")
    return project


def _merge(project):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR")}
    env["CLAUDE_PROJECT_DIR"] = str(project)
    result = subprocess.run(
        [sys.executable, str(project / ".claude" / "hooks" / MERGE_GATE.name)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git merge feat/t951"}}),
        capture_output=True, text=True, cwd=project, env=env, timeout=60)
    return result, (json.loads(result.stdout) if result.stdout.strip() else {})


@pytest.mark.parametrize("result_cell", ["☐ pass / ☐ fail / ☐ N/A", "☑ N/A", "auto"])
def test_ac4_gate_blocks_a_verify_row_that_says_only_auto_checked(tmp_path, result_cell):
    """Success Criterion 3: `verify` row = `auto-checked, not /verify` -> merge still blocked."""
    project = _project(tmp_path, _review_file(AUTO_CHECKED, result_cell))
    _, out = _merge(project)
    assert out.get("decision") == "block", out
    assert "T951 (no evidence row)" in out["reason"]


def test_ac4_gate_ignores_a_passing_auto_check_in_the_final_report(tmp_path):
    """The final report's `Checks:` line says the real run passed; it is not Evidence."""
    report = (f"## Auto decisions\n\n{MODE_MARKER}\n1. kept recurring.csv — SAFER OPTION: keeps all "
              f"data {FLAG}\nChecks: tests pass; real run `tally list` — pass ({AUTO_CHECKED})\n"
              "Not done: merge (yours); /verify (yours)\n\n")
    project = _project(tmp_path, _review_file("[what was observed]", auto_section=report))
    _, out = _merge(project)
    assert out.get("decision") == "block" and "T951 (no evidence row)" in out["reason"]


def test_ac4_control_a_real_verify_row_passes(tmp_path):
    """Positive control: same project, the row filled from a real `/verify` run -> no block. So the
    blocks above come from the row's text, not from a broken fixture."""
    project = _project(tmp_path, _review_file("user ran /verify T951 — pass", "☑ pass"))
    result, out = _merge(project)
    assert result.returncode == 0 and out == {}, out


def test_ac4_merge_gate_file_is_unchanged():
    """T180 AC 4: the gate is a Must-NOT-touch file for this task. The one definition of who may
    touch it is `.claude/hooks/tests/merge_gate_guard.py` — an allowlist of task IDs, each owning a
    named rule in the gate (T182, then T188 for the same rule on a Decision record)."""
    problems = merge_gate_guard.unauthorised_gate_commits(
        ROOT, BASE_REF, str(MERGE_GATE.relative_to(ROOT)))
    assert problems == [], (
        "pre_bash_block_unsafe_merge.py may only be changed by a task on "
        f"merge_gate_guard.AUTHORISED_TASKS ({', '.join(merge_gate_guard.AUTHORISED_TASKS)}): "
        + "; ".join(problems))


# ── AC 5 — glossary ───────────────────────────────────────────────────────────────────────
def _glossary_row(term: str) -> str:
    rows = [l for l in _read(SPEC).splitlines() if l.startswith(f"| {term} |")]
    assert len(rows) == 1, f"expected one glossary row for {term!r}, found {len(rows)}"
    return rows[0]


def test_ac5_glossary_auto_mode():
    row = _glossary_row("Auto mode")
    assert "`[auto]`" in row and f"`{MODE_MARKER}`" in row and "T180" in row
    assert "Not the installer's Update auto-approve" in row


def test_ac5_glossary_final_report():
    row = _glossary_row("Final report")
    assert "`## Auto decisions`" in row and "Decision record" in row
    assert "Not the Delivery Report" in row and "`delivery-report`" in row


def test_ac5_terms_follow_the_t179_block():
    lines = _read(SPEC).splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("| Safer option |"))
    assert lines[i + 1].startswith("| Auto mode |") and lines[i + 2].startswith("| Final report |")


# ── AC 6 fix — `DEBATED` only when Advocates ran ─────────────────────────────────────────
# AC 6 live check: task 4 (minimal) and task 5 (extended) wrote `DEBATED:` lines while the event
# trace held no Advocate `Agent` call. Causes: the minimal track said "no sub-agent" with no
# exception, and nothing tied the `DEBATED` label to Advocates that actually ran.
ADVOCATE_RULE = re.compile(r"`DEBATED`[^.]*only when ≥2 Advocate `Agent` calls ran for that question")
NO_ADVOCATE_RULE = re.compile(r"no Advocates is labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`")


def test_ac6fix_minimal_flow_allows_the_advocates_in_auto_mode():
    flow = _norm(_section(_read(TRACKS_MD), "Minimal-track flow"))
    assert re.search(r"[Nn]o task guide, no sub-agent, no Stage 4 skills", flow), "T178 pin"
    assert re.search(r"[Ii]n auto mode[^.]*read-only `Explore` Advocates[^.]*one exception", flow), flow


def test_d7_minimal_track_decides_by_risk():
    """D7 supersedes the AC 6 fix's "Advocates required on the minimal track": a minimal-track task
    is Risk Low by the track rule, so the Supervisor decides and logs, with no Advocates required."""
    sub = _norm(_subsection(_auto(), "Minimal track in auto mode"))
    assert re.search(r"Risk Low[^.]*decides[^.]*no Advocates are required", sub), sub
    assert re.search(r"Advocates[^.]*one exception to the track's no-sub-agent rule", sub), sub
    assert "`### Debate size by Risk`" in sub
    row = _row("minimal_unclear")
    assert "Risk Low" in row[2] and "Debate size by Risk" in row[2] and "decides" in row[2]
    assert "`RULE`" in row[3] and "⚠" in row[3]


def test_ac6fix_final_report_ties_debated_to_advocates_that_ran():
    sub = _norm(_subsection(_auto(), "Final report"))
    assert ADVOCATE_RULE.search(sub), sub
    assert re.search(r"naming each Advocate's option", sub), sub
    assert NO_ADVOCATE_RULE.search(sub), sub
    assert "`DEBATED: <who argued what>`" not in sub, "the old unconditioned shape must go"


@pytest.mark.parametrize("template", [REVIEW_TEMPLATE, MINIMAL_TEMPLATE], ids=["review", "minimal"])
def test_ac6fix_templates_tie_debated_to_advocates_that_ran(template):
    text = _norm(_read(template))
    assert ADVOCATE_RULE.search(text), template.name
    assert NO_ADVOCATE_RULE.search(text), template.name
    assert "(<who argued what>)" not in text, "the old unconditioned shape must go"


def test_ac6fix_skill_debate_step_says_no_advocates_is_no_debate():
    text = _read(SKILL)
    m = re.search(r"^#### Debate \(auto mode only\)$(.*?)(?=^#### |^---$|\Z)", text, re.M | re.S)
    body = _norm(m.group(1))
    assert re.search(r"[Ff]ewer than 2 Advocate calls ran: not a Debate; do not log it as one", body), body
    assert SKILL.stat().st_size <= 8192


# ── D7 — Debate size by the task's Risk (user, 2026-10-27, after AC 6 re-run 1) ───────────
def _d7_rows():
    sub = _subsection(_auto(), "Debate size by Risk")
    rows = [l for l in sub.splitlines() if l.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", l)]
    assert len(rows) == 4, "D7 is a table: a header row and Low / Medium / High"
    return {r.strip("|").split("|")[0].strip(): [c.strip() for c in r.strip("|").split("|")]
            for r in rows[1:]}


def test_d7_table_risk_to_who_decides_and_advocates():
    rows = _d7_rows()
    assert list(rows) == ["Low", "Medium", "High"]
    low, med, high = rows["Low"], rows["Medium"], rows["High"]
    assert "Supervisor decides" in low[1] and all(t in low[1] for t in ("`RULE`", "`FACT`", "`SAFER OPTION`"))
    assert "reason" in low[1] and low[2].startswith("none")
    assert "Debate" in med[1] and med[2].startswith("exactly 2") and "required" in med[2]
    assert "Debate" in high[1] and high[2].startswith("exactly 3") and "required" in high[2]
    assert "smallest safe thing" in high[2]


def test_d7_scope_supersedes_t179_count_only_in_auto_mode():
    sub = _norm(_subsection(_auto(), "Debate size by Risk"))
    assert "every decision that would have been a question to the user" in sub
    assert re.search(r"supersedes[^.]*\(\"2, or 3 for 3\+ options or High risk\"\)[^.]*in auto mode", sub), sub
    assert re.search(r"[Oo]utside auto mode, `resolve-question` is unchanged", sub)
    assert re.search(r"[Ee]very decision, at every Risk level, has its log line in the final report", sub)


def test_d7_stop_table_says_debate_follows_the_risk():
    legend = _norm(_subsection(_auto(), "Every user stop and its auto rule"))
    assert re.search(r"\"Debate\" in this table follows `### Debate size by Risk`", legend), legend
    assert re.search(r"Risk Low[^.]*logged `RULE`, `FACT` or `SAFER OPTION`", legend), legend


def test_d7_final_report_goes_in_its_file_before_the_run_ends():
    sub = _norm(_subsection(_auto(), "Final report"))
    assert re.search(r"written to its file before the run ends", sub), sub
    assert re.search(r"does not exist[^.]*create it from `templates/TASK_REVIEW_template\.md`", sub), sub
    assert "The chat message is a copy, not the report." in sub
    assert re.search(r"Stage 4 `code-review` still runs[^.]*not a user stop", sub), sub


def test_d7_pipeline_stage4_still_runs_in_auto_mode():
    stage4 = _norm(_section(_read(PIPELINE_MD), "Stage 4: Review").split("1. **Code Review**")[0])
    assert re.search(r"[Aa]uto mode[^.]*Stage 4 still runs[^.]*not a user stop", stage4), stage4


@pytest.mark.parametrize("template", [REVIEW_TEMPLATE, MINIMAL_TEMPLATE], ids=["review", "minimal"])
def test_d7_templates_say_the_file_is_the_report(template):
    text = _norm(_read(template))
    assert re.search(r"[Ww]rite it to (?:this|its) file before the run ends", text), template.name
    assert "the chat message is a copy, not the report" in text, template.name


def test_d7_skill_debate_size_follows_the_task_risk():
    text = _read(SKILL)
    body = _norm(re.search(r"^#### Debate \(auto mode only\)$(.*?)(?=^#### |^---$|\Z)",
                           text, re.M | re.S).group(1))
    assert re.search(r"By the task's Risk[^.]*Low, none \(decide, log why\); Medium, 2; High, 3", body), body
    assert "smallest safe thing" in body
    assert "3 for 3+ options" not in body, "D7 supersedes T179's count in auto mode"
    assert SKILL.stat().st_size <= 8192


# ── D8 — the label rule, Stage 4 in auto mode, and the auto-mode Stop hook ────────────────
# /verify T180: a Risk High `[auto]` run logged the `recurring.csv` choice as `FACT … ⚠`, ran no
# Advocate, and skipped Stage 4.
FLAGGED_NOT_FACT = re.compile(r"flagged `⚠ decided for you` is a choice, and is never labelled `FACT`")
SAFETY_IS_RULE = re.compile(r"safety action a rule requires[^.]*is `RULE` without the flag")


def test_d8_final_report_label_rules():
    sub = _norm(_subsection(_auto(), "Final report"))
    assert FLAGGED_NOT_FACT.search(sub), sub
    assert SAFETY_IS_RULE.search(sub), sub
    assert re.search(r"At Risk Medium or High, every `⚠` line is `DEBATED` with exactly 2 or 3 "
                     r"Advocates named", sub), sub
    assert re.search(r"Stage 4 `code-review` still runs[^.]*plus `security-review` at Risk Medium or High",
                     sub), sub


@pytest.mark.parametrize("template", [REVIEW_TEMPLATE, MINIMAL_TEMPLATE], ids=["review", "minimal"])
def test_d8_templates_carry_the_label_rules(template):
    text = _norm(_read(template))
    assert FLAGGED_NOT_FACT.search(text), template.name
    assert SAFETY_IS_RULE.search(text), template.name


def test_d8_stop_table_legend_every_flag_is_a_debate_at_medium_or_high():
    legend = _norm(_subsection(_auto(), "Every user stop and its auto rule"))
    assert re.search(r"At Risk Medium or High, every decision flagged `⚠` is a Debate", legend), legend


def test_d8_advocate_spawn_description_starts_with_advocate():
    # T221 supersedes `<option>`: an Advocate gets the question only, so the description names it.
    assert re.search(r'description: "Advocate <n>: <short question>"', _read(SKILL))
    size = _norm(_subsection(_auto(), "Debate size by Risk"))
    assert re.search(r"`description` starts with `Advocate`", size), size


def test_d8_tracks_md_documents_the_stop_hook():
    sub = _norm(_subsection(_auto(), "Auto-mode check (Stop hook)"))
    assert "`.claude/hooks/stop_auto_mode_check.py`" in sub
    for needle in ("`## Auto decisions`", "exactly 2 or 3 Advocates named", "description starting `Advocate`",
                   "`code-review`", "`security-review`", "`stop_hook_active`",
                   "`Paused: auto-mode check failed — <reasons>`", "`_untagged.jsonl`", "fail open"):
        assert needle in sub, needle


def test_d8_pipeline_stage4_names_both_reviews_in_auto_mode():
    stage4 = _norm(_section(_read(PIPELINE_MD), "Stage 4: Review").split("1. **Code Review**")[0])
    assert re.search(r"[Aa]uto mode[^.]*`code-review`, plus `security-review` at Medium/High", stage4), stage4


# ── D9 — cited labels at Risk Medium/High; the hook finds auto tasks from files ───────────
CITED_RULE_TEXT = re.compile(r"At Risk Medium or High, a `RULE:` counts only when it names a written rule")
FACT_CITATION_TEXT = re.compile(r"`FACT:` needs a Citation \(`path:line \"quoted text\"`\)")


def test_d9_final_report_states_the_cited_label_rule_with_examples():
    sub = _norm(_subsection(_auto(), "Final report"))
    assert CITED_RULE_TEXT.search(sub), sub
    assert "`path:line`" in sub and "`path § <heading>`" in sub
    assert "`docs/claude-md/tracks.md` `### <section>`" in sub
    assert FACT_CITATION_TEXT.search(sub), sub
    assert re.search(r"Good: `[^`]*RULE: `docs/claude-md/tracks\.md` `### ", sub), sub
    assert re.search(r"Bad: `[^`]*RULE: Surgical Changes`", sub), sub
    assert re.search(r"Low risk is unchanged", sub)


def test_d9_stop_hook_section_documents_discovery_and_cited_labels():
    sub = _norm(_subsection(_auto(), "Auto-mode check (Stop hook)"))
    assert "`tasks/TASK_REVIEW_*.md`" in sub and "newest" in sub and "`tasks/MINIMAL_LOG.md`" in sub
    assert re.search(r"no `PROJECT_KANBAN\.md`[^.]*still checked", sub), sub
    assert re.search(r"row is in Done", sub) and "`☑ pass`" in sub
    assert re.search(r"uncited `RULE:` or `FACT:`[^.]*counts as a choice", sub), sub
    assert re.search(r"decision number and its label", sub), sub


@pytest.mark.parametrize("template", [REVIEW_TEMPLATE, MINIMAL_TEMPLATE], ids=["review", "minimal"])
def test_d9_templates_carry_the_cited_label_rule_with_examples(template):
    text = _norm(_read(template))
    assert CITED_RULE_TEXT.search(text), template.name
    assert FACT_CITATION_TEXT.search(text), template.name
    assert re.search(r"Good: `[^`]*RULE: `docs/claude-md/tracks\.md` `### ", text), template.name
    assert re.search(r"Bad: `[^`]*RULE: Surgical Changes`", text), template.name


# ── D10 — High risk always debates ────────────────────────────────────────────────────────
def test_d10_tracks_md_says_high_risk_always_debates_one_decision():
    text = _norm(_subsection(_auto(), "Debate size by Risk"))
    assert re.search(r"At Risk High, at least one decision is always debated by 3 Advocates", text), text
    assert re.search(r"biggest effect on the user's data or scope", text), text
    assert re.search(r"[Cc]ited `RULE:` lines do not replace it", text), text
    hook = _norm(_subsection(_auto(), "Auto-mode check (Stop hook)"))
    assert "`Risk High, but no decision was DEBATED with 3 Advocates`" in hook, hook
