"""T240 — the repo is `thunderkds/easy-kit`; the old name `personal-agentic-claude` stays only in history.

  AC2 — no live file names the old repo, outside history paths and the allow list below (D3).
        History stays as written: GitHub redirects the old URLs (D1, proved on the real rename).
  AC3 — the installer's own URLs name `easy-kit`; a fork made before the rename, still named
        `personal-agentic-claude`, keeps working through `GITHUB_USERNAME` (Edge Case).

Supersedes T107's guard (`grep -c personal-agentic-claude setup.sh update.sh README.md` → 9): that was a
one-off grep in `tasks/TASK_REVIEW_T107.md`, never a test, and it held the slug only until the repo
itself was renamed — which is this task.

Run with: python3 -m pytest tests/test_repo_name.py -q
"""
import pytest
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD = "personal-agentic-claude"
NEW_URL = "https://github.com/thunderkds/easy-kit.git"
NEW_INSTALL_LINE = "curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh"

# History: written once, never rewritten (D3).
HISTORY_PREFIXES = (
    "tasks/", "memory/", "docs/archive/", "docs/brainstorming/", "docs/prd/", "docs/adr/",
    "docs/ddr/", "reports/", "PROJECT_KANBAN", "BRAINSTORMING_LOG.md",
    "docs/memory-usage-finding-2026-08-07.md",
)

# D4: the Vercel project keeps its own name until the user renames it, so its URL is still live.
VERCEL_HOST = OLD + ".vercel.app"

# (path, text on the line) -> reason. A line in `path` that holds the text may name the old repo.
ALLOWED = {
    ("setup.sh", "${_user}/" + OLD + ".git"):
        "fork fallback: a fork made before the rename still carries the old name",
    ("lib/harness.ps1", "$user/" + OLD + ".git"):
        "fork fallback in the PowerShell port of kit_repo_url (T268), as in setup.sh",
    ("scripts/memory_usage_report.py", OLD):
        "the local checkout folder's name in recorded event traces, not the GitHub repo",
    (".claude/hooks/tests/test_memory_usage_report.py", OLD):
        "trace fixture: a local checkout path",
    (".claude/hooks/tests/test_merge_gate_evidence.py", OLD):
        "trace records copied byte-for-byte from memory/event-trace/T043.jsonl",
    ("tests/test_repo_name.py", OLD):
        "this test names the old repo to look for it",
}


def live_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout
    for name in out.decode().split("\0"):
        if name and not name.startswith(HISTORY_PREFIXES) and (REPO / name).is_file():
            yield name


def stray_lines(path, text):
    """Lines of `text` (file `path`) that name the old repo and no rule allows."""
    bad = []
    for n, line in enumerate(text.splitlines(), 1):
        rest = line.replace(VERCEL_HOST, "")
        if OLD not in rest:
            continue
        if any(path == p and needle in rest for p, needle in ALLOWED):
            continue
        bad.append(f"{path}:{n}: {line.strip()[:160]}")
    return bad


# --- AC2: the sweep ---------------------------------------------------------------------------

def test_no_live_file_names_the_old_repo():
    bad = []
    for name in live_files():
        try:
            text = (REPO / name).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        bad.extend(stray_lines(name, text))
    assert not bad, "old repo name in live files (rename it, or allow it with a reason):\n" + "\n".join(bad)


def test_the_sweep_catches_the_old_name():
    """Anti-vacuity: the forms the live files held before T240 are flagged."""
    for path, line in (
        ("README.md", "curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"),
        ("site/index.html", '<a href="https://github.com/thunderkds/personal-agentic-claude">GitHub</a>'),
        ("setup.sh", '  log_error "  curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"'),
        ("site/index.html", "https://personal-agentic-claude.vercel.app/ and github.com/thunderkds/personal-agentic-claude"),
    ):
        assert stray_lines(path, line), line
    assert not stray_lines("README.md", "[site](https://personal-agentic-claude.vercel.app/)")


def test_every_allow_entry_still_matches_a_line():
    """A stale allow entry would hide a future stray line; each one must still be needed."""
    for (path, needle), reason in ALLOWED.items():
        if path == "tests/test_repo_name.py":
            continue
        text = (REPO / path).read_text(encoding="utf-8")
        assert any(needle in line.replace(VERCEL_HOST, "") for line in text.splitlines()), (path, reason)


# --- AC3: the installer's URLs ----------------------------------------------------------------

def sourced(snippet, env_extra=None, path_prefix=None):
    """Run `snippet` after loading setup.sh's functions (define-only, no main)."""
    env = {k: v for k, v in os.environ.items() if k not in ("SUPERVISOR_REPO", "GITHUB_USERNAME")}
    env.update(SETUP_SH_DEFINE_ONLY="1", SETUP_SH_DIR=str(REPO))
    env.update(env_extra or {})
    if path_prefix:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    script = f'. "{REPO}/setup.sh"\n{snippet}\n'
    return subprocess.run(["sh", "-c", script], capture_output=True, text=True, env=env, cwd=REPO)


def fake_git(tmp_path, ls_remote_rc):
    """A `git` whose `ls-remote` exits `ls_remote_rc` and logs its URL; nothing else is called."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "git.log"
    (bin_dir / "git").write_text(f'#!/bin/sh\necho "$*" >> "{log}"\nexit {ls_remote_rc}\n')
    (bin_dir / "git").chmod(0o755)
    return bin_dir, log


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via sourced]")
def test_default_repo_is_easy_kit(tmp_path):
    bin_dir, log = fake_git(tmp_path, 1)
    r = sourced('resolve_repo_url >/dev/null; printf "%s" "$SUPERVISOR_REPO"', path_prefix=bin_dir)
    assert r.returncode == 0, r.stderr
    assert r.stdout == NEW_URL
    assert not log.exists(), "the canonical repo needs no probe"


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via sourced]")
def test_fork_named_easy_kit_is_used(tmp_path):
    bin_dir, log = fake_git(tmp_path, 0)
    r = sourced('resolve_repo_url >/dev/null; printf "%s" "$SUPERVISOR_REPO"',
                {"GITHUB_USERNAME": "someone"}, bin_dir)
    assert r.stdout == "https://github.com/someone/easy-kit.git", r.stderr
    assert "ls-remote https://github.com/someone/easy-kit.git" in log.read_text()


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via sourced]")
def test_fork_made_before_the_rename_keeps_working(tmp_path):
    bin_dir, _ = fake_git(tmp_path, 2)
    r = sourced('resolve_repo_url >/dev/null; printf "%s" "$SUPERVISOR_REPO"',
                {"GITHUB_USERNAME": "someone"}, bin_dir)
    assert r.stdout == f"https://github.com/someone/{OLD}.git", r.stderr


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [via sourced]")
def test_supervisor_repo_wins(tmp_path):
    bin_dir, log = fake_git(tmp_path, 1)
    r = sourced('resolve_repo_url >/dev/null; printf "%s" "$SUPERVISOR_REPO"',
                {"SUPERVISOR_REPO": "file:///x/kit", "GITHUB_USERNAME": "someone"}, bin_dir)
    assert r.stdout == "file:///x/kit", r.stderr
    assert not log.exists()


@pytest.mark.posix_only("runs a shell script through sh/bash; shell suites are not run on Windows [sh]")
def test_error_messages_print_the_new_install_line(tmp_path):
    r = subprocess.run(["sh", str(REPO / "setup.sh"), "--harness", "codex"], capture_output=True, text=True)
    assert r.returncode == 1 and NEW_INSTALL_LINE in r.stderr, r.stderr
    lone = tmp_path / "update.sh"
    lone.write_text((REPO / "update.sh").read_text())
    r = subprocess.run(["sh", str(lone)], capture_output=True, text=True)
    assert r.returncode == 1 and NEW_INSTALL_LINE in r.stderr, r.stderr
