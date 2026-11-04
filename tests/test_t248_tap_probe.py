"""T248: `ux-evaluate` measures tap targets instead of guessing them from a screenshot, and its
scratch directory is an absolute path, so screenshots never land in the repo."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ux-evaluate" / "SKILL.md"
PROBE = ROOT / "skills" / "ux-evaluate" / "scripts" / "tap_probe.py"
CODEX_CAP = 8192

FIXTURE = """<!doctype html><html><head><meta charset="utf-8"><title>t</title>
<style>button{display:block;margin:8px;padding:0;border:0}</style></head><body>
<button id="small" style="width:80px;height:20px">Save</button>
<button id="big" style="width:120px;height:48px">Add task</button>
<label id="row" style="display:block;height:64px"><input type="checkbox"> Walk</label>
<p>Read the <a href="#x">terms</a> first.</p>
</body></html>"""


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROBE), *args], capture_output=True, text=True)


def _chrome() -> str | None:
    for name in ("google-chrome", "chromium-browser"):
        if shutil.which(name):
            return name
    return None


def test_probe_refuses_a_relative_out_dir(tmp_path):
    page = tmp_path / "p.html"
    page.write_text(FIXTURE)
    res = _run(str(page), "shots")
    assert res.returncode != 0
    assert "absolute" in res.stderr


def test_probe_refuses_a_relative_page(tmp_path):
    res = _run("p.html", str(tmp_path))
    assert res.returncode != 0
    assert "absolute" in res.stderr


def test_probe_writes_a_copy_that_loads_the_page_assets_and_the_probe(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    page = site / "p.html"
    page.write_text(FIXTURE)
    out = tmp_path / "out"
    res = _run(str(page), str(out))
    assert res.returncode == 0, res.stderr
    probe = out / "p-probe.html"
    assert res.stdout.strip() == str(probe)
    html = probe.read_text()
    assert f'<base href="file://{site}/">' in html
    assert "tap-probe" in html
    assert page.read_text() == FIXTURE, "the page itself is never changed"


@pytest.mark.skipif(_chrome() is None, reason="needs headless Chrome")
def test_probe_flags_only_the_target_under_44px(tmp_path):
    page = tmp_path / "p.html"
    page.write_text(FIXTURE)
    out = tmp_path / "out"
    probe = _run(str(page), str(out)).stdout.strip()
    dom = subprocess.run(
        [_chrome(), "--headless", "--disable-gpu", "--virtual-time-budget=2000", "--dump-dom", f"file://{probe}"],
        capture_output=True, text=True, timeout=60,
    ).stdout
    m = re.search(r"tap-probe: (\d+) under 44px: ([^<]*)", dom)
    assert m, dom[-800:]
    assert m.group(1) == "1", m.group(0)
    assert "Save 80x20" in m.group(2)
    assert "Add task" not in m.group(2) and "terms" not in m.group(2) and "Walk" not in m.group(2)


def test_skill_names_the_probe_for_b_d_and_an_absolute_dir():
    t = SKILL.read_text()
    assert "scripts/tap_probe.py" in t
    bd = re.search(r"\*\*B-d\*\*[^\n]*", t).group(0)
    assert "tap_probe" in bd or "measure" in bd
    step2 = re.search(r"#### 2\. Take the screenshots(.*?)#### 3\.", t, re.S).group(1)
    assert "absolute" in step2 and "mktemp -d" in step2
    assert len(SKILL.read_bytes()) <= CODEX_CAP, len(SKILL.read_bytes())
