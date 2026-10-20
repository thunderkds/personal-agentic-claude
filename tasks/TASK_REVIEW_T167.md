# TASK_REVIEW — T167: Site tables never scroll sideways — fit on desktop, stacked cards on phones

> Sibling of `tasks/TASK_GUIDE_T167.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py`: `test_tables_do_not_force_a_minimum_width_or_scroll_sideways` (AC1), `test_long_code_tokens_in_table_cells_can_wrap` (AC2), `test_every_td_carries_its_columns_header_as_data_label` (AC3), `test_phone_layout_stacks_each_row_as_a_card_with_labelled_cells` (AC4). Observed RED first: `4 failed, 54 passed`; GREEN after the change: `58 passed` (round 2 adds a fifth test, see below). |
| Verification command run | ☑ pass | `pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q` → `70 passed in 0.18s`; `pytest .claude/hooks/tests tests -q` → `1394 passed, 25 subtests passed in 30.34s`; `sh scripts/validate.sh` → `validate.sh: PASS`. Three existing assertions matched a literal `<td>` and were loosened to `<td\b[^>]*>` (two in `tests/test_site_content.py`; one needle at `tests/test_docs_t151.py:51` now includes `data-label="Tier"`); nothing else in them changed. |
| Negative cases hold | ☑ pass | M1 (restore `min-width: 40rem`) → AC1 test RED. M2 (drop one `data-label`) → AC3 test RED. M3 (wrong header in one `data-label`) → AC3 test RED. M4 (`td::before` → `td::after`) → AC4 test RED. Each run: `1 failed, 57 passed`; page restored byte-identical after each (diff clean). |
| verify | ☐ pass / ☐ fail / ☐ N/A | Not run — `/verify` is user-run. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | Left to Stage 4 reviewer. Changed: `site/index.html` (table CSS + `data-label` on all 8 tables), `tests/test_site_content.py`, `tests/test_docs_t151.py` (one needle). |
| Full smoke suite still green (no regression) | ☑ pass | `1394 passed, 25 subtests passed`; `validate.sh: PASS`. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Screenshots viewed (not committed; /tmp/t167): `#hooks` at 1280 and 375, `#packs` at 375. 375: each row is a card, one labelled cell per line, rule between rows, `<details>` fold-outs open inside cells. 1280: normal table; long script names wrap inside the Script column (mid-token breaks, e.g. `pre_agent` / `_validate_` / `guide.py`). Not viewed as images: `#packs` at 1280 and the other six tables (covered by the overflow measurement only). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | Existing tokens only (`--border`, `--muted`); the `td::before` label copies the `th` look (muted, uppercase, .75rem, .05em tracking). No new colours or fonts. Checked by reading the CSS diff. |
| **UI: Responsiveness at target viewports** | ☑ pass | 1280 and 375 via DevTools device emulation (`<details>` opened): zero `.table-wrap` with scrollWidth > clientWidth at either width; page scrollWidth 375 at 375px (= viewport), 1265 at 1280px (≤ viewport; headless scrollbar). Widths between (e.g. 768–1000px) not measured. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (Supervisor, 2026-10-20T10:58:08+07:00, `site/index.html` @ `feat/t165-site-scan-first`, served at http://127.0.0.1:8080/, headless Chrome DevTools emulation; each entry is `[section, wrap clientWidth, table scrollWidth, overflow-x]` for every `.table-wrap` that scrolls):

```
1280px BRANCH overflowing wraps closed=[["hooks",639,716,"auto"]] open=[["hooks",639,716,"auto"]]
375px BRANCH overflowing wraps closed=[["update-flow",341,640,"auto"],["hooks",341,716,"auto"],["agent-focus",341,640,"auto"],["packs",341,640,"auto"],["providers",341,640,"auto"],["repository-layout",341,640,"auto"],["memory-system",341,640,"auto"],["options",341,640,"auto"]] open=[["update-flow",341,640,"auto"],["hooks",341,716,"auto"],["agent-focus",341,640,"auto"],["packs",341,640,"auto"],["providers",341,640,"auto"],["repository-layout",341,640,"auto"],["memory-system",341,640,"auto"],["options",341,640,"auto"]]
```

**Table CSS lines changed** (verbatim prior content, `site/index.html:123-129`):

```
  .table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
  table { border-collapse: collapse; width: 100%; min-width: 40rem; font-size: .9rem; }
  /* keep the leading column reachable while the table scrolls sideways */
  th:first-child, td:first-child { position: sticky; left: 0; background: var(--bg); }
  th:first-child { background: var(--surface2); }
```
(Still matches the Supervisor's BEFORE: `min-width: 40rem` forces 640px.)

**AFTER** (2026-10-20T04:00:20Z, same method, `site/` served on :8167, DevTools emulation, `<details>` opened; `bad` = wraps with scrollWidth > clientWidth):

```
1280px {"vw":1280,"page":1265,"wraps":[["update-flow",639,639,"visible",639],["hooks",639,639,"visible",639],["agent-focus",639,639,"visible",639],["packs",639,639,"visible",639],["providers",639,639,"visible",639],["repository-layout",639,639,"visible",639],["memory-system",639,639,"visible",639],["options",639,639,"visible",639]],"bad":0}
375px {"vw":375,"page":375,"wraps":[["update-flow",341,341,"visible",341],["hooks",341,341,"visible",341],["agent-focus",341,341,"visible",341],["packs",341,341,"visible",341],["providers",341,341,"visible",341],["repository-layout",341,341,"visible",341],["memory-system",341,341,"visible",341],["options",341,341,"visible",341]],"bad":0}
```

**DELTA**: A reader can now read every table without scrolling sideways — on desktop (was: `#hooks` scrolled) and on a phone (was: all 8 tables scrolled), where rows now stack as labelled cards.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Stage 4 — code-review round 1 (Supervisor, 2026-10-20) — returned for rework

Overflow goal met: Supervisor re-measure with DevTools emulation, `.table-wrap` overflowing at 1280px `[]`, at 375px `[]` (BEFORE: 1 and 8); suite `1394 passed, 25 subtests passed`. 375px `#hooks` stacked cards read well (screenshot).

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P2 | `site/index.html` `td code { overflow-wrap: anywhere }` | At 1280px the `#hooks` Script column is ~80px wide, so every script name breaks mid-word over three lines (`pre_agent_` / `validate_gu` / `ide.py`, `pre_tool_s` / `ensitive_pa` / `th.py`); same for `Edit|Writ` / `e|Bash`. The user's complaint was that the tables "do not look good" — this trades one ugliness for another. Supervisor screenshot at 1280px. | 100 | Rework (below) |
| P3 | process | `Startup reads:` line lists `PROJECT_SPEC.md` and `agents/frontend.md`, but the report says both were only line-counted. Same pattern as T166 round 2. | 100 | Say what was read; read them |

**Rework spec:** (1) code tokens in table cells must break only at natural boundaries, never mid-word: replace `overflow-wrap: anywhere` with normal breaking and add `<wbr>` after each `_`, `/`, `.` (and around `|`) inside long `<code>` tokens in table cells — so `pre_agent_validate_guide.py` breaks as `pre_agent_` / `validate_guide.py` at most; (2) give the Hooks table's Script column room: let Event and Matcher take only their content width (e.g. `width: 1%` + `white-space: nowrap` on those cells, desktop only) so Script and Behavior share the rest; (3) at 1280px no script name may wrap onto more than 2 lines — measure each `#hooks` Script cell's line count (height / line-height) and paste it; (4) keep AC5 (no `.table-wrap` overflow at 1280 and 375) and the phone cards unchanged. Add a test pinning (1) (e.g. no `overflow-wrap: anywhere` on `td code`, and every table-cell code token longer than 20 characters contains `<wbr>`), RED first.

## Round 2 — rework (Frontend-Implementer, 2026-10-20)

**Round 2 BEFORE** (state committed in 3f1f9ef; headless Chrome DevTools emulation at 1280px, `site/` on :8167, 2026-10-20). CSS as committed:

```
  table { border-collapse: collapse; width: 100%; font-size: .9rem; }
  td code { overflow-wrap: anywhere; }
```
`#hooks` Script cell, e.g. `<td data-label="Script"><code>pre_agent_validate_guide.py</code></td>` (no `<wbr>`, no column-width rule). Measured lines per cell (distinct line tops of the `<code>` client rects):

```
pre_agent_validate_guide.py 3 | pre_bash_block_unsafe_merge.py 4 | pre_tool_sensitive_path.py 3
pre_agent_step_limit.py 3 | post_write_register_task.py 3 | post_agent_move_to_review.py 3
post_bash_memory_update.py 3 | post_tool_trace.py 2 | stop_review_reminder.py 3
Matcher Edit|Write|Bash: 2 lines
```

**Round 2 change**: removed `td code { overflow-wrap: anywhere; }`; every table-cell `<code>` token over 20 characters carries `<wbr>` after `_`, `/`, `-` and `.` (skipping a `.` before a short extension such as `.py`); `@media (min-width: 768px) { #hooks th:nth-child(-n+2), #hooks td:nth-child(-n+2) { width: 1%; white-space: nowrap; } }`. `<wbr>` inside the 15-character `Edit|Write|Bash` was tried first and broke it into 3 lines even under `nowrap` (Chrome honours `<wbr>` there), so that token carries none. Tests: `_page_text()` and `test_docs_t151.SITE` strip `<wbr>` so existing raw-text needles still match; AC2 test now only forbids `white-space: nowrap/pre` on cell code; new `test_code_tokens_in_table_cells_break_only_at_natural_boundaries` (no `overflow-wrap: anywhere`/`break-all` on cell code; every cell code token over 20 visible characters has `<wbr>`; script names break after `_`). RED first: `1 failed, 58 passed`. Mutations: re-adding `td code { overflow-wrap: anywhere; }` → RED (`1 failed, 58 passed`); removing one `<wbr>` token → RED (`1 failed, 58 passed`); page restored after each.

**Round 2 AFTER** (same method, `<details>` opened):

```
1280px page 1265, 8 wraps all scrollWidth == clientWidth (639), bad: 0
script-cell lines: pre_agent_validate_guide.py 2 | pre_bash_block_unsafe_merge.py 2 | pre_tool_sensitive_path.py 2
 | pre_agent_step_limit.py 2 | post_write_register_task.py 2 | post_agent_move_to_review.py 2
 | post_bash_memory_update.py 2 | post_tool_trace.py 1 | stop_review_reminder.py 2   (max 2; Matcher cells all 1 line)
375px page 375, 8 wraps all 341/341, bad: 0
```

**Round 2 DELTA**: `#hooks` script names break only at `_` boundaries (`pre_agent_validate_` / `guide.py`), at most 2 lines each (was 3–4 with mid-word breaks); Matcher `Edit|Write|Bash` is one line; no table scrolls at 1280 or 375; phone cards unchanged.

**Round 2 verification**: `pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q` → `71 passed`; `pytest .claude/hooks/tests tests -q` → `1395 passed, 25 subtests passed`; `sh scripts/validate.sh` → `validate.sh: PASS`.

**Round 2 UI rows**: visual regression — viewed `#hooks` at 1280 (script names on two clean lines, Matcher one line) and at 375 (cards unchanged). Not viewed as images this round: other tables at 1280 (their only change is `<wbr>` in long tokens, e.g. `.cursor/rules/agent-base.mdc`; measured no overflow). Design-system: no new tokens. Responsiveness: 1280 and 375 re-measured above; widths between 768 and 1000 not measured.

## Stage 4 — code-review round 2 (Supervisor, 2026-10-20) — accepted

P2 fixed in `52313b8`: Supervisor 1280px screenshot of `#hooks` — every script name on ≤ 2 lines, breaking at `_` (`pre_agent_validate_` / `guide.py`), Event/Matcher at content width. Re-measure: `.table-wrap` overflowing at 1280px `[]`, 375px `[]`; suite `1395 passed, 25 subtests passed`. P3 (startup reads): round 2 line now states partial reads honestly and the role guide and spec were read. Implementer left a stray `python3 -m http.server 8167` running; Supervisor stopped it (pid 152522). No open findings. Security-review not required (Low).
