#!/usr/bin/env python3
"""T235 — set up the current git project for the Easy Kit plugin (`/easy-kit:init`), add-only.

Usage (from the project root, as `commands/init.md` runs it):
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/plugin_init.py"

A plugin carries skills, agents and hooks, but no file of the project. This writes the files the
plugin cannot carry into the current directory, which must be inside a git work tree:
  * `CLAUDE.md` (the `@AGENTS.md` import line) and `AGENTS.md`
  * `PROJECT_KANBAN.md`: the board template's sections with no task rows, `tasks/`, `memory/`
  * copies of `templates/`, `docs/claude-md/` and `agents/` (D7, user decision 2026-11-03)
  * the scripts the doctrine calls by a repo-relative path (D7 a): `.claude/hooks/stop_auto_verify.py`
    with `.claude/hooks/lib/`, `scripts/board_sync.py`, `scripts/pull_moment.py`,
    `skills/craft-spawn-prompt/scripts/memory_slice.py`. Nothing wires these as hooks.

Add only: a path that exists is never written, and is named in the report (`= kept <path>`). A
second run changes no byte. The target is the cwd, never a parent folder with a board and never the
plugin folder (D7 c). `__pycache__` is never copied. Settings are not written here: the command
runs the `settings-setup` dry run and writes only after the user approves (D2).

Output: one line per path (`+ created`, `= kept`), then notes. Exit 0 done, 2 when the cwd is not
in a git work tree or is the kit's own folder (nothing written). Stdlib only.
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import date

KIT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SKIP = ("__pycache__", ".state", "tests")
TREES = ("templates", os.path.join("docs", "claude-md"), "agents", os.path.join(".claude", "hooks", "lib"))
FILES = ("AGENTS.md", os.path.join(".claude", "hooks", "stop_auto_verify.py"),
         os.path.join("scripts", "board_sync.py"), os.path.join("scripts", "pull_moment.py"),
         os.path.join("skills", "craft-spawn-prompt", "scripts", "memory_slice.py"))

# The same text `setup.sh` `scaffold_project` writes, so both install modes start memory alike.
MEMORY = {
    "MEMORY.md": """# MEMORY.md — Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 42,000 characters — a ratchet: `/compact-memory` may lower
> it, never raise it to fit growth. One-line summaries + links to cold files.
> Each spawn prompt carries a slice of these lines (craft-spawn-prompt's memory_slice.py) and this
> path to read in full only when the slice falls short; the whole file is not pasted.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary.
     Target ≤150 chars/entry. Advisory: reported by the size test, never enforced.
     The enforced gate is the 42,000-character whole-file budget above. -->
""",
    "decisions.md": """# decisions.md — Cold Tier: Architectural & Infrastructure Decisions

> **Rules**: Supervisor-only writes. Each entry: `### YYYY-MM-DD — Title`, then **Decision**, **Why**, and **Files** (cite paths — the diff-driven pass greps this file by changed file path).

## Architecture

## Infrastructure
""",
    "glossary.md": """# glossary.md — Cold Tier: Domain Terms & Domain Models

> **Rules**: Supervisor-only writes. One canonical definition per term — update in place, never duplicate. Domain Models section is populated at Stage 1 step 7 (Core Domain Models scan) and confirmed by the user.

## Domain Terms

## Domain Models
""",
    "learnings.md": """# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

## Patterns

## Gotchas
""",
}
# Template lines that are sample rows, not structure: a sample In Progress row would block every push.
SAMPLE_ROW = re.compile(r"^(- \[[ x~]\] \*\*T\d+\*\*|\| T\[NNN\] \|)")


def board_text():
    with open(os.path.join(KIT, "templates", "PROJECT_KANBAN_template.md"), encoding="utf-8") as fh:
        lines = [line for line in fh.read().splitlines(True) if not SAMPLE_ROW.match(line)]
    return "".join(lines).replace("[YYYY-MM-DD]", date.today().isoformat())


class Report:
    def __init__(self, root):
        self.root, self.created, self.lines = root, 0, []

    def write(self, rel, content=None, src=None):
        """Write `rel` from text or a source file, only when nothing is there yet."""
        dst = os.path.join(self.root, rel)
        if os.path.lexists(dst):
            self.lines.append(f"= kept {rel} (already there, not changed)")
            return False
        os.makedirs(os.path.dirname(dst) or self.root, exist_ok=True)
        if src is not None:
            shutil.copy2(src, dst)
        else:
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(content)
        self.created += 1
        self.lines.append(f"+ created {rel}")
        return True

    def tree(self, rel_dir):
        """Copy every file of the kit's `rel_dir`. A fully present tree is one line, not one per file."""
        start = len(self.lines)
        total = kept = 0
        for here, dirs, files in os.walk(os.path.join(KIT, rel_dir)):
            dirs[:] = sorted(d for d in dirs if d not in SKIP)
            for name in sorted(files):
                rel = os.path.relpath(os.path.join(here, name), KIT)
                total += 1
                kept += not self.write(rel, src=os.path.join(here, name))
        if total and kept == total:
            del self.lines[start:]
            self.lines.append(f"= kept {rel_dir}/ ({total} files, all already there)")


def git_toplevel(cwd):
    try:
        done = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True,
                              text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def populate(report, root):
    report.write("CLAUDE.md", content="@AGENTS.md\n")
    report.write("PROJECT_KANBAN.md", content=board_text())
    for rel in FILES:
        report.write(rel, src=os.path.join(KIT, rel))
    for rel in TREES:
        report.tree(rel)
    if os.path.isdir(os.path.join(root, "tasks")):
        report.lines.append("= kept tasks/ (already there)")
    else:
        os.makedirs(os.path.join(root, "tasks"))
        report.created += 1
        report.lines.append("+ created tasks/")
    for name, text in MEMORY.items():
        report.write(os.path.join("memory", name), content=text)
    report.write(os.path.join("memory", "learning-records", ".gitkeep"), content="")


def main():
    root = os.path.realpath(os.getcwd())
    if git_toplevel(root) is None:
        print("easy-kit init: not inside a git repository; nothing written. Run `git init` first, "
              "or run /easy-kit:init from inside your project.", file=sys.stderr)
        return 2
    if root == KIT:
        print("easy-kit init: this folder is the kit itself; nothing written.", file=sys.stderr)
        return 2

    print(f"easy-kit init in {root}")
    report = Report(root)
    try:
        populate(report, root)
    except OSError as exc:  # e.g. `templates` is a file: say so, never a traceback
        print("\n".join(report.lines))
        print(f"easy-kit init: stopped, cannot write ({exc}). The paths above were done; nothing "
              "was overwritten. Fix the path and run /easy-kit:init again.", file=sys.stderr)
        return 1
    print("\n".join(report.lines))
    print(f"{report.created} path(s) created." if report.created
          else "nothing changed: every path was already there.")
    try:
        with open(os.path.join(root, "CLAUDE.md"), encoding="utf-8") as fh:
            imports = "@AGENTS.md" in fh.read()
    except (OSError, UnicodeDecodeError):
        imports = False
    if not imports:
        print("note: your CLAUDE.md does not import the kit doctrine. Add the line `@AGENTS.md` "
              "to it yourself; init never edits an existing file.")
    print("note: templates/, docs/claude-md/, agents/ and the copied scripts go stale after a plugin "
          "update. Run /easy-kit:init again to add new files; it never replaces a file that is there.")
    print("note: the gates are plugin hooks. Each teammate must install the easy-kit plugin "
          "(`claude plugin install easy-kit@easy-kit`); a teammate without it has no gates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
