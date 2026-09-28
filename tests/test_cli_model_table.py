"""T136 — the spawn model is picked per CLI from the task's Complexity, never hard-coded
to Claude model names. Text-check drift guard, in the style of test_spawn_startup_reads.py.

  AC1 — templates/PROJECT_SPEC_template.md has a `## CLI Model Table` section right after
        `## Sub-Agent Team`, header row `CLI | Run command | C0 | C1 | C2 | C3`, a filled
        claude example row, and a placeholder row for another CLI.
  AC2 — this repo's PROJECT_SPEC.md has the same section: claude row filled, codex row
        present with empty model cells.
  AC3 — craft-spawn-prompt step 5 looks the model up in the table; no hard-coded
        C0→haiku-style map.
  AC4 — step 5 states: no row / empty cell → STOP and ask; never fall back to another CLI.
  AC5 — the skill's Output and Default Notification report `<cli> · <Cn> → <model>`; the
        string `[haiku/sonnet/opus]` is gone.
  AC6 — pipeline-stages.md Stage 1 item 2 asks per-CLI models per level; Stage 3 points at
        the table instead of a hard-coded map.
  AC7 — TASK_GUIDE_template.md Mandatory Startup item 5 no longer says to take a *model*
        from the role-guide matrix.
  AC8 — outside the excluded paths, no hard-coded C0-3→model map remains anywhere.
"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts)) as f:
        return f.read()


def test_ac1_project_spec_template_has_cli_model_table():
    tpl = _read("templates", "PROJECT_SPEC_template.md")
    assert "## Sub-Agent Team" in tpl
    assert "## CLI Model Table" in tpl
    after_team = tpl.split("## Sub-Agent Team", 1)[1]
    # The CLI Model Table heading must be the next `## ` section after Sub-Agent Team
    next_section_headings = re.findall(r"^## (.+)$", after_team, re.MULTILINE)
    assert next_section_headings[0] == "CLI Model Table"
    table_section = tpl.split("## CLI Model Table", 1)[1]
    assert "CLI | Run command | C0 | C1 | C2 | C3" in table_section
    assert "claude" in table_section.lower()
    # placeholder row for another CLI (e.g. codex)
    assert "codex" in table_section.lower() or "[cli]" in table_section.lower()


def test_ac2_project_spec_has_filled_claude_row_and_empty_codex_row():
    spec = _read("PROJECT_SPEC.md")
    assert "## CLI Model Table" in spec
    table_section = spec.split("## CLI Model Table", 1)[1].split("\n---", 1)[0]
    lines = [l for l in table_section.splitlines() if l.strip().startswith("|")]
    claude_lines = [l for l in lines if l.strip().lower().startswith("| claude")]
    codex_lines = [l for l in lines if l.strip().lower().startswith("| codex")]
    assert claude_lines, "expected a claude row in PROJECT_SPEC.md's CLI Model Table"
    assert codex_lines, "expected a codex row in PROJECT_SPEC.md's CLI Model Table"
    claude_cells = [c.strip() for c in claude_lines[0].strip().strip("|").split("|")]
    assert all(cell for cell in claude_cells), "claude row must be fully filled"
    codex_cells = [c.strip() for c in codex_lines[0].strip().strip("|").split("|")]
    # CLI name + run command filled, but the four C0-C3 model cells stay empty
    codex_model_cells = codex_cells[2:6]
    assert all(cell == "" for cell in codex_model_cells), (
        "codex model cells must stay empty (no invented model names): got %r" % codex_model_cells
    )


def test_ac3_step5_looks_up_table_no_hardcoded_map():
    skill = _read("skills", "craft-spawn-prompt", "SKILL.md")
    step5 = skill.split("#### 5.", 1)[1].split("#### 6.", 1)[0]
    assert "CLI Model Table" in step5
    assert not re.search(r"C0\s*→\s*haiku", step5)


def test_ac4_step5_stops_and_asks_when_no_row_or_empty_cell():
    skill = _read("skills", "craft-spawn-prompt", "SKILL.md")
    step5 = skill.split("#### 5.", 1)[1].split("#### 6.", 1)[0]
    assert "stop" in step5.lower() and "ask" in step5.lower()
    assert "never fall back" in step5.lower() or "never falls back" in step5.lower()


def test_ac5_output_and_notification_report_cli_and_level():
    skill = _read("skills", "craft-spawn-prompt", "SKILL.md")
    assert "[haiku/sonnet/opus]" not in skill
    assert "<cli> · <Cn> → <model>" in skill


def test_ac6_pipeline_stages_points_at_table():
    doc = _read("docs", "claude-md", "pipeline-stages.md")
    stage1_item2 = doc.split("2. **Multi-CLI Authentication**", 1)[1].split("3. **", 1)[0]
    assert "CLI Model Table" in stage1_item2
    assert "C0" in stage1_item2 and "C3" in stage1_item2
    stage3 = doc.split("## Stage 3:", 1)[1].split("## Stage 4:", 1)[0]
    assert "CLI Model Table" in stage3
    assert not re.search(r"C0\s*→\s*haiku", stage3)


def test_ac7_task_guide_template_drops_model_from_startup_item5():
    tpl = _read("templates", "TASK_GUIDE_template.md")
    startup = tpl.split("## Mandatory Startup", 1)[1].split("---", 1)[0]
    item5 = [l for l in startup.splitlines() if l.strip().startswith("5.")][0]
    assert "model" not in item5.lower()


def test_ac10_step5_stops_and_asks_when_no_cli_named():
    skill = _read("skills", "craft-spawn-prompt", "SKILL.md")
    step5 = skill.split("#### 5.", 1)[1].split("#### 6.", 1)[0]
    assert "no cli named" in step5.lower()
    assert "stop" in step5.lower() and "ask" in step5.lower()
    assert "never assume" in step5.lower()
    assert "claude" in step5.lower().split("no cli named", 1)[1][:200]


def test_ac8_no_hardcoded_map_outside_excluded_paths():
    excluded_prefixes = (
        "tasks/", "memory/", "reports/", "docs/adr/", "docs/ddr/",
        "CLAUDE_LEGACY.md", "scripts/token_audit.py",
        ".claude/hooks/tests/test_token_audit_",
        "tests/test_cli_model_table.py",
    )
    # git grep with -E and a unicode arrow needs the literal; use a python-side regex instead
    # to avoid shell/locale issues with the arrow character.
    proc = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    files = proc.stdout.splitlines()
    pattern = re.compile(r"C[0-3] ?→ ?(haiku|sonnet|opus)")
    hits = []
    for path in files:
        if any(path.startswith(p) for p in excluded_prefixes):
            continue
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full):
            continue
        try:
            with open(full, encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(content):
            hits.append(path)
    assert hits == [], "hard-coded CLI model map found outside excluded paths: %r" % hits
