"""T271 — run update.ps1 (the Update action of setup.ps1) in PowerShell 7 on Linux, through Docker.

Success Criteria 1-7 and AC 1, 3, 6-12. Reuses T268's Docker harness (tests/test_setup_ps1_pwsh.py):
the same pinned image, the same two mounts (the temp work dir read-write, the host `/usr` read-only),
no network, no privileged flag, the host user's UID. It never pulls an image and skips with the
reason when docker, the pinned image or the host loader is absent.

Kit A is this checkout's working tree as a git repo (`/work/kit`). Kit B (`/work/kitb`) is a clone
with a second commit: it edits AGENTS.md (X1) and one docs/claude-md file (X2), adds
skills/zz-t271-new/SKILL.md (Y) and deletes two templates files (Z1, Z2). The project is installed
from kit A with setup.ps1, then the user edits X2, X3 (a file kit B leaves alone) and Z2, adds a
file of their own under skills/ and a Stop hook of their own; then update.ps1 runs against kit B.

Linux PowerShell cannot prove junctions, `core.symlinks=false`, CRLF or PowerShell 5.1: the
Windows CI smoke (tests/windows/smoke-update.ps1) is the check for those.

Run with: python3 -m pytest tests/test_update_ps1_pwsh.py -q
"""
import json
import os
import shlex
import shutil
import subprocess

import pytest

import test_setup_ps1_pwsh as base

pytestmark = pytest.mark.posix_only("runs Linux PowerShell in Docker with the host's /usr loader; "
                                    "Windows runs tests/windows/smoke-update.ps1 instead")

needs_docker = base.needs_docker
ROOT = base.ROOT
NEW_SKILL = "skills/zz-t271-new/SKILL.md"
OWN_FILE = "skills/zz-my-own/SKILL.md"
USER_HOOK = {"hooks": [{"type": "command", "command": "echo user-own-hook"}]}
# The one line Install-HarnessUpdateFile uses to put the kit's copy in place (mutation control).
REPLACE_LINE = "    [IO.File]::Copy($Src, $Dst, $true)"


def _git(repo, *args):
    cmd = ["git", "-C", repo, "-c", "user.name=t271", "-c", "user.email=t271@example.invalid", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def _append(path, text):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _picks(kit):
    docs = sorted(n for n in os.listdir(os.path.join(kit, "docs/claude-md"))
                  if os.path.isfile(os.path.join(kit, "docs/claude-md", n)))
    tmpl = sorted(n for n in os.listdir(os.path.join(kit, "templates"))
                  if os.path.isfile(os.path.join(kit, "templates", n)))
    return {"X1": "AGENTS.md", "X2": "docs/claude-md/" + docs[0], "X3": "docs/claude-md/" + docs[1],
            "Z1": "templates/" + tmpl[0], "Z2": "templates/" + tmpl[1], "Y": NEW_SKILL}


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    if base.SKIP:
        pytest.skip(base.SKIP)
    w = str(tmp_path_factory.mktemp("t271"))
    base._make_shims(w)
    base._make_kit(w)
    os.makedirs(os.path.join(w, "home"))
    return w


@pytest.fixture(scope="module")
def kit_b(work):
    """Kit B: a second commit on a clone of kit A. Returns the picked paths."""
    b = os.path.join(work, "kitb")
    subprocess.run(["git", "clone", "-q", os.path.join(work, "kit"), b], check=True)
    pick = _picks(b)
    _append(os.path.join(b, pick["X1"]), "\nT271 kit change\n")
    _append(os.path.join(b, pick["X2"]), "\nT271 kit change\n")
    os.makedirs(os.path.dirname(os.path.join(b, NEW_SKILL)))
    with open(os.path.join(b, NEW_SKILL), "w", encoding="utf-8") as f:
        f.write("---\nname: zz-t271-new\ndescription: added by kit B\n---\n")
    os.remove(os.path.join(b, pick["Z1"]))
    os.remove(os.path.join(b, pick["Z2"]))
    _git(b, "add", "-A")
    _git(b, "commit", "-qm", "kit B")
    pick["A"] = _git(os.path.join(work, "kit"), "rev-parse", "--short", "HEAD")
    pick["B"] = _git(b, "rev-parse", "--short", "HEAD")
    return pick


def _user_edits(repo, pick):
    for key in ("X2", "X3", "Z2"):
        _append(os.path.join(repo, pick[key]), "\nmy own edit\n")
    os.makedirs(os.path.dirname(os.path.join(repo, OWN_FILE)))
    with open(os.path.join(repo, OWN_FILE), "w", encoding="utf-8") as f:
        f.write("mine\n")
    settings_path = os.path.join(repo, ".claude", "settings.json")
    settings = json.loads(_read(settings_path))
    settings["hooks"].setdefault("Stop", []).append(USER_HOOK)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


@pytest.fixture(scope="module")
def installed(work, kit_b):
    """A project installed by setup.ps1 from kit A, then edited by the user. Tests copy it."""
    repo, cdir = base._new_repo(work, "base")
    r = base._install(work, cdir)
    assert r.returncode == 0, r.stdout + r.stderr
    _user_edits(repo, kit_b)
    return repo


def _copy(work, installed, name):
    repo = os.path.join(work, name)
    shutil.copytree(installed, repo, symlinks=True)
    return repo, f"/work/{name}"


def _update(work, cdir, extra="-Yes", repo="/work/kitb", installer="/work/kit"):
    return base._pwsh(work, f"Set-Location '{cdir}'; & {installer}/update.ps1 {extra}; exit $LASTEXITCODE",
                      repo=repo)


def _lock(repo):
    return json.loads(_read(os.path.join(repo, ".claude", "harness-lock.json")))


def _tree(repo):
    """rel path -> sha256 / 'dir' / 'link:<target>', without .git and the update log."""
    found = {}
    for top, dirs, files in os.walk(repo):
        rel_top = os.path.relpath(top, repo)
        rel_top = "" if rel_top == "." else rel_top + "/"
        if rel_top == ".git/":
            dirs[:] = []
            continue
        for name in dirs + files:
            rel = rel_top + name
            full = os.path.join(repo, rel)
            if rel in (".git", ".claude/update-log.md"):
                continue
            if os.path.islink(full):
                found[rel] = "link:" + os.readlink(full)
            elif os.path.isdir(full):
                found[rel] = "dir"
            else:
                found[rel] = base._sha(full)
    return found


def _hooks(repo):
    return json.loads(_read(os.path.join(repo, ".claude", "settings.json")))["hooks"]


def sc1_problems(work, repo, pick):
    """Success Criterion 1: X1 replaced, Y added, Z1 removed, lock lists X1 and Y, not Z1."""
    kb = os.path.join(work, "kitb")
    found = []
    if base._sha(os.path.join(repo, pick["X1"])) != base._sha(os.path.join(kb, pick["X1"])):
        found.append("X1 was not replaced with kit B's copy")
    y = os.path.join(repo, pick["Y"])
    if not os.path.isfile(y) or base._sha(y) != base._sha(os.path.join(kb, pick["Y"])):
        found.append("Y was not added")
    if os.path.exists(os.path.join(repo, pick["Z1"])):
        found.append("Z1 was not removed")
    files = _lock(repo)["files"]
    if files.get(pick["X1"]) != base._sha(os.path.join(kb, pick["X1"])):
        found.append("the lock does not hold X1's new hash")
    if pick["Y"] not in files:
        found.append("the lock does not list Y")
    if pick["Z1"] in files:
        found.append("the lock still lists Z1")
    if _lock(repo).get("kit_commit") != pick["B"]:
        found.append("the lock does not record kit B's commit")
    return found


@pytest.fixture(scope="module")
def updated(work, kit_b, installed):
    """The main scenario: update.ps1 -Yes from kit A to kit B."""
    repo, cdir = _copy(work, installed, "upd")
    hooks_before = _hooks(repo)
    r = _update(work, cdir)
    return repo, cdir, r, hooks_before


@needs_docker
def test_sc1_untouched_replaced_new_added_unshipped_removed(work, kit_b, updated):
    repo, _, r, _ = updated
    assert sc1_problems(work, repo, kit_b) == [], r.stdout + r.stderr
    assert os.path.isfile(os.path.join(repo, OWN_FILE)), "the user's own file under skills/ was removed"
    assert not base._backups(repo), "Update made a .bak- backup with no overwrite chosen"


@needs_docker
def test_sc2_edited_and_changed_upstream_is_kept_with_a_kit_new_copy(work, kit_b, updated, installed):
    repo, _, r, _ = updated
    out = r.stdout + r.stderr
    assert r.returncode == 2, out  # an edited file left to merge by hand, as update.sh's no-terminal run
    x2 = os.path.join(repo, kit_b["X2"])
    assert _read(x2).endswith("my own edit\n"), "the user's X2 was overwritten"
    assert base._sha(x2 + ".kit-new") == base._sha(os.path.join(work, "kitb", kit_b["X2"]))
    assert kit_b["X2"] + ".kit-new" in out
    assert _lock(repo)["files"][kit_b["X2"]] == _lock(installed)["files"][kit_b["X2"]]
    x3 = os.path.join(repo, kit_b["X3"])
    assert _read(x3).endswith("my own edit\n") and not os.path.exists(x3 + ".kit-new")


@needs_docker
def test_sc3_edited_file_the_kit_stopped_shipping_is_kept_and_named(work, kit_b, updated):
    repo, _, r, _ = updated
    z2 = os.path.join(repo, kit_b["Z2"])
    assert os.path.isfile(z2) and _read(z2).endswith("my own edit\n")
    assert kit_b["Z2"] in r.stdout + r.stderr
    assert kit_b["Z2"] in _lock(repo)["files"]


@needs_docker
def test_sc4_settings_stay_in_exec_form_with_the_user_hook(work, kit_b, updated):
    repo, _, r, hooks_before = updated
    hooks = _hooks(repo)
    text = json.dumps(hooks)
    assert "python3" not in text, r.stdout + r.stderr
    kit = [h for groups in hooks.values() for g in groups for h in g["hooks"] if ".claude/hooks/" in json.dumps(h)]
    assert kit and all(h["command"] == "py" and h["args"][0] == "-3" for h in kit)
    assert sum(len(g) for g in hooks.values()) == sum(len(g) for g in hooks_before.values())
    assert USER_HOOK in hooks["Stop"]
    assert "Windows form" in r.stdout, r.stdout + r.stderr


@needs_docker
def test_ac7_canon_copy_is_refreshed_and_kept_in_the_lock(work, kit_b, updated):
    repo, _, r, _ = updated
    lock = _lock(repo)
    copies = lock.get("canon_copies", [])
    if ".claude/skills" in copies:
        assert os.path.isfile(os.path.join(repo, ".claude", NEW_SKILL)), r.stdout + r.stderr
    else:
        assert os.path.islink(os.path.join(repo, ".claude", "skills"))
    assert os.path.isfile(os.path.join(repo, ".claude/skills/zz-my-own/SKILL.md"))


@needs_docker
def test_ac9_update_log_entry(work, kit_b, updated):
    repo, _, _, _ = updated
    log = _read(os.path.join(repo, ".claude", "update-log.md")).splitlines()
    assert log[0].startswith("## ") and log[0].endswith(f"Update {kit_b['A']} → {kit_b['B']}")
    assert log[1] == "Decided by: -Yes (kept edits)"
    assert f"- {kit_b['X2']} — kept your version" in log
    assert f"- {kit_b['Z1']} — removed (upstream no longer ships it)" in log
    assert f"- {kit_b['Z2']} — kept (you edited it; upstream no longer ships it)" in log
    assert "- 1 files added" in log


@needs_docker
def test_sc5_a_second_update_changes_nothing(work, kit_b, updated):
    repo, _, _, _ = updated
    again, cdir = _copy(work, repo, "upd-again")
    tree = _tree(again)
    r = _update(work, cdir)
    assert r.returncode == 2, r.stdout + r.stderr
    assert _tree(again) == tree
    log = _read(os.path.join(again, ".claude", "update-log.md"))
    assert log.count("\n## ") == 1 and "- 0 files added" in log.split("\n## ")[0]


@needs_docker
def test_sc6_a_failed_replace_keeps_the_old_lock_and_the_file(work, kit_b, installed):
    repo, cdir = _copy(work, installed, "readonly")
    x1 = os.path.join(repo, kit_b["X1"])
    lock_path = os.path.join(repo, ".claude", "harness-lock.json")
    with open(lock_path, "rb") as f:
        lock_before = f.read()
    x1_before = base._sha(x1)
    os.chmod(x1, 0o444)
    try:
        r = _update(work, cdir)
    finally:
        os.chmod(x1, 0o644)
    out = r.stdout + r.stderr
    assert r.returncode == 1, out
    with open(lock_path, "rb") as f:
        assert f.read() == lock_before
    assert base._sha(x1) == x1_before
    errors = [l for l in out.splitlines() if "[error]" in l]
    assert any(kit_b["X1"] in l and "harness-lock.json" in l for l in errors), out


@needs_docker
def test_sc7_mutation_control_a_neutered_replace_is_caught(work, kit_b, installed):
    mut = os.path.join(work, "mut")
    os.makedirs(os.path.join(mut, "lib"))
    for rel in ("setup.ps1", "update.ps1", "lib/harness.ps1", "lib/harness-update.ps1"):
        shutil.copy2(os.path.join(work, "kit", rel), os.path.join(mut, rel))
    target = os.path.join(mut, "lib", "harness-update.ps1")
    text = _read(target)
    assert text.count(REPLACE_LINE) == 1
    with open(target, "w", encoding="utf-8") as f:
        f.write(text.replace(REPLACE_LINE, "    # neutered by the T271 mutation control"))
    repo, cdir = _copy(work, installed, "mutrepo")
    _update(work, cdir, installer="/work/mut")
    assert sc1_problems(work, repo, kit_b), "a neutered replace went unnoticed"


@needs_docker
def test_ac8_lock_and_log_match_update_sh(work, kit_b, installed):
    """Parity: update.ps1 and update.sh, both with no terminal, from the same kits and edits."""
    repo, cdir = _copy(work, installed, "parity")
    r = _update(work, cdir, extra="")
    assert r.returncode == 2, r.stdout + r.stderr
    twin = os.path.join(work, "twin-upd")
    subprocess.run(["git", "init", "-q", twin], check=True)
    for script, kit in (("setup.sh", "kit"), ("update.sh", "kitb")):
        env = dict(os.environ, SUPERVISOR_REPO=os.path.join(work, kit), PATH="/usr/bin:/bin")
        sh = subprocess.run(["sh", os.path.join(work, "kit", script)], cwd=twin, env=env, capture_output=True,
                            text=True, stdin=subprocess.DEVNULL, start_new_session=True, timeout=300)
        assert sh.returncode == (0 if script == "setup.sh" else 2), sh.stdout + sh.stderr
        if script == "setup.sh":
            _user_edits(twin, kit_b)
    ps_lock, sh_lock = _lock(repo), _lock(twin)
    assert ps_lock["files"] == sh_lock["files"]
    for field in ("kit_commit", "claude_md_source"):
        assert ps_lock.get(field) == sh_lock.get(field), field
    ps_log = _read(os.path.join(repo, ".claude", "update-log.md")).splitlines()
    sh_log = _read(os.path.join(twin, ".claude", "update-log.md")).splitlines()
    assert ps_log[0].split(" — ", 1)[1] == sh_log[0].split(" — ", 1)[1]
    assert sorted(ps_log[1:]) == sorted(sh_log[1:])


@needs_docker
def test_ac10_reinstall_removes_what_the_kit_stopped_shipping(work, kit_b, installed):
    repo, cdir = _copy(work, installed, "reinst")
    r = base._install(work, cdir, repo="/work/kitb")
    out = r.stdout + r.stderr
    assert r.returncode == 0, out
    kb = os.path.join(work, "kitb")
    assert not os.path.exists(os.path.join(repo, kit_b["Z1"])), out
    assert _read(os.path.join(repo, kit_b["Z2"])).endswith("my own edit\n")
    for key in ("X1", "X2", "X3", "Y"):
        assert base._sha(os.path.join(repo, kit_b[key])) == base._sha(os.path.join(kb, kit_b[key])), key
    names = sorted(os.path.basename(b) for b in base._backups(repo))
    assert len(names) == 2 and all(".bak-" in n for n in names), names  # X2 and X3, one file each
    assert os.path.isfile(os.path.join(repo, OWN_FILE))
    files = _lock(repo)["files"]
    assert kit_b["Z1"] not in files and kit_b["Z2"] in files and kit_b["Y"] in files
    assert OWN_FILE not in files


@needs_docker
def test_an_unsafe_lock_entry_stops_before_any_write(work, kit_b, installed):
    repo, cdir = _copy(work, installed, "badlock")
    lock_path = os.path.join(repo, ".claude", "harness-lock.json")
    text = _read(lock_path).replace('"files": {\n', '"files": {\n    "templates/../../victim": "' + "0" * 64 + '",\n', 1)
    with open(lock_path, "w", encoding="utf-8") as f:
        f.write(text)
    tree = _tree(repo)
    r = _update(work, cdir)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "templates/../../victim" in r.stderr
    assert _tree(repo) == tree


@needs_docker
def test_a_link_inside_a_kit_folder_stops_before_any_write(work, kit_b, installed):
    """Nothing is copied or removed through a link under a MANIFEST path (it could point anywhere)."""
    repo, cdir = _copy(work, installed, "linked")
    skill = sorted(n for n in os.listdir(os.path.join(repo, "skills"))
                   if os.path.isdir(os.path.join(repo, "skills", n)))[0]
    outside = os.path.join(work, "outside-skill")
    shutil.move(os.path.join(repo, "skills", skill), outside)
    os.symlink(outside, os.path.join(repo, "skills", skill))
    tree, outside_tree = _tree(repo), _tree(outside)
    r = _update(work, cdir)
    assert r.returncode == 1, r.stdout + r.stderr
    assert f"'./skills/{skill}' is a link" in r.stderr
    assert _tree(repo) == tree and _tree(outside) == outside_tree


@pytest.fixture(scope="module")
def kit_c(work):
    """Kit C: kit A with a case-only rename of one templates file, and the `docs/claude-md`
    MANIFEST line dropped (that folder is no longer shipped)."""
    c = os.path.join(work, "kitc")
    subprocess.run(["git", "clone", "-q", os.path.join(work, "kit"), c], check=True)
    tmpl = sorted(n for n in os.listdir(os.path.join(c, "templates"))
                  if os.path.isfile(os.path.join(c, "templates", n)))
    name = tmpl[2]
    renamed = name.swapcase()
    assert renamed != name
    os.rename(os.path.join(c, "templates", name), os.path.join(c, "templates", renamed))
    manifest = os.path.join(c, "MANIFEST")
    lines = [l for l in _read(manifest).splitlines(True) if not (l.split() and l.split()[0] == "docs/claude-md")]
    with open(manifest, "w", encoding="utf-8") as f:
        f.writelines(lines)
    _git(c, "add", "-A")
    _git(c, "commit", "-qm", "kit C")
    return {"old": "templates/" + name, "new": "templates/" + renamed}


@needs_docker
def test_a_case_only_rename_removes_nothing_the_kit_still_ships(work, kit_c, installed):
    """Review P2-1: on NTFS both casings are one file; removing the old key deleted the file just
    refreshed. On Linux they are two files: the safe outcome is that neither is removed."""
    repo, cdir = _copy(work, installed, "caserename")
    r = _update(work, cdir, repo="/work/kitc")
    out = r.stdout + r.stderr
    assert r.returncode in (0, 2), out
    new = os.path.join(repo, kit_c["new"])
    assert os.path.isfile(new) and base._sha(new) == base._sha(os.path.join(work, "kitc", kit_c["new"])), out
    assert kit_c["new"] in _lock(repo)["files"]
    assert os.path.isfile(os.path.join(repo, kit_c["old"])), "the old casing was removed:\n" + out


@needs_docker
def test_a_link_replacing_a_dropped_kit_folder_does_not_stop_update(work, kit_c, installed):
    """Review P3-1: lock entries outside every current MANIFEST path are only carried over, so a
    link there (a folder the kit stopped shipping) is no reason to stop."""
    repo, cdir = _copy(work, installed, "droproot")
    outside = os.path.join(work, "outside-docs")
    shutil.move(os.path.join(repo, "docs", "claude-md"), outside)
    os.symlink(outside, os.path.join(repo, "docs", "claude-md"))
    outside_tree = _tree(outside)
    r = _update(work, cdir, repo="/work/kitc")
    out = r.stdout + r.stderr
    assert r.returncode in (0, 2), out
    assert "is a link" not in out
    assert os.path.islink(os.path.join(repo, "docs", "claude-md")) and _tree(outside) == outside_tree


needs_script = pytest.mark.skipif(shutil.which("script") is None, reason="util-linux `script` is absent (it gives docker a pty)")


def _update_tty(work, cdir, answers, repo="/work/kitb"):
    """update.ps1 at a terminal: `docker run -it` under `script`, which supplies the pty."""
    cmd = ["docker", "run", "--rm", "-it", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
           "-v", "/usr:/host/usr:ro", "-v", f"{work}:/work",
           "-e", "HOME=/work/home", "-e", "GIT_EXEC_PATH=/work/git-core",
           "-e", "GIT_TEMPLATE_DIR=/host/usr/share/git-core/templates",
           "-e", "PATH=/work/bin-full:/opt/microsoft/powershell/7", "-e", f"SUPERVISOR_REPO={repo}",
           base.IMAGE, "/opt/microsoft/powershell/7/pwsh", "-NoProfile", "-Command",
           f"Set-Location '{cdir}'; & /work/kit/update.ps1; exit $LASTEXITCODE"]
    return subprocess.run(["script", "-qec", shlex.join(cmd), "/dev/null"], input=answers,
                          capture_output=True, text=True, timeout=300)


@needs_docker
@needs_script
def test_overwrite_all_at_a_terminal_backs_up_then_replaces(work, kit_b, installed):
    """Review P2-2: choose_update_mode 2 (overwrite all): the user's version goes to .bak-<id>."""
    repo, cdir = _copy(work, installed, "tty-over")
    x1 = os.path.join(repo, kit_b["X1"])
    _append(x1, "\nuser X1 edit\n")
    with open(x1, "rb") as f:
        mine = f.read()
    r = _update_tty(work, cdir, "2\n")
    assert r.returncode == 0, r.stdout
    baks = [n for n in os.listdir(repo) if n.startswith("AGENTS.md.bak-")]
    assert len(baks) == 1, r.stdout
    with open(os.path.join(repo, baks[0]), "rb") as f:
        assert f.read() == mine
    assert base._sha(x1) == base._sha(os.path.join(work, "kitb", kit_b["X1"]))
    log = _read(os.path.join(repo, ".claude", "update-log.md")).splitlines()
    assert "Decided by: auto-approve (overwrite all)" in log
    assert f"- AGENTS.md \u2014 overwrote (your edits; backup {baks[0]})" in log


@needs_docker
@needs_script
def test_a_failed_backup_keeps_the_users_file_and_its_lock_hash(work, kit_b, installed):
    """Review P2-2: overwrite all, but the backup cannot be made (read-only folder)."""
    repo, cdir = _copy(work, installed, "tty-bkfail")
    x2 = os.path.join(repo, kit_b["X2"])
    before = base._sha(x2)
    parent = os.path.dirname(x2)
    os.chmod(parent, 0o555)
    try:
        r = _update_tty(work, cdir, "2\n")
    finally:
        os.chmod(parent, 0o755)
    assert r.returncode == 2, r.stdout
    assert base._sha(x2) == before
    assert _lock(repo)["files"][kit_b["X2"]] == _lock(installed)["files"][kit_b["X2"]]
    assert f"- {kit_b['X2']} \u2014 kept (backup failed:" in _read(os.path.join(repo, ".claude", "update-log.md"))


@needs_docker
def test_update_ps1_refuses_where_nothing_is_installed(work):
    repo, cdir = base._new_repo(work, "noinstall")
    before = sorted(os.listdir(repo))
    r = _update(work, cdir, repo="/work/kit")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "No .claude/harness-lock.json found" in r.stderr
    assert sorted(os.listdir(repo)) == before


@needs_docker
def test_the_windows_ci_update_smoke_passes_in_linux_pwsh(work):
    r = base._pwsh(work, "& /work/kit/tests/windows/smoke-update.ps1; exit $LASTEXITCODE")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SMOKE PASS" in r.stdout
    assert not os.path.exists(os.path.join(work, "python3-was-called"))
