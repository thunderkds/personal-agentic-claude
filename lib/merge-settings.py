#!/usr/bin/env python3
"""merge-settings.py — reconcile the kit's hook entries into a project's
.claude/settings.json without disturbing anything the user added (T111, ADR-0002).

Usage:
    python3 lib/merge-settings.py <upstream-settings.json> <project-settings.json> <project-root>

Exit codes:
    0  merged (the file was rewritten, or was already correct and left alone)
    2  refused — nothing was written. The caller prints the kit hook block to add.

Ownership rule (Supervisor decision, TASK_GUIDE_T111 "Approach"):
    A hook *entry* (one element of settings["hooks"][<event>]) belongs to the kit
    if any of its `hooks[].command` strings references a path under
    `.claude/hooks/`. Matching is done on the PATH found inside the command, not
    on the whole string, so `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/x.py`
    and `python3 ./.claude/hooks/x.py` are the same entry.

    Kit entries are reconciled against the upstream file: an entry whose hook
    script set matches an upstream entry is REPLACED by upstream's version in
    place — so a user who copied a kit entry and edited its matcher or
    description gets upstream's version back. A kit entry upstream no longer
    ships is REMOVED. Entries upstream ships that the project lacks are appended
    to their event's list.

    Every other entry belongs to the user: never modified, never reordered,
    never removed.

Additional guarantees:
    * A kit entry whose hook file does not exist under the project root is
      dropped with a warning — a settings.json pointing at a missing hook file
      breaks every tool call in the project (memory/learnings.md, T074).
    * An event whose list is empty, null, or empties out is removed from
      "hooks"; this is stable across runs.
    * The file is only rewritten when the merged content differs, and the write
      is atomic (temp file in the same directory + os.replace), so an
      interrupted run can never truncate the user's settings.
    * `ensure_ascii=False`, so non-ASCII content the user added stays readable.
    * A symlinked settings.json is refused, never written through.
"""

import json
import os
import re
import sys
import tempfile

HOOK_PATH_RE = re.compile(r"\.claude/hooks/[^\s\"']+")


def die(reason):
    sys.stderr.write("merge-settings: %s\n" % reason)
    sys.exit(2)


def hook_paths(group):
    """Every `.claude/hooks/...` path referenced by one hook entry."""
    paths = []
    for hook in group.get("hooks") or []:
        if not isinstance(hook, dict):
            continue
        found = HOOK_PATH_RE.search(hook.get("command") or "")
        if found:
            paths.append(found.group(0))
    return paths


def is_kit_group(group):
    return isinstance(group, dict) and bool(hook_paths(group))


def group_key(group):
    return frozenset(hook_paths(group))


def merge_event_groups(project_groups, upstream_groups):
    """Reconcile one event's entry list. User entries keep their position."""
    upstream_by_key = {}
    upstream_order = []
    for group in upstream_groups:
        if not is_kit_group(group):
            # Upstream ships kit entries only; anything else is ignored rather
            # than injected into the user's file.
            continue
        key = group_key(group)
        if key not in upstream_by_key:
            upstream_by_key[key] = group
            upstream_order.append(key)

    merged_groups = []
    taken = set()
    for group in project_groups:
        if is_kit_group(group):
            key = group_key(group)
            if key in upstream_by_key and key not in taken:
                merged_groups.append(upstream_by_key[key])
                taken.add(key)
            # else: upstream no longer ships it (or it is a duplicate) -> drop
        else:
            merged_groups.append(group)

    # MUTATION POINT M1 — everything below adds the kit entries the project is
    # missing. tests/test_settings_merge.sh neutralises this step and asserts
    # that the SC1 "kit hooks are wired" check then fails.
    for key in upstream_order:
        if key not in taken:
            merged_groups.append(upstream_by_key[key])
            taken.add(key)

    return merged_groups


def drop_dangling(groups, project_root):
    """Remove kit entries whose hook file is absent from the project."""
    kept = []
    for group in groups:
        missing = [p for p in hook_paths(group)
                   if not os.path.exists(os.path.join(project_root, p))]
        if missing:
            sys.stderr.write(
                "merge-settings: dropping hook entry pointing at missing file(s): %s\n"
                % ", ".join(missing))
            continue
        kept.append(group)
    return kept


def merge(project, upstream, project_root):
    project_hooks = project.get("hooks")
    if project_hooks is None:
        project_hooks = {}
    if not isinstance(project_hooks, dict):
        die('"hooks" in the project settings is not an object')
    upstream_hooks = upstream.get("hooks") or {}
    if not isinstance(upstream_hooks, dict):
        die('"hooks" in the kit settings is not an object')

    events = list(project_hooks.keys())
    for event in upstream_hooks:
        if event not in events:
            events.append(event)

    merged_hooks = {}
    for event in events:
        project_groups = project_hooks.get(event) or []
        upstream_groups = upstream_hooks.get(event) or []
        if not isinstance(project_groups, list):
            die('"hooks.%s" in the project settings is not a list' % event)
        groups = merge_event_groups(project_groups, list(upstream_groups))
        groups = drop_dangling(groups, project_root)
        if groups:
            merged_hooks[event] = groups

    merged = dict(project)
    if merged_hooks:
        merged["hooks"] = merged_hooks
    else:
        merged.pop("hooks", None)
    return merged


def load(path, what):
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        die("cannot read the %s settings file %s: %s" % (what, path, exc))
    try:
        data = json.loads(text)
    except ValueError as exc:
        die("%s is not valid JSON (%s)" % (path, exc))
    if not isinstance(data, dict):
        die("%s does not contain a JSON object" % path)
    return data, text


def write_atomic(path, content):
    directory = os.path.dirname(os.path.abspath(path)) or "."
    handle, tmp = tempfile.mkstemp(prefix=".settings-merge-", dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(content)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv):
    if len(argv) != 4:
        die("usage: merge-settings.py <upstream> <project-settings> <project-root>")
    upstream_path, project_path, project_root = argv[1], argv[2], argv[3]

    if os.path.islink(project_path):
        die("%s is a symlink; refusing to write through it. Replace it with a "
            "regular file and re-run." % project_path)
    if not os.path.exists(project_path):
        die("%s does not exist" % project_path)

    upstream, _ = load(upstream_path, "kit")
    project, original = load(project_path, "project")

    merged = merge(project, upstream, project_root)
    content = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
    if content == original:
        return 0
    write_atomic(project_path, content)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
