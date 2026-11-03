# TASK_REVIEW — T245: `ux-evaluate` skill — the frontend agent checks its UI against the requirement's UX criteria

> Sibling of `tasks/TASK_GUIDE_T245.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | |

---

## Demonstration

**BEFORE** (verbatim prior content, captured 2026-11-03T15:23:41Z in `../wt-t245` at `00c9a5bf`, before any implementation commit):

```
$ ls skills/ux-evaluate
ls: cannot access 'skills/ux-evaluate': No such file or directory
$ grep -n "^### " templates/TASK_GUIDE_template.md   # UI section ends at:
133:### 3. Layout / Responsiveness
$ grep -c "ux-" skills/code-review/SKILL.md
0
$ wc -c skills/code-review/SKILL.md
8163 skills/code-review/SKILL.md
```
`agents/frontend.md` `## Available skills` rows: `brainstorming`, `code-review`, `security-review`, `verify`, `run`, `compound`, `optimize` — no UX skill.

**AFTER**: [filled at Stage 4]

**DELTA**: [filled at Stage 4]

**WITNESS**: [filled at Stage 4]
