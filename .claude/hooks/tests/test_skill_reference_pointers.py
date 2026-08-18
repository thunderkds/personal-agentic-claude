#!/usr/bin/env python3
"""T079 — every relative Markdown link in a `SKILL.md` must resolve, and stay one level deep.

T078 gates skill *frontmatter*. This module gates the other half of progressive
disclosure: the **context pointers** in a skill body. A pointer that names a file
which does not exist, or one buried under `references/deep/nested/`, breaks the
disclosure chain silently — the agent follows it, finds nothing, and carries on.

Constraints asserted (from `write-better-skill`'s *Agent Skills Spec Conformance*
section, which restates the spec):

  existence   a relative link target must exist on disk, resolved from the
              skill root (symlinked skill roots included — `packs/` symlinks
              skills into `.claude/skills/`, and `os.path.exists` follows them)
  depth       `references/REFERENCE.md` and `scripts/extract.py` are legal;
              anything two or more directories below the skill root is not, and
              neither is a `../` escape out of the skill

NOT links, and deliberately not checked:
  - external links (`https://`, `http://`, `mailto:`) — this suite does no network I/O
  - anchor-only links (`#section`) — intra-document, no file to resolve
  - anything inside a fenced code block or an inline code span. All three of the
    relative-looking links that predate this module (`compact-memory`'s
    `(cold-file.md#section)`, `learn`'s `(memory/learning-records/LR-NNNN-slug.md)`,
    `map-codebase`'s `(codebase-map.md)`) are *illustrative markup* — templates a
    skill tells the agent to write elsewhere, not pointers this skill follows.
    Treating them as pointers would make the gate un-passable without editing
    skills this task must not touch.

The free-passing failure mode this module is built against is recorded in
memory/learnings.md: "a negative-grep test is free-passing if its file list is
wrong". A link test that finds no links is the same defect wearing a different
hat, so `test_sc6_*` guards the extraction layer itself and comes first.

Run with: python3 -m pytest .claude/hooks/tests/test_skill_reference_pointers.py -v
"""
import os
import re

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
SKILLS_DIR = os.path.join(REPO_ROOT, ".claude", "skills")

# A relative link may sit at the skill root or one directory below it. One
# separator is the whole rule; named so a mutation to it is a single edit.
MAX_PATH_SEPARATORS = 1

NON_SKILL_DIRS = {"__pycache__", ".pytest_cache"}

EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "//")

LINK_RE = re.compile(r"\[[^\]]*?\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

def strip_inline_code(line):
    """Blank out inline code spans so their contents are never read as links.

    Backtick runs are matched by length, so ``` `a` `` and ``` ``a`` `` both close
    correctly and an unmatched trailing backtick leaves the rest of the line alone.
    """
    return re.sub(r"(`+)(?:(?!\1).)*\1", lambda m: " " * len(m.group(0)), line)


def extract_relative_links(text):
    """Every relative Markdown link target in `text`, as (line_number, target).

    Fenced blocks are skipped whole; inline code spans are blanked per line.
    External and anchor-only targets are dropped. Fragments (`x.md#y`) are
    trimmed to the path — the file is what must exist.
    """
    links = []
    fence = None
    for lineno, raw in enumerate(text.split("\n"), start=1):
        fence_match = FENCE_RE.match(raw)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[0] * 3
                continue
            if marker[0] * 3 == fence:
                fence = None
            continue
        if fence is not None:
            continue
        for match in LINK_RE.finditer(strip_inline_code(raw)):
            target = match.group(1).strip()
            if not target or target.startswith("#"):
                continue
            if target.lower().startswith(EXTERNAL_PREFIXES):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if target:
                links.append((lineno, target))
    return links


def discover_skill_dirs(root=SKILLS_DIR):
    """Every immediate subdirectory of `root`, symlinks included. Mirrors the
    discovery in `test_skill_spec_conformance.py`; kept local so neither module
    can break the other."""
    if not os.path.isdir(root):
        return []
    found = []
    for entry in os.scandir(root):
        if entry.name.startswith(".") or entry.name in NON_SKILL_DIRS:
            continue
        if entry.is_dir() or (entry.is_symlink() and not os.path.exists(entry.path)):
            found.append(entry.path)
    return sorted(found)


def collect_pointers(root=SKILLS_DIR):
    """(skill_name, lineno, target) for every relative link in every SKILL.md."""
    pointers = []
    for skill_dir in discover_skill_dirs(root):
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md, encoding="utf-8") as fh:
            text = fh.read()
        for lineno, target in extract_relative_links(text):
            pointers.append((os.path.basename(skill_dir), lineno, target))
    return pointers


POINTERS = collect_pointers()
POINTER_IDS = ["%s:%d:%s" % p for p in POINTERS]


# --------------------------------------------------------------------------
# SC6 — guard the extraction layer (first on purpose)
# --------------------------------------------------------------------------

def test_sc6_extraction_finds_at_least_one_pointer():
    """Zero pointers means every parametrized test below asserts nothing.

    Deleting the pointers from the skills, or breaking `extract_relative_links`,
    must turn this suite RED rather than green-and-empty.
    """
    assert os.path.isdir(SKILLS_DIR), "discovery root does not exist: %s" % SKILLS_DIR
    assert len(POINTERS) > 0, (
        "extracted zero relative SKILL.md links under %s — the pointer suite "
        "would pass vacuously" % SKILLS_DIR
    )


def test_sc6_extraction_includes_a_known_pointer():
    """A non-empty extraction can still be the wrong extraction. Pin the pointers
    this task introduced: `write-better-skill` reaches both reference files."""
    targets = {t for skill, _, t in POINTERS if skill == "write-better-skill"}
    for expected in ("references/descriptions.md", "references/instruction-patterns.md"):
        assert expected in targets, (
            "write-better-skill no longer links %s — found %s" % (expected, sorted(targets))
        )


def test_extractor_ignores_non_pointers():
    """The four exclusions, asserted directly rather than inferred from a green run."""
    sample = "\n".join([
        "[ext](https://example.com/a.md)",
        "[anchor](#section)",
        "Format: `- [Title](cold-file.md#section)`",
        "```",
        "[fenced](fenced-target.md)",
        "```",
        "[real](references/x.md#frag)",
    ])
    assert extract_relative_links(sample) == [(7, "references/x.md")]


# --------------------------------------------------------------------------
# SC3 — existence and depth
# --------------------------------------------------------------------------

@pytest.mark.parametrize("skill,lineno,target", POINTERS, ids=POINTER_IDS)
def test_sc3_pointer_target_exists(skill, lineno, target):
    """A pointer names a file the agent is told to read. It must be there."""
    resolved = os.path.join(SKILLS_DIR, skill, target)
    assert os.path.exists(resolved), (
        "%s/SKILL.md line %d points at `%s`, which does not exist (%s)"
        % (skill, lineno, target, resolved)
    )


@pytest.mark.parametrize("skill,lineno,target", POINTERS, ids=POINTER_IDS)
def test_sc3_pointer_stays_one_level_deep(skill, lineno, target):
    """`references/x.md` yes; `references/deep/x.md` and `../y.md` no."""
    parts = target.replace("\\", "/").split("/")
    assert ".." not in parts, (
        "%s/SKILL.md line %d points at `%s`, which escapes the skill root"
        % (skill, lineno, target)
    )
    assert target.count("/") <= MAX_PATH_SEPARATORS, (
        "%s/SKILL.md line %d points at `%s`, which is more than one directory "
        "below the skill root — the spec says keep bundled files one level deep"
        % (skill, lineno, target)
    )
