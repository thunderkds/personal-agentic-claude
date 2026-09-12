# TASK_REVIEW — T114: One command — it detects the project, shows a menu, and asks before acting

> Sibling of `tasks/TASK_GUIDE_T114.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | cancel = zero changes, invalid input, no-TTY never reinstalls, M1/M2 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| HITL: user reviewed menu transcripts (SC1, SC3, SC6) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | terminal text menu, no visual design surface; wording is reviewed through the HITL row above |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no design system applies to plain terminal output |
| **UI: Responsiveness at target viewports** | ☐ N/A | terminal output; no viewports |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9` — to be re-captured by the implementer on the
integration branch tip after T110–T113 merge, before this task's first commit):

```
===== update.sh as a user would run it (from their project) =====
ls: cannot access 'update.sh': No such file or directory
sh: 0: cannot open ./update.sh: No such file

===== re-running setup.sh on an existing, customized project =====
exit=0
local edit SILENTLY OVERWRITTEN
```

**AFTER**: [menu transcripts]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
