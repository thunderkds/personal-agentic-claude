#!/usr/bin/env python3
"""
Stop hook — fires when Claude is about to stop (T180 D8).

Auto mode (`docs/claude-md/tracks.md` `## Auto mode`) removes the user's stops, so the final report
is the only account of what was decided. This hook checks it before the run may end. For each
auto-mode task whose board row is In Progress or Ready for Review, it blocks the stop when:

  (1) the report has no `## Auto decisions` section whose first line is `Mode: auto` (extended), or
      the Decision record does not start with `Mode: auto` (minimal), or there is no report file;
  (2) at Risk Medium/High, a `⚠` line is not `DEBATED` with exactly 2 / 3 Advocates named;
  (3) the event trace holds fewer Advocate `Agent` calls (description starting `Advocate`) than
      2 / 3 per `DEBATED` line (2 at Risk Low);
  (4) on the extended track, the trace has no `code-review` Skill call, or no `security-review`
      Skill call at Risk Medium/High.
  (5) at Risk High, no `DEBATED` line names 3 Advocates, or the trace holds fewer than 3 Advocate
      `Agent` calls (D10): at least one High-risk decision is always debated.

Which tasks (D9): board rows in In Progress or Ready for Review, plus — so a project with no
`PROJECT_KANBAN.md` is still checked — every `tasks/TASK_REVIEW_*.md` carrying `## Auto decisions`
or a `Mode: auto` line, and the newest `tasks/MINIMAL_LOG.md` record carrying `Mode: auto` or
`[auto]`. Skipped as finished: a task whose row is in Done, and a review file whose `verify` row
has `☑ pass` in its Result cell. A board row counts as auto mode when its report is marked as
above, or the session's request carries `[auto]` (outside code spans) and the task's files
changed after it.

Labels (D9): at Risk Medium/High a decision line is a choice — so it must be `DEBATED` with
exactly 2 / 3 Advocates named — when it is flagged `⚠`, is a `SAFER OPTION`, is a `RULE:` that
cites no written rule (`path:line`, `path § <heading>`, `path` `### <section>`), or is a `FACT:`
with no Citation (`path:line "quoted text"`). The block reason names the decision number and
its label. Risk comes from the guide's `**Risk Level**`, else the review file, else the board
row, else Low; a Decision record is Low unless it says otherwise.

Never loops: on the second fire (`stop_hook_active`) it allows the stop and appends
`Paused: auto-mode check failed — <reasons>` to the report. Fails open: an unreadable file skips
that task with one stderr line. It never reads or writes the merge gate's Evidence.

Trace: `memory/event-trace/<ID>.jsonl` (all records) plus `memory/event-trace/_untagged.jsonl`
records from the last CLAUDE_AUTO_CHECK_WINDOW_S seconds (default 6h). Advocate and Scanner
prompts carry no task ID, so their calls land in `_untagged.jsonl` unless the active-task state
file is set.
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")
TASKS_DIR = os.path.join(ROOT, "tasks")
TRACE_DIR = os.path.join(ROOT, "memory", "event-trace")

TAG = "[auto]"
MARKER = "Mode: auto"
PAUSE = "Paused: auto-mode check failed — "
ADVOCATES_BY_RISK = {"Medium": 2, "High": 3}
D10_REASON = "Risk High, but no decision was DEBATED with 3 Advocates"
WINDOW_DEFAULT_S = 6 * 3600

ROW_ID = re.compile(r"\*\*([A-Za-z]+-?\d+)\*\*")
MINIMAL_MARKER = re.compile(r"\|\s*Track: minimal\b")
COMMENT = re.compile(r"<!--.*?-->", re.S)
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
RISK = re.compile(r"\bRisk(?: Level)?\**:\**\s*(Low|Med(?:ium)?|High)\b")
LABEL = re.compile(r"\b(DEBATED|SAFER OPTION|RULE|FACT):")
# D9: at Risk Medium/High a RULE must name a written rule, a FACT must carry a Citation.
PATH = r"[\w./-]*[\w-]+\.[A-Za-z0-9]+"
CITED_RULE = re.compile(rf"{PATH}(?::\d+|`?\s*§\s*\S|`?\s+`?###\s+\S)")
CITATION = re.compile(rf"{PATH}:\d+\s+\"[^\"]+\"")
VERIFY_PASSED = re.compile(r"^\|\s*verify\s*\|[^|\n]*☑\s*pass", re.M | re.I)


class Unreadable(Exception):
    pass


def warn(message):
    print(f"[hook:stop_auto_mode_check] {message}", file=sys.stderr)


def read(path):
    """Text of `path`, None when it does not exist, Unreadable on any other failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as exc:
        raise Unreadable(f"cannot read {os.path.relpath(path, ROOT)} ({type(exc).__name__})")


def window_s():
    try:
        value = int(os.environ.get("CLAUDE_AUTO_CHECK_WINDOW_S", ""))
        return value if value > 0 else WINDOW_DEFAULT_S
    except ValueError:
        return WINDOW_DEFAULT_S


def parse_ts(value):
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def worktree_tasks_dirs():
    """Each live worktree's `tasks/` (main checkout excluded); [] on any failure."""
    try:
        done = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=ROOT,
                              capture_output=True, text=True, timeout=5)
        if done.returncode != 0:
            return []
        paths = [l[len("worktree "):].strip() for l in done.stdout.splitlines()
                 if l.startswith("worktree ")]
        return [os.path.join(p, "tasks") for p in paths
                if p and os.path.abspath(p) != os.path.abspath(ROOT)]
    except Exception:
        return []


def find(name, dirs):
    """First existing `<dir>/<name>`, main checkout first; else the main-checkout path."""
    for d in dirs:
        path = os.path.join(d, name)
        if os.path.exists(path):
            return path
    return os.path.join(dirs[0], name)


def board_rows(kanban, titles=("In Progress", "Ready for Review")):
    rows = []
    for title in titles:
        m = re.search(rf"^### {re.escape(title)}\n(.*?)(?=^###|\Z)", kanban, re.S | re.M)
        for line in (m.group(1).splitlines() if m else []):
            hit = ROW_ID.search(line)
            if line.strip().startswith("- ") and hit:
                rows.append((hit.group(1), line))
    return rows


def file_tasks(dirs, skip):
    """D9: auto-mode tasks found from their files, so a project with no board is still checked.
    Every `TASK_REVIEW_*.md` carrying `## Auto decisions` or a `Mode: auto` line, and the newest
    `MINIMAL_LOG.md` record when it carries `Mode: auto` or `[auto]`. `skip` holds IDs already
    found on the board (In Progress, Ready for Review or Done)."""
    found = {}
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "TASK_REVIEW_*.md"))):
            task_id = os.path.basename(path)[len("TASK_REVIEW_"):-len(".md")]
            if task_id in skip or task_id in found or not re.fullmatch(r"[A-Za-z]+-?\d+", task_id):
                continue
            try:
                clean = COMMENT.sub("", read(path) or "")
            except Unreadable as exc:
                warn(f"{exc} — auto-mode check skipped for {task_id}")
                continue
            if section(clean, "## Auto decisions") or MARKER in clean.splitlines():
                found[task_id] = ("", False)
    try:
        log = COMMENT.sub("", read(find("MINIMAL_LOG.md", dirs)) or "")
    except Unreadable as exc:
        warn(f"{exc} — auto-mode check skipped for the newest Decision record")
        log = ""
    newest = re.search(r"^## ([A-Za-z]+-?\d+) — [^\n]*\n(.*?)(?=^## |\Z)", log, re.S | re.M)
    if newest and newest.group(1) not in skip and newest.group(1) not in found:
        body = newest.group(2)
        if MARKER in body.splitlines() or TAG in body:
            found[newest.group(1)] = ("", True)
    return found


def auto_request_time(transcript_path):
    """Timestamp of the first user message carrying `[auto]` outside code spans, or None."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if not isinstance(entry, dict) or entry.get("type") != "user" or entry.get("isMeta"):
                    continue
                content = (entry.get("message") or {}).get("content")
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content
                                       if isinstance(b, dict) and b.get("type") == "text")
                if isinstance(content, str) and TAG in CODE.sub(" ", content):
                    return parse_ts(entry.get("timestamp"))
    except Exception as exc:
        warn(f"cannot read the transcript ({type(exc).__name__}) — `[auto]` request not checked")
    return None


def section(text, heading_pattern):
    """(start, end, body) of the block under the first heading matching `heading_pattern`."""
    m = re.search(rf"^{heading_pattern}[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return (m.start(1), m.end(1), m.group(1)) if m else None


def first_line(body):
    lines = [l for l in body.splitlines() if l.strip()]
    return lines[0] if lines else ""


def trace_records(task_id):
    records = []
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_s())
    for name, windowed in ((f"{task_id}.jsonl", False), ("_untagged.jsonl", True)):
        try:
            with open(os.path.join(TRACE_DIR, name), encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            continue
        except Exception as exc:
            warn(f"cannot read memory/event-trace/{name} ({type(exc).__name__}) — counted as empty")
            continue
        for line in lines:
            try:
                record = json.loads(line)
            except Exception:
                continue
            if not isinstance(record, dict):
                continue
            if windowed:
                ts = parse_ts(record.get("timestamp"))
                if ts is None or ts < cutoff:
                    continue
            records.append(record)
    return records


def field(summary, key):
    """`key` from a trace record's summary: JSON first, then the truncated-JSON fallback."""
    try:
        value = json.loads(summary).get(key)
        return value if isinstance(value, str) else ""
    except Exception:
        m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)', summary or "")
        return m.group(1) if m else ""


def choice_reason(line, need):
    """Why a report line at Risk Medium/High is an unsettled choice, or None (D8, D9)."""
    if not re.match(r"\d+\.\s", line) and "⚠" not in line:
        return None
    label = LABEL.search(line)
    kind = label.group(1) if label else None
    after = line[label.end():] if label else line
    if kind == "DEBATED":
        named = len(re.findall(r"\bAdvocate \d+:", line))
        return None if named == need else f"it names {named} Advocates, not exactly {need}"
    if "⚠" in line:
        return "it is flagged ⚠"
    if kind == "SAFER OPTION":
        return "a safer-option pick is a choice"
    if kind == "RULE" and not CITED_RULE.search(after):
        return ("its RULE cites no written rule (`path:line`, `path § <heading>` or "
                "`docs/claude-md/tracks.md` `### <section>`)")
    if kind == "FACT" and not CITATION.search(after):
        return 'its FACT has no Citation (`path:line "quoted text"`)'
    return None


def check_task(task_id, row, request_ts, dirs):
    """The reasons this task's report fails, or [] (also [] when the task is not auto mode)."""
    minimal = bool(MINIMAL_MARKER.search(row))
    if minimal:
        report_path = find("MINIMAL_LOG.md", dirs)
        text = read(report_path)
        block = section(COMMENT.sub("", text), rf"## {re.escape(task_id)} — ") if text else None
        body = block[2] if block else ""
        marked = MARKER in body.splitlines() or TAG in body
        touched = [report_path] if block else []
        risk_text, strict = body, first_line(body) == MARKER
        missing = f"its Decision record in tasks/MINIMAL_LOG.md does not start with `{MARKER}`"
    else:
        report_path = find(f"TASK_REVIEW_{task_id}.md", dirs)
        text = read(report_path)
        if text and VERIFY_PASSED.search(text):
            return []  # D9: a verified task is finished, not an open auto-mode run
        clean = COMMENT.sub("", text or "")
        block = section(clean, "## Auto decisions")
        body = block[2] if block else ""
        marked = bool(block) or MARKER in clean.splitlines()
        guide_path = find(f"TASK_GUIDE_{task_id}.md", dirs)
        guide = read(guide_path) or ""
        touched = [p for p in (report_path, guide_path) if os.path.exists(p)]
        hit = re.search(r"\*\*Risk Level\*\*:\s*(Low|Med(?:ium)?|High)\b", guide)
        review_risk = RISK.search(clean)
        risk_text = hit.group(0) if hit else (review_risk.group(0) if review_risk else row)
        strict = bool(block) and first_line(body) == MARKER
        missing = (f"no tasks/TASK_REVIEW_{task_id}.md with `## Auto decisions` starting `{MARKER}`"
                   if text is None else
                   f"tasks/TASK_REVIEW_{task_id}.md has no `## Auto decisions` section starting "
                   f"with `{MARKER}`")

    if not marked and request_ts is not None:
        marked = any(datetime.fromtimestamp(os.path.getmtime(p), timezone.utc) >= request_ts
                     for p in touched)
    if not marked:
        return []

    hit = RISK.search(risk_text)
    risk = {"Med": "Medium"}.get(hit.group(1), hit.group(1)) if hit else "Low"
    need_per_line = ADVOCATES_BY_RISK.get(risk)
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    reasons = [] if strict else [missing]

    if need_per_line:
        for line in lines:
            why = choice_reason(line, need_per_line)
            if why:
                number = re.match(r"(\d+)\.", line)
                label = LABEL.search(line)
                which = f"decision {number.group(1)}" if number else f"`{line[:40]}`"
                reasons.append(f"Risk {risk}: {which} (`{label.group(1) if label else '⚠'}`) is a "
                               f"choice — {why} — so it must be `DEBATED` with exactly "
                               f"{need_per_line} Advocates named")

    records = trace_records(task_id)
    debated = [l for l in lines if "DEBATED:" in l]
    have = sum(1 for r in records if r.get("tool_name") == "Agent"
               and field(r.get("summary"), "description").startswith("Advocate"))
    if risk == "High":
        # D10: at Risk High at least one decision is always debated by 3 Advocates; cited RULE
        # lines do not replace it ("This is force for the high risk", D7).
        three = [l for l in debated if len(re.findall(r"\bAdvocate \d+:", l)) == 3]
        if not three or have < 3:
            reasons.append(D10_REASON)
    if debated:
        need = (need_per_line or 2) * len(debated)
        if have < need:
            reasons.append(f"{len(debated)} `DEBATED` line(s) need ≥{need} Advocate `Agent` calls "
                           f"(description starting `Advocate`); the trace has {have}")

    if not minimal:
        skills = {field(r.get("summary"), "skill").strip() for r in records
                  if r.get("tool_name") == "Skill"}
        if "code-review" not in skills:
            reasons.append("extended track, but the trace has no `code-review` Skill call "
                           "(Stage 4 runs in auto mode)")
        if need_per_line and "security-review" not in skills:
            reasons.append(f"Risk {risk}, but the trace has no `security-review` Skill call")

    return [(report_path, minimal, reason) for reason in reasons]


def record_pause(report_path, minimal, task_id, reasons):
    """Append the pause line inside the task's report block; never twice."""
    text = read(report_path)
    if text is None:
        warn(f"{task_id}: no report file to record the pause in")
        return
    pattern = rf"## {re.escape(task_id)} — " if minimal else "## Auto decisions"
    block = section(text, pattern)
    if not block:
        warn(f"{task_id}: no report section to record the pause in")
        return
    start, end, body = block
    if PAUSE in body:
        return
    line = PAUSE + "; ".join(reasons)
    new_body = body.rstrip("\n") + "\n" + line + "\n" + ("\n" if end < len(text) else "")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text[:start] + new_body + text[end:])


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(event, dict):
        sys.exit(0)
    try:
        kanban = read(KANBAN)
    except Unreadable as exc:
        warn(f"{exc} — board rows skipped; tasks are still found from their files")
        kanban = None
    kanban = kanban or ""  # D9: no board is fine; tasks are also found from their files

    dirs = [TASKS_DIR] + worktree_tasks_dirs()
    request_ts = auto_request_time(event.get("transcript_path"))
    open_rows = board_rows(kanban)
    done = {task_id for task_id, _ in board_rows(kanban, ("Done",))}
    tasks = [(task_id, row) for task_id, row in open_rows]
    skip = done | {task_id for task_id, _ in open_rows}
    for task_id, (_, minimal) in file_tasks(dirs, skip).items():
        tasks.append((task_id, "| Track: minimal" if minimal else ""))
    failures = {}
    for task_id, row in tasks:
        try:
            for report_path, minimal, reason in check_task(task_id, row, request_ts, dirs):
                failures.setdefault(task_id, (report_path, minimal, []))[2].append(reason)
        except Unreadable as exc:
            warn(f"{exc} — auto-mode check skipped for {task_id}")
        except Exception as exc:  # fail open: a bug here must never trap the session
            warn(f"{task_id}: check failed ({type(exc).__name__}: {exc}) — skipped")
    if not failures:
        sys.exit(0)

    if event.get("stop_hook_active"):
        for task_id, (report_path, minimal, reasons) in failures.items():
            try:
                record_pause(report_path, minimal, task_id, reasons)
            except Exception as exc:
                warn(f"{task_id}: could not record the pause ({type(exc).__name__})")
            warn(f"{task_id}: stop allowed on the second fire; {PAUSE}{'; '.join(reasons)}")
        sys.exit(0)

    lines = [f"{tid}: {reason}" for tid, (_, _, reasons) in failures.items() for reason in reasons]
    print(json.dumps({"decision": "block", "reason": (
        "[hook:stop_auto_mode_check] Auto-mode final report check failed — fix it before you stop "
        "(docs/claude-md/tracks.md `## Auto mode`):\n  • " + "\n  • ".join(lines))}))


main()
