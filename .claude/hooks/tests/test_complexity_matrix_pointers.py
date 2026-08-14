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

Run with: python3 -m pytest .claude/hooks/tests/test_complexity_matrix_pointers.py -v
"""
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
