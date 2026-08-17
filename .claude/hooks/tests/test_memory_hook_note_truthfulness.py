#!/usr/bin/env python3
"""T073 — the post-`git` memory-update prompt must tell the truth about which memory
files are tracked, so a Supervisor following it commits the cold-tier pass instead of
leaving it uncommitted.

`post_bash_memory_update.py`'s trailing NOTE claimed `memory/* is gitignored except
MEMORY.md` and told the Supervisor `Do NOT commit`. Both are false: only
`memory/event-trace/` is ignored (`.gitignore:53`); the cold-tier files
(decisions.md/glossary.md/learnings.md) are tracked and must be committed. T046 shipped
with its whole memory pass lost in a forgotten stash because of exactly this instruction.

AC1-4: prose assertions against the hook's actual prompt constant (imported, not
re-declared).
AC6:   ground-truth cross-check — `git check-ignore` against `memory/decisions.md`
       (not ignored) and `memory/event-trace/x.jsonl` (ignored) — so the NOTE is
       checked against reality, not against itself.

Run with: python3 -m pytest .claude/hooks/tests/test_memory_hook_note_truthfulness.py -v
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "post_bash_memory_update.py"

# post_bash_memory_update.py calls main() unconditionally at module scope (no
# `if __name__ == "__main__":` guard); main() reads stdin as JSON and, on any
# failure (including pytest's captured, unreadable stdin), does `sys.exit(0)`.
# That is existing hook behaviour (AC7 forbids touching it), so a plain
# `import` raises SystemExit mid-exec and Python evicts the partial module
# from sys.modules, losing the constant. Register the module object in
# sys.modules ourselves *before* exec_module runs, so the reference we hold
# is fully populated (MEMORY_UPDATE_PROMPT is defined before main() is
# called) regardless of the later SystemExit. Import it once — this IS the
# module object, not a copy (see the importlib-identity gotcha in learnings.md).
_spec = importlib.util.spec_from_file_location("post_bash_memory_update", HOOK_PATH)
post_bash_memory_update = importlib.util.module_from_spec(_spec)
sys.modules["post_bash_memory_update"] = post_bash_memory_update
try:
    _spec.loader.exec_module(post_bash_memory_update)
except SystemExit:
    pass

MEMORY_UPDATE_PROMPT = post_bash_memory_update.MEMORY_UPDATE_PROMPT

ROOT = Path(__file__).resolve().parents[3]
HOOK_FILE = HOOK_PATH

# Retired tokens: the false premises the old NOTE stated. AC4 is a file-wide
# negative scoped to .claude/hooks/*.py (not repo-wide — dated records legitimately
# quote the old text elsewhere).
RETIRED_TOKENS = [
    "gitignored except MEMORY.md",
    "writes are local-only",
    "Do NOT commit",
]


def test_ac1_note_no_longer_claims_gitignored_except_memory_md_or_do_not_commit():
    for token in RETIRED_TOKENS:
        assert token not in MEMORY_UPDATE_PROMPT, (
            f"retired token {token!r} still present in MEMORY_UPDATE_PROMPT"
        )


def test_ac2_replacement_note_states_positively_that_cold_tier_must_be_committed():
    assert "git-tracked" in MEMORY_UPDATE_PROMPT
    assert "Commit this pass" in MEMORY_UPDATE_PROMPT


def test_ac3_replacement_note_names_event_trace_as_the_only_local_only_path():
    assert "memory/event-trace/" in MEMORY_UPDATE_PROMPT
    assert "Only memory/event-trace/ is local-only" in MEMORY_UPDATE_PROMPT


def test_ac4_no_retired_token_appears_anywhere_in_claude_hooks_py_files():
    for py_file in (ROOT / ".claude" / "hooks").glob("*.py"):
        text = py_file.read_text()
        for token in RETIRED_TOKENS:
            assert token not in text, f"{token!r} still present in {py_file}"


def test_ac6_ground_truth_decisions_md_is_not_git_ignored():
    # git check-ignore exit codes are INVERTED from intuition:
    # 0 = the path IS ignored, 1 = the path is NOT ignored.
    # decisions.md is tracked, so we assert the non-zero (not-ignored) exit code.
    result = subprocess.run(
        ["git", "check-ignore", "memory/decisions.md"],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode != 0, (
        "memory/decisions.md unexpectedly reported as git-ignored (exit 0); "
        "it is a tracked cold-tier file"
    )


COLD_TIER = ("memory/decisions.md", "memory/glossary.md", "memory/learnings.md")


def test_ac6_ground_truth_cold_tier_files_are_actually_tracked():
    """The load-bearing half of AC6, added at Stage 4 review.

    `git check-ignore` is NOT sufficient on its own: git never reports a *tracked*
    path as ignored, so the sibling assertion above holds no matter what `.gitignore`
    says. The T073 implementer proved this — adding `memory/decisions.md` to
    `.gitignore` left that test green (SC6 did not reproduce RED).

    Tracked-ness is what the NOTE actually claims, and it is what can genuinely
    regress: untrack a cold file and this fails, which is the state that would make
    the NOTE a lie again.
    """
    for rel in COLD_TIER:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=ROOT, capture_output=True,
        )
        assert result.returncode == 0, (
            f"{rel} is NOT git-tracked, so the hook's NOTE telling the Supervisor to "
            f"commit the cold-tier pass would be false. Either restore tracking or "
            f"correct the NOTE — do not weaken this assertion."
        )


def test_ac6_ground_truth_event_trace_is_not_tracked():
    """The mirror of the above: the sole local-only path must stay untracked.

    Without this, `memory/event-trace/` could be committed and the NOTE's 'only
    event-trace is local-only' clause would silently become wrong in the other
    direction.
    """
    result = subprocess.run(
        ["git", "ls-files", "memory/event-trace/"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.stdout.strip() == "", (
        f"memory/event-trace/ has tracked files, contradicting the NOTE's claim that "
        f"it is the sole local-only path:\n{result.stdout}"
    )


def test_ac6_ground_truth_event_trace_path_is_git_ignored():
    # git check-ignore: 0 = ignored, 1 = not ignored (inverted from intuition).
    # event-trace/ is the sole local-only exception, so we assert exit code 0.
    # Works on a path that does not exist on disk — no fixture file needed.
    result = subprocess.run(
        ["git", "check-ignore", "memory/event-trace/x.jsonl"],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode == 0, (
        "memory/event-trace/x.jsonl unexpectedly reported as NOT git-ignored (exit 1); "
        "it should be the sole local-only exception"
    )


def test_ac7_hook_logic_unchanged_apart_from_the_note_constant():
    text = HOOK_FILE.read_text()
    # Trigger condition, patterns, and main() structure preserved.
    assert 'r"\\bgit\\s+push\\b"' in text
    assert 'r"\\bgit\\s+merge\\b"' in text
    assert 'r"\\bgit\\s+pull\\b"' in text
    for step in [
        "1. Run: git diff HEAD~1 --name-only",
        "2. Grep memory/decisions.md, memory/glossary.md, memory/learnings.md",
        "3. Update matched entries in place",
        "4. Append any new decisions or learnings from this session",
        "5. Summarize new/changed entries as one-liners in memory/MEMORY.md",
    ]:
        assert step in text
    assert "Routing: architectural/infra decisions → decisions.md" in text
    assert "def main():" in text
