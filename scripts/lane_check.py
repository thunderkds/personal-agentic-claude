#!/usr/bin/env python3
"""Warn-only Stage 4 check: does the branch diff fit the task's declared Complexity?

Usage: lane_check.py <TASK_GUIDE_Txxx.md> <base>...<head>  (three dots: diff against the
merge point, so work merged into base after the fork is not counted)
Prints one line; exit code is always 0 (never blocks).
"""
import fnmatch
import importlib.util
import os
import re
import subprocess
import sys

# One table. (max files, max changed lines). C3 has no ceiling.
# Calibrated on T128-T138 (tasks/TASK_REVIEW_T144.md): 1 of 9 exceeds.
BUDGETS = {
    "C0": (2, 30),
    "C1": (6, 250),
    "C2": (14, 500),
}

EXCLUDED = ("PROJECT_KANBAN.md", "memory/", "tasks/TASK_REVIEW_")
EXCLUDED_NAMES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
                  "Cargo.lock", "Gemfile.lock", "uv.lock", "Pipfile.lock")
GATE2 = re.compile(r"refactor|restructure|migrate to pattern|clean architecture|"
                   r"QA suite|test coverage", re.I)


def _table_paths(text):
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "skills", "craft-spawn-prompt", "scripts", "memory_slice.py")
    spec = importlib.util.spec_from_file_location("memory_slice", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.table_paths(text)


def is_excluded(path):
    if "__pycache__" in path.split("/"):
        return True
    if os.path.basename(path) in EXCLUDED_NAMES:
        return True
    return any(path == e or path.startswith(e) for e in EXCLUDED)


def is_predicted(path, predicted):
    for p in predicted:
        glob = re.search(r"[*?\[]", p)
        if glob:
            if path.startswith(p[:glob.start()]):
                return True
        elif p.endswith("/"):
            if path.startswith(p):
                return True
        elif path == p:
            return True
    return False


def diff_stats(rng):
    out = subprocess.run(["git", "diff", "--numstat", "-M", rng], capture_output=True,
                         text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "git diff failed")
    files = {}
    for line in out.stdout.splitlines():
        added, removed, name = line.split("\t", 2)
        if " => " in name:  # rename: count once, under the new path
            name = re.sub(r"\{[^}]*? => ([^}]*)\}", r"\1", name)
            if " => " in name:
                name = name.split(" => ")[-1]
            name = name.replace("//", "/")
        n = 0 if added == "-" else int(added) + int(removed)
        files[name] = n
    return files


def check(guide, rng):
    try:
        text = open(guide, encoding="utf-8").read()
    except OSError as e:
        return f"UNKNOWN ({e.strerror or e})"
    m = re.search(r"\*\*Complexity Level\*\*:\s*(C[0-3])\b", text)
    if not m:
        return "UNKNOWN (no Complexity Level in guide)"
    level = m.group(1)
    try:
        files = diff_stats(rng)
    except (RuntimeError, OSError) as e:
        return f"UNKNOWN ({e})"
    files = {f: n for f, n in files.items() if not is_excluded(f)}
    nfiles, nlines = len(files), sum(files.values())
    reasons = []
    if level in BUDGETS:
        max_f, max_l = BUDGETS[level]
        if nfiles > max_f:
            reasons.append(f"files {nfiles} > {max_f}")
        if nlines > max_l:
            reasons.append(f"lines {nlines} > {max_l}")
    head = text.split("\n", 1)[0]
    intent = re.search(r"\*\*Restated intent\*\*:(.*?)(?:\n\*\*|\n---)", text, re.S)
    scope = head + "\n" + (intent.group(1) if intent else "")
    if level in ("C0", "C1") and GATE2.search(scope):
        reasons.append("Gate 2 floor")
    verdict = f"EXCEEDS ({'; '.join(reasons)})" if reasons else "FITS"
    predicted = _table_paths(re.split(r"^## Files Must NOT Touch", text, flags=re.M)[0])
    unpredicted = sorted(f for f in files if not is_predicted(f, predicted))
    line = f"lane: {level}, {nfiles} files, {nlines} lines, {verdict}"
    if unpredicted:
        line += f"; unpredicted: {', '.join(unpredicted)}"
    return line


def main(argv):
    if len(argv) != 3:
        print("UNKNOWN (usage: lane_check.py <guide> <base>...<head>)")
        return 0
    try:
        print(check(argv[1], argv[2]))
    except Exception as e:  # warn-only: never crash into a non-zero exit
        print(f"UNKNOWN ({e})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
