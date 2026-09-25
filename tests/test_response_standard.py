"""Structural assertions for the shared Response Standard.

T100 (guidance-only) put six reply rules into `agents/general-agent-template.md`
and asserted two structural properties: the rules are defined once in that
shared template, and their text is not copy-pasted into the four role guides.

T103 fixes the premise T100's docstring stated wrongly. The template is *not*
"the one file every sub-agent and the Supervisor reach": the harness auto-loads
it as a sub-agent's system prompt, but it never auto-injects it into the
Supervisor's session, so the Supervisor got the standard only as a pointer it
had to remember to follow — and did not. T103 relocates the six rules verbatim
into `CLAUDE.md` (which IS auto-injected) and the tests below pin all three
directions so the fix cannot silently regress:

  AC1/AC4 — `CLAUDE.md` carries the six rule lines, byte-identical to the
            template's, compared by reading BOTH files at test time.
  AC2     — `CLAUDE.md` states the rules; it does not merely point at the
            template and tell the Supervisor to go read them.
  AC3     — the template still carries the standard, so the sub-agent channel
            stays pinned even if `CLAUDE.md` and the template drift.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "agents" / "general-agent-template.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
ROLE_GUIDES = [
    ROOT / "agents" / name
    for name in ("backend.md", "frontend.md", "qa.md", "common-infrastructure.md")
]


def _rule_lines(text: str) -> list[str]:
    """The Response Standard's bullet lines — every `- ` line in the section that
    starts at a `## Response Standard` / `### Response Standard` heading and runs
    to the next markdown heading. Read out of the file at test time, never
    hardcoded here, so the two copies cannot drift into a vacuous match."""
    m = re.search(r"^#{2,3} Response Standard\s*$(.*?)(?=^#)", text, re.M | re.S)
    body = m.group(1) if m else ""
    return [ln.rstrip() for ln in body.splitlines() if ln.startswith("- ")]


def test_response_standard_is_defined_once_in_the_shared_template():
    heading = "## Response Standard"
    assert TEMPLATE.read_text(encoding="utf-8").count(heading) == 1, (
        f"expected exactly one '{heading}' section in {TEMPLATE.name}"
    )


def test_response_standard_is_not_duplicated_into_the_role_guides():
    # A verbatim rule line, not the heading: a role guide may point at the
    # section by name, but must not carry the rules themselves. Taken from the
    # template itself so the two cannot drift apart into a vacuous assertion.
    rule = "recommendation first, alternatives one line each"
    assert rule in TEMPLATE.read_text(encoding="utf-8"), (
        f"the guard's probe string is no longer in {TEMPLATE.name}; "
        "update it to a current rule line or this test asserts nothing"
    )
    for guide in ROLE_GUIDES:
        assert rule not in guide.read_text(encoding="utf-8"), (
            f"{guide.name} duplicates the Response Standard rule text; it must point, not copy"
        )


# --------------------------------------------------------------------------
# T103 — the standard must reach the Supervisor, not just sub-agents.
# --------------------------------------------------------------------------
def test_t103_ac1_ac4_claude_md_carries_the_six_rules_byte_identical_to_the_template():
    template_rules = _rule_lines(TEMPLATE.read_text(encoding="utf-8"))
    claude_rules = _rule_lines(CLAUDE_MD.read_text(encoding="utf-8"))

    # Anti-vacuity: if the section moved or was renamed in the template, this
    # test would otherwise compare two empty lists and pass saying nothing.
    assert len(template_rules) == 7, (
        f"expected 7 Response Standard bullet lines in {TEMPLATE.name}, found "
        f"{len(template_rules)}: {template_rules}"
    )

    assert claude_rules == template_rules, (
        "CLAUDE.md's Response Standard rules are not byte-identical to the template's.\n"
        f"  CLAUDE.md: {claude_rules}\n"
        f"  template : {template_rules}\n"
        "The Supervisor reads CLAUDE.md (auto-injected) and sub-agents read the template "
        "(system prompt); the two copies must not drift."
    )


def test_t103_ac2_claude_md_states_the_rules_it_does_not_merely_point():
    text = CLAUDE_MD.read_text(encoding="utf-8")

    # Positive: the rules are actually present, as their own lines.
    assert len(_rule_lines(text)) == 7, (
        "CLAUDE.md does not carry the seven Response Standard rule lines; a pointer is not enough "
        "for the Supervisor, whose session the harness does not auto-inject the template into."
    )

    # Negative: the exact instruction that failed — telling the Supervisor to go
    # open the template and apply it — must be gone.
    banned = [
        "read it and apply it to your own replies",
        "binds the Supervisor too: read it",
    ]
    offenders = [p for p in banned if p in text]
    assert not offenders, (
        f"CLAUDE.md still tells the Supervisor to open the template instead of carrying the "
        f"rules inline: {offenders}"
    )


def test_t103_ac3_template_still_carries_the_standard_for_sub_agents():
    """The sub-agent channel stays pinned independently. A test that only checked
    CLAUDE.md would pass on a repo where the template had lost the section and
    every spawned agent was silently running without it."""
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "## Response Standard" in template, (
        "the '## Response Standard' section is gone from the template — sub-agents receive it as "
        "their system prompt and would silently lose it"
    )
    assert len(_rule_lines(template)) == 7, (
        "the template's Response Standard section no longer lists all seven rules"
    )
