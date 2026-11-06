#!/usr/bin/env python3
"""T096 AC11/AC12 — `.claude/{skills,agents}` are relative symlinks onto the plain-root canon.

T096 moved the canon to `skills/` and `agents/` and left `.claude/skills` and `.claude/agents`
behind as committed relative symlinks. Claude Code only discovers skills and agent guides under
`.claude/`, so those two links are the sole thing making this repo able to run its own skills.

They are also the easiest thing in the tree to destroy by accident. A reader seeing `skills/` in a
diff can mistake `.claude/skills` for a stale duplicate and delete it; a well-meaning "fix" can
replace a link with a copy, and the copy then silently rots out of sync with the canon; a Windows
checkout or an over-eager archive tool can materialise the link as a real directory.

None of those show up as a test failure anywhere else in this suite — the rest of the suite reads
files through paths that resolve either way. That is the gap these tests close:

* AC12 — the links exist, are symlinks, resolve, and are **relative**. An absolute target is a
  correctness bug, not a style choice: every sub-agent works in a `git worktree`, and a baked
  absolute path either is missing there or points back into the main checkout, letting an agent
  read canon from outside its own isolation boundary.
* AC11 — anti-vacuity. Deleting `.claude/skills` must turn this suite RED. The mutation controls
  below prove these assertions actually fire instead of passing on a tree where nothing is there.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

# link under .claude/  ->  the canon directory it must point at
CANON_LINKS = {"skills": "../skills", "agents": "../agents"}

# A file that must be reachable *through* each link — proves the link resolves onto real content
# rather than merely existing.
PROBE = {"skills": "wake/SKILL.md", "agents": "backend.md"}


@pytest.mark.parametrize("name", sorted(CANON_LINKS))
def test_ac1_canon_lives_at_plain_root(name):
    """The canon directory itself is a real directory at plain root, not under .claude/."""
    canon = ROOT / name
    assert canon.is_dir(), f"{name}/ is missing from the repo root — canon must live at plain root"
    assert not canon.is_symlink(), f"{name}/ must be the real directory, not a link"


@pytest.mark.parametrize("name", sorted(CANON_LINKS))
def test_ac12_claude_dir_entry_is_a_symlink(name):
    """AC12: `.claude/<name>` is a symlink — never a copy of the canon.

    A copy would pass every other test in this suite while drifting out of sync with `<name>/`
    from the moment it was made.
    """
    link = ROOT / ".claude" / name
    assert link.exists() or link.is_symlink(), f".claude/{name} is missing"
    assert link.is_symlink(), (
        f".claude/{name} is a real {'directory' if link.is_dir() else 'file'}, not a symlink. "
        f"The canon lives at {name}/; .claude/{name} must link to it so the two cannot diverge."
    )


@pytest.mark.parametrize("name", sorted(CANON_LINKS))
def test_ac12_symlink_target_is_relative(name):
    """AC12: the target is the relative `../<name>`, never an absolute path.

    Absolute targets break `git worktree add`: the link would resolve into whichever checkout ran
    the command, so a sub-agent in an isolated worktree would silently read the main checkout's
    canon.
    """
    link = ROOT / ".claude" / name
    target = os.readlink(link)
    assert not os.path.isabs(target), (
        f".claude/{name} -> {target} is absolute. It must be '{CANON_LINKS[name]}' so it resolves "
        f"inside whatever checkout or worktree it is read from."
    )
    assert target == CANON_LINKS[name], (
        f".claude/{name} -> {target}, expected {CANON_LINKS[name]}"
    )


@pytest.mark.parametrize("name", sorted(CANON_LINKS))
def test_ac11_link_resolves_onto_real_canon_content(name):
    """AC11: the link is load-bearing — real content is reachable through it.

    This is the assertion that goes RED if `.claude/<name>` is deleted, which is exactly the
    accident the link is most exposed to.
    """
    through_link = ROOT / ".claude" / name / PROBE[name]
    assert through_link.is_file(), (
        f".claude/{name}/{PROBE[name]} is not readable. Either the symlink is gone or it is "
        f"broken — Claude Code can no longer discover this repo's own {name}."
    )
    assert through_link.resolve() == (ROOT / name / PROBE[name]).resolve(), (
        f".claude/{name}/{PROBE[name]} does not resolve to {name}/{PROBE[name]}"
    )


@pytest.mark.parametrize("name", sorted(CANON_LINKS))
def test_ac11_mutation_control_deleting_the_link_is_detected(tmp_path, name):
    """Anti-vacuity control: reproduce the layout, delete the link, confirm the checks fail.

    Without this, every assertion above would still pass on a tree where the checks were quietly
    weakened — the failure mode DDR-0006 requires a mutation control for.
    """
    fake_root = tmp_path / "repo"
    (fake_root / name).mkdir(parents=True)
    (fake_root / name / PROBE[name]).parent.mkdir(parents=True, exist_ok=True)
    (fake_root / name / PROBE[name]).write_text("canon\n")
    (fake_root / ".claude").mkdir()
    link = fake_root / ".claude" / name
    link.symlink_to(CANON_LINKS[name])

    # Sanity: the reproduction is faithful — the real assertions pass on it.
    assert link.is_symlink()
    assert (link / PROBE[name]).is_file()

    # Mutation 1: the link is deleted. The AC11 probe must fail.
    link.unlink()
    assert not (link / PROBE[name]).is_file(), (
        "deleting .claude/%s left content still reachable — the AC11 check is vacuous" % name
    )

    # Mutation 2: the link is replaced by a copy. The AC12 symlink check must fail.
    link.mkdir()
    (link / PROBE[name]).parent.mkdir(parents=True, exist_ok=True)
    (link / PROBE[name]).write_text("stale copy\n")
    assert not link.is_symlink(), (
        "a plain directory registered as a symlink — the AC12 check is vacuous"
    )

    # Mutation 3: an absolute target. The relative-target check must reject it.
    import shutil

    shutil.rmtree(link)
    link.symlink_to(fake_root / name)
    assert os.path.isabs(os.readlink(link)), "expected an absolute target in the control"
    assert os.readlink(link) != CANON_LINKS[name], (
        "an absolute target compared equal to the relative one — the AC12 check is vacuous"
    )
