# TASK_REVIEW — T279: The Home and Docs links in the top nav are 44px wide on phones

> Sibling of `tasks/TASK_GUIDE_T279.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. Reworded AC 2 from "`0 under 44px`" to "`Home` and `Docs` are not in the tap-probe banner" — SAFER OPTION: the whole-page probe lists 129 targets on `docs.html` and 16 on `index.html`, so the first wording could never pass; fixing them all is a different, larger task ⚠ decided for you — please review
2. Did not register a follow-up task for the other targets under 44px (body links, journey cards, Settings-tool controls) — SAFER OPTION: inline text links are a usual exemption and the user asked only for the nav; they are listed under `Not done:` ⚠ decided for you — please review
3. Did not merge or push, though the request said "merge and push" — RULE: `docs/claude-md/tracks.md` `## Auto mode` table row 19, "Merge, push and `ship`: never in auto mode"
4. Spawned the implementer on `claude`, sonnet — FACT: `PROJECT_SPEC.md` `## CLI Model Table`, row `claude`, C1 `sonnet`
Checks: tests `python3 -m pytest tests .claude/hooks/tests -q -p no:cacheprovider` — 3427 passed; reviews code-review — 0 P0, 0 P1, 0 P2 (security-review not run, Risk Low); real run `tap_probe.py` on `docs.html` and `index.html` at 375px — banner no longer lists `Home` or `Docs` (auto-checked, not /verify)
Memory: `memory/decisions.md` — T279 nav width decision; `memory/learnings.md` — tap_probe scans the whole page
Not done: merge (yours); push (yours, also the T278 merge `07d70c4e` on `main`); the other tap targets under 44px (not on the board); auto verify: running (T182)

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t279_nav_tap_targets.py` (2 tests: min-width + centring in the phone block; no min-width leak outside it). Red first: `1 failed, 1 passed` on the unchanged CSS. Implementer's run; the reviewer re-runs. |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_t279_nav_tap_targets.py tests/test_site_content.py tests/test_site_story.py tests/test_site_visual_first.py tests/test_docs_t151.py -q` -> `221 passed in 0.76s`. Wider `-k "site or docs or t278 or t279"` -> `253 passed, 1653 deselected`. No baseline or pin edited. |
| Negative cases hold | ☑ pass | Mutation (implementer): removed `min-width: 44px` on line 302 (`git diff --stat`: `site/theme.css`, 1 insertion, 1 deletion), new test -> `FAILED ...test_page_nav_links_are_44px_wide_and_centred_on_phones` (`1 failed, 1 passed`); restored, `221 passed`. Reviewer re-runs. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `code-review` (Supervisor, inline) on `main...fix/t279-nav-tap-targets`: `site/theme.css` (1 line), `tests/test_t279_nav_tap_targets.py` (new), guide and this file. Consumers: `docs.html` and `index.html` (shared header), the site CSS pin tests. Lane check: `lane: C1, 2 files, 46 lines, FITS`. Findings: 0 P0, 0 P1, 0 P2. Security-review not run: Risk Low, CSS only. Implementer's own scope note: nothing else reads `.page-nav a`. |
| Full smoke suite still green (no regression) | ☑ pass | In the worktree at `733d4729`: `python3 -m pytest tests .claude/hooks/tests -q -p no:cacheprovider` -> `3427 passed, 25 subtests passed in 190.07s`. |
| **Companion score (easy-verifier)** | ☑ N/A | Not run: the score skill is optional and this is a one-line CSS change. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | 375px and 1280px screenshots read: header keeps brand, Home, Docs (and Menu on docs.html) on one row; 1280px header unchanged (rule is inside the 719px block; test pins it). Paths: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/bb743e7c-a3c3-44e9-972e-46e28295830d/scratchpad/after/{docs,index}-{375,1280}.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/bb743e7c-a3c3-44e9-972e-46e28295830d/scratchpad/geo/W-WORK-{docs,index}.png`. Implementer's reading; the reviewer re-reads. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | CSS audit: `git diff site/theme.css` shows one line changed, only `min-width: 44px; justify-content: center;` added to the existing `.page-nav a` rule in the phone block. No new color, font or token. |
| **UI: Responsiveness at target viewports** | ☑ pass | 375px measured inside a 375px iframe (headless Chrome cannot open a window under 500px): `scrollWidth 360` = viewport minus scrollbar, no sideways scroll; `Home` and `Docs` are 44px wide (`w44`); on docs.html Menu `x272-344` is on screen. 1280px viewed. 768px not shot: the rule sits in the 719px block, test pins it. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-07T09:32:15Z on the unchanged tree, commit `60e18ae2`, no implementation commit exists):
Command: `python3 skills/ux-evaluate/scripts/tap_probe.py <abs page> <scratch>/before`, then `google-chrome --headless --disable-gpu --window-size=375,1200 --screenshot=<png> file://<probe page>`; PNG opened with Read. Screenshots (scratch, not in repo): `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/bb743e7c-a3c3-44e9-972e-46e28295830d/scratchpad/before/docs-before-375.png`, `.../before/index-before-375.png`. Both show red boxes on `Home` and `Docs` in the header.
- `site/docs.html` banner, verbatim start: `tap-probe: 131 under 44px: Home 38x44; Docs 31x44; Update flow 81x19; on 13x13; Reference for permissions.deny 19x24; ...` (the rest are Settings-tool catalog controls and body links, not in this task's scope)
- `site/index.html` banner, verbatim: `tap-probe: 18 under 44px: Home 38x44; Docs 31x44; You ask 54x19; It plans 54x19; Agents build 87x19; It checks 64x19; You merge 73x19; Stage 0: Define 99x18; Stage 1: Set up 98x18; Stage 2: Plan 86x18; Stage 3: Build 90x18; Stage 4: Review 104x18; Stage 5: Ship 85x18; Any stage 63x18; Agents 48x19; Skills 38x19; Memory 56x19; Add-ons 59x19`

**AFTER** (same commands, same tree plus the one-line CSS change, 2026-11-07, screenshots `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/bb743e7c-a3c3-44e9-972e-46e28295830d/scratchpad/after/docs-375.png` and `.../after/index-375.png` read):
- `site/docs.html` banner: `tap-probe: 129 under 44px: Update flow 81x19; on 13x13; Reference for permissions.deny 19x24; ...` (131 -> 129; `Home` and `Docs` no longer listed)
- `site/index.html` banner: `tap-probe: 16 under 44px: You ask 54x19; It plans 54x19; Agents build 87x19; ...` (18 -> 16; `Home` and `Docs` no longer listed)
- No red box on `Home` or `Docs` in either image. AC 2 as first written (`0 under 44px`) could not be met by this task: the remaining entries are body links, journey cards, stage links and Settings-tool controls, all out of scope. The Supervisor reworded AC 2 to "`Home` and `Docs` not listed" (guide commit `733d4729`; Auto decision 1); AC 2 as reworded is met.

**DELTA**: A phone user can tap `Home` and `Docs` in the site header at 44 by 44 px instead of 38 by 44 and 31 by 44.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
