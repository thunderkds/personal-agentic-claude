"""T149: ship's GO gate requires a recorded production approval for the exact version."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIP = (ROOT / "skills/ship/SKILL.md").read_text()
RUNBOOK = (ROOT / "templates/RUNBOOK_template.md").read_text()
GATE = SHIP[SHIP.index("#### 7."):]


def test_gate_has_approval_line():
    assert "- [ ] Production approval recorded for <version> @ <commit>" in GATE
    assert "AskUserQuestion" in GATE
    assert "verbatim" in GATE


def test_mismatched_version_does_not_satisfy():
    assert "differs from the release being planned" in GATE
    assert "does not satisfy the gate" in GATE


def test_operator_executes_and_no_deploy_kept():
    assert "this is a recommendation; the operator executes." in SHIP
    assert "never executes the deploy itself" in SHIP


def test_runbook_release_log_has_approved_column():
    header = next(l for l in RUNBOOK.splitlines() if l.startswith("| Version / Tag"))
    assert "Approved (by / when / answer)" in header


def test_smoke_test_before_deploy_and_supervisor_record():
    plan = SHIP[SHIP.index("#### 3."):SHIP.index("#### 4.")]
    assert plan.index("Smoke test, defined before the deploy") < plan.index("Ordered deploy steps")
    assert "written by the Supervisor" in GATE


def test_size_stays_small():
    assert len(SHIP.encode()) < 8192
