# TASK_REVIEW — T115: Choose CLIs and project type from a list — every install flag is gone, and the docs show one line

> Sibling of `tasks/TASK_GUIDE_T115.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | any argument → exit 1 no write, empty CLI pick re-prompts, M1 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| HITL: user reviewed menu transcript + README install section | ☐ pass / ☐ fail | |
| `tests/test_pack_docs_flags.py` retired/rewritten — reason | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | terminal menus + Markdown/HTML doc text edits in existing sections; wording reviewed via HITL row; site layout untouched |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no CSS or markup structure changes |
| **UI: Responsiveness at target viewports** | ☐ N/A | no layout changes |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit):

```
README install section: sh -c "$(curl -fsSL …/setup.sh)" -- --harness codex    (plus --harness claude --harness codex form)
FAILED tests/test_readme_slim.py::test_readme_is_at_most_75_lines - AssertionError: README.md is 83 lines, expected <= 75
[error] Unknown flag: --pack. Valid flags: --copy, --pack=<name>, --harness <name>
```

**AFTER**: [menu transcript; `sh setup.sh --harness codex` → no-options message; README test pass]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
