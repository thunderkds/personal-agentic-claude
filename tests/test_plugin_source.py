"""
T242 — the marketplace installs `plugin/`, a folder of symlinks to the paths the plugin runs from.

A git install dereferences a link that points elsewhere in the marketplace repo, so the cache gets
real files and only these paths (T242 D1: 12 MB -> 1.3 MB). This test keeps the link list complete:
every path the plugin reads must resolve under `plugin/`, and nothing else (no tests) may ride along.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin")
_PLUGIN_LINKS = pytest.mark.posix_only("plugin/ is built from git symlinks; a Windows clone without the symlink right has plain files there, and the Windows plugin install is unverified (ADR-0003 addendum, T276)")
PLUGIN_ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)")


def plugin_root_paths():
    """Every `${CLAUDE_PLUGIN_ROOT}/<path>` named in hooks/hooks.json, commands/ and skills/."""
    files = [os.path.join(ROOT, "hooks", "hooks.json")]
    for top in ("commands", "skills"):
        for dirpath, _dirs, names in os.walk(os.path.join(ROOT, top)):
            files += [os.path.join(dirpath, n) for n in names if n.endswith((".md", ".json", ".py", ".sh"))]
    found = set()
    for path in files:
        with open(path, encoding="utf-8") as f:
            found.update(p.rstrip(".") for p in PLUGIN_ROOT_PATH.findall(f.read()))
    return sorted(found)


def plugin_init_paths():
    spec = importlib.util.spec_from_file_location("plugin_init", os.path.join(ROOT, "scripts", "plugin_init.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.TREES) + list(module.FILES)


def links():
    out = []
    for dirpath, dirs, names in os.walk(PLUGIN):
        out += [os.path.join(dirpath, n) for n in dirs + names if os.path.islink(os.path.join(dirpath, n))]
    return out


def test_marketplace_source_is_the_plugin_folder():
    with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as f:
        market = json.load(f)
    assert [p["source"] for p in market["plugins"]] == ["./plugin"]


def test_the_scan_finds_the_hook_and_init_paths():
    paths = plugin_root_paths()
    assert ".claude/hooks/pre_bash_block_unsafe_merge.py" in paths
    assert "scripts/plugin_init.py" in paths
    assert "skills/settings-setup/scripts/apply_profile.py" in paths


@_PLUGIN_LINKS
@pytest.mark.parametrize("rel", plugin_root_paths())
def test_every_plugin_root_path_resolves_under_plugin(rel):
    assert os.path.exists(os.path.join(PLUGIN, rel)), rel


@_PLUGIN_LINKS
@pytest.mark.parametrize("rel", plugin_init_paths())
def test_every_init_tree_and_file_resolves_under_plugin(rel):
    assert os.path.exists(os.path.join(PLUGIN, rel)), rel


def test_every_kit_hook_script_has_a_link():
    hooks = sorted(n for n in os.listdir(os.path.join(ROOT, ".claude", "hooks")) if n.endswith(".py"))
    assert hooks
    for name in hooks:
        assert os.path.isfile(os.path.join(PLUGIN, ".claude", "hooks", name)), name


@_PLUGIN_LINKS
def test_every_link_resolves_inside_the_repo_and_is_relative():
    found = links()
    assert found
    real_root = os.path.realpath(ROOT)
    for link in found:
        target = os.readlink(link)
        assert not os.path.isabs(target), (link, target)
        real = os.path.realpath(link)
        assert os.path.exists(real), (link, target)
        assert real.startswith(real_root + os.sep), (link, real)
        assert not real.startswith(os.path.realpath(PLUGIN) + os.sep), (link, real)


# T243: the plugin directory reads these through no link, so they are real copies of the root files
# (tests/test_directory_prep.py keeps them equal). Every other file in plugin/ is a link.
REAL_FILES = {".claude-plugin/plugin.json", ".claude-plugin/icon.png", "hooks/hooks.json"}


@_PLUGIN_LINKS
def test_plugin_holds_only_links_folders_and_the_real_copies():
    for dirpath, dirs, names in os.walk(PLUGIN):
        for name in names:
            path = os.path.join(dirpath, name)
            if os.path.relpath(path, PLUGIN) in REAL_FILES:
                continue
            assert os.path.islink(path), path


def test_hook_tests_are_left_out():
    tests_dir = os.path.realpath(os.path.join(ROOT, ".claude", "hooks", "tests"))
    assert not os.path.exists(os.path.join(PLUGIN, ".claude", "hooks", "tests"))
    for dirpath, _dirs, _names in os.walk(PLUGIN, followlinks=True):
        real = os.path.realpath(dirpath)
        assert real != tests_dir and not real.startswith(tests_dir + os.sep), dirpath


def test_setup_sh_does_not_ship_the_plugin_folder():
    with open(os.path.join(ROOT, "MANIFEST")) as f:
        entries = [line.split("#")[0].strip() for line in f]
    assert not [e for e in entries if e == "plugin" or e.startswith("plugin/")]


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_claude_plugin_validate_plugin_folder():
    result = subprocess.run(["claude", "plugin", "validate", "plugin/"], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Validation passed" in result.stdout, result.stdout
