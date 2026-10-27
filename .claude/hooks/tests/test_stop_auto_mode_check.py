"""T180 D8 — `stop_auto_mode_check.py`: a Stop hook that blocks the end of an auto-mode run whose
final report does not hold up.

For each auto-mode task whose board row is In Progress or Ready for Review, it blocks the stop when:
  (1) the report file has no `## Auto decisions` section starting with `Mode: auto` (or, for an
      `[auto]` request, there is no report file at all);
  (2) at Risk Medium/High, a `⚠` line is not `DEBATED` with exactly 2 / 3 Advocates named;
  (3) the event trace holds fewer Advocate `Agent` calls (description starting `Advocate`) than
      2 / 3 per `DEBATED` line;
  (4) on the extended track, the trace has no `code-review` Skill call, or no `security-review`
      Skill call at Medium/High.
On the second fire (`stop_hook_active`) it never blocks again: it allows the stop and appends
`Paused: auto-mode check failed — <reasons>` to the report. Unreadable files fail open, with one
stderr line.

Every test runs the real hook as the harness does: a subprocess against a temp project.
Run with: python3 -m pytest .claude/hooks/tests/test_stop_auto_mode_check.py -v
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOOKS = ROOT / ".claude" / "hooks"
HOOK = "stop_auto_mode_check.py"
FLAG = "⚠ decided for you — please review"
BASE_REF = "effd395"  # T180 head before D8: the merge gate as it must stay

EXT_ROW = "- [ ] **T951** — Move the data from CSV to JSON | Supervisor | C3 | Risk: High | P1"
MIN_ROW = ("- [ ] **T952** — Sort the names | Supervisor | C0 | Risk: Low | P2 "
           "| Track: minimal | Record: `tasks/MINIMAL_LOG.md`")
PLAIN_ROW = "- [ ] **T953** — Add a CSV export | backend-developer | C2 | Risk: Medium | P1"


def _advocates(n):
    return "; ".join(f"Advocate {i}: option {i}" for i in range(1, n + 1))


def _report(decisions, marker="Mode: auto", heading="## Auto decisions"):
    return (f"# TASK_REVIEW — T951: Move the data\n\n{heading}\n\n{marker}\n" + "\n".join(decisions)
            + "\nChecks: tests pass; code-review 0 P0/P1; real run ok (auto-checked, not /verify)\n"
            "Not done: merge (yours); /verify (yours)\n\n## Evidence\n\n| Check | Result | Notes |\n"
            "|---|---|---|\n| verify | ☐ pass / ☐ fail / ☐ N/A | |\n\n## Demonstration\n\n**BEFORE**: x\n")


def _good_decisions(n):
    return [f"1. kept recurring.csv — DEBATED: keep it ({_advocates(n)}) {FLAG}",
            "2. backed up data/expenses.csv before the delete — RULE: `docs/claude-md/tracks.md` `### Backups`"]


def _now(offset_s=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _rec(tool, payload, offset_s=0, is_error=False):
    return {"timestamp": _now(offset_s), "tool_name": tool, "summary": json.dumps(payload)[:300],
            "is_error": is_error}


def _agent(i, offset_s=0):
    return _rec("Agent", {"description": f"Advocate {i}: argue option {i}", "prompt": "Using the repo…",
                          "subagent_type": "Explore"}, offset_s)


def _skill(name, offset_s=0):
    return _rec("Skill", {"skill": name, "args": "task=T951"}, offset_s)


def _trace(n_advocates, skills=("code-review", "security-review"), offset_s=0):
    return [_agent(i, offset_s) for i in range(1, n_advocates + 1)] + [_skill(s, offset_s) for s in skills]


def _project(tmp_path, rows, risk="High", review=None, guide=True, minimal_log=None,
             untagged=(), tagged=(), transcript=None, board=True, done_rows=()):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    tasks = project / "tasks"
    tasks.mkdir()
    review_rows = "".join(f"{r}\n" for r in rows)
    done = "".join(f"{r}\n" for r in done_rows)
    if board:
        (project / "PROJECT_KANBAN.md").write_text(
            "# Kanban\n\n### Todo\n\n### In Progress\n\n"
            f"### Ready for Review\n{review_rows}\n### Done\n{done}", encoding="utf-8")
    if guide:
        (tasks / "TASK_GUIDE_T951.md").write_text(
            f"# TASK_GUIDE — T951: Move the data\n**Complexity Level**: C3\n**Risk Level**: {risk}\n",
            encoding="utf-8")
    if review is not None:
        (tasks / "TASK_REVIEW_T951.md").write_text(review, encoding="utf-8")
    if minimal_log is not None:
        (tasks / "MINIMAL_LOG.md").write_text(minimal_log, encoding="utf-8")
    trace_dir = project / "memory" / "event-trace"
    trace_dir.mkdir(parents=True)
    if untagged:
        (trace_dir / "_untagged.jsonl").write_text("".join(json.dumps(r) + "\n" for r in untagged))
    if tagged:
        (trace_dir / "T951.jsonl").write_text("".join(json.dumps(r) + "\n" for r in tagged))
    tpath = project / "transcript.jsonl"
    tpath.write_text("".join(json.dumps(e) + "\n" for e in (transcript or [])), encoding="utf-8")
    return project


def _user(text, offset_s=-60):
    return {"type": "user", "timestamp": _now(offset_s), "message": {"role": "user", "content": text}}


def _run(project, active=False, **env):
    event = {"session_id": "S1", "transcript_path": str(project / "transcript.jsonl"),
             "hook_event_name": "Stop", "stop_hook_active": active}
    full_env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR",)}
    full_env["CLAUDE_PROJECT_DIR"] = str(project)
    full_env.update(env)
    result = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / HOOK)],
                            input=json.dumps(event), capture_output=True, text=True, cwd=project,
                            env=full_env, timeout=60)
    out = json.loads(result.stdout) if result.stdout.strip() else {}
    return result, out


def _blocked(out):
    return out.get("decision") == "block"


# ── a correct report passes ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("risk,n", [("High", 3), ("Medium", 2)])
def test_a_correct_extended_report_passes(tmp_path, risk, n):
    project = _project(tmp_path, [EXT_ROW.replace("High", risk)], risk=risk,
                       review=_report(_good_decisions(n)), untagged=_trace(n))
    result, out = _run(project)
    assert result.returncode == 0 and out == {}, (out, result.stderr)


def test_a_correct_low_risk_extended_report_needs_no_advocates_nor_security_review(tmp_path):
    decisions = [f"1. kept recurring.csv — SAFER OPTION: it keeps all data {FLAG}"]
    project = _project(tmp_path, [EXT_ROW.replace("High", "Low")], risk="Low",
                       review=_report(decisions), untagged=_trace(0, skills=("code-review",)))
    _, out = _run(project)
    assert out == {}, out


def test_a_correct_minimal_record_passes(tmp_path):
    log = ("# Minimal-track Decision records\n\n## T952 — Sort the names · minimal\nMode: auto\n"
           "**Asked:** \"sort the names [auto]\"\n**Decisions:**\n"
           f"1. sort A–Z — SAFER OPTION: the literal reading of \"sort\" {FLAG}\n"
           "**Checked:**\n- Suite: `pytest -q` — 12 passed\n**Files:** `x.py`\n"
           "**Not done:** merge (yours); /verify (yours)\n")
    project = _project(tmp_path, [MIN_ROW], guide=False, minimal_log=log)
    _, out = _run(project)
    assert out == {}, out


# ── a non-auto task is ignored ────────────────────────────────────────────────────────────
def test_a_non_auto_task_is_ignored(tmp_path):
    plain = _report(["1. x — FACT: a.py:1 \"y\""]).replace("## Auto decisions\n\nMode: auto\n", "")
    project = _project(tmp_path, [EXT_ROW], review=plain,
                       transcript=[_user("move the data, and use `[auto]` next time")])
    _, out = _run(project)
    assert out == {}, out


def test_a_marked_task_not_on_the_board_is_checked_from_its_file(tmp_path):
    """D9 supersedes D8's board-only discovery: a marked review file with no board row is checked."""
    project = _project(tmp_path, [PLAIN_ROW], review=_report(["1. x — FACT: a.py:1 \"y\" " + FLAG]))
    _, out = _run(project)
    assert _blocked(out) and "T951" in out["reason"] and "T953" not in out["reason"], out


# ── check (1): the report file ────────────────────────────────────────────────────────────
def test_check1_marker_not_first_under_the_heading_blocks(tmp_path):
    review = _report(_good_decisions(3), marker="1. a stray line\nMode: auto")
    project = _project(tmp_path, [EXT_ROW], review=review, untagged=_trace(3))
    _, out = _run(project)
    assert _blocked(out) and "T951" in out["reason"] and "`Mode: auto`" in out["reason"], out


def test_check1_auto_request_with_no_report_file_blocks(tmp_path):
    """AC 6 re-run 1, task 5: the report was only in chat. The request carried `[auto]`."""
    project = _project(tmp_path, [EXT_ROW], review=None, untagged=_trace(3),
                       transcript=[_user("store expenses as JSON instead of CSV [auto]")])
    _, out = _run(project)
    assert _blocked(out), out
    assert "T951" in out["reason"] and "tasks/TASK_REVIEW_T951.md" in out["reason"], out


def test_check1_ignores_a_guide_older_than_the_auto_request(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=None,
                       transcript=[_user("store expenses as JSON [auto]", offset_s=+3600)])
    _, out = _run(project)
    assert out == {}, out


# ── check (2): flagged lines at Risk Medium/High ──────────────────────────────────────────
def test_check2_a_flagged_fact_at_high_risk_blocks(tmp_path):
    """/verify T180: `recurring.csv` logged `FACT … ⚠` at Risk High, no Debate."""
    decisions = [f"1. kept recurring.csv — FACT: data/recurring.csv:1 \"rent\" {FLAG}"]
    project = _project(tmp_path, [EXT_ROW], review=_report(decisions), untagged=_trace(0))
    _, out = _run(project)
    assert _blocked(out) and "Risk High" in out["reason"] and "exactly 3 Advocates" in out["reason"]


def test_check2_two_advocates_named_at_high_risk_blocks(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(2)), untagged=_trace(3))
    _, out = _run(project)
    assert _blocked(out) and "exactly 3 Advocates" in out["reason"], out


# ── check (3): Advocate calls in the trace ────────────────────────────────────────────────
def test_check3_too_few_advocate_calls_blocks(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(3)), untagged=_trace(2))
    _, out = _run(project)
    assert _blocked(out) and "Advocate `Agent` calls" in out["reason"] and "has 2" in out["reason"]


def test_check3_counts_calls_in_the_tasks_own_trace_too(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(3)),
                       untagged=_trace(1), tagged=[_agent(2), _agent(3)])
    _, out = _run(project)
    assert out == {}, out


def test_check3_ignores_untagged_calls_outside_the_window(tmp_path):
    old = [_agent(i, offset_s=-30 * 3600) for i in (1, 2, 3)]
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(3)),
                       untagged=old + _trace(0))
    _, out = _run(project)
    assert _blocked(out) and "has 0" in out["reason"], out


def test_check3_an_agent_call_not_named_advocate_does_not_count(tmp_path):
    other = [_rec("Agent", {"description": "Implement T951", "prompt": "x",
                            "subagent_type": "backend-developer"}) for _ in range(3)]
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(3)),
                       untagged=other + _trace(0))
    _, out = _run(project)
    assert _blocked(out) and "has 0" in out["reason"], out


# ── check (4): Stage 4 on the extended track ──────────────────────────────────────────────
def test_check4_no_code_review_blocks(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(3)),
                       untagged=_trace(3, skills=("security-review",)))
    _, out = _run(project)
    assert _blocked(out) and "`code-review`" in out["reason"], out


def test_check4_no_security_review_at_high_risk_blocks(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(3)),
                       untagged=_trace(3, skills=("code-review",)))
    _, out = _run(project)
    assert _blocked(out) and "`security-review`" in out["reason"], out


# ── the second fire never loops ───────────────────────────────────────────────────────────
def test_second_fire_allows_the_stop_and_records_the_pause(tmp_path):
    decisions = [f"1. kept recurring.csv — FACT: data/recurring.csv:1 \"rent\" {FLAG}"]
    project = _project(tmp_path, [EXT_ROW], review=_report(decisions), untagged=_trace(0))
    _, first = _run(project)
    assert _blocked(first)
    result, second = _run(project, active=True)
    assert result.returncode == 0 and second == {}, second
    text = (project / "tasks" / "TASK_REVIEW_T951.md").read_text(encoding="utf-8")
    auto = text.split("## Auto decisions", 1)[1].split("\n## ", 1)[0]
    assert "Paused: auto-mode check failed — " in auto, "the pause must land in the report section"
    _run(project, active=True)
    again = (project / "tasks" / "TASK_REVIEW_T951.md").read_text(encoding="utf-8")
    assert again.count("Paused: auto-mode check failed") == 1, "a third fire must not duplicate it"


def test_second_fire_records_the_pause_in_a_minimal_record(tmp_path):
    log = ("# Minimal-track Decision records\n\n## T952 — Sort the names · minimal\n"
           "Risk: High (track set by the user)\n**Asked:** \"sort [auto]\"\n**Decisions:**\n"
           f"1. sort A–Z — SAFER OPTION: literal {FLAG}\n**Not done:** merge (yours)\n\n"
           "## T950 — Older · minimal\n**Asked:** \"x\"\n")
    project = _project(tmp_path, [MIN_ROW], guide=False, minimal_log=log,
                       transcript=[_user("sort the names [auto]")])
    _, first = _run(project)
    assert _blocked(first) and "T952" in first["reason"] and "Risk High" in first["reason"], first
    _run(project, active=True)
    text = (project / "tasks" / "MINIMAL_LOG.md").read_text(encoding="utf-8")
    record = text.split("## T952", 1)[1].split("\n## ", 1)[0]
    assert "Paused: auto-mode check failed — " in record
    assert "Paused" not in text.split("## T950", 1)[1]


# ── fail open ─────────────────────────────────────────────────────────────────────────────
def test_an_unreadable_report_fails_open_with_one_stderr_line(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=None, untagged=_trace(0))
    (project / "tasks" / "TASK_REVIEW_T951.md").mkdir()  # reading it raises IsADirectoryError
    result, out = _run(project)
    assert result.returncode == 0 and out == {}, out
    lines = [l for l in result.stderr.splitlines() if "stop_auto_mode_check" in l]
    assert len(lines) == 1 and "TASK_REVIEW_T951.md" in lines[0], result.stderr


def test_bad_stdin_and_no_board_fail_open(tmp_path):
    """No board and no marked file: nothing to check (D9 still looks at the files)."""
    plain = _report(["1. x — FACT: a:1 \"b\" " + FLAG]).replace("## Auto decisions\n\nMode: auto\n", "")
    project = _project(tmp_path, [EXT_ROW], review=plain)
    (project / "PROJECT_KANBAN.md").unlink()
    result, out = _run(project)
    assert result.returncode == 0 and out == {}
    bad = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / HOOK)], input="not json",
                         capture_output=True, text=True, cwd=project, timeout=60)
    assert bad.returncode == 0 and not bad.stdout.strip()


# ── shipping and the merge gate ───────────────────────────────────────────────────────────
def test_settings_wires_the_hook_on_stop():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    commands = [h["command"] for entry in settings["hooks"]["Stop"] for h in entry["hooks"]]
    assert 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/stop_auto_mode_check.py' in commands
    assert any("stop_review_reminder.py" in c for c in commands), "the reminder stays wired"


def test_manifest_ships_the_hook():
    lines = [l.split()[0] for l in (ROOT / "MANIFEST").read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    assert ".claude/hooks" in lines and "!.claude/hooks/tests" in lines
    assert (HOOKS / HOOK).is_file()


def test_the_installer_merge_adds_the_stop_entry(tmp_path):
    """`setup.sh` merges the kit's hook entries into an existing settings.json with
    `lib/merge-settings.py`; a project that has only the old Stop reminder gains the new hook.
    The project root is this repo: the merge drops a kit entry whose hook file is missing there."""
    dst = tmp_path / "settings.json"
    dst.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command":
        'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/stop_review_reminder.py'}]}]}}))
    subprocess.run([sys.executable, str(ROOT / "lib" / "merge-settings.py"),
                    str(ROOT / ".claude" / "settings.json"), str(dst), str(ROOT)],
                   check=True, capture_output=True, text=True, cwd=tmp_path)
    merged = json.loads(dst.read_text())
    commands = [h["command"] for entry in merged["hooks"]["Stop"] for h in entry["hooks"]]
    assert any(c.endswith("stop_auto_mode_check.py") for c in commands), commands


def test_merge_gate_is_untouched():
    diff = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", BASE_REF, "--",
                           ".claude/hooks/pre_bash_block_unsafe_merge.py"])
    assert diff.returncode == 0


# ── D9 (a) — discovery from files; finished tasks skipped ─────────────────────────────────
# D8 live check: the copies had no PROJECT_KANBAN.md, so a board-only hook never fired.
UNCITED_RULE = "1. kept recurring.csv untouched — RULE: Surgical Changes"


def test_d9_no_board_a_marked_review_file_is_still_checked(tmp_path):
    project = _project(tmp_path, [], risk="Medium", board=False, review=_report([UNCITED_RULE]),
                       untagged=_trace(0))
    _, out = _run(project)
    assert _blocked(out) and "T951" in out["reason"], out


def test_d9_no_board_a_correct_report_passes(tmp_path):
    project = _project(tmp_path, [], risk="Medium", board=False, review=_report(_good_decisions(2)),
                       untagged=_trace(2))
    _, out = _run(project)
    assert out == {}, out


def test_d9_a_done_row_is_ignored(tmp_path):
    project = _project(tmp_path, [], risk="Medium", review=_report([UNCITED_RULE]),
                       done_rows=[EXT_ROW.replace("[ ]", "[x]")], untagged=_trace(0))
    _, out = _run(project)
    assert out == {}, out


def test_d9_a_review_with_a_passing_verify_row_is_ignored(tmp_path):
    review = _report([UNCITED_RULE]).replace("| verify | ☐ pass / ☐ fail / ☐ N/A | |",
                                             "| verify | ☑ pass | user ran /verify T951 — pass |")
    project = _project(tmp_path, [], risk="Medium", board=False, review=review, untagged=_trace(0))
    _, out = _run(project)
    assert out == {}, out


def test_d9_risk_comes_from_the_review_file_when_there_is_no_guide(tmp_path):
    review = _report([UNCITED_RULE]).replace("# TASK_REVIEW — T951: Move the data\n",
                                             "# TASK_REVIEW — T951: Move the data\n**Risk Level**: High\n")
    project = _project(tmp_path, [], guide=False, board=False, review=review, untagged=_trace(0))
    _, out = _run(project)
    assert _blocked(out) and "Risk High" in out["reason"], out


def _log(*records):
    return "# Minimal-track Decision records\n\n" + "\n".join(records)


def _record(tid, risk_line, decision):
    return (f"## {tid} — Sort the names · minimal\nMode: auto\n{risk_line}**Asked:** \"sort [auto]\"\n"
            f"**Decisions:**\n{decision}\n**Not done:** merge (yours)\n")


def test_d9_no_board_the_newest_minimal_record_is_checked(tmp_path):
    log = _log(_record("T952", "Risk: Medium (track set by the user)\n", UNCITED_RULE))
    project = _project(tmp_path, [], guide=False, board=False, minimal_log=log)
    _, out = _run(project)
    assert _blocked(out) and "T952" in out["reason"], out


def test_d9_only_the_newest_minimal_record_is_checked(tmp_path):
    log = _log(_record("T953", "", "1. sort A–Z — SAFER OPTION: literal " + FLAG),
               _record("T952", "Risk: Medium\n", UNCITED_RULE))
    project = _project(tmp_path, [], guide=False, board=False, minimal_log=log)
    _, out = _run(project)
    assert out == {}, out


# ── D9 (b) — at Risk Medium/High a label must cite a written rule or a Citation ───────────
def test_d9_an_uncited_rule_at_medium_blocks_with_its_number_and_label(tmp_path):
    project = _project(tmp_path, [EXT_ROW.replace("High", "Medium")], risk="Medium",
                       review=_report([UNCITED_RULE]), untagged=_trace(0))
    _, out = _run(project)
    assert _blocked(out), out
    assert "decision 1 (`RULE`)" in out["reason"] and "cites no written rule" in out["reason"], out


@pytest.mark.parametrize("cite", [
    "`docs/claude-md/tracks.md` `### Backups`",
    "docs/claude-md/tracks.md:86",
    "`AGENTS.md` § Karpathy Engineering Principles",
])
def test_d9_a_cited_rule_passes(tmp_path, cite):
    decisions = [f"1. backed up data/expenses.csv before the delete — RULE: {cite}"]
    project = _project(tmp_path, [EXT_ROW.replace("High", "Medium")], risk="Medium",
                       review=_report(decisions), untagged=_trace(0))
    _, out = _run(project)
    assert out == {}, out


def test_d9_an_uncited_fact_at_high_blocks(tmp_path):
    decisions = ["1. amounts are stored in cents — FACT: the code stores cents"]
    project = _project(tmp_path, [EXT_ROW], review=_report(decisions), untagged=_trace(0))
    _, out = _run(project)
    assert _blocked(out) and "decision 1 (`FACT`)" in out["reason"] and "no Citation" in out["reason"]


def test_d9_a_cited_fact_at_high_passes(tmp_path):
    decisions = ['1. amounts are stored in cents — FACT: src/tally/store.py:12 "amount_cents = int(...)"']
    project = _project(tmp_path, [EXT_ROW], review=_report(decisions), untagged=_trace(0))
    _, out = _run(project)
    assert out == {}, out


def test_d9_a_debated_line_with_the_wrong_count_names_its_number(tmp_path):
    project = _project(tmp_path, [EXT_ROW], review=_report(_good_decisions(2)), untagged=_trace(3))
    _, out = _run(project)
    assert _blocked(out) and "decision 1 (`DEBATED`)" in out["reason"], out


def test_d9_low_risk_is_unchanged(tmp_path):
    decisions = [UNCITED_RULE, "2. amounts in cents — FACT: the code stores cents"]
    project = _project(tmp_path, [EXT_ROW.replace("High", "Low")], risk="Low",
                       review=_report(decisions), untagged=_trace(0, skills=("code-review",)))
    _, out = _run(project)
    assert out == {}, out


def test_d9_second_fire_with_no_board_does_not_loop(tmp_path):
    project = _project(tmp_path, [], risk="Medium", board=False, review=_report([UNCITED_RULE]),
                       untagged=_trace(0))
    _, first = _run(project)
    assert _blocked(first)
    result, second = _run(project, active=True)
    assert result.returncode == 0 and second == {}
    text = (project / "tasks" / "TASK_REVIEW_T951.md").read_text(encoding="utf-8")
    assert text.count("Paused: auto-mode check failed") == 1
