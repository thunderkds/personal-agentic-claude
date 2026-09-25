"""T125 — `memory_slice.py`: the spawn prompt carries the MEMORY.md lines a task touches.

The script ships with the skill that runs it (`skills/craft-spawn-prompt/scripts/`), not
under repo-only `scripts/`: `skills` is in MANIFEST, `scripts` is not, and a downstream
install that got element 4 and the hook warning without the script could never satisfy
either (user decision at Stage 3, recorded in TASK_REVIEW_T125.md).

  SC1 — fixture guide + fixture MEMORY: exactly the 3 lines, under their headings, in
        order, inside markers, header `3 of 23`. Hand-written expectation.
  SC2 — 60 matching lines: within 30 lines / 4,000 chars, dropped count right,
        highest-hit lines kept (line cap and char cap each exercised).
  SC3 — no tables / no matches: markers + "no memory lines matched".
  SC4 — the real T124 guide against the real MEMORY.md: exit 0, within the caps.
  SC6 — the five AC6 docs state one rule: slice in the prompt, full file on need.
  SC7 — the script never writes.
Edge cases from the guide's checklist follow SC7.

Run with: python3 -m pytest tests/test_memory_slice.py -v
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "craft-spawn-prompt" / "scripts" / "memory_slice.py"
FIXTURES = ROOT / "tests" / "fixtures" / "memory_slice"
MAX_LINES = 30
MAX_CHARS = 4000


def run_slice(guide: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(guide)],
        capture_output=True, text=True, timeout=30,
    )


def make_project(tmp_path: Path, task: str, guide: str, memory: str | None) -> Path:
    (tmp_path / "tasks").mkdir()
    guide_path = tmp_path / "tasks" / f"TASK_GUIDE_{task}.md"
    guide_path.write_text(guide, encoding="utf-8")
    if memory is not None:
        (tmp_path / "memory").mkdir()
        (tmp_path / "memory" / "MEMORY.md").write_text(memory, encoding="utf-8")
    return guide_path


def guide_with(files: list[str], depends: str = "None", task: str = "T950") -> str:
    rows = "\n".join(f"| `{f}` | Edit |" for f in files)
    return (
        f"# TASK_GUIDE — {task}: generated\n\n"
        f"**Depends on**: {depends}\n\n"
        "## Files to Change (Predicted)\n\n| File | Change |\n|------|--------|\n"
        f"{rows}\n\n"
        "## Files Must NOT Touch\n\n| File | Reason |\n|------|--------|\n"
    )


# --------------------------------------------------------------------------
# SC1 — the exact output, hand-written
# --------------------------------------------------------------------------
SC1_EXPECTED = """\
<!-- memory-slice:T901 -->
memory/MEMORY.md — 3 of 23 index lines matched on: scripts/validate.sh, validate.sh, T122
### Decisions
- [T122 merged: CI is green again](decisions.md) — red since 2026-09-22
### Patterns & Gotchas
- [A validator is a consumer of the format](learnings.md) — `scripts/validate.sh` read `!` lines as paths
- [validate.sh runs in CI](learnings.md) — a bare basename mention
<!-- /memory-slice -->
"""


def test_sc1_exactly_the_matching_lines_under_headings_inside_markers():
    result = run_slice(FIXTURES / "basic" / "tasks" / "TASK_GUIDE_T901.md")
    assert result.returncode == 0, result.stderr
    assert result.stdout == SC1_EXPECTED


def test_sc1_traps_are_really_in_the_fixture():
    """Anti-vacuity: the negatives above only mean something if the traps exist."""
    memory = (FIXTURES / "basic" / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    for trap in ("lib/validate.sh", "T1220", "T12 ", "validate.sh.bak", "my_validate.sh"):
        assert trap in memory, trap
    assert sum(1 for l in memory.splitlines() if l.startswith("- [")) == 23


# --------------------------------------------------------------------------
# SC2 — the cap
# --------------------------------------------------------------------------
def _sixty_matching(pad: str) -> tuple[str, dict[str, int]]:
    """10 lines with 3 key hits, 15 with 2, 35 with 1 — interleaved, so file order and
    hit rank disagree. Returns the MEMORY text and each line's hit count."""
    hits_of = {}
    lines = ["# MEMORY.md", "", "### Decisions"]
    for i in range(60):
        if i % 6 == 0:
            body, hits = "`scripts/validate.sh` and `harness-fetch.sh` after T122", 3
        elif i % 4 == 1:
            body, hits = "`scripts/validate.sh` and `harness-fetch.sh`", 2
        else:
            body, hits = "`scripts/validate.sh`", 1
        line = f"- [entry {i:02d}](decisions.md) — {body}{pad}"
        hits_of[line] = hits
        lines.append(line)
    lines.append("- [unrelated](decisions.md) — nothing here")
    return "\n".join(lines) + "\n", hits_of


@pytest.mark.parametrize("pad", ["", " " + "x" * 200], ids=["line-cap", "char-cap"])
def test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped(tmp_path, pad):
    memory, hits_of = _sixty_matching(pad)
    assert sum(1 for h in hits_of.values()) == 60
    guide = make_project(
        tmp_path, "T950",
        guide_with(["scripts/validate.sh", "lib/harness-fetch.sh"], depends="T122 — fixture"),
        memory,
    )
    result = run_slice(guide)
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert len(out.splitlines()) <= MAX_LINES, len(out.splitlines())
    assert len(out) <= MAX_CHARS, len(out)
    assert out.startswith("<!-- memory-slice:T950 -->\n")
    assert out.endswith("<!-- /memory-slice -->\n")

    kept = [l for l in out.splitlines() if l in hits_of]
    dropped = [l for l in hits_of if l not in kept]
    assert kept and dropped, "control failed: the cap must have bitten"
    assert f"60 of 61 index lines matched" in out
    assert f"{len(dropped)} dropped" in out
    assert min(hits_of[l] for l in kept) >= max(hits_of[l] for l in dropped)
    assert all(l in kept for l, h in hits_of.items() if h == 3)
    # Still printed in file order, not rank order.
    assert kept == [l for l in hits_of if l in kept]


# --------------------------------------------------------------------------
# SC3 / SC4
# --------------------------------------------------------------------------
def test_sc3_no_tables_no_matches_prints_markers_and_says_so():
    result = run_slice(FIXTURES / "nomatch" / "tasks" / "TASK_GUIDE_T902.md")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "<!-- memory-slice:T902 -->"
    assert lines[-1] == "<!-- /memory-slice -->"
    assert "no memory lines matched this task's files" in result.stdout
    assert "0 of 23 index lines" in result.stdout
    assert not any(l.startswith("- [") for l in lines)


def test_sc4_real_t124_guide_against_real_memory_runs_within_caps():
    result = run_slice(ROOT / "tasks" / "TASK_GUIDE_T124.md")
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("<!-- memory-slice:T124 -->\n")
    assert result.stdout.endswith("<!-- /memory-slice -->\n")
    assert len(result.stdout.splitlines()) <= MAX_LINES
    assert len(result.stdout) <= MAX_CHARS


# --------------------------------------------------------------------------
# SC6 — one rule, five places
# --------------------------------------------------------------------------
AC6_DOCS = [
    "agents/general-agent-template.md",
    "templates/TASK_GUIDE_template.md",
    "docs/claude-md/pipeline-stages.md",
    "docs/claude-md/memory-write-protocol.md",
    "CLAUDE.md",
]
FULL_READ = re.compile(r"`memory/MEMORY\.md`[^.\n]{0,40}\bin full\b(?P<rest>[^\n]{0,20})")


@pytest.mark.parametrize("rel", AC6_DOCS)
def test_sc6_doc_states_slice_in_prompt_and_full_file_on_need(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert "memory slice" in text or "memory-slice" in text, f"{rel}: no slice in the rule"
    assert "in full only if" in text, f"{rel}: no full-file-on-need condition"
    unconditional = [m.group(0) for m in FULL_READ.finditer(text)
                     if "only if" not in m.group("rest")]
    assert not unconditional, f"{rel}: unconditional full read: {unconditional}"


def test_sc6_the_old_unconditional_rules_are_gone():
    stale = {
        "templates/TASK_GUIDE_template.md": "2. Read `memory/MEMORY.md`\n",
        "docs/claude-md/pipeline-stages.md": "with an instruction to read it in full",
        "docs/claude-md/memory-write-protocol.md": "the agent opens it itself as a mandatory startup step",
        "skills/craft-spawn-prompt/SKILL.md": "with an instruction to read it in full",
    }
    for rel, phrase in stale.items():
        assert phrase not in (ROOT / rel).read_text(encoding="utf-8"), f"{rel}: {phrase!r}"


def test_ac4_element_4_runs_the_slice_and_carries_the_escape_hatch():
    skill = (ROOT / "skills" / "craft-spawn-prompt" / "SKILL.md").read_text(encoding="utf-8")
    row = next(l for l in skill.splitlines() if l.startswith("| 4 |"))
    assert "scripts/memory_slice.py" in row and "verbatim" in row
    assert ("Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill "
            "or decision the slice does not cover.") in skill
    preflight = skill.split("#### 4.")[1].split("#### 5.")[0]
    assert "<!-- memory-slice:" in preflight


# --------------------------------------------------------------------------
# SC7 — read-only
# --------------------------------------------------------------------------
def test_sc7_script_never_writes():
    src = SCRIPT.read_text(encoding="utf-8")
    forbidden = [r"open\([^)]*['\"][wax+]", r"\.write_text\(", r"\.write_bytes\(",
                 r"mkdir", r"unlink", r"os\.remove", r"os\.rename", r"os\.replace",
                 r"shutil", r"rmtree", r"subprocess"]
    hits = [p for p in forbidden if re.search(p, src)]
    assert not hits, hits
    assert re.search(r"^import|^from", src, re.M), "control failed: not a Python source"


# --------------------------------------------------------------------------
# Edge cases (guide checklist)
# --------------------------------------------------------------------------
def test_edge_glob_matches_the_prefix_before_the_glob(tmp_path):
    memory = ("### D\n- [hit](l.md) — tests/fixtures/transcripts/a.jsonl\n"
              "- [miss](l.md) — tests/fixtures/other/a.jsonl\n")
    guide = make_project(tmp_path, "T950", guide_with(["tests/fixtures/transcripts/**"]), memory)
    out = run_slice(guide).stdout
    assert "- [hit]" in out and "- [miss]" not in out
    assert "1 of 2 index lines matched on: tests/fixtures/transcripts/" in out


def test_edge_skill_md_needs_its_directory(tmp_path):
    memory = ("### D\n- [generic](l.md) — every SKILL.md has frontmatter\n"
              "- [named](l.md) — `craft-spawn-prompt` element 4\n"
              "- [full](l.md) — skills/craft-spawn-prompt/SKILL.md line 33\n")
    guide = make_project(tmp_path, "T950",
                         guide_with(["skills/craft-spawn-prompt/SKILL.md"]), memory)
    out = run_slice(guide).stdout
    assert "- [generic]" not in out
    assert "- [named]" in out and "- [full]" in out


def test_edge_a_line_matched_by_several_keys_appears_once(tmp_path):
    memory = "### D\n- [both](l.md) — `scripts/validate.sh`, validate.sh, T122\n"
    guide = make_project(tmp_path, "T950",
                         guide_with(["scripts/validate.sh"], depends="T122 — x"), memory)
    out = run_slice(guide).stdout
    assert out.count("- [both]") == 1
    assert "1 of 1 index lines" in out


def test_edge_missing_memory_md_prints_markers_and_exits_zero(tmp_path):
    guide = make_project(tmp_path, "T950", guide_with(["scripts/validate.sh"]), None)
    result = run_slice(guide)
    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "<!-- memory-slice:T950 -->"
    assert "MEMORY.md not found" in result.stdout
    assert result.stdout.endswith("<!-- /memory-slice -->\n")


def test_edge_bugfix_flavoured_guide_same_tables_same_behaviour(tmp_path):
    memory = "### D\n- [hit](l.md) — `scripts/validate.sh`\n- [miss](l.md) — nope\n"
    bugfix = guide_with(["scripts/validate.sh"]).replace(
        "**Depends on**", "### Mental Model\n\nConfirmed with the user.\n\n**Depends on**")
    guide = make_project(tmp_path, "T950", bugfix, memory)
    out = run_slice(guide).stdout
    assert "- [hit]" in out and "- [miss]" not in out


def test_edge_session_handoff_section_is_matched_like_any_other(tmp_path):
    memory = ("### ⚠️ Session handoff — read first\n"
              "- **T115 is Done** — a handoff bullet, not an index line\n"
              "- [handoff hit](l.md) — `scripts/validate.sh`\n"
              "- [handoff miss](l.md) — unrelated\n")
    guide = make_project(tmp_path, "T950", guide_with(["scripts/validate.sh"]), memory)
    out = run_slice(guide).stdout
    assert "### ⚠️ Session handoff — read first\n- [handoff hit]" in out
    assert "handoff miss" not in out and "T115 is Done" not in out
    assert "1 of 2 index lines" in out


def test_missing_guide_is_an_error(tmp_path):
    result = run_slice(tmp_path / "tasks" / "TASK_GUIDE_T950.md")
    assert result.returncode != 0
    assert "not found" in result.stderr
