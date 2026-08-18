#!/usr/bin/env python3
"""T065 — the hot-tier memory contract: an honest channel and a gate that measures cost.

Two fictions were written into the harness and shipped downstream by `setup.sh`:

1. **The channel.** `craft-spawn-prompt` element 4 mandated *"Full contents of
   `memory/MEMORY.md`, verbatim"*. T063 established that practice passes a **path**
   (`docs/memory-usage-finding-2026-08-07.md` §b: zero of 49 `Agent` records carried
   the file's H1; 5 of 5 recent agents opened the file themselves). The sharp end was
   `docs/claude-md/pipeline-stages.md` — *"the agent must not re-read it; it is already
   in context"* — a sentence that, under the real channel, makes an obedient agent skip
   memory entirely.

2. **The size gate.** `assert len(lines) <= 200`, while the cost is characters. Over the
   last 12 commits touching the file, lines were pinned at 199–201 while characters went
   42,577 → 49,156 (+15.5%). The gate was green on every one of them.

  AC7  — no shipping file still claims verbatim injection
  AC8  — `setup.sh`'s seeded stub carries the corrected rules
  AC9  — no shipping file still states a 200-*line* memory cap
  AC10 — +4,000 chars onto existing entries (zero new lines) turns the gate RED
  AC11 — many short lines past 200 lines, still under budget, stays GREEN

**AC10 and AC11 operate on a copy under `tmp_path`.** Nothing in this module writes to the
real `memory/MEMORY.md`. T059 was a defect of exactly that shape and inside a worktree it
destroyed data.

Run with: python3 -m pytest .claude/hooks/tests/test_memory_channel_and_budget.py -v
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_token_audit_format import (  # noqa: E402
    HOT_TIER_CHAR_BUDGET,
    MEMORY_PATH,
    assert_hot_tier_within_budget,
    hot_tier_entry_report,
    measure_hot_tier,
)

ROOT = Path(__file__).resolve().parents[3]

# The **shipping** surface: files that state the contract to a reader or to a
# downstream repo. Enumerated explicitly rather than globbed, so adding a new
# contract location is a deliberate act.
SHIPPING_FILES = [
    "CLAUDE.md",
    "CLAUDE_LEGACY.md",
    "README.md",
    "setup.sh",
    "docs/claude-md/pipeline-stages.md",
    "docs/claude-md/memory-write-protocol.md",
    "docs/claude-md/folder-structure.md",
    "docs/claude-md/code-naming-conventions.md",
    "docs/claude-md/phase0-project-initiation.md",
    "memory/MEMORY.md",
    ".claude/skills/craft-spawn-prompt/SKILL.md",
    ".claude/skills/compact-memory/SKILL.md",
    ".claude/skills/compact-advisor/SKILL.md",
    ".claude/skills/bugfix/SKILL.md",
    ".claude/skills/wake/SKILL.md",
    ".claude/skills/learn/SKILL.md",
    ".claude/agents/general-agent-template.md",
    ".claude/agents/common-infrastructure.md",
    ".claude/agents/backend.md",
    ".claude/agents/frontend.md",
    ".claude/agents/qa.md",
    ".claude/hooks/post_bash_memory_update.py",
    ".claude/hooks/post_agent_move_to_review.py",
]

# Deliberately OUT of scope, with the reason stated rather than left implicit:
#
# * `memory/decisions.md`, `learnings.md`, `glossary.md` — cold tier, Supervisor-only,
#   and a dated record of what was believed at the time.
# * `docs/memory-usage-finding-2026-08-07.md`, `docs/ddr/*` — historical records of a
#   specific date. Rewriting them to match the new state destroys the evidence trail.
# * `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md`, `tasks/*` — they *describe* the old rule
#   and legitimately quote it; this very task's guide quotes it a dozen times.
# * `.claude/hooks/tests/*` — several carry the old spawn-prompt shape as **fixture data**
#   and as the recorded rationale for a hook's inertness. Editing fixture prose so a
#   sibling assertion goes green is the "loosen the test to fit the fix" family, which
#   this repo has recorded against itself repeatedly.

# AC7 — the literal claims that were on disk before T065, each recovered from the
# pre-change grep. A generic "MEMORY.md near the word paste/inject" regex was rejected:
# it fires on the *corrected* wording too ("Do **not** paste its contents"), which would
# force the fix to avoid naming what it is fixing.
VERBATIM_INJECTION_CLAIMS = [
    "Full contents of `memory/MEMORY.md`, verbatim",
    "Injected in full into every sub-agent spawn prompt",
    "Injected verbatim into every sub-agent spawn prompt",
    "injected verbatim into every spawn",
    "paste the full contents of `memory/MEMORY.md` verbatim",
    "pastes the full `memory/MEMORY.md` verbatim",
    "always injected into spawn prompts",
    "injected into every sub-agent spawn prompt",
    "the agent must not re-read it",
    "do not re-read it if present there",
    "`memory/MEMORY.md` verbatim, agent-guide pointer",
]

# AC9 — a line-based memory cap in any form.
LINE_CAP_PATTERN = re.compile(r"(?:≤\s*200|under \*\*200\*\*|Max 200|200)\s*lines", re.I)

# AC9's mandated exclusion, matched by CONTENT, never by count. `CLAUDE.md`'s Simplicity
# First row and its restatements in the agent guides contain "200 lines" in a completely
# unrelated sense. A count-based allowance ("one hit is fine") silently permits the next
# real regression, so the allowance is the sentence itself.
UNRELATED_200_LINES = [
    "If 200 lines can be 50, rewrite",
    "If 200 lines can be 50, write 50",
    "if 200 lines can be 50, rewrite",
]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Anti-vacuity guard. Every negative below is a "no hit" assertion, which a
# mistyped path satisfies for free. If any enumerated shipping file stops
# existing, the whole AC7/AC9 sweep is inspecting nothing — fail loudly.
# --------------------------------------------------------------------------
def test_every_enumerated_shipping_file_exists():
    missing = [rel for rel in SHIPPING_FILES if not (ROOT / rel).is_file()]
    assert not missing, (
        f"{len(missing)} enumerated shipping file(s) do not exist, so the AC7/AC9 "
        f"negative sweeps silently inspect nothing: {missing}"
    )


def test_ac7_no_shipping_file_claims_verbatim_memory_injection():
    hits = []
    for rel in SHIPPING_FILES:
        text = _read(rel)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for claim in VERBATIM_INJECTION_CLAIMS:
                if claim in line:
                    hits.append(f"{rel}:{lineno}: {claim!r}")
    assert not hits, (
        "shipping file(s) still claim `memory/MEMORY.md` is injected verbatim. "
        "The real channel passes a path the agent reads (T063 §b):\n  "
        + "\n  ".join(hits)
    )


def test_ac9_no_shipping_file_states_a_line_based_memory_cap():
    hits = []
    for rel in SHIPPING_FILES:
        for lineno, line in enumerate(_read(rel).splitlines(), start=1):
            if not LINE_CAP_PATTERN.search(line):
                continue
            if any(allowed in line for allowed in UNRELATED_200_LINES):
                continue  # excluded by content — see UNRELATED_200_LINES
            hits.append(f"{rel}:{lineno}: {line.strip()[:120]}")
    assert not hits, (
        "shipping file(s) still state a 200-LINE memory cap. Lines are not what the "
        "file costs — the cap is now HOT_TIER_CHAR_BUDGET characters:\n  "
        + "\n  ".join(hits)
    )


def test_ac9_exclusion_is_by_content_and_the_excluded_lines_really_exist():
    """The Simplicity First lines must still be present and untouched.

    Without this, deleting them would be an equally green way to pass AC9 — and the
    guide's Must-Not-Touch list names them explicitly.
    """
    found = 0
    for rel in SHIPPING_FILES:
        for line in _read(rel).splitlines():
            if any(allowed in line for allowed in UNRELATED_200_LINES):
                found += 1
    assert found >= 2, (
        f"expected the unrelated Simplicity-First 'If 200 lines can be 50' lines to "
        f"survive untouched; found {found}. They are on the Must-Not-Touch list."
    )


def test_ac5_and_ac6_the_contract_now_states_the_path_channel():
    """Positive counterpart to AC7 — absence of the old claim is not presence of the new one."""
    skill = _read(".claude/skills/craft-spawn-prompt/SKILL.md")
    assert "The **path** `memory/MEMORY.md`" in skill
    assert "Do **not** paste its contents" in skill

    stages = _read("docs/claude-md/pipeline-stages.md")
    assert "**the agent must read it itself**" in stages, (
        "pipeline-stages.md must invert the old 'must not re-read it' sentence (AC6)"
    )

    template = _read(".claude/agents/general-agent-template.md")
    assert "read `memory/MEMORY.md` yourself" in template


def test_ac8_setup_sh_seeded_stub_carries_the_corrected_rules():
    setup = _read("setup.sh")
    stub = setup.split("cat > ./memory/MEMORY.md <<'EOF'")[1].split("\nEOF")[0]
    assert f"{HOT_TIER_CHAR_BUDGET:,} characters" in stub, "seeded stub must carry the character budget"
    assert "ratchet" in stub, "seeded stub must say the budget only ever goes down"
    assert "path to read" in stub, "seeded stub must describe the real channel"
    assert "200 lines" not in stub
    assert "Injected in full" not in stub
    # The heredoc is quoted (<<'EOF'), so nothing in the stub may look like an
    # expansion — an unquoted `$` or backtick would be silently evaluated if anyone
    # ever unquotes it, and `$(` would be evaluated the moment they do.
    assert "$(" not in stub


# --------------------------------------------------------------------------
# AC10 / AC11 — the gate itself, on a COPY. Never the real file.
# --------------------------------------------------------------------------
def _memory_copy(tmp_path: Path) -> Path:
    dest = tmp_path / "MEMORY.md"
    dest.write_text(MEMORY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def test_live_memory_md_is_within_budget_today():
    """SC1 — this task must not turn the suite red on arrival."""
    chars, _ = measure_hot_tier(MEMORY_PATH)
    assert chars <= HOT_TIER_CHAR_BUDGET, hot_tier_entry_report(MEMORY_PATH)


def _pad_past_budget(copy: Path) -> tuple[int, int, int, int]:
    """Pad EXISTING `- [` entry lines, cycling over them, until the budget is
    breached — independent of the live file's distance to the cap (AC1/AC3).
    No line is ever added; only existing entry lines are appended to.
    """
    chars_before, _ = measure_hot_tier(copy)
    lines_before = len(copy.read_text(encoding="utf-8").splitlines())

    pad = " Additional qualifying detail appended to an existing entry, no newline."
    lines = copy.read_text(encoding="utf-8").split("\n")
    entry_idxs = [i for i, line in enumerate(lines) if line.startswith("- [")]
    assert entry_idxs, "control failed: no '- [' entry lines to pad — cannot construct a breach"

    added = 0
    j = 0
    while chars_before + added <= HOT_TIER_CHAR_BUDGET:
        idx = entry_idxs[j % len(entry_idxs)]
        lines[idx] += pad
        added += len(pad)
        j += 1
    copy.write_text("\n".join(lines), encoding="utf-8")

    chars_after, _ = measure_hot_tier(copy)
    lines_after = len(copy.read_text(encoding="utf-8").splitlines())
    return chars_before, chars_after, lines_before, lines_after


def test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red(tmp_path):
    """THE defect. Under `len(lines) <= 200` this mutation was completely invisible."""
    copy = _memory_copy(tmp_path)
    chars_before, chars_after, lines_before, lines_after = _pad_past_budget(copy)

    # The mutation must actually have happened, and must be invisible to lines.
    assert lines_after == lines_before, "the mutation added lines — it is not the AC10 mutation"
    assert chars_after > chars_before, "the mutation added no characters — it is inert"
    # The mutation must have achieved its actual purpose: breaching the budget.
    # A mutation that merely "changed something" is not proof it did its job.
    assert chars_after > HOT_TIER_CHAR_BUDGET, (
        f"control failed: mutation did not breach the budget "
        f"({chars_after:,} <= {HOT_TIER_CHAR_BUDGET:,})"
    )

    # The OLD gate's verdict is UNCHANGED by a mutation that adds thousands of
    # characters. That invariance is the defect, stated in a form that does not
    # depend on the file's absolute line count (the header rewrite in this very
    # task moved it past 200, which is now harmless and was not before).
    old_gate = (lambda p: len(p.read_text(encoding="utf-8").splitlines()) <= 200)
    assert old_gate(copy) == (lines_before <= 200), (
        "control failed: the old line cap must be blind to this mutation"
    )

    # The NEW gate is red, and says something actionable (AC2).
    with pytest.raises(AssertionError) as exc:
        assert_hot_tier_within_budget(copy)
    message = str(exc.value)
    assert f"{chars_after:,}" in message, "failure message must name the current size"
    assert f"{HOT_TIER_CHAR_BUDGET:,}" in message, "failure message must name the budget"
    assert f"{chars_after - HOT_TIER_CHAR_BUDGET:,}" in message, "must name the overage"
    assert "ratchet" in message, "must warn against raising the budget"


def test_ac10_turns_red_at_any_live_file_size(tmp_path):
    """AC3 — size-independence. A tiny synthetic stub must breach and go red
    the same way the live file does, proving the mutation does not silently
    depend on how close the real file happens to sit to the cap.
    """
    stub = tmp_path / "MEMORY.md"
    stub.write_text(
        "- [entry one](a.md) — short.\n"
        "- [entry two](b.md) — short.\n"
        "- [entry three](c.md) — short.\n",
        encoding="utf-8",
    )
    chars_before, chars_after, lines_before, lines_after = _pad_past_budget(stub)

    assert lines_after == lines_before
    assert chars_after > HOT_TIER_CHAR_BUDGET, (
        f"control failed: tiny-stub mutation did not breach the budget "
        f"({chars_after:,} <= {HOT_TIER_CHAR_BUDGET:,})"
    )
    with pytest.raises(AssertionError):
        assert_hot_tier_within_budget(stub)


def test_ac11_many_short_lines_past_200_stay_green_while_under_budget(tmp_path):
    """The opposite direction — the fix must not be the old bug under a new name."""
    copy = _memory_copy(tmp_path)
    text = copy.read_text(encoding="utf-8")
    lines_before = len(text.splitlines())

    copy.write_text(text + "\n".join([""] * 41), encoding="utf-8")

    lines_after = len(copy.read_text(encoding="utf-8").splitlines())
    chars_after, _ = measure_hot_tier(copy)

    assert lines_after > 200, (
        f"control failed: the mutation must push past the old 200-line cap "
        f"({lines_before} -> {lines_after})"
    )
    assert chars_after <= HOT_TIER_CHAR_BUDGET
    assert_hot_tier_within_budget(copy)  # green, as it should be


def test_ac3_per_entry_report_is_advisory_and_never_fails(tmp_path):
    """89% of entries miss the documented target; the report says so and stays green."""
    copy = _memory_copy(tmp_path)
    report = hot_tier_entry_report(copy)
    assert "advisory, not enforced" in report
    assert "over the documented 150-char target" in report
    assert_hot_tier_within_budget(copy)


def test_ac12_memory_md_header_rules_state_the_budget_and_the_channel():
    """AC12's *invariant* half. The scope-guard half is deliberately gone.

    As shipped this test asserted `len(entry_lengths) == 146` — the exact entry
    count at T065's review. That is a **scope guard**, not an invariant: it
    answered "did T065 touch the index?", which is a question only meaningful
    while T065 was in review. Committed as a standing assertion it forbade the
    harness from ever recording a new memory entry, and it failed on the very
    first legitimate memory pass after the merge. Neither the implementer nor
    the Supervisor caught it at Stage 4 because nothing added an entry while
    the test existed — it could only manifest in use.

    (Recorded rule: "working-tree-vs-HEAD is a scope guard, not a repeatable
    test — decide invariant or one-shot." AC12 was verified at review time by
    diffing the index lines directly: 0 changed, 6 insertions / 3 deletions,
    all header rules. That verification is done and does not need re-running
    forever.)

    What genuinely *is* invariant is that the header still states the budget and
    the path channel — the two things T065 exists to establish.
    """
    header = MEMORY_PATH.read_text(encoding="utf-8").split("---", 1)[0]
    assert f"{HOT_TIER_CHAR_BUDGET:,} characters" in header
    assert "ratchet" in header
    assert "path" in header.lower()
    assert "Injected in full" not in header


def test_ac4_documented_per_entry_limit_is_labelled_an_aspiration():
    """Silently keeping ≤150 while 89% violate it is not acceptable (AC4)."""
    header = _read("memory/MEMORY.md").split("### Decisions")[0]
    assert "ASPIRATION" in header
    assert "130 of 146 entries exceed it" in header
