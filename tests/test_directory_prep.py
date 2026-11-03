"""
T243 — the plugin folder passes the plugin directory's submission checks.

`claude plugin validate plugin --profile directory` could not read the manifest through T242's
`plugin/.claude-plugin/plugin.json` link, and refuses hooks read through a link (HOOKS_FILE_UNREAD).
So `plugin/` holds three real files, each a byte copy of the root file it mirrors: plugin.json,
hooks/hooks.json, and the listing icon (the site header mark, 1024 px). The marketplace has a
description. The first icon submitted to the directory is permanent.

Run with: python3 -m pytest tests/test_directory_prep.py -q
"""
import json
import os
import shutil
import struct
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin")
# each real file under plugin/ and the root file it must equal
COPIES = {
    ".claude-plugin/plugin.json": ".claude-plugin/plugin.json",
    "hooks/hooks.json": "hooks/hooks.json",
    ".claude-plugin/icon.png": ".claude-plugin/icon.png",
}


def read(path):
    with open(path, "rb") as f:
        return f.read()


@pytest.mark.parametrize("rel", sorted(COPIES))
def test_plugin_file_is_a_real_copy_of_the_root_file(rel):
    path = os.path.join(PLUGIN, rel)
    assert os.path.isfile(path) and not os.path.islink(path), path
    assert not os.path.islink(os.path.dirname(path)), os.path.dirname(path)
    root = os.path.join(ROOT, COPIES[rel])
    assert not os.path.islink(root), root
    assert read(path) == read(root), f"{rel} differs from the root copy: copy the root file over it"


def test_icon_is_a_square_png_the_directory_accepts():
    data = read(os.path.join(PLUGIN, ".claude-plugin", "icon.png"))
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert width == height and 512 <= width <= 2048, (width, height)
    assert len(data) < 2 * 1024 * 1024


def test_marketplace_has_a_description():
    with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as f:
        market = json.load(f)
    assert market.get("metadata", {}).get("description", "").strip()


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_directory_would_accept_the_plugin_folder():
    result = subprocess.run(["claude", "plugin", "validate", "plugin/", "--profile", "directory"],
                            cwd=ROOT, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "These checks found nothing to report" in output, output
