# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. On first use, the Supervisor creates `tasks/MINIMAL_LOG.md` from
> this template and deletes the example comment. The same block is the Supervisor's final chat message.

## T220 — Drop the stale `setup.sh --pack` install lines · minimal
Mode: auto
**Asked:** "compose all the tasks related, run with [auto], remember to add the docs, guide for that."
**Decisions:**
1. Track minimal — C1, Risk Low, docs text in 7 files + one test list; no user data, no UI — RULE: `docs/claude-md/tracks.md` track rule
2. Each PACK.md `## Install` section becomes `## Activate`: the pack ships inactive (ADR-0002); after approval the Supervisor runs two `cp` lines; `setup.sh` takes no options — FACT: `docs/adr/0002-one-confirmed-menu-driven-installer.md:83` "The installer copies all of `packs/` into the project as a **Pack catalog**"
3. Took over the `docs/claude-md/folder-structure.md` `--pack=` line that `tests/test_docs_match_installer.py` exempted for T117, and deleted the exemption (the test's own rule: delete it the moment the line is fixed). T117 (`select-packs`) still owns the automation — RULE: `tests/test_docs_match_installer.py` `test_owned_exemptions_are_still_needed`
4. Added `packs/tech-lead/` to the folder-structure pack list; merge T218 first so the line names a pack that exists ⚠ decided for you — please review
**Checked:**
- New test `test_live_docs_show_no_install_flags` (LIVE_DOCS now includes `packs/*/PACK.md` + `templates/PACK_template.md`) — failed before the change (11 hits: `--pack=` and `~/.supervisor` in 5 PACK.md + template), passes after
- Suite: `python3 -m pytest .claude/hooks/tests/ tests/ -q` — `5 failed, 2542 passed`; the 5 are the hot-tier memory budget tests (`memory/MEMORY.md` 42,252 > 42,000), failing identically on `main` since `ad7f928c`, not from this change; `bash tests/test_pack_catalog.sh` — `16 passed, 0 failed`
- Real run: `grep -rn -e "--pack" -e "supervisor/setup" packs templates/PACK_template.md docs/claude-md/folder-structure.md` — printed nothing (no stale line left)
**Memory:** nothing new for T220 (the run's memory pass is recorded in `tasks/TASK_REVIEW_T218.md`)
**Files:** `packs/{mobile,data,devops,ai-agent,api}/PACK.md`, `templates/PACK_template.md`, `docs/claude-md/folder-structure.md`, `tests/test_docs_match_installer.py`
**Not done:** merge (yours); auto verify: running (T182)

## T216 — Plugin spike: can the kit ship as a Claude Code plugin, and does the folder work in Codex · minimal
**Asked:** "go spike" — after "so what is your final solution" (Option C, step 1 of `docs/brainstorming/BRAINSTORMING_LOG_distribution.md`)
**Decisions:**
- Throwaway plugin in `experiments/plugin-spike/` (one skill, one agent, one blocking hook); kit code untouched — a spike answers questions, it ships nothing.
- Gate hook no-ops unless the folder has `PROJECT_KANBAN.md` — plugin hooks run in every repo where the plugin is on.
- Installs tested against throwaway config folders (`CLAUDE_CONFIG_DIR`, `CODEX_HOME` in the session scratchpad) — the user's real Claude and Codex configs stay unchanged; the Codex login copy (mode 0600) was deleted after each run.
- Not retried: the Codex run with `--dangerously-bypass-hook-trust` was refused by the session safety check; the Codex gate result stays open.
- Assumed: haiku runs are enough to test loading and blocking (no reasoning quality is measured).
**Checked:**
- New test `tests/test_plugin_spike.py` — 5 failed before the plugin existed, `5 passed in 1.42s` after
- Suite: `python3 -m pytest -q tests .claude/hooks/tests` — `2547 passed, 25 subtests passed in 145.88s`; `bash scripts/validate.sh` — `validate.sh: PASS`
- Real run (Claude Code 2.1.314, 5 headless haiku runs, $0.018): kit folder `ekspike gate: 'SPIKE_BLOCK_ME' is blocked in a kit project`; plain folder ran; `ekspike:probe` → `PROBE_OK`; bare `probe` → `Agent type 'probe' not found. Available agents: claude, ekspike:probe, …`; skill script by `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}` both `HELLO_OK`; marketplace install `Successfully installed plugin: ekspike@ekspike-market (scope: user)`
- Real run (codex-cli 0.163.0): same folder `Added plugin ekspike from marketplace ekspike-market`; skill listed as `ekspike:hello`; gate did NOT block (`SPIKE_BLOCK_ME` printed); `codex features list`: `plugin_hooks removed false`
- verify: ☑ pass — auto-run by hook, session a68ce49f-fda6-4965-8821-25bc9240579b, commit 79b59ad75a7a53fe66cea87759a4fb07f6cb371b, log .claude/verify-runs/T216-79b59ad75a7a.log
**Files:** `experiments/plugin-spike/` (new), `tests/test_plugin_spike.py` (new), `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` (new), `tasks/MINIMAL_LOG.md`, `PROJECT_KANBAN.md`
**Not done:** merge (yours); Codex gate cause (needs `/hooks` trust in an interactive Codex, or your OK for the bypass flag in the throwaway home)

## T214 — Remove the old background-spawn markers from git · minimal
**Asked:** "currently, the repos is messy with the file and the old setup also, let recheck and update the repos for clean," — then, asked about `.claude/markers`: "Remove them (Recommended)"
**Decisions:**
- Untrack all 88 files in `.claude/markers/` and delete them on disk — no code, hook or script reads that folder (`git grep` finds only board/task/memory text); last change 2026-09-23 (T122).
- Add `.claude/markers/` to `.gitignore` Section 6 (hook runtime state) — a later spawn that writes a marker must not show up as a change to commit.
- Assumed: the markers hold no record that is needed — each one is a `.pid`/`.done`/`.exit` flag or a copy of a spawn prompt; the tasks they belong to are Done with their evidence in `tasks/`. Git history keeps every file.
**Checked:**
- New test `tests/test_no_spawn_markers.py` — 2 failed before the change, `2 passed in 0.02s` after
- Suite: `python3 -m pytest -q tests .claude/hooks/tests` — `2535 passed, 25 subtests passed in 140.72s`
- Real run: `bash scripts/validate.sh` — printed `validate.sh: PASS`; `git ls-files .claude/markers | wc -l` — printed `0`
- verify: ☑ pass — auto-run by hook, session 43f193b7-9e5b-4be7-8d60-eb20f4e36552, commit d9af8829a55ef8dddf9c921a28c54d359c505ad7, log .claude/verify-runs/T214-d9af8829a55e.log
**Files:** `.gitignore`, `tests/test_no_spawn_markers.py`, `.claude/markers/` (88 files removed)
- Note: a first auto verify run at `e6a5e566` printed `verdict: pass` (log `.claude/verify-runs/T214-e6a5e566860b.log`) but could not write its line: the main checkout was switched to `main` mid-run, so this file was absent there.
**Not done:** merge (yours); auto verify: running
