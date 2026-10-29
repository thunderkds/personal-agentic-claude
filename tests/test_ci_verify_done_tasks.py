"""T143 - scripts/ci_verify_done_tasks.py: CI re-runs the Verification Command of
every task a PR moves to Done. Each test builds a real two-commit git repo."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "ci_verify_done_tasks.py")

TODO = "- [ ] **T900** - the task under test\n"
DONE = "- [x] **T900** - the task under test\n"
PLACEHOLDER = (
    "# the single command (or short sequence) that proves this task works\n"
    "[e.g. pytest tests/test_T001.py -q   |   npm test -- T001]\n"
)


def kanban(*rows):
    return "# Board\n\n### Done\n" + "".join(rows)


def guide(block, fence="bash"):
    body = f"```{fence}\n{block}\n```\n" if block is not None else "No command here.\n"
    return (
        "# TASK_GUIDE - T900\n\n## Evaluation\n\n"
        f"### Verification Command (exact, runnable)\n\n{body}\n### Evidence\n\nx\n"
    )


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True)


class Fixture:
    """Commit A (board_a), then commit B (board_b + guide)."""

    def __init__(self, board_a, board_b, guide_text, review_text=None):
        self.dir = tempfile.TemporaryDirectory()
        self.root = self.dir.name
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "t@example.com")
        git(self.root, "config", "user.name", "t")
        os.makedirs(os.path.join(self.root, "tasks"))
        self._write("PROJECT_KANBAN.md", board_a)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "A")
        self.base = self._rev()
        self._write("PROJECT_KANBAN.md", board_b)
        if guide_text is not None:
            self._write("tasks/TASK_GUIDE_T900.md", guide_text)
        if review_text is not None:
            self._write("tasks/TASK_REVIEW_T900.md", review_text)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "B")

    def _write(self, rel, text):
        with open(os.path.join(self.root, rel), "w", encoding="utf-8") as f:
            f.write(text)

    def _rev(self):
        return subprocess.run(["git", "-C", self.root, "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()

    def run(self):
        return subprocess.run(
            [sys.executable, SCRIPT, "--base", self.base, "--root", self.root],
            capture_output=True, text=True)

    def close(self):
        self.dir.cleanup()


class CiVerifyDoneTasksTest(unittest.TestCase):
    def fixture(self, block, **kw):
        fx = Fixture(kanban(TODO), kanban(DONE), guide(block, **kw))
        self.addCleanup(fx.close)
        return fx

    # SC1
    def test_passing_block_prints_pass_and_exits_zero(self):
        result = self.fixture("true").run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("T900: PASS", result.stdout)

    # SC2
    def test_failing_block_prints_fail_and_exits_one(self):
        result = self.fixture("false").run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)

    def test_block_runs_from_repo_root_and_command_is_printed_first(self):
        result = self.fixture("test -f PROJECT_KANBAN.md").run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertLess(result.stdout.index("test -f PROJECT_KANBAN.md"),
                        result.stdout.index("T900: PASS"))

    def test_block_runs_as_written_without_errexit(self):
        # `bash -c` as written: a failing middle line does not abort the block.
        result = self.fixture("false\ntrue").run()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_verification_command_falls_back_to_review_file(self):
        vacated = guide(None).replace("No command here.", "> **Moved.** See the review file.")
        review = "## Verification Command\n\n```bash\nfalse\n```\n"
        fx = Fixture(kanban(TODO), kanban(DONE), vacated, review)
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL (exit 1)", result.stdout)

    # SC3
    def test_skip_with_reason_is_skipped_by_name_with_reason(self):
        result = self.fixture("# ci: skip — needs /verify\nfalse").run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("T900: SKIP (needs /verify)", result.stdout)

    # SC4
    def test_skip_without_reason_fails(self):
        result = self.fixture("# ci: skip —").run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)

    def test_skip_with_template_reason_text_fails(self):
        result = self.fixture("# ci: skip — <reason>").run()
        self.assertEqual(result.returncode, 1, result.stdout)

    # SC5
    def test_missing_verification_command_fails_closed(self):
        fx = Fixture(kanban(TODO), kanban(DONE),
                     "# TASK_GUIDE - T900\n\n## Requirement\n\nx\n")
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)

    def test_missing_guide_file_fails_closed(self):
        fx = Fixture(kanban(TODO), kanban(DONE), None)
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)

    def test_section_without_a_fenced_block_fails_closed(self):
        result = self.fixture(None).run()
        self.assertEqual(result.returncode, 1, result.stdout)

    def test_empty_block_fails_closed(self):
        result = self.fixture("").run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)

    def test_template_placeholder_block_fails_closed(self):
        result = self.fixture(PLACEHOLDER.rstrip("\n")).run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)

    # SC6
    def test_bold_cross_reference_in_prose_is_not_selected(self):
        row_a = "- [x] **T900** - done, see also **T901** which is not mine\n"
        fx = Fixture(kanban("- [ ] **T900** - x\n"), kanban(row_a), guide("true"))
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("T900: PASS", result.stdout)
        self.assertNotIn("T901", result.stdout.replace("tasks moved to Done: T900", ""))

    def test_cross_reference_does_not_select_a_task_that_was_already_done(self):
        before = kanban("- [x] **T901** - already done\n", TODO)
        after = kanban("- [x] **T901** - already done\n",
                       "- [x] **T900** - moved, mentions **T901**\n")
        fx = Fixture(before, after, guide("true"))
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("tasks moved to Done: T900\n", result.stdout)

    # edge cases
    def test_closed_rows_are_not_done(self):
        fx = Fixture(kanban(TODO), kanban("- [~] **T900** - closed, will not do\n"),
                     guide("false"))
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("no tasks moved to Done", result.stdout)

    def test_pr_with_no_done_move_exits_zero(self):
        fx = Fixture(kanban(TODO), kanban(TODO + "- [ ] **T901** - new\n"), None)
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 0)
        self.assertIn("no tasks moved to Done", result.stdout)

    def test_task_already_done_at_base_is_not_rerun(self):
        fx = Fixture(kanban(DONE), kanban(DONE + "- [ ] **T901** - new\n"), guide("false"))
        self.addCleanup(fx.close)
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("no tasks moved to Done", result.stdout)

    def test_failing_task_does_not_hide_the_others(self):
        board_b = kanban(DONE, "- [x] **T901** - second\n")
        fx = Fixture(kanban(TODO, "- [ ] **T901** - second\n"), board_b, guide("false"))
        self.addCleanup(fx.close)
        fx._write("tasks/TASK_GUIDE_T901.md", guide("true").replace("T900", "T901"))
        git(fx.root, "add", "-A")
        git(fx.root, "commit", "-q", "-m", "guide")
        result = fx.run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("T900: FAIL", result.stdout)
        self.assertIn("T901: PASS", result.stdout)

    def test_base_that_advanced_on_main_does_not_select_main_only_moves(self):
        # BASE has moved on with T901 Done; the PR branch left before that.
        fx = Fixture(kanban(TODO, "- [ ] **T901** - other\n"),
                     kanban(DONE, "- [ ] **T901** - other\n"), guide("true"))
        self.addCleanup(fx.close)
        branch_head = fx._rev()
        git(fx.root, "checkout", "-q", "-b", "main-advanced", fx.base)
        fx._write("PROJECT_KANBAN.md", kanban(TODO, "- [x] **T901** - other\n"))
        git(fx.root, "commit", "-qam", "main moves T901")
        advanced = fx._rev()
        git(fx.root, "checkout", "-q", "--detach", branch_head)
        result = subprocess.run(
            [sys.executable, SCRIPT, "--base", advanced, "--head", branch_head,
             "--root", fx.root], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("tasks moved to Done: T900\n", result.stdout)

    def test_unknown_base_ref_exits_two_and_runs_nothing(self):
        fx = self.fixture("true")
        result = subprocess.run(
            [sys.executable, SCRIPT, "--base", "no-such-ref", "--root", fx.root],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertNotIn("PASS", result.stdout)

    # AC5 + AC6: template note and workflow wiring
    def test_template_documents_the_skip_convention(self):
        with open(os.path.join(ROOT, "templates", "TASK_GUIDE_template.md"), encoding="utf-8") as f:
            self.assertIn("# ci: skip", f.read())

    def test_ci_step_runs_on_pull_request_only_and_uses_no_secrets(self):
        with open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("scripts/ci_verify_done_tasks.py", text)
        self.assertNotIn("secrets.", text)
        step = text[text.index("- name: Re-run Verification Command"):]
        step = step.split("\n      - name:", 1)[0]
        self.assertIn("if: github.event_name == 'pull_request'", step)
        self.assertIn("fetch-depth: 0", text)
        # F1: the job runs guide-authored commands, so its token is read-only.
        self.assertRegex(text, r"(?m)^permissions:\n  contents: read$")
        self.assertNotRegex(text, r"(?m)^\s*[a-z-]+:\s*write\s*$")


if __name__ == "__main__":
    unittest.main()
