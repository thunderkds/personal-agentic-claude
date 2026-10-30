# TASK_REVIEW — T218: `packs/tech-lead` — tech-lead agent + architecture-docs skill

> Sibling of `tasks/TASK_GUIDE_T218.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. Brainstorming path: Option B — one `tech-lead` agent + one `architecture-docs` skill in `packs/tech-lead` (alternatives: A six per-document skills; C core agent, no pack) — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` row 4 (take the recommended direction) ⚠ decided for you — please review
2. The pack is not activated in this repo (no copy into `agents/`/`skills/`); PACK.md documents the manual approved copy until `select-packs` (T117) — SAFER OPTION: activation changes the live agent roster and ADR-0002 requires explicit approval ⚠ decided for you — please review
3. Task breakdown: T218 pack + README + site `#packs` row (site row folded in because `tests/test_site_content.py::test_every_pack_appears_on_page` fails without it); T219 pipeline pointers (hub file, Risk Medium); T220 stale `setup.sh --pack` lines (minimal track) — RULE: `docs/claude-md/tracks.md` row 12 (the Supervisor's own breakdown)
4. "Docs, guide" delivered as a user guide section in `packs/tech-lead/PACK.md`, the README pack list and the site row — RULE: user request "remember to add the docs, guide for that" ⚠ decided for you — please review
5. Code-review P1 fixes applied by the Supervisor during Stage 4 (approval signal; roadmap watched paths) — RULE: `.claude/skills/code-review/SKILL.md` § Phase 4 (apply unambiguous P0/P1 fixes)
6. `.github/workflows/ci.yml` gains the step that runs `tests/test_tech_lead_pack.sh` — RULE: `tests/test_ci_wires_shell_suites.py` `test_every_real_suite_is_wired_or_excluded`
Checks: tests `bash tests/test_tech_lead_pack.sh && bash tests/test_pack_catalog.sh && python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q` — `12 passed, 0 failed` / `16 passed, 0 failed` / `149 passed`; full suite `5 failed, 2545 passed` (pre-existing memory budget, fixed on main `5e0c7588`); reviews code-review — pass after 2 P1 + 1 P2 fixed, security-review not required (Risk Low); real run: followed the skill's map step on this repo — wrote `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/25310414-c88c-4c99-8e98-12ab54a13be4/scratchpad/t218-realrun/README.md`: 4 needed (C4, auto-verify sequence, install journey, risk register), ER and roadmap not needed with reasons, 6 link rows (auto-checked, not /verify)
Memory: memory/MEMORY.md — hot tier trimmed 42,252 → 41,884 chars (12 index lines shortened, `5e0c7588`, on main); memory/decisions.md — T218–T220 tech-lead pack entry (written on main at the end of the run)
Not done: merge (yours); activation of the pack in this repo (yours, ADR-0002); auto verify: ☑ pass (session 464804bf-6862-4a40-ac03-c45d74994d39, commit c4fdd7d021a291d4da6fb4aea90d75fd7e62297e, log .claude/verify-runs/T218-c4fdd7d021a2.log)
Paused: done not moved — Gate 6: the `UI: Design-system compliance` row has no evidence

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_tech_lead_pack.sh` (new, 12 checks incl. mutation controls M1-M3); `tests/test_site_visual_first.py` updated entry. Output: `12 passed, 0 failed` (AC1 files + frontmatter, AC2 sections, AC3 map template, AC4 agent rules, AC5 PACK.md, AC6 README, AC8 not activated, M1 never-edit rule removed -> AC4 check fails, M2 ER section renamed -> AC2 check fails, M3 `setup.sh --pack` line added -> AC5 check fails) |
| Verification command run | ☑ pass | `bash tests/test_tech_lead_pack.sh && bash tests/test_pack_catalog.sh && python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q` -> rc 0: `12 passed, 0 failed`; `16 passed, 0 failed`; `149 passed in 0.47s`. Full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `6 failed, 2544 passed`: 5 failures are memory-budget tests (`test_memory_channel_and_budget.py` x4, `test_token_audit_format.py` x1), the same 5 fail on main without this change; 1 failure was `tests/test_ci_wires_shell_suites.py::test_every_real_suite_is_wired_or_excluded` (needed a `run:` step); after the Supervisor-approved two-line `ci.yml` step: `python3 -m pytest tests/test_ci_wires_shell_suites.py -q` -> `5 passed in 0.01s`, `bash tests/test_tech_lead_pack.sh` -> `12 passed, 0 failed` |
| Negative cases hold | ☑ pass | `git diff main...HEAD --stat`: nothing under `agents/`, `skills/`, `.claude/`, `setup.sh`, `MANIFEST`; mutation controls M1 (never-edit rule removed), M2 (ER section renamed), M3 (`setup.sh --pack` line added) each turn a check red — `12 passed, 0 failed` |
| verify | ☑ pass | auto-run by hook, session 464804bf-6862-4a40-ac03-c45d74994d39, commit c4fdd7d021a291d4da6fb4aea90d75fd7e62297e, log .claude/verify-runs/T218-c4fdd7d021a2.log — pass; done not moved: Gate 6: the `UI: Design-system compliance` row has no evidence |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review on `main...feat/t218-tech-lead-pack` (9 files) — pass with 2 P1 fixed in `3eda6335` (map approval signal; roadmap stopped watching `PROJECT_KANBAN.md`) + 1 P2 fixed in `2fa995ad`; lane_check `EXCEEDS (lines 548 > 500); unpredicted: .github/workflows/ci.yml` (Markdown-heavy; ci.yml wiring required by `tests/test_ci_wires_shell_suites.py`) |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` — `5 failed, 2545 passed`; the 5 are the hot-tier memory budget tests, red on `main` too since `ad7f928c` and fixed on `main` by `5e0c7588` (MEMORY.md 41,884 chars, `18 passed`); none from this diff. `bash tests/test_pack_catalog.sh` — `16 passed, 0 failed` |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional companion; T218 is Risk Low Markdown + one shell test |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | headless Chrome screenshots of `#packs` (section rendered alone with the site CSS; the full page fades sections in on scroll): `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/25310414-c88c-4c99-8e98-12ab54a13be4/scratchpad/t218ui/packs-1280.png` — 6 rows, the `tech-lead` row matches the other five; `packs-375-bottom.png` — stacked card like the others |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | computed-style probe in headless Chrome: `{"rows":6,"sameCode":true,"sameTd":true,"overflow":0}` — the new row's code and td cells' font-family/size/color/background/padding equal the `api` row's; the row diff adds no class or inline style |
| **UI: Responsiveness at target viewports** | ☑ pass | 375, 768, 1280 px: `overflow` (scrollWidth − clientWidth) = 0 at each; 375 px renders the stacked `data-label` card |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (verbatim prior content, captured 2026-10-30 before the first implementation commit; non-executable change plus one new test):

`ls packs/`:
```
ai-agent
api
data
devops
mobile
```
`README.md:73` (pack list):
```
Repository layout, agent guides, packs (`mobile`/`data`/`devops`/`ai-agent`/`api`), the custom
```
`site/index.html:319` (hero count):
```
    <li><a href="#packs"><span class="num">5</span><span class="label">optional domain packs</span></a></li>
```
`site/index.html` `#packs` tbody: five rows, `mobile`, `data`, `devops`, `ai-agent`, `api`; the last one reads:
```
<tr><td data-label="Pack"><code>api</code></td><td data-label="Domain">REST/gRPC, OpenAPI, auth flows</td><td data-label="Agent"><code>api-designer</code></td><td data-label="Skills"><code>contract-review</code>, <code>auth-checklist</code></td></tr>
```
`tests/test_site_visual_first.py:245`:
```
    ("44b38a258e5f", '5optional domain packs'),
```
No `packs/tech-lead/` and no `tests/test_tech_lead_pack.sh` exist.

**AFTER** (verbatim new content):

`ls packs/`: `ai-agent api data devops mobile tech-lead`

`README.md:73`: ``Repository layout, agent guides, packs (`mobile`/`data`/`devops`/`ai-agent`/`api`/`tech-lead`), the custom``

`site/index.html:319`: `<li><a href="#packs"><span class="num">6</span><span class="label">optional domain packs</span></a></li>`

`site/index.html` `#packs` new last row:
```
<tr><td data-label="Pack"><code>tech-lead</code></td><td data-label="Domain">Top project documents: C4, sequence, journey, ER, risks, roadmap</td><td data-label="Agent"><code>tech-lead</code></td><td data-label="Skills"><code>architecture-docs</code></td></tr>
```
`tests/test_site_visual_first.py:245`: `    ("ad14bdffefcc", '6optional domain packs'),`

New files: `packs/tech-lead/PACK.md` (with `## User guide`), `packs/tech-lead/agents/tech-lead.md`, `packs/tech-lead/skills/architecture-docs/SKILL.md`, `tests/test_tech_lead_pack.sh`.

**DELTA**: A user can activate an optional `tech-lead` agent that writes an approved document map and then the project's C4, sequence, journey, ER, risk and roadmap documents in `docs/architecture/`, and can read how to do so in `packs/tech-lead/PACK.md`, the README and the site.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
