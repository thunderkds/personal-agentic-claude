"""
T233 — the repo root is a Claude Code plugin (`easy-kit`) and its own marketplace.

AC1: `claude plugin validate .` passes and reports no LICENSE_MISSING.
AC2: hooks/hooks.json and .claude/settings.json list the same hooks and matchers.
AC3: marketplace.json holds exactly one plugin, easy-kit, with no remote source.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_JSON = os.path.join(ROOT, ".claude-plugin", "plugin.json")
MARKET_JSON = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
HOOKS_JSON = os.path.join(ROOT, "hooks", "hooks.json")
SETTINGS_JSON = os.path.join(ROOT, ".claude", "settings.json")
SCRIPT = re.compile(r"/\.claude/hooks/([\w.-]+\.py)")


def load(path):
    with open(path) as f:
        return json.load(f)


def hook_list(doc, root_var):
    """Sorted (event, matcher, script) triples; the command must use root_var."""
    out = []
    for event, groups in doc["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                command = hook["command"]
                assert root_var in command, command
                out.append((event, group.get("matcher"), SCRIPT.search(command).group(1)))
    return sorted(out, key=lambda t: (t[0], t[1] or "", t[2]))


def test_plugin_hooks_equal_settings_hooks():
    plugin = hook_list(load(HOOKS_JSON), "${CLAUDE_PLUGIN_ROOT}")
    settings = hook_list(load(SETTINGS_JSON), "$CLAUDE_PROJECT_DIR")
    assert len(settings) == 11
    assert plugin == settings


def test_plugin_hook_scripts_exist():
    for _event, _matcher, script in hook_list(load(HOOKS_JSON), "${CLAUDE_PLUGIN_ROOT}"):
        assert os.path.isfile(os.path.join(ROOT, ".claude", "hooks", script)), script


def test_comparison_detects_a_different_matcher():
    doc = load(HOOKS_JSON)
    doc["hooks"]["PreToolUse"][0]["matcher"] = "Nothing"
    assert hook_list(doc, "${CLAUDE_PLUGIN_ROOT}") != hook_list(load(SETTINGS_JSON), "$CLAUDE_PROJECT_DIR")


def test_plugin_manifest_fields():
    manifest = load(PLUGIN_JSON)
    assert manifest["name"] == "easy-kit"
    assert manifest["license"] == "MIT"
    assert manifest["author"]["name"] == "thunderkds"
    with open(os.path.join(ROOT, "site", "index.html")) as f:
        site_version = re.search(r"supervisor kit &middot; v([\d.]+)", f.read()).group(1)
    assert manifest["version"] == site_version


def test_marketplace_has_one_local_easy_kit_plugin():
    market = load(MARKET_JSON)
    assert market["name"] == "easy-kit"
    assert [p["name"] for p in market["plugins"]] == ["easy-kit"]
    source = market["plugins"][0]["source"]
    assert isinstance(source, str) and source.startswith("."), source


def test_license_is_mit():
    with open(os.path.join(ROOT, "LICENSE")) as f:
        text = f.read()
    assert text.startswith("MIT License")
    assert "Copyright (c) 2026 thunderkds" in text
    assert "Permission is hereby granted, free of charge" in text


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_claude_validates_the_repo_root():
    result = subprocess.run(
        ["claude", "plugin", "validate", ROOT, "--profile", "directory"],
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "LICENSE_MISSING" not in output, output


def test_no_tracked_names_clash_on_windows_or_macos():
    """T238: Plugin upload refuses names that differ only by case, Unicode form or a trailing dot."""
    import collections
    import unicodedata

    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0")
    paths = set()
    for name in filter(None, tracked):
        parts = name.split("/")
        paths.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
    groups = collections.defaultdict(set)
    for path in paths:
        key = "/".join(unicodedata.normalize("NFC", p).casefold().rstrip(". ") for p in path.split("/"))
        groups[key].add(path)
    clashes = sorted(sorted(v) for v in groups.values() if len(v) > 1)
    assert clashes == []


# ---- T236: README offers both install paths with the commands that were run ----------------
README = os.path.join(ROOT, "README.md")
PLUGIN_COMMANDS = (
    "claude plugin marketplace add thunderkds/easy-kit",
    "claude plugin install easy-kit@easy-kit",
    "claude plugin install easy-kit --marketplace thunderkds/easy-kit",
)
SETUP_SH_LINE = "curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh"


def test_readme_quick_start_shows_the_plugin_and_setup_sh_paths():
    """T236 AC3: the README install section shows both paths, with the version floor of the one-step form."""
    with open(README, encoding="utf-8") as f:
        text = f.read()
    quick = text[text.index("## Quick Start"):]
    quick = quick[:quick.index("\n## ", 1)]
    for command in PLUGIN_COMMANDS + (SETUP_SH_LINE, "/easy-kit:init"):
        assert command in quick, f"README Quick Start lacks {command!r}"
    assert "2.1.292 or later" in quick, "README must state the one-step form's version floor"
