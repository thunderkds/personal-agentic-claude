# TASK_GUIDE — T027: DDR (Design Decision Record) — default decision artifact, ADR as rare escalation
**Date**: 2026-07-16
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)
1. Read `PROJECT_SPEC.md` (glossary now includes **DDR**, **ADR** (redefined), **decisions.md entry** — added this session)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `templates/ADR_template.md` in full — DDR's template is a structural clone with a loosened gate, not a redesign
6. Read `.claude/skills/grill-with-docs/SKILL.md` in full — its "Where decisions land" section (lines 43-46) is the exact spot that needs DDR-first / ADR-escalation wiring

---

## Requirement (Pillar 1 — Adapt the requirement)

User request: introduce DDR as the primary, low-ceremony decision-record artifact for day-to-day design decisions ("architecture in the app hardly changes... if you change it, it's optional, not required by the time"), keeping ADR as an optional, rare escalation. Explored via `Skill({ skill: "brainstorming" })` (`BRAINSTORMING_LOG.md`, 2026-07-16, Option A approved) and sharpened via `Skill({ skill: "grill-with-docs", args: "mode=terminology" })`.

**Restated intent**: Three decision-capture tiers now exist, ordered by ceremony:
1. **`memory/decisions.md` entry** — a one-liner/short paragraph in the rolling log, written for every decision regardless of tier (unchanged from today).
2. **DDR** — the **default** standalone artifact for real design decisions. One file per decision at `docs/ddr/NNNN-title.md`, referenced as `DDR-NNNN`. Gated at **2-of-3** of the ADR criteria (hard to reverse / surprising without context / genuine trade-off).
3. **ADR** — the **rare escalation**, unchanged in its own gate (still 3-of-3), but now framed as sitting *above* DDR rather than being the only standalone option. One file per decision at `docs/adr/NNNN-title.md`, referenced as `ADR-NNNN`.

`grill-with-docs` (terminology mode) checks the DDR gate first. If a decision also clears all 3 ADR criteria, it is flagged ADR-eligible and the Supervisor asks the user whether to escalate to a full ADR instead — DDR is never silently auto-upgraded. When a DDR or ADR file is written, the corresponding `decisions.md` entry gains a `→ see DDR-NNNN` / `→ see ADR-NNNN` pointer, mirroring the existing `MEMORY.md → decisions.md` link pattern.

**Out of scope**:
- Does not loosen ADR's existing 3-of-3 gate — ADR is supplemented, not changed.
- Does not retroactively split the existing 149-line `memory/decisions.md` into individual DDR files — this task drafts the mechanism only (per Edge Case Checklist in `BRAINSTORMING_LOG.md`).
- Does not build a DDR/ADR index or supersession-graph skill (BRAINSTORMING_LOG Option B, rejected — no scale problem exists yet with zero DDRs/ADRs currently on disk).
- Does not touch `.claude/skills/compound/SKILL.md` or `docs/solutions/` — different axis (reactive problem→solution capture), confirmed out of scope in brainstorming.

**Requirement Refs**: none (internal framework tooling, no `PRD.md` — same precedent as T023/T025).

### Requirement Fidelity Gate (sign off BEFORE implementation)
- [x] Restated intent confirmed to match the request (Supervisor, informed by approved brainstorming Option A)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (DDR / ADR / decisions.md entry added via `grill-with-docs` this session)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `.claude/skills/grill-with-docs/SKILL.md` "Where decisions land" section — the DDR-gate-first / ADR-escalation logic must appear there, since that's the only place either artifact is currently offered (Stage 2, before `to-issues`).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/DDR_template.md` exists, structurally mirrors `templates/ADR_template.md` (Status/Date/Deciders/Related, Context, Decision, Alternatives Considered, Consequences), with a header note stating the **2-of-3** gate and `docs/ddr/NNNN-title.md` path | DDR artifact shape |
| 2 | `templates/DDR_template.md`'s `Related` field supports `supersedes DDR-000X` / `superseded by DDR-000Y`, mirroring ADR's own supersession field | Edge case checklist item 4 |
| 3 | `.claude/skills/grill-with-docs/SKILL.md` "Where decisions land" section checks the DDR gate (2-of-3) first; if a decision also clears all 3 ADR criteria, flags it ADR-eligible and asks the user before escalating — DDR is not auto-upgraded | DDR-default/ADR-escalation wiring |
| 4 | `CLAUDE.md` folder-structure requirements list includes `templates/DDR_template.md`; the ADR-only sentence in Step 1.5's Ambiguity Resolution Protocol is updated to mention DDR as the default and ADR as the rare escalation | Surgical scope |
| 5 | `PROJECT_SPEC.md` glossary already contains DDR/ADR/decisions.md-entry terms (done this session, verify unchanged) | Terminology lock |
| 6 | DDR and ADR numbering sequences are independent (both may start at `0001`); cross-references disambiguate via `DDR-NNNN`/`ADR-NNNN` prefix, never bare `NNNN` | Edge case checklist item 2 |
| 7 | `grill-with-docs` terminology-mode wording does not blur into requirement-mode's distinct responsibilities — the DDR/ADR gate logic lives only in the terminology-mode section | Edge case checklist item 5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A synthetic decision meeting exactly 2-of-3 criteria (e.g. hard to reverse + genuine trade-off, but not surprising) | `grill-with-docs`'s updated instructions would offer a DDR, not an ADR | Manual dry-run walkthrough (no runtime harness in this repo — same precedent as T018/T023/T025) |
| 2 | A synthetic decision meeting all 3 ADR criteria | Instructions flag it ADR-eligible and ask before escalating, rather than defaulting straight to DDR | Manual dry-run walkthrough |
| 3 | A synthetic decision meeting 0-1 criteria | Instructions route it to a `decisions.md`-only entry, no DDR/ADR offered | Manual dry-run walkthrough |
| 4 | `templates/DDR_template.md` diffed against `templates/ADR_template.md` | Structurally parallel (same section headings/order), differing only in gate wording and file path | Manual diff read |

### Verification Command (exact, runnable)

```bash
# Structural checks — no test harness exists in this repo (same precedent as T018/T023/T025)
test -f templates/DDR_template.md && echo "DDR template exists"
grep -n "2-of-3\|2 of 3" templates/DDR_template.md
grep -n "DDR" .claude/skills/grill-with-docs/SKILL.md
grep -n "DDR" CLAUDE.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | No automated test suite exists in this doc/skill-framework repo (confirmed precedent: T018, T023, T025). Substitute evidence = `templates/DDR_template.md` diffed against `templates/ADR_template.md` by the Supervisor directly (not self-graded by the implementing agent): identical section order/headings (Context/Decision/Alternatives Considered/Consequences), differing only in gate (2-of-3 vs 3-of-3), path (`docs/ddr/` vs `docs/adr/`), and prefix terminology. `.claude/skills/grill-with-docs/SKILL.md` lines 46-49 confirmed to contain the DDR-gate-first / ADR-escalation-flag / 0-1-criteria decisions.md-only branches. |
| verify | ☑ pass | `T027 Stage 5 verify: re-running exact TASK_GUIDE_T027.md verification command` → `DDR template exists` → `gate wording present` → `grill-with-docs wired` → `CLAUDE.md wired` → `T027 verify: PASS`. Re-run by Supervisor against the worktree post Stage-4 fix (commit c105420). Recorded in `memory/event-trace/T027.jsonl`. |
| Negative cases hold | ☑ pass | `grill-with-docs` SKILL.md:48 confirmed present: "If fewer than two of the three criteria hold, skip both DDR and ADR — note the decision in memory/decisions.md only" |
| Review scope bounded to the change's blast radius | ☑ pass | Scope: `templates/DDR_template.md` (new), `.claude/skills/grill-with-docs/SKILL.md` (1 section + 1 review-fix line), `CLAUDE.md` (2 edits). `git diff main --stat` on `feat/ddr-decision-record` confirms no other files touched. |
| Full smoke suite still green (no regression) | ☐ N/A | No smoke suite in this repo |
| UI rows | ☐ N/A | Not a UI task — no UI/Design AC section below |

---

## Approach

1. **Clone the template**: copy `templates/ADR_template.md` to `templates/DDR_template.md`, change the header note to state the 2-of-3 gate, change the path convention to `docs/ddr/NNNN-title.md`, keep `Related` field's supersession pattern (`supersedes DDR-000X` / `superseded by DDR-000Y`).
2. **Wire `grill-with-docs`**: in the "Where decisions land" section (terminology mode only), replace the single ADR bullet with: check DDR's 2-of-3 gate first → offer a DDR if met → if all 3 ADR criteria are ALSO met, flag ADR-eligible and ask the user before escalating → if 0-1 criteria met, decisions.md-only.
3. **Update `CLAUDE.md`**: add `templates/DDR_template.md` to the folder-structure requirements list (alongside the existing `templates/ADR_template.md` line); reword the Step 1.5 Ambiguity Resolution Protocol sentence that currently says "...an ADR/`grill-with-docs`" to mention DDR as the default.
4. Do not touch `templates/ADR_template.md`'s own gate (still 3-of-3) or `memory/decisions.md`'s existing structure.

---

## Edge Case Checklist

- [ ] A decision meets DDR's 2-of-3 gate AND all 3 ADR criteria simultaneously — flag ADR-eligible, ask before defaulting to DDR-only, never silently downgrade
- [ ] Numbering collision — `docs/ddr/` and `docs/adr/` use independent sequences; cross-references always use `DDR-NNNN`/`ADR-NNNN` prefix, never bare `NNNN`
- [ ] Retro-filing existing `decisions.md` history into DDR files — explicitly out of scope for this task
- [ ] DDR later superseded — `Related` field supports `supersedes DDR-000X` / `superseded by DDR-000Y`
- [ ] DDR/ADR gate logic must live only in `grill-with-docs`'s terminology-mode section, not blur into requirement mode

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/DDR_template.md` | New, cloned from `templates/ADR_template.md` with 2-of-3 gate |
| `.claude/skills/grill-with-docs/SKILL.md` | "Where decisions land" section: DDR-gate-first, ADR-escalation logic |
| `CLAUDE.md` | Folder-structure requirements list + Step 1.5 Ambiguity Resolution Protocol sentence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `templates/ADR_template.md` | Its 3-of-3 gate is unchanged — DDR supplements, doesn't replace |
| `memory/decisions.md` | Structure unchanged; future entries gain an optional pointer, not a schema change |
| `.claude/skills/compound/SKILL.md`, `docs/solutions/` | Different axis (reactive problem→solution), out of scope |

---

## Test Plan

Manual dry-run walkthroughs (no automated test harness exists in this repo, per T018/T023/T025 precedent):
1. Dry-run a synthetic 2-of-3 decision — confirm DDR offered, not ADR.
2. Dry-run a synthetic 3-of-3 decision — confirm ADR-eligible flag + escalation question, not silent DDR.
3. Dry-run a synthetic 0-1 decision — confirm decisions.md-only, no DDR/ADR offered.
4. Diff `templates/DDR_template.md` against `templates/ADR_template.md` — confirm structural parity minus the gate/path differences.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Risk: Low)
- [ ] Lint passes — N/A (Markdown only)
- [ ] Tests written AND pass — manual dry-run walkthroughs pasted into Evidence table (Hard-Stop Gate 5, per T018/T023/T025 substitute precedent)
- [ ] `Skill({ skill: "verify" })` run — re-run the exact Verification Command for real and paste output (per T025 gotcha — Check cell must read exactly "verify")
- [ ] `memory/MEMORY.md` updated (DDR decision + one-liner)
- [ ] Supervisor notified: task ready for Stage 4 review
