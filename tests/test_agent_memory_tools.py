"""T195 — the four base sub-agents can call easy-memory and no longer read all of memory/MEMORY.md.

For each agent in the base team:
1. the single-line `tools:` frontmatter lists `mcp__easy-memory__memory_search` and
   `mcp__easy-memory__memory_read`;
2. the guide carries one memory rule (search once with the task goal, open a note only if it fits,
   treat notes as possibly out of date, skip without stopping if the tool is missing);
3. the Startup step that named `memory/MEMORY.md` now points to the spawn-prompt slice and reads the
   whole file only when the work reaches something the slice does not cover;
4. negative: the other Startup steps (PROJECT_SPEC, TASK_GUIDE, general template, codebase-map) stay.

Stdlib-only parsing, as in `tests/test_agent_frontmatter.py`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
BASE_AGENTS = ("common-infrastructure", "backend", "frontend", "qa")
MCP_TOOLS = ("mcp__easy-memory__memory_search", "mcp__easy-memory__memory_read")
EXISTING_TOOLS = {
    "common-infrastructure": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    "backend": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    "frontend": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    "qa": ["Read", "Write", "Edit", "Grep", "Glob", "Bash"],
}


def _text(name: str) -> str:
    return (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _tools(name: str) -> list[str]:
    lines = _text(name).splitlines()
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    matches = [l for l in lines[1:end] if l.startswith("tools:")]
    assert len(matches) == 1, f"{name}: expected one single-line tools: entry, got {matches}"
    return [t.strip() for t in matches[0].split(":", 1)[1].split(",")]


def _startup(name: str) -> str:
    """The text of the Mandatory Startup Sequence section, up to the next `## ` heading."""
    text = _text(name)
    m = re.search(r"^## Mandatory Startup Sequence\n(.*?)(?=^## )", text, re.S | re.M)
    assert m, f"{name}: no Mandatory Startup Sequence section"
    return m.group(1)


@pytest.mark.parametrize("name", BASE_AGENTS)
def test_tools_line_lists_both_memory_tools(name):
    tools = _tools(name)
    for tool in MCP_TOOLS:
        assert tool in tools, f"agents/{name}.md: tools: line does not list {tool}"
    # Negative: the tools the agent already had are all still there.
    for tool in EXISTING_TOOLS[name]:
        assert tool in tools, f"agents/{name}.md: tools: line lost {tool}"


@pytest.mark.parametrize("name", BASE_AGENTS)
def test_memory_rule_present(name):
    startup = _startup(name)
    assert "memory_search" in startup, f"agents/{name}.md: Startup has no memory_search rule"
    assert "memory_read" in startup, f"agents/{name}.md: Startup has no memory_read rule"
    low = startup.lower()
    assert "task goal" in low, f"agents/{name}.md: rule does not say to search with the task goal"
    assert "out of date" in low, f"agents/{name}.md: rule does not warn that notes may be out of date"
    assert "re-check" in low, f"agents/{name}.md: rule does not say to re-check changed files"
    assert "skip" in low, f"agents/{name}.md: rule does not say to skip when the tool is missing"


@pytest.mark.parametrize("name", BASE_AGENTS)
def test_memory_md_step_uses_the_slice(name):
    startup = _startup(name)
    assert "memory-slice" in startup, f"agents/{name}.md: Startup does not name the spawn-prompt slice"
    assert "yourself" not in startup, (
        f"agents/{name}.md: Startup still says to read memory/MEMORY.md yourself"
    )
    assert "only if" in startup.lower(), (
        f"agents/{name}.md: Startup does not limit the full read to what the slice does not cover"
    )


@pytest.mark.parametrize("name", BASE_AGENTS)
def test_other_startup_steps_kept(name):
    startup = _startup(name)
    for needle in (
        "`PROJECT_SPEC.md`",
        "`tasks/TASK_GUIDE_Txxx.md`",
        "`templates/general-agent-template.md`",
        "`memory/codebase-map.md`",
        "Karpathy Engineering Principles",
        "stop and notify the Supervisor",
    ):
        assert needle in startup, f"agents/{name}.md: Startup lost {needle}"
