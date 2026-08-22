"""
T083 — drift test for site/index.html.

The site's roster content (agents, skills, hooks, step limit) must never be
hand-copied: every assertion here reads the source of truth at test time
(`.claude/agents/*.md`, `.claude/skills/`, `.claude/settings.json`,
`pre_agent_step_limit.py`) rather than a hardcoded list. Adding a skill or
agent without updating the page must fail this suite.

Site scope: PROJECT_SPEC_SITE.md. Never assert against README.md — that
document is documented-wrong for two of the facts checked here.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_PAGE = os.path.join(ROOT, "site", "index.html")
AGENTS_DIR = os.path.join(ROOT, ".claude", "agents")
SKILLS_DIR = os.path.join(ROOT, ".claude", "skills")
SETTINGS_PATH = os.path.join(ROOT, ".claude", "settings.json")
STEP_LIMIT_HOOK = os.path.join(ROOT, ".claude", "hooks", "pre_agent_step_limit.py")


def _page_text():
    with open(SITE_PAGE, encoding="utf-8") as f:
        return f.read()


def _skill_dirs():
    return sorted(
        name
        for name in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, name))
    )


def _agent_names():
    """Return {display_name: file_stem} for every agent file, in
    frontmatter-declaration order isn't required; a dict keyed on the
    `name:` value read straight out of each file's frontmatter."""
    names = {}
    for fname in os.listdir(AGENTS_DIR):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(AGENTS_DIR, fname), encoding="utf-8") as f:
            text = f.read()
        match = re.search(r"^name:\s*(\S+)\s*$", text, re.MULTILINE)
        assert match, f"{fname} has no `name:` frontmatter field"
        names[match.group(1)] = fname
    return names


def _hook_scripts():
    """Every hook script basename wired anywhere in settings.json's hooks
    tree, deduped."""
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        settings = json.load(f)
    basenames = set()
    for event_hooks in settings.get("hooks", {}).values():
        for entry in event_hooks:
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                match = re.search(r"([A-Za-z0-9_]+\.py)", command)
                if match:
                    basenames.add(match.group(1))
    return basenames


def _step_limit_from_source():
    with open(STEP_LIMIT_HOOK, encoding="utf-8") as f:
        text = f.read()
    match = re.search(
        r'STEP_LIMIT\s*=\s*int\(os\.environ\.get\("CLAUDE_STEP_LIMIT",\s*"(\d+)"\)\)',
        text,
    )
    assert match, "could not parse STEP_LIMIT default out of pre_agent_step_limit.py"
    return match.group(1)


def _word_present(text, word):
    """Exact-token presence — `code-review` must not satisfy an assertion
    meant for `compound-refresh`. Word boundaries around the whole
    hyphenated token, not a naive substring check."""
    return re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text) is not None


def test_every_skill_dir_appears_on_page():
    text = _page_text()
    missing = [name for name in _skill_dirs() if not _word_present(text, name)]
    assert not missing, f"skill(s) missing from page: {missing}"


def test_every_spawnable_agent_appears_with_subagent_type():
    text = _page_text()
    agents = _agent_names()
    assert "general-agent-template" in agents  # sanity: fixture is real
    spawnable = {n: f for n, f in agents.items() if n != "general-agent-template"}
    assert len(spawnable) == 4, f"expected 4 spawnable agents, found {sorted(spawnable)}"
    missing = [name for name in spawnable if not _word_present(text, name)]
    assert not missing, f"spawnable agent(s) missing from page: {missing}"


def test_base_template_marked_not_spawnable():
    text = _page_text()
    idx = text.find("general-agent-template")
    assert idx != -1, "general-agent-template not mentioned on page"
    window = text[max(0, idx - 300) : idx + 300].lower()
    assert "not" in window and "spawn" in window, (
        "general-agent-template must be explicitly labelled not spawnable "
        "near its mention on the page"
    )


def test_every_wired_hook_appears_in_hook_table():
    text = _page_text()
    hooks = _hook_scripts()
    assert hooks, "no hooks parsed out of settings.json — fixture broken"
    missing = [h for h in hooks if h not in text]
    assert not missing, f"hook script(s) missing from page: {missing}"


def test_step_limit_matches_source():
    text = _page_text()
    limit = _step_limit_from_source()
    assert _word_present(text, limit), (
        f"step limit {limit} (parsed from pre_agent_step_limit.py) not found on page"
    )


def test_move_to_review_hook_documented_as_inert():
    text = _page_text()
    idx = text.find("post_agent_move_to_review.py")
    assert idx != -1, "post_agent_move_to_review.py not mentioned on page"
    window = text[max(0, idx - 300) : idx + 300].lower()
    assert "inert" in window or ("does not move" in window or "doesn't move" in window), (
        "page must document post_agent_move_to_review.py as inert / not moving "
        "anything, per its own source docstring"
    )


def test_no_project_state_on_page():
    text = _page_text()
    assert not re.search(r"\bT\d{3}\b", text), "page must not contain a task ID"
    assert "KANBAN" not in text, "page must not mention KANBAN"
    assert "In Progress" not in text, "page must not mention In Progress"
    assert "Ready for Review" not in text, "page must not mention Ready for Review"


def test_no_external_assets():
    """AC1/AC8: zero asset requests. Resource ``src`` attributes and
    stylesheet ``<link href>`` values must never point at an external origin.
    Ordinary ``<a href>`` documentation links are navigation, not assets.

    T084 (carried over from T083's Stage 4 review): also cover CSS
    `url(...)`, `@import`, and `<img srcset>` — a future addition through
    any of those three channels would fetch over the network with only the
    original src=/href= check still green. The page has none of these
    today; this closes a latent gap, not a live bug."""
    text = _page_text()
    for tag_match in re.finditer(r"<([A-Za-z][A-Za-z0-9-]*)([^>]*)>", text):
        tag_name, attributes = tag_match.groups()
        for attr_match in re.finditer(r'(src|href)\s*=\s*"([^"]*)"', attributes):
            attribute, value = attr_match.groups()
            is_resource = attribute == "src" or (tag_name.lower() == "link" and attribute == "href")
            if is_resource:
                assert not re.match(r"^(https?:)?//", value), f"external asset reference: {value}"

    for url_match in re.finditer(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', text):
        value = url_match.group(1)
        assert not re.match(r"^(https?:)?//", value), f"external CSS url(): {value}"

    for import_match in re.finditer(r'@import\s+["\']([^"\']+)["\']', text):
        value = import_match.group(1)
        assert not re.match(r"^(https?:)?//", value), f"external @import: {value}"

    for srcset_match in re.finditer(r'srcset\s*=\s*"([^"]*)"', text):
        for candidate in srcset_match.group(1).split(","):
            url = candidate.strip().split(" ")[0]
            assert not re.match(r"^(https?:)?//", url), f"external srcset entry: {url}"


def test_canonical_repository_is_linked_on_page():
    text = _page_text()
    assert 'href="https://github.com/thunderkds/personal-agentic-claude"' in text
    assert "GitHub repository" in text


PACKS_DIR = os.path.join(ROOT, "packs")


def _pack_names():
    return sorted(
        name
        for name in os.listdir(PACKS_DIR)
        if os.path.isdir(os.path.join(PACKS_DIR, name))
    )


def test_every_pack_appears_on_page():
    """T087 AC1: every pack directory under packs/*/ must be named on the
    page. Reads the packs/ directory at test time, not a hardcoded list —
    same drift-proofing pattern as the skill/agent/hook assertions above."""
    text = _page_text()
    packs = _pack_names()
    assert packs, "no pack directories found under packs/ — fixture broken"
    missing = [name for name in packs if not _word_present(text, name)]
    assert not missing, f"pack(s) missing from page: {missing}"


# T087 AC7: topics the (pre-slim) README promises live on the site. Keywords
# are chosen to match page content, not README wording, so this test does
# not degenerate into comparing the README to itself.
README_PROMISED_TOPICS = {
    "packs": "pack",
    "update flow": "harness-lock",
    "options table": "SUPERVISOR_REPO",
    "repository layout": "Repository layout",
    "memory system": "Memory System",
    "fork install": "GITHUB_USERNAME",
    "brownfield install": "brownfield",
}


def test_readme_promised_topics_are_on_the_page():
    text = _page_text()
    missing = [
        topic
        for topic, keyword in README_PROMISED_TOPICS.items()
        if not _word_present(text, keyword)
    ]
    assert not missing, f"README-promised topic(s) missing from page: {missing}"
