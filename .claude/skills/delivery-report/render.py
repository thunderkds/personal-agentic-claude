#!/usr/bin/env python3
"""
Delivery Report renderer — the ONE parser (AC1) that reads a task's
``## Demonstration`` block from either TASK_GUIDE flavor (implementation or
bugfix) and renders it against ``templates/delivery_report_template.html``.

Both flavors give the Demonstration block identical field names and ordering
(T053), so a single regex-based parser serves both by construction. If a
flavor-specific branch shows up here, that is a signal the two block shapes
have drifted apart — stop and report to the Supervisor rather than adding one.

WITNESS (AC7) is never read as free text from the guide. It is always
resolved from ``memory/event-trace/<task>.jsonl`` — see `resolve_witness`.
If no trace file/record exists, it renders as explicitly underived.

Usage:
    python3 .claude/skills/delivery-report/render.py <TASK_ID> <guide_path> <branch> [out_dir]

Prints the rendered HTML to stdout and the save path to stderr, matching the
thinking-report / html-report convention of a Supervisor-driven save step.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TEMPLATE_PATH = os.path.join(ROOT, "templates", "delivery_report_template.html")
TASKS_DIR = os.path.join(ROOT, "tasks")

# Both sections may live in the guide or in the sibling TASK_REVIEW file
# (T064) — one resolver, shared with the two hooks, so this file does not
# become a third independent copy of the same fallback.
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks", "lib"))
from guide_sections import read_review_text, resolve_section  # noqa: E402

DEMO_SECTION_RE = re.compile(r"^##\s*Demonstration\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
FIELD_RE = re.compile(
    r"\*\*(BEFORE|AFTER|DELTA|WITNESS)\*\*[^:\n]*:\s*(.*?)"
    r"(?=\n\s*\*\*(?:BEFORE|AFTER|DELTA|WITNESS)\*\*[^:\n]*:|\Z)",
    re.S,
)
REPRO_ROW_RE = re.compile(r"^\|\s*Repro loop\s*\|.*?\|\s*(.*?)\s*\|\s*$", re.M)
PLACEHOLDER_RE = re.compile(r"^\s*(\[.*\]|<.*>)\s*$", re.S)


class NoDemonstrationBlock(Exception):
    """Raised when a guide predates T053 and has no `## Demonstration` section."""


def parse_demonstration(guide_text, review_text=None):
    """Parse BEFORE/AFTER/DELTA from the Demonstration block — resolved from
    the guide first, then the sibling `TASK_REVIEW_Txxx.md` (T064).

    Raises NoDemonstrationBlock when *neither* source carries the block, so the
    pre-T053 edge case is still reported clearly rather than swallowed by the
    new fallback."""
    block = resolve_section(guide_text, review_text, "Demonstration")
    if block is None:
        raise NoDemonstrationBlock(
            "no '## Demonstration' section found in the guide or its TASK_REVIEW sibling"
        )

    fields = {}
    for fm in FIELD_RE.finditer(block):
        fields[fm.group(1)] = fm.group(2).strip()

    before = fields.get("BEFORE", "")
    # Bugfix flavor's BEFORE points at the Phase 1 repro loop by name rather
    # than containing it — resolve the reference from the Evidence table's
    # "Repro loop" row instead of printing the pointer text raw.
    if re.search(r"repro loop", before, re.I):
        # The row lives wherever the Evidence table resolved — the pointer must
        # follow the table when it moves to the review file.
        evidence = resolve_section(guide_text, review_text, "Evidence")
        row = REPRO_ROW_RE.search(evidence if evidence is not None else guide_text)
        if row and row.group(1).strip():
            before = f"[resolved from Evidence 'Repro loop' row] {row.group(1).strip()}"

    return {
        "before": before,
        "after": fields.get("AFTER", ""),
        "delta": fields.get("DELTA", ""),
    }


def field_is_blank(value):
    """Same definition as pre_agent_validate_guide.py's before_field_is_blank:
    empty, or only an unfilled [...]/<...> placeholder."""
    if not value or not value.strip():
        return True
    return bool(PLACEHOLDER_RE.match(value.strip()))


EVIDENCE_ROW_RE = re.compile(
    r"^\|\s*(?P<check>[^|]+?)\s*\|\s*(?P<result>[^|]+?)\s*\|\s*(?P<notes>[^|]*?)\s*\|\s*$",
    re.M,
)


def parse_evidence_table(guide_text, review_text=None):
    """Return (rows) where each row is {check, result, notes, status} and
    status is one of 'filled' | 'blank' | 'n_a'. Generic across both flavors
    and both row counts (9 implementation / 12 bugfix) — counts whatever rows
    are present rather than assuming a fixed total.

    Resolved guide-first, then the sibling `TASK_REVIEW_Txxx.md` (T064). The
    count comes from **wherever the table resolved** — the two sources are
    never summed, or a split pair whose guide still had a stale table would
    report a total spanning a file boundary."""
    section = resolve_section(guide_text, review_text, "Evidence")
    rows = []
    if section is None:
        return rows
    for rm in EVIDENCE_ROW_RE.finditer(section):
        check = rm.group("check").strip()
        result = rm.group("result").strip()
        notes = rm.group("notes").strip()
        if check.lower() in ("check", "") or set(check) == {"-"}:
            continue
        status = classify_evidence_row(result, notes)
        rows.append({"check": check, "result": result, "notes": notes, "status": status})
    return rows


def classify_evidence_row(result, notes):
    has_unfilled_box = "☐" in result
    notes_is_blank = field_is_blank(notes)
    if not has_unfilled_box:
        if re.search(r"n[/-]?a\b", result, re.I) and not re.search(r"pass|fail", result, re.I):
            return "n_a"
        if not notes_is_blank or re.search(r"pass|fail", result, re.I):
            return "filled"
    return "blank"


def resolve_witness(task_id, root=ROOT):
    """AC7: WITNESS is derived from memory/event-trace/<task>.jsonl, never
    accepted as free text. Returns a description string, never a fabricated
    name. If no trace record exists, says so explicitly."""
    trace_path = os.path.join(root, "memory", "event-trace", f"{task_id}.jsonl")
    if not os.path.isfile(trace_path):
        return "WITNESS underived — no memory/event-trace/{}.jsonl found".format(task_id)

    records = []
    with open(trace_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not records:
        return "WITNESS underived — memory/event-trace/{}.jsonl exists but has no records".format(task_id)

    timestamps = sorted(r.get("timestamp", "") for r in records if r.get("timestamp"))
    first_ts = timestamps[0] if timestamps else "unknown"
    last_ts = timestamps[-1] if timestamps else "unknown"
    return (
        f"Derived from memory/event-trace/{task_id}.jsonl: {len(records)} tool-call record(s), "
        f"{first_ts} → {last_ts} (session trace, not a claimed name)"
    )


def escape_none(value):
    return value if value else ""


def render(template_text, slots):
    out = template_text
    for key, value in slots.items():
        out = out.replace("{{" + key + "}}", escape_none(value))
    remaining = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if remaining:
        raise ValueError(f"unfilled template slots remain: {remaining}")
    return out


def build_slots(task_id, branch, guide_text, root=ROOT, tasks_dir=None):
    review_text = read_review_text(task_id, tasks_dir or TASKS_DIR)
    try:
        demo = parse_demonstration(guide_text, review_text)
        no_demo = False
    except NoDemonstrationBlock:
        demo = {
            "before": "(no '## Demonstration' section in this guide — it predates T053)",
            "after": "(no '## Demonstration' section in this guide — it predates T053)",
            "delta": "(no '## Demonstration' section in this guide — it predates T053)",
        }
        no_demo = True

    evidence_rows = parse_evidence_table(guide_text, review_text)
    total = len(evidence_rows)
    filled = sum(1 for r in evidence_rows if r["status"] == "filled")
    n_a = sum(1 for r in evidence_rows if r["status"] == "n_a")

    witness = resolve_witness(task_id, root=root)

    evidence_rows_html = "\n".join(
        '<tr><td class="ev-check"><pre>{check}</pre></td>'
        '<td class="ev-status ev-{status}"><pre>{result}</pre></td>'
        '<td class="ev-notes"><pre>{notes}</pre></td></tr>'.format(
            check=r["check"], status=r["status"].replace("_", "-"),
            result=r["result"], notes=r["notes"],
        )
        for r in evidence_rows
    ) if evidence_rows else '<tr><td colspan="3"><pre>No Evidence table found in this guide.</pre></td></tr>'

    return {
        "TASK_ID": task_id,
        "BRANCH": branch,
        "DATE": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "TIMESTAMP": datetime.now(timezone.utc).isoformat(),
        "BEFORE": demo["before"] if not field_is_blank(demo["before"]) else "(BEFORE is blank in this guide — rendering the gap, not silently succeeding)",
        "AFTER": demo["after"] if not field_is_blank(demo["after"]) else "(AFTER is blank in this guide)",
        "DELTA": demo["delta"] if not field_is_blank(demo["delta"]) else "(DELTA is blank in this guide)",
        "WITNESS": witness,
        "EVIDENCE_COUNT_SUMMARY": f"{filled} / {total} filled" + (f", {n_a} N/A" if n_a else ""),
        "EVIDENCE_ROWS": evidence_rows_html,
        "NO_DEMO_WARNING": (
            '<div class="no-demo-warning">This guide has no Demonstration block '
            "(it predates T053) — BEFORE/AFTER/DELTA above are placeholders.</div>"
        ) if no_demo else "",
    }


def main():
    if len(sys.argv) < 4:
        print("usage: render.py <TASK_ID> <guide_path> <branch> [out_dir]", file=sys.stderr)
        sys.exit(2)
    task_id, guide_path, branch = sys.argv[1], sys.argv[2], sys.argv[3]
    out_dir = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, "reports")

    with open(guide_path) as f:
        guide_text = f.read()
    with open(TEMPLATE_PATH) as f:
        template_text = f.read()

    # The review sibling lives next to the guide, wherever the caller pointed
    # us — not necessarily this checkout's tasks/.
    slots = build_slots(
        task_id, branch, guide_text,
        tasks_dir=os.path.dirname(os.path.abspath(guide_path)) or TASKS_DIR,
    )
    html = render(template_text, slots)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = os.path.join(out_dir, f"delivery-report_{branch}_{ts}.html")
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(html)

    print(html)
    print(f"SAVE → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
