# TASK_REVIEW — T116: Every pack ships as a dormant catalog; the broken install-time pack installer is removed

> Sibling of `tasks/TASK_GUIDE_T116.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | no CLI sees pack skills, M1/M2 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| `tests/test_pack_choice_parsing.sh` retired — reason | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | installer + MANIFEST; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit):

`--pack=mobile`:
```
[warn]  Pack 'mobile' not found in central clone (…/home/.supervisor/packs/mobile) — skipping.
[info]  Packs requested: mobile
NO mobile agent installed
```

Interactive menu via pty, answer `1, 5`:
```
[warn]  Pack 'mobile' not found in central clone (…/.supervisor/packs/mobile) — skipping.
[warn]  Pack 'api' not found in central clone (…/.supervisor/packs/api) — skipping.
[info]  Packs requested: mobile api
```

**AFTER**: [install output with catalog line; `packs/` present; no pack names under CLI dirs]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
