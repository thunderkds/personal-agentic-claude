# TASK_REVIEW — T110: Update delivers `CLAUDE.md`, through the same edit-safe rule as every other file

> Sibling of `tasks/TASK_GUIDE_T110.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | edited-file conflict, unknown heading, M1 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Upstream clone
changed `CLAUDE.md`, `.claude/settings.json` and `skills/tdd/SKILL.md`; installed project then ran
`update.sh </dev/null`:

```
exit=0
skill: UPDATED
CLAUDE.md: NOT updated
settings.json: NOT updated
```

**AFTER**: [same probe post-change — `CLAUDE.md: UPDATED`, plus the brownfield case]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
