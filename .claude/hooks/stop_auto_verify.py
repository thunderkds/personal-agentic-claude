#!/usr/bin/env python3
"""
Stop hook — auto verify (T182).

For each task on PROJECT_KANBAN.md's `### Ready for Review` whose `tasks/TASK_REVIEW_<ID>.md` carries
the T180 auto-mode marker (`Mode: auto` alone on a line, outside HTML comments), and whose `verify`
row is not filled for the head commit of the checkout that holds it (the main checkout first, then
each worktree), it starts one detached run and returns at once:

    claude -p "/verify <ID>" --max-budget-usd 2 --output-format json      (cwd = that checkout)

A new session (no --resume), the user's own permission settings (never
--dangerously-skip-permissions). The budget is CLAUDE_AUTO_VERIFY_BUDGET_USD (default 2), the time
limit CLAUDE_AUTO_VERIFY_TIMEOUT_S (default 1800). The run's output goes to
`.claude/verify-runs/<ID>-<12-hex commit>.log` (gitignored). That log is created exclusively before
the start, so one task and commit never run twice; delete it to run again.

When the run ends, this script (never the Supervisor) writes:
  * the run record (D5, `lib/verify_record.py`) where agents are denied write access;
  * the `verify` row (D4): `☑ pass` / `☑ fail` / `☐ blocked`, Notes
    `auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file> — <verdict>`.
The verdict is the result's `**Verdict:** PASS|FAIL` line. SKIP, BLOCKED, no verdict line, two
different verdicts, a non-success run (budget stop, error), output that is not JSON, a timeout or no
`claude` on PATH are all `blocked`. The run's text is data: only that line decides.

A row the user filled (a `☑` row that is not an `auto-run by hook` row) is never started over or
overwritten. The headless session's own Stop hooks see CLAUDE_AUTO_VERIFY_RUN=1 and do nothing.
Without the marker, nothing happens: `/verify` stays the user's. Merge stays with the user.
Fails open: any error is one stderr line, never a block.
"""
import json
import os
import re
import shlex
import signal
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
TASKS_DIR = os.path.join(ROOT, "tasks")
RUNS_REL = os.path.join(".claude", "verify-runs")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import verify_record as vr  # noqa: E402

CHILD_ENV = "CLAUDE_AUTO_VERIFY_RUN"
BUDGET_ENV, BUDGET_DEFAULT = "CLAUDE_AUTO_VERIFY_BUDGET_USD", "2"
TIMEOUT_ENV, TIMEOUT_DEFAULT_S = "CLAUDE_AUTO_VERIFY_TIMEOUT_S", 1800
MARKER = "Mode: auto"
COMMENT = re.compile(r"<!--.*?-->", re.S)
ROW_ID = re.compile(r"\*\*([A-Za-z]+-?\d+)\*\*")
MINIMAL = re.compile(r"\|\s*Track:\s*minimal\b", re.I)
VERIFY_ROW = re.compile(r"^\|\s*verify\s*\|(?P<result>[^|\n]*)\|(?P<notes>[^|\n]*)\|?[^\n]*$", re.M | re.I)
VERDICT = re.compile(r"^\s*\*\*Verdict:\*\*\s*([A-Z]+)\b", re.M)
SESSION = re.compile(r"[^A-Za-z0-9-]")


def warn(message):
    print(f"[hook:stop_auto_verify] {message}", file=sys.stderr)


def worktree_checkouts():
    try:
        done = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=ROOT,
                              capture_output=True, text=True, timeout=5)
        if done.returncode != 0:
            return []
        paths = [l[len("worktree "):].strip() for l in done.stdout.splitlines()
                 if l.startswith("worktree ")]
        return [p for p in paths if p and os.path.abspath(p) != os.path.abspath(ROOT)]
    except Exception:
        return []


def ready_for_review(kanban):
    m = re.search(r"^### Ready for Review\n(.*?)(?=^###|\Z)", kanban, re.S | re.M)
    rows = m.group(1).splitlines() if m else []
    return [ROW_ID.search(l).group(1) for l in rows
            if l.strip().startswith("- ") and ROW_ID.search(l) and not MINIMAL.search(l)]


def evidence_row(text):
    """The `verify` row inside `## Evidence`: (match, offset of the section), or (None, 0)."""
    m = re.search(r"^## Evidence[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return None, 0
    return VERIFY_ROW.search(m.group(1)), m.start(1)


def is_auto(text):
    return MARKER in COMMENT.sub("", text).splitlines()


def due(task_id, text, checkout, head):
    """True when the row is unfilled for `head`: never filled, or filled by an earlier auto run for
    other code. A row the user filled is never due."""
    row, _ = evidence_row(text)
    if row is None:
        warn(f"{task_id}: no `verify` row under `## Evidence` — auto verify not started")
        return False
    notes = row.group("notes")
    if vr.AUTO_ROW_TAG in notes:
        verified = vr.ROW_COMMIT.search(notes)
        return not (verified and vr.same_code(checkout, task_id, verified.group(1), head))
    return "☑" not in row.group("result")


def start(task_id, review_path, checkout, head):
    log_rel = os.path.join(RUNS_REL, f"{vr.safe_name(task_id, '_untagged')}-{head[:12]}.log")
    log_path = os.path.join(ROOT, log_rel)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    try:
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o644)
    except FileExistsError:
        return  # this task and commit already ran (or is running)
    env = dict(os.environ, **{CHILD_ENV: "1"})
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--run", task_id, review_path,
                          checkout, head, log_rel],
                         cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=fd, stderr=fd,
                         close_fds=True, start_new_session=True)  # setsid: survives this hook
    finally:
        os.close(fd)
    warn(f"{task_id}: auto verify started for commit {head[:12]} — log {log_rel}")


def stop_hook():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    try:
        with open(KANBAN, encoding="utf-8") as f:
            kanban = f.read()
    except Exception:
        return
    checkouts = [ROOT] + worktree_checkouts()
    for task_id in ready_for_review(kanban):
        try:
            for checkout in checkouts:
                review_path = os.path.join(checkout, "tasks", f"TASK_REVIEW_{task_id}.md")
                if os.path.exists(review_path):
                    break
            else:
                continue
            with open(review_path, encoding="utf-8") as f:
                text = f.read()
            if not is_auto(text):
                continue
            head = vr.head_commit(checkout)
            if head and due(task_id, text, checkout, head):
                start(task_id, review_path, checkout, head)
        except Exception as exc:  # fail open: a bug here must never trap the session
            warn(f"{task_id}: skipped ({type(exc).__name__}: {exc})")


# ── the detached run ──────────────────────────────────────────────────────────────────────
def budget():
    value = os.environ.get(BUDGET_ENV, "").strip()
    try:
        return value if float(value) > 0 else BUDGET_DEFAULT
    except ValueError:
        return BUDGET_DEFAULT


def timeout_s():
    try:
        value = int(os.environ.get(TIMEOUT_ENV, ""))
        return value if value > 0 else TIMEOUT_DEFAULT_S
    except ValueError:
        return TIMEOUT_DEFAULT_S


def parse(stdout):
    """(verdict, session, reason) from `claude -p --output-format json` output."""
    try:
        data = json.loads(stdout)
    except Exception:
        return "blocked", "none", "output is not JSON"
    if not isinstance(data, dict):
        return "blocked", "none", "output is not a JSON object"
    session = SESSION.sub("", str(data.get("session_id") or ""))[:64] or "none"
    if data.get("subtype") != "success" or data.get("is_error") is not False:
        return "blocked", session, "run did not succeed"
    verdicts = set(VERDICT.findall(str(data.get("result") or "")))
    if verdicts == {"PASS"}:
        return "pass", session, ""
    if verdicts == {"FAIL"}:
        return "fail", session, ""
    return "blocked", session, "no single verdict line"


def call_claude(checkout):
    command = ["claude", "-p", f"/verify {sys.argv[2]}", "--max-budget-usd", budget(),
               "--output-format", "json"]
    print("$ " + shlex.join(command), flush=True)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    try:
        proc = subprocess.Popen(command, cwd=checkout, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                start_new_session=True)
    except FileNotFoundError:
        return "", "claude not found on PATH"
    try:
        out, err = proc.communicate(timeout=timeout_s())
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()
        out, err = proc.communicate()
        print(out or "", err or "", sep="\n", flush=True)
        return None, f"timed out after {timeout_s()}s"
    print(out or "", err or "", sep="\n", flush=True)
    return out, ""


def write_row(review_path, task_id, cells):
    with open(review_path, encoding="utf-8") as f:
        text = f.read()
    row, offset = evidence_row(text)
    if row is None:
        print(f"no `verify` row in {review_path} — row not written", flush=True)
        return
    notes = row.group("notes")
    if "☑" in row.group("result") and vr.AUTO_ROW_TAG not in notes:
        print("the row was filled during the run — kept, not overwritten", flush=True)
        return
    new = f"| verify | {cells[0]} | {cells[1]} |"
    with open(review_path, "w", encoding="utf-8") as f:
        f.write(text[:offset + row.start()] + new + text[offset + row.end():])


def run():
    task_id, review_path, checkout, head, log_rel = sys.argv[2:7]
    out, reason = call_claude(checkout)
    if reason:
        verdict, session = "blocked", "none"
    else:
        verdict, session, reason = parse(out)
    print(f"verdict: {verdict}" + (f" ({reason})" if reason else ""), flush=True)
    try:
        vr.write_record(ROOT, task_id, head, verdict, session, log_rel)
    except Exception as exc:
        print(f"run record not written ({type(exc).__name__}: {exc})", flush=True)
    write_row(review_path, task_id, vr.row_cells(head, verdict, session, log_rel, reason))


def main():
    if len(sys.argv) == 7 and sys.argv[1] == "--run":
        run()
    elif not os.environ.get(CHILD_ENV):
        stop_hook()
    sys.exit(0)


main()
