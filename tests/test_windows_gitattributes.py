"""T262 — native Windows support, step 1: LF line endings and the decision record.

  AC1 — `docs/adr/0003-native-windows-support.md` records five decisions, each under its own heading.
  AC2 — the symlink fallback is recorded as decided (junction, else copy plus drift check) with its source.
  AC3 — `.gitattributes` makes git treat shell, Python and hook scripts as `eol=lf`.
  AC4 — binary files (png, jpg, ico, woff2) are marked `binary`.
  AC5 — the attribute file does not put a CRLF file into the index.
  Mutation control — delete the `eol=lf` rules and AC3 goes red.

Run with: python3 -m pytest tests/test_windows_gitattributes.py -q
"""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADR = REPO / "docs" / "adr" / "0003-native-windows-support.md"
LF_PATHS = [
    "setup.sh",
    ".claude/hooks/post_tool_trace.py",
    "skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh",
]
BINARY_PATHS = ["a.png", "a.jpg", "a.ico", "a.woff2"]

# The five decisions of AC1: (name, regex a heading line must match)
DECISION_HEADINGS = [
    ("native Windows only", r"native windows only.*wsl"),
    ("PowerShell shell target", r"powershell.*shell"),
    ("Python launcher", r"python launcher"),
    ("installer language", r"installer language"),
    ("symlink fallback", r"symlink fallback"),
]


def _check_attr(attr, paths, cwd=REPO):
    """Return {path: value} from `git check-attr <attr> -- <paths>` (no shell)."""
    out = subprocess.run(["git", "check-attr", attr, "--", *paths], cwd=cwd, capture_output=True,
                         check=True, text=True).stdout
    result = {}
    for line in out.splitlines():
        path, _, value = line.rsplit(": ", 2)
        result[path] = value
    return result


def _headings(text):
    return [line for line in text.splitlines() if line.startswith("#")]


# --- AC3 / AC4 -------------------------------------------------------------------------------

def test_scripts_are_eol_lf():
    assert _check_attr("eol", LF_PATHS) == {p: "lf" for p in LF_PATHS}


def test_binary_files_are_marked_binary():
    assert _check_attr("binary", BINARY_PATHS) == {p: "set" for p in BINARY_PATHS}


# --- AC5 -------------------------------------------------------------------------------------

def test_attribute_file_leaves_no_crlf_in_the_index():
    # Regression guard for the current index state, not a proof of AC 5: .gitattributes cannot put
    # CRLF into the index by itself, so this test cannot fail because of it.
    out = subprocess.run(["git", "ls-files", "--eol"], cwd=REPO, capture_output=True, check=True,
                         text=True).stdout
    crlf = [line for line in out.splitlines() if line.startswith("i/crlf") or line.startswith("i/mixed")]
    assert not crlf, "tracked files with CRLF in the index:\n" + "\n".join(crlf)


# --- AC1 / AC2 -------------------------------------------------------------------------------

def test_adr_has_the_five_decisions_each_under_its_own_heading():
    assert ADR.is_file(), f"{ADR} is missing"
    headings = _headings(ADR.read_text(encoding="utf-8"))
    for name, pattern in DECISION_HEADINGS:
        hits = [h for h in headings if re.search(pattern, h, re.IGNORECASE)]
        assert len(hits) == 1, f"decision '{name}': expected one heading matching /{pattern}/, got {hits}"


def test_adr_has_no_todo_and_uses_the_template_sections():
    text = ADR.read_text(encoding="utf-8")
    assert "TODO" not in text
    for section in ("## Context", "## Decision", "## Alternatives Considered", "## Consequences"):
        assert section in text, f"missing template section {section}"


def test_adr_records_the_symlink_fallback_with_its_source():
    text = ADR.read_text(encoding="utf-8")
    start = re.search(r"^#+ .*symlink fallback.*$", text, re.IGNORECASE | re.MULTILINE)
    assert start, "no symlink fallback heading"
    section = text[start.end():]
    nxt = re.search(r"^#{1,3} ", section, re.MULTILINE)
    section = section[:nxt.start()] if nxt else section
    low = section.lower()
    assert "junction" in low and "drift check" in low, "fallback must name the junction and the drift check"
    assert "2026-11-06" in section and "default" in low, "fallback must name its source: the user's default"


# --- Mutation control ------------------------------------------------------------------------

def test_deleting_the_eol_rules_turns_the_check_red(tmp_path):
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitattributes").write_text(attrs, encoding="utf-8")
    assert _check_attr("eol", LF_PATHS, cwd=tmp_path) == {p: "lf" for p in LF_PATHS}  # control: green
    mutated = "".join(line for line in attrs.splitlines(keepends=True) if "eol=lf" not in line)
    assert mutated != attrs, "mutation removed nothing"
    (tmp_path / ".gitattributes").write_text(mutated, encoding="utf-8")
    assert _check_attr("eol", LF_PATHS, cwd=tmp_path) != {p: "lf" for p in LF_PATHS}  # mutated: red
