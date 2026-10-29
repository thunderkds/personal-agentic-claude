# TASK_REVIEW — T207: Visual-first landing page — diagrams lead each heavy section, long prose folds into Details

> Sibling of `tasks/TASK_GUIDE_T207.md`. Everything here is **filled by the reviewer at Stage
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
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_visual_first.py` (15 tests, AC 1-7, D3-D5). RED on `c00d0fe`: `12 failed, 3 passed` (`720baed`). GREEN at `910aca8`: `python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q` -> `132 passed in 0.29s`. Mutations (AC 9), each RED then green on revert: M1 delete the hooks visual -> `6 failed, 9 passed`, revert `15 passed`; M2 200-word paragraph above the tracks fold -> `FAILED test_every_section_shows_at_most_150_words_on_first_load`, `1 failed, 14 passed`, revert `15 passed`; M3 delete the "Answer n to go back to the menu" `<li>` from the update-flow fold -> `FAILED test_every_paragraph_and_list_item_from_before_is_still_on_the_page`, `1 failed, 14 passed`, revert `15 passed`; M4 `#ff0000` in the page `<style>` -> `FAILED test_no_hex_colour_outside_the_token_block_and_no_third_party_asset`, `1 failed, 14 passed`, revert `15 passed`. Log: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/mut.txt`. |
| Verification command run | ☑ pass | After fix F1 (stale auto-verify/Done sentences in the tracks fold rewritten from `docs/claude-md/tracks.md`): `python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q` -> `132 passed in 0.34s`; `node --test tests/settings_tool/*.mjs` -> `tests 59, pass 59, fail 0`. Before the allow-list entry, the sentence-preservation test was RED: `FAILED test_every_paragraph_and_list_item_from_before_is_still_on_the_page` (`[('02fcd665c525', 'A Stop hook checks the final report before the r')]`), `1 failed, 131 passed`. The allow-list entry carries the reason `stale since T203/T189 (Supervisor decision)`; M3 still turns the test RED after it. |
| Negative cases hold | ☑ pass | M1-M4 above turn the new tests RED; no hex colour, no third-party `<link>`/`<script src>`, no `animation`/`transition` in the flow CSS (tests). |
| verify | ☐ pass / ☐ fail / ☐ N/A | not run: `/verify` is not mine to run. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests -q` -> `1156 passed in 108.59s`. `python3 -m pytest .claude/hooks/tests -q` -> `5 failed, 1153 passed`: the 5 failures are `test_memory_channel_and_budget.py` (x4) and `test_token_audit_format.py::test_memory_md_hot_tier_stays_within_char_budget`, all because `memory/MEMORY.md` is 42,770 characters, over the 42,000 budget. It is 42,770 at `c00d0fe` too (`git show c00d0fe:memory/MEMORY.md | wc -c`): pre-existing, not caused by T207, and `memory/*` is the Supervisor's. |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | 1440 px headless-Chrome section screenshots. BEFORE: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/before/before-{tracks,install,update-flow,hooks}-1440.png`. AFTER: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/after/after-{tracks,install,update-flow,hooks,agent-roles,memory-system,mcps}-1440.png` (also -1024, -768, -375). Verdict: each visual sits above its closed Details; prose, lists and tables appear unchanged when Details is opened (`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/after-open/open-{tracks,update-flow,hooks}-1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/after-open/open-*-375.png`). Settings tool at 1280 px: before `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/st/b-settings-tool-1280.png`, after `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/st/a-settings-tool-1280.png`; identical layout, only 1 px sub-pixel offsets from the fractional section y (PIL diff bbox is not empty for that reason). The BEFORE images are cropped 7 px at the right edge (the screenshot tool then rendered at 1440 with a 15 px scrollbar; fixed with `--hide-scrollbars` for AFTER). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | AC 7 test: no hex outside `theme.css` `:root`, no colour function in the flow CSS. Computed style via CDP at 1440 and 375: `.flow-title` IBM Plex Sans 15px/600; `.flow-meta`, `.flow-edge`, `.flow-items .tag` IBM Plex Mono 12.5/12/12px. Contrast (WCAG, test `test_flow_text_pairs_meet_wcag_aa`): text-strong 15.7:1, text 13.9:1, text-2 8.6:1, text-muted 6.0:1, accent 11.3:1 on `--bg`; all >= 4.5 on `--bg-sunken` too. Mint only on outcome nodes, the Done node and step numbers; role colours only on the four role dots. |
| **UI: Responsiveness at target viewports** | ☑ pass | Headless Chrome 155 via CDP. `scrollWidth == clientWidth` at 375 (375/375), 768 (768/768), 1024 (1024/1024), 1440 (1440/1440), and at 375 with every Details open (375/375). No element of `.flow-visual` has its right edge past the viewport at 375 (0 found). Flows stack at <= 768 px; the six-step auto flow and the hook lifecycle stack at <= 1100 px (`.is-long`). |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-29T11:53Z at `c00d0fe`, before any implementation commit):

Command: `git show c00d0fe:site/index.html > before_index.html; python3 wc.py before_index.html` (an `html.parser` counter: words of text outside `details`, `pre`, `code`, `svg`, `script`, `style`; script at `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/wc.py`). Output, verbatim:

```
# captured 2026-10-29T11:53:50Z at c00d0fe (git show c00d0fe:site/index.html)
section              visible  total
quick-reference           54     60
what-you-get             103    221
tracks                   365    398
install                  211    296
update-flow              450    711
settings-tool            121   8708
install-variants          65     88
agent-roles              225    239
skills                    93     93
hooks                    235    486
agent-focus              229    284
packs                    105    130
providers                205    258
repository-layout        133    162
memory-system             79    111
mcps                     324    330
options                   14     16
PAGE (sections)         3011  12591
MAIN visible words (incl hero, footer): 3124
```

Baseline for the page-budget test: 3124 visible words in `<main>` (60% = 1874).

BEFORE screenshots, 1440 px, headless Chrome 155 (CDP, `Page.captureScreenshot` clip of the section), directory `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad/t207/before/`:
- `before-tracks-1440.png` (920x824)
- `before-install-1440.png` (920x737)
- `before-update-flow-1440.png` (920x1784)
- `before-hooks-1440.png` (920x1360)

**AFTER** (captured 2026-10-29T12:19Z at `910aca8`, same counter):

```
section              visible  total
quick-reference           54     60
what-you-get             103    221
tracks                   129    489
install                   69    336
update-flow               87    798
settings-tool            121   8708
install-variants          65     88
agent-roles               55    265
skills                    93     93
hooks                    119    575
agent-focus               32    285
packs                    105    130
providers                 26    259
repository-layout        133    162
memory-system             53    147
mcps                     105    333
options                   14     16
PAGE (sections)         1363  12965
MAIN visible words (incl hero, footer): 1476   (47.2% of 3124; limit 1874)
```

Heavy sections, visible words before -> after: tracks 365 -> 129, update-flow 450 -> 87, hooks 235 -> 119, install 211 -> 69, agent-roles 225 -> 55, memory-system 79 -> 53, mcps 324 -> 105, agent-focus 229 -> 32, providers 205 -> 26. Total words per section grew or held (hidden text kept): e.g. tracks 398 -> 489, update-flow 711 -> 798. AFTER screenshots: see the Visual regression row.

**DELTA**: A reader sees a flow chart or diagram first in tracks, install, update flow, hooks, agent roles and memory, and opens Details only when they want the prose, so the page shows 1,476 words on first load instead of 3,124.

**WITNESS**: frontend-developer (implementing agent) ran the counter and the screenshots on 2026-10-29 (BEFORE 11:53Z, AFTER 12:19Z); the trace is `memory/event-trace/T207.jsonl`; a second witness (Supervisor / auto verify) is still required.
