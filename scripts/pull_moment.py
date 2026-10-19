#!/usr/bin/env python3
"""Run one pull moment (T157, FR-009, FR-010).

    python3 scripts/pull_moment.py wake            # session start
    python3 scripts/pull_moment.py spawn <ID>      # before spawning an agent for <ID>
    python3 scripts/pull_moment.py review <ID>     # before moving <ID> to Ready for Review

(The fourth moment, before merge, runs inside `pre_bash_block_unsafe_merge.py`.)

Board mode `online`: pull the board cache with `board_sync.py pull`. If the pull fails,
print `board unreachable — using cache (N unsynced)` and carry on with the cache.
`spawn` then records the hash of the cached `tasks/TASK_GUIDE_<ID>.md`; `review` compares
it and, if the guide changed since spawn, prints
`<ID>'s guide changed while you were working — review against the new version?`.

`wake` also prints `N new decisions from teammates since your last session` (T158): entries
in the cached Decision Log, written by others, after the position seen at the last wake.
After a good pull it also prints the lines of `board_sync.py triage --mark` (T160) under one
header: my tasks that are not planned yet or changed since the last wake. The `--mark`
advances the marker, so a change is shown at one wake. A failed pull skips triage.

Board mode `local` (or an unusable `.claude/board.json`): does nothing, prints nothing.

Exit 0 always — a pull moment never blocks work — except 2 for bad arguments.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks", "lib"))
from board import moments  # noqa: E402
from board.config import load_config  # noqa: E402


def triage_lines(root):
    """`board_sync.py triage --mark` output lines; [] on any failure (never blocks a wake)."""
    script = os.path.join(root, "scripts", "board_sync.py")
    try:
        done = subprocess.run([sys.executable, script, "triage", "--mark"], cwd=root,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              timeout=moments.PULL_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return []
    return done.stdout.splitlines() if done.returncode == 0 else []


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("moment", choices=["wake", "spawn", "review"])
    parser.add_argument("task_id", nargs="?")
    args = parser.parse_args(argv)

    task_id = None
    if args.moment != "wake":
        task_id = moments.safe_task_id(args.task_id) if args.task_id else None
        if not task_id:
            parser.error(f"{args.moment} needs a task ID made of letters, digits, # _ -")

    if moments.board_mode(root) != "online":
        return 0

    warning = moments.pull_cache(root)
    if warning:
        print(warning)
    elif args.moment == "wake" and moments.unsynced_count(root):
        print(f"⚠ {moments.unsynced_count(root)} unsynced board writes — run "
              f"python3 scripts/board_sync.py flush")

    if args.moment == "wake":
        decisions_line = moments.new_decisions_line(root, (load_config(root) or {}).get("me"))
        if decisions_line:
            print(decisions_line)
        lines = [] if warning else triage_lines(root)
        if lines:
            print(f"{len(lines)} of your board tasks to triage "
                  f"(skills/wake/references/triage.md):")
            for line in lines:
                print(f"  {line}")

    if args.moment == "spawn":
        path = moments.guide_hash_path(root, task_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(moments.guide_hash(root, task_id) + "\n")
    elif args.moment == "review":
        try:
            with open(moments.guide_hash_path(root, task_id), encoding="utf-8") as f:
                at_spawn = f.read().strip()
        except OSError:
            print(f"{task_id}: no spawn-time guide hash recorded — cannot tell whether its "
                  f"guide changed")
            return 0
        if at_spawn != moments.guide_hash(root, task_id):
            print(f"{task_id}'s guide changed while you were working — review against the "
                  f"new version?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
