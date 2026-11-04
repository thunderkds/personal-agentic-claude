# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. On first use, the Supervisor creates `tasks/MINIMAL_LOG.md` from
> this template and deletes the example comment. The same block is the Supervisor's final chat message.

## T246 — RUNBOOK names the `plugin/` file copies T243 added · minimal
**Asked:** "do you update the guide, docs realtd"
**Decisions:**
- The copies are a release step (a version bump edits the root `plugin.json`), so the note goes in RUNBOOK beside the plugin health check — the RUNBOOK is where a release is run
- Track minimal: one doc paragraph plus one test, C0, Risk Low — `docs/claude-md/tracks.md` `## Track rule`
- The icon copy is named but gets no `cp` line — a new icon never reaches the listing after the first submission
**Checked:**
- New test `test_runbook_says_to_copy_the_root_files_into_plugin` — `1 failed, 6 passed` before the RUNBOOK edit, passes after
- Suite: `python3 -m pytest tests -q` — `1721 passed in 166.04s (0:02:46)`
- Real run: `python3 -m pytest tests/test_directory_prep.py tests/test_runbook_plugin_check.py tests/test_docs_match_installer.py -q` — `17 passed in 0.84s`
- verify: ☐ blocked — auto-run by hook, session 140d1256-22ee-43cb-b698-215abeaec77f, commit 4a7d220281200b40e6f66f68491f3b522931c7c6, log .claude/verify-runs/T246-4a7d22028120.log (no single verdict line)
- User-run check (2026-11-04, PASS; the merge gate reads only hook-written lines): `/verify` by the user in session f5ea81bb-c349-4953-9f6b-0307a641966a, commit 5244fce5adeb, 2026-11-04 (the auto run before it, session 140d1256-22ee-43cb-b698-215abeaec77f, was blocked: no single verdict line). In a temp checkout: root `plugin.json` bumped to 9.9.9, plugin copy stayed 2.2.0; after the two RUNBOOK `cp` commands the copy read 9.9.9 and was still a regular file; `claude plugin validate plugin --profile directory` → `✔ Validation passed with warnings`
- verify: ☑ pass — /verify by the user, session b286dcd6-92b4-495b-8604-629533af55b4, commit 1dadd18f5958f9764237054e67753e408dfd0eb9
**Files:** `RUNBOOK.md`, `tests/test_directory_prep.py`, `tasks/MINIMAL_LOG.md`
**Memory:** nothing new
**Not done:** merge (the user decides); auto verify: ☐ blocked (session 140d1256-22ee-43cb-b698-215abeaec77f, commit 4a7d220281200b40e6f66f68491f3b522931c7c6, log .claude/verify-runs/T246-4a7d22028120.log)
Paused: auto-mode check failed — its Decision record in tasks/MINIMAL_LOG.md does not start with `Mode: auto` [report 1bfa1c6ec64a]

## T243 — Plugin directory submission prep: icon, manifest and hooks the directory can read · minimal
Mode: auto
**Asked:** "continue, I saw you draw the icon for the index page, let use it [auto]"
**Decisions:**
1. "Continue" is T243, the open task waiting on the icon — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` (decide from the repo); the last reply named T243 as next
2. Minimal track: three copied files, one image, one new test, C1, Risk Low, no UI component, no user data — RULE: `docs/claude-md/tracks.md` `## Track rule`
3. The icon is the site header mark (`site/index.html` `.brand` svg: three linked nodes), mint `#3CF5A8` on the `#121413` tile, 1024 px PNG, drawn with Pillow — SAFER OPTION: "the icon for the index page" could also mean the favicon (a chevron); the header mark is the one drawn beside the name. Nothing is submitted until you submit, and the first icon submitted is permanent ⚠ decided for you — please review
4. `plugin/.claude-plugin/plugin.json` and `plugin/hooks/hooks.json` are real byte copies of the root files, not links (changes T242 D2 for these two paths only) — FACT: `claude plugin validate plugin --profile directory` printed `✘ Validation failed (--profile directory could not read the plugin's manifest)`, then with the manifest copied `HOOKS_FILE_UNREAD ... Fix: Ship hooks/hooks.json as a regular file`
5. The root keeps its real `plugin.json`, `hooks/hooks.json` and an icon copy — FACT: `.claude/hooks/lib/project_root.py:64` "True when `path` is a plugin package (T233 `.claude-plugin/plugin.json`)"; a root icon link was not read (`ICON_MISSING`)
6. `marketplace.json` gains `metadata.description` — FACT: validator `description: No marketplace description provided`; the warning is gone after
7. The root `CLAUDE.md` warning stays — RULE: AGENTS.md: "Claude Code loads it through the `@AGENTS.md` import that `CLAUDE.md` holds"; the directory checks `plugin/`, which has no `CLAUDE.md`
8. The linked folders in `plugin/` (agents, commands, skills) keep their `This directory is a symlink, so the validator read nothing in it` warnings — SAFER OPTION: they are warnings, not refusals (`--profile directory` exit 0); copying them would undo T242. Unknown: whether the directory's own safety scan follows them ⚠ decided for you — please review
**Checked:**
- New test `tests/test_directory_prep.py` (6 tests) — `6 failed in 0.79s` on unchanged `main` 911a17cc, `6 passed` after; `tests/test_plugin_source.py` link-only pins updated for the 3 real files
- Suite: `python3 -m pytest tests -q` — `1720 passed in 161.77s (0:02:41)`; `python3 -m pytest .claude/hooks/tests -q` — `1389 passed, 25 subtests passed in 69.65s`; `sh scripts/smoke-install.sh` — `smoke-install.sh: PASS`
- Real run (auto-checked, not /verify): `claude plugin validate plugin --profile directory` — `✔ These checks found nothing to report` / `✔ Validation passed with warnings`, exit 0; root `--profile directory` — `✔ These checks found nothing to report`. Isolated install of this branch from a local smart-HTTP git marketplace (`CLAUDE_CONFIG_DIR` + scratch `HOME`, no SSH) — `✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)`; cache 1.3M, 0 links, `.claude-plugin/icon.png` present, `hooks/hooks.json` equal to root, no `.claude/hooks/tests`; `scripts/plugin_init.py` in a fresh repo ran and printed its notes
- verify: ☑ pass — auto-run by hook, session 3f69be33-29a4-4f42-ad30-a2c6d499c423, commit 40d1359815dc48cb4ceda739110df09aa133921d, log .claude/verify-runs/T243-40d1359815dc.log
**Files:** `.claude-plugin/marketplace.json`, `.claude-plugin/icon.png`, `plugin/.claude-plugin/plugin.json`, `plugin/.claude-plugin/icon.png`, `plugin/hooks/hooks.json`, `tests/test_directory_prep.py`, `tests/test_plugin_source.py`, `tasks/MINIMAL_LOG.md`
**Memory:** `memory/learnings.md` — the plugin directory reads no file through a link (T243)
**Not done:** merge (yours); the submission at claude.ai/directory/manage (yours); auto verify: ☑ pass (session 3f69be33-29a4-4f42-ad30-a2c6d499c423, commit 40d1359815dc48cb4ceda739110df09aa133921d, log .claude/verify-runs/T243-40d1359815dc.log)
Closed: row moved to Done 2026-11-03 — auto verify pass (session 3f69be33-29a4-4f42-ad30-a2c6d499c423, commit 40d1359815dc48cb4ceda739110df09aa133921d); Gates 5 and 6 checked

## T244 — Auto close-out writes `Closed:` into the report, not the template comment · minimal
**Asked:** "continue"
**Decisions:**
- Took T244, the open Low-risk follow-up; T243 waits for the user's icon — the first submitted icon cannot be changed.
- Fixed `auto_mode.section()` (`skip_comments=True`): a comment that ends the block (only blank lines and comments after it) is no longer part of the block. A comment between two fields stays inside. Every reader that skips comments gets the same boundary; with no comment after the block, nothing changes.
- First fix (`853daa7e`) cut the block at *any* comment; auto verify failed it: an inline `<!-- note -->` between `Checks:` and `Memory:` hid the fields below it (`report incomplete: Memory:`), a regression against `main`. Second fix keeps inline comments; two tests pin that case.
- Left T242's existing hidden `Closed:` line as written — it is the audit trail of that run, and the row is already Done.
- Assumed: no report puts its own fields inside a comment on purpose — the template says to copy the block out of the comment.
**Checked:**
- New test `tests/test_closeout_comment_boundary.py` (6 tests) — `2 failed, 2 passed` before the first fix (2026-11-03T13:17:33Z); the 2 inline-comment tests `2 failed, 4 passed` on `853daa7e`; `6 passed` after the second fix
- Suite (2026-11-03T13:24:04Z): `python3 -m pytest tests -q` — `1715 passed in 136.54s (0:02:16)`; `python3 -m pytest .claude/hooks/tests -q` — `1389 passed, 25 subtests passed in 28.90s`
- Real run: `auto_closeout.add_line` on T242's review file as committed at `87a03426` (before its close-out) — printed `Closed at char 2611 | comment starts at 2685 | inside comment: False`; re-run on the second fix — `real T242 file: inside comment: False`
- verify: ☑ pass — auto-run by hook, session 82210a04-e5b6-4280-a86a-da31a0789279, commit 8e7eeb82ee4c694756ec43f4296a7e72d9fa98bb, log .claude/verify-runs/T244-8e7eeb82ee4c.log
**Memory:** nothing new until the merge (normal mode; the memory pass runs at merge)
**Files:** `.claude/hooks/lib/auto_mode.py`, `tests/test_closeout_comment_boundary.py`, `tasks/MINIMAL_LOG.md`
**Not done:** merge (the user decides); auto verify: ☑ pass (session 82210a04-e5b6-4280-a86a-da31a0789279, commit 8e7eeb82ee4c694756ec43f4296a7e72d9fa98bb, log .claude/verify-runs/T244-8e7eeb82ee4c.log) — the first run failed at `853daa7e` (log .claude/verify-runs/T244-853daa7e711c.log)
Paused: auto-mode check failed — its Decision record in tasks/MINIMAL_LOG.md does not start with `Mode: auto`; no `Memory:` line in the report — run the memory pass before you stop and record it there (each entry written, or `Memory: nothing new`) [report fe3d759cbe82]
Paused: auto-mode check failed — its Decision record in tasks/MINIMAL_LOG.md does not start with `Mode: auto` [report fdab48bc4fb8]

## T241 — RUNBOOK post-deploy check also installs the plugin from GitHub · minimal
Mode: auto
**Asked:** "and continue the task [auto]"
**Decisions:**
1. "The task" is T241, the one P1 follow-up T236 left on the board — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` (decide from the repo); the user's last two requests were T236's merge and push
2. Minimal track: one doc section plus one new test, C1, Risk Low, no UI, no user data — RULE: `docs/claude-md/tracks.md` `## Track rule`
3. The plugin check installs into a throwaway `CLAUDE_CONFIG_DIR` and deletes it, never the operator's own config — SAFER OPTION: same isolation T236 used; an install into the real config would change every project the operator opens ⚠ decided for you — please review
4. Added it as step 5 after the `setup.sh` check, plus one rollback trigger line; the `setup.sh` check is unchanged — RULE: Surgical Changes (AGENTS.md § Karpathy Engineering Principles)
5. Fixed `main` first: `memory/MEMORY.md` was 42,209 chars, over the 42,000 hot-tier budget, after the T236/T240 memory passes, so 5 hook tests failed on `main`; shortened 5 index lines (2 commits on `main`, `5bbc1888`, `48a04e32`) and rebased this branch on them — RULE: Hard-Stop Gate 5 needs a passing suite; the overage was the Supervisor's own memory write
**Checked:**
- New test `tests/test_runbook_plugin_check.py` (4 tests) — `4 failed in 0.03s` before the change (2026-11-03T11:46:19Z), `4 passed in 0.02s` after
- Suite: `python3 -m pytest tests -q` — `1677 passed in 164.27s (0:02:44)`; `python3 -m pytest .claude/hooks/tests -q` after the rebase — `1389 passed, 25 subtests passed in 34.06s`
- Real run (auto-checked, not /verify): the step-5 block as written, 2026-11-03T11:46:46Z — `✔ Successfully added marketplace: easy-kit (declared in user settings)`, exit 0; `✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)`, exit 0; `claude plugin list` → `easy-kit@easy-kit  Version: 2.2.0  Status: ✔ enabled`, matching `.claude-plugin/plugin.json` `"version": "2.2.0"`
- verify: ☑ pass — auto-run by hook, session 338ea189-d1b0-402a-b1a2-c24106f9caa7, commit d28532c29e8b503e32dcd24953c029d53ddfb78a, log .claude/verify-runs/T241-d28532c29e8b.log
**Files:** `RUNBOOK.md`, `tests/test_runbook_plugin_check.py`, `tasks/MINIMAL_LOG.md`
**Memory:** `memory/MEMORY.md` — 5 index lines shortened to the 42,000-char budget; the minimal-track state-file line now says the Supervisor's write worked (T241)
**Not done:** merge (yours); push of `main` (yours: 2 memory commits); auto verify: ☑ pass (session 338ea189-d1b0-402a-b1a2-c24106f9caa7, commit d28532c29e8b503e32dcd24953c029d53ddfb78a, log .claude/verify-runs/T241-d28532c29e8b.log)
Closed: row moved to Done 2026-11-03 — auto verify pass (session 338ea189-d1b0-402a-b1a2-c24106f9caa7, commit d28532c29e8b503e32dcd24953c029d53ddfb78a); Gates 5 and 6 checked

## T238 — Rename a report file that clashed on Windows and macOS · minimal
**Asked:** "got this one when upload the pluggin Two file or folder names would clash on Windows or macOS Two files or folders in or beside the plugin folder differ only by letter case, Unicode form, a trailing dot, or a Windows short name (such as PROGRA~1), so a checkout on Windows or macOS would merge them. Rename one, then validate again."
**Decisions:**
- Renamed `experiments/kit-arms/results/REPORT.md` (the written analysis) to `ANALYSIS.md`, not `report.md` — `run_arms.py` writes `report.md`, so renaming that one would bring the clash back on a rerun.
- Left `tasks/` guides and reviews naming the old path — they are the audit trail of T176/T177.
- Assumed: this is the only clash — the new test scans every tracked path for case, Unicode form and trailing dots.
**Checked:**
- New test `test_no_tracked_names_clash_on_windows_or_macos` — failed before the rename, passes after: 8 passed in 0.96s
- Suite: `python3 -m pytest tests -q` — 1570 passed in 151.22s (0:02:31); `python3 -m pytest .claude/hooks/tests -q` — 1389 passed, 25 subtests passed in 46.44s; `python3 -m pytest experiments/kit-arms/tests -q` — 74 passed in 350.17s (0:05:50)
- Real run: `claude plugin validate . --profile directory` — printed `✔ Validation passed with warnings`. The upload check itself was not rerun: only the user's upload runs it.
- verify: ☑ pass — auto-run by hook, session 1610b4b1-a2dd-4aee-8d00-42e554a0765e, commit b81f49dedbe3ad0b302a20d470e0e8584e0d6989, log .claude/verify-runs/T238-b81f49dedbe3.log
**Files:** `experiments/kit-arms/results/ANALYSIS.md`, `experiments/kit-arms/RULE-2.md`, `memory/learnings.md`, `tests/test_plugin_package.py`
**Not done:** merge (the user decides); auto verify: ☑ pass (session 1610b4b1-a2dd-4aee-8d00-42e554a0765e, commit b81f49dedbe3ad0b302a20d470e0e8584e0d6989, log .claude/verify-runs/T238-b81f49dedbe3.log)

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
