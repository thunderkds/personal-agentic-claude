"""
T083 — drift test for site/index.html.

The site's roster content (agents, skills, hooks, step limit) must never be
hand-copied: every assertion here reads the source of truth at test time
(`agents/*.md`, `skills/`, `.claude/settings.json`,
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
AGENTS_DIR = os.path.join(ROOT, "agents")
SKILLS_DIR = os.path.join(ROOT, "skills")
SETTINGS_PATH = os.path.join(ROOT, ".claude", "settings.json")
STEP_LIMIT_HOOK = os.path.join(ROOT, ".claude", "hooks", "pre_agent_step_limit.py")


def _raw_page_text():
    with open(SITE_PAGE, encoding="utf-8") as f:
        return f.read()


def _page_text():
    # <wbr> only offers line-break points inside long code tokens (T167); it is not content.
    return _raw_page_text().replace("<wbr>", "")


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
    # T183: the base template lives in templates/, so every agents/*.md is a spawnable role.
    assert "general-agent-template" not in agents, "the base template is back in agents/"
    spawnable = agents
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


# ---- T183 AC 8: role cards show the agent's frontmatter colour and trigger ----

def _agent_frontmatter(fname):
    """{key: unquoted value} for one agents/*.md frontmatter block."""
    with open(os.path.join(AGENTS_DIR, fname), encoding="utf-8") as f:
        block = f.read().split("\n---\n", 1)[0]
    keys = {}
    for line in block.splitlines():
        m = re.match(r"^([a-z]+):\s*(.*)$", line)
        if m:
            value = m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            keys[m.group(1)] = value
    return keys


def _trigger(description):
    """The "Use when ..." trigger: the description's first sentence."""
    return re.split(r"(?<=\.)\s", description, maxsplit=1)[0]


def _agent_card(name):
    """The <div class="agent-card"> block whose .name is `name`, or None."""
    m = re.search(r'<section id="agent-roles">(.*?)</section>', _page_text(), re.DOTALL)
    assert m, 'page has no <section id="agent-roles">'
    for card in re.findall(r'<div class="agent-card">(.*?)\n</div>', m.group(1), re.DOTALL):
        if re.search(rf'<div class="name">{re.escape(name)}</div>', card):
            return card
    return None


def test_role_cards_show_frontmatter_colour_and_trigger():
    import html as _h
    agents = _agent_names()
    assert len(agents) == 4, f"expected 4 role agents, found {sorted(agents)}"
    for name, fname in sorted(agents.items()):
        fm = _agent_frontmatter(fname)
        card = _agent_card(name)
        assert card, f"no agent card for {name}"
        swatch = re.search(r'<span class="swatch" data-color="([a-z]+)"></span>\s*([a-z]+)', card)
        assert swatch, f"{name} card has no colour swatch + label"
        assert swatch.groups() == (fm["color"], fm["color"]), (
            f"{name} card colour {swatch.groups()} drifted from {fname} color: {fm['color']}"
        )
        trig = re.search(r'<p class="trigger">(.*?)</p>', card, re.DOTALL)
        assert trig, f"{name} card has no trigger line"
        shown = " ".join(_h.unescape(re.sub(r"<[^>]+>", "", trig.group(1))).split())
        assert shown == _trigger(fm["description"]), (
            f"{name} card trigger drifted from {fname}:\n  page: {shown!r}\n  file: "
            f"{_trigger(fm['description'])!r}"
        )
        assert shown.startswith("Use when"), f"{name} trigger does not start with 'Use when'"


def test_every_swatch_colour_has_a_css_rule():
    css = re.search(r"<style>(.*?)</style>", _page_text(), re.DOTALL).group(1)
    used = set(re.findall(r'<span class="swatch" data-color="([a-z]+)">', _page_text()))
    assert used, "no swatches on the page"
    missing = [c for c in sorted(used) if f'.swatch[data-color="{c}"]' not in css]
    assert not missing, f"swatch colour(s) with no CSS rule: {missing}"


def test_template_card_has_no_colour():
    card = _agent_card("general-agent-template")
    assert card, "general-agent-template card is missing"
    assert "swatch" not in card and "trigger" not in card, "the template is not an agent: no colour"
    assert "not directly spawnable" in card


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
    "options table": "Environment variable",  # T115: SUPERVISOR_REPO row removed (undocumented seam)
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


# ---------------------------------------------------------------------------
# T090 AC14 — the Providers section must stay in sync with the adapter files
# that actually exist on disk. Both directions are checked: an adapter file
# added on disk must be named on the page, and a path named on the page must
# still exist on disk — so renaming or removing an adapter turns this RED
# without a hardcoded copy of either list.
# ---------------------------------------------------------------------------

CURSOR_RULES_DIR = os.path.join(ROOT, ".cursor", "rules")


def _adapter_paths_on_disk():
    """Provider adapter file paths (repo-relative) that exist right now."""
    paths = []
    if os.path.isfile(os.path.join(ROOT, "AGENTS.md")):
        paths.append("AGENTS.md")
    if os.path.isdir(CURSOR_RULES_DIR):
        for fname in sorted(os.listdir(CURSOR_RULES_DIR)):
            if fname.endswith(".mdc"):
                paths.append(f".cursor/rules/{fname}")
    return paths


def _providers_section_body():
    text = _page_text()
    section = re.search(r'<section id="providers">(.*?)</section>', text, re.DOTALL)
    assert section, "page has no providers section — AC12"
    return section.group(1)


def _adapter_paths_mentioned_on_page(body):
    """Adapter-shaped paths (AGENTS.md or .cursor/rules/*) named in <code>
    tags inside the Providers section."""
    coded = re.findall(r"<code>([^<]+\.(?:md|mdc))</code>", body)
    return [p for p in coded if p == "AGENTS.md" or p.startswith(".cursor/rules/")]


def test_providers_section_lists_every_adapter_on_disk():
    body = _providers_section_body()
    on_disk = _adapter_paths_on_disk()
    assert on_disk, "no provider adapter files found on disk — fixture broken"
    missing = [p for p in on_disk if p not in body]
    assert not missing, f"adapter file(s) on disk missing from Providers section: {missing}"


def test_providers_section_names_no_dead_adapter_path():
    body = _providers_section_body()
    mentioned = _adapter_paths_mentioned_on_page(body)
    assert mentioned, "Providers section names no adapter path — fixture broken"
    dead = [p for p in mentioned if not os.path.isfile(os.path.join(ROOT, p))]
    assert not dead, f"Providers section names adapter path(s) no longer on disk: {dead}"


# ---------------------------------------------------------------------------
# T101 — drift tests for the four facts that went stale after T096 (canon
# relocation, DDR-0007) and T097 (per-harness projection). Each reads its
# source of truth at test time rather than a hardcoded copy, per the pattern
# in test_every_wired_hook_appears_in_hook_table.
# ---------------------------------------------------------------------------

HARNESS_FETCH_LIB = os.path.join(ROOT, "lib", "harness-fetch.sh")
SETUP_SH = os.path.join(ROOT, "setup.sh")


def _layout_section_body():
    text = _page_text()
    section = re.search(r'<section id="repository-layout">(.*?)</section>', text, re.DOTALL)
    assert section, "page has no repository-layout section"
    return section.group(1)


def test_layout_table_names_canon_root_and_relative_symlinks():
    """AC1/AC2: T096/DDR-0007 moved skills/ and agents/ to plain root as canon,
    with .claude/{skills,agents} as committed *relative* symlinks onto them
    (docs/ddr/0007-canonical-skills-and-agents-at-plain-root.md,
    docs/claude-md/folder-structure.md). The layout table must say so."""
    body = _layout_section_body()
    assert _word_present(body, "symlink"), (
        "Repository layout table does not mention symlink — .claude/skills and "
        "«.claude/agents» are relative symlinks onto plain-root canon (DDR-0007), not real dirs"
    )
    for canon_dir in ("skills/", "agents/"):
        assert re.search(
            r"<tr><td\b[^>]*><code>" + re.escape(canon_dir) + r"</code></td>", body
        ), f"Repository layout table has no dedicated row for canon root path {canon_dir}"


def test_install_section_names_every_cli_and_options_table_has_no_flags():
    """T115 (was T097 AC3's --harness row): setup.sh takes no options, so the
    Options table documents no flag; the CLIs are chosen from a menu, and the
    #install section names each one setup.sh's VALID_HARNESSES offers, in the
    user's words (ADR-0002: "CLI", never "harness")."""
    with open(SETUP_SH, encoding="utf-8") as f:
        setup_text = f.read()
    match = re.search(r'^VALID_HARNESSES="([^"]+)"', setup_text, re.MULTILINE)
    assert match, "could not parse VALID_HARNESSES out of setup.sh"
    valid_harnesses = match.group(1).split()
    assert valid_harnesses, "VALID_HARNESSES parsed empty — fixture broken"
    user_names = {"claude": "Claude Code", "codex": "Codex"}

    text = _page_text()
    options_section = re.search(r'<section id="options">(.*?)</section>', text, re.DOTALL)
    assert options_section, "page has no options section"
    assert not re.search(r"<code>--", options_section.group(1)), "Options table still lists a flag"

    install = re.search(r'<section id="install">(.*?)</section>', text, re.DOTALL)
    assert install, "page has no install section"
    for harness in valid_harnesses:
        assert harness in user_names, f"no user-facing name for CLI {harness!r} — add it here"
        assert user_names[harness] in install.group(1), (
            f"#install does not name the CLI {user_names[harness]!r} the menu offers"
        )


def _skills_over_codex_cap(cap):
    over = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if os.path.isfile(skill_md) and os.path.getsize(skill_md) > cap:
            over.append(name)
    return over


# ---------------------------------------------------------------------------
# T102 AC4/AC5 — the footer's drift-tested-against sentence must name the
# directories AGENTS_DIR/SKILLS_DIR actually resolve to, derived at test time
# (not a hardcoded "agents/"/"skills/" literal) so it re-trips if the canon
# moves again — same M3 pattern as test_step_limit_matches_source.
# ---------------------------------------------------------------------------


def _footer_body():
    text = _page_text()
    footer = re.search(r"<footer\b[^>]*>(.*?)</footer>", text, re.DOTALL)
    assert footer, "page has no <footer> element"
    return footer.group(1)


def test_footer_names_the_directories_it_is_actually_drift_tested_against():
    body = _footer_body()
    agents_rel = os.path.relpath(AGENTS_DIR, ROOT) + "/"
    skills_rel = os.path.relpath(SKILLS_DIR, ROOT) + "/"
    for expected in (agents_rel, skills_rel):
        assert f"<code>{expected}</code>" in body, (
            f"footer does not name the live {expected} directory "
            f"(derived from AGENTS_DIR/SKILLS_DIR's path relative to ROOT at test time)"
        )


def test_providers_section_names_codex_skill_cap_and_skipped_skills():
    """AC4/AC5: T097 gave Codex real skill-by-name execution with an 8 KB
    per-skill body cap (lib/harness-fetch.sh:harness_skill_body_cap), and the
    Providers section must no longer claim non-Claude providers get zero
    Skill tooling. Cap value and skip list are both derived from source at
    test time so a future skill crossing the cap re-trips this."""
    with open(HARNESS_FETCH_LIB, encoding="utf-8") as f:
        lib_text = f.read()
    match = re.search(r"codex\)\s*printf '(\d+)'", lib_text)
    assert match, "could not parse the Codex skill-body cap out of lib/harness-fetch.sh"
    cap_bytes = int(match.group(1))
    cap_kb = cap_bytes // 1024

    body = _providers_section_body()
    assert re.search(rf"{cap_kb}\s*KB", body), (
        f"Providers section does not name the {cap_kb} KB Codex skill-body cap "
        f"as an adjacent number+unit"
    )

    # AC5 (structural): the "cannot enforce" list must no longer pin
    # <code>Skill</code> as unenforceable — T097 gave Codex real skill-by-name
    # execution — while still pinning <code>Agent</code>, since the Agent spawn
    # tool genuinely does stay Claude-only. Asserting on the list's structure,
    # not on a prose literal the stale page never actually contained.
    enforce_para = re.search(
        r'<p class="lead">\s*What a non-Claude provider.*?</p>', body, re.DOTALL
    )
    assert enforce_para, (
        "Providers section has no 'What a non-Claude provider ... cannot enforce' paragraph"
    )
    enforce_text = enforce_para.group(0)
    assert "<code>Skill</code>" not in enforce_text, (
        "Providers 'cannot enforce' list still names <code>Skill</code> as unenforceable — "
        "stale post-T097 (Codex executes kit skills by name)"
    )
    assert "<code>Agent</code>" in enforce_text, (
        "Providers 'cannot enforce' list must still name <code>Agent</code> — the Agent "
        "spawn tool remains Claude-only"
    )

    skipped = _skills_over_codex_cap(cap_bytes)
    assert skipped, "no skill exceeds the Codex cap on disk — fixture broken"
    missing = [name for name in skipped if not _word_present(body, name)]
    assert not missing, (
        f"Providers section does not name skill(s) skipped for exceeding the Codex cap: {missing}"
    )


# ---------------------------------------------------------------------------
# T104 — the page must name the release it actually ships with. The expected
# version is parsed from RUNBOOK.md's Release Log table at test time (the
# newest/last data row), never hardcoded — see M1 in TASK_GUIDE_T104.md.
# ---------------------------------------------------------------------------

RUNBOOK_PATH = os.path.join(ROOT, "RUNBOOK.md")


def _newest_runbook_version():
    with open(RUNBOOK_PATH, encoding="utf-8") as f:
        text = f.read()
    section = re.search(r"## Release Log(.*?)(?=\n## |\Z)", text, re.DOTALL)
    assert section, "RUNBOOK.md has no '## Release Log' section"
    rows = re.findall(r"^\|\s*(v\d+\.\d+\.\d+)\s*\|", section.group(1), re.MULTILINE)
    assert rows, "no version rows found in RUNBOOK.md's Release Log table"
    return rows[-1]


def test_site_names_the_version_it_actually_ships_with():
    version = _newest_runbook_version()
    text = _page_text()
    assert f"supervisor kit &middot; {version}" in text, (
        f"sidebar does not name the shipping version {version} (from RUNBOOK.md's "
        f"Release Log, newest row)"
    )
    assert f"personal-agentic-claude — {version} release" in text, (
        f"footer does not name the shipping version {version} (from RUNBOOK.md's "
        f"Release Log, newest row)"
    )


# ---------------------------------------------------------------------------
# T130 — the page describes the agent-focus mechanisms (memory slice, startup
# reads, Response Standard). The slice caps are read from memory_slice.py at
# test time, never hardcoded (the T089 AC8 pattern above).
# ---------------------------------------------------------------------------

MEMORY_SLICE_SCRIPT = os.path.join(
    ROOT, "skills", "craft-spawn-prompt", "scripts", "memory_slice.py"
)
MANIFEST_PATH = os.path.join(ROOT, "MANIFEST")


def _table_row(text, needle):
    rows = [r for r in re.findall(r"<tr>.*?</tr>", text, re.DOTALL) if needle in r]
    assert rows, f"no table row on the page contains {needle!r}"
    return rows[0]


def _slice_caps_from_source():
    with open(MEMORY_SLICE_SCRIPT, encoding="utf-8") as f:
        src = f.read()
    caps = {}
    for name in ("MAX_LINES", "MAX_CHARS"):
        m = re.search(rf"^{name}\s*=\s*([\d_]+)", src, re.MULTILINE)
        assert m, f"could not parse {name} out of memory_slice.py"
        caps[name] = int(m.group(1).replace("_", ""))
    return caps


def _agent_focus_body():
    m = re.search(r'<section id="agent-focus">(.*?)</section>', _page_text(), re.DOTALL)
    assert m, 'page has no <section id="agent-focus">'
    return m.group(1)


def test_memory_md_row_describes_the_memory_slice_not_the_old_behaviour():
    row = _table_row(_page_text(), "<code>memory/MEMORY.md</code>")
    assert "memory slice" in row.lower(), "MEMORY.md row does not mention the memory slice"
    assert "not pasted" not in _page_text().lower(), (
        "page still says the memory index is 'not pasted' — every spawn prompt now "
        "carries a pasted memory slice"
    )


def test_spawn_hook_row_names_memory_slice_and_startup_reads():
    row = _table_row(_page_text(), "<code>pre_agent_validate_guide.py</code>").lower()
    assert "memory slice" in row, "hook row does not mention the memory-slice advisory"
    assert "startup reads" in row, "hook row does not mention the Startup-reads advisory"
    assert "tag-block" in row, "hook row lost its blocks tag"
    assert "tag-advise" in row, "hook row has no advises tag"


def test_slice_caps_on_page_match_memory_slice_source():
    caps = _slice_caps_from_source()
    body = _agent_focus_body()
    assert re.search(rf"\b{caps['MAX_LINES']}\s+lines", body), (
        f"agent-focus section does not publish the {caps['MAX_LINES']}-line slice cap"
    )
    chars = caps["MAX_CHARS"]
    assert _word_present(body, f"{chars:,}") or _word_present(body, str(chars)), (
        f"agent-focus section does not publish the {chars:,}-character slice cap"
    )


def test_agent_focus_table_reads_we_apply_to_save_idea_from():
    headers = re.findall(r"<th>(.*?)</th>", _agent_focus_body(), re.DOTALL)
    assert headers == ["We apply", "To save", "Idea from"], (
        f"agent-focus table headers are {headers}, want We apply / To save / Idea from"
    )


def test_agent_focus_names_all_six_mechanisms():
    body = _agent_focus_body().lower()
    for name in ("memory slice", "startup reads", "response standard",
                 "over-engineering reviewer", "compact-advisor", "measure before keeping"):
        assert name in body, f"agent-focus section does not name the mechanism {name!r}"


def test_agent_focus_credits_the_three_source_repos():
    # Read the "Idea from" column only: prose elsewhere in the section (row 6 says
    # "headroom-style") must not satisfy a credit that was dropped from its row.
    rows = re.findall(r"<tr>(.*?)</tr>", _agent_focus_body(), re.DOTALL)
    credits = [re.findall(r"<td\b[^>]*>(.*?)</td>", r, re.DOTALL)[-1].strip().lower()
               for r in rows if "<td" in r]
    for repo in ("headroom", "caveman", "ponytail"):
        assert repo in credits, f"no agent-focus row credits {repo} in its Idea-from column"


def test_agent_focus_states_purpose_not_figures():
    body = _agent_focus_body()
    assert "%" not in body, "agent-focus section carries a percent figure; write words, not numbers"


def _manifest_ships_scripts():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        for line in f:
            fields = line.split()
            if not fields or fields[0].startswith(("#", "!")):
                continue
            if fields[0].rstrip("/") == "scripts" or fields[0].startswith("scripts/"):
                return True
    return False


def test_page_does_not_name_token_meter_while_scripts_are_not_shipped():
    if _manifest_ships_scripts():
        return
    assert "token_meter" not in _page_text(), (
        "page names token_meter, but MANIFEST does not ship scripts/ — an install "
        "would not get it"
    )


# ---------------------------------------------------------------------------
# T135 — the Reference section introducing easy-verifier-mcp as a companion
# tool. The kit does not call it anywhere, so the section must not claim so.
# ---------------------------------------------------------------------------

VERIFIER_REPO_URL = "https://github.com/thunderkds/easy-verifier-mcp"


def _mcps_section_body():
    m = re.search(r'<section id="mcps">(.*?)</section>', _page_text(), re.DOTALL)
    assert m, 'page has no <section id="mcps">'
    return m.group(1)


def _mcp_entry_body(entry_id):
    """The card inside #mcps carrying id=<entry_id> (cards hold no nested <div>)."""
    m = re.search(rf'<div class="agent-card" id="{entry_id}">(.*?)</div>', _mcps_section_body(), re.DOTALL)
    assert m, f'#mcps has no entry with id="{entry_id}"'
    return m.group(1)


def _verifier_section_body():
    return _mcp_entry_body("verifier")


def test_mcps_section_is_linked_from_the_reference_nav_group():
    text = _page_text()
    nav = re.search(r"<nav\b[^>]*>(.*?)</nav>", text, re.DOTALL).group(1)
    reference = nav[nav.index("Reference"):]
    assert 'href="#mcps"' in reference, "Reference nav group has no #mcps link"
    assert 'href="#verifier"' not in reference, "Reference nav group still links #verifier"
    ids = _top_level_section_ids()
    assert "verifier" not in ids, "standalone top-level #verifier section is still there"
    assert ids.index("mcps") == ids.index("memory-system") + 1, "#mcps must sit right after #memory-system"
    assert ids.index("options") == ids.index("mcps") + 1, "#options must follow #mcps"
    assert "<h2>MCPs</h2>" in _mcps_section_body(), "section heading must be <h2>MCPs</h2>"


def test_mcps_section_has_one_named_entry_per_server():
    body = _mcps_section_body()
    for name in ("easy-verifier-mcp", "easy-ui-mcp", "easy-memory-mcp"):
        assert re.search(rf"<h3>[^<]*{name}[^<]*</h3>", body), f"no <h3> naming {name}"
    assert len(re.findall(r'<div class="agent-card"', body)) == 3, "expected exactly three entries"
    assert 'id="verifier"' in body, 'verifier entry lost id="verifier"; old #verifier links break'


def test_verifier_section_names_the_tool_and_links_the_repo_safely():
    body = _verifier_section_body()
    assert re.search(r"<h3>[^<]*easy-verifier-mcp[^<]*</h3>", body), "h3 must name easy-verifier-mcp"
    assert (
        f'href="{VERIFIER_REPO_URL}" target="_blank" rel="noopener noreferrer"' in body
    ), "section must link the repo with target=_blank rel=noopener noreferrer"


def test_verifier_section_is_short_with_four_to_six_highlights():
    body = _verifier_section_body()
    highlights = re.findall(r"<li>", body)
    assert 4 <= len(highlights) <= 6, f"expected 4-6 highlights, found {len(highlights)}"
    assert len(body.strip().splitlines()) <= 20, "verifier entry must stay within ~20 lines"


UI_MCP_REPO_URL = "https://github.com/thunderkds/easy-ui-mcp"
HONESTY_PHRASES = ("the kit uses", "ships with", "built in", "required")


def _ui_mcp_entry_body():
    m = re.search(r'<div class="agent-card" id="easy-ui-mcp">(.*?)</div>', _mcps_section_body(), re.DOTALL)
    assert m, '#mcps has no entry with id="easy-ui-mcp"'
    return m.group(1)


def test_ui_mcp_entry_has_four_to_five_one_line_highlights():
    body = _ui_mcp_entry_body()
    assert re.search(r"<h3>[^<]*easy-ui-mcp[^<]*</h3>", body), "h3 must name easy-ui-mcp"
    items = re.findall(r"<li>(.*?)</li>", body, re.DOTALL)
    assert 4 <= len(items) <= 5, f"expected 4-5 highlights, found {len(items)}"
    assert all("\n" not in i.strip() for i in items), "each highlight must sit on one line"


def test_ui_mcp_entry_links_the_repo_safely_and_invents_no_site():
    body = _ui_mcp_entry_body()
    assert (
        f'href="{UI_MCP_REPO_URL}" target="_blank" rel="noopener noreferrer"' in body
    ), "easy-ui-mcp entry must link its repo with target=_blank rel=noopener noreferrer"
    hrefs = re.findall(r'href="([^"]+)"', body)
    assert hrefs == [UI_MCP_REPO_URL], f"easy-ui-mcp entry must carry only its repo link, found {hrefs}"


def test_mcps_section_says_separate_and_never_claims_kit_integration():
    body = _mcps_section_body()
    lead = re.search(r'<p class="lead">(.*?)</p>', body, re.DOTALL)
    assert lead and "separate" in lead.group(1).lower() and "companion" in lead.group(1).lower(), (
        "section lead must call both servers separate companion tools"
    )
    lowered = body.lower()
    for phrase in HONESTY_PHRASES:
        assert phrase not in lowered, f"#mcps must not say {phrase!r}"


# ---------------------------------------------------------------------------
# T199 — easy-memory-mcp as a third, optional companion card. The kit does not
# ship, install or require it, so the card must say so and claim nothing more
# than the easy-memory-mcp README proves.
# ---------------------------------------------------------------------------

MEMORY_MCP_REPO_URL = "https://github.com/thunderkds/easy-memory-mcp"


def _memory_mcp_entry_body():
    return _mcp_entry_body("easy-memory-mcp")


def test_mcps_section_lead_counts_three_companions():
    lead = re.search(r'<p class="lead">(.*?)</p>', _mcps_section_body(), re.DOTALL).group(1).lower()
    assert "three" in lead and "two" not in lead, "section lead must say three companion tools, not two"


def test_memory_mcp_card_is_the_third_card_and_says_optional():
    body = _mcps_section_body()
    ids = re.findall(r'<div class="agent-card" id="([^"]+)"', body)
    assert ids == ["verifier", "easy-ui-mcp", "easy-memory-mcp"], f"card order is {ids}"
    card = _memory_mcp_entry_body()
    assert re.search(r"<h3>[^<]*easy-memory-mcp[^<]*</h3>", card), "h3 must name easy-memory-mcp"
    lead = re.search(r'<p class="lead">(.*?)</p>', card, re.DOTALL)
    assert lead, "easy-memory-mcp card has no lead paragraph"
    for word in ("separate", "companion", "optional"):
        assert word in lead.group(1).lower(), f"card lead must contain {word!r}"


def test_memory_mcp_card_has_four_to_five_one_line_highlights():
    items = re.findall(r"<li>(.*?)</li>", _memory_mcp_entry_body(), re.DOTALL)
    assert 4 <= len(items) <= 5, f"expected 4-5 highlights, found {len(items)}"
    assert all("\n" not in i.strip() for i in items), "each highlight must sit on one line"


def test_memory_mcp_card_says_the_kit_runs_as_before_without_it():
    items = [i.lower() for i in re.findall(r"<li>(.*?)</li>", _memory_mcp_entry_body(), re.DOTALL)]
    assert any("without it" in i and "runs as before" in i for i in items), (
        "one highlight must say the kit runs as before without easy-memory-mcp"
    )


def test_memory_mcp_card_names_the_four_tools_from_the_readme():
    card = _memory_mcp_entry_body()
    for tool in ("memory_search", "memory_read", "memory_list", "memory_forget"):
        assert f"<code>{tool}</code>" in card, f"card must name the MCP tool {tool}"


def test_memory_mcp_card_states_the_token_figure_only_as_a_scripted_test_result():
    items = [i.lower() for i in re.findall(r"<li>(.*?)</li>", _memory_mcp_entry_body(), re.DOTALL)]
    measured = [i for i in items if "28%" in i]
    assert len(measured) == 1, "exactly one highlight may carry the ~28% figure"
    assert "scripted" in measured[0] and "real work" in measured[0], (
        "the figure must be tied to scripted tests and say it is not yet measured on real work"
    )


def test_memory_mcp_card_links_the_repo_safely_and_invents_no_site():
    card = _memory_mcp_entry_body()
    assert (
        f'href="{MEMORY_MCP_REPO_URL}" target="_blank" rel="noopener noreferrer"' in card
    ), "easy-memory-mcp card must link its repo with target=_blank rel=noopener noreferrer"
    hrefs = re.findall(r'href="([^"]+)"', card)
    assert hrefs == [MEMORY_MCP_REPO_URL], f"easy-memory-mcp card must carry only its repo link, found {hrefs}"


# ---------------------------------------------------------------------------
# T138 — the Overview's pipeline diagram follows docs/claude-md/pipeline-stages.md
# ---------------------------------------------------------------------------

PIPELINE_DOC = os.path.join(ROOT, "docs", "claude-md", "pipeline-stages.md")


def _pipeline_stage_numbers():
    """Phase 0 first (it has no `## Stage` heading), then the number of every
    `## Stage N:` heading in document order, read at test time."""
    with open(PIPELINE_DOC, encoding="utf-8") as f:
        text = f.read()
    return ["0"] + re.findall(r"^## Stage (\d+(?:\.\d+)?)\b", text, re.MULTILINE)


def _pipeline_svg():
    match = re.search(
        r'<svg\b[^>]*\bid="pipeline-diagram"[^>]*>.*?</svg>', _page_text(), re.DOTALL
    )
    assert match, 'no <svg id="pipeline-diagram"> on the page'
    return match.group(0)


def test_pipeline_diagram_is_inside_the_overview_section():
    body = re.search(
        r'<section id="what-you-get">(.*?)</section>', _page_text(), re.DOTALL
    )
    assert body and 'id="pipeline-diagram"' in body.group(1)


def test_pipeline_diagram_is_accessible_svg():
    svg = _pipeline_svg()
    assert 'role="img"' in svg and "<title" in svg and "<desc" in svg
    assert "viewBox=" in svg


def test_pipeline_diagram_has_one_node_per_stage_in_document_order():
    svg = _pipeline_svg()
    nodes = re.findall(r'<g class="node" data-stage="([^"]+)">(.*?)</g>', svg, re.DOTALL)
    assert [n for n, _ in nodes] == _pipeline_stage_numbers()
    for number, body in nodes:
        label = "Phase 0" if number == "0" else f"Stage {number} "
        assert label in body, f"node {number} does not show its stage label"


def test_pipeline_diagram_joins_every_node_with_an_arrow():
    svg = _pipeline_svg()
    assert svg.count('class="arrow-head"') == len(_pipeline_stage_numbers()) - 1


def test_pipeline_diagram_uses_tokens_and_no_script_or_external_ref():
    svg = _pipeline_svg()
    assert "<script" not in svg and not re.search(r'(?:href|src)\s*=', svg)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", svg)
    css = re.search(r"svg\.pipeline.*?(?=footer \{)", _page_text(), re.DOTALL).group(0)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)


# ---------------------------------------------------------------------------
# T165 — scan-first page. Prose outside a <details> fold-out stays short; the
# quick-reference card's counts are derived from source at test time, never
# hardcoded here (the drift constraint in PROJECT_SPEC_SITE.md).
# ---------------------------------------------------------------------------

import html as _html

LEAD_WORD_CAP = 35
CELL_WORD_CAP = 25
ONE_LINE_INSTALL = (
    "curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"
)
EASY_VERIFIER_SITE_URL = "https://easy-verifier.vercel.app/"


def _words(fragment):
    return _html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split()


def _outside_details(text):
    return re.sub(r"<details\b.*?</details>", " ", text, flags=re.DOTALL)


def _quick_reference_body():
    m = re.search(r'<section id="quick-reference">(.*?)</section>', _page_text(), re.DOTALL)
    assert m, 'page has no <section id="quick-reference">'
    return m.group(1)


def _quick_reference_text():
    return " ".join(_words(_quick_reference_body()))


def _hooks_section_body():
    m = re.search(r'<section id="hooks">(.*?)</section>', _page_text(), re.DOTALL)
    assert m, 'page has no <section id="hooks">'
    return m.group(1)


def test_visible_lead_paragraphs_are_one_line_summaries():
    """AC1: a lead outside a <details> fold-out is a summary, not a paragraph."""
    leads = re.findall(r'<p class="lead">(.*?)</p>', _outside_details(_page_text()), re.DOTALL)
    assert leads, "no visible lead paragraphs — fixture broken"
    long_ones = [(len(_words(l)), " ".join(_words(l))[:60]) for l in leads
                 if len(_words(l)) > LEAD_WORD_CAP]
    assert not long_ones, f"visible lead(s) over {LEAD_WORD_CAP} words: {long_ones}"


def test_visible_table_cells_are_short():
    """AC2: a <td> outside a <details> fold-out holds at most 25 words."""
    cells = re.findall(r"<td\b[^>]*>(.*?)</td>", _outside_details(_page_text()), re.DOTALL)
    assert cells, "no table cells — fixture broken"
    long_ones = [(len(_words(c)), " ".join(_words(c))[:60]) for c in cells
                 if len(_words(c)) > CELL_WORD_CAP]
    assert not long_ones, f"visible table cell(s) over {CELL_WORD_CAP} words: {long_ones}"


def test_page_has_details_foldouts_with_content():
    """AC3: native fold-outs exist, each opens with a <summary> and holds detail."""
    foldouts = re.findall(r"<details\b[^>]*>(.*?)</details>", _page_text(), re.DOTALL)
    assert foldouts, "page has no <details> fold-out"
    for body in foldouts:
        summary = re.match(r"\s*<summary>(.*?)</summary>(.*)", body, re.DOTALL)
        assert summary, f"<details> does not open with a <summary>: {body[:60]!r}"
        assert _words(summary.group(2)), f"<details> {summary.group(1)!r} has no content"


def test_quick_reference_is_the_first_section_and_has_a_nav_link():
    """AC4: the card sits first under <main>, right after the header."""
    text = _page_text()
    assert _top_level_section_ids()[0] == "quick-reference", (
        f"first top-level section is {_top_level_section_ids()[0]!r}, want quick-reference"
    )
    assert text.index('<div class="header">') < text.index('<section id="quick-reference">')
    assert "quick-reference" in _nav_hrefs(), "sidebar nav has no #quick-reference link"


def test_quick_reference_shows_install_and_update_commands():
    body = _quick_reference_body()
    assert ONE_LINE_INSTALL in body, "quick reference does not show the install command"
    assert re.search(r"\bUpdate\b", body), "quick reference does not say how to update"


def test_quick_reference_shows_the_stage_sequence_from_the_pipeline_doc():
    stages = _pipeline_stage_numbers()
    expected = "Phase 0 → " + " → ".join(stages[1:])
    assert expected in _quick_reference_text(), (
        f"quick reference does not show the stage sequence {expected!r}"
    )


def _blocking_hook_count():
    """Wired hooks (settings.json) whose hook-table row carries the blocks tag."""
    rows = re.findall(r"<tr>.*?</tr>", _hooks_section_body(), re.DOTALL)
    count = 0
    for script in _hook_scripts():
        row = [r for r in rows if f"<code>{script}</code>" in r]
        assert row, f"hook {script} has no row in the hook table"
        count += "tag-block" in row[0]
    return count


def test_skills_heading_count_matches_source():
    """T173 AC12: the `Skills (N)` heading equals the number of skills/*/ folders."""
    m = re.search(r"<h2>Skills \((\d+)\)</h2>", _raw_page_text())
    assert m, "no `Skills (N)` heading on the page"
    assert int(m.group(1)) == len(_skill_dirs()), (
        f"heading says Skills ({m.group(1)}), source has {len(_skill_dirs())}"
    )


def test_quick_reference_counts_match_source():
    """AC5: skill, spawnable-role and blocking-hook counts, each derived here."""
    text = _quick_reference_text()
    skills = len(_skill_dirs())
    roles = len(_agent_names())  # T183: agents/ holds only spawnable roles
    blocking = _blocking_hook_count()
    hooks = len(_hook_scripts())
    assert blocking, "no hook row carries tag-block — fixture broken"
    assert re.search(rf"(?<!\d){skills} skills\b", text), f"quick reference does not say {skills} skills"
    assert re.search(rf"(?<!\d){roles} spawnable roles\b", text), (
        f"quick reference does not say {roles} spawnable roles"
    )
    assert re.search(rf"(?<!\d){blocking} blocking hooks \(of {hooks}\)", text), (
        f"quick reference does not say {blocking} blocking hooks (of {hooks})"
    )


def test_verifier_section_links_the_easy_verifier_site_beside_the_repo():
    """AC6: the Easy Verifier site link opens safely, next to the GitHub link."""
    body = _verifier_section_body()
    assert (
        f'href="{EASY_VERIFIER_SITE_URL}" target="_blank" rel="noopener noreferrer"' in body
    ), "verifier section must link the Easy Verifier site with target=_blank rel=noopener noreferrer"
    link_line = [l for l in body.splitlines() if EASY_VERIFIER_SITE_URL in l]
    assert VERIFIER_REPO_URL in link_line[0], "Easy Verifier site link must sit beside the GitHub link"


# --- T166: the Skills section is a stage flow with skill chips ----------------

# The one place the grouping is pinned (T166 Requirement): stage -> skills.
SKILL_FLOW_GROUPING = {
    "0.5": {"brainstorming", "ideate"},
    "1": {"git-guardrails-claude-code", "map-codebase", "settings-setup"},
    "1.5": {"craft-agent"},
    "2": {"grill-with-docs", "to-issues"},
    "3": {"tdd", "bugfix", "diagnose", "craft-spawn-prompt", "migration-safety"},
    "4": {"blast-radius", "code-review", "html-report"},
    "5": {"ship", "delivery-report"},
}


def _skills_section_body():
    m = re.search(r'<section id="skills">(.*?)</section>', _page_text(), re.DOTALL)
    assert m, 'page has no <section id="skills">'
    return m.group(1)


def _skill_flow():
    m = re.search(r'<ol\b[^>]*class="skill-flow"[^>]*>(.*?)</ol>', _skills_section_body(), re.DOTALL)
    assert m, '#skills has no <ol class="skill-flow">'
    return m


def _flow_steps():
    """[(stage number, step html)] in document order."""
    steps = re.findall(
        r'<li\b[^>]*class="flow-step"[^>]*data-stage="([^"]+)"[^>]*>(.*?)</li>\s*(?=<li\b[^>]*class="flow-step"|\Z)',
        _skill_flow().group(1),
        re.DOTALL,
    )
    return steps


def _chips(fragment):
    return [_html.unescape(c).strip() for c in re.findall(r'<span class="chip">(.*?)</span>', fragment, re.DOTALL)]


def _skill_band():
    m = re.search(r'<div\b[^>]*class="skill-band"[^>]*>(.*?)</div>', _skills_section_body(), re.DOTALL)
    assert m, '#skills has no <div class="skill-band">'
    return m.group(1)


def test_skills_flow_has_one_step_per_pipeline_stage_in_order():
    """AC1."""
    expected = [n for n in _pipeline_stage_numbers() if n != "0"]
    assert [s for s, _ in _flow_steps()] == expected


def test_skills_flow_steps_show_stage_label_and_chips():
    """AC2: stage number + name as text, skills as plain-text chips, no SVG text."""
    assert "<svg" not in _skills_section_body()
    for stage, body in _flow_steps():
        heading = re.search(r"<h3\b[^>]*>(.*?)</h3>", body, re.DOTALL)
        assert heading, f"stage {stage} step has no <h3>"
        label = " ".join(_words(heading.group(1)))
        assert label.startswith(f"Stage {stage}") and len(_words(label)) > 2, label
        assert _chips(body), f"stage {stage} step has no chips"


def test_skills_flow_is_accessible_and_arrows_are_visual_only():
    """AC3: named list; any arrow element is aria-hidden; no arrow glyph in reading text."""
    tag = re.search(r'<ol\b[^>]*class="skill-flow"[^>]*>', _skills_section_body()).group(0)
    assert re.search(r'aria-label="[^"]+"', tag), "skill-flow needs an accessible name"
    for el in re.findall(r"<[^>]*class=\"[^\"]*arrow[^\"]*\"[^>]*>", _skills_section_body()):
        assert 'aria-hidden="true"' in el, el
    reading = " ".join(_words(_skill_flow().group(1)))
    assert not re.search(r"[→↓➜►▶]", reading), "arrow glyphs would be read aloud"


def test_skills_cross_cutting_band_is_separate_and_below_the_flow():
    """AC4."""
    body = _skills_section_body()
    assert body.index('class="skill-band"') > body.index("</ol>")
    assert re.search(r"Any stage", _skill_band())
    assert len(_chips(_skill_band())) > 0
    assert not _chips(_skill_band()) or not (set(_chips(_skill_band())) & set().union(*SKILL_FLOW_GROUPING.values()))


def test_skills_section_lists_every_skill_dir_exactly_once_and_nothing_else():
    """AC5: both directions, derived from skills/."""
    all_chips = _chips(_skill_flow().group(1)) + _chips(_skill_band())
    on_disk = _skill_dirs()
    dupes = sorted({c for c in all_chips if all_chips.count(c) > 1})
    assert not dupes, f"skill(s) listed more than once: {dupes}"
    assert sorted(all_chips) == on_disk, (
        f"missing: {sorted(set(on_disk) - set(all_chips))}; unknown: {sorted(set(all_chips) - set(on_disk))}"
    )


def test_skills_flow_grouping_matches_the_requirement():
    """AC6."""
    assert {s: set(_chips(b)) for s, b in _flow_steps()} == SKILL_FLOW_GROUPING


def test_skills_flow_snakes_with_an_arrow_between_every_consecutive_pair():
    """T166 round 2: every step but the last names the direction of its arrow; the CSS draws all three."""
    tags = re.findall(r'<li\b[^>]*class="flow-step"[^>]*>', _skill_flow().group(1))
    dirs = [re.search(r'data-next="(right|left|down)"', t) for t in tags]
    assert all(dirs[:-1]), "every step except the last needs data-next=right|left|down"
    assert dirs[-1] is None, "the last step has no next step"
    assert [d.group(1) for d in dirs[:-1]] == ["right", "down", "left", "down", "right", "down"]
    css = _page_text()
    for d in ("right", "left", "down"):
        assert re.search(rf'\.flow-step\[data-next="{d}"\]::after', css), f"no CSS arrow rule for {d}"


# ---- T167: tables never scroll sideways --------------------------------

def _style_block():
    m = re.search(r"<style>(.*?)</style>", _page_text(), re.DOTALL)
    assert m, "page has no <style> block"
    return m.group(1)


def _css_rule(css, selector):
    """Body of the first rule whose selector list is exactly `selector`."""
    for sel, body in re.findall(r"(?m)^\s*([^{}@/]+?)\s*\{([^{}]*)\}", css):
        if ", ".join(x.strip() for x in sel.split(",")) == selector:
            return body
    return None


def _mobile_block():
    css = _style_block()
    start = css.index("@media (max-width: 767px)")
    depth, i = 0, css.index("{", start)
    for j in range(i, len(css)):
        depth += {"{": 1, "}": -1}.get(css[j], 0)
        if depth == 0:
            return css[i + 1:j]
    raise AssertionError("unbalanced 767px media block")


def test_tables_do_not_force_a_minimum_width_or_scroll_sideways():
    """AC1."""
    css = _style_block()
    table = _css_rule(css, "table")
    assert table is not None and "min-width" not in table, f"table rule forces a width: {table}"
    wrap = _css_rule(css, ".table-wrap")
    assert wrap is not None and not re.search(r"overflow(-x)?\s*:\s*(auto|scroll)", wrap), wrap
    assert "th:first-child, td:first-child" not in css, "sticky first column is only for sideways scrolling"


def test_long_code_tokens_in_table_cells_can_wrap():
    """AC2: wrapping comes from <wbr> break points (see the next test), so cell code may not be nowrap."""
    css = _style_block()
    assert not re.search(r"(?:td|th)\s+code\s*\{[^}]*white-space\s*:\s*(?:nowrap|pre)\b", css), \
        "code inside table cells is forbidden from wrapping"


def test_code_tokens_in_table_cells_break_only_at_natural_boundaries():
    """T167 round 2: no mid-word breaks — `overflow-wrap: anywhere` is gone and every long
    code token in a cell offers <wbr> break points after `_` `/` `.` `-`."""
    css = _style_block()
    assert not re.search(r"td\s+code\s*\{[^}]*overflow-wrap\s*:\s*anywhere", css)
    assert not re.search(r"(?:td|th)\s+code\s*\{[^}]*word-break\s*:\s*break-all", css)
    long_unbroken = []
    for t in re.findall(r"<table\b.*?</table>", _raw_page_text(), re.DOTALL):
        for code in re.findall(r"<code>(.*?)</code>", t, re.DOTALL):
            if len(_html.unescape(code.replace("<wbr>", ""))) > 20 and "<wbr>" not in code:
                long_unbroken.append(code)
    assert not long_unbroken, f"long code tokens in table cells without <wbr>: {long_unbroken}"
    hooks = re.search(r'<section id="hooks">(.*?)</section>', _raw_page_text(), re.DOTALL).group(1)
    assert "pre_<wbr>agent_<wbr>validate_<wbr>guide.py" in hooks, \
        "script names are not given break points after the underscores"


def _tables():
    """[(headers, [td-open-tags])] for every table on the page."""
    out = []
    for t in re.findall(r"<table\b.*?</table>", _page_text(), re.DOTALL):
        heads = [" ".join(_words(h)) for h in re.findall(r"<th\b[^>]*>(.*?)</th>", t, re.DOTALL)]
        body = re.search(r"<tbody>(.*?)</tbody>", t, re.DOTALL).group(1)
        rows = [re.findall(r"<td\b[^>]*>", r) for r in re.findall(r"<tr>(.*?)</tr>", body, re.DOTALL)]
        out.append((heads, rows))
    return out


def test_every_td_carries_its_columns_header_as_data_label():
    """AC3: both directions — none missing, none mismatched."""
    tables = _tables()
    assert len(tables) >= 8, "fixture broken: expected the page's tables"
    problems = []
    for heads, rows in tables:
        for r in rows:
            if len(r) != len(heads):
                problems.append(f"{heads}: row has {len(r)} cells for {len(heads)} headers")
                continue
            for h, tag in zip(heads, r):
                m = re.search(r'data-label="([^"]*)"', tag)
                got = _html.unescape(m.group(1)) if m else None
                if got != h:
                    problems.append(f"{heads}: expected {h!r}, got {got!r}")
    assert not problems, problems


def test_phone_layout_stacks_each_row_as_a_card_with_labelled_cells():
    """AC4."""
    m = _mobile_block()
    thead = _css_rule(m, "thead")
    assert thead and "display: none" not in thead.replace("display:none", "display: none") \
        and re.search(r"clip|position\s*:\s*absolute", thead), f"thead must be visually hidden, not removed: {thead}"
    for sel in ("table, tbody, tr, td", "table, tbody, tr, th, td", "tr, td", "tbody, tr, td"):
        blk = _css_rule(m, sel)
        if blk:
            assert "display: block" in blk
            break
    else:
        raise AssertionError("rows and cells are not made display: block on phones")
    before = _css_rule(m, "td::before")
    assert before and "content: attr(data-label)" in before, before


# ---------------------------------------------------------------------------
# T181 — the two tracks, `[auto]` and the Debate are on the page
# ---------------------------------------------------------------------------

def _tracks_section():
    match = re.search(
        r'<section id="tracks">(.*?)</section>', _page_text(), re.DOTALL
    )
    assert match, 'site/index.html has no <section id="tracks">'
    return match.group(1)


def test_tracks_section_sits_after_what_you_get_and_before_install():
    text = _page_text()
    assert text.index('id="what-you-get"') < text.index('id="tracks"') < text.index('id="install"')


def test_tracks_section_has_h2_naming_both_tracks():
    h2 = re.search(r"<h2>(.*?)</h2>", _tracks_section(), re.DOTALL)
    assert h2, "tracks section has no <h2>"
    assert "minimal" in h2.group(1).lower() and "extended" in h2.group(1).lower()


def test_tracks_nav_link_exists():
    assert 'href="#tracks"' in _raw_page_text()


def test_tracks_section_states_announcement_lines_and_override():
    sec = _tracks_section()
    for needle in ("Track: minimal", "Track: extended", "[auto]", "/verify",
                   "<code>full</code>", "<code>minimal</code>",
                   "MINIMAL_LOG.md", "Debate", "Advocate", "decided for you"):
        assert needle in sec, f"tracks section lacks {needle!r}"


def test_tracks_section_does_not_say_auto_merges_pushes_or_supervisor_runs_verify():
    sec = re.sub(r"<[^>]+>", " ", _tracks_section())
    sec = " ".join(sec.split()).lower()
    assert "merge" in sec and "user" in sec
    for bad in ("auto mode merges", "auto mode pushes", "merges your branch",
                "pushes your branch", "supervisor runs /verify",
                "supervisor runs `/verify`"):
        assert bad not in sec, f"tracks section says {bad!r}"


def test_pipeline_diagram_desc_says_stages_are_the_extended_track():
    desc = re.search(r'<desc id="pipeline-diagram-desc">(.*?)</desc>', _page_text(), re.DOTALL)
    assert desc and "extended track" in desc.group(1)

# ---------------------------------------------------------------------------
# T185 — Settings tool (Build mode). Spec: PROJECT_SPEC_SITE.md § "Settings tool".
# ---------------------------------------------------------------------------

def _script_block(script_id):
    match = re.search(
        r'<script\b[^>]*\bid="%s"[^>]*>(.*?)</script>' % re.escape(script_id),
        _page_text(), re.DOTALL,
    )
    assert match, f'page has no <script id="{script_id}">'
    return match.group(1)


def _settings_catalog():
    return json.loads(_script_block("settings-catalog"))


def _settings_section():
    match = re.search(r'<section id="settings-tool">.*?\n</section>', _page_text(), re.DOTALL)
    assert match, "page has no <section id=\"settings-tool\">"
    return match.group(0)


def test_settings_tool_section_nav_and_no_script_fallback():
    section = _settings_section()
    assert "<h2>Settings tool</h2>" in section
    nav = re.search(r'<nav id="site-nav".*?</nav>', _page_text(), re.DOTALL).group(0)
    assert nav.index('href="#update-flow"') < nav.index('href="#settings-tool"') < nav.index('href="#install-variants"')
    assert 'class="st-nojs"' in section
    assert "https://code.claude.com/docs/en/settings-reference" in section
    # T187: the Check tab is live (it was disabled "coming soon" in T185).
    tab = re.search(r'<button[^>]*id="st-tab-check"[^>]*>', section).group(0)
    assert "disabled" not in tab and "coming soon" not in section
    assert 'aria-controls="st-check-panel"' in tab and 'id="st-check-panel"' in section


def test_settings_check_mode_controls_and_privacy_line():
    """T187 AC1: paste area, target-file choice, the three buttons, the privacy line."""
    section = _settings_section()
    assert re.search(r'<textarea\b[^>]*id="st-paste"', section)
    for value in ("user", "project", "local"):
        assert f'name="st-check-target" value="{value}"' in section
    for button, label in (("st-format", "Format"), ("st-check", "Check"), ("st-edit", "Edit in Build")):
        assert re.search(rf'<button type="button"[^>]*id="{button}"[^>]*>{label}</button>', section), button
    assert "Runs in your browser only. Nothing is sent or saved." in section


def test_settings_tool_never_writes_html_from_text():
    """T187: pasted text is untrusted; the tool renders with textContent only."""
    source = _script_block("settings-tool-core") + _script_block("settings-tool-ui")
    for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
        assert banned not in source, f"tool script contains {banned}"


def test_settings_catalog_shape_and_version_stamp():
    catalog = _settings_catalog()
    assert re.fullmatch(r"\d+\.\d+\.\d+", catalog["version"])
    known = set(catalog["knownKeys"])
    assert catalog["settings"], "catalog has no settings"
    for entry in catalog["settings"]:
        for field in ("key", "category", "type", "scopes", "why"):
            assert entry.get(field), f"catalog entry {entry.get('key')} missing {field}"
        assert entry["category"] in catalog["categories"], entry["key"]
        assert set(entry["scopes"]) <= {"user", "project", "local"}, entry["key"]
        if entry["type"] == "enum":
            assert entry.get("values"), f"enum {entry['key']} has no values"
        assert entry["key"] in known, f"{entry['key']} not in knownKeys"
    keys = [e["key"] for e in catalog["settings"]]
    assert len(keys) == len(set(keys)), "duplicate catalog keys"


def test_settings_tool_script_uses_no_network_or_storage_api():
    """Spec rule 1: pasted and generated text never leaves the browser."""
    source = _script_block("settings-tool-core") + _script_block("settings-tool-ui")
    for banned in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket",
                   "localStorage", "sessionStorage", "indexedDB", "document.cookie"):
        assert banned not in source, f"tool script contains {banned}"
    assert "document" not in _script_block("settings-tool-core"), "core block must not touch the DOM"


def test_settings_tool_has_no_submitting_form_and_no_package_json():
    """Spec rules 2 and 4."""
    assert not re.search(r"<form\b", _settings_section(), re.IGNORECASE)
    assert not os.path.exists(os.path.join(ROOT, "package.json"))


def test_settings_tool_css_adds_no_color_literals():
    """Design-system rule: only existing var(--…) tokens inside the scoped CSS."""
    css = re.search(r"/\* ---- settings tool \(scoped\).*?(?=</style>)", _page_text(), re.DOTALL).group(0)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", css), "color literal in settings-tool CSS"


def _media_blocks(css):
    """[(min_width_px, body)] for every `@media (min-width: Npx)` block."""
    out = []
    for m in re.finditer(r"@media\s*\(min-width:\s*(\d+)px\)\s*\{", css):
        depth, i = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        out.append((int(m.group(1)), css[m.end():i - 1]))
    return out


def test_hooks_first_two_columns_only_refuse_to_wrap_from_900px():
    """Scope addendum: between 768 and ~884 px the nowrap EVENT and MATCHER columns made the
    4-column table 851 px wide, wider than the column, so the page scrolled sideways."""
    css = _style_block()
    nowrap = [w for w, body in _media_blocks(css)
              if re.search(r"#hooks td:nth-child\(-n\+2\)\s*\{[^}]*white-space\s*:\s*nowrap", body)]
    assert nowrap, "no media query holds the nowrap rule for the first two #hooks columns"
    assert min(nowrap) >= 900, f"nowrap starts at {min(nowrap)}px; below 900px the table overflows"
    outside = re.sub(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    assert not re.search(r"#hooks t[dh]:nth-child\(-n\+2\)[^{]*\{[^}]*nowrap", outside), \
        "nowrap on the first two #hooks columns sits outside a min-width media query"
    # Wrapping only helps if the Matcher cell offers break points: nowrap was not the only
    # thing that kept the table 554px wide, the unbreakable `Edit|Write|Bash` was too.
    hooks = re.search(r'<section id="hooks">(.*?)</section>', _raw_page_text(), re.DOTALL).group(1)
    assert "Edit|<wbr>Write|<wbr>Bash" in hooks, "the multi-tool Matcher has no break points after `|`"


# ---- T201: Build-tab profiles held equal to skills/settings-setup/profiles.json ----
PROFILES_PATH = os.path.join(ROOT, "skills", "settings-setup", "profiles.json")


def _profiles():
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)["profiles"]


def _expanded_page_preset(catalog, preset):
    """Preset values with `$suggest` replaced by the catalog entry's suggest list."""
    by_key = {e["key"]: e for e in catalog["settings"]}
    out = {}
    for key, value in preset["values"].items():
        out[key] = list(by_key[key]["suggest"]) if value == "$suggest" else value
    return out


def test_page_profiles_match_profiles_json_ids_in_order():
    """T201 AC1/AC3: same ids, same order; safe-baseline is gone."""
    page_ids = [p["id"] for p in _settings_catalog()["presets"]]
    assert page_ids == [p["id"] for p in _profiles()]
    assert "safe-baseline" not in page_ids


def test_page_profiles_values_label_and_for_equal_profiles_json():
    """T201 AC3: drift in a rule, a label or a for line fails here."""
    catalog = _settings_catalog()
    page = {p["id"]: p for p in catalog["presets"]}
    for profile in _profiles():
        preset = page[profile["id"]]
        assert preset["label"] == profile["label"], profile["id"]
        assert preset.get("for") == profile["for"], f"{profile['id']} for text drifted"
        assert _expanded_page_preset(catalog, preset) == profile["values"], f"{profile['id']} values drifted"


def test_no_page_profile_lowers_safety():
    """T201 AC7 / NFR-001."""
    text = json.dumps(_settings_catalog()["presets"])
    for banned in ("bypassPermissions", "permissions.allow", "defaultMode"):
        assert banned not in text, banned


def test_settings_lead_says_what_the_installer_and_stage_1_do():
    """T201 AC6 / FR-008: the old "installs no settings" claim is gone; the intro says what is true."""
    section = _settings_section()
    intro = re.sub(r"\s+", " ", section[:section.index('<div id="st-app"')])
    assert "installs no settings" not in section
    assert "The installer adds only the kit's hooks and 2 deny rules." in intro
    assert "At Stage 1 the Supervisor offers the profiles below, and uses High security if you skip." in intro
    assert "writes only after you approve, and never removes an entry" in intro


def test_build_tab_has_a_for_line_for_the_profiles():
    """T201 AC2: a static line the script fills with the hovered, focused or active profile's text."""
    section = _settings_section()
    assert re.search(r'<p\b[^>]*id="st-presetfor"[^>]*class="st-why"|<p\b[^>]*class="st-why"[^>]*id="st-presetfor"', section)
