#!/usr/bin/env python3
"""T198 - print only the Decisions and Learning Records entries of memory/MEMORY.md.

`wake` calls this instead of reading all of MEMORY.md. Entries are newest first. When the two
sections hold more than 20 entry lines together, print the first 5 of each; else print all.
No `memory/MEMORY.md`: print `No MEMORY.md found.`. Neither section: print the `## Index`
block as-is (nothing if that is missing too). Run from the repo root. Read-only; any failure
prints nothing and exits 0 so `wake` never halts.
"""
import sys

MEMORY = "memory/MEMORY.md"
SECTIONS = ("### Decisions", "### Learning Records")
CAP = 20
PER_SECTION = 5


def section_lines(lines, heading):
    """Lines of the `### ` section `heading`, to the next `## ` or `### ` heading; None if absent."""
    body, inside, found = [], False, False
    for line in lines:
        if line.startswith("#"):
            inside = line.strip() == heading
            found = found or inside
        elif inside:
            body.append(line)
    return body if found else None


def index_block(lines):
    """The `## Index` block as-is, to the next `## ` heading; None if absent."""
    block, inside, found = [], False, False
    for line in lines:
        if line.startswith("## ") or line.startswith("# "):
            inside = line.strip() == "## Index"
            found = found or inside
        elif inside:
            block.append(line)
    return block if found else None


def render(text):
    lines = [l.rstrip("\r\n") for l in text.splitlines()]
    bodies = [section_lines(lines, h) for h in SECTIONS]
    if all(b is None for b in bodies):
        block = index_block(lines)
        return [] if block is None else block
    groups = [[l.rstrip() for l in (b or []) if l.startswith("- ")] for b in bodies]
    if sum(len(g) for g in groups) > CAP:
        groups = [g[:PER_SECTION] for g in groups]
    return [l for g in groups for l in g]


def main():
    try:
        with open(MEMORY, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print("No MEMORY.md found.")
        return
    out = render(text)
    if out:
        print("\n".join(out))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
