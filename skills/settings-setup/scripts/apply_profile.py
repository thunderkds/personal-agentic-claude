#!/usr/bin/env python3
"""T200 - merge one settings profile into a project's .claude/settings.json, add-only.

Usage (run from the project root):
    python3 skills/settings-setup/scripts/apply_profile.py <profile-id> [--dry-run] [--settings PATH]

Profiles live in ../profiles.json: dotted keys -> values. The merge never takes anything away:
  * a list value is unioned: existing items first, in their order; missing profile items appended;
    no duplicates added
  * a scalar is set only when the key is absent; a different existing value is kept and reported
  * every other key (hooks included) is left as it is; key order is kept
No settings file: it is created with the profile only (not in --dry-run).

Output, one line each: `+ <key>: <value>` for every rule or key added, `= kept <key>: <theirs>`
for an existing key whose value differs from the profile, then `wrote <path>` (real run) or
`dry run: nothing written`. Nothing to add: `no change`, and the file is not rewritten.

Exit 0 on success. Exit 2, with the reason on stderr and the file byte-identical, when: the
profile id is unknown, the file is not valid JSON (JSONC comments included) or not an object,
a parent key such as `permissions` is not an object, a target list is not a list, or the path is
a symlink.

The file is written atomically (temp file in the same folder + os.replace) and keeps its
permission bits. Format after a write: 2-space indent, non-ASCII kept, trailing newline (the
original indent is not kept). Stdlib only.
"""
import argparse
import json
import os
import stat
import sys
import tempfile

PROFILES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles.json")
DEFAULT_SETTINGS = os.path.join(".claude", "settings.json")


def die(reason):
    sys.stderr.write("apply_profile: %s\n" % reason)
    sys.exit(2)


def load_profiles():
    try:
        with open(PROFILES, encoding="utf-8") as handle:
            return {p["id"]: p for p in json.load(handle)["profiles"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        die("cannot read %s (%s)" % (PROFILES, exc))


def load_settings(path):
    """The parsed settings object, or {} when the file does not exist."""
    if os.path.islink(path):
        die("%s is a symlink; refusing to write through it" % path)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.loads(handle.read())
    except (OSError, ValueError) as exc:
        die("%s is not valid JSON, file left unchanged (%s)" % (path, exc))
    if not isinstance(data, dict):
        die("%s does not hold a JSON object, file left unchanged" % path)
    return data


def show(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def merge(settings, values):
    """Add the profile values to `settings` in place. Returns (added lines, kept lines)."""
    added, kept = [], []
    for dotted, value in values.items():
        parts = dotted.split(".")
        node = settings
        for i, part in enumerate(parts[:-1]):
            if part not in node:
                node[part] = {}
            node = node[part]
            if not isinstance(node, dict):
                die('"%s" in the settings is not an object, file left unchanged' % ".".join(parts[:i + 1]))
        leaf = parts[-1]
        if isinstance(value, list):
            current = node.get(leaf, [])
            if not isinstance(current, list):
                die('"%s" in the settings is not a list, file left unchanged' % dotted)
            missing = []
            for item in value:
                if item not in current and item not in missing:
                    missing.append(item)
            if missing:
                node[leaf] = current + missing
                added.extend("+ %s: %s" % (dotted, show(item)) for item in missing)
        elif leaf not in node:
            node[leaf] = value
            added.append("+ %s: %s" % (dotted, json.dumps(value, ensure_ascii=False)))
        elif node[leaf] != value:
            kept.append("= kept %s: %s" % (dotted, json.dumps(node[leaf], ensure_ascii=False)))
    return added, kept


def write_atomic(path, content):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except OSError:
        mode = None
    handle, tmp = tempfile.mkstemp(prefix=".settings-setup-", dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(content)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv):
    parser = argparse.ArgumentParser(description="Merge a settings profile into .claude/settings.json, add-only.")
    parser.add_argument("profile")
    parser.add_argument("--dry-run", action="store_true", help="print the change, write nothing")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS, help="default: .claude/settings.json")
    args = parser.parse_args(argv)

    profiles = load_profiles()
    if args.profile not in profiles:
        die("unknown profile %r; valid ids: %s" % (args.profile, ", ".join(profiles)))

    settings = load_settings(args.settings)
    added, kept = merge(settings, profiles[args.profile]["values"])
    for line in added + kept:
        print(line)
    if not added:
        print("no change")
        return 0
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    try:
        write_atomic(args.settings, json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    except OSError as exc:
        die("cannot write %s (%s)" % (args.settings, exc))
    print("wrote %s" % args.settings)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
