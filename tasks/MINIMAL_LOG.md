# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. On first use, the Supervisor creates `tasks/MINIMAL_LOG.md` from
> this template and deletes the example comment. The same block is the Supervisor's final chat message.

## T119 — An aborted install says which path it did not replace, not "nothing was replaced" · minimal
Mode: auto
**Asked:** "yes, let go, and you can start for parallel task with tag [auto]"
**Decisions:**
1. T119 is a parallel task for this run: C0, Risk Low, it touches none of T250's files (`lib/harness-fetch.sh` and one test) — RULE: `docs/claude-md/tracks.md` `## Track rule` (minimal track); the last plan reply listed the small fixes as batch 2
2. The message names the one path and says earlier paths were installed: `'<path>' was not replaced; paths earlier in this run were already installed` — RULE: the T119 board row's scope ("the message wording, scoped to the one path … plus a test pinning it; explicitly NOT a rollback")
3. One wording serves all callers (install, Reinstall, Update `[o]verwrite`), because they share `harness_backup_path` — SAFER OPTION: "earlier paths in this run" is true when there are none, so no caller gets a false claim
**Checked:**
- New test `T119: abort says which path was not replaced, not 'nothing was replaced'` in `tests/test_install_backups.sh` — failed before the change (`17 passed, 1 failed`), passes after (`18 passed, 0 failed`)
- Suite: `python3 -m pytest .claude/hooks/tests/ tests/ -q` — `3163 passed, 25 subtests passed in 246.50s (0:04:06)`
- Real run (auto-checked, not /verify): `setup.sh` into a scratch git repo with its own `agents/mine.md` and an unwritable `docs/` — rc=1, printed `[warn]  Backed up your existing './agents' to './agents.bak-20261104' …` then `[error] Could not back up './docs/claude-md' to './docs/claude-md.bak-20261104' — './docs/claude-md' was not replaced; paths earlier in this run were already installed. Fix the permissions, then re-run.`; `agents/` then held the kit's `backend.md`, `common-infrastructure.md`, `frontend.md`, `qa.md`
**Files:** `lib/harness-fetch.sh`, `tests/test_install_backups.sh`, `tasks/MINIMAL_LOG.md`
**Memory:** nothing new
**Not done:** merge (yours); auto verify: running (T182)

## T248 — `ux-evaluate` measures tap targets and uses an absolute scratch folder · minimal
**Asked:** "let do it" (to: "add both as one small follow-up task" — the T245 verify run's two weak points: a relative screenshot path writes into the repo; B-d judged by eye)
**Decisions:**
- Minimal track: one small script, skill text, tests; C1, Risk Low, no UI component, no user data — `docs/claude-md/tracks.md` `## Track rule`
- Branch `fix/t248-ux-evaluate-measure` is cut from `feat/t245-ux-evaluate`, not `main` — the skill exists only on the T245 branch; T248 merges after T245
- B-d is measured by `skills/ux-evaluate/scripts/tap_probe.py`: it writes a copy of a static page (with `<base href>` so its CSS loads) that outlines targets under 44px in red and lists them as `name WxH` in a banner above the page — a screenshot alone gives no pixel size; the agent still reads the image, no new tool to install
- Inline links in a sentence are not counted (WCAG 2.5.8 exception); a checkbox inside a label is measured by its label
- Step 2 says `<dir>` is an absolute path from `mktemp -d`; the probe refuses a relative page or out dir
- The banner sits above the page, not fixed over it — the first run's fixed banner covered the header targets it should outline
- Assumed: static `file://` pages are the main case for the probe — a served app keeps the by-eye B-d; the skill says "for a static page"
**Checked:**
- New test `tests/test_t248_tap_probe.py` (5 tests, one drives headless Chrome on a fixture: a 80x20 button flagged, a 48px button, a 64px label row and an inline link not) — `5 failed in 2.24s` before the change, `5 passed` after; `tests/test_plugin_names.py` SAFE_ARGS gains `tap_probe.py --help`
- Suite: `python3 -m pytest .claude/hooks/tests/ tests/ -q` — `3157 passed, 25 subtests passed in 260.77s (0:04:20)`
- Real run: `python3 skills/ux-evaluate/scripts/tap_probe.py "$PWD/site/index.html" "$D"` then `google-chrome --headless --disable-gpu --window-size=375,500 --screenshot=$D/site-375.png "file://$D/index-probe.html"` — printed `52158 bytes written`; the image shows `tap-probe: 18 under 44px: Home 38x44; Docs 31x44; You ask 54x19; …` and red boxes on Home and Docs. On the blind-test build b2: `tap-probe: 0 under 44px`
- verify: ☑ pass — auto-run by hook, session 99e88592-3540-423f-b9d5-9760e24bf831, commit 60743097d132672e69bdffa04a8c55dffeea3812, log .claude/verify-runs/T248-60743097d132.log
**Files:** `skills/ux-evaluate/scripts/tap_probe.py`, `skills/ux-evaluate/SKILL.md`, `tests/test_t248_tap_probe.py`, `tests/test_plugin_names.py`, `tasks/MINIMAL_LOG.md`
**Memory:** `memory/learnings.md` — headless Chrome `--dump-dom` lays out at 500px; screenshots hide sideways overflow; tap targets measured, not judged by eye (T245, T248) (`eaf9ebd6` on main)
**Not done:** merge (yours; merge T245 first); auto verify: ☑ pass (session 99e88592-3540-423f-b9d5-9760e24bf831, commit 60743097d132672e69bdffa04a8c55dffeea3812, log .claude/verify-runs/T248-60743097d132.log)

## T229 — The auto-mode Stop check counts only work done under an `[auto]` request · minimal
Mode: auto
**Asked:** "continue [auto]"
**Decisions:**
1. "Continue" is T229, the P1 row next to T230 (P2) — RULE: `docs/claude-md/tracks.md` `### Every user stop and its auto rule` (decide from the repo); the last reply named T229 and T230 as next
2. Minimal track: two hook edits plus tests, C1, Risk Low, no UI, no user data — RULE: `docs/claude-md/tracks.md` `## Track rule`
3. An `[auto]` request covers the work until the next user request without the tag; a later `[auto]` request opens a new span — RULE: AGENTS.md § Tracks: "With the literal tag `[auto]` in the request (a bare word *auto* is not the tag), run either track in **auto mode**" — each request sets its own mode, so a plain `continue` is a normal-mode request
4. Tool results, task notifications (`origin.kind` not `human`), `isMeta` entries, the compact summary and `<bash-input>`/`<local-command` lines are not requests and do not close a span — FACT: this session's transcript holds them as `type: user` entries (204 tool results, 12 task notifications, 21 meta entries (skill bodies, reminders, peer messages), 2 `<bash-input>`, 1 compact summary), so counting them would close every span at the first tool call
5. The duplicate T228 row is fixed by telling the model, not by changing what the hook writes: the hook already skips an ID that has a row (`post_write_register_task.py` "Skip if already registered (any section)"); the second row came from a hand edit after the guide write (`ff45291b` added both rows). The notice now goes out as `additionalContext` — FACT: `.claude/hooks/post_bash_memory_update.py:93` "Plain stdout from a PostToolUse hook only reaches the debug log."
6. Residual: a plain reply inside an auto run (an answer `1` to a stop that stays, or a bare `continue`) closes the span. A report marked `Mode: auto` is still checked, because the marker does not depend on the span — SAFER OPTION: the span only matters for a report the Supervisor forgot to mark; the literal-tag rule decides the other way ⚠ decided for you — please review
**Checked:**
- New tests `test_t229_*` in `.claude/hooks/tests/test_stop_auto_mode_check.py` (4) — the bug case `test_t229_a_task_touched_after_a_later_plain_request_is_not_auto` failed before (`1 failed, 3 passed`), all 4 pass after; `test_t229_*` in `test_post_write_register_task_metadata.py` (2) — `1 failed, 1 passed` before, pass after
- Suite: `python3 -m pytest .claude/hooks/tests -q` — `1395 passed, 25 subtests passed in 39.06s`; `python3 -m pytest tests -q` — `1720 passed in 147.09s (0:02:27)`; `sh scripts/smoke-install.sh` — `smoke-install.sh: PASS`
- Real run (auto-checked, not /verify): `auto_windows()` on this session's own transcript — `window 11:57:06 -> 12:16:04`, `window 14:41:05 -> 14:54:57`, `window 14:56:03 -> open`; the 13:16:41 `continue` that started T244 is in no span, so T244's false `Mode: auto` flag would not fire
- verify: ☑ pass — auto-run by hook, session 7819efd6-8606-45e9-a214-f792ebee5be6, commit fa666f7e7a5dea4a9c99d4d8d2a27e0612b3e018, log .claude/verify-runs/T229-fa666f7e7a5d.log
**Files:** `.claude/hooks/stop_auto_mode_check.py`, `.claude/hooks/post_write_register_task.py`, `.claude/hooks/tests/test_stop_auto_mode_check.py`, `.claude/hooks/tests/test_post_write_register_task_metadata.py`, `tasks/MINIMAL_LOG.md`
**Memory:** `memory/learnings.md` — an `[auto]` request covers only the work before the next plain request; PostToolUse stderr never reaches the model (T229)
**Not done:** merge (yours); auto verify: ☑ pass (session 7819efd6-8606-45e9-a214-f792ebee5be6, commit fa666f7e7a5dea4a9c99d4d8d2a27e0612b3e018, log .claude/verify-runs/T229-fa666f7e7a5d.log)
Closed: row moved to Done 2026-11-03 — auto verify pass (session 7819efd6-8606-45e9-a214-f792ebee5be6, commit fa666f7e7a5dea4a9c99d4d8d2a27e0612b3e018); Gates 5 and 6 checked

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
