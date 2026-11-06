#!/usr/bin/env python3
"""T266 — kit hooks fire on the PowerShell tool, and the installer can write the Windows hook form.

AC1  matchers in .claude/settings.json and plugin/hooks/hooks.json cover PowerShell
AC2/3 pre_tool_sensitive_path.py and post_bash_memory_update.py accept tool_name "PowerShell"
AC4/10 merge-settings.py hook_paths and project_root.wires_in_repo_hook read exec-form `args`
AC5/6 lib/windows_hooks.py to_windows_settings converts kit entries to exec form
AC7  converted file round-trips through the real merge-settings.py; conversion is idempotent
AC8  the CLI refuses an unknown launcher with exit 2 and writes nothing
SC5  mutation control: an identity conversion turns the exec-form check red

Run with: python3 -m pytest tests/test_windows_hooks.py -q
"""
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS = os.path.join(REPO_ROOT, ".claude", "settings.json")
PLUGIN_HOOKS = os.path.join(REPO_ROOT, "plugin", "hooks", "hooks.json")
HOOKS_DIR = os.path.join(REPO_ROOT, ".claude", "hooks")
MERGE = os.path.join(REPO_ROOT, "lib", "merge-settings.py")
CONVERTER = os.path.join(REPO_ROOT, "lib", "windows_hooks.py")

EXPECTED_MATCHERS = ["Write", "Agent", "Bash|PowerShell", ".*", "Agent", "Bash|PowerShell",
                     "Edit|Write|Bash|PowerShell", ".*", None, None, None]


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_module(name, path, source=None):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if source is None:
        spec.loader.exec_module(module)
    else:
        exec(compile(source, path, "exec"), module.__dict__)
    return module


def all_hooks(settings):
    return [h for groups in settings["hooks"].values() for g in groups for h in g["hooks"]]


def all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from all_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from all_strings(v)


merge_settings = load_module("merge_settings", MERGE)
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
import project_root  # noqa: E402


# --- AC1: matchers ---------------------------------------------------------------

class MatcherTest(unittest.TestCase):
    def test_settings_and_plugin_matchers_cover_powershell(self):
        for path in (SETTINGS, PLUGIN_HOOKS):
            doc = load(path)
            matchers = [g.get("matcher") for ev in doc["hooks"].values() for g in ev]
            self.assertEqual(matchers, EXPECTED_MATCHERS, path)

    def test_settings_commands_stay_posix_python3(self):
        shape = re.compile(r'^python3 "\$CLAUDE_PROJECT_DIR"/\.claude/hooks/\w+\.py$')
        hooks = all_hooks(load(SETTINGS))
        self.assertEqual(len(hooks), 11)
        for hook in hooks:
            self.assertRegex(hook["command"], shape)
            self.assertNotIn("args", hook)

    def test_matchers_are_exact_tool_names(self):
        for matcher in ("Bash|PowerShell", "Edit|Write|Bash|PowerShell"):
            self.assertTrue(re.fullmatch(matcher, "PowerShell"))
            self.assertTrue(re.fullmatch(matcher, "Bash"))
            self.assertIsNone(re.fullmatch(matcher, "PowerShellFoo"))
            self.assertIsNone(re.fullmatch(matcher, "Read"))


# --- AC2/AC3: hooks accept the PowerShell tool -------------------------------------

def run_hook(script, payload, project):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR")}
    env["CLAUDE_PROJECT_DIR"] = project
    return subprocess.run([sys.executable, os.path.join(HOOKS_DIR, script)],
                          input=json.dumps(payload), capture_output=True, text=True,
                          env=env, cwd=project, timeout=20)


class SensitivePathPowerShellTest(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp(prefix="t266-")
        self.addCleanup(shutil.rmtree, self.project, True)
        os.makedirs(os.path.join(self.project, ".claude"))
        os.makedirs(os.path.join(self.project, "tasks"))
        shutil.copy(os.path.join(REPO_ROOT, ".claude", "sensitive-paths.txt"),
                    os.path.join(self.project, ".claude", "sensitive-paths.txt"))
        with open(os.path.join(self.project, "PROJECT_KANBAN.md"), "w") as f:
            f.write("### Todo\n")

    def call(self, tool_name, tool_input):
        return run_hook("pre_tool_sensitive_path.py",
                        {"tool_name": tool_name, "cwd": self.project, "tool_input": tool_input},
                        self.project)

    def verdict(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)["hookSpecificOutput"] if proc.stdout.strip() else None

    def test_powershell_reading_env_asks_like_bash(self):
        ps = self.verdict(self.call("PowerShell", {"command": "cat .env"}))
        bash = self.verdict(self.call("Bash", {"command": "cat .env"}))
        self.assertIsNotNone(ps, "PowerShell call touching .env got no decision")
        self.assertEqual(ps["permissionDecision"], "ask")
        self.assertEqual(ps["permissionDecision"], bash["permissionDecision"])
        self.assertEqual(ps["permissionDecisionReason"],
                         bash["permissionDecisionReason"].replace("Bash call", "PowerShell call"))

    def test_powershell_harmless_command_is_silent(self):
        self.assertIsNone(self.verdict(self.call("PowerShell", {"command": "Get-ChildItem README.md"})))

    def test_read_and_glob_still_exit_silently(self):
        for tool in ("Read", "Glob"):
            self.assertIsNone(self.verdict(self.call(tool, {"file_path": ".env", "pattern": ".env"})))

    def test_missing_command_fails_the_same_way_as_bash(self):
        ps = self.verdict(self.call("PowerShell", {}))
        bash = self.verdict(self.call("Bash", {}))
        self.assertEqual(ps["permissionDecision"], "ask")
        self.assertEqual(bash["permissionDecision"], "ask")
        self.assertIn("has no command string", ps["permissionDecisionReason"])
        self.assertIn("Bash call has no command string", bash["permissionDecisionReason"])


class MemoryHookPowerShellTest(unittest.TestCase):
    def call(self, tool_name, tool_input):
        return run_hook("post_bash_memory_update.py",
                        {"tool_name": tool_name, "tool_input": tool_input}, REPO_ROOT)

    def test_powershell_git_push_prompts_like_bash(self):
        ps = self.call("PowerShell", {"command": "git push origin feat/x"})
        bash = self.call("Bash", {"command": "git push origin feat/x"})
        self.assertEqual(ps.returncode, 0, ps.stderr)
        self.assertIn("memory update required", ps.stdout)
        self.assertEqual(ps.stdout, bash.stdout)

    def test_read_and_missing_command_stay_silent(self):
        for tool, tool_input in (("Read", {"file_path": "x"}), ("PowerShell", {}), ("Bash", {})):
            proc = self.call(tool, tool_input)
            self.assertEqual((proc.returncode, proc.stdout.strip()), (0, ""), tool)


# --- AC4/AC10: exec-form kit entries are recognised -----------------------------------

def exec_group(*args, command="py"):
    return {"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": command,
                                                       "args": list(args)}]}


class HookPathsTest(unittest.TestCase):
    def test_shell_form_keys_unchanged(self):
        for hook in all_hooks(load(SETTINGS)):
            group = {"hooks": [hook]}
            path = re.search(r"\.claude/hooks/\w+\.py", hook["command"]).group(0)
            self.assertEqual(merge_settings.hook_paths(group), [path])

    def test_exec_form_path_in_args_found(self):
        group = exec_group("-3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py")
        self.assertEqual(merge_settings.hook_paths(group), [".claude/hooks/x.py"])
        self.assertTrue(merge_settings.is_kit_group(group))
        self.assertEqual(merge_settings.group_key(group), frozenset([".claude/hooks/x.py"]))

    def test_exec_and_shell_form_share_a_key(self):
        shell = {"hooks": [{"type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/x.py'}]}
        self.assertEqual(merge_settings.group_key(shell),
                         merge_settings.group_key(exec_group("${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py",
                                                             command="python")))

    def test_bad_args_ignored_without_exception(self):
        for args in (None, "not-a-list", [1, None, {"a": 1}], 7):
            group = {"hooks": [{"type": "command", "command": "py", "args": args}]}
            self.assertEqual(merge_settings.hook_paths(group), [])
        group = {"hooks": [{"type": "command", "command": "py"}]}
        self.assertFalse(merge_settings.is_kit_group(group))

    def test_hook_path_regex_stops_at_whitespace_and_quotes(self):
        group = {"hooks": [{"type": "command",
                            "command": "python3 '.claude/hooks/a.py' --x \".claude/hooks/b.py\""}]}
        self.assertEqual(merge_settings.hook_paths(group), [".claude/hooks/a.py"])

    def test_negative_exec_form_outside_hooks_is_user_entry(self):
        group = exec_group("-3", "${CLAUDE_PROJECT_DIR}/scripts/mine.py")
        self.assertFalse(merge_settings.is_kit_group(group))
        merged = merge_settings.merge_event_groups([group], [])
        self.assertEqual(merged, [group])


class WiresInRepoHookTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="t266-wire-")
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, ".claude", "hooks"))
        open(os.path.join(self.root, ".claude", "hooks", "gate.py"), "w").close()

    def wire(self, group):
        with open(os.path.join(self.root, ".claude", "settings.json"), "w") as f:
            json.dump({"hooks": {"PreToolUse": [group]}}, f)
        return project_root.wires_in_repo_hook(self.root, "gate.py")

    def test_exec_form_project_entry_wires(self):
        self.assertTrue(self.wire(exec_group("-3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/gate.py")))

    def test_exec_form_plugin_entry_does_not_wire(self):
        self.assertFalse(self.wire(exec_group("-3", "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/gate.py")))

    def test_shell_form_unchanged(self):
        self.assertTrue(self.wire({"hooks": [{"type": "command",
                                              "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/gate.py'}]}))

    def test_bad_args_and_outside_path_do_not_wire(self):
        self.assertFalse(self.wire({"hooks": [{"type": "command", "command": "py", "args": "x"}]}))
        self.assertFalse(self.wire(exec_group("-3", "${CLAUDE_PROJECT_DIR}/scripts/gate.py")))


# --- AC5/AC6/AC7/AC8: the converter -------------------------------------------------

FORBIDDEN = ("python3", "sh -c", '"$CLAUDE_PROJECT_DIR"', "'")


def assert_exec_form(result, root_var, launcher, count=11):
    """SC3: every kit entry is exec form with the placeholder path in args, no shell text."""
    hooks = all_hooks(result)
    assert len(hooks) == count, len(hooks)
    lead = ["-3"] if launcher == "py" else []
    for hook in hooks:
        assert hook["command"] == launcher, hook
        assert hook["type"] == "command", hook
        assert hook["args"][:-1] == lead, hook
        assert re.fullmatch(r"\$\{%s\}/\.claude/hooks/\w+\.py" % root_var, hook["args"][-1]), hook
    for text in all_strings(result["hooks"]):
        assert "python3" not in text and "sh -c" not in text, text
    for hook in hooks:  # quotes: only the strings the harness executes, not description prose
        for text in [hook["command"]] + hook["args"]:
            for bad in FORBIDDEN:
                assert bad not in text, (bad, text)
            assert '"' not in text and "\\" not in text, text


class ConverterTest(unittest.TestCase):
    def setUp(self):
        self.wh = load_module("windows_hooks", CONVERTER)

    def test_repo_settings_to_py(self):
        src = load(SETTINGS)
        before = copy.deepcopy(src)
        out = self.wh.to_windows_settings(src, "py")
        self.assertEqual(src, before, "input mutated: the function must be pure")
        assert_exec_form(out, "CLAUDE_PROJECT_DIR", "py")
        first = out["hooks"]["PostToolUse"][0]["hooks"][0]
        self.assertEqual(first, {"type": "command", "command": "py",
                                 "args": ["-3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/post_write_register_task.py"]})

    def test_repo_settings_to_python(self):
        out = self.wh.to_windows_settings(load(SETTINGS), "python")
        assert_exec_form(out, "CLAUDE_PROJECT_DIR", "python")

    def test_plugin_root_converts(self):
        out = self.wh.to_windows_settings(load(PLUGIN_HOOKS), "py")
        assert_exec_form(out, "CLAUDE_PLUGIN_ROOT", "py")

    def test_order_matcher_description_and_other_keys_kept(self):
        src = load(SETTINGS)
        src["hooks"]["Stop"][0]["hooks"][0]["timeout"] = 30
        out = self.wh.to_windows_settings(src, "py")
        self.assertEqual(list(out), list(src))
        self.assertEqual(out["permissions"], src["permissions"])
        for event in src["hooks"]:
            self.assertEqual(len(out["hooks"][event]), len(src["hooks"][event]))
            for a, b in zip(src["hooks"][event], out["hooks"][event]):
                self.assertEqual({k: v for k, v in a.items() if k != "hooks"},
                                 {k: v for k, v in b.items() if k != "hooks"})
                self.assertEqual(merge_settings.hook_paths(a), merge_settings.hook_paths(b))
        self.assertEqual(out["hooks"]["Stop"][0]["hooks"][0]["timeout"], 30)

    def test_non_kit_entries_untouched(self):
        user = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/mine.py"}]}
        src = {"hooks": {"PreToolUse": [user]}, "env": {"A": "1"}}
        out = self.wh.to_windows_settings(src, "py")
        self.assertEqual(out, src)

    def test_unknown_launcher_raises(self):
        with self.assertRaises(ValueError):
            self.wh.to_windows_settings(load(SETTINGS), "python3")

    def test_idempotent(self):
        once = self.wh.to_windows_settings(load(SETTINGS), "py")
        self.assertEqual(self.wh.to_windows_settings(once, "py"), once)

    def test_no_literal_windows_path(self):
        out = json.dumps(self.wh.to_windows_settings(load(SETTINGS), "py"))
        self.assertNotRegex(out, r"[A-Za-z]:\\")


class RoundTripTest(unittest.TestCase):
    def setUp(self):
        self.wh = load_module("windows_hooks", CONVERTER)
        self.project = tempfile.mkdtemp(prefix="t266-rt-")
        self.addCleanup(shutil.rmtree, self.project, True)
        shutil.copytree(HOOKS_DIR, os.path.join(self.project, ".claude", "hooks"),
                        ignore=shutil.ignore_patterns("tests", "__pycache__"))
        self.target = os.path.join(self.project, ".claude", "settings.json")

    def merge(self):
        proc = subprocess.run([sys.executable, MERGE, SETTINGS, self.target, self.project],
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return load(self.target)

    def test_converted_entries_replaced_by_upstream_without_duplicates(self):
        converted = self.wh.to_windows_settings(load(SETTINGS), "py")
        user = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}
        converted["hooks"]["PreToolUse"].append(user)
        with open(self.target, "w") as f:
            json.dump(converted, f)
        merged = self.merge()
        upstream = load(SETTINGS)
        for event, groups in upstream["hooks"].items():
            kit = [g for g in merged["hooks"][event] if merge_settings.is_kit_group(g)]
            self.assertEqual(kit, groups, event)
        self.assertIn(user, merged["hooks"]["PreToolUse"])
        self.assertEqual(merged["permissions"], upstream["permissions"])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="t266-cli-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.out = os.path.join(self.dir, "out.json")

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, CONVERTER, SETTINGS, self.out, *extra],
                              capture_output=True, text=True, timeout=20)

    def test_cli_writes_exec_form(self):
        proc = self.run_cli("--launcher", "python")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        assert_exec_form(load(self.out), "CLAUDE_PROJECT_DIR", "python")

    def test_unknown_launcher_exits_2_and_writes_nothing(self):
        proc = self.run_cli("--launcher", "python3")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(os.path.exists(self.out))

    def test_missing_input_exits_2(self):
        proc = subprocess.run([sys.executable, CONVERTER, os.path.join(self.dir, "nope.json"),
                               self.out, "--launcher", "py"], capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(os.path.exists(self.out))


# --- SC5: mutation control ------------------------------------------------------------

class MutationControlTest(unittest.TestCase):
    ANCHOR = "    return converted\n"

    def test_identity_conversion_turns_exec_form_check_red(self):
        with open(CONVERTER, encoding="utf-8") as f:
            source = f.read()
        self.assertIn(self.ANCHOR, source, "mutation anchor drifted — update the control")
        mutant = load_module("windows_hooks_mutant", CONVERTER,
                             source.replace(self.ANCHOR, "    return hook\n"))
        with self.assertRaises(AssertionError):
            assert_exec_form(mutant.to_windows_settings(load(SETTINGS), "py"),
                             "CLAUDE_PROJECT_DIR", "py")


if __name__ == "__main__":
    unittest.main()
