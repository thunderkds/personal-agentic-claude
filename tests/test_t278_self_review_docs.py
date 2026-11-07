"""
T278 - site/docs.html shows the self-review loop as a flow diagram, words as labels only.
Spec: tasks/TASK_GUIDE_T278.md (AC 1-5). The facts come from skills/self-review/SKILL.md.
"""
import html as _html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "site", "docs.html")
ARIA = "The self-review loop, in order"
TITLE_CAP, META_CAP, LEAD_CAP, BLOCK_CAP = 4, 8, 15, 80
NEVER = ["edit kit files", "merge", "push", "call the network"]
BANNED = ("autonomous", "self-improving", "automatic")  # "automatically" contains "automatic"
ALLOWED_CLASSES = {"flow", "flow-row", "is-long", "flow-node", "step-no", "flow-title", "flow-meta",
                   "is-outcome", "flow-chips", "chip", "lead", "flow-visual"}


def _text(fragment):
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _block():
    """The diagram: from its heading to the end of the chips row, inside #skills."""
    with open(PAGE, encoding="utf-8") as f:
        page = f.read()
    section = re.search(r'<section id="skills">(.*?)</section>', page, re.DOTALL)
    assert section, 'page has no <section id="skills">'
    body = section.group(1)
    start = body.find("<h3><code>self-review</code>")
    assert start != -1, "no self-review heading in #skills"
    chips = body.index('<ul class="flow-chips"', start)
    end = body.index("</ul>", chips) + len("</ul>")
    return body[start:end]


def _nodes():
    flow = re.search(r'<ol class="flow flow-row is-long" aria-label="%s">(.*?)</ol>' % re.escape(ARIA),
                     _block(), re.DOTALL)
    assert flow, "no ol.flow with the self-review aria-label"
    return re.findall(r'<li class="(flow-node(?: is-outcome)?)">(.*?)</li>', flow.group(1), re.DOTALL)


def _chips():
    row = re.search(r'<ul class="flow-chips"[^>]*>(.*?)</ul>', _block(), re.DOTALL)
    assert row, "no flow-chips row"
    return [_text(c) for c in re.findall(r'<li class="chip">(.*?)</li>', row.group(1), re.DOTALL)]


def test_flow_has_six_nodes_in_order_and_the_last_is_the_outcome():  # AC 1, 2
    nodes = _nodes()
    assert len(nodes) == 6
    assert [c for c, _ in nodes[:5]] == ["flow-node"] * 5 and nodes[5][0] == "flow-node is-outcome"
    texts = [_text(b) for _, b in nodes]
    for i, needle in enumerate(["/self-review", "none", "miner", "up to 3 proposals", "approve", "kanban"]):
        assert needle in texts[i].lower(), f"node {i + 1} lacks {needle!r}: {texts[i]!r}"
    assert "normal pipeline" in texts[5]


def test_chips_row_lists_the_four_things_the_loop_never_does():  # AC 3
    assert _chips() == NEVER


def test_only_existing_flow_classes_are_used():  # AC 1
    used = set()
    for c in re.findall(r'class="([^"]+)"', _block()):
        used.update(c.split())
    assert used <= ALLOWED_CLASSES, f"unexpected classes: {used - ALLOWED_CLASSES}"
    assert "<p>" not in _block(), "no paragraph"


def test_words_stay_labels():  # AC 4
    block = _block()
    for title in re.findall(r'<span class="flow-title">(.*?)</span>', block, re.DOTALL):
        assert len(_text(title).split()) <= TITLE_CAP, f"title too long: {title!r}"
    for meta in re.findall(r'<span class="flow-meta">(.*?)</span>', block, re.DOTALL):
        assert len(_text(meta).split()) <= META_CAP, f"meta too long: {meta!r}"
    leads = re.findall(r'<p class="lead">(.*?)</p>', block, re.DOTALL)
    assert len(leads) <= 1
    for lead in leads:
        assert len(_text(lead).split()) <= LEAD_CAP
    assert len(_text(block).split()) <= BLOCK_CAP, f"{len(_text(block).split())} words, cap {BLOCK_CAP}"


def test_block_has_no_banned_claim():  # AC 5
    text = _text(_block()).lower()
    for word in BANNED:
        assert word not in text, f"banned word: {word}"
