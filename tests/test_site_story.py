"""
T231 - the story landing page. Spec: tasks/TASK_GUIDE_T231.md (AC 1-9, D1-D9).

site/index.html is a short story: hero, journey, paths, stops, deeper. All reference
content lives in site/docs.html, moved unchanged. This file pins the shape of the story
(sections, reading budget, plain words, true hook claims), that the reference lost nothing,
and that old links such as index.html#hooks land on docs.html#hooks.

The baseline of what index.html held at 09d2544c (the commit before this task) is
tests/fixtures/site_story_baseline.json: the 17 section ids, one hash per <p>/<li>/<td>/<dd>
text, and one hash per Settings tool script block. Regenerate it only from that commit:

    git show 09d2544c:site/index.html > /some/dir/old.html
    python3 -c "import sys; sys.path.insert(0, 'tests'); import test_site_story as t, json; \
print(json.dumps(t.baseline_of(open('/some/dir/old.html', encoding='utf-8').read()), indent=1))"
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from html.parser import HTMLParser

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
INDEX = os.path.join(SITE, "index.html")
DOCS = os.path.join(SITE, "docs.html")
THEME = os.path.join(SITE, "theme.css")
HOOKS_DIR = os.path.join(ROOT, ".claude", "hooks")
SETTINGS_JSON = os.path.join(ROOT, ".claude", "settings.json")
RUNBOOK = os.path.join(ROOT, "RUNBOOK.md")
BASELINE_PATH = os.path.join(ROOT, "tests", "fixtures", "site_story_baseline.json")

STORY_SECTIONS = ["hero", "journey", "paths", "stops", "deeper"]
WORD_CAP = 300  # D3: visible words in <main> of index.html
SCRIPT_IDS = ("settings-catalog", "settings-tool-core", "settings-tool-ui")
ONE_LINE_INSTALL = (
    "curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"
)
# D4: none of these may appear in text a reader sees or hears on index.html.
BANNED_TERMS = [
    r"C[0-3]", r"Risk", r"Gate", r"Stage", r"Phase", r"PreToolUse", r"PostToolUse", r"TASK_GUIDE",
    r"worktree", r"sub-agent", r"doctrine", r"harness", r"Evidence",
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def index_html():
    return _read(INDEX)


def docs_html():
    return _read(DOCS)


def theme_css():
    return _read(THEME)


def _baseline():
    with open(BASELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _main(html):
    m = re.search(r"<main\b[^>]*>(.*)</main>", html, re.DOTALL)
    assert m, "page has no <main>"
    return m.group(1)


def _no_comments(fragment):
    return re.sub(r"<!--.*?-->", "", fragment, flags=re.DOTALL)


def top_level_sections(html):
    """[(id, body)] for the <section> elements that are direct children of <main>."""
    main = _main(html)
    out, depth, start, sid = [], 0, 0, None
    for tag in re.finditer(r"<section\b([^>]*)>|</section>", main):
        if tag.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                out.append((sid, main[start:tag.start()]))
            continue
        if depth == 0:
            m = re.search(r'\bid="([^"]+)"', tag.group(1))
            assert m, f"top-level <section{tag.group(1)}> has no id"
            sid, start = m.group(1), tag.end()
        depth += 1
    return out


def section(html, section_id):
    for sid, body in top_level_sections(html):
        if sid == section_id:
            return body
    raise AssertionError(f'no <section id="{section_id}">')


# ---- text measures -------------------------------------------------------------

class _Words(HTMLParser):
    """Words a reader sees: all text outside pre, code, script, style (comments are dropped by the parser)."""

    SKIPPED = {"pre", "code", "script", "style"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip, self.chunks = 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIPPED:
            self.skip += 1
        for name, value in attrs:  # screen readers speak these too
            if name in ("aria-label", "title", "alt") and value:
                self.chunks.append(("attr", value))

    def handle_endtag(self, tag):
        if tag in self.SKIPPED and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.chunks.append(("text", data))


def _reading(fragment):
    parser = _Words()
    parser.feed(fragment)
    return parser.chunks


def visible_words(fragment):
    return [w for kind, text in _reading(fragment) if kind == "text" for w in text.split()]


def heard_text(fragment):
    return " ".join(text for _, text in _reading(fragment))


# ---- baseline of the old index.html -------------------------------------------

class _Sentences(HTMLParser):
    """Whitespace-normalised text of every <p>, <li>, <td> and <dd>, scripts and styles skipped."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.out, self.skip = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li", "td", "dd") and not self.skip:
            self.stack.append([])

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag in ("p", "li", "td", "dd") and not self.skip and self.stack:
            self.out.append(" ".join("".join(self.stack.pop()).split()))

    def handle_data(self, data):
        if not self.skip:
            for buf in self.stack:
                buf.append(data)


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def sentence_hashes(html):
    parser = _Sentences()
    parser.feed(html.replace("<wbr>", ""))
    return {_digest(t): t for t in parser.out if t}


def script_block(html, script_id):
    m = re.search(r'<script\b[^>]*\bid="%s"[^>]*>(.*?)</script>' % re.escape(script_id), html, re.DOTALL)
    assert m, f'page has no <script id="{script_id}">'
    return m.group(1)


def baseline_of(old_html):
    """What the fixture holds, computed from the old page."""
    return {
        "commit": "09d2544c",
        "sections": [sid for sid, _ in top_level_sections(old_html)],
        "sentences": [[h, t[:60]] for h, t in sorted(sentence_hashes(old_html).items(), key=lambda kv: kv[1])],
        "scripts": {i: hashlib.sha256(script_block(old_html, i).encode("utf-8")).hexdigest() for i in SCRIPT_IDS},
    }


# ---- AC 1: the five sections, no fold -------------------------------------------

def test_index_holds_the_five_story_sections_in_order_and_no_details():
    html = index_html()
    assert [sid for sid, _ in top_level_sections(html)] == STORY_SECTIONS
    assert "<details" not in html, "the story page opens no fold"


# ---- AC 2: the journey -----------------------------------------------------------

def _doc_ids(html):
    """Ids an old link can target: the sections, and the four MCP cards (#verifier and its siblings)."""
    ids = [sid for sid, _ in top_level_sections(html)]
    ids += re.findall(r'<div class="card agent-card" id="([^"]+)"', html)
    return ids


def _journey_steps():
    body = section(index_html(), "journey")
    lists = re.findall(r"<ol\b[^>]*>(.*?)</ol>", body, re.DOTALL)
    assert len(lists) == 1, f"journey must hold one ordered list, found {len(lists)}"
    return re.findall(r"<li\b[^>]*>(.*?)</li>", lists[0], re.DOTALL)


def test_journey_is_an_ordered_list_of_five_steps_each_linking_into_the_docs():
    steps = _journey_steps()
    assert len(steps) == 5, f"journey has {len(steps)} steps, want 5"
    known = set(_doc_ids(docs_html()))
    for step in steps:
        links = re.findall(r'href="docs\.html#([^"]+)"', step)
        assert links, f"journey step has no link into docs.html: {step[:60]!r}"
        assert all(link in known for link in links), f"journey links to an id docs.html lacks: {links}"


def test_journey_marks_the_users_two_steps_with_a_text_label():
    steps = _journey_steps()
    labelled = ["Your step" in " ".join(visible_words(s)).replace("  ", " ") for s in steps]
    assert labelled == [True, False, False, False, True], (
        f"the ask and merge steps (and only those) carry the text label 'Your step': {labelled}"
    )


# ---- AC 3: reading budget and plain words -----------------------------------------

def test_main_holds_at_most_300_words():
    words = visible_words(_main(index_html()))
    assert len(words) <= WORD_CAP, f"index.html <main> shows {len(words)} words, cap {WORD_CAP}"


@pytest.mark.parametrize("term", BANNED_TERMS)
def test_no_internal_term_on_the_story_page(term):
    heard = heard_text(index_html())
    hit = re.search(rf"(?<![\w-]){term}(?![\w-])", heard, re.IGNORECASE)
    assert not hit, f"index.html shows the internal term {hit.group(0)!r} (D4)"


def test_minimal_and_extended_are_each_named_once():
    text = " ".join(visible_words(_main(index_html()))).lower()
    for word in ("minimal", "extended"):
        assert len(re.findall(rf"\b{word}\b", text)) == 1, f"{word!r} must be named once on index.html"


def test_story_page_shows_no_project_state():
    html = _no_comments(index_html())
    assert not re.search(r"\bT\d{3}\b", html), "task ID on the story page"
    for word in ("KANBAN", "In Progress", "Ready for Review"):
        assert word not in html, f"{word!r} on the story page"


# ---- AC 4: the stops screen is true of real hooks ----------------------------------

def _wired_hook_scripts():
    with open(SETTINGS_JSON, encoding="utf-8") as f:
        settings = json.load(f)
    out = set()
    for entries in settings.get("hooks", {}).values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                out.update(re.findall(r"([A-Za-z0-9_]+\.py)", hook.get("command", "")))
    return out


def test_every_stop_names_a_real_wired_hook_in_a_comment_beside_it():
    body = section(index_html(), "stops")
    pairs = re.findall(r"<li\b", re.search(r"<ul\b[^>]*>(.*?)</ul>", body, re.DOTALL).group(1))
    comments = re.findall(r"<!--\s*hook:\s*(.*?)\s*-->", body)
    assert 3 <= len(pairs) <= 5, f"stops holds {len(pairs)} pairs, want 3 to 5"
    assert len(comments) == len(pairs), f"{len(pairs)} pairs but {len(comments)} hook comments"
    wired = _wired_hook_scripts()
    for name in comments:
        assert re.fullmatch(r"[A-Za-z0-9_]+\.py", name), f"hook comment is not a file name: {name!r}"
        assert os.path.isfile(os.path.join(HOOKS_DIR, name)), f"stops names a hook file that does not exist: {name}"
        assert name in wired, f"{name} exists but settings.json does not wire it"
    # each comment sits directly before its own <li>
    assert len(re.findall(r"<!--\s*hook:[^>]*-->\s*<li\b", body)) == len(pairs)


def test_stops_says_the_checks_run_on_claude_code_only():
    text = " ".join(visible_words(section(index_html(), "stops")))
    assert "Claude Code only" in text, "stops must say the checks run on Claude Code only"
    assert "Codex" in text and "Cursor" in text


# ---- the other screens ---------------------------------------------------------------

def test_hero_has_the_install_command_a_copy_button_and_one_docs_link():
    body = section(index_html(), "hero")
    box = re.search(r'<div class="codebox">(.*?)</div>', body, re.DOTALL)
    assert box and ONE_LINE_INSTALL in box.group(1), "hero lacks the install command in a codebox"
    button = re.search(r"<button\b[^>]*>", box.group(1))
    assert button and 'type="button"' in button.group(0) and re.search(r'aria-label="Copy [^"]+"', button.group(0))
    assert re.findall(r'href="docs\.html"', body) == ['href="docs.html"'], "hero must hold one link to docs.html"


def test_paths_splits_one_question_into_a_fast_and_a_full_path_with_an_example_each():
    body = section(index_html(), "paths")
    text = " ".join(visible_words(body))
    assert "Small or big job?" in text
    branches = re.search(r'<ul class="flow-branches">(.*?)</ul>', body, re.DOTALL)
    assert branches, "paths has no .flow-branches list"
    items = re.findall(r"<li\b[^>]*>(.*?)</li>", branches.group(1), re.DOTALL)
    assert len(items) == 2 and all("Example" in " ".join(visible_words(i)) for i in items), items


def test_deeper_has_four_cards_that_link_into_the_docs_and_one_settings_tool_link():
    body = section(index_html(), "deeper")
    cards = re.findall(r"<li\b[^>]*>(.*?)</li>", re.search(r"<ul\b[^>]*>(.*?)</ul>", body, re.DOTALL).group(1), re.DOTALL)
    assert len(cards) == 4, f"deeper has {len(cards)} cards, want 4"
    titles = [" ".join(visible_words(re.search(r"<h3\b[^>]*>(.*?)</h3>", c, re.DOTALL).group(1))) for c in cards]
    assert titles == ["Agents", "Skills", "Memory", "Add-ons"], titles
    known = set(_doc_ids(docs_html()))
    for c in cards:
        links = re.findall(r'href="docs\.html#([^"]+)"', c)
        assert links and all(link in known for link in links), f"card links {links}"
    addons = re.findall(r'href="docs\.html#([^"]+)"', cards[3])
    assert "packs" in addons and "mcps" in addons, "Add-ons covers packs and MCPs"
    assert 'href="docs.html#settings-tool"' in body, "deeper links to the Settings tool"


def test_every_flow_on_the_story_page_is_a_list():
    html = index_html()
    for sid in ("journey", "paths", "stops", "deeper"):
        assert re.search(r"<(?:ol|ul)\b", section(html, sid)), f"#{sid} holds no list"
        assert not re.search(r"<table\b", section(html, sid)), f"#{sid} lays out a flow in a table"


def test_story_page_names_the_shipping_version():
    with open(RUNBOOK, encoding="utf-8") as f:
        log = re.search(r"## Release Log(.*?)(?=\n## |\Z)", f.read(), re.DOTALL).group(1)
    version = re.findall(r"^\|\s*(v\d+\.\d+\.\d+)\s*\|", log, re.MULTILINE)[-1]
    assert f"supervisor kit &middot; {version}" in index_html()


# ---- AC 5: docs.html holds every section and the three Settings tool scripts ---------

def test_docs_holds_all_17_section_ids_in_the_old_order():
    base = _baseline()
    assert len(base["sections"]) == 17
    assert [sid for sid, _ in top_level_sections(docs_html())] == base["sections"]


@pytest.mark.parametrize("script_id", SCRIPT_IDS)
def test_settings_tool_script_blocks_are_byte_identical_to_the_old_page(script_id):
    block = script_block(docs_html(), script_id)
    assert hashlib.sha256(block.encode("utf-8")).hexdigest() == _baseline()["scripts"][script_id], (
        f"<script id={script_id}> on docs.html differs from index.html at 09d2544c"
    )


# ---- AC 6: no sentence is lost --------------------------------------------------------

def test_every_paragraph_item_cell_and_definition_of_the_old_page_is_on_docs():
    now = set(sentence_hashes(docs_html()))
    missing = [(h, t) for h, t in _baseline()["sentences"] if h not in now]
    assert not missing, f"{len(missing)} text(s) lost from docs.html: {missing[:5]}"


def test_the_baseline_is_not_empty():
    assert len(_baseline()["sentences"]) > 300


# ---- AC 7: old links keep working -----------------------------------------------------

def _redirect_script():
    for body in re.findall(r"<script>(.*?)</script>", index_html(), re.DOTALL):
        if "location.replace" in body:
            return body
    raise AssertionError("index.html has no inline script that calls location.replace")


def _redirect_ids():
    m = re.search(r"var\s+ids\s*=\s*\[(.*?)\]", _redirect_script(), re.DOTALL)
    assert m, "redirect script holds no `var ids = [...]` list"
    return re.findall(r'"([^"]+)"', m.group(1))


def test_redirect_id_list_equals_the_link_target_ids_of_docs():
    assert sorted(_redirect_ids()) == sorted(_doc_ids(docs_html()))


def _run_redirect(hash_value):
    """Run the inline script in node with a fake `location`; return the replace() argument or None."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    harness = (
        "const calls = []; const location = { hash: process.argv[1], replace: (u) => calls.push(u) };"
        "new Function('location', require('fs').readFileSync(0, 'utf8'))(location);"
        "console.log(JSON.stringify(calls));"
    )
    out = subprocess.run([node, "-e", harness, hash_value], input=_redirect_script(),
                         capture_output=True, text=True, check=True).stdout
    calls = json.loads(out)
    return calls[0] if calls else None


def test_a_docs_hash_on_the_story_page_replaces_the_location_with_docs():
    assert _run_redirect("#hooks") == "docs.html#hooks"
    assert _run_redirect("#verifier") == "docs.html#verifier"


def test_a_hash_that_is_not_a_docs_id_stays_on_the_page():
    for hash_value in ("", "#", "#journey", "#nonsense", "#hooks-x"):
        assert _run_redirect(hash_value) is None, hash_value


def test_the_redirect_never_assigns_location_so_back_is_not_trapped():
    script = _redirect_script()
    assert not re.search(r"location(?:\.href)?\s*=[^=]", script), "assigning location adds a Back-button trap"


# ---- AC 8: the two pages link to each other; the story has no sidebar ------------------

def _page_nav(html):
    header = re.search(r"<header\b[^>]*>(.*?)</header>", html, re.DOTALL).group(1)
    nav = re.search(r'<nav\b[^>]*class="page-nav"[^>]*>(.*?)</nav>', header, re.DOTALL)
    assert nav, "header has no .page-nav"
    return re.findall(r"<a\b([^>]*)>(.*?)</a>", nav.group(1), re.DOTALL)


def test_each_page_links_to_the_other_in_its_header_and_marks_itself_current():
    for html, current in ((index_html(), "Home"), (docs_html(), "Docs")):
        links = [(re.search(r'href="([^"]*)"', a).group(1), " ".join(visible_words(t)), 'aria-current="page"' in a)
                 for a, t in _page_nav(html)]
        assert [(h, t) for h, t, _ in links] == [("index.html", "Home"), ("docs.html", "Docs")], links
        assert [t for _, t, c in links if c] == [current], f"aria-current must mark {current} only: {links}"


def test_the_story_page_has_no_sidebar_and_no_menu_toggle():
    html = index_html()
    for marker in ('id="sidebar"', 'id="site-nav"', "<aside", "nav-toggle", "nav-group-title"):
        assert marker not in html, f"story page holds {marker}"


def test_the_family_nav_stays_reachable_on_the_story_page_below_900px():
    html = index_html()
    assert re.search(r'<nav\b[^>]*class="family-nav family-nav-drawer"', html), (
        "index.html has no drawer family nav; the header copy is hidden below 900px"
    )


# ---- AC 9: design system only ------------------------------------------------------------

@pytest.mark.parametrize("path", [INDEX, DOCS])
def test_no_hex_colour_and_no_third_party_asset_on_either_page(path):
    html = _read(path)
    stripped = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    assert not re.search(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![\w-])", stripped), "hex colour in page"
    assert not re.search(r"\b(?:rgba?|hsla?)\(", html), "colour function in page"
    for tag in re.findall(r"<(?:link|script)\b[^>]*>", html):
        for value in re.findall(r'\b(?:href|src)="([^"]*)"', tag):
            if tag.startswith("<link") and not value.startswith("data:") or tag.startswith("<script"):
                assert not re.match(r"^(?:https?:)?//", value), f"third-party asset: {tag}"
    assert 'href="theme.css"' in html


def test_the_story_page_carries_no_style_block_of_its_own():
    assert "<style" not in index_html(), "shared and story rules belong in theme.css (D1)"


def test_story_flows_stack_at_768px():
    css = re.sub(r"/\*.*?\*/", "", theme_css(), flags=re.DOTALL)
    m = re.search(r"@media \(max-width: 768px\)\s*\{", css)
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        i += 1
    phone = css[m.end():i - 1]
    for selector in (".story-stops", ".story-cards"):
        assert selector in phone, f"{selector} is not restacked at 768px"
