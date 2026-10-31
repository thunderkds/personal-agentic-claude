"""
T207 — visual-first landing page. A diagram leads each heavy section of
site/index.html and the long explanation folds into a <details class="more">
block under it. Spec: tasks/TASK_GUIDE_T207.md (AC 1-9, D1-D7).

The page's facts are pinned by tests/test_site_content.py; this file pins the
shape: where the visuals sit, how many words show on first load, that no
sentence was lost when prose moved into a fold, and that the visuals follow the
design system (tokens only, accessible lists, stacked on phones).
"""
import hashlib
import html as _html
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "site", "index.html")
THEME = os.path.join(ROOT, "site", "theme.css")

VISUAL_SECTIONS = ["tracks", "install", "update-flow", "hooks", "agent-roles", "memory-system"]
SECTION_WORD_CAP = 150          # D3: words visible on first load, per section
PAGE_WORD_SHARE = 0.60          # D3: the page keeps at most 60% of its old reading load
BASELINE_VISIBLE_WORDS = 3124   # <main> at c00d0fe, outside details, pre, code, svg, script, style
SKIPPED = {"details", "pre", "code", "svg", "script", "style"}


def _page():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _theme():
    with open(THEME, encoding="utf-8") as f:
        return f.read()


def _section(section_id):
    m = re.search(r'<section id="%s">(.*?)</section>' % re.escape(section_id), _page(), re.DOTALL)
    assert m, f'page has no <section id="{section_id}">'
    return m.group(1)


def _visual(section_id):
    """The one <div ... data-visual="id"> element of a section, balanced on <div>."""
    body = _section(section_id)
    starts = [m for m in re.finditer(r'<div\b[^>]*\bdata-visual="%s"[^>]*>' % re.escape(section_id), body)]
    assert len(starts) == 1, f"#{section_id} must hold exactly one data-visual=\"{section_id}\" element, found {len(starts)}"
    depth = 0
    for tag in re.finditer(r"<div\b|</div>", body[starts[0].start():]):
        depth += 1 if tag.group(0) == "<div" else -1
        if depth == 0:
            return body[starts[0].start():starts[0].start() + tag.end()]
    raise AssertionError(f"#{section_id} visual is not closed")


def _words_of(fragment):
    return _html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split()


class _Visible(HTMLParser):
    """Words of text outside details, pre, code, svg, script, style — what a reader sees on first load."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.depth = 0
        self.section = None
        self.per_section = {}
        self.total = 0

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            if self.depth == 0:
                self.section = dict(attrs).get("id")
            self.depth += 1
        if tag in SKIPPED:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in SKIPPED and self.skip:
            self.skip -= 1
        if tag == "section":
            self.depth -= 1
            if self.depth == 0:
                self.section = None

    def handle_data(self, data):
        if self.skip:
            return
        n = len(data.split())
        self.total += n
        if self.section:
            self.per_section[self.section] = self.per_section.get(self.section, 0) + n


def _visible():
    main = re.search(r"<main\b[^>]*>(.*)</main>", _page(), re.DOTALL).group(1)
    parser = _Visible()
    parser.feed(main)
    return parser


# ---- AC 1: one visual per heavy section, before its first fold ----------------

def test_each_visual_section_holds_one_visual_before_its_first_details_more():
    for sid in VISUAL_SECTIONS:
        body = _section(sid)
        assert body.count(f'data-visual="{sid}"') == 1, f"#{sid}: need exactly one data-visual"
        fold = body.find('<details class="more">')
        assert fold != -1, f'#{sid} has no <details class="more"> fold'
        assert body.index(f'data-visual="{sid}"') < fold, f"#{sid}: the visual must come before the fold"
        assert re.search(r'<details class="more">\s*<summary>Details</summary>', body), f"#{sid}: fold must open with <summary>Details</summary>"


def test_no_visual_marker_outside_its_own_section():
    marks = re.findall(r'data-visual="([^"]+)"', _page())
    assert sorted(marks) == sorted(VISUAL_SECTIONS), marks


# ---- AC 2: the tracks visual ---------------------------------------------------

def test_tracks_visual_names_both_outcomes_and_every_trigger():
    text = " ".join(_words_of(_visual("tracks"))).lower()
    for needle in ("extended track", "minimal track", "5-stage pipeline", "decision record",
                   "c2", "risk medium", "refactor", "migrate", "user data",
                   "more than one session or agent", "ui component", "yes", "no"):
        assert needle in text, f"tracks visual lacks {needle!r}"


def test_tracks_auto_flow_ends_at_done_and_a_lane_marks_merge_push_ship_as_the_users():
    visual = _visual("tracks")
    flows = re.findall(r"<ol\b[^>]*>(.*?)</ol>\s*(?=<|$)", visual, re.DOTALL)
    auto = [f for f in flows if "[auto]" in f]
    assert auto, "tracks visual has no auto-mode flow naming [auto]"
    steps = re.findall(r"<li\b[^>]*>(.*?)</li>", auto[0], re.DOTALL)
    assert len(steps) >= 5, steps
    assert "Done" in " ".join(_words_of(steps[-1])), "the auto flow must end at Done"
    for earlier in steps[:-1]:
        assert "Done" not in _words_of(earlier)
    lane = re.search(r'<div\b[^>]*class="flow-lane"[^>]*data-owner="you"[^>]*>(.*?)</div>', visual, re.DOTALL)
    assert lane, 'no <div class="flow-lane" data-owner="you"> in the tracks visual'
    lane_text = " ".join(_words_of(lane.group(1))).lower()
    for word in ("yours", "merge", "push", "ship"):
        assert word in lane_text, f"the user's lane lacks {word!r}"
    assert visual.index("flow-lane") > visual.index(auto[0][:40]), "the lane sits after the auto flow"


# ---- AC 3: the hooks visual ----------------------------------------------------

def test_hooks_visual_has_the_three_events_in_order_and_labels_every_hook():
    visual = _visual("hooks")
    pos = [visual.find(e) for e in ("PreToolUse", "PostToolUse", "Stop")]
    assert all(p != -1 for p in pos) and pos == sorted(pos), f"event order in the lifecycle strip: {pos}"
    items = re.findall(r'<li class="(is-(?:block|advise|inert))">(.*?)</li>', visual, re.DOTALL)
    assert len(items) >= 8, f"expected the hook items, found {len(items)}"
    for kind, body in items:
        label = re.match(r'\s*<span class="tag tag-(?:block|advise|inert)">(blocks|asks|advises|inert)</span>', body)
        assert label, f"hook item has no text label (colour alone is not enough): {body[:60]!r}"
    labels = {re.match(r'\s*<span[^>]*>(\w+)</span>', b).group(1) for _, b in items}
    assert {"blocks", "advises"} <= labels


# ---- AC 4: the reading budget (the ratchet) ------------------------------------

def test_every_section_shows_at_most_150_words_on_first_load():
    per = _visible().per_section
    assert per, "no sections measured — fixture broken"
    over = {k: v for k, v in per.items() if v > SECTION_WORD_CAP}
    assert not over, f"section(s) over {SECTION_WORD_CAP} visible words: {over}"
    for sid in VISUAL_SECTIONS:
        assert sid in per, f"#{sid} not measured"


def test_the_page_shows_at_most_60_percent_of_the_old_words():
    total = _visible().total
    limit = int(BASELINE_VISIBLE_WORDS * PAGE_WORD_SHARE)
    assert total <= limit, f"page shows {total} words on first load, limit {limit} (60% of {BASELINE_VISIBLE_WORDS})"


# ---- AC 5: no sentence is lost -------------------------------------------------

class _Sentences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.out, self.skip = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li") and not self.skip:
            self.stack.append([])

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag in ("p", "li") and not self.skip and self.stack:
            self.out.append(" ".join("".join(self.stack.pop()).split()))

    def handle_data(self, data):
        if not self.skip:
            for buf in self.stack:
                buf.append(data)


def _sentence_hashes():
    parser = _Sentences()
    parser.feed(_page().replace("<wbr>", ""))
    return {hashlib.sha1(t.encode()).hexdigest()[:12] for t in parser.out if t}


# Every <p>/<li> text at c00d0fe: (sha1 prefix of the whitespace-normalised text, its first 48 characters).
# A text that a visual now says in its own words may be dropped only by listing it in DUPLICATES_OF_A_VISUAL_LABEL.
BASELINE_SENTENCES = [
    ("c420931479e3", '// overview'),
    ("6bf2dad97765", 'Quick reference'),
    ("8ac7aa173f26", 'What you get'),
    ("1ee6cd82f344", 'Minimal and extended tracks'),
    ("d36721703315", '// getting started'),
    ("fd6c3ebf7bef", 'Install'),
    ("45bd51208d7e", 'Update flow'),
    ("a0ff84a8c3cb", 'Settings tool'),
    ("c84504c154df", 'Install variants'),
    ("12f790f63dbb", '// the team'),
    ("af4a53331b06", 'Agent roles'),
    ("e09212c7d3ea", 'Skills'),
    ("4bd8f3f03a57", 'Hooks'),
    ("63c7238ea2bb", 'Agent focus'),
    ("0b8787aa9fbc", '// reference'),
    ("db866831c3d0", 'Packs'),
    ("87b7c08baed1", 'Providers'),
    ("b463aa9e4948", 'Repository layout'),
    ("8180f342a27c", 'Memory system'),
    ("fcc695b67157", 'MCPs'),
    ("6bf5da9c080b", 'Options'),
    ("ba8c2d4b7a30", '> multi-agent supervisor framework'),
    ("a4d2005f8409", 'A multi-agent supervisor framework: one Supervis'),
    ("766f417cb3d1", 'Pipeline — plan → spawn isolated sub-agents → re'),
    ("d98b0542dec7", 'Claude Code — the Supervisor session and its hoo'),
    ("1a5a290a34ba", 'Other providers (Codex, Cursor) — Codex reads th'),
    ("03c82a500ce0", 'View the Supervisor GitHub repository for the so'),
    ("9741d6fdd3e3", '4spawnable roles'),
    ("c281ee27472b", '33skills'),
    ("d3c9027831fe", '5blocking hooks (of 11)'),
    ("ad14bdffefcc", '6optional domain packs'),
    ("e6bc75bc7897", 'Four spawnable sub-agent roles, skills for every'),
    ("cdef968136ca", '00 Phase 0 · Initiation PRD.md'),
    ("30979276a6f0", '0.5 Stage 0.5 · Grill + brainstorm BRAINSTORMING'),
    ("08001aef9d90", '01 Stage 1 · Environment setup codebase map, CLI'),
    ("c5ffe735f0f0", '1.5 Stage 1.5 · Sub-agent team agent roster'),
    ("c39729254e09", '02 Stage 2 · Plan PROJECT_SPEC + TASK_GUIDEs'),
    ("e2a945b4c57b", '03 Stage 3 · Parallel execution code in isolated'),
    ("09969b0392fe", '04 Stage 4 · Review findings + Evidence'),
    ("0535d46fdcee", '05 Stage 5 · Integrate verify, merge, release pl'),
    ("221b92270871", 'Small work runs on the minimal track. Big or ris'),
    ("fff3a4c76281", 'The line is a statement, not a question: Track: '),
    ("67e04a674a4a", 'Extended track if any of these is true: Complexi'),
    ("1a657ee69be4", 'Minimal track otherwise. The Supervisor writes t'),
    ("2bddf7c6882e", 'Your override: reply full or minimal at any time'),
    ("e1051d33825b", 'Put the exact tag [auto] in your request. The Su'),
    ("8922f359fa75", 'Low: the Supervisor decides and logs the reason.'),
    ("6a6801ff03e3", 'Medium: a Debate with 2 Advocates.'),
    ("fa521d7fa483", 'High: a Debate with 3 Advocates, and at least on'),
    ("059208c43012", 'In a Debate, read-only Advocate agents argue the'),
    ("02fcd665c525", 'A Stop hook checks the final report before the r'),
    ("f9119b4d4fa8", 'Prerequisites: an existing git repo, and git, cu'),
    ("a80b0e28e003", 'Restart Claude Code after install so it picks up'),
    ("e433c21e0474", 'Installing into an existing project never delete'),
    ("b6ad96bcde28", 'After the kit version it replaces: CLAUDE.md.bak'),
    ("b2393edfb6d3", "Today's date, such as CLAUDE.md.bak-20261008, wh"),
    ("f850d141ad55", 'A name already taken gets .1, .2, … so no backup'),
    ("f883d1b44782", 'The command takes no options — you choose from n'),
    ("aa0d503a8641", 'What to do — 1) Install 2) Cancel (or Update / R'),
    ("93c2366f8631", 'Which CLIs — 1) Claude Code 2) Codex. Pick one o'),
    ("1444f1952efb", 'New or existing project — 1) New project 2) Exis'),
    ("e09fd1287095", 'A plan then lists the CLIs, the project type and'),
    ("ec17b5c44832", 'No terminal (CI, containers) — no menus: the def'),
    ("4b8d2baa9c28", 'Anything on the command line — it stops with not'),
    ("445d1448d916", 'To pull in newer Easy Kit changes later, run the'),
    ("9ce95fee793d", 'There is one command: run the same install line '),
    ("16c5206f47d9", 'Before changing anything it shows a plan — files'),
    ("9c397a88681a", 'If the plan lists files you edited, one question'),
    ("120bcc17b417", '1 asks about each file, as in the table below. E'),
    ("f21e3936dc93", '2 moves each file to <file>.bak-<commit>, then o'),
    ("62424fc4176f", '3 keeps every edit. 4 changes nothing.'),
    ("ee7759ad12fe", 'Answer n to go back to the menu. Cancel changes '),
    ("c42281295f53", 'No terminal (CI, containers, ssh without -t) — n'),
    ("a2823f104444", 'An existing update.sh in a checkout still works:'),
    ("72307e6eceac", 'Update re-fetches the framework fresh, then comp'),
    ("666a1ddabeee", "The kit's hooks are reconciled into it."),
    ("e46bdecab7d8", "The kit's permissions.deny entries are appended "),
    ("6d9a29dfa7be", "The kit's allow or ask rules are never copied."),
    ("477e674c2e50", 'If it cannot be merged — invalid JSON, a symlink'),
    ("cdaba6efd60d", 'In .claude/harness-lock.json, which also records'),
    ("fa1bd08fbe2b", 'Every Update run adds a dated entry to the top o'),
    ("4f7541f83254", 'The log holds paths, outcomes and counts only, n'),
    ("be6b1a1524e6", 'CLAUDE.md is delivered from the same source the '),
    ("f2e8bb73877a", 'Easy Kit stores no list of CLIs. Update asks no '),
    ("b6f9614be110", 'A Codex-only project refreshes .codex/skills/ an'),
    ("ceb7d0aa2da9", 'A Claude project keeps its .claude/{skills,agent'),
    ("bbe6856a7c4e", 'Adding a CLI later: run the same command, choose'),
    ("ad490cd3fbe4", 'One edge worth knowing: if both .claude/skills a'),
    ("9d31c0d5f552", 'With nothing present, the project is indistingui'),
    ("425dc05dbb62", 'Pick the Claude Code settings you want and copy '),
    ("d55aff6b3b5b", 'At Stage 1 the Supervisor offers the profiles be'),
    ("9f191b70c54d", 'This tool needs JavaScript. Without it, read the'),
    ("545151b61f0f", 'Runs in your browser only. Nothing is sent or sa'),
    ("88c3a7449d90", 'Fork install — export your username first and sw'),
    ("8186d3c8ea7b", 'New vs. existing (brownfield) project — a menu c'),
    ("249e6e732b46", '2) Existing / legacy project — for an existing c'),
    ("54546dee64d4", '1) New project — the default with no terminal. Y'),
    ("17fa6b77d592", 'Four roles are directly spawnable via the Agent '),
    ("77d0fb13dfa2", 'Use when a TASK_GUIDE assigns server-side work —'),
    ("32286dd49f69", 'Core backend engineering role — server-side APIs'),
    ("04d85d6ac68a", 'Use when a task needs worktree setup, dependency'),
    ("b661452ddde0", 'Environment and shared-config specialist — workt'),
    ("d469edbbe2b8", 'Use when a TASK_GUIDE assigns client-side work —'),
    ("b5b7b63cae46", 'Core frontend engineering role — UI components, '),
    ("6d1e1f4569aa", 'Use when a task needs independent verification —'),
    ("f5e9d7a02f39", 'Quality and evaluation role — owns the smoke sui'),
    ("941282602229", 'Base template inherited by all four roles above.'),
    ("10b777ecffa6", 'One inline instruction set loaded per invocation'),
    ("08ca6d9dc109", 'brainstormingideate'),
    ("c424a50494ca", 'Stage 0.5 — Requirement Grilling / Brainstorming'),
    ("4b7804edc105", 'git-guardrails-claude-codemap-codebasesettings-s'),
    ("0d64e298bb52", 'Stage 1 — Environment & Provider Setup git-guard'),
    ("02dc3d4dceda", 'craft-agent'),
    ("d790b2230f59", 'Stage 1.5 — Sub-Agent Architecture craft-agent'),
    ("6ea65e8cc43f", 'grill-with-docsto-issues'),
    ("fc1f42f9b400", 'Stage 2 — Intent Transformation grill-with-docst'),
    ("221cf5685858", 'tddbugfixdiagnosecraft-spawn-promptmigration-saf'),
    ("17429ff8e0b6", 'Stage 3 — Parallel Execution via Isolation tddbu'),
    ("7d479d188af6", 'blast-radiuscode-reviewhtml-reportscore'),
    ("838e9632acef", 'Stage 4 — Review blast-radiuscode-reviewhtml-rep'),
    ("1c7b48c41f2b", 'shipdelivery-report'),
    ("9250c0a6cefa", 'Stage 5 — Integration & Verification shipdeliver'),
    ("9d5bff6dc560", 'compact-advisorcompact-memorycompoundcompound-re'),
    ("10af79f996d5", 'Deterministic shell/python guardrails the harnes'),
    ("7aa92feed719", 'The wiring lives in .claude/settings.json. Both '),
    ("05793001ea18", 'It merges into a .claude/settings.json your proj'),
    ("c409316bd3cf", 'The spawn prompt has no memory slice or no **Sta'),
    ("a5673f4c4d97", 'A Depends on task is not Done'),
    ("cfc737041c27", "A task's Demonstration BEFORE is still blank"),
    ("26fa89d6f34a", '.env*, secrets, production configs, infra.'),
    ("e3ccfe0ba5eb", 'The reminder is for the Supervisor. The hand mov'),
    ("f04bcc738253", 'Each line is linked to the one before by a hash '),
    ("d42b88c2694c", 'The report is in its file, marked Mode: auto'),
    ("b4d29fa04f9c", 'Each Medium/High-risk choice was argued by 2 or '),
    ("d8be3f58ad7a", 'Stage 4 review ran'),
    ("cf3a05f4f916", 'It writes the verify row and a run record'),
    ("9e76917ec693", 'The merge gate accepts that row only with the re'),
    ("d695b43c2a60", 'The merge stays yours'),
    ("756cca8ae428", 'Each row is a mechanism the kit applies, and the'),
    ("d031d4d9e52d", 'Any memory/decisions.md entry that lists those f'),
    ("a868f12c63ef", 'Code, exact error text, file paths, commands and'),
    ("faec5d05b7bc", "Where the kit repository's transcript meter is p"),
    ("8944a148255d", 'Packs add domain-specific agents and skills on t'),
    ("d53024aa523d", 'The installer never asks about packs.'),
    ("03c2f6556af0", 'Your Supervisor recommends packs for your projec'),
    ("61f19ba8be25", 'Update keeps the packs/ catalog current like any'),
    ("9160f8ef6633", 'AGENTS.md plus docs/claude-md/ stay the one prim'),
    ("e384f784f24a", "The kit's non-negotiable rules (the four Karpath"),
    ("0b3ee3f81ee6", "Codex executes the kit's skills directly, by nam"),
    ("a006ebe681ba", "Each skill's body is capped at 8 KB per Codex's "),
    ("183089d98455", 'A skill over the cap is skipped with a named, lo'),
    ("c4c0e14260fd", "Four of this kit's skills currently exceed it an"),
    ("19affec83916", 'What a non-Claude provider still cannot enforce:'),
    ("d51a57bb889f", 'code-review, security-review, verify, ship, migr'),
    ("96780aea2886", 'Those stay on the Claude supervisor: an adapter '),
    ("f2fc48ba4744", 'The mandatory folder structure created by instal'),
    ("4bbe506f5e25", 'A two-tier hot/cold memory design keeps agents a'),
    ("432ea0c9e64e", 'Pasted into each sub-agent spawn prompt: the ind'),
    ("d618329ebba1", 'Three separate companion tools, not part of this'),
    ("f0c3d5d8d5c1", 'A separate companion tool, not part of this kit:'),
    ("82151340a26d", 'No LLM and no model API key — ratings are determ'),
    ("36e9d8d7e911", 'Seven independently callable dimensions, from ar'),
    ("a0ed38db62ed", 'Auditable coverage — a "found 4/6" always shows '),
    ("bd34c7b7a294", 'Read-only and local — never runs the target repo'),
    ("e58283d61023", "Kit-aware mode treats this kit's specs, task gui"),
    ("42d3b4a36e1d", 'easy-verifier-mcp on GitHub · Easy Verifier site'),
    ("8323531822d2", 'A separate companion tool, not part of this kit:'),
    ("1134e5921315", 'Playwright browser automation that an agent such'),
    ("dfb7adc24dee", 'Returns a JSON and HTML report with screenshots '),
    ("49638dc71ab2", 'Separates claims from observations: ui_assert fa'),
    ("e8f0c10e52aa", 'Captures console errors, page errors and failed '),
    ("62e37483691f", 'Version 1 covers web only (Chromium) and runs lo'),
    ("efbda6d73eef", 'easy-ui-mcp on GitHub'),
    ("ffa5eb504d8d", 'A separate companion tool, optional and not part'),
    ("6e5d971e8e6a", 'Without it installed, the kit runs as before — i'),
    ("d80db43ad01d", 'After a long answer it saves a local note; your '),
    ("27833cf75824", 'MCP tools memory_search, memory_read, memory_lis'),
    ("162b39143c5f", 'One file, standard library only; notes are saved'),
    ("4a9d43367d1a", 'A working prototype: about 28% fewer tokens in s'),
    ("685318ee77a9", 'easy-memory-mcp on GitHub'),
]
# Allowed removals: hash -> reason. Nothing is allowed because a visual repeats it; the two entries are a stale claim and a reworded sentence.
DUPLICATES_OF_A_VISUAL_LABEL = {
    # The old tracks paragraph held two stale sentences: "Without [auto], you type /verify." and
    # "Merge, push and Done stay with you." It is replaced by three paragraphs that follow
    # docs/claude-md/tracks.md `### Auto verify (Stop hook)` and `### Auto close-out`.
    "02fcd665c525": "stale since T203/T189 (Supervisor decision)",
    # T221 AC 7: an Advocate now frames the problem and proposes its own option, so "argue the options" is reworded.
    "059208c43012": "reworded by T221 AC 7 (Advocates propose, not argue)",
}


def test_every_paragraph_and_list_item_from_before_is_still_on_the_page():
    now = _sentence_hashes()
    missing = [(h, t) for h, t in BASELINE_SENTENCES if h not in now and h not in DUPLICATES_OF_A_VISUAL_LABEL]
    assert not missing, f"{len(missing)} sentence(s) lost: {missing[:5]}"


# ---- AC 6: accessible visuals --------------------------------------------------

def test_every_visual_is_a_list_and_every_svg_is_named():
    for sid in VISUAL_SECTIONS:
        visual = _visual(sid)
        assert re.search(r"<(?:ol|ul)\b", visual), f"#{sid} visual holds no <ol>/<ul>: a flow must be a list"
        assert not re.search(r"<table\b", visual), f"#{sid} visual lays a flow out in a table"
    for svg in re.findall(r"<svg\b[^>]*>.*?</svg>", _page(), re.DOTALL):
        if 'aria-hidden="true"' in svg.split(">", 1)[0]:
            continue
        assert 'role="img"' in svg and "<title" in svg and "<desc" in svg, f"unnamed svg: {svg[:80]!r}"


def test_arrows_are_not_read_aloud():
    css = _theme()
    for content in re.findall(r"content:\s*([^;]+);", re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)):
        if re.search(r"\\2[01]9[0-9a-fA-F]", content):
            assert content.strip().endswith('/ ""'), f"arrow glyph with a spoken alt text: {content}"
    for sid in VISUAL_SECTIONS:
        assert not re.search(r"[→←↑↓➜►▶]", " ".join(_words_of(_visual(sid)))), f"#{sid}: arrow glyph in the reading text"


# ---- AC 7: design system only ---------------------------------------------------

def test_no_hex_colour_outside_the_token_block_and_no_third_party_asset():
    page = _page()
    assert not re.search(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![\w-])", re.sub(r"<script\b.*?</script>", "", page, flags=re.DOTALL)), \
        "hex colour in index.html"
    assert not re.search(r"\b(?:rgba?|hsla?)\(", page), "colour function in index.html"
    theme = _theme()
    outside_root = re.sub(r":root\s*\{.*?\n\}", "", re.sub(r"/\*.*?\*/", "", theme, flags=re.DOTALL), flags=re.DOTALL)
    assert not re.search(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![\w-])", outside_root), "hex colour in theme.css outside :root"
    assert "flow visuals (T207)" in theme, "theme.css has no flow-visuals block"
    flow_css = re.sub(r"/\*.*?\*/", "", theme[theme.index("flow visuals (T207)"):], flags=re.DOTALL)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(", flow_css), "colour literal in the flow CSS"
    for link in re.findall(r"<link\b[^>]*>", page):
        href = re.search(r'href="([^"]*)"', link)
        if href and not href.group(1).startswith("data:"):
            assert not re.match(r"^(https?:)?//", href.group(1)), f"third-party <link>: {link}"
    for script in re.findall(r"<script\b[^>]*>", page):
        assert "src=" not in script, f"external script: {script}"


def test_flow_text_pairs_meet_wcag_aa():
    tokens = dict(re.findall(r"(--[\w-]+):\s*(#[0-9A-Fa-f]{6})\s*;", _theme()))

    def lum(hex_):
        c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def ratio(a, b):
        hi, lo = sorted((lum(tokens[a]), lum(tokens[b])), reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    for fg in ("--text-strong", "--text", "--text-2", "--text-muted", "--accent"):
        for bg in ("--bg", "--bg-sunken"):
            assert ratio(fg, bg) >= 4.5, f"{fg} on {bg} is {ratio(fg, bg):.2f}:1"


# ---- D4 / D5: no motion; every flow stacks at 768px ----------------------------

def test_flows_use_no_animation_or_transition():
    css = re.sub(r"/\*.*?\*/", "", _theme(), flags=re.DOTALL)
    assert not re.search(r"\b(?:animation|transition)\s*:", css), "motion in theme.css"


def _media_block(css, query):
    m = re.search(re.escape(query) + r"\s*\{", css)
    assert m, f"no {query} block in theme.css"
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        i += 1
    return css[m.end():i - 1]


def test_every_flow_stacks_at_768px_and_the_long_ones_at_1100px():
    css = re.sub(r"/\*.*?\*/", "", _theme(), flags=re.DOTALL)
    phone = _media_block(css, "@media (max-width: 768px)")
    for selector in (".flow-row", ".flow-branches", ".flow-list", ".flow-map", ".flow-roles", ".flow-lane"):
        assert selector in phone, f"{selector} is not restacked at 768px"
    tablet = _media_block(css, "@media (max-width: 1100px)")
    assert ".flow-row.is-long" in tablet
    assert "flex-direction: column" in tablet


def test_long_flows_are_marked_is_long():
    assert 'class="flow flow-row is-long"' in _visual("tracks"), "the six-step auto flow must be is-long"
    assert 'is-long' in _visual("hooks"), "the five-part hook lifecycle must be is-long"
