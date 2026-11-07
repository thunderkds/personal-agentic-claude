"""T272 - setup.ps1 checks the fetched kit before it changes the project (Docker pwsh).

When the fetched kit has no lib/windows_hooks.py or no lib/merge-settings.py (both are read from the
clone by Install-HarnessSettings, neither is in the MANIFEST), setup.ps1 must stop right after the
fetch with exit 1 and leave the project tree byte-identical, on every action. Reuses T268's Docker
harness (tests/test_setup_ps1_pwsh.py): same pinned image, same mounts, no network. It skips, with
the reason, when docker, the pinned image or the host loader is absent.

Run with: python3 -m pytest tests/test_setup_ps1_preflight_pwsh.py -q
"""
import hashlib
import os
import shutil
import subprocess

import pytest

import test_setup_ps1_pwsh as base

pytestmark = pytest.mark.posix_only("runs Linux PowerShell in Docker with the host's /usr loader")

needs_docker = base.needs_docker
# The preflight block in setup.ps1 is fenced by these two marker lines (mutation control).
PREFLIGHT_BEGIN = "# T272 preflight begin"
PREFLIGHT_END = "# T272 preflight end"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _kit_without(work, name, rel):
    """A clone of kit A with `rel` deleted and committed."""
    bad = os.path.join(work, name)
    subprocess.run(["git", "clone", "-q", os.path.join(work, "kit"), bad], check=True)
    os.remove(os.path.join(bad, rel))
    git = ["git", "-C", bad, "-c", "user.name=t272", "-c", "user.email=t272@example.invalid"]
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", "without " + rel], check=True)
    return "/work/" + name


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    if base.SKIP:
        pytest.skip(base.SKIP)
    w = str(tmp_path_factory.mktemp("t272"))
    base._make_shims(w)
    base._make_kit(w)
    os.makedirs(os.path.join(w, "home"))
    return w


@pytest.fixture(scope="module")
def kits(work):
    return {"hooks": _kit_without(work, "kit-nohooks", "lib/windows_hooks.py"),
            "merge": _kit_without(work, "kit-nomerge", "lib/merge-settings.py")}


@pytest.fixture(scope="module")
def installed(work):
    """A project installed by setup.ps1 from the full kit (it has a lock). Tests copy it."""
    repo, cdir = base._new_repo(work, "t272-installed")
    r = base._install(work, cdir)
    assert r.returncode == 0, r.stdout + r.stderr
    return repo


def _existing_project(work, name):
    """A project that owns .claude/hooks, CLAUDE.md and .claude/settings.json (no lock)."""
    repo, cdir = base._new_repo(work, name)
    for rel, text in ((".claude/hooks/own.py", "print('mine')\n"), ("CLAUDE.md", "my own rules\n"),
                      (".claude/settings.json", '{"permissions": {"allow": ["Bash(ls)"]}}\n'),
                      ("scripts/verify_trace.py", "# mine\n")):
        os.makedirs(os.path.dirname(os.path.join(repo, rel)), exist_ok=True)
        with open(os.path.join(repo, rel), "w", encoding="utf-8") as f:
            f.write(text)
    return repo, cdir


def _copy(work, installed, name):
    repo = os.path.join(work, name)
    shutil.copytree(installed, repo, symlinks=True)
    return repo, f"/work/{name}"


def _tree(repo):
    """rel path -> sha256 / 'dir' / 'link:<target>' for the whole project, .git/info/exclude included."""
    found = {}
    for top, dirs, files in os.walk(repo):
        rel_top = os.path.relpath(top, repo)
        rel_top = "" if rel_top == "." else rel_top + "/"
        if rel_top == ".git/":
            dirs[:] = [d for d in dirs if d == "info"]
            files[:] = []
        elif rel_top.startswith(".git/") and rel_top != ".git/info/":
            dirs[:] = []
            continue
        for name in dirs + files:
            rel = rel_top + name
            full = os.path.join(repo, rel)
            if rel == ".git":
                continue
            if os.path.islink(full):
                found[rel] = "link:" + os.readlink(full)
            elif os.path.isdir(full):
                found[rel] = "dir"
            else:
                with open(full, "rb") as f:
                    found[rel] = hashlib.sha256(f.read()).hexdigest()
    return found


def _run(work, cdir, kit, script="setup.ps1", extra="-Yes", installer="/work/kit"):
    """Run an installer script with a private TMPDIR, then list that TMPDIR (the temp clone)."""
    tmp = "/work/tmp-" + os.path.basename(cdir)
    os.makedirs(work + tmp[len("/work"):], exist_ok=True)
    cmd = (f"$env:TMPDIR='{tmp}'; Set-Location '{cdir}'; & {installer}/{script} {extra}; $c = $LASTEXITCODE; "
           f"Write-Host ('LEFTOVER ' + @(Get-ChildItem -LiteralPath '{tmp}' -Force).Count); exit $c")
    return base._pwsh(work, cmd, repo=kit)


def _assert_stopped(r, repo, before, missing):
    out = r.stdout + r.stderr
    assert r.returncode == 1, out
    errors = [l for l in out.splitlines() if "[error]" in l]
    assert any(missing in l for l in errors), out
    assert any("Windows" in l for l in errors), out
    assert _tree(repo) == before, "the project tree changed"
    assert "LEFTOVER 0" in r.stdout, "the temp clone was not removed:\n" + out


@needs_docker
def test_sc1_a_kit_without_windows_hooks_stops_an_install_with_nothing_changed(work, kits):
    repo, cdir = _existing_project(work, "t272-sc1")
    before = _tree(repo)
    r = _run(work, cdir, kits["hooks"])
    _assert_stopped(r, repo, before, "lib/windows_hooks.py")
    assert not [p for p in before if ".bak-" in p] and not os.path.exists(os.path.join(repo, ".claude", "harness-lock.json"))


@needs_docker
def test_sc2_a_kit_without_merge_settings_stops_an_install_with_nothing_changed(work, kits):
    repo, cdir = _existing_project(work, "t272-sc2")
    before = _tree(repo)
    r = _run(work, cdir, kits["merge"])
    _assert_stopped(r, repo, before, "lib/merge-settings.py")


@needs_docker
@pytest.mark.parametrize("script,extra", [("setup.ps1", "-Yes"), ("setup.ps1", ""), ("update.ps1", "-Yes")])
def test_sc3_reinstall_and_update_stop_with_nothing_changed(work, kits, installed, script, extra):
    """-Yes on an installed project is Reinstall; update.ps1 is Update; with no -Yes the preflight
    still runs before the menu (AC 5), so a non-interactive run exits 1 instead of cancelling with 0."""
    name = "t272-sc3-" + script[:-4] + ("-yes" if extra else "-bare")
    repo, cdir = _copy(work, installed, name)
    before = _tree(repo)
    r = _run(work, cdir, kits["hooks"], script=script, extra=extra)
    _assert_stopped(r, repo, before, "lib/windows_hooks.py")


@needs_docker
def test_a_full_kit_still_installs(work):
    repo, cdir = _existing_project(work, "t272-full")
    r = _run(work, cdir, "/work/kit")
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.path.isfile(os.path.join(repo, ".claude", "harness-lock.json"))


@needs_docker
def test_sc4_mutation_control_without_the_preflight_scenario_1_goes_red(work, kits):
    """Remove the fenced preflight from a copy of setup.ps1: Install-HarnessSettings then finds the
    missing file only after the project was written, so the tree-unchanged check must fail."""
    mut = os.path.join(work, "mut")
    os.makedirs(os.path.join(mut, "lib"))
    for rel in ("setup.ps1", "update.ps1", "lib/harness.ps1", "lib/harness-update.ps1"):
        shutil.copy2(os.path.join(work, "kit", rel), os.path.join(mut, rel))
    target = os.path.join(mut, "setup.ps1")
    lines = _read(target).splitlines(keepends=True)
    begin = [i for i, l in enumerate(lines) if l.strip() == PREFLIGHT_BEGIN]
    end = [i for i, l in enumerate(lines) if l.strip() == PREFLIGHT_END]
    assert len(begin) == 1 and len(end) == 1 and begin[0] < end[0], "preflight markers missing in setup.ps1"
    with open(target, "w", encoding="utf-8", newline="") as f:
        f.write("".join(lines[:begin[0]] + lines[end[0] + 1:]))
    repo, cdir = _existing_project(work, "t272-mut")
    before = _tree(repo)
    r = _run(work, cdir, kits["hooks"], installer="/work/mut")
    assert _tree(repo) != before, "a removed preflight went unnoticed:\n" + r.stdout + r.stderr
