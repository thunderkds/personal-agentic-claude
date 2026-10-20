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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py`: `test_tables_do_not_force_a_minimum_width_or_scroll_sideways` (AC1), `test_long_code_tokens_in_table_cells_can_wrap` (AC2), `test_every_td_carries_its_columns_header_as_data_label` (AC3), `test_phone_layout_stacks_each_row_as_a_card_with_labelled_cells` (AC4). Observed RED first: `4 failed, 54 passed`; GREEN after the change: `58 passed`. |
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
