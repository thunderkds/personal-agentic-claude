#!/usr/bin/env python3
"""Token Audit Log generator (T040, DDR-0001 Amendment 1).

Derives DDR-0001-format Token Audit Log entries from the event trace already
written by `.claude/hooks/post_tool_trace.py` (memory/event-trace/*.jsonl) —
replacing the manual per-session logging convention that collapsed after one
session (see docs/ddr/0001-measure-first-token-refactor.md Amendment 1).

This is a GENERATOR, not a hook: it is invoked on demand (`scripts/token-audit.sh`),
never wired into a PreToolUse/PostToolUse matcher. Re-running it regenerates the
whole entries section from current trace data, which makes it idempotent by
construction — no dedup logic is needed because nothing is ever appended.

Hard constraint (DDR-0001 Amendment 1): token counts are never estimated,
inferred, or synthesized. Only real trace-derived event/task/model-tier data is
emitted; `?` marks anything the trace does not carry.
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TRACE_DIR = os.path.join(ROOT, "memory", "event-trace")
DEFAULT_REPORT_PATH = os.path.join(ROOT, "reports", "token-audit_2026-07-21.md")
WINDOW_DATE = "2026-07-21"

# Skill -> Token Audit Log `event` tag, per CLAUDE.md's `## Skills vs Agents`
# stage index. `wake` is handled separately as the literal `cold-start` event.
STAGE_MAP = {
    "brainstorming": "stage-0.5",
    "ideate": "stage-0.5",
    "git-guardrails-claude-code": "stage-1",
    "map-codebase": "stage-1",
    "fewer-permission-prompts": "stage-1",
    "update-config": "stage-1",
    "craft-agent": "stage-1.5",
    "grill-with-docs": "stage-2",
    "to-issues": "stage-2",
    "tdd": "stage-3",
    "bugfix": "stage-3",
    "diagnose": "stage-3",
    "craft-spawn-prompt": "stage-3",
    "migration-safety": "stage-3",
    "run": "stage-3",
    "blast-radius": "stage-4",
    "code-review": "stage-4",
    "html-report": "stage-4",
    "security-review": "stage-4",
    "ship": "stage-5",
    "verify": "stage-5",
}

SKILL_NAME_PATTERN = re.compile(r'"skill"\s*:\s*"([a-zA-Z0-9_.-]+)"')
MODEL_TIER_PATTERN = re.compile(r'"model"\s*:\s*"(haiku|sonnet|opus)"')
VALID_TIERS = {"haiku", "sonnet", "opus"}


def _iter_trace_files(trace_dir):
    if not os.path.isdir(trace_dir):
        return []
    return sorted(glob.glob(os.path.join(trace_dir, "*.jsonl")))


def _task_tag_for_path(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return "overhead" if base == "_untagged" else base


def iter_trace_records(trace_dir):
    """Yield (task_tag, record_dict) for every well-formed JSONL line under
    trace_dir. Malformed lines are skipped with a stderr warning, never
    treated as a valid entry (never silently dropped without a signal)."""
    for path in _iter_trace_files(trace_dir):
        task_tag = _task_tag_for_path(path)
        with open(path, encoding="utf-8") as f:
            for lineno, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    print(
                        f"token-audit: WARNING skipping malformed JSONL line "
                        f"{lineno} in {path}",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(record, dict):
                    print(
                        f"token-audit: WARNING skipping non-object JSONL line "
                        f"{lineno} in {path}",
                        file=sys.stderr,
                    )
                    continue
                yield task_tag, record


def _extract_skill_name(summary):
    if not isinstance(summary, str):
        return None
    match = SKILL_NAME_PATTERN.search(summary)
    return match.group(1) if match else None


def _extract_model_tier(summary):
    if not isinstance(summary, str):
        return "?"
    match = MODEL_TIER_PATTERN.search(summary)
    tier = match.group(1) if match else None
    return tier if tier in VALID_TIERS else "?"


def classify_event(record):
    """Return the DDR-0001 `event` tag for this trace record, or None if the
    record is not one of the three event types the log tracks (cold-start,
    stage-N, spawn) — e.g. a plain Read/Write/Bash call carries no Token
    Audit Log meaning on its own and is intentionally not emitted."""
    tool_name = record.get("tool_name")
    if tool_name == "Agent":
        return "spawn"
    if tool_name == "Skill":
        skill = _extract_skill_name(record.get("summary"))
        if skill == "wake":
            return "cold-start"
        if skill in STAGE_MAP:
            return STAGE_MAP[skill]
    return None


def _date_from_timestamp(timestamp):
    """DDR-0001 wants YYYY-MM-DD; trace timestamps are UTC ISO-8601. Convert
    explicitly and consistently in UTC (never local time)."""
    try:
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return "?"


def build_entries(trace_dir, window_start=None):
    """Return a list of DDR-0001-format entry tuples, sorted by timestamp.

    `cache` reproduces the manual convention's own documented heuristic —
    "not a real cache-hit measurement" (DDR-0001): the first entry emitted
    for a given task-tag is scored `miss`, every subsequent entry for that
    same tag is scored `hit`.

    `window_start` (T050): when given (a `YYYY-MM-DD` string), only records
    whose derived date is `>= window_start` are included — this is what lets
    a fresh window file start clean instead of re-deriving the entire trace
    history. `None` (the default) preserves the original, unfiltered
    behavior for backward compatibility (AC1). A record whose date cannot be
    parsed (`_date_from_timestamp` returns `"?"`) is excluded, with a stderr
    warning, whenever a window filter is active — it can never be compared
    against `window_start`, so silently including it would be a correctness
    bug, and silently dropping it without a signal would hide data loss.
    """
    records = []
    for task_tag, record in iter_trace_records(trace_dir):
        event = classify_event(record)
        if event is None:
            continue
        records.append((record.get("timestamp", ""), task_tag, event, record))

    records.sort(key=lambda r: r[0])

    seen_tags = set()
    entries = []
    for timestamp, task_tag, event, record in records:
        cache = "hit" if task_tag in seen_tags else "miss"
        seen_tags.add(task_tag)
        model_tier = _extract_model_tier(record.get("summary"))
        date = _date_from_timestamp(timestamp)
        if window_start is not None:
            if date == "?":
                print(
                    "token-audit: WARNING excluding a record with an "
                    "unparseable date from the window-filtered output "
                    f"(task_tag={task_tag!r})",
                    file=sys.stderr,
                )
                continue
            if date < window_start:
                continue
        notes = f"derived from {record.get('tool_name', '?')} trace record"
        entries.append((date, event, task_tag, cache, model_tier, notes))
    return entries


def render_report(entries, window_date=WINDOW_DATE):
    header = f"""# Token Audit Log — Window opened {window_date}

> **What this is**: baseline measurement instrument per DDR-0001 (see Amendment 1,
> {window_date}). Entries below are **derived automatically** from
> `memory/event-trace/*.jsonl` by `scripts/token-audit.sh` (T040) — not typed by
> hand. Re-running the script regenerates the entries table from current trace
> data each time; running it twice with unchanged trace data produces byte-identical
> output (idempotent by construction — nothing is ever appended). This is a
> generated, window-scoped artifact — it lives in `reports/`, not `memory/`.

## Window-close condition

This window closes at **7 logged sessions or 14 calendar days, whichever comes
first** (from {window_date}). A session = one conversation that ran `wake`. When
the window closes, start a new file
(`reports/token-audit_<next-window-date>.md`) rather than appending further.

## Entry format

```
<date> | <event> | <task-tag> | <cache> | <model-tier> | <notes>
```

| Field | Vocabulary |
|---|---|
| `date` | `YYYY-MM-DD` (UTC) |
| `event` | `cold-start` \\| `stage-N` (N = 0.5–5) \\| `spawn` |
| `task-tag` | `Txxx` (structurally attributed, see `lib/task_context.py`) or `overhead` (unattributed) |
| `cache` | `hit` \\| `miss` — heuristic only: first occurrence of a task-tag in this file is scored `miss`, repeats are `hit`. Not a real cache-hit measurement — do not over-trust it. |
| `model-tier` | `haiku` \\| `sonnet` \\| `opus` \\| `?` — `?` when the trace record does not carry a model field. Never guessed. |
| `notes` | free text — which trace record this line was derived from |

**Known ceiling (accepted, DDR-0001 Amendment 1)**: hooks cannot observe real
token counts and no hook can capture `/cost`. Only the event stream (cold-start /
stage transitions / spawns) is automated here. Append the session's `/cost`
output manually as a separate line at session end — that is the ground-truth
number the tagged entries are checked against. No token count is ever
estimated or synthesized by this generator.

## Entries (derived — do not hand-edit; re-run `scripts/token-audit.sh` instead)

"""
    if not entries:
        return header + "_(no trace data found under `memory/event-trace/` yet)_\n"

    lines = [
        f"{date} | {event} | {tag} | {cache} | {tier} | {notes}"
        for date, event, tag, cache, tier, notes in entries
    ]
    return header + "```\n" + "\n".join(lines) + "\n```\n"


def generate_report(
    trace_dir=DEFAULT_TRACE_DIR,
    report_path=DEFAULT_REPORT_PATH,
    window_start=None,
):
    """Regenerate report_path from trace_dir. Returns the entry count.
    Never raises on missing/empty trace_dir — that is a valid "no data yet"
    state, not an error.

    `window_start` (T050): forwarded to `build_entries` to scope the entries
    to a fresh window, and used as the report header's "Window opened" date
    when given. `None` preserves the original unfiltered behavior and keeps
    the module-level `WINDOW_DATE` as the header date (AC1)."""
    entries = build_entries(trace_dir, window_start=window_start)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    header_date = window_start if window_start is not None else WINDOW_DATE
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(render_report(entries, window_date=header_date))
    return len(entries)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Regenerate the Token Audit Log from memory/event-trace/*.jsonl."
    )
    parser.add_argument(
        "--window-start",
        default=os.environ.get("TOKEN_AUDIT_WINDOW_START"),
        help=(
            "YYYY-MM-DD lower bound (inclusive) — only records derived to this "
            "date or later are emitted. Omit to preserve the original "
            "unfiltered, single-window behavior (T050)."
        ),
    )
    parser.add_argument(
        "--report-path",
        default=os.environ.get("TOKEN_AUDIT_REPORT_PATH", DEFAULT_REPORT_PATH),
        help="Output report path. Defaults to the closed 2026-07-21 window's file.",
    )
    parser.add_argument(
        "--trace-dir",
        default=os.environ.get("TOKEN_AUDIT_TRACE_DIR", DEFAULT_TRACE_DIR),
        help="Directory of memory/event-trace/*.jsonl files to derive from.",
    )
    return parser.parse_args(argv)


def main():
    args = _parse_args(sys.argv[1:])
    trace_dir = args.trace_dir
    report_path = args.report_path
    window_start = args.window_start

    if not os.path.isdir(trace_dir):
        print(
            f"token-audit: no trace data found at {trace_dir} — writing an "
            f"empty-window report and exiting 0"
        )

    count = generate_report(trace_dir, report_path, window_start=window_start)
    print(f"token-audit: wrote {count} entries to {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
