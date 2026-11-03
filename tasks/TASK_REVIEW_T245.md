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
| **Companion score (easy-verifier)** | ☑ N/A | MCP not registered in this session (no `score`/`write_report` tools); `easy_verifier` not importable (`ModuleNotFoundError: No module named 'easy_verifier'` for `python` and `python3`); stopped at rung 3, 2026-11-03. Nothing was scored. To score: the operator starts the easy-verifier container (`127.0.0.1:8766`) and registers its MCP, then reruns `score` on `main...feat/t245-ux-evaluate` |
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


---

## Demonstration — BEFORE (amendment A1)

**BEFORE (amendment A1)** (verbatim current content of `skills/ux-evaluate/SKILL.md`, captured 2026-11-03T15:57:07Z in `../wt-t245` at `2e867618`, before any A1 edit; this task changes skill-instruction text, no executable code):

Line 17:
```
- **Simplicity First**: Judge only the rows. Never add a `fail` for something no row asks.
```
Line 28:
```
If there is no such section or it has no rows, the result is `no UX criteria`. Stop. Tell the caller to ask the Supervisor for the rows. Never write rows yourself and then judge them.
```
`### Workflow` step 1 heading block (lines 23-31):
```

#### 1. Read the rows

Open `tasks/TASK_GUIDE_<ID>.md`. Read `### 4. UX Acceptance Criteria` (columns `User story`, `User goal`, `Flow / state`, `Pass condition (observable)`), the requirement each row cites (a `PRD.md` US-ID or the quoted request), and `Entry point` under `## Dependencies & Reachability`. Rows the caller pastes into the prompt count as the rows.

If there is no such section or it has no rows, the result is `no UX criteria`. Stop. Tell the caller to ask the Supervisor for the rows. Never write rows yourself and then judge them.

Completion: every row listed with its story, state and pass condition.

```
Size before A1: 5223 bytes. `tests/test_t245_ux_evaluate.py::test_ac3_no_ux_rows_tells_the_caller_to_ask_the_supervisor` pins the stop at `no UX criteria`.

---

## Experiment: before/after the skill (2026-11-03, user: "should check before/after adding skill to make sure skill is good to use, by the experiment")

Fixture: a static task-list page (`list.html`, `empty.html`, `error.html`, `style.css`) with 3 seeded UX defects that are in the DOM but not visible when rendered: the "Add task" button is clipped at 375px (`width:900px` + `overflow:hidden`); "No tasks yet" is `#fafafa` on white; a `position:absolute` notice covers "Try again". One criterion is correct (3 titles readable). The key was confirmed by the Supervisor's own screenshots. Correct verdict: NOT READY, 3 defects. Every run: `general-purpose`, sonnet, its own fixture copy, told to act as the frontend agent with a given role guide.

| Round | Arm | Role guide | Task guide | Prompt | Runs | Defects found | Verdict right | Screenshots |
|---|---|---|---|---|---|---|---|---|
| 1 | before | `main` (no skill) | with UX rows | per-row report format, names "screenshots" as an example method | 2 | 3/3, 3/3 | 2/2 | 2/2 |
| 1 | after | branch (skill) | with UX rows | same | 2 | 3/3, 3/3 | 2/2 | 2/2 |
| 2 | before | `main` (no skill) | old template, no UX rows | neutral: "do the checks your role guide asks for" | 2 | 3/3, 3/3 | 2/2 | 2/2 (one run skipped 1 of 6 images) |
| 2 | after | branch (skill) | UX rows | same neutral prompt | 2 | 3/3, 3/3 | 2/2 | 2/2 (both followed `ux-evaluate`, per-row table) |

Result: no detection difference, 8/8 runs right. The baseline agent already takes headless-Chrome screenshots on its own when the requirement names widths. What the skill changed: every after run gave a per-row verdict traced to the guide's UX rows and opened every image; one before run skipped an image. One after run's summary line miscounted (said "2 of 4 pass" over a table with 1 pass).
Limits: n = 2 per arm per round; the seeded defects are also visible by reading the CSS, so this fixture does not test what only a screenshot shows; requirement-level misses (wrong flow, wrong copy) were not seeded.

### Round 3: harder fixture (user: "ys" to a harder test)

Fixture: 5 pages (`list`, `add`, `confirm`, `saved`, `error`). 4 seeded misses: the "Add task" button is hidden at 375px by a "responsive" script (`layoutHeader`, only seen at run time); adding takes 3 pages where the requirement says one step from the list; the "Task saved" toast is placed above the screen at 375px by a script; the error page says only "Error 503.". 1 true pass (titles readable). Before: `main` role guide + old-template guide (ACs, no UX rows). After: branch role guide + skill + UX rows. Same neutral prompt as round 2. 3 runs per arm, sonnet.

| Arm | Runs | Misses found | Verdict right | Notes |
|---|---|---|---|---|
| before | 3 | 4/4, 4/4, 4/4 | 3/3 | all took screenshots; 2 also dumped the live DOM (`top: -48px`); one skipped the overflow check and said so |
| after | 3 | 4/4, 4/4, 4/4 | 3/3 | all followed `ux-evaluate`, per-row table, every image read |

Total over 3 rounds: 14 runs, every run found every seeded miss and gave the right verdict. The skill gave no measurable detection gain. Its visible effect is format: a per-row verdict table tied to the guide's UX rows.
