# TASK_REVIEW — T138: Pipeline workflow diagram on the site Overview

> Sibling of `tasks/TASK_GUIDE_T138.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py` — 5 new tests (`test_pipeline_diagram_*`): in `#what-you-get`; role/title/desc/viewBox; node order == `## Stage` headings read at test time (+ Phase 0); one arrow-head per gap; no hex/script/href. `39 passed in 0.06s` (was 34) |
| Verification command run | ☑ pass | `tests/test_site_content.py`: 39 passed. Full: `1 failed, 996 passed in 13.74s`; the 1 failure `test_kanban_section_parsing.py::test_find_kanban_section_on_real_current_board` is **pre-existing** (same failure in BEFORE capture, untouched file). 3 screenshots written (320/768/1280). |
| Negative cases hold | ☑ pass | M1 (delete node 1.5): `AssertionError ... At index 3 diff: '2' != '1.5' / Right contains one more item: '5'` → 1 failed, 38 passed. M2 (swap 3↔4): `At index 5 diff: '4' != '3'` → RED. Both reverted via `git checkout`. |
| verify | ☐ N/A | user-run `/verify` pending — not run by implementer. [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | Implementer self-check only: diff touches `site/index.html` (`#what-you-get` + one CSS block), `tests/test_site_content.py`; `#install`/`#update-flow` untouched. `code-review` skill left to Stage 4. |
| Full smoke suite still green (no regression) | ☑ pass | 996 passed; only failure is the pre-existing one above |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Inspected `t138-320.png`, `t138-1280.png` (768 written, not viewed): all 8 nodes + 7 arrows visible, no clipped labels, rest of page unchanged. Files in session scratchpad `.../scratchpad/t138-{320,768,1280}.png`. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `git diff 792b486 -- site/index.html \| grep '^+' \| grep -c '#[0-9a-fA-F]{3,6}'` → `0`; fills/strokes are `var(--surface/--cyan/--text/--muted)`; `font-family: inherit`; width capped at 26rem inside `--measure`. |
| **UI: Responsiveness at target viewports** | ☑ pass | 320/768/1280 rendered; `viewBox` + `width:100%`, vertical layout; no horizontal overflow at 320 (text scales to ~10px, legible). JS-off: SVG is static markup, no script involved (inspection, not separately screenshotted). |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-08T15:03:44Z, before any implementation commit, branch `feat/t138-pipeline-diagram` @ 792b486):

```
$ grep -c 'pipeline-diagram' site/index.html
0
$ python3 -m pytest tests/test_site_content.py -q
34 passed in 0.08s
$ python3 -m pytest tests/ .claude/hooks/tests/ -q
FAILED .claude/hooks/tests/test_kanban_section_parsing.py::test_find_kanban_section_on_real_current_board
1 failed, 991 passed in 14.29s
```

`#what-you-get` is prose only (verbatim): `<section id="what-you-get"><h2>What you get</h2><p class="lead">A base team of four spawnable sub-agent roles, ...</p></section>` — no diagram. The 1 failure is pre-existing (unrelated to the site; present before my change).

**AFTER**: `grep -c pipeline-diagram site/index.html` → `3`; `python3 -m pytest tests/test_site_content.py -q` → `39 passed in 0.06s`. `#what-you-get` now ends with `<svg id="pipeline-diagram" role="img">` holding 8 nodes (Phase 0, Stage 0.5, 1, 1.5, 2, 3, 4, 5), each "stage · name" + main output, joined by 7 arrows.

**DELTA**: A reader of the Overview sees the pipeline's order and each stage's output in one diagram before any prose.

**WITNESS**: [Supervisor to fill from `memory/event-trace/T138.jsonl`; implementer ran the commands above 2026-10-08.]

## AC notes

- AC4 (return arrow): **none drawn.** `docs/claude-md/pipeline-stages.md:205` says only "Address all findings before moving to Stage 5" — it does not say findings go back to Stage 3, so a return arrow would be invented flow.
- Process note: I wrote the SVG before the test (not strictly test-first); mutation controls M1/M2 above confirm the test fails when the diagram drifts.
- Cut list unchanged from guide (no hover, links, animation, second diagram).

## Open questions

None.

---

## Stage 4 — Supervisor review (2026-10-08)

**code-review: 0 P0 / 0 P1 / 0 P2 / 2 P3.** Supervisor re-ran `tests/test_site_content.py` in `wt-t138`: 39 passed. Entry point `id="pipeline-diagram"`: present. AC4 decision (no return arrow, citing `pipeline-stages.md:205`) accepted.
- **UI sign-off by the Supervisor (Gate 6)**: own headless-Chrome screenshots at 320 / 768 / 1280 px inspected — 8 nodes in document order, arrows between each, no clipping, no horizontal scroll; colours only `var(--…)` tokens; rest of page unchanged.
- **P3**: at 320 px the 11px sub-labels render ≈8px — legible but small; optional bump.
- **P3**: SVG written before the test (self-reported); M1/M2 RED confirm the test discriminates.

security-review: not required (Low risk); static SVG, no script, no external ref (asserted by test).
