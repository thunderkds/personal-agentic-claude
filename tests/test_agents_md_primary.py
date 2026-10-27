"""T173: `AGENTS.md` is the primary doctrine file; `CLAUDE.md` imports it.

AC 1  — `AGENTS.md` carries every non-blank line of `CLAUDE.md` at the branch base, in order;
        only the listed allowed edits differ.
AC 2  — `CLAUDE.md` is exactly `@AGENTS.md\\n`; `AGENTS.md` holds no bare `@path` import.
AC 6  — `AGENTS.md` keeps one short section naming what non-Claude CLIs cannot enforce.
AC 7  — the Cursor adapter names `AGENTS.md` as canonical (<= 60 lines); `AGENTS.md` <= 200 lines
        and <= 32768 bytes (Codex `project_doc_max_bytes` default).
AC 8  — `scripts/validate.sh` fails, naming the path, when `AGENTS.md` references a missing file.
AC 9  — no shipped text points at a doctrine section of `CLAUDE.md`.
AC 10 — `CLAUDE_LEGACY.md` is byte-identical to the branch base; T173 commits touch no
        historical record.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_MD = ROOT / "AGENTS.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
CURSOR_MDC = ROOT / ".cursor" / "rules" / "agent-base.mdc"

# T173's branch base: `main` + T170 merged in (TASK_GUIDE_T173 "Depends on"). `CLAUDE.md` at this
# commit is the doctrine T173 moves. Repoint `CLAUDE_LEGACY.md`'s pin when a later task edits it.
BASE_REF = "c573bbf"

# AC 1 allowed edits (a) and (b): (base span, new span). Each span must hit exactly one base line.
REPLACED_SPANS = [
    ("# Claude Project Supervisor Guidelines", "# AGENTS.md — Project Supervisor Guidelines"),
    ("CLAUDE.md's Writing Principles", "AGENTS.md's Writing Principles"),
    # T183: the base template moved out of agents/ (Claude Code registers every agents/*.md).
    ("`agents/general-agent-template.md`", "`templates/general-agent-template.md`"),
]
AC6_HEADING = re.compile(r"^## .*cannot enforce", re.IGNORECASE)


def _git_show(rel: str, ref: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{rel}"], check=True, capture_output=True
    ).stdout


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ac6_start(lines: list[str]) -> int:
    hits = [i for i, line in enumerate(lines) if AC6_HEADING.match(line)]
    assert len(hits) == 1, f"expected one '## ... cannot enforce' section in AGENTS.md, found {len(hits)}"
    return hits[0]


def _ac6_section() -> str:
    lines = _text(AGENTS_MD).splitlines()
    start = _ac6_start(lines)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end])


# ── AC 1 ──────────────────────────────────────────────────────────────────────
def test_ac1_agents_md_carries_every_base_claude_md_line_in_order():
    base = [l for l in _git_show("CLAUDE.md", BASE_REF).decode("utf-8").splitlines() if l.strip()]
    used = {old: 0 for old, _ in REPLACED_SPANS}
    expected = []
    for line in base:
        for old, new in REPLACED_SPANS:
            if old in line:
                line = line.replace(old, new)
                used[old] += 1
        expected.append(line)
    assert all(n == 1 for n in used.values()), f"each allowed edit must hit one base line: {used}"

    lines = _text(AGENTS_MD).splitlines()
    body = lines[: _ac6_start(lines)]
    # The AC 6 section is preceded by its own `---` separator; it is part of the addition.
    while body and body[-1].strip() in ("", "---"):
        body.pop()
    body = [l for l in body if l.strip()]

    first_rule = body.index("---") if "---" in body else len(body)
    extras, i = [], 0
    for n, line in enumerate(body):
        if i < len(expected) and line == expected[i]:
            i += 1
        else:
            extras.append((n, line))
    assert i == len(expected), f"base CLAUDE.md line missing or out of order in AGENTS.md: {expected[i]!r}"
    stray = [line for n, line in extras if n >= first_rule]
    assert not stray, f"AGENTS.md adds lines outside the opening block and the AC 6 section: {stray}"
    assert len(extras) <= 2, f"opening block adds more than 2 lines: {extras}"


def test_ac1_opening_names_agents_md_as_this_file():
    opening = _text(AGENTS_MD).split("\n---\n", 1)[0]
    assert opening.startswith("# AGENTS.md")
    assert "Codex" in opening and "Claude Code" in opening and "`CLAUDE.md`" in opening


# ── AC 2 ──────────────────────────────────────────────────────────────────────
def test_ac2_claude_md_is_only_the_import():
    assert CLAUDE_MD.read_bytes() == b"@AGENTS.md\n"
    assert not CLAUDE_MD.is_symlink()


def test_ac2_agents_md_holds_no_bare_import():
    text = re.sub(r"```.*?```", "", _text(AGENTS_MD), flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    bare = re.findall(r"(?<![\w`])@[A-Za-z0-9_~./-]+", text)
    assert not bare, f"AGENTS.md has a bare @path (an import, or a self-import loop): {bare}"


# ── AC 6 ──────────────────────────────────────────────────────────────────────
def test_ac6_short_section_names_what_non_claude_clis_cannot_enforce():
    section = _ac6_section()
    assert len(section.splitlines()) <= 10, "the non-Claude CLI section must stay short"
    low = section.lower()
    for term in ("hooks", "code-review", "security-review", "verify", "ship", "migration-safety",
                 "git-guardrails", ".codex/skills", "8 kb", "codex", "cursor"):
        assert term in low, f"AC 6 section is missing {term!r}"


# ── AC 7 ──────────────────────────────────────────────────────────────────────
def test_ac7_cursor_adapter_names_agents_md_as_canonical():
    text = _text(CURSOR_MDC)
    assert len(text.splitlines()) <= 60
    norm = re.sub(r"\s+", " ", text)
    assert "`AGENTS.md` and `agents/` remain canonical" in norm
    assert "CLAUDE.md" not in text, "the Cursor adapter still points at CLAUDE.md"


def test_ac7_agents_md_size_caps():
    assert len(_text(AGENTS_MD).splitlines()) <= 200
    assert len(AGENTS_MD.read_bytes()) <= 32768  # Codex project_doc_max_bytes default (32 KiB)


# ── AC 9 ──────────────────────────────────────────────────────────────────────
# A pointer into a one-line file looks live and is not (T085). These shapes send the reader to a
# doctrine section; a text about the file itself ("copies CLAUDE.md", "CLAUDE.md.bak-…") does not
# match them.
POINTER_PATTERNS = [
    re.compile(r"CLAUDE\.md`?['’]s\b"),
    re.compile(r"\b(?:[Ss]ee|in|from|of|per|to|with)\s+`?CLAUDE\.md\b(?!\.bak)"),
    re.compile(r"`?CLAUDE\.md`?\s+(?:\+|plus|and)\s+.{0,40}?\b(?:remain|stay)s?\s+"
               r"(?:the\s+one\s+)?(?:primary|canonical)"),
    re.compile(r"`?CLAUDE\.md`?\s+is\s+the\s+primary"),
]


def _shipped_texts():
    paths = [ROOT / "README.md", ROOT / "site" / "index.html", ROOT / "AGENTS.md",
             ROOT / "docs" / "MULTI_AGENT.md", CURSOR_MDC]
    for d in ("agents", "skills", "templates", "docs/claude-md"):
        paths += sorted(p for p in (ROOT / d).rglob("*") if p.is_file() and p.suffix in (".md", ".html"))
    for p in paths:
        yield p.relative_to(ROOT), _text(p)


def test_ac9_no_shipped_text_points_at_a_claude_md_section():
    hits = []
    for rel, text in _shipped_texts():
        norm = re.sub(r"\s+", " ", re.sub(r"</?code>", "`", text))
        for pat in POINTER_PATTERNS:
            for m in pat.finditer(norm):
                hits.append(f"{rel}: …{norm[max(0, m.start() - 40): m.end() + 30]}…")
    assert not hits, "doctrine-section pointer(s) still name CLAUDE.md:\n" + "\n".join(hits)


# ── AC 10 ─────────────────────────────────────────────────────────────────────
def test_ac10_claude_legacy_md_unchanged():
    assert (ROOT / "CLAUDE_LEGACY.md").read_bytes() == _git_show("CLAUDE_LEGACY.md", BASE_REF)


OUT_OF_SCOPE = ("CLAUDE_LEGACY.md", "docs/ddr/", "docs/adr/", "RUNBOOK.md", "BRAINSTORMING_LOG",
                "memory/event-trace/", ".claude/skills", ".claude/agents", "tasks/")
T173_OWN = ("tasks/TASK_GUIDE_T173.md", "tasks/TASK_REVIEW_T173.md")


def test_ac10_t173_commits_touch_no_historical_record():
    shas = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--no-merges", "--format=%H", "--grep=T173", f"{BASE_REF}..HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    touched = set()
    for sha in shas:
        out = subprocess.run(["git", "-C", str(ROOT), "show", "--name-only", "--format=", sha],
                             check=True, capture_output=True, text=True).stdout
        touched.update(p for p in out.splitlines() if p)
    bad = sorted(p for p in touched if p.startswith(OUT_OF_SCOPE) and p not in T173_OWN)
    assert not bad, f"T173 commits changed out-of-scope file(s): {bad}"


# ── AC 8 ──────────────────────────────────────────────────────────────────────
def _validate(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["sh", "scripts/validate.sh"], cwd=cwd, capture_output=True, text=True)


def test_ac8_validate_fails_when_agents_md_references_a_missing_path():
    missing = "docs/claude-md/pipeline-stages.md"
    assert f"`{missing}`" in _text(AGENTS_MD), "fixture path must be referenced in AGENTS.md"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(ROOT, copy, symlinks=True, ignore=shutil.ignore_patterns(".git"))

        control = _validate(copy)  # unmodified copy passes, so the failure below is not vacuous
        assert control.returncode == 0, control.stdout + control.stderr

        (copy / missing).unlink()
        result = _validate(copy)
        assert result.returncode != 0
        assert f"AGENTS.md references missing path: {missing}" in result.stdout + result.stderr
