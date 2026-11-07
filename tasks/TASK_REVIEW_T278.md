# TASK_REVIEW — T278: The docs page says what the self-review loop does and does not do

> Sibling of `tasks/TASK_GUIDE_T278.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t278_self_review_docs.py` (5 tests: 6 nodes in order + `is-outcome` last, the four chips, existing classes only / no paragraph, word limits, banned words). Red first: `5 failed` on the unchanged tree. |
| Verification command run | ☑ pass | After the coordinator decision (node 4 "Up to 3 proposals" + meta "cited", node 5 "You approve", heading `<h3><code>self-review</code></h3>`): `python3 -m pytest tests/test_t278_self_review_docs.py tests/test_site_content.py tests/test_site_story.py tests/test_site_visual_first.py tests/test_docs_t151.py -q` -> `224 passed in 0.66s`. `#skills` shows 150 visible words (pin: 150), so nothing else was cut and the pin is unchanged. |
| Negative cases hold | ☑ pass | Final tree: deleted `<li class="chip">merge</li>` -> `FAILED tests/test_t278_self_review_docs.py::test_chips_row_lists_the_four_things_the_loop_never_does`, `1 failed, 4 passed in 0.02s`. Restored -> `5 passed in 0.02s`. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Headless Chrome screenshots of `#skills`: `/home/hungnguyenhuu/tmp.lTiRIa7j9V/s4-1280.png`, `/home/hungnguyenhuu/tmp.lTiRIa7j9V/s4-375.png`. The diagram uses the same `flow-visual` + `flow-row is-long` markup as the `#tracks` Auto mode flow; no other block moved. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | No CSS change (`site/theme.css` untouched). Classes: `flow-visual`, `flow`, `flow-row`, `is-long`, `flow-node`, `step-no`, `flow-title`, `flow-meta`, `is-outcome`, `flow-chips`, `chip`, `lead` (asserted by test). |
| **UI: Responsiveness at target viewports** | ☑ pass | 1280px: six nodes in one row, arrows between, last node green outcome, chips row below. 375px: nodes stack with down arrows, no sideways scroll. 768px not shot (same `is-long` stack rule as 375px, `theme.css` line 398). |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (non-executable change: verbatim prior content of `site/docs.html` lines 1907-1910, `#skills`, captured 2026-11-07T08:36Z before any implementation commit; `grep -n self-review site/docs.html` matched only the chip on line 1902):

```html
<p class="lead">
  <code>ux-evaluate</code> (Stage 3): the frontend agent screenshots its UI at 375px and 1280px,
  judges nine UX checks and the guide's UX rows, and fixes each fail. <code>code-review</code> runs it again.
</p>
</section>
```

Line 1902 (the only mention of the skill): `<span class="chip">self-review</span>` inside the "Any stage" chip band. No sentence says what the loop does.

Verification Command on the unchanged tree (new test file does not exist yet):

```
$ python3 -m pytest tests/test_t278_self_review_docs.py tests/test_site_content.py tests/test_site_story.py tests/test_site_visual_first.py tests/test_docs_t151.py -q
ERROR: file or directory not found: tests/test_t278_self_review_docs.py
no tests ran in 0.00s
```

The four existing files alone on the unchanged tree: `219 passed in 0.83s`.

**AFTER**: the same Verification Command, post-change: `224 passed in 0.60s`. New content in `#skills`, after the `ux-evaluate` paragraph: `<div class="flow-visual">` holding `<h3><code>self-review</code></h3>`, an `<ol class="flow flow-row is-long" aria-label="The self-review loop, in order">` of 6 nodes (You start it `/self-review` / New records? none: stops / One miner / Up to 3 proposals cited / You approve / Kanban task normal pipeline, `is-outcome`), `<p class="lead">Never:</p>`, and `<ul class="flow-chips">` with `edit kit files`, `merge`, `push`, `call the network`.

**DELTA**: A reader of the docs page sees, at a glance, that the user starts the self-review loop, approves each proposal, and that the loop never edits kit files, merges, pushes or calls the network.

**WITNESS**: [reviewer fills from `memory/event-trace/T278.jsonl`]
