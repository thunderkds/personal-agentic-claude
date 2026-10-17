#!/usr/bin/env python3
"""T146 — an Edit, Write or Bash call touching a sensitive path asks a human first.

Every case drives `pre_tool_sensitive_path.py` through its real protocol: a JSON
payload on stdin, the decision read back from stdout. Each test builds its own
project in a temp dir (`CLAUDE_PROJECT_DIR`), so nothing reads the live board,
the live `tasks/` directory or the live state file.

The two mutation controls (SC8) are run here as well as by the Supervisor: each
copies the hook into a temp dir with one rule reverted and asserts the matching
success criterion goes RED, so this file cannot pass against a hook that does
nothing.

Run with: python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(HOOKS_DIR, "pre_tool_sensitive_path.py")
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
SHIPPED_PATTERNS = os.path.join(REPO_ROOT, ".claude", "sensitive-paths.txt")

PREDICTING_GUIDE = """# TASK_GUIDE — T901: fixture

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `infra/main.tf` | edit |
| `./config/prod.yml` | edit |

## Files Must NOT Touch
"""


def run_hook(payload, project, env_extra=None, hook=HOOK, raw_stdin=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_ACTIVE_TASK", "CLAUDE_PROJECT_DIR")}
    env["CLAUDE_PROJECT_DIR"] = project
    env.update(env_extra or {})
    stdin = raw_stdin if raw_stdin is not None else json.dumps(payload)
    proc = subprocess.run([sys.executable, hook], input=stdin, capture_output=True,
                          text=True, env=env, cwd=project, timeout=20)
    return proc


def decision(proc):
    if not proc.stdout.strip():
        return None
    return json.loads(proc.stdout)["hookSpecificOutput"]


class SensitivePathHookTest(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp(prefix="t146-")
        os.makedirs(os.path.join(self.project, ".claude"))
        os.makedirs(os.path.join(self.project, "tasks"))
        shutil.copy(SHIPPED_PATTERNS, os.path.join(self.project, ".claude", "sensitive-paths.txt"))

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def write(self, file_path, **kw):
        return run_hook({"tool_name": "Write", "cwd": self.project,
                         "tool_input": {"file_path": file_path, "content": "x"}},
                        self.project, **kw)

    def edit(self, file_path, **kw):
        return run_hook({"tool_name": "Edit", "cwd": self.project,
                         "tool_input": {"file_path": file_path, "old_string": "a",
                                        "new_string": "b"}},
                        self.project, **kw)

    def bash(self, command, **kw):
        return run_hook({"tool_name": "Bash", "cwd": self.project,
                         "tool_input": {"command": command}}, self.project, **kw)

    def assert_ask(self, proc, *needles):
        out = decision(proc)
        self.assertIsNotNone(out, f"expected ask, got silence; stderr={proc.stderr!r}")
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "ask")
        for needle in needles:
            self.assertIn(needle, out["permissionDecisionReason"])
        self.assertEqual(proc.returncode, 0)

    def assert_silent(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "", f"expected no decision, got {proc.stdout!r}")

    # --- AC1: the shipped list --------------------------------------------

    def test_ac1_shipped_list_carries_the_default_patterns(self):
        with open(SHIPPED_PATTERNS) as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        self.assertEqual(lines, [
            ".env", ".env.*", "!.env.example", "**/secrets/**", "**/*.pem", "**/*.key",
            "**/prod*.{yml,yaml,json,tf}", "infra/**", "terraform/**",
        ])

    # --- SC1 / SC2 / AC2: Edit and Write ----------------------------------

    def test_sc1_write_env_asks_and_names_it(self):
        self.assert_ask(self.write(".env"), ".env", "pattern `.env`")

    def test_sc2_write_env_example_is_silent(self):
        self.assert_silent(self.write(".env.example"))

    def test_write_absolute_path_is_normalised_against_project_dir(self):
        self.assert_ask(self.write(os.path.join(self.project, ".env.local")), "`.env.*`")

    def test_edit_each_default_pattern_asks(self):
        for path in ("config/secrets/db.txt", "certs/server.pem", "a/b/id.key",
                     "deploy/prod.yaml", "prod-eu.tf", "infra/main.tf", "terraform/vpc.tf"):
            with self.subTest(path=path):
                self.assert_ask(self.edit(path), path)

    def test_ordinary_path_is_silent(self):
        for path in ("README.md", "src/app.py", "docs/infra.md", "envoy.yaml"):
            with self.subTest(path=path):
                self.assert_silent(self.edit(path))

    def test_symlink_to_sensitive_path_asks(self):
        os.makedirs(os.path.join(self.project, "infra"))
        target = os.path.join(self.project, "infra", "main.tf")
        open(target, "w").close()
        os.symlink(target, os.path.join(self.project, "harmless.tf"))
        self.assert_ask(self.edit("harmless.tf"), "infra/**")

    def test_windows_separators_in_pattern_file(self):
        with open(os.path.join(self.project, ".claude", "sensitive-paths.txt"), "w") as f:
            f.write("deploy\\keys\\**\n")
        self.assert_ask(self.write("deploy/keys/a.txt"), "deploy\\keys\\**")

    # --- SC3 / SC4 / SC5 / AC3: Bash via shell_data ------------------------

    def test_sc3_quoted_data_is_silent(self):
        self.assert_silent(self.bash('echo "edit .env later"'))

    def test_sc4_executable_quoted_span_asks(self):
        self.assert_ask(self.bash('bash -c "echo x > .env"'), ".env")

    def test_sc5_heredoc_body_mention_is_silent(self):
        self.assert_silent(self.bash("cat <<EOF > notes.md\nremember .env\nEOF"))

    def test_bash_redirect_into_env_asks(self):
        self.assert_ask(self.bash("echo KEY=1 >.env"), ".env")

    def test_bash_read_of_env_asks_by_design(self):
        self.assert_ask(self.bash("grep KEY .env"), ".env")

    def test_bash_glob_is_expanded(self):
        open(os.path.join(self.project, ".env.prod"), "w").close()
        self.assert_ask(self.bash("cat .env*"), ".env.prod")

    def test_bash_ordinary_command_is_silent(self):
        self.assert_silent(self.bash("python3 -m pytest tests/ -q && git status"))

    # --- SC6 / AC4: predicted paths ----------------------------------------

    def _guide(self):
        with open(os.path.join(self.project, "tasks", "TASK_GUIDE_T901.md"), "w") as f:
            f.write(PREDICTING_GUIDE)

    def test_sc6_predicted_path_is_silent(self):
        self._guide()
        self.assert_silent(self.edit("infra/main.tf", env_extra={"CLAUDE_ACTIVE_TASK": "T901"}))

    def test_predicted_path_with_dot_slash_prefix(self):
        self._guide()
        self.assert_silent(self.write("config/prod.yml", env_extra={"CLAUDE_ACTIVE_TASK": "T901"}))

    def test_predicted_is_exact_not_prefix(self):
        self._guide()
        self.assert_ask(self.edit("infra/other.tf", env_extra={"CLAUDE_ACTIVE_TASK": "T901"}),
                        "T901")

    def test_no_active_task_asks_even_if_some_guide_predicts(self):
        self._guide()
        self.assert_ask(self.edit("infra/main.tf"), "no active task")

    def test_bash_asks_when_any_sensitive_token_is_unpredicted(self):
        self._guide()
        self.assert_ask(self.bash("cp infra/main.tf .env", env_extra={"CLAUDE_ACTIVE_TASK": "T901"}),
                        ".env")

    # --- SC7 / AC5: fail toward the human -----------------------------------

    def test_sc7_missing_pattern_file_asks(self):
        os.remove(os.path.join(self.project, ".claude", "sensitive-paths.txt"))
        self.assert_ask(self.write("README.md"), "unreadable")

    def test_malformed_stdin_asks(self):
        self.assert_ask(run_hook(None, self.project, raw_stdin="not json{"), "Malformed")

    def test_write_without_file_path_asks(self):
        self.assert_ask(run_hook({"tool_name": "Write", "tool_input": {}}, self.project))

    def test_import_failure_asks(self):
        sandbox = tempfile.mkdtemp(prefix="t146-noimport-")
        try:
            hook_copy = os.path.join(sandbox, "pre_tool_sensitive_path.py")
            shutil.copy(HOOK, hook_copy)  # no lib/ beside it
            self.assert_ask(self.write("README.md", hook=hook_copy), "unavailable")
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    # --- AC6: reaches consumer projects --------------------------------------

    def test_ac6_manifest_ships_hook_and_list(self):
        with open(os.path.join(REPO_ROOT, "MANIFEST")) as f:
            entries = [l.split()[0] for l in f if l.strip() and not l.startswith(("#", "!"))]
        self.assertIn(".claude/hooks", entries)  # carries pre_tool_sensitive_path.py
        self.assertIn(".claude/sensitive-paths.txt", entries)

    def test_ac6_settings_merge_wires_the_hook_into_existing_settings(self):
        hooks = os.path.join(self.project, ".claude", "hooks")
        shutil.copytree(HOOKS_DIR, hooks, ignore=shutil.ignore_patterns("tests", "__pycache__"))
        settings = os.path.join(self.project, ".claude", "settings.json")
        user_entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}
        with open(settings, "w") as f:
            json.dump({"hooks": {"PreToolUse": [user_entry]}}, f)
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "lib", "merge-settings.py"),
             os.path.join(REPO_ROOT, ".claude", "settings.json"), settings, self.project],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(settings) as f:
            pre = json.load(f)["hooks"]["PreToolUse"]
        self.assertIn(user_entry, pre)
        ours = [g for g in pre if any("pre_tool_sensitive_path.py" in h["command"] for h in g["hooks"])]
        self.assertEqual(len(ours), 1)
        self.assertEqual(ours[0]["matcher"], "Edit|Write|Bash")

    # --- SC8: mutation controls ---------------------------------------------

    def _mutant(self, old, new):
        with open(HOOK) as f:
            source = f.read()
        self.assertIn(old, source, "mutation anchor drifted — update the control")
        sandbox = tempfile.mkdtemp(prefix="t146-mutant-")
        self.addCleanup(shutil.rmtree, sandbox, True)
        shutil.copytree(os.path.join(HOOKS_DIR, "lib"), os.path.join(sandbox, "lib"))
        path = os.path.join(sandbox, "pre_tool_sensitive_path.py")
        with open(path, "w") as f:
            f.write(source.replace(old, new))
        return path

    def test_sc8a_dropping_the_quoted_span_keep_rule_turns_sc4_red(self):
        # Strip every quoted span, as the naive T099 round did.
        mutant = self._mutant(
            "text = strip_quoted_spans(strip_heredoc_bodies(command))",
            "text = re.sub(r\"\\\"[^\\\"]*\\\"|'[^']*'\", ' ', strip_heredoc_bodies(command))",
        )
        proc = self.bash('bash -c "echo x > .env"', hook=mutant)
        self.assertEqual(proc.stdout.strip(), "", "mutant should wave SC4 through (RED)")

    def test_sc8b_failure_path_allowing_turns_sc7_red(self):
        mutant = self._mutant(
            "        ask(f\"Sensitive-path list unreadable",
            "        sys.exit(0)\n        ask(f\"Sensitive-path list unreadable",
        )
        os.remove(os.path.join(self.project, ".claude", "sensitive-paths.txt"))
        proc = self.write(".env", hook=mutant)
        self.assertEqual(proc.stdout.strip(), "", "mutant should allow SC7 (RED)")


if __name__ == "__main__":
    unittest.main()
