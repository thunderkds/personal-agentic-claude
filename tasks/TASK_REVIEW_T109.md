# TASK_REVIEW — T109: CI runs every install/update shell suite, and the one it would have caught is fixed

> Sibling of `tasks/TASK_GUIDE_T109.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | M1, M2, fake-suite control |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ N/A | CI and tests only; no user-facing behaviour or instruction changed |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | CI config + test files only; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit):

```
rc=0 tests/test_setup.sh                 :: ----- summary: 18 passed, 0 failed -----
rc=0 tests/test_update.sh                :: ----- summary: 31 passed, 0 failed -----
rc=1 tests/test_install_update_smoke.sh  :: 8 passed, 1 failed
rc=0 tests/test_pack_choice_parsing.sh   :: ----- summary: 15 passed, 0 failed -----
rc=0 tests/test_t098_harness_presence.sh :: 20 passed, 0 failed
(none of these in ci.yml)

FAIL: AC1: MANIFEST path 'skills          codex=.codex/skills' missing from target after setup.sh
```

**AFTER**: [same five commands post-change + the drift test]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
