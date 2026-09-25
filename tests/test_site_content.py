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
            r"<tr><td><code>" + re.escape(canon_dir) + r"</code></td>", body
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
