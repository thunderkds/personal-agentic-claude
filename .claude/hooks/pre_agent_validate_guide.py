#!/usr/bin/env python3
"""
PreToolUse hook — fires before every Agent tool call.

Extracts a task ID (Txxx) from the spawn prompt and blocks the spawn
if the corresponding tasks/TASK_GUIDE_Txxx.md does not exist.

Also blocks (T160) when the guide exists but is incomplete — a required section
(`guide_sections.missing_guide_sections`) is missing or blank — naming the sections, so
a one-line board issue's guide cannot be spawned on. A crash in that check fails
open (allows), like every advisory below.

Also reads the target guide's `Depends on:` field (if present) and warns
— non-blocking — if the referenced task isn't Done yet on
PROJECT_KANBAN.md, or doesn't exist at all. This is advisory only: it
never sets "decision": "block", so intentional parallel/stub work is
never prevented.

Also warns — non-blocking — when a prompt names a TASK_GUIDE but carries no
`<!-- memory-slice:` marker (T125): craft-spawn-prompt element 4 was skipped, so
the agent gets no memory lines about its task. The hook never inserts the
slice itself; hooks do not rewrite spawn prompts.

Likewise warns — non-blocking — when a prompt names a TASK_GUIDE but has no
`**Startup reads**` block (T129): the agent was never told to read PROJECT_SPEC.md
and its role guide first.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(ROOT, "tasks")
KANBAN = os.path.join(ROOT, "PROJECT_KANBAN.md")

# The Demonstration block may live in the guide or in the sibling TASK_REVIEW
# file (T064). This hook is advisory only, so a broken import degrades to "no
# Demonstration warnings" rather than blocking a spawn.
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from guide_sections import missing_guide_sections, read_guide_section
except Exception:  # pragma: no cover - fail open, never block a spawn
    def read_guide_section(task_id, heading, tasks_dir):
        return None

    def missing_guide_sections(text):
        return []

# Task IDs are `T\d+`, plus the board's `id_pattern` when `.claude/board.json` sets one
# (T153). A broken import degrades to today's `T\d+`, never to "no IDs": the
# missing-guide block keeps working for every `Txxx` task.
try:
    from board.config import PATH_SAFE_ID, normalize_task_id, task_id_pattern
except Exception:  # pragma: no cover - fall back to local IDs
    PATH_SAFE_ID = re.compile(r"\A[A-Z0-9#_-]{1,64}\Z")

    def task_id_pattern(root=None, local=r"T\d+", bounded=False):
        return rf"(?<![A-Za-z0-9_])(?:{local})(?![A-Za-z0-9_])" if bounded else local

    def normalize_task_id(task_id):
        return task_id.upper()


def task_key(raw_id):
    """A matched ID -> this hook's task key: the digits for a `Txxx` ID (the key
    every function here has always taken), the upper-cased ID for a board ID.
    None when the ID is not `PATH_SAFE_ID`: an over-broad `id_pattern` must
    never turn into a guide path outside `tasks/`."""
    if re.fullmatch(r"[Tt]\d+", raw_id):
        return raw_id[1:]
    key = normalize_task_id(raw_id)
    return key if PATH_SAFE_ID.match(key) else None


def task_ref(tid):
    """Task key -> displayed / file-name ID: `7` -> `T007`, `ENG-170` unchanged."""
    return f"T{tid.zfill(3)}" if tid.isdigit() else tid


def guide_candidates(tid, tasks_dir):
    """Zero-padded guide path first, then the raw digits; a board ID has one."""
    names = [f"TASK_GUIDE_{task_ref(tid)}.md"]
    if tid.isdigit():
        names.append(f"TASK_GUIDE_T{tid}.md")
    return [os.path.join(tasks_dir, name) for name in names]


def find_kanban_section(task_ref):
    """Return which board section (Todo/In Progress/Ready for Review/Done/Closed)
    contains task_ref, or None if it isn't found anywhere on the board.

    The match is anchored to the start of a list-item line — `- [ ] **Txxx**`,
    `- [x] **Txxx**` or `- [~] **Txxx**` — so only the row that *is* the task can
    determine its section (T093). Board rows routinely bold-reference *other*
    tasks in their prose (completion notes name their follow-ups, superseded rows
    name their successor); an unanchored `"**Txxx**" in body` test let any such
    mention from an earlier-scanned section win, and Done is scanned first.
    """
    try:
        with open(KANBAN) as f:
            kanban = f.read()
    except FileNotFoundError:
        return None

    for section in ("Done", "Ready for Review", "In Progress", "Todo", "Closed"):
        # The heading may carry a trailing qualifier ("### Closed (investigated,
        # will not do)"), so `[^\n]*` absorbs it. That makes the *heading* side
        # line-anchored too (`^###`): without it, a row quoting `` `### Closed` ``
        # inline — the live T093 row does — would be picked up as the heading and
        # the section body read from that row's own prose. The terminating
        # lookahead stops at the next H2 *or* H3 (`^##` matches both), so Closed's
        # body ends at `## Blocked` instead of running to end-of-file. T045's
        # line-anchoring is preserved on both sides.
        m = re.search(
            rf"^### {re.escape(section)}[^\n]*\n(.*?)(?=^##|\Z)", kanban,
            re.DOTALL | re.MULTILINE,
        )
        if not m:
            continue
        row = re.search(
            rf"^- \[[ x~]\] \*\*{re.escape(task_ref)}\*\*", m.group(1),
            re.MULTILINE,
        )
        if row:
            return section
    return None


def extract_structural_task_ids(prompt):
    """Extract task IDs that are *structurally* referenced in the spawn
    prompt — i.e. this spawn is genuinely about that task — as opposed to
    a bare Txxx substring appearing anywhere in pasted prose (e.g. a
    decision-log sentence from memory/MEMORY.md). Two structural markers
    are recognized:
      1. A literal TASK_GUIDE_Txxx.md file-path reference.
      2. An explicit "Task ID:" declaration line (with or without the
         "**...**" markdown-bold wrapper).
    Free-text mentions like "confirmed T013/T014 have no guide" or
    "T019: reconciled ..." are intentionally NOT matched.
    """
    pattern = task_id_pattern(ROOT)
    found = re.findall(rf"TASK_GUIDE_({pattern})(?:_[A-Z0-9_]+)?\.md", prompt, re.IGNORECASE)
    found += re.findall(rf"(?:\*\*Task ID\*\*|Task ID)\s*:\s*({task_id_pattern(ROOT, bounded=True)})",
                        prompt, re.IGNORECASE)
    return sorted({key for key in map(task_key, found) if key})


def check_dependency_warnings(task_ids):
    """For each spawned task, read its guide's `Depends on:` field and
    return a list of non-blocking warning strings."""
    warnings = []
    dep_pattern = task_id_pattern(ROOT, r"T\d{3}", bounded=True)
    for tid in task_ids:
        ref = task_ref(tid)
        paths = guide_candidates(tid, TASKS_DIR)
        guide_path = next((p for p in paths if os.path.exists(p)), paths[-1])
        try:
            with open(guide_path) as f:
                guide = f.read()
        except FileNotFoundError:
            continue

        m = re.search(r"\*\*Depends on\*\*:\s*(.+)", guide)
        if not m:
            continue
        dep_line = m.group(1).strip()
        if dep_line.lower().startswith("none") or dep_line.startswith("[Txxx"):
            continue

        dep_match = re.search(dep_pattern, dep_line, re.IGNORECASE)
        if not dep_match:
            continue
        dep_ref = normalize_task_id(dep_match.group(0))

        section = find_kanban_section(dep_ref)
        if section is None:
            warnings.append(
                f"{ref} declares 'Depends on: {dep_ref}' but {dep_ref} was not "
                f"found anywhere on PROJECT_KANBAN.md — unknown dependency, check for a typo."
            )
        elif section != "Done":
            warnings.append(
                f"{ref} declares 'Depends on: {dep_ref}', which is currently "
                f"'{section}' (not Done). Confirm this is intentional (e.g. parallel "
                f"stub work) before proceeding."
            )
    return warnings


def before_field_is_blank(guide):
    """True if the guide's `## Demonstration` BEFORE field carries no real
    captured content — i.e. the section is missing entirely, the BEFORE
    field is absent, or its value is only whitespace/template placeholder.

    A placeholder is the unfilled template text the field ships with:
    `[...]` or `<...>`. Prose that merely *contains* the word BEFORE
    elsewhere is never matched, because the field is anchored to the
    literal `**BEFORE**:` marker inside the Demonstration section only.
    """
    sect = re.search(r"^## Demonstration\s*$(.*?)(?=^## |\Z)", guide,
                     re.DOTALL | re.MULTILINE)
    if not sect:
        return True
    return before_value_is_blank(sect.group(1))


def before_value_is_blank(section_body):
    """The same judgement as `before_field_is_blank`, applied to a Demonstration
    section body that has already been resolved — from the guide, or from the
    sibling `TASK_REVIEW_Txxx.md` it moved to (T064). Split out so the resolver
    decides *where* the block lives while this function keeps deciding whether
    its BEFORE field is real; `before_field_is_blank`'s whole-guide signature is
    unchanged for existing callers."""
    if not section_body:
        return True

    m = re.search(r"\*\*BEFORE\*\*[^:]*:\s*(.*?)(?=^\s*\*\*(?:AFTER|DELTA|WITNESS)\*\*|\Z)",
                  section_body, re.DOTALL | re.MULTILINE)
    if not m:
        return True

    value = m.group(1)
    # Strip blockquote guidance lines and template placeholders, then see
    # whether any real captured content is left.
    value = re.sub(r"^\s*>.*$", "", value, flags=re.MULTILINE)
    value = re.sub(r"\[[^\]]*\]|<[^>]*>", "", value)
    # Only the standalone template separator, not the letters inside a word
    # such as "ERROR" — a substring replace here would corrupt real content.
    value = re.sub(r"\bOR\b", "", value)
    return not value.strip()


def check_demonstration_warnings(task_ids, tasks_dir=None):
    """Non-blocking warnings for tasks whose Demonstration BEFORE field is
    still blank at spawn time. A BEFORE cannot be back-filled once an
    implementation commit exists (DDR-0003), so the agent is told now.
    Never blocks: this hook cannot verify *when* a capture was taken, only
    that one is absent.

    The block is resolved guide-first, then `TASK_REVIEW_Txxx.md` (T064). A
    task with no guide at all is skipped — the missing-guide hard block in
    `main()` owns that case."""
    tasks_dir = tasks_dir or TASKS_DIR
    warnings = []
    for tid in task_ids:
        ref = task_ref(tid)
        if not any(os.path.exists(p) for p in guide_candidates(tid, tasks_dir)):
            continue

        section = read_guide_section(ref, "Demonstration", tasks_dir)

        if before_value_is_blank(section):
            warnings.append(
                f"{ref}'s Demonstration BEFORE field is blank. Capture it "
                f"BEFORE your first implementation commit — a BEFORE taken after "
                f"the change is not a BEFORE, and there is no N/A path."
            )
    return warnings


def incomplete_guides(task_ids, tasks_dir=None):
    """`<ID> (missing: A, B)` for each task whose existing guide is incomplete (T160).
    Raises on an unreadable guide; `main()` treats any exception as "allow"."""
    tasks_dir = tasks_dir or TASKS_DIR
    found = []
    for tid in task_ids:
        path = next(p for p in guide_candidates(tid, tasks_dir) if os.path.exists(p))
        with open(path, encoding="utf-8") as f:
            missing = missing_guide_sections(f.read())
        if missing:
            found.append(f"{task_ref(tid)} (missing: {', '.join(missing)})")
    return found


MEMORY_SLICE_MARKER = "<!-- memory-slice:"


def check_memory_slice_warning(prompt):
    """T125: a prompt naming a TASK_GUIDE without a memory-slice block gets one
    non-blocking warning. Keyed on a guide *path*, not a bare `Task ID:` line."""
    if not re.search(rf"TASK_GUIDE_(?:{task_id_pattern(ROOT)})", prompt) or MEMORY_SLICE_MARKER in prompt:
        return []
    return [
        "Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so "
        "the agent gets none of the memory lines its task touches. Run "
        "`python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste "
        "its output verbatim (craft-spawn-prompt element 4)."
    ]


# A line that *starts* with the bold label — a prose mention does not count.
STARTUP_READS_RE = re.compile(r"^\*\*Startup reads\*\*", re.MULTILINE)


def check_startup_reads_warning(prompt):
    """T129: a prompt naming a TASK_GUIDE without a `**Startup reads**` block gets one
    non-blocking warning. Independent of the memory-slice check."""
    if not re.search(rf"TASK_GUIDE_(?:{task_id_pattern(ROOT)})", prompt) or STARTUP_READS_RE.search(prompt):
        return []
    return [
        "Spawn prompt names a TASK_GUIDE but has no `**Startup reads**` block, so the "
        "agent is not told to read PROJECT_SPEC.md, its guide and its role guide first "
        "(craft-spawn-prompt element 8)."
    ]


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if event.get("tool_name") != "Agent":
        sys.exit(0)

    prompt = event.get("tool_input", {}).get("prompt", "")

    task_ids = extract_structural_task_ids(prompt)
    if not task_ids:
        # No task ID in prompt — allow through; Supervisor will handle
        sys.exit(0)

    missing = []
    for tid in task_ids:
        # Zero-padded, then raw digits; a board ID has one file name.
        if not any(os.path.exists(p) for p in guide_candidates(tid, TASKS_DIR)):
            missing.append(f"T{tid}" if tid.isdigit() else tid)

    if missing:
        result = {
            "decision": "block",
            "reason": (
                f"[hook:pre_agent] Cannot spawn agent — missing TASK_GUIDE for: "
                f"{', '.join(missing)}. "
                f"Run Stage 2 planning first to generate the guide(s) in tasks/."
            )
        }
        print(json.dumps(result))
        sys.exit(0)

    try:
        incomplete = incomplete_guides(task_ids)
    except Exception:
        incomplete = []  # fail open: a broken check must never block a spawn
    if incomplete:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"[hook:pre_agent] Cannot spawn agent — incomplete TASK_GUIDE for: "
                f"{'; '.join(incomplete)}. Fill those sections first (Stage 2); in board "
                f"mode push them with `python3 scripts/board_sync.py update --guide <ID>`."
            )
        }))
        sys.exit(0)

    try:
        warnings = check_dependency_warnings(task_ids)
        warnings += check_demonstration_warnings(task_ids)
        slice_warnings = check_memory_slice_warning(prompt)
        warnings += slice_warnings
        reads_warnings = check_startup_reads_warning(prompt)
        warnings += reads_warnings
    except Exception:
        # Fail-open: an advisory path must never block a spawn.
        sys.exit(0)

    for warning in slice_warnings:
        print(f"[hook:pre_agent] memory-slice missing: {warning}", file=sys.stderr)

    for warning in reads_warnings:
        print(f"[hook:pre_agent] startup-reads missing: {warning}", file=sys.stderr)

    if warnings:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": (
                    "[hook:pre_agent] Advisory warning (not blocking):\n  • "
                    + "\n  • ".join(warnings)
                ),
            }
        }))

if __name__ == "__main__":
    main()
