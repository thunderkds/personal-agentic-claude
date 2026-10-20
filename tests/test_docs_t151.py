"""T151 drift test: docs and site describe what T144/T145/T148/T149 changed."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def _line_with(text, needle):
    for line in text.splitlines():
        if needle in line:
            return line
    raise AssertionError(f"no line contains {needle!r}")


STAGES = _read("docs", "claude-md", "pipeline-stages.md")
SITE = _read("site", "index.html")


def test_ac1_memory_injection_names_decisions_entries():
    line = _line_with(STAGES, "**Memory injection**")
    assert "decisions.md" in line and "**Files**" in line


def test_ac2_code_review_names_lane_check_three_dot_warn_only():
    assert re.search(r"scripts/lane_check\.py <guide> <base>\.\.\.HEAD", STAGES)
    idx = STAGES.index("scripts/lane_check.py")
    window = STAGES[idx:idx + 500]
    assert "warns" in window and "never blocks" in window


def test_ac3_ship_names_approval_and_smoke_test():
    line = _line_with(STAGES, "never auto-deploys")
    assert "Release Log" in line and "<version> @ <commit>" in line
    assert "smoke test" in line and "before the deploy" in line


def test_ac4_trace_hook_row():
    row = _line_with(SITE, "<code>post_tool_trace.py</code>")
    for needle in ("hash chain", "harness-anchors", "scripts/verify_trace.py"):
        assert needle in row


def test_ac5_memory_slice_rows_mention_decisions():
    row548 = _line_with(SITE, "<strong>Memory slice</strong>")
    assert "decisions.md" in row548
    row655 = _line_with(SITE, "<code>memory/MEMORY.md</code></td><td data-label=\"Tier\">Hot")
    assert "decisions.md" in row655


def test_ac6_permissions_claim_replaced():
    assert "your own permissions and your own hook entries are kept exactly" not in SITE
    assert "never touch your own permissions" not in SITE
    assert SITE.count("permissions.deny") >= 2
    assert SITE.count("kept") >= 1
