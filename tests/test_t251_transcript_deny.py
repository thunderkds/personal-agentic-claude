"""T251 — agents cannot write a session transcript: deny rules in .claude/settings.json.

The merge gate trusts `<sid>.jsonl` in the transcripts folder as proof of the user's `/verify`
(T250). These tests pin the kit's deny list: the two run-record rules stay first and in order, and
two rules for the default transcripts folder `~/.claude/projects/` follow them.
"""
import fnmatch
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SETTINGS = REPO / ".claude" / "settings.json"

OLD_RULES = ["Edit(~/.claude/harness-anchors/**)", "Bash(*harness-anchors*)"]
EDIT_RULE = "Edit(~/.claude/projects/**/*.jsonl)"
BASH_RULE = "Bash(*.claude/projects/*)"


def settings():
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def deny():
    return settings()["permissions"]["deny"]


def bash_pattern():
    assert BASH_RULE.startswith("Bash(") and BASH_RULE.endswith(")")
    return BASH_RULE[len("Bash("):-1]


def hook_commands():
    commands = []
    for groups in settings()["hooks"].values():
        for group in groups:
            commands += [h["command"] for h in group["hooks"]]
    return commands


# --- AC 1, 2: the deny list ----------------------------------------------------------------------

def test_ac1_the_two_run_record_rules_stay_first_and_in_order():
    assert deny()[:2] == OLD_RULES


def test_ac1_an_edit_rule_covers_jsonl_files_under_the_default_transcripts_folder():
    assert EDIT_RULE in deny()


def test_ac2_a_bash_rule_matches_a_command_that_names_the_transcripts_folder():
    assert BASH_RULE in deny()


def test_ac1_ac2_each_new_rule_is_listed_once_after_the_old_ones():
    rules = deny()
    assert rules == OLD_RULES + [EDIT_RULE, BASH_RULE]


# --- the Bash pattern: stops the forgery, leaves the kit's own commands alone ---------------------

def test_bash_pattern_matches_commands_that_name_the_transcripts_folder():
    forged = [
        "cat > ~/.claude/projects/-home-u-repo/fake-sid.jsonl <<'EOF'\n{}\nEOF",
        "echo '{}' >> /home/u/.claude/projects/-home-u-repo/fake-sid.jsonl",
        "cp /tmp/x.jsonl $HOME/.claude/projects/p/s.jsonl",
        "python3 -c \"open('/home/u/.claude/projects/p/s.jsonl','w')\"",
    ]
    for command in forged:
        assert fnmatch.fnmatchcase(command, bash_pattern()), command


def test_bash_pattern_does_not_match_the_kits_normal_commands():
    normal = [
        "git status",
        "git merge --no-ff fix/t251-transcript-deny",
        "git push origin fix/t251-transcript-deny",
        "python3 -m pytest .claude/hooks/tests/ tests/ -q",
        "python3 -m pytest tests/test_t251_transcript_deny.py -q",
        "bash tests/test_settings_merge.sh",
        "python3 .claude/hooks/stop_auto_verify.py --start T251",
        "ls .claude/hooks/lib",
        "grep -rn permissions .claude/settings.json",
    ]
    normal += hook_commands()
    assert len(normal) > 9
    for command in normal:
        assert not fnmatch.fnmatchcase(command, bash_pattern()), command


# --- AC 6: no rule blocks the hooks' own reads ---------------------------------------------------

def test_ac6_no_deny_rule_is_a_read_rule():
    # The hooks read transcripts in Python, not through a tool call, so they are not stopped; a
    # `Read(...)` rule would only stop the agent reading, which the task does not ask for.
    assert not [r for r in deny() if r.startswith("Read(")]
