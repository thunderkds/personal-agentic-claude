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


def test_readme_does_not_claim_step_limit_default_is_40():
    text = _read()
    # Scoped to step-limit context so an unrelated "40" elsewhere can't false-positive.
    step_limit_context = re.findall(r".{0,40}step.limit.{0,40}", text, flags=re.IGNORECASE)
    for snippet in step_limit_context:
        assert "40" not in snippet, f"step-limit context still cites false default 40: {snippet!r}"
