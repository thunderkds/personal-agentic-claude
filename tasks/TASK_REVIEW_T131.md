# TASK_REVIEW — T131: The Agent focus section says "we apply A to save B"

> Sibling of `tasks/TASK_GUIDE_T131.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py` — 4 new tests (headers, six names, three credits, no `%`). RED first: `3 failed, 27 passed` (headers, names, credits); after: `30 passed in 0.05s` |
| Verification command run | ☑ pass | `tests/test_site_content.py` 30 passed; `.claude/hooks/tests tests` `977 passed in 14.25s`; `validate.sh: PASS` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☑ pass | User-run `/verify` 2026-09-25 — pass. Served page, headless Chrome, same-origin iframe, real nav clicks at 1280/768/375: hash `#agent-focus`, section top 16px, scroll-spy active on `#agent-focus`, mobile menu re-collapses; page overflow none (1265/1280, 753/768, 360/375). Rendered DOM: headers `We apply | To save | Idea from`; six rows in AC2 order; credits headroom / — / caveman / ponytail / — / —; row 5 states the install fallback. Finding (not an AC breach, same as the Hooks table): at 375px the table is 640px in a 326px `.table-wrap`, so the To-save and Idea-from columns sit off-screen until the reader scrolls the table sideways |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 (2026-09-25): `git diff tokenization-refactor...feat/t131-apply-to-save` — `site/index.html` (#agent-focus only), `tests/test_site_content.py`, this file; each row checked against its source. **0 P0 / 1 P1 (fixed) / 1 P2 (fixed) / 1 P3 (fixed).** P1: row 5 claimed `compact-advisor` measures context, but it runs `scripts/token_meter.py`, which `MANIFEST` does not ship — an installed project always falls back to judgment; row now says so. P2: the credit test passed on row 6's prose "headroom-style" with row 1's credit removed; it now reads the Idea-from column only — Supervisor mutation (row 1 credit → —) → `FAILED ...test_agent_focus_credits_the_three_source_repos`, restored → 30 passed. P3: T130's "Stage 4 checks the `Startup reads:` line" fact had dropped out; restored in row 2. Suite 977 passed, validate.sh PASS — pass |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass (by diff) | `git diff 3d76f9b -- site/index.html`: only the `#agent-focus` section changed (17 lines). Screenshots `reports/t131/{before,page}-1280.png` (gitignored) only show the page top — headless ignored the `#agent-focus` fragment, so they are not evidence of the section; the diff is |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `<style>` block extracted from 3d76f9b and HEAD: identical (`style identical: True`); no new classes used (`table-wrap`, `code`, `strong` already present) |
| **UI: Responsiveness at target viewports** | ☑ pass | 375px same-origin iframe (Chrome headless, `reports/t131/probe.html`): `innerWidth 375`, doc `scrollWidth 360` (≤375), `.table-wrap` clientWidth 326 / scrollWidth 640, `overflow-x: auto` — table scrolls inside its wrapper |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (verbatim T130 `#agent-focus` table, `site/index.html` at 3d76f9b, captured 2026-09-25 before any implementation commit):

```html
<div class="table-wrap">
<table>
<thead><tr><th>Mechanism</th><th>What it does</th></tr></thead>
<tbody>
<tr><td>Memory slice</td><td>The spawn prompt pastes only the <code>memory/MEMORY.md</code> index lines that name the task's files, dependencies or ID, capped at 30 lines / 4,000 characters (lines with the fewest matches are dropped first and the header says how many)</td></tr>
<tr><td>Startup reads</td><td>The spawn prompt lists what the agent must read first — <code>PROJECT_SPEC.md</code>, its TASK_GUIDE and its role guide — and the agent ends its report with a <code>Startup reads:</code> line naming what it read</td></tr>
<tr><td>Response Standard</td><td>Replies lead with the answer and stay short, but code, exact error text, file paths, commands and security warnings are quoted verbatim. The audit trail — board rows, guides and their Evidence, decisions, commit messages — stays fully detailed, and a report points to evidence by <code>path:line</code> instead of pasting logs</td></tr>
<tr><td>Stage 4 review</td><td><code>code-review</code> runs an over-engineering reviewer on any diff that adds a function, class, module, dependency or config option, and compares the agent's <code>Startup reads:</code> line with its spawn prompt — a missing required read is a P1 process finding</td></tr>
<tr><td>Measuring</td><td>A claim that a change saves or costs tokens is measured from session transcripts before it is kept (DDR-0009), never estimated by eye. No savings figure is published here</td></tr>
</tbody>
</table>
</div>
```

**AFTER**: `#agent-focus` in `site/index.html` now has headers `We apply | To save | Idea from` and six rows (Memory slice, Startup reads list, Response Standard, Over-engineering reviewer, Measured compact-advisor, Measure before keeping); credits headroom, caveman, ponytail.

**DELTA**: A reader sees, for each mechanism, what the kit applies and what it saves, and which repo the idea came from.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Mutation controls (M1–M3)

| Mutation | Result |
|---|---|
| M1 rename "To save" header | RED: `test_agent_focus_table_reads_we_apply_to_save_idea_from` — `1 failed, 29 passed` |
| M2 drop ponytail credit | RED: `test_agent_focus_credits_the_three_source_repos` — `1 failed, 29 passed` |
| M3 add "40%" to a row | RED: `test_agent_focus_states_purpose_not_figures` — `1 failed, 29 passed` |

All restored; GREEN `30 passed`. AC4(v): the "about 1%" was written "about 1 percent", so the test bans every `%` with no exception.
