# TASK_REVIEW — T111: Kit hooks reach a project that already has `settings.json`, and stay current on update

> Sibling of `tasks/TASK_GUIDE_T111.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | invalid JSON, no python3, user entries kept, M1 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ pass / ☐ fail | D1 site #update-flow, D2 site #hooks, D3 RUNBOOK.md |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer + Python merge script; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Repo pre-seeded with
`.claude/settings.json` = `{"permissions":{}}`, then `setup.sh </dev/null`:

```
settings.json now: {"permissions":{}}
```

No hooks wired, no message. Update probe (see T110 BEFORE): `settings.json: NOT updated`.

**AFTER**: [same probe — kit hooks present, `permissions` intact]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
