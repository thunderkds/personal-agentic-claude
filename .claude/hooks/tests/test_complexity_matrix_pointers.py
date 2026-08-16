#!/usr/bin/env python3
"""T070 — the surviving Complexity-matrix pointers must name the channel that carries it.

T066 moved the C0–C3 Complexity matrix out of `.claude/agents/general-agent-template.md` and into
each role guide, which is the channel the harness auto-loads as an agent's system prompt. Three
shipping files kept pointing at the file the matrix left:

  * `CLAUDE.md`                        — Supervisor-facing (General Agent Template base rules)
  * `docs/claude-md/pipeline-stages.md` — Supervisor-facing (Stage 2 labelling instructions)
  * `templates/TASK_GUIDE_template.md`  — agent-facing, and shipped downstream via `MANIFEST`

  AC4 — negative: across those three files, no line pairs a Complexity-matrix claim with
        `general-agent-template.md`. Each path is asserted to **exist** first, and each file is
        asserted to still carry a Complexity-matrix pointer line at all, so a wrong path or a
        deleted line errors loudly instead of free-passing (the recorded negative-grep trap).
  AC5 — positive: the file each new pointer names actually contains `## Complexity & escalation`.
        A pointer is only fixed if its new target really holds the content.
  AC7 — negative: the out-of-scope files are unchanged. The historical record (the ~35
        `tasks/TASK_GUIDE_T0*.md`, `memory/decisions.md`) still carries the OLD wording verbatim —
        back-editing it would falsify the audit trail of what each agent was actually told
        (T064's fallback-not-migration precedent). Files listed as must-not-touch and genuinely
        frozen are pinned byte-identical to the pre-T070 baseline ref.

Run with: python3 -m pytest .claude/hooks/tests/test_complexity_matrix_pointers.py -v
"""
import subprocess

import pytest

from pathlib import Path

# Resolve from __file__, never from the cwd: one pre-existing suite test resolves a path
# cwd-relative and therefore reads green from the repo root and red from `.claude/hooks/`.
ROOT = Path(__file__).resolve().parents[3]

# The three stale shipping files this task rewrites.
POINTER_FILES = [
    "CLAUDE.md",
    "docs/claude-md/pipeline-stages.md",
    "templates/TASK_GUIDE_template.md",
]

# The channel that actually carries the matrix since T066.
ROLE_GUIDES = [
    ".claude/agents/common-infrastructure.md",
    ".claude/agents/backend.md",
    ".claude/agents/frontend.md",
    ".claude/agents/qa.md",
]

RETIRED_TARGET = "general-agent-template.md"
MATRIX_SECTION = "## Complexity & escalation"

# T070's edit commit — the same ref `test_agent_guide_dedup.py` pins CLAUDE.md to. None of the
# paths below is touched by T070, so this ref and the pre-T070 tip `78d0f8f` are interchangeable
# for them; one shared ref keeps the two files answering the same question. A baseline *ref* dates
# the comparison; a baseline *count* would freeze the world (T065's AC12).
T070_BASELINE_REF = "9f3f2e9"

# The exact clause the three shipping files retire, and which the historical record must keep.
RETIRED_CLAUSE = "Complexity matrix in `.claude/agents/general-agent-template.md`"

# Must-not-touch AND genuinely frozen: a completed-work review record that no future stage writes
# to, so bytes are the strongest available assertion.
#
# `README.md` and `.claude/agents/general-agent-template.md` were byte-pinned here too until the
# Stage 4 review (P2) removed them. They are on T070's must-not-touch list, but they are *living*
# files — the template was rewritten by T041, T051, T065, T066 and T069, and the README by T065 and
# `304e6e6` — so a standing byte-pin would go RED on the next legitimate edit and force the repoint
# dance T070 itself had to perform on `CLAUDE.md`. That is the recorded "a scope guard committed as
# an invariant blocks what it guarded" (T065's AC12). Byte-identity was the right question to ask
# *during* T070's review and the wrong thing to freeze afterwards, so what survives below is the
# durable property instead: each of those two describes the move correctly and neither has
# regressed into a stale pointer.
FROZEN_PATHS = [
    "tasks/TASK_REVIEW_T066.md",
]

# Already correct before T070 and deliberately untouched by it: each *describes* where the matrix
# went rather than pointing stalely at the file it left.
ALREADY_CORRECT_FILES = [
    "README.md",
    ".claude/agents/general-agent-template.md",
]

# Where the old wording is the historical record and must survive verbatim.
HISTORICAL_TREES = ["tasks", "memory"]


def _lines(rel: str) -> list[str]:
    path = ROOT / rel
    assert path.exists(), (
        f"{rel} does not exist under {ROOT}. A negative assertion over a path that is not there "
        f"passes vacuously, so this is an error, not a pass."
    )
    return path.read_text(encoding="utf-8").splitlines()


def _mentions_matrix(line: str) -> bool:
    """A Complexity-matrix claim, however the three files happen to word it."""
    low = line.lower()
    return "matrix" in low and ("complexity" in low or "c0–c3" in low or "c0-c3" in low)


# --------------------------------------------------------------------------
# AC4 — negative, per file, with an existence check and a non-vacuity anchor.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", POINTER_FILES)
def test_ac4_no_shipping_file_points_the_matrix_at_the_retired_template(rel):
    lines = _lines(rel)

    matrix_lines = [(n, ln) for n, ln in enumerate(lines, 1) if _mentions_matrix(ln)]
    assert matrix_lines, (
        f"{rel} no longer contains any Complexity-matrix pointer at all. This test excludes by "
        f"content, so a deleted line would satisfy the negative for the wrong reason."
    )

    offenders = [f"{rel}:{n}: {ln.strip()}" for n, ln in matrix_lines if RETIRED_TARGET in ln]
    assert not offenders, (
        f"{rel} still sends the reader to {RETIRED_TARGET} for the Complexity matrix, which T066 "
        f"moved into the role guides:\n  " + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------
# AC5 — positive: the new target really holds the matrix.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", ROLE_GUIDES)
def test_ac5_every_role_guide_actually_carries_the_complexity_matrix(rel):
    path = ROOT / rel
    assert path.exists(), f"{rel} does not exist under {ROOT}; the new pointer names nothing."
    assert MATRIX_SECTION in path.read_text(encoding="utf-8"), (
        f"{rel} does not contain '{MATRIX_SECTION}'. The three rewritten pointers name the role "
        f"guides as the matrix's home; if a role guide does not carry it, the pointer is as stale "
        f"as the one it replaced."
    )


# --------------------------------------------------------------------------
# AC7 — the out-of-scope files are unchanged.
# --------------------------------------------------------------------------
def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, capture_output=True
    ).stdout.decode("utf-8")


def _read_at(rel: str, ref: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{rel}"], check=True, capture_output=True
    ).stdout


def _historical_carriers() -> list[str]:
    """Paths that carried the retired clause at the pre-T070 baseline.

    Derived from the baseline commit rather than hard-coded, so the check calibrates itself
    instead of pinning a count that some later task would have to fight.
    """
    out = _git("grep", "-l", "-F", RETIRED_CLAUSE, T070_BASELINE_REF, "--", *HISTORICAL_TREES)
    prefix = f"{T070_BASELINE_REF}:"
    return sorted(line[len(prefix):] for line in out.splitlines() if line.startswith(prefix))


def test_ac7_historical_record_still_carries_the_old_wording_verbatim():
    carriers = _historical_carriers()
    assert len(carriers) > 30, (
        f"expected the ~35 historical guides plus memory/decisions.md to carry the retired "
        f"clause at {T070_BASELINE_REF}; found {len(carriers)}. If this is near zero the grep is "
        f"wrong and every assertion below would pass vacuously."
    )

    missing = []
    for rel in carriers:
        path = ROOT / rel
        if not path.exists():
            missing.append(f"{rel} (deleted)")
        elif RETIRED_CLAUSE not in path.read_text(encoding="utf-8"):
            missing.append(f"{rel} (clause removed)")

    assert not missing, (
        "T070 changes references in the three shipping files only. These files record what an "
        "agent was actually told at the time; back-editing them falsifies the audit trail "
        "(T064's fallback-not-migration precedent):\n  " + "\n  ".join(missing)
    )


@pytest.mark.parametrize("rel", FROZEN_PATHS)
def test_ac7_frozen_out_of_scope_files_are_byte_identical_to_the_baseline(rel):
    path = ROOT / rel
    assert path.exists(), f"{rel} does not exist under {ROOT}."
    assert path.read_bytes() == _read_at(rel, T070_BASELINE_REF), (
        f"{rel} changed. It is completed-work record — the Stage 4/5 review of a task that closed "
        f"on 2026-08-09 — so nothing should ever write to it again."
    )


@pytest.mark.parametrize("rel", ALREADY_CORRECT_FILES)
def test_ac7_already_correct_files_still_describe_the_move(rel):
    """The durable half of AC7 for the two living files, in place of a byte-pin (Stage 4 P2).

    Deliberately asserts the *property* rather than the bytes: these two may legitimately be
    rewritten by a later task, and must simply never regress into the defect T070 fixed.
    """
    lines = _lines(rel)

    matrix_lines = [(n, ln) for n, ln in enumerate(lines, 1) if _mentions_matrix(ln)]
    assert matrix_lines, (
        f"{rel} no longer mentions the Complexity matrix at all. It is one of the two files that "
        f"document where T066 moved it; losing that statement is how the pointer went stale in the "
        f"first place."
    )

    # Whole-text, not per-line: in `general-agent-template.md` the sentence wraps, so "Complexity
    # matrix" sits on line 8 and "role guide" on line 9. A line-scoped check here reads RED on a
    # correct file — caught by the control run for this fix.
    assert "role guide" in "\n".join(lines).lower(), (
        f"{rel} mentions the Complexity matrix but no longer names the role guide as its home."
    )

    offenders = [f"{rel}:{n}: {ln.strip()}" for n, ln in matrix_lines if RETIRED_TARGET in ln]
    assert not offenders, (
        f"{rel} now pairs a Complexity-matrix claim with {RETIRED_TARGET}. It described the move "
        f"correctly before T070 and has regressed into the stale pointer T070 retired:\n  "
        + "\n  ".join(offenders)
    )
