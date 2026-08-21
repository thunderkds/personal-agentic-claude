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
    """AC1/AC8: zero network requests. src=/href= must never point at an
    external origin (http://, https://, or protocol-relative //). The
    install command's URL lives in visible text/code content, not in a
    src=/href= attribute, so it never trips this check.

    T084 (carried over from T083's Stage 4 review): also cover CSS
    `url(...)`, `@import`, and `<img srcset>` — a future addition through
    any of those three channels would fetch over the network with only the
    original src=/href= check still green. The page has none of these
    today; this closes a latent gap, not a live bug."""
    text = _page_text()
    for attr_match in re.finditer(r'(?:src|href)\s*=\s*"([^"]*)"', text):
        value = attr_match.group(1)
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


# ---------------------------------------------------------------------------
# T089 — navigation integrity. The page is now a navigable document with a
# sticky sidebar; a sidebar whose links rot is worse than no sidebar, and
# nothing else in this repo would catch that. AC2/AC3 are the load-bearing
# assertions: every nav link resolves, and every section is reachable.
# ---------------------------------------------------------------------------

TOKEN_AUDIT_TEST = os.path.join(
    ROOT, ".claude", "hooks", "tests", "test_token_audit_format.py"
)


def _nav_hrefs():
    """Every in-page anchor href inside the sidebar <nav> block."""
    text = _page_text()
    nav = re.search(r"<nav\b[^>]*>(.*?)</nav>", text, re.DOTALL)
    assert nav, "page has no <nav> element — the sidebar navigation is missing"
    return re.findall(r'href\s*=\s*"#([^"]+)"', nav.group(1))


def _top_level_section_ids():
    """ids of <section> elements that are direct children of <main>.

    Nesting is tracked explicitly so a future nested <section> inside a
    top-level one does not register as an orphan (Edge Case: AC3 needs a
    precise definition of "top-level")."""
    text = _page_text()
    main = re.search(r"<main\b[^>]*>(.*)</main>", text, re.DOTALL)
    assert main, "page has no <main> element — cannot identify top-level sections"
    ids, depth = [], 0
    for tag in re.finditer(r"<section\b([^>]*)>|</section>", main.group(1)):
        if tag.group(0).startswith("</"):
            depth -= 1
            continue
        if depth == 0:
            attrs = tag.group(1)
            id_match = re.search(r'id\s*=\s*"([^"]+)"', attrs)
            assert id_match, f"top-level <section{attrs}> has no id — AC3"
            ids.append(id_match.group(1))
        depth += 1
    return ids


def _element_ids():
    return set(re.findall(r'\bid\s*=\s*"([^"]+)"', _page_text()))


def test_every_nav_link_resolves_to_a_section_id():
    """AC2: no dead links. Every sidebar href="#x" must have an element
    with id="x" on the page."""
    present = _element_ids()
    hrefs = _nav_hrefs()
    assert hrefs, "sidebar <nav> contains no in-page links"
    dead = sorted({h for h in hrefs if h not in present})
    assert not dead, f"dead nav link(s) — no element with these id(s): {dead}"


def test_every_section_has_a_nav_link():
    """AC3: no orphan sections. Every top-level <section id=…> under <main>
    must be reachable from the sidebar."""
    linked = set(_nav_hrefs())
    sections = _top_level_section_ids()
    assert sections, "no top-level <section id=…> found under <main>"
    orphans = [s for s in sections if s not in linked]
    assert not orphans, f"section(s) with no nav link: {orphans}"


def test_all_scripts_are_inline():
    """AC9 / SC3: the page may execute script, but only inline script.
    Zero external requests remains absolute."""
    for script in re.finditer(r"<script\b([^>]*)>", _page_text()):
        assert not re.search(r"\bsrc\s*=", script.group(1)), (
            f"<script{script.group(1)}> loads an external file — "
            "all script must be inline"
        )


def _enforced_hot_tier_budget():
    with open(TOKEN_AUDIT_TEST, encoding="utf-8") as f:
        match = re.search(r"HOT_TIER_CHAR_BUDGET\s*=\s*([\d_]+)", f.read())
    assert match, "could not parse HOT_TIER_CHAR_BUDGET out of test_token_audit_format.py"
    return int(match.group(1).replace("_", ""))


def test_memory_cap_matches_enforced_budget():
    """AC8: the memory cap published on the page must equal the enforced
    HOT_TIER_CHAR_BUDGET, read from the enforcing test at test time — not a
    hardcoded 45,000. Publishing a stale figure (50,000) is exactly the
    defect this replaces."""
    budget = _enforced_hot_tier_budget()
    text = _page_text()
    assert _word_present(text, f"{budget:,}") or _word_present(text, str(budget)), (
        f"page does not publish the enforced hot-tier budget {budget:,}"
    )
    stale = [
        n
        for n in re.findall(r"\b\d{2},\d{3}\b(?=\s*character)", text)
        if int(n.replace(",", "")) != budget
    ]
    assert not stale, (
        f"page publishes character-cap figure(s) {stale} that disagree with the "
        f"enforced HOT_TIER_CHAR_BUDGET of {budget:,}"
    )
