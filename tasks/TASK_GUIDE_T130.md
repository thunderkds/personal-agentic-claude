# TASK_GUIDE — T130: The site describes the agent-focus work (T124–T129) and stops contradicting it
**Date**: 2026-09-25
**Complexity Level**: C1
**Risk Level**: Low — static page content and drift tests; no script, no CSS token change
**Priority**: P1
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read the sources the page must describe — never the README: `skills/craft-spawn-prompt/SKILL.md` (elements 4 and 8), `skills/craft-spawn-prompt/scripts/memory_slice.py` (`MAX_LINES`, `MAX_CHARS`), `.claude/hooks/pre_agent_validate_guide.py` (every warning it prints), `docs/claude-md/token-economy.md`, `skills/compact-advisor/SKILL.md` Step 2a, `skills/code-review/SKILL.md` (over-engineering reviewer, Startup-reads check), `MANIFEST`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25, after T123–T129 merged into `tokenization-refactor`: *"update the site for this improvement"*.

**Observed defects on `site/index.html` (measured by the Supervisor, 2026-09-25):**
- Memory System table, `memory/MEMORY.md` row: *"referenced by path in every sub-agent spawn prompt and read by the agent — not pasted"*. Since T125 this is false: each spawn prompt carries a pasted **memory slice**, and the full file is read only as a fallback.
- Hooks table, `pre_agent_validate_guide.py` row says only *"blocks spawn if the TASK_GUIDE is missing"*. Since T125/T129 it also **advises** (never blocks) when a spawn prompt has no memory slice or no `**Startup reads**` block.
- Nothing on the page describes the agent-focus work at all: focused spawn prompts, the Response Standard (short replies, verbatim code/errors/paths), the over-engineering reviewer, the Startup-reads check at review.

**Restated intent:**
> The page tells a visitor, from source files, how the kit keeps each agent focused on its request and
> its replies short without losing exact detail — and no longer states the old "not pasted" behaviour.
> Drift tests make the next change to these mechanisms fail the suite instead of leaving the page wrong.

**Out of scope:**
- Savings figures. DDR-0009's evaluation window is open (3 of 5+ spawns measured, target not met) — publishing a number now would be a claim the data does not support.
- `scripts/token_meter.py`: it lives in the kit repo only (`MANIFEST` does not ship `scripts/`), so the page must not present it as something an install gets.
- The site's other sections, the sidebar JS, CSS tokens, the hot-tier cap figure (already drift-tested), `PROJECT_KANBAN_SITE.md` housekeeping.

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's request and the defects above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user request 2026-09-25; scope set by the Supervisor from the measured defects)
- [x] Domain terms align: *memory slice*, *startup reads*, *spawn prompt*, *Response Standard*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: T125, T127, T129 — the mechanisms the page describes (all Done on `tokenization-refactor`)

**Entry point**: `site/index.html` — the sidebar nav link `#agent-focus`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Memory System, `memory/MEMORY.md` row: states that each spawn prompt carries a pasted **memory slice** (the index lines naming the task's files, dependencies or ID) and the agent reads the whole file only if its work reaches what the slice misses. The words "not pasted" are gone. The cap figure stays exactly as it is | defect 1 |
| 2 | Hooks table, `pre_agent_validate_guide.py` row: keeps the block, and adds that it **advises** without blocking when the prompt lacks a memory slice or a `**Startup reads**` block — worded from the hook's real messages; if the hook prints other advisories, list them too or say "and other spawn-readiness warnings" | defect 2 |
| 3 | New section `<section id="agent-focus">` with an `<h2>`, and a sidebar link to it in the nav group that fits best. It covers, each in plain words from source: (a) the spawn prompt carries a memory slice capped at `MAX_LINES` lines / `MAX_CHARS` characters plus a `**Startup reads**` list, and the agent ends its report with a `Startup reads:` line; (b) the Response Standard — short replies, but code, exact errors, paths, commands and security warnings are quoted verbatim, and the audit trail (board, guides, decisions, commits) stays fully detailed; (c) Stage 4 `code-review` runs an over-engineering reviewer and checks the agent's `Startup reads:` line; (d) token work is measured from session transcripts before it is kept (DDR-0009), with no savings figure | defect 3 |
| 4 | Drift tests in `tests/test_site_content.py`: (i) the MEMORY.md row mentions "memory slice" and not "not pasted"; (ii) the hook row mentions both the memory slice and Startup reads; (iii) the slice caps on the page equal `MAX_LINES` / `MAX_CHARS` **read from `memory_slice.py` at test time**, never hardcoded (the T089 AC8 pattern); (iv) the page does not name `token_meter` while `MANIFEST` does not ship `scripts` | can't rot silently |
| 5 | Existing tests stay green unchanged, including every-nav-link-resolves / every-section-has-a-link, no-external-assets, all-scripts-inline | no regression |
| 6 | No new CSS custom property or colour; the new section reuses existing classes (`lead`, `table-wrap`, `code`, `tag-*`) | design system |

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#memory-system`, `#hooks`, new `#agent-focus` | headless `google-chrome --screenshot` of the served page, BEFORE vs AFTER, at 1280px; LLM-vision verdict | Only the two rows and the new section differ; nothing else moves |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | `git diff` of the `<style>` block | empty — no style change |
| Typography matches spec | screenshot | new section's `h2`/`p` match the neighbouring sections |
| Spacing / layout matches spec | screenshot | same section spacing as `#memory-system` |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375px) | headless chrome, `document.documentElement.scrollWidth <= innerWidth` + screenshot | no horizontal page scroll; any table scrolls inside `.table-wrap` |
| Tablet (768px) | same | same |
| Desktop (1280px) | screenshot | sidebar shows the new link; scroll-spy highlights it on the section |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Current page | new AC4 tests RED (i, ii, iii at least) | pytest, before editing the page |
| 2 | Edited page | all of `tests/test_site_content.py` green | pytest |
| 3 | Served page | AC3 content visible, nav link jumps to it | headless chrome |

**Mutation controls:** **M1** — put back "not pasted" → (i) RED. **M2** — change `MAX_LINES` in a scratch copy of `memory_slice.py` (or monkeypatch the reader) → (iii) RED, proving the cap is read, not hardcoded. **M3** — add `scripts/token_meter.py` to the page → (iv) RED. **M4** — remove the `#agent-focus` nav link → the existing every-section-has-a-link test RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T130.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T130.md`. BEFORE: the two rows verbatim plus a 1280px screenshot of
> `#memory-system`. AFTER: the same, plus the new section.

---

## Approach

**Pattern reference**: `test_memory_cap_matches_enforced_budget` and `_enforced_hot_tier_budget` in `tests/test_site_content.py` — read the real constant at test time; `#memory-system` markup for the new section's shape.

**Vital slice**: AC1, AC2, AC4 (i–iii).

**Cut list**: savings figures; a diagram; per-skill pages; describing `token_meter.py`.

---

## Edge Case Checklist

- [ ] Parse `MAX_LINES`/`MAX_CHARS` from the source text (or import by path) — `memory_slice.py` is not a package
- [ ] The page renders `4,000` with a comma: match either form, like the hot-tier cap test
- [ ] The new section must not add a script, a `url()`, or an external link
- [ ] Keep the hook row's `blocks` tag; add an `advises` tag — don't turn the row into "advises" only

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | Two rows, one section, one nav link |
| `tests/test_site_content.py` | AC4 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/**`, `.claude/hooks/**`, `scripts/**` | Sources the page describes, not changed by this task |
| `CLAUDE.md`, `agents/**` | Harness scope |
| `memory/*` | Supervisor-only writes |

---

## Test Plan

1. `tdd`: AC4 tests first, observed RED. 2. Edit the page. 3. M1–M4 RED/GREEN pasted. 4. Screenshots at 375/768/1280. 5. User-run `/verify`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Risk Low; no script change)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T130.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M4 pasted
- [ ] UI Evidence rows filled with screenshots (Hard-Stop Gate 6)
- [ ] `/verify` — user-run
- [ ] Supervisor notified: task ready for Stage 4 review
