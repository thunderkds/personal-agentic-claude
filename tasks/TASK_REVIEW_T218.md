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


## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_tech_lead_pack.sh` (new, 12 checks incl. mutation controls M1-M3); `tests/test_site_visual_first.py` updated entry. Output: `12 passed, 0 failed` (AC1 files + frontmatter, AC2 sections, AC3 map template, AC4 agent rules, AC5 PACK.md, AC6 README, AC8 not activated, M1 never-edit rule removed -> AC4 check fails, M2 ER section renamed -> AC2 check fails, M3 `setup.sh --pack` line added -> AC5 check fails) |
| Verification command run | ☑ pass | `bash tests/test_tech_lead_pack.sh && bash tests/test_pack_catalog.sh && python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py -q` -> rc 0: `12 passed, 0 failed`; `16 passed, 0 failed`; `149 passed in 0.47s`. Full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `6 failed, 2544 passed`: 5 failures are memory-budget tests (`test_memory_channel_and_budget.py` x4, `test_token_audit_format.py` x1), the same 5 fail on main without this change; 1 failure is `tests/test_ci_wires_shell_suites.py::test_every_real_suite_is_wired_or_excluded` — it names `test_tech_lead_pack.sh`, which needs a `run:` step in `.github/workflows/ci.yml` (CI config, not changed by the implementer; Supervisor decision) |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

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
