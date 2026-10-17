#!/usr/bin/env python3
"""T150 - report In Progress tasks whose worktree holds uncommitted changes.

One line per task: `<Txxx> <worktree path> <N> modified, <M> untracked`. A worktree whose
branch names two tasks yields one line per In Progress task. Read-only; any failure (no git,
no board, missing worktree) prints nothing and exits 0 so `wake` never halts.
"""
import os
import re
import subprocess

BOARD = "PROJECT_KANBAN.md"


def in_progress_ids(board_path):
    ids, inside = set(), False
    with open(board_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                inside = line.strip().lower().startswith("### in progress")
            elif inside:
                m = re.match(r"\s*-\s*\[.\]\s*\*\*(T\d+)\*\*", line)
                if m:
                    ids.add(m.group(1).upper())
    return ids


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
    ids = in_progress_ids(BOARD)
    for tree in worktrees():
        path, branch = tree.get("worktree", ""), tree.get("branch", "")
        if "prunable" in tree or not branch or not os.path.isdir(path):
            continue
        tasks = sorted({"T" + n for n in re.findall(r"t(\d{3,})", branch, re.I)} & ids)
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
