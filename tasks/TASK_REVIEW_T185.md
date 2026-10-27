# TASK_REVIEW — T185: Site Settings tool, part 1 — Build mode

> Sibling of `tasks/TASK_GUIDE_T185.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/settings_tool/test_generate.mjs (16 tests: presets, target filtering, validation, nesting, no-network); tests/test_site_content.py (+5 T185 tests). node: ℹ tests 16 ℹ pass 16 ℹ fail 0 ; pytest: 68 passed in 0.12s |
| Verification command run | pass | `node --test "tests/settings_tool/*.mjs" && python3 -m pytest tests/test_site_content.py -q` -> ℹ tests 16 ℹ pass 16 ℹ fail 0 / 68 passed in 0.12s. The guide form `node --test tests/settings_tool/` fails on Node 26.7 (directory arg is read as a module path), so the glob form is used |
| Negative cases hold | pass | Mutation: catalog entry `model` with `why` removed -> pytest test_settings_catalog_shape_and_version_stamp FAILED and node 'catalog ... required shape' FAILED (pass 15 / fail 1); restored -> 16/16 and 68 passed. Out-of-range numbers omitted, user-only keys removed on project/local |
| verify | pass | /verify 2026-10-27 (user-invoked, Supervisor ran it): headless Chrome over CDP, file:// page, 13 steps — presets, preset-over-picks confirm bar, target switch removes user-only keys with note ("2 keys removed: not read from .claude/settings.local.json"), bypassPermissions on Local removed with row message, cleanupPeriodDays=0 rejected, markup typed into a deny rule rendered as text (0 img elements), duplicate rule refused, filter, Copy fallback ("Text selected. Press Ctrl+C to copy."), Check tab disabled, output JSON.parse valid, 375px scrollWidth 375, no console errors, no network requests — pass. Friction: empty-list tick emits nothing; filter with no match shows a blank list; category "on" count includes a removed key |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Supervisor code-review 2026-10-27: scope = `site/index.html` (new `#settings-tool` section, catalog, core + UI scripts, scoped CSS), `tests/settings_tool/test_generate.mjs`, `tests/test_site_content.py`. No callers outside the page. lane_check: `C2, 3 files, 779 lines, EXCEEDS (lines 779 > 500)` — ~330 lines are the inline catalog JSON (data), so C2 stands |
| Full smoke suite still green (no regression) | pass | Supervisor re-run in worktree: `sh scripts/validate.sh` → `validate.sh: PASS`; `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `1452 passed, 25 subtests passed in 30.34s`; `node --test "tests/settings_tool/*.mjs"` → `tests 16 · pass 16 · fail 0` |
| **UI: Visual regression (diff or verdict pasted)** | pass (self-assessed) | Headless Chrome via CDP, Team project preset + Project target: 1280px shows catalog left, output right (4 keys · valid); 375px stacks. Screenshots in scratchpad (tool-375/768/1280.png), Supervisor to confirm visually |
| **UI: Design-system compliance (tokens/colors/typography verified)** | pass | test_settings_tool_css_adds_no_color_literals (no #hex/rgb/hsl in the scoped CSS); reuses .tag, .chip, pre.install, details, code styles |
| **UI: Responsiveness at target viewports** | pass for the tool; page-level finding | CDP at 375/768/1280: columns 343px / 440px (stacked) / 2x454px. documentElement.scrollWidth is 375 / 851 / 1265 at 375/768/1280. The 851px at 768 is the existing hooks table (TABLE right edge 851), same value on the pre-change page, not from #settings-tool. Light theme: the page has dark tokens only, so no light capture exists |

### Stage 4 — code-review (Supervisor, 2026-10-27)

P0: none. P1: 1 (process). P2: 3. P3: 2. Safe fixes applied: 0 (no code P0/P1).

| Sev | Where | Finding | Conf | Action |
|-----|-------|---------|------|--------|
| P1 (process) | agent report | Startup reads: `agents/frontend.md` not read; `PROJECT_SPEC.md` only skimmed — Permanent-Rule reads (T129 check) | 100 | Recorded. No code impact found in review; user decides whether it blocks merge |
| P2 | catalog `permissions.defaultMode` | The `bypassPermissions` value lowers safety but the row carries no "lowers safety" badge (guide Catalog note: "bypass lowersSafety") | 100 | Suggest: badge text "bypass lowers safety", or a per-value warning in the row |
| P2 | `.github/workflows/ci.yml` | Neither `node --test "tests/settings_tool/*.mjs"` nor `tests/test_site_content.py` runs in CI (site pytest gap pre-dates T185) | 100 | Follow-up task; out of T185 file scope |
| P2 | catalog `knownKeys` | Holds only catalog keys + a few named ones, not the full reference key list | 100 | Forwarded to T187 (its W2 unknown-key rule needs the full list) |
| P3 | catalog `why` text | `blockReadsOutsideWorkingDirectories` says "sibling worktrees (../wt-tNNN)" and `disableBypassPermissionsMode` says "not a gate" — kit-internal wording on a public page | 75 | Suggest plain wording |
| P3 | guide | Verification Command `node --test tests/settings_tool/` fails on Node 26.7 (directory read as module) | 100 | Fixed on `main` in both T185 and T187 guides: quoted glob form |

Visual check (Supervisor viewed `tool-1280.png` and `tool-768.png`): two columns at 1280, stacked at 768; output pane scrolls inside its own box (`max-height: 28rem; overflow: auto`, focusable). Light theme: N/A — the site is dark-only by design.

Banned-API grep on `site/index.html` (`fetch(`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`, `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, `innerHTML`, `<form`): no matches.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-27T14:47:45Z, worktree wt-t185, before any implementation commit):
```
$ python3 -m pytest tests/test_site_content.py -q
...............................................................          [100%]
63 passed in 0.14s
$ grep -c 'settings-tool' site/index.html
0
$ ls tests/settings_tool
ls: cannot access 'tests/settings_tool': No such file or directory
```

**AFTER**: `grep -c settings-tool site/index.html` -> 57; pytest 68 passed in 0.12s; node ℹ tests 16 ℹ pass 16 ℹ fail 0 

**DELTA**: A developer can pick Claude Code settings on the site, choose the target file, and copy valid formatted JSON.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
