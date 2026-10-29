"""Auto close-out (T189): after an auto verify pass, the detached run moves the task's board row to Done.

`stop_auto_verify.py`'s detached run calls `close_out` once its verdict is pass (D1) and it has written
the run record, the result and the report's auto verify slot. A `fail` or `blocked` verdict never
reaches this module: the row stays where it is. The move happens only when all three hold:

  * **D3, forgery guard** — the T182 run record for this task and the head commit exists and says
    pass, for the session that ran, and the merge gate's own `has_filled_verify_row` accepts the
    result under the same rule. A hand-typed `auto-run by hook` result never moves a row.
  * **D2, Hard-Stop Gates 5 and 6** — the tests row is `☑ pass` with pasted output (minimal track: a
    `New test` line under `Checked:`), the trace holds a real test run (`trace_shows_verification`),
    and each of the three UI design rows is `☑ pass` with evidence or N/A with a written reason. A
    pure-backend task's three `☐ N/A` rows with a reason satisfy Gate 6. Auto mode never launders a gate.
  * **D9, the report is complete** — `Mode: auto`, a numbered decision line, `Checks:` (minimal:
    `**Checked:**`), `Memory:`, the `Not done:` auto verify slot filled (T188 D7), and `Not done:`
    still naming the merge. A field that still holds a template `<...>` placeholder is missing.

Every stop writes one line in the run log (`done not moved: <reason>` / `report incomplete: <field>`)
and one `Paused: done not moved — <reasons>` line in the report (D8); a D2 stop also adds the suffix
`done not moved: <reason>` to the hook-written result Notes. A move writes the D8 `Closed:` line, then
re-reads the report, then moves the row (D4): `- [ ]` becomes `- [x]`, the row goes to the top of
`### Done`, it gains `Done <date>: auto verify pass (session <id>, commit <sha>)`, and `**Last
updated**` is set to that date. Nothing else in the row is rewritten. Each line is added once; a line
the user wrote is never rewritten.

The registry is the main checkout's `PROJECT_KANBAN.md` (`root`), re-read just before the write and
matched by task ID, never by line number. A row already gone from Ready for Review (the user moved it)
is left alone, with no note. One lock file serialises close-outs, so two runs that end together cannot
lose each other's board write. This module runs no git command that writes, writes no memory file,
and never merges, pushes or runs `ship` (D5, D6).

The Gate 5/6 and record readers are the merge gate's own (`pre_bash_block_unsafe_merge.py`), loaded
without running its bottom-of-file `main()` — the technique its tests use. Any failure to load them
is an exception, which the caller turns into "done not moved" (fail closed, never a crash).
"""
import fcntl
import os
import re
import types
from contextlib import contextmanager
from datetime import date

import auto_mode as am
import verify_record as vr

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_FILE = os.path.join(HOOKS_DIR, "pre_bash_block_unsafe_merge.py")
KANBAN_NAME = "PROJECT_KANBAN.md"
LOCK_REL = os.path.join(".claude", "hooks", ".state", "closeout.lock")  # gitignored hook state

PAUSED = "Paused: done not moved — "
NOT_MOVED = "done not moved: "
INCOMPLETE = "report incomplete: "
TESTS_ROW = "New test(s) cover"

# A template placeholder (`<what was decided>`, `<command>`), never real text such as `<ID>` or `<=`.
PLACEHOLDER = re.compile(r"<[a-z][^<>\n]*>")
FIELD = r"^[ \t]*(?:\*\*)?{name}(?:\*\*)?(?P<value>[^\n]*)$"
MEMORY_LINE = re.compile(FIELD.format(name="Memory:"), re.M)
CHECKS_LINE = re.compile(FIELD.format(name="Checks:"), re.M)
NOT_DONE_LINE = re.compile(FIELD.format(name="Not done:"), re.M)
DECISION_LINE = re.compile(r"^[ \t]*\d+\.[ \t]+(?P<value>\S[^\n]*)$", re.M)
NEW_TEST_BULLET = re.compile(r"^[ \t]*[-+*][ \t]*New tests?\b(?P<value>[^\n]*)$", re.M | re.I)
SLOT_FILLED = re.compile(r"auto verify:[ \t]*[☑☐]")
MERGE_WORD = re.compile(r"\bmerge\b", re.I)
VERIFY_ROW = re.compile(r"^\|\s*verify\s*\|(?P<result>[^|\n]*)\|(?P<notes>[^|\n]*)\|?[^\n]*$",
                        re.M | re.I)
NA_CHECKED = re.compile(r"☑\s*\**\s*N/A", re.I)
NA_ONLY = re.compile(r"\s*☐\s*\**\s*N/A\s*\**\s*", re.I)

_gate = None


def filled(value):
    """True for text that is there and is not a template placeholder."""
    return bool(value and value.strip() and not PLACEHOLDER.search(value))


def has_memory_line(body):
    """D5: the report block holds a `Memory:` line that is not a placeholder."""
    return any(filled(m.group("value")) for m in MEMORY_LINE.finditer(body or ""))


def report_gaps(body, minimal):
    """D9: each required field the report block lacks, in the order the guide lists them."""
    body = am.COMMENT.sub("", body or "")
    gaps = []
    if am.MARKER not in [line.strip() for line in body.splitlines()]:
        gaps.append(am.MARKER)
    if not any(filled(m.group("value")) for m in DECISION_LINE.finditer(body)):
        gaps.append("decision line")
    if minimal:
        field = vr.checked_field(body)
        bullets = field.group(0).splitlines()[1:] if field else []
        if not any(filled(re.sub(r"^[ \t]*[-+*]", "", b)) for b in bullets):
            gaps.append("**Checked:**")
    elif not any(filled(m.group("value")) for m in CHECKS_LINE.finditer(body)):
        gaps.append("Checks:")
    if not has_memory_line(body):
        gaps.append("Memory:")
    not_done = list(NOT_DONE_LINE.finditer(body))
    if len(not_done) != 1:
        gaps.append("Not done:")
    else:
        value = not_done[0].group("value")
        if not SLOT_FILLED.search(value):
            gaps.append("auto verify slot")
        if not MERGE_WORD.search(value):
            gaps.append("Not done: merge")
    return gaps


def load_gate():
    """The merge gate as a module, without running its bottom-of-file `main()`."""
    global _gate
    if _gate is None:
        with open(GATE_FILE, encoding="utf-8") as f:
            source = f.read()
        head, marker, tail = source.rpartition("\nmain()")
        if not marker or tail.strip():
            raise RuntimeError("the merge gate no longer ends in a bare main() call")
        module = types.ModuleType("_auto_closeout_merge_gate")
        module.__file__ = GATE_FILE
        try:
            exec(compile(head + "\n", GATE_FILE, "exec"), module.__dict__)
        except SystemExit:  # its guarded import failed: it printed a block and exited
            raise RuntimeError("the merge gate's Evidence readers are unavailable")
        _gate = module
    return _gate


def _unfilled_notes(notes):
    text = (notes or "").strip()
    return not text or bool(re.fullmatch(r"\[[^\]]*\]", text)) or bool(PLACEHOLDER.search(text))


def evidence_gaps(gate, task_id, tasks_dir, minimal, body):
    """D2: why Hard-Stop Gate 5 or 6 is not met, or []."""
    gaps = []
    if minimal:
        field = vr.checked_field(am.COMMENT.sub("", body or ""))
        tests = [m for m in NEW_TEST_BULLET.finditer(field.group(0))] if field else []
        if not any(filled(m.group("value")) for m in tests):
            gaps.append("Gate 5: no `New test` line with its result under `Checked:`")
    else:
        section = gate.read_guide_section(task_id, "Evidence", tasks_dir)
        if not section:
            return ["Gate 5: no `## Evidence` section"]
        tests = gate._companion_row_pattern(TESTS_ROW).search(section)
        if (tests is None or not gate.CHECKED_PASS_PATTERN.search(tests.group("result"))
                or gate.CHECKED_FAIL_PATTERN.search(tests.group("result"))
                or _unfilled_notes(tests.group("notes"))):
            gaps.append("Gate 5: the tests row is not `☑ pass` with pasted output")
        for name, pattern in gate.COMPANION_ROW_PATTERNS:
            if not name.startswith("UI:"):
                continue
            row = pattern.search(section)
            result, notes = (row.group("result"), row.group("notes")) if row else ("", "")
            if gate.CHECKED_FAIL_PATTERN.search(result):
                gaps.append(f"Gate 6: the `{name}` row is `☑ fail`")
            elif gate.CHECKED_PASS_PATTERN.search(result) or NA_CHECKED.search(result) \
                    or NA_ONLY.fullmatch(result):
                if _unfilled_notes(notes):
                    gaps.append(f"Gate 6: the `{name}` row has no "
                                f"{'reason' if 'N/A' in result else 'evidence'}")
            else:
                gaps.append(f"Gate 6: the `{name}` row is blank")
    if not gate.trace_shows_verification(task_id):
        gaps.append(f"Gate 5: no test run in memory/event-trace/{task_id}.jsonl")
    return gaps


def record_gaps(gate, root, task_id, tasks_dir, head, session):
    """D3: why the pass is not proved by the run record the agent cannot write, or []."""
    record = vr.read_record(root, task_id, head)
    if not record:
        return [f"no run record for {task_id} at commit {head[:12]}"]
    if record.get("verdict") != "pass":
        return [f"the run record says {record.get('verdict')!s}, not pass"]
    if (record.get("task"), record.get("commit"), record.get("session")) != (task_id, head, session):
        return ["the run record names another task, commit or session"]
    if not gate.has_filled_verify_row(task_id, [tasks_dir]):
        return ["the verify result is not confirmed by its run record (the merge gate's rule)"]
    return []


@contextmanager
def _lock(root):
    path = os.path.join(root, LOCK_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _write(path, text):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def _block(text, task_id, minimal):
    return (am.record_block(text, task_id, skip_comments=True) if minimal
            else am.section(text, am.AUTO_SECTION, skip_comments=True))


def add_line(report_path, task_id, minimal, line):
    """Append `line` at the end of the task's report block, once. True when it is there after."""
    text = am.read(report_path)
    block = _block(text or "", task_id, minimal) if text is not None else None
    if block is None:
        return False
    start, end, body = block
    if line in [l.strip() for l in body.splitlines()]:
        return True
    new_body = body.rstrip("\n") + "\n" + line + "\n" + ("\n" if end < len(text) else "")
    _write(report_path, text[:start] + new_body + text[end:])
    return True


def add_notes_suffix(report_path, task_id, minimal, reason):
    """D2: `done not moved: <reason>` at the end of the hook-written result. A result the user wrote,
    or one that already carries the suffix, is left exactly as it is."""
    text = am.read(report_path)
    if text is None:
        return
    suffix = "; " + NOT_MOVED + re.sub(r"[|\r\n]", " ", reason)
    if minimal:
        block = am.record_block(text, task_id, skip_comments=True)
        if block is None:
            return
        start, _, body = block
        hit, _, notes = vr.record_verify_line(body)
        if hit is None or vr.AUTO_ROW_TAG not in notes or NOT_MOVED in notes:
            return
        at = start + hit.end()
    else:
        section = re.search(r"^## Evidence[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        row = VERIFY_ROW.search(section.group(1)) if section else None
        if row is None or vr.AUTO_ROW_TAG not in row.group("notes") or NOT_MOVED in row.group("notes"):
            return
        at = section.start(1) + row.end("notes")
        while at > 0 and text[at - 1] == " ":  # keep the cell's closing space after the suffix
            at -= 1
    _write(report_path, text[:at] + suffix + text[at:])


def _section_span(board, title):
    m = re.search(rf"^### {re.escape(title)}[ \t]*\n(.*?)(?=^###|\Z)", board, re.S | re.M)
    return (m.start(1), m.end(1)) if m else None


def ready_row(board, task_id):
    """(start, end) of the task's one row in `### Ready for Review` (newline included), or None."""
    span = _section_span(board, "Ready for Review")
    if span is None:
        return None
    hits = []
    for m in re.finditer(r"^[^\n]*\n?", board[span[0]:span[1]], re.M):
        line = m.group(0)
        row_id = am.ROW_ID.search(line)
        if line.strip().startswith("- ") and row_id and row_id.group(1) == task_id:
            hits.append((span[0] + m.start(), span[0] + m.end()))
    return hits[0] if len(hits) == 1 else None


def move_to_done(board_path, task_id, note, day):
    """D4: the row from Ready for Review to the top of Done, `- [x]`, `note` appended. True if moved."""
    board = am.read(board_path) or ""
    found = ready_row(board, task_id)
    if found is None or _section_span(board, "Done") is None:
        return False
    row = board[found[0]:found[1]].rstrip("\n")
    row = re.sub(r"^([ \t]*)- \[ \]", r"\1- [x]", row, count=1) + f" | {note}\n"
    board = board[:found[0]] + board[found[1]:]
    done = re.search(r"^### Done[ \t]*\n", board, re.M)
    board = board[:done.end()] + row + board[done.end():]
    board = re.sub(r"^\*\*Last updated\*\*:[^\n]*", f"**Last updated**: {day}", board, count=1,
                   flags=re.M)
    _write(board_path, board)
    return True


def close_out(root, task_id, report_path, head, session, minimal, say=print):
    """After a pass: move the row to Done when D2, D3 and D9 all hold; else say why and pause."""
    tasks_dir = os.path.dirname(os.path.abspath(report_path))
    board_path = os.path.join(root, KANBAN_NAME)
    with _lock(root):
        text = am.read(report_path)
        if text is None:
            say(f"{INCOMPLETE}file missing — done not moved")
            return False
        if ready_row(am.read(board_path) or "", task_id) is None:
            # The user already moved it (or it was never there): nothing to move, no note added.
            say(f"{task_id} has no row in Ready for Review — nothing moved")
            return False
        block = _block(text, task_id, minimal)
        body = block[2] if block else ""
        gate = load_gate()
        proof = record_gaps(gate, root, task_id, tasks_dir, head, session)
        evidence = evidence_gaps(gate, task_id, tasks_dir, minimal, body)
        reasons = proof + evidence + [INCOMPLETE + f for f in report_gaps(body, minimal)]
        day = date.today().isoformat()
        if not reasons:
            closed = (f"Closed: row moved to Done {day} — auto verify pass (session {session}, "
                      f"commit {head}); Gates 5 and 6 checked")
            add_line(report_path, task_id, minimal, closed)
            again = am.read(report_path) or ""
            block = _block(again, task_id, minimal)
            after = block[2] if block else ""
            reasons = [INCOMPLETE + f for f in report_gaps(after, minimal)]
            if closed not in [l.strip() for l in am.COMMENT.sub("", after).splitlines()]:
                reasons.append(INCOMPLETE + "Closed:")
        if reasons:
            for reason in reasons:
                say(reason if reason.startswith(INCOMPLETE) else NOT_MOVED + reason)
            if evidence:
                add_notes_suffix(report_path, task_id, minimal, "; ".join(evidence))
            if not add_line(report_path, task_id, minimal, PAUSED + "; ".join(reasons)):
                say(f"no report section for {task_id} — the `Paused:` line was not written")
            return False
        note = f"Done {day}: auto verify pass (session {session}, commit {head})"
        if not move_to_done(board_path, task_id, note, day):
            say(f"{task_id}: the row left Ready for Review during the close-out — nothing moved")
            return False
        say(f"{task_id}: moved to Done on {board_path}")
        return True
