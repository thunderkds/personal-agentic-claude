#!/usr/bin/env python3
"""Print the `memory/MEMORY.md` index lines a TASK_GUIDE touches (T125).

    python3 skills/craft-spawn-prompt/scripts/memory_slice.py tasks/TASK_GUIDE_Txxx.md

`craft-spawn-prompt` element 4 pastes this output verbatim into a spawn prompt, so the
agent starts with the few memory lines about its own files instead of reading the whole
index (the most-read file before a spawn's first edit — docs/token-focus-finding-2026-09-25.md
§ 3). Stdlib only, read-only, stdout only.

**Keys** — deterministic, taken from the guide the Supervisor wrote at Stage 2:
  * every backticked path in the first column of the *Files to Change* and *Files Must NOT
    Touch* tables, plus its basename. A glob matches the prefix before the glob. A generic
    basename (`SKILL.md`) is replaced by its directory name, which is how memory names a skill;
  * every `T<digits>` on the `**Depends on**` line;
  * the task's own ID.

**Matching** — a key matches a whole path token: not preceded by a path character, so the
basename `validate.sh` matches a bare mention but not `lib/validate.sh`, where only the full
path would. A path key ending in `/` (or cut at a glob) matches as a prefix.

**Output** — every matching `- [` index line, once, under its heading, in file order, between
`<!-- memory-slice:Txxx -->` and `<!-- /memory-slice -->`, after a one-line header. Over the
cap (30 lines / 4,000 chars of output) the lines with the fewest distinct key hits are
dropped first and the header says how many. The known risk is omission — a relevant decision
whose line names none of these keys — so the spawn prompt keeps the full file as a fallback.
"""
import os
import re
import sys

MAX_LINES = 30
MAX_CHARS = 4000
GENERIC_BASENAMES = {"SKILL.md"}
PATH_CHARS = "A-Za-z0-9_./-"
TABLE_HEADINGS = re.compile(r"^## Files (?:to Change|Must NOT Touch)\b", re.IGNORECASE)


def task_id_of(guide_path, text):
    m = re.search(r"TASK_GUIDE_(T\d+)", os.path.basename(guide_path))
    if not m:
        m = re.search(r"^# TASK_GUIDE\W+(T\d+)", text, re.MULTILINE)
    return m.group(1) if m else "T???"


def table_paths(text):
    """Backticked paths in the first column of the two Files tables."""
    paths, in_table = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_table = bool(TABLE_HEADINGS.match(line))
            continue
        if not in_table or not line.startswith("|"):
            continue
        first_cell = line.strip("|").split("|")[0]
        for span in re.findall(r"`([^`\s]+)`", first_cell):
            if "/" in span or "." in span:
                paths.append(span)
    return paths


def keys_for_path(path):
    """[(key, is_prefix)] for one table path."""
    glob = re.search(r"[*?\[]", path)
    if glob:
        return [(path[:glob.start()], True)]
    if path.endswith("/"):
        return [(path, True)]
    keys = [(path, False)]
    parent, base = os.path.split(path)
    if base in GENERIC_BASENAMES:
        if parent:
            keys.append((os.path.basename(parent), False))
    elif parent:
        keys.append((base, False))
    return keys


def extract_keys(guide_path, text):
    keys = []
    for path in table_paths(text):
        keys.extend(keys_for_path(path))
    dep = re.search(r"\*\*Depends on\*\*:\s*(.+)", text)
    if dep:
        keys.extend((t, False) for t in re.findall(r"\bT\d+\b", dep.group(1)))
    keys.append((task_id_of(guide_path, text), False))
    seen, unique = set(), []
    for key, is_prefix in keys:
        if key and key not in seen:
            seen.add(key)
            unique.append((key, is_prefix))
    return unique


def key_pattern(key, is_prefix):
    tail = "" if is_prefix else r"(?![A-Za-z0-9_/-]|\.[A-Za-z0-9])"
    return re.compile(rf"(?<![{PATH_CHARS}]){re.escape(key)}{tail}")


def index_lines(memory_text):
    """[(heading, line)] for every `- [` index line, with its nearest ##/### heading."""
    heading, lines = None, []
    for line in memory_text.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            heading = line
        elif line.startswith("- ["):
            lines.append((heading, line))
    return lines


def render(task, header, entries):
    out, last_heading = [f"<!-- memory-slice:{task} -->", header], None
    for heading, line in entries:
        if heading != last_heading and heading is not None:
            out.append(heading)
        last_heading = heading
        out.append(line)
    out.append("<!-- /memory-slice -->")
    return "\n".join(out) + "\n"


def build_slice(guide_path, guide_text, memory_text):
    task = task_id_of(guide_path, guide_text)
    keys = extract_keys(guide_path, guide_text)
    if memory_text is None:
        return render(task, "memory/MEMORY.md — MEMORY.md not found; no slice.", [])

    patterns = [(key, key_pattern(key, is_prefix)) for key, is_prefix in keys]
    entries = index_lines(memory_text)
    matched = []  # (position, heading, line, hit keys)
    for pos, (heading, line) in enumerate(entries):
        hits = [key for key, pat in patterns if pat.search(line)]
        if hits:
            matched.append((pos, heading, line, hits))

    if not matched:
        header = (f"memory/MEMORY.md — no memory lines matched this task's files "
                  f"(0 of {len(entries)} index lines; keys: {', '.join(k for k, _ in keys)})")
        return render(task, header, [])

    hit_keys = {k for *_, hits in matched for k in hits}
    names = ", ".join(k for k, _ in keys if k in hit_keys)
    base = f"memory/MEMORY.md — {len(matched)} of {len(entries)} index lines matched on: {names}"

    def header_for(n_kept):
        if n_kept == len(matched):
            return base
        return (f"{base}; {n_kept} shown, {len(matched) - n_kept} dropped by the cap "
                f"({MAX_LINES} lines / {MAX_CHARS:,} chars), fewest key hits first")

    # Rank by distinct key hits, file order breaking ties, and admit in rank order until
    # the next line would push the rendered output over either cap. Stopping there (not
    # skipping to a shorter line) keeps every kept line at least as relevant as any dropped.
    kept = []
    for cand in sorted(matched, key=lambda m: (-len(m[3]), m[0])):
        trial = sorted(kept + [cand])
        text = render(task, header_for(len(trial)), [(h, l) for _, h, l, _ in trial])
        if len(text.splitlines()) > MAX_LINES or len(text) > MAX_CHARS:
            break
        kept = trial
    return render(task, header_for(len(kept)), [(h, l) for _, h, l, _ in kept])


def main(argv):
    if len(argv) != 2:
        print("usage: memory_slice.py <path/to/TASK_GUIDE_Txxx.md>", file=sys.stderr)
        return 2
    guide_path = argv[1]
    try:
        with open(guide_path, encoding="utf-8") as f:
            guide_text = f.read()
    except OSError:
        print(f"memory_slice: guide not found: {guide_path}", file=sys.stderr)
        return 2
    root = os.path.dirname(os.path.dirname(os.path.abspath(guide_path)))
    try:
        with open(os.path.join(root, "memory", "MEMORY.md"), encoding="utf-8") as f:
            memory_text = f.read()
    except OSError:
        memory_text = None
    sys.stdout.write(build_slice(guide_path, guide_text, memory_text))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
