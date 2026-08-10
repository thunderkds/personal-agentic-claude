#!/usr/bin/env python3
"""T066 — de-duplicate the agent startup read set, in the direction the channel allows.

The obvious de-duplication is wrong here. `general-agent-template.md` arrives in an agent's
context only if the agent chooses to open it; `.claude/agents/<name>.md` is auto-loaded by the
harness as the agent's system prompt and therefore *always* arrives. Consolidating shared content
into the template would move it out of a guaranteed channel into an optional one — the
"already covered must mean reaches-the-context" error (T041). So the direction is **into the role
guides**.

  AC1  — every shared section is present in all four role guides after the change
  AC2  — `common-infrastructure.md` gains Communication Protocol + Complexity (it had NEITHER)
  AC3  — the template no longer restates a section all four role guides carry
  AC4  — no startup sequence tells an agent to read the file that is already its system prompt
  AC5  — `CLAUDE.md` byte-identical to the pre-task baseline
  AC6  — the Karpathy table and the Search-Before-You-Build ladder stay reachable per role
  AC7  — per-role loaded size strictly lower than the baseline, for all four roles
  AC9  — no role guide loses its role-specific sections
  AC10 — `MANIFEST` byte-identical to the pre-task baseline

Sections are matched by **content probes**, not by heading name. The guide's edge-case checklist
warns that a shared heading can carry materially different bodies across roles; a heading-name
match would call two different things "the same section" and pass on a file that says nothing.

Run with: python3 -m pytest .claude/hooks/tests/test_agent_guide_dedup.py -v
"""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

# The pre-task branch tip (parent of T066's own Stage 2 guide commit; the last commit before
# this task touched anything). AC5/AC10 are "unchanged vs HEAD" questions, and `HEAD` moves with
# every commit this task makes — pinning the ref is what keeps them answerable after merge.
# (Contrast T065's AC12, which pinned a *count* captured at review time and then forbade the
# thing it was guarding from ever changing again. A baseline ref dates the comparison; a
# baseline count freezes the world.)
BASELINE_REF = "8fc4dd2"

# T069's own pre-implementation tip (the Stage 2 guide commit + the BEFORE capture), not T066's.
# Same reasoning as above: a baseline *ref* dates the comparison; a baseline *count* freezes it.
T069_BASELINE_REF = "8d6d56b"

TEMPLATE = ".claude/agents/general-agent-template.md"
ROLE_GUIDES = {
    "c-infra": ".claude/agents/common-infrastructure.md",
    "backend": ".claude/agents/backend.md",
    "frontend": ".claude/agents/frontend.md",
    "qa": ".claude/agents/qa.md",
}
ALL_AGENT_FILES = [TEMPLATE, *ROLE_GUIDES.values()]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def read_at(rel: str, ref: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{rel}"],
        check=True, capture_output=True,
    ).stdout


def headings(text: str) -> list[str]:
    return re.findall(r"^##\s+(.+?)\s*$", text, re.M)


# --------------------------------------------------------------------------
# Shared-section probes. Each entry is (label, [substrings that must ALL appear]).
# These are the four sections the TASK_GUIDE measured as duplicated between the
# template and the role guides.
# --------------------------------------------------------------------------
STARTUP_PROBES = [
    "PROJECT_SPEC.md",
    "memory/MEMORY.md",
    "tasks/TASK_GUIDE_Txxx.md",
    "memory/codebase-map.md",
    "stop and notify the Supervisor",
]
COMMUNICATION_PROBES = [
    "## Communication Protocol",
    "Task ID",
    "Status:",
    "Changed files:",
    "ready for review",
]
COMPLEXITY_PROBES = ["C0", "C1", "C2", "C3", "hub", "escalate and pause"]
SKILLS_PROBES = ['Skill({ skill: "code-review" })', 'Skill({ skill: "verify" })']

SHARED_SECTIONS = {
    "Mandatory Startup Sequence": STARTUP_PROBES,
    "Communication Protocol": COMMUNICATION_PROBES,
    "Complexity guidance": COMPLEXITY_PROBES,
    "Available Skills": SKILLS_PROBES,
}


# --------------------------------------------------------------------------
# Anti-vacuity guard. Every assertion below reads a file by path; a mistyped or
# vacated path would make the whole module inspect nothing.
# --------------------------------------------------------------------------
def test_every_agent_file_exists():
    missing = [rel for rel in ALL_AGENT_FILES if not (ROOT / rel).is_file()]
    assert not missing, f"agent file(s) missing, so this module inspects nothing: {missing}"


# --------------------------------------------------------------------------
# AC1 / AC2 — the guards. Written before any deletion: they are what makes every
# later removal from the template safe.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
@pytest.mark.parametrize("section", sorted(SHARED_SECTIONS))
def test_ac1_every_shared_section_is_present_in_every_role_guide(role, section):
    text = read(ROLE_GUIDES[role])
    absent = [p for p in SHARED_SECTIONS[section] if p not in text]
    assert not absent, (
        f"{ROLE_GUIDES[role]} does not carry {section!r} — missing probe(s) {absent}. "
        f"The role guide is the guaranteed channel (it is the auto-loaded system prompt); "
        f"nothing may be removed from the template unless all four role guides carry it."
    )


def test_ac2_common_infrastructure_gained_communication_protocol_and_complexity():
    """The trap. `common-infrastructure.md` had 0 chars of both and relied entirely on the
    template. The first deletion from the template silently strips both from every c-infra
    spawn — the agent type this project uses most."""
    text = read(ROLE_GUIDES["c-infra"])
    for section in ("Communication Protocol", "Complexity guidance"):
        absent = [p for p in SHARED_SECTIONS[section] if p not in text]
        assert not absent, f"c-infra still lacks {section!r}: missing {absent}"


# --------------------------------------------------------------------------
# AC3 — the template no longer restates what all four role guides carry.
# --------------------------------------------------------------------------
def test_ac3_template_does_not_restate_any_fully_shared_section():
    template = read(TEMPLATE)
    tmpl_headings = headings(template)
    banned = [
        "Mandatory Startup Sequence (Every Agent, Every Task)",
        "Complexity Levels — How Much Process to Apply",
        "Available Skills (Callable by Any Agent)",
        "Communication Protocol",
    ]
    still_there = [h for h in tmpl_headings if h in banned]
    assert not still_there, (
        f"the template still carries section(s) every role guide now has: {still_there}"
    )
    # Heading removal alone is not the criterion — the *body* must be gone too.
    assert "| **C0** Trivial" not in template, "the C0–C3 matrix body is still in the template"
    assert "Blockers / notes:" not in template, "the report-format block is still in the template"
    assert 'Skill({ skill: "code-review" })' not in template, (
        "the skills table is still in the template"
    )


# --------------------------------------------------------------------------
# AC4 — do not tell an agent to read its own system prompt.
# --------------------------------------------------------------------------
def test_ac4_no_guide_tells_an_agent_to_re_read_its_own_system_prompt():
    offenders = []
    for role, rel in ROLE_GUIDES.items():
        for lineno, line in enumerate(read(rel).splitlines(), start=1):
            if re.match(r"^\s*\d+\.", line) and re.search(
                r"[Rr]ead this file|[Rr]ead the relevant guide in `\.claude/agents/`", line
            ):
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    for lineno, line in enumerate(read(TEMPLATE).splitlines(), start=1):
        if "Read the relevant guide in `.claude/agents/` for your role" in line:
            offenders.append(f"{TEMPLATE}:{lineno}: {line.strip()}")
    assert not offenders, (
        "a startup step still instructs a re-read of the auto-loaded role guide:\n  "
        + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------
# AC5 / AC10 — file-wide negatives.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", ["CLAUDE.md", "MANIFEST"])
def test_ac5_ac10_out_of_scope_files_are_byte_identical_to_the_baseline(rel):
    assert (ROOT / rel).read_bytes() == read_at(rel, BASELINE_REF), (
        f"{rel} changed. CLAUDE.md never reaches a sub-agent at all, so its overlap with the "
        f"agent guides is CROSS-context redundancy and must not be collapsed; MANIFEST already "
        f"deploys `.claude/agents` as a directory entry."
    )


# --------------------------------------------------------------------------
# AC6 — T041's fix must survive, per role, in whatever that role actually loads.
# --------------------------------------------------------------------------
KARPATHY_PROBES = [
    "## Karpathy Engineering Principles (Compact)",
    "Think Before Coding",
    "Simplicity First",
    "Surgical Changes",
    "Goal-Driven Execution",
]
LADDER_PROBES = [
    "## Search Before You Build",
    "Does this need to exist at all?",
    "Is it already in this codebase?",
    "Does the stdlib already do this?",
    "native platform/framework feature",
    "already-installed dependency",
    "Can it be one line?",
    "write the minimum working code",
]


def reachable_text(role: str) -> tuple[str, list[str]]:
    """Everything a role's context can contain: its auto-loaded guide, plus every
    `.claude/agents/*.md` that guide instructs it to read."""
    rel = ROLE_GUIDES[role]
    guide = read(rel)
    files = [rel]
    for ref in sorted(set(re.findall(r"\.claude/agents/[a-z-]+\.md", guide))):
        if ref != rel and (ROOT / ref).is_file():
            files.append(ref)
    return "\n".join(read(f) for f in files), files


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac6_karpathy_table_is_reachable_directly_from_the_role_guide(role):
    """T069 tightens T066's AC6 for the Karpathy half.

    "Reachable" used to mean "in the guide, or in any agent file the guide *tells* the agent to
    read". For a **Permanent Rule** that is too weak: the template arrives only if the agent opens
    it, and the event trace showed 9 `Read` records on it across 66 task buckets. So for the
    Karpathy table, reachable must mean the guaranteed channel — the auto-loaded role guide
    itself, with no second hop.
    """
    guide = read(ROLE_GUIDES[role])
    missing = [p for p in KARPATHY_PROBES if p not in guide]
    assert not missing, (
        f"the Karpathy table is not in {ROLE_GUIDES[role]} itself; missing: {missing}. "
        f"It must reach {role} through the auto-loaded system prompt, not through an optional "
        f"read of the template."
    )


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac6_ladder_stays_reachable_from_every_role(role):
    """The advisory half keeps the weaker, second-hop definition on purpose (T069 AC7)."""
    text, files = reachable_text(role)
    assert len(files) > 1, (
        f"{role}'s guide references no other agent file, so this assertion could only ever "
        f"inspect the guide itself — that is the vacuous case, not a pass."
    )
    missing = [p for p in LADDER_PROBES if p not in text]
    assert not missing, (
        f"T041's ladder is no longer reachable from {role}'s context (files: {files}); "
        f"missing: {missing}"
    )


# --------------------------------------------------------------------------
# AC7 — measured, not asserted.
# --------------------------------------------------------------------------
def loaded_chars(role: str) -> int:
    return len(read(ROLE_GUIDES[role])) + len(read(TEMPLATE))


def baseline_loaded_chars(role: str) -> int:
    # `.decode()` is load-bearing: these files are full of em dashes and `≤`, so a byte count
    # runs ~4% above the character count. Comparing bytes-before against chars-after made AC7
    # pass while the files were still untouched — a saving conjured entirely out of UTF-8.
    return len(read_at(ROLE_GUIDES[role], BASELINE_REF).decode("utf-8")) + len(
        read_at(TEMPLATE, BASELINE_REF).decode("utf-8")
    )


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline(role):
    before, after = baseline_loaded_chars(role), loaded_chars(role)
    assert after < before, (
        f"{role}: {before:,} -> {after:,} chars — not lower. Report the real number rather "
        f"than reframing the criterion."
    )


# --------------------------------------------------------------------------
# AC9 — role-specific content is not collateral damage.
# --------------------------------------------------------------------------
ROLE_SPECIFIC = {
    "c-infra": ["## Environment Health Checklist", "## Output Format", "## Responsibilities"],
    "backend": [
        "## Scope boundaries (who owns what)",
        "## Appendix — Advanced / distributed patterns (decision-gated)",
        "## The three pillars (your gates)",
    ],
    "frontend": [
        "## Scope boundaries (who owns what)",
        "## Appendix — Advanced UI patterns (decision-gated)",
        "## The three pillars (your gates)",
    ],
    "qa": [
        "## The independence rule (why this role exists)",
        "## Scope boundaries (who owns what)",
        "## Evaluation checklist (apply what the task needs)",
    ],
}


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac9_role_specific_sections_survive(role):
    text = read(ROLE_GUIDES[role])
    missing = [s for s in ROLE_SPECIFIC[role] if s not in text]
    assert not missing, f"{role} lost role-specific section(s): {missing}"


def test_ac9_decision_gated_appendices_stay_below_the_body():
    """An Appendix is decision-gated and must not be promoted into the always-loaded body."""
    for role in ("backend", "frontend"):
        text = read(ROLE_GUIDES[role])
        idx = text.index("## Appendix")
        assert "**not defaults.**" in text[idx:], f"{role}'s appendix lost its gating sentence"
        assert text[idx:].count("## ") == 1, f"{role} has content after the appendix"


# ==========================================================================
# T069 — move the Karpathy table into the guaranteed channel.
#
# T066 consolidated *role-shaped* guidance into the role guides. The Karpathy table is not
# role-shaped: `CLAUDE.md` calls it "mandatory for the Supervisor and all sub-agents", which
# makes reaching it through an optional read the defect. It moves into all four role guides and
# out of the template. The Search-Before-You-Build ladder is advisory and does NOT move.
#
#   AC1 — the table is present, verbatim, in all four role guides
#   AC2 — the table is gone from the template (heading, principle names, operational commands)
#   AC5 — `craft-agent` emits the table in newly generated role guides
#   AC7 — the ladder is byte-identical in the template and absent from every role guide
#   AC9 — per-role pair size, reported not asserted
# ==========================================================================

# The single source these four assertions compare against, so they cannot drift from each
# other. Deliberately a literal in the test rather than an extraction from one of the files
# under test: extracting it from a role guide would make "all four match" trivially true against
# whichever file happened to be the source.
KARPATHY_TABLE = """## Karpathy Engineering Principles (Compact)

| Principle | Operational Command |
|---|---|
| Think Before Coding | Ask vs. Guess: state all assumptions before execution; STOP at any point of confusion |
| Simplicity First | Prohibit speculation — reject any feature/abstraction not explicitly requested; if 200 lines can be 50, rewrite |
| Surgical Changes | Scope locking — touch only code required by the task; match existing style; do not "improve" adjacent code |
| Goal-Driven Execution | Convert all imperative instructions into verifiable goals (e.g. "fix the bug" -> "write a failing test, then make it pass") |"""

# The four operational commands, byte-identical to the strings `scripts/test-agent-template.sh`
# pins with `grep -qF`. AC2 is a file-wide negative over these, not just over the heading:
# T058's lesson is that a retired token outlives the one occurrence an AC table enumerates.
OPERATIONAL_COMMANDS = [
    "Ask vs. Guess",
    "Prohibit speculation",
    "Scope locking",
    "Convert all imperative instructions",
]


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_t069_ac1_karpathy_table_is_verbatim_in_every_role_guide(role):
    text = read(ROLE_GUIDES[role])
    assert KARPATHY_TABLE in text, (
        f"{ROLE_GUIDES[role]} does not carry the Karpathy table verbatim. The role guide is the "
        f"channel the harness guarantees (it is the auto-loaded system prompt); a Permanent Rule "
        f"must arrive there, not one optional read away in the template."
    )


def test_t069_ac2_template_no_longer_carries_the_karpathy_table():
    template = read(TEMPLATE)
    assert "## Karpathy Engineering Principles (Compact)" not in template, (
        "the Karpathy H2 is still in the template"
    )
    leftovers = [c for c in OPERATIONAL_COMMANDS if c in template]
    assert not leftovers, (
        f"the template still carries operational-command string(s) {leftovers}. Removing the "
        f"heading is not the criterion — the body must be gone too."
    )


def test_t069_ac2_removal_happened_only_after_every_role_guide_had_it():
    """The order invariant, stated as a property of the tree rather than of the history.

    The failure mode this guards is an intermediate state in which the table exists in neither
    location: for as long as that state ships, every spawn loses a Permanent Rule. Equivalent to
    `test_ac1_...`'s docstring rule at line 119, specialised to the section T069 moves.
    """
    present = [r for r in ROLE_GUIDES if KARPATHY_TABLE in read(ROLE_GUIDES[r])]
    in_template = "## Karpathy Engineering Principles (Compact)" in read(TEMPLATE)
    assert present or in_template, (
        "the Karpathy table exists in NEITHER the template nor any role guide — no context "
        "receives it at all. This is strictly worse than the defect T069 set out to fix."
    )
    if not in_template:
        assert sorted(present) == sorted(ROLE_GUIDES), (
            f"the table was removed from the template while only {sorted(present)} carry it; "
            f"missing: {sorted(set(ROLE_GUIDES) - set(present))}"
        )


def test_t069_ac5_craft_agent_emits_the_table_in_generated_role_guides():
    skill = read(".claude/skills/craft-agent/SKILL.md")
    assert "## Karpathy Engineering Principles (Compact)" in skill, (
        "craft-agent does not name the Karpathy table, so a role it generates is born without a "
        "Permanent Rule — it can no longer inherit one from the template (T066 edge case #6)"
    )
    # Both halves, because they are separately deletable and each alone free-passes the other.
    # A control that removed the drafting bullet left this test green off the skeleton alone.
    assert "copied VERBATIM from `backend.md`" in skill, (
        "craft-agent's drafting checklist no longer tells the drafter to copy the table verbatim; "
        "an 'adapt it to the role' instruction would let a generated guide reword a Permanent Rule"
    )
    assert "Carries the ## Karpathy Engineering Principles (Compact)" in skill, (
        "the emitted draft skeleton no longer declares that the generated guide carries the table"
    )
    assert "Karpathy Principles / Search-Before-You-Build from" not in skill, (
        "the emitted draft skeleton still claims the Karpathy principles are INHERITED from "
        "general-agent-template.md — the template no longer has them"
    )


# --------------------------------------------------------------------------
# AC7 — the advisory half does not move. Pinned positively (byte-identical in the template)
# and negatively (absent from every role guide).
# --------------------------------------------------------------------------
def ladder_section(text: str) -> str:
    start = text.index("## Search Before You Build")
    end = text.index("\n---\n", start)
    return text[start:end].rstrip("\n")


def test_t069_ac7_ladder_is_byte_identical_to_the_baseline():
    # Both sides are `str`. T066's AC7 compared `git show` BYTES against `read_text` CHARS and
    # passed while the files were untouched — these guides are dense with `—`/`≤`, so the byte
    # side ran ~4% high and manufactured a saving out of UTF-8. One reader, both sides.
    now = ladder_section(read(TEMPLATE))
    base = ladder_section(read_at(TEMPLATE, BASELINE_REF).decode("utf-8"))
    assert now == base, (
        "the Search-Before-You-Build ladder changed. T069 moves the Karpathy table only; the "
        "ladder is advisory, stays in the template, and is pinned byte-identical."
    )
    assert len(re.findall(r"^\d+\.", now, re.M)) == 7, "the ladder lost or gained a rung"


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_t069_ac7_ladder_is_absent_from_every_role_guide(role):
    text = read(ROLE_GUIDES[role])
    assert "## Search Before You Build" not in text, (
        f"{ROLE_GUIDES[role]} inlined the ladder. Only the Karpathy table moves; inlining both "
        f"sections costs c-infra +1,187 chars per spawn and is net worse than before T066."
    )


# --------------------------------------------------------------------------
# AC9 — measurement, reported not asserted.
#
# A pinned number here would be T065's AC12 again: a scope guard committed as an invariant,
# correct during review and a blocker on the next legitimate edit. The assertion is only the
# direction the guide claims (no *increase*); the numbers themselves are printed.
# --------------------------------------------------------------------------
def pair_chars(role: str, ref: str | None = None) -> int:
    if ref is None:
        return len(read(ROLE_GUIDES[role])) + len(read(TEMPLATE))
    return len(read_at(ROLE_GUIDES[role], ref).decode("utf-8")) + len(
        read_at(TEMPLATE, ref).decode("utf-8")
    )


def test_t069_ac9_report_per_role_pair_size(capsys):
    with capsys.disabled():
        print("\n  role      | before | after  | delta")
        print("  ----------|--------|--------|------")
        for role in sorted(ROLE_GUIDES):
            before, after = pair_chars(role, T069_BASELINE_REF), pair_chars(role)
            print(f"  {role:<10}| {before:>6,} | {after:>6,} | {after - before:+,}")
    # Reporting, with ONE assertion, and deliberately not `after <= before`: that would be a
    # scope guard committed as an invariant (T065 AC12) — correct today, and a blocker on the
    # first legitimate sentence anyone adds to the template afterwards.
    #
    # The substantive claim is that moving the table did not cost a *copy* of the table: the
    # guide gains one and the template loses one, so the pair moves by prose-sized amounts, not
    # by table-sized ones. That has a real failure mode — forget the removal and the delta is
    # +622 — while leaving future edits free.
    for role in sorted(ROLE_GUIDES):
        delta = pair_chars(role) - pair_chars(role, T069_BASELINE_REF)
        assert abs(delta) < len(KARPATHY_TABLE), (
            f"{role}: pair moved {delta:+,} chars, which is a whole copy of the "
            f"{len(KARPATHY_TABLE):,}-char table. Either the removal from the template did not "
            f"happen, or the table was added somewhere it should not be."
        )
