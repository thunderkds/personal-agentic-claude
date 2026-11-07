"""
T279 - the Home and Docs links in the top nav reach 44px wide on phones.
Spec: tasks/TASK_GUIDE_T279.md (AC 1, 3). The older test_touch_targets_reach_44px_below_720px
checks min-height only, so it missed the width (T278 ux-evaluate finding B-d).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(ROOT, "site", "theme.css")


def _css():
    with open(THEME, encoding="utf-8") as f:
        return re.sub(r"/\*.*?\*/", "", f.read(), flags=re.DOTALL)


def _phone_block(css):
    m = re.search(r"@media \(max-width: 719px\)\s*\{", css)
    assert m, "no phone (max-width: 719px) block"
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        i += 1
    return css[m.end():i - 1]


def _bodies(css, selector):
    return [b for sel, b in re.findall(r"([^{}]+)\{([^{}]*)\}", css) if selector in [s.strip() for s in sel.split(",")]]


def test_page_nav_links_are_44px_wide_and_centred_on_phones():
    bodies = _bodies(_phone_block(_css()), ".page-nav a")
    assert len(bodies) == 1, "one .page-nav a rule in the phone block"
    assert "min-width: 44px" in bodies[0], ".page-nav a lacks min-width: 44px on phones"
    assert "justify-content: center" in bodies[0], ".page-nav a label is not centred"
    assert "min-height: 44px" in bodies[0]


def test_width_rule_stays_inside_the_phone_block():
    css = _css()
    outside = css.replace(_phone_block(css), "")
    for b in _bodies(outside, ".page-nav a"):
        assert "min-width" not in b, "min-width on .page-nav a must not leak above 719px"
