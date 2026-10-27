# TASK_REVIEW — T186: Site Settings tool, part 2 — Check mode

> Sibling of `tasks/TASK_GUIDE_T186.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/settings_tool/test_check.mjs` (38 new node tests: one or more per rule E1–E5, W1–W7, I1–I2; clean file; empty paste; format; masking; tree; fromSettings; round trip over every fixture; `__proto__`/builtin keys; AC8 fixture; 30-finding fixture; 1 MB / depth-200 robustness). Synthetic fixtures `tests/settings_tool/fixtures/{clean_project,local_broad_allow,many_findings}.json`. `tests/test_site_content.py`: T185 tab assertion changed to "Check tab enabled" (AC1 reverses it); new `test_settings_check_mode_controls_and_privacy_line`, `test_settings_tool_never_writes_html_from_text`. Implementing agent, 2026-10-27T15:35:34Z |
| Verification command run | ☑ pass | `node --test "tests/settings_tool/*.mjs" && python3 -m pytest tests/test_site_content.py -q` at 3a86ccd, 2026-10-27T15:35:34Z: `ℹ tests 54 / ℹ pass 54 / ℹ fail 0` then `70 passed in 0.15s`. Mutation (2026-10-27T15:34:18Z): W3 rule deleted from the core block → `ℹ fail 4` incl. `✖ W3: broad allow rule, exactly one W3 plus I1 (Success 1)`; restored → 54 pass |
| Negative cases hold | ☑ pass | Node: `{,}` → E1 line 1 col 2; BOM and `//`/`/* */` named; a `/**` rule glob not blamed as a comment; E1 never echoes pasted text; empty paste → no findings; `permissions: null` → E3; `<script>` rules carried as text; `__proto__`/`constructor`/`toString` keys → W2, no prototype pollution. Robustness (node): 1 MB keys 238 ms (41001 findings), depth 200 1.4 ms, depth 200 under permissions/hooks/env 3.5 ms, 1 MB string 16 ms. In page (CDP): 1 MB Check+Format 151 ms (300 rows drawn + "more not shown"), depth 200 6 ms, no console errors |
| verify | ☐ pass / ☐ fail / ☐ N/A | Pending: the `verify` skill was not run by the implementing agent (no Skill tool in its session) — Supervisor to run. Agent's own headless Chrome CDP run (file:// page, 27 steps) passed 27/27: tab + arrow keys, privacy line, empty hint, 36 findings for the 30-finding fixture, no `ghp_`/`sk-ant` in findings/map DOM, map groups + deny→ask→allow columns, 36 badges, finding→node highlight+focus, Format masked / Keep shows secrets, Format on `{,}` → E1 and no output, Edit in Build (tab, target, hooks + unknown keys kept, secrets removed), UI round trip deep-equal, Add in Build, markup as text (0 img), 0 network requests |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Supervisor Stage 4: `site/index.html` (core + UI + catalog), `tests/settings_tool/test_check.mjs`, fixtures, `tests/test_site_content.py`; no callers outside the page |
| Full smoke suite still green (no regression) | pass | `validate.sh: PASS`; full pytest 1448 passed, 6 failed — none from this branch's code (see Stage 4 note: 5 = hot-tier budget fixed on main 41562ab; 1 = this file's unfilled verify row) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass (self-assessed) | Headless Chrome CDP, `many_findings.json` checked as Project: 1280px shows findings (tag · path · problem + fix) then map (Permissions deny/ask/allow columns with W3/W4/I1 badges, Hooks event ▸ matcher ▸ command with W6 badges), then Formatted — matches the wireframe. Screenshots: scratchpad `shots/check-{375,768,1280}-{findings,map}.png` (paths in the agent report). Supervisor to confirm visually |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `test_settings_tool_css_adds_no_color_literals` green: no color literal in the scoped CSS. Severity reuses `.tag` + `tag-block` (error), `tag-inert` (warn), `tag-advise` (tip), plus a ●/▲/○ symbol and the word, so not color-only. All new CSS is under `#settings-tool`; `code` / body styles reused |
| **UI: Responsiveness at target viewports** | ☑ pass for the tool; page-level note | CDP 375/768/1280: section right edge 359/736/1233 ≤ viewport; findings list 343/440/928 px with 0 children past its right edge; map 341/423/911 px wide, scrolls inside itself at 375/768 (scrollWidth 512). documentElement.scrollWidth 375/851/1265 — the 851 at 768 is the existing hooks table, same as T185's pre-change measurement. Dark-only page: no light theme exists, so no light capture |

### Stage 4 — code-review + security-review (Supervisor, 2026-10-27)

Re-run by Supervisor in the worktree: `node --test "tests/settings_tool/*.mjs"` → `tests 54 · pass 54 · fail 0`; `python3 -m pytest tests/test_site_content.py -q` → `70 passed`; `sh scripts/validate.sh` → `validate.sh: PASS`; full `pytest .claude/hooks/tests/ tests/` → 6 failed / 1448 passed: 5 = `MEMORY.md` hot-tier budget (Supervisor's T185 memory commit, fixed on `main` 41562ab, not this branch's code) and 1 = `test_verify_row_fill_detection` AC6 reading this file's unfilled `verify` row (clears when /verify fills it).
lane_check: `C2, 6 files, 1129 lines, EXCEEDS (lines 1129 > 500); unpredicted: tests/test_site_content.py` — the unpredicted edit inverts T185's "Check tab disabled" assertion, which AC 1 requires; ~250 lines are `knownKeys` data. C2 stands.
Startup reads: all Permanent-Rule reads present (PROJECT_SPEC.md, guide, agents/frontend.md).

**code-review** — P0: none. P1: none. P2: 2. P3: 3.

| Sev | Where | Finding | Conf | Action |
|-----|-------|---------|------|--------|
| P2 | catalog `knownKeys` | `$schema` is reported W2 "unknown key" — real settings files often carry it (editor schema hint), so most real pastes get a false warning | 100 | Suggest: treat `$schema` as known and ignored. User decision (not in the reference) |
| P2 | agent process | Agent ran only the task's Verification Command, not the full suite | 100 | Recorded; Supervisor ran it (above) |
| P3 | `maskText` | Free-text masking skips token runs that contain `/` (keeps paths readable), so a base64 secret with `/` inside a hook command or `apiKeyHelper` string can show. `env` values use the full guide rule | 75 | Documented limit; tighten later if wanted |
| P3 | T185 friction | Ticking an empty list setting emits nothing; a filter with no match shows a blank list | 100 | Still open (outside T186 edits) |
| P3 | parse | Duplicate JSON keys are not detected (`JSON.parse` keeps the last) | 100 | Documented limit |

**security-review** (Medium risk; focus XSS via pasted text, persistence/transmission) — no findings.
- Rendering: every pasted value reaches the DOM through `textContent` (the shared `el()` helper sets `text` via `textContent`; attribute values come from code or catalog, never from pasted keys into `href`/`on*`). Banned-API grep (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(`, `new Function`, `fetch(`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`, `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, `<form`): no matches.
- Secrets: map built from `maskSecrets(data)`; findings mask via `short()`; Format output masked unless "keep secret values" is ticked; Build gets `""` for secret env values by default.
- Prototype pollution: object copies use `Object.defineProperty` on fresh objects and `hasOwnProperty`; agent's `__proto__` / `constructor` test passes.
- Robustness: 1 MB check+format 151 ms in page; depth 200 6 ms; render capped at 300 rows per list.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-27T15:14:26Z, worktree `feat/t186-settings-tool-check` at b949bb8, before any implementation commit; node v26.7.0):

```
$ node --test "tests/settings_tool/*.mjs"
...
✔ statusLine is emitted as a command object (0.101738ms)
✔ output always round-trips through JSON.parse with 2-space indent (0.453555ms)
✔ unknown selection keys are ignored (0.06674ms)
✔ tool script source holds no network or storage API (spec rule 1) (0.25171ms)
ℹ tests 16
ℹ pass 16
ℹ fail 0
$ python3 -m pytest tests/test_site_content.py -q
68 passed in 0.18s
$ grep -n -i "coming soon" site/index.html
584:    <button type="button" role="tab" class="st-tab" aria-selected="false" disabled id="st-tab-check">Check <span class="st-soon">(coming soon)</span></button>
```

Note: the Check tab is disabled "(coming soon)"; no `check`, `format`, `fromSettings` or `maskSecrets` function exists, and there is no `tests/settings_tool/test_check.mjs`.

**AFTER** (2026-10-27T15:35:34Z, commit 3a86ccd, node v26.7.0):

```
$ node --test "tests/settings_tool/*.mjs"
# robustness 1 MB keys: 1002781 chars, 41001 findings, 238.2 ms
# robustness depth 200: 1201 chars, 2 findings, 1.4 ms
✔ E1: invalid JSON names line 1, column 2 for {,} (0.359608ms)
✔ W3: broad allow rule, exactly one W3 plus I1 (Success 1) (0.325519ms)
✔ round trip: generate(fromSettings(parsed)) deep-equals every fixture (1.166337ms)
...
ℹ tests 54
ℹ pass 54
ℹ fail 0
$ python3 -m pytest tests/test_site_content.py -q
70 passed in 0.15s
```

The Check tab is enabled (no "coming soon"). The page now has a paste area, Format / Check / Edit in Build and a findings list. It also has a map grouped by category. Browser run over CDP: 27/27 steps pass.

**DELTA**: A developer can paste a `settings.json`, see it formatted, see each problem with its fix and a grouped map, and load it into Build without losing any key. Secret values stay hidden.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
