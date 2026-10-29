"""T182 — auto verify: for an `[auto]` task at Ready for Review, a Stop hook starts one detached,
headless `claude -p "/verify <ID>"` run per head commit; the run (never the Supervisor) writes the
task's `verify` row and a run record outside the agent's write reach; the merge gate accepts an
`auto-run by hook` row only with that record.

AC 2 — the Stop hook starts the run only when every D2 condition holds, returns at once (the run is
       detached in a new session), and never starts the same task and commit twice.
AC 3 — the run: a new session (no `--resume`), `--max-budget-usd 2` (overridable), no
       `--dangerously-skip-permissions`, cwd = the task's checkout, log under `.claude/verify-runs/`
       (gitignored).
AC 4 — the D4 row for pass, fail and blocked; a blocked or failed run's Notes never contain "pass".
AC 5 — the merge gate accepts an `auto-run by hook` row only with a matching D5 record; it blocks the
       row with no record, a record for another commit or task, a fail record, a record the agent
       could write (in the repo), and `auto-checked, not /verify`.
AC 6 — no `Mode: auto` marker -> nothing happens; `docs/claude-md/tracks.md` names the step;
       `AGENTS.md` stays <= 200 lines; glossary; settings.json wires the hook.

Every test stubs `claude`: PATH is the stub's directory plus /usr/bin:/bin, and `_env` asserts that
no other `claude` is reachable. The real binary is never run.

Run with: python3 -m pytest tests/test_auto_verify.py -v
"""
import ast
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
HOOK = "stop_auto_verify.py"
GATE = "pre_bash_block_unsafe_merge.py"
FIXTURE = ROOT / "tests" / "fixtures" / "auto_verify" / "verify_pass.json"
TRACKS_MD = ROOT / "docs" / "claude-md" / "tracks.md"
SPEC = ROOT / "PROJECT_SPEC.md"

TASK = "T951"
RFR_ROW = f"- [ ] **{TASK}** — Move the data | Supervisor | C2 | Risk: Medium | P1"
UNFILLED = "☐ pass / ☐ fail / ☐ N/A | [what was observed]"
SAFE_PATH = "/usr/bin:/bin"
WAIT_S = 20

# T188 — the minimal track: a board row that says so, and a Decision record instead of a review file.
MIN_TASK = "T952"
MIN_ROW = (f"- [ ] **{MIN_TASK}** — Sort the names | Supervisor | C0 | Risk: Low | P2 "
           "| Track: minimal | Record: `tasks/MINIMAL_LOG.md`")
RUNNING_SLOT = "auto verify: running (T182)"
# T189 D2: Hard-Stop Gates 5 and 6 as a complete fixture holds them — three design rows N/A with a
# reason (a pure-backend task), and a minimal record's `New test` line — so that only the field a
# test leaves out decides whether the close-out moves the row.
UI_ROWS = "".join(f"| **UI: {name}** | ☐ N/A | no UI: a data script |\n" for name in (
    "Visual regression (diff or verdict pasted)",
    "Design-system compliance (tokens/colors/typography verified)",
    "Responsiveness at target viewports"))
NEW_TEST = "- New test `test_sort_is_alphabetical` — failed before the change, passes after"
NOT_DONE = f"merge (yours); {RUNNING_SLOT}"


# ── fixtures ──────────────────────────────────────────────────────────────────────────────
def _review(verify_cells=UNFILLED, marker="Mode: auto", task=TASK, not_done=NOT_DONE, memory=None):
    auto = (f"## Auto decisions\n\n{marker}\n"
            "1. kept recurring.csv — RULE: `docs/claude-md/tracks.md` `### Stops that stay`\n"
            "Checks: tests pass (auto-checked, not /verify)\n"
            + (f"{memory}\n" if memory else "") +
            f"Not done: {not_done}\n\n")
    return (f"# TASK_REVIEW — {task}: Move the data\n\n{auto}"
            "## Evidence\n\n| Check | Result | Notes / output snippet |\n|-------|--------|----|\n"
            "| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | tests/x.py |\n"
            f"| verify | {verify_cells} |\n"
            f"{UI_ROWS}"
            "| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |\n\n"
            "## Demonstration\n\n**BEFORE**: x\n")


def _record(task=MIN_TASK, marker="Mode: auto", checked=("- Suite: `pytest -q` — 12 passed", NEW_TEST),
            not_done=NOT_DONE, title="Sort the names", memory=None):
    """One minimal-track Decision record (`templates/MINIMAL_LOG_template.md`)."""
    return (f"## {task} — {title} · minimal\n{marker}\n"
            f'**Asked:** "sort the names [auto]"\n**Decisions:**\n'
            "1. sort A–Z — RULE: `docs/claude-md/tracks.md` `### Minimal-track flow`\n"
            "**Checked:**\n" + "".join(f"{line}\n" for line in checked) +
            "**Files:** `src/app.py`\n"
            + (f"**Memory:** {memory}\n" if memory else "") +
            f"**Not done:** {not_done}\n")


def _log(*records):
    """`tasks/MINIMAL_LOG.md`: the records newest first, under the file's note."""
    return "# Minimal-track Decision records\n\n" + "\n".join(records or (_record(),))


def _git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def _trace(checkout_root, task=TASK):
    trace = checkout_root / "memory" / "event-trace"
    trace.mkdir(parents=True, exist_ok=True)
    (trace / f"{task}.jsonl").write_text(json.dumps(
        {"tool_name": "Bash", "summary": json.dumps({"command": "python3 -m pytest -q"}),
         "is_error": False}) + "\n", encoding="utf-8")


def _project(tmp_path, review=None, rows=(RFR_ROW,), worktree=False, extra_reviews=(),
             minimal_log=None, review_file=True):
    """A temp git project with the kit's hooks, settings.json and .gitignore. The review file lives
    in the main checkout, or (worktree=True) only in a `git worktree` on branch feat/t951.

    T188: `minimal_log` writes `tasks/MINIMAL_LOG.md` into the same checkout the review file would
    go to, and `review_file=False` leaves the extended track's review file out altogether — a
    minimal-track task has none.
    """
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, project / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    shutil.copy(ROOT / ".claude" / "settings.json", project / ".claude" / "settings.json")
    shutil.copy(ROOT / ".gitignore", project / ".gitignore")
    (project / "tasks").mkdir()
    (project / "src").mkdir()
    (project / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    board = "\n".join(rows)
    (project / "PROJECT_KANBAN.md").write_text(
        f"# Kanban\n**Last updated**: 2026-01-01\n\n### Todo\n\n### In Progress\n\n"
        f"### Ready for Review\n{board}\n\n### Done\n",
        encoding="utf-8")
    if not worktree and review_file:
        (project / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(
            _review() if review is None else review, encoding="utf-8")
    for task, text in extra_reviews:
        (project / "tasks" / f"TASK_REVIEW_{task}.md").write_text(text, encoding="utf-8")
        _trace(project, task)
    _trace(project)
    if minimal_log is not None:
        _trace(project, MIN_TASK)
    if minimal_log is not None and not worktree:
        (project / "tasks" / "MINIMAL_LOG.md").write_text(minimal_log, encoding="utf-8")
    _git(project, "init", "-q", "-b", "main")
    _git(project, "config", "user.email", "t@example.com")
    _git(project, "config", "user.name", "t")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", "base")
    checkout = project
    if worktree:
        checkout = tmp_path / "wt-t951"
        _git(project, "worktree", "add", "-q", "-b", "feat/t951", str(checkout))
        (checkout / "tasks").mkdir(exist_ok=True)  # git does not carry the main checkout's empty tasks/
        if review_file:
            (checkout / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(
                _review() if review is None else review, encoding="utf-8")
        if minimal_log is not None:
            (checkout / "tasks" / "MINIMAL_LOG.md").write_text(minimal_log, encoding="utf-8")
        _git(checkout, "add", "-A")
        _git(checkout, "commit", "-qm", "task work")
    return project, checkout


def _stub(tmp_path, output=None, sleep=0.0, exit_code=0):
    """A fake `claude`: logs argv, cwd, its parent's session and env flags, then prints `output`."""
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir(exist_ok=True)
    out = tmp_path / "stub_out.txt"
    out.write_text(FIXTURE.read_text(encoding="utf-8") if output is None else output, encoding="utf-8")
    calls = tmp_path / "stub_calls.jsonl"
    script = stub_dir / "claude"
    script.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys, time\n"
        f"with open({str(calls)!r}, 'a') as f:\n"
        "    f.write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(),\n"
        "        'parent_pid': os.getppid(), 'parent_sid': os.getsid(os.getppid()),\n"
        "        'child_flag': os.environ.get('CLAUDE_AUTO_VERIFY_RUN'),\n"
        "        'project_dir': os.environ.get('CLAUDE_PROJECT_DIR')}) + '\\n')\n"
        f"time.sleep({sleep})\n"
        f"sys.stdout.write(open({str(out)!r}, encoding='utf-8').read())\n"
        f"sys.exit({exit_code})\n", encoding="utf-8")
    script.chmod(0o755)
    return stub_dir, calls


def _env(tmp_path, project, stub_dir=None, **extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_", "T182_"))}
    env["PATH"] = (f"{stub_dir}{os.pathsep}" if stub_dir else "") + SAFE_PATH
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env["CLAUDE_TRACE_ANCHOR_DIR"] = str(tmp_path / "anchors")
    env.update(extra)
    found = shutil.which("claude", path=env["PATH"])
    assert found in (None, str(Path(stub_dir or "/nonexistent") / "claude")), \
        f"a real claude is reachable on the test PATH: {found}"
    return env


def _stop(project, env, event=None):
    start = time.monotonic()
    result = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / HOOK)],
                            input=json.dumps(event or {"hook_event_name": "Stop"}),
                            capture_output=True, text=True, cwd=project, env=env, timeout=30)
    return result, time.monotonic() - start


def _calls(calls):
    return [json.loads(l) for l in calls.read_text().splitlines()] if calls.exists() else []


def _row(checkout, task=TASK):
    text = (checkout / "tasks" / f"TASK_REVIEW_{task}.md").read_text(encoding="utf-8")
    rows = [l for l in text.splitlines() if re.match(r"\|\s*verify\s*\|", l)]
    assert len(rows) == 1, rows
    cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    return cells[1], cells[2]


def _wait_row(checkout, task=TASK):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        result, notes = _row(checkout, task)
        if "auto-run by hook" in notes:
            return result, notes
        time.sleep(0.1)
    raise AssertionError(f"the hook never wrote the verify row: {_row(checkout, task)}")


def _settle(seconds=1.0):
    time.sleep(seconds)


def _lib():
    sys.path.insert(0, str(HOOKS / "lib"))
    try:
        import verify_record  # noqa: WPS433
        return verify_record
    finally:
        sys.path.pop(0)


def _merge(project, env):
    result = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / GATE)],
                            input=json.dumps({"tool_name": "Bash",
                                              "tool_input": {"command": "git merge feat/t951"}}),
                            capture_output=True, text=True, cwd=project, env=env, timeout=60)
    out = json.loads(result.stdout) if result.stdout.strip() else {}
    return "block" if out.get("decision") == "block" else "allow", out.get("reason", "")


def _set_row(checkout, cells, task=TASK):
    path = checkout / "tasks" / f"TASK_REVIEW_{task}.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r"^\|\s*verify\s*\|.*$", f"| verify | {cells} |", text, count=1, flags=re.M),
                    encoding="utf-8")


def _verdict_output(verdict_line, **fields):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["result"] = data["result"].replace("**Verdict:** PASS", verdict_line)
    data.update(fields)
    return json.dumps(data)


# ── AC 2 — trigger, detached, once per commit ─────────────────────────────────────────────
def test_ac2_stop_hook_returns_at_once_and_the_detached_run_writes_the_row(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path, sleep=3)
    result, elapsed = _stop(project, _env(tmp_path, project, stub_dir))
    assert result.returncode == 0 and not result.stdout.strip(), result
    assert elapsed < 2.5, f"the Stop hook waited for the run ({elapsed:.1f}s)"
    assert _row(checkout)[0].startswith("☐"), "the row was written before the run finished"
    assert f"{TASK}" in result.stderr and "auto verify started" in result.stderr
    verdict, notes = _wait_row(checkout)
    assert verdict == "☑ pass" and notes.endswith("— pass"), notes
    [call] = _calls(calls)
    # Detached: the runner (claude's parent) leads its own session (setsid), so it survives the
    # Stop hook and is not in the Supervisor's session.
    assert call["parent_sid"] == call["parent_pid"] != os.getsid(0)


def test_ac2_same_task_and_commit_never_start_twice(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path, sleep=1)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _stop(project, env)  # while the first run is still going
    _wait_row(checkout)
    _stop(project, env)  # after it finished, same commit
    _settle()
    assert len(_calls(calls)) == 1


def test_ac2_a_blocked_run_is_not_retried_on_the_same_commit(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path, output="not json")
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    assert _wait_row(checkout)[0] == "☐ blocked"
    _stop(project, env)
    _settle()
    assert len(_calls(calls)) == 1


def test_ac2_a_new_code_commit_starts_a_new_run(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _, first = _wait_row(checkout)
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2")
    head = _git(checkout, "rev-parse", "HEAD")
    _stop(project, env)
    deadline = time.monotonic() + WAIT_S
    while head not in _row(checkout)[1] and time.monotonic() < deadline:
        time.sleep(0.1)
    assert head in _row(checkout)[1] and head not in first
    assert len(_calls(calls)) == 2


def test_ac2_committing_only_the_review_file_does_not_start_a_new_run(tmp_path):
    """The Supervisor commits the hook-written row: the verified code did not change."""
    project, checkout = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _wait_row(checkout)
    _git(checkout, "commit", "-qam", "review: verify row")
    _stop(project, env)
    _settle()
    assert len(_calls(calls)) == 1


@pytest.mark.parametrize("where", ["nowhere", "In Progress", "Done"])
def test_ac2_no_run_unless_the_task_is_ready_for_review(tmp_path, where):
    project, _ = _project(tmp_path)
    board = {s: (RFR_ROW if s == where else "") for s in ("In Progress", "Ready for Review", "Done")}
    (project / "PROJECT_KANBAN.md").write_text(
        "# Kanban\n\n" + "".join(f"### {s}\n{row}\n\n" for s, row in board.items()), encoding="utf-8")
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []


def test_ac2_no_run_when_the_user_already_filled_the_row(tmp_path):
    project, checkout = _project(tmp_path, review=_review("☑ pass | user ran /verify T951 — pass"))
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert _calls(calls) == [] and _row(checkout) == ("☑ pass", "user ran /verify T951 — pass")


def test_ac2_the_headless_run_never_starts_another(tmp_path):
    """The run's own session fires Stop hooks too; the run marks its env so they do nothing."""
    project, _ = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY_RUN="1"))
    _settle()
    assert _calls(calls) == []


def test_ac2_two_auto_tasks_get_two_runs_with_their_own_log_and_record(tmp_path):
    second = "- [ ] **T952** — Sort | Supervisor | C2 | Risk: Medium | P1"
    project, checkout = _project(tmp_path, rows=(RFR_ROW, second),
                                 extra_reviews=[("T952", _review(task="T952"))])
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _wait_row(checkout)
    _wait_row(checkout, "T952")
    assert sorted(c["argv"][1] for c in _calls(calls)) == ["/verify T951", "/verify T952"]
    head = _git(project, "rev-parse", "HEAD")
    logs = sorted(p.name for p in (project / ".claude" / "verify-runs").iterdir())
    assert logs == [f"T951-{head[:12]}.log", f"T952-{head[:12]}.log"]
    lib = _lib()
    os.environ["CLAUDE_TRACE_ANCHOR_DIR"], saved = env["CLAUDE_TRACE_ANCHOR_DIR"], os.environ.get(
        "CLAUDE_TRACE_ANCHOR_DIR")
    try:
        assert lib.read_record(str(project), "T951", head)["verdict"] == "pass"
        assert lib.read_record(str(project), "T952", head)["verdict"] == "pass"
    finally:
        if saved is None:
            del os.environ["CLAUDE_TRACE_ANCHOR_DIR"]
        else:
            os.environ["CLAUDE_TRACE_ANCHOR_DIR"] = saved


# ── AC 3 — the run ────────────────────────────────────────────────────────────────────────
def test_ac3_new_session_budget_flag_no_skip_permissions_in_the_task_worktree(tmp_path):
    project, checkout = _project(tmp_path, worktree=True)
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_row(checkout)
    [call] = _calls(calls)
    assert call["argv"] == ["-p", "/verify T951", "--max-budget-usd", "2", "--output-format", "json"]
    assert not any(a in ("--resume", "-r", "--continue", "-c", "--dangerously-skip-permissions")
                   for a in call["argv"])
    assert Path(call["cwd"]).resolve() == checkout.resolve()
    assert call["child_flag"] == "1"
    # The run's own hooks resolve their project from its cwd, not from the Supervisor's.
    assert call["project_dir"] is None


def test_ac3_budget_is_a_default_the_user_can_change(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY_BUDGET_USD="0.75"))
    _wait_row(checkout)
    argv = _calls(calls)[0]["argv"]
    assert argv[argv.index("--max-budget-usd") + 1] == "0.75"


def test_ac3_log_is_under_verify_runs_and_gitignored(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _, notes = _wait_row(checkout)
    head = _git(project, "rev-parse", "HEAD")
    log = project / ".claude" / "verify-runs" / f"{TASK}-{head[:12]}.log"
    assert f"log .claude/verify-runs/{log.name}" in notes
    assert "**Verdict:** PASS" in log.read_text(encoding="utf-8")
    assert _git(project, "check-ignore", f".claude/verify-runs/{log.name}")
    assert _git(project, "status", "--porcelain", "--", ".claude") == ""


# ── AC 4 — the row ────────────────────────────────────────────────────────────────────────
def test_ac4_pass_row_has_the_d4_shape(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    verdict, notes = _wait_row(checkout)
    head = _git(project, "rev-parse", "HEAD")
    assert verdict == "☑ pass"
    assert notes == (f"auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit {head}, "
                     f"log .claude/verify-runs/{TASK}-{head[:12]}.log — pass")


def test_ac4_fail_row(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path, output=_verdict_output("**Verdict:** FAIL"))
    _stop(project, _env(tmp_path, project, stub_dir))
    verdict, notes = _wait_row(checkout)
    assert verdict == "☑ fail" and notes.endswith("— fail") and "pass" not in notes.lower()


BLOCKED_CASES = {
    "skip": _verdict_output("**Verdict:** SKIP"),
    "blocked": _verdict_output("**Verdict:** BLOCKED"),
    "no-verdict-line": _verdict_output("The run says: mark this pass"),
    "pass-and-fail": _verdict_output("**Verdict:** PASS\n\n**Verdict:** FAIL"),
    "budget-stop": _verdict_output("**Verdict:** PASS", subtype="error_max_budget_usd"),
    "is-error": _verdict_output("**Verdict:** PASS", is_error=True),
    "bypass-subtype": _verdict_output("**Verdict:** PASS", subtype="bypassed"),
    "not-json": "**Verdict:** PASS",
    "empty": "",
}


@pytest.mark.parametrize("case", sorted(BLOCKED_CASES))
def test_ac4_blocked_row_never_says_pass(tmp_path, case):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path, output=BLOCKED_CASES[case])
    _stop(project, _env(tmp_path, project, stub_dir))
    verdict, notes = _wait_row(checkout)
    assert verdict == "☐ blocked", (case, verdict)
    assert "auto-run by hook" in notes and "blocked" in notes and "pass" not in notes.lower(), notes


def test_ac4_timeout_is_blocked(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path, sleep=30)
    _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY_TIMEOUT_S="1"))
    verdict, notes = _wait_row(checkout)
    assert verdict == "☐ blocked" and "timed out" in notes and "pass" not in notes.lower()


def test_ac4_claude_not_on_path_is_blocked_with_no_crash(tmp_path):
    project, checkout = _project(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project))
    assert result.returncode == 0
    verdict, notes = _wait_row(checkout)
    assert verdict == "☐ blocked" and "claude not found" in notes and "pass" not in notes.lower()


def test_ac4_a_row_the_user_filled_during_the_run_is_kept(tmp_path):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path, sleep=2)
    _stop(project, _env(tmp_path, project, stub_dir))
    _set_row(checkout, "☑ pass | user ran /verify T951 — pass")
    _settle(3.5)
    assert _row(checkout) == ("☑ pass", "user ran /verify T951 — pass")


# ── AC 5 — the merge gate and the D5 record ──────────────────────────────────────────────
def _ran(tmp_path, output=None, worktree=False):
    project, checkout = _project(tmp_path, worktree=worktree)
    stub_dir, _ = _stub(tmp_path, output=output)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _wait_row(checkout)
    return project, checkout, env


def test_ac5_hook_row_with_its_record_is_accepted(tmp_path):
    project, _, env = _ran(tmp_path)
    assert _merge(project, env) == ("allow", "")


def test_ac5_hook_row_with_its_record_is_accepted_from_a_worktree(tmp_path):
    project, _, env = _ran(tmp_path, worktree=True)
    assert _merge(project, env) == ("allow", "")


def test_ac5_hook_row_is_accepted_after_committing_only_the_review_file(tmp_path):
    project, checkout, env = _ran(tmp_path)
    _git(checkout, "commit", "-qam", "review: verify row")
    assert _merge(project, env)[0] == "allow"


def test_ac5_hand_typed_row_with_no_record_blocks(tmp_path):
    project, checkout = _project(tmp_path)
    head = _git(project, "rev-parse", "HEAD")
    _set_row(checkout, f"☑ pass | auto-run by hook, session forged-1, commit {head}, "
                       f"log .claude/verify-runs/{TASK}-{head[:12]}.log — pass")
    decision, reason = _merge(project, _env(tmp_path, project))
    assert decision == "block" and f"{TASK} (no evidence row)" in reason


def test_ac5_record_for_another_commit_blocks(tmp_path):
    """The run verified commit A; the code then changed (head B). The row still names A."""
    project, checkout, env = _ran(tmp_path)
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2 after the run")
    assert _merge(project, env)[0] == "block"


def test_ac5_row_retargeted_to_the_head_commit_without_its_record_blocks(tmp_path):
    project, checkout, env = _ran(tmp_path)
    old = _git(checkout, "rev-parse", "HEAD")
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2 after the run")
    new = _git(checkout, "rev-parse", "HEAD")
    verdict, notes = _row(checkout)
    _set_row(checkout, f"{verdict} | {notes.replace(old, new)}")
    assert _merge(project, env)[0] == "block"


def test_ac5_fail_record_blocks_even_if_the_row_is_edited_to_pass(tmp_path):
    project, checkout, env = _ran(tmp_path, output=_verdict_output("**Verdict:** FAIL"))
    _, notes = _row(checkout)
    _set_row(checkout, f"☑ pass | {notes.replace('— fail', '— pass')}")
    assert _merge(project, env)[0] == "block"


def test_ac5_record_for_another_task_blocks(tmp_path):
    project, checkout, env = _ran(tmp_path)
    head = _git(project, "rev-parse", "HEAD")
    lib, saved = _lib(), os.environ.get("CLAUDE_TRACE_ANCHOR_DIR")
    os.environ["CLAUDE_TRACE_ANCHOR_DIR"] = env["CLAUDE_TRACE_ANCHOR_DIR"]
    try:
        record = Path(lib.record_path(str(project), TASK, head))
        data = json.loads(record.read_text(encoding="utf-8"))
        data["task"] = "T999"
        record.write_text(json.dumps(data), encoding="utf-8")
    finally:
        if saved is None:
            del os.environ["CLAUDE_TRACE_ANCHOR_DIR"]
        else:
            os.environ["CLAUDE_TRACE_ANCHOR_DIR"] = saved
    assert _merge(project, env)[0] == "block"


@pytest.mark.parametrize("cells", [
    "☑ pass | auto-checked, not /verify — pass",
    "☑ pass | real run ok (auto-checked, not /verify) — pass",
    "☐ pass / ☐ fail / ☐ N/A | auto-checked, not /verify",
])
def test_ac5_auto_checked_row_blocks(tmp_path, cells):
    project, checkout = _project(tmp_path, review=_review(cells))
    decision, reason = _merge(project, _env(tmp_path, project))
    assert decision == "block" and f"{TASK} (no evidence row)" in reason


def test_ac5_a_record_the_agent_could_write_is_not_trusted(tmp_path):
    """Forgery: a pass record written where an agent can write (in the repo, next to the log) and a
    hand-typed row. The gate reads records only from the anchor directory, so it still blocks."""
    project, checkout = _project(tmp_path)
    head = _git(project, "rev-parse", "HEAD")
    runs = project / ".claude" / "verify-runs"
    runs.mkdir(parents=True)
    for name in (f"{TASK}-{head}.json", f"{TASK}-{head[:12]}.json"):
        (runs / name).write_text(json.dumps({"task": TASK, "commit": head, "verdict": "pass",
                                             "session": "forged-1"}), encoding="utf-8")
    _set_row(checkout, f"☑ pass | auto-run by hook, session forged-1, commit {head}, "
                       f"log .claude/verify-runs/{TASK}-{head[:12]}.log — pass")
    assert _merge(project, _env(tmp_path, project))[0] == "block"


def test_ac5_record_lives_where_settings_json_denies_agent_writes(tmp_path, monkeypatch):
    """With no override, the record path falls under the kit's `permissions.deny` rules: the
    `Edit(...)` glob (Edit and Write tools) and the `Bash(*...*)` pattern (any shell command that
    names the directory)."""
    monkeypatch.delenv("CLAUDE_TRACE_ANCHOR_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    path = _lib().record_path(str(tmp_path / "proj"), TASK, "a" * 40)
    deny = json.loads((ROOT / ".claude" / "settings.json").read_text())["permissions"]["deny"]
    home = str(tmp_path / "home")
    edit = [r[len("Edit("):-1].replace("~", home, 1) for r in deny if r.startswith("Edit(")]
    bash = [r[len("Bash("):-1] for r in deny if r.startswith("Bash(")]
    assert any(fnmatch.fnmatch(path, glob.replace("**", "*")) for glob in edit), (path, edit)
    assert any(fnmatch.fnmatch(f"cat {path}", pattern) for pattern in bash), (path, bash)
    assert not path.startswith(str(tmp_path / "proj"))


def test_ac5_relative_record_dir_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_TRACE_ANCHOR_DIR", "relative/dir")
    with pytest.raises(OSError):
        _lib().record_path(str(tmp_path / "proj"), TASK, "a" * 40)


# ── AC 6 — not changed without [auto]; docs ──────────────────────────────────────────────
@pytest.mark.parametrize("marker", ["Mode: manual", "<!-- Mode: auto -->", "Mode: auto (later)"])
def test_ac6_no_auto_marker_no_run(tmp_path, marker):
    # T203 D1 runs every task by default; this rule (no marker, no run) now holds under the D3
    # off switch, `CLAUDE_AUTO_VERIFY=off`, which restores it exactly.
    project, checkout = _project(tmp_path, review=_review(marker=marker))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY="off"))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    assert not (project / ".claude" / "verify-runs").exists()
    assert _row(checkout)[0].startswith("☐ pass")


def test_ac6_auto_mode_check_stays_silent_inside_the_headless_run(tmp_path):
    """T180's auto-mode Stop hook must not block the `/verify` session's own stop (it would tell
    that session to fix the final report)."""
    project, _ = _project(tmp_path)
    env = _env(tmp_path, project)
    hook = project / ".claude" / "hooks" / "stop_auto_mode_check.py"
    plain = subprocess.run([sys.executable, str(hook)], input="{}", capture_output=True, text=True,
                           cwd=project, env=env, timeout=30)
    assert json.loads(plain.stdout)["decision"] == "block", "fixture must fail the check"
    child = subprocess.run([sys.executable, str(hook)], input="{}", capture_output=True, text=True,
                           cwd=project, env={**env, "CLAUDE_AUTO_VERIFY_RUN": "1"}, timeout=30)
    assert child.returncode == 0 and not child.stdout.strip()


def _auto_mode_section():
    text = TRACKS_MD.read_text(encoding="utf-8")
    m = re.search(r"^## Auto mode\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m
    return m.group(1)


def test_ac6_tracks_md_names_the_auto_verify_step():
    section = _auto_mode_section()
    m = re.search(r"^### Auto verify[^\n]*\n(.*?)(?=^##+ |\Z)", section, re.M | re.S)
    assert m, "no `### Auto verify` subsection in `## Auto mode`"
    body = re.sub(r"\s+", " ", m.group(1))
    for needle in ("`.claude/hooks/stop_auto_verify.py`", "`/verify", "--max-budget-usd 2",
                   "`.claude/verify-runs/", "`auto-run by hook", "record", "never the Supervisor",
                   "merge"):
        assert needle in body, needle
    never = re.sub(r"\s+", " ", section.split("### Never in auto mode", 1)[1])
    assert "The one exception the gate can check is an `auto-run by hook` row" in never


def test_ac6_agents_md_stays_within_its_line_cap():
    assert len((ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()) <= 200


def test_ac6_glossary_auto_verify():
    rows = [l for l in SPEC.read_text(encoding="utf-8").splitlines() if l.startswith("| Auto verify |")]
    assert len(rows) == 1
    assert "Not the Supervisor's `auto-checked` real-run check (T180)" in rows[0]
    assert "T182" in rows[0] and "`auto-run by hook`" in rows[0]


def test_ac6_settings_wires_the_hook_on_stop():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    commands = [h["command"] for e in settings["hooks"]["Stop"] for h in e["hooks"]]
    assert f'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/{HOOK}' in commands
    assert (HOOKS / HOOK).is_file()


# ══ T188 — both tracks, one reader, and the result lands in the report ════════════════════
# AC 1 — `.claude/hooks/lib/auto_mode.py` is the one reader of auto-mode tasks: per task its ID,
#        its track and the file that holds its report. Both Stop hooks call it.
# AC 2 — a `Track: minimal` row at Ready for Review whose Decision record carries `Mode: auto`
#        starts exactly one detached run, with the extended track's log path and lock.
# AC 3 — the run writes the D3 `verify:` line into that record for pass, fail and blocked; a
#        blocked line never says "pass"; a `Checked:` line the user wrote is left as it was.
# AC 4 — extended track unchanged: `Mode: auto` inside an HTML comment is not auto, and a copy of
#        either template starts no run.
# AC 5 — the merge gate accepts a minimal `verify:` line only with a matching run record for the
#        head commit: no record, another commit, a fail record and a hand-typed line all block.
# AC 6 — with no marker, neither track starts a run.
# AC 7 — when the run ends, the `Not done:` auto verify slot holds the result and no longer says
#        "running"; the merge clause is unchanged; a slot the user wrote is left alone.
SESSION_ID = "bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4"
RESULT_CELL = {"pass": "☑ pass", "fail": "☑ fail", "blocked": "☐ blocked"}
VERDICT_OUTPUT = {"pass": None, "fail": _verdict_output("**Verdict:** FAIL"), "blocked": "not json"}
# a run whose output is not JSON reports no session id
RUN_SESSION = {"pass": SESSION_ID, "fail": SESSION_ID, "blocked": "none"}


def _auto_mode():
    sys.path.insert(0, str(HOOKS / "lib"))
    try:
        import auto_mode  # noqa: WPS433
        return auto_mode
    finally:
        sys.path.pop(0)


def _record_body(checkout, task=MIN_TASK):
    text = (checkout / "tasks" / "MINIMAL_LOG.md").read_text(encoding="utf-8")
    assert f"## {task} — " in text, text
    return text.split(f"## {task} — ", 1)[1].split("\n## ", 1)[0]


def _verify_line(checkout, task=MIN_TASK):
    """The Decision record's `verify:` line, stripped, or `''` when it has none."""
    lines = [l.strip() for l in _record_body(checkout, task).splitlines()
             if re.match(r"\s*[-*]?\s*verify:", l)]
    assert len(lines) <= 1, lines
    return lines[0] if lines else ""


def _wait_verify_line(checkout, task=MIN_TASK):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        line = _verify_line(checkout, task)
        if "auto-run by hook" in line:
            return line
        time.sleep(0.1)
    raise AssertionError(f"the hook never wrote the record's verify line: {_verify_line(checkout)!r}")


def _set_verify_line(checkout, line, task=MIN_TASK):
    path = checkout / "tasks" / "MINIMAL_LOG.md"
    text = path.read_text(encoding="utf-8")
    if re.search(r"^\s*[-*]?\s*verify:.*$", text, re.M):
        text = re.sub(r"^\s*[-*]?\s*verify:.*$", line, text, count=1, flags=re.M)
    else:
        text = text.replace("**Checked:**\n", f"**Checked:**\n{line}\n", 1)
    path.write_text(text, encoding="utf-8")


def _not_done(checkout, task=None):
    """The report's `Not done:` line — the extended review file's, or a Decision record's."""
    if task is None:
        text = (checkout / "tasks" / f"TASK_REVIEW_{TASK}.md").read_text(encoding="utf-8")
        body = text.split("## Auto decisions", 1)[1].split("\n## ", 1)[0]
    else:
        body = _record_body(checkout, task)
    lines = [l.strip() for l in body.splitlines()
             if l.lstrip().startswith(("Not done:", "**Not done:**"))]
    assert len(lines) == 1, lines
    return lines[0]


def _wait_slot(checkout, task=None):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        line = _not_done(checkout, task)
        if re.search(r"auto verify: [☑☐]", line):
            return line
        time.sleep(0.1)
    raise AssertionError(f"the auto verify slot was never written: {_not_done(checkout, task)!r}")


def _run_log(project, task, checkout=None):
    head = _git(checkout or project, "rev-parse", "HEAD")
    return (project / ".claude" / "verify-runs" / f"{task}-{head[:12]}.log").read_text(encoding="utf-8")


# ── AC 1 — one reader for both hooks ──────────────────────────────────────────────────────
def test_ac1_the_reader_returns_each_task_with_its_track_and_report_file(tmp_path):
    project, _ = _project(tmp_path, rows=(RFR_ROW, MIN_ROW), minimal_log=_log())
    am = _auto_mode()
    dirs = am.tasks_dirs(str(project))
    kanban = (project / "PROJECT_KANBAN.md").read_text(encoding="utf-8")
    found = {}
    for task_id, row in am.board_rows(kanban, ("Ready for Review",)):
        task = am.resolve(task_id, row, dirs)
        found[task_id] = (task.track, task.report_path, task.marker, task.marked)
    assert found[TASK] == ("extended", str(project / "tasks" / f"TASK_REVIEW_{TASK}.md"), True, True)
    assert found[MIN_TASK] == ("minimal", str(project / "tasks" / "MINIMAL_LOG.md"), True, True)


def test_ac1_the_reader_matches_a_record_by_task_id_never_by_position(tmp_path):
    """The newest record belongs to another task; the row's record is the older one."""
    project, _ = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log(
        _record(task="T953", marker="Mode: manual"), _record()))
    am = _auto_mode()
    dirs = am.tasks_dirs(str(project))
    assert am.resolve(MIN_TASK, MIN_ROW, dirs).marker is True
    assert am.resolve("T953", MIN_ROW, dirs).marker is False


def test_ac1_two_records_for_one_task_the_newest_wins(tmp_path):
    project, _ = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log(
        _record(checked=("- Suite: `pytest -q` — the re-run",)),
        _record(marker="Mode: manual", checked=("- Suite: `pytest -q` — the first run",))))
    task = _auto_mode().resolve(MIN_TASK, MIN_ROW, _auto_mode().tasks_dirs(str(project)))
    assert task.marker is True
    assert "the re-run" in task.body and "the first run" not in task.body


def _code(path):
    """A hook's source with its docstrings and comments removed — what actually runs, so a
    docstring that *describes* the reader is not mistaken for a second copy of it."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(getattr(body[0], "value", None), ast.Constant) \
                and isinstance(body[0].value.value, str):
            body.pop(0)
    return ast.unparse(tree)


def test_ac1_neither_stop_hook_holds_a_second_copy_of_the_reader():
    for name in (HOOK, "stop_auto_mode_check.py"):
        code = _code(HOOKS / name)
        assert "import auto_mode" in code, f"{name} does not use the shared reader"
        for duplicate in (r"\*\*([A-Za-z]+-?\d+)\*\*", "<!--.*?-->", r"Track:\s*minimal",
                          "Track: minimal", '"worktree", "list"', "### Ready for Review"):
            assert duplicate not in code, f"{name} still holds its own `{duplicate}`"


# ── AC 2 — the minimal-track run ──────────────────────────────────────────────────────────
def test_ac2_a_minimal_track_row_starts_one_detached_run(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    stub_dir, calls = _stub(tmp_path, sleep=3)
    result, elapsed = _stop(project, _env(tmp_path, project, stub_dir))
    assert result.returncode == 0 and not result.stdout.strip(), result
    assert elapsed < 2.5, f"the Stop hook waited for the run ({elapsed:.1f}s)"
    assert MIN_TASK in result.stderr and "auto verify started" in result.stderr
    head = _git(project, "rev-parse", "HEAD")
    assert _wait_verify_line(checkout) == (
        f"- verify: ☑ pass — auto-run by hook, session {SESSION_ID}, commit {head}, "
        f"log .claude/verify-runs/{MIN_TASK}-{head[:12]}.log")
    [call] = _calls(calls)
    assert call["argv"] == ["-p", f"/verify {MIN_TASK}", "--max-budget-usd", "2",
                            "--output-format", "json"]
    assert call["parent_sid"] == call["parent_pid"] != os.getsid(0)  # detached (setsid)
    log = project / ".claude" / "verify-runs" / f"{MIN_TASK}-{head[:12]}.log"
    assert log.is_file() and _git(project, "check-ignore", f".claude/verify-runs/{log.name}")


def test_ac2_a_second_stop_on_the_same_commit_starts_nothing_on_the_minimal_track(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    stub_dir, calls = _stub(tmp_path, sleep=1)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _stop(project, env)  # while the first run is still going
    _wait_verify_line(checkout)
    _stop(project, env)  # after it finished, same commit
    _settle()
    assert len(_calls(calls)) == 1
    assert _verify_line(checkout).count("auto-run by hook") == 1


def test_ac2_a_record_in_a_worktree_is_resolved_like_evidence(tmp_path):
    row = f"{MIN_ROW} | Started 2026-10-29: branch `feat/t951` in `../wt-t951`"  # T203 sec review
    project, checkout = _project(tmp_path, rows=(row,), review_file=False, worktree=True,
                                 minimal_log=_log())
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert _git(checkout, "rev-parse", "HEAD") in _wait_verify_line(checkout)
    [call] = _calls(calls)
    assert Path(call["cwd"]).resolve() == checkout.resolve()


def test_ac2_a_minimal_and_an_extended_task_both_due_get_their_own_run(tmp_path):
    project, checkout = _project(tmp_path, rows=(RFR_ROW, MIN_ROW), minimal_log=_log())
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_row(checkout)
    _wait_verify_line(checkout)
    head = _git(project, "rev-parse", "HEAD")
    assert sorted(c["argv"][1] for c in _calls(calls)) == [f"/verify {TASK}", f"/verify {MIN_TASK}"]
    assert sorted(p.name for p in (project / ".claude" / "verify-runs").iterdir()) == [
        f"{TASK}-{head[:12]}.log", f"{MIN_TASK}-{head[:12]}.log"]


def test_ac2_no_decision_record_is_one_stderr_line_and_no_run(tmp_path):
    project, _ = _project(tmp_path, rows=(MIN_ROW,), review_file=False)
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    assert not (project / ".claude" / "verify-runs").exists()
    lines = [l for l in result.stderr.splitlines() if "stop_auto_verify" in l]
    assert len(lines) == 1 and MIN_TASK in lines[0] and "MINIMAL_LOG.md" in lines[0], result.stderr


def test_ac2_a_record_with_no_checked_field_is_one_stderr_line_and_no_run(tmp_path):
    record = _record().replace("**Checked:**\n- Suite: `pytest -q` — 12 passed\n", "")
    project, _ = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log(record))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    lines = [l for l in result.stderr.splitlines() if "stop_auto_verify" in l]
    assert len(lines) == 1 and "`Checked:`" in lines[0], result.stderr


# ── AC 3 — the D3 `verify:` line ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("verdict", sorted(VERDICT_OUTPUT))
def test_ac3_the_record_gets_the_d3_line_for_pass_fail_and_blocked(tmp_path, verdict):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    stub_dir, _ = _stub(tmp_path, output=VERDICT_OUTPUT[verdict])
    _stop(project, _env(tmp_path, project, stub_dir))
    line = _wait_verify_line(checkout)
    head = _git(project, "rev-parse", "HEAD")
    assert line.startswith(f"- verify: {RESULT_CELL[verdict]} — auto-run by hook, session "), line
    assert f"commit {head}" in line, line
    assert f"log .claude/verify-runs/{MIN_TASK}-{head[:12]}.log" in line, line
    if verdict != "pass":
        assert "pass" not in line.lower(), line


def test_ac3_the_checked_lines_the_user_wrote_are_left_exactly_as_they_were(tmp_path):
    mine = ["- New test `test_sort_is_alphabetical` — failed before the change, passes after",
            "- Real run: `python3 -m app sort` — printed `Ann, Bob`"]
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                 minimal_log=_log(_record(checked=mine)))
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_verify_line(checkout)
    body = _record_body(checkout)
    for line in mine:
        assert line in body, line
    # inside the `Checked:` field: after the user's own bullets, before the next field
    assert body.index(mine[0]) < body.index(mine[1]) < body.index("- verify:")
    assert body.index("- verify:") < body.index("**Files:**") < body.index("**Not done:**")
    assert "**Files:** `src/app.py`" in body and "**Decisions:**" in body


def test_ac3_a_verify_line_the_user_filled_is_never_run_over(tmp_path):
    mine = "- verify: ☑ pass — user ran /verify T952 — pass"
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                 minimal_log=_log(_record(checked=(mine,))))
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert _calls(calls) == [] and _verify_line(checkout) == mine


def test_ac3_an_earlier_auto_line_for_other_code_is_replaced_not_duplicated(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    first = _wait_verify_line(checkout)
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2")
    head = _git(checkout, "rev-parse", "HEAD")
    _stop(project, env)
    deadline = time.monotonic() + WAIT_S
    while head not in _verify_line(checkout) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert head in _verify_line(checkout) and head not in first
    assert len(_calls(calls)) == 2


def test_ac3_committing_only_the_record_does_not_start_a_new_run(tmp_path):
    """The Supervisor commits the hook-written line: the verified code did not change."""
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _wait_verify_line(checkout)
    _git(checkout, "commit", "-qam", "record: the verify line")
    _stop(project, env)
    _settle()
    assert len(_calls(calls)) == 1


# ── AC 4 — the extended track is unchanged; a template copy is not marked ────────────────
def test_ac4_a_review_file_copied_from_the_template_starts_no_run(tmp_path):
    # T203 D1 runs every task by default; this rule (no marker, no run) now holds under the D3
    # off switch, `CLAUDE_AUTO_VERIFY=off`, which restores it exactly.
    project, _ = _project(tmp_path, review=(ROOT / "templates" / "TASK_REVIEW_template.md"
                                            ).read_text(encoding="utf-8"))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY="off"))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    assert not (project / ".claude" / "verify-runs").exists()


def test_ac4_a_minimal_log_copied_from_the_template_starts_no_run(tmp_path):
    project, _ = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                          minimal_log=(ROOT / "templates" / "MINIMAL_LOG_template.md"
                                       ).read_text(encoding="utf-8"))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    assert not (project / ".claude" / "verify-runs").exists()


# ── AC 5 — the merge gate reads a minimal line only with its run record ──────────────────
# T203 security review: a worktree is chosen by the branch its board row names, so a worktree
# fixture names `_project`'s branch (`feat/t951`) in the row.
MIN_ROW_WT = f"{MIN_ROW} | Started 2026-10-29: branch `feat/t951` in `../wt-t951`"


def _ran_minimal(tmp_path, output=None, worktree=False):
    project, checkout = _project(tmp_path, rows=(MIN_ROW_WT if worktree else MIN_ROW,),
                                 review_file=False, worktree=worktree,
                                 minimal_log=_log())
    stub_dir, _ = _stub(tmp_path, output=output)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _wait_verify_line(checkout)
    return project, checkout, env


def test_ac5_a_minimal_line_with_its_record_is_accepted(tmp_path):
    project, _, env = _ran_minimal(tmp_path)
    assert _merge(project, env) == ("allow", "")


def test_ac5_a_minimal_line_from_a_worktree_record_is_accepted(tmp_path):
    project, _, env = _ran_minimal(tmp_path, worktree=True)
    assert _merge(project, env) == ("allow", "")


def test_ac5_a_minimal_line_with_no_record_blocks(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    head = _git(project, "rev-parse", "HEAD")
    _set_verify_line(checkout, f"- verify: ☑ pass — auto-run by hook, session forged-1, "
                               f"commit {head}, log .claude/verify-runs/{MIN_TASK}-{head[:12]}.log")
    decision, reason = _merge(project, _env(tmp_path, project))
    assert decision == "block" and f"{MIN_TASK} (no evidence row)" in reason


def test_ac5_a_minimal_record_for_another_commit_blocks(tmp_path):
    project, checkout, env = _ran_minimal(tmp_path)
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2 after the run")
    assert _merge(project, env)[0] == "block"


def test_ac5_a_minimal_fail_record_blocks_even_if_the_line_is_edited_to_pass(tmp_path):
    project, checkout, env = _ran_minimal(tmp_path, output=_verdict_output("**Verdict:** FAIL"))
    _set_verify_line(checkout, _verify_line(checkout).replace("☑ fail", "☑ pass"))
    assert _merge(project, env)[0] == "block"


@pytest.mark.parametrize("line", [
    "- verify: ☑ pass — user ran /verify T952 — pass",
    "- verify: ☑ pass — auto-checked, not /verify — pass",
    "- verify: ☐ pass / ☐ fail — not run yet",
])
def test_ac5_a_hand_typed_minimal_line_blocks(tmp_path, line):
    project, _ = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                          minimal_log=_log(_record(checked=(line,))))
    decision, reason = _merge(project, _env(tmp_path, project))
    assert decision == "block" and f"{MIN_TASK} (no evidence row)" in reason


def test_ac5_a_record_the_agent_could_write_is_not_trusted_on_the_minimal_track(tmp_path):
    """Forgery: a pass record written where an agent can write (in the repo, next to the log) plus
    a hand-typed line. The gate reads records only from the anchor directory, so it still blocks."""
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    head = _git(project, "rev-parse", "HEAD")
    runs = project / ".claude" / "verify-runs"
    runs.mkdir(parents=True)
    for name in (f"{MIN_TASK}-{head}.json", f"{MIN_TASK}-{head[:12]}.json"):
        (runs / name).write_text(json.dumps({"task": MIN_TASK, "commit": head, "verdict": "pass",
                                             "session": "forged-1"}), encoding="utf-8")
    _set_verify_line(checkout, f"- verify: ☑ pass — auto-run by hook, session forged-1, "
                               f"commit {head}, log .claude/verify-runs/{MIN_TASK}-{head[:12]}.log")
    assert _merge(project, _env(tmp_path, project))[0] == "block"


# ── AC 6 — no marker, no run, on either track ────────────────────────────────────────────
@pytest.mark.parametrize("marker", ["Mode: manual", "<!-- Mode: auto -->", "Mode: auto (later)"])
def test_ac6_a_minimal_record_without_the_marker_starts_no_run(tmp_path, marker):
    # T203 D1 runs every task by default; this rule (no marker, no run) now holds under the D3
    # off switch, `CLAUDE_AUTO_VERIFY=off`, which restores it exactly.
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                 minimal_log=_log(_record(marker=marker)))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY="off"))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    assert not (project / ".claude" / "verify-runs").exists()
    assert _verify_line(checkout) == ""
    assert _not_done(checkout, MIN_TASK) == f"**Not done:** {NOT_DONE}"


# ── AC 7 — the report stops saying "running" ─────────────────────────────────────────────
@pytest.mark.parametrize("verdict", sorted(VERDICT_OUTPUT))
def test_ac7_the_extended_report_slot_names_the_result(tmp_path, verdict):
    project, checkout = _project(tmp_path)
    stub_dir, _ = _stub(tmp_path, output=VERDICT_OUTPUT[verdict])
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_row(checkout)
    head = _git(project, "rev-parse", "HEAD")
    slot = _wait_slot(checkout)
    assert slot.startswith("Not done: merge (yours); "), slot
    assert f"auto verify: {RESULT_CELL[verdict]} (session {RUN_SESSION[verdict]}, " \
           f"commit {head}, log .claude/verify-runs/{TASK}-{head[:12]}.log)" in slot, slot
    assert "running (T182)" not in slot


@pytest.mark.parametrize("verdict", sorted(VERDICT_OUTPUT))
def test_ac7_the_minimal_record_slot_names_the_result(tmp_path, verdict):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log())
    stub_dir, _ = _stub(tmp_path, output=VERDICT_OUTPUT[verdict])
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_verify_line(checkout)
    head = _git(project, "rev-parse", "HEAD")
    slot = _wait_slot(checkout, MIN_TASK)
    assert slot.startswith("**Not done:** merge (yours); "), slot
    assert f"auto verify: {RESULT_CELL[verdict]} (session {RUN_SESSION[verdict]}, " \
           f"commit {head}, log .claude/verify-runs/{MIN_TASK}-{head[:12]}.log)" in slot, slot
    assert "running (T182)" not in slot


def test_ac7_the_template_placeholder_slot_is_the_unwritten_state(tmp_path):
    placeholder = ("merge (yours); <auto verify: running (T182) | auto verify: <result> "
                   "| /verify (yours)>")
    project, checkout = _project(tmp_path, review=_review(not_done=placeholder))
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_row(checkout)
    slot = _wait_slot(checkout)
    assert "<" not in slot and ">" not in slot, slot
    assert slot.startswith("Not done: merge (yours); auto verify: ☑ pass (session "), slot


def test_ac7_a_slot_the_user_wrote_is_left_alone_and_the_reason_goes_in_the_log(tmp_path):
    mine = "merge (yours); /verify (yours)"
    project, checkout = _project(tmp_path, review=_review(not_done=mine))
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_row(checkout)
    _settle()
    assert _not_done(checkout) == f"Not done: {mine}"
    assert "auto verify slot" in _run_log(project, TASK)


@pytest.mark.parametrize("lines,count", [(f"Not done: {NOT_DONE}\nNot done: merge (yours)", 2),
                                         ("", 0)])
def test_ac7_no_single_not_done_line_writes_nothing_and_says_which_in_the_log(tmp_path, lines, count):
    review = _review().replace(f"Not done: {NOT_DONE}", lines)
    project, checkout = _project(tmp_path, review=review)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_row(checkout)
    _settle()
    log = _run_log(project, TASK)
    assert f"{count} `Not done:`" in log, log
    assert (checkout / "tasks" / f"TASK_REVIEW_{TASK}.md").read_text(
        encoding="utf-8").count("auto verify: ☑") == 0


# ── AC 8 — the doctrine says the minimal track is included ───────────────────────────────
def test_ac8_tracks_md_says_both_tracks_and_where_each_result_lands():
    section = _auto_mode_section()
    m = re.search(r"^### Auto verify[^\n]*\n(.*?)(?=^##+ |\Z)", section, re.M | re.S)
    assert m, "no `### Auto verify` subsection in `## Auto mode`"
    body = re.sub(r"\s+", " ", m.group(1))
    for needle in ("minimal track", "`tasks/MINIMAL_LOG.md`", "`Checked:`", "`Not done:`",
                   "`.claude/hooks/lib/auto_mode.py`", "T188"):
        assert needle in body, needle


def test_ac8_glossary_auto_verify_covers_both_tracks():
    rows = [l for l in SPEC.read_text(encoding="utf-8").splitlines()
            if l.startswith("| Auto verify |")]
    assert len(rows) == 1
    assert "both tracks" in rows[0] and "T188" in rows[0], rows[0]
    assert "tasks/MINIMAL_LOG.md" in rows[0], rows[0]


# ══ T189 — auto close-out: after an auto verify pass the run moves the row to Done ═══════════
# AC 1 — a pass with its run record, complete Gate 5/6 evidence and a complete report moves the row
#        from Ready for Review to the top of Done, `- [x]`, with the D4 note; the rest of the row and
#        of the board is byte-identical; `**Last updated**` is that date.
# AC 2 — a `fail` or `blocked` verdict leaves the board and the report's close-out lines untouched.
# AC 3 — D2: a blank tests row, a blank design row, a `☐ N/A` design row with no reason (and on the
#        minimal track, no `New test` line) each keep the row and write `done not moved: <reason>`.
# AC 4 — D3: no run record, a record for another commit, a fail record, or a hand-typed
#        `auto-run by hook` result each keep the row.
# AC 6 — the detached run issues no git command that writes; `### Stops that stay` is unchanged.
# AC 7 — the D8 `Closed:` line once (extended and minimal); a stop writes `Paused: done not moved —`;
#        a line the user wrote is never rewritten.
# AC 8 — D9: one test per missing report field; a complete report moves the row.
MEMORY = "Memory: nothing new"
COMPLETE = _review(memory=MEMORY)
DONE_ROW_BEFORE = "- [x] **T900** — An older task | Supervisor | C1 | Risk: Low | P2"
STOPS_THAT_STAY_SHA256 = "774b98a717e3f90b52929e2f73a91386af8b29c9d27ea88b3b74db75e35045ba"
CLOSE_TERMINAL = ("moved to Done", "done not moved", "report incomplete", "nothing moved")
WRITING_GIT = {"merge", "push", "commit", "checkout", "switch", "reset", "rebase", "pull", "add",
               "rm", "mv", "tag", "stash", "branch", "cherry-pick", "revert", "restore", "apply",
               "am", "fetch", "update-ref", "gc", "clean"}


def _today():
    import datetime
    return datetime.date.today().isoformat()


def _board_text(project):
    return (project / "PROJECT_KANBAN.md").read_text(encoding="utf-8")


def _with_done_row(project):
    """Put one older row under `### Done`, so the move can be seen to leave it as it was."""
    path = project / "PROJECT_KANBAN.md"
    path.write_text(_board_text(project).replace("### Done\n", f"### Done\n{DONE_ROW_BEFORE}\n"),
                    encoding="utf-8")
    _git(project, "commit", "-qam", "board: an older Done row")


def _section_rows(board, title):
    m = re.search(rf"^### {re.escape(title)}\n(.*?)(?=^###|\Z)", board, re.M | re.S)
    return [l for l in (m.group(1).splitlines() if m else []) if l.startswith("- ")]


def _wait_close(project, task, checkout=None):
    """The run log once the close-out wrote its terminal line (or the run's last line, for no pass)."""
    deadline = time.monotonic() + WAIT_S
    log = ""
    while time.monotonic() < deadline:
        try:
            log = _run_log(project, task, checkout)
        except FileNotFoundError:
            log = ""
        if any(marker in log for marker in CLOSE_TERMINAL):
            return log
        time.sleep(0.1)
    raise AssertionError(f"the close-out never finished; run log:\n{log}")


def _auto_section(checkout, task=TASK):
    text = (checkout / "tasks" / f"TASK_REVIEW_{task}.md").read_text(encoding="utf-8")
    return text.split("## Auto decisions", 1)[1].split("\n## ", 1)[0]


def _passed(tmp_path, review=COMPLETE, minimal_log=None, record="pass", record_commit=None,
            row_session=SESSION_ID, write_result=True):
    """The state an auto verify pass leaves behind, built directly: the result (hook-shaped), the
    report's slot, and — unless `record` is None — the run record for `record_commit` (default: head).
    For the close-out unit cases, where a real run could not produce the state under test."""
    minimal = minimal_log is not None
    if minimal:
        project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                     minimal_log=minimal_log)
        task, report = MIN_TASK, checkout / "tasks" / "MINIMAL_LOG.md"
    else:
        project, checkout = _project(tmp_path, review=review)
        task, report = TASK, checkout / "tasks" / f"TASK_REVIEW_{TASK}.md"
    head = _git(checkout, "rev-parse", "HEAD")
    log_rel = f".claude/verify-runs/{task}-{head[:12]}.log"
    lib = _lib()
    if write_result:
        if minimal:
            _set_verify_line(checkout, "- " + lib.record_line(head, "pass", row_session, log_rel), task)
        else:
            _set_row(checkout, " | ".join(lib.row_cells(head, "pass", row_session, log_rel)))
    report.write_text(report.read_text(encoding="utf-8").replace(
        RUNNING_SLOT, f"auto verify: ☑ pass (session {row_session}, commit {head}, log {log_rel})"),
        encoding="utf-8")
    env = _env(tmp_path, project)
    if record is not None:
        saved = os.environ.get("CLAUDE_TRACE_ANCHOR_DIR")
        os.environ["CLAUDE_TRACE_ANCHOR_DIR"] = env["CLAUDE_TRACE_ANCHOR_DIR"]
        try:
            lib.write_record(str(project), task, record_commit or head, record, SESSION_ID, log_rel)
        finally:
            if saved is None:
                del os.environ["CLAUDE_TRACE_ANCHOR_DIR"]
            else:
                os.environ["CLAUDE_TRACE_ANCHOR_DIR"] = saved
    return project, checkout, head, env, task, report


def _close(project, env, task, report, head, minimal=False, session=SESSION_ID):
    """Call the project's own `auto_closeout.close_out`, as the detached run does after a pass."""
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import auto_closeout as ac; "
            "print('RESULT', ac.close_out(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], "
            "sys.argv[6], sys.argv[7] == 'minimal'))")
    done = subprocess.run([sys.executable, "-c", code, str(project / ".claude" / "hooks" / "lib"),
                           str(project), task, str(report), head, session,
                           "minimal" if minimal else "extended"],
                          capture_output=True, text=True, cwd=project, env=env, timeout=60)
    assert done.returncode == 0, done.stderr
    return done.stdout


def _assert_not_moved(project, board_before, task=TASK):
    assert _board_text(project) == board_before, "the board changed"
    assert any(f"**{task}**" in r for r in _section_rows(board_before, "Ready for Review"))


# ── AC 1 — the gated Done move ────────────────────────────────────────────────────────────
def test_t189_ac1_a_pass_with_complete_evidence_moves_the_row_to_done(tmp_path):
    project, checkout = _project(tmp_path, review=COMPLETE)
    _with_done_row(project)
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    log = _wait_close(project, TASK)
    assert f"{TASK}: moved to Done" in log, log
    head, day = _git(checkout, "rev-parse", "HEAD"), _today()
    moved = (RFR_ROW.replace("- [ ]", "- [x]", 1)
             + f" | Done {day}: auto verify pass (session {SESSION_ID}, commit {head})")
    expected = (before.replace(f"{RFR_ROW}\n", "", 1)
                .replace("### Done\n", f"### Done\n{moved}\n", 1)
                .replace("**Last updated**: 2026-01-01", f"**Last updated**: {day}", 1))
    assert _board_text(project) == expected


def test_t189_ac1_a_minimal_track_pass_moves_its_row_to_done(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                 minimal_log=_log(_record(memory="nothing new")))
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert f"{MIN_TASK}: moved to Done" in _wait_close(project, MIN_TASK)
    board = _board_text(project)
    assert _section_rows(board, "Ready for Review") == []
    [row] = _section_rows(board, "Done")
    assert row.startswith(MIN_ROW.replace("- [ ]", "- [x]", 1) + f" | Done {_today()}: auto verify pass")


# ── AC 2 — fail and blocked leave the row exactly where it was ────────────────────────────
@pytest.mark.parametrize("verdict", ["fail", "blocked"])
def test_t189_ac2_a_fail_or_blocked_verdict_leaves_the_row_untouched(tmp_path, verdict):
    project, checkout = _project(tmp_path, review=COMPLETE)
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path, output=VERDICT_OUTPUT[verdict])
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_slot(checkout)
    _settle()
    assert _board_text(project) == before
    section = _auto_section(checkout)
    assert "Closed:" not in section and "done not moved" not in section
    assert not any(m in _run_log(project, TASK) for m in CLOSE_TERMINAL)


# ── AC 3 — Hard-Stop Gates 5 and 6 come first (D2) ───────────────────────────────────────
TESTS_ROW = "| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | tests/x.py |"
VISUAL_ROW = "| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI: a data script |"
D2_CASES = {
    "blank tests row": (TESTS_ROW, "| **New test(s) cover Acceptance Criteria (file paths pasted)** "
                                   "| ☐ pass / ☐ fail | [test file path(s) — required before Done] |",
                        "Gate 5: the tests row"),
    "blank design row": (VISUAL_ROW, "| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / "
                                     "☐ fail / ☐ N/A | [screenshot path or LLM verdict] |",
                         "Gate 6: the `UI: Visual regression` row is blank"),
    "N/A design row with no reason": (VISUAL_ROW, "| **UI: Visual regression (diff or verdict "
                                                  "pasted)** | ☐ N/A |  |",
                                      "Gate 6: the `UI: Visual regression` row has no reason"),
    "design row marked fail": (VISUAL_ROW, "| **UI: Visual regression (diff or verdict pasted)** | "
                                           "☑ fail | the header overflows at 375 px |",
                               "Gate 6: the `UI: Visual regression` row is `☑ fail`"),
}


@pytest.mark.parametrize("case", sorted(D2_CASES))
def test_t189_ac3_a_gate_5_or_6_gap_keeps_the_row_and_says_why(tmp_path, case):
    old, new, reason = D2_CASES[case]
    assert old in COMPLETE
    project, checkout = _project(tmp_path, review=COMPLETE.replace(old, new))
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    log = _wait_close(project, TASK)
    _assert_not_moved(project, before)
    assert f"done not moved: {reason}" in log, log
    assert f"Paused: done not moved — {reason}" in _auto_section(checkout)
    result, notes = _row(checkout)
    assert result == "☑ pass" and f"done not moved: {reason}" in notes, notes
    assert "Closed:" not in _auto_section(checkout)


def test_t189_ac3_no_test_run_in_the_trace_keeps_the_row(tmp_path):
    project, checkout = _project(tmp_path, review=COMPLETE)
    (project / "memory" / "event-trace" / f"{TASK}.jsonl").write_text("", encoding="utf-8")
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert f"done not moved: Gate 5: no test run in memory/event-trace/{TASK}.jsonl" in _wait_close(
        project, TASK)
    _assert_not_moved(project, before)


def test_t189_ac3_a_minimal_record_with_no_new_test_line_keeps_the_row(tmp_path):
    record = _record(checked=("- Suite: `pytest -q` — 12 passed",), memory="nothing new")
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log(record))
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    log = _wait_close(project, MIN_TASK)
    _assert_not_moved(project, before, MIN_TASK)
    assert "done not moved: Gate 5: no `New test` line" in log, log
    assert "done not moved: Gate 5" in _verify_line(checkout)
    assert "Paused: done not moved — Gate 5" in _record_body(checkout)


def test_t189_ac3_a_pure_backend_task_with_three_na_rows_and_a_reason_moves(tmp_path):
    """Edge case: `☐ N/A` with a written reason satisfies Gate 6 — the COMPLETE fixture's rows."""
    project, checkout, head, env, task, report = _passed(tmp_path)
    assert "RESULT True" in _close(project, env, task, report, head)


# ── AC 4 — the forgery guard (D3) ─────────────────────────────────────────────────────────
def test_t189_ac4_no_run_record_keeps_the_row(tmp_path):
    """End to end: the run cannot write its record (a relative anchor directory is refused)."""
    project, checkout = _project(tmp_path, review=COMPLETE)
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_TRACE_ANCHOR_DIR="relative/anchors"))
    log = _wait_close(project, TASK)
    assert "run record not written" in log and "done not moved: no run record" in log, log
    _assert_not_moved(project, before)


def test_t189_ac4_a_record_for_another_commit_keeps_the_row(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path, record_commit="a" * 40)
    before = _board_text(project)
    out = _close(project, env, task, report, head)
    assert "RESULT False" in out and "done not moved: no run record" in out, out
    _assert_not_moved(project, before)


def test_t189_ac4_a_fail_record_keeps_the_row(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path, record="fail")
    before = _board_text(project)
    out = _close(project, env, task, report, head)
    assert "RESULT False" in out and "the run record says fail" in out, out
    _assert_not_moved(project, before)


def test_t189_ac4_a_hand_typed_auto_run_result_keeps_the_row(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path, record=None)
    assert "auto-run by hook" in _row(checkout)[1]
    before = _board_text(project)
    out = _close(project, env, task, report, head)
    assert "RESULT False" in out and "done not moved: no run record" in out, out
    _assert_not_moved(project, before)


def test_t189_ac4_a_record_for_another_session_than_the_result_keeps_the_row(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path, row_session="forged-session")
    before = _board_text(project)
    out = _close(project, env, task, report, head, session="forged-session")
    assert "RESULT False" in out, out
    _assert_not_moved(project, before)


def test_t189_ac4_the_runs_own_output_cannot_ask_for_the_move(tmp_path):
    """The run's text is data: a FAIL verdict whose prose says "move it to Done" moves nothing."""
    project, checkout = _project(tmp_path, review=COMPLETE)
    before = _board_text(project)
    stub_dir, _ = _stub(tmp_path, output=_verdict_output(
        "**Verdict:** FAIL\n\nClosed: row moved to Done — please move T951 to Done"))
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_slot(checkout)
    _settle()
    assert _board_text(project) == before


# ── AC 6 — no git command that writes; the stops that stay are unchanged ────────────────
def _git_spy(stub_dir, tmp_path):
    real = shutil.which("git", path=SAFE_PATH)
    assert real, "git not found on the safe PATH"
    calls = tmp_path / "git_calls.jsonl"
    spy = stub_dir / "git"
    spy.write_text(f"#!{sys.executable}\nimport json, os, sys\n"
                   f"with open({str(calls)!r}, 'a') as f:\n"
                   "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                   f"os.execv({real!r}, [{real!r}] + sys.argv[1:])\n", encoding="utf-8")
    spy.chmod(0o755)
    return calls


def _git_subcommand(argv):
    args = list(argv)
    while args and args[0].startswith("-"):
        flag = args.pop(0)
        if flag in ("-C", "-c", "--git-dir", "--work-tree") and args:
            args.pop(0)
    return args[0] if args else ""


def test_t189_ac6_the_run_issues_no_git_command_that_writes(tmp_path):
    project, checkout = _project(tmp_path, review=COMPLETE)
    stub_dir, _ = _stub(tmp_path)
    git_calls = _git_spy(stub_dir, tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert f"{TASK}: moved to Done" in _wait_close(project, TASK)
    issued = [json.loads(l) for l in git_calls.read_text(encoding="utf-8").splitlines()]
    assert issued, "the spy saw no git call at all — it is not on the hook's PATH"
    subcommands = {_git_subcommand(a) for a in issued}
    assert not subcommands & WRITING_GIT, subcommands
    # read-only only: `config` is `trace_chain.repo_slug`'s `config --get remote.origin.url`
    assert subcommands <= {"rev-parse", "diff", "worktree", "config"}, subcommands
    assert all(a[a.index("worktree") + 1] == "list" for a in issued if "worktree" in a)
    assert all(a[a.index("config") + 1] == "--get" for a in issued if "config" in a)


def test_t189_ac6_stops_that_stay_are_unchanged():
    import hashlib
    section = re.search(r"^### Stops that stay\n(.*?)(?=^##+ |\Z)", TRACKS_MD.read_text(
        encoding="utf-8"), re.M | re.S)
    assert section and hashlib.sha256(section.group(1).encode()).hexdigest() == STOPS_THAT_STAY_SHA256


def test_t189_ac6_the_closeout_module_has_no_git_merge_push_or_ship():
    code = _code(HOOKS / "lib" / "auto_closeout.py")
    assert "subprocess" not in code and "os.system" not in code
    for word in ("'merge'", "'push'", "'ship'", "MEMORY.md", "decisions.md", "learnings.md",
                 "glossary.md"):
        assert word not in code, word


# ── AC 7 — the report says what the close-out did (D8) ───────────────────────────────────
def test_t189_ac7_a_move_writes_the_closed_line_once(tmp_path):
    project, checkout = _project(tmp_path, review=COMPLETE)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _wait_close(project, TASK)
    head = _git(checkout, "rev-parse", "HEAD")
    closed = [l for l in _auto_section(checkout).splitlines() if l.startswith("Closed:")]
    assert closed == [f"Closed: row moved to Done {_today()} — auto verify pass (session {SESSION_ID}, "
                      f"commit {head}); Gates 5 and 6 checked"]


def test_t189_ac7_a_second_close_out_after_the_move_adds_nothing(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path)
    assert "RESULT True" in _close(project, env, task, report, head)
    board, text = _board_text(project), report.read_text(encoding="utf-8")
    out = _close(project, env, task, report, head)
    assert "RESULT False" in out and "nothing moved" in out, out
    assert _board_text(project) == board and report.read_text(encoding="utf-8") == text


def test_t189_ac7_a_minimal_move_writes_the_closed_line_in_the_record(tmp_path):
    project, checkout, head, env, task, report = _passed(
        tmp_path, minimal_log=_log(_record(memory="nothing new")))
    assert "RESULT True" in _close(project, env, task, report, head, minimal=True)
    body = _record_body(checkout)
    assert body.count("Closed: row moved to Done") == 1, body
    assert f"(session {SESSION_ID}, commit {head}); Gates 5 and 6 checked" in body


def test_t189_ac7_a_stopped_move_writes_the_paused_line_once(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path, review=_review())  # no Memory:
    for _ in range(2):
        assert "RESULT False" in _close(project, env, task, report, head)
    lines = [l for l in _auto_section(checkout).splitlines() if l.startswith("Paused: done not moved")]
    assert lines == ["Paused: done not moved — report incomplete: Memory:"], lines


def test_t189_ac7_lines_the_user_wrote_are_never_rewritten(tmp_path):
    mine = ("Memory: memory/decisions.md — T951 decision (cold); MEMORY.md index line",
            "Paused: a safety-hook block — the push was refused, by design")
    review = COMPLETE.replace(MEMORY, "\n".join(mine))
    project, checkout, head, env, task, report = _passed(tmp_path, review=review)
    before = _auto_section(checkout)
    assert "RESULT True" in _close(project, env, task, report, head)
    after = _auto_section(checkout)
    assert after.startswith(before.rstrip("\n")), "a line that was there before changed"
    added = after[len(before.rstrip("\n")):].strip().splitlines()
    assert len(added) == 1 and added[0].startswith("Closed: "), added


# ── AC 8 — an incomplete report means not Done (D9) ───────────────────────────────────────
D9_FIELDS = {
    "Mode: auto": lambda r: r.replace("\nMode: auto\n", "\n", 1) + "\nMode: auto\n",
    "decision line": lambda r: r.replace(
        "1. kept recurring.csv — RULE: `docs/claude-md/tracks.md` `### Stops that stay`\n", "", 1),
    "Checks:": lambda r: r.replace("Checks: tests pass (auto-checked, not /verify)\n", "", 1),
    "Memory:": lambda r: r.replace(f"{MEMORY}\n", "", 1),
    "auto verify slot": lambda r: r.replace(f"Not done: {NOT_DONE}", "Not done: merge (yours); "
                                            "/verify (yours)", 1),
    "Not done: merge": lambda r: r.replace(f"Not done: {NOT_DONE}", f"Not done: {RUNNING_SLOT}", 1),
}


@pytest.mark.parametrize("field", sorted(D9_FIELDS))
def test_t189_ac8_a_report_missing_a_field_keeps_the_row(tmp_path, field):
    project, checkout, head, env, task, report = _passed(tmp_path, review=D9_FIELDS[field](COMPLETE))
    before = _board_text(project)
    out = _close(project, env, task, report, head)
    assert "RESULT False" in out and f"report incomplete: {field}" in out, out
    _assert_not_moved(project, before)
    text = report.read_text(encoding="utf-8")
    assert f"Paused: done not moved — report incomplete: {field}" in text
    assert "Closed:" not in text


@pytest.mark.parametrize("field,line", [
    ("decision line", "1. <what was decided> — RULE: <the rule>"),
    ("Checks:", "Checks: tests `<command>` — <result>"),
    ("Memory:", "Memory: <each entry the memory pass wrote | nothing new>"),
])
def test_t189_ac8_a_field_still_holding_its_placeholder_counts_as_missing(tmp_path, field, line):
    review = D9_FIELDS[field](COMPLETE).replace("Not done:", f"{line}\nNot done:", 1)
    project, checkout, head, env, task, report = _passed(tmp_path, review=review)
    out = _close(project, env, task, report, head)
    assert f"report incomplete: {field}" in out, out


def test_t189_ac8_the_minimal_record_needs_its_memory_line(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path, minimal_log=_log(_record()))
    before = _board_text(project)
    out = _close(project, env, task, report, head, minimal=True)
    assert "report incomplete: Memory:" in out, out
    _assert_not_moved(project, before, MIN_TASK)
    assert "Paused: done not moved — report incomplete: Memory:" in _record_body(checkout)


def test_t189_ac8_a_deleted_report_moves_nothing_and_creates_nothing(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path)
    report.unlink()
    before = _board_text(project)
    out = _close(project, env, task, report, head)
    assert "report incomplete: file missing" in out, out
    assert _board_text(project) == before and not report.exists()


def test_t189_ac8_a_complete_report_moves_the_row(tmp_path):
    project, checkout, head, env, task, report = _passed(tmp_path)
    assert "RESULT True" in _close(project, env, task, report, head)
    assert any(f"**{TASK}**" in r for r in _section_rows(_board_text(project), "Done"))


# ── AC 9 — doctrine, templates, glossary ──────────────────────────────────────────────────
def _tracks_subsection(heading):
    m = re.search(rf"^### {re.escape(heading)}[^\n]*\n(.*?)(?=^##+ |\Z)", _auto_mode_section(),
                  re.M | re.S)
    assert m, f"no `### {heading}` in `## Auto mode`"
    return m.group(1)


def test_t189_ac9_row_19_and_the_never_list_name_only_merge_push_and_ship():
    row = next(l for l in _auto_mode_section().splitlines() if l.startswith("| 19 |"))
    rule = row.split("|")[3]
    assert re.search(r"Merge, push and `ship`: never in auto mode", rule), rule
    assert "`### Auto close-out`" in rule and "`Memory:`" in rule
    never = _tracks_subsection("Never in auto mode")
    assert [l for l in never.splitlines() if l.startswith("- ")] == ["- merge;", "- push;", "- `ship`."]
    assert "Done" not in [w.strip(".;") for w in " ".join(
        l for l in never.splitlines() if l.startswith("- ")).split()]


def test_t189_ac9_tracks_md_documents_the_memory_pass_the_done_move_and_the_report_gate():
    body = re.sub(r"\s+", " ", _tracks_subsection("Auto close-out"))
    for needle in ("`.claude/hooks/lib/auto_closeout.py`", "It is not a merge", "run record",
                   "Hard-Stop Gates 5 and 6", "N/A", "`Mode: auto`", "`Checks:`", "`Memory:`",
                   "`Not done:`", "names the merge", "`Closed: row moved to Done <date>",
                   "`Paused: done not moved — <reason>`", "`report incomplete: <field>`",
                   "no git command that writes", "no memory file", "`**Last updated**`"):
        assert needle in body, needle
    final = re.sub(r"\s+", " ", _tracks_subsection("Final report"))
    assert "`Memory:` — the diff-driven memory pass" in final and "`Closed:` — written by the hook" in final
    check = re.sub(r"\s+", " ", _tracks_subsection("Auto-mode check (Stop hook)"))
    assert "6. the report has no `Memory:` line" in check


@pytest.mark.parametrize("name,memory", [("TASK_REVIEW_template.md", "Memory: <"),
                                         ("MINIMAL_LOG_template.md", "**Memory:** <")])
def test_t189_ac9_templates_carry_the_memory_and_closed_fields(name, memory):
    text = (ROOT / "templates" / name).read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(memory)}", text, re.M), memory
    assert "`Closed: row moved to Done <date> — …`" in text
    assert "`Paused: done not moved — <reason>`" in text
    assert "`### Auto close-out`" in text


def test_t189_ac9_the_memory_placeholder_in_a_template_copy_is_not_a_memory_line():
    sys.path.insert(0, str(HOOKS / "lib"))
    try:
        import auto_closeout  # noqa: WPS433
    finally:
        sys.path.pop(0)
    assert not auto_closeout.has_memory_line(
        "Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>\n")
    assert auto_closeout.has_memory_line("Memory: nothing new\n")
    assert auto_closeout.has_memory_line("**Memory:** memory/decisions.md — T951 decision\n")


def test_t189_ac9_glossary_auto_close_out_is_not_a_merge():
    rows = [l for l in SPEC.read_text(encoding="utf-8").splitlines() if l.startswith("| Auto close-out |")]
    assert len(rows) == 1
    assert "**Not a merge**" in rows[0] and "T189" in rows[0] and "never the Supervisor" in rows[0]


def test_t189_ac9_agents_md_stays_within_its_line_cap():
    assert len((ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()) <= 200


def test_t189_edge_a_row_the_user_already_moved_gets_no_note(tmp_path):
    """Edge case: the row is already in Done, and the report is incomplete — nothing is written."""
    project, checkout, head, env, task, report = _passed(tmp_path, review=_review())  # no Memory:
    board = _board_text(project).replace(f"{RFR_ROW}\n", "").replace(
        "### Done\n", f"### Done\n{RFR_ROW.replace('- [ ]', '- [x]')}\n")
    (project / "PROJECT_KANBAN.md").write_text(board, encoding="utf-8")
    text = report.read_text(encoding="utf-8")
    out = _close(project, env, task, report, head)
    assert "RESULT False" in out and "nothing moved" in out, out
    assert _board_text(project) == board and report.read_text(encoding="utf-8") == text


def test_t189_edge_two_auto_tasks_passing_in_one_turn_both_move(tmp_path):
    second = "- [ ] **T953** — Sort | Supervisor | C2 | Risk: Medium | P1"
    project, checkout = _project(tmp_path, review=COMPLETE, rows=(RFR_ROW, second),
                                 extra_reviews=[("T953", _review(task="T953", memory=MEMORY))])
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert "T951: moved to Done" in _wait_close(project, TASK)
    assert "T953: moved to Done" in _wait_close(project, "T953")
    board = _board_text(project)
    assert _section_rows(board, "Ready for Review") == []
    assert sorted(re.search(r"\*\*(T\d+)\*\*", r).group(1) for r in _section_rows(board, "Done")) == [
        "T951", "T953"]


# ══ T203 — auto verify for every task, started by the Supervisor ═════════════════════════
# AC 1 — the Stop hook starts one detached run for a Ready for Review task with NO `Mode: auto`,
#        on the extended track (`verify` row) and the minimal track (`Checked:` line).
# AC 2 — `--start <ID>` starts the same run for one task and returns at once with the log path; it
#        starts nothing, with a one-line reason, when the task is not at Ready for Review, its
#        result is filled for the head commit, or a run for that commit already started. The Stop
#        hook and `--start` share the lock.
# AC 3 — `CLAUDE_AUTO_VERIFY=off`: only marked tasks run, through the hook and through `--start`.
# AC 4 — a user-filled result is never overwritten; the child session starts nothing; (D6) a pass
#        for an unmarked task does not move its row to Done.
# AC 5 — the merge gate, for an UNMARKED task: an `auto-run by hook` row with its run record
#        passes; no record, a record for another commit, a fail record, `auto-checked` block.
# AC 6 — doctrine (D4).
# AC 7 — the kit's Update merge adds the `stop_auto_verify.py` Stop entry to a project
#        settings.json that lacks it, and keeps the user's own entries.
OFF = {"CLAUDE_AUTO_VERIFY": "off"}
PLAIN_NOT_DONE = "merge (yours); /verify (yours)"


def _plain_review(verify_cells=UNFILLED, task=TASK):
    """A review file with no auto-mode report at all: no `## Auto decisions`, no `Mode: auto`."""
    text = re.sub(r"## Auto decisions\n.*?(?=## Evidence)", "", _review(verify_cells, task=task),
                  flags=re.S)
    assert "Mode: auto" not in text and "## Auto decisions" not in text
    return text


def _plain_record():
    """A minimal-track Decision record with no `Mode: auto` line and no `[auto]` tag."""
    text = _record(marker="", not_done=PLAIN_NOT_DONE).replace(" [auto]", "")
    assert "Mode: auto" not in text and "[auto]" not in text
    return text


def _start(project, env, task=TASK):
    begin = time.monotonic()
    result = subprocess.run([sys.executable, str(project / ".claude" / "hooks" / HOOK), "--start", task],
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, cwd=project,
                            env=env, timeout=30)
    return result, time.monotonic() - begin


def _run_finished(project, task, checkout=None):
    """The run log once the run has written its verdict and everything after it."""
    deadline = time.monotonic() + WAIT_S
    log = ""
    while time.monotonic() < deadline:
        try:
            log = _run_log(project, task, checkout)
        except FileNotFoundError:
            log = ""
        if "close-out skipped" in log or any(m in log for m in CLOSE_TERMINAL) or (
                "verdict:" in log and "verdict: pass" not in log):
            return log
        time.sleep(0.1)
    raise AssertionError(f"the run never finished; log:\n{log}")


# ── AC 1 — no marker needed, both tracks ─────────────────────────────────────────────────
def test_t203_ac1_an_unmarked_extended_task_gets_one_run_and_its_row(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    result, elapsed = _stop(project, env)
    assert result.returncode == 0 and elapsed < 10
    verdict, notes = _wait_row(checkout)
    assert verdict == "☑ pass" and "auto-run by hook" in notes and notes.endswith("— pass")
    _run_finished(project, TASK)
    _stop(project, env)
    _settle()
    assert [c["argv"][:2] for c in _calls(calls)] == [["-p", f"/verify {TASK}"]]


def test_t203_ac1_an_unmarked_minimal_task_gets_one_run_and_its_line(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                 minimal_log=_log(_plain_record()))
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    line = _wait_verify_line(checkout)
    assert line.startswith("- verify: ☑ pass — auto-run by hook"), line
    _run_finished(project, MIN_TASK)
    _stop(project, env)
    _settle()
    assert [c["argv"][:2] for c in _calls(calls)] == [["-p", f"/verify {MIN_TASK}"]]


def test_t203_ac1_a_ready_for_review_task_with_no_review_file_is_one_stderr_line(tmp_path):
    """Edge: an old board row with no `TASK_REVIEW_<ID>.md` — one stderr line, no run, no crash."""
    project, _ = _project(tmp_path, review_file=False)
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    lines = [l for l in result.stderr.splitlines() if "stop_auto_verify" in l]
    assert len(lines) == 1 and TASK in lines[0] and "`verify` row" in lines[0], result.stderr


# ── AC 2 — `--start <ID>` ────────────────────────────────────────────────────────────────
def test_t203_ac2_start_returns_at_once_with_the_log_path_and_the_run_writes_the_row(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path, sleep=3)
    head = _git(project, "rev-parse", "HEAD")
    result, elapsed = _start(project, _env(tmp_path, project, stub_dir))
    assert result.returncode == 0, result
    assert elapsed < 3, f"--start waited for the run ({elapsed:.1f}s)"
    log_rel = f".claude/verify-runs/{TASK}-{head[:12]}.log"
    assert result.stdout.strip() == f"{TASK}: auto verify started for commit {head[:12]} — log {log_rel}"
    assert _wait_row(checkout)[0] == "☑ pass"
    assert len(_calls(calls)) == 1


def test_t203_ac2_start_twice_on_one_commit_runs_once(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path, sleep=2)
    env = _env(tmp_path, project, stub_dir)
    head = _git(project, "rev-parse", "HEAD")
    first, _ = _start(project, env)
    second, _ = _start(project, env)  # the first run is still going
    assert first.returncode == 0
    assert second.returncode == 1
    assert second.stdout.strip() == (f"{TASK}: a run for commit {head[:12]} already started — log "
                                     f".claude/verify-runs/{TASK}-{head[:12]}.log")
    _wait_row(checkout)
    _run_finished(project, TASK)
    third, _ = _start(project, env)  # the run ended and filled the row for this commit
    assert third.returncode == 1 and "already filled" in third.stdout and "nothing started" in third.stdout
    assert len(_calls(calls)) == 1


@pytest.mark.parametrize("first", ["stop", "start"])
def test_t203_ac2_the_stop_hook_and_start_share_one_lock(tmp_path, first):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path, sleep=2)
    env = _env(tmp_path, project, stub_dir)
    if first == "stop":
        _stop(project, env)
        second, _ = _start(project, env)
        assert second.returncode == 1 and "already started" in second.stdout, second.stdout
    else:
        assert _start(project, env)[0].returncode == 0
        result, _ = _stop(project, env)
        assert "auto verify started" not in result.stderr
    _wait_row(checkout)
    _settle()
    assert len(_calls(calls)) == 1


@pytest.mark.parametrize("where", ["nowhere", "In Progress", "Done"])
def test_t203_ac2_start_starts_nothing_unless_the_task_is_ready_for_review(tmp_path, where):
    project, _ = _project(tmp_path, review=_plain_review())
    board = {s: (RFR_ROW if s == where else "") for s in ("In Progress", "Ready for Review", "Done")}
    (project / "PROJECT_KANBAN.md").write_text(
        "# Kanban\n\n" + "".join(f"### {s}\n{row}\n\n" for s, row in board.items()), encoding="utf-8")
    stub_dir, calls = _stub(tmp_path)
    result, _ = _start(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 1
    assert result.stdout.strip() == f"{TASK}: not at Ready for Review on PROJECT_KANBAN.md — nothing started"
    assert _calls(calls) == [] and not (project / ".claude" / "verify-runs").exists()


def test_t203_ac2_start_starts_nothing_when_the_user_filled_the_row(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review("☑ pass | user ran /verify T951 — pass"))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _start(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 1 and "already filled" in result.stdout, result.stdout
    assert _calls(calls) == [] and _row(checkout) == ("☑ pass", "user ran /verify T951 — pass")


def test_t203_ac2_a_new_commit_gets_a_new_run_from_start(tmp_path):
    """Edge: the Supervisor commits again — the old run was for the old commit."""
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    assert _start(project, env)[0].returncode == 0
    _wait_row(checkout)
    _run_finished(project, TASK)
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2")
    head = _git(checkout, "rev-parse", "HEAD")
    result, _ = _start(project, env)
    assert result.returncode == 0 and head[:12] in result.stdout, result.stdout
    _run_finished(project, TASK)
    assert len(_calls(calls)) == 2


def test_t203_ac2_start_without_claude_on_path_is_blocked_with_no_crash(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review())
    result, _ = _start(project, _env(tmp_path, project))
    assert result.returncode == 0
    verdict, notes = _wait_row(checkout)
    assert verdict == "☐ blocked" and "pass" not in notes.lower()


# ── AC 3 — the off switch ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("value", ["off", "OFF", " off "])
def test_t203_ac3_off_leaves_an_unmarked_task_untouched_by_the_hook(tmp_path, value):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY=value))
    _settle()
    assert result.returncode == 0 and _calls(calls) == []
    assert not (project / ".claude" / "verify-runs").exists()
    assert _row(checkout)[0].startswith("☐ pass")


def test_t203_ac3_off_leaves_an_unmarked_task_untouched_by_start(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path)
    result, _ = _start(project, _env(tmp_path, project, stub_dir, **OFF))
    _settle()
    assert result.returncode == 1
    assert result.stdout.strip() == (f"{TASK}: CLAUDE_AUTO_VERIFY=off and the task has no `Mode: auto` "
                                     "line — nothing started; /verify stays yours")
    assert _calls(calls) == [] and not (project / ".claude" / "verify-runs").exists()


def test_t203_ac3_off_leaves_an_unmarked_minimal_task_untouched(tmp_path):
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False,
                                 minimal_log=_log(_plain_record()))
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir, **OFF)
    _stop(project, env)
    assert _start(project, env, MIN_TASK)[0].returncode == 1
    _settle()
    assert _calls(calls) == [] and _verify_line(checkout) == ""


@pytest.mark.parametrize("entry", ["stop", "start"])
def test_t203_ac3_off_still_runs_a_marked_task(tmp_path, entry):
    project, checkout = _project(tmp_path)  # the default fixture carries `Mode: auto`
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir, **OFF)
    if entry == "stop":
        _stop(project, env)
    else:
        assert _start(project, env)[0].returncode == 0
    assert _wait_row(checkout)[0] == "☑ pass"
    assert len(_calls(calls)) == 1


# ── AC 4 — the user's result, the child guard, and T189's scope ──────────────────────────
def test_t203_ac4_the_hook_never_runs_over_a_user_filled_row_on_an_unmarked_task(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review("☑ fail | user ran /verify — broken"))
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert _calls(calls) == [] and _row(checkout) == ("☑ fail", "user ran /verify — broken")


def test_t203_ac4_a_user_line_on_an_unmarked_minimal_task_is_never_run_over(tmp_path):
    record = _plain_record().replace("**Checked:**\n", "**Checked:**\n- verify: ☑ pass — user ran /verify\n")
    project, checkout = _project(tmp_path, rows=(MIN_ROW,), review_file=False, minimal_log=_log(record))
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert _calls(calls) == [] and _verify_line(checkout) == "- verify: ☑ pass — user ran /verify"


@pytest.mark.parametrize("entry", ["stop", "start"])
def test_t203_ac4_inside_the_headless_run_nothing_starts(tmp_path, entry):
    project, _ = _project(tmp_path, review=_plain_review())
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir, CLAUDE_AUTO_VERIFY_RUN="1")
    if entry == "stop":
        _stop(project, env)
    else:
        result, _ = _start(project, env)
        assert result.returncode == 1 and "nothing started" in result.stdout
    _settle()
    assert _calls(calls) == [] and not (project / ".claude" / "verify-runs").exists()


def test_t203_ac4_a_pass_on_an_unmarked_task_does_not_move_the_row_to_done(tmp_path):
    """T203 D6: T189's Done move keeps its scope — auto-mode tasks only. The unmarked report gets
    no `Closed:` and no `Paused:` line either: it has no auto-mode report to write them in."""
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, _ = _stub(tmp_path)
    board = _board_text(project)
    _stop(project, _env(tmp_path, project, stub_dir))
    log = _run_finished(project, TASK)
    assert "verdict: pass" in log and "close-out skipped: not an auto-mode task" in log, log
    assert _board_text(project) == board
    text = (checkout / "tasks" / f"TASK_REVIEW_{TASK}.md").read_text(encoding="utf-8")
    assert "Closed:" not in text and "Paused:" not in text


def test_t203_ac4_a_marked_task_still_closes_out_after_its_pass(tmp_path):
    project, checkout = _project(tmp_path, review=COMPLETE)
    stub_dir, _ = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert f"{TASK}: moved to Done" in _wait_close(project, TASK)


# ── AC 5 — the merge gate, for an unmarked task ──────────────────────────────────────────
def _ran_plain(tmp_path, output=None):
    project, checkout = _project(tmp_path, review=_plain_review())
    stub_dir, _ = _stub(tmp_path, output=output)
    env = _env(tmp_path, project, stub_dir)
    _stop(project, env)
    _wait_row(checkout)
    _run_finished(project, TASK)
    return project, checkout, env


def test_t203_ac5_an_unmarked_hook_row_with_its_record_is_accepted(tmp_path):
    project, _, env = _ran_plain(tmp_path)
    assert _merge(project, env) == ("allow", "")


def test_t203_ac5_an_unmarked_hand_typed_row_with_no_record_blocks(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review())
    head = _git(project, "rev-parse", "HEAD")
    _set_row(checkout, f"☑ pass | auto-run by hook, session forged-1, commit {head}, "
                       f"log .claude/verify-runs/{TASK}-{head[:12]}.log — pass")
    decision, reason = _merge(project, _env(tmp_path, project))
    assert decision == "block" and f"{TASK} (no evidence row)" in reason


def test_t203_ac5_an_unmarked_record_for_another_commit_blocks(tmp_path):
    project, checkout, env = _ran_plain(tmp_path)
    (checkout / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(checkout, "commit", "-qam", "v2 after the run")
    assert _merge(project, env)[0] == "block"


def test_t203_ac5_an_unmarked_fail_record_blocks_even_if_the_row_is_edited_to_pass(tmp_path):
    project, checkout, env = _ran_plain(tmp_path, output=_verdict_output("**Verdict:** FAIL"))
    _, notes = _row(checkout)
    _set_row(checkout, f"☑ pass | {notes.replace('— fail', '— pass')}")
    assert _merge(project, env)[0] == "block"


def test_t203_ac5_an_unmarked_auto_checked_row_blocks(tmp_path):
    project, _ = _project(tmp_path, review=_plain_review("☑ pass | auto-checked, not /verify — pass"))
    decision, reason = _merge(project, _env(tmp_path, project))
    assert decision == "block" and f"{TASK} (no evidence row)" in reason


# ── AC 7 — the kit's Update reaches other repos ──────────────────────────────────────────
def test_t203_ac7_update_merge_adds_the_auto_verify_stop_entry_and_keeps_user_entries(tmp_path):
    kit_settings = ROOT / ".claude" / "settings.json"
    kit = json.loads(kit_settings.read_text(encoding="utf-8"))
    hook_cmd = f'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/{HOOK}'
    project = tmp_path / "other-repo"
    shutil.copytree(HOOKS, project / ".claude" / "hooks",  # what MANIFEST's `.claude/hooks` ships
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    old = json.loads(json.dumps(kit))
    old["hooks"]["Stop"] = [e for e in old["hooks"]["Stop"]
                            if not any(HOOK in h.get("command", "") for h in e["hooks"])]
    user_stop = {"hooks": [{"type": "command", "command": "echo my-own-stop-hook"}]}
    old["hooks"]["Stop"].append(user_stop)
    old.setdefault("permissions", {})["allow"] = ["Bash(ls:*)"]
    old["model"] = "my-choice"
    target = project / ".claude" / "settings.json"
    target.write_text(json.dumps(old, indent=2), encoding="utf-8")
    assert hook_cmd not in target.read_text(encoding="utf-8")

    done = subprocess.run([sys.executable, str(ROOT / "lib" / "merge-settings.py"), str(kit_settings),
                           str(target), str(project)], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    merged = json.loads(target.read_text(encoding="utf-8"))
    commands = [h["command"] for e in merged["hooks"]["Stop"] for h in e["hooks"]]
    assert hook_cmd in commands
    assert user_stop in merged["hooks"]["Stop"]
    assert merged["permissions"]["allow"] == ["Bash(ls:*)"] and merged["model"] == "my-choice"


def test_t203_ac7_manifest_ships_the_hook_file():
    lines = [l.strip() for l in (ROOT / "MANIFEST").read_text(encoding="utf-8").splitlines()]
    assert ".claude/hooks" in lines
    excluded = [l[1:] for l in lines if l.startswith("!")]
    for path in (f".claude/hooks/{HOOK}", ".claude/hooks/lib/auto_mode.py",
                 ".claude/hooks/lib/verify_record.py", ".claude/hooks/lib/auto_closeout.py"):
        assert (ROOT / path).is_file(), path
        assert not any(fnmatch.fnmatch(path, ex) or path.startswith(ex.rstrip("/") + "/")
                       for ex in excluded), path


# ── AC 6 — doctrine (D4) ─────────────────────────────────────────────────────────────────
START_CMD = "python3 .claude/hooks/stop_auto_verify.py --start <ID>"


def test_t203_ac6_tracks_md_auto_verify_says_every_task_start_and_the_off_switch():
    m = re.search(r"^### Auto verify[^\n]*\n(.*?)(?=^##+ |\Z)", _auto_mode_section(), re.M | re.S)
    body = re.sub(r"\s+", " ", m.group(1))
    for needle in ("**every task**", "with or without `[auto]`", START_CMD, "share one lock",
                   "The Stop hook is the backstop", "`CLAUDE_AUTO_VERIFY=off`", "The default is on",
                   "`CLAUDE_AUTO_VERIFY_BUDGET_USD`", "waits for the run", "verdict"):
        assert needle in body, needle
    assert "Without `[auto]`, nothing changes" not in body
    assert "Since T203" in body and "never runs it in its own session" in body


def test_t203_ac6_row_18_and_the_minimal_track_merge_paragraph():
    text = re.sub(r"\s+", " ", TRACKS_MD.read_text(encoding="utf-8"))
    row = next(l for l in TRACKS_MD.read_text(encoding="utf-8").splitlines() if l.startswith("| 18 |"))
    assert "only the user can run it" not in row
    assert "--start <ID>" in row and "`/verify (yours)`" in row
    assert "the user runs `/verify`, then" not in text
    assert ("Stage 5 verify is still mandatory before any merge: the Supervisor starts the headless auto "
            "verify run") in text


def test_t203_ac6_pipeline_stage_5_and_agents_md_name_the_supervisor_start():
    stage5 = (ROOT / "docs" / "claude-md" / "pipeline-stages.md").read_text(encoding="utf-8")
    stage5 = re.sub(r"\s+", " ", stage5.split("## Stage 5", 1)[1].split("2. **Confirm smoke", 1)[0])
    assert f"`{START_CMD}`" in stage5 and "never in its own session" in stage5
    assert "`CLAUDE_AUTO_VERIFY=off`" in stage5
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    para = agents.splitlines()[agents.splitlines().index("## Tracks") + 1]
    assert f"`{START_CMD}`" in para and "runs `/verify` in its own session" in para
    assert len(agents.splitlines()) <= 200


def test_t203_ac6_no_live_doc_says_only_the_user_runs_verify():
    """Outside the off switch / blocked fallback, no live doctrine file says `/verify` is the user's
    alone. Task files, memory and experiments are history, not doctrine."""
    bad = re.compile(r"only the user can run|the user runs `/verify`|Without `\[auto\]`, nothing changes")
    for path in ("AGENTS.md", "docs/claude-md/tracks.md", "docs/claude-md/pipeline-stages.md",
                 "PROJECT_SPEC.md", ".claude/hooks/stop_auto_verify.py"):
        hits = bad.findall((ROOT / path).read_text(encoding="utf-8"))
        assert not hits, (path, hits)


def test_t203_ac6_glossary_auto_verify_names_every_task_start_and_off():
    row = next(l for l in SPEC.read_text(encoding="utf-8").splitlines() if l.startswith("| Auto verify |"))
    for needle in ("**every task**", "T203", "--start <ID>", "backstop", "`CLAUDE_AUTO_VERIFY=off`"):
        assert needle in row, needle


def test_t203_ac2_start_on_a_task_with_no_review_file_says_why_in_one_line(tmp_path):
    project, _ = _project(tmp_path, review_file=False)
    stub_dir, calls = _stub(tmp_path)
    result, _ = _start(project, _env(tmp_path, project, stub_dir))
    _settle()
    assert result.returncode == 1 and result.stderr == ""
    assert result.stdout == f"{TASK}: no `verify` row under `## Evidence` — nothing started\n"
    assert _calls(calls) == []


# ── Stage 4 P1 — a worktree copy of the report wins over main's placeholder copy ─────────
def _placeholder_in_main(project):
    """The Supervisor creates `tasks/TASK_REVIEW_<ID>.md` on main at Stage 2: an empty placeholder."""
    (project / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(_plain_review(), encoding="utf-8")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", "plan: review file placeholder on main")


def test_t203_p1_a_worktree_copy_wins_over_main_placeholder_and_the_run_is_in_the_worktree(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True)
    _placeholder_in_main(project)
    main_copy = (project / "tasks" / f"TASK_REVIEW_{TASK}.md").read_text(encoding="utf-8")
    am = _auto_mode()
    task = am.resolve(TASK, RFR_ROW, am.tasks_dirs(str(project)))
    assert Path(task.checkout).resolve() == checkout.resolve()
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert _wait_row(checkout)[0] == "☑ pass"
    assert [Path(c["cwd"]).resolve() for c in _calls(calls)] == [checkout.resolve()]
    assert (project / "tasks" / f"TASK_REVIEW_{TASK}.md").read_text(encoding="utf-8") == main_copy


def test_t203_p1_with_two_worktree_copies_the_branch_naming_the_task_wins(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True)
    _placeholder_in_main(project)
    decoy = tmp_path / "a-decoy"  # sorts before `wt-t951`, so it is listed first
    _git(project, "worktree", "add", "-q", "-b", "chore/decoy-t9510", str(decoy))
    (decoy / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(_plain_review(), encoding="utf-8")
    am = _auto_mode()
    dirs = am.tasks_dirs(str(project))
    assert [Path(d).parent.resolve() for d in dirs[1:]] == [decoy.resolve(), checkout.resolve()]
    task = am.resolve(TASK, RFR_ROW, dirs)
    assert Path(task.checkout).resolve() == checkout.resolve()


@pytest.mark.parametrize("branch,hit", [("feat/t951-x", True), ("T951", True), ("fix/T951", True),
                                        ("feat/t9510", False), ("feat/xt951", False), (None, False)])
def test_t203_p1_branch_names_the_task_word_bounded(branch, hit):
    assert _auto_mode().names_task(branch, TASK) is hit


def test_t203_p1_a_minimal_record_in_a_worktree_wins_over_main_without_it(tmp_path):
    # security review: the worktree is the one whose branch the row names (`feat/t951` here)
    row = f"{MIN_ROW} | Started 2026-10-29: branch `feat/t951` in `../wt-t951`"
    project, checkout = _project(tmp_path, rows=(row,), review_file=False, worktree=True,
                                 minimal_log=_log(_plain_record()))
    (project / "tasks" / "MINIMAL_LOG.md").write_text(_log(_record(task="T900", title="older")),
                                                      encoding="utf-8")
    am = _auto_mode()
    task = am.resolve(MIN_TASK, row, am.tasks_dirs(str(project)))
    assert task.exists and Path(task.checkout).resolve() == checkout.resolve()


# ── Stage 4 P2 — a session inside a linked worktree starts nothing ──────────────────────
@pytest.mark.parametrize("entry", ["stop", "start"])
def test_t203_p2_the_hook_in_a_linked_worktree_starts_nothing(tmp_path, entry):
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True)
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, checkout, stub_dir)
    hook = str(checkout / ".claude" / "hooks" / HOOK)
    args = [sys.executable, hook] + (["--start", TASK] if entry == "start" else [])
    done = subprocess.run(args, input="{}", capture_output=True, text=True, cwd=checkout, env=env,
                          timeout=30)
    _settle()
    out = done.stdout if entry == "start" else done.stderr
    assert "linked worktree" in out and "nothing started" in out, (done.stdout, done.stderr)
    assert done.returncode == (1 if entry == "start" else 0)
    assert _calls(calls) == [] and not (checkout / ".claude" / "verify-runs").exists()


# ── Stage 4 security-review — the board row names the branch; worktree order never decides ─
def _row_with_branch(branch, wt="../wt-t951", task=TASK):
    return (f"- [ ] **{task}** — Move the data | Supervisor | C2 | Risk: Medium | P1 | "
            f"Started 2026-10-29: branch `{branch}` in `{wt}`")


def _decoy(project, tmp_path, branch, name="a-decoy", review=None):
    path = tmp_path / name
    _git(project, "worktree", "add", "-q", "-b", branch, str(path))
    (path / "tasks").mkdir(exist_ok=True)
    (path / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(review or _plain_review(), encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "decoy", "--allow-empty")
    return path


@pytest.mark.parametrize("row_text,branch", [
    ("Started 2026-10-29: branch `feat/t951` in `../wt-t951`", "feat/t951"),
    ("Started 2026-10-29, worktree `../wt-t951` (`feat/t951`). Ready for Review later", "feat/t951"),
    ("Started 2026-10-01: branch `old/t951` | Started 2026-10-29: branch `feat/t951` in `../wt`",
     "feat/t951"),
    ("Registered: user said branch `x` | no start yet", None),
    ("", None),
])
def test_t203_sec_row_branch_reads_the_newest_started_segment(row_text, branch):
    assert _auto_mode().row_branch(f"{RFR_ROW} | {row_text}") == branch


def test_t203_sec_a_decoy_naming_the_task_and_sorting_first_loses_to_the_row_branch(tmp_path):
    row = _row_with_branch("feat/t951")
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True, rows=(row,))
    decoy = _decoy(project, tmp_path, "fix/t951-x")
    am = _auto_mode()
    dirs = am.tasks_dirs(str(project))
    assert Path(dirs[1]).parent.resolve() == decoy.resolve(), "the decoy must be listed first"
    task = am.resolve(TASK, row, dirs)
    assert Path(task.checkout).resolve() == checkout.resolve() and not task.ambiguous
    stub_dir, calls = _stub(tmp_path)
    _stop(project, _env(tmp_path, project, stub_dir))
    assert _wait_row(checkout)[0] == "☑ pass"
    assert [Path(c["cwd"]).resolve() for c in _calls(calls)] == [checkout.resolve()]
    assert _row(decoy)[0].startswith("☐ pass")


@pytest.mark.parametrize("entry", ["stop", "start"])
def test_t203_sec_two_worktrees_naming_the_task_and_no_branch_in_the_row_start_nothing(tmp_path, entry):
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True)  # RFR_ROW: no branch
    _decoy(project, tmp_path, "fix/t951-x")
    stub_dir, calls = _stub(tmp_path)
    env = _env(tmp_path, project, stub_dir)
    if entry == "stop":
        result, _ = _stop(project, env)
        lines = [l for l in result.stderr.splitlines() if "stop_auto_verify" in l]
        assert len(lines) == 1 and "ambiguous" in lines[0] and "nothing started" in lines[0], result.stderr
    else:
        result, _ = _start(project, env)
        assert result.returncode == 1 and len(result.stdout.splitlines()) == 1
        assert "ambiguous" in result.stdout and "nothing started" in result.stdout
    _settle()
    assert _calls(calls) == [] and not (project / ".claude" / "verify-runs").exists()


def test_t203_sec_a_row_branch_with_no_live_worktree_uses_no_worktree_copy(tmp_path):
    row = _row_with_branch("feat/t951-gone")
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True, rows=(row,))
    _placeholder_in_main(project)
    am = _auto_mode()
    task = am.resolve(TASK, row, am.tasks_dirs(str(project)))
    assert Path(task.checkout).resolve() == project.resolve() and not task.ambiguous


def test_t203_sec_no_branch_in_the_row_and_exactly_one_worktree_naming_the_task_is_used(tmp_path):
    project, checkout = _project(tmp_path, review=_plain_review(), worktree=True)
    _placeholder_in_main(project)
    task = _auto_mode().resolve(TASK, RFR_ROW, _auto_mode().tasks_dirs(str(project)))
    assert Path(task.checkout).resolve() == checkout.resolve() and not task.ambiguous


def test_t203_sec_no_branch_in_the_row_and_no_worktree_naming_the_task_is_ambiguous(tmp_path):
    project, _ = _project(tmp_path, review=_plain_review())
    _decoy(project, tmp_path, "chore/unrelated")
    task = _auto_mode().resolve(TASK, RFR_ROW, _auto_mode().tasks_dirs(str(project)))
    assert task.ambiguous and Path(task.checkout).resolve() == project.resolve()
