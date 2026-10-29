#!/usr/bin/env python3
"""T143 - CI re-runs the Verification Command of every task a PR moves to Done.

Usage: ci_verify_done_tasks.py --base REF [--head REF] [--root DIR]

1. Select: task IDs whose `PROJECT_KANBAN.md` row is `- [x] **Txxx**` at HEAD and
   was not at the merge-base of BASE and HEAD. Rows are matched by their own
   leading ID, never by a bold cross-reference in prose (T093).
2. Extract: the fenced `bash`/`sh` blocks under `### Verification Command`,
   resolved guide first, review file second (`guide_sections`).
3. Run: each block as written with `bash -c`, from the repo root, 600 s limit.

A block whose first non-blank line is `# ci: skip - <reason>` is skipped by name
with its reason printed. A skip with no reason fails. A Done task with no
Verification Command section, an empty block or the template placeholder fails
(fail closed). Exit 0 only when every selected task passed or was skipped.

The commands come from task guides, so they run only in the CI job that the
workflow limits to `pull_request`, with no secrets. Stdlib only.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".claude", "hooks", "lib"))
from guide_sections import read_guide_section  # noqa: E402

KANBAN = "PROJECT_KANBAN.md"
TIMEOUT_SECONDS = 600

DONE_ROW = re.compile(r"^- \[x\] \*\*(T\d+)\*\*", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^```(?:bash|sh)[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
SKIP_LINE = re.compile(r"^#\s*ci:\s*skip\b\s*(?:—|–|--|-)?\s*(.*)$")
PLACEHOLDER_LINE = re.compile(r"^\[.*\]$")


def git(root, *args):
    result = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def done_ids_at(root, ref):
    """Task IDs with a `- [x] **Txxx**` row in the board at `ref`. No board file = none."""
    try:
        text = git(root, "show", f"{ref}:{KANBAN}")
    except RuntimeError:
        return set()
    return set(DONE_ROW.findall(text))


def tasks_moved_to_done(root, base, head):
    for ref in (base, head):  # a bad ref must stop the job, not read as an empty board
        git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    try:
        base = git(root, "merge-base", base, head).strip() or base
    except RuntimeError:
        pass  # no common ancestor in a shallow clone: compare against BASE itself
    return sorted(done_ids_at(root, head) - done_ids_at(root, base),
                  key=lambda t: int(t[1:]))


def extract_blocks(section):
    return [b for b in FENCED_BLOCK.findall(section or "")]


def classify(block):
    """('skip', reason) | ('run', None) | ('empty', None) | ('bad-skip', None)."""
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if lines:
        match = SKIP_LINE.match(lines[0])
        if match:
            reason = match.group(1).strip()
            return ("skip", reason) if reason and reason != "<reason>" else ("bad-skip", None)
    code = [ln for ln in lines if not ln.startswith("#") and not PLACEHOLDER_LINE.match(ln)]
    return ("run", None) if code else ("empty", None)


def verify_task(root, task):
    """Print the task's result line; return True when it passed or was skipped."""
    section = read_guide_section(task, "Verification Command", os.path.join(root, "tasks"))
    blocks = extract_blocks(section)
    if not blocks:
        print(f"{task}: FAIL (no Verification Command block in the guide or review file)")
        return False
    ok = True
    for block in blocks:
        kind, reason = classify(block)
        if kind == "skip":
            print(f"{task}: SKIP ({reason})")
        elif kind == "bad-skip":
            print(f"{task}: FAIL (`# ci: skip` needs a reason after the dash)")
            ok = False
        elif kind == "empty":
            print(f"{task}: FAIL (Verification Command block is empty or only the template placeholder)")
            ok = False
        else:
            print(f"{task}: running Verification Command:\n{block.rstrip()}", flush=True)
            try:
                code = subprocess.run(["bash", "-c", block], cwd=root,
                                      timeout=TIMEOUT_SECONDS).returncode
            except subprocess.TimeoutExpired:
                print(f"{task}: FAIL (timed out after {TIMEOUT_SECONDS} s)")
                ok = False
                continue
            if code == 0:
                print(f"{task}: PASS")
            else:
                print(f"{task}: FAIL (exit {code})")
                ok = False
    return ok


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--root", default=os.path.join(HERE, ".."))
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)
    try:
        tasks = tasks_moved_to_done(root, args.base, args.head)
    except RuntimeError as err:
        print(f"ci_verify_done_tasks: {err}", file=sys.stderr)
        return 2
    if not tasks:
        print("no tasks moved to Done")
        return 0
    print(f"tasks moved to Done: {', '.join(tasks)}", flush=True)
    results = [verify_task(root, t) for t in tasks]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
