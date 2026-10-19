"""T155 — `board_sync.py init` asks the board questions and writes `.claude/board.json`.

No network: a scripted `ask` and a fake setup board stand in for the terminal and Linear.

  AC1 — api key / team 1 / project 1: ids, `me`, escaped `id_pattern`, `status_map`
  AC2 — api key chosen, LINEAR_API_KEY unset: prints how to set it, writes nothing
  AC3 — mcp: prints the `claude mcp add` command, connection mcp, no fetch
  AC4 — no terminal / answer no: no file, no network, no output
  AC5 — no key material in the config or the output
  Plus: bad id_pattern refused, existing config needs a confirm, `me` token form.

Run with: python3 -m pytest tests/test_board_init.py -v
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "board_sync.py"
KEY = "lin_api_SECRETtestkey0123456789"


def load_sync():
    spec = importlib.util.spec_from_file_location("board_sync_init_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sync = load_sync()


class SetupBoard:
    """Stands in for LinearBoard's setup queries."""
    def __init__(self, team_key="ENG", display="Hùng Nguyễn.h", fail=None):
        self.calls = []
        self.team_key = team_key
        self.display = display
        self.fail = fail

    def _go(self, name):
        self.calls.append(name)
        if self.fail:
            raise self.fail

    def viewer(self):
        self._go("viewer")
        return self.display

    def list_teams(self):
        self._go("teams")
        return [{"id": "t-1", "key": self.team_key, "name": "Engineering"},
                {"id": "t-2", "key": "OPS", "name": "Operations"}]

    def list_projects(self, team_id):
        self._go("projects")
        return [{"id": "p-1", "name": "Online board"}, {"id": "p-2", "name": "Other"}]

    def list_states(self, team_id):
        self._go("states")
        return [{"name": "Backlog", "type": "backlog"}, {"name": "Todo", "type": "unstarted"},
                {"name": "In Progress", "type": "started"},
                {"name": "Code Review", "type": "started"}, {"name": "Done", "type": "completed"}]


def scripted(*answers):
    queue = list(answers)

    def ask(prompt):
        if not queue:
            return None
        return queue.pop(0)
    return ask


def run_init(root, answers, board=None, env=None, tty=True):
    out, err = [], []
    board = board or SetupBoard()
    code = sync.init(str(root), scripted(*answers) if tty else (lambda p: None),
                     lambda key: board, {} if env is None else env,
                     lambda text: out.append(text), lambda text: err.append(text))
    return code, "\n".join(out), "\n".join(err), board


def config(root):
    return json.loads((root / ".claude" / "board.json").read_text())


# AC1 ---------------------------------------------------------------------------------------
def test_api_key_flow_writes_config(tmp_path):
    # connection 1 (api key), team 1, project 1, map Code Review -> 3 (Ready for Review), git auto: n
    code, out, err, board = run_init(tmp_path, ["1", "1", "1", "3", "n"], env={"LINEAR_API_KEY": KEY})
    assert code == 0, err
    cfg = config(tmp_path)
    assert cfg["board"] == "linear" and cfg["connection"] == "api"
    assert cfg["team"] == "t-1" and cfg["project"] == "p-1"
    assert cfg["me"] == "HngNguyn.h"
    assert cfg["id_pattern"] == r"ENG-\d+"
    assert cfg["status_map"] == {"Code Review": "Ready for Review"}
    assert cfg["git_auto_status"] is False
    assert "mode" not in cfg


def test_whole_team_when_project_zero(tmp_path):
    code, *_ = run_init(tmp_path, ["1", "1", "0", "3", "n"], env={"LINEAR_API_KEY": KEY})
    assert code == 0
    assert config(tmp_path)["project"] == ""


def test_team_key_is_regex_escaped_and_validated(tmp_path):
    from_config = load_board_config()
    code, *_ = run_init(tmp_path, ["1", "1", "1", "3", "n"], board=SetupBoard(team_key="E.G+"),
                        env={"LINEAR_API_KEY": KEY})
    assert code == 2, "a key that makes a bad id_pattern must not be saved"
    assert not (tmp_path / ".claude" / "board.json").exists()
    code, *_ = run_init(tmp_path, ["1", "1", "1", "3", "n"], board=SetupBoard(team_key="ENG2"),
                        env={"LINEAR_API_KEY": KEY})
    assert code == 0
    assert from_config.board_id_pattern(str(tmp_path)) == r"ENG2-\d+"


def load_board_config():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "lib"))
    from board import config as board_config
    return board_config


def test_me_matches_render_assignee_token(tmp_path):
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "lib"))
    from board import render
    run_init(tmp_path, ["1", "1", "1", "3", "n"], env={"LINEAR_API_KEY": KEY})
    assert config(tmp_path)["me"] == render.assignee_token("Hùng Nguyễn.h")


def test_default_state_names_need_no_mapping(tmp_path):
    # Enter on the unknown state keeps the default-by-type, so nothing is stored for it
    code, *_ = run_init(tmp_path, ["1", "1", "1", "", "y"], env={"LINEAR_API_KEY": KEY})
    assert code == 0
    cfg = config(tmp_path)
    assert cfg["status_map"] == {} and cfg["git_auto_status"] is True


# AC2 ---------------------------------------------------------------------------------------
def test_missing_key_prints_how_and_writes_nothing(tmp_path):
    code, out, err, board = run_init(tmp_path, ["1"], env={})
    assert code == 1
    assert "export LINEAR_API_KEY=" in out + err
    assert not (tmp_path / ".claude").exists()
    assert board.calls == []


# AC3 ---------------------------------------------------------------------------------------
def test_mcp_prints_command_and_fetches_nothing(tmp_path):
    code, out, err, board = run_init(tmp_path, ["2", "ENG", "Hung", "n"], env={})
    assert code == 0, err
    assert "claude mcp add" in out and "mcp.linear.app" in out
    assert board.calls == []
    cfg = config(tmp_path)
    assert cfg["connection"] == "mcp" and cfg["board"] == "linear"
    assert cfg["id_pattern"] == r"ENG-\d+" and cfg["me"] == "Hung"


# AC4 ---------------------------------------------------------------------------------------
def test_no_terminal_does_nothing(tmp_path):
    code, out, err, board = run_init(tmp_path, [], env={"LINEAR_API_KEY": KEY}, tty=False)
    assert code == 0 and out == "" and err == ""
    assert board.calls == [] and not (tmp_path / ".claude").exists()


def test_no_controlling_terminal_subprocess(tmp_path):
    (tmp_path / "scripts").mkdir()
    r = subprocess.run([sys.executable, str(SCRIPT), "init"], cwd=tmp_path, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, start_new_session=True,
                       env={"PATH": "/usr/bin:/bin"})
    assert r.returncode == 0 and r.stdout == ""
    assert not (ROOT / ".claude" / "board.json").exists()


def test_eof_mid_questions_writes_nothing(tmp_path):
    code, *_ = run_init(tmp_path, ["1", "1"], env={"LINEAR_API_KEY": KEY})
    assert code != 0 and not (tmp_path / ".claude").exists()


# AC5 ---------------------------------------------------------------------------------------
def test_no_key_material_anywhere(tmp_path):
    code, out, err, _ = run_init(tmp_path, ["1", "1", "1", "3", "n"], env={"LINEAR_API_KEY": KEY})
    blob = (tmp_path / ".claude" / "board.json").read_text() + out + err
    assert KEY not in blob and "lin_api" not in blob


def test_board_failure_message_never_carries_key(tmp_path):
    exc = sync.BoardAuthError("Linear rejected the API key (HTTP 401/403); check LINEAR_API_KEY")
    code, out, err, _ = run_init(tmp_path, ["1"], board=SetupBoard(fail=exc), env={"LINEAR_API_KEY": KEY})
    assert code == 1 and KEY not in out + err
    assert not (tmp_path / ".claude").exists()


# Existing config ---------------------------------------------------------------------------
def test_existing_config_needs_confirm(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "board.json").write_text('{"board": "linear", "team": "old"}')
    code, *_ = run_init(tmp_path, ["n"], env={"LINEAR_API_KEY": KEY})
    assert code == 0 and config(tmp_path)["team"] == "old"
    code, *_ = run_init(tmp_path, ["y", "1", "1", "1", "3", "n"], env={"LINEAR_API_KEY": KEY})
    assert code == 0 and config(tmp_path)["team"] == "t-1"


# CLI ---------------------------------------------------------------------------------------
def test_init_subcommand_exists_and_local_mode_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "tty_ask", lambda prompt: None)
    assert sync.main(["init"], root=str(tmp_path)) == 0
    assert not (tmp_path / ".board").exists()


def test_linear_setup_queries_parse_answers(monkeypatch):
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "lib"))
    from board.linear import LinearBoard
    board = LinearBoard(KEY, "")
    answers = {
        "viewer": {"viewer": {"displayName": "Hung"}},
        "teams": {"teams": {"nodes": [{"id": "t", "key": "ENG", "name": "E"}]}},
        "team": {"team": {"projects": {"nodes": [{"id": "p", "name": "P"}]},
                          "states": {"nodes": [{"name": "Done", "type": "completed"}]}}},
    }

    def fake_post(query, variables):
        for word, data in answers.items():
            if f"{word}" in query.split("{")[1]:
                return data, None
        raise AssertionError(query)
    monkeypatch.setattr(board, "_post", fake_post)
    assert board.viewer() == "Hung"
    assert board.list_teams() == [{"id": "t", "key": "ENG", "name": "E"}]
    assert board.list_projects("t") == [{"id": "p", "name": "P"}]
    assert board.list_states("t") == [{"name": "Done", "type": "completed"}]


# setup.sh --------------------------------------------------------------------------------
def run_offer(tmp_path, tty_ok, answer, with_script=True, with_config=False):
    tmp_path.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "scripts").mkdir(exist_ok=True)
    if with_script:
        (tmp_path / "scripts" / "board_sync.py").write_text("")
    if with_config:
        (tmp_path / ".claude").mkdir(exist_ok=True)
        (tmp_path / ".claude" / "board.json").write_text("{}")
    func = subprocess.run(["sed", "-n", "/^offer_board_mode() {/,/^}/p", str(ROOT / "setup.sh")],
                          capture_output=True, text=True, check=True).stdout
    assert func.strip(), "offer_board_mode() missing from setup.sh"
    script = f'''log_warn() {{ echo "WARN $*"; }}
{func}
TTY_OK={tty_ok}
tty_read() {{ TTY_ANSWER="{answer}"; return 0; }}
python3() {{ echo "INIT-CALLED $*"; }}
offer_board_mode
'''
    r = subprocess.run(["sh", "-c", script], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_setup_asks_nothing_without_a_terminal(tmp_path):
    assert run_offer(tmp_path, 0, "y") == ""


def test_setup_default_is_no(tmp_path):
    out = run_offer(tmp_path, 1, "")
    assert "online board" in out and "INIT-CALLED" not in out


def test_setup_yes_calls_init(tmp_path):
    assert "INIT-CALLED scripts/board_sync.py init" in run_offer(tmp_path, 1, "y")


def test_setup_skips_when_already_configured_or_script_absent(tmp_path):
    assert run_offer(tmp_path, 1, "y", with_config=True) == ""
    assert run_offer(tmp_path / "x", 1, "y", with_script=False) == ""
