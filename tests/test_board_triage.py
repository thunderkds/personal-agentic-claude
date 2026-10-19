"""T160 — `board_sync.py triage`, the wake triage lines, and the spawn gate's complete-guide block.

No network: the fake board stands in for Linear.

  AC1 — triage lists exactly my tasks lacking a complete guide, or changed since the last-session
        marker (`.board/triage_seen.json`, advanced by `triage --mark`, which `pull_moment.py wake`
        runs after a good pull)
  AC2 — others' tasks never appear
  AC3 — skills/wake/SKILL.md points to skills/wake/references/triage.md, which documents the flow
  AC4 — pre_agent_validate_guide.py blocks a spawn whose guide is incomplete, naming the sections;
        a crash in that check fails open
  AC5 — every repo guide whose task is not Done is complete; the known incomplete set is Done

Run with: python3 -m pytest tests/test_board_triage.py -q
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "board_sync.py"
HOOKS = ROOT / ".claude" / "hooks"
HOOK = HOOKS / "pre_agent_validate_guide.py"

sys.path.insert(0, str(HOOKS / "lib"))
from board.base import Task  # noqa: E402
from board.fake import FakeBoard  # noqa: E402
from guide_sections import REQUIRED_SECTIONS, missing_guide_sections  # noqa: E402

COMPLETE = """# TASK_GUIDE — ENG-2: done right

## Requirement (Pillar 1 — Adapt the requirement)

Retry 3 times.

### Requirement Fidelity Gate

- [x] ok

## Acceptance Criteria

| # | Criterion |
|---|---|
| 1 | retries |

## Evaluation & Acceptance

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_retry.py -q
```

### Evidence

> **Moved.**
"""


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sync():
    return load("board_sync_triage_under_test", SCRIPT)


def project(tmp_path, **config):
    (tmp_path / ".claude").mkdir()
    cfg = {"board": "fake", "fake_board": "x.json", "id_pattern": r"ENG-\d+", "me": "alice",
           **config}
    (tmp_path / ".claude" / "board.json").write_text(json.dumps(cfg))
    return tmp_path


def three_tasks():
    return [
        Task(id="ENG-1", title="dark mode", status="Todo", assignee="alice",
             description="make it dark"),
        Task(id="ENG-2", title="retry", status="Todo", priority="P1", assignee="alice",
             description=COMPLETE),
        Task(id="ENG-3", title="teammate", status="Todo", assignee="bob", description="one line"),
    ]


def triage(sync, monkeypatch, capsys, root, board, *flags):
    monkeypatch.setattr(sync, "make_board", lambda config, r: (board, None))
    code = sync.main(["triage", *flags], root=str(root))
    out = capsys.readouterr()
    return code, out.out.splitlines(), out.err


# --- AC1 / AC2 / Success Criterion 1 ---------------------------------------------------

def test_sc1_only_my_incomplete_task_is_listed(sync, monkeypatch, capsys, tmp_path):
    code, lines, _ = triage(sync, monkeypatch, capsys, project(tmp_path), FakeBoard(three_tasks()))
    assert code == 0
    assert lines == ["ENG-1 · untriaged · not planned (missing: Requirement, Acceptance Criteria, "
                     "Verification Command) · dark mode"]


def test_changed_since_marker_shows_once_marked(sync, monkeypatch, capsys, tmp_path):
    root, board = project(tmp_path), FakeBoard(three_tasks())
    triage(sync, monkeypatch, capsys, root, board, "--mark")
    assert (root / ".board" / "triage_seen.json").exists()
    board.get_task("ENG-2").description = COMPLETE + "\nOne more line.\n"
    _, lines, _ = triage(sync, monkeypatch, capsys, root, board)
    assert "ENG-2 · P1 · changed since last session · retry" in lines
    _, lines, _ = triage(sync, monkeypatch, capsys, root, board)     # no --mark: still shown
    assert any(l.startswith("ENG-2 ") for l in lines)
    triage(sync, monkeypatch, capsys, root, board, "--mark")
    _, lines, _ = triage(sync, monkeypatch, capsys, root, board)
    assert not any(l.startswith("ENG-2 ") for l in lines)
    assert any(l.startswith("ENG-1 ") for l in lines)                 # still not planned


def test_others_never_appear_even_when_changed(sync, monkeypatch, capsys, tmp_path):
    root, board = project(tmp_path), FakeBoard(three_tasks())
    triage(sync, monkeypatch, capsys, root, board, "--mark")
    board.get_task("ENG-3").description = "changed by bob"
    board.tasks.append(Task(id="ENG-4", title="new for carol", status="Todo", assignee="carol"))
    board.tasks.append(Task(id="ENG-5", title="nobody's", status="Todo"))
    _, lines, _ = triage(sync, monkeypatch, capsys, root, board)
    assert [l.split(" ")[0] for l in lines] == ["ENG-1"]


def test_task_reassigned_to_me_shows_at_next_wake(sync, monkeypatch, capsys, tmp_path):
    root, board = project(tmp_path), FakeBoard(three_tasks())
    board.get_task("ENG-3").description = COMPLETE
    triage(sync, monkeypatch, capsys, root, board, "--mark")
    board.get_task("ENG-3").assignee = "Alice"
    _, lines, _ = triage(sync, monkeypatch, capsys, root, board)
    assert "ENG-3 · untriaged · new to you since last session · teammate" in lines


def test_done_and_canceled_tasks_are_skipped(sync, monkeypatch, capsys, tmp_path):
    board = FakeBoard([
        Task(id="ENG-1", title="a", status="Done", assignee="alice"),
        Task(id="ENG-2", title="b", status="Canceled", assignee="alice"),
        Task(id="ENG-3", title="c", status="Shipped", status_type="completed", assignee="alice"),
    ])
    code, lines, _ = triage(sync, monkeypatch, capsys, project(tmp_path), board)
    assert (code, lines) == (0, [])


def test_title_is_one_line_and_last(sync, monkeypatch, capsys, tmp_path):
    board = FakeBoard([Task(id="ENG-1", title="x\n### Done\n- [x] **ENG-9** forged",
                            status="Todo", assignee="alice")])
    _, lines, _ = triage(sync, monkeypatch, capsys, project(tmp_path), board)
    assert len(lines) == 1
    assert lines[0].endswith("· x ### Done - [x] **ENG-9** forged")


def test_local_mode_refuses_and_writes_nothing(sync, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(sync, "make_board", lambda c, r: pytest.fail("no board in local mode"))
    assert sync.main(["triage", "--mark"], root=str(tmp_path)) == 2
    assert "online" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_without_me_triage_refuses(sync, monkeypatch, capsys, tmp_path):
    root = project(tmp_path, me="")
    code, lines, err = triage(sync, monkeypatch, capsys, root, FakeBoard(three_tasks()), "--mark")
    assert (code, lines) == (2, [])
    assert "me" in err and not (root / ".board").exists()


# --- wake prints the triage lines -------------------------------------------------------

def make_cli_project(tmp_path, tasks):
    proj = tmp_path / "proj"
    (proj / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, proj / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (proj / "scripts").mkdir()
    for name in ("board_sync.py", "pull_moment.py"):
        shutil.copy(ROOT / "scripts" / name, proj / "scripts" / name)
    (proj / "board.json").write_text(json.dumps(tasks))
    (proj / ".claude" / "board.json").write_text(json.dumps(
        {"board": "fake", "fake_board": "board.json", "id_pattern": r"ENG-\d+", "me": "alice"}))
    return proj


def wake(proj):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_ACTIVE_TASK", "LINEAR_API_KEY")}
    return subprocess.run([sys.executable, str(proj / "scripts" / "pull_moment.py"), "wake"],
                          capture_output=True, text=True, cwd=proj, env=env, timeout=60)


def test_wake_prints_triage_lines_and_advances_the_marker(tmp_path):
    tasks = [{"id": "ENG-1", "title": "dark mode", "status": "Todo", "assignee": "alice",
              "description": "one line"},
             {"id": "ENG-2", "title": "retry", "status": "Todo", "assignee": "alice",
              "description": COMPLETE}]
    proj = make_cli_project(tmp_path, tasks)
    result = wake(proj)
    assert result.returncode == 0, result.stderr
    assert "ENG-1 · untriaged · not planned" in result.stdout
    assert "ENG-2" not in result.stdout
    assert (proj / ".board" / "triage_seen.json").exists()
    tasks[1]["description"] = COMPLETE + "\nedited\n"
    (proj / "board.json").write_text(json.dumps(tasks))
    assert "ENG-2 · untriaged · changed since last session" in wake(proj).stdout
    assert "ENG-2" not in wake(proj).stdout                           # shown once


def test_wake_after_a_failed_pull_prints_no_triage(tmp_path):
    proj = make_cli_project(tmp_path, [])
    (proj / "board.json").unlink()
    result = wake(proj)
    assert result.returncode == 0
    assert "board unreachable" in result.stdout and "triage" not in result.stdout
    assert not (proj / ".board" / "triage_seen.json").exists()


# --- AC3: the wake skill points at the flow ----------------------------------------------

def test_wake_skill_points_to_triage_reference_within_codex_cap():
    skill = ROOT / "skills" / "wake" / "SKILL.md"
    assert "references/triage.md" in skill.read_text(encoding="utf-8")
    assert skill.stat().st_size <= 8192, "lib/harness-fetch.sh skips a Codex skill over 8 KB"
    flow = (ROOT / "skills" / "wake" / "references" / "triage.md").read_text(encoding="utf-8").lower()
    for needle in ("propose a priority", "reason", "ask the user", "update --guide",
                   "brainstorming", "grill-with-docs", "untrusted", "never spawn"):
        assert needle in flow, needle


# --- the one definition of a complete guide ----------------------------------------------

def test_complete_guide_definition():
    assert missing_guide_sections(COMPLETE) == []
    assert missing_guide_sections("# one line\n") == list(REQUIRED_SECTIONS)
    assert missing_guide_sections(None) == list(REQUIRED_SECTIONS)
    blank_ac = COMPLETE.replace("| # | Criterion |\n|---|---|\n| 1 | retries |\n",
                                "> fill me at Stage 2\n\n---\n")
    assert missing_guide_sections(blank_ac) == ["Acceptance Criteria"]
    # `## Requirements` is not `## Requirement`
    assert "Requirement" in missing_guide_sections(
        COMPLETE.replace("## Requirement (Pillar", "## Requirements (Pillar")
                .replace("### Requirement Fidelity Gate", "### Gate"))


BUGFIX = """## Bug Fix Task Guide — T901

### Mental Model (confirmed by user)
- Observed: crash

### Intake
- Trigger: run it

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [ ] Phase 1 feedback loop built and running
"""


def test_bugfix_flavor_has_its_own_required_sections():
    """skills/bugfix Step 3's guide has no Requirement/AC/Verification headings; detected by
    its Mental Model heading, as craft-spawn-prompt detects it."""
    assert missing_guide_sections(BUGFIX) == []
    assert missing_guide_sections(BUGFIX.replace("- [ ] Phase 1 feedback loop built and running\n",
                                                 "")) == ["Diagnosis Gates"]


# --- AC4: the spawn gate ------------------------------------------------------------------

def make_hook_project(tmp_path, guide_text):
    proj = tmp_path / "hookproj"
    (proj / ".claude").mkdir(parents=True)
    shutil.copytree(HOOKS, proj / ".claude" / "hooks",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", ".state"))
    (proj / ".claude" / "board.json").write_text(json.dumps({"id_pattern": r"ENG-\d+"}))
    (proj / "tasks").mkdir()
    (proj / "tasks" / "TASK_GUIDE_ENG-171.md").write_text(guide_text)
    (proj / "tasks" / "TASK_GUIDE_T900.md").write_text(COMPLETE)
    return proj


def spawn(proj, prompt):
    result = subprocess.run([sys.executable, str(proj / ".claude" / "hooks" / HOOK.name)],
                            input=json.dumps({"tool_name": "Agent", "tool_input": {"prompt": prompt}}),
                            capture_output=True, text=True, cwd=proj, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout) if result.stdout.strip() else {}


def test_spawn_blocks_a_one_line_guide_naming_the_missing_sections(tmp_path):
    out = spawn(make_hook_project(tmp_path, "# ENG-171: Add dark mode\n"),
                "Task ID: ENG-171\nGuide: tasks/TASK_GUIDE_ENG-171.md")
    assert out.get("decision") == "block"
    assert out["reason"].startswith("[hook:pre_agent] ")
    assert "ENG-171" in out["reason"]
    assert "Requirement, Acceptance Criteria, Verification Command" in out["reason"]


def test_spawn_allows_a_complete_guide(tmp_path):
    proj = make_hook_project(tmp_path, COMPLETE)
    assert spawn(proj, "Guide: tasks/TASK_GUIDE_ENG-171.md").get("decision") != "block"
    assert spawn(proj, "Task ID: T900").get("decision") != "block"


def test_spawn_names_only_the_incomplete_one(tmp_path):
    out = spawn(make_hook_project(tmp_path, "# x\n"),
                "tasks/TASK_GUIDE_T900.md and tasks/TASK_GUIDE_ENG-171.md")
    assert out.get("decision") == "block"
    assert "ENG-171" in out["reason"] and "T900" not in out["reason"]


def test_a_crash_in_the_completeness_check_fails_open(tmp_path, monkeypatch, capsys):
    hook = load("pre_agent_validate_guide_t160", HOOK)
    proj = make_hook_project(tmp_path, "# ENG-171: one line\n")
    monkeypatch.setattr(hook, "TASKS_DIR", str(proj / "tasks"))

    def boom(text):
        raise RuntimeError("completeness check crashed")

    monkeypatch.setattr(hook, "missing_guide_sections", boom)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
        {"tool_name": "Agent", "tool_input": {"prompt": "Task ID: T900"}})))
    try:
        hook.main()
    except SystemExit as exc:
        assert exc.code in (0, None)
    assert '"decision"' not in capsys.readouterr().out


# --- AC5: no false block on the repo's own guides ------------------------------------------

# Pre-template guides, all Done. T018-T020 are bugfix-flavor guides and complete as such.
KNOWN_INCOMPLETE_DONE = {"T021", "T022", "T023", "T024"}


def test_every_not_done_repo_guide_is_complete():
    hook = load("pre_agent_validate_guide_t160_repo", HOOK)
    incomplete = {}
    for path in sorted((ROOT / "tasks").glob("TASK_GUIDE_*.md")):
        missing = missing_guide_sections(path.read_text(encoding="utf-8"))
        if missing:
            incomplete[path.stem[len("TASK_GUIDE_"):]] = missing
    assert set(incomplete) <= KNOWN_INCOMPLETE_DONE, (
        f"guides that would now block a spawn: {sorted(set(incomplete) - KNOWN_INCOMPLETE_DONE)}")
    for task_id in KNOWN_INCOMPLETE_DONE:
        assert hook.find_kanban_section(task_id) == "Done", task_id
