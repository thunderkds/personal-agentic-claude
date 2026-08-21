"""
T088 — drift test between packs/*/PACK.md and setup.sh's own flag parser.

Every `setup.sh` invocation documented in a PACK.md must use a flag form that
setup.sh's `case "$arg" in` block actually accepts. The valid flag patterns
are parsed out of setup.sh at test time (not hardcoded) so this test learns
new flags automatically — see AC4 in TASK_GUIDE_T088.md.
"""
import fnmatch
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP_SH = os.path.join(ROOT, "setup.sh")
PACKS_DIR = os.path.join(ROOT, "packs")


def _setup_sh_text():
    with open(SETUP_SH, encoding="utf-8") as f:
        return f.read()


def _valid_flag_patterns():
    """Parse setup.sh's `case "$arg" in ... esac` flag block and return the
    glob patterns it matches (e.g. "--copy", "--pack=*"). The catch-all `*)`
    branch is excluded — it is the reject path, not a valid pattern."""
    text = _setup_sh_text()
    match = re.search(r'for arg in "\$@"; do\s*case "\$arg" in(.*?)esac', text, re.DOTALL)
    assert match, "could not locate the arg-parsing case block in setup.sh"
    block = match.group(1)
    patterns = []
    for line in block.splitlines():
        line = line.strip()
        pattern_match = re.match(r"([^)]+)\)", line)
        if not pattern_match:
            continue
        pattern = pattern_match.group(1).strip()
        if pattern == "*":
            continue
        patterns.append(pattern)
    return patterns


def _pack_md_files():
    return sorted(
        os.path.join(PACKS_DIR, name, "PACK.md")
        for name in os.listdir(PACKS_DIR)
        if os.path.isfile(os.path.join(PACKS_DIR, name, "PACK.md"))
    )


def _setup_sh_invocations(text):
    """Extract flag tokens from each local `setup.sh <flags>` invocation
    line. Skips bare backtick-quoted mentions with no flags (prose) and
    skips URL references (e.g. `curl .../setup.sh | sh`)."""
    invocations = []
    for line in text.splitlines():
        if "setup.sh" not in line:
            continue
        if re.search(r"https?://\S*setup\.sh", line):
            # setup.sh reached via a URL (e.g. curl .../setup.sh | sh) — not
            # a local invocation line.
            continue
        match = re.search(r"\bsetup\.sh\b(.*)$", line)
        if not match:
            continue
        rest = match.group(1).strip()
        if not rest:
            # bare `setup.sh` mention, e.g. prose in backticks — no flags.
            continue
        tokens = [t for t in rest.split() if t.startswith("-")]
        if tokens:
            invocations.append((line.strip(), tokens))
    return invocations


def test_every_pack_doc_flag_is_accepted_by_setup_sh():
    patterns = _valid_flag_patterns()
    assert patterns, "no flag patterns parsed out of setup.sh — fixture broken"

    pack_files = _pack_md_files()
    assert len(pack_files) == 5, f"expected 5 PACK.md files, found {len(pack_files)}"

    files_with_invocations = 0
    failures = []
    for path in pack_files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        invocations = _setup_sh_invocations(text)
        if invocations:
            files_with_invocations += 1
        for line, tokens in invocations:
            for token in tokens:
                if not any(fnmatch.fnmatch(token, pattern) for pattern in patterns):
                    failures.append(f"{path}: flag {token!r} (from line: {line!r}) not accepted by setup.sh")

    assert files_with_invocations == 5, (
        f"expected all 5 PACK.md files to contain a setup.sh invocation with "
        f"flags, found {files_with_invocations}"
    )
    assert not failures, "\n".join(failures)
