# TASK_REVIEW — T201: Settings tool profiles — High security and Legacy on the Build tab

> Sibling of `tasks/TASK_GUIDE_T201.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/settings_tool/test_generate.mjs` (AC1-5, AC7 + drift vs profiles.json), `tests/test_site_content.py` (5 new tests: ids order, label/for/values drift, NFR-001, lead, for line). Tail: `ℹ tests 59 / ℹ pass 59 / ℹ fail 0` (node, `*.mjs`); `92 passed` (test_site_content.py); `964 passed in 64.44s` (full `python3 -m pytest tests -q`). Mutations (all RED then green): M1 one high-security rule changed -> node AC2/AC3 + AC4 and pytest `test_page_profiles_values_label_and_for_equal_profiles_json` fail; M2 extra preset id on page only -> node AC1 + AC2/AC3 and pytest `test_page_profiles_match_profiles_json_ids_in_order` fail; M3 old lead sentence restored -> pytest `test_settings_lead_says_what_the_installer_and_stage_1_do` fails; restored -> 59 / 92 pass. |
| Verification command run | ☑ pass | Supervisor re-run 2026-10-29 (active task T201): `node --test tests/settings_tool/*.mjs` → `ℹ tests 59 / ℹ pass 59 / ℹ fail 0`; `python3 -m pytest tests -q` → `964 passed in 70.85s`. Guide command `node --test tests/settings_tool/` fails on Node v26.7.0 with or without this change (implementer finding); the glob form is the working one. |
| Negative cases hold | ☑ pass | Mutations M1 (page high-security rule changed), M2 (page-only preset id), M3 (old lead sentence) each turned tests RED, green on restore (implementer, pasted in Mutations). NFR-001 test: no preset emits `bypassPermissions`, `allow` or `defaultMode`. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor code-review 2026-10-29 on `git diff feat/t200-settings-setup...HEAD` (4 files): 0 P0, 0 P1, 0 P2; P3: Legacy `for` text says "trace anchors", internal wording (comes verbatim from `profiles.json`, T200). Security: new text set with `textContent` only, `aria-describedby` static; no new input path. Startup reads: T185 guide not read (PRD grepped) — P1 process finding per code-review Phase 0.5, recorded, no code effect (T185 patterns followed: confirm still shows, per implementer check). |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests -q` → `964 passed` (Supervisor re-run). |
| **Companion score (easy-verifier)** | ☑ N/A | easy-verifier is optional (T190); not run. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Supervisor screenshots, headless Chrome, High security applied: 1280 px — five `.st-btn` profile buttons on one row, `for` line under the bar in the same muted small text as `.st-why`, output pane shows the deny list; 375 px — buttons wrap to 2 rows, `for` line wraps, no sideways scroll. Visual verdict: matches existing Build-tab styling, no new colors. Shots: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/e4d4da43-1878-4b0a-9367-a5c8960a5d1b/scratchpad/shots/t201-1280.png`, `t201-375-tall.png`. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | Headless Chrome computed style, `#st-presetfor` vs existing `p.st-why`: both `13.6px / rgb(107, 107, 154) / margin-top 3.2px / margin-bottom 4.8px`. No new CSS added, so `test_settings_tool_css_adds_no_color_literals` still passes. |
| **UI: Responsiveness at target viewports** | ☑ pass | Headless Chrome (new headless has a 500 px floor, so 375 was measured in a 375 px iframe on a local server): 375 px: `scrollWidth 360 == clientWidth 360` (scrollbar 15 px), preset bar 5 buttons wrap to height 66.6 px; 1280 px: `scrollWidth 1265 == clientWidth 1265`, bar height 30.1 px (one row). No overflow after click, confirm and Replace. Screenshots not reviewed. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29T07:08:26Z, before any implementation commit, command `node demo.mjs` (loads `site/index.html` core + catalog in node:vm, prints preset ids and the section lead):

```
presets: safe-baseline [no for], solo-engineer [no for], team-project [no for], empty [no for]
lead: Pick the Claude Code settings you want and copy a ready <code>settings.json</code>, or paste yours to check it. The kit installs no settings of its own. Everything stays in your browser.
```

**AFTER**: same probe, 2026-10-29, after the change:

```
presets: high-security [for], legacy [for], solo-engineer [for], team-project [for], empty [for]
lead: Pick the Claude Code settings you want and copy a ready <code>settings.json</code>, or paste yours to check it. The installer adds only the kit's hooks and 2 deny rules.
```
Headless Chrome run on the page: hover Legacy shows "Legacy: Keeps today's kit behavior: only the 2 deny rules that protect the trace anchors."; clicking it gives output `{"permissions":{"deny":["Edit(~/.claude/harness-anchors/**)","Bash(*harness-anchors*)"]}}` and the note "The kit's hooks are added by the installer, not by this file."

**DELTA**: A user can start the Build tab from High security or Legacy as well as Solo engineer, Team project and Empty, read who each is for, and the page values cannot drift from `skills/settings-setup/profiles.json` unnoticed.

**WITNESS**: [left for the Supervisor: derived from `memory/event-trace/T201.jsonl`]

---

## Decisions

1. **Intro split in two.** `test_visible_lead_paragraphs_are_one_line_summaries` caps a lead at 35 words. The lead keeps the true installer fact ("The installer adds only the kit's hooks and 2 deny rules."). The Stage 1 / approval / never-removes sentences sit in a second paragraph, `p.st-why`, so no new CSS. SAFER OPTION: keeps the existing cap test, no test loosened.
2. **`for` line** is `p#st-presetfor.st-why`, filled by `textContent` (never `innerHTML`). Buttons get `aria-describedby="st-presetfor"`. Hover or focus shows that profile as "Label: for text"; otherwise the last applied profile while the picks still equal it (any edit ends it, so the line and the Legacy note never describe a stale state); otherwise the hint "Point at a profile to see who it is for." Touch users see it after a tap, because a tap applies the profile.
3. **Legacy note** is a `note` field on the Legacy preset in the catalog, appended to the existing `#st-note` text only while Legacy is the active unedited profile. Only Legacy has a `note` (tested).
4. **Catalog stays compact**: `high-security`, `solo-engineer`, `team-project` keep `$suggest` for deny/ask (the catalog `suggest` lists already equal the profile lists); the drift tests expand `$suggest` and compare to `profiles.json` in both node (through the real `applyPreset`) and pytest. `legacy` lists its 2 rules explicitly.
5. **AC3 "generate() equals"**: pytest compares expanded values (no node subprocess); the node test compares `applyPreset` output to `profiles.json` through the real core, and AC4/AC5 test `generate()` output.
6. **Verification command**: `node --test tests/settings_tool/` (directory form from the guide) exits with `test failed` on this machine's Node v26.7.0 even before my change (checked with `git stash`); the glob form `node --test tests/settings_tool/*.mjs` runs all 59 tests. Not fixed (out of scope); Supervisor may want the guide command changed.
7. **Not done**: `Skill code-review` and `Skill verify` were not invoked (no Skill tool in this run); screenshots not taken or reviewed (the Visual regression row is left for the Supervisor); Evidence rows other than the ones above are untouched.
