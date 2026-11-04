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
# T200: `CLAUDE_LEGACY.md` gains the `settings-setup` skills-list line (CLAUDE_LEGACY.md sync policy),
# so its pin moves off BASE_REF to T200's edit commit. BASE_REF stays for CLAUDE.md (AC 1).
# T228: `CLAUDE_LEGACY.md` gains the `dotfiles` skills-list line; the pin moves to T228's merge commit (holds the T226 and T228 lines).
# T239: `CLAUDE_LEGACY.md` renames its stage names (Stage 1 step Agent team, Stage 0); the pin moves to T239's edit commit.
CLAUDE_LEGACY_REF = "8c381c20"

# AC 1 allowed edits (a) and (b): (base span, new span). Each span must hit exactly one base line.
REPLACED_SPANS = [
    ("# Claude Project Supervisor Guidelines", "# AGENTS.md — Project Supervisor Guidelines"),
    ("CLAUDE.md's Writing Principles", "AGENTS.md's Writing Principles"),
    # v2.2.0 release: the doctrine version label moves with the T178–T182 doctrine change.
    ("**Version:** 1.17", "**Version:** 1.18"),
    # T183: the base template moved out of agents/ (Claude Code registers every agents/*.md).
    ("`agents/general-agent-template.md`", "`templates/general-agent-template.md`"),
    # T178 (two tracks, `docs/claude-md/tracks.md`): Hard-Stop Gate 1 and the code-review
    # Permanent Rule are scoped to the extended track. Pinned exactly by `tests/test_tracks.py`.
    ("**No TASK_GUIDE = no work.** If the user",
     "**No TASK_GUIDE = no work.** This gate applies to the extended track. If the user"),
    ("implementation code directly.",
     "implementation code directly. On the minimal track the Supervisor writes the code itself, "
     "with no guide, and ends with a Decision record (`docs/claude-md/tracks.md`)."),
    ("Stage 4 (code-review) is mandatory for every task.",
     "Stage 4 (code-review) is mandatory for every extended-track task."),
    # T200: the Stage 1 skill `settings-setup` joins the stage index.
    ("1=`git-guardrails-claude-code`,`map-codebase` |",
     "1=`git-guardrails-claude-code`,`map-codebase`,`settings-setup` |"),
    # T226: the Stage 1 skill `companion-setup` joins the stage index.
    ("`map-codebase`,`settings-setup` |",
     "`map-codebase`,`settings-setup`,`companion-setup` |"),
    # T228: the optional `dotfiles` skill joins the cross-cutting list.
    ("`resolve-question` (a confused Supervisor",
     "`dotfiles` (shared agent config, optional), `resolve-question` (a confused Supervisor"),
    # T234: the role table gains a column with the plugin form of each agent name, and one
    # sentence says when to use it.
    ("`prompt` only needs the task pointer (Task ID + guide refs) -- do **not** re-paste the guide.",
     "`prompt` only needs the task pointer (Task ID + guide refs) -- do **not** re-paste the guide. "
     "In the Claude Code plugin, use the right-hand form: a bare name fails with `Agent type '...' not found`."),
    ("| Role | `subagent_type` | Definition |", "| Role | `subagent_type` | Definition | Plugin `subagent_type` |"),
    ("|---|---|---|", "|---|---|---|---|"),
    ("| `common-infrastructure` | `agents/common-infrastructure.md` |",
     "| `common-infrastructure` | `agents/common-infrastructure.md` | `easy-kit:common-infrastructure` |"),
    ("| `backend-developer` | `agents/backend.md` |",
     "| `backend-developer` | `agents/backend.md` | `easy-kit:backend-developer` |"),
    ("| `frontend-developer` | `agents/frontend.md` |",
     "| `frontend-developer` | `agents/frontend.md` | `easy-kit:frontend-developer` |"),
    ("| `qa-expert` | `agents/qa.md` |", "| `qa-expert` | `agents/qa.md` | `easy-kit:qa-expert` |"),
    # T239: the pipeline reads Stage 0 to Stage 5. Phase 0 becomes Stage 0 step Requirements, Stage 0.5 becomes
    # the Stage 0 steps Grilling and Direction, Stage 1.5 becomes the Stage 1 step Agent team. One line per
    # base line; nothing is added or collapsed. The base text below is the old wording, on purpose.
    ("run the 5-stage pipeline below", "run the Stage 0–5 pipeline below"),
    ("0.5=`brainstorming`,`ideate` |", "0=`brainstorming`,`ideate` |"),
    ("`companion-setup` | 1.5=`craft-agent` | 2=", "`companion-setup`,`craft-agent` | 2="),
    ("## Phase 0: Project Initiation & Context Gathering", "## Stage 0, step Requirements: Project Initiation & Context Gathering"),
    ("[`docs/claude-md/phase0-project-initiation.md`](docs/claude-md/phase0-project-initiation.md) for full Step 1 / Step 1.5 (Ambiguity Resolution Protocol) / Step 2 detail.",
     "[`docs/claude-md/stage0-define.md`](docs/claude-md/stage0-define.md) for full Initialization / Ambiguity Resolution Protocol / Project Context Document detail."),
    ("resolve ambiguity via forced choice (Step 1.5), then produce and confirm the Project Context Document + `PRD.md` (Step 2).",
     "resolve ambiguity via forced choice (Ambiguity Resolution Protocol), then produce and confirm the Project Context Document + `PRD.md`."),
    ('> "Context locked. PRD.md generated. Entering 5-Stage Agentic Pipeline. Initializing Stage 0.5: Requirement Grilling → Creative Brainstorming."',
     '> "Stage 0, step Requirements: context locked, PRD.md generated. Moving to step Grilling."'),
    ("## 5-Stage Agentic Pipeline", "## Stage 0–5 Agentic Pipeline"),
    ("full Stage 0.5–5 detail", "full Stage 0–5 detail"),
    ('- **Stage 0.5** (Requirement Grilling → Brainstorming): `Skill({ skill: "grill-with-docs", args: "mode=requirement" })` then `Skill({ skill: "brainstorming" })`. Runs after Phase 0, before Stage 1.',
     '- **Stage 0** (Define): three steps in order, each with its own stop, never merged: step Requirements (the section above; the user confirms the Project Context Document), step Grilling (`Skill({ skill: "grill-with-docs", args: "mode=requirement" })`; the PRD gate must pass), step Direction (`Skill({ skill: "brainstorming" })`; the user picks a direction). Must complete before Stage 1.'),
    # T245: the `ux-evaluate` skill joins the Stage 3 index.
    ("`craft-spawn-prompt`,`migration-safety` |", "`craft-spawn-prompt`,`migration-safety`,`ux-evaluate` |"),
    ("- **Stage 1** (Environment & Provider Setup): checklist", "- **Stage 1, step Environment** (Set up): checklist"),
    ('- **Stage 1.5** (Sub-Agent Architecture): design the sub-agent team; base team is always Common-Infrastructure/Backend/Frontend/QA; `Skill({ skill: "craft-agent" })` only if an uncovered role is needed.',
     '- **Stage 1, step Agent team** (Sub-Agent Architecture): design the sub-agent team; base team is always Common-Infrastructure/Backend/Frontend/QA; `Skill({ skill: "craft-agent" })` only if an uncovered role is needed. The user is asked to approve the team only when `craft-agent` proposes a role beyond the base team; with the base team alone, state it in one line and go on.'),
]
AC6_HEADING = re.compile(r"^## .*cannot enforce", re.IGNORECASE)
# T178: the one later section allowed outside the opening block and the AC 6 section. Its
# content is pinned by `tests/test_tracks.py` (<= 12 lines, the short rule, the pointer).
ADDED_SECTIONS = ("## Tracks",)


def _without_added_sections(lines: list[str]) -> list[str]:
    out, skipping = [], False
    for line in lines:
        if line.strip() in ADDED_SECTIONS:
            skipping = True
            continue
        if skipping and (line.startswith("## ") or line.strip() == "---"):
            skipping = False
        if not skipping:
            out.append(line)
    return out


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
    body = _without_added_sections(lines[: _ac6_start(lines)])
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
    paths = [ROOT / "README.md", ROOT / "site" / "index.html", ROOT / "site" / "docs.html", ROOT / "AGENTS.md",
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
    assert (ROOT / "CLAUDE_LEGACY.md").read_bytes() == _git_show("CLAUDE_LEGACY.md", CLAUDE_LEGACY_REF)


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
