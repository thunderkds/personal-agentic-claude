"""T200 - settings-setup skill: shipped profiles + add-only apply_profile.py.

AC refs are TASK_GUIDE_T200 Acceptance Criteria. Mutations M1-M4 (AC 12) are expected to turn
the tests named in each comment RED.
"""
import hashlib
import html
import json
import os
import re
import stat
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skills", "settings-setup")
PROFILES = os.path.join(SKILL_DIR, "profiles.json")
SCRIPT = os.path.join(SKILL_DIR, "scripts", "apply_profile.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
KIT_SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
PAGE = os.path.join(ROOT, "site", "index.html")

PROFILE_IDS = {"high-security", "legacy", "solo-engineer", "team-project", "empty"}

HIGH_SECURITY = {
    "permissions.deny": [
        "Read(./.env)", "Read(./.env.*)", "Read(./**/*.pem)", "Read(./**/*.key)",
        "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.config/gh/**)",
    ],
    "permissions.ask": [
        "Bash(git push --force *)", "Bash(git push -f *)", "Bash(git reset --hard *)", "Bash(rm -rf *)",
    ],
    "permissions.disableBypassPermissionsMode": "disable",
}

KIT_DENY = ["Edit(~/.claude/harness-anchors/**)", "Bash(*harness-anchors*)"]
KIT_HOOKS = {
    "PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre_bash.py"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python3 ./.claude/hooks/stop.py"}]}],
}


def profiles():
    with open(PROFILES, encoding="utf-8") as f:
        return json.load(f)


def profile(pid):
    return next(p for p in profiles()["profiles"] if p["id"] == pid)


def run(args, cwd):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=cwd, capture_output=True, text=True)


def settings_path(tmp_path):
    return tmp_path / ".claude" / "settings.json"


def write_settings(tmp_path, data_or_text):
    p = settings_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = data_or_text if isinstance(data_or_text, str) else json.dumps(data_or_text, indent=2) + "\n"
    p.write_text(text, encoding="utf-8")
    return p


def read_settings(tmp_path):
    return json.loads(settings_path(tmp_path).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def kit_shaped(**extra):
    data = {"hooks": json.loads(json.dumps(KIT_HOOKS)), "permissions": {"deny": list(KIT_DENY)}}
    data.update(extra)
    return data


# ---- AC 1: profile file shape -------------------------------------------------------------------

def test_ac1_profiles_have_exactly_the_five_ids_and_each_field():
    ps = profiles()["profiles"]
    assert [p["id"] for p in ps].count("high-security") == 1
    assert {p["id"] for p in ps} == PROFILE_IDS
    assert len(ps) == len(PROFILE_IDS), "duplicate profile id"
    for p in ps:
        assert set(p) == {"id", "label", "for", "values"}, p["id"]
        assert isinstance(p["label"], str) and p["label"].strip(), p["id"]
        assert isinstance(p["for"], str) and p["for"].strip() and "\n" not in p["for"], p["id"]
        assert isinstance(p["values"], dict), p["id"]


def test_ac1_no_suggest_placeholder_lists_written_out():
    assert "$suggest" not in open(PROFILES, encoding="utf-8").read()
    for p in profiles()["profiles"]:
        for key, value in p["values"].items():
            assert re.fullmatch(r"[A-Za-z]+(\.[A-Za-z]+)*", key), key
            if isinstance(value, list):
                assert value and all(isinstance(v, str) and v for v in value), (p["id"], key)


# ---- AC 2: high-security is exactly D5 ----------------------------------------------------------

def test_ac2_high_security_is_exactly_the_d5_rule_set():
    assert profile("high-security")["values"] == HIGH_SECURITY


# ---- AC 3: legacy = this repo's shipped deny (M4) -----------------------------------------------

def test_ac3_legacy_equals_the_kit_settings_deny_read_from_the_file():
    with open(KIT_SETTINGS, encoding="utf-8") as f:
        kit = json.load(f)
    assert kit["permissions"]["deny"], "fixture broken: kit settings has no deny"
    assert profile("legacy")["values"] == {"permissions.deny": kit["permissions"]["deny"]}


# ---- AC 4: solo/team equal today's page presets with $suggest expanded ---------------------------

def _page_presets_expanded():
    text = open(PAGE, encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="settings-catalog">(.*?)</script>', text, re.DOTALL)
    assert m, "page has no settings catalog"
    catalog = json.loads(html.unescape(m.group(1)))
    suggest = {s["key"]: s.get("suggest") for s in catalog["settings"]}
    out = {}
    for preset in catalog["presets"]:
        out[preset["id"]] = {k: (list(suggest[k]) if v == "$suggest" else v) for k, v in preset["values"].items()}
    return out


@pytest.mark.parametrize("pid", ["solo-engineer", "team-project", "empty"])
def test_ac4_shared_profiles_equal_the_page_presets(pid):
    page = _page_presets_expanded()
    assert pid in page, f"page lost preset {pid}"
    assert profile(pid)["values"] == page[pid]


# ---- AC 5: add-only merge (M1, M2) --------------------------------------------------------------

def test_ac5_high_security_on_kit_file_adds_7_deny_4_ask_1_scalar_and_keeps_the_rest(tmp_path):
    original = kit_shaped(model="opus", env={"A": "b"})
    write_settings(tmp_path, original)
    r = run(["high-security"], tmp_path)
    assert r.returncode == 0, r.stderr
    after = read_settings(tmp_path)
    assert after["permissions"]["deny"] == KIT_DENY + HIGH_SECURITY["permissions.deny"]
    assert after["permissions"]["ask"] == HIGH_SECURITY["permissions.ask"]
    assert after["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert json.dumps(after["hooks"], sort_keys=False) == json.dumps(original["hooks"], sort_keys=False)
    assert after["model"] == "opus" and after["env"] == {"A": "b"}
    assert list(after)[:4] == ["hooks", "permissions", "model", "env"], "top-level order changed"


def test_ac5_existing_list_order_kept_and_no_duplicates(tmp_path):
    ask = ["Bash(npm publish *)", "Bash(rm -rf *)"]
    deny = ["Read(./.env)", "WebFetch"]
    write_settings(tmp_path, {"permissions": {"ask": ask, "deny": deny}})
    assert run(["high-security"], tmp_path).returncode == 0
    after = read_settings(tmp_path)["permissions"]
    assert after["ask"][:2] == ask
    assert after["ask"].count("Bash(rm -rf *)") == 1
    assert len(after["ask"]) == 5
    assert after["deny"][:2] == deny
    assert after["deny"].count("Read(./.env)") == 1
    assert list(after)[:2] == ["ask", "deny"]


def test_ac5_scalar_set_only_if_absent(tmp_path):
    write_settings(tmp_path, {"cleanupPeriodDays": 30, "permissions": {"disableBypassPermissionsMode": "x"}})
    assert run(["solo-engineer"], tmp_path).returncode == 0
    after = read_settings(tmp_path)
    assert after["cleanupPeriodDays"] == 30
    assert after["autoUpdatesChannel"] == "stable"
    assert run(["high-security"], tmp_path).returncode == 0
    assert read_settings(tmp_path)["permissions"]["disableBypassPermissionsMode"] == "x"


def test_ac5_user_rules_never_removed(tmp_path):
    """Success Criterion 3 + never-remove: a user rule not in the profile survives."""
    write_settings(tmp_path, {"permissions": {"allow": ["Bash(ls *)"], "ask": ["Bash(git push -f *)", "Custom"]}})
    assert run(["high-security"], tmp_path).returncode == 0
    after = read_settings(tmp_path)["permissions"]
    assert after["allow"] == ["Bash(ls *)"]
    assert after["ask"][:2] == ["Bash(git push -f *)", "Custom"]
    assert after["ask"].count("Bash(git push -f *)") == 1


def test_ac5_file_mode_is_kept(tmp_path):
    p = write_settings(tmp_path, kit_shaped())
    os.chmod(p, 0o644)
    assert run(["high-security"], tmp_path).returncode == 0
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o644


def test_ac5_written_file_is_two_space_json_with_trailing_newline(tmp_path):
    write_settings(tmp_path, kit_shaped())
    assert run(["high-security"], tmp_path).returncode == 0
    text = settings_path(tmp_path).read_text(encoding="utf-8")
    assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


# ---- AC 6: create when absent, refuse when unsafe -----------------------------------------------

def test_ac6_no_file_creates_it_with_the_profile_only(tmp_path):
    r = run(["high-security"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert read_settings(tmp_path) == {"permissions": {
        "deny": HIGH_SECURITY["permissions.deny"],
        "ask": HIGH_SECURITY["permissions.ask"],
        "disableBypassPermissionsMode": "disable",
    }}


def test_ac6_settings_flag_names_another_file(tmp_path):
    target = tmp_path / "other.json"
    r = run(["legacy", "--settings", str(target)], tmp_path)
    assert r.returncode == 0, r.stderr
    assert json.loads(target.read_text())["permissions"]["deny"] == profile("legacy")["values"]["permissions.deny"]
    assert not settings_path(tmp_path).exists()


@pytest.mark.parametrize("text", [
    '{\n  // a comment\n  "permissions": {}\n}\n',          # JSONC
    "{not json",                                           # invalid
    "[]\n",                                                # not an object
    '{"permissions": ["Read(./.env)"]}\n',                 # permissions not an object
    '{"permissions": {"deny": "Read(./.env)"}}\n',         # target list not a list
    '{"permissions": {"ask": null}}\n',                    # target list null
])
def test_ac6_unsafe_file_exit_2_byte_identical_reason_on_stderr(tmp_path, text):
    p = write_settings(tmp_path, text)
    before, mtime = sha(p), os.stat(p).st_mtime_ns
    for args in (["high-security"], ["high-security", "--dry-run"]):
        r = run(args, tmp_path)
        assert r.returncode == 2, (args, r.stdout)
        assert r.stderr.startswith("apply_profile: "), r.stderr
        assert sha(p) == before and os.stat(p).st_mtime_ns == mtime


def test_ac6_symlinked_settings_is_refused(tmp_path):
    real = tmp_path / "real.json"
    real.write_text("{}\n")
    settings_path(tmp_path).parent.mkdir(parents=True)
    os.symlink(real, settings_path(tmp_path))
    r = run(["high-security"], tmp_path)
    assert r.returncode == 2 and r.stderr.startswith("apply_profile: "), r.stderr
    assert real.read_text() == "{}\n"


def test_ac6_unknown_profile_exit_2_lists_valid_ids(tmp_path):
    r = run(["paranoid"], tmp_path)
    assert r.returncode == 2
    for pid in PROFILE_IDS:
        assert pid in r.stderr
    assert not settings_path(tmp_path).exists()


# ---- AC 7: dry-run and idempotence --------------------------------------------------------------

def test_ac7_dry_run_prints_adds_and_kept_writes_nothing(tmp_path):
    p = write_settings(tmp_path, {"cleanupPeriodDays": 30, "permissions": {"deny": ["Read(~/.ssh/**)"]}})
    before, mtime = sha(p), os.stat(p).st_mtime_ns
    r = run(["solo-engineer", "--dry-run"], tmp_path)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    expected_deny = [d for d in HIGH_SECURITY["permissions.deny"] if d != "Read(~/.ssh/**)"]
    for rule in expected_deny:
        assert f"+ permissions.deny: {rule}" in lines
    for rule in HIGH_SECURITY["permissions.ask"]:
        assert f"+ permissions.ask: {rule}" in lines
    assert "+ permissions.deny: Read(~/.ssh/**)" not in lines
    assert '+ autoUpdatesChannel: "stable"' in lines
    assert "= kept cleanupPeriodDays: 30" in lines
    assert not any(l.startswith("+ cleanupPeriodDays") for l in lines)
    assert sha(p) == before and os.stat(p).st_mtime_ns == mtime


def test_ac7_dry_run_on_missing_file_creates_nothing(tmp_path):
    r = run(["high-security", "--dry-run"], tmp_path)
    assert r.returncode == 0
    assert '+ permissions.disableBypassPermissionsMode: "disable"' in r.stdout.splitlines()
    assert not settings_path(tmp_path).exists()
    assert not (tmp_path / ".claude").exists()


def test_ac7_second_run_says_no_change_and_does_not_rewrite(tmp_path):
    p = write_settings(tmp_path, kit_shaped())
    assert run(["high-security"], tmp_path).returncode == 0
    before, mtime = sha(p), os.stat(p).st_mtime_ns
    r = run(["high-security"], tmp_path)
    assert r.returncode == 0
    assert r.stdout.strip() == "no change"
    assert sha(p) == before and os.stat(p).st_mtime_ns == mtime
    assert run(["high-security", "--dry-run"], tmp_path).stdout.strip() == "no change"


def test_ac7_legacy_on_kit_installed_project_is_a_no_op(tmp_path):
    p = write_settings(tmp_path, kit_shaped())
    before = sha(p)
    r = run(["legacy"], tmp_path)
    assert r.returncode == 0 and r.stdout.strip() == "no change"
    assert sha(p) == before


# ---- AC 8: NFR-001 no profile lowers safety (M3) ------------------------------------------------

@pytest.mark.parametrize("pid", sorted(PROFILE_IDS))
def test_ac8_no_profile_lowers_safety(pid):
    values = profile(pid)["values"]
    assert "bypassPermissions" not in json.dumps(values)
    for key in values:
        assert "allow" not in key.split("."), f"{pid} sets an allow key: {key}"
        assert key != "permissions.defaultMode", f"{pid} sets permissions.defaultMode"
        assert not key.startswith("sandbox."), f"{pid} sets a sandbox key (D5)"


# ---- AC 9-11: skill text and wiring -------------------------------------------------------------

def test_ac9_skill_md_within_codex_cap_and_names_the_flow():
    assert os.path.getsize(SKILL_MD) <= 8192
    text = open(SKILL_MD, encoding="utf-8").read()
    assert re.search(r"^name: settings-setup$", text, re.MULTILINE)
    for needle in ("--dry-run", "high-security", "[auto]", "scripts/apply_profile.py", "profiles.json"):
        assert needle in text, needle
    assert re.search(r"(?i)skip", text)


def test_ac10_stage_1_item_1_and_stage_index_name_the_skill():
    stages = open(os.path.join(ROOT, "docs", "claude-md", "pipeline-stages.md"), encoding="utf-8").read()
    item1 = re.search(r"^1\. \*\*One-Time Setup.*?(?=^2\. )", stages, re.MULTILINE | re.DOTALL)
    assert item1, "Stage 1 item 1 not found"
    assert 'Skill({ skill: "settings-setup" })' in item1.group(0)
    assert re.search(r"Auto mode:[^\n]*settings-setup", item1.group(0))
    agents = open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8").read()
    one = re.search(r"\| 1=([^|]*)\|", agents)
    assert one and "`settings-setup`" in one.group(1)


def test_ac11_site_roster_lists_the_skill_under_stage_1():
    text = open(PAGE, encoding="utf-8").read()
    step = re.search(r'<li class="flow-step" data-stage="1"[^>]*>(.*?)</li>', text, re.DOTALL)
    assert step and '<span class="chip">settings-setup</span>' in step.group(1)
