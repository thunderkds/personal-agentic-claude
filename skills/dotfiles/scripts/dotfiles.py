#!/usr/bin/env python3
"""T228 - keep shared agent config in one source folder, add-only.

Usage: dotfiles.py {plan,apply,status} [--source DIR] [--claude-dir DIR]... [--codex-dir DIR]...

`plan` prints every change and writes nothing, `apply` makes them, `status` reports drift. With no
target folder it lists the folders it found and changes nothing: a folder is never picked for you.
Only `permissions.deny` and `permissions.ask` leave settings.base.json. `permissions.allow` never
does: an allow would widen what an agent may do (lib/merge-settings.py, T148). Codex folders get
skills and instructions only. settings.json is the one file opened in a target folder.

Exit: 0 done or in sync; 1 status found drift or a conflict; 2 a target or the source was refused,
an empty path, or status on a missing source or a missing target.
"""
import argparse
import glob
import json
import os
import stat
import sys
import tempfile
import time
from types import SimpleNamespace

RULE_KEYS = ("deny", "ask")
LAYOUT = """expected source layout (each part is optional):
  settings.base.json   permissions.deny and permissions.ask are added to Claude folders
  AGENTS.md            linked as CLAUDE.md (Claude folders) and AGENTS.md (Codex folders)
  skills/<name>/       linked as skills/<name> in each folder"""


def unique_keys(pairs):
    """A rewrite would lose the value of a duplicate key, so refuse it."""
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError("duplicate JSON key")
    return dict(pairs)


def not_json(name):
    raise ValueError("%s is not JSON" % name)


def finite_float(text):
    value = float(text)
    return not_json(text) if abs(value) == float("inf") else value


def parse_settings(raw):
    """(data, permissions) from JSON bytes. ValueError on bad JSON or a wrong type."""
    data = json.loads(raw, object_pairs_hook=unique_keys, parse_constant=not_json,
                      parse_float=finite_float)
    if not isinstance(data, dict):
        raise ValueError("not a JSON object")
    permissions = data.get("permissions", {})
    if not isinstance(permissions, dict):
        raise ValueError("permissions is not an object")
    for key in RULE_KEYS:
        values = permissions.get(key, [])
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise ValueError("permissions.%s is not a list of strings" % key)
    return data, permissions


def load_source(root):
    """What the source offers. ValueError or OSError when it cannot be read safely."""
    source = SimpleNamespace(root=root, rules={key: [] for key in RULE_KEYS}, ignored=[])
    base = os.path.join(root, "settings.base.json")
    if os.path.lexists(base):
        with open(base, "rb") as handle:
            data, permissions = parse_settings(handle.read())
        json.dumps(data, ensure_ascii=False).encode("utf-8")  # text with no UTF-8 form is refused
        for key in RULE_KEYS:
            source.rules[key] = list(dict.fromkeys(permissions.get(key, [])))
            if not all(rule and rule.isprintable() for rule in source.rules[key]):
                raise ValueError("permissions.%s has an empty or unprintable rule" % key)
        source.ignored = sorted("permissions." + k for k in permissions if k not in RULE_KEYS)
        source.ignored += sorted(k for k in data if k != "permissions")
    agents = os.path.join(root, "AGENTS.md")
    if os.path.lexists(agents) and not os.path.isfile(agents):
        raise ValueError("AGENTS.md is not a file")  # T230: a folder would be skipped unseen
    source.agents = agents if os.path.isfile(agents) else None
    skills = os.path.join(root, "skills")
    if os.path.lexists(skills) and not os.path.isdir(skills):
        raise ValueError("skills is not a folder")
    names = sorted(os.listdir(skills)) if os.path.isdir(skills) else []
    source.skills = [n for n in names
                     if not n.startswith(".") and os.path.isdir(os.path.join(skills, n))]
    if not all(n.isprintable() for n in source.skills):
        # T230: a newline in a folder name could print a fake `plan` line
        raise ValueError("a skills folder name has unprintable text")
    return source


def inspect_settings(target, rules, found):
    """Fill `found` with the rules this target lacks. A symlink is never read or replaced."""
    path = os.path.join(target, "settings.json")
    if os.path.islink(path):
        found.conflicts.append("settings.json: symlink")
        return
    try:
        if os.path.lexists(path):
            if not os.path.isfile(path):
                raise ValueError("not a regular file")
            with open(path, "rb") as handle:
                found.raw = handle.read()
        data, permissions = parse_settings(b"{}" if found.raw is None else found.raw)
        for key in RULE_KEYS:
            current = permissions.get(key, [])
            missing = [rule for rule in rules[key] if rule not in current]
            if missing:
                permissions[key] = current + missing
                found.changes += ["+ permissions.%s: %s" % (key, rule) for rule in missing]
        if found.changes:
            if found.raw is not None and not os.access(path, os.W_OK):
                raise ValueError("file is read-only")  # a rename would get past the lock
            data["permissions"] = permissions
            text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            found.merged = text.encode("utf-8")  # here, so plan and apply refuse alike
    except (OSError, ValueError, RecursionError) as exc:
        found.refused = "settings.json: %s" % exc


def broken_links(target, root):
    """Links at our paths that point inside the source at something gone. Opens nothing."""
    names = ["CLAUDE.md", "AGENTS.md"]
    skills = os.path.join(target, "skills")
    if os.path.isdir(skills) and not os.path.islink(skills):
        names += ["skills/" + name for name in sorted(os.listdir(skills))]
    roots = (root + os.sep, os.path.realpath(root) + os.sep)
    broken = []
    for name in names:
        path = os.path.join(target, name)
        if os.path.islink(path) and not os.path.exists(path):
            stored = os.path.join(os.path.dirname(path), os.readlink(path))
            if os.path.normpath(stored).startswith(roots):
                broken.append(name)
    return broken


def inspect_target(target, kind, source):
    found = SimpleNamespace(changes=[], conflicts=[], links=[], refused=None, merged=None, raw=None)
    real_target, real_root = os.path.realpath(target), os.path.realpath(source.root)
    if real_target == real_root:
        found.refused = "target is the source folder"
        return found
    if real_target.startswith(real_root + os.sep):
        found.refused = "target is inside the source folder"  # T230: links would point into itself
        return found
    if kind == "claude" and any(source.rules.values()):
        inspect_settings(target, source.rules, found)
    if found.refused:
        return found
    try:
        broken = broken_links(target, source.root)
    except OSError as exc:
        found.refused = "skills: %s" % exc
        return found
    found.conflicts += ["%s: broken link" % name for name in broken]
    pairs = []
    if source.agents:
        pairs.append((source.agents, "CLAUDE.md" if kind == "claude" else "AGENTS.md"))
    skills_dir = os.path.join(target, "skills")
    if source.skills and os.path.lexists(skills_dir) and (
            os.path.islink(skills_dir) or not os.path.isdir(skills_dir)):
        found.conflicts.append("skills: not a plain folder")
    elif source.skills:
        pairs += [(os.path.join(source.root, "skills", n), "skills/" + n) for n in source.skills]
    for origin, name in pairs:
        dest = os.path.join(target, name)
        if name in broken:
            continue
        if not os.path.lexists(dest):
            found.links.append((origin, dest))
            found.changes.append("+ link %s -> %s" % (name, origin))
        elif not os.path.islink(dest):
            found.conflicts.append("%s: real file or folder" % name)
        elif os.path.realpath(dest) != os.path.realpath(origin):
            found.conflicts.append("%s: link to elsewhere" % name)
    return found


def write_backup(path, raw, mode):
    """Write `raw` to a new timestamped file; an existing backup is never overwritten."""
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    base, count = "%s.bak-%s" % (path, stamp), 0
    while True:
        name = base if not count else "%s.%d" % (base, count)
        try:
            handle = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        except FileExistsError:
            count += 1
            continue
        with os.fdopen(handle, "wb") as out:
            out.write(raw)
        return name


def write_settings(target, found):
    path = os.path.join(target, "settings.json")
    mode = 0o600
    if found.raw is not None:
        mode = stat.S_IMODE(os.stat(path).st_mode)
        print("  backup %s" % write_backup(path, found.raw, mode))
    handle, temp = tempfile.mkstemp(dir=target, prefix=".settings.json.")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(found.merged)
            out.flush()
            os.fsync(out.fileno())
            os.fchmod(out.fileno(), mode)
        os.replace(temp, path)
    except BaseException:
        os.unlink(temp)
        raise
    print("  wrote %s" % path)


def apply_target(target, found):
    if found.merged is not None:
        write_settings(target, found)
    for origin, dest in found.links:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        os.symlink(origin, dest)


def found_folders():
    home = os.path.expanduser("~")
    folders = [path for path in sorted(glob.glob(os.path.join(home, ".claude*")))
               if os.path.isdir(path) and os.path.isfile(os.path.join(path, "settings.json"))]
    codex = os.path.join(home, ".codex")
    return folders + ([codex] if os.path.isdir(codex) else [])


def run_targets(command, source, targets):
    """Plan, apply or check each target. Return the exit code."""
    code = 0
    if source.ignored:
        print("ignored in settings.base.json: %s" % ", ".join(source.ignored))
    for kind, target in targets:
        if not os.path.isdir(target):
            print("skipped %s: folder not found" % target)
            code = 2 if command == "status" else code
            continue
        print("%s (%s)" % (target, kind))
        found = inspect_target(target, kind, source)
        if found.refused:
            print("  refused %s, nothing written here" % found.refused)
            code = 2
            continue
        for line in found.changes:
            print("  " + line)
        for line in found.conflicts:
            print("  conflict %s, not changed" % line)
        if command == "status" and (found.changes or found.conflicts):
            print("  drift")
            code = max(code, 1)
        elif not found.changes and not found.conflicts:
            print("  in sync" if command == "status" else "  no change")
        if command == "apply":
            try:
                apply_target(target, found)
            except OSError as exc:
                print("  refused %s" % exc)
                code = 2
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Keep agent config in one source folder.")
    parser.add_argument("command", choices=("plan", "apply", "status"))
    parser.add_argument("--source", default="~/.dotfiles/agents")
    parser.add_argument("--claude-dir", action="append", default=[])
    parser.add_argument("--codex-dir", action="append", default=[])
    args = parser.parse_args(argv)
    if "" in [args.source] + args.claude_dir + args.codex_dir:
        parser.error("--source, --claude-dir and --codex-dir must not be empty")
    full = lambda path: os.path.abspath(os.path.expanduser(path))
    root = full(args.source)
    targets = [("claude", full(p)) for p in args.claude_dir]
    targets += [("codex", full(p)) for p in args.codex_dir]
    if not os.path.isdir(root):
        print("source not found: %s\n%s" % (root, LAYOUT))
        if args.command == "status" and targets:
            return 2  # a script reads 0 as in sync
    elif targets:
        try:
            source = load_source(root)
        except (OSError, ValueError, RecursionError) as exc:
            print("refused source %s: %s" % (root, exc), file=sys.stderr)
            return 2
        return run_targets(args.command, source, targets)
    if not targets:
        print("no target folder chosen, nothing changed. Found:")
        for path in found_folders():
            print("  " + path)
        print("choose with --claude-dir <dir> or --codex-dir <dir>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
