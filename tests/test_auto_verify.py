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


# ── fixtures ──────────────────────────────────────────────────────────────────────────────
def _review(verify_cells=UNFILLED, marker="Mode: auto", task=TASK):
    auto = (f"## Auto decisions\n\n{marker}\n"
            "1. kept recurring.csv — RULE: `docs/claude-md/tracks.md` `### Stops that stay`\n"
            "Checks: tests pass (auto-checked, not /verify)\nNot done: merge (yours)\n\n")
    return (f"# TASK_REVIEW — {task}: Move the data\n\n{auto}"
            "## Evidence\n\n| Check | Result | Notes / output snippet |\n|-------|--------|----|\n"
            "| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | tests/x.py |\n"
            f"| verify | {verify_cells} |\n"
            "| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |\n\n"
            "## Demonstration\n\n**BEFORE**: x\n")


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


def _project(tmp_path, review=None, rows=(RFR_ROW,), worktree=False, extra_reviews=()):
    """A temp git project with the kit's hooks, settings.json and .gitignore. The review file lives
    in the main checkout, or (worktree=True) only in a `git worktree` on branch feat/t951."""
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
        f"# Kanban\n\n### Todo\n\n### In Progress\n\n### Ready for Review\n{board}\n\n### Done\n",
        encoding="utf-8")
    if not worktree:
        (project / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(
            _review() if review is None else review, encoding="utf-8")
    for task, text in extra_reviews:
        (project / "tasks" / f"TASK_REVIEW_{task}.md").write_text(text, encoding="utf-8")
        _trace(project, task)
    _trace(project)
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
        (checkout / "tasks" / f"TASK_REVIEW_{TASK}.md").write_text(
            _review() if review is None else review, encoding="utf-8")
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
    project, checkout = _project(tmp_path, review=_review(marker=marker))
    stub_dir, calls = _stub(tmp_path)
    result, _ = _stop(project, _env(tmp_path, project, stub_dir))
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
