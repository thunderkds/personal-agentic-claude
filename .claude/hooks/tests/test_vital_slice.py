#!/usr/bin/env python3
"""T071 — the Vital Slice rule reaches the implementing agent, and cannot eat an AC.

DDR-0005: the rule extends Simplicity First in the **guaranteed channel** (the role guide, which
the harness auto-loads as the agent's system prompt), written per-role, with the number confined
to `CLAUDE.md`, and bounded so a "cut" can never mean cutting an Acceptance Criterion.

  AC1  — all four role guides carry `## Simplicity First (your defining constraint)`
  AC2  — the four sections are role-specific: no 12-word run is shared by any two
  AC3  — every section states AC-immunity in full (AC / pipeline stage / Hard-Stop Gate)
  AC4  — negative, file-wide: no percentage or `Pareto` in a role guide or the TASK_GUIDE template
  AC5  — `CLAUDE.md` names the heuristic exactly once, in the Simplicity First row
  AC6  — `KARPATHY_TABLE` is unmodified and its Simplicity First row is still verbatim in all four
  AC7  — `scripts/test-agent-template.sh` is unmodified and still exits 0
  AC8  — the `If 200 lines can be 50` occurrences survive
  AC9  — the template's `## Approach` gained `Vital slice` + `Cut list`, T046's shape
  AC11 — per-file line caps
  AC12 — no enforcement machinery: no non-test hook changed, no hook mentions the fields
  AC13 — no backfill: every pre-existing TASK_GUIDE is byte-identical

Anti-vacuity, per the 7 recorded incidents in `memory/learnings.md`:
  * every negative asserts its target files EXIST and carry the positive marker first, so a
    mistyped path fails loudly instead of passing for free;
  * the line cap counts with `splitlines()` on the raw text and never `rstrip`s — T067's P3 was a
    cap that caught non-blank padding and was blind to blank padding;
  * "unmodified" is checked against a pinned pre-task ref, never `HEAD` (a working-tree-vs-HEAD
    comparison stops asserting anything the moment the change is committed).

Run with: python3 -m pytest .claude/hooks/tests/test_vital_slice.py -v
"""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

# The branch base — the last commit before T071 touched anything. Pinned, not `HEAD`.
PRE_TASK_REF = "b69410c"

ROLE_GUIDES = {
    "backend": ".claude/agents/backend.md",
    "frontend": ".claude/agents/frontend.md",
    "c-infra": ".claude/agents/common-infrastructure.md",
    "qa": ".claude/agents/qa.md",
}
TASK_GUIDE_TEMPLATE = "templates/TASK_GUIDE_template.md"
SECTION_HEADING = "## Simplicity First (your defining constraint)"

# AC11 — as-of-this-task budgets (baseline +8 / +2 / +4), NOT a standing invariant. T065's
# recorded failure was a scope guard pinned as an invariant that then blocked what it guarded,
# so this is a ceiling with slack, never an equality, and it is expected to be retired or
# repointed after review.
LINE_CAPS = {
    ".claude/agents/backend.md": 145,
    ".claude/agents/frontend.md": 142,
    ".claude/agents/common-infrastructure.md": 137,
    ".claude/agents/qa.md": 129,
    "CLAUDE.md": 200,
    TASK_GUIDE_TEMPLATE: 197,
}

FORBIDDEN_NUMBERS = ["80/20", "80%", "20%", "Pareto"]
AC_IMMUNITY_TERMS = ["Acceptance Criterion", "pipeline stage", "Hard-Stop Gate"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def read_at(rel: str, ref: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{rel}"],
        check=True, capture_output=True,
    ).stdout


def section(text: str, heading: str) -> str:
    """The body of `heading` up to the next `## ` heading (or EOF)."""
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def added_section(role: str) -> str:
    """The Vital Slice text this task added to a role guide.

    For backend/frontend the section pre-existed, so the added text is what the section gained
    since PRE_TASK_REF; for c-infra/qa the whole section is new. Deriving it by diff rather than
    by hand is what keeps AC2 honest — it compares what T071 wrote, not the pre-existing prose
    T069/T066 already made role-specific.
    """
    now = section(read(ROLE_GUIDES[role]), SECTION_HEADING)
    before = section(read_at(ROLE_GUIDES[role], PRE_TASK_REF).decode("utf-8"), SECTION_HEADING)
    if before and now.startswith(before.rstrip() ) is False and before.strip() in now:
        return now.replace(before.strip(), "")
    return now if not before else now.replace(before.strip(), "")


def words(text: str) -> list[str]:
    return re.sub(r"[^\w\s-]", " ", text.lower()).split()


# --------------------------------------------------------------------------
# Anti-vacuity gate. Every assertion below reads a file by path.
# --------------------------------------------------------------------------
def test_every_inspected_file_exists():
    targets = list(ROLE_GUIDES.values()) + [TASK_GUIDE_TEMPLATE, "CLAUDE.md", "CLAUDE_LEGACY.md"]
    missing = [rel for rel in targets if not (ROOT / rel).is_file()]
    assert not missing, f"file(s) missing, so this module inspects nothing: {missing}"


# --------------------------------------------------------------------------
# AC1 / AC2 / AC3 — the rule, in the guaranteed channel, per role, bounded.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac1_every_role_guide_carries_the_simplicity_first_section(role):
    assert SECTION_HEADING in read(ROLE_GUIDES[role]), (
        f"{ROLE_GUIDES[role]} has no {SECTION_HEADING!r}. The role guide is the only channel the "
        f"harness guarantees reaches the implementing agent (DDR-0005 §1)."
    )


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac1_the_section_actually_states_the_vital_slice_rule(role):
    """Presence of a heading is not presence of a rule."""
    added = added_section(role).lower()
    assert "vital slice" in added, (
        f"{role}'s Simplicity First section does not name the vital slice; the heading alone "
        f"carries no instruction."
    )
    assert "cut list" in added, f"{role}'s section names no cut list — the artifact of the rule"


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac3_every_section_states_ac_immunity_in_full(role):
    added = added_section(role)
    missing = [t for t in AC_IMMUNITY_TERMS if t not in added]
    assert not missing, (
        f"{role}'s Vital Slice text omits {missing} from the AC-immunity sentence. This is the "
        f"load-bearing bound (DDR-0005 §4): a cut narrows implementation surface only. Without "
        f"all three clauses the rule supplies a vocabulary for descoping."
    )


def test_ac2_no_two_role_guides_share_a_twelve_word_run():
    added = {role: words(added_section(role)) for role in ROLE_GUIDES}
    for role, w in added.items():
        assert len(w) >= 12, (
            f"{role}'s added text is only {len(w)} words, so a 12-word overlap check on it is "
            f"vacuous. The user ruled the rule be written per-role, not that it be a stub."
        )
    runs = {role: {tuple(w[i:i + 12]) for i in range(len(w) - 11)} for role, w in added.items()}
    roles = sorted(runs)
    for i, a in enumerate(roles):
        for b in roles[i + 1:]:
            shared = runs[a] & runs[b]
            assert not shared, (
                f"{a} and {b} share a 12-word run, so the text was copy-pasted rather than "
                f"written per-role: {' '.join(sorted(shared)[0])!r}"
            )


# --------------------------------------------------------------------------
# AC4 / AC5 — the number is confined to CLAUDE.md.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", sorted(list(ROLE_GUIDES.values()) + [TASK_GUIDE_TEMPLATE]))
def test_ac4_no_operative_file_names_a_percentage(rel):
    text = read(rel)
    # Positive first: if this file does not carry the rule at all, the negative below is
    # inspecting the wrong file and would pass for free.
    assert "ital slice" in text, (
        f"{rel} does not mention the vital slice, so the percentage sweep over it proves nothing"
    )
    hits = [
        f"{rel}:{n}: {line.strip()[:100]}"
        for n, line in enumerate(text.splitlines(), 1)
        for bad in FORBIDDEN_NUMBERS
        if bad in line
    ]
    assert not hits, (
        "a file an agent acts from names a percentage. A number with no instrument behind it "
        "becomes a target — the failure recorded three times already (DDR-0005 §3):\n  "
        + "\n  ".join(hits)
    )


def test_ac5_claude_md_names_the_heuristic_exactly_once_and_labels_it():
    text = read("CLAUDE.md")
    assert text.count("80/20") == 1, (
        f"CLAUDE.md mentions 80/20 {text.count('80/20')} times; DDR-0005 §3 says exactly once"
    )
    row = [l for l in text.splitlines() if l.startswith("| Simplicity First")]
    assert len(row) == 1, f"expected one Simplicity First row in CLAUDE.md, found {len(row)}"
    assert "80/20" in row[0], "the single mention must live in the Simplicity First row"
    assert "heuristic" in row[0] and "never a target" in row[0], (
        "the mention must be explicitly labelled a heuristic and not a target"
    )
    missing = [t for t in AC_IMMUNITY_TERMS if t not in row[0]]
    assert not missing, f"CLAUDE.md's row states the rule without AC-immunity: missing {missing}"


def test_ac10_claude_legacy_received_the_matching_edit():
    row = [l for l in read("CLAUDE_LEGACY.md").splitlines() if l.startswith("| Simplicity First")]
    assert len(row) == 1, "expected one Simplicity First row in CLAUDE_LEGACY.md"
    assert "vital slice" in row[0].lower(), "CLAUDE_LEGACY.md drifted — the recorded sync policy"
    missing = [t for t in AC_IMMUNITY_TERMS if t not in row[0]]
    assert not missing, f"CLAUDE_LEGACY.md's row omits {missing} from AC-immunity"


# --------------------------------------------------------------------------
# AC6 / AC7 / AC8 — the design routes AROUND every pin; nothing pinned moved.
# --------------------------------------------------------------------------
DEDUP_TEST = ".claude/hooks/tests/test_agent_guide_dedup.py"


def karpathy_table(text: str) -> str:
    m = re.search(r'KARPATHY_TABLE = """(.*?)"""', text, re.S)
    assert m, "KARPATHY_TABLE literal not found — this assertion would inspect nothing"
    return m.group(1)


def test_ac6_karpathy_table_constant_is_byte_identical_to_the_pre_task_state():
    now = karpathy_table(read(DEDUP_TEST))
    before = karpathy_table(read_at(DEDUP_TEST, PRE_TASK_REF).decode("utf-8"))
    assert now == before, (
        "KARPATHY_TABLE changed. The whole T071 design is 'add prose AROUND the pin, never "
        "renegotiate the pin' — the recorded rule 'when a test pins prose, fix the prose around "
        "it, not the test', applied by placement."
    )


@pytest.mark.parametrize("role", sorted(ROLE_GUIDES))
def test_ac6_the_pinned_simplicity_row_still_matches_every_role_guide(role):
    row = [l for l in karpathy_table(read(DEDUP_TEST)).splitlines()
           if l.startswith("| Simplicity First")]
    assert len(row) == 1, "expected one Simplicity First row in the pinned table"
    assert row[0] in read(ROLE_GUIDES[role]), (
        f"{role}'s Karpathy table row no longer matches the pinned constant verbatim — the "
        f"addition was made INSIDE the table instead of beside it"
    )


def test_ac7_agent_template_script_is_unmodified_and_still_passes():
    rel = "scripts/test-agent-template.sh"
    assert (ROOT / rel).read_bytes() == read_at(rel, PRE_TASK_REF), f"{rel} was modified"
    proc = subprocess.run(["sh", str(ROOT / rel)], capture_output=True, text=True)
    assert proc.returncode == 0, f"{rel} failed:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"


def test_ac8_the_two_simplicity_first_compression_lines_survive():
    """`test_memory_channel_and_budget.py` excludes these lines BY CONTENT; deleting them would
    be an equally green way to pass that test, so assert they are still there."""
    needles = ["If 200 lines can be 50, rewrite", "If 200 lines can be 50, write 50"]
    found = {n: 0 for n in needles}
    for rel in list(ROLE_GUIDES.values()) + ["CLAUDE.md", ".claude/hooks/tests/test_memory_channel_and_budget.py"]:
        for n in needles:
            found[n] += read(rel).count(n)
    assert all(v >= 2 for v in found.values()), (
        f"the Simplicity First compression lines did not survive untouched: {found}"
    )
    rel = ".claude/hooks/tests/test_memory_channel_and_budget.py"
    assert (ROOT / rel).read_bytes() == read_at(rel, PRE_TASK_REF), f"{rel} was modified"


# --------------------------------------------------------------------------
# AC9 — the artifact, in T046's shape.
# --------------------------------------------------------------------------
def test_ac9_template_approach_gained_both_advisory_fields():
    approach = section(read(TASK_GUIDE_TEMPLATE), "## Approach")
    assert approach.strip(), "the ## Approach slice is empty — the slicer is vacuous"
    for field in ("**Vital slice**:", "**Cut list**:"):
        assert field in approach, f"{field} missing from the template's ## Approach section"
    # T046's shape: a bold field name with an `or None` escape hatch, so a task with no
    # meaningful surface can answer legitimately instead of leaving a blank.
    assert approach.count("`None") >= 2, (
        "both fields need an explicit `None` escape hatch, like Pattern reference — otherwise a "
        "single-AC task with no surface has no honest answer"
    )
    missing = [t for t in AC_IMMUNITY_TERMS if t not in approach]
    assert not missing, f"the template states the fields without AC-immunity: missing {missing}"


# --------------------------------------------------------------------------
# AC11 — line caps. NO rstrip anywhere: T067's cap was blind to blank padding.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", sorted(LINE_CAPS))
def test_ac11_line_cap(rel):
    lines = len(read(rel).splitlines())
    assert lines <= LINE_CAPS[rel], (
        f"{rel} is {lines} lines, over its {LINE_CAPS[rel]} budget. Tighten the prose — do not "
        f"raise the cap (DDR-0005 §6)."
    )


# --------------------------------------------------------------------------
# AC12 / AC13 — advisory by design, and no backfill.
# --------------------------------------------------------------------------
def test_ac12_no_enforcement_machinery_was_added():
    hooks = ROOT / ".claude" / "hooks"
    machinery = [p for p in hooks.rglob("*.py") if "tests" not in p.parts]
    assert machinery, "found no hook modules — this assertion would inspect nothing"
    changed, mentions = [], []
    for p in machinery:
        rel = str(p.relative_to(ROOT))
        if p.read_bytes() != read_at(rel, PRE_TASK_REF):
            changed.append(rel)
        if "Vital slice" in p.read_text(encoding="utf-8"):
            mentions.append(rel)
    assert not changed, f"non-test hook file(s) changed; T071 is advisory only: {changed}"
    assert not mentions, (
        f"a hook references the advisory field: {mentions}. DDR-0005 §5 explicitly refused the "
        f"gate; enforcement would contradict the T046 precedent this design follows."
    )


def test_ac13_no_pre_existing_task_guide_was_backfilled():
    listing = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "--name-only", PRE_TASK_REF, "tasks/"],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    guides = [g for g in listing
              if re.fullmatch(r"tasks/TASK_GUIDE_T0\d+\.md", g) and "T071" not in g]
    assert len(guides) > 20, f"expected the historical guide corpus, found {len(guides)}"
    drifted = [g for g in guides
               if not (ROOT / g).is_file() or (ROOT / g).read_bytes() != read_at(g, PRE_TASK_REF)]
    assert not drifted, (
        f"{len(drifted)} pre-existing TASK_GUIDE(s) changed: {drifted[:5]}. T064's precedent is "
        f"fallback, not migration — the historical record stays byte-identical."
    )
