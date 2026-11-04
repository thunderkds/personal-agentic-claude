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
7. Stage 4 review R2: a baseline `fail` on a part the diff did not change is `fail (older)`, P3 — USER: "yes [auto]" (2026-11-04) to the Supervisor's recommendation
8. Stage 4 P1 on `agents/frontend.md` withdrawn: the dropped "don't introduce it unilaterally" rule is still in the Appendix — FACT: agents/frontend.md:141 "`grill-with-docs`)** — don't introduce it unilaterally."
Checks: auto-checked, not /verify — `tests/test_t245_ux_evaluate.py` 35 passed; full suite `3150 passed, 25 subtests passed`; code-review 0 P0 / 0 P1, R2-R4 fixed (`466e2769`); security-review no findings; AC 8 real run of `ux-evaluate` on `site/index.html` (screenshots at 375 and 1280); round 4 blind no-design builds 35/35 vs 29/29
Memory: `memory/learnings.md` "Measure a UX skill on no-design builds, judged blind (T245)" + its `memory/MEMORY.md` index line (`ac4569c5` on main)
Not done: merge (yours); auto verify: ☑ pass (session b06b5e49-dcaf-4473-ae88-3836eff368af, commit 530531912cc226158bf063eb0649da147a6c23b3, log .claude/verify-runs/T245-530531912cc2.log)
Closed: row moved to Done 2026-11-04 — auto verify pass (session b06b5e49-dcaf-4473-ae88-3836eff368af, commit 530531912cc226158bf063eb0649da147a6c23b3); Gates 5 and 6 checked

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t245_ux_evaluate.py` (AC 1-7, 23 tests): `23 passed in 0.32s`; red run before the edits `19 failed, 4 passed`. A1 + review R2/R3 tests added (2026-11-04): red `3 failed, 32 passed`, then `35 passed in 0.29s` |
| Verification command run | ☑ pass | 2026-11-04 at `466e2769`: `35 passed in 0.29s`; `[ok]   skills/ux-evaluate/SKILL.md`; `7368 skills/ux-evaluate/SKILL.md`, `8175 skills/code-review/SKILL.md` (each ≤ 8192); Chrome line: `56772 bytes written to file …/scratchpad/t245-375.png` |
| Negative cases hold | ☑ pass | tests pin `not checked` never `pass`, `not checkable` never `pass`, `no UX criteria — baseline checks only`, the old early stop gone, `fail (older)` → P3. AC 8 real run produced a real `fail` (B-d, header links ~20 px at 375) and a real `not checked` (B-g) |
| verify | ☑ pass | auto-run by hook, session b06b5e49-dcaf-4473-ae88-3836eff368af, commit 530531912cc226158bf063eb0649da147a6c23b3, log .claude/verify-runs/T245-530531912cc2.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review on `merge-base..HEAD` (14 files). Lane: `EXCEEDS (lines 506 > 500)`, unpredicted test/site files — warn-only, mostly tests + records. Findings: 0 P0, 0 P1 (one P1 raised and withdrawn: the two 'dropped' `agents/frontend.md` lines duplicate rules still in the file — commit `ea388ac9`), 3 P2 R2-R4 fixed in this commit. security-review (Risk Medium): no findings — static text in `site/*.html`, markdown, tests only |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q`: `3138 passed, 25 subtests passed in 201.12s`; `main` run: `3109 passed, 25 subtests passed in 209.70s` (0 failures on both) |
| **Companion score (easy-verifier)** | ☑ N/A | MCP not registered in this session (no `score`/`write_report` tools); `easy_verifier` not importable (`ModuleNotFoundError: No module named 'easy_verifier'` for `python` and `python3`); stopped at rung 3, 2026-11-03. Nothing was scored. To score: the operator starts the easy-verifier container (`127.0.0.1:8766`) and registers its MCP, then reruns `score` on `main...feat/t245-ux-evaluate` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component built; the only page change is one chip label and a count on `site/*.html`, seen in the AC 8 screenshots (index-375.png, index-1280.png) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | same: the new chip reuses the existing `chip` class, no new style |
| **UI: Responsiveness at target viewports** | ☑ N/A | same; AC 8 run: the Stage 3 chip row wraps cleanly at 375 and 1280 |

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

**AFTER** (2026-11-04, branch HEAD):
```
$ ls skills/ux-evaluate
SKILL.md
$ grep -n "^### 4" templates/TASK_GUIDE_template.md
141:### 4. UX Acceptance Criteria
$ grep -c "ux-evaluate" skills/code-review/SKILL.md
1
$ wc -c skills/code-review/SKILL.md skills/ux-evaluate/SKILL.md
8175 skills/code-review/SKILL.md
7368 skills/ux-evaluate/SKILL.md
```
`agents/frontend.md`: `| \`ux-evaluate\` | Any UI change: UX rows and baseline checks on screenshots |` in `## Available skills`; `- UX:` checklist line; Pillar 3 names `ux-evaluate`.

**DELTA**: the frontend agent gains a UX skill it reads and follows before Ready for Review (nine baseline checks + the guide's UX rows, on screenshots at 375 and 1280); the template gains `### 4. UX Acceptance Criteria`; `code-review` gains one row that reruns the skill (`fail` P1, `fail (older)` P3, `not checked` / `no UX criteria` P2). Measured: no-design builds, blind-judged, 35/35 with the skill vs 29/29 without (round 4).

**WITNESS**: `python3 -m pytest tests/test_t245_ux_evaluate.py -q` → `35 passed`; AC 8 real run table above; round 4 blind scores above.


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

### Round 4: build with no design, blind-judged (2026-11-04, per the user's "build FE without design, it got the poor UX")

Setup: one requirement with no design and no UX rows (habit tracker, static `index.html`/`style.css`/`app.js`, `?state=empty|list|error`). 4 builds, `general-purpose` sonnet, each in its own folder: before = `main` `agents/frontend.md` (b1, b2); after = branch `agents/frontend.md` + `skills/ux-evaluate/SKILL.md` (a1, a2). Same prompt otherwise. Only the 3 page files were copied into folders P/Q/R/T in a random order (Python `random.shuffle`); the key stayed in a separate file. One judge (`general-purpose`, opus) read only those folders and an 8-item rubric that is not the skill's B-a to B-i list. It took 24 screenshots (4 builds × 3 states × 2 widths) and scored each item 1-5.

| Build (blind) | Arm | Clarity | Primary | Status | Empty | Error | Mobile | Polish | Overall | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| T = a1 | after | 4 | 5 | 4 | 4 | 4 | 5 | 5 | 4 | 35 |
| Q = a2 | after | 4 | 5 | 4 | 4 | 5 | 5 | 4 | 4 | 35 |
| P = b1 | before | 4 | 4 | 4 | 3 | 3 | 4 | 4 | 3 | 29 |
| R = b2 | before | 4 | 4 | 4 | 3 | 3 | 4 | 4 | 3 | 29 |

Result: both builds made with the skill rank above both builds made without it (35, 35 vs 29, 29). The judge rated this gap "high" confidence before unblinding: the skill builds have a retry action in the error state, an empty state that names the button, and bigger phone tap targets; the others have none of these. Both skill runs reported a baseline `fail` and fixed it (a1: retry button style, B-i; a2: a wrapped button). Both opened every screenshot; the before runs opened 3 of 8 (b2) and 3 of 7 (b1).
Limits: n = 2 per arm, one judge, one requirement; the judge did not drive the add/tick flow. Self-reported "all pass" from the builds is not part of the score.

## AC 8 real run: `ux-evaluate` on `site/index.html` (Supervisor, 2026-11-04, Stage 4)

Commands: `google-chrome --headless --disable-gpu --hide-scrollbars --window-size=375,2400 --screenshot=/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/f5ea81bb-c349-4953-9f6b-0307a641966a/scratchpad/t245-ac8/index-375.png "file://$PWD/site/index.html"`, then `--window-size=1280,2400` → `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/f5ea81bb-c349-4953-9f6b-0307a641966a/scratchpad/t245-ac8/index-1280.png`. Both opened with `Read`.
Test UX rows (written for this run, from the T245 change to the page): 1 — "a reader sees ux-evaluate under Stage 3: Build"; 2 — "the numbers strip says 36 skills".

| # | User story | Flow / state | Width | Verdict | Screenshot | Reason |
|---|---|---|---|---|---|---|
| 1 | T245 request | Skills by stage | 375 / 1280 | pass | index-375.png, index-1280.png | `ux-evaluate` chip is the last chip of "Stage 3: Build" at both widths, same style as its row |
| 2 | T245 request | numbers strip | 375 / 1280 | pass | index-375.png, index-1280.png | "36 skills" in the strip at both widths (2×2 grid at 375, one row at 1280) |
| B-a | baseline | default | 375 / 1280 | pass | both | the install command with its green "Copy" button is the first and most prominent action, in view at both widths |
| B-b | baseline | default | 375 / 1280 | pass | both | title, one-line pitch, command, then sections in one reading order |
| B-c | baseline | default | 375 / 1280 | pass | both | cards on one grid, equal gaps |
| B-d | baseline | default | 375 | fail | index-375.png | header links "Home" / "Docs" are about 20 px tall at 375; present on `main` too, not caused by this diff |
| B-e | baseline | default | 375 / 1280 | pass | both | body text readable on the dark ground; chip labels are small monospace but readable |
| B-f | baseline | default | 375 / 1280 | pass | both | static page, no empty/loading/error state named |
| B-g | baseline | default | — | not checked: no action was run (the Copy click was not driven) | — | — |
| B-h | baseline | default | 375 | pass | index-375.png | stacked single column, no sideways scroll, the command wraps inside its box |
| B-i | baseline | default | 375 / 1280 | pass | both | one green accent, one chip style, one radius |

ux-evaluate: 9 pass, 1 fail, 1 not checked, 0 not checkable. Overall: fail (the one fail is older than this diff; see review finding R2).

## Verify fail at `e9012dc5` and the fix (2026-11-04)

The auto verify run (session 27f3055e) failed T245 on step 2 of the skill: `--window-size=375` measured `innerWidth=500`, so it judged the 375 images a cropped 500px layout, and a page with a fixed 1100px wrapper looked clean at 375.
Supervisor re-check (Chrome 156.0.8078.79): the 500 comes from `--dump-dom`, which lays the page out at 500px. At `--screenshot` time the viewport is 375. A probe page that rewrites its text on `resize` showed `iw=375 sw=1100 mq400=true` in the 375 PNG. So the 375 layout in the images was right. The real gap the run found holds: `--hide-scrollbars` plus the crop hide sideways overflow (`sw=1100`), so B-h could pass on an overflowing page. Without `--hide-scrollbars` the same page shows a horizontal scrollbar at the bottom of the image.
Fix: step 2 keeps scrollbars at 375 (the bar is the B-h evidence), says never to measure widths with `--dump-dom`, and names the snap `chromium` `/tmp` limit (the run's second finding). Tests: `test_v1_step2_keeps_scrollbars_at_375_so_overflow_shows`, `test_v1_step2_names_the_snap_chromium_tmp_limit` (red on the old step 2, then `37 passed`). Real run of the new command on `site/index.html`: `99948 bytes written` (375) and `114792 bytes written` (1280); the 375 image has a vertical scrollbar only, no horizontal bar, so B-h passes.
Effect on earlier evidence: round 4's judge shots and the AC 8 run used `--hide-scrollbars` at 375, so sideways overflow would not have shown in them; their layouts were real 375 layouts. The build agents b1, b2 and a1 measured `scrollWidth` over DevTools, not from images.
