"""T276: the Windows beta writes down what it does not claim, and gives a human a manual end-to-end check.

Two open risks cannot be proven from Linux: installing the kit as a Claude Code plugin on Windows
(`plugin/` is built from git symlinks) and whether the agent-write deny rule matches Windows paths.
The ADR addendum says so, and `docs/windows-manual-checklist.md` tells a person how to check both.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ADR = REPO / "docs" / "adr" / "0003-native-windows-support.md"
CHECKLIST = REPO / "docs" / "windows-manual-checklist.md"


def _addendum():
    text = ADR.read_text(encoding="utf-8")
    m = re.search(r"^### Addendum \(T276\b.*?(?=^#{1,3} |\Z)", text, re.M | re.S)
    assert m, "the ADR has no '### Addendum (T276' section"
    return m.group(0)


def test_adr_addendum_names_both_unverified_risks():
    body = _addendum().lower()
    assert "plugin" in body and "symlink" in body and "unverified" in body
    assert "deny" in body and "windows-manual-checklist.md" in body
    assert "setup.ps1" in body, "the addendum must name the supported Windows install path"


def test_checklist_has_the_end_to_end_steps():
    assert CHECKLIST.is_file(), "docs/windows-manual-checklist.md is missing"
    text = CHECKLIST.read_text(encoding="utf-8")
    for needle in ("/wake", "minimal", "blocked", "auto verify", "deny", "plugin", "Result:"):
        assert needle.lower() in text.lower(), f"checklist lacks: {needle}"
    steps = re.findall(r"^\d+\. ", text, re.M)
    assert len(steps) >= 8, "the checklist needs at least 8 numbered steps"
