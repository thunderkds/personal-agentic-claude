import importlib.util
import os
import sys

HOOKS_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HOOKS_TESTS_DIR)))
RENDER_PATH = os.path.join(ROOT, ".claude", "skills", "delivery-report", "render.py")

spec = importlib.util.spec_from_file_location("delivery_report_render", RENDER_PATH)
render_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_mod)


IMPL_GUIDE = """# TASK_GUIDE — T900: example

### Evidence (filled by reviewer at Stage 4/5)
| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_x.py |
| Verification command run | pass | output pasted |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | pass | ran, pass |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | N/A | no UI surface |
| **UI: Design-system compliance** | N/A | no UI surface |
| **UI: Responsiveness** | N/A | no UI surface |

## Demonstration

**BEFORE**: `curl localhost/health` returns 404 with <no route> & unknown status.

**AFTER**: `curl localhost/health` returns 200.

**DELTA**: users can now check service health.

**WITNESS**: [ignored by the parser]
"""

BUGFIX_GUIDE = """# Bug Fix Task Guide — T901

### Evidence (filled by reviewer at Stage 4/5)
| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_y.py |
| Verification command run | pass | output pasted |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | pass | ran, pass |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | N/A | no UI surface |
| **UI: Design-system compliance** | N/A | no UI surface |
| **UI: Responsiveness** | N/A | no UI surface |
| Repro loop | pass | `curl localhost/health` returns 500 before the fix |
| Regression test | pass | tests/test_regression.py |
| Smoke suite | pass | bug-specific smoke green |

## Demonstration

**BEFORE**: same command as the Phase 1 repro loop above, captured before any fix commit exists —
do not restate it here as a second copy; point at it by name (e.g. "see Phase 1 repro loop") so
the two cannot drift out of sync.

**AFTER**: the same Phase 1 repro loop, re-run post-fix, showing the bug no longer reproduces.

**DELTA**: the endpoint now returns 200 instead of 500.

**WITNESS**: <ignored by the parser>
"""

BLANK_EVIDENCE_GUIDE = """# TASK_GUIDE — T902: example

### Evidence (filled by reviewer at Stage 4/5)
| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [must literally state "pass" or "fail"] |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Design-system compliance** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Responsiveness** | ☐ pass / ☐ fail / ☐ N/A | |

## Demonstration

**BEFORE**: [pasted timestamped command output showing the thing absent/failing]

**AFTER**: [same command, post-change]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
"""

ESCAPE_GUIDE = """# TASK_GUIDE — T903: example

### Evidence (filled by reviewer at Stage 4/5)
| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| verify | pass | output was `<div>&amp;</div>` |

## Demonstration

**BEFORE**: `<script>alert(1)</script>` & other <weird> markup.

**AFTER**: fixed, no <script> tags rendered raw.

**DELTA**: input containing `<`, `>`, `&` is now handled safely.

**WITNESS**: n/a
"""


def test_ac1_one_parser_serves_both_flavors():
    impl_slots = render_mod.build_slots("T900", "branch-a", IMPL_GUIDE, root="/nonexistent")
    bugfix_slots = render_mod.build_slots("T901", "branch-b", BUGFIX_GUIDE, root="/nonexistent")
    assert set(impl_slots.keys()) == set(bugfix_slots.keys())
    assert "returns 500 before the fix" in bugfix_slots["BEFORE"]
    assert "Phase 1 repro loop" not in bugfix_slots["BEFORE"] or "[resolved from Evidence" in bugfix_slots["BEFORE"]
    assert impl_slots["DELTA"] == "users can now check service health."


def test_sc2_bugfix_repro_loop_reference_resolved_not_printed_raw():
    demo = render_mod.parse_demonstration(BUGFIX_GUIDE)
    assert "[resolved from Evidence 'Repro loop' row]" in demo["before"]
    assert "returns 500 before the fix" in demo["before"]


def test_sc3_blank_evidence_renders_gap_not_omission():
    rows = render_mod.parse_evidence_table(BLANK_EVIDENCE_GUIDE)
    assert len(rows) == 9
    filled = sum(1 for r in rows if r["status"] == "filled")
    assert filled == 0
    slots = render_mod.build_slots("T902", "branch-c", BLANK_EVIDENCE_GUIDE, root="/nonexistent")
    assert slots["EVIDENCE_COUNT_SUMMARY"].startswith("0 / 9")
    assert "blank in this guide" in slots["BEFORE"]


def test_sc4_angle_bracket_and_ampersand_render_literally_in_pre():
    template = "<html>{{BEFORE}}|{{AFTER}}|{{DELTA}}</html>"
    slots = render_mod.build_slots("T903", "branch-d", ESCAPE_GUIDE, root="/nonexistent")
    # explicit contract: render.py does not manually escape — it is the
    # template's job to wrap in <pre>, matching the html-report convention
    assert "<script>alert(1)</script>" in slots["BEFORE"]
    assert "&amp;" not in slots["BEFORE"]  # not double-escaped
    html = render_mod.render(template, slots)
    assert "{{" not in html


def test_sc5_missing_trace_file_renders_explicitly_underived():
    witness = render_mod.resolve_witness("T_DOES_NOT_EXIST", root="/nonexistent-root-for-test")
    assert "underived" in witness
    assert "T_DOES_NOT_EXIST" in witness
    # never a guessed/fabricated name
    assert "Claude" not in witness and "agent" not in witness.lower()


def test_no_demonstration_block_reported_not_crashed():
    guide_without_demo = "# TASK_GUIDE — T904\n\n### Evidence\n| Check | Result | Notes |\n|---|---|---|\n"
    slots = render_mod.build_slots("T904", "branch-e", guide_without_demo, root="/nonexistent")
    assert "predates T053" in slots["BEFORE"]
    assert "no-demo-warning" in slots["NO_DEMO_WARNING"]


def test_no_unfilled_slots_survive_full_render():
    with open(os.path.join(ROOT, "templates", "delivery_report_template.html")) as f:
        template_text = f.read()
    slots = render_mod.build_slots("T900", "branch-a", IMPL_GUIDE, root="/nonexistent")
    html = render_mod.render(template_text, slots)
    assert "{{" not in html and "}}" not in html


def test_real_bugfix_guide_t055_parity_no_flavor_branch():
    guide_path = os.path.join(ROOT, "tasks", "TASK_GUIDE_T055.md")
    if not os.path.isfile(guide_path):
        return
    with open(guide_path) as f:
        text = f.read()
    rows = render_mod.parse_evidence_table(text)
    assert len(rows) >= 9
