#!/usr/bin/env python3
"""Memory-usage evidence report (T063) — read-only analysis over the event trace.

Regenerates every number in `docs/memory-usage-finding-2026-08-07.md` from the
repo. Takes **no arguments** and writes **nothing**: stdout only. It never opens
a file for writing, never creates a directory, and touches nothing under
`memory/` or `reports/` (AC9 — T059 was a defect of exactly that shape: an
analysis-adjacent script that wrote to a tracked data file and destroyed it in a
worktree).

Structure follows `scripts/token_audit.py` (the read side of it). Deliberately
NOT followed: that script's report-writing half, and its test.

**Root resolution.** `memory/event-trace/` is gitignored, so a fresh worktree has
none. The trace directory is resolved off `$CLAUDE_PROJECT_DIR` when set,
otherwise off `__file__` — the same precedence `.claude/hooks/lib/task_context.py:
_resolve_root` already uses in this repo, so there is one convention rather than
two. That is a *root* selector, not a CLI argument: the script's behaviour is
identical either way, and with neither available it reports zeros rather than
crashing (AC10).

Every question this answers is an attribution question, so the vocabulary matters:

* **bucket** — which `<task>.jsonl` a record landed in. Decided by
  `task_context.resolve_task_id`, i.e. by the active-task pointer / a guide path,
  **not** by who made the call.
* **locus** — which working copy the record's file paths point at, recovered from
  the record `summary`. A `/pets/wt-t0NN/` or `/worktrees/...` path is a Stage-3
  sub-agent's own worktree; the main checkout path is the Supervisor's. This is
  the only actor signal the trace carries, and it is a heuristic — it works
  because every recent spawn prompt says "work only inside this worktree", and it
  is silent for `Bash` commands that name no path.
"""
import collections
import glob
import json
import os
import re
import sys

_FILE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = "MEMORY.md"
UNTAGGED = "_untagged"

# A Stage-3 worktree, in either convention this repo has used:
#   /pets/wt-t063/...                    (current)
#   /pets/worktrees/pac-T031/...         (older)
#   /personal-agentic-claude/.claude/worktrees/t056/...
WORKTREE_PATTERN = re.compile(r"/(?:wt-|worktrees/)([A-Za-z0-9_.-]+)")

# Element 4 of craft-spawn-prompt mandates the *full contents* of MEMORY.md
# verbatim. These two patterns separate the mandated channel from the one
# actually observed. `summary` is capped at MAX_SUMMARY_LEN (300) by the hook, so
# both are evaluated against the prompt's opening only — see the report's limits
# section; a hit is evidence, a miss is not.
PROMPT_MEMORY_PATH_PATTERN = re.compile(r"memory/MEMORY\.md")
# The first heading of memory/MEMORY.md. Its presence in a prompt is the only
# positive marker of a verbatim paste that survives truncation.
PROMPT_MEMORY_VERBATIM_MARKER = "# MEMORY.md — Hot-Tier Memory Index"

# tool_stats (T061) has no `write` category; harness `editFileCount` covers Edit
# and Write together, so the trace side must be summed the same way to compare.
EDIT_LIKE_TOOLS = ("Edit", "Write", "NotebookEdit")


def resolve_root():
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    return env_root if env_root else _FILE_ROOT


def trace_dir():
    return os.path.join(resolve_root(), "memory", "event-trace")


def load_records(directory):
    """All trace records, tagged with their bucket. Malformed lines are skipped
    silently and counted — a half-written JSONL line (the hook appends on every
    tool call, including during a crash) must never abort the analysis."""
    records = []
    skipped = 0
    for path in sorted(glob.glob(os.path.join(directory, "*.jsonl"))):
        bucket = os.path.basename(path)[: -len(".jsonl")]
        try:
            with open(path) as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                skipped += 1
                continue
            if not isinstance(record, dict):
                skipped += 1
                continue
            record["_bucket"] = bucket
            records.append(record)
    return records, skipped


def locus_of(record):
    """Which working copy this record's paths point at: `worktree:<name>`,
    `main-checkout`, or `unknown`. See the module docstring on why this is the
    only actor signal available, and why it is a heuristic."""
    summary = record.get("summary") or ""
    match = WORKTREE_PATTERN.search(summary)
    if match:
        return "worktree:" + match.group(1).lower()
    if "personal-agentic-claude" in summary:
        return "main-checkout"
    return "unknown"


def is_memory_read(record):
    return record.get("tool_name") == "Read" and MEMORY_FILE in (record.get("summary") or "")


def naive_task_coverage(records):
    """The untrustworthy BEFORE figure, reproduced exactly: how many `<task>.jsonl`
    buckets contain at least one Read of MEMORY.md. Reproduced so the report can
    show *why* it is untrustworthy, not because it means anything."""
    buckets = {r["_bucket"] for r in records if r["_bucket"] != UNTAGGED}
    hit = {r["_bucket"] for r in records if r["_bucket"] != UNTAGGED and is_memory_read(r)}
    return len(hit), len(buckets)


def reconcile_spawns(records):
    """For every `Agent` record carrying T061 `tool_stats`, compare the sub-agent's
    self-reported tool mix against the trace records filed under the same bucket.

    This is the AC1 instrument: if the two reconcile, the bucket holds the
    sub-agent's own calls. Records outside the bucket (the sub-agent's calls made
    *before* it armed the active-task pointer) land in `_untagged`, so the
    in-window untagged count is reported alongside rather than folded in.
    """
    untagged = [r for r in records if r["_bucket"] == UNTAGGED]
    rows = []
    for record in records:
        if record.get("tool_name") != "Agent":
            continue
        stats = (record.get("spawn") or {}).get("tool_stats")
        if not stats:
            continue
        bucket = record["_bucket"]
        # A spawn filed under _untagged has no bucket to reconcile against; the
        # whole _untagged file is every task's leftovers, not this spawn's.
        if bucket == UNTAGGED:
            continue
        peers = [r for r in records if r["_bucket"] == bucket and r is not record]
        if not peers:
            continue
        hi = record.get("timestamp", "")
        # Window start = the sub-agent session's first observable touch of its own
        # worktree, NOT the bucket's first record. The bucket also holds the
        # Supervisor's own Stage-2 writes to the guide, made hours earlier; taking
        # those as the start would sweep the Supervisor's unrelated `_untagged`
        # Bash calls into the comparison and destroy it.
        worktree = locus_of(record)
        session = [r for r in records if locus_of(r) == worktree] if worktree.startswith("worktree:") else []
        if session:
            lo = min(r.get("timestamp", "") for r in session)
        else:
            lo = min(r.get("timestamp", "") for r in peers)
        # The window is applied to BOTH sides. Applying it only to `_untagged`
        # leaves the Supervisor's own pre-spawn guide Write inside the bucket
        # count, where it silently compensates for a missing agent call and
        # manufactures a false EXACT — which is what the first cut of this
        # function did (T067: 15 == 15 on edit_like, but only because one of the
        # 15 was the Supervisor's and one agent edit was missing).
        in_bucket = [r for r in peers if lo <= (r.get("timestamp") or "") <= hi]
        counts = collections.Counter(r.get("tool_name") for r in in_bucket)
        excluded = len(peers) - len(in_bucket)
        in_window = [r for r in untagged if lo <= (r.get("timestamp") or "") <= hi]
        window_counts = collections.Counter(r.get("tool_name") for r in in_window)
        rows.append({
            "bucket": bucket,
            "window": (lo, hi),
            "excluded_pre_session": excluded,
            "reported": {
                "read": stats.get("read_count"),
                "bash": stats.get("bash_count"),
                "edit_like": stats.get("edit_file_count"),
                "total": (record.get("spawn") or {}).get("tool_use_count"),
            },
            "bucket_counts": {
                "read": counts.get("Read", 0),
                "bash": counts.get("Bash", 0),
                "edit_like": sum(counts.get(t, 0) for t in EDIT_LIKE_TOOLS),
                "total": sum(counts.values()),
            },
            "untagged_in_window": {
                "read": window_counts.get("Read", 0),
                "bash": window_counts.get("Bash", 0),
                "edit_like": sum(window_counts.get(t, 0) for t in EDIT_LIKE_TOOLS),
                "total": sum(window_counts.values()),
            },
        })
    return rows


def spawn_prompt_channels(records):
    """How MEMORY.md appears in the recovered spawn-prompt openings: as a path to
    read, verbatim, or not at all (AC3/AC4)."""
    agents = [r for r in records if r.get("tool_name") == "Agent"]
    path_channel, verbatim_channel, truncated = [], [], 0
    for record in agents:
        summary = record.get("summary") or ""
        if len(summary) >= 300:
            truncated += 1
        if PROMPT_MEMORY_VERBATIM_MARKER in summary:
            verbatim_channel.append(record["_bucket"])
        elif PROMPT_MEMORY_PATH_PATTERN.search(summary):
            path_channel.append(record["_bucket"])
    return {
        "total": len(agents),
        "with_spawn_telemetry": sum(1 for r in agents if r.get("spawn")),
        "truncated": truncated,
        "path_channel": path_channel,
        "verbatim_channel": verbatim_channel,
    }


def section(title):
    print()
    print(title)
    print("-" * len(title))


def main():
    directory = trace_dir()
    print("memory_usage_report (T063) — read-only; writes nothing")
    print("trace dir: %s" % directory)

    if not os.path.isdir(directory):
        print("trace dir: ABSENT — 0 records. (memory/event-trace/ is gitignored;")
        print("a fresh worktree has none. Set CLAUDE_PROJECT_DIR to a checkout that has one.)")
        return 0

    records, skipped = load_records(directory)
    print("records: %d   malformed lines skipped: %d" % (len(records), skipped))
    if not records:
        print("trace dir: EMPTY — 0 records.")
        return 0

    section("1. The naive figure (reproduced, NOT trusted)")
    hit, total = naive_task_coverage(records)
    print("task buckets with >=1 Read of MEMORY.md: %d of %d" % (hit, total))
    untagged = [r for r in records if r["_bucket"] == UNTAGGED]
    print("_untagged records: %d (counted separately, never folded into a task)" % len(untagged))
    print("_untagged Reads of MEMORY.md: %d" % sum(1 for r in untagged if is_memory_read(r)))

    section("2. Where MEMORY.md reads actually happen (locus, not bucket)")
    loci = collections.Counter(locus_of(r) for r in records if is_memory_read(r))
    for key in sorted(loci):
        print("%-24s %d" % (key, loci[key]))

    section("3. Sub-agent worktrees: activity vs. MEMORY.md read")
    active = collections.Counter()
    read_it = collections.Counter()
    for record in records:
        locus = locus_of(record)
        if not locus.startswith("worktree:"):
            continue
        active[locus] += 1
        if is_memory_read(record):
            read_it[locus] += 1
    for key in sorted(active):
        print("%-24s records=%-4d MEMORY.md reads=%d" % (key, active[key], read_it.get(key, 0)))
    print("worktrees with >=1 MEMORY.md read: %d of %d" % (len(read_it), len(active)))

    section("4. AC1 — spawn tool_stats vs. same-bucket trace records")
    rows = reconcile_spawns(records)
    if not rows:
        print("no Agent record carries tool_stats (all records predate T061) — NOT CAPTURED")
    for row in rows:
        print("bucket %s   session window %s .. %s" % (row["bucket"], row["window"][0], row["window"][1]))
        print("  bucket records excluded as pre-session (Supervisor's own): %d" % row["excluded_pre_session"])
        for field in ("read", "bash", "edit_like", "total"):
            reported = row["reported"][field]
            bucket = row["bucket_counts"][field]
            window = row["untagged_in_window"][field]
            combined = bucket + window
            if reported == combined:
                mark = "EXACT"
            elif isinstance(reported, int):
                mark = "residual %+d" % (combined - reported)
            else:
                mark = "NOT CAPTURED"
            print("  %-10s agent-reported=%-4s in-window bucket=%-4d +untagged=%-4d => %-4d %s"
                  % (field, reported, bucket, window, combined, mark))

    section("5. AC3/AC4 — how MEMORY.md reaches a spawn prompt")
    channels = spawn_prompt_channels(records)
    print("Agent records: %d (with T061 spawn telemetry: %d; summary truncated at 300 chars: %d)"
          % (channels["total"], channels["with_spawn_telemetry"], channels["truncated"]))
    print("openings naming memory/MEMORY.md as a PATH to read: %d %s"
          % (len(channels["path_channel"]), sorted(set(channels["path_channel"]))))
    print("openings containing MEMORY.md VERBATIM (its own H1): %d %s"
          % (len(channels["verbatim_channel"]), sorted(set(channels["verbatim_channel"]))))
    print("NOTE: a miss is not evidence of absence — only the first 300 chars are stored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
