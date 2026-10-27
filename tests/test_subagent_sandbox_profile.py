"""T147 — CLI-spawned sub-agents run under a tighter sandbox profile than the Supervisor.

  SC1/AC1 — every `.claude/sensitive-paths.txt` pattern has a Read and an Edit deny rule
            in `templates/subagent-sandbox.settings.json`, and Bash has no network.
  AC3     — drift: the committed profile is exactly what the generator produces, and a
            pattern added to the list without regenerating is caught.
  AC5     — the profile never waits on a human (`dontAsk`) and pre-allows the test runners.
  SC5/AC4 — the Supervisor's `.claude/settings.json` carries no permissions or sandbox block,
            except T148's deny-only trace-anchor rules (narrowed by user decision, 2026-10-17).
  AC2     — craft-spawn-prompt's CLI spawn command passes the profile; Agent() is said to be
            unsandboxed.

The deny check re-derives the expected rules here rather than calling the generator, so a
generator that silently drops a pattern cannot pass by agreeing with itself.

Run with: python3 -m pytest tests/test_subagent_sandbox_profile.py -q
"""
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS = os.path.join(ROOT, ".claude", "sensitive-paths.txt")
PROFILE = os.path.join(ROOT, "templates", "subagent-sandbox.settings.json")
GENERATOR = os.path.join(ROOT, "scripts", "gen_sandbox_profile.py")
SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
SKILL = os.path.join(ROOT, "skills", "craft-spawn-prompt", "SKILL.md")
SKILL_SANDBOX_REF = os.path.join(ROOT, "skills", "craft-spawn-prompt", "references", "sandbox.md")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _profile():
    return json.loads(_read(PROFILE))


def _expand(pattern):
    match = re.search(r"\{([^{}]*)\}", pattern)
    if not match:
        return [pattern]
    return [g for opt in match.group(1).split(",")
            for g in _expand(pattern[:match.start()] + opt + pattern[match.end():])]


def missing_denies(patterns_text, profile):
    deny = set(profile["permissions"]["deny"])
    missing = []
    for line in patterns_text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith(("#", "!")):
            continue
        for glob in _expand(raw.replace("\\", "/").lstrip("/")):
            for tool in ("Read", "Edit"):
                if f"{tool}({glob})" not in deny:
                    missing.append(f"{tool}({glob})")
    return missing


def test_sc1_every_sensitive_pattern_is_denied_for_read_and_edit():
    assert missing_denies(_read(PATTERNS), _profile()) == []


def test_sc1_brace_patterns_are_expanded():
    deny = _profile()["permissions"]["deny"]
    for ext in ("yml", "yaml", "json", "tf"):
        assert f"Edit(**/prod*.{ext})" in deny


def test_ac3_profile_is_exactly_what_the_generator_produces():
    proc = subprocess.run([sys.executable, GENERATOR, "--check"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_ac3_a_new_pattern_without_regenerating_is_caught():
    grown = _read(PATTERNS) + "\nvault/**\n"
    assert missing_denies(grown, _profile()) == ["Read(vault/**)", "Edit(vault/**)"]


def test_ac1_no_network_for_bash_or_web_tools():
    profile = _profile()
    sandbox = profile["sandbox"]
    assert sandbox["enabled"] is True
    assert sandbox["network"]["allowedDomains"] == []
    assert sandbox["network"]["strictAllowlist"] is True
    assert sandbox["allowUnsandboxedCommands"] is False  # no escape hatch out of the sandbox
    assert sandbox["failIfUnavailable"] is True  # never silently run unsandboxed
    assert {"WebFetch", "WebSearch"} <= set(profile["permissions"]["deny"])


def test_ac1_writes_only_inside_the_worktree_and_never_to_memory():
    permissions = _profile()["permissions"]
    assert [r for r in permissions["allow"] if r.startswith("Edit(")] == ["Edit(./**)"]
    assert "Edit(memory/**)" in permissions["deny"]


def test_no_rule_is_anchored_at_the_profile_file():
    # `/path` in a --settings file anchors at templates/, `//path` is absolute; the worktree
    # differs per spawn, so every path rule must stay cwd-relative.
    permissions = _profile()["permissions"]
    for rule in permissions["allow"] + permissions["deny"]:
        inner = rule[rule.find("(") + 1:-1] if "(" in rule else ""
        assert not inner.startswith("/"), rule


def test_ac5_never_waits_on_a_human_and_test_runners_are_preallowed():
    permissions = _profile()["permissions"]
    assert permissions["defaultMode"] == "dontAsk"
    assert "Bash(python3 -m pytest *)" in permissions["allow"]
    assert _profile()["sandbox"]["autoAllowBashIfSandboxed"] is True


# T148 (user decision, 2026-10-17): the Supervisor's settings may carry exactly one
# permissions block — deny-only, holding exactly the trace-anchor rules. Anything else
# (allow, ask, defaultMode, sandbox, another deny entry) still changes the Supervisor's
# permissions and fails T147's AC4.
ANCHOR_DENY_RULES = ["Edit(~/.claude/harness-anchors/**)", "Bash(*harness-anchors*)"]


def supervisor_settings_violations(settings):
    problems = []
    if "sandbox" in settings:
        problems.append("sandbox block present")
    permissions = settings.get("permissions")
    if permissions is None:
        return problems
    if not isinstance(permissions, dict) or set(permissions) != {"deny"}:
        problems.append("permissions must hold only 'deny': %r" % (permissions,))
    elif sorted(permissions["deny"]) != sorted(ANCHOR_DENY_RULES):
        problems.append("deny must be exactly the anchor rules: %r" % (permissions["deny"],))
    return problems


def test_sc5_supervisor_settings_have_no_permissions_or_sandbox():
    settings = json.loads(_read(SETTINGS))
    assert supervisor_settings_violations(settings) == []
    has_main = subprocess.run(["git", "-C", ROOT, "rev-parse", "--verify", "-q", "main"],
                              capture_output=True).returncode == 0
    if has_main:
        diff = subprocess.run(["git", "-C", ROOT, "diff", "main", "--", ".claude/settings.json"],
                              capture_output=True, text=True).stdout
        assert "sandbox" not in diff
        changed = [line[1:].strip().rstrip(",") for line in diff.splitlines()
                   if line[:1] in "+-" and not line.startswith(("+++", "---"))]
        allowed = {'"permissions": {', '"deny": [', "]", "}", "},", ""} | {
            json.dumps(rule) for rule in ANCHOR_DENY_RULES}
        # T180 D8: one Stop hook entry (a hook, not a permission or sandbox setting). Named
        # line by line, so any other settings change still fails here.
        allowed |= {"{", '"hooks": [', '"type": "command"',
                    '"description": "Auto mode (T180 D8): block the stop until the final report '
                    'holds up — report file, Advocates per Risk, Stage 4"',
                    '"command": "python3 \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/'
                    'stop_auto_mode_check.py"'}
        # T182: one more Stop hook entry (auto verify), likewise named line by line.
        allowed |= {'"description": "Auto verify (T182): for a Mode: auto task at Ready for Review, '
                    'start one detached headless /verify run per head commit; the run writes the '
                    'verify row and its record"',
                    '"command": "python3 \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/'
                    'stop_auto_verify.py"'}
        assert set(changed) <= allowed, set(changed) - allowed


@pytest.mark.parametrize("extra", [
    {"allow": ["Bash(python3 -m pytest *)"]},
    {"ask": ["Bash(git push *)"]},
    {"defaultMode": "dontAsk"},
])
def test_sc5_any_permission_beyond_the_anchor_deny_still_fails(extra):
    settings = json.loads(_read(SETTINGS))
    settings.setdefault("permissions", {"deny": list(ANCHOR_DENY_RULES)}).update(extra)
    assert supervisor_settings_violations(settings)


def test_sc5_an_extra_deny_entry_or_a_sandbox_block_still_fails():
    base = {"permissions": {"deny": ANCHOR_DENY_RULES + ["Edit(src/**)"]}}
    assert supervisor_settings_violations(base)
    assert supervisor_settings_violations({"sandbox": {"enabled": True}})
    assert supervisor_settings_violations({"permissions": {"deny": ANCHOR_DENY_RULES[:1]}})


def test_ac2_cli_spawn_command_passes_the_profile():
    skill = _read(SKILL)
    assert "`references/sandbox.md`" in skill  # step 6 points at the command
    command = re.search(r"^claude .*$", _read(SKILL_SANDBOX_REF), re.MULTILINE).group(0)
    assert "--settings templates/subagent-sandbox.settings.json" in command
    assert "--add-dir <main-checkout>/.claude/hooks/.state" in command  # element 6 still lands


def test_ac2_agent_spawns_are_said_to_be_unsandboxed():
    for text in (_read(SKILL), _read(SKILL_SANDBOX_REF)):
        assert re.search(r"`Agent\(\)`(?: in-process)? spawns are \*\*not\*\*\s+sandboxed", text)


def test_manifest_ships_profile_and_generator():
    entries = [l.split()[0] for l in _read(os.path.join(ROOT, "MANIFEST")).splitlines()
               if l.strip() and not l.startswith(("#", "!"))]
    assert "templates" in entries  # carries subagent-sandbox.settings.json
    assert "scripts/gen_sandbox_profile.py" in entries
    assert ".claude/sensitive-paths.txt" in entries
