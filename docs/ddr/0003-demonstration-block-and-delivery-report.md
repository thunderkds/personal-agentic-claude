# 0003. Demonstration block + Delivery Report for post-implementation and post-bugfix output validation

**Status**: Accepted
**Date**: 2026-08-05
**Deciders**: User (hungnh1110@gmail.com), Project Supervisor AI
**Related**: T053 · T054 · T055 · `BRAINSTORMING_LOG.md` (2026-08-05) · builds on the attribution chain T043/T047/T048

---

## Context

The originating request was for "a number or the checklist to validate the output after implementation
or bugfix." Investigation against the actual files found that checklists already exist in both task
flavors, and that a score computed over them would measure the wrong thing.

**What exists today:**

| Flavor | Source | Checkable items |
|---|---|---|
| Implementation | `templates/TASK_GUIDE_template.md` | 22 — Requirement Fidelity Gate (4), Evidence table (9), Completion Checklist (9) |
| Bugfix | `.claude/skills/bugfix/SKILL.md:92-133` | 22 + 1 conditional table — Diagnosis Gates (4), Attempts Log, Stuck checkpoint (3), Fix Gates (4), Cleanup (4), Evidence (3), Step-5 review gate (4) |

Three defects were verified:

1. **These are conformance checklists, not demonstration artifacts.** Ticking all 22 proves the
   process ran; it shows no reader what the implementation does or what the bug did. Only ~4 of 22
   rows on the implementation path and ~3 of 22 on the bugfix path carry content a reader could not
   have predicted before the task began. The rest is a compliance signature.
2. **The implementation path has no before/after anchor.** The bugfix repro loop is the single place
   in the whole system that demonstrates a *delta*. The implementation path has no equivalent — its
   `Verification command run` row proves the new thing passes but never establishes the contrast that
   makes a pass meaningful. Same failure shape as the recorded gotcha *"An assertion never observed
   failing is not evidence"* (3 occurrences: T036/T042/T039).
3. **The bugfix Evidence table is not wired to the merge gate.** The implementation table carries a
   `verify` row whose Notes column `pre_bash_block_unsafe_merge.py` greps for "pass". The bugfix table
   has 3 free-text rows and no `verify` row at all — so the mandated gate is not failing on a bugfix,
   it is structurally absent. It also lacks negative-cases, blast-radius-scope, and the three UI rows,
   leaving Hard-Stop Gates 5 and 6 nothing to bind to.

**Why a decision is needed now**: any fix changes `templates/TASK_GUIDE_template.md`, which
`MANIFEST`/`setup.sh` propagate to every downstream project, and which every future task guide
inherits.

**Gate criteria — 3 of 3 hold** (ADR-eligible; user was asked and chose DDR, since "hard to reverse"
is the weak leg — this is a process-artifact change, not an architectural commitment like ADR-0001):

1. *Hard to reverse* — every guide already generated would carry a dead section; propagates downstream.
2. *Surprising without context* — "why a new block when 22 checks exist?" and "why HTML when Markdown
   was half the code?" both require the reasoning.
3. *Genuine trade-off* — four distinct ones, recorded below.

---

## Decision

We will add a **Demonstration** block to **both** TASK_GUIDE flavors, and render it as a **Delivery
Report**.

**1. The Demonstration block** — identical four-field structure in both flavors, so one renderer
serves both:

| Field | Implementation flavor | Bugfix flavor |
|---|---|---|
| BEFORE | Command showing the thing absent/failing | The Phase 1 repro loop |
| AFTER | Same command, post-change | Same loop, bug no longer reproduces |
| DELTA | One sentence: what a user can now do that they could not before | One sentence: what now behaves correctly |
| WITNESS | Who ran it and when — derived from the event trace, never the implementing agent alone | same |

**2. BEFORE has no `N/A` path.** When the task changes executable code, BEFORE is a pasted,
timestamped terminal capture. When it does not (docs, templates, skill-instruction text), BEFORE is
the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**3. The Delivery Report** is a self-contained `.html` file rendered from a new
`templates/delivery_report_template.html` by a new `delivery-report` skill. It conforms to the
canonical `Report` glossary shape (HTML, self-contained, `reports/`-hosted) but carries **no scored
dimensions and no findings table** — it demonstrates what a task delivered, it does not assess it.

**4. It fires at Stage 5, after `verify` passes and before merge.**

**5. Invocation is a reminder plus a spawn-time warning, not automatic and not blocking.** Nothing in
this system can auto-invoke a skill — `html-report` and `thinking-report` are both "Invoked by the
Supervisor", i.e. discipline; hooks can only print to stderr or block a Bash command. We extend the
`stop_review_reminder.py` pattern to print `Run: Skill({ skill: 'delivery-report' })` for a verified
task lacking one, and add a **non-blocking blank-BEFORE warning** to `pre_agent_validate_guide.py` at
spawn time, alongside its existing `Depends on` warning.

**6. Bugfix Evidence-table parity** (defect 3) is fixed as an independent task, bringing that table to
the implementation flavor's gate-visible shape including the `verify` row.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| **Demonstration block + HTML Delivery Report (chosen)** | Fixes all 3 defects; applies to both flavors by construction; follows the `thinking-report` precedent; the count the user asked for now counts something meaningful | Largest surface (~300 lines, 3 tasks); WITNESS remains partly claim-shaped | **Selected** |
| A score over the existing 22 checklist items | Trivial to build; literally what was asked for | Produces a confident-looking number measuring process conformance, not delivered outcome | Rejected — measures the wrong thing; would have *legitimised* the false-Evidence pattern with a metric |
| Extend `html-report` with `mode=delivery` | Smallest diff; no new skill or MANIFEST change | `report_template.html`'s slots are review-shaped (`{{RISK_SCORE}}`, `{{FINDINGS_ROWS}}`); needs fake scores or unsupported conditional suppression | Rejected — contradicts the recorded *"thinking-report is separate from html-report"* decision, made for exactly this situation; slots are load-bearing in HTML **and** CSS width attributes |
| Demonstration block only, no report | ~15% of the cost; fixes the substantive defect | A markdown block inside a TASK_GUIDE has no reader — guides are read by agents at spawn and the Supervisor at review, never to see what shipped | Rejected — real work, zero value against the stated goal ("show off" means handing someone a link) |
| Markdown Delivery Report instead of HTML | Removes the template file, slot-filling, and theming — the largest single chunk (~120 lines) | Violates the canonical `Report` term on format, stage, and content | Rejected by user — the artifact's purpose is to be shown to someone, and a browsable page serves that better than a file in a gitignored directory |
| Widen the `Report` glossary term to cover `.md` and Stage 5 | One-line glossary edit | Edits a term 4 skills depend on, to accommodate one new consumer; weakens its discriminating power | Rejected — `thinking-report` set the precedent that a different artifact earns a *new* term |
| Block the merge when the Demonstration block is incomplete | Actually enforced, not skippable | Enters a hook family with 6 recorded parsing defects (T018/T022/T024/T042/T045 + Kanban `###` truncation) | Deferred, not rejected — the reminder first produces the evidence for whether blocking is needed |
| Allow `N/A` on BEFORE with a written justification | Cheap and honest-looking | Becomes the default escape. The three UI Evidence rows are the control experiment already running in this repo, and mostly carry `☐ N/A` | Rejected — of the last 4 completed tasks (T049/T050/T051/T052) only T050 has a runnable BEFORE, so the N/A path would be the *majority* path, not an edge case |

---

## Consequences

### Positive
- Every task gains an observable before/after anchor; the implementation flavor gets one for the first time.
- The BEFORE capture cannot be back-filled for executable work — it must be taken before the code exists, unlike all 22 existing checklist rows, which are satisfiable by assertion.
- Defect 3 is closed: the bugfix Evidence table becomes visible to the merge gate.
- A reader can be handed a URL that shows what a task delivered, without reading a TASK_GUIDE.
- The completion count the user originally asked for exists, computed over demonstration content rather than conformance boilerplate.

### Negative (accepted trade-offs)
- **`Delivery Report` becomes the first `reports/` artifact that is not Stage 4.** "Everything in `reports/` comes from Stage 4" stops being true; `Report`/`Report Session` keep their Stage 4 clauses and remain accurate for what they describe. A small, real loss of regularity.
- **~300 lines instead of the ~180 the Markdown form would have cost.** Accepted deliberately for the artifact's purpose.
- **A non-executable BEFORE is reconstructible from `git show HEAD~1`.** For the task type that dominates this repo, BEFORE degrades from un-forgeable proof to documentation. Partial mitigations only: trace-derived WITNESS, and a spawn-time warning that fires before code exists — making back-fill *detectable*, not impossible. No full fix exists inside the chosen option.
- **The reminder protects the report, not the capture.** A Stage 5 reminder fires long after the only moment a BEFORE could have been captured truthfully; the spawn-time warning is the substantive half.
- **WITNESS is the most claim-shaped field in the design** — a name and a date, exactly the pattern memory warns about. Mitigated only if it is genuinely derived from `memory/event-trace/<task>.jsonl` rather than typed.

### Follow-up
- [ ] **T053** — `## Demonstration` block in both guide flavors; `craft-spawn-prompt` BEFORE-capture instruction; blank-BEFORE warning in `pre_agent_validate_guide.py`
- [ ] **T054** — `delivery-report` skill + `templates/delivery_report_template.html` + `MANIFEST` + `CLAUDE.md`/`CLAUDE_LEGACY.md` sync + reminder hook
- [ ] **T055** — bugfix Evidence-table parity with the gate-visible implementation shape
- [ ] Revisit merge-gate blocking once the reminder has run for enough tasks to show whether it is honored or ignored
- [ ] Confirm WITNESS is trace-derived, not typed, before T054 closes — otherwise the field's stated mitigation is fiction
- [x] Verify no guide-hook regex depends on TASK_GUIDE section ordering — **checked 2026-08-05**: all regexes in `post_write_register_task.py` and `pre_agent_validate_guide.py` are field-anchored (`**Depends on**:`, `Complexity Level:`, `^# TASK_GUIDE`); the ordering-sensitive parser is `find_kanban_section`'s `(?=###|\Z)`, which constrains Kanban row text only, not the template
