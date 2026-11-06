"""T228 - dotfiles skill: plan/apply/status from one source into chosen CLI folders.

Every test works in a temp HOME; none touches the real ~/.claude* or ~/.codex.
"""
import ast
import builtins
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "dotfiles"
SCRIPT = SKILL_DIR / "scripts" / "dotfiles.py"

DENY = ["Read(./.env)", "Read(~/.ssh/**)", "Bash(rm -rf *)", "Bash(sudo *)",
        "Bash(curl *)", "Edit(~/.bashrc)", "Bash(git push --force*)"]
SECRET = "sk-secret-value-T228"


@pytest.fixture
def home(tmp_path):
    root = tmp_path / "home"
    root.mkdir()
    return root


def run(home, *args):
    env = dict(os.environ, HOME=str(home))
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                          capture_output=True, text=True, timeout=30)


def make_source(home, base=None, agents=None, skills=()):
    source = home / "dots"
    source.mkdir()
    if base is not None:
        (source / "settings.base.json").write_text(json.dumps(base))
    if agents is not None:
        (source / "AGENTS.md").write_text(agents)
    for name in skills:
        (source / "skills" / name).mkdir(parents=True)
        (source / "skills" / name / "SKILL.md").write_text("x")
    return source


def make_claude(home, name=".claude", settings=None):
    target = home / name
    target.mkdir()
    if settings is not None:
        (target / "settings.json").write_text(
            settings if isinstance(settings, str) else json.dumps(settings))
    return target


def tree_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path).encode())
        if path.is_symlink():
            digest.update(os.readlink(path).encode())
        elif path.is_file():
            digest.update(path.read_bytes())
            digest.update(str(path.stat().st_mtime_ns).encode())
    return digest.hexdigest()


def backups(target):
    return sorted(p.name for p in target.iterdir() if p.name.startswith("settings.json.bak-"))


# --- AC1: script shape, no target folder ------------------------------------------------------

def test_no_target_lists_found_folders_and_changes_nothing(home):
    source = make_source(home, base={"permissions": {"deny": DENY}})
    make_claude(home, ".claude", {})
    make_claude(home, ".claude-work", {})
    make_claude(home, ".claude-empty")  # no settings.json: not listed
    (home / ".claude.json").write_text("{}")  # a file: not listed
    (home / ".codex").mkdir()
    before = tree_hash(home)
    for command in ("plan", "apply", "status"):
        result = run(home, command, "--source", str(source))
        assert result.returncode == 0, result.stderr
        assert str(home / ".claude\n") in result.stdout + "\n"
        assert str(home / ".claude-work") in result.stdout
        assert str(home / ".codex") in result.stdout
        assert ".claude-empty" not in result.stdout
        assert ".claude.json" not in result.stdout
    assert tree_hash(home) == before


def test_source_defaults_to_dotfiles_agents_under_home(home):
    source = home / ".dotfiles" / "agents"
    source.mkdir(parents=True)
    (source / "AGENTS.md").write_text("rules")
    target = make_claude(home)
    result = run(home, "plan", "--claude-dir", str(target))
    assert result.returncode == 0
    assert "CLAUDE.md" in result.stdout


# --- AC2: source layout -----------------------------------------------------------------------

def test_missing_source_prints_layout_exits_zero_no_write(home):
    target = make_claude(home, settings={})
    before = tree_hash(home)
    for command, code in (("plan", 0), ("apply", 0), ("status", 2)):
        result = run(home, command, "--source", str(home / "nope"), "--claude-dir", str(target))
        assert result.returncode == code, command
        for part in ("settings.base.json", "AGENTS.md", "skills/<name>/"):
            assert part in result.stdout
    assert tree_hash(home) == before


def test_status_with_missing_source_and_no_target_exits_zero(home):
    assert run(home, "status", "--source", str(home / "nope")).returncode == 0


@pytest.mark.parametrize("command", ["plan", "apply", "status"])
@pytest.mark.parametrize("flag", ["--source", "--claude-dir", "--codex-dir"])
def test_empty_path_is_rejected_with_no_write(home, tmp_path, flag, command):
    """abspath('') is the current folder, so an empty value must never reach it."""
    source = make_source(home, agents="rules", skills=["one"])
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    args = {"--source": str(source), "--claude-dir": str(make_claude(home))}
    args[flag] = ""
    flat = [item for pair in args.items() for item in pair]
    env = dict(os.environ, HOME=str(home))
    before = tree_hash(tmp_path)
    result = subprocess.run([sys.executable, str(SCRIPT), command, *flat], env=env, cwd=cwd,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "must not be empty" in result.stderr
    assert tree_hash(tmp_path) == before


@pytest.mark.parametrize("key", ["deny", "ask"])
@pytest.mark.parametrize("rule", ["", "Bash(ls)\nBash(rm *)", "a\tb", "a\rb", "a\x7fb", "a\x1b[2Kb"])
def test_source_rule_that_prints_differently_is_refused(home, key, rule):
    source = make_source(home, base={"permissions": {key: ["ok", rule]}})
    target = make_claude(home, settings={})
    before = tree_hash(home)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 2
    assert "refused source" in result.stderr
    assert tree_hash(home) == before


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_dangling_source_base_link_is_refused(home):
    source = make_source(home, agents="rules")
    (source / "settings.base.json").symlink_to(home / "gone.json")
    target = make_claude(home, settings={})
    before = tree_hash(home)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 2
    assert "refused source" in result.stderr
    assert tree_hash(home) == before


def test_duplicate_key_in_source_is_refused(home):
    source = make_source(home)
    (source / "settings.base.json").write_text(
        '{"permissions": {"deny": ["a"], "deny": ["b"]}}')
    target = make_claude(home, settings={})
    before = tree_hash(home)
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 2
    assert tree_hash(home) == before


def test_source_that_cannot_be_written_as_utf8_is_refused(home):
    source = make_source(home)
    (source / "settings.base.json").write_text('{"permissions": {"deny": ["\\ud800"]}, "\\ud800": 1}')
    target = make_claude(home, settings={})
    before = tree_hash(home)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 2
    assert "refused source" in result.stderr
    assert "Traceback" not in result.stderr
    assert tree_hash(home) == before


def test_each_source_part_is_optional(home):
    source = make_source(home, skills=["one"])
    target = make_claude(home, settings={"a": 1})
    raw = (target / "settings.json").read_bytes()
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 0
    assert (target / "skills" / "one").is_symlink()
    assert not (target / "CLAUDE.md").exists()
    assert (target / "settings.json").read_bytes() == raw


def test_invalid_source_base_refuses_everything(home):
    source = make_source(home, agents="rules")
    (source / "settings.base.json").write_text("{bad")
    target = make_claude(home, settings={})
    before = tree_hash(home)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode != 0
    assert tree_hash(home) == before


@pytest.mark.parametrize("base", [[], {"permissions": []}, {"permissions": {"deny": "x"}},
                                  {"permissions": {"ask": [1]}}])
def test_source_base_of_wrong_type_is_refused(home, base):
    source = make_source(home, base=base)
    target = make_claude(home, settings={})
    before = tree_hash(home)
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode != 0
    assert tree_hash(home) == before


# --- AC3 / SC3: plan writes nothing -----------------------------------------------------------

def test_plan_prints_every_change_and_writes_nothing(home):
    source = make_source(home, base={"permissions": {"deny": DENY, "ask": ["Bash(npm *)"]}},
                         agents="rules", skills=["one", "two"])
    claude = make_claude(home, settings={"permissions": {"deny": [DENY[0]]}})
    codex = home / ".codex"
    codex.mkdir()
    before = tree_hash(home)
    result = run(home, "plan", "--source", str(source), "--claude-dir", str(claude),
                 "--codex-dir", str(codex))
    assert result.returncode == 0
    assert tree_hash(home) == before
    for rule in DENY[1:] + ["Bash(npm *)"]:
        assert rule in result.stdout
    assert f"+ permissions.deny: {DENY[0]}" not in result.stdout
    assert result.stdout.count("+ link skills/one") == 2
    assert result.stdout.count("+ link skills/two") == 2
    assert "CLAUDE.md" in result.stdout and "AGENTS.md" in result.stdout
    assert result.stdout.index(str(claude)) < result.stdout.index(str(codex))


# --- AC4 / SC1: settings union ----------------------------------------------------------------

def test_apply_adds_deny_only_and_keeps_every_target_key(home):
    source = make_source(home, base={
        "permissions": {"deny": DENY, "allow": ["Bash(*)", "Read(*)"], "defaultMode": "bypassPermissions"},
        "env": {"TOKEN": SECRET},
        "hooks": {"Stop": []},
    })
    original = {"model": "opus", "permissions": {"allow": ["Bash(ls)"], "ask": ["Bash(a)"]},
                "hooks": {"Stop": [{"x": 1}]}, "env": {"KEEP": "é"}, "zzz": [1, 2]}
    target = make_claude(home, settings=original)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 0, result.stderr
    after = json.loads((target / "settings.json").read_text(encoding="utf-8"))
    assert after["permissions"]["deny"] == DENY
    assert after["permissions"]["allow"] == ["Bash(ls)"]
    assert after["permissions"]["ask"] == ["Bash(a)"]
    assert "defaultMode" not in after["permissions"]
    for key in ("model", "hooks", "env", "zzz"):
        assert after[key] == original[key]
    assert list(after) == list(original)
    for ignored in ("env", "hooks", "permissions.allow", "permissions.defaultMode"):
        assert ignored in result.stdout
    assert SECRET not in result.stdout + result.stderr


def test_lists_keep_target_order_first_without_duplicates(home):
    source = make_source(home, base={"permissions": {"deny": ["b", "c", "c"], "ask": ["q"]}})
    target = make_claude(home, settings={"permissions": {"deny": ["z", "b"], "ask": ["q"]}})
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 0
    after = json.loads((target / "settings.json").read_text())
    assert after["permissions"] == {"deny": ["z", "b", "c"], "ask": ["q"]}


def test_missing_settings_is_created_with_only_the_added_rules(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    target = make_claude(home)
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 0
    assert json.loads((target / "settings.json").read_text()) == {"permissions": {"deny": ["a"]}}
    assert backups(target) == []


# --- AC5 / SC2 / SC8: write safety ------------------------------------------------------------

def test_apply_backs_up_prior_bytes_before_a_change(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    raw = '{\n    "kept":   true\n}\n'
    target = make_claude(home, settings=raw)
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 0
    names = backups(target)
    assert len(names) == 1
    assert re.fullmatch(r"settings\.json\.bak-\d{8}T\d{6}Z(\.\d+)?", names[0])
    assert (target / names[0]).read_text() == raw


def test_second_apply_writes_nothing(home):
    source = make_source(home, base={"permissions": {"deny": DENY}}, agents="rules", skills=["one"])
    target = make_claude(home, settings={})
    args = ("--source", str(source), "--claude-dir", str(target))
    assert run(home, "apply", *args).returncode == 0
    before = tree_hash(home)
    second = run(home, "apply", *args)
    assert second.returncode == 0
    assert "no change" in second.stdout
    assert tree_hash(home) == before
    assert len(backups(target)) == 1


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [S_IMODE]")
def test_mode_600_survives_on_settings_and_on_the_backup(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    target = make_claude(home, settings={})
    (target / "settings.json").chmod(0o600)
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 0
    assert stat.S_IMODE((target / "settings.json").stat().st_mode) == 0o600
    assert stat.S_IMODE((target / backups(target)[0]).stat().st_mode) == 0o600


def test_apply_leaves_no_temp_file(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    target = make_claude(home, settings={})
    run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert sorted(p.name for p in target.iterdir()) == sorted(["settings.json"] + backups(target))


def test_backup_never_overwrites_an_existing_backup(home, monkeypatch):
    module = load_module()
    target = make_claude(home, settings={})
    monkeypatch.setattr(module.time, "strftime", lambda *a: "20261101T000000Z")
    first = module.write_backup(str(target / "settings.json"), b"one", 0o600)
    second = module.write_backup(str(target / "settings.json"), b"two", 0o600)
    assert first != second
    assert Path(first).read_bytes() == b"one" and Path(second).read_bytes() == b"two"


# --- AC6 / SC5: links -------------------------------------------------------------------------

def test_links_are_made_for_skills_and_instructions(home):
    source = make_source(home, agents="rules", skills=["one", ".hidden"])
    (source / "skills" / "notes.txt").write_text("not a skill")
    claude = make_claude(home)
    codex = home / ".codex"
    codex.mkdir()
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(claude),
                 "--codex-dir", str(codex))
    assert result.returncode == 0, result.stderr
    assert os.readlink(claude / "CLAUDE.md") == str(source / "AGENTS.md")
    assert os.readlink(codex / "AGENTS.md") == str(source / "AGENTS.md")
    for target in (claude, codex):
        assert os.readlink(target / "skills" / "one") == str(source / "skills" / "one")
        assert not (target / "skills" / ".hidden").exists()
        assert not (target / "skills" / "notes.txt").exists()


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_conflicts_are_reported_and_left_unchanged(home):
    source = make_source(home, agents="rules", skills=["x", "y"])
    target = make_claude(home)
    (target / "CLAUDE.md").write_text("my own rules")
    (target / "skills").mkdir()
    elsewhere = home / "elsewhere"
    elsewhere.mkdir()
    (target / "skills" / "x").symlink_to(elsewhere)
    before = tree_hash(target)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert (target / "CLAUDE.md").read_text() == "my own rules"
    assert os.readlink(target / "skills" / "x") == str(elsewhere)
    assert re.search(r"conflict.*CLAUDE\.md", result.stdout)
    assert re.search(r"conflict.*skills/x", result.stdout)
    # the part with no conflict still goes on
    assert (target / "skills" / "y").is_symlink()
    os.unlink(target / "skills" / "y")
    assert tree_hash(target) == before


def test_empty_claude_md_is_a_conflict(home):
    source = make_source(home, agents="rules")
    target = make_claude(home)
    (target / "CLAUDE.md").write_text("")
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert "conflict" in result.stdout
    assert not (target / "CLAUDE.md").is_symlink()


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_dangling_link_is_a_conflict(home):
    source = make_source(home, agents="rules")
    target = make_claude(home)
    (target / "CLAUDE.md").symlink_to(home / "gone")
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert "conflict" in result.stdout
    assert os.readlink(target / "CLAUDE.md") == str(home / "gone")


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_correct_link_is_no_change(home):
    source = make_source(home, agents="rules")
    target = make_claude(home)
    (target / "CLAUDE.md").symlink_to(source / "AGENTS.md")
    result = run(home, "plan", "--source", str(source), "--claude-dir", str(target))
    assert "no change" in result.stdout and "conflict" not in result.stdout


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
@pytest.mark.parametrize("kind", ["link", "file"])
def test_skills_path_that_is_not_a_plain_folder_is_a_conflict(home, kind):
    """A link there would drop our links into whatever folder it points at."""
    source = make_source(home, skills=["one"])
    target = make_claude(home)
    outside = home / "outside"
    outside.mkdir()
    if kind == "link":
        (target / "skills").symlink_to(outside)
    else:
        (target / "skills").write_text("x")
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert "conflict" in result.stdout
    assert list(outside.iterdir()) == []


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_symlinked_settings_is_reported_and_not_replaced(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    real = home / "real.json"
    real.write_text("{}")
    target = make_claude(home)
    (target / "settings.json").symlink_to(real)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert "conflict" in result.stdout
    assert (target / "settings.json").is_symlink()
    assert real.read_text() == "{}"


# --- AC7: Codex and missing folders -----------------------------------------------------------

def test_codex_target_never_gets_settings(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}}, agents="rules")
    codex = home / ".codex"
    codex.mkdir()
    (codex / "settings.json").write_text("{bad, and not ours")
    result = run(home, "apply", "--source", str(source), "--codex-dir", str(codex))
    assert result.returncode == 0, result.stderr
    assert (codex / "settings.json").read_text() == "{bad, and not ours"
    assert sorted(p.name for p in codex.iterdir()) == ["AGENTS.md", "settings.json"]


def test_missing_target_gets_one_skipped_line(home):
    source = make_source(home, agents="rules")
    missing = home / ".claude-missing"
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(missing))
    assert result.returncode == 0
    assert len([l for l in result.stdout.splitlines() if "skipped" in l]) == 1
    assert not missing.exists()


# --- AC8 / SC4: refusals and status -----------------------------------------------------------

@pytest.mark.parametrize("bad", ["", "{not json", "[]", '{"permissions": []}',
                                 '{"permissions": {"deny": "x"}}', '{"permissions": {"ask": 1}}',
                                 '{"permissions": null}'])
def test_bad_target_is_refused_and_the_next_goes_on(home, bad):
    source = make_source(home, base={"permissions": {"deny": ["a"], "ask": ["b"]}},
                         agents="rules", skills=["one"])
    broken = make_claude(home, ".claude-a", bad)
    good = make_claude(home, ".claude-b", {})
    before = tree_hash(broken)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(broken),
                 "--claude-dir", str(good))
    assert result.returncode != 0
    assert tree_hash(broken) == before  # no link either: nothing written there
    assert json.loads((good / "settings.json").read_text())["permissions"]["deny"] == ["a"]
    assert "refused" in result.stdout + result.stderr


@pytest.mark.parametrize("command", ["plan", "apply"])
@pytest.mark.parametrize("bad", ['{"a": "\\ud800"}',  # no UTF-8 form, so it cannot be rewritten
                                 '{"a": 1, "a": 2}',  # a rewrite would lose a value
                                 '{"nested": {"b": 1, "b": 2}}'])
def test_unwritable_target_is_refused_before_any_backup(home, command, bad):
    source = make_source(home, base={"permissions": {"deny": ["a"]}}, agents="rules")
    broken = make_claude(home, ".claude-a", bad)
    good = make_claude(home, ".claude-b", {})
    before = tree_hash(broken)
    result = run(home, command, "--source", str(source), "--claude-dir", str(broken),
                 "--claude-dir", str(good))
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    assert "refused" in result.stdout
    assert tree_hash(broken) == before
    assert backups(broken) == []
    assert str(good) in result.stdout
    if command == "apply":
        assert json.loads((good / "settings.json").read_text())["permissions"]["deny"] == ["a"]


@pytest.mark.parametrize("command", ["plan", "apply"])
@pytest.mark.parametrize("bad", ['{"w": NaN}', '{"w": Infinity}', '{"w": -Infinity}',
                                 '{"t": 1e400}', '{"t": -1e400}'])
def test_non_finite_number_in_target_is_refused(home, command, bad):
    """Strict JSON has none of these, and a rewrite would turn 1e400 into `Infinity`."""
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    broken = make_claude(home, ".claude-a", bad)
    good = make_claude(home, ".claude-b", {})
    before = tree_hash(broken)
    result = run(home, command, "--source", str(source), "--claude-dir", str(broken),
                 "--claude-dir", str(good))
    assert result.returncode == 2, result.stderr
    assert "refused" in result.stdout
    assert tree_hash(broken) == before
    assert backups(broken) == []
    assert str(good) in result.stdout
    if command == "apply":
        assert json.loads((good / "settings.json").read_text())["permissions"]["deny"] == ["a"]


def test_ordinary_float_is_kept(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    target = make_claude(home, settings='{"t": 0.5, "big": 1e300}')
    assert run(home, "apply", "--source", str(source), "--claude-dir", str(target)).returncode == 0
    after = json.loads((target / "settings.json").read_text())
    assert after["t"] == 0.5 and after["big"] == 1e300


@pytest.mark.parametrize("bad", ['{"w": NaN}', '{"t": 1e400}'])
def test_non_finite_number_in_source_is_refused(home, bad):
    source = make_source(home)
    (source / "settings.base.json").write_text(bad)
    target = make_claude(home, settings={})
    before = tree_hash(home)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 2
    assert "refused source" in result.stderr
    assert tree_hash(home) == before


# The kernel lets root write a 444 file, so os.access says yes: these two need a non-root user.
needs_non_root = pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="needs a non-root user")


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0o444)]")
@needs_non_root
@pytest.mark.parametrize("command", ["plan", "apply", "status"])
def test_read_only_settings_is_refused_and_the_lock_holds(home, command):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    locked = make_claude(home, ".claude-a", {"old": 1})
    good = make_claude(home, ".claude-b", {})
    (locked / "settings.json").chmod(0o444)
    before = tree_hash(locked)
    result = run(home, command, "--source", str(source), "--claude-dir", str(locked),
                 "--claude-dir", str(good))
    assert result.returncode == 2
    assert "refused" in result.stdout
    assert tree_hash(locked) == before
    assert stat.S_IMODE((locked / "settings.json").stat().st_mode) == 0o444
    assert backups(locked) == []
    if command == "apply":
        assert json.loads((good / "settings.json").read_text())["permissions"]["deny"] == ["a"]


@pytest.mark.posix_only("relies on POSIX permission bits or execute bits, which Windows does not enforce [chmod(0o444)]")
@needs_non_root
def test_read_only_settings_with_nothing_to_add_is_in_sync(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    target = make_claude(home, settings={"permissions": {"deny": ["a"]}})
    (target / "settings.json").chmod(0o444)
    assert run(home, "status", "--source", str(source), "--claude-dir", str(target)).returncode == 0


def test_write_failure_is_refused_and_the_next_goes_on(home, monkeypatch, capsys):
    """A crash at the rename leaves the old file and no temp file."""
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    first = make_claude(home, ".claude-a", {"old": 1})
    second = make_claude(home, ".claude-b", {})
    module = load_module()
    real_replace = os.replace

    def fail_once(src, dst):
        monkeypatch.setattr(module.os, "replace", real_replace)
        raise OSError("disk full")

    monkeypatch.setattr(module.os, "replace", fail_once)
    code = module.main(["apply", "--source", str(source), "--claude-dir", str(first),
                        "--claude-dir", str(second)])
    assert code == 2
    assert json.loads((first / "settings.json").read_text()) == {"old": 1}
    assert not [p for p in first.iterdir() if p.name.startswith(".settings.json")]
    assert json.loads((second / "settings.json").read_text())["permissions"]["deny"] == ["a"]
    assert "disk full" in capsys.readouterr().out


def test_missing_target_folder_codes(home):
    source = make_source(home, agents="rules")
    good = make_claude(home)
    args = ("--source", str(source), "--claude-dir", str(home / ".claude-gone"))
    status = run(home, "status", *args)
    assert status.returncode == 2
    assert "skipped" in status.stdout
    assert run(home, "plan", *args).returncode == 0
    assert run(home, "apply", *args, "--claude-dir", str(good)).returncode == 0
    assert run(home, "status", *args, "--claude-dir", str(good)).returncode == 2
    assert run(home, "status", "--source", str(source), "--claude-dir", str(good)).returncode == 0


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
@pytest.mark.parametrize("command", ["plan", "apply", "status"])
@pytest.mark.parametrize("flag", ["--claude-dir", "--codex-dir"])
def test_target_equal_to_source_is_refused_and_the_next_goes_on(home, command, flag):
    source = make_source(home, base={"permissions": {"deny": ["a"]}}, agents="rules", skills=["one"])
    alias = home / "alias"
    alias.symlink_to(source)
    good = make_claude(home, settings={})
    before = tree_hash(source)
    result = run(home, command, "--source", str(source), flag, str(alias), "--claude-dir", str(good))
    assert result.returncode == 2
    assert "refused" in result.stdout
    assert tree_hash(source) == before
    assert str(good) in result.stdout


def test_status_exit_codes(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}}, agents="rules")
    target = make_claude(home, settings={})
    args = ("--source", str(source), "--claude-dir", str(target))
    before = tree_hash(home)
    assert run(home, "status", *args).returncode == 1
    assert tree_hash(home) == before
    assert run(home, "apply", *args).returncode == 0
    in_sync = run(home, "status", *args)
    assert in_sync.returncode == 0 and "in sync" in in_sync.stdout


@pytest.mark.parametrize("gone", ["AGENTS.md", "skills/one", "skills/two"])
@pytest.mark.parametrize("flag", ["--claude-dir", "--codex-dir"])
def test_link_left_broken_by_the_source_is_a_conflict(home, gone, flag):
    source = make_source(home, agents="rules", skills=["one", "two"])
    target = home / "target"
    target.mkdir()
    args = ("--source", str(source), flag, str(target))
    assert run(home, "apply", *args).returncode == 0
    assert run(home, "status", *args).returncode == 0
    origin = source / gone
    if origin.is_dir():
        (origin / "SKILL.md").unlink()
        origin.rmdir()
    else:
        origin.unlink()
    name = {"AGENTS.md": "CLAUDE.md" if flag == "--claude-dir" else "AGENTS.md"}.get(gone, gone)
    before = tree_hash(target)
    status = run(home, "status", *args)
    assert status.returncode == 1
    assert f"conflict {name}: broken link, not changed" in status.stdout
    applied = run(home, "apply", *args)
    assert applied.returncode == 0
    assert applied.stdout.count("broken link") == 1
    assert tree_hash(target) == before  # apply never removes it


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_broken_link_is_reported_once_when_the_source_part_exists(home):
    source = make_source(home, agents="rules")
    target = make_claude(home)
    (target / "CLAUDE.md").symlink_to(source / "OLD.md")
    result = run(home, "status", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 1
    assert result.stdout.count("conflict") == 1
    assert "conflict CLAUDE.md: broken link, not changed" in result.stdout


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_broken_link_outside_the_source_is_left_alone(home):
    source = make_source(home)
    target = make_claude(home)
    (target / "skills").mkdir()
    (target / "skills" / "mine").symlink_to(home / "gone")
    (target / "AGENTS.md").symlink_to(str(source) + "-other/AGENTS.md")
    result = run(home, "status", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 0
    assert "broken link" not in result.stdout


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_relative_broken_link_into_the_source_is_found(home):
    source = make_source(home)
    target = make_claude(home)
    (target / "CLAUDE.md").symlink_to(os.path.join("..", source.name, "AGENTS.md"))
    assert run(home, "status", "--source", str(source), "--claude-dir", str(target)).returncode == 1


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_broken_link_found_through_a_linked_source_path(home):
    source = make_source(home)
    alias = home / "alias"
    alias.symlink_to(source)
    target = make_claude(home)
    (target / "CLAUDE.md").symlink_to(source / "AGENTS.md")
    assert run(home, "status", "--source", str(alias), "--claude-dir", str(target)).returncode == 1


def test_status_is_drift_on_a_conflict(home):
    source = make_source(home, agents="rules")
    target = make_claude(home)
    (target / "CLAUDE.md").write_text("mine")
    assert run(home, "status", "--source", str(source), "--claude-dir", str(target)).returncode == 1


def test_extra_target_rules_are_not_drift(home):
    source = make_source(home, base={"permissions": {"deny": ["a"]}})
    target = make_claude(home, settings={"permissions": {"deny": ["a", "mine"]}})
    assert run(home, "status", "--source", str(source), "--claude-dir", str(target)).returncode == 0


# --- AC9 / SC6 / SC7: what the script may touch -------------------------------------------------

def load_module():
    spec = importlib.util.spec_from_file_location("dotfiles_t228", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.posix_only("creates a symlink, which needs Developer Mode or admin rights on Windows [symlink_to]")
def test_only_settings_json_is_opened_in_a_target(home, monkeypatch, capsys):
    source = make_source(home, base={"permissions": {"deny": ["a"]}}, agents="rules", skills=["one"])
    target = make_claude(home, settings={})
    (target / ".credentials.json").write_text(json.dumps({"token": SECRET}))
    (target / "history.jsonl").write_text(SECRET)
    (target / "CLAUDE.md").write_text(SECRET)
    (target / "skills").mkdir()
    (target / "skills" / "gone").symlink_to(source / "skills" / "gone")
    for name in ("projects", "sessions"):
        (target / name).mkdir()
        (target / name / "x").write_text(SECRET)
    module = load_module()
    opened, listed = [], []
    real_open, real_listdir = builtins.open, os.listdir
    real_os_open = os.open

    def spy_open(path, *args, **kwargs):
        opened.append(str(path))
        return real_open(path, *args, **kwargs)

    def spy_os_open(path, *args, **kwargs):
        opened.append(str(path))
        return real_os_open(path, *args, **kwargs)

    def spy_listdir(path="."):
        listed.append(str(path))
        return real_listdir(path)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(os, "open", spy_os_open)
    monkeypatch.setattr(os, "listdir", spy_listdir)
    code = module.main(["apply", "--source", str(source), "--claude-dir", str(target)])
    monkeypatch.undo()
    out = capsys.readouterr()
    assert code == 0
    assert SECRET not in out.out + out.err
    inside = [p for p in opened if p.startswith(str(target))]
    assert inside, "the spy saw no open in the target"
    allowed = re.compile(re.escape(str(target)) + r"/(\.?settings\.json.*)$")
    assert all(allowed.fullmatch(p) for p in inside), inside
    assert [p for p in listed if p.startswith(str(target))] == [str(target / "skills")]


def test_script_names_no_private_path():
    text = SCRIPT.read_text(encoding="utf-8")
    for name in (".credentials", "history.jsonl", "projects", "sessions"):
        assert name not in text


def test_script_imports_stdlib_only_with_no_network_or_process():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    assert names <= set(sys.stdlib_module_names), names
    assert not names & {"subprocess", "socket", "urllib", "http", "ftplib", "smtplib",
                        "ssl", "requests", "multiprocessing", "asyncio"}, names
    calls = {node.func.attr for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert not calls & {"system", "popen", "execv", "execvp", "spawnv", "fork"}, calls


# --- AC10: the skill --------------------------------------------------------------------------

def test_skill_states_the_safety_rules():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert re.search(r"^name: dotfiles$", text, re.MULTILINE)
    lowered = text.lower()
    assert "optional" in lowered
    assert text.index('dotfiles.py" plan') < text.index('dotfiles.py" apply')
    assert "only after the user approves" in lowered
    assert "never pick a folder" in lowered
    auto = re.search(r"### Auto mode.*?(?=\n### |\Z)", text, re.DOTALL)
    assert auto, "no Auto mode section"
    assert "`plan`" in auto.group(0) and "Not done:" in auto.group(0)
    assert 'dotfiles.py" apply' not in auto.group(0)
    assert "the `plan` lines" not in auto.group(0)
    assert "folder list" in auto.group(0)
    step3 = re.search(r"### Step 3.*?(?=\n### )", text, re.DOTALL).group(0)
    assert "`1.10` to `1.1`" in step3
    assert "The value does not" not in step3
    assert "the backup keeps the original" in step3
    limits = re.search(r"^## Known limits\n(.*?)(?=\n#|\Z)", text, re.DOTALL | re.MULTILINE)
    assert limits, "no Known limits section"
    assert len(limits.group(1).strip().splitlines()) <= 5
    for phrase in ("run `status`", "FIFO", "traceback"):
        assert phrase in limits.group(1)
    assert "`refused`" in step3 and "were not made" in step3


# --- AC11: docs -------------------------------------------------------------------------------

def test_docs_name_the_skill():
    assert "dotfiles" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "`dotfiles/SKILL.md`" in (ROOT / "CLAUDE_LEGACY.md").read_text(encoding="utf-8")


# --- T230: target inside the source, unprintable skill names, wrong source shape -------------

@pytest.mark.parametrize("command", ["plan", "apply", "status"])
def test_t230_a_target_inside_the_source_is_refused(home, command):
    source = make_source(home, agents="rules", skills=["one"])
    inner = source / "skills" / "one"
    before = tree_hash(home)
    result = run(home, command, "--source", str(source), "--claude-dir", str(inner))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "target is inside the source folder" in result.stdout
    assert tree_hash(home) == before


def test_t230_a_target_holding_the_source_is_still_allowed(home):
    """~/.dotfiles/agents sits under HOME; a target that holds the source is not refused for it."""
    source = make_source(home, agents="rules")
    result = run(home, "plan", "--source", str(source), "--claude-dir", str(home))
    assert "inside the source" not in result.stdout, result.stdout


@pytest.mark.parametrize("name", ["evil\nplan: + link CLAUDE.md", "a\tb", "a\x1b[2Kb"])
def test_t230_a_skill_folder_name_with_unprintable_text_is_refused(home, name):
    source = make_source(home, skills=["ok"])
    (source / "skills" / name).mkdir()
    target = make_claude(home)
    before = tree_hash(home)
    result = run(home, "apply", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 2
    assert "refused source" in result.stderr and "unprintable" in result.stderr
    assert tree_hash(home) == before


@pytest.mark.parametrize("shape", ["agents_folder", "skills_file"])
def test_t230_a_wrong_source_shape_is_reported(home, shape):
    source = make_source(home)
    if shape == "agents_folder":
        (source / "AGENTS.md").mkdir()
        expect = "AGENTS.md is not a file"
    else:
        (source / "skills").write_text("x")
        expect = "skills is not a folder"
    target = make_claude(home)
    before = tree_hash(home)
    result = run(home, "plan", "--source", str(source), "--claude-dir", str(target))
    assert result.returncode == 2
    assert "refused source" in result.stderr and expect in result.stderr, result.stderr
    assert tree_hash(home) == before
