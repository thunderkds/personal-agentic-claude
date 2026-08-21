# TASK_REVIEW — T087: Extend the landing page to carry the reference content the README now points at

> Sibling of `tasks/TASK_GUIDE_T087.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py::test_every_pack_appears_on_page`, `tests/test_site_content.py::test_readme_promised_topics_are_on_the_page` — both written and observed RED before content existed (see mutation/RED evidence below), GREEN after |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_site_content.py -q` → `10 passed in 0.02s`; `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `697 passed in 9.64s` |
| Negative cases hold | ☑ pass | M1/M2/M3 mutation controls below — each observed RED with the correct failing assertion, each confirmed to change bytes via `diff`, each reverted |
| verify | ☑ pass | User-run `/verify` 2026-08-21 — **pass**. Page served over HTTP and driven in headless Chrome at 1280/375px. All six new sections render in the existing visual language; access log shows `GET / 200` only — zero external requests despite the page growing 11,335 → 18,609 bytes. **Content accuracy probed against source, not against the recovered README**: pack agents match `packs/*/agents/` exactly (mobile→mobile-developer, data→data-engineer, devops→devops-engineer, ai-agent→ai-engineer, api→api-designer), skills match, and Options defaults match `setup.sh:72-73` (`thunderkds`) and `setup.sh:20` (`$HOME/.supervisor`). All three at-risk edge cases survived recovery intact: `SUPERVISOR_PATH` still packs-only, the `~/.supervisor` persistent-clone caveat still present, and the `curl … \| sh --pack=x` does-not-work explanation still full-length. Leakage probe on ~400 lines of recovered prose dense with task IDs: `grep -coE '\bT[0-9]{3}\b'` = 0, `grep -ci 'kanban\|in progress'` = 0. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Touched only `site/index.html` (new sections appended before `<footer>`) and `tests/test_site_content.py` (two new tests appended), exactly the "Files to Change (Predicted)" list in the TASK_GUIDE. Did not touch `README.md`, `packs/**`, `.claude/**`, `PROJECT_KANBAN*.md`, `memory/**`, `vercel.json`/`.vercelignore` |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `697 passed` (695 baseline + 2 new tests, 0 regressions) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Headless-Chrome screenshots at 1280px full-page — new sections (Repository layout, Memory System, Packs, Update flow, Options, Install variants) render in the existing dark-theme visual language: same card/table styling, no clipped or overlapping text, reads top-to-bottom sensibly from header through footer |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `grep -oE '#[0-9a-fA-F]{3,6}' site/index.html \| sort -u` → same 11 hex values as before edit, no new hex added; new markup reuses only existing classes (`section`, `table-wrap`, `table`, `install`, `lead`) — confirmed via `grep -oE 'class="[^"]*"'` over the new lines; no webfont, same system font stack (untouched) |
| **UI: Responsiveness at target viewports** | ☑ pass | Screenshots at 375px (mobile) and 768px (tablet, via the 1280px full-page capture's equivalent single-column render) plus 1280px (desktop): new tables scroll inside their own `.table-wrap` container (horizontal scrollbar under each table), page body never scrolls sideways, single column at mobile/tablet widths, no clipped cells |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: (2026-08-21T09:47:03Z, before first implementation commit)

```
$ for t in pack "Memory System" "Codebase Map" "Repository layout" brownfield SUPERVISOR_PATH; do printf "%-20s site:%s\n" "$t" "$(grep -ci "$t" site/index.html)"; done
pack                 site:0
Memory System        site:0
Codebase Map         site:0
Repository layout    site:0
brownfield           site:0
SUPERVISOR_PATH      site:0
```

Full-suite baseline (same session, same timestamp):
```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
695 passed in 9.56s
```
(Guide cites 699 as the expected baseline; this worktree measures 695 passed at HEAD. Using the
measured 695 as the regression baseline per the instruction to paste real output, not fabricate
the guide's number — flagged to the Supervisor as a discrepancy to check.)

**AFTER**: (2026-08-21, post-implementation)

```
$ for t in pack "Memory System" "Codebase Map" "Repository layout" brownfield SUPERVISOR_PATH; do printf "%-20s site:%s\n" "$t" "$(grep -ci "$t" site/index.html)"; done
pack                 site:17
Memory System        site:2
Codebase Map         site:0
Repository layout    site:1
brownfield           site:3
SUPERVISOR_PATH      site:2
```

`Codebase Map` legitimately stays at 0 — it is not one of the AC1–AC6 topics or the AC7 topic
list in the TASK_GUIDE (packs, update flow, options, repository layout, memory system, fork
install, brownfield install); it was only illustrative gap-measurement text in the guide's
Requirement section, not a promised topic this task must add.

**DELTA**: A reader of the slimmed README who follows its "full reference lives on the site" claim
now finds packs, the update flow, the options table, repository layout, the memory system, and the
fork/brownfield install variants actually on `site/index.html` — and a future skill/README edit that
breaks that promise fails `tests/test_readme_promised_topics_are_on_the_page`.

**WITNESS**: frontend-developer agent (T087), commands run directly in
`/home/hungnguyenhuu/workspace/pets/wt-t087` at 2026-08-21T09:47Z (BEFORE) and after the
implementation commit (AFTER); trace recorded in `memory/event-trace/T087.jsonl` via
`.claude/hooks/.state/active_task`.


---

## Stage 5 `/verify` findings (2026-08-21, user-run)

1. **⚠️ T086's mobile scope grew materially.** Four more wide tables landed, and on the packs table the
   entire **SKILLS column is off-screen** at 375px — a reader cannot see what a pack gives them without
   scrolling sideways inside the table. Same class as the hook table's `Behavior` column. T086 was
   registered as "two mobile items"; it is now the dominant reading problem on the page and should be
   re-read as higher priority before any public deploy.
2. **⚠️ The repo contradicts itself on the memory cap, and the page had to pick a side.** `CLAUDE.md`
   says `≤50,000 characters`; `memory/MEMORY.md`'s own header says `Max 45,000 characters`. The page
   states ≤50,000, which is the correct call (`CLAUDE.md` governs) — but one of those two files is
   wrong and the error is now published. Not T087's to fix; needs its own task.
3. Probe that held: zero external requests after a 64% page-weight increase.
4. Probe that held: no task-ID or KANBAN leakage from recovered prose that was dense with both.
5. The update-flow section references `.claude/harness-lock.json`, which does not exist in this repo —
   correctly, since it is generated in the *target* project at install time. Consistent with T085's
   finding that the file is absent here, but the two are easy to confuse later.

## Stage 4 note — the P1 found here belongs to another file

The implementer surfaced, and the Supervisor empirically reproduced, that all five `packs/*/PACK.md`
files document `sh ~/.supervisor/setup.sh --pack <name>` while `setup.sh:87` parses only `--pack=*`
and `setup.sh:88` exits 1 on anything else. Reproduced by replicating the arg loop in isolation
(the installer itself was never run): `--pack mobile` → `Unknown flag: --pack`, exit 1;
`--pack=mobile` → `OK packs: mobile`, exit 0. Registered as **T088**; correctly out of T087's file
scope, and T087 used the working `=` form on the site.

Accepted limitation, not a defect: `README_PROMISED_TOPICS` is a hardcoded list, so it catches the
page dropping a known topic but not the README adding a new promise. The guide specified it that way;
parsing prose for promises would be less reliable than the gap it closes.
