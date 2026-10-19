#!/usr/bin/env python3
"""Report whether a task's event trace still matches its chain and its anchor (T148).

    python3 scripts/verify_trace.py <task>

Reads memory/event-trace/<task>.jsonl and the out-of-repo anchor file
(~/.claude/harness-anchors/<repo-slug>/<task>.anchors, or under
$CLAUDE_TRACE_ANCHOR_DIR). Prints one verdict line, preceded by an UNANCHORED
line when the trace starts with lines written before the chain existed:

    INTACT                   every chained line links and matches its anchor   exit 0
    UNANCHORED               no chained line at all (pre-T148 trace)            exit 0
    BROKEN at line N         line N does not link to the line before it         exit 1
    ANCHOR MISMATCH at line N  the chain links, but line N is not what was
                             anchored when it was written (a rewrite that
                             recomputed the chain, or a deleted/forged line)  exit 1

    UNVERIFIED at line N     the chain links and every anchor matches, but line
                             N was written with "anchor": "failed" (anchor dir
                             unwritable) — nothing outside the repo vouches
                             for it, and a forged append could claim the same  exit 1

BROKEN and ANCHOR MISMATCH take precedence over UNVERIFIED; within a verdict
the earliest line is reported.

Exit 2: bad task name or no trace file. This reports; it blocks nothing.

Limits: the anchor is protected by permission rules, which raise the bar but
are not a proof (see TASK_REVIEW_T148).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks", "lib"))
from trace_chain import GENESIS, anchor_path, chain_hash, safe_name  # noqa: E402

try:
    import fcntl
except Exception:
    fcntl = None


def read_locked(trace, anchor_file, task):
    """Trace bytes and anchors, both read under a shared lock on the trace, so an
    append in flight (anchor written, line not yet) can't look like a mismatch."""
    with open(trace, "rb") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        except Exception:
            pass
        return f.read(), read_anchors(anchor_file, task)


def read_anchors(path, task):
    """{line_no: {hash, ...}} from the anchor file; a missing file is empty."""
    anchors = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                parts = raw.split()
                if len(parts) != 3 or parts[0] != task or not parts[1].isdigit():
                    continue
                anchors.setdefault(int(parts[1]), set()).add(parts[2])
    except (FileNotFoundError, NotADirectoryError):  # never written: no anchors
        pass
    return anchors


def verify(trace_bytes, anchors):
    """Return (lines_out, exit_code)."""
    lines = trace_bytes.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    first_chained = None
    prev = GENESIS
    hashes = {}
    anchor_failed = []
    for n, raw in enumerate(lines, 1):
        try:
            rec = json.loads(raw)
        except Exception:
            rec = None
        chained = isinstance(rec, dict) and isinstance(rec.get("hash"), str)
        if first_chained is None:
            if not chained:
                continue
            first_chained = n
            if n > 1:
                out.append("UNANCHORED: lines 1-%d predate the chain" % (n - 1))
        if not chained:
            return out + ["BROKEN at line %d: not a chained record" % n], 1
        if rec.get("prev") != prev:
            return out + ["BROKEN at line %d: prev does not match the chain head before it" % n], 1
        if chain_hash(rec) != rec["hash"]:
            return out + ["BROKEN at line %d: content does not match its hash" % n], 1
        prev = rec["hash"]
        hashes[n] = prev
        if rec.get("anchor") == "failed":
            anchor_failed.append(n)
    if first_chained is None:
        if not lines and not anchors:
            return ["INTACT: empty trace"], 0
        if not anchors:
            return ["UNANCHORED: lines 1-%d predate the chain" % len(lines)], 0
    mismatched = [n for n, anchored in anchors.items() if hashes.get(n) not in anchored]
    mismatched += [n for n in hashes if n not in anchors and n not in anchor_failed]
    if mismatched:
        n = min(mismatched)
        why = "no anchor recorded for it" if n not in anchors else "anchored hash differs"
        return out + ["ANCHOR MISMATCH at line %d: %s" % (n, why)], 1
    if anchor_failed:
        # A line marked anchor: failed has nothing outside the repo to check it
        # against, so it is exactly what a forged append would claim to be.
        return out + ["UNVERIFIED at line %d: written with anchor: failed — not anchor-checked"
                      % min(anchor_failed)], 1
    return out + ["INTACT: lines %d-%d chained and anchored" % (first_chained, len(lines))], 0


def main(argv):
    if len(argv) != 2 or safe_name(argv[1], "") != argv[1]:
        print("usage: verify_trace.py <task>   (letters, digits, _ and - only)", file=sys.stderr)
        return 2
    task = argv[1]
    trace = os.path.join(ROOT, "memory", "event-trace", task + ".jsonl")
    if not os.path.isfile(trace):
        print("NO TRACE: %s" % trace, file=sys.stderr)
        return 2
    try:
        anchor_file = anchor_path(ROOT, task)
    except OSError as e:
        print("cannot locate anchor file: %s" % e, file=sys.stderr)
        return 2
    lines, code = verify(*read_locked(trace, anchor_file, task))
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
