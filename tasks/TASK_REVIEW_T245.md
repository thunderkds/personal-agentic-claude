# TASK_REVIEW — T245: `ux-evaluate` skill — the frontend agent checks its UI against the requirement's UX criteria

> Sibling of `tasks/TASK_GUIDE_T245.md`. Filled by the reviewer at Stage 4/5.

---

## Auto decisions

Mode: auto
1. Extended track — RULE: `AGENTS.md` § Tracks ("The extended track applies if any of: C2 or above; Risk Medium or High")
2. Requirement Fidelity Gate signed `auto (Supervisor)` — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` (row 13)
3. Base team, `common-infrastructure` implements — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` (row 11)
4. Spawn model `claude · C2 → sonnet` — FACT: PROJECT_SPEC.md:146 "| claude | `claude` | haiku | sonnet | sonnet or opus | opus |"
5. Duplicate ID: the `ux-evaluate` task keeps T245; the hook fix added in `00c9a5bf` becomes T246 — DEBATED: renumber the row-only task (Advocate 1: keep T245 for the task with guide, branch and trace, rename the row-only one; Advocate 2: argued renaming the ux task, found it breaks guide, trace and pushed `e97c7586`, so proposed renaming the row-only one too) ⚠ decided for you — please review
6. The frontend agent reads `skills/ux-evaluate/SKILL.md` instead of calling `Skill(...)` — FACT: memory/learnings.md:895 "## A sub-agent has no `Skill` tool (T065, 2026-08-09)"
Paused: run in progress — implementer running; Stage 4 (`code-review`, `security-review`), the memory pass and auto verify not yet run
Checks: pending — filled at Stage 4
Memory: pending — the diff-driven pass runs at Stage 4
Not done: merge (yours); auto verify: not started
Paused: auto-mode check failed — no test run in memory/event-trace/T245.jsonl — write /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID with the task ID (minimal-track step 1): `mkdir -p /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d && printf '%s\n%s\n' "T245" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID`, then rerun the task's tests so the trace records them under the task, then stop; extended track, but the trace has no `code-review` Skill call (Stage 4 runs in auto mode) [report e07fb4895580]

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t245_ux_evaluate.py` (AC 1-7, 23 tests): `23 passed in 0.32s`; red run before the edits `19 failed, 4 passed` |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q`: `3138 passed, 25 subtests passed in 201.12s`; `main` run: `3109 passed, 25 subtests passed in 209.70s` (0 failures on both) |
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

Added by the implementer before the first implementation commit (verbatim, from the files as they stood at `e96bef31`):

`agents/frontend.md` `## Implementation checklist (apply what the task needs)`:
```
- Accessibility: semantic HTML, keyboard navigation, ARIA where needed, WCAG per the TASK_GUIDE
- State: use the project's existing state pattern; lift state only as far as required
- Forms: client-side validation that mirrors server rules; clear error surfaces
- Performance: meet the NFR targets stated in the TASK_GUIDE/PRD - measure (bundle size, render), don't assume a number
- Responsiveness: match the TASK_GUIDE's breakpoints/design
- Tests: cover the acceptance criteria and the negative/edge cases before marking ready
```
`agents/frontend.md` Pillar 3: `run the TASK_GUIDE's verification command and confirm the UI behaves in the browser; paste real output/observation into the Evidence table.`

`skills/code-review/SKILL.md` `#### Conditional reviewers` table rows (persona | activates on): security-reviewer, performance-reviewer, migration-reviewer, adversarial-reviewer, api-reviewer, over-engineering-reviewer. None names UI, UX or a screenshot.

`templates/TASK_GUIDE_template.md` UI section ends with `### 3. Layout / Responsiveness`; no UX block. `tests/test_t245_ux_evaluate.py` red run: `19 failed, 4 passed`.

**AFTER**: [filled at Stage 4]

**DELTA**: [filled at Stage 4]

**WITNESS**: [filled at Stage 4]
