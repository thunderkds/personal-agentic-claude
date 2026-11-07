# TASK_GUIDE — T278: The docs page shows the self-review loop as a flow diagram
**Date**: 2026-11-07
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt
3. Read this file completely
4. Read `agents/frontend.md`
5. Read the **shipped** `skills/self-review/SKILL.md` and `skills/self-review/scripts/self_review.py`. The copy describes what shipped (T255, T256, T260), never what was planned
6. Read `site/docs.html` lines 1865–1910 (`#skills`, the `ux-evaluate` lead paragraph is the pattern)
7. Read `memory/learning-records/LR-0004-pin-tests-hit-later-tasks.md` and `LR-0005-stale-text-after-change.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-07: *"for the self loop to improve the harness, do you update the document related for that"*, then *"do you think its good thing to note and let people know about that"*, then *"yes, let go"* to the Supervisor's recommendation of one short entry on `site/docs.html`. Revised 2026-11-07, user: *"for visualize, the docs should show the flow, chart, and anything to visualize, do not text too much from home"*. So the entry is a **diagram**, not a paragraph.

**Restated intent**:
> A reader of the docs page sees `self-review` only as a chip name. They cannot learn that the loop proposes changes and never edits the kit. The page gets one flow diagram that shows what the loop does, that the user starts it and approves each proposal, and that a kit change goes through the normal pipeline. Words are labels only.

**Out of scope** (what this task explicitly does NOT do):
- Any change to `skills/self-review/`, its script, or its register. The skill text is the source of truth and stays as is
- `AGENTS.md`, `site/index.html` (300-word cap, T231), the chip rows, and the skill count
- Any claim that the kit improves itself without a human. The diagram must not say "autonomous", "self-improving" or "automatic"

**Requirement Refs**: None — docs follow-up to T255, T256 and T260. No `PRD.md` FR covers site copy; `docs/prd/PRD_self-review.md` is the behaviour source.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, user said "yes, let go" to this exact scope)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (the term is `self-review`, the register is `memory/self-review/register.md`)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above (none claimed)

---

## Dependencies & Reachability

**Depends on**: T260 — `self_review.py` and the `self-review` skill text in their final merged form (merged 2026-11-05)

**Entry point**: `docs.html#skills` — the new diagram sits in `<section id="skills">`, after the `ux-evaluate` lead paragraph

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `site/docs.html` holds one new `<ol class="flow flow-row is-long" aria-label="The self-review loop, in order">` inside `<section id="skills">`, built only from the existing `flow`, `flow-node`, `step-no`, `flow-title`, `flow-meta`, `is-outcome` and `flow-chips` classes. No new CSS, no new image | "show the flow" |
| 2 | The diagram has 6 nodes in this order: `/self-review` (you start it) → new review files? (if none: stops, no agent call) → one miner reads them → at most 3 proposals with citations → you approve or reject → approved becomes a Kanban task and a Learning Record, then the normal pipeline. The last node uses `is-outcome` | "let people know" |
| 3 | A `flow-chips` row under the diagram holds the four things the loop never does: `edit kit files`, `merge`, `push`, `call the network` | "never edits" |
| 4 | Words stay labels: each `flow-title` is at most 4 words, each `flow-meta` is at most 8 words, there is at most one one-line `<p class="lead">` of at most 15 words, and the whole block is at most 80 visible words. No paragraph | "do not text too much" |
| 5 | The block contains none of: `autonomous`, `self-improving`, `automatic`, `automatically` | Out of scope |
| 6 | Every fact in the diagram matches `skills/self-review/SKILL.md` (Rules, Steps 1–6) as shipped | LR-0005 |
| 7 | The existing site tests still pass with no edit to a baseline or a pin, except one new entry only if a pin test forces it (state which, and why) | LR-0004 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `site/docs.html` after the change | the `#skills` section holds the `ol.flow` with `aria-label="The self-review loop, in order"` and 6 `flow-node` items; the last has `is-outcome` | automated test |
| 2 | The diagram text | contains `/self-review`, `3 proposals`, `approve`, `Kanban`; the chips row lists the four "never" items | automated test (new `tests/test_t278_self_review_docs.py`) |
| 3 | The diagram text | within the word limits of AC 4; none of the banned words of AC 5 | automated test (same file) |
| 4 | Mutation: delete the `merge` chip | the new test fails | mutation control, run by the reviewer |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_t278_self_review_docs.py tests/test_site_content.py tests/test_site_story.py tests/test_site_visual_first.py tests/test_docs_t151.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T278.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T278.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `docs.html#skills`, the new diagram | LLM-vision screenshot (`ux-evaluate`) | The diagram renders in the same style as the Auto mode flow in `#tracks`; no other block moves |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | CSS audit | No new color; only existing flow classes |
| Typography matches spec | computed style | Same font-family, size and weight as the nodes in the `#tracks` Auto mode flow |
| Spacing / layout matches spec | computed style | Same gaps as the `#tracks` Auto mode flow |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375px) | Playwright screenshot | No sideways scroll; the nodes stack in order |
| Tablet (768px) | Playwright screenshot | Same as mobile |
| Desktop (1280px) | Playwright screenshot | The nodes read left to right, as in the Auto mode flow |

### 4. UX Acceptance Criteria

| User story | User goal | Flow / state | Pass condition (observable) |
|------------|-----------|--------------|-----------------------------|
| Request: "the docs should show the flow … do not text too much" | A reader sees the loop's steps and its limits at a glance | Open `docs.html#skills`, scroll to the diagram | The 6 steps and the four "never" chips show at 375px and 1280px without a click |

---

## Approach

**Pattern reference**: `site/docs.html` lines 406–416 — the Auto mode `<ol class="flow flow-row is-long">` with `step-no`, `flow-title`, `flow-meta`, an `is-outcome` last node, and a `flow-chips` row. Imitate its markup. For the "no new files" branch use `flow-branches` and `flow-edge` as at lines 399–401 only if the 6-node row cannot show it; otherwise put it in that node's `flow-meta`.

**Vital slice**: One flow diagram plus the chips row in `#skills`, and one test file.
**Cut list**: A paragraph of prose; a new SVG or image; a new CSS class; a link to `docs/prd/PRD_self-review.md`; a note in `AGENTS.md`; an `index.html` change (the 300-word cap, T231).

Draft the labels from the skill's Rules and Steps, not from memory. Suggested nodes (title / meta):

1. You start it / `/self-review`, never a hook
2. New records? / none: stops, no agent call
3. One miner / reads the new reviews
4. Up to 3 proposals / each with citations
5. You decide / approve or reject each
6. Kanban task / normal pipeline does the change

Chips row, label "The loop never": `edit kit files` · `merge` · `push` · `call the network`.

---

## Edge Case Checklist

- [ ] The "never" chips stay true: re-read `skills/self-review/SKILL.md` Rules before committing the labels
- [ ] The skill still writes the register and a Learning Record; no label may say it "writes nothing"
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep the repo for `self-review` wording in `README.md`, `site/`, `docs/claude-md/`, and `agents/`; list any that now disagree, and fix only those inside `site/docs.html`
- [ ] The chip band on `docs.html` and on `index.html` stays equal (`test_site_story.py` line 423)
- [ ] The row does not scroll sideways at 375px (`is-long` stacks); no long unbroken token needs `<wbr>`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/docs.html` | One `ol.flow` diagram, a `flow-chips` row and at most one one-line lead, after the `ux-evaluate` paragraph in `#skills` |
| `tests/test_t278_self_review_docs.py` | New: AC 1–4 as tests, with the mutation control for the `never edits` sentence |
| Pre-existing pin tests | `tests/test_site_visual_first.py` (`BASELINE_SENTENCES` — adding text loses no old sentence, so no edit expected); `tests/test_site_story.py` (chip band equality, unchanged); `tests/test_docs_t151.py`, `tests/test_site_content.py` (grep for `self-review` and the section line range). Handling: none expected; escalate if one fails |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/self-review/**` | The skill is the source of truth (T255, T256, T260) |
| `memory/self-review/register.md` | Loop state, not docs |
| `site/index.html`, `AGENTS.md` | Out of scope (300-word cap; doctrine only) |
| `site/theme.css` | No new style; the diagram reuses the existing flow classes |

---

## Test Plan

1. Write `tests/test_t278_self_review_docs.py` first (red: the diagram is absent).
2. Add the diagram (green).
3. Run the Verification Command.
4. Screenshot `docs.html#skills` at 375px and 1280px with `ux-evaluate`.
5. Mutation: remove the `merge` chip; the test must fail. Restore it.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T278.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] UI Evidence rows (visual, design-system, responsiveness) filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
