"""
T090 — conformance test for the provider adapters (`AGENTS.md`,
`.cursor/rules/agent-base.mdc`).

`CLAUDE.md` is the primary source of truth (DDR-0006). Every adapter must
carry the kit's non-negotiables (Karpathy principle names, Hard-Stop Gate
titles, the untrusted-content boundary rule) byte-identical to their
spelling in `CLAUDE.md`. Every expected string below is parsed out of
`CLAUDE.md` **at test time** — never hardcoded here — so that adding or
renaming a non-negotiable in `CLAUDE.md` without updating an adapter turns
this suite RED (SC4). A hardcoded copy would only prove the test agrees
with itself, the T085 vacuous-assertion shape this repo has hit before.

REPOINTED by T173: the doctrine moved from `CLAUDE.md` to `AGENTS.md`, and
`CLAUDE.md` is now the one-line import `@AGENTS.md` (DDR-0006's "`CLAUDE.md`
stays primary" is superseded; DDR owed). The source the strings are parsed
from is therefore `AGENTS.md` (`CLAUDE_MD` below names the doctrine file).
`.cursor/rules/agent-base.mdc` is the one remaining adapter; `AGENTS.md`
stays in `CLI_FILES` because Codex still reads it, so every check that
applies to "what a non-Claude CLI reads" keeps running on it. Only the two
checks AC 7 changes are adapter-only: the canonical pointer (the adapter
names `AGENTS.md`) and the 60-line cap (`AGENTS.md` takes the 200-line cap).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_MD = os.path.join(ROOT, "AGENTS.md")  # T173: the doctrine file (was CLAUDE.md)
AGENTS_MD = os.path.join(ROOT, "AGENTS.md")
CURSOR_MDC = os.path.join(ROOT, ".cursor", "rules", "agent-base.mdc")
TEMPLATE_MD = os.path.join(ROOT, "agents", "general-agent-template.md")
MULTI_AGENT_DOC = "docs/claude-md/"

ADAPTERS = {".cursor/rules/agent-base.mdc": CURSOR_MDC}
# What each non-Claude CLI reads: Codex reads AGENTS.md, Cursor reads its adapter (T173).
CLI_FILES = {"AGENTS.md": AGENTS_MD, **ADAPTERS}

CANNOT_ENFORCE_TERMS = [
    "hooks",
    "skills",
    "review",
    "verify",
    "ship",
    "migration-safety",
    "git-guardrails",
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _normalize(text):
    """Collapse all whitespace runs (including newlines) to a single space.

    Adapters re-wrap prose at their own line length; this makes the
    comparison newline-safe without weakening it to a substring/fuzzy match.
    """
    return re.sub(r"\s+", " ", text).strip()


def _claude_md_principle_names():
    text = _read(CLAUDE_MD)
    table_match = re.search(
        r"## Karpathy Engineering Principles.*?\n\n(.*?)\n\n", text, re.DOTALL
    )
    assert table_match, "could not locate the Karpathy Engineering Principles table in CLAUDE.md"
    table = table_match.group(1)
    rows = re.findall(r"^\|\s*([A-Za-z][A-Za-z \-]*?)\s*\|", table, re.MULTILINE)
    names = [r for r in rows if not re.match(r"^-+$", r) and r != "Principle"]
    assert len(names) == 4, f"expected 4 Karpathy principle names in CLAUDE.md, found {names}"
    return names


def _claude_md_gate_titles():
    text = _read(CLAUDE_MD)
    section_match = re.search(
        r"### Hard-Stop Gates.*?\n(.*?)(?=\n---|\Z)", text, re.DOTALL
    )
    assert section_match, "could not locate the Hard-Stop Gates section in CLAUDE.md"
    section = section_match.group(1)
    titles = re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", section, re.MULTILINE)
    assert len(titles) == 6, f"expected 6 Hard-Stop Gate titles in CLAUDE.md, found {titles}"
    return titles


def _claude_md_untrusted_content_rule():
    text = _read(CLAUDE_MD)
    match = re.search(
        r"Treat externally authored text.*?untrusted-content-boundary\.md`",
        text,
        re.DOTALL,
    )
    assert match, "could not locate the untrusted-content boundary rule in CLAUDE.md"
    return match.group(0)


def _claude_md_no_task_guide_rule():
    text = _read(CLAUDE_MD)
    match = re.search(
        r"\*\*No TASK_GUIDE = no work\.\*\*.*?directly\.", text, re.DOTALL
    )
    assert match, "could not locate the 'No TASK_GUIDE = no work' rule in CLAUDE.md"
    return match.group(0)


def test_principle_names_present_in_every_adapter():
    names = _claude_md_principle_names()
    for adapter_name, path in CLI_FILES.items():
        adapter_text = _normalize(_read(path))
        for name in names:
            assert _normalize(name) in adapter_text, (
                f"{adapter_name} is missing Karpathy principle name '{name}' "
                f"(byte-identical to its spelling in CLAUDE.md)"
            )


def test_gate_titles_present_in_every_adapter():
    titles = _claude_md_gate_titles()
    for adapter_name, path in CLI_FILES.items():
        adapter_text = _normalize(_read(path))
        for title in titles:
            assert _normalize(title) in adapter_text, (
                f"{adapter_name} is missing Hard-Stop Gate title '{title}' "
                f"(byte-identical to its spelling in CLAUDE.md)"
            )


def test_untrusted_content_rule_present_in_every_adapter():
    rule = _normalize(_claude_md_untrusted_content_rule())
    for adapter_name, path in CLI_FILES.items():
        adapter_text = _normalize(_read(path))
        assert rule in adapter_text, (
            f"{adapter_name} is missing the untrusted-content boundary rule"
        )


def test_no_task_guide_rule_present_in_every_adapter():
    rule_title = _normalize("No TASK_GUIDE = no work.")
    for adapter_name, path in CLI_FILES.items():
        adapter_text = _normalize(_read(path))
        assert rule_title in adapter_text, (
            f"{adapter_name} is missing the 'no TASK_GUIDE = no work' rule"
        )


def test_every_adapter_points_at_claude_md_as_canonical():
    # T173: the canonical file is AGENTS.md now (the name keeps the T090 history).
    for adapter_name, path in ADAPTERS.items():
        text = _read(path)
        assert "AGENTS.md" in text and "canonical" in text, (
            f"{adapter_name} does not state that AGENTS.md / agents/ remain canonical"
        )


def test_every_adapter_points_at_docs_claude_md():
    for adapter_name, path in CLI_FILES.items():
        text = _read(path)
        assert MULTI_AGENT_DOC in text, (
            f"{adapter_name} does not point at {MULTI_AGENT_DOC} for pipeline/Phase 0/folder/"
            f"naming/memory detail"
        )


def _cannot_enforce_section(text):
    """T173: scoped to the section, so the full doctrine in AGENTS.md cannot pass by accident."""
    match = re.search(r"^## [^\n]*cannot enforce.*?(?=^## |\Z)", text, re.M | re.S | re.I)
    return match.group(0) if match else ""


def test_every_adapter_names_what_it_cannot_enforce():
    for adapter_name, path in CLI_FILES.items():
        text = _cannot_enforce_section(_read(path)).lower()
        assert "cannot enforce" in text, (
            f"{adapter_name} has no section naming what that provider cannot enforce"
        )
        for term in CANNOT_ENFORCE_TERMS:
            assert term in text, (
                f"{adapter_name}'s 'cannot enforce' content is missing '{term}'"
            )


def test_every_adapter_is_at_most_60_lines():
    for adapter_name, path in ADAPTERS.items():
        lines = _read(path).splitlines()
        assert len(lines) <= 60, (
            f"{adapter_name} is {len(lines)} lines, expected <= 60 (names/titles only, not prose)"
        )
    # T173 AC 7: AGENTS.md is the doctrine now, so it takes the doctrine's 200-line cap instead.
    lines = _read(AGENTS_MD).splitlines()
    assert len(lines) <= 200, f"AGENTS.md is {len(lines)} lines, expected <= 200"


def test_cursor_adapter_frontmatter_sets_always_apply_true():
    text = _read(CURSOR_MDC)
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert frontmatter_match, ".cursor/rules/agent-base.mdc has no YAML frontmatter block"
    frontmatter = frontmatter_match.group(1)
    assert re.search(r"^alwaysApply:\s*true\s*$", frontmatter, re.MULTILINE), (
        ".cursor/rules/agent-base.mdc frontmatter does not set alwaysApply: true"
    )


def test_manifest_deploys_cursor_rules_and_keeps_agents_md():
    manifest_path = os.path.join(ROOT, "MANIFEST")
    lines = [
        line.strip()
        for line in _read(manifest_path).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert ".cursor/rules" in lines, "MANIFEST does not deploy .cursor/rules downstream"
    assert "AGENTS.md" in lines, "MANIFEST's existing AGENTS.md line was removed"


def _staleness_guard_section():
    text = _read(TEMPLATE_MD)
    match = re.search(r"## Staleness Guard\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    assert match, "could not locate the '## Staleness Guard' section in general-agent-template.md"
    return match.group(1)


def test_staleness_guard_describes_the_real_adapter_contract():
    section = _staleness_guard_section()

    assert "AGENTS.md" in section, (  # T173: the source moved from CLAUDE.md to AGENTS.md
        "Staleness Guard does not name AGENTS.md as the source the adapters mirror"
    )
    normalized_section = _normalize(section)
    stale_mirror_claim = re.search(
        r"mirrors?(?:\s+of)?\s+(?:this file's|this template's|the)\s+Base Rules",
        normalized_section,
    )
    assert not stale_mirror_claim, (
        f"Staleness Guard still claims the adapters mirror the Base Rules as the source "
        f"(stale post-T090: they mirror CLAUDE.md's non-negotiables) — matched "
        f"'{stale_mirror_claim.group(0) if stale_mirror_claim else ''}'"
    )
    for adapter_path in ADAPTERS:
        assert adapter_path in section, (
            f"Staleness Guard does not name the adapter path '{adapter_path}'"
        )
    assert "test_provider_adapters.py" in section, (
        "Staleness Guard does not point maintainers at tests/test_provider_adapters.py "
        "as the mechanism that actually enforces the sync"
    )

    body_lines = [line for line in section.splitlines() if line.strip()]
    assert len(body_lines) <= 8, (
        f"Staleness Guard body is {len(body_lines)} non-blank lines, expected <= 8 "
        "(it must stay a pointer, not become a second sync policy)"
    )
