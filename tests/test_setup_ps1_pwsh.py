"""T268 — run setup.ps1 in PowerShell 7 on Linux, through Docker (Success Criteria 1-5, AC 2, 10, 13).

The official PowerShell image has no git and no Python. The host's own `git` and `python3` are run
inside the container through the host's dynamic loader, from `/usr` mounted read-only at `/host/usr`
(small wrapper scripts in a temp dir). The kit is a fresh git repo built in a temp dir from this
checkout's working tree, so uncommitted work is what gets installed. Mounts: that temp dir
(read-write) and the host `/usr` (read-only). No network, no privileged flag, the host user's UID.

This test never pulls an image. It skips, with the reason, when docker, the pinned image or the
host loader is absent. Pull the image by hand once: `docker pull mcr.microsoft.com/powershell`.

Linux PowerShell cannot prove junctions, `core.symlinks=false`, CRLF checkouts or Windows paths:
the Windows CI smoke (tests/windows/smoke-install.ps1 in .github/workflows/windows.yml) is the
real check for those.

Run with: python3 -m pytest tests/test_setup_ps1_pwsh.py -q
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

pytestmark = pytest.mark.posix_only("runs Linux PowerShell in Docker with the host's /usr loader; "
                                    "Windows runs tests/windows/smoke-install.ps1 instead")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Pinned: mcr.microsoft.com/powershell:latest as pulled on 2026-11-06 (PowerShell 7.4.2, Ubuntu 22.04).
IMAGE = "mcr.microsoft.com/powershell@sha256:810c4f1e0c9d23022c3ec18c50a6205ee4b60766f1739d329b2948df1fd7d5b0"
LOADER = "/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"
LIBDIR = "/usr/lib/x86_64-linux-gnu"
PROBE = "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"


def _skip_reason():
    if not shutil.which("docker"):
        return "docker is not on PATH"
    try:
        r = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"docker is not usable: {exc}"
    if r.returncode != 0:
        return f"image {IMAGE} is absent (pull it by hand: docker pull mcr.microsoft.com/powershell)"
    if not os.path.exists(LOADER):
        return f"host loader {LOADER} is absent"
    git = shutil.which("git")
    py = os.path.realpath(sys.executable)
    if not git or not os.path.realpath(git).startswith("/usr/") or not py.startswith("/usr/") \
            or not os.path.realpath(sys.base_prefix).startswith("/usr"):
        return "host git or python is not under /usr, so it cannot be mounted into the container"
    return None


SKIP = _skip_reason()
needs_docker = pytest.mark.skipif(SKIP is not None, reason=SKIP or "")


def _wrapper(target, argv0=None, env=""):
    a0 = f"--argv0 {argv0} " if argv0 else ""
    return f'#!/bin/sh\n{env}exec /host{LOADER} --library-path /host{LIBDIR} {a0}/host{target} "$@"\n'


def _write(path, text, mode=0o755):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, mode)


def _make_shims(work):
    """bin-full: git, py (needs -3), a python3 trap; bin-python: git, python; bin-nopy: git only;
    bin-stub: git and a `python` that fails the probe like the Microsoft Store stub."""
    git = os.path.realpath(shutil.which("git"))
    py = os.path.realpath(sys.executable)
    home = os.path.realpath(sys.base_prefix)
    core = os.path.join(work, "git-core")
    os.makedirs(core)
    exec_path = subprocess.run(["git", "--exec-path"], capture_output=True, text=True, check=True).stdout.strip()
    for name in os.listdir(exec_path):
        full = os.path.join(exec_path, name)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            _write(os.path.join(core, name), _wrapper(os.path.realpath(full), argv0=name))
    python = _wrapper(py, env=f"PYTHONHOME=/host{home} ")
    for d in ("bin-full", "bin-python", "bin-nopy", "bin-stub"):
        os.makedirs(os.path.join(work, d))
        _write(os.path.join(work, d, "git"), _wrapper(git))
    _write(os.path.join(work, "bin-full", "py"),
           '#!/bin/sh\n[ "$1" = "-3" ] || exit 9\nshift\nexec /work/bin-python/python "$@"\n')
    _write(os.path.join(work, "bin-full", "python3"), "#!/bin/sh\ntouch /work/python3-was-called\nexit 1\n")
    _write(os.path.join(work, "bin-python", "python"), python)
    _write(os.path.join(work, "bin-stub", "python"), "#!/bin/sh\necho 'Python was not found' >&2\nexit 9009\n")


def _make_kit(work):
    """A git repo holding this checkout's working tree (tracked + untracked, not ignored)."""
    kit = os.path.join(work, "kit")
    os.makedirs(kit)
    listed = subprocess.run(["git", "-C", ROOT, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            capture_output=True, check=True).stdout.decode().split("\0")
    for rel in filter(None, listed):
        src = os.path.join(ROOT, rel)
        if not os.path.lexists(src):
            continue  # deleted in the working tree
        dst = os.path.join(kit, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.islink(src):
            os.symlink(os.readlink(src), dst)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
    git = ["git", "-C", kit, "-c", "user.name=t268", "-c", "user.email=t268@example.invalid"]
    subprocess.run(["git", "init", "-q", kit], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", "kit"], check=True)
    return kit


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    if SKIP:
        pytest.skip(SKIP)
    w = str(tmp_path_factory.mktemp("t268"))
    _make_shims(w)
    _make_kit(w)
    os.makedirs(os.path.join(w, "home"))
    return w


def _pwsh(work, script, path="bin-full", timeout=300, repo="/work/kit"):
    """Run a PowerShell command line in the container; `/work` is `work`."""
    cmd = ["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
           "-v", "/usr:/host/usr:ro", "-v", f"{work}:/work",
           "-e", "HOME=/work/home", "-e", "GIT_EXEC_PATH=/work/git-core",
           "-e", "GIT_TEMPLATE_DIR=/host/usr/share/git-core/templates",
           "-e", f"PATH=/work/{path}:/opt/microsoft/powershell/7", "-e", f"SUPERVISOR_REPO={repo}",
           "-e", "GIT_AUTHOR_NAME=t268", "-e", "GIT_AUTHOR_EMAIL=t268@example.invalid",
           "-e", "GIT_COMMITTER_NAME=t268", "-e", "GIT_COMMITTER_EMAIL=t268@example.invalid",
           IMAGE, "/opt/microsoft/powershell/7/pwsh", "-NoProfile", "-NonInteractive", "-Command", script]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)


def _new_repo(work, name):
    repo = os.path.join(work, name)
    subprocess.run(["git", "init", "-q", repo], check=True)
    return repo, f"/work/{name}"


def _install(work, cdir, path="bin-full", extra="-Yes", repo="/work/kit"):
    return _pwsh(work, f"Set-Location '{cdir}'; & /work/kit/setup.ps1 {extra}; exit $LASTEXITCODE", path, repo=repo)


def _files_block(lock):
    with open(lock, encoding="utf-8") as f:
        return json.load(f)["files"]


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _manifest_paths():
    paths, excl = [], []
    with open(os.path.join(ROOT, "MANIFEST"), encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            (excl if s.startswith("!") else paths).append(s.split()[0].lstrip("!"))
    return paths, excl


def _backups(repo):
    found = []
    for base, dirs, files in os.walk(repo):
        if ".git" in dirs:
            dirs.remove(".git")
        found += [os.path.join(base, n) for n in dirs + files if ".bak-" in n]
    return sorted(found)


@needs_docker
def test_the_windows_ci_smoke_passes_in_linux_pwsh(work):
    """The very script CI runs on windows-latest: install, second run, edited file, third run."""
    r = _pwsh(work, "& /work/kit/tests/windows/smoke-install.ps1; exit $LASTEXITCODE")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SMOKE PASS" in r.stdout
    assert not os.path.exists(os.path.join(work, "python3-was-called"))


@needs_docker
def test_install_matches_the_manifest_and_setup_sh(work):
    """SC 1 and AC 10: every MANIFEST path, no `!` path, exec-form hooks, and the lock that
    lib/harness-update.sh reads holds the same entries as a lock written by setup.sh itself."""
    repo, cdir = _new_repo(work, "fresh")
    r = _install(work, cdir)
    assert r.returncode == 0, r.stdout + r.stderr
    paths, excl = _manifest_paths()
    for p in paths:
        assert os.path.exists(os.path.join(repo, p)), p
    for p in excl:
        assert not os.path.exists(os.path.join(repo, p)), p
    for canon in ("skills", "agents"):
        assert os.path.isdir(os.path.join(repo, ".claude", canon, "")), canon
    with open(os.path.join(repo, ".claude", "settings.json"), encoding="utf-8") as f:
        settings = json.load(f)
    commands = [h for groups in settings["hooks"].values() for g in groups for h in g["hooks"]]
    assert commands and all("python3" not in json.dumps(h) for h in commands)
    assert all(h["command"] == "py" and h["args"][0] == "-3" for h in commands if ".claude/hooks/" in json.dumps(h))
    assert not os.path.exists(os.path.join(work, "python3-was-called"))

    lock = os.path.join(repo, ".claude", "harness-lock.json")
    files = _files_block(lock)
    assert files and all(_sha(os.path.join(repo, k)) == v for k, v in files.items())
    # The loader lib/harness-update.sh uses (extract_lock_pairs, lookup_lock_field).
    loader = subprocess.run(
        ["sh", "-c", 'SETUP_SH_DEFINE_ONLY=1 SETUP_SH_DIR="$1" . "$1/setup.sh"; extract_lock_pairs "$2"; '
         'printf "kit_commit=%s\\nsource=%s\\n" "$(lookup_lock_field "$2" kit_commit)" '
         '"$(lookup_lock_field "$2" claude_md_source)"', "-", ROOT, lock],
        capture_output=True, text=True, check=True).stdout.splitlines()
    pairs = dict(l.split("\t") for l in loader if "\t" in l)
    assert pairs == files
    kit_head = subprocess.run(["git", "-C", os.path.join(work, "kit"), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    assert f"kit_commit={kit_head}" in loader and "source=CLAUDE.md" in loader

    # Parity: setup.sh, run with no terminal, on a twin repo from the same kit.
    twin = os.path.join(work, "twin")
    subprocess.run(["git", "init", "-q", twin], check=True)
    env = dict(os.environ, SUPERVISOR_REPO=os.path.join(work, "kit"), PATH="/usr/bin:/bin")
    sh = subprocess.run(["sh", os.path.join(work, "kit", "setup.sh")], cwd=twin, env=env, capture_output=True,
                        text=True, stdin=subprocess.DEVNULL, start_new_session=True, timeout=300)
    assert sh.returncode == 0, sh.stdout + sh.stderr
    assert _files_block(os.path.join(twin, ".claude", "harness-lock.json")) == files
    for rel in ("memory/MEMORY.md", "memory/decisions.md", "memory/glossary.md", "memory/learnings.md",
                "memory/learning-records/.gitkeep", "CLAUDE.md"):
        assert _sha(os.path.join(repo, rel)) == _sha(os.path.join(twin, rel)), rel


@needs_docker
def test_edited_file_is_backed_up_and_a_rerun_is_idempotent(work):
    """SC 2, SC 3, AC 6, AC 13."""
    repo, cdir = _new_repo(work, "edited")
    assert _install(work, cdir).returncode == 0
    lock = os.path.join(repo, ".claude", "harness-lock.json")
    first = _files_block(lock)
    settings_path = os.path.join(repo, ".claude", "settings.json")
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)
    user_hook = {"hooks": [{"type": "command", "command": "echo user-own-hook"}]}
    settings["hooks"].setdefault("Stop", []).append(user_hook)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    count = sum(len(g) for g in settings["hooks"].values())
    r = _install(work, cdir)
    assert r.returncode == 0, r.stdout + r.stderr
    assert _backups(repo) == [] and _files_block(lock) == first
    with open(settings_path, encoding="utf-8") as f:
        after = json.load(f)
    assert sum(len(g) for g in after["hooks"].values()) == count  # review P3: no entry lost or added
    assert user_hook in after["hooks"]["Stop"]
    agents = os.path.join(repo, "AGENTS.md")
    with open(agents, "a", encoding="utf-8") as f:
        f.write("\nmy own line\n")
    r = _install(work, cdir)
    assert r.returncode == 0, r.stdout + r.stderr
    backups = _backups(repo)
    assert len(backups) == 1 and os.path.basename(backups[0]).startswith("AGENTS.md.bak-"), backups
    assert "[warn]" in r.stdout + r.stderr and "AGENTS.md.bak-" in r.stdout + r.stderr
    with open(backups[0], encoding="utf-8") as f:
        assert f.read().endswith("my own line\n")
    assert _sha(agents) == _sha(os.path.join(work, "kit", "AGENTS.md"))
    assert _install(work, cdir).returncode == 0
    assert _backups(repo) == backups and _files_block(lock) == first
    with open(os.path.join(repo, ".git", "info", "exclude"), encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if l.startswith("/.claude/")]
    assert sorted(lines) == ["/.claude/agents", "/.claude/skills"]


@needs_docker
def test_python_is_found_when_py_and_python3_are_absent(work):
    """SC 4: PATH holds git and `python` only."""
    repo, cdir = _new_repo(work, "pythononly")
    r = _install(work, cdir, path="bin-python")
    assert r.returncode == 0, r.stdout + r.stderr
    with open(os.path.join(repo, ".claude", "settings.json"), encoding="utf-8") as f:
        text = f.read()
    assert '"command": "python"' in text and "python3" not in text and '"-3"' not in text


@needs_docker
@pytest.mark.parametrize("path", ["bin-nopy", "bin-stub"])
def test_no_usable_python_stops_with_nothing_written(work, path):
    """SC 5 and AC 2: no Python, or a `python` that fails the probe (the Store stub)."""
    repo, cdir = _new_repo(work, "nopy-" + path)
    before = sorted(os.listdir(repo))
    r = _install(work, cdir, path=path)
    assert r.returncode == 1, r.stdout + r.stderr
    errors = [l for l in (r.stdout + r.stderr).splitlines() if "[error]" in l]
    assert len(errors) == 1 and "Python" in errors[0], r.stdout + r.stderr
    assert sorted(os.listdir(repo)) == before


@needs_docker
def test_outside_a_git_repo_stops_with_nothing_written(work):
    """AC 2: not a git work tree."""
    plain = os.path.join(work, "plain")
    os.makedirs(plain)
    r = _install(work, "/work/plain")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[error]" in r.stdout + r.stderr and os.listdir(plain) == []


@needs_docker
def test_existing_install_without_consent_cancels(work):
    """AC 12: an existing install, no terminal and no -Yes: Reinstall is never chosen; nothing written."""
    repo, cdir = _new_repo(work, "nocons")
    assert _install(work, cdir).returncode == 0
    with open(os.path.join(repo, "AGENTS.md"), "a", encoding="utf-8") as f:
        f.write("edit\n")
    r = _install(work, cdir, extra="")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "update.ps1" in r.stdout + r.stderr or "Update" in r.stdout + r.stderr
    assert _backups(repo) == []


@needs_docker
def test_a_manifest_path_outside_the_project_stops_before_any_write(work):
    """A fetched MANIFEST line `../escape` would copy outside the project: the run stops first."""
    bad = os.path.join(work, "badkit")
    subprocess.run(["git", "clone", "-q", os.path.join(work, "kit"), bad], check=True)
    with open(os.path.join(bad, "MANIFEST"), "a", encoding="utf-8") as f:
        f.write("../escape\n")
    os.makedirs(os.path.join(bad, "..", "escape-src"), exist_ok=True)
    git = ["git", "-C", bad, "-c", "user.name=t268", "-c", "user.email=t268@example.invalid"]
    subprocess.run(git + ["commit", "-qam", "bad"], check=True)
    repo, cdir = _new_repo(work, "escape-target")
    before = sorted(os.listdir(repo))
    r = _install(work, cdir, repo="/work/badkit")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "MANIFEST path '../escape'" in r.stderr
    assert sorted(os.listdir(repo)) == before and not os.path.exists(os.path.join(work, "escape"))


@needs_docker
def test_an_exclusion_outside_the_project_stops_before_any_write(work):
    """Review P2: `!.claude/hooks/../../../victim` must not reach the hold/remove code."""
    bad = os.path.join(work, "badexcl")
    subprocess.run(["git", "clone", "-q", os.path.join(work, "kit"), bad], check=True)
    with open(os.path.join(bad, "MANIFEST"), "a", encoding="utf-8") as f:
        f.write("!.claude/hooks/../../../victim\n")
    git = ["git", "-C", bad, "-c", "user.name=t268", "-c", "user.email=t268@example.invalid"]
    subprocess.run(git + ["commit", "-qam", "bad"], check=True)
    repo, cdir = _new_repo(work, "excl-target")
    os.makedirs(os.path.join(repo, "victim"))
    with open(os.path.join(repo, "victim", "keep.txt"), "w") as f:
        f.write("mine")
    before = sorted(os.listdir(repo))
    r = _install(work, cdir, repo="/work/badexcl")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "'.claude/hooks/../../../victim'" in r.stderr
    assert sorted(os.listdir(repo)) == before and os.path.isfile(os.path.join(repo, "victim", "keep.txt"))


HOLD_SCRIPT = r"""
. /work/kit/lib/harness.ps1
$root = '/tmp/hold-' + '{case}'
$src = "$root/kit"; $dst = "$root/proj/hooks"
foreach ($d in @("$src", "$dst/t1", "$dst/t2")) { [void][IO.Directory]::CreateDirectory($d) }
[IO.File]::WriteAllText("$src/a.py", 'kit')
[IO.File]::WriteAllText("$dst/t1/own1.txt", 'mine1')
[IO.File]::WriteAllText("$dst/t2/own2.txt", 'mine2')
$script:moves = 0
function Move-HarnessItem([string]$From, [string]$To) {
    $script:moves += 1
    if ('{case}' -eq 'restore' -and $To.StartsWith("$dst/")) { throw 'locked by antivirus' }
    if ('{case}' -eq 'hold' -and $From.StartsWith("$dst/") -and $script:moves -eq 2) { throw 'locked by antivirus' }
    if ([IO.Directory]::Exists($From)) { [IO.Directory]::Move($From, $To) } else { [IO.File]::Move($From, $To) }
}
try { Install-HarnessExcluding $src $dst 'hooks' @('t1', 't2') } catch { Write-Host "caught: $_" }
Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object { Write-Host "FILE $($_.FullName)" }
"""


@needs_docker
@pytest.mark.parametrize("case", ["restore", "hold"])
def test_held_excluded_content_survives_a_failed_move(work, case):
    """Review P1: when a move of the project's own excluded content fails, it is never deleted."""
    r = _pwsh(work, HOLD_SCRIPT.replace("{case}", case))
    out = r.stdout + r.stderr
    files = [l.split(" ", 1)[1] for l in r.stdout.splitlines() if l.startswith("FILE ")]
    for own in ("own1.txt", "own2.txt"):
        assert any(f.endswith("/" + own) for f in files), f"{own} was deleted:\n{out}"
    if case == "restore":
        assert "[error]" in out and "/held" in out, out
