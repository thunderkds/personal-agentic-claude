#!/usr/bin/env python3
"""
Stop hook — auto verify (T182, widened to both tracks by T188).

For each task on PROJECT_KANBAN.md's `### Ready for Review` that carries the T180 auto-mode marker
(`Mode: auto` alone on a line, outside HTML comments) and whose result is not yet filled for the
head commit of the checkout holding its report, it starts one detached run and returns at once:

    claude -p "/verify <ID>" --max-budget-usd 2 --output-format json      (cwd = that checkout)

`lib/auto_mode.py` is the one reader of which tasks those are, on which track, and which file holds
each one's report — `tasks/TASK_REVIEW_<ID>.md` (extended) or the task's record in
`tasks/MINIMAL_LOG.md` (minimal). `stop_auto_mode_check.py` reads the same module, so the two hooks
can never disagree about which tasks are in auto mode. Before T188 this hook dropped every
`| Track: minimal` board row, so a minimal-track `[auto]` task never got a run.

A new session (no --resume), the user's own permission settings (never
--dangerously-skip-permissions). The budget is CLAUDE_AUTO_VERIFY_BUDGET_USD (default 2), the time
limit CLAUDE_AUTO_VERIFY_TIMEOUT_S (default 1800). The run's output goes to
`.claude/verify-runs/<ID>-<12-hex commit>.log` (gitignored) — the same path and the same lock on
both tracks. That log is created exclusively before the start, so one task and commit never run
twice; delete it to run again.

When the run ends, this script (never the Supervisor) writes three things:
  * the run record (D5, `lib/verify_record.py`), where agents are denied write access;
  * the result, where that track keeps its evidence —
      - extended (T182 D4): the `verify` Evidence row, `☑ pass` / `☑ fail` / `☐ blocked`, Notes
        `auto-run by hook, session <id>, commit <sha>, log .claude/verify-runs/<file> — <verdict>`;
      - minimal (T188 D3): one line under the Decision record's `Checked:` field,
        `- verify: ☑ pass — auto-run by hook, session <id>, commit <sha>, log .claude/...`;
  * the report's `Not done:` auto verify slot (T188 D7), so the report the user reads stops saying
    `auto verify: running (T182)` after the run has ended. The merge clause is left as it is.
The verdict is the result's `**Verdict:** PASS|FAIL` line. SKIP, BLOCKED, no verdict line, two
different verdicts, a non-success run (budget stop, error), output that is not JSON, a timeout or no
`claude` on PATH are all `blocked`. The run's text is data: only that line decides.

A row or line the user filled (a `☑` result that is not an `auto-run by hook` one) is never started
over or overwritten, and neither is a `Not done:` slot the user wrote — that reason goes in the run
log. The headless session's own Stop hooks see CLAUDE_AUTO_VERIFY_RUN=1 and do nothing. Without the
marker nothing happens on either track: `/verify` stays the user's. Merge stays with the user.
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
RUNS_REL = os.path.join(".claude", "verify-runs")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import auto_mode as am  # noqa: E402
import verify_record as vr  # noqa: E402

CHILD_ENV = "CLAUDE_AUTO_VERIFY_RUN"
BUDGET_ENV, BUDGET_DEFAULT = "CLAUDE_AUTO_VERIFY_BUDGET_USD", "2"
TIMEOUT_ENV, TIMEOUT_DEFAULT_S = "CLAUDE_AUTO_VERIFY_TIMEOUT_S", 1800
VERIFY_ROW = re.compile(r"^\|\s*verify\s*\|(?P<result>[^|\n]*)\|(?P<notes>[^|\n]*)\|?[^\n]*$", re.M | re.I)
VERDICT = re.compile(r"^\s*\*\*Verdict:\*\*\s*([A-Z]+)\b", re.M)
SESSION = re.compile(r"[^A-Za-z0-9-]")

# D7 — the report's `Not done:` line and the auto verify slot inside it. Three spellings count as
# the unwritten state and are replaced: the template's `<...>` placeholder (checked first, because
# the running text sits inside it; it spells its own options with `<result>` inside, so the match
# runs to the last `>` on the line), `auto verify: running (T182)`, and an earlier hook-written
# result. Anything else in that slot is the user's text and is left alone.
NOT_DONE = re.compile(r"^(?:[ \t]*)(?:\*\*Not done:\*\*|Not done:)[ \t]*(?P<body>[^\n]*)$", re.M)
SLOT_UNWRITTEN = (re.compile(r"<[ \t]*auto verify:[^\n]*>"),
                  re.compile(r"auto verify:[ \t]*running[ \t]*\(T182\)"),
                  re.compile(r"auto verify:[ \t]*[☑☐][^;\n]*"))


def warn(message):
    print(f"[hook:stop_auto_verify] {message}", file=sys.stderr)


def evidence_row(text):
    """The `verify` row inside `## Evidence`: (match, offset of the section), or (None, 0)."""
    m = re.search(r"^## Evidence[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return None, 0
    return VERIFY_ROW.search(m.group(1)), m.start(1)


def report_rel(task):
    """The file that holds this task's result, relative to its checkout — the one file a commit may
    touch without invalidating the run (`vr.same_code`)."""
    return vr.MINIMAL_LOG_REL if task.minimal else f"tasks/TASK_REVIEW_{task.task_id}.md"


def filled_for(task, result, notes, head):
    """True when this result stands for `head`: an earlier auto run for the same code, or a result
    the user filled. Either way no new run is due."""
    if vr.AUTO_ROW_TAG in notes:
        verified = vr.ROW_COMMIT.search(notes)
        return bool(verified and vr.same_code(task.checkout, task.task_id, verified.group(1), head,
                                              report_rel(task)))
    return "☑" in result


def due(task, head):
    """True when this task's result is unfilled for `head`. Anything unreadable or missing is one
    stderr line and False — the run is not started."""
    if task.minimal:
        hit, result, notes = vr.record_verify_line(task.body)
        if hit is None and vr.checked_field(task.body) is None:
            warn(f"{task.task_id}: its Decision record has no `Checked:` field — auto verify not "
                 "started")
            return False
        return hit is None or not filled_for(task, result, notes, head)
    row, _ = evidence_row(task.text or "")
    if row is None:
        warn(f"{task.task_id}: no `verify` row under `## Evidence` — auto verify not started")
        return False
    return not filled_for(task, row.group("result"), row.group("notes"), head)


def start(task, head):
    log_rel = os.path.join(RUNS_REL, f"{vr.safe_name(task.task_id, '_untagged')}-{head[:12]}.log")
    log_path = os.path.join(ROOT, log_rel)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    try:
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o644)
    except FileExistsError:
        return  # this task and commit already ran (or is running)
    env = dict(os.environ, **{CHILD_ENV: "1"})
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--run", task.task_id,
                          task.report_path, task.checkout, head, log_rel, task.track],
                         cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=fd, stderr=fd,
                         close_fds=True, start_new_session=True)  # setsid: survives this hook
    finally:
        os.close(fd)
    warn(f"{task.task_id}: auto verify started for commit {head[:12]} — log {log_rel}")


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
    dirs = am.tasks_dirs(ROOT)
    for task_id, row in am.board_rows(kanban, ("Ready for Review",)):
        try:
            task = am.resolve(task_id, row, dirs)
            if task.minimal and not task.exists:
                # A minimal-track task always ends with a Decision record (T178 D5), so a row at
                # Ready for Review without one is worth saying once — and auto mode cannot be read.
                warn(f"{task_id}: no Decision record for it in {vr.MINIMAL_LOG_REL} — auto verify "
                     "not started")
                continue
            if not task.marker:  # D4: the one marker, never inside an HTML comment
                continue
            head = vr.head_commit(task.checkout)
            if head and due(task, head):
                start(task, head)
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


def write_verify_line(log_path, task_id, line):
    """D3: the `verify:` line under the Decision record's `Checked:` field. The file is re-read
    immediately before the write, because a live session may be editing another record in it."""
    with open(log_path, encoding="utf-8") as f:
        text = f.read()
    block = am.record_block(text, task_id, skip_comments=True)
    if block is None:
        print(f"no Decision record for {task_id} in {log_path} — line not written", flush=True)
        return
    start_at, end_at, body = block
    hit, result, notes = vr.record_verify_line(body)
    if hit is not None:
        if "☑" in result and vr.AUTO_ROW_TAG not in notes:
            print("the record's `verify:` line was filled during the run — kept, not overwritten",
                  flush=True)
            return
        new_body = body[:hit.start()] + f"- {line}" + body[hit.end():]
    else:
        field = vr.checked_field(body)
        if field is None:
            print(f"the Decision record for {task_id} has no `Checked:` field — line not written",
                  flush=True)
            return
        new_body = body[:field.end()] + f"\n- {line}" + body[field.end():]
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(text[:start_at] + new_body + text[end_at:])


def write_slot(report_path, task_id, minimal, slot):
    """D7: the report's `Not done:` auto verify slot. The merge clause is left exactly as it is; a
    slot the user wrote, no `Not done:` line, or two of them, write nothing and say so here."""
    with open(report_path, encoding="utf-8") as f:
        text = f.read()
    block = (am.record_block(text, task_id, skip_comments=True) if minimal
             else am.section(text, am.AUTO_SECTION, skip_comments=True))
    if block is None:
        print(f"no report section for {task_id} in {report_path} — auto verify slot not written",
              flush=True)
        return
    start_at, end_at, body = block
    lines = list(NOT_DONE.finditer(body))
    if len(lines) != 1:
        print(f"{len(lines)} `Not done:` line(s) in the report for {task_id} — auto verify slot not "
              "written; never guess which one is the report's", flush=True)
        return
    old = lines[0].group("body")
    for pattern in SLOT_UNWRITTEN:
        unwritten = pattern.search(old)
        if unwritten:
            new = old[:unwritten.start()] + slot + old[unwritten.end():]
            break
    else:
        print(f"the `Not done:` auto verify slot of {task_id} is not the unwritten state "
              f"({old!r}) — left as the user wrote it", flush=True)
        return
    new_body = body[:lines[0].start("body")] + new + body[lines[0].end("body"):]
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text[:start_at] + new_body + text[end_at:])


def run():
    task_id, report_path, checkout, head, log_rel, track = sys.argv[2:8]
    minimal = track == "minimal"
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
    if minimal:
        write_verify_line(report_path, task_id,
                          vr.record_line(head, verdict, session, log_rel, reason))
    else:
        write_row(report_path, task_id, vr.row_cells(head, verdict, session, log_rel, reason))
    write_slot(report_path, task_id, minimal,
               f"auto verify: {vr.RESULT_CELL[verdict]} (session {session}, commit {head}, "
               f"log {log_rel})")


def main():
    if len(sys.argv) == 8 and sys.argv[1] == "--run":
        run()
    elif not os.environ.get(CHILD_ENV):
        stop_hook()
    sys.exit(0)


main()
