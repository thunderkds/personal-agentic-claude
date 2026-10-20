# TASK_REVIEW — T165: The landing page reads as a scan-first reference, and links the Easy Verifier site

> Sibling of `tasks/TASK_GUIDE_T165.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | M1–M4: |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | |

---

## Demonstration

**BEFORE** (Supervisor, 2026-10-20T09:46:03+07:00, `site/index.html` on `main` @ `2b4c73c`):

```
visible words: 2699
lead paragraphs: 30 words in them: 1207 longest: 99
td cells: 118 cells >25 words: 9 longest: 43
details elements: 0
```

Verbatim `#verifier` link line before the change:

```html
<p><a href="https://github.com/thunderkds/easy-verifier-mcp" target="_blank" rel="noopener noreferrer">easy-verifier-mcp on GitHub</a></p>
```

**AFTER**: [same measurement + the new link line]

**DELTA**: [one sentence]

**WITNESS**: [from `memory/event-trace/T165.jsonl`]
