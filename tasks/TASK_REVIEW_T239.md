# TASK_REVIEW — T239: Pipeline becomes Stage 0–5 with no half numbers

> Sibling of `tasks/TASK_GUIDE_T239.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_stage_names.py` (AC1-AC7, D6); pins updated: `tests/test_auto_mode.py`, `tests/test_tracks.py`, `tests/test_site_content.py`, `tests/test_site_story.py`, `tests/test_site_visual_first.py`, `tests/test_companion_setup.py`, `.claude/hooks/tests/test_pre_agent_validate_guide.py`. Red first at commit `test: red tests` (13 failed, 3 passed) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_stage_names.py tests/test_site_content.py tests/test_site_story.py tests/test_tracks.py tests/test_auto_mode.py -q` -> 380 passed in 1.74s |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests .claude/hooks/tests -q`: 3006 passed, 1 failed (`test_memory_usage_report::test_script_does_not_touch_the_real_repository`, only because files were uncommitted during the run; re-run after commit: pass). `sh scripts/smoke-install.sh`: PASS. `node --test tests/settings_tool/*.mjs`: 59 pass. `node --test tests/site_scrollspy/*.mjs`: 8 pass |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | headless Chrome 1440 px, `file://` URLs. After: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/91713a2d-c4ca-4ba6-9c19-2b966a122175/scratchpad/shots/after_index.png` (six stages, snake 0->1 / 3<-2 / 4->5, arrows intact); before: `.../shots/before_index.png`. Positions read by script: 0@129,818 1@733,818 2@733,983 3@129,983 4@129,1148 5@733,1148 |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | existing hex-colour tests in `tests/test_site_content.py` pass; no colour added, only grid-area rules changed in `site/theme.css` |
| **UI: Responsiveness at target viewports** | ☑ pass | `scrollWidth == clientWidth` on index and docs at 1440 (1425/1425), 768 (753/753); headless Chrome has a minimum window width, so the 375 run measured 485/485 (no overflow, but not a true 375 px) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-02, before any implementation commit; script `before.sh` run in the worktree, with the sample hook event described in the last section):

```
2026-11-02T14:25:46Z
--- stage headings of docs/claude-md/pipeline-stages.md
1:# 5-Stage Agentic Pipeline
23:## Stage 0.5: Requirement Grilling → Creative Brainstorming (The First Mind)
55:## Stage 1: Environment & Provider Setup
119:## Stage 1.5: Sub-Agent Architecture (Dynamic Team Design)
142:## Stage 2: Intent Transformation (Planning) — `/plan`
179:## Stage 3: Parallel Execution via Isolation
202:## Stage 4: Review
245:## Stage 5: Integration & Verification
--- live-file line counts per pattern (git grep, excluding tasks memory docs/brainstorming docs/prd docs/adr reports experiments docs/archive PROJECT_KANBAN.md tests/fixtures)
Stage 0\.5: lines=37 files=18
Stage 1\.5: lines=17 files=11
Phase 0: lines=58 files=29
--- hook readiness warning, sample event (empty Readiness)
⚠ HIGH RISK — project readiness incomplete: `Requirements` line missing; `Direction` line missing; `Codebase map` line missing; `Tech stack` line missing; `Main flow` line missing; `Approved by` line missing. Risk: agents will code on a design nobody checked, and architecture gaps found later cost rework. To fix: fill `PROJECT_SPEC.md` `## Readiness` (run Phase 0 / Stage 0.5 / Stage 1), or ask the user for a `Waived` line (`- **Waived**: user YYYY-MM-DD — reason`). The spawn goes ahead (warning only).
```

**AFTER** (same script, 2026-11-02, after the change; the remaining old-name lines are the mapping note, test baselines that pin pre-T239 text, and `tests/test_stage_names.py` itself):

```
2026-11-02T14:40:00Z
--- stage headings of docs/claude-md/pipeline-stages.md
1:# Stage 0–5 Agentic Pipeline
25:## Stage 0: Define (Requirements → Grilling → Direction)
63:## Stage 1: Set up (Environment → Agent team)
151:## Stage 2: Intent Transformation (Planning) — `/plan`
188:## Stage 3: Parallel Execution via Isolation
211:## Stage 4: Review
254:## Stage 5: Integration & Verification
--- live-file line counts per pattern (git grep, excluding tasks memory docs/brainstorming docs/prd docs/adr reports experiments docs/archive PROJECT_KANBAN.md tests/fixtures)
Stage 0\.5: lines=15 files=5
Stage 1\.5: lines=14 files=5
Phase 0: lines=33 files=15
--- hook readiness warning, sample event (empty Readiness)
⚠ HIGH RISK — project readiness incomplete: `Requirements` line missing; `Direction` line missing; `Codebase map` line missing; `Tech stack` line missing; `Main flow` line missing; `Approved by` line missing. Risk: agents will code on a design nobody checked, and architecture gaps found later cost rework. To fix: fill `PROJECT_SPEC.md` `## Readiness` (run Stage 0 / Stage 1), or ask the user for a `Waived` line (`- **Waived**: user YYYY-MM-DD — reason`). The spawn goes ahead (warning only).
```

**DELTA**: The pipeline reads Stage 0 to Stage 5 with no half numbers; Stage 0 keeps its three stops (Requirements, Grilling, Direction) and the team stop now fires only when `craft-agent` proposes a new role.

**WITNESS**: common-infrastructure agent ran it 2026-11-02 (trace `memory/event-trace/T239.jsonl`); independent witness pending: the Supervisor's auto verify run.
