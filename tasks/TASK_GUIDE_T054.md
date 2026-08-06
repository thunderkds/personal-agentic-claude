# TASK_GUIDE — T054: delivery-report skill + HTML template + reminder hook + harness sync
**Date**: 2026-08-05
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from `.claude/agents/general-agent-template.md`
6. Read `docs/ddr/0003-demonstration-block-and-delivery-report.md` — this task implements decisions 3, 4 and 5
7. Read `.claude/skills/thinking-report/SKILL.md` and `templates/thinking_report_template.html` — the precedent this task copies
8. C2 task: read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Original user request (verbatim, opening message):

> "we should have number or the checklist to validation the list"

and, on the artifact's purpose:

> "is it good to show off the whole implementation or the bugs fix"

and, on format, when offered Markdown vs. conforming to the canonical `Report` term:

> "html i think"

**Restated intent**:
> Render a task's Demonstration block as a browsable, self-contained HTML page that someone can be
> handed as a link to see what the task delivered — including the completion count over the Evidence
> table that the original "number" request asked for.

**Out of scope**:
- The Demonstration block itself (T053)
- Bugfix Evidence-table parity (T055)
- Any scored dimension, risk percentage, or findings table — a Delivery Report demonstrates, it does not assess (DDR-0003 decision 3)
- Merge blocking

**Requirement Refs**: DDR-0003 decisions 3, 4, 5; `PROJECT_SPEC.md` glossary term `Delivery Report`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary — `Delivery Report`, `Demonstration`, `BEFORE capture` added 2026-08-05
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist and are fully covered by the Acceptance Criteria above

---

## Dependencies & Reachability

**Depends on**: T053 — the `## Demonstration` block must exist in both guide flavors before there is anything to render

**Entry point**: `Skill({ skill: "delivery-report" })`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/skills/delivery-report/SKILL.md` exists and reads a task's Demonstration block from **either** guide flavor with one parser | "apply for the implementation and bugfix" |
| 2 | `templates/delivery_report_template.html` exists, is self-contained (no external assets), and uses the established dark neon theme | recorded decision: dark neon theme on report templates |
| 3 | The rendered page shows BEFORE and AFTER side by side, DELTA as the headline, and the Evidence table as a completion count (`filled / total / N-A`) | the original "number" request |
| 4 | The report carries **no** scored dimension, risk percentage, or findings table | DDR-0003 decision 3 — Delivery Report demonstrates, does not assess |
| 5 | Output is saved to `reports/delivery-report_<branch>_<YYYYMMDDTHHMMSS>.html`, matching the established naming convention | recorded: "Report filename: skill_branch_timestamp.html" |
| 6 | The skill's description states it is invoked at **Stage 5, after `verify` passes and before merge** | DDR-0003 decision 4 |
| 7 | `WITNESS` is derived from `memory/event-trace/<task>.jsonl`, **not** accepted as free text | DDR-0003 follow-up — blocks this task closing |
| 8 | A reminder fires for a verified task that has no delivery report, following the `stop_review_reminder.py` stderr pattern | DDR-0003 decision 5 |
| 9 | `MANIFEST` gains the new skill and template paths so `setup.sh`/`update.sh` deploy them downstream | recorded: T049 MANIFEST omission, T051 MANIFEST conflict |
| 10 | `CLAUDE.md` stage index and `CLAUDE_LEGACY.md` both list the new skill, version bumped | recorded decision: CLAUDE_LEGACY.md sync policy |
| 11 | Findings/field text is wrapped in `<pre>`, never manually HTML-escaped | recorded: "html-report findings use `<pre>`" |
| 12 | Rendering a task whose Evidence table is still blank shows the gap explicitly rather than omitting those rows | DDR-0003 edge case |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `tasks/TASK_GUIDE_T053.md` (implementation flavor, Demonstration filled) | Valid self-contained HTML at the conventional path, BEFORE/AFTER/DELTA/WITNESS all populated | manual run + file assertion |
| 2 | A bugfix-flavor guide with a filled Demonstration block | Same parser produces an equivalent page — no flavor-specific code path | automated test |
| 3 | A guide with a blank Evidence table | Count renders as `0 / 9 filled`, blank rows visibly marked, page still valid | automated test |
| 4 | Field text containing `<`, `>`, `&` | Renders literally inside `<pre>`, no broken markup, no double-escaping | automated test |
| 5 | A task with no `memory/event-trace/<task>.jsonl` | WITNESS renders as explicitly underived — never a fabricated name | automated test |
| 6 | Full existing suite | Still green | `python3 -m pytest .claude/hooks/tests -q` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q && bash scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_delivery_report_render.py` — 8 tests: AC1 both-flavor parity, SC2-SC5, no-Demonstration edge case, slot completeness |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `177 passed in 5.67s`, re-run by the Supervisor after committing the agent's unverified `stop_review_reminder.py` edit |
| Negative cases hold | ☑ pass | SC3 blank Evidence renders the gap; SC4 `<`/`>`/`&` render literally inside `<pre>` with no double-escaping; SC5 missing trace → WITNESS explicitly underived, never fabricated |
| verify | ☑ pass | Real end-to-end render, not asserted: `render.py T053 tasks/TASK_GUIDE_T053.md t054-delivery-report` → `reports/delivery-report_t054-delivery-report_20260806T094426.html`, 9380 bytes, `grep '{{[A-Z_]*}}'` returns zero unfilled slots — pass |
| Review scope bounded to the change's blast radius | ☑ pass | 6 files: new skill dir (SKILL.md + render.py), new template, reminder hook, CLAUDE.md, CLAUDE_LEGACY.md, new test file. `report_template.html`, `html-report/SKILL.md`, `pre_bash_block_unsafe_merge.py` and `TASK_GUIDE_template.md` all untouched per Files Must NOT Touch |
| Full smoke suite still green (no regression) | ☑ pass | `177 passed`; no pre-existing test modified |
| **UI: Visual regression** | ☑ pass | No prior baseline (new artifact), so verdict-based: rendered page is valid self-contained HTML — 0 external assets (`src="http`/`href="http`/`@import`/CDN all absent), correct section order (header → Before/After → DELTA → Witness → Evidence Completion), 12 `<pre>`-wrapped field blocks |
| **UI: Design-system compliance** | ☑ pass | Palette matches `templates/report_template.html`: `#0a0a12`, `#111128`, `#16162e`, `#1e1e42`, `#00d4ff`, `#00ff88` all shared. No scoring slots leaked in (`grep -ci risk_score\|code_quality\|adaptation\|findings` → 0), per DDR-0003 decision 3 |
| **UI: Responsiveness** | ☑ pass | `max-width: 980px` container fits 1024px with no horizontal scroll; BEFORE/AFTER uses `display:flex` + `flex: 1 1 320px`, so panes wrap to stacked on narrow viewports without a media query; wide content sits in `overflow-x: auto` |

> Note: unlike T053 and T055, this task **does** produce a visual surface. The three UI rows are live,
> not N/A, and Hard-Stop Gate 6 applies.

---

## Demonstration

**BEFORE**: no `delivery-report` skill and no delivery template exist.
`ls .claude/skills/delivery-report/ templates/delivery_report_template.html` → expect `No such file or directory` for both.
There is no way to see what any completed task delivered except by opening its TASK_GUIDE.

**AFTER**: same command lists both files; running the skill against T053's guide produces
`reports/delivery-report_<branch>_<timestamp>.html`, openable in a browser, showing T053's BEFORE/AFTER
side by side.

**DELTA**: a completed task can be handed to someone as a link that shows what it delivered, instead
of a guide file they would have to know how to read.

**BEFORE captured pre-implementation** (2026-08-06, before the first commit):
```
$ ls .claude/skills/delivery-report/ templates/delivery_report_template.html
ls: cannot access '.claude/skills/delivery-report/': No such file or directory
ls: cannot access 'templates/delivery_report_template.html': No such file or directory
```

**AFTER** (real run, post-implementation):
```
$ python3 .claude/skills/delivery-report/render.py T053 tasks/TASK_GUIDE_T053.md t054-delivery-report
SAVE → reports/delivery-report_t054-delivery-report_20260806T094426.html
$ grep -o '{{[A-Z_]*}}' reports/delivery-report_*.html | sort -u
(no output — zero unfilled slots)
```
The rendered page shows T053's BEFORE and AFTER side by side, its DELTA as the headline, and
`6 / 9 filled` over the Evidence table — the completion count the original "number" request asked for.

**WITNESS**: Supervisor, 2026-08-06, on branch `t054-delivery-report`. The implementing agent was
killed by the step-limit hook at 42 calls before committing anything; the Supervisor committed its
work, re-ran the suite to check its one unverified edit, completed the CLAUDE.md/CLAUDE_LEGACY.md
registration it never reached, and performed the visual sign-off — which the guide assigns to the
Supervisor precisely so the implementer is not its own sole oracle.

Note on this task's own WITNESS field: `render.py` would report it as **underived**, because
`memory/event-trace/T054.jsonl` is local-only and absent here. That is the correct behaviour (AC7)
and is exactly what it did when rendering T053 — whose guide contains a typed WITNESS paragraph that
the renderer refused to echo.

---

## Approach

**Pattern reference**: `.claude/skills/thinking-report/SKILL.md` + `templates/thinking_report_template.html`
— the exact precedent for a second report type with its own skill, own template, and own trigger.
Copy its structure: slot table, save-path convention, notification line. Do **not** copy
`report_template.html`'s scoring slots — a Delivery Report has no scores, and DDR-0003 rejected
overloading `html-report` for precisely this reason.

The single parser serving both flavors (AC1) is what makes the "both implementation and bugfix"
requirement hold structurally rather than by discipline — T053 gives both flavors identical field
names and ordering specifically to enable this. If a flavor-specific branch appears in the parser,
that is a signal T053's block shapes have drifted apart; stop and report to the Supervisor.

AC7 is the one that decides whether this design keeps its integrity. DDR-0003 states plainly that
WITNESS is "the most claim-shaped field in the design" and that its mitigation is fiction if shipped
as a typed field. The attribution chain T043 → T047 → T048 exists and works; use it.

---

## Edge Case Checklist

- [ ] Two tasks complete in the same second — filename collision on the timestamp convention
- [ ] `reports/` is gitignored (except the token-audit exception) — confirm whether a delivery report generated inside a worktree needs to survive the merge before choosing its path (recorded: "Worktree-isolated files silently die if gitignored")
- [ ] Demonstration block present but BEFORE blank — render the gap, do not silently succeed
- [ ] Guide predates T053 and has no Demonstration section at all — skill must report this clearly, not crash
- [ ] `MANIFEST` is append-only and shared — expect a merge conflict if another task touches it concurrently (recorded: T051 hit exactly this against T049)
- [ ] Bugfix flavor's BEFORE points at the Phase 1 repro loop rather than containing it — parser must resolve the reference, not print it raw
- [ ] Event trace exists but contains no record for this task — WITNESS underived, must not fall back to a guessed name
- [ ] Template slot left unfilled renders a literal `{{SLOT}}` into the page — assert none remain after rendering
- [ ] **A filled-looking BEFORE is not proof a capture happened.** Verified 2026-08-06 against T053's shipped advisory: `before_field_is_blank` only detects an empty field or an unfilled `[...]`/`<...>` placeholder, so *any* prose — including a sentence describing what the author intends to capture later — satisfies it. This task must not present BEFORE as verified evidence; render what the field contains, and treat "the spawn hook didn't warn" as no signal at all

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/delivery-report/SKILL.md` | New skill |
| `templates/delivery_report_template.html` | New template, dark neon theme, no scoring slots |
| `.claude/hooks/stop_review_reminder.py` | Add the delivery-report reminder for verified tasks |
| `MANIFEST` | Register both new paths |
| `CLAUDE.md` | Stage index gains `delivery-report` under Stage 5; version bump |
| `CLAUDE_LEGACY.md` | Mirror per sync policy |
| `.claude/hooks/tests/` | New tests for SC2–SC5 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `templates/report_template.html` | Stage 4 reports render from it; slots load-bearing in HTML + CSS |
| `.claude/skills/html-report/SKILL.md` | Separate artifact, separate trigger (DDR-0003) |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Merge blocking deferred |
| `templates/TASK_GUIDE_template.md` | T053 owns it |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Test Plan

Automated tests for SC2–SC5 (both-flavor parity, blank Evidence, escaping, missing trace) plus an
assertion that no `{{SLOT}}` survives rendering. Manual browser check for the three UI Evidence rows.
Because this task's own acceptance depends on a rendered page, the Supervisor — not the implementing
agent — signs off the visual verdict; the implementer must not be its own sole oracle.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — Medium risk, mandatory
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence (Hard-Stop Gate 5)
- [ ] All three UI Evidence rows filled with pasted evidence (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] AC7 confirmed: WITNESS is trace-derived, not typed — task may not close otherwise
- [ ] Demonstration block filled, BEFORE captured before the first implementation commit
- [ ] Supervisor notified: task ready for Stage 4 review
