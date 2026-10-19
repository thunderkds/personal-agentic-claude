#!/usr/bin/env python3
"""T150 - report In Progress tasks whose worktree holds uncommitted changes.

One line per task: `<Txxx> <worktree path> <N> modified, <M> untracked`. A worktree whose
branch names two tasks yields one line per In Progress task. Read-only; any failure (no git,
no board, missing worktree) prints nothing and exits 0 so `wake` never halts.
"""
import os
import re
import subprocess
import sys

BOARD = "PROJECT_KANBAN.md"

# Task IDs: `T\d+`, plus the board's `id_pattern` when `.claude/board.json` sets one
# (T153). The helper ships with the kit's hooks; without it, today's `T\d+` only.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))))), ".claude", "hooks", "lib"))
try:
    from board.config import normalize_task_id, task_id_pattern
except Exception:  # pragma: no cover - fall back to local IDs
    def task_id_pattern(root=None, local=r"T\d+", bounded=False):
        return rf"(?<![A-Za-z0-9_])(?:{local})(?![A-Za-z0-9_])" if bounded else local

    def normalize_task_id(task_id):
        return task_id.upper()


def in_progress_ids(board_path, id_pattern=r"T\d+"):
    ids, inside = set(), False
    with open(board_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                inside = line.strip().lower().startswith("### in progress")
            elif inside:
                m = re.match(rf"\s*-\s*\[.\]\s*\*\*({id_pattern})\*\*", line)
                if m:
                    ids.add(m.group(1).upper())
    return ids


def toplevel():
    return subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()


def worktrees():
    out = subprocess.run(["git", "worktree", "list", "--porcelain"],
                         capture_output=True, text=True, check=True).stdout
    trees = []
    for block in out.strip().split("\n\n"):
        info = {}
        for line in block.splitlines():
            key, _, val = line.partition(" ")
            info[key] = val
        trees.append(info)
    return trees[1:]  # first entry is the main worktree


def counts(path):
    out = subprocess.run(["git", "--no-optional-locks", "-C", path, "status", "--porcelain"],
                         capture_output=True, text=True, check=True).stdout
    lines = [l for l in out.splitlines() if l]
    untracked = sum(1 for l in lines if l.startswith("??"))
    return len(lines) - untracked, untracked


def main():
    root = toplevel()
    ids = in_progress_ids(os.path.join(root, BOARD), task_id_pattern(root))
    # Branch names are lower-case (`feat/t142-x`, Linear's `eng-170-dark-mode`). Not inside
    # another word (`st100`), but `_` may touch the ID (`t142_fix`), as it always could.
    ids_in_branch = task_id_pattern(root, r"T\d{3,}")
    branch_id = re.compile(rf"(?<![A-Za-z0-9])(?:{ids_in_branch})(?![0-9])", re.I)
    for tree in worktrees():
        path, branch = tree.get("worktree", ""), tree.get("branch", "")
        if "prunable" in tree or not branch or not os.path.isdir(path):
            continue
        tasks = sorted({normalize_task_id(t) for t in branch_id.findall(branch)} & ids)
        if not tasks:
            continue
        modified, untracked = counts(path)
        if modified or untracked:
            for task in tasks:
                print(f"{task} {path} {modified} modified, {untracked} untracked")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
