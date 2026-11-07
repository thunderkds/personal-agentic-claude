"""T226 - Stage 1 offers the optional companion MCP servers.

The skill's script reads a data file and the PATH only. These tests run it as a
subprocess with a controlled PATH, then check the data file, the skill text and the
doc edits against the Acceptance Criteria of tasks/TASK_GUIDE_T226.md.
"""
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skills", "companion-setup")
SCRIPT = os.path.join(SKILL_DIR, "scripts", "check_companions.py")
DATA = os.path.join(SKILL_DIR, "companions.json")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
SITE = os.path.join(ROOT, "site", "docs.html")  # T231: the reference moved from index.html

IDS = ["easy-verifier", "easy-ui", "easy-memory", "easy-personal"]
PRIVATE_OR_UNPUBLISHED_REPOS = ("easy-verifier-mcp", "easy-memory-mcp", "easy-personal-mcp")


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def _data():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)["companions"]


def _run(args, tools=()):
    """Run the script with a PATH that holds only the fake tools named in `tools`."""
    import tempfile

    with tempfile.TemporaryDirectory() as bindir:
        windows = os.name == "nt"  # Windows runs a fake tool only as <tool>.cmd, found through PATHEXT
        for tool in tools:
            path = os.path.join(bindir, tool + (".cmd" if windows else ""))
            with open(path, "w") as f:
                f.write("@exit /b 0\r\n" if windows else "#!/bin/sh\nexit 0\n")
            os.chmod(path, 0o755)
        env = {"PATH": bindir, "HOME": bindir}
        if windows:
            env["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
        return subprocess.run(
            [sys.executable, SCRIPT] + list(args), capture_output=True, text=True, env=env, cwd=bindir
        )


def _line(out, companion_id):
    lines = [l for l in out.splitlines() if companion_id in l]
    assert len(lines) == 1, f"expected one line for {companion_id}, got {lines}"
    return lines[0]


# --- AC1: the data file ------------------------------------------------------

def test_data_file_has_the_four_companions_and_no_easy_context():
    entries = _data()
    assert [e["id"] for e in entries] == IDS
    assert "easy-context" not in json.dumps(entries)
    for e in entries:
        assert set(e) >= {"id", "adds", "tools", "link", "access"}, e
        assert e["access"] in ("public", "private"), e
        assert e["adds"].strip() and isinstance(e["tools"], list) and e["tools"], e


def test_data_file_required_tools_and_access():
    by_id = {e["id"]: e for e in _data()}
    assert by_id["easy-ui"]["tools"] == ["docker"]
    assert by_id["easy-verifier"]["tools"] == ["docker"]
    assert by_id["easy-memory"]["tools"] == ["python3"]
    assert by_id["easy-personal"]["tools"] == ["python3", "uv", "node"]
    assert [e["id"] for e in _data() if e["access"] == "public"] == ["easy-verifier", "easy-ui"]


def test_every_site_card_has_an_entry_and_public_links_never_point_at_a_private_repo():
    body = re.search(r'<section id="mcps">(.*?)</section>', _read("site", "docs.html"), re.DOTALL).group(1)
    names = re.findall(r"<h3>([^<]*)</h3>", body)
    assert sorted(names) == sorted(i + "-mcp" for i in IDS)
    by_id = {e["id"]: e for e in _data()}
    for i in IDS:
        assert i in by_id
    for e in _data():
        if e["access"] == "public":
            for repo in PRIVATE_OR_UNPUBLISHED_REPOS:
                assert f"github.com/thunderkds/{repo}" not in e["link"], e
            assert e["link"].startswith("https://"), e
    assert by_id["easy-ui"]["link"] == "https://github.com/thunderkds/easy-ui-mcp"


# --- AC2, AC3, AC4: the script -----------------------------------------------

def test_nothing_installed_and_no_docker():
    r = _run([], tools=["python3"])
    assert r.returncode == 0, r.stderr
    for i in ("easy-ui", "easy-verifier"):
        line = _line(r.stdout, i)
        assert line.startswith("choice:"), line
        assert "missing docker" in line, line
        assert "https://" in line, line
    for i in ("easy-memory", "easy-personal"):
        line = _line(r.stdout, i)
        assert not line.startswith("choice:"), line
        assert "repo access" in line, line
        assert "https://" not in line, line


def test_choice_line_says_what_it_adds_and_what_it_needs():
    r = _run([], tools=["docker"])
    line = _line(r.stdout, "easy-ui")
    by_id = {e["id"]: e for e in _data()}
    assert by_id["easy-ui"]["adds"] in line
    assert "Needs docker" in line
    assert "missing" not in line


def test_installed_private_server_is_shown_as_installed_not_as_needing_access():
    r = _run(["--installed", "easy-memory"])
    assert r.returncode == 0, r.stderr
    line = _line(r.stdout, "easy-memory")
    assert "already installed" in line and "private" in line, line
    assert "repo access" not in line and not line.startswith("choice:"), line


def test_installed_public_server_is_shown_as_installed_with_no_choice():
    r = _run(["--installed", "easy-ui,easy-verifier"], tools=["docker"])
    for i in ("easy-ui", "easy-verifier"):
        line = _line(r.stdout, i)
        assert "already installed" in line and "public" in line, line
        assert not line.startswith("choice:"), line


def test_unknown_id_is_ignored():
    r = _run(["--installed", "unknown-id"])
    assert r.returncode == 0, r.stderr
    assert "unknown-id" not in r.stdout and "Traceback" not in r.stderr
    assert "choice:" in r.stdout


def test_empty_installed_and_missing_tools_exit_zero():
    for args in ([], ["--installed", ""], ["--installed", " , ,"]):
        r = _run(args)
        assert r.returncode == 0, (args, r.stderr)
        assert r.stdout.strip()


def test_script_writes_no_file_and_changes_nothing():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        env = {"PATH": d, "HOME": d}
        subprocess.run([sys.executable, SCRIPT], env=env, cwd=d, check=True, capture_output=True)
        assert os.listdir(d) == []


def test_script_source_imports_no_network_or_process_module_and_never_opens_for_write():
    src = _read("skills", "companion-setup", "scripts", "check_companions.py")
    imports = set(re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.MULTILINE))
    banned = {"subprocess", "socket", "urllib", "http", "requests", "ssl", "asyncio", "ftplib", "os"}
    assert not (imports & banned), imports & banned
    assert not re.search(r"open\([^)]*['\"][wax+]", src)
    assert "system(" not in src and "Popen" not in src


# --- AC5: the skill ----------------------------------------------------------

def _skill():
    return open(SKILL_MD, encoding="utf-8").read()


def test_skill_frontmatter_and_script_run():
    text = _skill()
    assert re.match(r"---\nname: companion-setup\ndescription: \".+\"\n---\n", text)
    assert 'python3 "${CLAUDE_SKILL_DIR}/scripts/check_companions.py"' in text
    assert "--installed" in text


def test_skill_defaults_to_skip_and_the_kit_never_installs():
    text = _skill().lower()
    assert "skip" in text and "default" in text
    assert "never install" in text
    assert "never start" in text or "never runs" in text or "does not start" in text
    assert "link" in text and "missing tools" in text


def test_skill_sudo_only_ever_says_the_kit_does_not_run_it():
    for line in _skill().splitlines():
        if "sudo" in line.lower():
            assert re.search(r"\b(not|never)\b", line.lower()), line


def test_skill_warns_verifier_listens_on_loopback_without_authentication():
    text = _skill()
    assert "127.0.0.1:8766" in text
    assert re.search(r"no authentication", text, re.IGNORECASE)


def test_skill_auto_mode_asks_nothing_and_names_one_not_done_line():
    text = _skill()
    m = re.search(r"### Auto mode.*", text, re.DOTALL)
    assert m, "no Auto mode section"
    auto = m.group(0)
    assert re.search(r"[Aa]sk no question", auto)
    assert "Not done:" in auto and "companion-setup" in auto


# --- AC6: the doc pointers ---------------------------------------------------

def test_pipeline_stages_stage_1_item_1_names_the_skill_and_its_auto_rule():
    stage1 = _read("docs", "claude-md", "pipeline-stages.md").split("## Stage 1:")[1].split("### Step Agent team")[0]
    assert 'Skill({ skill: "companion-setup" })' in stage1
    assert "companion-setup" in stage1.split("2. **Multi-CLI")[0]
    auto = [l for l in stage1.splitlines() if l.strip().startswith("Auto mode:") and "settings-setup" in l]
    assert auto and "companion-setup" in auto[0]


def test_legacy_stage_1_and_skill_list_name_the_skill():
    text = _read("CLAUDE_LEGACY.md")
    assert re.search(r"Stage 1: Environment Check\*\*.*?companion-setup", text, re.DOTALL)
    assert "`companion-setup/SKILL.md`" in text


def test_tracks_row_5_names_the_skill_and_its_auto_rule():
    rows = [l for l in _read("docs", "claude-md", "tracks.md").splitlines() if l.startswith("| 5 |")]
    assert len(rows) == 1 and "companion-setup" in rows[0], rows
    assert "Not done:" in rows[0] and rows[0].rstrip().endswith("`RULE` |")


# --- AC7: setup.sh -----------------------------------------------------------

def test_setup_sh_logs_one_companion_line_after_the_pack_catalog_line_and_adds_no_prompt():
    lines = _read("setup.sh").splitlines()
    comp = [i for i, l in enumerate(lines) if "companion" in l.lower()]
    assert len(comp) == 1, comp
    assert lines[comp[0]].strip().startswith("log_info ")
    assert "Pack catalog" in lines[comp[0] - 1]
    assert "Stage 1" in lines[comp[0]]
    assert "read" not in lines[comp[0]].split()  # no prompt on this line


# --- AC8: README and site ----------------------------------------------------

def test_readme_names_the_offer_within_its_cap():
    text = _read("README.md")
    assert len(text.splitlines()) <= 75
    assert "companion-setup" in text


def test_site_mcps_section_says_the_supervisor_offers_them_at_stage_1():
    body = re.search(r'<section id="mcps">(.*?)</section>', _read("site", "docs.html"), re.DOTALL).group(1)
    assert re.search(r"Stage 1", body) and "Supervisor" in body
    assert re.search(r"skip", body, re.IGNORECASE)
    assert "companion-setup" in _read("site", "docs.html")
