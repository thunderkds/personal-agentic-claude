#!/usr/bin/env python3
"""T066 — de-duplicate the agent startup read set, in the direction the channel allows.

The obvious de-duplication is wrong here. `general-agent-template.md` arrives in an agent's
context only if the agent chooses to open it; `agents/<name>.md` is auto-loaded by the
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

import canon_paths

ROOT = Path(__file__).resolve().parents[3]

# The pre-task branch tip (parent of T066's own Stage 2 guide commit; the last commit before
# this task touched anything). AC5/AC10 are "unchanged vs HEAD" questions, and `HEAD` moves with
# every commit this task makes — pinning the ref is what keeps them answerable after merge.
# (Contrast T065's AC12, which pinned a *count* captured at review time and then forbade the
# thing it was guarding from ever changing again. A baseline ref dates the comparison; a
# baseline count freezes the world.)
BASELINE_REF = "8fc4dd2"

# REPOINTED by T090 (`8fc4dd2` -> `360fc36`) for MANIFEST only: T090 adds a `.cursor/rules` line so
# the new Cursor adapter (`.cursor/rules/agent-base.mdc`) deploys downstream, per DDR-0006. This is
# a legitimate, required change (AC10 in TASK_GUIDE_T090.md), not drift — `8fc4dd2` is now
# MANIFEST's own unfixed state and comparing against it is red by construction. `360fc36` is T090's
# MANIFEST edit commit. `BASELINE_REF` itself is left unchanged for CLAUDE.md's other AC5/AC7/AC9
# uses below, which T090 does not touch.
# REPOINTED AGAIN by T096 (`360fc36` -> `8f8cc47`): T096 relocates the canon to plain root, so
# MANIFEST's `.claude/agents` / `.claude/skills` entries become `agents` / `skills`. That is the
# task's whole point (AC9 in TASK_GUIDE_T096.md), not drift — `360fc36` is now MANIFEST's own
# unfixed state. `8f8cc47` is T096's MANIFEST edit commit. The pin's purpose is unchanged: MANIFEST
# still deploys agents as a directory entry and must not be collapsed into the agent guides.
# MANIFEST_BASELINE_REF retired by T097 — see
# test_ac5_ac10_manifest_still_deploys_agents_as_one_directory_entry below.

# T069's own pre-implementation tip (the Stage 2 guide commit + the BEFORE capture), not T066's.
# Same reasoning as above: a baseline *ref* dates the comparison; a baseline *count* freezes it.
T069_BASELINE_REF = "8d6d56b"

# T070's own edit commit — the first commit in which `CLAUDE.md:86` names the role guides instead
# of the template the matrix left in T066. It is the *new* fixed point for CLAUDE.md, exactly as
# `8fc4dd2` is for MANIFEST: the pre-T070 tip (`78d0f8f`) cannot serve, because comparing the fixed
# file against its own unfixed state is red by construction and would only be satisfiable by
# undoing AC1.
#
# The assertion shape is deliberately unchanged (`read_bytes() == read_at(rel, <ref>)`) and the
# parametrize entry is NOT removed. What AC5 protects — that CLAUDE.md's overlap with the agent
# guides is CROSS-context redundancy and must not be collapsed — is still true after T070 and must
# still be guarded. `MANIFEST` is untouched by T070 and stays on `BASELINE_REF`.
#
# REPOINTED AGAIN by T071 (`9f3f2e9` -> `c512ae9`), for the same reason and by the same rule: T071
# adds the Vital Slice sentence to CLAUDE.md's Simplicity First row, so `9f3f2e9` is now the file's
# own unfixed state and comparing against it is red by construction. `c512ae9` is T071's CLAUDE.md
# edit commit. Repointed, NOT deleted — the assertion body and the parametrize list are untouched,
# and T071's AC15 re-proves the pin still discriminates by mutating CLAUDE.md and observing RED.
#
# REPOINTED AGAIN by T082 (`c512ae9` -> `ebb2958`): T082 adds a Base Rule pointer bullet to
# CLAUDE.md's `## General Agent Template` Base Rules list (the untrusted-content trust boundary),
# so `c512ae9` is now the file's own unfixed state. `ebb2958` is T082's CLAUDE.md edit commit.
#
# REPOINTED AGAIN by T096 (`ebb2958` -> `8f8cc47`): T096 rewrites CLAUDE.md's `.claude/agents/` and
# `.claude/skills/` paths to the relocated canon and adds one line naming the symlinks, so
# `ebb2958` is now the file's own unfixed state. `8f8cc47` is T096's CLAUDE.md edit commit. The
# cross-context redundancy this pin protects is untouched — only path strings moved.
#
# REPOINTED AGAIN by T100 (`8f8cc47` -> `c87097e`): T100's AC1 replaces the false claim "the harness
# already keeps chat replies short and plain by default" with text matching observed behaviour and
# points at the shared `## Response Standard`, so `8f8cc47` is now the file's own unfixed state and
# comparing against it is red by construction. `c87097e` is T100's CLAUDE.md edit commit. Repointed,
# NOT deleted, and the assertion body is untouched: the replacement is line-for-line (CLAUDE.md
# stays at 200 lines, 13 sections), so nothing was collapsed into the agent guides.
#
# REPOINTED AGAIN by T103 (`c87097e` -> `b1da25a`): T100's pointer form did not bind the Supervisor
# (measured on the T101 session — see memory/learnings.md). T103's AC1 inlines the six Response
# Standard rules verbatim into CLAUDE.md's `## Supervisor Communication Style` section, so `c87097e`
# is now the file's own unfixed state and comparing against it is red by construction. `b1da25a` is
# T103's CLAUDE.md edit commit. Repointed, NOT deleted, assertion body untouched: CLAUDE.md stays at
# 200 lines and the six rules replace a pointer + tightened adjacent prose — nothing was collapsed
# into the agent guides, which T103 leaves byte-unchanged.
#
# REPOINTED AGAIN by T127 (`b1da25a` -> `998166d`): T127's AC1 adds the seventh Response Standard
# rule and one pointer line to CLAUDE.md, so `b1da25a` is now the file's own unfixed state. CLAUDE.md
# stays at its 200-line cap (the compact-advisor paragraph was tightened to make room). Repointed,
# NOT deleted, assertion body untouched; the agent guides gain only the same one rule line.
# Repointed once more at T127's Stage 4 (`998166d` -> `05bb7fe`): review restored the dropped
# "judgment call, not a rigid step/token trigger" clause in the same two lines (still 200 lines).
#
# REPOINTED AGAIN by T125 (`b1da25a` -> `2e5331e`): T125's AC6 rewrites the one `## Memory Write
# Protocol` line from "passed to every spawn as a **path the agent reads**" to a pasted memory slice
# plus a full read on need, so `b1da25a` is now the file's own unfixed state. `2e5331e` is T125's
# CLAUDE.md edit commit. Repointed, NOT deleted, assertion body untouched: one line replaced in
# place, CLAUDE.md stays at 200 lines, no other rule reworded, nothing collapsed into agent guides.
# Merged on `tokenization-refactor` (T127 + T125 both edit CLAUDE.md in disjoint lines): the pin
# moves to the merge commit that carries the combined file (set in the commit after the merge).
T070_BASELINE_REF = "MERGE_PENDING"

# T082's own edit commit (same commit as the repoint above). T082 adds a mandatory Base Rule bullet
# to `general-agent-template.md` too (the same untrusted-content pointer) — a legitimate, required
# change, not drift.
#
# Used by AC9 for ALL roles, and by AC7 for exactly ONE. The two guards are not in the same
# position and were wrongly repointed together in T082's first pass (corrected at Stage 4):
#
#   AC9  — the pair-drift bound was ALREADY at ~96% of its `len(KARPATHY_TABLE)` budget before
#          T082, so the shared +160 pushes all four roles over (+640..+760 vs `8d6d56b`). The
#          repoint is genuinely forced, and AC9's own comment below explicitly warns against
#          letting this guard fossilize. Repointing keeps it live.
#   AC7  — three of four roles still clear T066's floor strictly, with ~1,400 chars of headroom.
#          Only `c-infra` breaches. See `AC7_ROLE_BASELINE` below: pin the one, leave the three.
T082_BASELINE_REF = "ebb2958"

TEMPLATE = "agents/general-agent-template.md"
ROLE_GUIDES = {
    "c-infra": "agents/common-infrastructure.md",
    "backend": "agents/backend.md",
    "frontend": "agents/frontend.md",
    "qa": "agents/qa.md",
}
ALL_AGENT_FILES = [TEMPLATE, *ROLE_GUIDES.values()]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def read_at(rel: str, ref: str) -> bytes:
    return canon_paths.read_at(ROOT, rel, ref)


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
                r"[Rr]ead this file|[Rr]ead the relevant guide in `agents/`", line
            ):
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    for lineno, line in enumerate(read(TEMPLATE).splitlines(), start=1):
        if "Read the relevant guide in `agents/` for your role" in line:
            offenders.append(f"{TEMPLATE}:{lineno}: {line.strip()}")
    assert not offenders, (
        "a startup step still instructs a re-read of the auto-loaded role guide:\n  "
        + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------
# AC5 / AC10 — file-wide negatives.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel,ref", [("CLAUDE.md", T070_BASELINE_REF)])
def test_ac5_ac10_out_of_scope_files_are_byte_identical_to_the_baseline(rel, ref):
    assert (ROOT / rel).read_bytes() == read_at(rel, ref), (
        f"{rel} changed. CLAUDE.md never reaches a sub-agent at all, so its overlap with the "
        f"agent guides is CROSS-context redundancy and must not be collapsed."
    )


def test_ac5_ac10_manifest_still_deploys_agents_as_one_directory_entry():
    """MANIFEST is no longer pinned byte-identical to MANIFEST_BASELINE_REF.

    T097 deliberately extends MANIFEST with an optional per-harness destination
    column (`<path>  <harness>=<dest>`), which is inside that task's scope lock
    and mandated by DDR-0007. A byte-identity pin would forbid a change the
    project has since decided to make.

    What the original pin was actually protecting survives here, asserted
    directly: `agents` must remain ONE directory entry. The dedup work this
    guard belongs to must never expand it into per-file agent entries, and the
    new destination column must not be mistaken for a second path.
    """
    lines = [
        ln.split("#", 1)[0].strip()
        for ln in (ROOT / "MANIFEST").read_text(encoding="utf-8").splitlines()
    ]
    entries = [ln for ln in lines if ln]
    paths = [ln.split()[0] for ln in entries]

    assert paths.count("agents") == 1, (
        "MANIFEST must deploy `agents` as exactly one directory entry, not per-file"
    )
    assert not any(p.startswith("agents/") for p in paths), (
        f"MANIFEST gained per-file agent entries: {[p for p in paths if p.startswith('agents/')]}"
    )
    # Every trailing field must be a well-formed `<harness>=<dest>` pair, so a
    # stray second path can never be silently ignored by the base install.
    for entry in entries:
        for field in entry.split()[1:]:
            assert "=" in field and not field.startswith("="), (
                f"MANIFEST line {entry!r} has trailing field {field!r} that is not a "
                f"<harness>=<destination> pair"
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
    `agents/*.md` that guide instructs it to read."""
    rel = ROLE_GUIDES[role]
    guide = read(rel)
    files = [rel]
    for ref in sorted(set(re.findall(r"agents/[a-z-]+\.md", guide))):
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


# AC7 is a PER-ROLE floor, and only one role actually needed repointing at T082 (Stage 4 finding).
#
# T082 adds ~160 chars to the shared TEMPLATE, so it moves every role's pair by the same amount —
# but the roles do not sit the same distance above T066's floor. Measured against `8fc4dd2` with
# T082's changes in place:
#
#     backend               12,528 vs 13,928   -1,400   still strictly lower
#     frontend              12,177 vs 13,581   -1,404   still strictly lower
#     qa                    11,343 vs 12,748   -1,405   still strictly lower
#     common-infrastructure 10,327 vs 10,167     +160   breaches
#
# `common-infrastructure.md` is the smallest role guide, so the shared +160 tips only that pair
# over. T082's first pass repointed ALL FOUR to its own edit commit and relaxed `<` to `<=`, which
# threw away ~1,400 chars of live headroom on three roles to fix a breach on one — and made the
# assertion `x <= x` at the moment it landed, i.e. vacuous exactly when it was introduced. The
# commit message's claim that "the original T066 savings are preserved structurally" was true for
# the three roles that did not need the repoint and false for the one that forced it.
#
# So: keep T066's floor and strict `<` where they still hold, and pin only the role that genuinely
# breaches. A blanket repoint would have made the next role to breach invisible.
#
# REPOINTED by T100 for `c-infra` only, on exactly T082's reasoning and with its warning intact.
# T100 adds the shared `## Response Standard` (617 chars) to the TEMPLATE, so every pair moves by
# the same amount; measured against each role's current floor with T100 in place:
#
#     backend               13,145 vs 13,928 (T066)   -783   still strictly lower
#     frontend              12,794 vs 13,581 (T066)   -787   still strictly lower
#     qa                    11,960 vs 12,748 (T066)   -788   still strictly lower
#     common-infrastructure 10,944 vs 10,327 (T082)   +617   breaches
#
# Same shape as T082: the smallest role guide is the only one tipped over, so pin the one and leave
# the three on T066's floor with their remaining ~780 chars of live headroom. A blanket repoint
# would still hide the next role to breach. `c87097e` is T100's template edit commit.
T100_BASELINE_REF = "c87097e"

# REPOINTED by T127 for `c-infra` only: the seventh Response Standard rule adds 110 chars to the
# TEMPLATE (c-infra 10,944 -> 11,054, +110 vs its T100 floor). backend/frontend/qa keep T066's
# floor and strict `<`. `998166d` is T127's edit commit.
T127_BASELINE_REF = "998166d"

AC7_ROLE_BASELINE = {"c-infra": T127_BASELINE_REF}  # key must match ROLE_GUIDES above


def baseline_loaded_chars(role: str) -> int:
    # `.decode()` is load-bearing: these files are full of em dashes and `≤`, so a byte count
    # runs ~4% above the character count. Comparing bytes-before against chars-after made AC7
    # pass while the files were still untouched — a saving conjured entirely out of UTF-8.
    ref = AC7_ROLE_BASELINE.get(role, BASELINE_REF)
    return len(read_at(ROLE_GUIDES[role], ref).decode("utf-8")) + len(
        read_at(TEMPLATE, ref).decode("utf-8")
    )


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline(role):
    before, after = baseline_loaded_chars(role), loaded_chars(role)
    if role in AC7_ROLE_BASELINE:
        # Pinned to its own T082 floor, so `<=`: `<` would be red by construction against a
        # baseline that reads the same content. Still catches any further growth past this point.
        assert after <= before, (
            f"{role}: {before:,} -> {after:,} chars — grew past its T082 floor. Report the real "
            f"number rather than reframing the criterion."
        )
    else:
        # Unchanged from T066: still strictly lower, with ~1,400 chars of headroom.
        assert after < before, (
            f"{role}: {before:,} -> {after:,} chars — not lower than the T066 floor. Report the "
            f"real number rather than reframing the criterion."
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
    skill = read("skills/craft-agent/SKILL.md")
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
            before, after = pair_chars(role, T127_BASELINE_REF), pair_chars(role)
            print(f"  {role:<10}| {before:>6,} | {after:>6,} | {after - before:+,}")
    # Reporting, with ONE assertion, and deliberately not `after <= before`: that would be a
    # scope guard committed as an invariant (T065 AC12) — correct today, and a blocker on the
    # first legitimate sentence anyone adds to the template afterwards.
    #
    # The substantive claim is that moving the table did not cost a *copy* of the table: the
    # guide gains one and the template loses one, so the pair moves by prose-sized amounts, not
    # by table-sized ones. That has a real failure mode — forget the removal and the delta is
    # +622 — while leaving future edits free.
    #
    # Repointed T069_BASELINE_REF -> T082_BASELINE_REF for the same reason as AC7 above: T082 adds
    # a legitimate sentence to the template, and re-measuring drift from that new floor (rather
    # than from T069's tip) is what keeps this a live guard instead of a fossil.
    # Repointed again, T082 -> T127: the seventh Response Standard rule adds 110 chars to every pair
    # (backend +727 vs the 620-char budget), a legitimate one-line rule, not a copied table.
    for role in sorted(ROLE_GUIDES):
        delta = pair_chars(role) - pair_chars(role, T127_BASELINE_REF)
        assert abs(delta) < len(KARPATHY_TABLE), (
            f"{role}: pair moved {delta:+,} chars, which is a whole copy of the "
            f"{len(KARPATHY_TABLE):,}-char table. Either the removal from the template did not "
            f"happen, or the table was added somewhere it should not be."
        )


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_t069_role_guide_does_not_advertise_the_template_as_the_karpathy_source(role):
    """Stage 4 P2 fix, given its own assertion so it cannot silently regress.

    Every role guide's startup step 4 used to read "Read general-agent-template.md — Base Rules,
    the Karpathy Engineering Principles, and the Search-Before-You-Build ladder". After T069 that
    sentence is false, and it is the same defect class T069 exists to fix — a pointer naming a
    channel that no longer holds the content — living in the guaranteed channel itself.

    Asserted as a *relationship*, not a pinned sentence: the guide may describe the template
    however it likes, as long as it does not name the Karpathy principles as living there.
    """
    text = read(ROLE_GUIDES[role])
    start = text.index("general-agent-template.md")
    sentence = text[start : start + 220]
    assert "Karpathy Engineering\n   Principles, and" not in sentence, (
        f"{ROLE_GUIDES[role]} still tells the agent the Karpathy Principles are in the template"
    )
    assert not re.search(
        r"general-agent-template\.md`? — Base Rules, the Karpathy", text
    ), (
        f"{ROLE_GUIDES[role]}'s startup step 4 still advertises the template as the source of "
        f"the Karpathy principles; they are in this guide now"
    )
