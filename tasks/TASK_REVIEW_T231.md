# TASK_REVIEW — T231: Story landing page — one visual flow on index.html, reference moves to docs.html

> Sibling of `tasks/TASK_GUIDE_T231.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_story.py` (48 tests after round 2, new in this task), fixture `tests/fixtures/site_story_baseline.json`. Supervisor rerun: 202 passed across the three site test files. |
| Verification command run | ☑ pass | Supervisor rerun at `be0ac17f`: `202 passed in 0.60s`; settings tool `pass 59, fail 0`; scroll-spy `pass 8, fail 0`. |
| Negative cases hold | ☑ pass | M1–M6 each went RED then green (implementer table). Round 2 added M6 (delete a chip) and M6b (unmark a key chip). |
| verify | ☑ fail | auto-run by hook, session a90cb9b7-c68e-4951-bf18-b77d0e63ad1e, commit 8222a5a6edaa08e0fe9947ec58ac8b7058c9880f, log .claude/verify-runs/T231-8222a5a6edaa.log — fail |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review run inline on `main..HEAD` plus direct readers of the moved page. P0 0, P1 0, P2 2 fixed here (`PROJECT_SPEC_SITE.md:73` and `RUNBOOK.md:156` still named index.html alone), P3 1 left (hero eyebrow "multi-agent supervisor framework" is not plain, not on the D4 list). lane: `C2, 16 files, 6875 lines, EXCEEDS`: moved text and a fixture, label kept. Startup-reads line complete. Round 2 (`07694fb1..be0ac17f`): P0 0, P1 0, P2 0. |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor rerun at `be0ac17f`: `pytest tests` 1448 passed; `pytest .claude/hooks/tests` 1388 passed, 25 subtests passed. |
| **Companion score (easy-verifier)** | ☐ N/A | Optional tool, not run for this task. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Supervisor viewed `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/91713a2d-c4ca-4ba6-9c19-2b966a122175/scratchpad/shots/r2_index_1440_full.png`: six sections, stage flow with chips, starred key skills, numbers strip. Round 1 docs check stands; round 2 removed only CSS from docs.html `<style>`, moved to theme.css (`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/91713a2d-c4ca-4ba6-9c19-2b966a122175/scratchpad/shots/r2_docs_1440x900.png`). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | AC 9 test: no hex outside theme.css, no third-party assets. Computed fonts IBM Plex Sans and IBM Plex Mono (implementer, headless Chrome). Mint on final journey node, Copy button, links. |
| **UI: Responsiveness at target viewports** | ☑ pass | `scrollWidth == clientWidth` on both pages at 1440, 1024, 768, 375 at `be0ac17f` (implementer, headless Chrome). |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-02T02:48:58Z on branch `feat/t231-story-page` at `97763d7a`; `site/index.html` is byte-identical to `09d2544c`, checked with `git show 09d2544c:site/index.html | cmp - site/index.html`; no implementation commit exists yet):

Word counts of `site/index.html` `<main>`, per top-level section, counted with `_Visible` from `tests/test_site_visual_first.py` (visible = outside `<details>`, `<pre>`, `<code>`, `<svg>`, `<script>`, `<style>`) and with a second pass that also counts the folds (`<details>`; script and style still skipped):

| Section | Visible | With folds |
|---|---|---|
| quick-reference | 54 | 60 |
| what-you-get | 103 | 221 |
| tracks | 129 | 548 |
| install | 69 | 336 |
| update-flow | 87 | 798 |
| settings-tool | 121 | 128 |
| install-variants | 65 | 88 |
| agent-roles | 55 | 265 |
| skills | 95 | 95 |
| hooks | 119 | 575 |
| agent-focus | 32 | 285 |
| packs | 114 | 142 |
| providers | 26 | 259 |
| repository-layout | 133 | 162 |
| memory-system | 53 | 147 |
| mcps | 146 | 439 |
| options | 14 | 16 |
| **Total (17 sections)** | **1528** | **4564** |

Screenshot of the page as it is now (headless Chrome, `file://` URL, 1440x900 viewport): `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/91713a2d-c4ca-4ba6-9c19-2b966a122175/scratchpad/shots/before_index_1440x900.png`. A 1440x16000 tall capture, still not the whole page, is in the same folder: `before_index_1440_tall.png`. Copy of the old page: `.../scratchpad/before_index.html`.

**AFTER** (implementation commits `0f1d67be` red tests, `71ed455f` story + docs + header fix; branch `feat/t231-story-page`, 2026-11-02):

`site/index.html` `<main>`, same counter as BEFORE (`_visible` rules, `<details>` none): **270 words** in five sections: hero 29, journey 65, paths 60, stops 70, deeper 46 (cap 300; BEFORE 1528 visible, 4564 with folds). Page height at 1440 px: 1774 px (cap 5 x 900 = 4500; BEFORE 17 sections). No `<details>`. `site/docs.html` holds the 17 sections and the hero unchanged: all 367 baseline `<p>/<li>/<td>/<dd>` texts found, three Settings tool scripts byte-identical (sha256).

Verification command, run after the change:

```
$ python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py tests/test_site_story.py -q
197 passed in 0.59s
$ node --test tests/settings_tool/*.mjs   -> tests 59, pass 59, fail 0
$ node --test tests/site_scrollspy/*.mjs  -> tests 8, pass 8, fail 0   (now loads /docs.html)
$ python3 -m pytest tests -q              -> 1443 passed in 118.91s
$ python3 -m pytest .claude/hooks/tests -q -> 1388 passed, 25 subtests passed
```

Red first: `tests/test_site_story.py` at `0f1d67be` ran `38 failed, 5 passed` before `docs.html` existed. After: 43 passed.

Mutations (each new test RED, then green on revert; `pytest tests/test_site_story.py`):

| Mutation | RED | Green on revert |
|---|---|---|
| M1 delete the "It plans" step | 2 failed (`test_journey_is_an_ordered_list_of_five_steps...`, `test_journey_marks_the_users_two_steps...`) | 43 passed |
| M2 add `PreToolUse` to the `paths` heading | 1 failed (`test_no_internal_term_on_the_story_page[PreToolUse]`) | 43 passed |
| M3 delete the "Medium: a Debate with 2 Advocates." item from `docs.html` | 1 failed (`test_every_paragraph_item_cell_and_definition_of_the_old_page_is_on_docs`) | 43 passed |
| M4 remove `quick-reference` from the redirect id list | 1 failed (`test_redirect_id_list_equals_the_link_target_ids_of_docs`) | 43 passed |
| M5 name `pre_tool_secret_path.py` (no such file) in `stops` | 1 failed (`test_every_stop_names_a_real_wired_hook_in_a_comment_beside_it`) | 43 passed |

Headless Chrome (`file://`, raw CDP script in the scratchpad, `cdp_check.mjs`): `scrollWidth == clientWidth` on both pages at 1440, 1024, 768 and 375 px. `index.html#hooks` ends on `docs.html#hooks`; `#verifier` ends on `docs.html#verifier`; `#nonsense` and `#journey` stay on `index.html`. Computed font of step title and card title: IBM Plex Sans; step label: IBM Plex Mono. Copy button on `index.html` runs (headless denies the clipboard, so it shows "Select and copy", as on `docs.html`).

Screenshots (outside the repo, folder `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/91713a2d-c4ca-4ba6-9c19-2b966a122175/scratchpad/shots/`): `after_index_1440x900.png`, `after_index_1024.png`, `after_index_768.png`, `after_index_375.png`, `after_docs_1440x900.png`, `idx_1440_crop.png` (1440x1700 crop of the whole story). Header fix found by the screenshots: the new Home/Docs nav overlapped the version tag at 1024 and the brand at 900, so the tag hides below 1200 px and the family nav tightens at 900-1099 px (`site/theme.css`).

The Stops claims, each read in the hook before it was written: `pre_agent_validate_guide.py` blocks a spawn when the task guide is missing; `pre_bash_block_unsafe_merge.py` blocks git push/merge when a task has no passing `verify` row and no test command in its trace; `pre_tool_sensitive_path.py` returns `ask` for a path in `.claude/sensitive-paths.txt` (`.env*`, `**/secrets/**`, `*.pem`...); `pre_agent_step_limit.py` blocks a task's tool call once it passes the step limit.

**DELTA**: A first-time reader now sees what Easy Kit does as one five-step flow in 270 plain words (was 1528 visible words in 17 sections), and the full reference is one click away on `docs.html` with no sentence lost.

**AFTER, round 2 (amendments A1 and A2, 2026-11-02)**:

- `site/index.html` now holds six sections: hero, journey, stages, paths, stops, deeper. New `stages` screen ("Skills by stage"): the 7 docs stages with their skill chips in the `docs.html#skills` order, plus the "Any stage" group. Chips are `<code class="chip">`, so they are outside the word count; each stage title links to `docs.html#skills`. Hero gains the numbers strip (4 spawnable roles, 35 skills, 5 blocking hooks (of 11), 6 optional domain packs), each cell linking to its docs section. Key skill per stage (a taste choice, flagged to the Supervisor): brainstorming, map-codebase, craft-agent, grill-with-docs, tdd, code-review, ship. Each key chip has a star (shape cue, `aria-hidden`), a `visually-hidden` "key skill" text, a bold weight and the accent-line border; the screen says "star marks the key skill of each stage".
- `<main>` words: **297** (cap 300): hero 43, journey 55, stages 36, paths 47, stops 70, deeper 46. To fit the cap, four descriptions were shortened (journey step 3 and 5, both path branches). Page height at 1440 px: 2711 px (cap 4500).
- CSS: the skill-flow, flow-step, chips, skill-band and strip-link rules moved from the docs page `<style>` to `site/theme.css` (both pages use them). The docs mobile stacking rule moved too, at `max-width: 767.98px` so docs keeps its exact old breakpoint (`docs.html` at 768 px is 13671 px tall, same as round 1); the story page stacks at 768 px with a `.story`-scoped rule.
- Story tests changed only as far as the amendments need: `STORY_SECTIONS` gains `stages`; the D4 `Stage` case skips the `#stages` section; the list test and the layout-class test include `stages` and `skill-flow`. New tests: skill chips equal docs `#skills` (stage order, per-stage chips, Any-stage group), chips are `<code>`, each stage names its number and links into docs, hero strip equals docs quick reference (numbers, labels, links), one key skill per stage with shape and text cue. One older test changed: `test_site_content.py::test_skills_flow_snakes_with_an_arrow_between_every_consecutive_pair` read the arrow CSS from the page text; the rules moved to theme.css, so it reads `_style_block()` (theme plus page style), a wider source.
- Red first: after the new tests and before the markup, `tests/test_site_story.py` gave 8 failed, 40 passed. After: 48 passed.
- **M6** (delete the `ideate` chip from `#stages`): `1 failed, 47 passed` (`test_stages_screen_skill_chips_equal_the_docs_skills_section`); restored: `48 passed`. Extra M6b (replace the `tdd` key chip with a plain chip): `1 failed, 47 passed` (`test_each_stage_marks_exactly_one_key_skill_with_a_shape_and_a_text_cue`); restored: `48 passed`.
- Verification command: `pytest tests/test_site_content.py tests/test_site_visual_first.py tests/test_site_story.py` gave `202 passed`; `node --test tests/settings_tool/*.mjs` pass 59 fail 0; `node --test tests/site_scrollspy/*.mjs` pass 8 fail 0; `pytest tests` gave `1448 passed in 120.26s`; `pytest .claude/hooks/tests` gave `1388 passed, 25 subtests passed`.
- Headless Chrome (`cdp_check.mjs`): `scrollWidth == clientWidth` on both pages at 1440, 1024, 768, 375 (index heights 2711, 3287, 4482, 5266 px); redirects as in round 1.
- Screenshots in `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/91713a2d-c4ca-4ba6-9c19-2b966a122175/scratchpad/shots/`: `r2_index_1440x900.png`, `r2_index_1440_full.png`, `r2_index_1024.png`, `r2_index_768.png`, `r2_index_375.png`, `r2_docs_1440x900.png`, `r2_docs_skills_375.png`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
