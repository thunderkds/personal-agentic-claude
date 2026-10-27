"""T178 — two tracks: the minimal track (small, low-risk work, no process stop, ends with a
Decision record) and the extended track (today's 5-stage pipeline, unchanged).

AC 1 — `docs/claude-md/tracks.md`: the D1 rule as a table (each condition -> extended), the D2
       announcement with both literal examples, the up-only switch, the D4 flow as numbered steps.
AC 2 — `AGENTS.md`: a `## Tracks` section (<= 12 lines) with the short rule and the pointer;
       Hard-Stop Gate 1 scoped to the extended track; <= 200 lines and <= 32,768 bytes.
AC 3 — `templates/MINIMAL_LOG_template.md`: the D5 record with every field; the doc says
       `tasks/MINIMAL_LOG.md` is created on first use from it, newest record first.
AC 4 — `docs/claude-md/pipeline-stages.md`: the 5 stages are the extended track; Gates 2-6 still
       apply to it unchanged; Gate 5 also applies to the minimal track through `Checked:`.
AC 5 — `PROJECT_SPEC.md` glossary: Minimal track, Extended track, Decision record, each with a
       "Not ..." line for its near-synonym.
AC 6 — the four hooks, run as the harness runs them against a temp project, for a task that has
       no guide (only a Decision record). The merge gate must not get weaker.

Run with: python3 -m pytest tests/test_tracks.py -v
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
AGENTS_MD = ROOT / "AGENTS.md"
TRACKS_MD = ROOT / "docs" / "claude-md" / "tracks.md"
PIPELINE_MD = ROOT / "docs" / "claude-md" / "pipeline-stages.md"
TEMPLATE = ROOT / "templates" / "MINIMAL_LOG_template.md"
SPEC = ROOT / "PROJECT_SPEC.md"

GATE2_WORDS = ("refactor", "restructure", "migrate to pattern", "clean architecture",
               "QA suite", "test coverage")
RECORD_FIELDS = ("Asked:", "Decisions:", "Assumed:", "Checked:", "Files:", "Not done:")


def _read(path: Path) -> str:
    assert path.exists(), f"{path.relative_to(ROOT)} does not exist"
    return path.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _section(text: str, heading: str) -> str:
    """The body under the first `## <heading>...` line, up to the next `## ` heading."""
    m = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"no '## {heading}' section"
    return m.group(1)


# ── AC 1 — docs/claude-md/tracks.md ───────────────────────────────────────────────────────
def _rule_rows():
    body = _section(_read(TRACKS_MD), "Track rule")
    rows = [l for l in body.splitlines() if l.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", l)]
    assert len(rows) >= 2, "the track rule is not a table"
    return rows[1:]  # drop the header row


def test_ac1_rule_table_maps_each_d1_condition_to_extended():
    rows = _rule_rows()
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[-1].lower().startswith("extended"), f"rule row does not lead to extended: {row}"
    table = " ".join(rows)
    for needle in ("C2", "Medium", "High", "migrate", "session", "agent", "UI component",
                   *GATE2_WORDS):
        assert needle in table, f"D1 condition {needle!r} missing from the rule table"


def test_ac1_rule_says_any_condition_wins_and_otherwise_minimal():
    body = _norm(_section(_read(TRACKS_MD), "Track rule"))
    assert re.search(r"\bany\b", body, re.I), "the rule must say ANY one condition selects extended"
    assert re.search(r"Otherwise[^.]*\bminimal\b", body), "no 'Otherwise ... minimal' line"


def test_ac1_rule_names_a_risky_file_as_risk():
    """Edge case: a minimal-looking request that touches a migration, auth or a delete is Risk."""
    table = " ".join(_rule_rows()).lower()
    for word in ("migration", "auth", "delete"):
        assert word in table, f"risky-file example {word!r} missing from the rule table"


def test_ac1_announcement_has_both_literal_examples():
    body = _section(_read(TRACKS_MD), "Announcement")
    assert re.search(r"^Track: minimal — \S.+$", body, re.M), "no literal 'Track: minimal — …' line"
    assert re.search(r"^Track: extended — \S.+$", body, re.M), "no literal 'Track: extended — …' line"
    assert re.search(r"before any work", body, re.I)


def test_ac1_switch_is_user_both_ways_supervisor_up_only():
    body = _norm(_section(_read(TRACKS_MD), "Switching track"))
    assert "`full`" in body and "`minimal`" in body, "the user's two switch words are missing"
    assert re.search(r"\bup\b", body) and re.search(r"never moves a task \**down\**", body), (
        "the up-only rule for the Supervisor is missing")
    assert "track set by the user" in body, "a user-set track must be noted in the record"


def _flow_steps():
    body = _section(_read(TRACKS_MD), "Minimal-track flow")
    steps = re.findall(r"^(\d+)\. (.+?)(?=^\d+\. |^\S|\Z)", body, re.M | re.S)
    assert steps, "the minimal-track flow is not a numbered list"
    assert [int(n) for n, _ in steps] == list(range(1, len(steps) + 1)), "steps are not 1..N"
    return [_norm(s) for _, s in steps], _norm(body)


def test_ac1_flow_has_the_d4_steps_in_order():
    steps, _ = _flow_steps()
    wanted = [
        r"task ID.*active-task state",
        r"new branch.*never on `main`",
        r"[Tt]est first",
        r"[Cc]hange",
        r"the way a user would",
        r"Decision record.*`tasks/MINIMAL_LOG\.md`",
        r"board row",
    ]
    at = 0
    for pattern in wanted:
        hit = next((i for i in range(at, len(steps)) if re.search(pattern, steps[i])), None)
        assert hit is not None, f"flow step matching {pattern!r} missing or out of order"
        at = hit + 1


def test_ac1_flow_states_the_one_stop_and_what_it_omits():
    _, body = _flow_steps()
    assert "ask one clear question and stop" in body, "the only stop (unclear request) is missing"
    assert re.search(r"[Nn]o task guide, no sub-agent, no Stage 4 skills", body)
    assert re.search(r"[Mm]erge is never automatic", body)
    # Edge case: a fact about the code is not a stop — the Supervisor reads the code.
    assert re.search(r"fact[^.]*code[^.]*not a stop", body, re.I)


def test_ac1_flow_keeps_gate5_test_and_its_output():
    steps, _ = _flow_steps()
    test_step = next(s for s in steps if re.search(r"[Tt]est first", s))
    assert re.search(r"fails", test_step) and "Gate 5" in test_step


def test_ac1_move_up_when_the_task_grows():
    body = _norm(_read(TRACKS_MD))
    assert re.search(r"more than one file|second session", body)
    assert re.search(r"write the task guide from what (?:was|you) learned", body)


def test_ac1_board_mode_online_keeps_record_local():
    body = _norm(_read(TRACKS_MD))
    assert re.search(r"online[^.]*`tasks/MINIMAL_LOG\.md`", body)
    assert "board_sync.py" in body



# ── AC 8 fix — a change to user data is an extended-track condition of its own ────────────
# AC 8 task 5 ("store expenses as JSON instead of CSV … get rid of the old CSV stuff") ran on the
# minimal track: no Gate-2 word, no "migrate", and the only row that caught it needed a Risk rating
# first. The rule must name the data change itself, in AGENTS.md (read every session) and tracks.md.
DATA_VERBS = ("delete", "move", "rename", "convert")


def _names_a_user_data_change(text: str) -> bool:
    low = text.lower()
    return ("user data" in low and "storage format" in low
            and all(v in low for v in DATA_VERBS))


def test_ac8_tracks_table_has_a_user_data_row_of_its_own():
    rows = [r for r in _rule_rows() if _names_a_user_data_change(r)]
    assert rows, "no rule row names a delete/move/rename/convert of user data or its storage format"
    row = rows[0]
    assert "Risk" not in row, "the data-change row must not depend on a Risk rating"
    assert [c.strip() for c in row.strip("|").split("|")][-1].lower().startswith("extended")


def test_ac8_tracks_table_covers_a_conversion_without_the_word_migrate():
    row = next(r for r in _rule_rows() if _names_a_user_data_change(r))
    assert re.search(r"CSV to JSON", row), "the row needs the format-conversion example"
    assert re.search(r"even (?:when|if) the request (?:does not say|never says) \*migrate\*", row)


def test_ac8_agents_md_short_rule_names_the_user_data_change():
    text = _norm("\n".join(_agents_tracks_section()))
    m = re.search(r"any of: (.+?)\. Otherwise", text)
    assert m, "the short rule has no 'any of: … . Otherwise' list"
    items = [i.strip() for i in m.group(1).split(";")]
    hits = [i for i in items if _names_a_user_data_change(i)]
    assert hits, f"no condition in the short rule names a user-data change: {items}"
    assert "Risk" not in hits[0] and "migrate" in hits[0], (
        "the data-change condition must stand alone and say it holds without *migrate*")


def test_ac8_minimal_track_excludes_a_user_data_change():
    body = _norm(_section(_read(TRACKS_MD), "Track rule"))
    assert re.search(r"Otherwise[^.]*no change to user data", body)


def test_ac8_record_step_requires_every_template_field():
    steps, _ = _flow_steps()
    record = next(s for s in steps if "`tasks/MINIMAL_LOG.md`" in s and "Decision record" in s)
    assert "every field of the template" in record
    for field in ("Asked:", "Decisions:", "Checked:", "Files:", "Not done:"):
        assert f"`{field}`" in record, f"step 6 does not name {field!r}"


def test_ac8_backup_never_in_tmp():
    _, body = _flow_steps()
    assert re.search(r"backup[^.]*inside the project or in a path the user named[^.]*never in `/tmp`",
                     body, re.I)

# ── AC 2 — AGENTS.md ──────────────────────────────────────────────────────────────────────
def _agents_tracks_section():
    lines = _read(AGENTS_MD).splitlines()
    starts = [i for i, l in enumerate(lines) if l.strip() == "## Tracks"]
    assert len(starts) == 1, f"expected one '## Tracks' heading in AGENTS.md, found {len(starts)}"
    s = starts[0]
    e = next((i for i in range(s + 1, len(lines))
              if lines[i].startswith("## ") or lines[i].strip() == "---"), len(lines))
    return lines[s:e]


def test_ac2_tracks_section_is_short_and_points_at_the_doc():
    section = _agents_tracks_section()
    while section and not section[-1].strip():
        section.pop()
    assert len(section) <= 12, f"## Tracks is {len(section)} lines, cap is 12"
    text = _norm("\n".join(section))
    assert "`docs/claude-md/tracks.md`" in text
    assert "Track: minimal" in text and "Track: extended" in text


def test_ac2_tracks_section_carries_the_short_rule():
    text = _norm("\n".join(_agents_tracks_section()))
    for needle in ("C2", "Medium", "High", "Gate 2", "migrate", "session", "agent", "UI"):
        assert needle in text, f"short rule is missing {needle!r}"
    assert re.search(r"[Oo]therwise[^.]*minimal", text)
    assert "Decision record" in text and "`tasks/MINIMAL_LOG.md`" in text
    assert re.search(r"5-stage pipeline[^.]*extended track", text, re.I)


def _gate(n: int) -> str:
    m = re.search(rf"^{n}\. \*\*(.+)$", _read(AGENTS_MD), re.M)
    assert m, f"Hard-Stop Gate {n} not found"
    return m.group(0)


def test_ac2_gate1_title_kept_and_scoped_to_the_extended_track():
    gate1 = _gate(1)
    assert gate1.startswith("1. **No TASK_GUIDE = no work.**"), "the Gate 1 title must stay literal"
    assert "This gate applies to the extended track." in gate1
    assert "On the minimal track the Supervisor writes the code itself" in gate1
    assert "Decision record" in gate1 and "`docs/claude-md/tracks.md`" in gate1


def test_ac2_gates_2_to_6_are_unchanged():
    base = subprocess.run(["git", "-C", str(ROOT), "show", "8386b17:AGENTS.md"],
                          check=True, capture_output=True, text=True).stdout
    for n in range(2, 7):
        old = re.search(rf"^{n}\. \*\*.+$", base, re.M).group(0)
        assert _gate(n) == old, f"Hard-Stop Gate {n} changed"


def test_ac2_code_review_rule_scoped_to_the_extended_track():
    """D4: the minimal track runs no Stage 4 skills, so this Permanent Rule may not claim every task."""
    text = _read(AGENTS_MD)
    assert "Stage 4 (code-review) is mandatory for every extended-track task." in text
    assert "Stage 4 (code-review) is mandatory for every task." not in text


def test_ac2_agents_md_size_caps():
    assert len(_read(AGENTS_MD).splitlines()) <= 200
    assert len(AGENTS_MD.read_bytes()) <= 32768


# ── AC 3 — the Decision record template ───────────────────────────────────────────────────
def test_ac3_template_holds_every_d5_field_in_order():
    text = _read(TEMPLATE)
    assert re.search(r"^## <ID> — <title> · <track>$", text, re.M), "no ID/title/track heading"
    record = text[text.find("## <ID>"):]
    at = 0
    for field in RECORD_FIELDS:
        # D5: `Assumed:` is a prefix on a line inside `Decisions:`, not a field of its own.
        needle = f"- {field}" if field == "Assumed:" else f"**{field}**"
        hit = record.find(needle, at)
        assert hit != -1, f"field {field!r} missing or out of order"
        at = hit
    not_done = record[record.find("**Not done:**"):]
    assert "merge" in not_done.lower(), "Not done: must always include the merge"


def test_ac3_template_says_assumed_lives_under_decisions_and_newest_first():
    text = _norm(_read(TEMPLATE))
    assert re.search(r"Assumed:[^.]*assumption", text)
    assert "newest first" in text


def test_ac3_doc_says_log_is_created_on_first_use_newest_first():
    body = _norm(_read(TRACKS_MD))
    assert "`templates/MINIMAL_LOG_template.md`" in body
    assert re.search(r"does not exist[^.]*create it from", body)
    assert "newest first" in body
    assert re.search(r"same block is the Supervisor's final (?:chat )?message", body)


# ── AC 4 — pipeline-stages.md ─────────────────────────────────────────────────────────────
def _pipeline_head():
    text = _read(PIPELINE_MD)
    return _norm(text.split("## Stage 0.5", 1)[0])


def test_ac4_pipeline_doc_says_the_stages_are_the_extended_track():
    head = _pipeline_head()
    assert re.search(r"5 stages[^.]*\bextended track\b", head), head
    assert "`docs/claude-md/tracks.md`" in head


def test_ac4_gates_2_to_6_apply_unchanged_and_gate5_reaches_minimal():
    head = _pipeline_head()
    assert re.search(r"Gates 2[–-]6 still apply[^.]*unchanged", head)
    assert re.search(r"Gate 5[^.]*minimal track[^.]*`Checked:`", head)


# ── AC 5 — glossary ───────────────────────────────────────────────────────────────────────
def _glossary_row(term: str) -> str:
    rows = [l for l in _read(SPEC).splitlines() if l.startswith(f"| {term} |")]
    assert len(rows) == 1, f"expected one glossary row for {term!r}, found {len(rows)}"
    return rows[0]


@pytest.mark.parametrize("term,not_line", [
    ("Minimal track", "Not a Lane"),
    ("Extended track", "Not a Lane"),
    ("Decision record", "Not the Decision Log"),
])
def test_ac5_glossary_defines_each_term_with_its_not_line(term, not_line):
    assert not_line in _glossary_row(term)


def test_ac5_decision_record_names_its_file_and_board_mode():
    row = _glossary_row("Decision record")
    assert "`tasks/MINIMAL_LOG.md`" in row and "online" in row and "DDR" in row


def test_ac5_three_terms_are_one_block_of_their_own():
    lines = _read(SPEC).splitlines()
    idx = [i for i, l in enumerate(lines)
           if l.startswith(("| Minimal track |", "| Extended track |", "| Decision record |"))]
    assert idx == list(range(idx[0], idx[0] + 3)), "the three terms are not one contiguous block"


# ── AC 6 — hooks, for a task that has no guide ────────────────────────────────────────────
MINIMAL_ROW = ("- [ ] **T901** — Fix the comma bug in amounts | Supervisor | C0 | Risk: Low | P2 "
               "| Track: minimal | Record: `tasks/MINIMAL_LOG.md`")
EXTENDED_ROW = "- [ ] **T902** — Add a CSV export | backend-developer | C2 | Risk: Medium | P1"

# A full Decision record, plus an adversarial line shaped like a filled `verify` Evidence row.
RECORD = """# Minimal-track Decision records

## T901 — Fix the comma bug in amounts · minimal
**Asked:** "amounts with a comma crash the parser"
**Decisions:**
- Strip thousands separators before `float()` — the crash is in `parse_amount`.
**Checked:**
- New test `test_parse_amount_accepts_thousands_comma` — failed before, passes after.
- Suite: `python3 -m pytest -q` — 42 passed.
- Real run: `tally add 1,200 food` — printed `Added 1200.00 food`.
| verify | ☑ pass | user ran it — pass |
**Files:** `src/tally/parse.py`, `tests/test_parse.py`
**Not done:** merge (the user decides).
"""


def _kanban(in_progress=(), review=(), done=()):
    def block(rows):
        return "".join(f"{r}\n" for r in rows)
    return ("# Kanban\n**Last updated**: 2026-10-27\n\n### Todo\n\n"
            f"### In Progress\n{block(in_progress)}\n"
            f"### Ready for Review\n{block(review)}\n"
            f"### Done\n{block(done)}")


def _project(tmp_path, kanban, record=True, trace=True):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (project / "tasks").mkdir()
    (project / "PROJECT_KANBAN.md").write_text(kanban, encoding="utf-8")
    if record:
        (project / "tasks" / "MINIMAL_LOG.md").write_text(RECORD, encoding="utf-8")
    if trace:  # the minimal track's own test run, attributed through the active-task state
        (project / "memory" / "event-trace").mkdir(parents=True)
        summary = json.dumps({"command": "python3 -m pytest -q"})
        (project / "memory" / "event-trace" / "T901.jsonl").write_text(
            json.dumps({"tool_name": "Bash", "summary": summary, "is_error": False}) + "\n")
    return project


def _env(project, **extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR", "CLAUDE_STEP_LIMIT")}
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env.update(extra)
    return env


def _hook(project, name, event, **env):
    return subprocess.run([sys.executable, str(project / ".claude" / "hooks" / name)],
                          input=json.dumps(event), capture_output=True, text=True,
                          cwd=project, env=_env(project, **env), timeout=60)


MERGE = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/t901-comma"}}
PUSH = {"tool_name": "Bash", "tool_input": {"command": "git push origin feat/t901-comma"}}


def _decision(result):
    return json.loads(result.stdout) if result.stdout.strip() else {}


@pytest.mark.parametrize("event", [MERGE, PUSH], ids=["merge", "push"])
def test_ac6_merge_gate_blocks_a_minimal_task_awaiting_the_user(tmp_path, event):
    """Record + a real test run in the trace are present; still blocked: a Decision record is
    not Evidence, even when it carries a line shaped like a filled `verify` row."""
    project = _project(tmp_path, _kanban(review=[MINIMAL_ROW]))
    out = _decision(_hook(project, "pre_bash_block_unsafe_merge.py", event))
    assert out.get("decision") == "block"
    assert "T901 (no evidence row)" in out["reason"]


def test_ac6_merge_gate_blocks_a_minimal_task_in_progress(tmp_path):
    project = _project(tmp_path, _kanban(in_progress=[MINIMAL_ROW]))
    out = _decision(_hook(project, "pre_bash_block_unsafe_merge.py", MERGE))
    assert out.get("decision") == "block" and "Tasks still In Progress: T901" in out["reason"]


def test_ac6_track_marker_does_not_exempt_a_row_from_the_merge_gate(tmp_path):
    """Negative control: the same row without the marker gives the same block, so the marker
    changes nothing in the gate."""
    plain = MINIMAL_ROW.split(" | Track: minimal")[0]
    marked = _decision(_hook(_project(tmp_path / "a", _kanban(review=[MINIMAL_ROW])),
                             "pre_bash_block_unsafe_merge.py", MERGE))
    unmarked = _decision(_hook(_project(tmp_path / "b", _kanban(review=[plain])),
                               "pre_bash_block_unsafe_merge.py", MERGE))
    assert marked == unmarked and marked.get("decision") == "block"


def test_ac6_merge_gate_passes_only_once_the_row_leaves_review(tmp_path):
    """The boundary the doctrine reserves for the user: the row moves to Done only on the user's
    ask (tracks.md). Same project, the row in Done: the gate no longer blocks."""
    project = _project(tmp_path, _kanban(done=[MINIMAL_ROW.replace("[ ]", "[x]")]))
    result = _hook(project, "pre_bash_block_unsafe_merge.py", MERGE)
    assert result.returncode == 0 and _decision(result) == {}


def test_ac6_doc_reserves_the_done_move_and_merge_for_the_user():
    body = _norm(_section(_read(TRACKS_MD), "Minimal-track flow"))
    assert re.search(r"Ready for Review[^.]*merge gate blocks", body)
    assert re.search(r"only when the user asks", body)
    assert "/verify" in body, "the Permanent Rule 'verify before any merge' still holds"


def test_ac6_step_limit_counts_a_guideless_task_by_its_active_task(tmp_path):
    project = _project(tmp_path, _kanban(review=[MINIMAL_ROW]))
    event = {"tool_name": "Read", "tool_input": {"file_path": str(project / "src" / "x.py")},
             "session_id": "S1"}
    runs = [_hook(project, "pre_agent_step_limit.py", event,
                  CLAUDE_ACTIVE_TASK="T901", CLAUDE_STEP_LIMIT="2") for _ in range(3)]
    assert [r.returncode for r in runs] == [0, 0, 0]
    assert not runs[0].stdout.strip() and not runs[1].stdout.strip()
    assert _decision(runs[2]).get("decision") == "block" and "T901" in runs[2].stdout
    counter = project / ".claude" / "hooks" / ".state" / "step_count_S1_T901.txt"
    assert counter.exists(), "the guideless task was not counted under its own ID"


def test_ac6_step_limit_ignores_an_unattributed_call(tmp_path):
    project = _project(tmp_path, _kanban())
    event = {"tool_name": "Read", "tool_input": {"file_path": str(project / "src" / "x.py")}}
    result = _hook(project, "pre_agent_step_limit.py", event, CLAUDE_STEP_LIMIT="0")
    assert result.returncode == 0 and not result.stdout.strip()


def test_ac6_register_hook_leaves_the_board_alone_for_a_decision_record(tmp_path):
    project = _project(tmp_path, _kanban(review=[MINIMAL_ROW]))
    before = (project / "PROJECT_KANBAN.md").read_text()
    event = {"tool_name": "Write",
             "tool_input": {"file_path": str(project / "tasks" / "MINIMAL_LOG.md")}}
    result = _hook(project, "post_write_register_task.py", event)
    assert result.returncode == 0 and "Registered" not in result.stderr
    assert (project / "PROJECT_KANBAN.md").read_text() == before


def test_ac6_register_hook_still_registers_a_guide(tmp_path):
    """Positive control: the hook still works, so the no-op above is not vacuous."""
    project = _project(tmp_path, _kanban())
    guide = project / "tasks" / "TASK_GUIDE_T903.md"
    guide.write_text("# TASK_GUIDE — T903: Something\n**Complexity Level**: C2\n")
    event = {"tool_name": "Write", "tool_input": {"file_path": str(guide)}}
    result = _hook(project, "post_write_register_task.py", event)
    assert "Registered T903" in result.stderr
    assert "**T903**" in (project / "PROJECT_KANBAN.md").read_text()


def test_ac6_stop_reminder_does_not_ask_stage4_for_a_minimal_row(tmp_path):
    project = _project(tmp_path, _kanban(review=[MINIMAL_ROW]))
    err = _hook(project, "stop_review_reminder.py", {}).stderr
    assert "T901" in err, "the minimal row must still be visible: its branch awaits the user"
    assert "code-review" not in err and "Stage 4" not in err
    assert "merge" in err and "tasks/MINIMAL_LOG.md" in err


def test_ac6_stop_reminder_still_asks_stage4_for_an_extended_row(tmp_path):
    project = _project(tmp_path, _kanban(review=[MINIMAL_ROW, EXTENDED_ROW]))
    err = _hook(project, "stop_review_reminder.py", {}).stderr
    parts = err.split("Tasks awaiting Stage 4 Review:", 1)
    assert len(parts) == 2, err
    stage4, minimal = parts[1].split("Minimal-track tasks", 1)
    assert "T902" in stage4 and "code-review" in stage4
    assert "T901" not in stage4, "the minimal row must not be listed for Stage 4"
    assert "T901" in minimal


def test_ac6_stop_reminder_unchanged_with_no_minimal_row(tmp_path):
    project = _project(tmp_path, _kanban(review=[EXTENDED_ROW]))
    err = _hook(project, "stop_review_reminder.py", {}).stderr
    assert "Tasks awaiting Stage 4 Review:" in err and "Skill({ skill: 'code-review' })" in err
    assert "MINIMAL_LOG" not in err
