# TASK_REVIEW — T[NNN]: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/site_scrollspy/test_scrollspy.mjs` (5 tests: AC1 fresh-page per link, AC1 sequential, AC2 section at top, AC3 wheel-up after last-section click, 375px drawer click). Before fix: fail 6 of 6 (16 of 17 links wrong). After fix 2026-10-29T15:50Z: `ℹ tests 5 / ℹ pass 5 / ℹ fail 0`. Mutation checks: no wheel release -> AC3 fails; topEdge 0 -> AC2 and AC3 fail. Round 2 (2026-10-29): +3 tests in the same file. RED at 16:04:29Z before the fix: `ℹ tests 8 / ℹ pass 7 / ℹ fail 1` — `✖ round 2: a scroll with no wheel, touch or key event releases the hold` (`actual: [ 'settings-tool' ], expected: [ 'agent-roles' ]`); the smooth-jump and last-section tests are guards that already passed. Green at 16:05:21Z: `ℹ tests 8 / ℹ pass 8 / ℹ fail 0`; `pytest tests/test_site_content.py` 134 passed; settings_tool 59 pass. |
| Verification command run | ☑ pass | `node --test tests/site_scrollspy/*.mjs` pass 5/5; `python3 -m pytest tests/test_site_content.py -q` 134 passed; `node --test tests/settings_tool/*.mjs` pass 59/59. Note: the guide's `node --test tests/site_scrollspy/` (bare directory) errors on Node 26 with MODULE_NOT_FOUND, so the glob form is used. |
| Negative cases hold | ☑ pass | Script still returns early without IntersectionObserver (guard line untouched, before the new code). Wheel after a click releases the hold (AC3). Mutations above fail the tests as expected. Round 2: a mutation that releases on every scroll event fails AC1 (both), 375px and the smooth-jump test, so the settle logic is exercised; a click where the page cannot scroll (`options` at bottom) stays held across 1.3s with no scroll event. |
| verify | ☑ pass | auto-run by hook, session 02bca57e-7f93-493f-9c36-ebaaf51d16ea, commit 82d1ef664840860fde540eece7c806bcf505ed54, log .claude/verify-runs/T213-82d1ef664840.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor code-review 2026-10-29: diff main..HEAD (site/index.html scroll-spy block, tests/site_scrollspy/test_scrollspy.mjs); `lane: C1, 3 files, 260 lines, EXCEEDS (lines 260 > 250)` — excess is the new test file, C1 kept; 0 P0/P1/P2, 3 P3 (scrollbar drag keeps the hold — agreed cut; Space/arrows typed in settings-tool fields release the hold, harmless repaint; links queried twice). Fix matches mental model (a)(b)(c). Supervisor re-run: scrollspy 5/5, test_site_content 134 passed |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests -q` -> `1226 passed in 112.54s`. |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional; C1 Risk Low |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | No CSS touched. Measured at 1440x900 (headless Chrome, CDP): all 17 sidebar links, fresh page and sequential, show exactly the clicked link `.active`; every section that can reach 80px below the top (>=10 of 17) is the active one when scrolled there; after a click on the last 3 links plus a real wheel-up of 1500px, the active link equals the section at the top of the view. No screenshot taken (`reports/` is gitignored). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Diff touches only the scroll-spy script in `site/index.html`; no colour, glow or token edit (`git diff main -- site/theme.css` is empty). The offset is read from the existing `scroll-margin-top` token. |
| **UI: Responsiveness at target viewports** | ☑ pass | 1440x900 and 375x700 (CDP `Emulation.setDeviceMetricsOverride`): open the Menu drawer, click `skills`, `hooks`, `agent-focus`, `options` -> only the clicked link is `.active` each time. No overflow checked; layout unchanged. |
| Repro loop | ☑ pass | `node --test tests/site_scrollspy/*.mjs` on unfixed code, 2026-10-29T15:44:52Z: 16 of 17 links leave the link above active (full list in Demonstration BEFORE). Re-run after fix: no repro. |
| Regression test | ☑ pass | `tests/site_scrollspy/test_scrollspy.mjs` (skips with a message when no Chrome binary is found; set `CHROME` to override). |
| Smoke suite | ☑ pass | Bug-specific: sequential click of all 17 links on one page, plus the 375px drawer click, both pass. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Repro loop = `node --test tests/site_scrollspy/*.mjs` (headless Chrome over raw CDP, 1440x900, `scroll-behavior: auto`, `el.click()` per sidebar link), run 2026-10-29T15:44:52Z on `fix/t213-scrollspy` at `2cb0f2b` (script unchanged from `main`). 16 of 17 sidebar links leave a different link active:
```
what-you-get -> active: [quick-reference]
tracks -> active: [what-you-get]
install -> active: [tracks]
update-flow -> active: [install]
settings-tool -> active: [update-flow]
install-variants -> active: [settings-tool]
agent-roles -> active: [install-variants]
skills -> active: [agent-roles]
hooks -> active: [skills]
agent-focus -> active: [hooks]
packs -> active: [agent-focus]
providers -> active: [packs]
repository-layout -> active: [providers]
memory-system -> active: [repository-layout]
mcps -> active: [memory-system]
options -> active: [memory-system]
```
(only `quick-reference`, the first link, is right). Result: `fail 6` of 6 tests (AC1 x2, AC2, AC3, 375px drawer). Instrumentation after clicking `#skills`: scrollY 5964, `agent-roles` rect top=-446 bottom=40, `skills` top=80; IntersectionObserver hits with today's `rootMargin "0px 0px -60% 0px"` = `["agent-roles","skills"]`; with `"-80px 0px -60% 0px"` = `["skills"]`.

**AFTER**: same command, 2026-10-29T15:50Z, after `site/index.html` fix:
```
✔ AC1: after a click on any sidebar link, only that link is active (fresh page per link)
✔ AC1: clicking every link in order on one page keeps the clicked link the only active one
✔ AC2: a section scrolled to just below the header is the active one
✔ AC3: after clicking a last section, a manual scroll up hands the highlight back to the scroll
✔ 375px: opening the drawer and clicking a link makes that link the only active one
ℹ tests 5  ℹ pass 5  ℹ fail 0
```

**AFTER (round 2)**: 2026-10-29T16:05:21Z, same command: 8 of 8 pass, including `scrollBy(0, 2500)` with no input event after a `#settings-tool` click (active becomes `agent-roles`, the section at the top). Note: the coordinator's `scrollBy(0, 1500)` stays inside `settings-tool` (about 1930px tall), so the test uses 2500.

**DELTA**: Clicking any sidebar link now lights that link (not the one above it), and the highlight follows the section at the top of the view when the user scrolls by hand.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T213.jsonl`, never the
implementing agent alone]
