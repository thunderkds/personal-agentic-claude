"""T273: the Windows parity ledger (`docs/windows-parity.md`) stays complete and honest.

The ledger lists every hook, script, library, installer entry point and shell test, and says for
each one how it is proven on Windows. These tests fail when:
  - a file exists in the repo but no ledger row names it (the ledger went stale);
  - a row has a status outside covered / partial / gap / n/a, or a partial / gap / n/a row has no reason;
  - a "Windows proof" cell cites a file that does not exist;
  - the posix_only skip inventory differs from the real count in the test files;
  - the "Windows CI run seen" line is missing.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "docs" / "windows-parity.md"
STATUSES = {"covered", "partial", "gap", "n/a"}
TOKEN = re.compile(r"`([^`]+)`")


def _text():
    assert LEDGER.is_file(), "docs/windows-parity.md is missing"
    return LEDGER.read_text(encoding="utf-8")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _rows(section):
    """Table rows (list of cells) under the `## <section>` heading, header and rule rows dropped."""
    out, on = [], False
    for line in _text().splitlines():
        if line.startswith("## "):
            on = line[3:].strip().lower().startswith(section.lower())
            continue
        if on and line.startswith("|"):
            cells = _cells(line)
            if cells[0].lower() in ("item", "file") or set(cells[0]) <= set("-: "):
                continue
            out.append(cells)
    return out


def _inventory():
    names = set()
    for pat in (".claude/hooks/*.py", ".claude/hooks/lib/*.py", "scripts/*.py", "scripts/*.sh",
                "lib/*.py", "lib/*.sh", "lib/*.ps1", "skills/*/scripts/*.py",
                "skills/*/scripts/*.sh", "tests/*.sh", "tests/windows/*.ps1"):
        names.update(p.name for p in REPO.glob(pat))
    names.update(n for n in ("setup.sh", "update.sh", "setup.ps1", "update.ps1") if (REPO / n).is_file())
    return names


def test_the_ledger_says_whether_a_windows_run_was_seen():
    assert re.search(r"^Windows CI run seen: (no|yes \(.+\))\s*$", _text(), re.M)


def test_every_repo_file_in_scope_has_a_row():
    named = set()
    for cells in _rows("Ledger"):
        for tok in TOKEN.findall(cells[0]):
            named.add(Path(tok).name)
    missing = sorted(_inventory() - named)
    assert not missing, "no ledger row names: " + ", ".join(missing)


def test_rows_have_a_known_status_and_a_reason_when_not_covered():
    rows = _rows("Ledger")
    assert rows, "the Ledger table has no rows"
    for cells in rows:
        assert len(cells) == 5, f"a ledger row needs 5 cells: {cells[0]}"
        item, _ubuntu, _win, status, reason = cells
        assert status in STATUSES, f"{item}: status {status!r} is not one of {sorted(STATUSES)}"
        if status != "covered":
            assert reason and reason != "-", f"{item}: a {status} row needs a written reason"


def test_every_cited_windows_proof_exists():
    for cells in _rows("Ledger"):
        for tok in TOKEN.findall(cells[2]):
            if "/" in tok or tok.endswith((".py", ".ps1", ".yml")):
                path = tok.split("::")[0].split(" ")[0]
                assert (REPO / path).exists(), f"{cells[0]}: Windows proof {path} does not exist"


def test_skip_inventory_matches_the_posix_only_marks_in_the_tests():
    actual = {}
    for base in ("tests", ".claude/hooks/tests"):
        for p in (REPO / base).glob("*.py"):
            if p.name == Path(__file__).name:
                continue  # this file names the mark in its own text
            n = sum(1 for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
                    if "posix_only" in line)
            if n:
                actual[f"{base}/{p.name}"] = n
    listed = {}
    for cells in _rows("Skip inventory"):
        listed[cells[0].strip("`")] = int(cells[1])
    assert listed == actual
