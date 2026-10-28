# TASK_REVIEW — T199: site MCPs section lists easy-memory-mcp

> Sibling of `tasks/TASK_GUIDE_T199.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py`: 7 new tests in a T199 block plus `test_mcps_section_has_one_named_entry_per_server` now expecting three; red first: `8 failed, 78 passed` (2026-10-28T08:33:08Z) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_site_content.py -q` -> `86 passed` (agent); Supervisor re-ran full review below |
| Negative cases hold | ☑ pass | M1 to M4 each turn a test RED and revert green (agent output in the Demonstration block below) |
| verify | ☑ pass | /verify T199 (user-invoked, 2026-10-28), pass: the real page served over HTTP and loaded in headless Chrome showed three cards in order (easy-verifier-mcp, easy-ui-mcp, easy-memory-mcp), the lead "Three separate companion tools...", the first bullet "Without it installed, the kit runs as before — it is optional and not needed", link `https://github.com/thunderkds/easy-memory-mcp` with `target=_blank rel="noopener noreferrer"`, 4 `<code>` chips, no banned phrase in the rendered `#mcps` text, no console or page errors, and the sidebar `MCPs` link target exists. Probe pass: at 780 px the page overflows horizontally (scrollWidth 851), but identically on `main`; the overflowing element is a `TABLE` outside `#mcps`, so it is not caused by T199. Limit: scroll-to-anchor could not be observed in headless Chrome (it did not scroll for the existing `#easy-ui-mcp` either), so only that the ids and nav target exist is verified. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor read the full `site/index.html` and `tests/test_site_content.py` diffs; no other file changed. Merge-conflict spots with T194: the `#mcps` lead sentence and `test_mcps_section_has_one_named_entry_per_server`. Multi-reviewer `code-review` skill not run (copy and tests only) |
| Full smoke suite still green (no regression) | ☑ pass | agent run: `python3 -m pytest tests -q -x` -> `880 passed in 41.64s` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Supervisor render of `#mcps` with the page's own CSS at 900 px wide (headless Chrome): the third card has the same border, heading colour, lead, bullet list, `<code>` chips and link row as the easy-ui card. Screenshot: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/354ed0dc-1ecc-43c8-9c57-a47ef83f4256/scratchpad/shot_mcps2.png` |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | headless Chrome computed styles of `h3`, `.lead`, `li` and the card (font size/weight/family, colour, margins, padding, border, radius, background): identical for easy-ui-mcp and easy-memory-mcp at both widths. No new CSS class or colour (`git diff` touches no `<style>`) |
| **UI: Responsiveness at target viewports** | ☑ pass | At 1280 px: `scrollWidth 1265` of `innerWidth 1280`, all three cards 641 px wide, links visible. At 375 px (iframe): `scrollWidth 360` of `innerWidth 375`, cards 328 px wide, links inside the viewport. Baseline `main` gives the same numbers, so no new overflow |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28, before any implementation commit; worktree `/home/hungnguyenhuu/workspace/pets/wt-t199`, branch `feat/t199-site-easy-memory-card`):

(a) Verbatim `#mcps` section lead and both card headings from `site/index.html` (lines 2013-2036 at capture):

```html
<section id="mcps">
<h2>MCPs</h2>
<p class="lead">
  Two separate companion tools, not part of this kit: MCP servers you can run alongside it, each from its own repository.
</p>

<div class="agent-card" id="verifier">
<h3>easy-verifier-mcp</h3>
...
<div class="agent-card" id="easy-ui-mcp">
<h3>easy-ui-mcp</h3>
```

There is no `id="easy-memory-mcp"` card. `grep -c easy-memory-mcp site/index.html` is 0.

(b) Existing test file before any edit:

```
$ date -u +%Y-%m-%dT%H:%M:%SZ && python3 -m pytest tests/test_site_content.py -q
2026-10-28T08:32:24Z
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 0.26s
(finished 2026-10-28T08:32:25Z)
```

(c) New tests failing (red) before the card exists:

```
$ date -u +%Y-%m-%dT%H:%M:%SZ && python3 -m pytest tests/test_site_content.py -q   # after writing tests, before the card
2026-10-28T08:33:08Z
FAILED tests/test_site_content.py::test_mcps_section_has_one_named_entry_per_server
FAILED tests/test_site_content.py::test_mcps_section_lead_counts_three_companions
FAILED tests/test_site_content.py::test_memory_mcp_card_is_the_third_card_and_says_optional
FAILED tests/test_site_content.py::test_memory_mcp_card_has_four_to_five_one_line_highlights
FAILED tests/test_site_content.py::test_memory_mcp_card_says_the_kit_runs_as_before_without_it
FAILED tests/test_site_content.py::test_memory_mcp_card_names_the_four_tools_from_the_readme
FAILED tests/test_site_content.py::test_memory_mcp_card_states_the_token_figure_only_as_a_scripted_test_result
FAILED tests/test_site_content.py::test_memory_mcp_card_links_the_repo_safely_and_invents_no_site
8 failed, 78 passed in 0.50s
```
(e.g. `AssertionError: #mcps has no entry with id="easy-memory-mcp"`.)

**AFTER** (2026-10-28, agent run, same command):

```
$ python3 -m pytest tests/test_site_content.py -q
86 passed in 0.21s
$ python3 -m pytest tests -q -x
880 passed in 41.64s
```

Section lead now reads `Three separate companion tools, not part of this kit: ...`. New third card `<div class="agent-card" id="easy-memory-mcp">` with `<h3>easy-memory-mcp</h3>`, 5 one-line highlights, and one link to `https://github.com/thunderkds/easy-memory-mcp` (`target="_blank" rel="noopener noreferrer"`).

Mutations by hand (each applied alone, suite run, page restored; restored page: 86 passed):

| Mutation | Result |
|---|---|
| M1 insert `the kit ships with easy-memory-mcp` | RED: `test_mcps_section_says_separate_and_never_claims_kit_integration` (1 failed, 85 passed) |
| M2 insert `easy-memory-mcp is required` | RED: same test (1 failed, 85 passed) |
| M3 delete the "Without it installed, the kit runs as before" highlight | RED: `test_memory_mcp_card_says_the_kit_runs_as_before_without_it` (1 failed, 85 passed) |
| M4 remove the repo link | RED: `test_memory_mcp_card_links_the_repo_safely_and_invents_no_site` (1 failed, 85 passed) |

**DELTA**: A visitor to the site sees easy-memory-mcp listed beside the other two companion tools, labelled optional, with the kit shown to run as before without it and with the 28% figure tied to scripted tests.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
