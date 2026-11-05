#!/usr/bin/env python3
"""Self-review spike scorer. Usage: check_runs.py REPO RUN.json [RUN.json ...]

Per run: each citation is valid when its quote (whitespace-normalised, first 60 chars)
appears within +-3 lines of the cited line. A pattern is supported when >=3 distinct
tasks have a valid citation. Across runs: task-set overlap (Jaccard) of the best match.
"""
import json
import os
import re
import sys


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def citation_ok(repo, c):
    path = os.path.join(repo, c["file"])
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return False
    needle = norm(c["quote"])[:60].rstrip(". …")
    lo, hi = max(0, c["line"] - 4), min(len(lines), c["line"] + 3)
    return any(needle in norm(line) for line in lines[lo:hi])


def score(repo, run):
    out = []
    for p in run["patterns"]:
        valid = [c for c in p["citations"] if citation_ok(repo, c)]
        tasks = {m.group(0) for c in valid for m in [re.search(r"T\d{3}", c["file"])] if m}
        out.append({"id": p["id"], "cited": len(p["citations"]), "valid": len(valid),
                    "tasks_valid": sorted(tasks), "supported": len(tasks) >= 3,
                    "already_open": p.get("already_open", False)})
    return out


def main():
    repo, paths = sys.argv[1], sys.argv[2:]
    scored = {}
    for p in paths:
        scored[p] = score(repo, json.load(open(p)))
        print(f"== {os.path.basename(p)}")
        for s in scored[p]:
            print(f"  {s['id']:<45} valid {s['valid']}/{s['cited']}  tasks {len(s['tasks_valid'])}"
                  f"  supported={s['supported']}  open={s['already_open']}")
    if len(paths) >= 2:
        a, b = scored[paths[0]], scored[paths[1]]
        print("== agreement (best task-set Jaccard of each A pattern vs B)")
        for s in a:
            best = max(((len(set(s["tasks_valid"]) & set(t["tasks_valid"])) /
                         max(1, len(set(s["tasks_valid"]) | set(t["tasks_valid"]))), t["id"])
                        for t in b), default=(0, "-"))
            print(f"  {s['id']:<45} -> {best[1]:<45} {best[0]:.2f}")


if __name__ == "__main__":
    main()
