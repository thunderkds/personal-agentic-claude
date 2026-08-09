#!/usr/bin/env python3
"""Shared section resolver for the TASK_GUIDE / TASK_REVIEW split (T064).

Answers "where does this task's `### Evidence` / `## Demonstration` section
live?" for the three consumers that read them:

  * ``pre_agent_validate_guide.py`` — the blank-BEFORE spawn advisory
  * ``pre_bash_block_unsafe_merge.py`` — the Stage 5 merge gate's `verify` row
  * ``.claude/skills/delivery-report/render.py`` — the delivery report

Both sections are filled by the *reviewer* at Stage 4/5, and the implementing
agent re-reads its guide on every turn, so they moved out of
``tasks/TASK_GUIDE_Txxx.md`` into a sibling ``tasks/TASK_REVIEW_Txxx.md``.

**Fallback, not migration — and inline wins.** Resolution order is fixed:

  1. the section in ``TASK_GUIDE_Txxx.md``
  2. the section in ``TASK_REVIEW_Txxx.md``

Every pre-T064 guide keeps both sections inline, so every parser keeps finding
them exactly where it always did and no historical task changes behaviour. A
stray review file can never override a guide that still carries the section
itself. This hook family has five recorded parsing defects
(T018/T022/T024/T042/T045); a big-bang migration would have put all existing
guides on the new path at once, so it was rejected.

A *vacated* section — the heading kept in place with only a ``> **Moved.**``
blockquote pointer under it — counts as **absent**, so resolution falls through
to the review file. That is the "distinguish absent from present-but-blank"
edge case: a section whose body is nothing but blockquote guidance carries no
reviewer-filled content, while a genuinely blank *field* inside a real section
is the caller's business (`before_field_is_blank` still decides that).

Contract, copied deliberately from ``lib/task_context.py``:

* **Never raises.** Every entry point degrades to ``None`` on any bad input,
  missing directory, unreadable file, or malformed argument. Two of the three
  consumers run before *every* tool call in the repo.
* **``None`` means "no section", never "assume it is fine".** The merge gate
  fails **closed** on ``None`` (AC7): if "review file missing" were ever treated
  as anything other than "no evidence", the gate would stop gating on every
  task, silently. The advisory hook fails *open* by warning, which is its
  correct direction.
* **``task_id`` is sanitised before it reaches a path.** It is externally
  supplied and reaches a filename, the same shape as the ``session_id`` traversal
  fixed on T056. Anything that is not ``T`` + digits resolves to ``None``.
"""
import os
import re

GUIDE_PREFIX = "TASK_GUIDE_"
REVIEW_PREFIX = "TASK_REVIEW_"

# `T64` and `T064` name the same task. Anchored end-to-end: no separators, no
# path components, no shell metacharacters can survive this.
TASK_ID_PATTERN = re.compile(r"\AT(\d{1,6})\Z", re.IGNORECASE)

# A blockquote line, a horizontal rule, or blank. A body made only of these is
# the vacated `> **Moved.**` pointer (or leftover template guidance) — not
# content. The `---` rule matters: it is what separates sections in every guide
# in this repo, so it sits inside the vacated body and would otherwise make an
# empty section look filled.
POINTER_LINE_PATTERN = re.compile(r"\A\s*(?:>.*|-{3,}|\*{3,}|_{3,})?\Z")


def normalize_task_id(task_id):
    """`'T64'` / `'t064'` / `'064'`-shaped input -> `'T064'`, else None."""
    if not isinstance(task_id, str):
        return None
    match = TASK_ID_PATTERN.match(task_id.strip())
    if not match:
        return None
    return "T" + match.group(1).zfill(3)


def is_pointer_only(body):
    """True when a section body carries no content — empty, or nothing but
    blockquote lines (the `> **Moved.** See tasks/TASK_REVIEW_Txxx.md.`
    pointer left in a vacated position)."""
    if not isinstance(body, str):
        return True
    return all(POINTER_LINE_PATTERN.match(line) for line in body.splitlines())


def slice_section(text, heading):
    """Return the body under `## <heading>` / `### <heading>`, or None.

    The heading may carry a trailing qualifier — `### Evidence (filled by
    reviewer at Stage 4/5)` is the legacy guides' spelling and must resolve the
    same as the review file's bare `## Evidence`.

    Terminated by the next line-start `##`/`###` heading, anchored with
    ``re.MULTILINE``. Anchoring is not optional: an unanchored lookahead
    truncates at the first inline `##` in any line, which is the recorded
    `###`-in-a-Kanban-row defect (T045, the 5th in this family).
    """
    if not isinstance(text, str) or not isinstance(heading, str) or not heading:
        return None
    pattern = rf"^#{{2,3}}\s*{re.escape(heading)}\b[^\n]*$(.*?)(?=^#{{2,3}}\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def _read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _candidate_paths(tasks_dir, prefix, task_id):
    """Zero-padded first, then the raw digits — the two-line path juggling that
    was duplicated at three call sites before this module existed."""
    digits = task_id[1:]
    names = [f"{prefix}{task_id}.md"]
    unpadded = digits.lstrip("0") or "0"
    if unpadded != digits:
        names.append(f"{prefix}T{unpadded}.md")
    return [os.path.join(tasks_dir, name) for name in names]


def _section_from(tasks_dir, prefix, task_id, heading):
    for path in _candidate_paths(tasks_dir, prefix, task_id):
        text = _read_text(path)
        if text is None:
            continue
        body = slice_section(text, heading)
        if body is not None and not is_pointer_only(body):
            return body
    return None


def read_guide_section(task_id, heading, tasks_dir):
    """Resolve a task's `heading` section: guide first, review file second.

    Returns the section *body* (heading line excluded) or ``None`` when neither
    source carries it. Never raises.
    """
    try:
        normalized = normalize_task_id(task_id)
        if not normalized or not isinstance(tasks_dir, str) or not tasks_dir:
            return None
        for prefix in (GUIDE_PREFIX, REVIEW_PREFIX):
            body = _section_from(tasks_dir, prefix, normalized, heading)
            if body is not None:
                return body
        return None
    except Exception:
        return None


def read_review_text(task_id, tasks_dir):
    """The sibling review file's full text, or None. For callers handed a guide
    path rather than a task id (`delivery-report`'s renderer)."""
    try:
        normalized = normalize_task_id(task_id)
        if not normalized or not isinstance(tasks_dir, str) or not tasks_dir:
            return None
        for path in _candidate_paths(tasks_dir, REVIEW_PREFIX, normalized):
            text = _read_text(path)
            if text is not None:
                return text
        return None
    except Exception:
        return None


def resolve_section(guide_text, review_text, heading):
    """Same ordered precedence as `read_guide_section`, for callers that already
    hold both texts in memory. Returns the body or None. Never raises."""
    try:
        for text in (guide_text, review_text):
            body = slice_section(text, heading)
            if body is not None and not is_pointer_only(body):
                return body
        return None
    except Exception:
        return None
