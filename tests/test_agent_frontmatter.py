"""T183 — every spawnable subagent definition carries the frontmatter the Claude Academy
"Creating a subagent" lesson names: `name`, a single-line trigger-style `description`, `tools`,
`model` and `color`.

Claude Code registers every `.md` under `.claude/agents` (a symlink onto `agents/`) as an agent
type. So `agents/` must hold only spawnable role agents: a file there without these keys — such as
the shared base template, which now lives at `templates/general-agent-template.md` — fails here.

Pack agents (`packs/*/agents/*.md`) are checked too: activation copies them into `agents/`.

Stdlib-only parsing, as in `tests/test_site_content.py`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
TEMPLATE = ROOT / "templates" / "general-agent-template.md"

REQUIRED_KEYS = ("name", "description", "tools", "model", "color")
ALLOWED_COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
BASE_COLORS = {
    "common-infrastructure": "orange",
    "backend-developer": "blue",
    "frontend-developer": "purple",
    "qa-expert": "green",
}


def _agent_files() -> list[Path]:
    return sorted(AGENTS_DIR.glob("*.md")) + sorted(ROOT.glob("packs/*/agents/*.md"))


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    """Return ({key: raw value}, raw frontmatter lines) for the leading `---` block."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{_rel(path)}: no frontmatter (first line is not ---)"
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        pytest.fail(f"{_rel(path)}: frontmatter is not closed by ---")
    block = lines[1:end]
    keys: dict[str, str] = {}
    for line in block:
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            keys[m.group(1)] = m.group(2).strip()
    return keys, block


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


FILES = _agent_files()


def test_agent_files_found():
    """Anti-vacuity: the globs must find the base team and at least one pack agent."""
    assert len(list(AGENTS_DIR.glob("*.md"))) >= 4, "agents/ glob found fewer than 4 files"
    assert list(ROOT.glob("packs/*/agents/*.md")), "packs/*/agents/*.md glob found nothing"


@pytest.mark.parametrize("path", FILES, ids=_rel)
def test_required_keys_present(path):
    keys, _ = _frontmatter(path)
    missing = [k for k in REQUIRED_KEYS if not keys.get(k)]
    assert not missing, f"{_rel(path)}: frontmatter missing key(s) {missing}"


@pytest.mark.parametrize("path", FILES, ids=_rel)
def test_description_is_single_line_trigger(path):
    keys, block = _frontmatter(path)
    raw = keys.get("description", "")
    assert raw, f"{_rel(path)}: no description"
    assert raw not in ("|", ">", "|-", ">-"), f"{_rel(path)}: description is a block scalar, not one line"
    idx = next(i for i, l in enumerate(block) if l.startswith("description:"))
    if idx + 1 < len(block):
        assert not block[idx + 1].startswith((" ", "\t")), (
            f"{_rel(path)}: description continues on the next line — it must be a single line"
        )
    text = _unquote(raw)
    assert text.startswith(("Use when", "Use for")), (
        f"{_rel(path)}: description must say when to delegate (start with 'Use when' or 'Use for'), "
        f"got: {text[:60]!r}"
    )
    assert "proactively" not in text.lower(), (
        f"{_rel(path)}: description must not say 'proactively' — spawns go through the Supervisor"
    )


@pytest.mark.parametrize("path", FILES, ids=_rel)
def test_color_in_allowed_set(path):
    keys, _ = _frontmatter(path)
    color = _unquote(keys.get("color", ""))
    assert color in ALLOWED_COLORS, (
        f"{_rel(path)}: color {color!r} not in {sorted(ALLOWED_COLORS)}"
    )


def test_names_unique():
    seen: dict[str, str] = {}
    dupes = []
    for path in FILES:
        name = _unquote(_frontmatter(path)[0].get("name", ""))
        if name in seen:
            dupes.append(f"{name}: {seen[name]} and {_rel(path)}")
        seen[name] = _rel(path)
    assert not dupes, f"duplicate agent name(s): {dupes}"


def test_base_team_colors():
    by_name = {}
    for path in sorted(AGENTS_DIR.glob("*.md")):
        keys, _ = _frontmatter(path)
        by_name[_unquote(keys.get("name", ""))] = _unquote(keys.get("color", ""))
    got = {n: by_name.get(n) for n in BASE_COLORS}
    assert got == BASE_COLORS, f"base team colours {got} != expected {BASE_COLORS}"
    assert len(set(got.values())) == len(BASE_COLORS), f"base team colours not distinct: {got}"


def test_template_lives_outside_agents_dir():
    """The base template is not a spawnable agent type, so it must not sit in agents/."""
    assert not (AGENTS_DIR / "general-agent-template.md").exists(), (
        "agents/general-agent-template.md exists — Claude Code would register it as an agent type; "
        "it belongs at templates/general-agent-template.md"
    )
    assert TEMPLATE.is_file(), "templates/general-agent-template.md is missing"
