# TASK_GUIDE — T181: README and site describe the two tracks, the Debate step and `[auto]`
**Date**: 2026-10-27
**Complexity Level**: C1
**Risk Level**: Low — `README.md` text and one static HTML page plus drift tests; no harness file, no deploy config
**Priority**: P2
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

> Starts only after T178, T179, T180 and T182 are merged. The facts below are their **planned** design;
> before the spawn, the Supervisor re-reads the merged `docs/claude-md/tracks.md` (incl. T182's auto verify step),
> `skills/resolve-question/SKILL.md` and `AGENTS.md` and corrects this guide in a commit of its own
> (a batch guide ages against the tasks that merge after it).

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` (glossary: Minimal track, Extended track, Decision record, Debate, Advocate, Auto mode, Final report) and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read the source of truth: `docs/claude-md/tracks.md` (T178 + T180), the `#### Debate (auto mode only)` step of `skills/resolve-question/SKILL.md` (T179), and the `## Tracks` section of `AGENTS.md`
7. Read `site/index.html` (`#quick-reference`, `#what-you-get` with `#pipeline-diagram`, the Stage sections, `#skills`), `tests/test_site_content.py` and `tests/test_readme_slim.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-27, asked whether any task updates "the guide from the README or the page for refer" for T178–T180; none did (T178 cuts "a site page"). User: "yes, register new one".

**Restated intent:**
> After T178–T180 merge, a reader of `README.md` or the project site learns that the kit has two
> tracks (minimal and extended), how the Supervisor picks one and how to override it, that
> `[auto]` runs either track to Ready for Review with a final report of every decision, and that
> `resolve-question` can run a Debate in auto mode, and that a hook then runs `/verify` for an `[auto]`
> task. Merge stays with the user — the pages say so.

**Facts to state (re-checked by the Supervisor against merged `main` at `453b2d5`, 2026-10-27):**
- Every implementation request goes on a track, announced in one line: `Track: minimal — <reasons>` or `Track: extended — <reasons>`; with `[auto]`: `Track: minimal · auto — …` / `Track: extended · auto — …`. The line is a statement, never a question. The user can reply `full` or `minimal` at any time to switch (`docs/claude-md/tracks.md` `## Switching track`).
- Extended track if any of: Complexity C2+; Risk Medium/High; a Gate-2 word or *migrate*; a change that deletes, moves, renames or converts user data or its storage format (e.g. CSV to JSON); more than one session or agent; a UI component. Otherwise minimal (`## Track rule`).
- Minimal track: test first, change, real run, a Decision record in `tasks/MINIMAL_LOG.md`, a board row marked `| Track: minimal`, commit without asking; no task guide, no sub-agent (`## Minimal-track flow`, 7 steps).
- Extended track: the 5-stage pipeline, unchanged.
- `[auto]` in the request (only that exact tag): no stops for questions; every decision goes to a final report (`## Auto decisions`, marker line `Mode: auto`); how each decision is made follows the task's Risk — Low: the Supervisor decides and logs; Medium: a Debate with 2 Advocates; High: 3 Advocates, and at least one decision is always debated. A Stop hook checks the report before the run may end. Safety hooks still block; merge, push and Done stay with the user (`## Auto mode`).
- Auto verify (T182, merged): for an extended-track `[auto]` task at Ready for Review, a Stop hook — not the Supervisor — starts one fresh headless `claude -p "/verify <ID>"` run per commit (budget $2 by default), and the hook writes the `verify` row; the merge gate accepts that row only with its run record. Merge stays with the user. Without `[auto]`, `/verify` is still typed by the user (`### Auto verify (Stop hook)`).
- Debate (auto mode only, `resolve-question`): read-only Advocate agents argue the options (count by Risk, above); the Supervisor decides, safer option on a tie, flagged `⚠ decided for you — please review`; at most 3 Debates per task, the 4th question goes to the user.

**Out of scope:** the site restructure (T089); any change to the Stage 0.5–5 section content beyond saying they are the extended track; a new diagram for the minimal track unless it fits the existing SVG with no new CSS; any harness file.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-10-27: "yes, register new one")
- [x] Facts above re-checked against the merged T178–T180 and T182 docs (Supervisor, 2026-10-27, `main` at `453b2d5`)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: T178, T179, T180, T182 (merged to `main`)

**Entry point**: `site/index.html` — new `<section id="tracks">`; `README.md` intro

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `site/index.html` has `<section id="tracks">` with an `<h2>` naming the two tracks, placed after `#what-you-get` and before the Stage 0.5 section; the sidebar nav has `href="#tracks"` | two tracks |
| 2 | The section states the track rule, both literal announcement lines, the `full` / `minimal` override, and what the minimal track does and skips | facts 1–3 |
| 3 | The section (or a sub-heading in it) describes `[auto]`: the literal tag, the final report, auto verify run by a hook in a fresh session, and that merge and Done stay with the user | facts 5–6 |
| 4 | The section names the Debate with its cap and the review flag; the `#skills` entry for `resolve-question` mentions the Debate, if that list carries descriptions | fact 7 |
| 5 | Each Stage 0.5–5 heading area or the pipeline diagram's `<desc>` says these stages are the extended track (one line, not a rewrite) | fact 4 |
| 6 | `README.md` intro mentions the two tracks and `[auto]` in ≤3 lines and stays ≤75 lines (`tests/test_readme_slim.py`) | README |
| 7 | New tests in `tests/test_site_content.py`: section + nav link exist; the section contains `Track: minimal`, `Track: extended`, `[auto]`, `/verify`; the section does not say auto mode merges or pushes, or that the Supervisor runs `/verify` | drift |

**Mutation controls:** **M1** — delete the nav `<li>` → RED. **M2** — remove `[auto]` from the section → RED. **M3** — insert "auto mode merges your branch" into the section → RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_readme_slim.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T181.md`. BEFORE: the verbatim `README.md` lines 1–9 and the `#what-you-get` → Stage 0.5 boundary of `site/index.html` as they are at spawn time. Paste M1–M3 results in its "Negative cases hold" row.

---

## UI / Design Acceptance Criteria

- Reuse the page's existing markup patterns (`<p class="lead">`, plain `<ul>`, `<code>`, `.chip`); no new CSS, fonts, images or scripts.
- The two announcement lines and `[auto]` sit in `<code>` and wrap at 375px width with no horizontal scroll.
- Plain words for a first-time reader: one idea per sentence (AGENTS.md Writing Principles).

---

## Approach

**Pattern reference**: the `#memory-system` section (lead + short list) and T135's `#verifier` section for size and tests.

**Vital slice**: AC1–AC3, AC6. **Cut list**: a second SVG for the minimal track; a worked example of a Decision record or final report on the page; a separate page.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | nav `<li>`, `<section id="tracks">`, one-line extended-track note at the stages |
| `README.md` | ≤3 intro lines |
| `tests/test_site_content.py` | AC7 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | Deploy config unchanged |
| `AGENTS.md`, `docs/claude-md/**`, `skills/**`, `.claude/hooks/**` | Source of truth for the facts; T178–T180 and T182 own them |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Completion Checklist

- [x] Supervisor re-checked the facts against the merged T178–T180 and T182 docs (before spawn)
- [ ] Implementation done; AC7 tests observed RED first
- [ ] M1–M3 pasted in the Evidence table
- [ ] All three UI Evidence rows filled
- [ ] Stage 4: code-review
- [ ] `/verify` — user-run
- [ ] Merge only when the user asks

---

## Questions Log
