"""T268 / T271 — static checks of the PowerShell installer source (AC 1, Success Criterion 6).

`setup.ps1` and `lib/harness.ps1` must run on Windows PowerShell 5.1 as well as PowerShell 7, and must
not reach for a POSIX tool. This test reads the source only; the behaviour is checked by
tests/test_setup_ps1_pwsh.py (Docker) and tests/windows/smoke-install.ps1 (Windows CI).

Run with: python3 -m pytest tests/test_setup_ps1_static.py -q
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLER = ("setup.ps1", "lib/harness.ps1", "update.ps1", "lib/harness-update.ps1")
SMOKES = ("tests/windows/smoke-install.ps1", "tests/windows/smoke-update.ps1")

# A POSIX tool or a Python name the Windows installer must never call (AC 1). Whole words:
# `setup.sh` in a comment is a file name, not a call to `sh`.
BANNED_WORDS = {
    "python3": re.compile(r"(?<![\w.-])python3(?![\w.-])"),
    "sh": re.compile(r"(?<![\w./\\-])sh(?![\w.-])"),
    "bash": re.compile(r"(?<![\w./\\-])bash(?![\w.-])"),
    "/dev/null": re.compile(r"/dev/null"),
    # T271 AC 15: a recursive Remove-Item follows a junction into its target; use Remove-HarnessPath.
    "Remove-Item -Recurse": re.compile(r"Remove-Item\b[^\n]*-Recurse", re.IGNORECASE),
}

# Syntax PowerShell 5.1 does not parse, or API it does not have (AC 1, Edge Case Checklist).
PS7_ONLY = {
    "&& pipeline chain": re.compile(r"&&"),
    "|| pipeline chain": re.compile(r"\|\|"),
    "?? null-coalescing": re.compile(r"\?\?"),
    "?. / ?[ null-conditional": re.compile(r"\}\?[.\[]|\$\w+\?[.\[]"),
    "?: ternary": re.compile(r"\s\?\s"),
    "-Parallel": re.compile(r"-Parallel\b", re.IGNORECASE),
    "-AsHashtable": re.compile(r"-AsHashtable\b", re.IGNORECASE),
    "-AdditionalChildPath": re.compile(r"-AdditionalChildPath\b", re.IGNORECASE),
    "GetRelativePath": re.compile(r"GetRelativePath"),
}

HEADER = ("Set-StrictMode -Version Latest", "$ErrorActionPreference = 'Stop'")


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _code(text):
    """The source without comments: `<# ... #>` blocks and `#` to end of line outside a string."""
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)
    out = []
    for line in text.splitlines():
        quote = None
        for i, ch in enumerate(line):
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "'\"":
                quote = ch
            elif ch == "#":
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def _first_statements(code):
    """The code lines after an optional leading `[CmdletBinding()]` / `param(...)` block."""
    lines = [l.strip() for l in code.splitlines() if l.strip()]
    i = 0
    if i < len(lines) and lines[i].startswith("[CmdletBinding"):
        i += 1
    if i < len(lines) and lines[i].lower().startswith("param("):
        depth = 0
        while i < len(lines):
            depth += lines[i].count("(") - lines[i].count(")")
            i += 1
            if depth <= 0:
                break
    return lines[i:i + 2]


def problems(rel, text, installer=True):
    """Every way `text` (the content of `rel`) breaks AC 1. An empty list means it conforms."""
    found = []
    try:
        text.encode("ascii")
    except UnicodeEncodeError as exc:
        found.append(f"{rel}: non-ASCII byte at offset {exc.start} (5.1 reads a BOM-less file as ANSI)")
    code = _code(text)
    if _first_statements(code) != list(HEADER):
        found.append(f"{rel}: must start with {HEADER[0]!r} then {HEADER[1]!r}")
    for name, rx in PS7_ONLY.items():
        for n, line in enumerate(code.splitlines(), 1):
            if rx.search(line):
                found.append(f"{rel}:{n}: PowerShell-7-only {name}: {line.strip()}")
    if installer:
        for name, rx in BANNED_WORDS.items():
            for n, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    found.append(f"{rel}:{n}: banned {name!r}: {line.strip()}")
    if "Get-Content" in code and "Set-Content" in code:
        found.append(f"{rel}: Get-Content | Set-Content re-encodes files (AC 5)")
    return found


@pytest.mark.parametrize("rel", INSTALLER)
def test_installer_source_is_51_safe_and_posix_free(rel):
    assert os.path.isfile(os.path.join(ROOT, rel)), f"{rel} is missing"
    assert problems(rel, _read(rel)) == []


@pytest.mark.parametrize("rel", SMOKES)
def test_smoke_script_is_51_safe(rel):
    assert os.path.isfile(os.path.join(ROOT, rel)), f"{rel} is missing"
    assert problems(rel, _read(rel), installer=False) == []


def test_update_ps1_is_a_thin_alias_for_the_update_action():
    """T271 AC 1: update.ps1 selects Update through the EASYKIT_ACTION seam and runs setup.ps1;
    setup.ps1 dot-sources the update library and offers Update."""
    alias = _code(_read("update.ps1"))
    assert "EASYKIT_ACTION" in alias and "setup.ps1" in alias
    setup = _read("setup.ps1")
    assert re.search(r"^\.\s+.*harness-update\.ps1", setup, re.M), "setup.ps1 must dot-source lib/harness-update.ps1"
    assert "1) Update (keeps your edits)" in setup


def test_setup_ps1_dot_sources_the_library_and_calls_both_helpers():
    text = _read("setup.ps1") + _read("lib/harness.ps1")
    assert re.search(r"^\.\s+.*harness\.ps1", _read("setup.ps1"), re.M), "setup.ps1 must dot-source lib/harness.ps1"
    for helper in ("merge-settings.py", "windows_hooks.py"):
        assert helper in text, f"{helper} is never called"


def test_manifest_does_not_list_the_installers():
    """setup.sh and lib/*.sh are not MANIFEST paths, so their PowerShell twins are not either."""
    paths = [l.split()[0] for l in _read("MANIFEST").splitlines() if l.strip() and not l.lstrip().startswith("#")]
    assert not {"setup.ps1", "lib/harness.ps1", "lib", "setup.sh", "update.ps1", "lib/harness-update.ps1"} & set(paths)


@pytest.mark.parametrize("old,new", [
    ("$ErrorActionPreference = 'Stop'", "$ErrorActionPreference = 'Continue'"),
    ("Set-StrictMode -Version Latest", "Set-StrictMode -Off"),
])
def test_mutation_control_a_missing_header_is_caught(old, new):
    text = _read("setup.ps1")
    assert old in text
    assert problems("setup.ps1", text.replace(old, new, 1))


@pytest.mark.parametrize("injected", [
    "& python3 -c 'print(1)'",
    "git status && git log",
    "$x = $a ?? 'b'",
    "& sh -c 'true'",
    "Remove-Item /dev/null",
    "$y = 'café'",
    "$x = Get-Content $a | Set-Content $b",
    "Remove-Item -LiteralPath $p -Recurse -Force",
])
def test_mutation_control_a_banned_token_is_caught(injected):
    """Success Criterion 6: a banned token injected into setup.ps1 makes the static test fail."""
    text = _read("setup.ps1")
    assert problems("setup.ps1", text) == []
    mutated = text + "\n" + injected + "\n"
    assert problems("setup.ps1", mutated), f"{injected!r} went unnoticed"
