# TASK_REVIEW — T113: Update removes what upstream stopped shipping (unless edited), and kit tests stop shipping

> Sibling of `tasks/TASK_GUIDE_T113.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | edited kept, user-added kept, empty-upstream abort, M1/M2 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit):

Upstream `git rm -r skills/optimize`, then update:

```
[warn]  upstream no longer ships 'skills/optimize/SKILL.md' — leaving your local copy untouched (not deleted).
optimize skill still present (orphan, still loaded by Claude)
```

Fresh install footprint:

```
     47 .claude/hooks
total files: 119
1.4M	.
tests count: 36        (.claude/hooks/tests/)
```

**AFTER**: [same probes — skill removed; `.claude/hooks/tests` absent]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
