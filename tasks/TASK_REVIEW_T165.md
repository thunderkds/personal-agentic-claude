# TASK_REVIEW — T165: The landing page reads as a scan-first reference, and links the Easy Verifier site

> Sibling of `tasks/TASK_GUIDE_T165.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass / ☐ fail | `tests/test_site_content.py` (T165 block, 8 tests): `test_visible_lead_paragraphs_are_one_line_summaries` (AC1), `test_visible_table_cells_are_short` (AC2), `test_page_has_details_foldouts_with_content` (AC3), `test_quick_reference_is_the_first_section_and_has_a_nav_link` + `test_quick_reference_shows_install_and_update_commands` + `test_quick_reference_shows_the_stage_sequence_from_the_pipeline_doc` (AC4), `test_quick_reference_counts_match_source` (AC5 — skill count from `skills/`, spawnable roles from agent `name:` frontmatter, blocking hooks = wired `settings.json` hooks whose hook-table row carries `tag-block`, total = wired hooks), `test_verifier_section_links_the_easy_verifier_site_beside_the_repo` (AC6). **RED first** (commit `8d261b8`, page unchanged), 2026-10-20T10:04:57+07:00: `8 failed, 39 passed in 0.14s` — all 8 new tests FAILED. **GREEN** after `e6892d5`/`d470d8d`: `53 passed in 0.11s` (site + docs-match files). |
| Verification command run | ☑ pass / ☐ fail | 2026-10-20T10:12:56+07:00 — `python3 -m pytest tests/test_site_content.py tests/test_docs_match_installer.py -q` → `53 passed in 0.11s`; `python3 -m pytest .claude/hooks/tests tests -q \| tail -1` → `1383 passed, 25 subtests passed in 88.32s (0:01:28)`; `sh scripts/validate.sh` → `validate.sh: PASS`. **AC7 diff** (base `2b4c73c`) → `missing: []` — all 125 BEFORE `<code>` tokens present. |
| Negative cases hold | ☑ pass / ☐ fail | M1–M4 (each applied to the page, `tests/test_site_content.py` run, page restored; `git status` clean afterwards): **M1** 40-word sentence in the header's visible lead → `1 failed, 46 passed` — `test_visible_lead_paragraphs_are_one_line_summaries`. **M2** quick-reference `30 skills` → `29 skills` → `1 failed, 46 passed` — `test_quick_reference_counts_match_source`. **M3** Easy Verifier site link removed → `1 failed, 46 passed` — `test_verifier_section_links_the_easy_verifier_site_beside_the_repo`. **M4** a visible `<td>` padded to 30 words → `1 failed, 46 passed` — `test_visible_table_cells_are_short`. |
| verify | ☐ pass / ☐ fail / ☐ N/A | user-run `/verify` — not run by the implementer |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass / ☐ fail | Supervisor Stage 4 (2026-10-20): scope = `site/index.html` + `tests/test_site_content.py` diff from `2a439d5`, plus page readers `tests/test_docs_t151.py`, `tests/test_docs_match_installer.py`, `tests/test_readme_current.sh` (all re-run green). `lane: C2, 2 files, 373 lines, FITS`. Agent's note: Diff touches `site/index.html` + `tests/test_site_content.py` only (plus this file). Other suites that read the page: `tests/test_docs_t151.py` (line-based — first draft broke `test_ac4_trace_hook_row` / `test_ac5_memory_slice_rows_mention_decisions`; fixed by keeping each fold-out on its table row's line), `tests/test_docs_match_installer.py`, `tests/test_vercel_config.py` — all green. |
| Full smoke suite still green (no regression) | ☑ pass / ☐ fail | `1383 passed, 25 subtests passed` (see the Verification row) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass / ☐ fail / ☐ N/A | Headless Chrome (`google-chrome --headless=new`) screenshots at 1280px and 375px, checked by eye: the header, the new quick-reference card (dt/dd grid, wrapped install `<pre>`), and the hooks table with one fold-out forced open all render with the existing look. Pipeline SVG unchanged (`test_pipeline_diagram_*` green). Hooks table width measured unchanged vs BEFORE: `wrap=639 table=716` both (its sideways scroll was already there). The header's new `Providers` link showed in the browser default link colour on the dark surface, so I put back the original plain text "see Providers below" (`d470d8d`). No pixel-diff tooling — this verdict is by eye. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass / ☐ fail / ☐ N/A | New CSS covers only `.quick-ref`, `details` and `summary`, and uses only existing `:root` variables (`--surface`, `--surface2`, `--border`, `--muted`, `--cyan`). Scan of added lines: `git diff 2b4c73c -- site/index.html \| grep '^+' \| grep -E "#[0-9a-fA-F]{3,8}\b\|rgba?\(\|font-family\|url\(\|<img\|<script"` → nothing found. Reuses `pre.install`, `.table-wrap`, `.tag-*`, `ul.lead`. `<details>` is native, so fold-outs work with JS off. The sidebar script still finds every section — `#quick-reference` is a `main > section[id]` with a nav link. |
| **UI: Responsiveness at target viewports** | ☑ pass / ☐ fail / ☐ N/A | Headless Chrome can't make a window narrower than about 485px, so I loaded the page in a 375px iframe (`--allow-file-access-from-files`) and measured it in the browser: `vw=360 scrollWidth=360 overflowing=[] qrpre=286/286` — no horizontal page scroll, and no element outside a `.table-wrap` overflows. The quick-reference install `<pre>` wraps inside its block (its scrollWidth equals its clientWidth). At ≤767px the dl collapses to one column. Not checked: real mobile devices or Safari/Firefox rendering. |

---

## Demonstration

**BEFORE** (Supervisor, 2026-10-20T09:46:03+07:00, `site/index.html` on `main` @ `2b4c73c`):

```
visible words: 2699
lead paragraphs: 30 words in them: 1207 longest: 99
td cells: 118 cells >25 words: 9 longest: 43
details elements: 0
```

Verbatim `#verifier` link line before the change:

```html
<p><a href="https://github.com/thunderkds/easy-verifier-mcp" target="_blank" rel="noopener noreferrer">easy-verifier-mcp on GitHub</a></p>
```

**AFTER** (Frontend-Implementer, 2026-10-20T10:12:56+07:00, `site/index.html` @ `d470d8d`; same metrics, plus a split by `<details>`):

```
visible words: 2748            (whole page incl. fold-out text, SVG excluded — BEFORE by the same method: 2697)
visible words outside <details>: 2356
lead paragraphs: 29 words in them: 726 longest: 35
td cells: 126 cells >25 words: 9 longest: 89   (counting fold-out text inside the cell)
outside <details>: td cells >25 words: 0 longest: 25
details elements: 14
```

(Method note: my visible-word count excludes `<script>`, `<style>` and the pipeline `<svg>`. Applied to `2b4c73c` it gives 2697, not the Supervisor's 2699 — a tokenizer difference of 2 words.)

New `#verifier` link line:

```html
<p><a href="https://github.com/thunderkds/easy-verifier-mcp" target="_blank" rel="noopener noreferrer">easy-verifier-mcp on GitHub</a> &middot; <a href="https://easy-verifier.vercel.app/" target="_blank" rel="noopener noreferrer">Easy Verifier site</a></p>
```

**DELTA**: A reader now gets the install/update command, stage sequence and roster counts from a card at the top. Every lead reads as a ≤35-word summary and every table cell as ≤25 words, with the detail one click away in 14 native fold-outs. The verifier section links the Easy Verifier site — and no `<code>` fact from the old page was dropped (`missing: []`).

**WITNESS**: Supervisor re-run 2026-10-20T03:17:30Z, recorded in `memory/event-trace/T165.jsonl` (`scripts/verify_trace.py T165` → `INTACT: lines 1-22 chained and anchored`): site tests `53 passed`, full suite `1383 passed, 25 subtests passed`, `validate.sh: PASS`, `test_readme_current: ALL PASS`, AC7 `missing: []`; visible words outside `<details>` 2699 → 2358, 14 fold-outs. Independent 1280px headless-Chrome screenshot viewed by the Supervisor: quick-reference card and header render with the page's existing look. The implementer's own Bash calls after 10:03 local did not reach the trace (agent's note), so this witness rests on the Supervisor re-run.

## Stage 4 — code-review (Supervisor, 2026-10-20)

P0 0 · P1 0 · P2 1 · P3 2. No safe fixes applied (none P0/P1). Startup reads line present, all three Permanent-Rule reads named. Entry point `site/index.html` reachable.

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P2 | `site/index.html` quick-reference Roster | "4 blocking hooks (of 9)" counts `pre_tool_sensitive_path.py`, which **asks** for confirmation rather than blocks; the count follows the hook table's pre-existing `tag-block` styling on that row | 75 | Suggest: user decides wording (e.g. "4 gating hooks") — left as is |
| P3 | `site/index.html` header | "View the Supervisor GitHub repository" link renders in browser-default blue on the dark header (pre-existing, visible in the screenshot) | 100 | Follow-up, out of T165 scope |
| P3 | page overall | Visible text dropped 13% (2699 → 2358 words); the gain is structure (card, bullets, fold-outs), not volume | 100 | Inform user; further cuts would need fact removal or more fold-outs |

**security-review (Medium risk, Gate-2 floor)**: diff adds no script, form, input handling or external asset (`test_no_external_assets`, `test_all_scripts_are_inline` green); the one new outbound link uses `target="_blank" rel="noopener noreferrer"`. No findings.
