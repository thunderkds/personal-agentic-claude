"""Format/convention test for the Token Audit Log scaffold (T028, DDR-0001).

Validates that reports/token-audit_2026-07-17.md documents the required
convention elements and that its sample entries match the entry regex the
convention defines. Also asserts a malformed entry (missing the Task-ID/
overhead tag) is rejected by that same regex, so the format is actually
constraining rather than decorative (Hard-Stop Gate 5).
"""
import re
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parents[3] / "reports" / "token-audit_2026-07-17.md"

ENTRY_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2} \| "
    r"(cold-start|stage-[0-9.]+|spawn|cost) \| "
    r"(T\d+|overhead) \| "
    r"(hit|miss) \| "
    r"(haiku|sonnet|opus) \| "
    r".+$"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_scaffold_file_exists():
    assert REPORT_PATH.is_file()


def test_header_documents_required_convention_elements():
    text = _report_text().lower()
    required_phrases = [
        "window-close condition",
        "7 logged sessions or 14 calendar days",
        "task-tag",
        "cache",
        "model-tier",
        "/cost",
    ]
    for phrase in required_phrases:
        assert phrase in text, f"missing required convention element: {phrase!r}"


def test_sample_entries_match_entry_regex():
    text = _report_text()
    sample_block = text.split("## Sample entries")[1].split("## Real entries")[0]
    sample_lines = [
        line for line in sample_block.splitlines()
        if re.match(r"^\d{4}-\d{2}-\d{2} \|", line.strip())
    ]
    assert len(sample_lines) >= 3
    for line in sample_lines:
        assert ENTRY_REGEX.match(line), f"sample entry did not match format: {line!r}"


def test_malformed_entry_missing_task_tag_is_rejected():
    malformed = "2026-07-17 | spawn | hit | sonnet | missing the task-tag field"
    assert not ENTRY_REGEX.match(malformed)


# --------------------------------------------------------------------------
# Hot-tier memory size gate (T065).
#
# Lives in this token-audit file for historical reasons (T028 added it here) and
# is deliberately left in place — moving it is out of T065's scope.
# --------------------------------------------------------------------------

MEMORY_PATH = Path(__file__).resolve().parents[3] / "memory" / "MEMORY.md"

# Whole-file character budget for `memory/MEMORY.md`.
#
# This replaced `assert len(lines) <= 200` (T065). Lines are not what the file
# costs. Across the last 12 commits that touched it the line count sat pinned at
# 199-201 while the character count went 42,577 -> 49,156 (+15.5%), and the old
# gate was green on every one of those commits. Twice the line count went *down*
# while the character count went *up*. Characters are what an agent pays to read
# the file, so characters are what is measured.
#
# ### THIS NUMBER IS A RATCHET.
# It may be **lowered** — by `/compact-memory`, or by any pass that genuinely
# shrinks the file — and it must **never be raised to accommodate growth**.
# Raising it is precisely the decay that made the old line cap meaningless. If
# the file no longer fits, compact the file, not the budget.
#
# 50,000 = 47,712 (the file after the 2026-08-09 /compact-memory pass) + ~5%
# headroom, so the next few honest edits land without anyone being tempted to
# edit this line. Ratcheted DOWN from 52,000 by that pass, which consolidated 26
# gotcha entries into 5 — the only direction this number is ever allowed to move.
HOT_TIER_CHAR_BUDGET = 45_000

# Characters, not bytes. The file is full of `—`, `≤`, `☐`; its byte count is
# ~1.1% higher than its character count, so a byte budget would not mean what
# this one says. The count is of the decoded text exactly as read from disk,
# **trailing newline included** — pinned here so the number is reproducible.
#
# Advisory only, never enforced (T065 AC3): `memory/MEMORY.md` documents a
# per-entry target of 150 characters that 130 of its 146 entries currently miss
# (mean 326, max 796). Enforcing it would turn the suite red on arrival and
# compacting the content is `/compact-memory`'s job, so the per-entry figure is
# reported and the whole-file budget is what gates.
DOCUMENTED_ENTRY_CHAR_TARGET = 150

_ENTRY_PREFIX = "- ["


def measure_hot_tier(memory_path: Path):
    """Read `memory_path` and return `(char_count, [entry_length, ...])`.

    Read-only — it opens the file and nothing else. Callers in the test suite
    must pass a **copy** under `tmp_path`; nothing here may ever write to the
    real `memory/MEMORY.md` (T059 was a defect of exactly that shape and inside
    a worktree it destroyed data).
    """
    text = memory_path.read_text(encoding="utf-8")
    entry_lengths = [
        len(line) for line in text.splitlines() if line.startswith(_ENTRY_PREFIX)
    ]
    return len(text), entry_lengths


def hot_tier_entry_report(memory_path: Path) -> str:
    """Advisory per-entry statistics. Never raises on the per-entry figures."""
    chars, entry_lengths = measure_hot_tier(memory_path)
    if not entry_lengths:
        return (
            f"hot-tier report: {chars:,} / {HOT_TIER_CHAR_BUDGET:,} chars, "
            f"0 index entries found"
        )
    over = sum(1 for n in entry_lengths if n > DOCUMENTED_ENTRY_CHAR_TARGET)
    return (
        f"hot-tier report: {chars:,} / {HOT_TIER_CHAR_BUDGET:,} chars "
        f"({HOT_TIER_CHAR_BUDGET - chars:,} remaining)\n"
        f"  entries: {len(entry_lengths)}  "
        f"mean {sum(entry_lengths) // len(entry_lengths)}  "
        f"max {max(entry_lengths)}  "
        f"over the documented {DOCUMENTED_ENTRY_CHAR_TARGET}-char target: "
        f"{over} ({round(100 * over / len(entry_lengths))}%) — advisory, not enforced"
    )


def assert_hot_tier_within_budget(memory_path: Path) -> None:
    """Fail if `memory_path` exceeds `HOT_TIER_CHAR_BUDGET`.

    The message names the current size, the budget and the overage: a bare
    `assert x <= y` tells the next Supervisor nothing it can act on (T065 AC2).
    """
    chars, _ = measure_hot_tier(memory_path)
    assert chars <= HOT_TIER_CHAR_BUDGET, (
        f"{memory_path.name} is {chars:,} characters, over the "
        f"{HOT_TIER_CHAR_BUDGET:,}-character hot-tier budget by "
        f"{chars - HOT_TIER_CHAR_BUDGET:,}. "
        f"Run `/compact-memory` to shrink the file — do NOT raise "
        f"HOT_TIER_CHAR_BUDGET, it is a ratchet that only ever goes down."
    )


def test_memory_md_hot_tier_stays_within_char_budget():
    # Printed, not asserted (AC3). pytest shows captured stdout on failure, and
    # `-s` shows it on a pass, so the numbers are available without ever being
    # able to turn the suite red on the per-entry figures.
    print(hot_tier_entry_report(MEMORY_PATH))
    assert_hot_tier_within_budget(MEMORY_PATH)
