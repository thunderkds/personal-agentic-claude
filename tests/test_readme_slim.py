"""T085 — README.md slimming + hook-fact correction assertions (AC1, AC2, AC8)."""
import re
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"


def _read():
    return README.read_text(encoding="utf-8")


def test_readme_is_at_most_60_lines():
    lines = _read().splitlines()
    assert len(lines) <= 60, f"README.md is {len(lines)} lines, expected <= 60"


def test_readme_contains_exact_install_command():
    text = _read()
    install = (
        "curl -fsSL "
        "https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"
    )
    assert install in text, "exact install one-liner (curl ... | sh) not found verbatim"


def test_readme_does_not_claim_move_to_review_hook_moves_or_resets():
    text = _read().lower()
    # The false claim asserted the hook moves a task In Progress -> Ready for Review
    # and/or resets a step-limit counter. Neither claim may appear.
    assert "moves task" not in text, "README still claims the move-to-review hook moves a task"
    assert not re.search(
        r"resets?\s+(that\s+task'?s\s+)?step-limit counter", text
    ), "README still claims the move-to-review hook resets a step-limit counter"


def test_readme_step_limit_default_matches_hook_source():
    """AC5/AC8. Positive assertion against the source of truth, mirroring
    T083's `test_step_limit_matches_source`, rather than a negative check for
    the literal "40".

    The original negative form was **vacuous** and Stage 4 measured it passing
    against a README that read `default 40 calls`. Two independent reasons:
    `.` does not match a newline, so on the wrapped README the context window
    stopped at the line break; and even normalised to one line, a `.{0,40}`
    window after `step_limit` ends inside `(defa`, six characters short of the
    number it was meant to inspect. A negative assertion that never reaches the
    text it negates is satisfied by anything.
    """
    hook = README.parent / ".claude" / "hooks" / "pre_agent_step_limit.py"
    match = re.search(
        r'STEP_LIMIT\s*=\s*int\(os\.environ\.get\("CLAUDE_STEP_LIMIT",\s*"(\d+)"\)\)',
        hook.read_text(encoding="utf-8"),
    )
    assert match, "could not parse STEP_LIMIT default out of pre_agent_step_limit.py"
    limit = match.group(1)

    text = " ".join(_read().split())
    cited = re.findall(r"default\s+(\d+)\s+calls", text, flags=re.IGNORECASE)
    assert cited, (
        "README states no step-limit default at all — the corrected fact must "
        "survive the slimming, not be deleted by it (AC7)"
    )
    for value in cited:
        assert value == limit, (
            f"README cites step-limit default {value}, but "
            f"pre_agent_step_limit.py's source says {limit}"
        )
