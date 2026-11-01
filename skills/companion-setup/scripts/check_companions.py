#!/usr/bin/env python3
"""T226 - show the optional companion MCP servers for the Stage 1 offer. Read-only.

Usage (run from the project root):
    python3 skills/companion-setup/scripts/check_companions.py [--installed ID,ID,...]

Reads ../companions.json and looks up each required tool on PATH. It makes no network
call, starts no process and writes no file. The Supervisor passes the servers it sees as
installed in --installed; an id that is not in companions.json is ignored.

One line per server:
    choice: <id> - <what it adds>. Needs <tools>; missing <tools> | all present. Link: <url>
    already installed: <id> (public|private)
    needs repo access: <id> - private repository, not a choice here

Exit 0 always, including when tools are missing or --installed is empty. Stdlib only.
"""
import argparse
import json
import shutil
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "companions.json"


def parse_installed(raw):
    return {part.strip() for part in raw.split(",") if part.strip()}


def describe(entry, installed):
    cid = entry["id"]
    if cid in installed:
        return "already installed: %s (%s)" % (cid, entry["access"])
    if entry["access"] == "private":
        return "needs repo access: %s - private repository, not a choice here" % cid
    missing = [t for t in entry["tools"] if shutil.which(t) is None]
    state = "missing " + ", ".join(missing) if missing else "all present"
    return "choice: %s - %s Needs %s; %s. Link: %s" % (
        cid, entry["adds"], ", ".join(entry["tools"]), state, entry["link"])


def main():
    parser = argparse.ArgumentParser(description="Show the optional companion MCP servers.")
    parser.add_argument("--installed", default="", help="comma-separated ids already installed")
    args = parser.parse_args()
    installed = parse_installed(args.installed)
    entries = json.loads(DATA.read_text(encoding="utf-8"))["companions"]
    for entry in entries:
        print(describe(entry, installed))
    print("Default: skip. The kit never installs a server.")


if __name__ == "__main__":
    main()
