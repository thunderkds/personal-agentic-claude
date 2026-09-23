"""T115 D9 / AC8 — the live docs and the installer's own output agree that
Easy Kit takes no options.

Since T115 `setup.sh` accepts no arguments: the user picks CLIs and project
type from menus. A doc that still tells a user to type `--harness codex`, or
the `sh -c "$(curl …)" --` form that only existed to pass flags, sends them
straight into the no-options error. The file list is explicit (never a repo
glob) so historical records — task guides, ADRs, the RUNBOOK release table —
are never in scope. T116 and T117 extend FORBIDDEN / LIVE_DOCS here.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LIVE_DOCS = [
    "README.md",
    "site/index.html",
    "RUNBOOK.md",
    "AGENTS.md",
    *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs" / "claude-md").glob("*.md")),
]

FORBIDDEN = ["--harness", "--copy", "update.sh --", 'sh -c "$(curl']

# RUNBOOK.md ends with a release log table: a historical record, never rewritten.
RUNBOOK_HISTORY_HEADING = re.compile(r"^## Release Log", re.MULTILINE)

INSTALLER_SCRIPTS = ["setup.sh", "update.sh", *sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "lib").glob("*.sh"))]


def _live_text(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if rel == "RUNBOOK.md":
        m = RUNBOOK_HISTORY_HEADING.search(text)
        assert m, "RUNBOOK.md release-history heading not found — update RUNBOOK_HISTORY_HEADING"
        text = text[: m.start()]
    return text


def test_live_docs_show_no_install_flags():
    hits = []
    for rel in LIVE_DOCS:
        for n, line in enumerate(_live_text(rel).splitlines(), 1):
            for bad in FORBIDDEN:
                if bad in line:
                    hits.append(f"{rel}:{n}: {bad!r}")
    assert not hits, "live docs still document a removed install flag:\n" + "\n".join(hits)


def test_live_docs_show_the_one_line_command():
    one_line = "curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"
    for rel in ("README.md", "site/index.html", "RUNBOOK.md"):
        assert one_line in _live_text(rel), f"{rel} does not show the one install/update line"


# A user-facing string: the quoted literal passed to log_* / _harness_log_* /
# printf. Internal identifiers and file names that merely contain "harness"
# (harness_fetch, harness-lock.json, lib/harness-fetch.sh, $_harness,
# $HARNESS_…) are not renamed (ADR-0002) and are stripped before the check.
_CALL = re.compile(r"^\s*(?:[^#]*?[;&|{(]\s*)?(?:_harness_)?(?:log_(?:info|warn|error)|printf)\b(.*)$")
_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'')
_NOT_WORDS = re.compile(
    r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"      # variable references
    r"|harness_[a-z_]+"                     # function names
    r"|harness-(?:lock|fetch|update)"        # file names
    r"|_?HARNESS_[A-Z_]+"
)


def _user_strings(rel):
    for n, line in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        m = _CALL.match(line)
        if not m:
            continue
        for q in _QUOTED.finditer(m.group(1)):
            yield n, q.group(1) if q.group(1) is not None else q.group(2)


def test_installer_user_strings_say_cli_not_harness():
    hits = []
    for rel in INSTALLER_SCRIPTS:
        for n, s in _user_strings(rel):
            if re.search(r"harness", _NOT_WORDS.sub("", s), re.IGNORECASE):
                hits.append(f"{rel}:{n}: {s}")
    assert not hits, "user-facing installer output says 'harness' (say CLI / Easy Kit):\n" + "\n".join(hits)


def test_user_string_scan_is_not_vacuous():
    """Guards the regexes above: they must find real strings to check."""
    found = [s for rel in INSTALLER_SCRIPTS for _, s in _user_strings(rel)]
    assert any("Easy Kit" in s for s in found), "scan found no user-facing strings — regex broken"
    assert any("Setup complete" in s for s in found)
