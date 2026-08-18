#!/usr/bin/env python3
"""T078 — Agent Skills spec conformance gate over every skill in `.claude/skills/`.

The 30 skills in this repo all satisfy the Agent Skills specification
(https://agentskills.io/specification) today, but that compliance is *accidental*:
nothing states the constraints and nothing checks them, so the 31st skill can
violate any of them silently. This module converts accidental compliance into
checked compliance.

Constraints asserted (verbatim from the spec's frontmatter table and `name` /
`description` / progressive-disclosure sections):

  name           required; 1-64 chars; lowercase alphanumeric (a-z, 0-9) and
                 hyphens only; must not start or end with `-`; must not contain
                 `--`; must match the parent directory name
  description    required; non-empty; max 1024 characters
  compatibility  optional; max 500 characters if present
  SKILL.md       <= 500 lines (the spec's progressive-disclosure budget)

Deliberately NOT asserted (see TASK_GUIDE_T078 Cut list):
  - the 5,000-token instruction budget — the 500-line rule is the stdlib-checkable
    proxy; a real tokenizer is a dependency for a soft recommendation.
  - `allowed-tools` — the spec marks it Experimental and says support varies by
    implementation; it is unused in this repo.

Discovery is filesystem-driven on purpose (AC8): there is no hardcoded list of
skill names, so a new skill is covered the moment its directory appears. Because
a discovery bug is exactly the failure mode that makes a suite like this
free-pass ("a negative-grep test free-passes when its file list is wrong",
recorded in memory/learnings.md), `test_ac9_*` guards the discovery layer itself
and comes first in this file.

Symlinks: followed. `packs/` symlink skill directories into `.claude/skills/`
per CLAUDE.md, and those skills must be gated like any other. A *broken* symlink
is not skipped — it is discovered and then fails loudly on the missing SKILL.md.

Run with: python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -v
"""
import os
import re

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
SKILLS_DIR = os.path.join(REPO_ROOT, ".claude", "skills")

# Spec constants. Named rather than inlined so a mutation to any one of them is
# a single visible edit.
NAME_MAX_CHARS = 64
DESCRIPTION_MAX_CHARS = 1024
COMPATIBILITY_MAX_CHARS = 500
SKILL_MD_MAX_LINES = 500

NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")

# Directory names that are never skills even if they sit directly under
# `.claude/skills/`. Kept minimal on purpose: anything not listed here IS
# treated as a skill and must carry a SKILL.md, so a stray folder fails loudly
# instead of being silently skipped.
NON_SKILL_DIRS = {"__pycache__", ".pytest_cache"}


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

def discover_skill_dirs(root=SKILLS_DIR):
    """Every immediate subdirectory of `root`, symlinks included.

    Uses `os.scandir` at depth 1 only: `delivery-report/__pycache__` and
    `git-guardrails-claude-code/scripts` live one level *below* a skill and must
    never be mistaken for skills themselves.
    """
    if not os.path.isdir(root):
        return []
    found = []
    for entry in os.scandir(root):
        if entry.name.startswith(".") or entry.name in NON_SKILL_DIRS:
            continue
        # `is_dir()` follows symlinks; a broken symlink reports False for both
        # is_dir and is_file, so catch it explicitly rather than dropping it.
        if entry.is_dir() or (entry.is_symlink() and not entry.exists()):
            found.append(entry.path)
    return sorted(found)


SKILL_DIRS = discover_skill_dirs()
SKILL_IDS = [os.path.basename(p) for p in SKILL_DIRS]


# --------------------------------------------------------------------------
# Minimal stdlib frontmatter parser
# --------------------------------------------------------------------------

def parse_frontmatter(text):
    """Parse top-level scalar keys out of YAML frontmatter. Stdlib only.

    Returns a dict of top-level key -> string value. Raises ValueError when the
    file does not open with a `---` fence or the fence is never closed.

    Handles the cases the repo's skills actually use and the ones the edge-case
    checklist names:
      - values containing `:` or `#` (split on the FIRST colon only; no comment
        stripping, so a `#` inside a description stays part of the value)
      - block scalars (`>` / `|`), joined into one value so length is measured
        on the whole description, not its first line
      - nested maps such as `metadata:` — only column-0 keys are top-level, so
        `  author: x` is never mistaken for a top-level field
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("file does not begin with a `---` frontmatter fence")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        raise ValueError("frontmatter fence opened but never closed")

    body = lines[1:end]
    data = {}
    i = 0
    while i < len(body):
        line = body[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1] in (" ", "\t"):  # nested / continuation, not a top-level key
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value in (">", "|", ">-", "|-", ">+", "|+"):
            chunk = []
            while i < len(body) and (not body[i].strip() or body[i][:1] in (" ", "\t")):
                chunk.append(body[i].strip())
                i += 1
            value = " ".join(part for part in chunk if part)
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        data[key] = value
    return data


def read_skill_md(skill_dir):
    path = os.path.join(skill_dir, "SKILL.md")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def count_lines(text):
    """Line count that does not shift across the 500 boundary on a trailing
    newline: `"a\\n"` and `"a"` are both one line."""
    return len(text.splitlines())


# --------------------------------------------------------------------------
# AC9 — guard the discovery layer (first on purpose)
# --------------------------------------------------------------------------

def test_ac9_discovery_finds_at_least_one_skill():
    """An empty or mis-rooted glob must fail, not vacuously pass.

    Every other test in this module is parametrized over `SKILL_DIRS`. If that
    list is empty, pytest reports zero failures — a green suite that asserted
    nothing. This is the guard against that.
    """
    assert os.path.isdir(SKILLS_DIR), (
        "discovery root does not exist: %s" % SKILLS_DIR
    )
    assert len(SKILL_DIRS) > 0, (
        "discovered zero skill directories under %s — the conformance suite "
        "would pass vacuously" % SKILLS_DIR
    )


def test_ac9_discovery_includes_a_known_skill():
    """A root that exists but points somewhere wrong would still be non-empty.
    Pin one skill known to live under `.claude/skills/`."""
    assert "write-better-skill" in SKILL_IDS, (
        "known skill 'write-better-skill' not among discovered skills %s — "
        "discovery root %s is wrong" % (SKILL_IDS, SKILLS_DIR)
    )


def test_ac8_no_hardcoded_skill_list():
    """Discovery is filesystem-driven: re-running it against the real root
    reproduces the module-level list, and it returns [] for a nonexistent root
    rather than a baked-in constant."""
    assert discover_skill_dirs(SKILLS_DIR) == SKILL_DIRS
    assert discover_skill_dirs(os.path.join(SKILLS_DIR, "no-such-root")) == []


def test_discovery_ignores_nested_non_skill_dirs():
    """`delivery-report/__pycache__` and `git-guardrails-claude-code/scripts`
    sit one level below a skill and must not be discovered as skills."""
    for bad in ("__pycache__", "scripts", "references", "assets"):
        assert bad not in SKILL_IDS


# --------------------------------------------------------------------------
# AC7 — the five hard constraints, over every discovered skill
# --------------------------------------------------------------------------

@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_skill_md_exists(skill_dir):
    path = os.path.join(skill_dir, "SKILL.md")
    assert os.path.isfile(path), (
        "%s is a directory under .claude/skills/ with no SKILL.md — either it "
        "is not a skill and does not belong here, or it is a broken skill"
        % os.path.basename(skill_dir)
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_frontmatter_parses(skill_dir):
    try:
        parse_frontmatter(read_skill_md(skill_dir))
    except ValueError as exc:
        pytest.fail("%s/SKILL.md frontmatter: %s" % (os.path.basename(skill_dir), exc))


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_name_field_conforms(skill_dir):
    """Spec `name` field: 1-64 chars; unicode lowercase alphanumeric (a-z, 0-9)
    and hyphens only; no leading/trailing hyphen; no consecutive hyphens; must
    match the parent directory name."""
    dirname = os.path.basename(skill_dir)
    data = parse_frontmatter(read_skill_md(skill_dir))
    name = data.get("name")
    violations = []

    if not name:
        pytest.fail("%s/SKILL.md: `name` is required and missing/empty" % dirname)

    if not (1 <= len(name) <= NAME_MAX_CHARS):
        violations.append(
            "length %d is outside 1-%d" % (len(name), NAME_MAX_CHARS))
    if not NAME_PATTERN.match(name):
        violations.append(
            "contains characters outside lowercase a-z, 0-9 and `-` "
            "(uppercase is not allowed)")
    if name.startswith("-") or name.endswith("-"):
        violations.append("must not start or end with a hyphen")
    if "--" in name:
        violations.append("must not contain consecutive hyphens (`--`)")
    if name != dirname:
        violations.append(
            "must match the parent directory name (name=%r, directory=%r)"
            % (name, dirname))

    assert not violations, "%s/SKILL.md `name` violates the spec: %s" % (
        dirname, "; ".join(violations))


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_description_field_conforms(skill_dir):
    """Spec `description` field: required, non-empty, max 1024 characters."""
    dirname = os.path.basename(skill_dir)
    data = parse_frontmatter(read_skill_md(skill_dir))
    assert "description" in data, (
        "%s/SKILL.md: `description` is required and absent" % dirname)
    description = data["description"].strip()
    assert description, "%s/SKILL.md: `description` is present but empty" % dirname
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        "%s/SKILL.md: `description` is %d chars, spec max is %d"
        % (dirname, len(description), DESCRIPTION_MAX_CHARS))


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_skill_md_within_line_budget(skill_dir):
    """Progressive disclosure: keep the main SKILL.md under 500 lines."""
    dirname = os.path.basename(skill_dir)
    lines = count_lines(read_skill_md(skill_dir))
    assert lines <= SKILL_MD_MAX_LINES, (
        "%s/SKILL.md is %d lines, spec budget is %d — move detailed reference "
        "material into a separate file" % (dirname, lines, SKILL_MD_MAX_LINES))


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_compatibility_field_within_budget(skill_dir):
    """Optional `compatibility`: 1-500 characters if provided."""
    dirname = os.path.basename(skill_dir)
    data = parse_frontmatter(read_skill_md(skill_dir))
    if "compatibility" not in data:
        return
    value = data["compatibility"].strip()
    assert value, "%s/SKILL.md: `compatibility` is present but empty" % dirname
    assert len(value) <= COMPATIBILITY_MAX_CHARS, (
        "%s/SKILL.md: `compatibility` is %d chars, spec max is %d"
        % (dirname, len(value), COMPATIBILITY_MAX_CHARS))


# --------------------------------------------------------------------------
# Parser unit tests — the edge cases from the guide's checklist
# --------------------------------------------------------------------------

def test_parser_handles_colon_and_hash_in_value():
    data = parse_frontmatter(
        "---\nname: x\ndescription: Use when A: do B # not a comment\n---\nbody\n")
    assert data["description"] == "Use when A: do B # not a comment"


def test_parser_joins_block_scalar_description():
    text = (
        "---\n"
        "name: x\n"
        "description: >\n"
        "  first line\n"
        "  second line\n"
        "---\n"
    )
    assert parse_frontmatter(text)["description"] == "first line second line"


def test_parser_ignores_nested_map_keys():
    text = "---\nname: x\nmetadata:\n  name: not-the-skill-name\n---\n"
    assert parse_frontmatter(text)["name"] == "x"


def test_parser_rejects_missing_frontmatter():
    for text in ("# just a heading\n", "", "not a fence\n---\nname: x\n---\n"):
        with pytest.raises(ValueError):
            parse_frontmatter(text)


def test_parser_rejects_unclosed_frontmatter():
    with pytest.raises(ValueError):
        parse_frontmatter("---\nname: x\n")


def test_count_lines_is_trailing_newline_stable():
    body = "\n".join("l%d" % i for i in range(SKILL_MD_MAX_LINES))
    assert count_lines(body) == SKILL_MD_MAX_LINES
    assert count_lines(body + "\n") == SKILL_MD_MAX_LINES
    assert count_lines(body + "\nextra") == SKILL_MD_MAX_LINES + 1
