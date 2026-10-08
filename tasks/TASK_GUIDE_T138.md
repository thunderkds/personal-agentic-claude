# TASK_GUIDE — T138: The site's Overview shows the pipeline as a workflow diagram
**Date**: 2026-10-08
**Complexity Level**: C1 — one page section plus one drift test; no design choice beyond the diagram itself
**Risk Level**: Low — static page content; no script, installer or hook change
**Priority**: P2
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md` (site rules: no external asset hosts, no analytics)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `docs/claude-md/pipeline-stages.md` (the `## Stage …` headings are the diagram's source of truth), `site/index.html` (`:root` tokens ~line 10, `#what-you-get` ~line 228), `tests/test_site_content.py` (pattern: assertions read the source at test time, never a hard-coded list)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-08: *"create the workflow graph for the overview steps and attach to the page"* — then chose **"5-stage pipeline"** (placed in the Overview section) and **"Plan + implement"**.

**Restated intent:**
> A reader landing on the site sees, in the Overview section, one diagram of the pipeline's steps in
> order — Phase 0 → Stage 0.5 → 1 → 1.5 → 2 → 3 → 4 → 5 — each box naming the stage and its main
> output, so the order and the hand-offs are clear before reading any prose.

**Out of scope:**
- Any other diagram (install/update flow was offered and not chosen).
- JavaScript, a diagram library, or an external image. Inline SVG only.
- Rewriting the existing `#what-you-get` prose or other sections. Nav entries unchanged.
- Changing `docs/claude-md/pipeline-stages.md`.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-08; user picked "5-stage pipeline")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `id="pipeline-diagram"`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `site/index.html`'s `#what-you-get` section contains one inline `<svg id="pipeline-diagram" role="img">` with a `<title>` and `<desc>` | "attach to the page", Overview section |
| 2 | The diagram has one node per `## Stage …` heading in `docs/claude-md/pipeline-stages.md`, plus Phase 0, in document order — the test reads the headings at test time | "the overview steps" |
| 3 | Each node shows the stage number and short name; nodes are joined by arrows in order | "order and hand-offs" |
| 4 | A return arrow is drawn only for a loop the pipeline doc actually describes (e.g. review findings sent back to implementation); cite the doc line in the TASK_REVIEW. If none is described, draw none | no invented flow |
| 5 | Colours use the page's `:root` tokens (`var(--cyan)` etc.) via CSS — no new hard-coded hex | design-system compliance |
| 6 | Readable at 320px: no horizontal page scroll; the diagram scales (`viewBox`, `width:100%`) or switches to a vertical layout | responsiveness |
| 7 | No `<script>`, no external `href`/`src` added; `PROJECT_SPEC_SITE.md` rules hold | site rules |
| 8 | Adding a stage heading to the pipeline doc without adding a node makes the new test fail (M1) | drift-proof |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Current page + pipeline doc | new test in `tests/test_site_content.py` passes: SVG present, node labels match headings in order | pytest |
| 2 | Page rendered headless at 320, 768, 1280 px | screenshot shows every node legible, no horizontal scroll | `google-chrome --headless --screenshot --window-size=W,H` — inspect PNGs |
| 3 | Page with JS disabled (`no-js`) | diagram still renders (it is static SVG) | screenshot/inspection |

**Mandatory mutation controls** (run each, paste RED output, revert):
- **M1**: delete one stage node from the SVG → SC1 goes RED naming the missing stage.
- **M2**: swap two nodes' order → SC1 goes RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
for w in 320 768 1280; do google-chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=$w,1600 --screenshot=/tmp/t138-$w.png "file://$PWD/site/index.html"; done
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled in `tasks/TASK_REVIEW_T138.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T138.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#what-you-get` with diagram | headless Chrome screenshot, inspected (LLM vision) | all nodes and arrows visible, labels not clipped; rest of page unchanged |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | grep the new SVG/CSS for `#[0-9a-f]{3,6}` | none new; only `var(--…)` |
| Typography matches spec | computed style / visual | inherits page `font-family` |
| Spacing / layout matches spec | visual | sits within `--measure` like other section content |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (320–480px) | headless Chrome 320px | legible, no horizontal scroll |
| Tablet (768px) | headless Chrome 768px | legible |
| Desktop (1024px+) | headless Chrome 1280px | legible |

---

## Approach

**Pattern reference**: `site/index.html` existing `.tag` / `pre.install` styling for token use; `tests/test_site_content.py` for read-the-source drift tests.

**Vital slice**: one static SVG + one drift test.
**Cut list**: hover/tooltips, links from nodes to sections, animation, a second (install/update) diagram.

Recommended: a vertical flow (top → bottom) is the simplest shape that stays legible at 320px without a second layout. Each node: `Stage N` + short name (e.g. "Plan — PROJECT_SPEC + TASK_GUIDEs"). Keep labels short enough not to clip; text in SVG does not wrap.

---

## Edge Case Checklist

- [ ] Headings contain `—`, `→`, backticks (`` `/plan` ``) — the test must normalise to the stage number + short name, not compare raw markdown.
- [ ] Phase 0 is not a `## Stage` heading — assert it separately.
- [ ] SVG text is not selectable-wrapped: check 320px for clipping.
- [ ] `<title>`/`<desc>` for screen readers; `role="img"`.
- [ ] Do not touch `#install` / `#update-flow` — T137 edits those in parallel.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | SVG in `#what-you-get` + small CSS block using tokens |
| `tests/test_site_content.py` | drift test(s) |
| `tasks/TASK_REVIEW_T138.md` | new, from `templates/TASK_REVIEW_template.md` |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/index.html` `#install`, `#update-flow` | T137 edits these in parallel |
| `docs/claude-md/pipeline-stages.md` | source of truth, read-only here |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |

---

## Test Plan

New pytest drift test; full suite; three headless screenshots; M1/M2 with RED output pasted into the review file.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T138.md` (Hard-Stop Gate 5)
- [ ] All three UI Evidence rows filled with screenshots (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run — user-run
- [ ] Supervisor notified: task ready for Stage 4 review
