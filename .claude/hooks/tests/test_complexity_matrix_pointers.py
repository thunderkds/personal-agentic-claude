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

# Must-not-touch AND genuinely frozen: no future stage writes to these three, so bytes are the
# strongest available assertion. Deliberately excludes `memory/decisions.md` and the TASK_GUIDEs,
# which legitimately gain content later (the memory pass; T070's own Evidence/Checklist) — those
# are protected by content below instead, which is the property actually at stake.
FROZEN_PATHS = [
    "README.md",
    ".claude/agents/general-agent-template.md",
    "tasks/TASK_REVIEW_T066.md",
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
        f"{rel} changed. It is on T070's Files-Must-NOT-Touch list: README.md was already correct "
        f"as of 304e6e6, general-agent-template.md line 8 *describes* the move rather than "
        f"pointing stalely at it, and TASK_REVIEW_T066.md is completed-work record."
    )
